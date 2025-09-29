import unittest
from unittest.mock import Mock, patch
import flet as ft
from views.components.flowchart_widget import FlowchartWidget
from services.workflow_service import WorkflowService
from models.workflow_state import WorkflowState, WorkflowStage, WorkflowStageStatus


class TestEnhancedFlowchartFeatures(unittest.TestCase):
    """Test cases for enhanced flowchart widget features."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.page = Mock(spec=ft.Page)
        self.workflow_service = Mock(spec=WorkflowService)
        
        # Patch the _build_content method to avoid UI initialization issues during testing
        with patch.object(FlowchartWidget, '_build_content', return_value=Mock()):
            self.widget = FlowchartWidget(
                page=self.page,
                workflow_service=self.workflow_service
            )
    
    def test_modern_card_styling(self):
        """Test that stage nodes use modern card-based styling."""
        stage = WorkflowStage("Test Stage", WorkflowStageStatus.IN_PROGRESS)
        
        node = self.widget._create_stage_node(stage)
        
        # Verify it's a container with modern styling
        self.assertIsInstance(node, ft.Container)
        self.assertEqual(node.border_radius, 12)
        self.assertIsNotNone(node.shadow)
        self.assertEqual(node.height, 70)
        
        # Verify hover effect is set
        self.assertIsNotNone(node.on_hover)
    
    def test_responsive_node_width(self):
        """Test responsive node width calculation."""
        stage = WorkflowStage("Test Stage", WorkflowStageStatus.PENDING)
        
        # Test with custom width
        custom_width = 100
        node = self.widget._create_stage_node(stage, custom_width)
        
        self.assertEqual(node.width, custom_width)
    
    def test_progress_indicator_creation(self):
        """Test progress indicator with workflow data."""
        workflow_state = WorkflowState.create_default_document_workflow()
        # Complete a few stages for testing
        workflow_state.stages[0].mark_completed()
        workflow_state.stages[1].mark_completed()
        
        self.widget.workflow_state = workflow_state
        
        progress_indicator = self.widget._create_progress_indicator()
        
        self.assertIsInstance(progress_indicator, ft.Container)
        self.assertEqual(progress_indicator.height, 20)
    
    def test_progress_indicator_no_workflow(self):
        """Test progress indicator with no workflow."""
        self.widget.workflow_state = None
        
        progress_indicator = self.widget._create_progress_indicator()
        
        self.assertIsInstance(progress_indicator, ft.Container)
        self.assertEqual(progress_indicator.height, 0)
    
    def test_enhanced_connector_styling(self):
        """Test enhanced connector with progress indication."""
        completed_stage = WorkflowStage("Completed", WorkflowStageStatus.COMPLETED)
        next_stage = WorkflowStage("Next", WorkflowStageStatus.PENDING)
        
        connector = self.widget._create_connector(completed_stage, next_stage)
        
        self.assertIsInstance(connector, ft.Container)
        self.assertEqual(connector.width, 30)
        self.assertEqual(connector.height, 70)
    
    def test_stage_status_colors(self):
        """Test different colors for different stage statuses."""
        statuses = [
            WorkflowStageStatus.COMPLETED,
            WorkflowStageStatus.IN_PROGRESS,
            WorkflowStageStatus.BLOCKED,
            WorkflowStageStatus.PENDING
        ]
        
        for status in statuses:
            stage = WorkflowStage("Test Stage", status)
            node = self.widget._create_stage_node(stage)
            
            # Verify node is created with appropriate styling
            self.assertIsInstance(node, ft.Container)
            self.assertIsNotNone(node.bgcolor)
            self.assertIsNotNone(node.border)
    
    def test_responsive_layout_update(self):
        """Test responsive layout functionality."""
        workflow_state = WorkflowState.create_default_document_workflow()
        self.widget.workflow_state = workflow_state
        
        # Test with different container widths
        test_widths = [400, 800, 1200, 1600]
        
        for width in test_widths:
            self.widget.update_responsive_layout(width)
            
            # Verify responsive width is calculated and stored
            self.assertTrue(hasattr(self.widget, '_responsive_node_width'))
            self.assertIsInstance(self.widget._responsive_node_width, int)
            self.assertGreaterEqual(self.widget._responsive_node_width, 60)  # min width
            self.assertLessEqual(self.widget._responsive_node_width, 140)    # max width
    
    def test_stage_details_retrieval(self):
        """Test getting detailed stage information."""
        workflow_state = WorkflowState.create_default_document_workflow()
        self.widget.workflow_state = workflow_state
        
        # Test getting details for first stage (current)
        details = self.widget.get_stage_details("Postagem Inicial")
        
        self.assertIsNotNone(details)
        self.assertEqual(details['name'], "Postagem Inicial")
        self.assertEqual(details['status'], "in_progress")
        self.assertTrue(details['is_current'])
        self.assertEqual(details['order'], 0)
        
        # Test getting details for other stages
        details = self.widget.get_stage_details("Verificação")
        
        self.assertIsNotNone(details)
        self.assertEqual(details['name'], "Verificação")
        self.assertEqual(details['status'], "pending")
        self.assertFalse(details['is_current'])
        self.assertEqual(details['order'], 1)
    
    def test_enhanced_flowchart_layout(self):
        """Test enhanced flowchart layout with progress indicator."""
        workflow_state = WorkflowState.create_default_document_workflow()
        self.widget.workflow_state = workflow_state
        
        flowchart = self.widget._build_flowchart()
        
        # Verify it's a container with proper height
        self.assertIsInstance(flowchart, ft.Container)
        self.assertEqual(flowchart.height, 120)
        self.assertTrue(flowchart.expand)
    
    def test_no_workflow_display(self):
        """Test enhanced no workflow display."""
        self.widget.workflow_state = None
        
        flowchart = self.widget._build_flowchart()
        
        # Verify enhanced no-workflow display
        self.assertIsInstance(flowchart, ft.Container)
        self.assertEqual(flowchart.height, 100)
    
    def test_tooltip_content(self):
        """Test enhanced tooltip content."""
        stage = WorkflowStage("Test Stage", WorkflowStageStatus.BLOCKED, description="Test description")
        
        node = self.widget._create_stage_node(stage)
        
        # Verify tooltip contains enhanced information
        self.assertIn("Test Stage", node.tooltip)
        self.assertIn("Blocked", node.tooltip)
        self.assertIn("Click to view details", node.tooltip)
    
    def test_interactive_features(self):
        """Test interactive features are properly set up."""
        stage = WorkflowStage("Interactive Stage", WorkflowStageStatus.IN_PROGRESS)
        
        node = self.widget._create_stage_node(stage)
        
        # Verify interactive features
        self.assertIsNotNone(node.on_click)
        self.assertIsNotNone(node.on_hover)
        self.assertIsNotNone(node.tooltip)
    
    def test_visual_feedback_states(self):
        """Test visual feedback for different interaction states."""
        stage = WorkflowStage("Feedback Stage", WorkflowStageStatus.COMPLETED)
        
        node = self.widget._create_stage_node(stage)
        
        # Test hover effect function
        hover_event_enter = Mock()
        hover_event_enter.data = "true"
        hover_event_exit = Mock()
        hover_event_exit.data = "false"
        
        # Should not raise errors
        node.on_hover(hover_event_enter)
        node.on_hover(hover_event_exit)
    
    def test_workflow_integration(self):
        """Test integration with workflow service."""
        workflow_state = WorkflowState.create_default_document_workflow()
        self.widget.workflow_state = workflow_state
        
        # Test that all stages are rendered
        flowchart = self.widget._build_flowchart()
        
        # Should create a proper layout
        self.assertIsInstance(flowchart, ft.Container)
        
        # Test progress calculation
        progress = self.widget.get_progress_percentage()
        self.assertIsInstance(progress, float)
        self.assertGreaterEqual(progress, 0.0)
        self.assertLessEqual(progress, 100.0)


if __name__ == '__main__':
    unittest.main()