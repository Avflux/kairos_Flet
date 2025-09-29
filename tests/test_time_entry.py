import unittest
from datetime import datetime, timedelta
from models.time_entry import TimeEntry


class TestTimeEntry(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.start_time = datetime.now()
        self.valid_time_entry_data = {
            'activity_id': 'test-activity-123',
            'start_time': self.start_time
        }
    
    def test_time_entry_creation_valid(self):
        """Test creating a valid time entry."""
        time_entry = TimeEntry(**self.valid_time_entry_data)
        
        self.assertEqual(time_entry.activity_id, 'test-activity-123')
        self.assertEqual(time_entry.start_time, self.start_time)
        self.assertIsNone(time_entry.end_time)
        self.assertIsNone(time_entry.notes)
        self.assertIsInstance(time_entry.id, str)
        self.assertTrue(time_entry.is_active)
    
    def test_time_entry_creation_with_end_time(self):
        """Test creating time entry with end time."""
        end_time = self.start_time + timedelta(hours=1)
        time_entry = TimeEntry(
            activity_id='test-activity-123',
            start_time=self.start_time,
            end_time=end_time
        )
        
        self.assertEqual(time_entry.end_time, end_time)
        self.assertFalse(time_entry.is_active)
    
    def test_time_entry_validation_empty_activity_id(self):
        """Test validation fails with empty activity_id."""
        with self.assertRaises(ValueError) as context:
            TimeEntry(activity_id='', start_time=self.start_time)
        self.assertIn('Activity ID cannot be empty', str(context.exception))
    
    def test_time_entry_validation_invalid_start_time(self):
        """Test validation fails with invalid start_time."""
        with self.assertRaises(ValueError) as context:
            TimeEntry(activity_id='test-123', start_time='invalid')
        self.assertIn('start_time must be a datetime object', str(context.exception))
    
    def test_time_entry_validation_invalid_end_time(self):
        """Test validation fails with invalid end_time."""
        with self.assertRaises(ValueError) as context:
            TimeEntry(
                activity_id='test-123',
                start_time=self.start_time,
                end_time='invalid'
            )
        self.assertIn('end_time must be a datetime object', str(context.exception))
    
    def test_time_entry_validation_end_before_start(self):
        """Test validation fails when end_time is before start_time."""
        end_time = self.start_time - timedelta(hours=1)
        with self.assertRaises(ValueError) as context:
            TimeEntry(
                activity_id='test-123',
                start_time=self.start_time,
                end_time=end_time
            )
        self.assertIn('end_time must be after start_time', str(context.exception))
    
    def test_time_entry_validation_notes_too_long(self):
        """Test validation fails with notes too long."""
        long_notes = 'a' * 501  # 501 characters
        with self.assertRaises(ValueError) as context:
            TimeEntry(
                activity_id='test-123',
                start_time=self.start_time,
                notes=long_notes
            )
        self.assertIn('Notes cannot exceed 500 characters', str(context.exception))
    
    def test_time_entry_duration_active(self):
        """Test duration calculation for active time entry."""
        time_entry = TimeEntry(**self.valid_time_entry_data)
        duration = time_entry.duration
        
        self.assertIsInstance(duration, timedelta)
        # Duration should be positive and reasonable (less than a few seconds)
        self.assertGreater(duration.total_seconds(), 0)
        self.assertLess(duration.total_seconds(), 10)  # Should be very recent
    
    def test_time_entry_duration_completed(self):
        """Test duration calculation for completed time entry."""
        end_time = self.start_time + timedelta(hours=2, minutes=30)
        time_entry = TimeEntry(
            activity_id='test-123',
            start_time=self.start_time,
            end_time=end_time
        )
        
        duration = time_entry.duration
        expected_duration = timedelta(hours=2, minutes=30)
        
        self.assertEqual(duration, expected_duration)
    
    def test_time_entry_stop_valid(self):
        """Test stopping a time entry."""
        time_entry = TimeEntry(**self.valid_time_entry_data)
        self.assertTrue(time_entry.is_active)
        
        stop_time = self.start_time + timedelta(hours=1)
        time_entry.stop(stop_time)
        
        self.assertEqual(time_entry.end_time, stop_time)
        self.assertFalse(time_entry.is_active)
    
    def test_time_entry_stop_already_stopped(self):
        """Test stopping an already stopped time entry."""
        end_time = self.start_time + timedelta(hours=1)
        time_entry = TimeEntry(
            activity_id='test-123',
            start_time=self.start_time,
            end_time=end_time
        )
        
        with self.assertRaises(ValueError) as context:
            time_entry.stop()
        self.assertIn('already stopped', str(context.exception))
    
    def test_time_entry_stop_invalid_time(self):
        """Test stopping with invalid stop time."""
        time_entry = TimeEntry(**self.valid_time_entry_data)
        invalid_stop_time = self.start_time - timedelta(hours=1)
        
        with self.assertRaises(ValueError) as context:
            time_entry.stop(invalid_stop_time)
        self.assertIn('Stop time must be after start time', str(context.exception))
    
    def test_time_entry_add_notes_valid(self):
        """Test adding valid notes."""
        time_entry = TimeEntry(**self.valid_time_entry_data)
        notes = 'This is a test note'
        
        time_entry.add_notes(notes)
        self.assertEqual(time_entry.notes, notes)
    
    def test_time_entry_add_notes_invalid(self):
        """Test adding invalid notes."""
        time_entry = TimeEntry(**self.valid_time_entry_data)
        
        # Test non-string notes
        with self.assertRaises(ValueError):
            time_entry.add_notes(123)
        
        # Test notes too long
        with self.assertRaises(ValueError):
            time_entry.add_notes('a' * 501)
    
    def test_time_entry_duration_string(self):
        """Test formatted duration string."""
        end_time = self.start_time + timedelta(hours=2, minutes=30, seconds=45)
        time_entry = TimeEntry(
            activity_id='test-123',
            start_time=self.start_time,
            end_time=end_time
        )
        
        duration_string = time_entry.get_duration_string()
        self.assertEqual(duration_string, '02:30:45')
    
    def test_time_entry_to_dict(self):
        """Test converting time entry to dictionary."""
        time_entry = TimeEntry(**self.valid_time_entry_data)
        result = time_entry.to_dict()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['activity_id'], 'test-activity-123')
        self.assertIsNone(result['end_time'])
        self.assertIsNone(result['notes'])
        self.assertIn('id', result)
        self.assertIn('start_time', result)
        self.assertIn('duration_seconds', result)
    
    def test_time_entry_from_dict(self):
        """Test creating time entry from dictionary."""
        end_time = self.start_time + timedelta(hours=1)
        time_entry = TimeEntry(
            activity_id='test-123',
            start_time=self.start_time,
            end_time=end_time,
            notes='Test notes'
        )
        data = time_entry.to_dict()
        
        restored_time_entry = TimeEntry.from_dict(data)
        
        self.assertEqual(restored_time_entry.activity_id, time_entry.activity_id)
        self.assertEqual(restored_time_entry.start_time, time_entry.start_time)
        self.assertEqual(restored_time_entry.end_time, time_entry.end_time)
        self.assertEqual(restored_time_entry.notes, time_entry.notes)
        self.assertEqual(restored_time_entry.id, time_entry.id)


if __name__ == '__main__':
    unittest.main()