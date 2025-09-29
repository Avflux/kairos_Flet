import unittest
from unittest.mock import Mock
from datetime import datetime
from services.notification_service import NotificationService
from models.notification import Notification, NotificationType


class TestNotificationService(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = NotificationService()
    
    def test_service_initialization(self):
        """Test that the service initializes correctly."""
        self.assertEqual(len(self.service._notifications), 0)
        self.assertEqual(len(self.service._observers), 0)
        self.assertEqual(self.service.get_unread_count(), 0)
    
    def test_add_notification_basic(self):
        """Test adding a basic notification."""
        notification = self.service.add_notification(
            title="Test Title",
            message="Test Message"
        )
        
        self.assertIsInstance(notification, Notification)
        self.assertEqual(notification.title, "Test Title")
        self.assertEqual(notification.message, "Test Message")
        self.assertEqual(notification.type, NotificationType.INFO)
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.action_url)
        self.assertEqual(len(self.service._notifications), 1)
    
    def test_add_notification_with_type_and_action(self):
        """Test adding a notification with specific type and action URL."""
        notification = self.service.add_notification(
            title="Error Title",
            message="Error Message",
            notification_type=NotificationType.ERROR,
            action_url="https://example.com/fix"
        )
        
        self.assertEqual(notification.type, NotificationType.ERROR)
        self.assertEqual(notification.action_url, "https://example.com/fix")
    
    def test_get_notifications_all(self):
        """Test getting all notifications."""
        # Add multiple notifications
        self.service.add_notification("Title 1", "Message 1", NotificationType.INFO)
        self.service.add_notification("Title 2", "Message 2", NotificationType.WARNING)
        self.service.add_notification("Title 3", "Message 3", NotificationType.ERROR)
        
        notifications = self.service.get_notifications()
        self.assertEqual(len(notifications), 3)
        
        # Should be sorted by timestamp, newest first
        self.assertEqual(notifications[0].title, "Title 3")
        self.assertEqual(notifications[1].title, "Title 2")
        self.assertEqual(notifications[2].title, "Title 1")
    
    def test_get_notifications_unread_only(self):
        """Test getting only unread notifications."""
        # Add notifications and mark one as read
        n1 = self.service.add_notification("Title 1", "Message 1")
        n2 = self.service.add_notification("Title 2", "Message 2")
        n3 = self.service.add_notification("Title 3", "Message 3")
        
        self.service.mark_as_read(n2.id)
        
        unread_notifications = self.service.get_notifications(unread_only=True)
        self.assertEqual(len(unread_notifications), 2)
        
        unread_titles = [n.title for n in unread_notifications]
        self.assertIn("Title 1", unread_titles)
        self.assertIn("Title 3", unread_titles)
        self.assertNotIn("Title 2", unread_titles)
    
    def test_get_notifications_by_type(self):
        """Test getting notifications filtered by type."""
        self.service.add_notification("Info 1", "Message", NotificationType.INFO)
        self.service.add_notification("Warning 1", "Message", NotificationType.WARNING)
        self.service.add_notification("Info 2", "Message", NotificationType.INFO)
        self.service.add_notification("Error 1", "Message", NotificationType.ERROR)
        
        info_notifications = self.service.get_notifications(notification_type=NotificationType.INFO)
        self.assertEqual(len(info_notifications), 2)
        
        warning_notifications = self.service.get_notifications(notification_type=NotificationType.WARNING)
        self.assertEqual(len(warning_notifications), 1)
        
        error_notifications = self.service.get_notifications(notification_type=NotificationType.ERROR)
        self.assertEqual(len(error_notifications), 1)
    
    def test_get_notification_by_id(self):
        """Test getting a specific notification by ID."""
        notification = self.service.add_notification("Test", "Message")
        
        found_notification = self.service.get_notification_by_id(notification.id)
        self.assertIsNotNone(found_notification)
        self.assertEqual(found_notification.id, notification.id)
        self.assertEqual(found_notification.title, "Test")
        
        # Test with non-existent ID
        not_found = self.service.get_notification_by_id("non-existent-id")
        self.assertIsNone(not_found)
    
    def test_mark_as_read(self):
        """Test marking a notification as read."""
        notification = self.service.add_notification("Test", "Message")
        self.assertFalse(notification.is_read)
        
        result = self.service.mark_as_read(notification.id)
        self.assertTrue(result)
        self.assertTrue(notification.is_read)
        
        # Test with non-existent ID
        result = self.service.mark_as_read("non-existent-id")
        self.assertFalse(result)
    
    def test_mark_as_unread(self):
        """Test marking a notification as unread."""
        notification = self.service.add_notification("Test", "Message")
        notification.mark_as_read()
        self.assertTrue(notification.is_read)
        
        result = self.service.mark_as_unread(notification.id)
        self.assertTrue(result)
        self.assertFalse(notification.is_read)
        
        # Test with non-existent ID
        result = self.service.mark_as_unread("non-existent-id")
        self.assertFalse(result)
    
    def test_mark_all_as_read(self):
        """Test marking all notifications as read."""
        # Add multiple notifications
        n1 = self.service.add_notification("Title 1", "Message 1")
        n2 = self.service.add_notification("Title 2", "Message 2")
        n3 = self.service.add_notification("Title 3", "Message 3")
        
        # Mark one as read already
        self.service.mark_as_read(n2.id)
        
        count = self.service.mark_all_as_read()
        self.assertEqual(count, 2)  # Only 2 were unread
        
        # All should now be read
        self.assertTrue(n1.is_read)
        self.assertTrue(n2.is_read)
        self.assertTrue(n3.is_read)
    
    def test_clear_all_notifications(self):
        """Test clearing all notifications."""
        # Add multiple notifications
        self.service.add_notification("Title 1", "Message 1")
        self.service.add_notification("Title 2", "Message 2")
        self.service.add_notification("Title 3", "Message 3")
        
        self.assertEqual(len(self.service._notifications), 3)
        
        count = self.service.clear_all_notifications()
        self.assertEqual(count, 3)
        self.assertEqual(len(self.service._notifications), 0)
    
    def test_clear_read_notifications(self):
        """Test clearing only read notifications."""
        # Add multiple notifications
        n1 = self.service.add_notification("Title 1", "Message 1")
        n2 = self.service.add_notification("Title 2", "Message 2")
        n3 = self.service.add_notification("Title 3", "Message 3")
        
        # Mark some as read
        self.service.mark_as_read(n1.id)
        self.service.mark_as_read(n3.id)
        
        count = self.service.clear_read_notifications()
        self.assertEqual(count, 2)  # 2 read notifications cleared
        self.assertEqual(len(self.service._notifications), 1)
        
        # Only unread notification should remain
        remaining = self.service.get_notifications()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].title, "Title 2")
        self.assertFalse(remaining[0].is_read)
    
    def test_get_unread_count(self):
        """Test getting the count of unread notifications."""
        self.assertEqual(self.service.get_unread_count(), 0)
        
        # Add notifications
        n1 = self.service.add_notification("Title 1", "Message 1")
        n2 = self.service.add_notification("Title 2", "Message 2")
        n3 = self.service.add_notification("Title 3", "Message 3")
        
        self.assertEqual(self.service.get_unread_count(), 3)
        
        # Mark some as read
        self.service.mark_as_read(n1.id)
        self.assertEqual(self.service.get_unread_count(), 2)
        
        self.service.mark_as_read(n2.id)
        self.assertEqual(self.service.get_unread_count(), 1)
        
        self.service.mark_as_read(n3.id)
        self.assertEqual(self.service.get_unread_count(), 0)
    
    def test_observer_pattern(self):
        """Test the observer pattern for new notifications."""
        observer_mock = Mock()
        
        # Add observer
        self.service.add_observer(observer_mock)
        self.assertEqual(len(self.service._observers), 1)
        
        # Add notification - observer should be called
        notification = self.service.add_notification("Test", "Message")
        observer_mock.assert_called_once_with(notification)
        
        # Remove observer
        self.service.remove_observer(observer_mock)
        self.assertEqual(len(self.service._observers), 0)
        
        # Add another notification - observer should not be called
        observer_mock.reset_mock()
        self.service.add_notification("Test 2", "Message 2")
        observer_mock.assert_not_called()
    
    def test_observer_error_handling(self):
        """Test that observer errors don't break the service."""
        def failing_observer(notification):
            raise Exception("Observer error")
        
        working_observer = Mock()
        
        # Add both observers
        self.service.add_observer(failing_observer)
        self.service.add_observer(working_observer)
        
        # Add notification - should not raise exception despite failing observer
        notification = self.service.add_notification("Test", "Message")
        
        # Working observer should still be called
        working_observer.assert_called_once_with(notification)
        
        # Notification should still be added
        self.assertEqual(len(self.service._notifications), 1)
    
    def test_duplicate_observer_prevention(self):
        """Test that duplicate observers are not added."""
        observer_mock = Mock()
        
        # Add observer twice
        self.service.add_observer(observer_mock)
        self.service.add_observer(observer_mock)
        
        # Should only be added once
        self.assertEqual(len(self.service._observers), 1)
        
        # Should only be called once when notification is added
        notification = self.service.add_notification("Test", "Message")
        observer_mock.assert_called_once_with(notification)


if __name__ == '__main__':
    unittest.main()