import unittest
from datetime import datetime
from models.workflow_state import WorkflowState, WorkflowStage, WorkflowStageStatus


class TestWorkflowStage(unittest.TestCase):
    
    def test_workflow_stage_creation_valid(self):
        """Test creating a valid workflow stage."""
        stage = WorkflowStage(name='Test Stage', order=1)
        
        self.assertEqual(stage.name, 'Test Stage')
        self.assertEqual(stage.status, WorkflowStageStatus.PENDING)
        self.assertEqual(stage.order, 1)
        self.assertIsNone(stage.description)
        self.assertEqual(stage.metadata, {})
    
    def test_workflow_stage_validation_empty_name(self):
        """Test validation fails with empty name."""
        with self.assertRaises(ValueError) as context:
            WorkflowStage(name='', order=1)
        self.assertIn('name cannot be empty', str(context.exception))
    
    def test_workflow_stage_validation_negative_order(self):
        """Test validation fails with negative order."""
        with self.assertRaises(ValueError) as context:
            WorkflowStage(name='Test', order=-1)
        self.assertIn('Order must be non-negative', str(context.exception))
    
    def test_workflow_stage_status_changes(self):
        """Test workflow stage status changes."""
        stage = WorkflowStage(name='Test Stage', order=1)
        
        # Test mark in progress
        stage.mark_in_progress()
        self.assertEqual(stage.status, WorkflowStageStatus.IN_PROGRESS)
        
        # Test mark completed
        stage.mark_completed()
        self.assertEqual(stage.status, WorkflowStageStatus.COMPLETED)
        
        # Test mark blocked
        stage.mark_blocked()
        self.assertEqual(stage.status, WorkflowStageStatus.BLOCKED)
        
        # Test reset
        stage.reset()
        self.assertEqual(stage.status, WorkflowStageStatus.PENDING)
    
    def test_workflow_stage_to_dict(self):
        """Test converting workflow stage to dictionary."""
        stage = WorkflowStage(
            name='Test Stage',
            order=1,
            description='Test description',
            metadata={'key': 'value'}
        )
        result = stage.to_dict()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['name'], 'Test Stage')
        self.assertEqual(result['status'], 'pending')
        self.assertEqual(result['order'], 1)
        self.assertEqual(result['description'], 'Test description')
        self.assertEqual(result['metadata'], {'key': 'value'})
    
    def test_workflow_stage_from_dict(self):
        """Test creating workflow stage from dictionary."""
        stage = WorkflowStage(name='Test Stage', order=1)
        data = stage.to_dict()
        
        restored_stage = WorkflowStage.from_dict(data)
        
        self.assertEqual(restored_stage.name, stage.name)
        self.assertEqual(restored_stage.status, stage.status)
        self.assertEqual(restored_stage.order, stage.order)


class TestWorkflowState(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.stages = [
            WorkflowStage(name='Stage 1', order=0),
            WorkflowStage(name='Stage 2', order=1),
            WorkflowStage(name='Stage 3', order=2)
        ]
        self.valid_workflow_data = {
            'current_stage': 'Stage 1',
            'stages': self.stages
        }
    
    def test_workflow_state_creation_valid(self):
        """Test creating a valid workflow state."""
        workflow = WorkflowState(**self.valid_workflow_data)
        
        self.assertEqual(workflow.current_stage, 'Stage 1')
        self.assertEqual(len(workflow.stages), 3)
        self.assertIsInstance(workflow.last_updated, datetime)
        self.assertIsNone(workflow.project_id)
    
    def test_workflow_state_validation_empty_current_stage(self):
        """Test validation fails with empty current stage."""
        with self.assertRaises(ValueError) as context:
            WorkflowState(current_stage='', stages=self.stages)
        self.assertIn('Current stage cannot be empty', str(context.exception))
    
    def test_workflow_state_validation_empty_stages(self):
        """Test validation fails with empty stages list."""
        with self.assertRaises(ValueError) as context:
            WorkflowState(current_stage='Stage 1', stages=[])
        self.assertIn('Stages list cannot be empty', str(context.exception))
    
    def test_workflow_state_validation_current_stage_not_found(self):
        """Test validation fails when current stage not in stages."""
        with self.assertRaises(ValueError) as context:
            WorkflowState(current_stage='Nonexistent Stage', stages=self.stages)
        self.assertIn('not found in stages', str(context.exception))
    
    def test_workflow_state_validation_duplicate_orders(self):
        """Test validation fails with duplicate stage orders."""
        duplicate_stages = [
            WorkflowStage(name='Stage 1', order=0),
            WorkflowStage(name='Stage 2', order=0)  # Duplicate order
        ]
        with self.assertRaises(ValueError) as context:
            WorkflowState(current_stage='Stage 1', stages=duplicate_stages)
        self.assertIn('Stage orders must be unique', str(context.exception))
    
    def test_workflow_state_get_current_stage(self):
        """Test getting current stage object."""
        workflow = WorkflowState(**self.valid_workflow_data)
        current_stage = workflow.get_current_stage()
        
        self.assertIsNotNone(current_stage)
        self.assertEqual(current_stage.name, 'Stage 1')
    
    def test_workflow_state_advance_to_stage(self):
        """Test advancing to a specific stage."""
        workflow = WorkflowState(**self.valid_workflow_data)
        
        workflow.advance_to_stage('Stage 2')
        
        self.assertEqual(workflow.current_stage, 'Stage 2')
        # Previous stages should be completed
        self.assertEqual(workflow.stages[0].status, WorkflowStageStatus.COMPLETED)
        # Current stage should be in progress
        self.assertEqual(workflow.stages[1].status, WorkflowStageStatus.IN_PROGRESS)
    
    def test_workflow_state_advance_to_invalid_stage(self):
        """Test advancing to invalid stage."""
        workflow = WorkflowState(**self.valid_workflow_data)
        
        with self.assertRaises(ValueError) as context:
            workflow.advance_to_stage('Nonexistent Stage')
        self.assertIn('not found in workflow', str(context.exception))
    
    def test_workflow_state_complete_current_stage(self):
        """Test completing current stage."""
        workflow = WorkflowState(**self.valid_workflow_data)
        
        result = workflow.complete_current_stage()
        
        self.assertTrue(result)  # Should return True when there's a next stage
        self.assertEqual(workflow.current_stage, 'Stage 2')
        self.assertEqual(workflow.stages[0].status, WorkflowStageStatus.COMPLETED)
        self.assertEqual(workflow.stages[1].status, WorkflowStageStatus.IN_PROGRESS)
    
    def test_workflow_state_complete_last_stage(self):
        """Test completing the last stage."""
        workflow = WorkflowState(current_stage='Stage 3', stages=self.stages)
        
        result = workflow.complete_current_stage()
        
        self.assertFalse(result)  # Should return False when no next stage
        self.assertEqual(workflow.current_stage, 'Stage 3')
        self.assertEqual(workflow.stages[2].status, WorkflowStageStatus.COMPLETED)
    
    def test_workflow_state_get_next_stage(self):
        """Test getting next stage."""
        workflow = WorkflowState(**self.valid_workflow_data)
        
        next_stage = workflow.get_next_stage()
        
        self.assertIsNotNone(next_stage)
        self.assertEqual(next_stage.name, 'Stage 2')
    
    def test_workflow_state_get_previous_stage(self):
        """Test getting previous stage."""
        workflow = WorkflowState(current_stage='Stage 2', stages=self.stages)
        
        previous_stage = workflow.get_previous_stage()
        
        self.assertIsNotNone(previous_stage)
        self.assertEqual(previous_stage.name, 'Stage 1')
    
    def test_workflow_state_get_progress_percentage(self):
        """Test calculating progress percentage."""
        workflow = WorkflowState(**self.valid_workflow_data)
        
        # No completed stages initially
        self.assertEqual(workflow.get_progress_percentage(), 0.0)
        
        # Complete one stage
        workflow.stages[0].mark_completed()
        self.assertAlmostEqual(workflow.get_progress_percentage(), 33.33, places=2)
        
        # Complete all stages
        for stage in workflow.stages:
            stage.mark_completed()
        self.assertEqual(workflow.get_progress_percentage(), 100.0)
    
    def test_workflow_state_to_dict(self):
        """Test converting workflow state to dictionary."""
        workflow = WorkflowState(**self.valid_workflow_data)
        result = workflow.to_dict()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['current_stage'], 'Stage 1')
        self.assertEqual(len(result['stages']), 3)
        self.assertIn('last_updated', result)
        self.assertIn('progress_percentage', result)
    
    def test_workflow_state_from_dict(self):
        """Test creating workflow state from dictionary."""
        workflow = WorkflowState(**self.valid_workflow_data)
        data = workflow.to_dict()
        
        restored_workflow = WorkflowState.from_dict(data)
        
        self.assertEqual(restored_workflow.current_stage, workflow.current_stage)
        self.assertEqual(len(restored_workflow.stages), len(workflow.stages))
        self.assertEqual(restored_workflow.project_id, workflow.project_id)
    
    def test_workflow_state_create_default_document_workflow(self):
        """Test creating default document workflow."""
        workflow = WorkflowState.create_default_document_workflow()
        
        self.assertEqual(workflow.current_stage, 'Postagem Inicial')
        self.assertEqual(len(workflow.stages), 11)
        
        # Check that all expected stages are present
        expected_stages = [
            'Postagem Inicial', 'Verificação', 'Aprovação', 'Emissão',
            'Comentários Cliente', 'Análise Cliente', 'Comentários Proprietário',
            'Análise Técnica', 'Revisão Aprovado', 'Emissão Aprovado', 'Postagem Concluída'
        ]
        
        stage_names = [stage.name for stage in workflow.stages]
        for expected_stage in expected_stages:
            self.assertIn(expected_stage, stage_names)
    
    def test_workflow_state_create_default_with_project_id(self):
        """Test creating default workflow with project ID."""
        project_id = 'test-project-123'
        workflow = WorkflowState.create_default_document_workflow(project_id)
        
        self.assertEqual(workflow.project_id, project_id)


if __name__ == '__main__':
    unittest.main()