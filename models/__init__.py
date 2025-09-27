# Models package initialization

from .notification import Notification, NotificationType
from .activity import Activity
from .time_entry import TimeEntry
from .workflow_state import WorkflowState, WorkflowStage, WorkflowStageStatus
from .interfaces import (
    NotificationServiceInterface,
    TimeTrackingServiceInterface,
    WorkflowServiceInterface,
    ActivityServiceInterface,
    StorageInterface,
    UIComponentInterface,
    TimerUpdateListener,
    NotificationListener,
    WorkflowListener,
    NotificationCallback,
    TimerCallback,
    WorkflowCallback,
    MAX_NOTIFICATION_TITLE_LENGTH,
    MAX_NOTIFICATION_MESSAGE_LENGTH,
    MAX_ACTIVITY_NAME_LENGTH,
    MAX_ACTIVITY_CATEGORY_LENGTH,
    MAX_TIME_ENTRY_NOTES_LENGTH,
    MAX_WORKFLOW_STAGE_NAME_LENGTH,
    DEFAULT_TIMER_UPDATE_INTERVAL,
    DEFAULT_NOTIFICATION_DISPLAY_DURATION,
    DEFAULT_MAX_NOTIFICATIONS
)

__all__ = [
    # Core models
    'Notification',
    'NotificationType',
    'Activity',
    'TimeEntry',
    'WorkflowState',
    'WorkflowStage',
    'WorkflowStageStatus',
    
    # Interfaces
    'NotificationServiceInterface',
    'TimeTrackingServiceInterface',
    'WorkflowServiceInterface',
    'ActivityServiceInterface',
    'StorageInterface',
    'UIComponentInterface',
    'TimerUpdateListener',
    'NotificationListener',
    'WorkflowListener',
    
    # Type aliases
    'NotificationCallback',
    'TimerCallback',
    'WorkflowCallback',
    
    # Constants
    'MAX_NOTIFICATION_TITLE_LENGTH',
    'MAX_NOTIFICATION_MESSAGE_LENGTH',
    'MAX_ACTIVITY_NAME_LENGTH',
    'MAX_ACTIVITY_CATEGORY_LENGTH',
    'MAX_TIME_ENTRY_NOTES_LENGTH',
    'MAX_WORKFLOW_STAGE_NAME_LENGTH',
    'DEFAULT_TIMER_UPDATE_INTERVAL',
    'DEFAULT_NOTIFICATION_DISPLAY_DURATION',
    'DEFAULT_MAX_NOTIFICATIONS'
]