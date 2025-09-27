#!/usr/bin/env python3
"""
Enhanced Flowchart Widget Demo

This demo showcases the enhanced interactive flowchart visualization with:
- Modern card-based styling for workflow stages
- Interactive stage nodes with hover effects and click handlers
- Current stage highlighting and progress indicators
- Responsive scaling for different container widths
- Connected workflow stages rendering
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flet as ft
from views.components.flowchart_widget import FlowchartWidget
from services.workflow_service import WorkflowService
from models.workflow_state import WorkflowStageStatus


def main(page: ft.Page):
    """Main demo application."""
    page.title = "Enhanced Flowchart Widget Demo"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO
    
    # Create workflow service and widget
    workflow_service = WorkflowService()
    
    def on_stage_click(stage_name: str):
        """Handle stage click events."""
        details = flowchart_widget.get_stage_details(stage_name)
        if details:
            status_text.value = f"Clicked: {stage_name}\nStatus: {details['status']}\nOrder: {details['order']}"
            if details['description']:
                status_text.value += f"\nDescription: {details['description']}"
            status_text.update()
    
    flowchart_widget = FlowchartWidget(
        page=page,
        workflow_service=workflow_service,
        on_stage_click=on_stage_click
    )
    
    # Status display
    status_text = ft.Text(
        "Click on a workflow stage to see details",
        size=14,
        color="on_surface_variant"
    )
    
    # Control buttons
    def create_workflow(e):
        """Create a default workflow."""
        success = flowchart_widget.create_default_workflow("demo_workflow", "demo_project")
        if success:
            status_text.value = "Default workflow created successfully!"
            status_text.update()
    
    def advance_stage(e):
        """Advance to next stage."""
        current_stage = flowchart_widget.get_current_stage()
        if current_stage:
            success = flowchart_widget.complete_current_stage()
            if success:
                new_stage = flowchart_widget.get_current_stage()
                status_text.value = f"Advanced to: {new_stage.name if new_stage else 'Completed'}"
            else:
                status_text.value = "Workflow completed!"
            status_text.update()
    
    def reset_workflow(e):
        """Reset workflow to beginning."""
        if flowchart_widget.current_workflow_id:
            workflow_service.reset_workflow(flowchart_widget.current_workflow_id)
            flowchart_widget.load_workflow(flowchart_widget.current_workflow_id)
            status_text.value = "Workflow reset to beginning"
            status_text.update()
    
    def simulate_progress(e):
        """Simulate workflow progress."""
        if not flowchart_widget.current_workflow_id:
            create_workflow(None)
        
        # Advance a few stages to show different states
        stages_to_advance = ["Verificação", "Aprovação", "Emissão"]
        for stage_name in stages_to_advance:
            flowchart_widget.advance_to_stage(stage_name)
        
        # Set one stage as blocked for demonstration
        workflow_service.set_stage_status(
            flowchart_widget.current_workflow_id, 
            "Comentários Cliente", 
            WorkflowStageStatus.BLOCKED
        )
        
        flowchart_widget.load_workflow(flowchart_widget.current_workflow_id)
        status_text.value = "Simulated workflow progress with mixed states"
        status_text.update()
    
    def test_responsive(e):
        """Test responsive layout."""
        # Simulate different container widths
        widths = [600, 800, 1200, 400]
        current_width = getattr(test_responsive, 'current_width', 0)
        width = widths[current_width % len(widths)]
        test_responsive.current_width = current_width + 1
        
        flowchart_widget.update_responsive_layout(width)
        status_text.value = f"Updated layout for container width: {width}px"
        status_text.update()
    
    # Create UI layout
    controls_row = ft.Row([
        ft.ElevatedButton("Create Workflow", on_click=create_workflow),
        ft.ElevatedButton("Advance Stage", on_click=advance_stage),
        ft.ElevatedButton("Reset Workflow", on_click=reset_workflow),
        ft.ElevatedButton("Simulate Progress", on_click=simulate_progress),
        ft.ElevatedButton("Test Responsive", on_click=test_responsive),
    ], spacing=10, wrap=True)
    
    # Main layout
    page.add(
        ft.Column([
            ft.Text(
                "Enhanced Flowchart Widget Demo",
                size=24,
                weight=ft.FontWeight.BOLD,
                color="primary"
            ),
            ft.Text(
                "This demo showcases the enhanced interactive flowchart with modern styling, "
                "hover effects, progress indicators, and responsive design.",
                size=14,
                color="on_surface_variant"
            ),
            ft.Divider(),
            controls_row,
            ft.Container(
                content=flowchart_widget,
                border=ft.border.all(1, "outline_variant"),
                border_radius=8,
                padding=10,
                margin=ft.margin.symmetric(vertical=10)
            ),
            ft.Container(
                content=status_text,
                padding=10,
                bgcolor="surface_variant",
                border_radius=8
            ),
            ft.Container(
                content=ft.Text(
                    "Features demonstrated:",
                    size=16,
                    weight=ft.FontWeight.W_600
                ),
                margin=ft.margin.only(top=20)
            ),
            ft.Column([
                ft.Text("• Modern card-based styling with shadows and rounded corners"),
                ft.Text("• Interactive hover effects with smooth animations"),
                ft.Text("• Color-coded stage status (completed, in-progress, blocked, pending)"),
                ft.Text("• Progress indicator showing workflow completion percentage"),
                ft.Text("• Responsive scaling that adapts to container width"),
                ft.Text("• Connected stages with progress-aware connectors"),
                ft.Text("• Click handlers for stage interaction"),
                ft.Text("• Tooltips with stage information"),
            ], spacing=5)
        ], spacing=10)
    )


if __name__ == "__main__":
    ft.app(target=main)