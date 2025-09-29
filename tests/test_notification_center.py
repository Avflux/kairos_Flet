import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import flet as ft
from views.components.notification_center import NotificationCenter
from services.notification_service import NotificationService
from models.notification import NotificationType


class TestNotificationCenter(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.page_mock = Mock(spec=ft.Page)
        self.notification_service = NotificationService()
        
        # Mock the page.update method
        self.page_mock.update = Mock()
    
    def test_notification_center_initialization(self):
        """Test that the notification center initializes correctly."""
        center = NotificationCenter(self.page_mock, self.notification_service)
        
        # Check that the service is set
        self.assertEqual(center.notification_service, self.notification_service)
        self.assertEqual(center.page, self.page_mock)
        self.assertFalse(center.is_expanded)
        
        # Check that it's registered as an observer
        self.assertIn(center._on_new_notification, self.notification_service._observers)
    
    def test_badge_visibility_with_no_notifications(self):
        """Test that badge is hidden when there are no notifications."""
        center = NotificationCenter(self.page_mock, self.notification_service)
        
        # Badge should be hidden initially
        self.assertFalse(center.badge.visible)
        self.assertEqual(center.notification_icon.icon_color, ft.Colors.GREY_600)
    
    def test_badge_visibility_with_notifications(self):
        """Test that badge shows when there are unread notifications."""
        center = NotificationCenter(self.page_mock, self.notification_service)
        
        # Add a notification
        self.notification_service.add_notification("Test", "Message")
        
        # Badge should be visible
        self.assertTrue(center.badge.visible)
        self.assertEqual(center.badge.content.value, "1")
        self.assertEqual(center.notification_icon.icon_color, ft.Colors.BLUE_600)
    
    def test_badge_count_multiple_notifications(self):
        """Test badge count with multiple notifications."""
        center = NotificationCenter(self.page_mock, self.notification_service)
        
        # Add multiple notifications
        for i in range(5):
            self.notification_service.add_notification(f"Test {i}", f"Message {i}")
        
        # Badge should show count
        self.assertTrue(center.badge.visible)
        self.assertEqual(center.badge.content.value, "5")
    
    def test_badge_count_cap_at_99(self):
        """Test that badge count caps at 99."""
        center = NotificationCenter(self.page_mock, self.notification_service)
        
        # Add more than 99 notifications
        for i in range(105):
            self.notification_service.add_notification(f"Test {i}", f"Message {i}")
        
        # Badge should cap at 99
        self.assertTrue(center.badge.visible)
        self.assertEqual(center.badge.content.value, "99")
    
    def test_badge_updates_when_marked_as_read(self):
        """Test that badge updates when notifications are marked as read."""
        center = NotificationCenter(self.page_mock, self.notification_service)
        
        # Add notifications
        n1 = self.notification_service.add_notification("Test 1", "Message 1")
        n2 = self.notification_service.add_notification("Test 2", "Message 2")
        
        # Should show 2
        self.assertEqual(center.badge.content.value, "2")
        
        # Mark one as read
        self.notification_service.mark_as_read(n1.id)
        center._update_display()
        
        # Should show 1
        self.assertEqual(center.badge.content.value, "1")
        
        # Mark all as read
        self.notification_service.mark_as_read(n2.id)
        center._update_display()
        
        # Badge should be hidden
        self.assertFalse(center.badge.visible)
    
    def test_panel_toggle(self):
        """Test panel visibility toggle."""
        center = NotificationCenter(self.page_mock, self.notification_service)
        
        # Panel should be hidden initially
        self.assertFalse(center.notification_panel.visible)
        self.assertFalse(center.is_expanded)
        
        # Simulate click to toggle
        center._toggle_panel(None)
        
        # Panel should be visible
        self.assertTrue(center.notification_panel.visible)
        self.assertTrue(center.is_expanded)
        
        # Toggle again
        center._toggle_panel(None)
        
        # Panel should be hidden
        self.assertFalse(center.notification_panel.visible)
        self.assertFalse(center.is_expanded)
    
    def test_notification_item_creation(self):
        """Test creating notification items."""
        center = NotificationCenter(self.page_mock, self.notification_service)
        
        # Create a test notification
        notification = self.notification_service.add_notification(
            "Test Title",
            "Test Message",
            NotificationType.WARNING
        )
        
        # Create notification item
        item = center._create_notification_item(notification)
        
        # Check that it's a container
        self.assertIsInstance(item, ft.Container)
        
        # Check that it has the expected structure
        self.assertIsNotNone(item.content)
        self.assertIsInstance(item.content, ft.Row)
    
    def test_mark_all_as_read_functionality(self):
        """Test mark all as read functionality."""
        center = NotificationCenter(self.page_mock, self.notification_service)
        
        # Add multiple notifications
        self.notification_service.add_notification("Test 1", "Message 1")
        self.notification_service.add_notification("Test 2", "Message 2")
        self.notification_service.add_notification("Test 3", "Message 3")
        
        # All should be unread
        self.assertEqual(self.notification_service.get_unread_count(), 3)
        
        # Mark all as read
        center._mark_all_as_read(None)
        
        # All should be read
        self.assertEqual(self.notification_service.get_unread_count(), 0)
    
    def test_clear_all_notifications_functionality(self):
        """Test clear all notifications functionality."""
        center = NotificationCenter(self.page_mock, self.notification_service)
        
        # Add multiple notifications
        self.notification_service.add_notification("Test 1", "Message 1")
        self.notification_service.add_notification("Test 2", "Message 2")
        
        # Should have notifications
        self.assertEqual(len(self.notification_service.get_notifications()), 2)
        
        # Clear all
        center._clear_all_notifications(None)
        
        # Should have no notifications
        self.assertEqual(len(self.notification_service.get_notifications()), 0)
    
    def test_add_test_notification(self):
        """Test adding test notifications."""
        center = NotificationCenter(self.page_mock, self.notification_service)
        
        # Add test notifications of different types
        center.add_test_notification(NotificationType.INFO)
        center.add_test_notification(NotificationType.SUCCESS)
        center.add_test_notification(NotificationType.WARNING)
        center.add_test_notification(NotificationType.ERROR)
        
        # Should have 4 notifications
        notifications = self.notification_service.get_notifications()
        self.assertEqual(len(notifications), 4)
        
        # Check that different types were created
        types = [n.type for n in notifications]
        self.assertIn(NotificationType.INFO, types)
        self.assertIn(NotificationType.SUCCESS, types)
        self.assertIn(NotificationType.WARNING, types)
        self.assertIn(NotificationType.ERROR, types)
    
    def test_observer_callback(self):
        """Test that the observer callback works correctly."""
        center = NotificationCenter(self.page_mock, self.notification_service)
        
        # Mock the update display method
        center._update_display = Mock()
        
        # Add a notification (should trigger observer)
        notification = self.notification_service.add_notification("Test", "Message")
        
        # Update display should have been called
        center._update_display.assert_called()
    
    def test_category_filtering(self):
        """Test notification filtering by category."""
        center = NotificationCenter(self.page_mock, self.notification_service)
        
        # Add notifications of different types
        self.notification_service.add_notification("Info", "Info message", NotificationType.INFO)
        self.notification_service.add_notification("Success", "Success message", NotificationType.SUCCESS)
        self.notification_service.add_notification("Warning", "Warning message", NotificationType.WARNING)
        self.notification_service.add_notification("Error", "Error message", NotificationType.ERROR)
        
        # Test filtering by INFO
        info_notifications = center.get_notifications_by_category(NotificationType.INFO)
        self.assertEqual(len(info_notifications), 1)
        self.assertEqual(info_notifications[0].type, NotificationType.INFO)
        
        # Test filtering by SUCCESS
        success_notifications = center.get_notifications_by_category(NotificationType.SUCCESS)
        self.assertEqual(len(success_notifications), 1)
        self.assertEqual(success_notifications[0].type, NotificationType.SUCCESS)
    
    def test_unread_notifications_by_category(self):
        """Test getting unread notifications by category."""
        center = NotificationCenter(self.page_mock, self.notification_service)
        
        # Add notifications and mark some as read
        n1 = self.notification_service.add_notification("Info 1", "Message", NotificationType.INFO)
        n2 = self.notification_service.add_notification("Info 2", "Message", NotificationType.INFO)
        n3 = self.notification_service.add_notification("Success", "Message", NotificationType.SUCCESS)
        
        # Mark one info notification as read
        self.notification_service.mark_as_read(n1.id)
        
        # Get unread info notifications
        unread_info = center.get_unread_notifications_by_category(NotificationType.INFO)
        self.assertEqual(len(unread_info), 1)
        self.assertEqual(unread_info[0].id, n2.id)
        
        # Get unread success notifications
        unread_success = center.get_unread_notifications_by_category(NotificationType.SUCCESS)
        self.assertEqual(len(unread_success), 1)
        self.assertEqual(unread_success[0].id, n3.id)
    
    def test_timestamp_formatting(self):
        """Test timestamp formatting functionality."""
        center = NotificationCenter(self.page_mock, self.notification_service)
        
        now = datetime.now()
        
        # Test "Just now" (less than 1 minute)
        recent_time = now - timedelta(seconds=30)
        self.assertEqual(center._format_timestamp(recent_time), "Just now")
        
        # Test minutes ago
        minutes_ago = now - timedelta(minutes=5)
        self.assertEqual(center._format_timestamp(minutes_ago), "5m ago")
        
        # Test today (same day, more than 1 hour ago)
        today_time = now - timedelta(hours=2)
        expected = today_time.strftime("%H:%M")
        self.assertEqual(center._format_timestamp(today_time), expected)
        
        # Test yesterday
        yesterday_time = now - timedelta(days=1)
        expected = f"Yesterday {yesterday_time.strftime('%H:%M')}"
        self.assertEqual(center._format_timestamp(yesterday_time), expected)
    
    def test_notification_grouping_by_date(self):
        """Test grouping notifications by date."""
        center = NotificationCenter(self.page_mock, self.notification_service)
        
        now = datetime.now()
        
        # Create notifications with different timestamps
        notifications = []
        
        # Today
        today_notification = self.notification_service.add_notification("Today", "Message")
        today_notification.timestamp = now
        notifications.append(today_notification)
        
        # Yesterday
        yesterday_notification = self.notification_service.add_notification("Yesterday", "Message")
        yesterday_notification.timestamp = now - timedelta(days=1)
        notifications.append(yesterday_notification)
        
        # Last week
        week_ago_notification = self.notification_service.add_notification("Week ago", "Message")
        week_ago_notification.timestamp = now - timedelta(days=8)
        notifications.append(week_ago_notification)
        
        # Group notifications
        grouped = center._group_notifications_by_date(notifications)
        
        # Should have different date groups
        self.assertIn("Today", grouped)
        self.assertIn("Yesterday", grouped)
        self.assertEqual(len(grouped["Today"]), 1)
        self.assertEqual(len(grouped["Yesterday"]), 1)
    
    def test_toggle_read_status(self):
        """Test toggling notification read status."""
        center = NotificationCenter(self.page_mock, self.notification_service)
        
        # Add a notification
        notification = self.notification_service.add_notification("Test", "Message")
        
        # Should be unread initially
        self.assertFalse(notification.is_read)
        
        # Toggle to read
        center._toggle_read_status(notification.id)
        updated_notification = self.notification_service.get_notification_by_id(notification.id)
        self.assertTrue(updated_notification.is_read)
        
        # Toggle back to unread
        center._toggle_read_status(notification.id)
        updated_notification = self.notification_service.get_notification_by_id(notification.id)
        self.assertFalse(updated_notification.is_read)
    
    def test_enhanced_visual_indicators(self):
        """Test enhanced visual indicators for notifications."""
        center = NotificationCenter(self.page_mock, self.notification_service)
        
        # Add notifications to trigger badge updates
        self.notification_service.add_notification("Test 1", "Message")
        self.notification_service.add_notification("Test 2", "Message")
        
        # Badge should be visible with count
        self.assertTrue(center.badge.visible)
        self.assertEqual(center.badge.content.value, "2")
        self.assertEqual(center.notification_icon.icon_color, ft.Colors.BLUE_600)
        
        # Mark all as read
        center._mark_all_as_read(None)
        
        # Badge should be hidden
        self.assertFalse(center.badge.visible)
        self.assertEqual(center.notification_icon.icon_color, ft.Colors.GREY_600)
    
    def test_clear_read_notifications(self):
        """Test clearing only read notifications."""
        center = NotificationCenter(self.page_mock, self.notification_service)
        
        # Add notifications and mark some as read
        n1 = self.notification_service.add_notification("Test 1", "Message")
        n2 = self.notification_service.add_notification("Test 2", "Message")
        n3 = self.notification_service.add_notification("Test 3", "Message")
        
        # Mark two as read
        self.notification_service.mark_as_read(n1.id)
        self.notification_service.mark_as_read(n2.id)
        
        # Should have 3 total, 1 unread
        self.assertEqual(len(self.notification_service.get_notifications()), 3)
        self.assertEqual(self.notification_service.get_unread_count(), 1)
        
        # Clear read notifications
        center._clear_read_notifications(None)
        
        # Should have 1 total (the unread one)
        remaining_notifications = self.notification_service.get_notifications()
        self.assertEqual(len(remaining_notifications), 1)
        self.assertEqual(remaining_notifications[0].id, n3.id)
        self.assertFalse(remaining_notifications[0].is_read)
    
    def test_category_change_handler(self):
        """Test category filter change handling."""
        center = NotificationCenter(self.page_mock, self.notification_service)
        
        # Mock the event object
        mock_event = Mock()
        mock_event.control.selected_index = 1  # INFO tab
        
        # Initially no filter
        self.assertIsNone(center.current_filter)
        
        # Change to INFO filter
        center._on_category_change(mock_event)
        self.assertEqual(center.current_filter, NotificationType.INFO)
        
        # Change to ALL filter
        mock_event.control.selected_index = 0
        center._on_category_change(mock_event)
        self.assertIsNone(center.current_filter)


if __name__ == '__main__':
    unittest.main()