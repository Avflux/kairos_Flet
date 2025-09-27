"""
Demonstration of TopSidebarContainer integration with MainView.
This shows how the container would be integrated into the existing layout.
"""

import flet as ft
from unittest.mock import Mock
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from views.components.top_sidebar_container import TopSidebarContainer


def main(page: ft.Page):
    """Main application demonstrating TopSidebarContainer integration."""
    page.title = "TopSidebarContainer Demo"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 10
    
    # State for sidebar expansion
    sidebar_expanded = True
    
    def toggle_sidebar(e):
        """Toggle sidebar expansion and update container layout."""
        nonlocal sidebar_expanded
        sidebar_expanded = not sidebar_expanded
        
        # Update the top sidebar container layout
        top_sidebar.update_layout(sidebar_expanded)
        
        # Update sidebar width animation
        sidebar_container.width = 250 if sidebar_expanded else 80
        
        # Update visibility of text elements (simplified for demo)
        sidebar_title.visible = sidebar_expanded
        
        page.update()
    
    def add_test_notification(e):
        """Add a test notification for demonstration."""
        top_sidebar.add_test_notification()
    
    def advance_workflow(e):
        """Advance workflow for demonstration."""
        success = top_sidebar.complete_current_workflow_stage()
        if success:
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Workflow stage completed!"),
                    bgcolor='primary'
                )
            )
    
    # Create the top sidebar container
    top_sidebar = TopSidebarContainer(page)
    
    # Create sidebar content (simplified version of MainView sidebar)
    sidebar_title = ft.Text(
        "Kairos Demo", 
        weight=ft.FontWeight.BOLD, 
        size=18, 
        visible=sidebar_expanded
    )
    
    sidebar_content = ft.Column([
        ft.Row([
            sidebar_title,
            ft.IconButton(
                icon=ft.Icons.MENU, 
                on_click=toggle_sidebar
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        
        ft.Divider(),
        
        ft.Text("Demo Controls:", weight=ft.FontWeight.BOLD, visible=sidebar_expanded),
        
        ft.ElevatedButton(
            "Add Test Notification",
            on_click=add_test_notification,
            width=200 if sidebar_expanded else None
        ),
        
        ft.ElevatedButton(
            "Advance Workflow",
            on_click=advance_workflow,
            width=200 if sidebar_expanded else None
        ),
        
        ft.Container(expand=True),  # Spacer
        
        ft.Text(
            "TopSidebarContainer Demo\nShowing responsive layout", 
            size=10, 
            color='on_surface_variant',
            visible=sidebar_expanded
        )
    ])
    
    # Create sidebar container with animation
    sidebar_container = ft.Container(
        width=250,
        animate=ft.Animation(300, ft.AnimationCurve.EASE),
        content=ft.Column([
            top_sidebar,  # Our new top sidebar container
            ft.Container(height=10),  # Spacing
            ft.Container(
                content=sidebar_content,
                expand=True,
                padding=ft.padding.all(15),
                bgcolor='surface_variant',
                border_radius=ft.border_radius.all(10)
            )
        ])
    )
    
    # Create main content area
    main_content = ft.Container(
        expand=True,
        content=ft.Column([
            ft.Container(
                content=ft.Text(
                    "Main Content Area", 
                    size=24, 
                    weight=ft.FontWeight.BOLD
                ),
                alignment=ft.alignment.center,
                expand=True,
                bgcolor='surface_variant',
                border_radius=ft.border_radius.all(10)
            )
        ])
    )
    
    # Create the main layout
    main_layout = ft.Row([
        sidebar_container,
        ft.Container(width=10),  # Spacing
        main_content
    ], expand=True)
    
    # Add instructions
    instructions = ft.Container(
        content=ft.Column([
            ft.Text(
                "TopSidebarContainer Demo Instructions:",
                size=16,
                weight=ft.FontWeight.BOLD
            ),
            ft.Text("• Click the menu button to toggle sidebar expansion"),
            ft.Text("• Notice how the top container adapts to sidebar state"),
            ft.Text("• Try adding test notifications"),
            ft.Text("• Try advancing the workflow"),
            ft.Text("• In collapsed mode, click compact icons for messages"),
        ]),
        padding=ft.padding.all(10),
        bgcolor='primary_container',
        border_radius=ft.border_radius.all(8),
        margin=ft.margin.only(bottom=10)
    )
    
    # Add everything to the page
    page.add(
        ft.Column([
            instructions,
            main_layout
        ], expand=True)
    )


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)