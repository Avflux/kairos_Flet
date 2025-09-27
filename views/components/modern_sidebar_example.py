"""
Example usage of the ModernSidebar component.

This file demonstrates how to integrate the ModernSidebar into a Flet application.
"""

import flet as ft
from views.components.modern_sidebar import ModernSidebar


def main(page: ft.Page):
    """Example application using ModernSidebar"""
    page.title = "Modern Sidebar Example"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    
    # Track current route
    current_route = {"value": "/workflow-overview"}
    
    def handle_navigation(route: str):
        """Handle navigation events from the sidebar"""
        current_route["value"] = f"/{route}"
        content_area.content = ft.Text(
            f"Current page: {route}",
            size=24,
            weight=ft.FontWeight.BOLD
        )
        page.update()
    
    # Create the modern sidebar
    sidebar = ModernSidebar(page, on_navigation=handle_navigation)
    
    # Create main content area
    content_area = ft.Container(
        content=ft.Text(
            "Current page: workflow-overview",
            size=24,
            weight=ft.FontWeight.BOLD
        ),
        expand=True,
        padding=ft.padding.all(20),
        bgcolor='rgba(255, 255, 255, 0.03)',
        border_radius=ft.border_radius.all(16)
    )
    
    # Create the main layout
    main_layout = ft.Row([
        sidebar,
        content_area
    ], spacing=16, expand=True)
    
    # Add to page
    page.add(
        ft.Container(
            content=main_layout,
            padding=ft.padding.all(16),
            expand=True
        )
    )


if __name__ == "__main__":
    ft.app(target=main)