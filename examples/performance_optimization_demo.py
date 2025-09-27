"""
Performance Optimization Demo

This demo showcases the performance optimizations implemented in task 12:
- Responsive design adaptation
- Timer update throttling
- Efficient notification rendering
- Component lifecycle management
- Smooth animations and transitions
"""

import flet as ft
import time
import threading
from datetime import datetime, timedelta

from views.components.time_tracker_widget import TimeTrackerWidget
from views.components.notification_center import NotificationCenter
from views.components.top_sidebar_container import TopSidebarContainer
from views.components.modern_sidebar import ModernSidebar
from views.components.performance_utils import (
    performance_monitor, layout_manager, lifecycle_manager
)
from services.time_tracking_service import TimeTrackingService
from services.notification_service import NotificationService
from services.workflow_service import WorkflowService
from models.notification import NotificationType
from models.activity import Activity


class PerformanceOptimizationDemo:
    """Demo application showcasing performance optimizations."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Performance Optimization Demo"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 20
        
        # Initialize services
        self.time_service = TimeTrackingService()
        self.notification_service = NotificationService()
        self.workflow_service = WorkflowService()
        
        # Performance monitoring
        self.performance_stats = ft.Text("Performance Stats: Loading...", size=12)
        self.layout_info = ft.Text("Layout: Desktop", size=12)
        
        # Create components
        self.setup_components()
        self.setup_layout()
        self.setup_performance_monitoring()
        
        # Add test data
        self.add_test_data()
    
    def setup_components(self):
        """Initialize UI components with performance optimizations."""
        # Time tracker with throttled updates
        self.time_tracker = TimeTrackerWidget(self.page, self.time_service)
        
        # Notification center with virtual scrolling
        self.notification_center = NotificationCenter(self.page, self.notification_service)
        
        # Top sidebar container with responsive layout
        self.top_sidebar = TopSidebarContainer(
            self.page,
            self.time_service,
            self.workflow_service,
            self.notification_service
        )
        
        # Modern sidebar with responsive design
        self.sidebar = ModernSidebar(self.page, self.on_navigation)
    
    def setup_layout(self):
        """Setup the main application layout."""
        # Performance controls
        performance_controls = ft.Container(
            content=ft.Column([
                ft.Text("Performance Optimization Demo", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                
                # Performance stats
                ft.Row([
                    self.performance_stats,
                    self.layout_info
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                # Test controls
                ft.Row([
                    ft.ElevatedButton(
                        "Add 10 Notifications",
                        on_click=self.add_bulk_notifications,
                        icon=ft.Icons.NOTIFICATIONS_ACTIVE
                    ),
                    ft.ElevatedButton(
                        "Start Timer Stress Test",
                        on_click=self.start_timer_stress_test,
                        icon=ft.Icons.TIMER
                    ),
                    ft.ElevatedButton(
                        "Toggle Sidebar",
                        on_click=self.toggle_sidebar,
                        icon=ft.Icons.MENU
                    ),
                    ft.ElevatedButton(
                        "Show Performance Stats",
                        on_click=self.show_performance_stats,
                        icon=ft.Icons.ANALYTICS
                    )
                ], wrap=True, spacing=10),
                
                ft.Divider(),
            ], spacing=10),
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.BLUE_50,
            border_radius=10
        )
        
        # Main content area
        main_content = ft.Container(
            content=ft.Column([
                # Top sidebar container
                self.top_sidebar,
                
                ft.Divider(),
                
                # Demo content
                ft.Container(
                    content=ft.Column([
                        ft.Text("Responsive Design Test", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text("Resize the window to see responsive layout changes."),
                        
                        ft.Text("Performance Features:", size=16, weight=ft.FontWeight.BOLD),
                        ft.Column([
                            ft.Text("✓ Timer updates throttled to 2 FPS for smooth performance"),
                            ft.Text("✓ Notification rendering with virtual scrolling for large lists"),
                            ft.Text("✓ Responsive layout adaptation for different screen sizes"),
                            ft.Text("✓ Component lifecycle management to prevent memory leaks"),
                            ft.Text("✓ Debounced layout updates to prevent excessive redraws"),
                            ft.Text("✓ Smooth animations with optimized timing"),
                        ], spacing=5),
                        
                        ft.Text("Memory Management:", size=16, weight=ft.FontWeight.BOLD),
                        ft.Column([
                            ft.Text("✓ Automatic cleanup of timers and listeners"),
                            ft.Text("✓ Notification item caching with size limits"),
                            ft.Text("✓ Weak references for component lifecycle tracking"),
                            ft.Text("✓ Throttled UI updates to prevent excessive rendering"),
                        ], spacing=5),
                    ], spacing=15),
                    padding=ft.padding.all(20)
                )
            ], spacing=20),
            expand=True
        )
        
        # Layout with sidebar
        app_layout = ft.Row([
            self.sidebar,
            ft.Container(
                content=ft.Column([
                    performance_controls,
                    main_content
                ], expand=True),
                expand=True,
                padding=ft.padding.only(left=20)
            )
        ], expand=True)
        
        self.page.add(app_layout)
        
        # Setup window resize handler for responsive testing
        self.page.on_resize = self.on_window_resize
    
    def setup_performance_monitoring(self):
        """Setup performance monitoring and stats display."""
        def update_stats():
            while True:
                try:
                    # Get performance metrics
                    metrics = performance_monitor.get_metrics()
                    
                    # Format stats
                    stats_text = "Performance: "
                    if metrics:
                        avg_times = [m.get('avg_time', 0) for m in metrics.values()]
                        if avg_times:
                            avg_time = sum(avg_times) / len(avg_times)
                            stats_text += f"Avg: {avg_time*1000:.1f}ms"
                    else:
                        stats_text += "No data"
                    
                    # Update layout info
                    breakpoint = layout_manager.current_breakpoint
                    layout_text = f"Layout: {breakpoint} ({'Mobile' if layout_manager.is_mobile() else 'Desktop'})"
                    
                    # Update UI (throttled)
                    if hasattr(self, 'performance_stats'):
                        self.performance_stats.value = stats_text
                        self.layout_info.value = layout_text
                        
                        if self.page:
                            self.page.update()
                    
                    time.sleep(1)  # Update every second
                except Exception as e:
                    print(f"Stats update error: {e}")
                    time.sleep(1)
        
        # Start stats thread
        stats_thread = threading.Thread(target=update_stats, daemon=True)
        stats_thread.start()
    
    def add_test_data(self):
        """Add test data for demonstration."""
        # Add some test activities
        activities = [
            Activity(name="Development", category="Work"),
            Activity(name="Testing", category="Work"),
            Activity(name="Documentation", category="Work"),
            Activity(name="Meeting", category="Communication"),
        ]
        
        self.time_tracker.set_activities(activities)
        
        # Add some test notifications
        test_notifications = [
            ("Welcome", "Welcome to the performance optimization demo!", NotificationType.INFO),
            ("Timer Ready", "Time tracker is ready for use.", NotificationType.SUCCESS),
            ("Performance", "All optimizations are active.", NotificationType.INFO),
        ]
        
        for title, message, type_ in test_notifications:
            self.notification_service.add_notification(title, message, type_)
    
    def add_bulk_notifications(self, e):
        """Add multiple notifications to test performance."""
        notification_types = [
            NotificationType.INFO,
            NotificationType.SUCCESS,
            NotificationType.WARNING,
            NotificationType.ERROR
        ]
        
        for i in range(10):
            type_ = notification_types[i % len(notification_types)]
            self.notification_service.add_notification(
                f"Bulk Notification {i+1}",
                f"This is test notification number {i+1} for performance testing.",
                type_
            )
        
        # Show success message
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text("Added 10 notifications - check performance!"),
                bgcolor=ft.Colors.GREEN
            )
        )
    
    def start_timer_stress_test(self, e):
        """Start a timer stress test to demonstrate throttling."""
        if not self.time_tracker.is_running:
            # Start with first activity
            activities = [
                Activity(name="Stress Test", category="Performance"),
            ]
            self.time_tracker.set_activities(activities)
            self.time_tracker.current_activity = activities[0]
            self.time_tracker._on_start_click(None)
            
            # Show info
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Timer stress test started - watch the smooth updates!"),
                    bgcolor=ft.Colors.BLUE
                )
            )
        else:
            self.time_tracker._on_stop_click(None)
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Timer stopped"),
                    bgcolor=ft.Colors.ORANGE
                )
            )
    
    def toggle_sidebar(self, e):
        """Toggle sidebar to test responsive layout."""
        self.sidebar._toggle_sidebar(None)
        
        # Update top sidebar layout
        self.top_sidebar.update_layout(self.sidebar.expanded)
    
    def show_performance_stats(self, e):
        """Show detailed performance statistics."""
        metrics = performance_monitor.get_metrics()
        
        if not metrics:
            stats_text = "No performance data available yet.\nTry using the timer or adding notifications."
        else:
            stats_lines = ["Performance Statistics:", ""]
            for operation, data in metrics.items():
                stats_lines.append(f"{operation}:")
                stats_lines.append(f"  Calls: {data['count']}")
                stats_lines.append(f"  Avg Time: {data['avg_time']*1000:.2f}ms")
                stats_lines.append(f"  Min Time: {data['min_time']*1000:.2f}ms")
                stats_lines.append(f"  Max Time: {data['max_time']*1000:.2f}ms")
                stats_lines.append("")
            
            stats_text = "\n".join(stats_lines)
        
        # Show in dialog
        dialog = ft.AlertDialog(
            title=ft.Text("Performance Statistics"),
            content=ft.Container(
                content=ft.Text(stats_text, selectable=True),
                width=400,
                height=300
            ),
            actions=[
                ft.TextButton("Reset Stats", on_click=self.reset_performance_stats),
                ft.TextButton("Close", on_click=self.close_dialog)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def reset_performance_stats(self, e):
        """Reset performance statistics."""
        performance_monitor.reset_metrics()
        self.page.dialog.open = False
        self.page.update()
        
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text("Performance statistics reset"),
                bgcolor=ft.Colors.GREEN
            )
        )
    
    def close_dialog(self, e):
        """Close the current dialog."""
        self.page.dialog.open = False
        self.page.update()
    
    def on_window_resize(self, e):
        """Handle window resize for responsive testing."""
        # Update layout manager with new dimensions
        if hasattr(e, 'width') and e.width:
            layout_manager.update_layout(e.width)
    
    def on_navigation(self, route: str):
        """Handle navigation events."""
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text(f"Navigated to: {route}"),
                duration=1000
            )
        )
    
    def cleanup(self):
        """Clean up resources when closing the app."""
        # Clean up components
        if hasattr(self.time_tracker, 'cleanup'):
            self.time_tracker.cleanup()
        if hasattr(self.notification_center, 'cleanup'):
            self.notification_center.cleanup()
        if hasattr(self.top_sidebar, 'cleanup'):
            self.top_sidebar.cleanup()
        if hasattr(self.sidebar, 'cleanup'):
            self.sidebar.cleanup()
        
        # Clean up lifecycle manager
        lifecycle_manager.cleanup_all()


def main(page: ft.Page):
    """Main application entry point."""
    demo = PerformanceOptimizationDemo(page)
    
    # Handle app close
    def on_window_event(e):
        if e.data == "close":
            demo.cleanup()
    
    page.on_window_event = on_window_event


if __name__ == "__main__":
    # Run the demo
    ft.app(
        target=main,
        name="Performance Optimization Demo",
        assets_dir="assets"
    )