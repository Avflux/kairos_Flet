import flet as ft
from typing import Optional
from views.components.time_tracker_widget import TimeTrackerWidget
from views.components.flowchart_widget import FlowchartWidget
from views.components.notification_center import NotificationCenter
from services.time_tracking_service import TimeTrackingService
from services.workflow_service import WorkflowService
from services.notification_service import NotificationService
from views.components.performance_utils import (
    performance_tracked, throttled, debounced, lifecycle_manager,
    layout_manager, animation_manager
)


class TopSidebarContainer(ft.Container):
    """
    Container that houses time tracker, flowchart, and notification center
    in a responsive horizontal layout that adapts to sidebar expansion state.
    """
    
    def __init__(
        self, 
        page: ft.Page,
        time_tracking_service: Optional[TimeTrackingService] = None,
        workflow_service: Optional[WorkflowService] = None,
        notification_service: Optional[NotificationService] = None
    ):
        """
        Initialize the top sidebar container.
        
        Args:
            page: The Flet page instance
            time_tracking_service: Service for time tracking functionality
            workflow_service: Service for workflow management
            notification_service: Service for notification management
        """
        super().__init__()
        
        self.page = page
        self.sidebar_expanded = True  # Track sidebar state
        
        # Performance optimization: Register with lifecycle manager
        lifecycle_manager.register_component(self)
        
        # Initialize services with defaults if not provided
        self.time_tracking_service = time_tracking_service or TimeTrackingService()
        self.workflow_service = workflow_service or WorkflowService()
        self.notification_service = notification_service or NotificationService()
        
        # Responsive layout state
        self._current_breakpoint = 'lg'
        layout_manager.register_layout_callback('top_sidebar', self._on_layout_change)
        
        # Initialize component widgets
        self.time_tracker = TimeTrackerWidget(page, self.time_tracking_service)
        self.flowchart = FlowchartWidget(page, self.workflow_service)
        self.notifications = NotificationCenter(page, self.notification_service)
        
        # Initialize default workflow for demonstration
        self.flowchart.create_default_workflow("default_project")
        
        # Build the container layout
        self._build_layout()
    
    @performance_tracked("top_sidebar_layout_build")
    def _build_layout(self):
        """Build the responsive horizontal layout with performance optimization."""
        # Determine layout based on both sidebar state and screen size
        is_mobile = layout_manager.is_mobile()
        is_tablet = layout_manager.is_tablet()
        
        if is_mobile:
            # Mobile layout - stack vertically or show minimal components
            layout = self._create_mobile_layout()
        elif is_tablet:
            # Tablet layout - compact horizontal layout
            layout = self._create_tablet_layout()
        elif self.sidebar_expanded:
            # Desktop expanded layout
            layout = self._create_desktop_expanded_layout()
        else:
            # Desktop collapsed layout
            layout = self._create_desktop_collapsed_layout()
    
    def _create_mobile_layout(self) -> ft.Row:
        """Create mobile-optimized layout."""
        return ft.Row(
            controls=[
                # Only show essential components on mobile
                ft.Container(
                    content=self._create_compact_time_tracker(),
                    width=50,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    content=self._create_compact_flowchart(),
                    expand=1,
                    alignment=ft.alignment.center,
                    padding=ft.padding.symmetric(horizontal=4)
                ),
                ft.Container(
                    content=self.notifications,
                    width=50,
                    alignment=ft.alignment.center
                )
            ],
            spacing=2,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
    
    def _create_tablet_layout(self) -> ft.Row:
        """Create tablet-optimized layout."""
        return ft.Row(
            controls=[
                ft.Container(
                    content=self._create_compact_time_tracker(),
                    width=60,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    content=self.flowchart,
                    expand=1,
                    padding=ft.padding.symmetric(horizontal=4)
                ),
                ft.Container(
                    content=self.notifications,
                    width=60,
                    alignment=ft.alignment.center
                )
            ],
            spacing=4,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
    
    def _create_desktop_expanded_layout(self) -> ft.Row:
        """Create desktop expanded layout."""
        return ft.Row(
            controls=[
                # Time tracker on the left
                ft.Container(
                    content=self.time_tracker,
                    expand=1,
                    padding=ft.padding.only(right=8)
                ),
                # Flowchart in the center
                ft.Container(
                    content=self.flowchart,
                    expand=2,
                    padding=ft.padding.symmetric(horizontal=4)
                ),
                # Notifications on the right
                ft.Container(
                    content=self.notifications,
                    width=60,  # Fixed width for notification icon
                    alignment=ft.alignment.center_right,
                    padding=ft.padding.only(left=8)
                )
            ],
            spacing=0,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
    
    def _create_desktop_collapsed_layout(self) -> ft.Row:
        """Create desktop collapsed layout."""
        return ft.Row(
            controls=[
                # Compact time tracker
                ft.Container(
                    content=self._create_compact_time_tracker(),
                    width=40,
                    alignment=ft.alignment.center
                ),
                # Compact flowchart indicator
                ft.Container(
                    content=self._create_compact_flowchart(),
                    expand=1,
                    alignment=ft.alignment.center,
                    padding=ft.padding.symmetric(horizontal=4)
                ),
                # Notifications (always visible)
                ft.Container(
                    content=self.notifications,
                    width=40,
                    alignment=ft.alignment.center
                )
            ],
            spacing=4,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
        
        # Apply consistent styling and spacing with responsive adjustments
        self.content = layout
        
        # Responsive height adjustment
        if layout_manager.is_mobile():
            self.height = 50
            self.padding = ft.padding.all(8)
        else:
            self.height = 60
            self.padding = ft.padding.all(12)
        
        self.bgcolor = 'surface_variant'
        self.border_radius = ft.border_radius.all(12)
        self.border = ft.border.all(1, 'outline_variant')
        
        # Add subtle shadow for depth
        self.shadow = ft.BoxShadow(
            spread_radius=0,
            blur_radius=4,
            color='rgba(0, 0, 0, 0.1)',
            offset=ft.Offset(0, 2)
        )
        
        # Enable smooth transitions with performance optimization
        self.animate = animation_manager.create_slide_animation()
    
    def _create_compact_time_tracker(self) -> ft.Control:
        """Create a compact version of the time tracker for collapsed sidebar."""
        # Get current state from the time tracker
        is_running = self.time_tracker.is_running
        elapsed_time = self.time_tracker.elapsed_time
        
        # Choose icon and color based on state
        if is_running:
            if self.time_tracker.is_paused:
                icon = ft.Icons.PAUSE_CIRCLE_FILLED
                color = 'warning'
            else:
                icon = ft.Icons.PLAY_CIRCLE_FILLED
                color = 'primary'
        else:
            icon = ft.Icons.TIMER_OUTLINED
            color = 'on_surface_variant'
        
        return ft.IconButton(
            icon=icon,
            icon_color=color,
            icon_size=24,
            tooltip=f"Time Tracker - {self.time_tracker._format_time(elapsed_time)}",
            on_click=self._on_compact_timer_click
        )
    
    def _create_compact_flowchart(self) -> ft.Control:
        """Create a compact version of the flowchart for collapsed sidebar."""
        # Get current workflow progress
        progress = self.flowchart.get_progress_percentage()
        current_stage = self.flowchart.get_current_stage()
        
        # Create progress indicator
        progress_bar = ft.ProgressBar(
            value=progress / 100.0,
            width=40,
            height=4,
            color='primary',
            bgcolor='surface_variant'
        )
        
        stage_name = current_stage.name if current_stage else "No workflow"
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.ACCOUNT_TREE,
                        size=16,
                        color='primary'
                    ),
                    progress_bar
                ],
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            tooltip=f"Workflow: {stage_name} ({progress:.0f}%)",
            on_click=self._on_compact_flowchart_click
        )
    
    def _on_compact_timer_click(self, e):
        """Handle click on compact timer icon."""
        # In a full implementation, this could open a timer dialog
        # For now, we'll just show a simple message
        if self.page:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Expand sidebar to access full time tracker"),
                    duration=2000
                )
            )
    
    def _on_compact_flowchart_click(self, e):
        """Handle click on compact flowchart indicator."""
        # In a full implementation, this could open a workflow dialog
        # For now, we'll just show a simple message
        if self.page:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Expand sidebar to access full workflow view"),
                    duration=2000
                )
            )
    
    @debounced(delay=0.1)  # Debounce layout updates
    def update_layout(self, sidebar_expanded: bool):
        """
        Update the layout based on sidebar expansion state.
        
        Args:
            sidebar_expanded: Whether the sidebar is expanded
        """
        if self.sidebar_expanded != sidebar_expanded:
            self.sidebar_expanded = sidebar_expanded
            self._build_layout()
            
            # Update the page if available
            if self.page:
                self.page.update()
    
    def _on_layout_change(self, breakpoint: str, width: float) -> None:
        """Handle responsive layout changes."""
        if self._current_breakpoint != breakpoint:
            self._current_breakpoint = breakpoint
            self._build_layout()
            
            if self.page:
                self.page.update()
    
    def cleanup(self) -> None:
        """Clean up resources to prevent memory leaks."""
        # Clean up child components
        if hasattr(self.time_tracker, 'cleanup'):
            self.time_tracker.cleanup()
        if hasattr(self.flowchart, 'cleanup'):
            self.flowchart.cleanup()
        if hasattr(self.notifications, 'cleanup'):
            self.notifications.cleanup()
        
        # Clean up lifecycle manager
        lifecycle_manager.cleanup_component(self)
    
    def refresh_components(self):
        """Refresh all child components."""
        # Refresh time tracker
        if hasattr(self.time_tracker, 'refresh'):
            self.time_tracker.refresh()
        
        # Refresh flowchart
        if hasattr(self.flowchart, '_refresh_display'):
            self.flowchart._refresh_display()
        
        # Refresh notifications (update display)
        if hasattr(self.notifications, '_update_display'):
            self.notifications._update_display()
        
        # Update compact views if in collapsed mode
        if not self.sidebar_expanded:
            self._build_layout()
        
        # Update the page if available
        if self.page:
            self.page.update()
    
    def get_time_tracker(self) -> TimeTrackerWidget:
        """Get the time tracker widget instance."""
        return self.time_tracker
    
    def get_flowchart(self) -> FlowchartWidget:
        """Get the flowchart widget instance."""
        return self.flowchart
    
    def get_notifications(self) -> NotificationCenter:
        """Get the notification center instance."""
        return self.notifications
    
    def add_test_notification(self):
        """Add a test notification for demonstration purposes."""
        self.notifications.add_test_notification()
    
    def advance_workflow_stage(self, stage_name: str) -> bool:
        """
        Advance the workflow to a specific stage.
        
        Args:
            stage_name: Name of the stage to advance to
            
        Returns:
            True if successful, False otherwise
        """
        return self.flowchart.advance_to_stage(stage_name)
    
    def complete_current_workflow_stage(self) -> bool:
        """
        Complete the current workflow stage and advance to next.
        
        Returns:
            True if successful, False otherwise
        """
        return self.flowchart.complete_current_stage()