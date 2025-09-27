#!/usr/bin/env python3
"""
Enhanced Time Tracker Widget Demo

This demo showcases the enhanced time tracker widget with:
- Circular progress indicator
- Modern button styling
- Visual state feedback
- Activity management
- Real-time timer updates
"""

import flet as ft
from datetime import timedelta
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from views.components.time_tracker_widget import TimeTrackerWidget
from services.time_tracking_service import TimeTrackingService
from models.activity import Activity


def main(page: ft.Page):
    """Main demo application."""
    page.title = "Enhanced Time Tracker Demo"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 400
    page.window_height = 600
    page.window_resizable = False
    
    # Create services
    time_service = TimeTrackingService()
    
    # Create the enhanced time tracker widget
    time_tracker = TimeTrackerWidget(page, time_service)
    
    # Add some sample activities
    sample_activities = [
        Activity(name="Development", category="Work"),
        Activity(name="Code Review", category="Work"),
        Activity(name="Meeting", category="Work"),
        Activity(name="Documentation", category="Work"),
        Activity(name="Learning", category="Personal"),
        Activity(name="Break", category="Personal")
    ]
    
    time_tracker.set_activities(sample_activities)
    
    # Create demo info
    demo_info = ft.Container(
        content=ft.Column([
            ft.Text(
                "Enhanced Time Tracker Demo",
                size=20,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER
            ),
            ft.Text(
                "Features demonstrated:",
                size=14,
                weight=ft.FontWeight.W_500
            ),
            ft.Column([
                ft.Text("• Circular progress indicator", size=12),
                ft.Text("• Modern button styling", size=12),
                ft.Text("• Visual state feedback", size=12),
                ft.Text("• Activity selection & management", size=12),
                ft.Text("• Real-time timer updates", size=12),
                ft.Text("• Enhanced user feedback", size=12),
            ], spacing=4),
            ft.Text(
                "Instructions:",
                size=14,
                weight=ft.FontWeight.W_500
            ),
            ft.Column([
                ft.Text("1. Select an activity from dropdown", size=12),
                ft.Text("2. Or add a quick activity", size=12),
                ft.Text("3. Click Start to begin tracking", size=12),
                ft.Text("4. Use Pause/Resume as needed", size=12),
                ft.Text("5. Click Stop to complete", size=12),
            ], spacing=4),
        ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.padding.all(20),
        border_radius=ft.border_radius.all(12),
        bgcolor='surface_variant',
        margin=ft.margin.only(bottom=20)
    )
    
    # Layout
    page.add(
        ft.Container(
            content=ft.Column([
                demo_info,
                time_tracker
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
            padding=ft.padding.all(20),
            expand=True
        )
    )


if __name__ == "__main__":
    ft.app(target=main)