import unittest
from datetime import datetime
from models.activity import Activity


class TestActivity(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.valid_activity_data = {
            'name': 'Test Activity',
            'category': 'Development'
        }
    
    def test_activity_creation_valid(self):
        """Test creating a valid activity."""
        activity = Activity(**self.valid_activity_data)
        
        self.assertEqual(activity.name, 'Test Activity')
        self.assertEqual(activity.category, 'Development')
        self.assertIsNone(activity.description)
        self.assertIsInstance(activity.created_at, datetime)
        self.assertIsInstance(activity.id, str)
    
    def test_activity_creation_with_description(self):
        """Test creating activity with description."""
        activity = Activity(
            name='Test Activity',
            category='Development',
            description='This is a test activity'
        )
        
        self.assertEqual(activity.description, 'This is a test activity')
    
    def test_activity_validation_empty_name(self):
        """Test validation fails with empty name."""
        with self.assertRaises(ValueError) as context:
            Activity(name='', category='Development')
        self.assertIn('name cannot be empty', str(context.exception))
    
    def test_activity_validation_whitespace_name(self):
        """Test validation fails with whitespace-only name."""
        with self.assertRaises(ValueError) as context:
            Activity(name='   ', category='Development')
        self.assertIn('name cannot be empty', str(context.exception))
    
    def test_activity_validation_empty_category(self):
        """Test validation fails with empty category."""
        with self.assertRaises(ValueError) as context:
            Activity(name='Test Activity', category='')
        self.assertIn('category cannot be empty', str(context.exception))
    
    def test_activity_validation_name_too_long(self):
        """Test validation fails with name too long."""
        long_name = 'a' * 101  # 101 characters
        with self.assertRaises(ValueError) as context:
            Activity(name=long_name, category='Development')
        self.assertIn('cannot exceed 100 characters', str(context.exception))
    
    def test_activity_validation_category_too_long(self):
        """Test validation fails with category too long."""
        long_category = 'a' * 51  # 51 characters
        with self.assertRaises(ValueError) as context:
            Activity(name='Test Activity', category=long_category)
        self.assertIn('cannot exceed 50 characters', str(context.exception))
    
    def test_activity_validation_invalid_description_type(self):
        """Test validation fails with invalid description type."""
        with self.assertRaises(ValueError) as context:
            Activity(
                name='Test Activity',
                category='Development',
                description=123  # Should be string or None
            )
        self.assertIn('description must be a string or None', str(context.exception))
    
    def test_activity_update_name_valid(self):
        """Test updating activity name with valid value."""
        activity = Activity(**self.valid_activity_data)
        activity.update_name('Updated Activity')
        
        self.assertEqual(activity.name, 'Updated Activity')
    
    def test_activity_update_name_invalid(self):
        """Test updating activity name with invalid value."""
        activity = Activity(**self.valid_activity_data)
        
        with self.assertRaises(ValueError):
            activity.update_name('')
        
        with self.assertRaises(ValueError):
            activity.update_name('a' * 101)
    
    def test_activity_update_category_valid(self):
        """Test updating activity category with valid value."""
        activity = Activity(**self.valid_activity_data)
        activity.update_category('Testing')
        
        self.assertEqual(activity.category, 'Testing')
    
    def test_activity_update_category_invalid(self):
        """Test updating activity category with invalid value."""
        activity = Activity(**self.valid_activity_data)
        
        with self.assertRaises(ValueError):
            activity.update_category('')
        
        with self.assertRaises(ValueError):
            activity.update_category('a' * 51)
    
    def test_activity_update_description_valid(self):
        """Test updating activity description with valid value."""
        activity = Activity(**self.valid_activity_data)
        activity.update_description('New description')
        
        self.assertEqual(activity.description, 'New description')
        
        # Test setting to None
        activity.update_description(None)
        self.assertIsNone(activity.description)
    
    def test_activity_update_description_invalid(self):
        """Test updating activity description with invalid value."""
        activity = Activity(**self.valid_activity_data)
        
        with self.assertRaises(ValueError):
            activity.update_description(123)
    
    def test_activity_to_dict(self):
        """Test converting activity to dictionary."""
        activity = Activity(**self.valid_activity_data)
        result = activity.to_dict()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['name'], 'Test Activity')
        self.assertEqual(result['category'], 'Development')
        self.assertIsNone(result['description'])
        self.assertIn('id', result)
        self.assertIn('created_at', result)
    
    def test_activity_from_dict(self):
        """Test creating activity from dictionary."""
        activity = Activity(**self.valid_activity_data)
        data = activity.to_dict()
        
        restored_activity = Activity.from_dict(data)
        
        self.assertEqual(restored_activity.name, activity.name)
        self.assertEqual(restored_activity.category, activity.category)
        self.assertEqual(restored_activity.description, activity.description)
        self.assertEqual(restored_activity.id, activity.id)
    
    def test_activity_name_trimming(self):
        """Test that names are properly trimmed."""
        activity = Activity(name='  Test Activity  ', category='Development')
        self.assertEqual(activity.name, '  Test Activity  ')  # Original behavior preserved
        
        # But update methods should trim
        activity.update_name('  Updated Name  ')
        self.assertEqual(activity.name, 'Updated Name')


if __name__ == '__main__':
    unittest.main()