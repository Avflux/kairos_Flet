import flet as ft
import math
import threading
from typing import Optional, List, Dict, Any
from datetime import timedelta

from models.activity import Activity
from models.time_entry import TimeEntry
from models.interfaces import TimerUpdateListener
from services.time_tracking_service import TimeTrackingService
from views.components.performance_utils import (
    performance_tracked, throttled, debounced, lifecycle_manager,
    layout_manager, animation_manager, ResponsiveLayoutManager
)
from views.components.error_handling import (
    create_error_boundary, get_fallback_manager, safe_execute
)
import logging


class TimeTrackerWidget(ft.Container, TimerUpdateListener):
    """Enhanced widget for time tracking with circular progress indicator and modern controls."""
    
    def __init__(self, page: ft.Page, time_tracking_service: TimeTrackingService):
        super().__init__()
        self.page = page
        self.time_service = time_tracking_service
        self.time_service.add_listener(self)
        
        # Error handling
        self.error_boundary = create_error_boundary("TimeTrackerWidget", page)
        self.fallback_manager = get_fallback_manager()
        
        # Register fallback component
        self.fallback_manager.register_fallback(
            "TimeTrackerWidget", 
            self._create_fallback_component
        )
        
        # Performance optimization: Register with lifecycle manager
        lifecycle_manager.register_component(self)
        
        # State
        self.current_activity: Optional[Activity] = None
        self.elapsed_time = timedelta()
        self.is_running = False
        self.is_paused = False
        self.max_session_time = timedelta(hours=8)  # 8 hour max for progress circle
        
        # Performance optimization: Track update frequency
        self._last_update_time = 0
        self._update_lock = threading.Lock()
        self._pending_update = False
        
        # Responsive layout state
        self._current_layout = 'desktop'
        layout_manager.register_layout_callback('time_tracker', self._on_layout_change)
        
        # Create circular progress indicator
        self.progress_ring = ft.ProgressRing(
            width=120,
            height=120,
            stroke_width=8,
            value=0,
            color='primary',
            bgcolor='surface_variant'
        )
        
        # Digital time display (centered in progress ring) - fonte melhorada
        self.time_display = ft.Text(
            "00:00:00",
            size=18,  # Tamanho aumentado
            weight=ft.FontWeight.W_600,  # Peso melhorado
            color='on_surface',
            text_align=ft.TextAlign.CENTER,
            font_family="monospace"  # Fonte monoespaçada para números
        )
        
        # Activity display - fonte melhorada
        self.activity_display = ft.Text(
            "No activity selected",
            size=13,  # Tamanho ligeiramente aumentado
            weight=ft.FontWeight.W_400,
            color='on_surface_variant',
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
            text_align=ft.TextAlign.CENTER
        )
        
        # Status display - fonte melhorada
        self.status_display = ft.Text(
            "Stopped",
            size=11,  # Tamanho ligeiramente aumentado
            weight=ft.FontWeight.W_500,
            color='on_surface_variant',
            text_align=ft.TextAlign.CENTER
        )
        
        # Modern control buttons with enhanced styling
        self.start_button = ft.ElevatedButton(
            text="Start",
            icon=ft.Icons.PLAY_ARROW,
            style=ft.ButtonStyle(
                color='on_primary',
                bgcolor='primary',
                elevation=2,
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=16, vertical=8)
            ),
            on_click=self._on_start_click
        )
        
        self.pause_button = ft.ElevatedButton(
            text="Pause",
            icon=ft.Icons.PAUSE,
            style=ft.ButtonStyle(
                color='on_secondary',
                bgcolor='secondary',
                elevation=2,
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=16, vertical=8)
            ),
            on_click=self._on_pause_click,
            visible=False
        )
        
        self.stop_button = ft.ElevatedButton(
            text="Stop",
            icon=ft.Icons.STOP,
            style=ft.ButtonStyle(
                color='on_error',
                bgcolor='error',
                elevation=2,
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=16, vertical=8)
            ),
            on_click=self._on_stop_click,
            visible=False
        )
        
        # Activity selection dropdown with modern styling
        self.activity_dropdown = ft.Dropdown(
            label="Select Activity",
            width=240,
            options=[],
            on_change=self._on_activity_change,
            border_radius=8,
            filled=True
        )
        
        # Quick activity input with modern styling
        self.quick_activity_field = ft.TextField(
            label="Quick activity",
            width=180,
            height=56,
            on_submit=self._on_quick_activity_submit,
            border_radius=8,
            filled=True
        )
        
        self.add_activity_button = ft.IconButton(
            icon=ft.Icons.ADD_CIRCLE,
            icon_color='primary',
            icon_size=24,
            tooltip="Add activity",
            on_click=self._on_add_activity_click,
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                bgcolor='primary_container',
                color='on_primary_container'
            )
        )
        
        # Visual state indicator
        self.state_indicator = ft.Container(
            width=16,
            height=16,
            border_radius=8,
            bgcolor='surface_variant'
        )
        
        # Build the widget
        self._build_widget()
        self._update_ui_state()
    
    def _build_widget(self):
        """Build the enhanced widget layout with circular progress indicator."""
        # Circular timer display with overlaid text
        timer_stack = ft.Stack([
            # Progress ring
            ft.Container(
                content=self.progress_ring,
                alignment=ft.alignment.center
            ),
            # Centered time and status display
            ft.Container(
                content=ft.Column([
                    self.time_display,
                    self.status_display
                ], 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
                tight=True),
                alignment=ft.alignment.center
            )
        ], width=120, height=120)
        
        # Timer section simplified - apenas título e tempo
        timer_section = ft.Container(
            content=ft.Column([
                ft.Text("Timer", size=14, weight=ft.FontWeight.W_600, color='on_surface'),
                self.time_display
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            padding=ft.padding.symmetric(horizontal=12, vertical=8)
        )
        
        # Modern controls section with responsive layout
        controls_section = ft.Container(
            content=ft.Row([
                self.start_button,
                self.pause_button,
                self.stop_button
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
            padding=ft.padding.symmetric(horizontal=16, vertical=8)
        )
        
        # Activity management section
        activity_section = ft.Container(
            content=ft.Column([
                self.activity_dropdown,
                ft.Row([
                    self.quick_activity_field,
                    self.add_activity_button
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=8)
            ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.all(16)
        )
        
        # Main layout with modern card styling
        # Layout simplificado - apenas timer
        self.content = ft.Container(
            content=timer_section,
            padding=ft.padding.all(8),
            width=None,  # Largura flexível
            height=None  # Altura flexível
        )
    
    @throttled(min_interval=0.1)  # Throttle UI updates to max 10 FPS
    @performance_tracked("time_tracker_ui_update")
    def _update_ui_state(self):
        """Update UI based on current state with smooth animations and performance optimization."""
        with self._update_lock:
            if self._pending_update:
                return  # Skip if update is already pending
            self._pending_update = True
        
        try:
            # Update time display
            self.time_display.value = self._format_time(self.elapsed_time)
            
            # Update circular progress indicator
            self._update_progress_ring()
            
            # Update activity display
            if self.current_activity:
                self.activity_display.value = self.current_activity.name
            else:
                self.activity_display.value = "No activity selected"
            
            # Update status display and visual feedback
            self._update_status_display()
            
            # Update button visibility and styling
            self._update_control_buttons()
            
            # Update state indicator with animation
            self._update_state_indicator()
            
            # Update activity controls
            self.activity_dropdown.disabled = self.is_running
            self.quick_activity_field.disabled = self.is_running
            self.add_activity_button.disabled = self.is_running
            
            # Batch page update for better performance
            if self.page:
                self.page.update()
        finally:
            with self._update_lock:
                self._pending_update = False
    
    def _update_progress_ring(self):
        """Update the circular progress indicator based on elapsed time."""
        if self.elapsed_time.total_seconds() > 0:
            # Calculate progress as percentage of max session time
            progress = min(self.elapsed_time.total_seconds() / self.max_session_time.total_seconds(), 1.0)
            self.progress_ring.value = progress
            
            # Change color based on progress
            if progress < 0.5:
                self.progress_ring.color = 'primary'
            elif progress < 0.8:
                self.progress_ring.color = 'secondary'
            else:
                self.progress_ring.color = 'error'
        else:
            self.progress_ring.value = 0
            self.progress_ring.color = 'primary'
    
    def _update_status_display(self):
        """Update status text and colors based on current state."""
        if self.is_running:
            if self.is_paused:
                self.status_display.value = "Paused"
                self.status_display.color = 'secondary'
            else:
                self.status_display.value = "Running"
                self.status_display.color = 'primary'
        else:
            self.status_display.value = "Stopped"
            self.status_display.color = 'on_surface_variant'
    
    def _update_control_buttons(self):
        """Update control button visibility and styling."""
        # Update button visibility
        self.start_button.visible = not self.is_running
        self.pause_button.visible = self.is_running
        self.stop_button.visible = self.is_running
        
        # Update pause button text and icon based on state
        if self.is_paused:
            self.pause_button.text = "Resume"
            self.pause_button.icon = ft.Icons.PLAY_ARROW
            self.pause_button.style.bgcolor = 'primary'
            self.pause_button.style.color = 'on_primary'
        else:
            self.pause_button.text = "Pause"
            self.pause_button.icon = ft.Icons.PAUSE
            self.pause_button.style.bgcolor = 'secondary'
            self.pause_button.style.color = 'on_secondary'
        
        # Disable start button if no activity selected
        self.start_button.disabled = self.current_activity is None
    
    def _update_state_indicator(self):
        """Update the visual state indicator with smooth color transitions."""
        if self.is_running:
            if self.is_paused:
                self.state_indicator.bgcolor = 'secondary'
            else:
                self.state_indicator.bgcolor = 'primary'
        else:
            self.state_indicator.bgcolor = 'surface_variant'
    
    def _format_time(self, time_delta: timedelta) -> str:
        """Format timedelta as HH:MM:SS string."""
        total_seconds = int(time_delta.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def _on_start_click(self, e):
        """Handle start button click with enhanced feedback."""
        if not self.current_activity:
            self._show_error("Please select an activity first")
            return
        
        try:
            self.time_service.start_tracking(self.current_activity)
            self._show_success(f"Started tracking: {self.current_activity.name}")
        except ValueError as ex:
            self._show_error(str(ex))
    
    def _on_pause_click(self, e):
        """Handle pause/resume button click with enhanced feedback."""
        if self.is_paused:
            if self.time_service.resume_tracking():
                self._show_success("Timer resumed")
            else:
                self._show_error("Failed to resume timer")
        else:
            if self.time_service.pause_tracking():
                self._show_success("Timer paused")
            else:
                self._show_error("Failed to pause timer")
    
    def _on_stop_click(self, e):
        """Handle stop button click with enhanced feedback."""
        activity_name = self.current_activity.name if self.current_activity else "Unknown"
        completed_entry = self.time_service.stop_tracking()
        if completed_entry:
            self._show_success(f"Completed: {self._format_time(completed_entry.duration)} for {activity_name}")
        else:
            self._show_error("No active tracking session to stop")
    
    def _on_activity_change(self, e):
        """Handle activity dropdown change."""
        if e.control.value:
            # In a real implementation, you would fetch the activity by ID
            # For now, create a simple activity
            self.current_activity = Activity(
                name=e.control.value,
                category="General"
            )
            self._update_ui_state()
    
    def _on_quick_activity_submit(self, e):
        """Handle quick activity field submit."""
        activity_name = e.control.value.strip()
        if activity_name:
            self._add_quick_activity(activity_name)
            e.control.value = ""
            self._update_ui_state()
    
    def _on_add_activity_click(self, e):
        """Handle add activity button click."""
        activity_name = self.quick_activity_field.value.strip()
        if activity_name:
            self._add_quick_activity(activity_name)
            self.quick_activity_field.value = ""
            self._update_ui_state()
    
    def _add_quick_activity(self, name: str):
        """Add a quick activity and select it."""
        self.current_activity = Activity(
            name=name,
            category="Quick"
        )
        
        # Add to dropdown if not already there
        existing_options = [opt.key for opt in self.activity_dropdown.options]
        if name not in existing_options:
            self.activity_dropdown.options.append(
                ft.dropdown.Option(key=name, text=name)
            )
        
        self.activity_dropdown.value = name
    
    def _show_error(self, message: str):
        """Show error message to user with modern styling."""
        if self.page:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Row([
                        ft.Icon(ft.Icons.ERROR_OUTLINE, color='on_error'),
                        ft.Text(message, color='on_error')
                    ], spacing=8),
                    bgcolor='error',
                    action="Dismiss",
                    action_color='on_error'
                )
            )
    
    def _show_success(self, message: str):
        """Show success message to user with modern styling."""
        if self.page:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color='on_primary'),
                        ft.Text(message, color='on_primary')
                    ], spacing=8),
                    bgcolor='primary',
                    action="Dismiss",
                    action_color='on_primary'
                )
            )
    
    # TimerUpdateListener implementation with performance optimization
    def on_timer_start(self, activity: Activity) -> None:
        """Called when timer starts."""
        self.current_activity = activity
        self.is_running = True
        self.is_paused = False
        self._update_ui_state()
    
    def on_timer_stop(self, time_entry: TimeEntry) -> None:
        """Called when timer stops."""
        self.is_running = False
        self.is_paused = False
        self.elapsed_time = timedelta()
        self._update_ui_state()
    
    def on_timer_pause(self) -> None:
        """Called when timer is paused."""
        self.is_paused = True
        self._update_ui_state()
    
    def on_timer_resume(self) -> None:
        """Called when timer is resumed."""
        self.is_paused = False
        self._update_ui_state()
    
    @throttled(min_interval=2.0)  # Throttle timer ticks to 0.5 FPS to reduce WebView loading indicators
    def on_timer_tick(self, elapsed_time: timedelta) -> None:
        """Called on each timer update with performance optimization."""
        self.elapsed_time = elapsed_time
        self._update_ui_state()
    
    def _on_layout_change(self, breakpoint: str, width: float) -> None:
        """Handle responsive layout changes."""
        self._current_layout = breakpoint
        
        if layout_manager.is_mobile():
            # Mobile layout optimizations
            self.width = min(280, width - 32)
            self.progress_ring.width = 80
            self.progress_ring.height = 80
        elif layout_manager.is_tablet():
            # Tablet layout optimizations
            self.width = min(320, width - 48)
            self.progress_ring.width = 100
            self.progress_ring.height = 100
        else:
            # Desktop layout (default)
            self.width = 300
            self.progress_ring.width = 120
            self.progress_ring.height = 120
        
        # Rebuild layout if needed
        if self.page:
            self._build_widget()
            self.page.update()
    
    def cleanup(self) -> None:
        """Clean up resources to prevent memory leaks."""
        # Remove timer listener
        if hasattr(self.time_service, 'remove_listener'):
            self.time_service.remove_listener(self)
        
        # Clean up lifecycle manager
        lifecycle_manager.cleanup_component(self)
    
    def set_activities(self, activities: List[Activity]):
        """Set available activities for selection."""
        self.activity_dropdown.options = [
            ft.dropdown.Option(key=activity.name, text=activity.name)
            for activity in activities
        ]
        if self.page:
            self.page.update()
    
    def refresh(self):
        """Refresh the widget state."""
        # Sync with service state
        self.is_running = self.time_service.is_tracking()
        self.is_paused = self.time_service.is_paused()
        
        if self.is_running:
            self.elapsed_time = self.time_service.get_elapsed_time()
            current_entry = self.time_service.get_current_entry()
            if current_entry:
                # In a real implementation, you would fetch the activity by ID
                # For now, keep the current activity if it matches
                pass
        else:
            self.elapsed_time = timedelta()
            self.current_activity = None
        
        self._update_ui_state()  
  
    def _create_fallback_component(self, error_message: str) -> ft.Control:
        """Create a fallback component when time tracker fails."""
        return ft.Container(
            content=ft.Column([
                ft.Icon(
                    ft.Icons.TIMER_OFF_OUTLINED,
                    size=48,
                    color=ft.Colors.GREY_400
                ),
                ft.Text(
                    "Time Tracker Unavailable",
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
                    on_click=self._retry_time_tracker,
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
            border_radius=16,
            border=ft.border.all(1, ft.Colors.GREY_200),
            width=300,
            height=400
        )
    
    def _retry_time_tracker(self, e) -> None:
        """Retry initializing the time tracker."""
        def retry_operation():
            # Reinitialize the time tracker
            self.__init__(self.page, self.time_service)
            if self.page:
                self.page.update()
        
        safe_execute(
            retry_operation,
            "TimeTrackerWidget",
            "retry_initialization",
            self.page
        )
    
    def _safe_start_click(self, e) -> None:
        """Safely handle start button click."""
        def start_operation():
            self._on_start_click(e)
        
        safe_execute(
            start_operation,
            "TimeTrackerWidget",
            "start_tracking",
            self.page,
            user_data={"activity": self.current_activity.name if self.current_activity else None}
        )
    
    def _safe_pause_click(self, e) -> None:
        """Safely handle pause button click."""
        def pause_operation():
            self._on_pause_click(e)
        
        safe_execute(
            pause_operation,
            "TimeTrackerWidget",
            "pause_tracking",
            self.page
        )
    
    def _safe_stop_click(self, e) -> None:
        """Safely handle stop button click."""
        def stop_operation():
            self._on_stop_click(e)
        
        safe_execute(
            stop_operation,
            "TimeTrackerWidget",
            "stop_tracking",
            self.page,
            user_data={"activity": self.current_activity.name if self.current_activity else None}
        )
    
    def _safe_update_ui_state(self) -> None:
        """Safely update UI state with error handling."""
        def update_operation():
            self._update_ui_state()
        
        result = safe_execute(
            update_operation,
            "TimeTrackerWidget",
            "update_ui",
            self.page,
            fallback_result=False
        )
        
        if result is False:
            self._show_error_state("Failed to update timer display")
    
    def _show_error_state(self, error_message: str) -> None:
        """Show error state in the time tracker."""
        try:
            # Update time display to show error
            self.time_display.value = "ERROR"
            self.time_display.color = ft.Colors.RED_600
            
            # Update status display
            self.status_display.value = "Error"
            self.status_display.color = ft.Colors.RED_600
            
            # Update activity display
            self.activity_display.value = error_message
            self.activity_display.color = ft.Colors.RED_500
            
            # Disable all controls
            self.start_button.disabled = True
            self.pause_button.disabled = True
            self.stop_button.disabled = True
            
            # Update progress ring to show error state
            self.progress_ring.value = 0
            self.progress_ring.color = ft.Colors.RED_400
            
            # Update state indicator
            self.state_indicator.bgcolor = ft.Colors.RED_400
            
            if self.page:
                self.page.update()
                
        except Exception as e:
            logging.error(f"Failed to show error state in time tracker: {e}")
    
    def _recover_from_error(self) -> bool:
        """Attempt to recover from error state."""
        try:
            # Reset UI state
            self.time_display.color = 'on_surface'
            self.status_display.color = 'on_surface_variant'
            self.activity_display.color = 'on_surface_variant'
            
            # Re-enable controls
            self.start_button.disabled = False
            self.pause_button.disabled = False
            self.stop_button.disabled = False
            
            # Sync with service state
            self.refresh()
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to recover from error state: {e}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get the health status of the time tracker."""
        try:
            return {
                "component": "TimeTrackerWidget",
                "status": "healthy",
                "is_tracking": self.is_running,
                "is_paused": self.is_paused,
                "current_activity": self.current_activity.name if self.current_activity else None,
                "elapsed_time": str(self.elapsed_time),
                "last_update": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "component": "TimeTrackerWidget",
                "status": "error",
                "error": str(e),
                "last_update": datetime.now().isoformat()
            }
    
    # Override timer listener methods with error handling
    def on_timer_start(self, activity: Activity) -> None:
        """Called when timer starts with error handling."""
        try:
            self.current_activity = activity
            self.is_running = True
            self.is_paused = False
            self._safe_update_ui_state()
        except Exception as e:
            logging.error(f"Error in timer start handler: {e}")
            self._show_error_state("Timer start failed")
    
    def on_timer_stop(self, time_entry: TimeEntry) -> None:
        """Called when timer stops with error handling."""
        try:
            self.is_running = False
            self.is_paused = False
            self.elapsed_time = timedelta()
            self._safe_update_ui_state()
        except Exception as e:
            logging.error(f"Error in timer stop handler: {e}")
            self._show_error_state("Timer stop failed")
    
    def on_timer_pause(self) -> None:
        """Called when timer is paused with error handling."""
        try:
            self.is_paused = True
            self._safe_update_ui_state()
        except Exception as e:
            logging.error(f"Error in timer pause handler: {e}")
            self._show_error_state("Timer pause failed")
    
    def on_timer_resume(self) -> None:
        """Called when timer is resumed with error handling."""
        try:
            self.is_paused = False
            self._safe_update_ui_state()
        except Exception as e:
            logging.error(f"Error in timer resume handler: {e}")
            self._show_error_state("Timer resume failed")
    
    def on_timer_tick(self, elapsed_time: timedelta) -> None:
        """Called on each timer update with error handling."""
        try:
            self.elapsed_time = elapsed_time
            self._safe_update_ui_state()
        except Exception as e:
            logging.error(f"Error in timer tick handler: {e}")
            # Don't show error state for tick failures as they're frequent