import flet as ft
from typing import Optional, List, Callable, Dict, Any
from datetime import datetime
import logging
from models.workflow_state import WorkflowState, WorkflowStage, WorkflowStageStatus
from services.workflow_service import WorkflowService
from views.components.error_handling import (
    create_error_boundary, get_fallback_manager, safe_execute
)


class FlowchartWidget(ft.Container):
    """Widget for displaying workflow flowchart with interactive elements."""
    
    def __init__(
        self, 
        page: ft.Page,
        workflow_service: Optional[WorkflowService] = None,
        on_stage_click: Optional[Callable[[str], None]] = None
    ):
        """Initialize the flowchart widget."""
        # Store attributes before calling super().__init__
        self.page = page
        self.workflow_service = workflow_service or WorkflowService()
        self.on_stage_click = on_stage_click
        self.current_workflow_id: Optional[str] = None
        self.workflow_state: Optional[WorkflowState] = None
        
        # Error handling
        self.error_boundary = create_error_boundary("FlowchartWidget", page)
        self.fallback_manager = get_fallback_manager()
        
        # Register fallback component
        self.fallback_manager.register_fallback(
            "FlowchartWidget", 
            self._create_fallback_component
        )
        
        # Create the main container
        super().__init__(
            padding=ft.padding.all(10),
            border_radius=8,
            bgcolor="surface_variant",
            border=ft.border.all(1, "outline_variant")
        )
        
        # Set content after initialization to avoid issues with _build_content
        self.content = self._build_content()
    
    def _build_content(self) -> ft.Control:
        """Build the main content of the flowchart widget."""
        return ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.ACCOUNT_TREE, size=20, color="primary"),
                ft.Text(
                    "Workflow Progress",
                    size=16,
                    weight=ft.FontWeight.W_600,
                    color="on_surface"
                )
            ], spacing=8),
            ft.Container(
                content=self._build_flowchart(),
                padding=ft.padding.symmetric(vertical=10)
            )
        ], spacing=10)
    
    def _build_flowchart(self) -> ft.Control:
        """Build the flowchart visualization with responsive scaling."""
        if not self.workflow_state:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ACCOUNT_TREE_OUTLINED, size=32, color="outline"),
                    ft.Text(
                        "No workflow loaded",
                        color="on_surface_variant",
                        size=14,
                        text_align=ft.TextAlign.CENTER
                    )
                ], 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8
                ),
                alignment=ft.alignment.center,
                height=100,
                padding=ft.padding.all(20)
            )
        
        # Create stage nodes with responsive sizing
        stage_nodes = []
        sorted_stages = sorted(self.workflow_state.stages, key=lambda s: s.order)
        
        # Calculate responsive node width based on container and number of stages
        total_stages = len(sorted_stages)
        min_node_width = 70
        max_node_width = 120
        
        # Use responsive width if available, otherwise calculate default
        if hasattr(self, '_responsive_node_width'):
            calculated_node_width = self._responsive_node_width
        else:
            connector_width = 30
            # Estimate available width (conservative estimate for responsive design)
            estimated_container_width = 800  # Base estimate, will scale responsively
            available_width = estimated_container_width - (total_stages - 1) * connector_width
            calculated_node_width = max(min_node_width, min(max_node_width, available_width // total_stages))
        
        for i, stage in enumerate(sorted_stages):
            # Create stage node with responsive width
            stage_node = self._create_stage_node(stage, calculated_node_width)
            stage_nodes.append(stage_node)
            
            # Add connector arrow if not the last stage
            if i < len(sorted_stages) - 1:
                connector = self._create_connector(stage, sorted_stages[i + 1] if i + 1 < len(sorted_stages) else None)
                stage_nodes.append(connector)
        
        # Create scrollable horizontal layout with responsive behavior
        flowchart_row = ft.Row(
            controls=stage_nodes,
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            alignment=ft.MainAxisAlignment.START,
            tight=True
        )
        
        # Add progress indicator
        progress_indicator = self._create_progress_indicator()
        
        return ft.Container(
            content=ft.Column([
                progress_indicator,
                ft.Container(
                    content=flowchart_row,
                    padding=ft.padding.symmetric(vertical=10, horizontal=5)
                )
            ], spacing=10),
            height=120,
            expand=True
        )
    
    def _create_stage_node(self, stage: WorkflowStage, width: int = 80) -> ft.Control:
        """Create a modern card-based visual node for a workflow stage."""
        # Determine modern colors and styling based on stage status
        if stage.status == WorkflowStageStatus.COMPLETED:
            bg_color = ft.Colors.GREEN_50
            border_color = ft.Colors.GREEN_400
            text_color = ft.Colors.GREEN_800
            icon = ft.Icons.CHECK_CIRCLE_ROUNDED
            icon_color = ft.Colors.GREEN_600
            shadow_color = ft.Colors.GREEN_100
        elif stage.status == WorkflowStageStatus.IN_PROGRESS:
            bg_color = ft.Colors.BLUE_50
            border_color = ft.Colors.BLUE_400
            text_color = ft.Colors.BLUE_800
            icon = ft.Icons.PLAY_CIRCLE_FILLED_ROUNDED
            icon_color = ft.Colors.BLUE_600
            shadow_color = ft.Colors.BLUE_100
        elif stage.status == WorkflowStageStatus.BLOCKED:
            bg_color = ft.Colors.RED_50
            border_color = ft.Colors.RED_400
            text_color = ft.Colors.RED_800
            icon = ft.Icons.BLOCK_ROUNDED
            icon_color = ft.Colors.RED_600
            shadow_color = ft.Colors.RED_100
        else:  # PENDING
            bg_color = ft.Colors.GREY_50
            border_color = ft.Colors.GREY_300
            text_color = ft.Colors.GREY_700
            icon = ft.Icons.RADIO_BUTTON_UNCHECKED_ROUNDED
            icon_color = ft.Colors.GREY_500
            shadow_color = ft.Colors.GREY_100
        
        # Create modern card-based stage container
        stage_container = ft.Container(
            content=ft.Column([
                # Status icon with subtle background
                ft.Container(
                    content=ft.Icon(icon, size=18, color=icon_color),
                    width=32,
                    height=32,
                    bgcolor=shadow_color,
                    border_radius=16,
                    alignment=ft.alignment.center
                ),
                # Stage name with better typography
                ft.Text(
                    stage.name,
                    size=11,
                    weight=ft.FontWeight.W_600,
                    color=text_color,
                    text_align=ft.TextAlign.CENTER,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS
                )
            ], 
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER
            ),
            width=width,
            height=70,
            padding=ft.padding.all(8),
            bgcolor=bg_color,
            border=ft.border.all(1.5, border_color),
            border_radius=12,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 2)
            ),
            on_click=lambda e, stage_name=stage.name: self._handle_stage_click(stage_name),
            tooltip=f"{stage.name}\nStatus: {stage.status.value.replace('_', ' ').title()}\nClick to view details"
        )
        
        # Enhanced hover effect with smooth animations
        def on_hover(e):
            if e.data == "true":
                stage_container.elevation = 8
                stage_container.scale = 1.08
                stage_container.shadow = ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=8,
                    color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
                    offset=ft.Offset(0, 4)
                )
            else:
                stage_container.elevation = 0
                stage_container.scale = 1.0
                stage_container.shadow = ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=4,
                    color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                    offset=ft.Offset(0, 2)
                )
            # Only update if the widget is attached to a page
            try:
                if hasattr(stage_container, 'page') and stage_container.page is not None:
                    stage_container.update()
            except (AssertionError, AttributeError):
                # Widget not attached to page, skip update
                pass
        
        stage_container.on_hover = on_hover
        
        return stage_container
    
    def _create_connector(self, from_stage: WorkflowStage, to_stage: Optional[WorkflowStage] = None) -> ft.Control:
        """Create a modern connector arrow between stages with progress indication."""
        # Determine connector color based on progress
        if from_stage.status == WorkflowStageStatus.COMPLETED:
            connector_color = ft.Colors.GREEN_400
            arrow_icon = ft.Icons.ARROW_FORWARD_ROUNDED
        elif from_stage.status == WorkflowStageStatus.IN_PROGRESS:
            connector_color = ft.Colors.BLUE_300
            arrow_icon = ft.Icons.ARROW_FORWARD_ROUNDED
        else:
            connector_color = ft.Colors.GREY_300
            arrow_icon = ft.Icons.ARROW_FORWARD_ROUNDED
        
        return ft.Container(
            content=ft.Column([
                # Progress line
                ft.Container(
                    height=2,
                    width=24,
                    bgcolor=connector_color,
                    border_radius=1
                ),
                # Arrow icon
                ft.Icon(
                    arrow_icon,
                    size=14,
                    color=connector_color
                ),
                # Progress line
                ft.Container(
                    height=2,
                    width=24,
                    bgcolor=connector_color,
                    border_radius=1
                )
            ],
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER
            ),
            alignment=ft.alignment.center,
            width=30,
            height=70,
            padding=ft.padding.symmetric(horizontal=3)
        )
    
    def _create_progress_indicator(self) -> ft.Control:
        """Create a progress indicator showing workflow completion."""
        if not self.workflow_state:
            return ft.Container(height=0)
        
        progress_percentage = self.workflow_state.get_progress_percentage()
        completed_stages = len([s for s in self.workflow_state.stages if s.status == WorkflowStageStatus.COMPLETED])
        total_stages = len(self.workflow_state.stages)
        
        return ft.Container(
            content=ft.Row([
                ft.Text(
                    f"Progress: {completed_stages}/{total_stages} stages",
                    size=12,
                    color="on_surface_variant",
                    weight=ft.FontWeight.W_500
                ),
                ft.Container(
                    content=ft.ProgressBar(
                        value=progress_percentage / 100,
                        color=ft.Colors.BLUE_400,
                        bgcolor=ft.Colors.GREY_200,
                        height=4
                    ),
                    expand=True,
                    padding=ft.padding.symmetric(horizontal=10)
                ),
                ft.Text(
                    f"{progress_percentage:.0f}%",
                    size=12,
                    color="on_surface_variant",
                    weight=ft.FontWeight.W_600
                )
            ], 
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.padding.symmetric(horizontal=5),
            height=20
        )
    
    def _handle_stage_click(self, stage_name: str) -> None:
        """Handle stage node click."""
        if self.on_stage_click:
            self.on_stage_click(stage_name)
    
    def load_workflow(self, workflow_id: str) -> bool:
        """Load a workflow by ID."""
        workflow = self.workflow_service.get_workflow(workflow_id)
        if workflow:
            self.current_workflow_id = workflow_id
            self.workflow_state = workflow
            self._refresh_display()
            return True
        return False
    
    def create_default_workflow(self, workflow_id: str = "default", project_id: Optional[str] = None) -> bool:
        """Create and load a default workflow."""
        try:
            workflow = self.workflow_service.create_workflow(workflow_id, project_id)
            self.current_workflow_id = workflow_id
            self.workflow_state = workflow
            self._refresh_display()
            return True
        except ValueError:
            # Workflow already exists, try to load it
            return self.load_workflow(workflow_id)
    
    def advance_to_stage(self, stage_name: str) -> bool:
        """Advance workflow to a specific stage."""
        if not self.current_workflow_id:
            return False
        
        success = self.workflow_service.advance_workflow_stage(self.current_workflow_id, stage_name)
        if success:
            # Reload workflow state
            self.workflow_state = self.workflow_service.get_workflow(self.current_workflow_id)
            self._refresh_display()
        return success
    
    def complete_current_stage(self) -> bool:
        """Complete the current stage and advance to next."""
        if not self.current_workflow_id:
            return False
        
        success = self.workflow_service.complete_current_stage(self.current_workflow_id)
        if success:
            # Reload workflow state
            self.workflow_state = self.workflow_service.get_workflow(self.current_workflow_id)
            self._refresh_display()
        return success
    
    def get_current_stage(self) -> Optional[WorkflowStage]:
        """Get the current workflow stage."""
        if self.workflow_state:
            return self.workflow_state.get_current_stage()
        return None
    
    def get_progress_percentage(self) -> float:
        """Get workflow completion percentage."""
        if self.workflow_state:
            return self.workflow_state.get_progress_percentage()
        return 0.0
    
    def _refresh_display(self) -> None:
        """Refresh the flowchart display."""
        self.content = self._build_content()
        # Only update if the widget is attached to a page
        try:
            if hasattr(self, 'update') and hasattr(self, 'page') and self.page is not None:
                self.update()
        except (AssertionError, AttributeError):
            # Widget not attached to page, skip update
            pass
    
    def set_on_stage_click(self, callback: Callable[[str], None]) -> None:
        """Set the callback for stage click events."""
        self.on_stage_click = callback
    
    def update_responsive_layout(self, container_width: Optional[int] = None) -> None:
        """Update the flowchart layout for responsive design."""
        if container_width and self.workflow_state:
            # Recalculate node sizes based on container width
            total_stages = len(self.workflow_state.stages)
            min_node_width = 60
            max_node_width = 140
            connector_width = 30
            
            available_width = container_width - (total_stages - 1) * connector_width - 40  # padding
            calculated_node_width = max(min_node_width, min(max_node_width, available_width // total_stages))
            
            # Store the calculated width for use in _build_flowchart
            self._responsive_node_width = calculated_node_width
            self._refresh_display()
    
    def get_stage_details(self, stage_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific stage."""
        if not self.workflow_state:
            return None
        
        for stage in self.workflow_state.stages:
            if stage.name == stage_name:
                return {
                    'name': stage.name,
                    'status': stage.status.value,
                    'description': stage.description,
                    'order': stage.order,
                    'metadata': stage.metadata,
                    'is_current': stage.name == self.workflow_state.current_stage
                }
        return None    
    
    def _create_fallback_component(self, error_message: str) -> ft.Control:
        """Create a fallback component when flowchart fails."""
        return ft.Container(
            content=ft.Column([
                ft.Icon(
                    ft.Icons.ACCOUNT_TREE_OUTLINED,
                    size=48,
                    color=ft.Colors.GREY_400
                ),
                ft.Text(
                    "Workflow Unavailable",
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
                    on_click=self._retry_flowchart,
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
            border=ft.border.all(1, ft.Colors.GREY_200),
            height=120
        )
    
    def _retry_flowchart(self, e) -> None:
        """Retry initializing the flowchart."""
        def retry_operation():
            if self.current_workflow_id:
                self.load_workflow_safe(self.current_workflow_id)
            else:
                self.create_default_workflow_safe()
            
            if self.page:
                self.page.update()
        
        safe_execute(
            retry_operation,
            "FlowchartWidget",
            "retry_initialization",
            self.page
        )
    
    def load_workflow_safe(self, workflow_id: str) -> bool:
        """Load a workflow by ID with error handling."""
        def load_operation():
            return self.load_workflow(workflow_id)
        
        result = safe_execute(
            load_operation,
            "FlowchartWidget",
            "load_workflow",
            self.page,
            fallback_result=False,
            user_data={"workflow_id": workflow_id}
        )
        
        if result is False:
            self._show_error_state(f"Failed to load workflow: {workflow_id}")
            return False
        
        return result
    
    def create_default_workflow_safe(self, workflow_id: str = "default", project_id: Optional[str] = None) -> bool:
        """Create and load a default workflow with error handling."""
        def create_operation():
            return self.create_default_workflow(workflow_id, project_id)
        
        result = safe_execute(
            create_operation,
            "FlowchartWidget",
            "create_default_workflow",
            self.page,
            fallback_result=False,
            user_data={"workflow_id": workflow_id, "project_id": project_id}
        )
        
        if result is False:
            self._show_error_state("Failed to create default workflow")
            return False
        
        return result
    
    def advance_to_stage_safe(self, stage_name: str) -> bool:
        """Advance workflow to a specific stage with error handling."""
        def advance_operation():
            return self.advance_to_stage(stage_name)
        
        result = safe_execute(
            advance_operation,
            "FlowchartWidget",
            "advance_to_stage",
            self.page,
            fallback_result=False,
            user_data={"stage_name": stage_name, "workflow_id": self.current_workflow_id}
        )
        
        if result is False:
            self._show_error_state(f"Failed to advance to stage: {stage_name}")
            return False
        
        return result
    
    def _show_error_state(self, error_message: str) -> None:
        """Show error state in the flowchart."""
        try:
            error_content = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.ERROR_OUTLINE, size=20, color=ft.Colors.RED_400),
                        ft.Text(
                            "Workflow Error",
                            size=16,
                            weight=ft.FontWeight.W_600,
                            color=ft.Colors.RED_600
                        )
                    ], spacing=8),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                error_message,
                                color=ft.Colors.RED_500,
                                size=12,
                                text_align=ft.TextAlign.CENTER
                            ),
                            ft.ElevatedButton(
                                "Retry",
                                icon=ft.Icons.REFRESH,
                                on_click=lambda e: self._retry_flowchart(e),
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.RED_100,
                                    color=ft.Colors.RED_800
                                )
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8
                        ),
                        padding=ft.padding.symmetric(vertical=10)
                    )
                ], spacing=10),
                padding=ft.padding.all(10),
                border_radius=8,
                bgcolor=ft.Colors.RED_50,
                border=ft.border.all(1, ft.Colors.RED_200)
            )
            
            self.content = error_content
            
            if self.page:
                self.page.update()
                
        except Exception as e:
            logging.error(f"Failed to show error state in flowchart: {e}")
    
    def _safe_refresh_display(self) -> None:
        """Safely refresh the flowchart display."""
        def refresh_operation():
            self._refresh_display()
        
        result = safe_execute(
            refresh_operation,
            "FlowchartWidget",
            "refresh_display",
            self.page,
            fallback_result=False
        )
        
        if result is False:
            self._show_error_state("Failed to refresh flowchart display")
    
    def _safe_handle_stage_click(self, stage_name: str) -> None:
        """Safely handle stage click events."""
        def click_operation():
            self._handle_stage_click(stage_name)
        
        safe_execute(
            click_operation,
            "FlowchartWidget",
            "handle_stage_click",
            self.page,
            user_data={"stage_name": stage_name}
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get the health status of the flowchart widget."""
        try:
            return {
                "component": "FlowchartWidget",
                "status": "healthy",
                "workflow_id": self.current_workflow_id,
                "has_workflow": self.workflow_state is not None,
                "current_stage": self.workflow_state.current_stage if self.workflow_state else None,
                "progress": self.get_progress_percentage(),
                "last_update": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "component": "FlowchartWidget",
                "status": "error",
                "error": str(e),
                "last_update": datetime.now().isoformat()
            }
    
    def _recover_from_workflow_error(self) -> bool:
        """Attempt to recover from workflow errors."""
        try:
            # Try to reload current workflow
            if self.current_workflow_id:
                workflow = self.workflow_service.get_workflow_safe(self.current_workflow_id)
                if workflow:
                    self.workflow_state = workflow
                    self._safe_refresh_display()
                    return True
            
            # If no current workflow or reload failed, create default
            if self.create_default_workflow_safe():
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Failed to recover from workflow error: {e}")
            return False
    
    # Override methods to use safe versions
    def load_workflow(self, workflow_id: str) -> bool:
        """Load a workflow by ID with enhanced error handling."""
        try:
            workflow = self.workflow_service.get_workflow_safe(workflow_id)
            if workflow:
                self.current_workflow_id = workflow_id
                self.workflow_state = workflow
                self._safe_refresh_display()
                return True
            return False
        except Exception as e:
            logging.error(f"Failed to load workflow {workflow_id}: {e}")
            return False
    
    def create_default_workflow(self, workflow_id: str = "default", project_id: Optional[str] = None) -> bool:
        """Create and load a default workflow with enhanced error handling."""
        try:
            workflow = self.workflow_service.create_workflow_safe(workflow_id, project_id)
            if workflow:
                self.current_workflow_id = workflow_id
                self.workflow_state = workflow
                self._safe_refresh_display()
                return True
            return False
        except Exception as e:
            logging.error(f"Failed to create default workflow: {e}")
            return False
    
    def advance_to_stage(self, stage_name: str) -> bool:
        """Advance workflow to a specific stage with enhanced error handling."""
        if not self.current_workflow_id:
            return False
        
        try:
            success = self.workflow_service.advance_workflow_stage_safe(self.current_workflow_id, stage_name)
            if success:
                # Reload workflow state
                self.workflow_state = self.workflow_service.get_workflow_safe(self.current_workflow_id)
                self._safe_refresh_display()
            return success
        except Exception as e:
            logging.error(f"Failed to advance to stage {stage_name}: {e}")
            return False