#!/usr/bin/env python3
"""
Enhanced Notification Center Demo

This demo showcases the completed notification center functionality including:
- Categorized notification display with filter tabs
- Enhanced visual indicators and badge counters
- Improved interaction handlers (mark as read, clear all, etc.)
- Better timestamp display and action button functionality
- Modern UI design with animations and improved styling
"""

import flet as ft
from datetime import datetime, timedelta
import time
import threading
from views.components.notification_center import NotificationCenter
from services.notification_service import NotificationService
from models.notification import NotificationType


def main(page: ft.Page):
    """Main demo application."""
    page.title = "Enhanced Notification Center Demo"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 800
    page.window.height = 600
    page.padding = 20
    
    # Initialize services
    notification_service = NotificationService()
    
    # Create notification center
    notification_center = NotificationCenter(page, notification_service)
    
    # Demo controls
    def add_info_notification(e):
        notification_service.add_notification(
            "Information Update",
            "New features have been added to the application. Check them out!",
            NotificationType.INFO,
            action_url="/features"
        )
    
    def add_success_notification(e):
        notification_service.add_notification(
            "Task Completed Successfully",
            "Your time tracking session has been saved and synchronized.",
            NotificationType.SUCCESS
        )
    
    def add_warning_notification(e):
        notification_service.add_notification(
            "Storage Warning",
            "You are running low on storage space. Consider cleaning up old files.",
            NotificationType.WARNING,
            action_url="/storage"
        )
    
    def add_error_notification(e):
        notification_service.add_notification(
            "Connection Error",
            "Failed to sync data with the server. Please check your internet connection.",
            NotificationType.ERROR,
            action_url="/settings/network"
        )
    
    def add_multiple_notifications(e):
        """Add multiple notifications to test grouping and filtering."""
        notifications = [
            ("Project Update", "Sprint planning meeting scheduled for tomorrow", NotificationType.INFO),
            ("Backup Complete", "Daily backup completed successfully", NotificationType.SUCCESS),
            ("License Expiring", "Your software license expires in 7 days", NotificationType.WARNING),
            ("Sync Failed", "Unable to sync project files", NotificationType.ERROR),
            ("New Message", "You have received a new message from your team", NotificationType.INFO),
            ("Task Reminder", "Don't forget to submit your timesheet", NotificationType.WARNING),
        ]
        
        for i, (title, message, ntype) in enumerate(notifications):
            # Add some with different timestamps to test grouping
            notification = notification_service.add_notification(title, message, ntype)
            if i < 2:
                # Make some notifications from yesterday
                notification.timestamp = datetime.now() - timedelta(days=1, hours=i)
            elif i < 4:
                # Some from earlier today
                notification.timestamp = datetime.now() - timedelta(hours=i+2)
    
    def simulate_real_time_notifications(e):
        """Simulate real-time notifications arriving."""
        def add_notifications():
            messages = [
                ("System Update", "Installing security updates...", NotificationType.INFO),
                ("Download Complete", "File download finished", NotificationType.SUCCESS),
                ("Memory Warning", "High memory usage detected", NotificationType.WARNING),
                ("Network Error", "Connection timeout occurred", NotificationType.ERROR),
            ]
            
            for title, message, ntype in messages:
                notification_service.add_notification(title, message, ntype)
                time.sleep(2)  # Wait 2 seconds between notifications
        
        # Run in background thread
        thread = threading.Thread(target=add_notifications, daemon=True)
        thread.start()
    
    # Create demo UI
    demo_controls = ft.Column([
        ft.Text("Enhanced Notification Center Demo", size=24, weight=ft.FontWeight.BOLD),
        ft.Text("Click the buttons below to test different notification features:", size=14),
        
        ft.Divider(),
        
        ft.Text("Add Individual Notifications:", size=16, weight=ft.FontWeight.BOLD),
        ft.Row([
            ft.ElevatedButton(
                "Add Info",
                icon=ft.Icons.INFO_OUTLINE,
                on_click=add_info_notification,
                style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_100)
            ),
            ft.ElevatedButton(
                "Add Success",
                icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                on_click=add_success_notification,
                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_100)
            ),
            ft.ElevatedButton(
                "Add Warning",
                icon=ft.Icons.WARNING_OUTLINED,
                on_click=add_warning_notification,
                style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_100)
            ),
            ft.ElevatedButton(
                "Add Error",
                icon=ft.Icons.ERROR_OUTLINE,
                on_click=add_error_notification,
                style=ft.ButtonStyle(bgcolor=ft.Colors.RED_100)
            ),
        ], wrap=True),
        
        ft.Divider(),
        
        ft.Text("Bulk Operations:", size=16, weight=ft.FontWeight.BOLD),
        ft.Row([
            ft.ElevatedButton(
                "Add Multiple Notifications",
                icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                on_click=add_multiple_notifications,
                style=ft.ButtonStyle(bgcolor=ft.Colors.PURPLE_100)
            ),
            ft.ElevatedButton(
                "Simulate Real-time",
                icon=ft.Icons.PLAY_ARROW,
                on_click=simulate_real_time_notifications,
                style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_100)
            ),
        ], wrap=True),
        
        ft.Divider(),
        
        ft.Text("Features to Test:", size=16, weight=ft.FontWeight.BOLD),
        ft.Column([
            ft.Text("• Click the notification bell icon to open/close the panel"),
            ft.Text("• Use the category tabs to filter notifications by type"),
            ft.Text("• Click on notifications to mark them as read"),
            ft.Text("• Use the three-dot menu for individual notification actions"),
            ft.Text("• Try the 'Mark all as read' and 'Clear read' buttons"),
            ft.Text("• Notice the badge counter and visual indicators"),
            ft.Text("• Observe timestamp formatting and date grouping"),
            ft.Text("• Test action buttons on notifications with URLs"),
        ], spacing=5),
    ], spacing=10)
    
    # Main layout
    main_layout = ft.Row([
        ft.Container(
            content=demo_controls,
            expand=True,
            padding=20
        ),
        ft.Container(
            content=notification_center,
            alignment=ft.alignment.top_right,
            padding=20
        )
    ], expand=True)
    
    page.add(main_layout)
    
    # Add some initial notifications for demo
    notification_service.add_notification(
        "Welcome!",
        "Welcome to the Enhanced Notification Center demo. Try the features!",
        NotificationType.INFO
    )


if __name__ == "__main__":
    ft.app(target=main)