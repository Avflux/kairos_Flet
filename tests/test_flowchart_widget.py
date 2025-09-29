import unittest
from unittest.mock import Mock, MagicMock, patch
import flet as ft
from views.components.flowchart_widget import FlowchartWidget
from services.workflow_service import WorkflowService
from models.workflow_state import WorkflowState, WorkflowStage, WorkflowStageStatus


class TestFlowchartWidget(unittest.TestCase):
    """Test cases for FlowchartWidget class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.page = Mock(spec=ft.Page)
        self.workflow_service = Mock(spec=WorkflowService)
        self.on_stage_click = Mock()
        
        # Patch the _build_content method to avoid UI initialization issues during testing
        with patch.object(FlowchartWidget, '_build_content', return_value=Mock()):
            self.widget = FlowchartWidget(
                page=self.page,
                workflow_service=self.workflow_service,
                on_stage_click=self.on_stage_click
            )
    
    def test_initialization(self):
        """Test widget initialization."""
        # Test that attributes are set correctly
        self.assertEqual(self.widget.workflow_service, self.workflow_service)
        self.assertEqual(self.widget.on_stage_click, self.on_stage_click)
        self.assertIsNone(self.widget.current_workflow_id)
        self.assertIsNone(self.widget.workflow_state)
        
        # Test initialization without optional parameters
        with patch.object(FlowchartWidget, '_build_content', return_value=Mock()):
            widget = FlowchartWidget(self.page)
            self.assertIsInstance(widget.workflow_service, WorkflowService)
            self.assertIsNone(widget.on_stage_click)
    
    def test_load_workflow_success(self):
        """Test successfully loading a workflow."""
        workflow_id = "test_workflow"
        workflow_state = WorkflowState.create_default_document_workflow()
        
        self.workflow_service.get_workflow.return_value = workflow_state
        
        result = self.widget.load_workflow(workflow_id)
        
        self.assertTrue(result)
        self.assertEqual(self.widget.current_workflow_id, workflow_id)
        self.assertEqual(self.widget.workflow_state, workflow_state)
        self.workflow_service.get_workflow.assert_called_once_with(workflow_id)
    
    def test_load_workflow_failure(self):
        """Test loading a non-existent workflow."""
        workflow_id = "non_existent"
        
        self.workflow_service.get_workflow.return_value = None
        
        result = self.widget.load_workflow(workflow_id)
        
        self.assertFalse(result)
        self.assertIsNone(self.widget.current_workflow_id)
        self.assertIsNone(self.widget.workflow_state)
    
    def test_create_default_workflow_success(self):
        """Test creating a default workflow."""
        workflow_id = "default"
        project_id = "test_project"
        workflow_state = WorkflowState.create_default_document_workflow(project_id)
        
        self.workflow_service.create_workflow.return_value = workflow_state
        
        result = self.widget.create_default_workflow(workflow_id, project_id)
        
        self.assertTrue(result)
        self.assertEqual(self.widget.current_workflow_id, workflow_id)
        self.assertEqual(self.widget.workflow_state, workflow_state)
        self.workflow_service.create_workflow.assert_called_once_with(workflow_id, project_id)
    
    def test_create_default_workflow_already_exists(self):
        """Test creating a workflow that already exists."""
        workflow_id = "existing"
        workflow_state = WorkflowState.create_default_document_workflow()
        
        # First call raises ValueError (workflow exists)
        self.workflow_service.create_workflow.side_effect = ValueError("Workflow already exists")
        # Second call (load_workflow) succeeds
        self.workflow_service.get_workflow.return_value = workflow_state
        
        result = self.widget.create_default_workflow(workflow_id)
        
        self.assertTrue(result)
        self.assertEqual(self.widget.current_workflow_id, workflow_id)
        self.assertEqual(self.widget.workflow_state, workflow_state)
    
    def test_advance_to_stage_success(self):
        """Test advancing to a specific stage."""
        workflow_id = "test_workflow"
        stage_name = "Verificação"
        updated_workflow = WorkflowState.create_default_document_workflow()
        updated_workflow.advance_to_stage(stage_name)
        
        self.widget.current_workflow_id = workflow_id
        self.workflow_service.advance_workflow_stage.return_value = True
        self.workflow_service.get_workflow.return_value = updated_workflow
        
        result = self.widget.advance_to_stage(stage_name)
        
        self.assertTrue(result)
        self.assertEqual(self.widget.workflow_state, updated_workflow)
        self.workflow_service.advance_workflow_stage.assert_called_once_with(workflow_id, stage_name)
    
    def test_advance_to_stage_no_workflow(self):
        """Test advancing stage when no workflow is loaded."""
        result = self.widget.advance_to_stage("Verificação")
        
        self.assertFalse(result)
        self.workflow_service.advance_workflow_stage.assert_not_called()
    
    def test_advance_to_stage_failure(self):
        """Test advancing to an invalid stage."""
        workflow_id = "test_workflow"
        stage_name = "Invalid Stage"
        
        self.widget.current_workflow_id = workflow_id
        self.workflow_service.advance_workflow_stage.return_value = False
        
        result = self.widget.advance_to_stage(stage_name)
        
        self.assertFalse(result)
    
    def test_complete_current_stage_success(self):
        """Test completing the current stage."""
        workflow_id = "test_workflow"
        updated_workflow = WorkflowState.create_default_document_workflow()
        updated_workflow.complete_current_stage()
        
        self.widget.current_workflow_id = workflow_id
        self.workflow_service.complete_current_stage.return_value = True
        self.workflow_service.get_workflow.return_value = updated_workflow
        
        result = self.widget.complete_current_stage()
        
        self.assertTrue(result)
        self.assertEqual(self.widget.workflow_state, updated_workflow)
        self.workflow_service.complete_current_stage.assert_called_once_with(workflow_id)
    
    def test_complete_current_stage_no_workflow(self):
        """Test completing stage when no workflow is loaded."""
        result = self.widget.complete_current_stage()
        
        self.assertFalse(result)
        self.workflow_service.complete_current_stage.assert_not_called()
    
    def test_get_current_stage(self):
        """Test getting the current stage."""
        workflow_state = WorkflowState.create_default_document_workflow()
        self.widget.workflow_state = workflow_state
        
        current_stage = self.widget.get_current_stage()
        
        self.assertIsNotNone(current_stage)
        self.assertEqual(current_stage.name, "Postagem Inicial")
        
        # Test with no workflow loaded
        self.widget.workflow_state = None
        current_stage = self.widget.get_current_stage()
        self.assertIsNone(current_stage)
    
    def test_get_progress_percentage(self):
        """Test getting progress percentage."""
        workflow_state = WorkflowState.create_default_document_workflow()
        self.widget.workflow_state = workflow_state
        
        progress = self.widget.get_progress_percentage()
        self.assertEqual(progress, 0.0)
        
        # Complete a stage
        workflow_state.complete_current_stage()
        progress = self.widget.get_progress_percentage()
        self.assertGreater(progress, 0.0)
        
        # Test with no workflow loaded
        self.widget.workflow_state = None
        progress = self.widget.get_progress_percentage()
        self.assertEqual(progress, 0.0)
    
    def test_set_on_stage_click(self):
        """Test setting stage click callback."""
        new_callback = Mock()
        
        self.widget.set_on_stage_click(new_callback)
        
        self.assertEqual(self.widget.on_stage_click, new_callback)
    
    def test_handle_stage_click(self):
        """Test handling stage click events."""
        stage_name = "Verificação"
        
        self.widget._handle_stage_click(stage_name)
        
        self.on_stage_click.assert_called_once_with(stage_name)
        
        # Test with no callback set
        self.widget.on_stage_click = None
        # Should not raise an error
        self.widget._handle_stage_click(stage_name)
    
    def test_build_flowchart_no_workflow(self):
        """Test building flowchart with no workflow loaded."""
        content = self.widget._build_flowchart()
        
        self.assertIsInstance(content, ft.Container)
        # Should show "No workflow loaded" message
    
    def test_build_flowchart_with_workflow(self):
        """Test building flowchart with workflow loaded."""
        workflow_state = WorkflowState.create_default_document_workflow()
        self.widget.workflow_state = workflow_state
        
        content = self.widget._build_flowchart()
        
        self.assertIsInstance(content, ft.Container)
        # Should contain stage nodes and connectors
    
    def test_create_stage_node_different_statuses(self):
        """Test creating stage nodes with different statuses."""
        # Test completed stage
        completed_stage = WorkflowStage("Test Stage", WorkflowStageStatus.COMPLETED)
        node = self.widget._create_stage_node(completed_stage)
        self.assertIsInstance(node, ft.Container)
        
        # Test in-progress stage
        in_progress_stage = WorkflowStage("Test Stage", WorkflowStageStatus.IN_PROGRESS)
        node = self.widget._create_stage_node(in_progress_stage)
        self.assertIsInstance(node, ft.Container)
        
        # Test blocked stage
        blocked_stage = WorkflowStage("Test Stage", WorkflowStageStatus.BLOCKED)
        node = self.widget._create_stage_node(blocked_stage)
        self.assertIsInstance(node, ft.Container)
        
        # Test pending stage
        pending_stage = WorkflowStage("Test Stage", WorkflowStageStatus.PENDING)
        node = self.widget._create_stage_node(pending_stage)
        self.assertIsInstance(node, ft.Container)
    
    def test_create_connector(self):
        """Test creating connector arrows."""
        from_stage = WorkflowStage("Test Stage", WorkflowStageStatus.COMPLETED)
        to_stage = WorkflowStage("Next Stage", WorkflowStageStatus.PENDING)
        
        connector = self.widget._create_connector(from_stage, to_stage)
        
        self.assertIsInstance(connector, ft.Container)
    
    @patch('views.components.flowchart_widget.FlowchartWidget._refresh_display')
    def test_refresh_display_called(self, mock_refresh):
        """Test that refresh display is called when needed."""
        workflow_id = "test_workflow"
        workflow_state = WorkflowState.create_default_document_workflow()
        
        self.workflow_service.get_workflow.return_value = workflow_state
        
        self.widget.load_workflow(workflow_id)
        
        mock_refresh.assert_called_once()
    
    def test_widget_properties(self):
        """Test widget container properties."""
        # Test that widget has proper styling
        self.assertIsNotNone(self.widget.padding)
        self.assertIsNotNone(self.widget.border_radius)
        self.assertIsNotNone(self.widget.bgcolor)
        self.assertIsNotNone(self.widget.border)
    
    def test_update_responsive_layout(self):
        """Test responsive layout updates."""
        workflow_state = WorkflowState.create_default_document_workflow()
        self.widget.workflow_state = workflow_state
        
        # Test with specific container width
        container_width = 1000
        self.widget.update_responsive_layout(container_width)
        
        # Should have set responsive node width
        self.assertTrue(hasattr(self.widget, '_responsive_node_width'))
        self.assertIsInstance(self.widget._responsive_node_width, int)
        
        # Test with no workflow loaded
        self.widget.workflow_state = None
        self.widget.update_responsive_layout(container_width)
        # Should not raise an error
    
    def test_get_stage_details(self):
        """Test getting stage details."""
        workflow_state = WorkflowState.create_default_document_workflow()
        self.widget.workflow_state = workflow_state
        
        # Test getting details for existing stage
        details = self.widget.get_stage_details("Postagem Inicial")
        self.assertIsNotNone(details)
        self.assertEqual(details['name'], "Postagem Inicial")
        self.assertEqual(details['status'], "in_progress")
        self.assertTrue(details['is_current'])
        
        # Test getting details for non-existent stage
        details = self.widget.get_stage_details("Non-existent Stage")
        self.assertIsNone(details)
        
        # Test with no workflow loaded
        self.widget.workflow_state = None
        details = self.widget.get_stage_details("Postagem Inicial")
        self.assertIsNone(details)
    
    def test_create_progress_indicator(self):
        """Test creating progress indicator."""
        workflow_state = WorkflowState.create_default_document_workflow()
        self.widget.workflow_state = workflow_state
        
        progress_indicator = self.widget._create_progress_indicator()
        self.assertIsInstance(progress_indicator, ft.Container)
        
        # Test with no workflow loaded
        self.widget.workflow_state = None
        progress_indicator = self.widget._create_progress_indicator()
        self.assertIsInstance(progress_indicator, ft.Container)


if __name__ == '__main__':
    unittest.main()