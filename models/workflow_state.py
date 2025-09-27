from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class WorkflowStageStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


@dataclass
class WorkflowStage:
    name: str
    status: WorkflowStageStatus = WorkflowStageStatus.PENDING
    description: Optional[str] = None
    order: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate workflow stage data after initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate workflow stage data integrity."""
        if not self.name or not self.name.strip():
            raise ValueError("Workflow stage name cannot be empty")
        
        if not isinstance(self.status, WorkflowStageStatus):
            raise ValueError("Status must be a WorkflowStageStatus enum")
        
        if not isinstance(self.order, int):
            raise ValueError("Order must be an integer")
        
        if self.order < 0:
            raise ValueError("Order must be non-negative")
        
        if self.description is not None and not isinstance(self.description, str):
            raise ValueError("Description must be a string or None")
        
        if not isinstance(self.metadata, dict):
            raise ValueError("Metadata must be a dictionary")

    def mark_in_progress(self) -> None:
        """Mark the stage as in progress."""
        self.status = WorkflowStageStatus.IN_PROGRESS

    def mark_completed(self) -> None:
        """Mark the stage as completed."""
        self.status = WorkflowStageStatus.COMPLETED

    def mark_blocked(self) -> None:
        """Mark the stage as blocked."""
        self.status = WorkflowStageStatus.BLOCKED

    def reset(self) -> None:
        """Reset the stage to pending status."""
        self.status = WorkflowStageStatus.PENDING

    def to_dict(self) -> dict:
        """Convert workflow stage to dictionary for serialization."""
        return {
            'name': self.name,
            'status': self.status.value,
            'description': self.description,
            'order': self.order,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'WorkflowStage':
        """Create workflow stage from dictionary."""
        return cls(
            name=data['name'],
            status=WorkflowStageStatus(data['status']),
            description=data.get('description'),
            order=data['order'],
            metadata=data.get('metadata', {})
        )


@dataclass
class WorkflowState:
    current_stage: str
    stages: List[WorkflowStage]
    last_updated: datetime = field(default_factory=datetime.now)
    project_id: Optional[str] = None

    def __post_init__(self):
        """Validate workflow state data after initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate workflow state data integrity."""
        if not self.current_stage or not self.current_stage.strip():
            raise ValueError("Current stage cannot be empty")
        
        if not isinstance(self.stages, list):
            raise ValueError("Stages must be a list")
        
        if not self.stages:
            raise ValueError("Stages list cannot be empty")
        
        if not isinstance(self.last_updated, datetime):
            raise ValueError("last_updated must be a datetime object")
        
        if self.project_id is not None and not isinstance(self.project_id, str):
            raise ValueError("project_id must be a string or None")
        
        # Validate that all stages are WorkflowStage instances
        for stage in self.stages:
            if not isinstance(stage, WorkflowStage):
                raise ValueError("All stages must be WorkflowStage instances")
        
        # Validate that current_stage exists in stages
        stage_names = [stage.name for stage in self.stages]
        if self.current_stage not in stage_names:
            raise ValueError(f"Current stage '{self.current_stage}' not found in stages")
        
        # Validate stage order uniqueness
        orders = [stage.order for stage in self.stages]
        if len(orders) != len(set(orders)):
            raise ValueError("Stage orders must be unique")

    def get_current_stage(self) -> Optional[WorkflowStage]:
        """Get the current workflow stage object."""
        for stage in self.stages:
            if stage.name == self.current_stage:
                return stage
        return None

    def advance_to_stage(self, stage_name: str) -> None:
        """Advance workflow to a specific stage."""
        stage_names = [stage.name for stage in self.stages]
        if stage_name not in stage_names:
            raise ValueError(f"Stage '{stage_name}' not found in workflow")
        
        # Mark previous stages as completed and current as in progress
        current_found = False
        for stage in sorted(self.stages, key=lambda s: s.order):
            if stage.name == stage_name:
                stage.mark_in_progress()
                current_found = True
                break
            else:
                stage.mark_completed()
        
        if current_found:
            self.current_stage = stage_name
            self.last_updated = datetime.now()

    def complete_current_stage(self) -> bool:
        """Complete the current stage and advance to next if available."""
        current_stage_obj = self.get_current_stage()
        if not current_stage_obj:
            return False
        
        current_stage_obj.mark_completed()
        
        # Find next stage by order
        next_stage = self.get_next_stage()
        if next_stage:
            self.advance_to_stage(next_stage.name)
            return True
        
        self.last_updated = datetime.now()
        return False

    def get_next_stage(self) -> Optional[WorkflowStage]:
        """Get the next stage in the workflow."""
        current_stage_obj = self.get_current_stage()
        if not current_stage_obj:
            return None
        
        sorted_stages = sorted(self.stages, key=lambda s: s.order)
        for i, stage in enumerate(sorted_stages):
            if stage.name == self.current_stage and i + 1 < len(sorted_stages):
                return sorted_stages[i + 1]
        
        return None

    def get_previous_stage(self) -> Optional[WorkflowStage]:
        """Get the previous stage in the workflow."""
        current_stage_obj = self.get_current_stage()
        if not current_stage_obj:
            return None
        
        sorted_stages = sorted(self.stages, key=lambda s: s.order)
        for i, stage in enumerate(sorted_stages):
            if stage.name == self.current_stage and i > 0:
                return sorted_stages[i - 1]
        
        return None

    def get_progress_percentage(self) -> float:
        """Calculate workflow completion percentage."""
        if not self.stages:
            return 0.0
        
        completed_stages = sum(1 for stage in self.stages if stage.status == WorkflowStageStatus.COMPLETED)
        return (completed_stages / len(self.stages)) * 100

    def to_dict(self) -> dict:
        """Convert workflow state to dictionary for serialization."""
        return {
            'current_stage': self.current_stage,
            'stages': [stage.to_dict() for stage in self.stages],
            'last_updated': self.last_updated.isoformat(),
            'project_id': self.project_id,
            'progress_percentage': self.get_progress_percentage()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'WorkflowState':
        """Create workflow state from dictionary."""
        stages = [WorkflowStage.from_dict(stage_data) for stage_data in data['stages']]
        return cls(
            current_stage=data['current_stage'],
            stages=stages,
            last_updated=datetime.fromisoformat(data['last_updated']),
            project_id=data.get('project_id')
        )

    @classmethod
    def create_default_document_workflow(cls, project_id: Optional[str] = None) -> 'WorkflowState':
        """Create a default document workflow based on the requirements."""
        stages = [
            WorkflowStage("Postagem Inicial", WorkflowStageStatus.IN_PROGRESS, order=0, description="Initial document posting"),
            WorkflowStage("Verificação", order=1, description="Document verification"),
            WorkflowStage("Aprovação", order=2, description="Document approval"),
            WorkflowStage("Emissão", order=3, description="Document emission"),
            WorkflowStage("Comentários Cliente", order=4, description="Client comments"),
            WorkflowStage("Análise Cliente", order=5, description="Client analysis"),
            WorkflowStage("Comentários Proprietário", order=6, description="Owner comments"),
            WorkflowStage("Análise Técnica", order=7, description="Technical analysis"),
            WorkflowStage("Revisão Aprovado", order=8, description="Approved revision"),
            WorkflowStage("Emissão Aprovado", order=9, description="Approved emission"),
            WorkflowStage("Postagem Concluída", order=10, description="Completed posting")
        ]
        
        return cls(
            current_stage="Postagem Inicial",
            stages=stages,
            project_id=project_id
        )