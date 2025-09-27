"""
Performance utilities for optimizing UI components and preventing memory leaks.
Provides throttling, debouncing, and lifecycle management for Flet components.
"""

import flet as ft
import threading
import time
from typing import Callable, Optional, Any, Dict, Set
from datetime import datetime, timedelta
from functools import wraps
from weakref import WeakSet, WeakKeyDictionary


class PerformanceMonitor:
    """Monitor and track performance metrics for UI components."""
    
    def __init__(self):
        self.metrics: Dict[str, Dict[str, Any]] = {}
        self.start_times: Dict[str, float] = {}
    
    def start_timer(self, operation: str) -> None:
        """Start timing an operation."""
        self.start_times[operation] = time.perf_counter()
    
    def end_timer(self, operation: str) -> float:
        """End timing an operation and return duration."""
        if operation in self.start_times:
            duration = time.perf_counter() - self.start_times[operation]
            
            if operation not in self.metrics:
                self.metrics[operation] = {
                    'count': 0,
                    'total_time': 0,
                    'min_time': float('inf'),
                    'max_time': 0,
                    'avg_time': 0
                }
            
            metrics = self.metrics[operation]
            metrics['count'] += 1
            metrics['total_time'] += duration
            metrics['min_time'] = min(metrics['min_time'], duration)
            metrics['max_time'] = max(metrics['max_time'], duration)
            metrics['avg_time'] = metrics['total_time'] / metrics['count']
            
            del self.start_times[operation]
            return duration
        return 0
    
    def get_metrics(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """Get performance metrics for an operation or all operations."""
        if operation:
            return self.metrics.get(operation, {})
        return self.metrics.copy()
    
    def reset_metrics(self, operation: Optional[str] = None) -> None:
        """Reset metrics for an operation or all operations."""
        if operation:
            self.metrics.pop(operation, None)
        else:
            self.metrics.clear()


class Throttler:
    """Throttle function calls to prevent excessive updates."""
    
    def __init__(self, min_interval: float = 0.1):
        """
        Initialize throttler.
        
        Args:
            min_interval: Minimum interval between calls in seconds
        """
        self.min_interval = min_interval
        self.last_call_time = 0
        self.pending_call = None
        self.lock = threading.Lock()
    
    def throttle(self, func: Callable) -> Callable:
        """
        Decorator to throttle function calls.
        
        Args:
            func: Function to throttle
            
        Returns:
            Throttled function
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.lock:
                current_time = time.time()
                time_since_last = current_time - self.last_call_time
                
                if time_since_last >= self.min_interval:
                    # Execute immediately
                    self.last_call_time = current_time
                    return func(*args, **kwargs)
                else:
                    # Schedule for later execution
                    if self.pending_call:
                        self.pending_call.cancel()
                    
                    delay = self.min_interval - time_since_last
                    self.pending_call = threading.Timer(delay, func, args, kwargs)
                    self.pending_call.start()
        
        return wrapper


class Debouncer:
    """Debounce function calls to prevent rapid successive calls."""
    
    def __init__(self, delay: float = 0.3):
        """
        Initialize debouncer.
        
        Args:
            delay: Delay in seconds before executing the function
        """
        self.delay = delay
        self.timer = None
        self.lock = threading.Lock()
    
    def debounce(self, func: Callable) -> Callable:
        """
        Decorator to debounce function calls.
        
        Args:
            func: Function to debounce
            
        Returns:
            Debounced function
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.lock:
                if self.timer:
                    self.timer.cancel()
                
                self.timer = threading.Timer(self.delay, func, args, kwargs)
                self.timer.start()
        
        return wrapper


class ComponentLifecycleManager:
    """Manage component lifecycle to prevent memory leaks."""
    
    def __init__(self):
        self.active_components: WeakSet = WeakSet()
        self.timers: WeakKeyDictionary = WeakKeyDictionary()
        self.listeners: WeakKeyDictionary = WeakKeyDictionary()
    
    def register_component(self, component: Any) -> None:
        """Register a component for lifecycle management."""
        self.active_components.add(component)
        self.timers[component] = []
        self.listeners[component] = []
    
    def add_timer(self, component: Any, timer: threading.Timer) -> None:
        """Add a timer associated with a component."""
        if component in self.timers:
            self.timers[component].append(timer)
    
    def add_listener(self, component: Any, listener: Any) -> None:
        """Add a listener associated with a component."""
        if component in self.listeners:
            self.listeners[component].append(listener)
    
    def cleanup_component(self, component: Any) -> None:
        """Clean up resources associated with a component."""
        # Cancel timers
        if component in self.timers:
            for timer in self.timers[component]:
                if timer.is_alive():
                    timer.cancel()
            del self.timers[component]
        
        # Remove listeners
        if component in self.listeners:
            # In a real implementation, you'd call specific cleanup methods
            # for each listener type
            del self.listeners[component]
        
        # Remove from active components
        self.active_components.discard(component)
    
    def cleanup_all(self) -> None:
        """Clean up all registered components."""
        components_to_cleanup = list(self.active_components)
        for component in components_to_cleanup:
            self.cleanup_component(component)


class ResponsiveLayoutManager:
    """Manage responsive layouts based on container size."""
    
    def __init__(self):
        self.breakpoints = {
            'xs': 0,
            'sm': 576,
            'md': 768,
            'lg': 992,
            'xl': 1200,
            'xxl': 1400
        }
        self.current_breakpoint = 'lg'
        self.layout_callbacks: Dict[str, Callable] = {}
    
    def register_layout_callback(self, component_id: str, callback: Callable) -> None:
        """Register a callback for layout changes."""
        self.layout_callbacks[component_id] = callback
    
    def update_layout(self, width: float) -> None:
        """Update layout based on container width."""
        new_breakpoint = self._get_breakpoint(width)
        
        if new_breakpoint != self.current_breakpoint:
            self.current_breakpoint = new_breakpoint
            
            # Notify all registered components
            for callback in self.layout_callbacks.values():
                try:
                    callback(new_breakpoint, width)
                except Exception as e:
                    print(f"Error in layout callback: {e}")
    
    def _get_breakpoint(self, width: float) -> str:
        """Determine the current breakpoint based on width."""
        for breakpoint in reversed(list(self.breakpoints.keys())):
            if width >= self.breakpoints[breakpoint]:
                return breakpoint
        return 'xs'
    
    def is_mobile(self) -> bool:
        """Check if current layout is mobile."""
        return self.current_breakpoint in ['xs', 'sm']
    
    def is_tablet(self) -> bool:
        """Check if current layout is tablet."""
        return self.current_breakpoint in ['md']
    
    def is_desktop(self) -> bool:
        """Check if current layout is desktop."""
        return self.current_breakpoint in ['lg', 'xl', 'xxl']


class AnimationManager:
    """Manage smooth animations and transitions."""
    
    @staticmethod
    def create_fade_animation(duration: int = 300) -> ft.Animation:
        """Create a fade animation."""
        return ft.Animation(duration, ft.AnimationCurve.EASE_IN_OUT)
    
    @staticmethod
    def create_slide_animation(duration: int = 250) -> ft.Animation:
        """Create a slide animation.""" 
        return ft.Animation(duration, ft.AnimationCurve.EASE_OUT)
    
    @staticmethod
    def create_scale_animation(duration: int = 200) -> ft.Animation:
        """Create a scale animation."""
        return ft.Animation(duration, ft.AnimationCurve.EASE_IN_OUT)
    
    @staticmethod
    def create_bounce_animation(duration: int = 400) -> ft.Animation:
        """Create a bounce animation."""
        return ft.Animation(duration, ft.AnimationCurve.BOUNCE_OUT)


class VirtualScrollManager:
    """Manage virtual scrolling for large lists."""
    
    def __init__(self, item_height: float = 60, visible_items: int = 10):
        """
        Initialize virtual scroll manager.
        
        Args:
            item_height: Height of each item in pixels
            visible_items: Number of visible items in the viewport
        """
        self.item_height = item_height
        self.visible_items = visible_items
        self.scroll_offset = 0
        self.total_items = 0
        self.rendered_items: Dict[int, Any] = {}
    
    def calculate_visible_range(self, scroll_position: float) -> tuple[int, int]:
        """
        Calculate which items should be visible based on scroll position.
        
        Args:
            scroll_position: Current scroll position
            
        Returns:
            Tuple of (start_index, end_index)
        """
        start_index = max(0, int(scroll_position // self.item_height) - 1)
        end_index = min(
            self.total_items,
            start_index + self.visible_items + 2
        )
        return start_index, end_index
    
    def get_virtual_height(self) -> float:
        """Get the total virtual height of all items."""
        return self.total_items * self.item_height
    
    def update_scroll_position(self, position: float) -> tuple[int, int]:
        """
        Update scroll position and return visible range.
        
        Args:
            position: New scroll position
            
        Returns:
            Tuple of (start_index, end_index) for visible items
        """
        self.scroll_offset = position
        return self.calculate_visible_range(position)


# Global instances
performance_monitor = PerformanceMonitor()
lifecycle_manager = ComponentLifecycleManager()
layout_manager = ResponsiveLayoutManager()
animation_manager = AnimationManager()


def performance_tracked(operation_name: str):
    """Decorator to track performance of a function."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            performance_monitor.start_timer(operation_name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = performance_monitor.end_timer(operation_name)
                # Log slow operations (> 100ms)
                if duration > 0.1:
                    print(f"Slow operation detected: {operation_name} took {duration:.3f}s")
        return wrapper
    return decorator


def throttled(min_interval: float = 0.1):
    """Decorator to throttle function calls."""
    throttler = Throttler(min_interval)
    return throttler.throttle


def debounced(delay: float = 0.3):
    """Decorator to debounce function calls."""
    debouncer = Debouncer(delay)
    return debouncer.debounce