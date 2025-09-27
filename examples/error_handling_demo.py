"""
Comprehensive error handling and user feedback demonstration.
Shows how to implement robust error handling across all components.
"""

import flet as ft
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Optional

from models.activity import Activity
from models.notification import NotificationType
from services.notification_service import NotificationService
from services.time_tracking_service import TimeTrackingService
from services.workflow_service import WorkflowService
from views.components.error_handling import (
    create_error_boundary, get_recovery_manager, get_storage_manager,
    ToastNotificationManager, FeedbackType, ErrorSeverity
)
from views.components.notification_center import NotificationCenter
from views.components.time_tracker_widget import TimeTrackerWidget
from views.components.flowchart_widget import FlowchartWidget


class ErrorHandlingDemo:
    """Demonstration of comprehensive error handling and recovery."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Error Handling & User Feedback Demo"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        
        # Initialize services
        self.notification_service = NotificationService()
        self.time_service = TimeTrackingService()
        self.workflow_service = WorkflowService()
        
        # Initialize error handling components
        self.toast_manager = ToastNotificationManager(page)
        self.recovery_manager = get_recovery_manager()
        self.storage_manager = get_storage_manager()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Register custom recovery strategies
        self._register_recovery_strategies()
        
        # Create UI components
        self._create_ui()
    
    def _register_recovery_strategies(self):
        """Register custom recovery strategies for demo scenarios."""
        
        def recover_from_demo_error(context):
            """Custom recovery strategy for demo errors."""
            logging.info(f"Attempting recovery for {context.component_name}.{context.operation}")
            
            # Simulate recovery process
            time.sleep(1)
            
            # Show recovery notification
            self.toast_manager.show_success(
                f"Recovered from error in {context.component_name}",
                "Recovery Successful"
            )
            
            return True
        
        self.recovery_manager.register_recovery_strategy(
            'DemoError', recover_from_demo_error
        )
        self.recovery_manager.register_recovery_strategy(
            'ValueError', recover_from_demo_error
        )
        self.recovery_manager.register_recovery_strategy(
            'ConnectionError', recover_from_demo_error
        )
    
    def _create_ui(self):
        """Create the demonstration UI."""
        
        # Title
        title = ft.Text(
            "Error Handling & User Feedback Demo",
            size=24,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_800
        )
        
        # Error simulation section
        error_section = self._create_error_simulation_section()
        
        # Recovery demonstration section
        recovery_section = self._create_recovery_demonstration_section()
        
        # Toast notification section
        toast_section = self._create_toast_demonstration_section()
        
        # Component health monitoring section
        health_section = self._create_health_monitoring_section()
        
        # Backup and restore section
        backup_section = self._create_backup_demonstration_section()
        
        # Main layout
        main_content = ft.Column([
            title,
            ft.Divider(),
            error_section,
            ft.Divider(),
            recovery_section,
            ft.Divider(),
            toast_section,
            ft.Divider(),
            health_section,
            ft.Divider(),
            backup_section
        ], spacing=20, scroll=ft.ScrollMode.AUTO)
        
        self.page.add(
            ft.Container(
                content=main_content,
                padding=ft.padding.all(20),
                expand=True
            )
        )
    
    def _create_error_simulation_section(self) -> ft.Container:
        """Create error simulation demonstration section."""
        
        def simulate_service_error(e):
            """Simulate a service error."""
            try:
                # Intentionally cause an error
                raise ConnectionError("Simulated network failure")
            except Exception as error:
                error_boundary = create_error_boundary("DemoComponent", self.page)
                error_boundary._handle_error(error, error_boundary.error_boundary.ErrorContext(
                    component_name="DemoComponent",
                    operation="simulate_error",
                    severity=ErrorSeverity.MEDIUM
                ))
        
        def simulate_critical_error(e):
            """Simulate a critical error."""
            try:
                # Simulate memory error
                raise MemoryError("Simulated memory exhaustion")
            except Exception as error:
                error_boundary = create_error_boundary("DemoComponent", self.page)
                error_boundary._handle_error(error, error_boundary.error_boundary.ErrorContext(
                    component_name="DemoComponent",
                    operation="critical_error",
                    severity=ErrorSeverity.CRITICAL
                ))
        
        def simulate_validation_error(e):
            """Simulate a validation error."""
            try:
                # Simulate validation failure
                raise ValueError("Invalid input data provided")
            except Exception as error:
                error_boundary = create_error_boundary("DemoComponent", self.page)
                error_boundary._handle_error(error, error_boundary.error_boundary.ErrorContext(
                    component_name="DemoComponent",
                    operation="validation",
                    severity=ErrorSeverity.LOW
                ))
        
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "Error Simulation",
                    size=18,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.RED_700
                ),
                ft.Text(
                    "Simulate different types of errors to see error handling in action:",
                    size=14,
                    color=ft.Colors.GREY_700
                ),
                ft.Row([
                    ft.ElevatedButton(
                        "Service Error",
                        icon=ft.Icons.CLOUD_OFF,
                        on_click=simulate_service_error,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.ORANGE_100,
                            color=ft.Colors.ORANGE_800
                        )
                    ),
                    ft.ElevatedButton(
                        "Critical Error",
                        icon=ft.Icons.ERROR,
                        on_click=simulate_critical_error,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.RED_100,
                            color=ft.Colors.RED_800
                        )
                    ),
                    ft.ElevatedButton(
                        "Validation Error",
                        icon=ft.Icons.WARNING,
                        on_click=simulate_validation_error,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.YELLOW_100,
                            color=ft.Colors.YELLOW_800
                        )
                    )
                ], spacing=10)
            ], spacing=10),
            padding=ft.padding.all(16),
            bgcolor=ft.Colors.RED_50,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.RED_200)
        )
    
    def _create_recovery_demonstration_section(self) -> ft.Container:
        """Create recovery demonstration section."""
        
        self.recovery_status = ft.Text(
            "No recovery attempts yet",
            size=12,
            color=ft.Colors.GREY_600
        )
        
        def test_recovery_mechanism(e):
            """Test the recovery mechanism."""
            def recovery_test():
                try:
                    # Simulate an error that can be recovered
                    raise ValueError("Recoverable error for testing")
                except Exception as error:
                    error_boundary = create_error_boundary("RecoveryDemo", self.page)
                    
                    # Attempt recovery
                    recovery_attempted = self.recovery_manager.attempt_recovery(
                        "ValueError",
                        error_boundary.error_boundary.ErrorContext(
                            component_name="RecoveryDemo",
                            operation="recovery_test"
                        )
                    )
                    
                    if recovery_attempted:
                        self.recovery_status.value = f"Recovery successful at {datetime.now().strftime('%H:%M:%S')}"
                        self.recovery_status.color = ft.Colors.GREEN_600
                    else:
                        self.recovery_status.value = f"Recovery failed at {datetime.now().strftime('%H:%M:%S')}"
                        self.recovery_status.color = ft.Colors.RED_600
                    
                    self.page.update()
            
            # Run recovery test in background
            threading.Thread(target=recovery_test, daemon=True).start()
        
        def show_error_patterns(e):
            """Show error patterns analysis."""
            patterns = self.recovery_manager.get_error_patterns()
            
            if patterns:
                pattern_text = "Error Patterns:\n" + "\n".join([
                    f"• {pattern}: {count} occurrences"
                    for pattern, count in patterns.items()
                ])
            else:
                pattern_text = "No error patterns recorded yet"
            
            self.toast_manager.show_info(pattern_text, "Error Analysis")
        
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "Recovery Mechanisms",
                    size=18,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.GREEN_700
                ),
                ft.Text(
                    "Test automatic error recovery and pattern analysis:",
                    size=14,
                    color=ft.Colors.GREY_700
                ),
                ft.Row([
                    ft.ElevatedButton(
                        "Test Recovery",
                        icon=ft.Icons.HEALING,
                        on_click=test_recovery_mechanism,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.GREEN_100,
                            color=ft.Colors.GREEN_800
                        )
                    ),
                    ft.ElevatedButton(
                        "Show Error Patterns",
                        icon=ft.Icons.ANALYTICS,
                        on_click=show_error_patterns,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.BLUE_100,
                            color=ft.Colors.BLUE_800
                        )
                    )
                ], spacing=10),
                self.recovery_status
            ], spacing=10),
            padding=ft.padding.all(16),
            bgcolor=ft.Colors.GREEN_50,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREEN_200)
        )
    
    def _create_toast_demonstration_section(self) -> ft.Container:
        """Create toast notification demonstration section."""
        
        def show_success_toast(e):
            self.toast_manager.show_success(
                "Operation completed successfully!",
                "Success"
            )
        
        def show_error_toast(e):
            self.toast_manager.show_error(
                "An error occurred while processing your request.",
                "Error"
            )
        
        def show_warning_toast(e):
            self.toast_manager.show_warning(
                "Please check your input before proceeding.",
                "Warning"
            )
        
        def show_info_toast(e):
            self.toast_manager.show_info(
                "Here's some helpful information for you.",
                "Information"
            )
        
        def show_action_toast(e):
            def handle_action():
                self.toast_manager.show_success("Action completed!", "Done")
            
            self.toast_manager.show_toast(
                "Click the action button to continue.",
                FeedbackType.INFO,
                "Action Required",
                action_text="Continue",
                action_callback=lambda e: handle_action()
            )
        
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "Toast Notifications",
                    size=18,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.BLUE_700
                ),
                ft.Text(
                    "Non-blocking user feedback messages:",
                    size=14,
                    color=ft.Colors.GREY_700
                ),
                ft.Row([
                    ft.ElevatedButton(
                        "Success",
                        icon=ft.Icons.CHECK_CIRCLE,
                        on_click=show_success_toast,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.GREEN_100,
                            color=ft.Colors.GREEN_800
                        )
                    ),
                    ft.ElevatedButton(
                        "Error",
                        icon=ft.Icons.ERROR,
                        on_click=show_error_toast,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.RED_100,
                            color=ft.Colors.RED_800
                        )
                    ),
                    ft.ElevatedButton(
                        "Warning",
                        icon=ft.Icons.WARNING,
                        on_click=show_warning_toast,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.ORANGE_100,
                            color=ft.Colors.ORANGE_800
                        )
                    ),
                    ft.ElevatedButton(
                        "Info",
                        icon=ft.Icons.INFO,
                        on_click=show_info_toast,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.BLUE_100,
                            color=ft.Colors.BLUE_800
                        )
                    ),
                    ft.ElevatedButton(
                        "With Action",
                        icon=ft.Icons.TOUCH_APP,
                        on_click=show_action_toast,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.PURPLE_100,
                            color=ft.Colors.PURPLE_800
                        )
                    )
                ], spacing=10, wrap=True)
            ], spacing=10),
            padding=ft.padding.all(16),
            bgcolor=ft.Colors.BLUE_50,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.BLUE_200)
        )
    
    def _create_health_monitoring_section(self) -> ft.Container:
        """Create component health monitoring section."""
        
        self.health_display = ft.Column([], spacing=5)
        
        def check_component_health(e):
            """Check and display component health status."""
            self.health_display.controls.clear()
            
            # Check service health
            services = [
                ("NotificationService", self.notification_service),
                ("TimeTrackingService", self.time_service),
                ("WorkflowService", self.workflow_service)
            ]
            
            for service_name, service in services:
                try:
                    # Basic health check - try to call a simple method
                    if hasattr(service, 'get_notifications'):
                        service.get_notifications()
                    elif hasattr(service, 'is_tracking'):
                        service.is_tracking()
                    elif hasattr(service, 'get_all_workflows'):
                        service.get_all_workflows()
                    
                    status_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_600, size=16)
                    status_text = "Healthy"
                    status_color = ft.Colors.GREEN_600
                    
                except Exception as e:
                    status_icon = ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_600, size=16)
                    status_text = f"Error: {str(e)[:50]}..."
                    status_color = ft.Colors.RED_600
                
                health_row = ft.Row([
                    status_icon,
                    ft.Text(service_name, size=14, weight=ft.FontWeight.W_500),
                    ft.Text(status_text, size=12, color=status_color)
                ], spacing=8)
                
                self.health_display.controls.append(health_row)
            
            # Add timestamp
            timestamp = ft.Text(
                f"Last checked: {datetime.now().strftime('%H:%M:%S')}",
                size=10,
                color=ft.Colors.GREY_500
            )
            self.health_display.controls.append(timestamp)
            
            self.page.update()
        
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "Component Health Monitoring",
                    size=18,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.PURPLE_700
                ),
                ft.Text(
                    "Monitor the health status of application components:",
                    size=14,
                    color=ft.Colors.GREY_700
                ),
                ft.ElevatedButton(
                    "Check Health",
                    icon=ft.Icons.HEALTH_AND_SAFETY,
                    on_click=check_component_health,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.PURPLE_100,
                        color=ft.Colors.PURPLE_800
                    )
                ),
                self.health_display
            ], spacing=10),
            padding=ft.padding.all(16),
            bgcolor=ft.Colors.PURPLE_50,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.PURPLE_200)
        )
    
    def _create_backup_demonstration_section(self) -> ft.Container:
        """Create backup and restore demonstration section."""
        
        self.backup_status = ft.Text(
            "No backup operations yet",
            size=12,
            color=ft.Colors.GREY_600
        )
        
        def create_backup(e):
            """Create a backup of critical data."""
            try:
                # Backup notifications
                notifications = self.notification_service.get_notifications()
                notification_data = [
                    {
                        'id': n.id,
                        'title': n.title,
                        'message': n.message,
                        'type': n.type.value,
                        'timestamp': n.timestamp.isoformat(),
                        'is_read': n.is_read
                    }
                    for n in notifications
                ]
                
                success = self.storage_manager.backup_data('demo_notifications', notification_data)
                
                if success:
                    self.backup_status.value = f"Backup created at {datetime.now().strftime('%H:%M:%S')}"
                    self.backup_status.color = ft.Colors.GREEN_600
                    self.toast_manager.show_success("Backup created successfully", "Backup")
                else:
                    self.backup_status.value = "Backup failed"
                    self.backup_status.color = ft.Colors.RED_600
                    self.toast_manager.show_error("Failed to create backup", "Backup Error")
                
            except Exception as e:
                self.backup_status.value = f"Backup error: {str(e)}"
                self.backup_status.color = ft.Colors.RED_600
                self.toast_manager.show_error(f"Backup error: {str(e)}", "Backup Error")
            
            self.page.update()
        
        def restore_backup(e):
            """Restore data from backup."""
            try:
                backup_data = self.storage_manager.restore_data('demo_notifications')
                
                if backup_data:
                    self.backup_status.value = f"Restored {len(backup_data)} items at {datetime.now().strftime('%H:%M:%S')}"
                    self.backup_status.color = ft.Colors.BLUE_600
                    self.toast_manager.show_success(f"Restored {len(backup_data)} notifications", "Restore")
                else:
                    self.backup_status.value = "No backup data found"
                    self.backup_status.color = ft.Colors.ORANGE_600
                    self.toast_manager.show_warning("No backup data found", "Restore")
                
            except Exception as e:
                self.backup_status.value = f"Restore error: {str(e)}"
                self.backup_status.color = ft.Colors.RED_600
                self.toast_manager.show_error(f"Restore error: {str(e)}", "Restore Error")
            
            self.page.update()
        
        def list_backups(e):
            """List available backups."""
            try:
                backups = self.storage_manager.list_backups()
                
                if backups:
                    backup_list = "Available backups:\n" + "\n".join([f"• {backup}" for backup in backups])
                    self.toast_manager.show_info(backup_list, "Backup List")
                else:
                    self.toast_manager.show_info("No backups available", "Backup List")
                
            except Exception as e:
                self.toast_manager.show_error(f"Failed to list backups: {str(e)}", "Backup Error")
        
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "Backup & Restore",
                    size=18,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.TEAL_700
                ),
                ft.Text(
                    "Demonstrate data backup and recovery mechanisms:",
                    size=14,
                    color=ft.Colors.GREY_700
                ),
                ft.Row([
                    ft.ElevatedButton(
                        "Create Backup",
                        icon=ft.Icons.BACKUP,
                        on_click=create_backup,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.TEAL_100,
                            color=ft.Colors.TEAL_800
                        )
                    ),
                    ft.ElevatedButton(
                        "Restore Backup",
                        icon=ft.Icons.RESTORE,
                        on_click=restore_backup,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.BLUE_100,
                            color=ft.Colors.BLUE_800
                        )
                    ),
                    ft.ElevatedButton(
                        "List Backups",
                        icon=ft.Icons.LIST,
                        on_click=list_backups,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.GREY_100,
                            color=ft.Colors.GREY_800
                        )
                    )
                ], spacing=10),
                self.backup_status
            ], spacing=10),
            padding=ft.padding.all(16),
            bgcolor=ft.Colors.TEAL_50,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.TEAL_200)
        )


def main(page: ft.Page):
    """Main function to run the error handling demo."""
    demo = ErrorHandlingDemo(page)


if __name__ == "__main__":
    ft.app(target=main)