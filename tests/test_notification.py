import unittest
from datetime import datetime
from models.notification import Notification, NotificationType


class TestNotification(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.valid_notification_data = {
            'title': 'Test Notification',
            'message': 'This is a test message',
            'type': NotificationType.INFO
        }
    
    def test_notification_creation_valid(self):
        """Test creating a valid notification."""
        notification = Notification(**self.valid_notification_data)
        
        self.assertEqual(notification.title, 'Test Notification')
        self.assertEqual(notification.message, 'This is a test message')
        self.assertEqual(notification.type, NotificationType.INFO)
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.action_url)
        self.assertIsInstance(notification.timestamp, datetime)
        self.assertIsInstance(notification.id, str)
    
    def test_notification_validation_empty_title(self):
        """Test validation fails with empty title."""
        with self.assertRaises(ValueError) as context:
            Notification(
                title='',
                message='Valid message',
                type=NotificationType.INFO
            )
        self.assertIn('title cannot be empty', str(context.exception))
    
    def test_notification_validation_empty_message(self):
        """Test validation fails with empty message."""
        with self.assertRaises(ValueError) as context:
            Notification(
                title='Valid title',
                message='',
                type=NotificationType.INFO
            )
        self.assertIn('message cannot be empty', str(context.exception))
    
    def test_notification_validation_invalid_type(self):
        """Test validation fails with invalid type."""
        with self.assertRaises(ValueError) as context:
            notification = Notification(
                title='Valid title',
                message='Valid message',
                type='invalid_type'  # This should be NotificationType
            )
        self.assertIn('must be a NotificationType enum', str(context.exception))
    
    def test_notification_mark_as_read(self):
        """Test marking notification as read."""
        notification = Notification(**self.valid_notification_data)
        self.assertFalse(notification.is_read)
        
        notification.mark_as_read()
        self.assertTrue(notification.is_read)
    
    def test_notification_mark_as_unread(self):
        """Test marking notification as unread."""
        notification = Notification(**self.valid_notification_data)
        notification.mark_as_read()
        self.assertTrue(notification.is_read)
        
        notification.mark_as_unread()
        self.assertFalse(notification.is_read)
    
    def test_notification_to_dict(self):
        """Test converting notification to dictionary."""
        notification = Notification(**self.valid_notification_data)
        result = notification.to_dict()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['title'], 'Test Notification')
        self.assertEqual(result['message'], 'This is a test message')
        self.assertEqual(result['type'], 'info')
        self.assertFalse(result['is_read'])
        self.assertIsNone(result['action_url'])
        self.assertIn('id', result)
        self.assertIn('timestamp', result)
    
    def test_notification_from_dict(self):
        """Test creating notification from dictionary."""
        notification = Notification(**self.valid_notification_data)
        data = notification.to_dict()
        
        restored_notification = Notification.from_dict(data)
        
        self.assertEqual(restored_notification.title, notification.title)
        self.assertEqual(restored_notification.message, notification.message)
        self.assertEqual(restored_notification.type, notification.type)
        self.assertEqual(restored_notification.is_read, notification.is_read)
        self.assertEqual(restored_notification.id, notification.id)
    
    def test_notification_types(self):
        """Test all notification types."""
        types = [NotificationType.INFO, NotificationType.WARNING, 
                NotificationType.SUCCESS, NotificationType.ERROR]
        
        for notification_type in types:
            notification = Notification(
                title='Test',
                message='Test message',
                type=notification_type
            )
            self.assertEqual(notification.type, notification_type)
    
    def test_notification_with_action_url(self):
        """Test notification with action URL."""
        notification = Notification(
            title='Test',
            message='Test message',
            type=NotificationType.INFO,
            action_url='https://example.com'
        )
        
        self.assertEqual(notification.action_url, 'https://example.com')
    
    def test_notification_validation_invalid_action_url_type(self):
        """Test validation fails with invalid action_url type."""
        with self.assertRaises(ValueError) as context:
            notification = Notification(
                title='Valid title',
                message='Valid message',
                type=NotificationType.INFO,
                action_url=123  # Should be string or None
            )
        self.assertIn('action_url must be a string or None', str(context.exception))


if __name__ == '__main__':
    unittest.main()