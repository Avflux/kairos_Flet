import unittest
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from models.interfaces import (
    NotificationServiceInterface,
    TimeTrackingServiceInterface,
    WorkflowServiceInterface,
    ActivityServiceInterface,
    StorageInterface,
    MAX_NOTIFICATION_TITLE_LENGTH,
    MAX_ACTIVITY_NAME_LENGTH,
    DEFAULT_TIMER_UPDATE_INTERVAL
)
from models.notification import Notification, NotificationType
from models.activity import Activity
from models.time_entry import TimeEntry
from models.workflow_state import WorkflowState, WorkflowStage


class MockNotificationService(NotificationServiceInterface):
    """Mock implementation for testing."""
    
    def __init__(self):
        self.notifications: List[Notification] = []
    
    def add_notification(self, notification: Notification) -> None:
        self.notifications.append(notification)
    
    def get_notifications(self, limit: Optional[int] = None) -> List[Notification]:
        if limit:
            return self.notifications[:limit]
        return self.notifications.copy()
    
    def get_unread_notifications(self) -> List[Notification]:
        return [n for n in self.notifications if not n.is_read]
    
    def mark_as_read(self, notification_id: str) -> bool:
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.mark_as_read()
                return True
        return False
    
    def mark_all_as_read(self) -> int:
        count = 0
        for notification in self.notifications:
            if not notification.is_read:
                notification.mark_as_read()
                count += 1
        return count
    
    def clear_all(self) -> int:
        count = len(self.notifications)
        self.notifications.clear()
        return count
    
    def get_unread_count(self) -> int:
        return len(self.get_unread_notifications())


class MockTimeTrackingService(TimeTrackingServiceInterface):
    """Mock implementation for testing."""
    
    def __init__(self):
        self.current_entry: Optional[TimeEntry] = None
        self.time_entries: List[TimeEntry] = []
        self.is_paused = False
    
    def start_tracking(self, activity: Activity) -> TimeEntry:
        if self.current_entry and self.current_entry.is_active:
            self.stop_tracking()
        
        self.current_entry = TimeEntry(
            activity_id=activity.id,
            start_time=datetime.now()
        )
        self.is_paused = False
        return self.current_entry
    
    def stop_tracking(self) -> Optional[TimeEntry]:
        if self.current_entry and self.current_entry.is_active:
            self.current_entry.stop()
            self.time_entries.append(self.current_entry)
            completed_entry = self.current_entry
            self.current_entry = None
            self.is_paused = False
            return completed_entry
        return None
    
    def pause_tracking(self) -> bool:
        if self.current_entry and self.current_entry.is_active and not self.is_paused:
            self.is_paused = True
            return True
        return False
    
    def resume_tracking(self) -> bool:
        if self.current_entry and self.current_entry.is_active and self.is_paused:
            self.is_paused = False
            return True
        return False
    
    def get_current_entry(self) -> Optional[TimeEntry]:
        return self.current_entry
    
    def get_time_entries(self, activity_id: Optional[str] = None) -> List[TimeEntry]:
        if activity_id:
            return [entry for entry in self.time_entries if entry.activity_id == activity_id]
        return self.time_entries.copy()
    
    def is_tracking(self) -> bool:
        return self.current_entry is not None and self.current_entry.is_active and not self.is_paused
    
    def get_elapsed_time(self) -> timedelta:
        if self.current_entry:
            return self.current_entry.duration
        return timedelta()


class TestInterfaces(unittest.TestCase):
    
    def test_notification_service_interface(self):
        """Test notification service interface implementation."""
        service = MockNotificationService()
        
        # Test adding notification
        notification = Notification(
            title='Test',
            message='Test message',
            type=NotificationType.INFO
        )
        service.add_notification(notification)
        
        # Test getting notifications
        notifications = service.get_notifications()
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].title, 'Test')
        
        # Test unread count
        self.assertEqual(service.get_unread_count(), 1)
        
        # Test marking as read
        self.assertTrue(service.mark_as_read(notification.id))
        self.assertEqual(service.get_unread_count(), 0)
        
        # Test clearing all
        count = service.clear_all()
        self.assertEqual(count, 1)
        self.assertEqual(len(service.get_notifications()), 0)
    
    def test_time_tracking_service_interface(self):
        """Test time tracking service interface implementation."""
        service = MockTimeTrackingService()
        activity = Activity(name='Test Activity', category='Development')
        
        # Test starting tracking
        entry = service.start_tracking(activity)
        self.assertIsNotNone(entry)
        self.assertTrue(service.is_tracking())
        
        # Test pausing
        self.assertTrue(service.pause_tracking())
        self.assertFalse(service.is_tracking())
        
        # Test resuming
        self.assertTrue(service.resume_tracking())
        self.assertTrue(service.is_tracking())
        
        # Test stopping
        completed_entry = service.stop_tracking()
        self.assertIsNotNone(completed_entry)
        self.assertFalse(service.is_tracking())
        
        # Test getting entries
        entries = service.get_time_entries()
        self.assertEqual(len(entries), 1)
    
    def test_constants_validation(self):
        """Test that constants are properly defined."""
        self.assertIsInstance(MAX_NOTIFICATION_TITLE_LENGTH, int)
        self.assertGreater(MAX_NOTIFICATION_TITLE_LENGTH, 0)
        
        self.assertIsInstance(MAX_ACTIVITY_NAME_LENGTH, int)
        self.assertGreater(MAX_ACTIVITY_NAME_LENGTH, 0)
        
        self.assertIsInstance(DEFAULT_TIMER_UPDATE_INTERVAL, float)
        self.assertGreater(DEFAULT_TIMER_UPDATE_INTERVAL, 0)
    
    def test_interface_inheritance(self):
        """Test that interfaces can be properly inherited."""
        # This test ensures that the abstract base classes work correctly
        service = MockNotificationService()
        self.assertIsInstance(service, NotificationServiceInterface)
        
        time_service = MockTimeTrackingService()
        self.assertIsInstance(time_service, TimeTrackingServiceInterface)


if __name__ == '__main__':
    unittest.main()