from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Protocol
from datetime import datetime, timedelta

from .notification import Notification, NotificationType
from .activity import Activity
from .time_entry import TimeEntry
from .workflow_state import WorkflowState, WorkflowStage


class NotificationServiceInterface(ABC):
    """Interface for notification service operations."""
    
    @abstractmethod
    def add_notification(self, notification: Notification) -> None:
        """Add a new notification to the system."""
        pass
    
    @abstractmethod
    def get_notifications(self, limit: Optional[int] = None) -> List[Notification]:
        """Get all notifications, optionally limited."""
        pass
    
    @abstractmethod
    def get_unread_notifications(self) -> List[Notification]:
        """Get all unread notifications."""
        pass
    
    @abstractmethod
    def mark_as_read(self, notification_id: str) -> bool:
        """Mark a notification as read. Returns True if successful."""
        pass
    
    @abstractmethod
    def mark_all_as_read(self) -> int:
        """Mark all notifications as read. Returns count of notifications marked."""
        pass
    
    @abstractmethod
    def clear_all(self) -> int:
        """Clear all notifications. Returns count of notifications cleared."""
        pass
    
    @abstractmethod
    def get_unread_count(self) -> int:
        """Get count of unread notifications."""
        pass


class TimeTrackingServiceInterface(ABC):
    """Interface for time tracking service operations."""
    
    @abstractmethod
    def start_tracking(self, activity: Activity) -> TimeEntry:
        """Start tracking time for an activity."""
        pass
    
    @abstractmethod
    def stop_tracking(self) -> Optional[TimeEntry]:
        """Stop current time tracking. Returns the completed time entry."""
        pass
    
    @abstractmethod
    def pause_tracking(self) -> bool:
        """Pause current time tracking. Returns True if successful."""
        pass
    
    @abstractmethod
    def resume_tracking(self) -> bool:
        """Resume paused time tracking. Returns True if successful."""
        pass
    
    @abstractmethod
    def get_current_entry(self) -> Optional[TimeEntry]:
        """Get the currently active time entry."""
        pass
    
    @abstractmethod
    def get_time_entries(self, activity_id: Optional[str] = None) -> List[TimeEntry]:
        """Get time entries, optionally filtered by activity."""
        pass
    
    @abstractmethod
    def is_tracking(self) -> bool:
        """Check if time tracking is currently active."""
        pass
    
    @abstractmethod
    def get_elapsed_time(self) -> timedelta:
        """Get elapsed time for current tracking session."""
        pass


class WorkflowServiceInterface(ABC):
    """Interface for workflow service operations."""
    
    @abstractmethod
    def get_workflow_state(self, project_id: Optional[str] = None) -> Optional[WorkflowState]:
        """Get current workflow state for a project."""
        pass
    
    @abstractmethod
    def update_workflow_state(self, workflow_state: WorkflowState) -> None:
        """Update workflow state."""
        pass
    
    @abstractmethod
    def advance_to_stage(self, stage_name: str, project_id: Optional[str] = None) -> bool:
        """Advance workflow to a specific stage."""
        pass
    
    @abstractmethod
    def complete_current_stage(self, project_id: Optional[str] = None) -> bool:
        """Complete current stage and advance to next."""
        pass
    
    @abstractmethod
    def get_available_stages(self, project_id: Optional[str] = None) -> List[WorkflowStage]:
        """Get all available workflow stages."""
        pass
    
    @abstractmethod
    def create_default_workflow(self, project_id: Optional[str] = None) -> WorkflowState:
        """Create a default workflow for a project."""
        pass


class ActivityServiceInterface(ABC):
    """Interface for activity service operations."""
    
    @abstractmethod
    def create_activity(self, name: str, category: str, description: Optional[str] = None) -> Activity:
        """Create a new activity."""
        pass
    
    @abstractmethod
    def get_activities(self, category: Optional[str] = None) -> List[Activity]:
        """Get activities, optionally filtered by category."""
        pass
    
    @abstractmethod
    def get_activity(self, activity_id: str) -> Optional[Activity]:
        """Get a specific activity by ID."""
        pass
    
    @abstractmethod
    def update_activity(self, activity: Activity) -> bool:
        """Update an existing activity."""
        pass
    
    @abstractmethod
    def delete_activity(self, activity_id: str) -> bool:
        """Delete an activity."""
        pass
    
    @abstractmethod
    def get_categories(self) -> List[str]:
        """Get all available activity categories."""
        pass


class StorageInterface(ABC):
    """Interface for data storage operations."""
    
    @abstractmethod
    def save(self, key: str, data: Dict[str, Any]) -> bool:
        """Save data with a key."""
        pass
    
    @abstractmethod
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load data by key."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete data by key."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in storage."""
        pass
    
    @abstractmethod
    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all keys, optionally with prefix filter."""
        pass


class UIComponentInterface(Protocol):
    """Protocol for UI components that can be updated and rendered."""
    
    def update_display(self) -> None:
        """Update the component's display."""
        ...
    
    def refresh(self) -> None:
        """Refresh the component's data and display."""
        ...
    
    def set_visible(self, visible: bool) -> None:
        """Set component visibility."""
        ...


class TimerUpdateListener(Protocol):
    """Protocol for components that listen to timer updates."""
    
    def on_timer_start(self, activity: Activity) -> None:
        """Called when timer starts."""
        ...
    
    def on_timer_stop(self, time_entry: TimeEntry) -> None:
        """Called when timer stops."""
        ...
    
    def on_timer_pause(self) -> None:
        """Called when timer is paused."""
        ...
    
    def on_timer_resume(self) -> None:
        """Called when timer is resumed."""
        ...
    
    def on_timer_tick(self, elapsed_time: timedelta) -> None:
        """Called on each timer update."""
        ...


class NotificationListener(Protocol):
    """Protocol for components that listen to notification events."""
    
    def on_notification_added(self, notification: Notification) -> None:
        """Called when a new notification is added."""
        ...
    
    def on_notification_read(self, notification_id: str) -> None:
        """Called when a notification is marked as read."""
        ...
    
    def on_notifications_cleared(self) -> None:
        """Called when all notifications are cleared."""
        ...


class WorkflowListener(Protocol):
    """Protocol for components that listen to workflow events."""
    
    def on_workflow_stage_changed(self, old_stage: str, new_stage: str) -> None:
        """Called when workflow stage changes."""
        ...
    
    def on_workflow_completed(self, workflow_state: WorkflowState) -> None:
        """Called when workflow is completed."""
        ...
    
    def on_workflow_updated(self, workflow_state: WorkflowState) -> None:
        """Called when workflow state is updated."""
        ...


# Type aliases for common data structures
from typing import Callable
NotificationCallback = Callable[[Notification], None]
TimerCallback = Callable[[timedelta], None]
WorkflowCallback = Callable[[WorkflowState], None]

# Constants for validation
MAX_NOTIFICATION_TITLE_LENGTH = 100
MAX_NOTIFICATION_MESSAGE_LENGTH = 500
MAX_ACTIVITY_NAME_LENGTH = 100
MAX_ACTIVITY_CATEGORY_LENGTH = 50
MAX_TIME_ENTRY_NOTES_LENGTH = 500
MAX_WORKFLOW_STAGE_NAME_LENGTH = 100

# Default values
DEFAULT_TIMER_UPDATE_INTERVAL = 1.0  # seconds
DEFAULT_NOTIFICATION_DISPLAY_DURATION = 5.0  # seconds
DEFAULT_MAX_NOTIFICATIONS = 100