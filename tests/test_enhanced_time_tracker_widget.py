import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import timedelta, datetime
import flet as ft

from views.components.time_tracker_widget import TimeTrackerWidget
from services.time_tracking_service import TimeTrackingService
from models.activity import Activity
from models.time_entry import TimeEntry


class TestEnhancedTimeTrackerWidget(unittest.TestCase):
    """Test suite for enhanced TimeTrackerWidget functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.page = Mock(spec=ft.Page)
        self.page.show_snack_bar = Mock()  # Add show_snack_bar method to mock
        self.time_service = Mock(spec=TimeTrackingService)
        self.widget = TimeTrackerWidget(self.page, self.time_service)
        
        # Test activity
        self.test_activity = Activity(
            name="Test Activity",
            category="Testing"
        )
    
    def test_initialization(self):
        """Test widget initialization with enhanced features."""
        # Verify service listener registration
        self.time_service.add_listener.assert_called_once_with(self.widget)
        
        # Verify initial state
        self.assertIsNone(self.widget.current_activity)
        self.assertEqual(self.widget.elapsed_time, timedelta())
        self.assertFalse(self.widget.is_running)
        self.assertFalse(self.widget.is_paused)
        
        # Verify UI components exist
        self.assertIsNotNone(self.widget.progress_ring)
        self.assertIsNotNone(self.widget.time_display)
        self.assertIsNotNone(self.widget.status_display)
        self.assertIsNotNone(self.widget.state_indicator)
        
        # Verify modern button styling
        self.assertEqual(self.widget.start_button.text, "Start")
        self.assertEqual(self.widget.pause_button.text, "Pause")
        self.assertEqual(self.widget.stop_button.text, "Stop")
    
    def test_circular_progress_indicator(self):
        """Test circular progress indicator functionality."""
        # Test initial state
        self.assertEqual(self.widget.progress_ring.value, 0)
        self.assertEqual(self.widget.progress_ring.color, 'primary')
        
        # Test progress calculation
        self.widget.elapsed_time = timedelta(hours=2)  # 25% of 8 hour max
        self.widget._update_progress_ring()
        self.assertEqual(self.widget.progress_ring.value, 0.25)
        
        # Test color changes based on progress
        self.widget.elapsed_time = timedelta(hours=5)  # 62.5% of max
        self.widget._update_progress_ring()
        self.assertEqual(self.widget.progress_ring.color, 'secondary')
        
        self.widget.elapsed_time = timedelta(hours=7)  # 87.5% of max
        self.widget._update_progress_ring()
        self.assertEqual(self.widget.progress_ring.color, 'error')
    
    def test_visual_state_feedback(self):
        """Test visual feedback for different tracking states."""
        # Test stopped state
        self.widget.is_running = False
        self.widget.is_paused = False
        self.widget._update_status_display()
        self.assertEqual(self.widget.status_display.value, "Stopped")
        self.assertEqual(self.widget.status_display.color, 'on_surface_variant')
        
        # Test running state
        self.widget.is_running = True
        self.widget.is_paused = False
        self.widget._update_status_display()
        self.assertEqual(self.widget.status_display.value, "Running")
        self.assertEqual(self.widget.status_display.color, 'primary')
        
        # Test paused state
        self.widget.is_running = True
        self.widget.is_paused = True
        self.widget._update_status_display()
        self.assertEqual(self.widget.status_display.value, "Paused")
        self.assertEqual(self.widget.status_display.color, 'secondary')
    
    def test_control_button_states(self):
        """Test control button visibility and styling based on state."""
        # Test stopped state
        self.widget.is_running = False
        self.widget.current_activity = self.test_activity
        self.widget._update_control_buttons()
        
        self.assertTrue(self.widget.start_button.visible)
        self.assertFalse(self.widget.pause_button.visible)
        self.assertFalse(self.widget.stop_button.visible)
        self.assertFalse(self.widget.start_button.disabled)
        
        # Test running state
        self.widget.is_running = True
        self.widget.is_paused = False
        self.widget._update_control_buttons()
        
        self.assertFalse(self.widget.start_button.visible)
        self.assertTrue(self.widget.pause_button.visible)
        self.assertTrue(self.widget.stop_button.visible)
        self.assertEqual(self.widget.pause_button.text, "Pause")
        self.assertEqual(self.widget.pause_button.icon, ft.Icons.PAUSE)
        
        # Test paused state
        self.widget.is_paused = True
        self.widget._update_control_buttons()
        
        self.assertEqual(self.widget.pause_button.text, "Resume")
        self.assertEqual(self.widget.pause_button.icon, ft.Icons.PLAY_ARROW)
        
        # Test no activity selected
        self.widget.is_running = False
        self.widget.current_activity = None
        self.widget._update_control_buttons()
        self.assertTrue(self.widget.start_button.disabled)
    
    def test_start_tracking_with_feedback(self):
        """Test start tracking with enhanced user feedback."""
        # Test successful start
        self.widget.current_activity = self.test_activity
        self.time_service.start_tracking.return_value = Mock()
        
        self.widget._on_start_click(Mock())
        
        self.time_service.start_tracking.assert_called_once_with(self.test_activity)
        self.page.show_snack_bar.assert_called_once()
        
        # Verify success message
        snack_bar_call = self.page.show_snack_bar.call_args[0][0]
        # Check that snack bar was called with success styling
        self.assertEqual(snack_bar_call.bgcolor, 'primary')
        
        # Test start without activity
        self.widget.current_activity = None
        self.page.show_snack_bar.reset_mock()
        
        self.widget._on_start_click(Mock())
        
        # Verify error message
        snack_bar_call = self.page.show_snack_bar.call_args[0][0]
        self.assertEqual(snack_bar_call.bgcolor, 'error')
        
        # Test service error
        self.widget.current_activity = self.test_activity
        self.time_service.start_tracking.side_effect = ValueError("Already tracking")
        self.page.show_snack_bar.reset_mock()
        
        self.widget._on_start_click(Mock())
        
        snack_bar_call = self.page.show_snack_bar.call_args[0][0]
        self.assertEqual(snack_bar_call.bgcolor, 'error')
    
    def test_pause_resume_with_feedback(self):
        """Test pause/resume functionality with enhanced feedback."""
        # Test pause
        self.widget.is_paused = False
        self.time_service.pause_tracking.return_value = True
        
        self.widget._on_pause_click(Mock())
        
        self.time_service.pause_tracking.assert_called_once()
        self.page.show_snack_bar.assert_called_once()
        
        # Verify success message
        snack_bar_call = self.page.show_snack_bar.call_args[0][0]
        self.assertEqual(snack_bar_call.bgcolor, 'primary')
        
        # Test resume
        self.widget.is_paused = True
        self.time_service.resume_tracking.return_value = True
        self.page.show_snack_bar.reset_mock()
        
        self.widget._on_pause_click(Mock())
        
        self.time_service.resume_tracking.assert_called_once()
        snack_bar_call = self.page.show_snack_bar.call_args[0][0]
        self.assertEqual(snack_bar_call.bgcolor, 'primary')
        
        # Test pause failure
        self.widget.is_paused = False
        self.time_service.pause_tracking.return_value = False
        self.page.show_snack_bar.reset_mock()
        
        self.widget._on_pause_click(Mock())
        
        snack_bar_call = self.page.show_snack_bar.call_args[0][0]
        self.assertEqual(snack_bar_call.bgcolor, 'error')
    
    def test_stop_tracking_with_feedback(self):
        """Test stop tracking with enhanced feedback."""
        # Test successful stop
        self.widget.current_activity = self.test_activity
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=30)
        completed_entry = TimeEntry(
            activity_id=self.test_activity.id,
            start_time=start_time,
            end_time=end_time
        )
        self.time_service.stop_tracking.return_value = completed_entry
        
        self.widget._on_stop_click(Mock())
        
        self.time_service.stop_tracking.assert_called_once()
        self.page.show_snack_bar.assert_called_once()
        
        # Verify success message styling
        snack_bar_call = self.page.show_snack_bar.call_args[0][0]
        self.assertEqual(snack_bar_call.bgcolor, 'primary')
        
        # Test stop with no active session
        self.time_service.stop_tracking.return_value = None
        self.page.show_snack_bar.reset_mock()
        
        self.widget._on_stop_click(Mock())
        
        snack_bar_call = self.page.show_snack_bar.call_args[0][0]
        self.assertEqual(snack_bar_call.bgcolor, 'error')
    
    def test_activity_management(self):
        """Test enhanced activity selection and management."""
        # Test activity dropdown change
        mock_event = Mock()
        mock_event.control.value = "New Activity"
        
        self.widget._on_activity_change(mock_event)
        
        self.assertIsNotNone(self.widget.current_activity)
        self.assertEqual(self.widget.current_activity.name, "New Activity")
        
        # Test quick activity addition
        self.widget.quick_activity_field.value = "Quick Task"
        
        self.widget._on_add_activity_click(Mock())
        
        self.assertEqual(self.widget.current_activity.name, "Quick Task")
        self.assertEqual(self.widget.activity_dropdown.value, "Quick Task")
        self.assertEqual(self.widget.quick_activity_field.value, "")
        
        # Test quick activity submit
        mock_event = Mock()
        mock_event.control.value = "Submitted Task"
        
        self.widget._on_quick_activity_submit(mock_event)
        
        self.assertEqual(self.widget.current_activity.name, "Submitted Task")
        self.assertEqual(mock_event.control.value, "")
    
    def test_timer_accuracy(self):
        """Test timer accuracy and real-time updates."""
        # Test time formatting
        test_time = timedelta(hours=2, minutes=30, seconds=45)
        formatted = self.widget._format_time(test_time)
        self.assertEqual(formatted, "02:30:45")
        
        # Test timer listener callbacks
        self.widget.on_timer_start(self.test_activity)
        self.assertEqual(self.widget.current_activity, self.test_activity)
        self.assertTrue(self.widget.is_running)
        self.assertFalse(self.widget.is_paused)
        
        # Test timer tick updates
        elapsed_time = timedelta(minutes=15)
        self.widget.on_timer_tick(elapsed_time)
        self.assertEqual(self.widget.elapsed_time, elapsed_time)
        
        # Test pause callback
        self.widget.on_timer_pause()
        self.assertTrue(self.widget.is_paused)
        
        # Test resume callback
        self.widget.on_timer_resume()
        self.assertFalse(self.widget.is_paused)
        
        # Test stop callback
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=15)
        completed_entry = TimeEntry(
            activity_id=self.test_activity.id,
            start_time=start_time,
            end_time=end_time
        )
        self.widget.on_timer_stop(completed_entry)
        self.assertFalse(self.widget.is_running)
        self.assertFalse(self.widget.is_paused)
        self.assertEqual(self.widget.elapsed_time, timedelta())
    
    def test_ui_state_synchronization(self):
        """Test UI state synchronization with service state."""
        # Mock service state
        self.time_service.is_tracking.return_value = True
        self.time_service.is_paused.return_value = False
        self.time_service.get_elapsed_time.return_value = timedelta(minutes=10)
        self.time_service.get_current_entry.return_value = Mock()
        
        self.widget.refresh()
        
        self.assertTrue(self.widget.is_running)
        self.assertFalse(self.widget.is_paused)
        self.assertEqual(self.widget.elapsed_time, timedelta(minutes=10))
        
        # Test stopped state
        self.time_service.is_tracking.return_value = False
        self.time_service.is_paused.return_value = False
        
        self.widget.refresh()
        
        self.assertFalse(self.widget.is_running)
        self.assertEqual(self.widget.elapsed_time, timedelta())
    
    def test_modern_styling_elements(self):
        """Test modern styling and visual elements."""
        # Test progress ring properties
        self.assertEqual(self.widget.progress_ring.width, 120)
        self.assertEqual(self.widget.progress_ring.height, 120)
        self.assertEqual(self.widget.progress_ring.stroke_width, 8)
        
        # Test button styling
        self.assertIsNotNone(self.widget.start_button.style)
        self.assertIsNotNone(self.widget.pause_button.style)
        self.assertIsNotNone(self.widget.stop_button.style)
        
        # Test container styling
        self.assertEqual(self.widget.content.width, 300)
        self.assertIsNotNone(self.widget.content.shadow)
        
        # Test state indicator properties
        self.assertEqual(self.widget.state_indicator.width, 16)
        self.assertEqual(self.widget.state_indicator.height, 16)
    
    def test_responsive_layout(self):
        """Test responsive layout adaptation."""
        # Test activity controls disabled during tracking
        self.widget.is_running = True
        self.widget._update_ui_state()
        
        self.assertTrue(self.widget.activity_dropdown.disabled)
        self.assertTrue(self.widget.quick_activity_field.disabled)
        self.assertTrue(self.widget.add_activity_button.disabled)
        
        # Test controls enabled when stopped
        self.widget.is_running = False
        self.widget._update_ui_state()
        
        self.assertFalse(self.widget.activity_dropdown.disabled)
        self.assertFalse(self.widget.quick_activity_field.disabled)
        self.assertFalse(self.widget.add_activity_button.disabled)
    
    def test_error_handling(self):
        """Test error handling and user feedback."""
        # Test error message styling
        self.widget._show_error("Test error")
        
        self.page.show_snack_bar.assert_called_once()
        snack_bar = self.page.show_snack_bar.call_args[0][0]
        self.assertEqual(snack_bar.bgcolor, 'error')
        self.assertEqual(snack_bar.action, "Dismiss")
        
        # Test success message styling
        self.page.show_snack_bar.reset_mock()
        self.widget._show_success("Test success")
        
        snack_bar = self.page.show_snack_bar.call_args[0][0]
        self.assertEqual(snack_bar.bgcolor, 'primary')
        self.assertEqual(snack_bar.action, "Dismiss")


if __name__ == '__main__':
    unittest.main()