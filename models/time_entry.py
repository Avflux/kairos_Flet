from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import uuid


@dataclass
class TimeEntry:
    activity_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    notes: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """Validate time entry data after initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate time entry data integrity."""
        if not self.activity_id or not self.activity_id.strip():
            raise ValueError("Activity ID cannot be empty")
        
        if not isinstance(self.start_time, datetime):
            raise ValueError("start_time must be a datetime object")
        
        if self.end_time is not None:
            if not isinstance(self.end_time, datetime):
                raise ValueError("end_time must be a datetime object or None")
            
            if self.end_time <= self.start_time:
                raise ValueError("end_time must be after start_time")
        
        if self.notes is not None and not isinstance(self.notes, str):
            raise ValueError("notes must be a string or None")
        
        # Validate notes length
        if self.notes is not None and len(self.notes) > 500:
            raise ValueError("Notes cannot exceed 500 characters")

    @property
    def duration(self) -> timedelta:
        """Calculate the duration of the time entry."""
        if self.end_time is None:
            # If still running, calculate duration from start to now
            return datetime.now() - self.start_time
        return self.end_time - self.start_time

    @property
    def is_active(self) -> bool:
        """Check if the time entry is currently active (no end time)."""
        return self.end_time is None

    def stop(self, end_time: Optional[datetime] = None) -> None:
        """Stop the time entry by setting the end time."""
        if self.end_time is not None:
            raise ValueError("Time entry is already stopped")
        
        stop_time = end_time or datetime.now()
        
        if stop_time <= self.start_time:
            raise ValueError("Stop time must be after start time")
        
        self.end_time = stop_time

    def add_notes(self, notes: str) -> None:
        """Add or update notes for the time entry."""
        if not isinstance(notes, str):
            raise ValueError("Notes must be a string")
        
        if len(notes) > 500:
            raise ValueError("Notes cannot exceed 500 characters")
        
        self.notes = notes

    def get_duration_string(self) -> str:
        """Get a formatted string representation of the duration."""
        duration = self.duration
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def to_dict(self) -> dict:
        """Convert time entry to dictionary for serialization."""
        return {
            'id': self.id,
            'activity_id': self.activity_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'notes': self.notes,
            'duration_seconds': self.duration.total_seconds()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TimeEntry':
        """Create time entry from dictionary."""
        return cls(
            id=data['id'],
            activity_id=data['activity_id'],
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']) if data['end_time'] else None,
            notes=data.get('notes')
        )