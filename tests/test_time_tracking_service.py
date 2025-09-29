import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import time
import threading

from models.activity import Activity
from models.time_entry import TimeEntry
from models.interfaces import TimerUpdateListener
from services.time_tracking_service import TimeTrackingService


class MockTimerListener(TimerUpdateListener):
    """Mock listener for testing timer events."""
    
    def __init__(self):
        self.start_calls = []
        self.stop_calls = []
        self.pause_calls = []
        self.resume_calls = []
        self.tick_calls = []
    
    def on_timer_start(self, activity: Activity) -> None:
        self.start_calls.append(activity)
    
    def on_timer_stop(self, time_entry: TimeEntry) -> None:
        self.stop_calls.append(time_entry)
    
    def on_timer_pause(self) -> None:
        self.pause_calls.append(True)
    
    def on_timer_resume(self) -> None:
        self.resume_calls.append(True)
    
    def on_timer_tick(self, elapsed_time: timedelta) -> None:
        self.tick_calls.append(elapsed_time)


class TestTimeTrackingService(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = TimeTrackingService()
        self.test_activity = Activity(
            name="Test Activity",
            category="Development"
        )
        self.listener = MockTimerListener()
    
    def tearDown(self):
        """Clean up after tests."""
        # Stop any running timers
        if self.service.is_tracking():
            self.service.stop_tracking()
        
        # Wait a bit for threads to clean up
        time.sleep(0.1)
    
    def test_initial_state(self):
        """Test service initial state."""
        self.assertFalse(self.service.is_tracking())
        self.assertFalse(self.service.is_paused())
        self.assertIsNone(self.service.get_current_entry())
        self.assertEqual(self.service.get_elapsed_time(), timedelta())
        self.assertEqual(len(self.service.get_time_entries()), 0)
    
    def test_start_tracking_valid(self):
        """Test starting time tracking with valid activity."""
        start_time = datetime.now()
        
        entry = self.service.start_tracking(self.test_activity)
        
        self.assertIsInstance(entry, TimeEntry)
        self.assertEqual(entry.activity_id, self.test_activity.id)
        self.assertIsNone(entry.end_time)
        self.assertTrue(self.service.is_tracking())
        self.assertFalse(self.service.is_paused())
        self.assertEqual(self.service.get_current_entry(), entry)
        
        # Check that start time is reasonable
        self.assertGreater(entry.start_time, start_time - timedelta(seconds=1))
        self.assertLess(entry.start_time, datetime.now() + timedelta(seconds=1))
    
    def test_start_tracking_already_active(self):
        """Test starting tracking when already active."""
        self.service.start_tracking(self.test_activity)
        
        with self.assertRaises(ValueError) as context:
            self.service.start_tracking(self.test_activity)
        
        self.assertIn("already active", str(context.exception))
    
    def test_stop_tracking_valid(self):
        """Test stopping time tracking."""
        self.service.start_tracking(self.test_activity)
        
        # Wait a small amount to ensure duration > 0
        time.sleep(0.01)
        
        completed_entry = self.service.stop_tracking()
        
        self.assertIsNotNone(completed_entry)
        self.assertIsNotNone(completed_entry.end_time)
        self.assertFalse(self.service.is_tracking())
        self.assertFalse(self.service.is_paused())
        self.assertIsNone(self.service.get_current_entry())
        self.assertEqual(self.service.get_elapsed_time(), timedelta())
        
        # Check that entry is stored
        entries = self.service.get_time_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0], completed_entry)
    
    def test_stop_tracking_not_active(self):
        """Test stopping tracking when not active."""
        result = self.service.stop_tracking()
        self.assertIsNone(result)
    
    def test_pause_tracking_valid(self):
        """Test pausing time tracking."""
        self.service.start_tracking(self.test_activity)
        
        result = self.service.pause_tracking()
        
        self.assertTrue(result)
        self.assertTrue(self.service.is_tracking())
        self.assertTrue(self.service.is_paused())
    
    def test_pause_tracking_not_active(self):
        """Test pausing when not tracking."""
        result = self.service.pause_tracking()
        self.assertFalse(result)
    
    def test_pause_tracking_already_paused(self):
        """Test pausing when already paused."""
        self.service.start_tracking(self.test_activity)
        self.service.pause_tracking()
        
        result = self.service.pause_tracking()
        self.assertFalse(result)
    
    def test_resume_tracking_valid(self):
        """Test resuming paused tracking."""
        self.service.start_tracking(self.test_activity)
        self.service.pause_tracking()
        
        result = self.service.resume_tracking()
        
        self.assertTrue(result)
        self.assertTrue(self.service.is_tracking())
        self.assertFalse(self.service.is_paused())
    
    def test_resume_tracking_not_paused(self):
        """Test resuming when not paused."""
        self.service.start_tracking(self.test_activity)
        
        result = self.service.resume_tracking()
        self.assertFalse(result)
    
    def test_resume_tracking_not_active(self):
        """Test resuming when not tracking."""
        result = self.service.resume_tracking()
        self.assertFalse(result)
    
    def test_elapsed_time_calculation(self):
        """Test elapsed time calculation."""
        self.service.start_tracking(self.test_activity)
        
        # Wait a bit
        time.sleep(0.05)
        
        elapsed = self.service.get_elapsed_time()
        self.assertGreater(elapsed.total_seconds(), 0.04)
        self.assertLess(elapsed.total_seconds(), 0.1)
    
    def test_elapsed_time_with_pause(self):
        """Test elapsed time calculation with pause."""
        self.service.start_tracking(self.test_activity)
        
        # Run for a bit
        time.sleep(0.02)
        
        # Pause
        self.service.pause_tracking()
        pause_elapsed = self.service.get_elapsed_time()
        
        # Wait while paused
        time.sleep(0.02)
        
        # Elapsed time should not increase while paused
        paused_elapsed = self.service.get_elapsed_time()
        self.assertAlmostEqual(
            pause_elapsed.total_seconds(),
            paused_elapsed.total_seconds(),
            delta=0.01
        )
        
        # Resume and check time increases
        self.service.resume_tracking()
        time.sleep(0.02)
        
        resumed_elapsed = self.service.get_elapsed_time()
        self.assertGreater(resumed_elapsed.total_seconds(), paused_elapsed.total_seconds())
    
    def test_get_time_entries_filtering(self):
        """Test getting time entries with filtering."""
        activity1 = Activity(name="Activity 1", category="Dev")
        activity2 = Activity(name="Activity 2", category="Test")
        
        # Create some entries
        self.service.start_tracking(activity1)
        time.sleep(0.01)
        self.service.stop_tracking()
        
        self.service.start_tracking(activity2)
        time.sleep(0.01)
        self.service.stop_tracking()
        
        self.service.start_tracking(activity1)
        time.sleep(0.01)
        self.service.stop_tracking()
        
        # Test getting all entries
        all_entries = self.service.get_time_entries()
        self.assertEqual(len(all_entries), 3)
        
        # Test filtering by activity
        activity1_entries = self.service.get_time_entries(activity1.id)
        self.assertEqual(len(activity1_entries), 2)
        
        activity2_entries = self.service.get_time_entries(activity2.id)
        self.assertEqual(len(activity2_entries), 1)
    
    def test_listener_notifications(self):
        """Test that listeners are properly notified."""
        self.service.add_listener(self.listener)
        
        # Test start notification
        self.service.start_tracking(self.test_activity)
        self.assertEqual(len(self.listener.start_calls), 1)
        self.assertEqual(self.listener.start_calls[0], self.test_activity)
        
        # Test pause notification
        self.service.pause_tracking()
        self.assertEqual(len(self.listener.pause_calls), 1)
        
        # Test resume notification
        self.service.resume_tracking()
        self.assertEqual(len(self.listener.resume_calls), 1)
        
        # Test stop notification
        time.sleep(0.01)
        self.service.stop_tracking()
        self.assertEqual(len(self.listener.stop_calls), 1)
        self.assertIsInstance(self.listener.stop_calls[0], TimeEntry)
    
    def test_listener_tick_notifications(self):
        """Test that tick notifications are sent."""
        self.service.add_listener(self.listener)
        self.service.start_tracking(self.test_activity)
        
        # Wait for a few ticks
        time.sleep(1.5)
        
        # Should have received at least one tick
        self.assertGreater(len(self.listener.tick_calls), 0)
        
        # All tick calls should have positive elapsed time
        for elapsed in self.listener.tick_calls:
            self.assertGreater(elapsed.total_seconds(), 0)
    
    def test_listener_management(self):
        """Test adding and removing listeners."""
        # Add listener
        self.service.add_listener(self.listener)
        
        # Start tracking to generate events
        self.service.start_tracking(self.test_activity)
        self.assertEqual(len(self.listener.start_calls), 1)
        
        # Remove listener
        self.service.remove_listener(self.listener)
        
        # Stop tracking - should not notify removed listener
        self.service.stop_tracking()
        self.assertEqual(len(self.listener.stop_calls), 0)
    
    def test_get_current_activity_id(self):
        """Test getting current activity ID."""
        self.assertIsNone(self.service.get_current_activity_id())
        
        self.service.start_tracking(self.test_activity)
        self.assertEqual(self.service.get_current_activity_id(), self.test_activity.id)
        
        self.service.stop_tracking()
        self.assertIsNone(self.service.get_current_activity_id())
    
    def test_clear_all_entries(self):
        """Test clearing all time entries."""
        # Create some entries
        self.service.start_tracking(self.test_activity)
        time.sleep(0.01)
        self.service.stop_tracking()
        
        self.service.start_tracking(self.test_activity)
        time.sleep(0.01)
        self.service.stop_tracking()
        
        self.assertEqual(len(self.service.get_time_entries()), 2)
        
        # Clear entries
        count = self.service.clear_all_entries()
        self.assertEqual(count, 2)
        self.assertEqual(len(self.service.get_time_entries()), 0)
    
    def test_get_total_time_for_activity(self):
        """Test getting total time for specific activity."""
        activity1 = Activity(name="Activity 1", category="Dev")
        activity2 = Activity(name="Activity 2", category="Test")
        
        # Track activity1 twice
        self.service.start_tracking(activity1)
        time.sleep(0.02)
        self.service.stop_tracking()
        
        self.service.start_tracking(activity1)
        time.sleep(0.02)
        self.service.stop_tracking()
        
        # Track activity2 once
        self.service.start_tracking(activity2)
        time.sleep(0.01)
        self.service.stop_tracking()
        
        # Check totals
        total1 = self.service.get_total_time_for_activity(activity1.id)
        total2 = self.service.get_total_time_for_activity(activity2.id)
        
        self.assertGreater(total1.total_seconds(), 0.03)
        self.assertGreater(total2.total_seconds(), 0.005)
        self.assertGreater(total1.total_seconds(), total2.total_seconds())
    
    def test_get_total_time_includes_current_session(self):
        """Test that total time includes current active session."""
        self.service.start_tracking(self.test_activity)
        time.sleep(0.02)
        
        # Should include current session
        total = self.service.get_total_time_for_activity(self.test_activity.id)
        self.assertGreater(total.total_seconds(), 0.01)
        
        # Stop and check it's still included
        self.service.stop_tracking()
        total_after_stop = self.service.get_total_time_for_activity(self.test_activity.id)
        self.assertAlmostEqual(
            total.total_seconds(),
            total_after_stop.total_seconds(),
            delta=0.01
        )
    
    def test_get_daily_total(self):
        """Test getting daily total time."""
        # Create entries for today
        self.service.start_tracking(self.test_activity)
        time.sleep(0.02)
        self.service.stop_tracking()
        
        activity2 = Activity(name="Activity 2", category="Test")
        self.service.start_tracking(activity2)
        time.sleep(0.02)
        self.service.stop_tracking()
        
        # Get today's total
        daily_total = self.service.get_daily_total()
        self.assertGreater(daily_total.total_seconds(), 0.03)
    
    def test_get_daily_total_includes_current_session(self):
        """Test that daily total includes current session."""
        self.service.start_tracking(self.test_activity)
        time.sleep(0.02)
        
        daily_total = self.service.get_daily_total()
        self.assertGreater(daily_total.total_seconds(), 0.01)
    
    @patch('datetime.datetime')
    def test_pause_duration_calculation(self, mock_datetime):
        """Test that pause duration is correctly calculated and excluded."""
        # Mock datetime to control time progression
        base_time = datetime(2023, 1, 1, 10, 0, 0)
        mock_datetime.now.side_effect = [
            base_time,  # start_tracking
            base_time + timedelta(seconds=10),  # pause_tracking
            base_time + timedelta(seconds=20),  # resume_tracking (10 sec paused)
            base_time + timedelta(seconds=30),  # get_elapsed_time (10 sec more active)
        ]
        
        self.service.start_tracking(self.test_activity)
        self.service.pause_tracking()
        self.service.resume_tracking()
        
        elapsed = self.service.get_elapsed_time()
        
        # Should be 20 seconds total (10 + 10) minus 10 seconds paused = 10 seconds
        self.assertEqual(elapsed.total_seconds(), 20)


if __name__ == '__main__':
    unittest.main()