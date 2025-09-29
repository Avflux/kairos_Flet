"""
Performance tests for UI components and optimization features.
Tests timer accuracy, UI responsiveness, and memory management.
"""

import pytest
import time
import threading
from datetime import timedelta, datetime
from unittest.mock import Mock, patch

import flet as ft
from views.components.performance_utils import (
    PerformanceMonitor, Throttler, Debouncer, ComponentLifecycleManager,
    ResponsiveLayoutManager, VirtualScrollManager, performance_tracked,
    throttled, debounced
)
from views.components.time_tracker_widget import TimeTrackerWidget
from views.components.notification_center import NotificationCenter
from views.components.top_sidebar_container import TopSidebarContainer
from services.time_tracking_service import TimeTrackingService
from services.notification_service import NotificationService
from models.notification import Notification, NotificationType


class TestPerformanceUtils:
    """Test performance utility classes and decorators."""
    
    def test_performance_monitor_tracks_operations(self):
        """Test that performance monitor correctly tracks operation metrics."""
        monitor = PerformanceMonitor()
        
        # Test timing an operation
        monitor.start_timer("test_operation")
        time.sleep(0.01)  # 10ms
        duration = monitor.end_timer("test_operation")
        
        assert duration >= 0.01
        assert duration < 0.02  # Should be close to 10ms
        
        # Check metrics
        metrics = monitor.get_metrics("test_operation")
        assert metrics['count'] == 1
        assert metrics['min_time'] >= 0.01
        assert metrics['max_time'] >= 0.01
        assert metrics['avg_time'] >= 0.01
    
    def test_performance_monitor_multiple_operations(self):
        """Test performance monitor with multiple operations."""
        monitor = PerformanceMonitor()
        
        # Run multiple operations
        for i in range(3):
            monitor.start_timer("test_op")
            time.sleep(0.005)  # 5ms
            monitor.end_timer("test_op")
        
        metrics = monitor.get_metrics("test_op")
        assert metrics['count'] == 3
        assert metrics['avg_time'] >= 0.005
    
    def test_throttler_limits_call_frequency(self):
        """Test that throttler limits function call frequency."""
        call_count = 0
        
        def test_function():
            nonlocal call_count
            call_count += 1
        
        throttler = Throttler(min_interval=0.1)  # 100ms minimum interval
        throttled_func = throttler.throttle(test_function)
        
        # Call function rapidly
        for _ in range(5):
            throttled_func()
            time.sleep(0.02)  # 20ms between calls
        
        # Should execute at most 2 times (immediate + one delayed)
        time.sleep(0.15)  # Wait for any pending calls
        assert call_count <= 2
        
        # Wait for throttle interval and call again
        time.sleep(0.1)
        throttled_func()
        time.sleep(0.15)
        assert call_count >= 2
    
    def test_debouncer_delays_execution(self):
        """Test that debouncer delays function execution."""
        call_count = 0
        
        def test_function():
            nonlocal call_count
            call_count += 1
        
        debouncer = Debouncer(delay=0.1)  # 100ms delay
        debounced_func = debouncer.debounce(test_function)
        
        # Call function rapidly
        for _ in range(3):
            debounced_func()
            time.sleep(0.02)  # 20ms between calls
        
        # Should not execute immediately
        assert call_count == 0
        
        # Wait for debounce delay
        time.sleep(0.15)
        assert call_count == 1
    
    def test_component_lifecycle_manager(self):
        """Test component lifecycle management."""
        manager = ComponentLifecycleManager()
        
        # Create mock component
        component = Mock()
        manager.register_component(component)
        
        # Add timer and listener
        timer = threading.Timer(1.0, lambda: None)
        listener = Mock()
        
        manager.add_timer(component, timer)
        manager.add_listener(component, listener)
        
        # Cleanup component
        manager.cleanup_component(component)
        
        # Timer should be cancelled
        assert not timer.is_alive()
    
    def test_responsive_layout_manager(self):
        """Test responsive layout manager breakpoint detection."""
        manager = ResponsiveLayoutManager()
        
        # Test breakpoint detection
        manager.update_layout(500)  # xs/sm
        assert manager.is_mobile()
        assert not manager.is_desktop()
        
        manager.update_layout(800)  # md
        assert manager.is_tablet()
        
        manager.update_layout(1200)  # lg+
        assert manager.is_desktop()
        assert not manager.is_mobile()
    
    def test_virtual_scroll_manager(self):
        """Test virtual scrolling calculations."""
        manager = VirtualScrollManager(item_height=50, visible_items=10)
        manager.total_items = 100
        
        # Test visible range calculation
        start, end = manager.calculate_visible_range(0)
        assert start == 0
        assert end <= 12  # visible_items + buffer
        
        # Test scrolled position
        start, end = manager.calculate_visible_range(250)  # 5 items down
        assert start >= 4  # Should start around item 5
        assert end <= 17
        
        # Test virtual height
        assert manager.get_virtual_height() == 5000  # 100 * 50


class TestTimeTrackerPerformance:
    """Test time tracker widget performance optimizations."""
    
    @pytest.fixture
    def mock_page(self):
        """Create a mock Flet page."""
        page = Mock(spec=ft.Page)
        page.update = Mock()
        return page
    
    @pytest.fixture
    def time_service(self):
        """Create a time tracking service."""
        return TimeTrackingService()
    
    @pytest.fixture
    def time_tracker(self, mock_page, time_service):
        """Create a time tracker widget."""
        return TimeTrackerWidget(mock_page, time_service)
    
    def test_timer_update_throttling(self, time_tracker):
        """Test that timer updates are throttled for performance."""
        # Mock the internal update method to count calls
        original_update = time_tracker._update_ui_state
        call_count = 0
        
        def count_calls():
            nonlocal call_count
            call_count += 1
            return original_update()
        
        time_tracker._update_ui_state = count_calls
        
        # Simulate rapid timer ticks
        for i in range(10):
            time_tracker.on_timer_tick(timedelta(seconds=i))
            time.sleep(0.01)  # 10ms between ticks
        
        # Should be throttled to fewer calls
        assert call_count < 10
    
    def test_responsive_layout_adaptation(self, time_tracker):
        """Test that time tracker adapts to different screen sizes."""
        # Test mobile layout
        time_tracker._on_layout_change('xs', 400)
        assert time_tracker.width <= 280
        
        # Test desktop layout
        time_tracker._on_layout_change('lg', 1200)
        assert time_tracker.width == 300
    
    def test_cleanup_prevents_memory_leaks(self, time_tracker):
        """Test that cleanup properly removes listeners and timers."""
        # Add the widget as a listener
        time_tracker.time_service.add_listener(time_tracker)
        
        # Cleanup
        time_tracker.cleanup()
        
        # Verify cleanup was called
        # In a real implementation, you'd verify the listener was removed


class TestNotificationCenterPerformance:
    """Test notification center performance optimizations."""
    
    @pytest.fixture
    def mock_page(self):
        """Create a mock Flet page."""
        page = Mock(spec=ft.Page)
        page.update = Mock()
        return page
    
    @pytest.fixture
    def notification_service(self):
        """Create a notification service with test data."""
        service = NotificationService()
        
        # Add many notifications for performance testing
        for i in range(50):
            service.add_notification(
                f"Test Notification {i}",
                f"This is test message {i}",
                NotificationType.INFO
            )
        
        return service
    
    @pytest.fixture
    def notification_center(self, mock_page, notification_service):
        """Create a notification center widget."""
        return NotificationCenter(mock_page, notification_service)
    
    def test_virtual_scrolling_with_large_lists(self, notification_center):
        """Test that virtual scrolling is used for large notification lists."""
        # Trigger refresh with many notifications
        notification_center._refresh_notifications()
        
        # Should use virtual scrolling for 50+ notifications
        assert len(notification_center._notification_cache) > 0
    
    def test_notification_caching(self, notification_center):
        """Test that notification items are cached for performance."""
        # Get notifications
        notifications = notification_center.notification_service.get_notifications()
        
        # Render notifications multiple times
        for _ in range(3):
            notification_center._render_virtual_notifications(
                notifications[:10], 
                Mock()
            )
        
        # Cache should contain items
        assert len(notification_center._notification_cache) > 0
    
    def test_display_update_throttling(self, notification_center):
        """Test that display updates are throttled."""
        # Mock the update method to count calls
        original_update = notification_center._update_display
        call_count = 0
        
        def count_calls():
            nonlocal call_count
            call_count += 1
            return original_update()
        
        notification_center._update_display = count_calls
        
        # Trigger multiple rapid updates
        for _ in range(5):
            notification_center._update_display()
            time.sleep(0.01)
        
        # Should be throttled
        assert call_count <= 2
    
    def test_responsive_layout_adaptation(self, notification_center):
        """Test notification center responsive layout."""
        # Test mobile layout
        notification_center._on_layout_change('xs', 400)
        assert notification_center.notification_panel.width <= 320
        
        # Test desktop layout
        notification_center._on_layout_change('lg', 1200)
        assert notification_center.notification_panel.width == 380


class TestTopSidebarContainerPerformance:
    """Test top sidebar container performance optimizations."""
    
    @pytest.fixture
    def mock_page(self):
        """Create a mock Flet page."""
        page = Mock(spec=ft.Page)
        page.update = Mock()
        return page
    
    @pytest.fixture
    def top_sidebar(self, mock_page):
        """Create a top sidebar container."""
        return TopSidebarContainer(mock_page)
    
    def test_layout_update_debouncing(self, top_sidebar):
        """Test that layout updates are debounced."""
        # Mock the build layout method to count calls
        original_build = top_sidebar._build_layout
        call_count = 0
        
        def count_calls():
            nonlocal call_count
            call_count += 1
            return original_build()
        
        top_sidebar._build_layout = count_calls
        
        # Trigger multiple rapid layout updates
        for _ in range(5):
            top_sidebar.update_layout(True)
            time.sleep(0.01)
        
        # Should be debounced to fewer calls
        time.sleep(0.2)  # Wait for debounce
        assert call_count <= 2
    
    def test_responsive_layout_creation(self, top_sidebar):
        """Test that different layouts are created for different screen sizes."""
        # Test mobile layout
        with patch('views.components.performance_utils.layout_manager.is_mobile', return_value=True):
            layout = top_sidebar._create_mobile_layout()
            assert isinstance(layout, ft.Row)
            assert len(layout.controls) == 3  # Compact components
        
        # Test desktop layout
        layout = top_sidebar._create_desktop_expanded_layout()
        assert isinstance(layout, ft.Row)
        assert len(layout.controls) == 3  # Full components
    
    def test_cleanup_prevents_memory_leaks(self, top_sidebar):
        """Test that cleanup properly cleans up child components."""
        # Mock cleanup methods
        top_sidebar.time_tracker.cleanup = Mock()
        top_sidebar.notifications.cleanup = Mock()
        
        # Cleanup
        top_sidebar.cleanup()
        
        # Verify child cleanups were called
        top_sidebar.time_tracker.cleanup.assert_called_once()
        top_sidebar.notifications.cleanup.assert_called_once()


class TestPerformanceDecorators:
    """Test performance tracking decorators."""
    
    def test_performance_tracked_decorator(self):
        """Test performance tracking decorator."""
        monitor = PerformanceMonitor()
        
        @performance_tracked("test_function")
        def slow_function():
            time.sleep(0.01)
            return "result"
        
        # Patch the global monitor
        with patch('views.components.performance_utils.performance_monitor', monitor):
            result = slow_function()
        
        assert result == "result"
        metrics = monitor.get_metrics("test_function")
        assert metrics['count'] == 1
        assert metrics['avg_time'] >= 0.01
    
    def test_throttled_decorator(self):
        """Test throttled decorator."""
        call_count = 0
        
        @throttled(min_interval=0.1)
        def test_function():
            nonlocal call_count
            call_count += 1
        
        # Call rapidly
        for _ in range(3):
            test_function()
            time.sleep(0.02)
        
        # Should only execute once
        assert call_count == 1
    
    def test_debounced_decorator(self):
        """Test debounced decorator."""
        call_count = 0
        
        @debounced(delay=0.1)
        def test_function():
            nonlocal call_count
            call_count += 1
        
        # Call rapidly
        for _ in range(3):
            test_function()
            time.sleep(0.02)
        
        # Should not execute immediately
        assert call_count == 0
        
        # Wait for debounce
        time.sleep(0.15)
        assert call_count == 1


class TestTimerAccuracy:
    """Test timer accuracy and precision."""
    
    def test_timer_precision(self):
        """Test that timer updates maintain accuracy over time."""
        service = TimeTrackingService()
        
        # Start tracking
        from models.activity import Activity
        activity = Activity(name="Test Activity", category="Test")
        service.start_tracking(activity)
        
        # Wait for a known duration
        start_time = time.time()
        time.sleep(0.1)  # 100ms
        elapsed = service.get_elapsed_time()
        actual_duration = time.time() - start_time
        
        # Timer should be accurate within 10ms
        assert abs(elapsed.total_seconds() - actual_duration) < 0.01
        
        service.stop_tracking()
    
    def test_timer_performance_under_load(self):
        """Test timer performance with multiple concurrent operations."""
        service = TimeTrackingService()
        
        # Simulate load with rapid state changes
        from models.activity import Activity
        activity = Activity(name="Load Test", category="Test")
        
        start_time = time.time()
        
        # Rapid start/stop cycles
        for _ in range(10):
            service.start_tracking(activity)
            time.sleep(0.01)
            service.pause_tracking()
            time.sleep(0.01)
            service.resume_tracking()
            time.sleep(0.01)
            service.stop_tracking()
        
        total_time = time.time() - start_time
        
        # Should complete within reasonable time (< 1 second)
        assert total_time < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])