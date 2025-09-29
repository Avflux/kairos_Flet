import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import timedelta
import flet as ft

from models.activity import Activity
from models.time_entry import TimeEntry
from services.time_tracking_service import TimeTrackingService
from views.components.time_tracker_widget import TimeTrackerWidget


class TestTimeTrackerWidget(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_page = Mock(spec=ft.Page)
        self.mock_service = Mock(spec=TimeTrackingService)
        
        # Set up mock service default returns
        self.mock_service.is_tracking.return_value = False
        self.mock_service.is_paused.return_value = False
        self.mock_service.get_elapsed_time.return_value = timedelta()
        self.mock_service.get_current_entry.return_value = None
        
        self.test_activity = Activity(
            name="Test Activity",
            category="Development"
        )
        
        # Create widget
        self.widget = TimeTrackerWidget(self.mock_page, self.mock_service)
    
    def test_widget_initialization(self):
        """Test widget initializes correctly."""
        self.assertEqual(self.widget.page, self.mock_page)
        self.assertEqual(self.widget.time_service, self.mock_service)
        self.assertIsNone(self.widget.current_activity)
        self.assertEqual(self.widget.elapsed_time, timedelta())
        self.assertFalse(self.widget.is_running)
        self.assertFalse(self.widget.is_paused)
        
        # Check that widget registered as listener
        self.mock_service.add_listener.assert_called_once_with(self.widget)
    
    def test_initial_ui_state(self):
        """Test initial UI state."""
        self.assertEqual(self.widget.time_display.value, "00:00:00")
        self.assertEqual(self.widget.activity_display.value, "No activity")
        self.assertTrue(self.widget.start_button.visible)
        self.assertFalse(self.widget.pause_button.visible)
        self.assertFalse(self.widget.stop_button.visible)
    
    def test_format_time(self):
        """Test time formatting."""
        # Test zero time
        self.assertEqual(self.widget._format_time(timedelta()), "00:00:00")
        
        # Test various durations
        self.assertEqual(
            self.widget._format_time(timedelta(seconds=30)),
            "00:00:30"
        )
        self.assertEqual(
            self.widget._format_time(timedelta(minutes=5, seconds=30)),
            "00:05:30"
        )
        self.assertEqual(
            self.widget._format_time(timedelta(hours=2, minutes=30, seconds=45)),
            "02:30:45"
        )
        self.assertEqual(
            self.widget._format_time(timedelta(hours=25, minutes=70, seconds=80)),
            "26:11:20"  # 25h + 1h10m + 1m20s
        )
    
    def test_on_timer_start(self):
        """Test timer start event handling."""
        self.widget.on_timer_start(self.test_activity)
        
        self.assertEqual(self.widget.current_activity, self.test_activity)
        self.assertTrue(self.widget.is_running)
        self.assertFalse(self.widget.is_paused)
        self.assertEqual(self.widget.activity_display.value, "Test Activity")
        self.assertFalse(self.widget.start_button.visible)
        self.assertTrue(self.widget.pause_button.visible)
        self.assertTrue(self.widget.stop_button.visible)
    
    def test_on_timer_stop(self):
        """Test timer stop event handling."""
        # Set up running state first
        self.widget.is_running = True
        self.widget.current_activity = self.test_activity
        self.widget.elapsed_time = timedelta(minutes=30)
        
        test_entry = TimeEntry(
            activity_id=self.test_activity.id,
            start_time=self.test_activity.created_at
        )
        
        self.widget.on_timer_stop(test_entry)
        
        self.assertFalse(self.widget.is_running)
        self.assertFalse(self.widget.is_paused)
        self.assertEqual(self.widget.elapsed_time, timedelta())
        self.assertTrue(self.widget.start_button.visible)
        self.assertFalse(self.widget.pause_button.visible)
        self.assertFalse(self.widget.stop_button.visible)
    
    def test_on_timer_pause(self):
        """Test timer pause event handling."""
        # Set up running state first
        self.widget.is_running = True
        
        self.widget.on_timer_pause()
        
        self.assertTrue(self.widget.is_paused)
        self.assertEqual(self.widget.pause_button.icon, ft.icons.PLAY_ARROW)
        self.assertEqual(self.widget.pause_button.tooltip, "Resume tracking")
    
    def test_on_timer_resume(self):
        """Test timer resume event handling."""
        # Set up paused state first
        self.widget.is_running = True
        self.widget.is_paused = True
        
        self.widget.on_timer_resume()
        
        self.assertFalse(self.widget.is_paused)
        self.assertEqual(self.widget.pause_button.icon, ft.icons.PAUSE)
        self.assertEqual(self.widget.pause_button.tooltip, "Pause tracking")
    
    def test_on_timer_tick(self):
        """Test timer tick event handling."""
        elapsed = timedelta(minutes=15, seconds=30)
        
        self.widget.on_timer_tick(elapsed)
        
        self.assertEqual(self.widget.elapsed_time, elapsed)
        self.assertEqual(self.widget.time_display.value, "00:15:30")
    
    def test_start_click_no_activity(self):
        """Test start button click without selected activity."""
        self.widget.current_activity = None
        
        # Mock the error display
        self.widget._show_error = Mock()
        
        self.widget._on_start_click(None)
        
        self.widget._show_error.assert_called_once_with("Please select an activity first")
        self.mock_service.start_tracking.assert_not_called()
    
    def test_start_click_with_activity(self):
        """Test start button click with selected activity."""
        self.widget.current_activity = self.test_activity
        
        self.widget._on_start_click(None)
        
        self.mock_service.start_tracking.assert_called_once_with(self.test_activity)
    
    def test_start_click_service_error(self):
        """Test start button click when service raises error."""
        self.widget.current_activity = self.test_activity
        self.mock_service.start_tracking.side_effect = ValueError("Already tracking")
        
        # Mock the error display
        self.widget._show_error = Mock()
        
        self.widget._on_start_click(None)
        
        self.widget._show_error.assert_called_once_with("Already tracking")
    
    def test_pause_click_when_running(self):
        """Test pause button click when running."""
        self.widget.is_paused = False
        
        self.widget._on_pause_click(None)
        
        self.mock_service.pause_tracking.assert_called_once()
    
    def test_pause_click_when_paused(self):
        """Test pause button click when paused (resume)."""
        self.widget.is_paused = True
        
        self.widget._on_pause_click(None)
        
        self.mock_service.resume_tracking.assert_called_once()
    
    def test_stop_click(self):
        """Test stop button click."""
        test_entry = TimeEntry(
            activity_id=self.test_activity.id,
            start_time=self.test_activity.created_at
        )
        test_entry.stop()
        
        self.mock_service.stop_tracking.return_value = test_entry
        self.widget.current_activity = self.test_activity
        
        # Mock the success display
        self.widget._show_success = Mock()
        
        self.widget._on_stop_click(None)
        
        self.mock_service.stop_tracking.assert_called_once()
        self.widget._show_success.assert_called_once()
    
    def test_activity_change(self):
        """Test activity dropdown change."""
        # Mock the dropdown event
        mock_event = Mock()
        mock_event.control.value = "New Activity"
        
        self.widget._on_activity_change(mock_event)
        
        self.assertIsNotNone(self.widget.current_activity)
        self.assertEqual(self.widget.current_activity.name, "New Activity")
        self.assertEqual(self.widget.current_activity.category, "General")
    
    def test_quick_activity_submit(self):
        """Test quick activity field submit."""
        # Mock the text field event
        mock_event = Mock()
        mock_event.control.value = "Quick Task"
        
        self.widget._on_quick_activity_submit(mock_event)
        
        self.assertIsNotNone(self.widget.current_activity)
        self.assertEqual(self.widget.current_activity.name, "Quick Task")
        self.assertEqual(self.widget.current_activity.category, "Quick")
        self.assertEqual(mock_event.control.value, "")
        
        # Check that activity was added to dropdown
        option_texts = [opt.text for opt in self.widget.activity_dropdown.options]
        self.assertIn("Quick Task", option_texts)
    
    def test_add_activity_button_click(self):
        """Test add activity button click."""
        self.widget.quick_activity_field.value = "Button Task"
        
        self.widget._on_add_activity_click(None)
        
        self.assertIsNotNone(self.widget.current_activity)
        self.assertEqual(self.widget.current_activity.name, "Button Task")
        self.assertEqual(self.widget.quick_activity_field.value, "")
    
    def test_add_quick_activity_duplicate(self):
        """Test adding duplicate activity doesn't create duplicate options."""
        # Add activity first time
        self.widget._add_quick_activity("Duplicate Task")
        initial_count = len(self.widget.activity_dropdown.options)
        
        # Add same activity again
        self.widget._add_quick_activity("Duplicate Task")
        final_count = len(self.widget.activity_dropdown.options)
        
        self.assertEqual(initial_count, final_count)
    
    def test_set_activities(self):
        """Test setting available activities."""
        activities = [
            Activity(name="Activity 1", category="Dev"),
            Activity(name="Activity 2", category="Test"),
            Activity(name="Activity 3", category="Design")
        ]
        
        self.widget.set_activities(activities)
        
        self.assertEqual(len(self.widget.activity_dropdown.options), 3)
        option_texts = [opt.text for opt in self.widget.activity_dropdown.options]
        self.assertIn("Activity 1", option_texts)
        self.assertIn("Activity 2", option_texts)
        self.assertIn("Activity 3", option_texts)
    
    def test_refresh_syncs_with_service(self):
        """Test refresh method syncs with service state."""
        # Set up service state
        self.mock_service.is_tracking.return_value = True
        self.mock_service.is_paused.return_value = True
        self.mock_service.get_elapsed_time.return_value = timedelta(minutes=10)
        
        test_entry = TimeEntry(
            activity_id=self.test_activity.id,
            start_time=self.test_activity.created_at
        )
        self.mock_service.get_current_entry.return_value = test_entry
        
        self.widget.refresh()
        
        self.assertTrue(self.widget.is_running)
        self.assertTrue(self.widget.is_paused)
        self.assertEqual(self.widget.elapsed_time, timedelta(minutes=10))
    
    def test_refresh_not_tracking(self):
        """Test refresh when not tracking."""
        # Set up widget as if it was tracking
        self.widget.is_running = True
        self.widget.elapsed_time = timedelta(minutes=5)
        self.widget.current_activity = self.test_activity
        
        # Service says not tracking
        self.mock_service.is_tracking.return_value = False
        
        self.widget.refresh()
        
        self.assertFalse(self.widget.is_running)
        self.assertEqual(self.widget.elapsed_time, timedelta())
        self.assertIsNone(self.widget.current_activity)
    
    def test_ui_controls_disabled_when_running(self):
        """Test that activity controls are disabled when running."""
        self.widget.is_running = True
        self.widget._update_ui_state()
        
        self.assertTrue(self.widget.activity_dropdown.disabled)
        self.assertTrue(self.widget.quick_activity_field.disabled)
        self.assertTrue(self.widget.add_activity_button.disabled)
    
    def test_ui_controls_enabled_when_stopped(self):
        """Test that activity controls are enabled when stopped."""
        self.widget.is_running = False
        self.widget._update_ui_state()
        
        self.assertFalse(self.widget.activity_dropdown.disabled)
        self.assertFalse(self.widget.quick_activity_field.disabled)
        self.assertFalse(self.widget.add_activity_button.disabled)
    
    def test_status_indicator_colors(self):
        """Test status indicator color changes."""
        # Stopped state
        self.widget.is_running = False
        self.widget._update_ui_state()
        self.assertEqual(self.widget.status_indicator.bgcolor, ft.colors.SURFACE_VARIANT)
        
        # Running state
        self.widget.is_running = True
        self.widget.is_paused = False
        self.widget._update_ui_state()
        self.assertEqual(self.widget.status_indicator.bgcolor, ft.colors.PRIMARY)
        
        # Paused state
        self.widget.is_running = True
        self.widget.is_paused = True
        self.widget._update_ui_state()
        self.assertEqual(self.widget.status_indicator.bgcolor, ft.colors.WARNING)
    
    def test_show_error_displays_snackbar(self):
        """Test error message display."""
        self.widget._show_error("Test error message")
        
        self.mock_page.show_snack_bar.assert_called_once()
        call_args = self.mock_page.show_snack_bar.call_args[0][0]
        self.assertIsInstance(call_args, ft.SnackBar)
        self.assertEqual(call_args.bgcolor, ft.colors.ERROR)
    
    def test_show_success_displays_snackbar(self):
        """Test success message display."""
        self.widget._show_success("Test success message")
        
        self.mock_page.show_snack_bar.assert_called_once()
        call_args = self.mock_page.show_snack_bar.call_args[0][0]
        self.assertIsInstance(call_args, ft.SnackBar)
        self.assertEqual(call_args.bgcolor, ft.colors.PRIMARY)


if __name__ == '__main__':
    unittest.main()