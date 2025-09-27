from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Activity:
    name: str
    category: str
    description: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate activity data after initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate activity data integrity."""
        if not self.name or not self.name.strip():
            raise ValueError("Activity name cannot be empty")
        
        if not self.category or not self.category.strip():
            raise ValueError("Activity category cannot be empty")
        
        if not isinstance(self.created_at, datetime):
            raise ValueError("created_at must be a datetime object")
        
        if self.description is not None and not isinstance(self.description, str):
            raise ValueError("description must be a string or None")
        
        # Validate name length
        if len(self.name.strip()) > 100:
            raise ValueError("Activity name cannot exceed 100 characters")
        
        # Validate category length
        if len(self.category.strip()) > 50:
            raise ValueError("Activity category cannot exceed 50 characters")

    def update_name(self, new_name: str) -> None:
        """Update activity name with validation."""
        if not new_name or not new_name.strip():
            raise ValueError("Activity name cannot be empty")
        if len(new_name.strip()) > 100:
            raise ValueError("Activity name cannot exceed 100 characters")
        self.name = new_name.strip()

    def update_category(self, new_category: str) -> None:
        """Update activity category with validation."""
        if not new_category or not new_category.strip():
            raise ValueError("Activity category cannot be empty")
        if len(new_category.strip()) > 50:
            raise ValueError("Activity category cannot exceed 50 characters")
        self.category = new_category.strip()

    def update_description(self, new_description: Optional[str]) -> None:
        """Update activity description with validation."""
        if new_description is not None and not isinstance(new_description, str):
            raise ValueError("description must be a string or None")
        self.description = new_description

    def to_dict(self) -> dict:
        """Convert activity to dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Activity':
        """Create activity from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            category=data['category'],
            description=data.get('description'),
            created_at=datetime.fromisoformat(data['created_at'])
        )