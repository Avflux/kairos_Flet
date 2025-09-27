from typing import List, Optional, Callable
from datetime import datetime
import logging
from models.notification import Notification, NotificationType
from views.components.error_handling import (
    ErrorBoundary, get_recovery_manager, get_storage_manager,
    ErrorSeverity, ErrorContext
)


class NotificationService:
    """Service for managing notifications in the Kairos application."""
    
    def __init__(self):
        """Initialize the notification service."""
        self._notifications: List[Notification] = []
        self._observers: List[Callable[[Notification], None]] = []
        self._recovery_manager = get_recovery_manager()
        self._storage_manager = get_storage_manager()
        
        # Register recovery strategies
        self._recovery_manager.register_recovery_strategy(
            'NotificationLoadError', self._recover_from_load_error
        )
        self._recovery_manager.register_recovery_strategy(
            'NotificationSaveError', self._recover_from_save_error
        )
        
        # Try to restore notifications from backup
        self._restore_notifications_from_backup()
    
    def add_notification(self, 
                        title: str, 
                        message: str, 
                        notification_type: NotificationType = NotificationType.INFO,
                        action_url: Optional[str] = None) -> Optional[Notification]:
        """
        Add a new notification to the system with error handling.
        
        Args:
            title: The notification title
            message: The notification message
            notification_type: The type of notification (default: INFO)
            action_url: Optional URL for notification action
            
        Returns:
            The created notification or None if failed
        """
        try:
            # Validate inputs
            if not title or not message:
                raise ValueError("Title and message are required")
            
            notification = Notification(
                title=title,
                message=message,
                type=notification_type,
                action_url=action_url
            )
            
            self._notifications.append(notification)
            
            # Backup notifications after adding
            self._backup_notifications()
            
            self._notify_observers(notification)
            
            return notification
            
        except Exception as e:
            logging.error(f"Failed to add notification: {e}")
            context = ErrorContext(
                component_name="NotificationService",
                operation="add_notification",
                user_data={"title": title, "message": message, "type": notification_type.value}
            )
            self._recovery_manager.record_error(context)
            return None
    
    def get_notifications(self, 
                         unread_only: bool = False,
                         notification_type: Optional[NotificationType] = None) -> List[Notification]:
        """
        Get notifications based on filters.
        
        Args:
            unread_only: If True, return only unread notifications
            notification_type: Filter by notification type
            
        Returns:
            List of filtered notifications
        """
        notifications = self._notifications.copy()
        
        if unread_only:
            notifications = [n for n in notifications if not n.is_read]
        
        if notification_type:
            notifications = [n for n in notifications if n.type == notification_type]
        
        # Sort by timestamp, newest first
        notifications.sort(key=lambda n: n.timestamp, reverse=True)
        
        return notifications
    
    def get_notification_by_id(self, notification_id: str) -> Optional[Notification]:
        """
        Get a specific notification by ID.
        
        Args:
            notification_id: The notification ID
            
        Returns:
            The notification if found, None otherwise
        """
        for notification in self._notifications:
            if notification.id == notification_id:
                return notification
        return None
    
    def mark_as_read(self, notification_id: str) -> bool:
        """
        Mark a notification as read.
        
        Args:
            notification_id: The notification ID
            
        Returns:
            True if notification was found and marked as read, False otherwise
        """
        notification = self.get_notification_by_id(notification_id)
        if notification:
            notification.mark_as_read()
            return True
        return False
    
    def mark_as_unread(self, notification_id: str) -> bool:
        """
        Mark a notification as unread.
        
        Args:
            notification_id: The notification ID
            
        Returns:
            True if notification was found and marked as unread, False otherwise
        """
        notification = self.get_notification_by_id(notification_id)
        if notification:
            notification.mark_as_unread()
            return True
        return False
    
    def mark_all_as_read(self) -> int:
        """
        Mark all notifications as read.
        
        Returns:
            Number of notifications marked as read
        """
        count = 0
        for notification in self._notifications:
            if not notification.is_read:
                notification.mark_as_read()
                count += 1
        return count
    
    def clear_all_notifications(self) -> int:
        """
        Clear all notifications from the system.
        
        Returns:
            Number of notifications cleared
        """
        count = len(self._notifications)
        self._notifications.clear()
        return count
    
    def clear_read_notifications(self) -> int:
        """
        Clear only read notifications from the system.
        
        Returns:
            Number of notifications cleared
        """
        initial_count = len(self._notifications)
        self._notifications = [n for n in self._notifications if not n.is_read]
        return initial_count - len(self._notifications)
    
    def get_unread_count(self) -> int:
        """
        Get the count of unread notifications.
        
        Returns:
            Number of unread notifications
        """
        return len([n for n in self._notifications if not n.is_read])
    
    def add_observer(self, observer: Callable[[Notification], None]) -> None:
        """
        Add an observer to be notified when new notifications are added.
        
        Args:
            observer: Callback function that takes a Notification parameter
        """
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer: Callable[[Notification], None]) -> None:
        """
        Remove an observer from the notification system.
        
        Args:
            observer: The observer callback to remove
        """
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify_observers(self, notification: Notification) -> None:
        """
        Notify all observers about a new notification with enhanced error handling.
        
        Args:
            notification: The new notification
        """
        failed_observers = []
        
        for observer in self._observers:
            try:
                observer(notification)
            except Exception as e:
                # Log error but don't let observer failures break the service
                logging.error(f"Error notifying observer: {e}")
                failed_observers.append(observer)
        
        # Remove failed observers to prevent repeated failures
        for failed_observer in failed_observers:
            try:
                self._observers.remove(failed_observer)
                logging.warning(f"Removed failed observer: {failed_observer}")
            except ValueError:
                pass  # Observer already removed
    
    def _backup_notifications(self) -> None:
        """Backup notifications to local storage."""
        try:
            # Convert notifications to serializable format
            backup_data = [
                {
                    'id': n.id,
                    'title': n.title,
                    'message': n.message,
                    'type': n.type.value,
                    'timestamp': n.timestamp.isoformat(),
                    'is_read': n.is_read,
                    'action_url': n.action_url
                }
                for n in self._notifications
            ]
            
            self._storage_manager.backup_data('notifications', backup_data)
        except Exception as e:
            logging.error(f"Failed to backup notifications: {e}")
    
    def _restore_notifications_from_backup(self) -> None:
        """Restore notifications from local storage backup."""
        try:
            backup_data = self._storage_manager.restore_data('notifications')
            if backup_data:
                for item in backup_data:
                    try:
                        notification = Notification(
                            id=item['id'],
                            title=item['title'],
                            message=item['message'],
                            type=NotificationType(item['type']),
                            timestamp=datetime.fromisoformat(item['timestamp']),
                            is_read=item['is_read'],
                            action_url=item.get('action_url')
                        )
                        self._notifications.append(notification)
                    except Exception as e:
                        logging.warning(f"Failed to restore notification: {e}")
                
                logging.info(f"Restored {len(self._notifications)} notifications from backup")
        except Exception as e:
            logging.error(f"Failed to restore notifications from backup: {e}")
    
    def _recover_from_load_error(self, context: ErrorContext) -> bool:
        """Recovery strategy for notification loading errors."""
        try:
            # Try to restore from backup
            self._restore_notifications_from_backup()
            return True
        except Exception as e:
            logging.error(f"Recovery from load error failed: {e}")
            return False
    
    def _recover_from_save_error(self, context: ErrorContext) -> bool:
        """Recovery strategy for notification saving errors."""
        try:
            # Retry backup operation
            self._backup_notifications()
            return True
        except Exception as e:
            logging.error(f"Recovery from save error failed: {e}")
            return False