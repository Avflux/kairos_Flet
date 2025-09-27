from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class NotificationType(Enum):
    INFO = "info"
    WARNING = "warning"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class Notification:
    title: str
    message: str
    type: NotificationType
    timestamp: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_read: bool = False
    action_url: Optional[str] = None

    def __post_init__(self):
        """Validate notification data after initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate notification data integrity."""
        if not self.title or not self.title.strip():
            raise ValueError("Notification title cannot be empty")
        
        if not self.message or not self.message.strip():
            raise ValueError("Notification message cannot be empty")
        
        if not isinstance(self.type, NotificationType):
            raise ValueError("Notification type must be a NotificationType enum")
        
        if not isinstance(self.timestamp, datetime):
            raise ValueError("Timestamp must be a datetime object")
        
        if not isinstance(self.is_read, bool):
            raise ValueError("is_read must be a boolean")
        
        if self.action_url is not None and not isinstance(self.action_url, str):
            raise ValueError("action_url must be a string or None")

    def mark_as_read(self) -> None:
        """Mark the notification as read."""
        self.is_read = True

    def mark_as_unread(self) -> None:
        """Mark the notification as unread."""
        self.is_read = False

    def to_dict(self) -> dict:
        """Convert notification to dictionary for serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.type.value,
            'timestamp': self.timestamp.isoformat(),
            'is_read': self.is_read,
            'action_url': self.action_url
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Notification':
        """Create notification from dictionary."""
        return cls(
            id=data['id'],
            title=data['title'],
            message=data['message'],
            type=NotificationType(data['type']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            is_read=data['is_read'],
            action_url=data.get('action_url')
        )