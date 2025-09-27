"""
Comprehensive error handling and user feedback system for the Kairos application.
Provides graceful error handling, fallback displays, and non-blocking error messages.
"""

import flet as ft
import logging
import traceback
from typing import Optional, Callable, Dict, Any, List, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from contextlib import contextmanager
import threading
import json
import os


class ErrorSeverity(Enum):
    """Error severity levels for categorization and handling."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeedbackType(Enum):
    """Types of user feedback messages."""
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ErrorContext:
    """Context information for error tracking and recovery."""
    component_name: str
    operation: str
    timestamp: datetime = field(default_factory=datetime.now)
    user_data: Dict[str, Any] = field(default_factory=dict)
    recovery_actions: List[str] = field(default_factory=list)
    severity: ErrorSeverity = ErrorSeverity.MEDIUM


@dataclass
class FeedbackMessage:
    """User feedback message with metadata."""
    id: str
    type: FeedbackType
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    duration: Optional[timedelta] = None
    action_text: Optional[str] = None
    action_callback: Optional[Callable] = None
    dismissible: bool = True


class ErrorRecoveryManager:
    """Manages error recovery strategies and fallback mechanisms."""
    
    def __init__(self):
        self._recovery_strategies: Dict[str, Callable] = {}
        self._fallback_data: Dict[str, Any] = {}
        self._error_history: List[ErrorContext] = []
        self._max_history = 100
    
    def register_recovery_strategy(self, error_type: str, strategy: Callable) -> None:
        """Register a recovery strategy for a specific error type."""
        self._recovery_strategies[error_type] = strategy
    
    def set_fallback_data(self, key: str, data: Any) -> None:
        """Set fallback data for when primary data is unavailable."""
        self._fallback_data[key] = data
    
    def get_fallback_data(self, key: str, default: Any = None) -> Any:
        """Get fallback data for a specific key."""
        return self._fallback_data.get(key, default)
    
    def attempt_recovery(self, error_type: str, context: ErrorContext) -> bool:
        """Attempt to recover from an error using registered strategies."""
        strategy = self._recovery_strategies.get(error_type)
        if strategy:
            try:
                return strategy(context)
            except Exception as e:
                logging.error(f"Recovery strategy failed for {error_type}: {e}")
        return False
    
    def record_error(self, context: ErrorContext) -> None:
        """Record an error in the history for analysis."""
        self._error_history.append(context)
        if len(self._error_history) > self._max_history:
            self._error_history.pop(0)
    
    def get_error_patterns(self) -> Dict[str, int]:
        """Analyze error patterns for proactive handling."""
        patterns = {}
        for error in self._error_history:
            key = f"{error.component_name}:{error.operation}"
            patterns[key] = patterns.get(key, 0) + 1
        return patterns


class LocalStorageManager:
    """Manages local storage backup for critical data."""
    
    def __init__(self, storage_dir: str = "data/backup"):
        self.storage_dir = storage_dir
        self._ensure_storage_directory()
        self._lock = threading.Lock()
    
    def _ensure_storage_directory(self) -> None:
        """Ensure the storage directory exists."""
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)
    
    def backup_data(self, key: str, data: Any) -> bool:
        """Backup data to local storage."""
        try:
            with self._lock:
                file_path = os.path.join(self.storage_dir, f"{key}.json")
                backup_data = {
                    'data': data,
                    'timestamp': datetime.now().isoformat(),
                    'version': '1.0'
                }
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, default=str)
                return True
        except Exception as e:
            logging.error(f"Failed to backup data for {key}: {e}")
            return False
    
    def restore_data(self, key: str) -> Optional[Any]:
        """Restore data from local storage."""
        try:
            with self._lock:
                file_path = os.path.join(self.storage_dir, f"{key}.json")
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        backup_data = json.load(f)
                        return backup_data.get('data')
        except Exception as e:
            logging.error(f"Failed to restore data for {key}: {e}")
        return None
    
    def clear_backup(self, key: str) -> bool:
        """Clear backup data for a specific key."""
        try:
            with self._lock:
                file_path = os.path.join(self.storage_dir, f"{key}.json")
                if os.path.exists(file_path):
                    os.remove(file_path)
                return True
        except Exception as e:
            logging.error(f"Failed to clear backup for {key}: {e}")
            return False
    
    def list_backups(self) -> List[str]:
        """List all available backup keys."""
        try:
            backups = []
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    backups.append(filename[:-5])  # Remove .json extension
            return backups
        except Exception as e:
            logging.error(f"Failed to list backups: {e}")
            return []


class ToastNotificationManager:
    """Manages non-blocking toast notifications for user feedback."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self._active_toasts: Dict[str, FeedbackMessage] = {}
        self._toast_queue: List[FeedbackMessage] = []
        self._max_concurrent_toasts = 3
        self._default_durations = {
            FeedbackType.SUCCESS: timedelta(seconds=3),
            FeedbackType.INFO: timedelta(seconds=4),
            FeedbackType.WARNING: timedelta(seconds=5),
            FeedbackType.ERROR: timedelta(seconds=6)
        }
    
    def show_toast(
        self,
        message: str,
        feedback_type: FeedbackType = FeedbackType.INFO,
        title: Optional[str] = None,
        duration: Optional[timedelta] = None,
        action_text: Optional[str] = None,
        action_callback: Optional[Callable] = None
    ) -> str:
        """Show a toast notification."""
        toast_id = f"toast_{datetime.now().timestamp()}"
        
        feedback_message = FeedbackMessage(
            id=toast_id,
            type=feedback_type,
            title=title or feedback_type.value.title(),
            message=message,
            duration=duration or self._default_durations.get(feedback_type, timedelta(seconds=4)),
            action_text=action_text,
            action_callback=action_callback
        )
        
        if len(self._active_toasts) < self._max_concurrent_toasts:
            self._display_toast(feedback_message)
        else:
            self._toast_queue.append(feedback_message)
        
        return toast_id
    
    def _display_toast(self, feedback_message: FeedbackMessage) -> None:
        """Display a toast notification on the page."""
        self._active_toasts[feedback_message.id] = feedback_message
        
        # Create toast UI
        toast_content = self._create_toast_content(feedback_message)
        
        # Show as snack bar
        snack_bar = ft.SnackBar(
            content=toast_content,
            bgcolor=self._get_toast_color(feedback_message.type),
            action=feedback_message.action_text,
            action_color="white",
            on_action=feedback_message.action_callback if feedback_message.action_callback else None,
            duration=int(feedback_message.duration.total_seconds() * 1000) if feedback_message.duration else 4000
        )
        
        self.page.show_snack_bar(snack_bar)
        
        # Auto-dismiss after duration
        if feedback_message.duration:
            threading.Timer(
                feedback_message.duration.total_seconds(),
                self._dismiss_toast,
                args=[feedback_message.id]
            ).start()
    
    def _create_toast_content(self, feedback_message: FeedbackMessage) -> ft.Control:
        """Create the content for a toast notification."""
        icon_map = {
            FeedbackType.SUCCESS: ft.Icons.CHECK_CIRCLE_OUTLINE,
            FeedbackType.INFO: ft.Icons.INFO_OUTLINE,
            FeedbackType.WARNING: ft.Icons.WARNING_OUTLINED,
            FeedbackType.ERROR: ft.Icons.ERROR_OUTLINE
        }
        
        icon = ft.Icon(
            icon_map.get(feedback_message.type, ft.Icons.INFO_OUTLINE),
            color="white",
            size=20
        )
        
        content_column = [
            ft.Text(
                feedback_message.message,
                color="white",
                size=14,
                weight=ft.FontWeight.W_400
            )
        ]
        
        if feedback_message.title and feedback_message.title != feedback_message.type.value.title():
            content_column.insert(0, ft.Text(
                feedback_message.title,
                color="white",
                size=16,
                weight=ft.FontWeight.W_600
            ))
        
        return ft.Row([
            icon,
            ft.Column(content_column, spacing=2, tight=True)
        ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    
    def _get_toast_color(self, feedback_type: FeedbackType) -> str:
        """Get the background color for a toast type."""
        color_map = {
            FeedbackType.SUCCESS: ft.Colors.GREEN_600,
            FeedbackType.INFO: ft.Colors.BLUE_600,
            FeedbackType.WARNING: ft.Colors.ORANGE_600,
            FeedbackType.ERROR: ft.Colors.RED_600
        }
        return color_map.get(feedback_type, ft.Colors.BLUE_600)
    
    def _dismiss_toast(self, toast_id: str) -> None:
        """Dismiss a toast notification."""
        if toast_id in self._active_toasts:
            del self._active_toasts[toast_id]
            
            # Show next toast in queue if available
            if self._toast_queue:
                next_toast = self._toast_queue.pop(0)
                self._display_toast(next_toast)
    
    def dismiss_all_toasts(self) -> None:
        """Dismiss all active toast notifications."""
        self._active_toasts.clear()
        self._toast_queue.clear()
    
    def show_success(self, message: str, title: str = "Success") -> str:
        """Show a success toast notification."""
        return self.show_toast(message, FeedbackType.SUCCESS, title)
    
    def show_error(self, message: str, title: str = "Error") -> str:
        """Show an error toast notification."""
        return self.show_toast(message, FeedbackType.ERROR, title)
    
    def show_warning(self, message: str, title: str = "Warning") -> str:
        """Show a warning toast notification."""
        return self.show_toast(message, FeedbackType.WARNING, title)
    
    def show_info(self, message: str, title: str = "Info") -> str:
        """Show an info toast notification."""
        return self.show_toast(message, FeedbackType.INFO, title)


class ErrorBoundary:
    """Error boundary for wrapping components with error handling."""
    
    def __init__(
        self,
        component_name: str,
        toast_manager: ToastNotificationManager,
        recovery_manager: ErrorRecoveryManager,
        storage_manager: LocalStorageManager
    ):
        self.component_name = component_name
        self.toast_manager = toast_manager
        self.recovery_manager = recovery_manager
        self.storage_manager = storage_manager
        self._error_count = 0
        self._max_errors = 5
        self._error_window = timedelta(minutes=5)
        self._last_error_time: Optional[datetime] = None
    
    @contextmanager
    def handle_errors(self, operation: str, user_data: Optional[Dict[str, Any]] = None):
        """Context manager for handling errors in operations."""
        context = ErrorContext(
            component_name=self.component_name,
            operation=operation,
            user_data=user_data or {}
        )
        
        try:
            yield context
        except Exception as e:
            self._handle_error(e, context)
    
    def _handle_error(self, error: Exception, context: ErrorContext) -> None:
        """Handle an error with appropriate recovery and user feedback."""
        # Determine error severity
        context.severity = self._determine_severity(error, context)
        
        # Record error
        self.recovery_manager.record_error(context)
        
        # Check for error rate limiting
        if self._should_rate_limit():
            logging.warning(f"Error rate limit reached for {self.component_name}")
            return
        
        # Attempt recovery
        error_type = type(error).__name__
        recovery_attempted = self.recovery_manager.attempt_recovery(error_type, context)
        
        # Backup critical data if needed
        if context.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self._backup_critical_data(context)
        
        # Show user feedback
        self._show_user_feedback(error, context, recovery_attempted)
        
        # Log error
        self._log_error(error, context)
    
    def _determine_severity(self, error: Exception, context: ErrorContext) -> ErrorSeverity:
        """Determine the severity of an error."""
        # Critical errors that break core functionality
        if isinstance(error, (MemoryError, SystemError)):
            return ErrorSeverity.CRITICAL
        
        # High severity for data loss or corruption
        if isinstance(error, (FileNotFoundError, PermissionError)) and 'save' in context.operation.lower():
            return ErrorSeverity.HIGH
        
        # Medium severity for service failures
        if isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorSeverity.MEDIUM
        
        # Low severity for validation or user input errors
        if isinstance(error, (ValueError, TypeError)):
            return ErrorSeverity.LOW
        
        return ErrorSeverity.MEDIUM
    
    def _should_rate_limit(self) -> bool:
        """Check if error rate limiting should be applied."""
        now = datetime.now()
        
        if self._last_error_time is None:
            self._last_error_time = now
            self._error_count = 1
            return False
        
        if now - self._last_error_time > self._error_window:
            # Reset error count if outside window
            self._error_count = 1
            self._last_error_time = now
            return False
        
        self._error_count += 1
        self._last_error_time = now
        
        return self._error_count > self._max_errors
    
    def _backup_critical_data(self, context: ErrorContext) -> None:
        """Backup critical data when high severity errors occur."""
        if context.user_data:
            backup_key = f"{self.component_name}_{context.operation}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            success = self.storage_manager.backup_data(backup_key, context.user_data)
            if success:
                context.recovery_actions.append(f"Data backed up as {backup_key}")
    
    def _show_user_feedback(self, error: Exception, context: ErrorContext, recovery_attempted: bool) -> None:
        """Show appropriate user feedback based on error severity."""
        if context.severity == ErrorSeverity.CRITICAL:
            self.toast_manager.show_error(
                f"Critical error in {self.component_name}. Please restart the application.",
                "Critical Error"
            )
        elif context.severity == ErrorSeverity.HIGH:
            message = f"Error in {context.operation}. "
            if recovery_attempted:
                message += "Recovery attempted. Please check your data."
            else:
                message += "Please try again or contact support."
            
            self.toast_manager.show_error(message, "Error")
        elif context.severity == ErrorSeverity.MEDIUM:
            message = f"Service temporarily unavailable. "
            if recovery_attempted:
                message += "Retrying automatically."
            else:
                message += "Please try again later."
            
            self.toast_manager.show_warning(message, "Service Issue")
        else:  # LOW severity
            self.toast_manager.show_info(
                f"Please check your input and try again.",
                "Input Error"
            )
    
    def _log_error(self, error: Exception, context: ErrorContext) -> None:
        """Log error details for debugging."""
        logging.error(
            f"Error in {context.component_name}.{context.operation}: "
            f"{type(error).__name__}: {str(error)}\n"
            f"Severity: {context.severity.value}\n"
            f"Context: {context.user_data}\n"
            f"Traceback: {traceback.format_exc()}"
        )


class FallbackDisplayManager:
    """Manages fallback displays for component failures."""
    
    def __init__(self):
        self._fallback_components: Dict[str, Callable] = {}
    
    def register_fallback(self, component_name: str, fallback_factory: Callable) -> None:
        """Register a fallback component factory."""
        self._fallback_components[component_name] = fallback_factory
    
    def get_fallback_component(self, component_name: str, error_message: str = "Component unavailable") -> ft.Control:
        """Get a fallback component for a failed component."""
        if component_name in self._fallback_components:
            try:
                return self._fallback_components[component_name](error_message)
            except Exception as e:
                logging.error(f"Fallback component factory failed for {component_name}: {e}")
        
        # Default fallback
        return self._create_default_fallback(component_name, error_message)
    
    def _create_default_fallback(self, component_name: str, error_message: str) -> ft.Control:
        """Create a default fallback component."""
        return ft.Container(
            content=ft.Column([
                ft.Icon(
                    ft.Icons.ERROR_OUTLINE,
                    size=48,
                    color=ft.Colors.GREY_400
                ),
                ft.Text(
                    f"{component_name} Unavailable",
                    size=16,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.GREY_600,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    error_message,
                    size=12,
                    color=ft.Colors.GREY_500,
                    text_align=ft.TextAlign.CENTER,
                    max_lines=2
                ),
                ft.ElevatedButton(
                    "Retry",
                    icon=ft.Icons.REFRESH,
                    on_click=lambda e: None,  # Will be overridden by component
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE_100,
                        color=ft.Colors.BLUE_800
                    )
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12
            ),
            padding=ft.padding.all(24),
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.GREY_50,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_200)
        )


# Global instances for easy access
_recovery_manager = ErrorRecoveryManager()
_storage_manager = LocalStorageManager()
_fallback_manager = FallbackDisplayManager()


def get_recovery_manager() -> ErrorRecoveryManager:
    """Get the global error recovery manager."""
    return _recovery_manager


def get_storage_manager() -> LocalStorageManager:
    """Get the global local storage manager."""
    return _storage_manager


def get_fallback_manager() -> FallbackDisplayManager:
    """Get the global fallback display manager."""
    return _fallback_manager


def create_error_boundary(
    component_name: str,
    page: ft.Page
) -> ErrorBoundary:
    """Create an error boundary for a component."""
    toast_manager = ToastNotificationManager(page)
    return ErrorBoundary(
        component_name=component_name,
        toast_manager=toast_manager,
        recovery_manager=_recovery_manager,
        storage_manager=_storage_manager
    )


def safe_execute(
    func: Callable,
    component_name: str,
    operation: str,
    page: ft.Page,
    fallback_result: Any = None,
    user_data: Optional[Dict[str, Any]] = None
) -> Any:
    """Safely execute a function with error handling."""
    error_boundary = create_error_boundary(component_name, page)
    
    try:
        with error_boundary.handle_errors(operation, user_data):
            return func()
    except Exception:
        return fallback_result