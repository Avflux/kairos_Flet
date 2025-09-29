import unittest
from unittest.mock import Mock, patch
import flet as ft
from views.components.top_sidebar_container import TopSidebarContainer
from services.time_tracking_service import TimeTrackingService
from services.workflow_service import WorkflowService
from services.notification_service import NotificationService


class TestOptimizedHeights(unittest.TestCase):
    """Test optimized heights for different devices in TopBar."""
    
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
    
    def test_mobile_optimized_heights(self):
        """Test that mobile devices get optimized heights (40px/28px)."""
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
            
            # Test optimized heights method directly
            altura_expandida, altura_recolhida = container._get_optimized_heights()
            self.assertEqual(altura_expandida, 40, "Mobile expanded height should be 40px")
            self.assertEqual(altura_recolhida, 28, "Mobile collapsed height should be 28px")
            
            # Test that container uses these heights
            self.assertEqual(container.height, 40, "Container should use mobile expanded height")
            
            # Test collapsed state
            container._topbar_expanded = False
            container._build_layout()
            self.assertEqual(container.height, 28, "Container should use mobile collapsed height")
    
    def test_tablet_optimized_heights(self):
        """Test that tablet devices get optimized heights (41px/30px)."""
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
            
            # Test optimized heights method directly
            altura_expandida, altura_recolhida = container._get_optimized_heights()
            self.assertEqual(altura_expandida, 41, "Tablet expanded height should be 41px")
            self.assertEqual(altura_recolhida, 30, "Tablet collapsed height should be 30px")
            
            # Test that container uses these heights
            self.assertEqual(container.height, 41, "Container should use tablet expanded height")
            
            # Test collapsed state
            container._topbar_expanded = False
            container._build_layout()
            self.assertEqual(container.height, 30, "Container should use tablet collapsed height")
    
    def test_desktop_optimized_heights(self):
        """Test that desktop devices get optimized heights (42px/32px)."""
        with patch('views.components.top_sidebar_container.FlowchartWidget') as mock_flowchart, \
             patch('views.components.top_sidebar_container.TimeTrackerWidget') as mock_time_tracker, \
             patch('views.components.top_sidebar_container.NotificationCenter') as mock_notifications, \
             patch('views.components.top_sidebar_container.layout_manager') as mock_layout:
            
            # Mock widget instances
            mock_flowchart.return_value = Mock()
            mock_time_tracker.return_value = Mock()
            mock_notifications.return_value = Mock()
            
            # Mock desktop layout (neither mobile nor tablet)
            mock_layout.is_mobile.return_value = False
            mock_layout.is_tablet.return_value = False
            
            container = TopSidebarContainer(
                self.mock_page,
                self.mock_time_service,
                self.mock_workflow_service,
                self.mock_notification_service
            )
            
            # Test optimized heights method directly
            altura_expandida, altura_recolhida = container._get_optimized_heights()
            self.assertEqual(altura_expandida, 42, "Desktop expanded height should be 42px")
            self.assertEqual(altura_recolhida, 32, "Desktop collapsed height should be 32px")
            
            # Test that container uses these heights
            self.assertEqual(container.height, 42, "Container should use desktop expanded height")
            
            # Test collapsed state
            container._topbar_expanded = False
            container._build_layout()
            self.assertEqual(container.height, 32, "Container should use desktop collapsed height")
    
    def test_minimal_padding_applied(self):
        """Test that minimal padding (2px vertical) is applied correctly."""
        with patch('views.components.top_sidebar_container.FlowchartWidget') as mock_flowchart, \
             patch('views.components.top_sidebar_container.TimeTrackerWidget') as mock_time_tracker, \
             patch('views.components.top_sidebar_container.NotificationCenter') as mock_notifications, \
             patch('views.components.top_sidebar_container.layout_manager') as mock_layout:
            
            # Mock widget instances
            mock_flowchart.return_value = Mock()
            mock_time_tracker.return_value = Mock()
            mock_notifications.return_value = Mock()
            
            # Test mobile padding
            mock_layout.is_mobile.return_value = True
            mock_layout.is_tablet.return_value = False
            
            container = TopSidebarContainer(
                self.mock_page,
                self.mock_time_service,
                self.mock_workflow_service,
                self.mock_notification_service
            )
            
            # Check mobile padding (expanded state)
            expected_mobile_padding = ft.padding.symmetric(horizontal=8, vertical=2)
            self.assertEqual(container.padding.top, 2, "Mobile vertical padding should be 2px")
            self.assertEqual(container.padding.bottom, 2, "Mobile vertical padding should be 2px")
            
            # Test desktop padding
            mock_layout.is_mobile.return_value = False
            mock_layout.is_tablet.return_value = False
            container._build_layout()
            
            # Check desktop padding (expanded state)
            self.assertEqual(container.padding.top, 2, "Desktop vertical padding should be 2px")
            self.assertEqual(container.padding.bottom, 2, "Desktop vertical padding should be 2px")
            
            # Test collapsed state (zero padding)
            container._topbar_expanded = False
            container._build_layout()
            self.assertEqual(container.padding.top, 0, "Collapsed state should have zero padding")
            self.assertEqual(container.padding.bottom, 0, "Collapsed state should have zero padding")
    
    def test_smooth_animation_configuration(self):
        """Test that smooth animations are configured with 300ms duration."""
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
            
            # Check animation configuration
            self.assertIsNotNone(container.animate, "Animation should be configured")
            self.assertEqual(container.animate.duration, 300, "Animation duration should be 300ms")
            self.assertEqual(container.animate.curve, "ease", "Animation curve should be 'ease'")
            
            # Test collapsed layout animation
            collapsed_layout = container._create_collapsed_topbar_layout()
            self.assertIsNotNone(collapsed_layout.animate, "Collapsed layout should have animation")
            self.assertEqual(collapsed_layout.animate.duration, 300, "Collapsed animation duration should be 300ms")
            self.assertEqual(collapsed_layout.animate.curve, "ease", "Collapsed animation curve should be 'ease'")
    
    def test_space_liberation_verification(self):
        """Test that additional space is properly liberated when TopBar is collapsed."""
        with patch('views.components.top_sidebar_container.FlowchartWidget') as mock_flowchart, \
             patch('views.components.top_sidebar_container.TimeTrackerWidget') as mock_time_tracker, \
             patch('views.components.top_sidebar_container.NotificationCenter') as mock_notifications, \
             patch('views.components.top_sidebar_container.layout_manager') as mock_layout:
            
            # Mock widget instances
            mock_flowchart.return_value = Mock()
            mock_time_tracker.return_value = Mock()
            mock_notifications.return_value = Mock()
            
            # Test space liberation for each device type
            device_configs = [
                {'is_mobile': True, 'is_tablet': False, 'expanded': 40, 'collapsed': 28, 'space_saved': 12},
                {'is_mobile': False, 'is_tablet': True, 'expanded': 41, 'collapsed': 30, 'space_saved': 11},
                {'is_mobile': False, 'is_tablet': False, 'expanded': 42, 'collapsed': 32, 'space_saved': 10}
            ]
            
            for config in device_configs:
                mock_layout.is_mobile.return_value = config['is_mobile']
                mock_layout.is_tablet.return_value = config['is_tablet']
                
                container = TopSidebarContainer(
                    self.mock_page,
                    self.mock_time_service,
                    self.mock_workflow_service,
                    self.mock_notification_service
                )
                
                # Test expanded state
                expanded_height = container.height
                self.assertEqual(expanded_height, config['expanded'])
                
                # Test collapsed state
                container._topbar_expanded = False
                container._build_layout()
                collapsed_height = container.height
                self.assertEqual(collapsed_height, config['collapsed'])
                
                # Verify space saved
                space_saved = expanded_height - collapsed_height
                self.assertEqual(space_saved, config['space_saved'], 
                               f"Should save {config['space_saved']}px of space when collapsed")


if __name__ == '__main__':
    unittest.main()