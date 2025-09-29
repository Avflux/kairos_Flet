import unittest
from unittest.mock import Mock, patch, MagicMock
import flet as ft
from views.main_view import MainView


class TestMainViewIntegration(unittest.TestCase):
    """Integration tests for MainView with enhanced components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_page = Mock(spec=ft.Page)
        self.mock_page.padding = 10
        self.mock_page.update = Mock()
        self.mock_page.show_snack_bar = Mock()
    
    @patch('views.main_view.TopSidebarContainer')
    @patch('views.main_view.ModernSidebar')
    @patch('views.main_view.TimeTrackingService')
    @patch('views.main_view.WorkflowService')
    @patch('views.main_view.NotificationService')
    def test_enhanced_components_initialization(
        self, 
        mock_notification_service_cls,
        mock_workflow_service_cls,
        mock_time_tracking_service_cls,
        mock_modern_sidebar_cls,
        mock_top_sidebar_container_cls
    ):
        """Test that enhanced components are properly initialized."""
        # Set up mock instances
        mock_time_tracking_service = Mock()
        mock_workflow_service = Mock()
        mock_notification_service = Mock()
        mock_top_sidebar_container = Mock()
        mock_modern_sidebar = Mock()
        mock_modern_sidebar.width = 280
        
        mock_time_tracking_service_cls.return_value = mock_time_tracking_service
        mock_workflow_service_cls.return_value = mock_workflow_service
        mock_notification_service_cls.return_value = mock_notification_service
        mock_top_sidebar_container_cls.return_value = mock_top_sidebar_container
        mock_modern_sidebar_cls.return_value = mock_modern_sidebar
        
        # Create MainView
        main_view = MainView(self.mock_page)
        
        # Verify services are initialized
        self.assertIsNotNone(main_view.time_tracking_service)
        self.assertIsNotNone(main_view.workflow_service)
        self.assertIsNotNone(main_view.notification_service)
        
        # Verify enhanced components are created
        self.assertTrue(main_view.use_enhanced_components)
        self.assertIsNotNone(main_view.top_sidebar_container)
        self.assertIsNotNone(main_view.modern_sidebar)
        
        # Verify TopSidebarContainer was initialized with correct parameters
        mock_top_sidebar_container_cls.assert_called_once_with(
            page=self.mock_page,
            time_tracking_service=mock_time_tracking_service,
            workflow_service=mock_workflow_service,
            notification_service=mock_notification_service
        )
        
        # Verify ModernSidebar was initialized with correct parameters
        mock_modern_sidebar_cls.assert_called_once_with(
            page=self.mock_page,
            on_navigation=main_view._handle_navigation
        )
    
    @patch('views.main_view.TopSidebarContainer')
    @patch('views.main_view.ModernSidebar')
    def test_sidebar_toggle_functionality_with_enhanced_components(
        self, 
        mock_modern_sidebar_cls,
        mock_top_sidebar_container_cls
    ):
        """Test sidebar toggle functionality with enhanced components."""
        # Set up mock instances
        mock_top_sidebar_container = Mock()
        mock_modern_sidebar = Mock()
        mock_modern_sidebar.width = 280
        mock_modern_sidebar._toggle_sidebar = Mock()
        
        mock_top_sidebar_container_cls.return_value = mock_top_sidebar_container
        mock_modern_sidebar_cls.return_value = mock_modern_sidebar
        
        # Create MainView
        main_view = MainView(self.mock_page)
        
        # Test sidebar toggle
        mock_event = Mock()
        main_view.toggle_sidebar(mock_event)
        
        # Verify modern sidebar toggle was called
        mock_modern_sidebar._toggle_sidebar.assert_called_once_with(mock_event)
        
        # Verify top sidebar container layout update was called
        mock_top_sidebar_container.update_layout.assert_called_once_with(False)
        
        # Verify page update was called
        self.mock_page.update.assert_called()
    
    def test_fallback_to_original_components(self):
        """Test fallback to original components when enhanced components are disabled."""
        # Create MainView with enhanced components disabled
        main_view = MainView(self.mock_page)
        main_view.set_enhanced_components_enabled(False)
        
        # Verify enhanced components are not used
        self.assertFalse(main_view.use_enhanced_components)
    
    @patch('views.main_view.TopSidebarContainer')
    @patch('views.main_view.ModernSidebar')
    def test_navigation_handling(
        self, 
        mock_modern_sidebar_cls,
        mock_top_sidebar_container_cls
    ):
        """Test navigation handling from modern sidebar."""
        # Set up mock instances
        mock_top_sidebar_container = Mock()
        mock_modern_sidebar = Mock()
        mock_modern_sidebar.width = 280
        
        mock_top_sidebar_container_cls.return_value = mock_top_sidebar_container
        mock_modern_sidebar_cls.return_value = mock_modern_sidebar
        
        # Create MainView
        main_view = MainView(self.mock_page)
        
        # Test navigation
        test_route = "time-tracker"
        main_view._handle_navigation(test_route)
        
        # Verify main content was updated
        self.assertIsNotNone(main_view.main_content.content)
        
        # Verify snack bar was shown
        self.mock_page.show_snack_bar.assert_called_once()
        
        # Verify the snack bar content
        call_args = self.mock_page.show_snack_bar.call_args[0][0]
        self.assertIsInstance(call_args, ft.SnackBar)
    
    @patch('views.main_view.TopSidebarContainer')
    @patch('views.main_view.ModernSidebar')
    def test_main_content_updates_for_different_routes(
        self, 
        mock_modern_sidebar_cls,
        mock_top_sidebar_container_cls
    ):
        """Test main content updates for different navigation routes."""
        # Set up mock instances
        mock_top_sidebar_container = Mock()
        mock_modern_sidebar = Mock()
        mock_modern_sidebar.width = 280
        
        mock_top_sidebar_container_cls.return_value = mock_top_sidebar_container
        mock_modern_sidebar_cls.return_value = mock_modern_sidebar
        
        # Create MainView
        main_view = MainView(self.mock_page)
        
        # Test different routes
        test_routes = [
            "time-tracker",
            "workflow-overview", 
            "video-library",
            "settings",
            "unknown-route"
        ]
        
        for route in test_routes:
            main_view._update_main_content(route)
            
            # Verify content was updated
            self.assertIsNotNone(main_view.main_content.content)
            self.assertIsInstance(main_view.main_content.content, ft.Column)
            
            # Verify content has expected structure
            content_column = main_view.main_content.content
            self.assertGreaterEqual(len(content_column.controls), 1)
            self.assertIsInstance(content_column.controls[0], ft.Text)
    
    @patch('views.main_view.TopSidebarContainer')
    @patch('views.main_view.ModernSidebar')
    def test_enhanced_component_access_methods(
        self, 
        mock_modern_sidebar_cls,
        mock_top_sidebar_container_cls
    ):
        """Test methods for accessing enhanced components."""
        # Set up mock instances
        mock_top_sidebar_container = Mock()
        mock_modern_sidebar = Mock()
        mock_modern_sidebar.width = 280
        
        mock_top_sidebar_container_cls.return_value = mock_top_sidebar_container
        mock_modern_sidebar_cls.return_value = mock_modern_sidebar
        
        # Create MainView
        main_view = MainView(self.mock_page)
        
        # Test get_enhanced_components
        components = main_view.get_enhanced_components()
        
        self.assertIn('top_sidebar_container', components)
        self.assertIn('modern_sidebar', components)
        self.assertIn('time_tracking_service', components)
        self.assertIn('workflow_service', components)
        self.assertIn('notification_service', components)
        
        self.assertEqual(components['top_sidebar_container'], mock_top_sidebar_container)
        self.assertEqual(components['modern_sidebar'], mock_modern_sidebar)
    
    @patch('views.main_view.TopSidebarContainer')
    @patch('views.main_view.ModernSidebar')
    def test_add_test_notification(
        self, 
        mock_modern_sidebar_cls,
        mock_top_sidebar_container_cls
    ):
        """Test adding test notifications through MainView."""
        # Set up mock instances
        mock_top_sidebar_container = Mock()
        mock_modern_sidebar = Mock()
        mock_modern_sidebar.width = 280
        
        mock_top_sidebar_container_cls.return_value = mock_top_sidebar_container
        mock_modern_sidebar_cls.return_value = mock_modern_sidebar
        
        # Create MainView
        main_view = MainView(self.mock_page)
        
        # Test add_test_notification
        main_view.add_test_notification()
        
        # Verify method was called on top sidebar container
        mock_top_sidebar_container.add_test_notification.assert_called_once()
    
    @patch('views.main_view.TopSidebarContainer')
    @patch('views.main_view.ModernSidebar')
    def test_advance_workflow_stage(
        self, 
        mock_modern_sidebar_cls,
        mock_top_sidebar_container_cls
    ):
        """Test advancing workflow stages through MainView."""
        # Set up mock instances
        mock_top_sidebar_container = Mock()
        mock_modern_sidebar = Mock()
        mock_modern_sidebar.width = 280
        mock_top_sidebar_container.advance_workflow_stage.return_value = True
        
        mock_top_sidebar_container_cls.return_value = mock_top_sidebar_container
        mock_modern_sidebar_cls.return_value = mock_modern_sidebar
        
        # Create MainView
        main_view = MainView(self.mock_page)
        
        # Test advance_workflow_stage
        result = main_view.advance_workflow_stage("Verificação")
        
        # Verify method was called and returned expected result
        mock_top_sidebar_container.advance_workflow_stage.assert_called_once_with("Verificação")
        self.assertTrue(result)
    
    @patch('views.main_view.TopSidebarContainer')
    @patch('views.main_view.ModernSidebar')
    def test_layout_structure_with_enhanced_components(
        self, 
        mock_modern_sidebar_cls,
        mock_top_sidebar_container_cls
    ):
        """Test that the layout structure is correct with enhanced components."""
        # Set up mock instances
        mock_top_sidebar_container = Mock()
        mock_modern_sidebar = Mock()
        mock_modern_sidebar.width = 280
        
        mock_top_sidebar_container_cls.return_value = mock_top_sidebar_container
        mock_modern_sidebar_cls.return_value = mock_modern_sidebar
        
        # Create MainView
        main_view = MainView(self.mock_page)
        
        # Verify layout structure
        self.assertIsNotNone(main_view.controls)
        self.assertEqual(len(main_view.controls), 1)
        
        # Verify main row structure
        main_row = main_view.controls[0]
        self.assertIsInstance(main_row, ft.Row)
        self.assertEqual(len(main_row.controls), 2)
        
        # Verify sidebar container
        self.assertEqual(main_row.controls[0], main_view.animating_sidebar_container)
        self.assertEqual(main_view.animating_sidebar_container.width, 280)  # Enhanced width
        
        # Verify top sidebar container is used
        self.assertEqual(main_view.top_bar_left, mock_top_sidebar_container)
    
    def test_compatibility_with_existing_theme_system(self):
        """Test that enhanced components maintain compatibility with existing theme system."""
        # Create MainView
        main_view = MainView(self.mock_page)
        
        # Verify page padding is preserved
        self.assertEqual(self.mock_page.padding, 10)
        
        # Verify route is set correctly
        self.assertEqual(main_view.route, "/")
        
        # Verify basic properties are maintained
        self.assertIsNotNone(main_view.page)
        self.assertIsInstance(main_view.sidebar_expanded, bool)


class TestMainViewFallbackBehavior(unittest.TestCase):
    """Test MainView fallback behavior when enhanced components are disabled."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_page = Mock(spec=ft.Page)
        self.mock_page.padding = 10
        self.mock_page.update = Mock()
    
    def test_original_sidebar_behavior_when_enhanced_disabled(self):
        """Test that original sidebar behavior works when enhanced components are disabled."""
        # Create MainView
        main_view = MainView(self.mock_page)
        main_view.use_enhanced_components = False
        
        # Manually create original components for testing
        main_view.sidebar_texts = [Mock(), Mock()]
        main_view.nav_items = {
            "studio_header": Mock(),
            "studio_items": Mock()
        }
        
        # Test original toggle behavior
        main_view.sidebar_expanded = True
        mock_event = Mock()
        main_view.toggle_sidebar(mock_event)
        
        # Verify original behavior
        self.assertFalse(main_view.sidebar_expanded)
        self.assertEqual(main_view.animating_sidebar_container.width, 80)
        
        # Verify text visibility was updated
        for text_control in main_view.sidebar_texts:
            self.assertFalse(text_control.visible)
    
    def test_original_section_toggle_when_enhanced_disabled(self):
        """Test original section toggle behavior when enhanced components are disabled."""
        # Create MainView
        main_view = MainView(self.mock_page)
        main_view.use_enhanced_components = False
        
        # Set up mock nav items
        mock_header = Mock()
        mock_header.controls = [Mock(), Mock()]
        mock_header.controls[1].icon = 'arrow_drop_down'
        
        mock_items = Mock()
        mock_items.visible = False
        
        main_view.nav_items = {
            "test_header": mock_header,
            "test_items": mock_items
        }
        
        # Test section toggle
        mock_event = Mock()
        mock_event.control.data = "test"
        main_view.toggle_section(mock_event)
        
        # Verify section was toggled
        self.assertTrue(mock_items.visible)
        self.assertEqual(mock_header.controls[1].icon, 'arrow_drop_up')


if __name__ == '__main__':
    unittest.main()