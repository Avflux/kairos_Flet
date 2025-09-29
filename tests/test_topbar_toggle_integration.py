import unittest
from unittest.mock import Mock, patch
import flet as ft
from views.components.top_sidebar_container import TopSidebarContainer
from services.time_tracking_service import TimeTrackingService
from services.workflow_service import WorkflowService
from services.notification_service import NotificationService


class TestTopBarToggleIntegration(unittest.TestCase):
    """Integration tests for TopBar toggle functionality across different screen sizes."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_page = Mock(spec=ft.Page)
        self.mock_page.update = Mock()
        self.mock_page.show_snack_bar = Mock()
        
        # Create mock services
        self.mock_time_service = Mock(spec=TimeTrackingService)
        self.mock_workflow_service = Mock(spec=WorkflowService)
        self.mock_notification_service = Mock(spec=NotificationService)
        
        # Set up default service behaviors
        self.mock_time_service.is_tracking.return_value = False
        self.mock_time_service.is_paused.return_value = False
        self.mock_notification_service.get_unread_count.return_value = 0
        self.mock_notification_service.get_notifications.return_value = []
        self.mock_notification_service.add_observer = Mock()
    
    def test_toggle_functionality_desktop(self):
        """Test toggle functionality on desktop screen size."""
        with patch('views.components.top_sidebar_container.FlowchartWidget') as mock_flowchart, \
             patch('views.components.top_sidebar_container.TimeTrackerWidget') as mock_time_tracker, \
             patch('views.components.top_sidebar_container.NotificationCenter') as mock_notifications, \
             patch('views.components.top_sidebar_container.layout_manager') as mock_layout:
            
            # Mock widget instances
            mock_flowchart.return_value = Mock()
            mock_time_tracker.return_value = Mock()
            mock_notifications.return_value = Mock()
            
            # Mock desktop layout
            mock_layout.is_mobile.return_value = False
            mock_layout.is_tablet.return_value = False
            
            container = TopSidebarContainer(
                self.mock_page,
                self.mock_time_service,
                self.mock_workflow_service,
                self.mock_notification_service
            )
            
            # Test initial state (expanded)
            self.assertTrue(container._topbar_expanded)
            self.assertEqual(container.height, 42)  # Desktop expanded height
            
            # Test toggle to collapsed
            container._on_topbar_toggle_click(None)
            self.assertFalse(container._topbar_expanded)
            self.assertEqual(container.height, 32)  # Desktop collapsed height
            
            # Verify feedback message
            self.mock_page.show_snack_bar.assert_called()
            call_args = self.mock_page.show_snack_bar.call_args[0][0]
            self.assertIn("recolhida", call_args.content.value)
            
            # Test toggle back to expanded
            container._on_topbar_toggle_click(None)
            self.assertTrue(container._topbar_expanded)
            self.assertEqual(container.height, 42)  # Back to desktop expanded height
    
    def test_toggle_functionality_mobile(self):
        """Test toggle functionality on mobile screen size."""
        with patch('views.components.top_sidebar_container.FlowchartWidget') as mock_flowchart, \
             patch('views.components.top_sidebar_container.TimeTrackerWidget') as mock_time_tracker, \
             patch('views.components.top_sidebar_container.NotificationCenter') as mock_notifications, \
             patch('views.components.top_sidebar_container.layout_manager') as mock_layout:
            
            # Mock widget instances
            mock_flowchart.return_value = Mock()
            mock_time_tracker.return_value = Mock()
            mock_notifications.return_value = Mock()
            
            # Mock mobile layout
            mock_layout.is_mobile.return_value = True
            mock_layout.is_tablet.return_value = False
            
            container = TopSidebarContainer(
                self.mock_page,
                self.mock_time_service,
                self.mock_workflow_service,
                self.mock_notification_service
            )
            
            # Test initial state (expanded)
            self.assertTrue(container._topbar_expanded)
            self.assertEqual(container.height, 40)  # Mobile expanded height
            
            # Test toggle to collapsed
            container._on_topbar_toggle_click(None)
            self.assertFalse(container._topbar_expanded)
            self.assertEqual(container.height, 28)  # Mobile collapsed height
            
            # Test toggle back to expanded
            container._on_topbar_toggle_click(None)
            self.assertTrue(container._topbar_expanded)
            self.assertEqual(container.height, 40)  # Back to mobile expanded height
    
    def test_toggle_functionality_tablet(self):
        """Test toggle functionality on tablet screen size."""
        with patch('views.components.top_sidebar_container.FlowchartWidget') as mock_flowchart, \
             patch('views.components.top_sidebar_container.TimeTrackerWidget') as mock_time_tracker, \
             patch('views.components.top_sidebar_container.NotificationCenter') as mock_notifications, \
             patch('views.components.top_sidebar_container.layout_manager') as mock_layout:
            
            # Mock widget instances
            mock_flowchart.return_value = Mock()
            mock_time_tracker.return_value = Mock()
            mock_notifications.return_value = Mock()
            
            # Mock tablet layout
            mock_layout.is_mobile.return_value = False
            mock_layout.is_tablet.return_value = True
            
            container = TopSidebarContainer(
                self.mock_page,
                self.mock_time_service,
                self.mock_workflow_service,
                self.mock_notification_service
            )
            
            # Test initial state (expanded)
            self.assertTrue(container._topbar_expanded)
            self.assertEqual(container.height, 41)  # Tablet expanded height
            
            # Test toggle to collapsed
            container._on_topbar_toggle_click(None)
            self.assertFalse(container._topbar_expanded)
            self.assertEqual(container.height, 30)  # Tablet collapsed height
            
            # Test toggle back to expanded
            container._on_topbar_toggle_click(None)
            self.assertTrue(container._topbar_expanded)
            self.assertEqual(container.height, 41)  # Back to tablet expanded height
    
    def test_toggle_button_icon_changes(self):
        """Test that toggle button icon changes correctly."""
        with patch('views.components.top_sidebar_container.FlowchartWidget') as mock_flowchart, \
             patch('views.components.top_sidebar_container.TimeTrackerWidget') as mock_time_tracker, \
             patch('views.components.top_sidebar_container.NotificationCenter') as mock_notifications:
            
            # Mock widget instances
            mock_flowchart.return_value = Mock()
            mock_time_tracker.return_value = Mock()
            mock_notifications.return_value = Mock()
            
            container = TopSidebarContainer(
                self.mock_page,
                self.mock_time_service,
                self.mock_workflow_service,
                self.mock_notification_service
            )
            
            # Test expanded state button
            button = container._create_topbar_toggle_button()
            self.assertEqual(button.icon, ft.Icons.EXPAND_LESS)
            self.assertIn("Recolher", button.tooltip)
            
            # Toggle to collapsed
            container._topbar_expanded = False
            
            # Test collapsed state button
            button = container._create_topbar_toggle_button()
            self.assertEqual(button.icon, ft.Icons.EXPAND_MORE)
            self.assertIn("Expandir", button.tooltip)
    
    def test_smooth_animation_enabled(self):
        """Test that smooth animations are enabled for transitions."""
        with patch('views.components.top_sidebar_container.FlowchartWidget') as mock_flowchart, \
             patch('views.components.top_sidebar_container.TimeTrackerWidget') as mock_time_tracker, \
             patch('views.components.top_sidebar_container.NotificationCenter') as mock_notifications:
            
            # Mock widget instances
            mock_flowchart.return_value = Mock()
            mock_time_tracker.return_value = Mock()
            mock_notifications.return_value = Mock()
            
            container = TopSidebarContainer(
                self.mock_page,
                self.mock_time_service,
                self.mock_workflow_service,
                self.mock_notification_service
            )
            
            # Check that animation is enabled
            self.assertIsNotNone(container.animate)
            self.assertEqual(container.animate.duration, 300)
            self.assertEqual(container.animate.curve, "ease")


if __name__ == '__main__':
    unittest.main()