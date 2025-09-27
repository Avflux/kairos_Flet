from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import os
import logging
from models.workflow_state import WorkflowState, WorkflowStage, WorkflowStageStatus
from views.components.error_handling import (
    ErrorBoundary, get_recovery_manager, get_storage_manager,
    ErrorSeverity, ErrorContext
)


class WorkflowService:
    """Service for managing workflow states and transitions."""
    
    def __init__(self, storage_path: str = "data/workflows.json"):
        """Initialize the workflow service with optional storage path."""
        self.storage_path = storage_path
        self._workflows: Dict[str, WorkflowState] = {}
        
        # Error handling components
        self._recovery_manager = get_recovery_manager()
        self._storage_manager = get_storage_manager()
        
        # Register recovery strategies
        self._recovery_manager.register_recovery_strategy(
            'WorkflowLoadError', self._recover_from_load_error
        )
        self._recovery_manager.register_recovery_strategy(
            'WorkflowSaveError', self._recover_from_save_error
        )
        
        self._ensure_storage_directory()
        self._load_workflows_safe()
    
    def _ensure_storage_directory(self) -> None:
        """Ensure the storage directory exists."""
        directory = os.path.dirname(self.storage_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    
    def _load_workflows(self) -> None:
        """Load workflows from storage."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for workflow_id, workflow_data in data.items():
                        self._workflows[workflow_id] = WorkflowState.from_dict(workflow_data)
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            # If loading fails, start with empty workflows
            self._workflows = {}
    
    def _load_workflows_safe(self) -> None:
        """Load workflows with error handling and backup recovery."""
        try:
            self._load_workflows()
            logging.info(f"Loaded {len(self._workflows)} workflows from storage")
        except Exception as e:
            logging.error(f"Failed to load workflows: {e}")
            
            # Try to recover from backup
            try:
                backup_data = self._storage_manager.restore_data('workflows_backup')
                if backup_data:
                    self._workflows = {}
                    for workflow_id, workflow_data in backup_data.items():
                        try:
                            self._workflows[workflow_id] = WorkflowState.from_dict(workflow_data)
                        except Exception as restore_error:
                            logging.warning(f"Failed to restore workflow {workflow_id}: {restore_error}")
                    
                    logging.info(f"Recovered {len(self._workflows)} workflows from backup")
                else:
                    # Create default workflow if no backup available
                    self._create_default_workflow_safe()
            except Exception as recovery_error:
                logging.error(f"Workflow recovery failed: {recovery_error}")
                self._workflows = {}
                self._create_default_workflow_safe()
    
    def _create_default_workflow_safe(self) -> None:
        """Create a default workflow safely."""
        try:
            default_workflow = WorkflowState.create_default_document_workflow()
            self._workflows['default'] = default_workflow
            self._save_workflows_safe()
            logging.info("Created default workflow")
        except Exception as e:
            logging.error(f"Failed to create default workflow: {e}")
    
    def _save_workflows(self) -> None:
        """Save workflows to storage."""
        try:
            data = {
                workflow_id: workflow.to_dict() 
                for workflow_id, workflow in self._workflows.items()
            }
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            # Log error but don't raise to prevent data loss
            print(f"Warning: Failed to save workflows: {e}")
    
    def _save_workflows_safe(self) -> bool:
        """Save workflows with error handling and backup."""
        try:
            # Create backup before saving
            self._backup_workflows()
            
            # Save to primary storage
            self._save_workflows()
            
            logging.debug("Workflows saved successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to save workflows: {e}")
            
            # Record error for recovery
            context = ErrorContext(
                component_name="WorkflowService",
                operation="save_workflows",
                severity=ErrorSeverity.HIGH
            )
            self._recovery_manager.record_error(context)
            
            return False
    
    def _backup_workflows(self) -> None:
        """Backup workflows to local storage."""
        try:
            data = {
                workflow_id: workflow.to_dict() 
                for workflow_id, workflow in self._workflows.items()
            }
            self._storage_manager.backup_data('workflows_backup', data)
        except Exception as e:
            logging.error(f"Failed to backup workflows: {e}")
    
    def create_workflow(self, workflow_id: str, project_id: Optional[str] = None) -> WorkflowState:
        """Create a new workflow with default document stages."""
        if workflow_id in self._workflows:
            raise ValueError(f"Workflow with ID '{workflow_id}' already exists")
        
        workflow = WorkflowState.create_default_document_workflow(project_id)
        self._workflows[workflow_id] = workflow
        self._save_workflows()
        return workflow
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get a workflow by ID."""
        return self._workflows.get(workflow_id)
    
    def get_all_workflows(self) -> Dict[str, WorkflowState]:
        """Get all workflows."""
        return self._workflows.copy()
    
    def update_workflow(self, workflow_id: str, workflow: WorkflowState) -> None:
        """Update an existing workflow."""
        if workflow_id not in self._workflows:
            raise ValueError(f"Workflow with ID '{workflow_id}' not found")
        
        self._workflows[workflow_id] = workflow
        self._save_workflows()
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow by ID."""
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            self._save_workflows()
            return True
        return False
    
    def advance_workflow_stage(self, workflow_id: str, stage_name: str) -> bool:
        """Advance a workflow to a specific stage."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return False
        
        try:
            workflow.advance_to_stage(stage_name)
            self._save_workflows()
            return True
        except ValueError:
            return False
    
    def complete_current_stage(self, workflow_id: str) -> bool:
        """Complete the current stage and advance to next."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return False
        
        result = workflow.complete_current_stage()
        self._save_workflows()
        return result
    
    def get_workflow_progress(self, workflow_id: str) -> Optional[float]:
        """Get workflow completion percentage."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        
        return workflow.get_progress_percentage()
    
    def get_current_stage(self, workflow_id: str) -> Optional[WorkflowStage]:
        """Get the current stage of a workflow."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        
        return workflow.get_current_stage()
    
    def get_next_stage(self, workflow_id: str) -> Optional[WorkflowStage]:
        """Get the next stage of a workflow."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        
        return workflow.get_next_stage()
    
    def get_previous_stage(self, workflow_id: str) -> Optional[WorkflowStage]:
        """Get the previous stage of a workflow."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        
        return workflow.get_previous_stage()
    
    def set_stage_status(self, workflow_id: str, stage_name: str, status: WorkflowStageStatus) -> bool:
        """Set the status of a specific stage."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return False
        
        for stage in workflow.stages:
            if stage.name == stage_name:
                stage.status = status
                workflow.last_updated = datetime.now()
                self._save_workflows()
                return True
        
        return False
    
    def get_stages_by_status(self, workflow_id: str, status: WorkflowStageStatus) -> List[WorkflowStage]:
        """Get all stages with a specific status."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return []
        
        return [stage for stage in workflow.stages if stage.status == status]
    
    def reset_workflow(self, workflow_id: str) -> bool:
        """Reset a workflow to its initial state."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return False
        
        # Reset all stages to pending
        for stage in workflow.stages:
            stage.reset()
        
        # Set current stage to first stage
        if workflow.stages:
            first_stage = min(workflow.stages, key=lambda s: s.order)
            workflow.current_stage = first_stage.name
            first_stage.mark_in_progress()
        
        workflow.last_updated = datetime.now()
        self._save_workflows()
        return True
    
    def get_workflow_summary(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of workflow status."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        
        current_stage = workflow.get_current_stage()
        next_stage = workflow.get_next_stage()
        previous_stage = workflow.get_previous_stage()
        
        return {
            'workflow_id': workflow_id,
            'project_id': workflow.project_id,
            'current_stage': current_stage.name if current_stage else None,
            'next_stage': next_stage.name if next_stage else None,
            'previous_stage': previous_stage.name if previous_stage else None,
            'progress_percentage': workflow.get_progress_percentage(),
            'total_stages': len(workflow.stages),
            'completed_stages': len([s for s in workflow.stages if s.status == WorkflowStageStatus.COMPLETED]),
            'last_updated': workflow.last_updated.isoformat()
        }    
    
    def _recover_from_load_error(self, context: ErrorContext) -> bool:
        """Recovery strategy for workflow loading errors."""
        try:
            # Try to restore from backup
            backup_data = self._storage_manager.restore_data('workflows_backup')
            if backup_data:
                self._workflows.clear()
                for workflow_id, workflow_data in backup_data.items():
                    try:
                        self._workflows[workflow_id] = WorkflowState.from_dict(workflow_data)
                    except Exception as e:
                        logging.warning(f"Failed to restore workflow {workflow_id}: {e}")
                
                logging.info(f"Recovered {len(self._workflows)} workflows from backup")
                return True
            else:
                # Create minimal default workflow
                self._create_default_workflow_safe()
                return True
        except Exception as e:
            logging.error(f"Workflow load recovery failed: {e}")
            return False
    
    def _recover_from_save_error(self, context: ErrorContext) -> bool:
        """Recovery strategy for workflow saving errors."""
        try:
            # Try alternative save location
            backup_path = self.storage_path + '.backup'
            
            data = {
                workflow_id: workflow.to_dict() 
                for workflow_id, workflow in self._workflows.items()
            }
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logging.info(f"Workflows saved to backup location: {backup_path}")
            return True
            
        except Exception as e:
            logging.error(f"Workflow save recovery failed: {e}")
            return False
    
    def get_workflow_safe(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get a workflow by ID with error handling."""
        try:
            return self.get_workflow(workflow_id)
        except Exception as e:
            logging.error(f"Failed to get workflow {workflow_id}: {e}")
            
            # Try to recover from backup
            context = ErrorContext(
                component_name="WorkflowService",
                operation="get_workflow",
                user_data={"workflow_id": workflow_id}
            )
            
            if self._recovery_manager.attempt_recovery('WorkflowLoadError', context):
                try:
                    return self.get_workflow(workflow_id)
                except Exception:
                    pass
            
            return None
    
    def create_workflow_safe(self, workflow_id: str, project_id: Optional[str] = None) -> Optional[WorkflowState]:
        """Create a new workflow with error handling."""
        try:
            return self.create_workflow(workflow_id, project_id)
        except Exception as e:
            logging.error(f"Failed to create workflow {workflow_id}: {e}")
            
            context = ErrorContext(
                component_name="WorkflowService",
                operation="create_workflow",
                user_data={"workflow_id": workflow_id, "project_id": project_id}
            )
            self._recovery_manager.record_error(context)
            
            return None
    
    def update_workflow_safe(self, workflow_id: str, workflow: WorkflowState) -> bool:
        """Update an existing workflow with error handling."""
        try:
            self.update_workflow(workflow_id, workflow)
            return True
        except Exception as e:
            logging.error(f"Failed to update workflow {workflow_id}: {e}")
            
            context = ErrorContext(
                component_name="WorkflowService",
                operation="update_workflow",
                user_data={"workflow_id": workflow_id},
                severity=ErrorSeverity.HIGH
            )
            self._recovery_manager.record_error(context)
            
            return False
    
    def advance_workflow_stage_safe(self, workflow_id: str, stage_name: str) -> bool:
        """Advance a workflow to a specific stage with error handling."""
        try:
            return self.advance_workflow_stage(workflow_id, stage_name)
        except Exception as e:
            logging.error(f"Failed to advance workflow {workflow_id} to stage {stage_name}: {e}")
            
            context = ErrorContext(
                component_name="WorkflowService",
                operation="advance_workflow_stage",
                user_data={"workflow_id": workflow_id, "stage_name": stage_name}
            )
            self._recovery_manager.record_error(context)
            
            return False