import unittest
import tempfile
import os
import json
from datetime import datetime
from services.workflow_service import WorkflowService
from models.workflow_state import WorkflowState, WorkflowStage, WorkflowStageStatus


class TestWorkflowService(unittest.TestCase):
    """Test cases for WorkflowService class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.service = WorkflowService(storage_path=self.temp_file.name)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary file
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_create_workflow(self):
        """Test creating a new workflow."""
        workflow_id = "test_workflow"
        project_id = "test_project"
        
        workflow = self.service.create_workflow(workflow_id, project_id)
        
        self.assertIsInstance(workflow, WorkflowState)
        self.assertEqual(workflow.project_id, project_id)
        self.assertEqual(workflow.current_stage, "Postagem Inicial")
        self.assertEqual(len(workflow.stages), 11)
        
        # Verify workflow is stored
        retrieved = self.service.get_workflow(workflow_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.project_id, project_id)
    
    def test_create_duplicate_workflow(self):
        """Test creating a workflow with duplicate ID raises error."""
        workflow_id = "test_workflow"
        
        self.service.create_workflow(workflow_id)
        
        with self.assertRaises(ValueError):
            self.service.create_workflow(workflow_id)
    
    def test_get_workflow(self):
        """Test retrieving a workflow by ID."""
        workflow_id = "test_workflow"
        
        # Test non-existent workflow
        result = self.service.get_workflow(workflow_id)
        self.assertIsNone(result)
        
        # Create and retrieve workflow
        created = self.service.create_workflow(workflow_id)
        retrieved = self.service.get_workflow(workflow_id)
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.current_stage, created.current_stage)
        self.assertEqual(len(retrieved.stages), len(created.stages))
    
    def test_get_all_workflows(self):
        """Test retrieving all workflows."""
        # Initially empty
        workflows = self.service.get_all_workflows()
        self.assertEqual(len(workflows), 0)
        
        # Create multiple workflows
        self.service.create_workflow("workflow1")
        self.service.create_workflow("workflow2")
        
        workflows = self.service.get_all_workflows()
        self.assertEqual(len(workflows), 2)
        self.assertIn("workflow1", workflows)
        self.assertIn("workflow2", workflows)
    
    def test_update_workflow(self):
        """Test updating an existing workflow."""
        workflow_id = "test_workflow"
        
        # Test updating non-existent workflow
        workflow = WorkflowState.create_default_document_workflow()
        with self.assertRaises(ValueError):
            self.service.update_workflow(workflow_id, workflow)
        
        # Create and update workflow
        self.service.create_workflow(workflow_id)
        workflow.current_stage = "Verificação"
        
        self.service.update_workflow(workflow_id, workflow)
        
        retrieved = self.service.get_workflow(workflow_id)
        self.assertEqual(retrieved.current_stage, "Verificação")
    
    def test_delete_workflow(self):
        """Test deleting a workflow."""
        workflow_id = "test_workflow"
        
        # Test deleting non-existent workflow
        result = self.service.delete_workflow(workflow_id)
        self.assertFalse(result)
        
        # Create and delete workflow
        self.service.create_workflow(workflow_id)
        result = self.service.delete_workflow(workflow_id)
        self.assertTrue(result)
        
        # Verify deletion
        retrieved = self.service.get_workflow(workflow_id)
        self.assertIsNone(retrieved)
    
    def test_advance_workflow_stage(self):
        """Test advancing workflow to a specific stage."""
        workflow_id = "test_workflow"
        
        # Test with non-existent workflow
        result = self.service.advance_workflow_stage(workflow_id, "Verificação")
        self.assertFalse(result)
        
        # Create workflow and advance stage
        self.service.create_workflow(workflow_id)
        result = self.service.advance_workflow_stage(workflow_id, "Verificação")
        self.assertTrue(result)
        
        workflow = self.service.get_workflow(workflow_id)
        self.assertEqual(workflow.current_stage, "Verificação")
        
        # Test advancing to invalid stage
        result = self.service.advance_workflow_stage(workflow_id, "Invalid Stage")
        self.assertFalse(result)
    
    def test_complete_current_stage(self):
        """Test completing current stage and advancing to next."""
        workflow_id = "test_workflow"
        
        # Test with non-existent workflow
        result = self.service.complete_current_stage(workflow_id)
        self.assertFalse(result)
        
        # Create workflow and complete stage
        self.service.create_workflow(workflow_id)
        result = self.service.complete_current_stage(workflow_id)
        self.assertTrue(result)
        
        workflow = self.service.get_workflow(workflow_id)
        self.assertEqual(workflow.current_stage, "Verificação")
        
        # Verify previous stage is completed
        for stage in workflow.stages:
            if stage.name == "Postagem Inicial":
                self.assertEqual(stage.status, WorkflowStageStatus.COMPLETED)
            elif stage.name == "Verificação":
                self.assertEqual(stage.status, WorkflowStageStatus.IN_PROGRESS)
    
    def test_get_workflow_progress(self):
        """Test getting workflow completion percentage."""
        workflow_id = "test_workflow"
        
        # Test with non-existent workflow
        progress = self.service.get_workflow_progress(workflow_id)
        self.assertIsNone(progress)
        
        # Create workflow and test progress
        self.service.create_workflow(workflow_id)
        progress = self.service.get_workflow_progress(workflow_id)
        self.assertEqual(progress, 0.0)
        
        # Complete a stage and test progress
        self.service.complete_current_stage(workflow_id)
        progress = self.service.get_workflow_progress(workflow_id)
        self.assertGreater(progress, 0.0)
    
    def test_get_current_stage(self):
        """Test getting current workflow stage."""
        workflow_id = "test_workflow"
        
        # Test with non-existent workflow
        stage = self.service.get_current_stage(workflow_id)
        self.assertIsNone(stage)
        
        # Create workflow and get current stage
        self.service.create_workflow(workflow_id)
        stage = self.service.get_current_stage(workflow_id)
        
        self.assertIsNotNone(stage)
        self.assertEqual(stage.name, "Postagem Inicial")
        self.assertEqual(stage.status, WorkflowStageStatus.IN_PROGRESS)
    
    def test_get_next_stage(self):
        """Test getting next workflow stage."""
        workflow_id = "test_workflow"
        
        # Test with non-existent workflow
        stage = self.service.get_next_stage(workflow_id)
        self.assertIsNone(stage)
        
        # Create workflow and get next stage
        self.service.create_workflow(workflow_id)
        stage = self.service.get_next_stage(workflow_id)
        
        self.assertIsNotNone(stage)
        self.assertEqual(stage.name, "Verificação")
    
    def test_get_previous_stage(self):
        """Test getting previous workflow stage."""
        workflow_id = "test_workflow"
        
        # Create workflow and advance to second stage
        self.service.create_workflow(workflow_id)
        self.service.advance_workflow_stage(workflow_id, "Verificação")
        
        stage = self.service.get_previous_stage(workflow_id)
        self.assertIsNotNone(stage)
        self.assertEqual(stage.name, "Postagem Inicial")
        
        # Test at first stage
        self.service.advance_workflow_stage(workflow_id, "Postagem Inicial")
        stage = self.service.get_previous_stage(workflow_id)
        self.assertIsNone(stage)
    
    def test_set_stage_status(self):
        """Test setting stage status."""
        workflow_id = "test_workflow"
        
        # Test with non-existent workflow
        result = self.service.set_stage_status(workflow_id, "Verificação", WorkflowStageStatus.BLOCKED)
        self.assertFalse(result)
        
        # Create workflow and set stage status
        self.service.create_workflow(workflow_id)
        result = self.service.set_stage_status(workflow_id, "Verificação", WorkflowStageStatus.BLOCKED)
        self.assertTrue(result)
        
        workflow = self.service.get_workflow(workflow_id)
        for stage in workflow.stages:
            if stage.name == "Verificação":
                self.assertEqual(stage.status, WorkflowStageStatus.BLOCKED)
        
        # Test with invalid stage name
        result = self.service.set_stage_status(workflow_id, "Invalid Stage", WorkflowStageStatus.COMPLETED)
        self.assertFalse(result)
    
    def test_get_stages_by_status(self):
        """Test getting stages by status."""
        workflow_id = "test_workflow"
        
        # Test with non-existent workflow
        stages = self.service.get_stages_by_status(workflow_id, WorkflowStageStatus.PENDING)
        self.assertEqual(len(stages), 0)
        
        # Create workflow and test
        self.service.create_workflow(workflow_id)
        
        # Get pending stages
        pending_stages = self.service.get_stages_by_status(workflow_id, WorkflowStageStatus.PENDING)
        self.assertEqual(len(pending_stages), 10)  # All except first stage
        
        # Get in-progress stages
        in_progress_stages = self.service.get_stages_by_status(workflow_id, WorkflowStageStatus.IN_PROGRESS)
        self.assertEqual(len(in_progress_stages), 1)  # First stage
        
        # Complete a stage and test
        self.service.complete_current_stage(workflow_id)
        completed_stages = self.service.get_stages_by_status(workflow_id, WorkflowStageStatus.COMPLETED)
        self.assertEqual(len(completed_stages), 1)
    
    def test_reset_workflow(self):
        """Test resetting workflow to initial state."""
        workflow_id = "test_workflow"
        
        # Test with non-existent workflow
        result = self.service.reset_workflow(workflow_id)
        self.assertFalse(result)
        
        # Create workflow, advance stages, then reset
        self.service.create_workflow(workflow_id)
        self.service.complete_current_stage(workflow_id)
        self.service.complete_current_stage(workflow_id)
        
        result = self.service.reset_workflow(workflow_id)
        self.assertTrue(result)
        
        workflow = self.service.get_workflow(workflow_id)
        self.assertEqual(workflow.current_stage, "Postagem Inicial")
        
        # Verify all stages are reset except first
        for stage in workflow.stages:
            if stage.name == "Postagem Inicial":
                self.assertEqual(stage.status, WorkflowStageStatus.IN_PROGRESS)
            else:
                self.assertEqual(stage.status, WorkflowStageStatus.PENDING)
    
    def test_get_workflow_summary(self):
        """Test getting workflow summary."""
        workflow_id = "test_workflow"
        project_id = "test_project"
        
        # Test with non-existent workflow
        summary = self.service.get_workflow_summary(workflow_id)
        self.assertIsNone(summary)
        
        # Create workflow and get summary
        self.service.create_workflow(workflow_id, project_id)
        summary = self.service.get_workflow_summary(workflow_id)
        
        self.assertIsNotNone(summary)
        self.assertEqual(summary['workflow_id'], workflow_id)
        self.assertEqual(summary['project_id'], project_id)
        self.assertEqual(summary['current_stage'], "Postagem Inicial")
        self.assertEqual(summary['next_stage'], "Verificação")
        self.assertIsNone(summary['previous_stage'])
        self.assertEqual(summary['progress_percentage'], 0.0)
        self.assertEqual(summary['total_stages'], 11)
        self.assertEqual(summary['completed_stages'], 0)
        self.assertIsInstance(summary['last_updated'], str)
    
    def test_persistence(self):
        """Test workflow persistence across service instances."""
        workflow_id = "test_workflow"
        
        # Create workflow in first service instance
        self.service.create_workflow(workflow_id)
        self.service.advance_workflow_stage(workflow_id, "Verificação")
        
        # Create new service instance with same storage
        new_service = WorkflowService(storage_path=self.temp_file.name)
        
        # Verify workflow is loaded
        workflow = new_service.get_workflow(workflow_id)
        self.assertIsNotNone(workflow)
        self.assertEqual(workflow.current_stage, "Verificação")
    
    def test_storage_error_handling(self):
        """Test handling of storage errors."""
        # Test with invalid storage path
        import uuid
        unique_id = str(uuid.uuid4())
        invalid_service = WorkflowService(storage_path="/invalid/path/workflows.json")
        
        # Should still work but not persist
        workflow = invalid_service.create_workflow(f"test_invalid_{unique_id}")
        self.assertIsNotNone(workflow)
        
        # Test loading corrupted data
        with open(self.temp_file.name, 'w') as f:
            f.write("invalid json")
        
        # Should handle gracefully
        corrupted_service = WorkflowService(storage_path=self.temp_file.name)
        workflows = corrupted_service.get_all_workflows()
        self.assertEqual(len(workflows), 0)


if __name__ == '__main__':
    unittest.main()