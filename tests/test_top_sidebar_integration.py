import unittest
from unittest.mock import Mock, MagicMock, patch
import flet as ft


class TestTopSidebarIntegration(unittest.TestCase):
    """Integration tests for TopSidebarContainer component interaction and layout responsiveness."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_page = Mock(spec=ft.Page)
        self.mock_page.update = Mock()
        self.mock_page.show_snack_bar = Mock()
    
    @patch('views.components.top_sidebar_container.TimeTrackerWidget')
    @patch('views.components.top_sidebar_container.FlowchartWidget')
    @patch('views.components.top_sidebar_container.NotificationCenter')
    def test_component_integration_and_layout_responsiveness(
        self, 
        mock_notification_center_cls,
        mock_flowchart_cls,
        mock_time_tracker_cls
    ):
        """Test component integration and responsive layout adaptation."""
        # Set up mock instances with realistic behavior
        mock_time_tracker = Mock()
        mock_flowchart = Mock()
        mock_notification_center = Mock()
        
        # Configure class mocks to return instances
        mock_time_tracker_cls.return_value = mock_time_tracker
        mock_flowchart_cls.return_value = mock_flowchart
        mock_notification_center_cls.return_value = mock_notification_center
        
        # Configure time tracker mock
        mock_time_tracker.is_running = False
        mock_time_tracker.is_paused = False
        mock_time_tracker.elapsed_time = Mock()
        mock_time_tracker._format_time = Mock(return_value="00:15:30")
        mock_time_tracker.refresh = Mock()
        
        # Configure flowchart mock
        mock_stage = Mock()
        mock_stage.name = "Verification"
        mock_flowchart.create_default_workflow = Mock()
        mock_flowchart.get_progress_percentage = Mock(return_value=75.0)
        mock_flowchart.get_current_stage = Mock(return_value=mock_stage)
        mock_flowchart._refresh_display = Mock()
        mock_flowchart.advance_to_stage = Mock(return_value=True)
        mock_flowchart.complete_current_stage = Mock(return_value=True)
        
        # Configure notification center mock
        mock_notification_center._update_display = Mock()
        mock_notification_center.add_test_notification = Mock()
        
        # Import and create container
        from views.components.top_sidebar_container import TopSidebarContainer
        
        container = TopSidebarContainer(self.mock_page)
        
        # Test 1: Verify initial expanded layout structure
        self.assertTrue(container.sidebar_expanded)
        self.assertIsInstance(container.content, ft.Row)
        
        expanded_controls = container.content.controls
        self.assertEqual(len(expanded_controls), 3)
        
        # Verify expanded layout properties
        time_container = expanded_controls[0]
        flowchart_container = expanded_controls[1]
        notification_container = expanded_controls[2]
        
        self.assertEqual(time_container.expand, 1)
        self.assertEqual(flowchart_container.expand, 2)
        self.assertEqual(notification_container.width, 60)
        
        # Test 2: Switch to collapsed layout and verify structure
        container.update_layout(False)
        
        self.assertFalse(container.sidebar_expanded)
        collapsed_controls = container.content.controls
        self.assertEqual(len(collapsed_controls), 3)
        
        # Verify collapsed layout properties
        compact_timer = collapsed_controls[0]
        compact_flowchart = collapsed_controls[1]
        compact_notification = collapsed_controls[2]
        
        self.assertEqual(compact_timer.width, 40)
        self.assertEqual(compact_flowchart.expand, 1)
        self.assertEqual(compact_notification.width, 40)
        
        # Test 3: Verify component refresh functionality
        container.refresh_components()
        
        mock_time_tracker.refresh.assert_called_once()
        mock_flowchart._refresh_display.assert_called_once()
        mock_notification_center._update_display.assert_called_once()
        
        # Test 4: Test workflow delegation methods
        result = container.advance_workflow_stage("next_stage")
        self.assertTrue(result)
        mock_flowchart.advance_to_stage.assert_called_once_with("next_stage")
        
        result = container.complete_current_workflow_stage()
        self.assertTrue(result)
        mock_flowchart.complete_current_stage.assert_called_once()
        
        # Test 5: Test notification delegation
        container.add_test_notification()
        mock_notification_center.add_test_notification.assert_called_once()
        
        # Test 6: Verify component getters
        self.assertEqual(container.get_time_tracker(), mock_time_tracker)
        self.assertEqual(container.get_flowchart(), mock_flowchart)
        self.assertEqual(container.get_notifications(), mock_notification_center)
        
        # Test 7: Verify page updates were called for layout changes
        self.mock_page.update.assert_called()
    
    @patch('views.components.top_sidebar_container.TimeTrackerWidget')
    @patch('views.components.top_sidebar_container.FlowchartWidget')
    @patch('views.components.top_sidebar_container.NotificationCenter')
    def test_compact_mode_interactions(
        self, 
        mock_notification_center_cls,
        mock_flowchart_cls,
        mock_time_tracker_cls
    ):
        """Test interactions in compact mode show appropriate user feedback."""
        # Set up mock instances
        mock_time_tracker = Mock()
        mock_flowchart = Mock()
        mock_notification_center = Mock()
        
        # Configure class mocks to return instances
        mock_time_tracker_cls.return_value = mock_time_tracker
        mock_flowchart_cls.return_value = mock_flowchart
        mock_notification_center_cls.return_value = mock_notification_center
        
        # Configure mock methods and attributes
        mock_flowchart.create_default_workflow = Mock()
        mock_flowchart.get_progress_percentage = Mock(return_value=50.0)
        mock_flowchart.get_current_stage = Mock(return_value=None)
        mock_time_tracker.is_running = False
        mock_time_tracker.is_paused = False
        mock_time_tracker.elapsed_time = Mock()
        mock_time_tracker._format_time = Mock(return_value="00:00:00")
        
        # Import and create container
        from views.components.top_sidebar_container import TopSidebarContainer
        
        container = TopSidebarContainer(self.mock_page)
        
        # Switch to collapsed layout
        container.update_layout(False)
        
        # Test compact timer click
        container._on_compact_timer_click(None)
        
        # Verify snack bar was shown with appropriate message
        self.mock_page.show_snack_bar.assert_called()
        call_args = self.mock_page.show_snack_bar.call_args[0][0]
        self.assertIsInstance(call_args, ft.SnackBar)
        self.assertIn("Expand sidebar", call_args.content.value)
        self.assertIn("time tracker", call_args.content.value)
        
        # Reset mock for next test
        self.mock_page.show_snack_bar.reset_mock()
        
        # Test compact flowchart click
        container._on_compact_flowchart_click(None)
        
        # Verify snack bar was shown with appropriate message
        self.mock_page.show_snack_bar.assert_called()
        call_args = self.mock_page.show_snack_bar.call_args[0][0]
        self.assertIsInstance(call_args, ft.SnackBar)
        self.assertIn("Expand sidebar", call_args.content.value)
        self.assertIn("workflow", call_args.content.value)
    
    @patch('views.components.top_sidebar_container.TimeTrackerWidget')
    @patch('views.components.top_sidebar_container.FlowchartWidget')
    @patch('views.components.top_sidebar_container.NotificationCenter')
    def test_layout_no_change_optimization(
        self, 
        mock_notification_center_cls,
        mock_flowchart_cls,
        mock_time_tracker_cls
    ):
        """Test that layout update with same state doesn't trigger unnecessary rebuilds."""
        # Set up mock instances
        mock_time_tracker = Mock()
        mock_flowchart = Mock()
        mock_notification_center = Mock()
        
        # Configure class mocks to return instances
        mock_time_tracker_cls.return_value = mock_time_tracker
        mock_flowchart_cls.return_value = mock_flowchart
        mock_notification_center_cls.return_value = mock_notification_center
        
        # Configure mock methods and attributes
        mock_flowchart.create_default_workflow = Mock()
        mock_flowchart.get_progress_percentage = Mock(return_value=50.0)
        mock_flowchart.get_current_stage = Mock(return_value=None)
        mock_time_tracker.is_running = False
        mock_time_tracker.is_paused = False
        mock_time_tracker.elapsed_time = Mock()
        mock_time_tracker._format_time = Mock(return_value="00:00:00")
        
        # Import and create container
        from views.components.top_sidebar_container import TopSidebarContainer
        
        container = TopSidebarContainer(self.mock_page)
        
        # Reset mock to clear initialization calls
        self.mock_page.update.reset_mock()
        
        # Update layout to same state (expanded)
        container.update_layout(True)
        
        # Verify no page update was called (optimization)
        self.mock_page.update.assert_not_called()
        
        # Now change state and verify update is called
        container.update_layout(False)
        self.mock_page.update.assert_called_once()
    
    @patch('views.components.top_sidebar_container.TimeTrackerWidget')
    @patch('views.components.top_sidebar_container.FlowchartWidget')
    @patch('views.components.top_sidebar_container.NotificationCenter')
    def test_container_styling_consistency(
        self, 
        mock_notification_center_cls,
        mock_flowchart_cls,
        mock_time_tracker_cls
    ):
        """Test that container maintains consistent styling across layout changes."""
        # Set up mock instances
        mock_time_tracker = Mock()
        mock_flowchart = Mock()
        mock_notification_center = Mock()
        
        # Configure class mocks to return instances
        mock_time_tracker_cls.return_value = mock_time_tracker
        mock_flowchart_cls.return_value = mock_flowchart
        mock_notification_center_cls.return_value = mock_notification_center
        
        # Configure mock methods and attributes
        mock_flowchart.create_default_workflow = Mock()
        mock_flowchart.get_progress_percentage = Mock(return_value=50.0)
        mock_flowchart.get_current_stage = Mock(return_value=None)
        mock_time_tracker.is_running = False
        mock_time_tracker.is_paused = False
        mock_time_tracker.elapsed_time = Mock()
        mock_time_tracker._format_time = Mock(return_value="00:00:00")
        
        # Import and create container
        from views.components.top_sidebar_container import TopSidebarContainer
        
        container = TopSidebarContainer(self.mock_page)
        
        # Store initial styling properties
        initial_height = container.height
        initial_bgcolor = container.bgcolor
        initial_border_radius = container.border_radius
        initial_padding = container.padding
        initial_border = container.border
        initial_shadow = container.shadow
        initial_animate = container.animate
        
        # Change layout and verify styling remains consistent
        container.update_layout(False)
        
        self.assertEqual(container.height, initial_height)
        self.assertEqual(container.bgcolor, initial_bgcolor)
        self.assertEqual(container.border_radius, initial_border_radius)
        self.assertEqual(container.padding, initial_padding)
        self.assertEqual(container.border, initial_border)
        self.assertEqual(container.shadow, initial_shadow)
        self.assertEqual(container.animate, initial_animate)
        
        # Change back and verify again
        container.update_layout(True)
        
        self.assertEqual(container.height, initial_height)
        self.assertEqual(container.bgcolor, initial_bgcolor)
        self.assertEqual(container.border_radius, initial_border_radius)
        self.assertEqual(container.padding, initial_padding)
        self.assertEqual(container.border, initial_border)
        self.assertEqual(container.shadow, initial_shadow)
        self.assertEqual(container.animate, initial_animate)


if __name__ == '__main__':
    unittest.main()