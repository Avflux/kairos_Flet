import unittest
from unittest.mock import Mock, patch, MagicMock
import flet as ft
from views.components.modern_sidebar import ModernSidebar, SidebarSection, NavItem


class TestNavItem(unittest.TestCase):
    """Test cases for NavItem dataclass"""
    
    def test_nav_item_creation(self):
        """Test creating a NavItem with default values"""
        item = NavItem(icon="home", text="Home")
        
        self.assertEqual(item.icon, "home")
        self.assertEqual(item.text, "Home")
        self.assertIsNone(item.route)
        self.assertFalse(item.is_selected)
        self.assertFalse(item.is_button)
        self.assertFalse(item.is_link)
        self.assertIsNone(item.on_click)
        self.assertIsNone(item.badge_count)
    
    def test_nav_item_with_all_parameters(self):
        """Test creating a NavItem with all parameters"""
        on_click_mock = Mock()
        
        item = NavItem(
            icon="settings",
            text="Settings",
            route="/settings",
            is_selected=True,
            is_button=True,
            is_link=True,
            on_click=on_click_mock,
            badge_count=5
        )
        
        self.assertEqual(item.icon, "settings")
        self.assertEqual(item.text, "Settings")
        self.assertEqual(item.route, "/settings")
        self.assertTrue(item.is_selected)
        self.assertTrue(item.is_button)
        self.assertTrue(item.is_link)
        self.assertEqual(item.on_click, on_click_mock)
        self.assertEqual(item.badge_count, 5)


class TestSidebarSection(unittest.TestCase):
    """Test cases for SidebarSection component"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_page = Mock(spec=ft.Page)
        self.test_items = [
            NavItem(icon="home", text="Home", route="/home"),
            NavItem(icon="settings", text="Settings", route="/settings", is_selected=True),
            NavItem(icon="help", text="Help", route="/help", badge_count=3)
        ]
    
    def test_sidebar_section_creation(self):
        """Test creating a SidebarSection"""
        section = SidebarSection("Test Section", self.test_items)
        
        self.assertEqual(section.title, "Test Section")
        self.assertEqual(len(section.items), 3)
        self.assertTrue(section.expanded)
        self.assertTrue(section._sidebar_expanded)
    
    def test_sidebar_section_with_custom_parameters(self):
        """Test creating a SidebarSection with custom parameters"""
        on_toggle_mock = Mock()
        
        section = SidebarSection(
            "Custom Section",
            self.test_items,
            expanded=False,
            on_toggle=on_toggle_mock
        )
        
        self.assertEqual(section.title, "Custom Section")
        self.assertFalse(section.expanded)
        self.assertEqual(section.on_toggle, on_toggle_mock)
    
    def test_toggle_section(self):
        """Test toggling section expanded state"""
        on_toggle_mock = Mock()
        section = SidebarSection("Test Section", self.test_items, on_toggle=on_toggle_mock)
        
        # Mock the event object
        mock_event = Mock()
        
        # Initial state should be expanded
        self.assertTrue(section.expanded)
        
        # Toggle to collapsed
        section._toggle_section(mock_event)
        self.assertFalse(section.expanded)
        on_toggle_mock.assert_called_once_with("Test Section", False)
        
        # Toggle back to expanded
        section._toggle_section(mock_event)
        self.assertTrue(section.expanded)
        self.assertEqual(on_toggle_mock.call_count, 2)
    
    def test_update_sidebar_expansion(self):
        """Test updating sidebar expansion state"""
        section = SidebarSection("Test Section", self.test_items)
        
        # Test collapsing
        section.update_sidebar_expansion(False)
        self.assertFalse(section._sidebar_expanded)
        self.assertFalse(section.title_text.visible)
        
        # Test expanding
        section.update_sidebar_expansion(True)
        self.assertTrue(section._sidebar_expanded)
        self.assertTrue(section.title_text.visible)
    
    def test_set_selected_item(self):
        """Test setting selected navigation item"""
        section = SidebarSection("Test Section", self.test_items)
        
        # Initially, "Settings" should be selected
        selected_items = [item for item in section.items if item.is_selected]
        self.assertEqual(len(selected_items), 1)
        self.assertEqual(selected_items[0].text, "Settings")
        
        # Change selection to "Home"
        section.set_selected_item("Home")
        
        # Check that only "Home" is now selected
        for item in section.items:
            if item.text == "Home":
                self.assertTrue(item.is_selected)
            else:
                self.assertFalse(item.is_selected)


class TestModernSidebar(unittest.TestCase):
    """Test cases for ModernSidebar component"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_page = Mock(spec=ft.Page)
        self.on_navigation_mock = Mock()
    
    def test_modern_sidebar_creation(self):
        """Test creating a ModernSidebar"""
        sidebar = ModernSidebar(self.mock_page, self.on_navigation_mock)
        
        self.assertEqual(sidebar.page, self.mock_page)
        self.assertEqual(sidebar.on_navigation, self.on_navigation_mock)
        self.assertTrue(sidebar.expanded)
        self.assertEqual(sidebar.width, 280)
        
        # Check that all three sections are created
        self.assertIn("time_management", sidebar.sections)
        self.assertIn("project_workflows", sidebar.sections)
        self.assertIn("educational_videos", sidebar.sections)
    
    def test_sidebar_sections_content(self):
        """Test that sidebar sections have correct content"""
        sidebar = ModernSidebar(self.mock_page)
        
        # Test Time Management section
        time_section = sidebar.sections["time_management"]
        self.assertEqual(time_section.title, "Time Management")
        self.assertEqual(len(time_section.items), 4)
        
        # Test Project Workflows section
        project_section = sidebar.sections["project_workflows"]
        self.assertEqual(project_section.title, "Project Workflows")
        self.assertEqual(len(project_section.items), 4)
        
        # Test Educational Videos section
        videos_section = sidebar.sections["educational_videos"]
        self.assertEqual(videos_section.title, "Educational Videos")
        self.assertEqual(len(videos_section.items), 4)
    
    def test_toggle_sidebar(self):
        """Test toggling sidebar expanded/collapsed state"""
        sidebar = ModernSidebar(self.mock_page)
        
        # Mock the event object
        mock_event = Mock()
        
        # Initial state should be expanded
        self.assertTrue(sidebar.expanded)
        self.assertEqual(sidebar.width, 280)
        
        # Toggle to collapsed
        sidebar._toggle_sidebar(mock_event)
        self.assertFalse(sidebar.expanded)
        self.assertEqual(sidebar.width, 80)
        
        # Toggle back to expanded
        sidebar._toggle_sidebar(mock_event)
        self.assertTrue(sidebar.expanded)
        self.assertEqual(sidebar.width, 280)
    
    def test_handle_navigation(self):
        """Test navigation handling"""
        sidebar = ModernSidebar(self.mock_page, self.on_navigation_mock)
        
        # Test navigation call
        sidebar._handle_navigation("time-tracker")
        
        # Check that callback was called
        self.on_navigation_mock.assert_called_once_with("time-tracker")
    
    def test_get_selected_route(self):
        """Test getting the currently selected route"""
        sidebar = ModernSidebar(self.mock_page)
        
        # Should have a default selected route (workflow-overview)
        selected_route = sidebar.get_selected_route()
        self.assertEqual(selected_route, "/workflow-overview")
    
    def test_set_selected_route(self):
        """Test setting the selected route programmatically"""
        sidebar = ModernSidebar(self.mock_page)
        
        # Set a new selected route
        sidebar.set_selected_route("/time-tracker")
        
        # Check that the route is now selected
        selected_route = sidebar.get_selected_route()
        self.assertEqual(selected_route, "/time-tracker")
        
        # Verify that only one item is selected across all sections
        selected_count = 0
        for section in sidebar.sections.values():
            for item in section.items:
                if item.is_selected:
                    selected_count += 1
        
        self.assertEqual(selected_count, 1)
    
    def test_navigation_items_have_callbacks(self):
        """Test that navigation items have proper click callbacks"""
        sidebar = ModernSidebar(self.mock_page, self.on_navigation_mock)
        
        # Check that all navigation items have on_click callbacks
        for section in sidebar.sections.values():
            for item in section.items:
                self.assertIsNotNone(item.on_click)
    
    def test_badge_counts_in_project_workflows(self):
        """Test that project workflow items have appropriate badge counts"""
        sidebar = ModernSidebar(self.mock_page)
        
        project_section = sidebar.sections["project_workflows"]
        
        # Find items with badges
        active_projects = next(item for item in project_section.items if item.text == "Active Projects")
        approval_queue = next(item for item in project_section.items if item.text == "Approval Queue")
        
        self.assertEqual(active_projects.badge_count, 3)
        self.assertEqual(approval_queue.badge_count, 7)
    
    def test_external_link_items(self):
        """Test that external link items are properly marked"""
        sidebar = ModernSidebar(self.mock_page)
        
        videos_section = sidebar.sections["educational_videos"]
        external_resources = next(item for item in videos_section.items if item.text == "External Resources")
        
        self.assertTrue(external_resources.is_link)
    
    def test_section_toggle_callback(self):
        """Test section toggle callback handling"""
        sidebar = ModernSidebar(self.mock_page)
        
        # Get a section and test its toggle callback
        time_section = sidebar.sections["time_management"]
        
        # The callback should not raise an error
        try:
            sidebar._handle_section_toggle("Time Management", False)
        except Exception as e:
            self.fail(f"Section toggle callback raised an exception: {e}")
    
    def test_default_section_expansion_states(self):
        """Test that sections have correct default expansion states"""
        sidebar = ModernSidebar(self.mock_page)
        
        # Time Management and Project Workflows should be expanded by default
        self.assertTrue(sidebar.sections["time_management"].expanded)
        self.assertTrue(sidebar.sections["project_workflows"].expanded)
        
        # Educational Videos should be collapsed by default
        self.assertFalse(sidebar.sections["educational_videos"].expanded)


class TestSidebarIntegration(unittest.TestCase):
    """Integration tests for sidebar components"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_page = Mock(spec=ft.Page)
        self.navigation_calls = []
        
        def track_navigation(route):
            self.navigation_calls.append(route)
        
        self.sidebar = ModernSidebar(self.mock_page, track_navigation)
    
    def test_navigation_flow(self):
        """Test complete navigation flow"""
        # Simulate clicking on different navigation items
        self.sidebar._handle_navigation("time-tracker")
        self.sidebar._handle_navigation("workflow-overview")
        self.sidebar._handle_navigation("video-library")
        
        # Check that all navigation calls were tracked
        expected_calls = ["time-tracker", "workflow-overview", "video-library"]
        self.assertEqual(self.navigation_calls, expected_calls)
    
    def test_sidebar_state_consistency(self):
        """Test that sidebar state remains consistent during operations"""
        # Toggle sidebar multiple times
        mock_event = Mock()
        
        original_width = self.sidebar.width
        self.sidebar._toggle_sidebar(mock_event)
        collapsed_width = self.sidebar.width
        self.sidebar._toggle_sidebar(mock_event)
        final_width = self.sidebar.width
        
        # Should return to original state
        self.assertEqual(original_width, final_width)
        self.assertNotEqual(original_width, collapsed_width)
    
    def test_section_and_sidebar_interaction(self):
        """Test interaction between section expansion and sidebar expansion"""
        # Get a section
        time_section = self.sidebar.sections["time_management"]
        
        # Collapse sidebar
        mock_event = Mock()
        self.sidebar._toggle_sidebar(mock_event)
        
        # Section should update its text visibility
        self.assertFalse(time_section._sidebar_expanded)
        self.assertFalse(time_section.title_text.visible)
        
        # Expand sidebar again
        self.sidebar._toggle_sidebar(mock_event)
        
        # Section should restore text visibility
        self.assertTrue(time_section._sidebar_expanded)
        self.assertTrue(time_section.title_text.visible)


if __name__ == '__main__':
    unittest.main()