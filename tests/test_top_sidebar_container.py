import unittest
from unittest.mock import Mock, MagicMock, patch
import flet as ft
from views.components.top_sidebar_container import TopSidebarContainer
from services.time_tracking_service import TimeTrackingService
from services.workflow_service import WorkflowService
from services.notification_service import NotificationService
from models.notification import NotificationType


class TestTopSidebarContainer(unittest.TestCase):
    """Test cases for TopSidebarContainer component integration and layout responsiveness."""
    
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
    
    def test_container_initialization(self):
        """Test that the container initializes correctly with all components."""
        container = TopSidebarContainer(
            self.mock_page,
            self.mock_time_service,
            self.mock_workflow_service,
            self.mock_notification_service
        )
        
        # Verify container properties
        self.assertEqual(container.page, self.mock_page)
        self.assertTrue(container.sidebar_expanded)
        self.assertEqual(container.height, 60)
        self.assertIsNotNone(container.content)
        
        # Verify components are initialized
        self.assertIsNotNone(container.time_tracker)
        self.assertIsNotNone(container.flowchart)
        self.assertIsNotNone(container.notifications)
        
        # Verify services are assigned
        self.assertEqual(container.time_tracking_service, self.mock_time_service)
        self.assertEqual(container.workflow_service, self.mock_workflow_service)
        self.assertEqual(container.notification_service, self.mock_notification_service)
    
    def test_container_initialization_with_default_services(self):
        """Test that the container initializes with default services when none provided."""
        with patch('views.components.top_sidebar_container.TimeTrackingService') as mock_time_cls, \
             patch('views.components.top_sidebar_container.WorkflowService') as mock_workflow_cls, \
             patch('views.components.top_sidebar_container.NotificationService') as mock_notification_cls:
            
            # Set up mock service instances
            mock_time_instance = Mock()
            mock_workflow_instance = Mock()
            mock_notification_instance = Mock()
            
            mock_time_cls.return_value = mock_time_instance
            mock_workflow_cls.return_value = mock_workflow_instance
            mock_notification_cls.return_value = mock_notification_instance
            
            # Set up notification service mock
            mock_notification_instance.get_unread_count.return_value = 0
            mock_notification_instance.get_notifications.return_value = []
            mock_notification_instance.add_observer = Mock()
            
            container = TopSidebarContainer(self.mock_page)
            
            # Verify default services are created
            mock_time_cls.assert_called_once()
            mock_workflow_cls.assert_called_once()
            mock_notification_cls.assert_called_once()
            
            self.assertEqual(container.time_tracking_service, mock_time_instance)
            self.assertEqual(container.workflow_service, mock_workflow_instance)
            self.assertEqual(container.notification_service, mock_notification_instance)
    
    def test_expanded_layout_structure(self):
        """Test that expanded layout contains all components with correct structure."""
        container = TopSidebarContainer(
            self.mock_page,
            self.mock_time_service,
            self.mock_workflow_service,
            self.mock_notification_service
        )
        
        # Verify expanded layout (default state)
        self.assertTrue(container.sidebar_expanded)
        
        # Check that content is a Row
        self.assertIsInstance(container.content, ft.Row)
        
        # Verify three main containers in the row
        row_controls = container.content.controls
        self.assertEqual(len(row_controls), 3)
        
        # Verify each container has the expected content type
        time_container = row_controls[0]
        flowchart_container = row_controls[1]
        notification_container = row_controls[2]
        
        self.assertIsInstance(time_container, ft.Container)
        self.assertIsInstance(flowchart_container, ft.Container)
        self.assertIsInstance(notification_container, ft.Container)
        
        # Verify expand properties
        self.assertEqual(time_container.expand, 1)
        self.assertEqual(flowchart_container.expand, 2)
        self.assertEqual(notification_container.width, 60)
    
    def test_collapsed_layout_structure(self):
        """Test that collapsed layout shows compact versions of components."""
        container = TopSidebarContainer(
            self.mock_page,
            self.mock_time_service,
            self.mock_workflow_service,
            self.mock_notification_service
        )
        
        # Switch to collapsed layout
        container.update_layout(False)
        
        # Verify collapsed state
        self.assertFalse(container.sidebar_expanded)
        
        # Check that content is still a Row
        self.assertIsInstance(container.content, ft.Row)
        
        # Verify three compact containers in the row
        row_controls = container.content.controls
        self.assertEqual(len(row_controls), 3)
        
        # Verify compact layout properties
        compact_timer = row_controls[0]
        compact_flowchart = row_controls[1]
        notification_container = row_controls[2]
        
        self.assertEqual(compact_timer.width, 40)
        self.assertEqual(compact_flowchart.expand, 1)
        self.assertEqual(notification_container.width, 40)
    
    def test_layout_update_triggers_rebuild(self):
        """Test that updating layout triggers a rebuild and page update."""
        container = TopSidebarContainer(
            self.mock_page,
            self.mock_time_service,
            self.mock_workflow_service,
            self.mock_notification_service
        )
        
        # Store initial content reference
        initial_content = container.content
        
        # Update layout to collapsed
        container.update_layout(False)
        
        # Verify state changed
        self.assertFalse(container.sidebar_expanded)
        
        # Verify page update was called
        self.mock_page.update.assert_called()
        
        # Update back to expanded
        self.mock_page.update.reset_mock()
        container.update_layout(True)
        
        # Verify state changed back
        self.assertTrue(container.sidebar_expanded)
        self.mock_page.update.assert_called()
    
    def test_layout_update_no_change_skips_rebuild(self):
        """Test that updating layout with same state doesn't trigger rebuild."""
        container = TopSidebarContainer(
            self.mock_page,
            self.mock_time_service,
            self.mock_workflow_service,
            self.mock_notification_service
        )
        
        # Reset mock to clear initialization calls
        self.mock_page.update.reset_mock()
        
        # Update layout to same state (expanded)
        container.update_layout(True)
        
        # Verify no page update was called
        self.mock_page.update.assert_not_called()
    
    def test_refresh_components_calls_all_refresh_methods(self):
        """Test that refresh_components calls refresh on all child components."""
        container = TopSidebarContainer(
            self.mock_page,
            self.mock_time_service,
            self.mock_workflow_service,
            self.mock_notification_service
        )
        
        # Mock refresh methods on components
        container.time_tracker.refresh = Mock()
        container.flowchart._refresh_display = Mock()
        container.notifications._update_display = Mock()
        
        # Call refresh
        container.refresh_components()
        
        # Verify all refresh methods were called
        container.time_tracker.refresh.assert_called_once()
        container.flowchart._refresh_display.assert_called_once()
        container.notifications._update_display.assert_called_once()
        
        # Verify page update was called
        self.mock_page.update.assert_called()
    
    def test_compact_timer_click_shows_message(self):
        """Test that clicking compact timer shows appropriate message."""
        container = TopSidebarContainer(
            self.mock_page,
            self.mock_time_service,
            self.mock_workflow_service,
            self.mock_notification_service
        )
        
        # Switch to collapsed layout to enable compact timer
        container.update_layout(False)
        
        # Simulate compact timer click
        container._on_compact_timer_click(None)
        
        # Verify snack bar was shown
        self.mock_page.show_snack_bar.assert_called_once()
        
        # Verify message content
        call_args = self.mock_page.show_snack_bar.call_args[0][0]
        self.assertIsInstance(call_args, ft.SnackBar)
        self.assertIn("Expand sidebar", call_args.content.value)
    
    def test_compact_flowchart_click_shows_message(self):
        """Test that clicking compact flowchart shows appropriate message."""
        container = TopSidebarContainer(
            self.mock_page,
            self.mock_time_service,
            self.mock_workflow_service,
            self.mock_notification_service
        )
        
        # Switch to collapsed layout to enable compact flowchart
        container.update_layout(False)
        
        # Simulate compact flowchart click
        container._on_compact_flowchart_click(None)
        
        # Verify snack bar was shown
        self.mock_page.show_snack_bar.assert_called_once()
        
        # Verify message content
        call_args = self.mock_page.show_snack_bar.call_args[0][0]
        self.assertIsInstance(call_args, ft.SnackBar)
        self.assertIn("Expand sidebar", call_args.content.value)
    
    def test_component_getters_return_correct_instances(self):
        """Test that component getter methods return correct instances."""
        container = TopSidebarContainer(
            self.mock_page,
            self.mock_time_service,
            self.mock_workflow_service,
            self.mock_notification_service
        )
        
        # Test getters
        self.assertEqual(container.get_time_tracker(), container.time_tracker)
        self.assertEqual(container.get_flowchart(), container.flowchart)
        self.assertEqual(container.get_notifications(), container.notifications)
    
    def test_add_test_notification_delegates_to_notification_center(self):
        """Test that add_test_notification delegates to notification center."""
        container = TopSidebarContainer(
            self.mock_page,
            self.mock_time_service,
            self.mock_workflow_service,
            self.mock_notification_service
        )
        
        # Mock the notification center method
        container.notifications.add_test_notification = Mock()
        
        # Call the container method
        container.add_test_notification()
        
        # Verify delegation
        container.notifications.add_test_notification.assert_called_once()
    
    def test_workflow_methods_delegate_to_flowchart(self):
        """Test that workflow methods delegate to flowchart widget."""
        container = TopSidebarContainer(
            self.mock_page,
            self.mock_time_service,
            self.mock_workflow_service,
            self.mock_notification_service
        )
        
        # Mock flowchart methods
        container.flowchart.advance_to_stage = Mock(return_value=True)
        container.flowchart.complete_current_stage = Mock(return_value=True)
        
        # Test advance_workflow_stage
        result = container.advance_workflow_stage("test_stage")
        self.assertTrue(result)
        container.flowchart.advance_to_stage.assert_called_once_with("test_stage")
        
        # Test complete_current_workflow_stage
        result = container.complete_current_workflow_stage()
        self.assertTrue(result)
        container.flowchart.complete_current_stage.assert_called_once()
    
    def test_container_styling_properties(self):
        """Test that container has correct styling properties applied."""
        container = TopSidebarContainer(
            self.mock_page,
            self.mock_time_service,
            self.mock_workflow_service,
            self.mock_notification_service
        )
        
        # Verify styling properties
        self.assertEqual(container.height, 60)
        self.assertEqual(container.bgcolor, 'surface_variant')
        self.assertIsNotNone(container.border_radius)
        self.assertIsNotNone(container.padding)
        self.assertIsNotNone(container.border)
        self.assertIsNotNone(container.shadow)
        self.assertIsNotNone(container.animate)
    
    def test_responsive_layout_adaptation(self):
        """Test that layout adapts correctly to different sidebar states."""
        container = TopSidebarContainer(
            self.mock_page,
            self.mock_time_service,
            self.mock_workflow_service,
            self.mock_notification_service
        )
        
        # Test expanded layout properties
        self.assertTrue(container.sidebar_expanded)
        expanded_controls = container.content.controls
        self.assertEqual(len(expanded_controls), 3)
        
        # Verify expanded layout spacing and alignment
        self.assertEqual(container.content.spacing, 0)
        self.assertEqual(container.content.alignment, ft.MainAxisAlignment.SPACE_BETWEEN)
        self.assertEqual(container.content.vertical_alignment, ft.CrossAxisAlignment.CENTER)
        
        # Switch to collapsed layout
        container.update_layout(False)
        
        # Test collapsed layout properties
        self.assertFalse(container.sidebar_expanded)
        collapsed_controls = container.content.controls
        self.assertEqual(len(collapsed_controls), 3)
        
        # Verify collapsed layout spacing
        self.assertEqual(container.content.spacing, 4)
    
    def test_topbar_toggle_functionality(self):
        """Test TopBar toggle functionality and state management."""
        with patch('views.components.top_sidebar_container.FlowchartWidget') as mock_flowchart, \
             patch('views.components.top_sidebar_container.TimeTrackerWidget') as mock_time_tracker, \
             patch('views.components.top_sidebar_container.NotificationCenter') as mock_notifications:
            
            # Mock the widget instances
            mock_flowchart_instance = Mock()
            mock_time_tracker_instance = Mock()
            mock_notifications_instance = Mock()
            
            mock_flowchart.return_value = mock_flowchart_instance
            mock_time_tracker.return_value = mock_time_tracker_instance
            mock_notifications.return_value = mock_notifications_instance
            
            container = TopSidebarContainer(
                self.mock_page,
                self.mock_time_service,
                self.mock_workflow_service,
                self.mock_notification_service
            )
        
        # Initial state should be expanded
        self.assertTrue(container._topbar_expanded)
        
        # Test toggle to collapsed
        container._on_topbar_toggle_click(None)
        self.assertFalse(container._topbar_expanded)
        
        # Verify page update was called
        self.mock_page.update.assert_called()
        
        # Verify feedback message was shown
        self.mock_page.show_snack_bar.assert_called()
        
        # Test toggle back to expanded
        container._on_topbar_toggle_click(None)
        self.assertTrue(container._topbar_expanded)
    
    def test_get_optimized_heights(self):
        """Test optimized heights for different device types."""
        with patch('views.components.top_sidebar_container.FlowchartWidget') as mock_flowchart, \
             patch('views.components.top_sidebar_container.TimeTrackerWidget') as mock_time_tracker, \
             patch('views.components.top_sidebar_container.NotificationCenter') as mock_notifications:
            
            mock_flowchart.return_value = Mock()
            mock_time_tracker.return_value = Mock()
            mock_notifications.return_value = Mock()
            
            container = TopSidebarContainer(
                self.mock_page,
                self.mock_time_service,
                self.mock_workflow_service,
                self.mock_notification_service
            )
        
        # Mock layout_manager for different device types
        with patch('views.components.top_sidebar_container.layout_manager') as mock_layout:
            # Test mobile heights
            mock_layout.is_mobile.return_value = True
            mock_layout.is_tablet.return_value = False
            altura_expandida, altura_recolhida = container._get_optimized_heights()
            self.assertEqual(altura_expandida, 40)
            self.assertEqual(altura_recolhida, 28)
            
            # Test tablet heights
            mock_layout.is_mobile.return_value = False
            mock_layout.is_tablet.return_value = True
            altura_expandida, altura_recolhida = container._get_optimized_heights()
            self.assertEqual(altura_expandida, 41)
            self.assertEqual(altura_recolhida, 30)
            
            # Test desktop heights
            mock_layout.is_mobile.return_value = False
            mock_layout.is_tablet.return_value = False
            altura_expandida, altura_recolhida = container._get_optimized_heights()
            self.assertEqual(altura_expandida, 42)
            self.assertEqual(altura_recolhida, 32)
    
    def test_build_layout_with_optimized_heights(self):
        """Test that _build_layout applies optimized heights correctly."""
        with patch('views.components.top_sidebar_container.FlowchartWidget') as mock_flowchart, \
             patch('views.components.top_sidebar_container.TimeTrackerWidget') as mock_time_tracker, \
             patch('views.components.top_sidebar_container.NotificationCenter') as mock_notifications:
            
            mock_flowchart.return_value = Mock()
            mock_time_tracker.return_value = Mock()
            mock_notifications.return_value = Mock()
            
            container = TopSidebarContainer(
                self.mock_page,
                self.mock_time_service,
                self.mock_workflow_service,
                self.mock_notification_service
            )
        
        with patch('views.components.top_sidebar_container.layout_manager') as mock_layout:
            # Test expanded state on desktop
            mock_layout.is_mobile.return_value = False
            mock_layout.is_tablet.return_value = False
            container._topbar_expanded = True
            container._build_layout()
            self.assertEqual(container.height, 42)
            
            # Test collapsed state on desktop
            container._topbar_expanded = False
            container._build_layout()
            self.assertEqual(container.height, 32)
            
            # Test expanded state on mobile
            mock_layout.is_mobile.return_value = True
            mock_layout.is_tablet.return_value = False
            container._topbar_expanded = True
            container._build_layout()
            self.assertEqual(container.height, 40)
            
            # Test collapsed state on mobile
            container._topbar_expanded = False
            container._build_layout()
            self.assertEqual(container.height, 28)
    
    def test_toggle_topbar_expansion_method(self):
        """Test the toggle_topbar_expansion method."""
        with patch('views.components.top_sidebar_container.FlowchartWidget') as mock_flowchart, \
             patch('views.components.top_sidebar_container.TimeTrackerWidget') as mock_time_tracker, \
             patch('views.components.top_sidebar_container.NotificationCenter') as mock_notifications:
            
            mock_flowchart.return_value = Mock()
            mock_time_tracker.return_value = Mock()
            mock_notifications.return_value = Mock()
            
            container = TopSidebarContainer(
                self.mock_page,
                self.mock_time_service,
                self.mock_workflow_service,
                self.mock_notification_service
            )
        
        # Initial state should be expanded
        self.assertTrue(container._topbar_expanded)
        
        # Test toggle method
        container.toggle_topbar_expansion()
        self.assertFalse(container._topbar_expanded)
        
        # Verify feedback message
        self.mock_page.show_snack_bar.assert_called()
        call_args = self.mock_page.show_snack_bar.call_args[0][0]
        self.assertIn("recolhida", call_args.content.value)
        self.assertIn("mais área disponível", call_args.content.value)
        
        # Toggle back
        container.toggle_topbar_expansion()
        self.assertTrue(container._topbar_expanded)
        
        # Verify expanded feedback message
        call_args = self.mock_page.show_snack_bar.call_args[0][0]
        self.assertIn("expandida", call_args.content.value)
    
    def test_topbar_state_methods(self):
        """Test TopBar state query and setter methods."""
        with patch('views.components.top_sidebar_container.FlowchartWidget') as mock_flowchart, \
             patch('views.components.top_sidebar_container.TimeTrackerWidget') as mock_time_tracker, \
             patch('views.components.top_sidebar_container.NotificationCenter') as mock_notifications:
            
            mock_flowchart.return_value = Mock()
            mock_time_tracker.return_value = Mock()
            mock_notifications.return_value = Mock()
            
            container = TopSidebarContainer(
                self.mock_page,
                self.mock_time_service,
                self.mock_workflow_service,
                self.mock_notification_service
            )
        
        # Test is_topbar_expanded
        self.assertTrue(container.is_topbar_expanded())
        
        # Test set_topbar_expanded
        container.set_topbar_expanded(False)
        self.assertFalse(container.is_topbar_expanded())
        
        container.set_topbar_expanded(True)
        self.assertTrue(container.is_topbar_expanded())
        
        # Test that setting same state doesn't trigger toggle
        initial_call_count = self.mock_page.show_snack_bar.call_count
        container.set_topbar_expanded(True)  # Already True
        self.assertEqual(self.mock_page.show_snack_bar.call_count, initial_call_count)


if __name__ == '__main__':
    unittest.main()