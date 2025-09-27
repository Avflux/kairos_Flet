#!/usr/bin/env python3
"""
Demo script for MainView integration with enhanced components.

This script demonstrates the integrated MainView with TopSidebarContainer,
ModernSidebar, and all enhanced components working together.
"""

import flet as ft
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from views.main_view import MainView


def main(page: ft.Page):
    """Main application entry point."""
    # Configure page
    page.title = "Kairos - Enhanced UI Integration Demo"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0
    
    # Set window properties
    page.window_width = 1200
    page.window_height = 800
    page.window_min_width = 800
    page.window_min_height = 600
    
    # Create and add the enhanced MainView
    main_view = MainView(page)
    page.views.append(main_view)
    
    # Add some demo functionality
    def add_demo_notification():
        """Add a demo notification."""
        main_view.add_test_notification()
        page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text("Demo notification added!"),
                duration=2000
            )
        )
    
    def advance_demo_workflow():
        """Advance the demo workflow."""
        stages = ["Verificação", "Aprovação", "Emissão", "Comentários Cliente"]
        import random
        stage = random.choice(stages)
        
        success = main_view.advance_workflow_stage(stage)
        if success:
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Workflow advanced to: {stage}"),
                    duration=2000
                )
            )
        else:
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Failed to advance workflow"),
                    duration=2000
                )
            )
    
    # Add demo controls to the page
    demo_controls = ft.Row([
        ft.ElevatedButton(
            "Add Demo Notification",
            on_click=lambda e: add_demo_notification(),
            icon=ft.icons.NOTIFICATIONS
        ),
        ft.ElevatedButton(
            "Advance Workflow",
            on_click=lambda e: advance_demo_workflow(),
            icon=ft.icons.ARROW_FORWARD
        ),
        ft.ElevatedButton(
            "Toggle Enhanced Components",
            on_click=lambda e: toggle_enhanced_components(),
            icon=ft.icons.TOGGLE_ON
        )
    ], spacing=10)
    
    def toggle_enhanced_components():
        """Toggle between enhanced and original components."""
        current_state = main_view.use_enhanced_components
        page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text(
                    f"Enhanced components are {'enabled' if current_state else 'disabled'}. "
                    "Restart the app to toggle."
                ),
                duration=3000
            )
        )
    
    # Add demo controls to the top right area
    if hasattr(main_view, 'top_bar_right') and main_view.top_bar_right:
        main_view.top_bar_right.content = ft.Column([
            ft.Text("Demo Controls", weight=ft.FontWeight.BOLD),
            demo_controls
        ], spacing=10)
    
    # Show initial information
    page.show_snack_bar(
        ft.SnackBar(
            content=ft.Text("Enhanced MainView loaded! Try the sidebar navigation and demo controls."),
            duration=4000
        )
    )
    
    # Update the page
    page.update()


if __name__ == "__main__":
    print("Starting Kairos Enhanced UI Integration Demo...")
    print("This demo shows the integrated MainView with all enhanced components.")
    print("Features:")
    print("- Modern sidebar with three sections")
    print("- Top sidebar container with time tracker, flowchart, and notifications")
    print("- Responsive layout that adapts to sidebar state")
    print("- Navigation handling and content updates")
    print("- Service integration for time tracking, workflows, and notifications")
    print()
    
    # Run the Flet app
    ft.app(target=main, view=ft.WEB_BROWSER)