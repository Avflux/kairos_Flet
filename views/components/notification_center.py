import flet as ft
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime, timedelta
from models.notification import Notification, NotificationType
from services.notification_service import NotificationService
from views.components.design_system import (
    ColorTokens, Typography, Spacing, BorderRadius, Shadows, Animations,
    ComponentStyles, StateColors, HoverEffects, apply_card_style, create_styled_text
)
from views.components.performance_utils import (
    performance_tracked, throttled, debounced, lifecycle_manager,
    layout_manager, VirtualScrollManager, animation_manager
)
from views.components.error_handling import (
    create_error_boundary, get_fallback_manager, safe_execute
)


class NotificationCenter(ft.Container):
    """
    A notification center widget that displays notifications in a dropdown panel.
    Provides basic display functionality with notification management capabilities.
    """
    
    def __init__(self, page: ft.Page, notification_service: NotificationService):
        """
        Initialize the notification center.
        
        Args:
            page: The Flet page instance
            notification_service: The notification service instance
        """
        super().__init__()
        
        self.page = page
        self.notification_service = notification_service
        self.is_expanded = False
        
        # Error handling
        self.error_boundary = create_error_boundary("NotificationCenter", page)
        self.fallback_manager = get_fallback_manager()
        
        # Register fallback component
        self.fallback_manager.register_fallback(
            "NotificationCenter", 
            self._create_fallback_component
        )
        
        # Performance optimization: Register with lifecycle manager
        lifecycle_manager.register_component(self)
        
        # Virtual scrolling for large notification lists
        self.virtual_scroll = VirtualScrollManager(item_height=80, visible_items=8)
        
        # Cache for rendered notification items
        self._notification_cache: Dict[str, ft.Container] = {}
        self._last_cache_update = 0
        
        # Responsive layout state
        layout_manager.register_layout_callback('notification_center', self._on_layout_change)
        
        # UI components
        self.notification_icon = ft.IconButton(
            icon=ft.Icons.NOTIFICATIONS_OUTLINED,
            icon_color=ColorTokens.ON_SURFACE_VARIANT,
            tooltip="Notifications",
            on_click=self._toggle_panel,
            style=ComponentStyles.icon_button('standard')
        )
        
        self.badge = ft.Container(
            content=create_styled_text("0", "label_small", ColorTokens.ON_ERROR),
            bgcolor=ColorTokens.ERROR,
            border_radius=BorderRadius.FULL,
            padding=Spacing.padding_all(Spacing.XS),
            visible=False,
            width=20,
            height=20,
            alignment=ft.alignment.center
        )
        
        self.notification_button = ft.Stack(
            controls=[
                self.notification_icon,
                ft.Container(
                    content=self.badge,
                    alignment=ft.alignment.top_right,
                    margin=ft.margin.only(top=-5, right=-5)
                )
            ],
            width=40,
            height=40
        )
        
        # Category filter tabs
        self.category_tabs = ft.Tabs(
            selected_index=0,
            animation_duration=Animations.NORMAL,
            tabs=[
                ft.Tab(text="All", icon=ft.Icons.ALL_INCLUSIVE),
                ft.Tab(text="Info", icon=ft.Icons.INFO_OUTLINE),
                ft.Tab(text="Success", icon=ft.Icons.CHECK_CIRCLE_OUTLINE),
                ft.Tab(text="Warning", icon=ft.Icons.WARNING_OUTLINED),
                ft.Tab(text="Error", icon=ft.Icons.ERROR_OUTLINE),
            ],
            on_change=self._on_category_change
        )
        
        self.notification_panel = ft.Container(
            content=ft.Column(
                controls=[
                    # Header with title and unread count
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                create_styled_text("Notifications", "title_medium", ColorTokens.ON_SURFACE),
                                ft.Container(
                                    content=create_styled_text("0 unread", "body_small", ColorTokens.ON_SURFACE_VARIANT),
                                    ref=ft.Ref[ft.Container]()
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        padding=Spacing.padding_all(Spacing.MD),
                        border=ft.border.only(bottom=ft.BorderSide(1, ColorTokens.OUTLINE_VARIANT))
                    ),
                    # Category filter tabs
                    ft.Container(
                        content=self.category_tabs,
                        padding=Spacing.padding_symmetric(horizontal=Spacing.SM),
                        border=ft.border.only(bottom=ft.BorderSide(1, ColorTokens.OUTLINE_VARIANT))
                    ),
                    # Notification list
                    ft.Container(
                        content=ft.Column(
                            controls=[],
                            scroll=ft.ScrollMode.AUTO,
                            spacing=0
                        ),
                        height=300,
                        padding=Spacing.padding_all(Spacing.SM)
                    ),
                    # Action buttons
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.ElevatedButton(
                                    "Mark all as read",
                                    icon=ft.Icons.MARK_EMAIL_READ,
                                    style=ft.ButtonStyle(
                                        color=ColorTokens.ON_INFO_CONTAINER,
                                        bgcolor=ColorTokens.INFO_CONTAINER,
                                        shape=ft.RoundedRectangleBorder(radius=BorderRadius.SM),
                                        text_style=Typography.LABEL_MEDIUM
                                    ),
                                    on_click=self._mark_all_as_read
                                ),
                                ft.ElevatedButton(
                                    "Clear read",
                                    icon=ft.Icons.CLEAR_ALL,
                                    style=ft.ButtonStyle(
                                        color=ColorTokens.ON_ERROR_CONTAINER,
                                        bgcolor=ColorTokens.ERROR_CONTAINER,
                                        shape=ft.RoundedRectangleBorder(radius=BorderRadius.SM),
                                        text_style=Typography.LABEL_MEDIUM
                                    ),
                                    on_click=self._clear_read_notifications
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        padding=Spacing.padding_all(Spacing.MD),
                        border=ft.border.only(top=ft.BorderSide(1, ColorTokens.OUTLINE_VARIANT))
                    )
                ],
                spacing=0
            ),
            bgcolor=ColorTokens.SURFACE,
            border_radius=BorderRadius.all(BorderRadius.MD),
            border=ft.border.all(1, ColorTokens.OUTLINE_VARIANT),
            shadow=Shadows.elevation_3(),
            width=380,
            visible=False,
            animate_opacity=Animations.SLOW,
            animate_scale=Animations.normal_ease_in_out()
        )
        
        # Main container setup
        self.content = ft.Stack(
            controls=[
                self.notification_button,
                ft.Container(
                    content=self.notification_panel,
                    alignment=ft.alignment.top_right,
                    margin=ft.margin.only(top=45, right=-150)
                )
            ]
        )
        
        # Current filter state
        self.current_filter = None  # None means "All"
        
        # Store reference to unread count display
        self.unread_count_display = self.notification_panel.content.controls[0].content.controls[1]
        
        # Register as observer for new notifications
        self.notification_service.add_observer(self._on_new_notification)
        
        # Initial update
        self._update_display()
    
    def _toggle_panel(self, e):
        """Toggle the notification panel visibility."""
        self.is_expanded = not self.is_expanded
        self.notification_panel.visible = self.is_expanded
        
        if self.is_expanded:
            self._refresh_notifications()
        
        self.page.update()
    
    @throttled(min_interval=0.2)  # Throttle display updates
    @performance_tracked("notification_display_update")
    def _update_display(self):
        """Update the notification display and badge count with performance optimization."""
        unread_count = self.notification_service.get_unread_count()
        
        # Update badge with enhanced visual indicators
        if unread_count > 0:
            self.badge.visible = True
            self.badge.content.value = str(min(unread_count, 99))  # Cap at 99
            self.notification_icon.icon_color = ft.Colors.BLUE_600
            
            # Add pulsing animation for new notifications
            self.badge.animate_scale = animation_manager.create_bounce_animation()
        else:
            self.badge.visible = False
            self.notification_icon.icon_color = ft.Colors.GREY_600
        
        # Update unread count in panel header
        if hasattr(self, 'unread_count_display'):
            unread_text = f"{unread_count} unread" if unread_count != 1 else "1 unread"
            if unread_count == 0:
                unread_text = "All read"
            self.unread_count_display.content.value = unread_text
            self.unread_count_display.content.color = ft.Colors.GREEN_600 if unread_count == 0 else ft.Colors.ORANGE_600
        
        if self.page:
            self.page.update()
    
    @performance_tracked("notification_refresh")
    def _refresh_notifications(self):
        """Refresh the notification list with virtual scrolling and caching for performance."""
        # Get filtered notifications based on current category
        if self.current_filter:
            notifications = self.notification_service.get_notifications(notification_type=self.current_filter)
        else:
            notifications = self.notification_service.get_notifications()
        
        notification_list = self.notification_panel.content.controls[2].content
        
        # Performance optimization: Use virtual scrolling for large lists
        if len(notifications) > 20:
            self._render_virtual_notifications(notifications, notification_list)
        else:
            self._render_standard_notifications(notifications, notification_list)
        
        if self.page:
            self.page.update()
    
    def _render_virtual_notifications(self, notifications: List[Notification], container: ft.Column):
        """Render notifications using virtual scrolling for performance."""
        container.controls.clear()
        
        # Update virtual scroll manager
        self.virtual_scroll.total_items = len(notifications)
        
        # Calculate visible range (for now, render first 10 items)
        # In a full implementation, this would be based on scroll position
        visible_start, visible_end = 0, min(10, len(notifications))
        
        # Add virtual spacer for items above visible range
        if visible_start > 0:
            spacer_height = visible_start * self.virtual_scroll.item_height
            container.controls.append(
                ft.Container(height=spacer_height, bgcolor=ft.Colors.TRANSPARENT)
            )
        
        # Render visible notifications with caching
        for i in range(visible_start, visible_end):
            notification = notifications[i]
            
            # Use cached item if available and not stale
            cache_key = f"{notification.id}_{notification.is_read}"
            if cache_key in self._notification_cache:
                container.controls.append(self._notification_cache[cache_key])
            else:
                # Create new item and cache it
                item = self._create_notification_item(notification)
                self._notification_cache[cache_key] = item
                container.controls.append(item)
                
                # Limit cache size to prevent memory issues
                if len(self._notification_cache) > 50:
                    # Remove oldest entries
                    oldest_keys = list(self._notification_cache.keys())[:10]
                    for key in oldest_keys:
                        del self._notification_cache[key]
        
        # Add virtual spacer for items below visible range
        remaining_items = len(notifications) - visible_end
        if remaining_items > 0:
            spacer_height = remaining_items * self.virtual_scroll.item_height
            container.controls.append(
                ft.Container(height=spacer_height, bgcolor=ft.Colors.TRANSPARENT)
            )
    
    def _render_standard_notifications(self, notifications: List[Notification], container: ft.Column):
        """Render notifications using standard method for smaller lists."""
        container.controls.clear()
        
        if not notifications:
            # Show empty state with category-specific message
            empty_message = "No notifications"
            if self.current_filter:
                filter_names = {
                    NotificationType.INFO: "info notifications",
                    NotificationType.SUCCESS: "success notifications", 
                    NotificationType.WARNING: "warning notifications",
                    NotificationType.ERROR: "error notifications"
                }
                empty_message = f"No {filter_names.get(self.current_filter, 'notifications')}"
            
            container.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(
                                ft.Icons.NOTIFICATIONS_OFF_OUTLINED,
                                size=48,
                                color=ft.Colors.GREY_400
                            ),
                            ft.Text(
                                empty_message,
                                size=14,
                                color=ft.Colors.GREY_500,
                                text_align=ft.TextAlign.CENTER
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8
                    ),
                    alignment=ft.alignment.center,
                    padding=ft.padding.all(40)
                )
            )
        else:
            # Group notifications by date for better organization
            grouped_notifications = self._group_notifications_by_date(notifications)
            
            for date_group, group_notifications in grouped_notifications.items():
                # Add date header
                if len(grouped_notifications) > 1:  # Only show date headers if multiple days
                    container.controls.append(
                        ft.Container(
                            content=ft.Text(
                                date_group,
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.GREY_600
                            ),
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            margin=ft.margin.only(top=8 if container.controls else 0)
                        )
                    )
                
                # Add notification items for this date
                for notification in group_notifications:
                    notification_item = self._create_notification_item(notification)
                    container.controls.append(notification_item)
    
    def _create_notification_item(self, notification: Notification) -> ft.Container:
        """
        Create an enhanced notification item widget with improved styling and functionality.
        
        Args:
            notification: The notification to display
            
        Returns:
            Container with the notification content
        """
        # Enhanced color scheme and icons based on type using design system
        type_config = {
            NotificationType.INFO: {
                "bg_color": ColorTokens.INFO_CONTAINER,
                "border_color": ColorTokens.INFO,
                "icon": ft.Icons.INFO_OUTLINE,
                "icon_color": ColorTokens.INFO
            },
            NotificationType.SUCCESS: {
                "bg_color": ColorTokens.SUCCESS_CONTAINER,
                "border_color": ColorTokens.SUCCESS,
                "icon": ft.Icons.CHECK_CIRCLE_OUTLINE,
                "icon_color": ColorTokens.SUCCESS
            },
            NotificationType.WARNING: {
                "bg_color": ColorTokens.WARNING_CONTAINER,
                "border_color": ColorTokens.WARNING,
                "icon": ft.Icons.WARNING_OUTLINED,
                "icon_color": ColorTokens.WARNING
            },
            NotificationType.ERROR: {
                "bg_color": ColorTokens.ERROR_CONTAINER,
                "border_color": ColorTokens.ERROR,
                "icon": ft.Icons.ERROR_OUTLINE,
                "icon_color": ColorTokens.ERROR
            }
        }
        
        config = type_config.get(notification.type, {
            "bg_color": ColorTokens.SURFACE_VARIANT,
            "border_color": ColorTokens.OUTLINE,
            "icon": ft.Icons.NOTIFICATIONS_OUTLINED,
            "icon_color": ColorTokens.ON_SURFACE_VARIANT
        })
        
        # Enhanced timestamp formatting
        time_str = self._format_timestamp(notification.timestamp)
        
        # Create action buttons if action_url is provided
        action_buttons = []
        if notification.action_url:
            action_buttons.append(
                ft.TextButton(
                    "View",
                    icon=ft.Icons.OPEN_IN_NEW,
                    style=ft.ButtonStyle(
                        color=config["icon_color"],
                        text_style=Typography.LABEL_SMALL
                    ),
                    on_click=lambda e, url=notification.action_url: self._handle_action_click(url)
                )
            )
        
        # Unread indicator
        unread_indicator = ft.Container(
            width=8,
            height=8,
            bgcolor=config["icon_color"],
            border_radius=4,
            visible=not notification.is_read
        )
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    # Type icon with enhanced styling
                    ft.Container(
                        content=ft.Icon(
                            config["icon"],
                            size=24,
                            color=config["icon_color"]
                        ),
                        padding=Spacing.padding_all(Spacing.SM),
                        bgcolor=config["bg_color"],
                        border_radius=BorderRadius.all(BorderRadius.XL),
                        border=ft.border.all(1, config["border_color"])
                    ),
                    # Content area
                    ft.Container(
                        expand=True,
                        content=ft.Column(
                            controls=[
                                # Title row with unread indicator
                                ft.Row(
                                    controls=[
                                        ft.Text(
                                            notification.title,
                                            size=Typography.LABEL_LARGE.size,
                                            weight=ft.FontWeight.BOLD if not notification.is_read else Typography.LABEL_LARGE.weight,
                                            color=ColorTokens.ON_SURFACE if not notification.is_read else ColorTokens.ON_SURFACE_VARIANT,
                                            expand=True
                                        ),
                                        unread_indicator
                                    ],
                                    spacing=8
                                ),
                                # Message
                                ft.Text(
                                    notification.message,
                                    size=13,
                                    color=ft.Colors.GREY_700,
                                    max_lines=3,
                                    overflow=ft.TextOverflow.ELLIPSIS
                                ),
                                # Footer with timestamp and actions
                                ft.Row(
                                    controls=[
                                        ft.Text(
                                            time_str,
                                            size=11,
                                            color=ft.Colors.GREY_500,
                                            weight=ft.FontWeight.W_400
                                        ),
                                        *action_buttons
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    spacing=8
                                )
                            ],
                            spacing=4,
                            tight=True
                        )
                    ),
                    # Action menu
                    ft.PopupMenuButton(
                        icon=ft.Icons.MORE_VERT,
                        icon_size=16,
                        tooltip="More actions",
                        items=[
                            ft.PopupMenuItem(
                                text="Mark as read" if not notification.is_read else "Mark as unread",
                                icon=ft.Icons.MARK_EMAIL_READ if not notification.is_read else ft.Icons.MARK_EMAIL_UNREAD,
                                on_click=lambda e, nid=notification.id: self._toggle_read_status(nid)
                            ),
                            ft.PopupMenuItem(
                                text="Remove",
                                icon=ft.Icons.DELETE_OUTLINE,
                                on_click=lambda e, nid=notification.id: self._remove_notification(nid)
                            )
                        ]
                    )
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.START
            ),
            bgcolor=ft.Colors.WHITE if not notification.is_read else ft.Colors.GREY_50,
            border_radius=8,
            border=ft.border.all(
                1, 
                config["border_color"] if not notification.is_read else ft.Colors.GREY_200
            ),
            padding=ft.padding.all(16),
            margin=ft.margin.only(bottom=8),
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            on_click=lambda e, nid=notification.id: self._mark_notification_as_read(nid) if not notification.is_read else None
        )
    
    def _mark_notification_as_read(self, notification_id: str):
        """Mark a specific notification as read."""
        self.notification_service.mark_as_read(notification_id)
        self._update_display()
        if self.is_expanded:
            self._refresh_notifications()
    
    def _dismiss_notification(self, notification_id: str):
        """Dismiss (remove) a specific notification."""
        # For now, we'll mark as read. In a full implementation, 
        # we might want to add a remove method to the service
        self.notification_service.mark_as_read(notification_id)
        self._update_display()
        if self.is_expanded:
            self._refresh_notifications()
    
    def _mark_all_as_read(self, e):
        """Mark all notifications as read."""
        self.notification_service.mark_all_as_read()
        self._update_display()
        if self.is_expanded:
            self._refresh_notifications()
    
    def _clear_read_notifications(self, e):
        """Clear only read notifications."""
        self.notification_service.clear_read_notifications()
        self._update_display()
        if self.is_expanded:
            self._refresh_notifications()
    
    def _clear_all_notifications(self, e):
        """Clear all notifications."""
        self.notification_service.clear_all_notifications()
        self._update_display()
        if self.is_expanded:
            self._refresh_notifications()
    
    def _on_new_notification(self, notification: Notification):
        """
        Callback for when a new notification is added.
        
        Args:
            notification: The new notification
        """
        self._update_display()
        
        # If panel is open, refresh the list
        if self.is_expanded:
            self._refresh_notifications()
    
    def add_test_notification(self, notification_type: NotificationType = NotificationType.INFO):
        """
        Add a test notification for development/testing purposes.
        
        Args:
            notification_type: The type of test notification to add
        """
        test_messages = {
            NotificationType.INFO: ("New Update", "A new version is available for download."),
            NotificationType.SUCCESS: ("Task Completed", "Your time tracking session has been saved successfully."),
            NotificationType.WARNING: ("Storage Warning", "You are running low on storage space."),
            NotificationType.ERROR: ("Connection Error", "Failed to sync data with the server.")
        }
        
        title, message = test_messages.get(notification_type, ("Test", "This is a test notification."))
        self.notification_service.add_notification(title, message, notification_type)
    
    def _on_category_change(self, e):
        """Handle category filter change."""
        selected_index = e.control.selected_index
        
        # Map tab index to notification type
        filter_map = {
            0: None,  # All
            1: NotificationType.INFO,
            2: NotificationType.SUCCESS,
            3: NotificationType.WARNING,
            4: NotificationType.ERROR
        }
        
        self.current_filter = filter_map.get(selected_index)
        
        if self.is_expanded:
            self._refresh_notifications()
    
    def _group_notifications_by_date(self, notifications: List[Notification]) -> Dict[str, List[Notification]]:
        """
        Group notifications by date for better organization.
        
        Args:
            notifications: List of notifications to group
            
        Returns:
            Dictionary with date strings as keys and notification lists as values
        """
        grouped = {}
        now = datetime.now()
        
        for notification in notifications:
            # Calculate relative date
            time_diff = now - notification.timestamp
            
            if time_diff.days == 0:
                date_key = "Today"
            elif time_diff.days == 1:
                date_key = "Yesterday"
            elif time_diff.days < 7:
                date_key = notification.timestamp.strftime("%A")  # Day name
            else:
                date_key = notification.timestamp.strftime("%B %d")  # Month Day
            
            if date_key not in grouped:
                grouped[date_key] = []
            grouped[date_key].append(notification)
        
        return grouped
    
    def _format_timestamp(self, timestamp: datetime) -> str:
        """
        Format timestamp with relative time display.
        
        Args:
            timestamp: The timestamp to format
            
        Returns:
            Formatted timestamp string
        """
        now = datetime.now()
        time_diff = now - timestamp
        
        if time_diff.total_seconds() < 60:
            return "Just now"
        elif time_diff.total_seconds() < 3600:
            minutes = int(time_diff.total_seconds() / 60)
            return f"{minutes}m ago"
        elif time_diff.days == 0:
            return timestamp.strftime("%H:%M")
        elif time_diff.days == 1:
            return f"Yesterday {timestamp.strftime('%H:%M')}"
        elif time_diff.days < 7:
            return timestamp.strftime("%a %H:%M")
        else:
            return timestamp.strftime("%b %d %H:%M")
    
    def _handle_action_click(self, action_url: str):
        """
        Handle action button click.
        
        Args:
            action_url: The URL or action to handle
        """
        # For now, just print the action. In a real implementation,
        # this could navigate to a specific page or perform an action
        print(f"Action clicked: {action_url}")
        
        # You could implement URL navigation here:
        # if action_url.startswith("http"):
        #     self.page.launch_url(action_url)
        # else:
        #     # Handle internal navigation
        #     pass
    
    def _toggle_read_status(self, notification_id: str):
        """
        Toggle the read status of a notification.
        
        Args:
            notification_id: The notification ID
        """
        notification = self.notification_service.get_notification_by_id(notification_id)
        if notification:
            if notification.is_read:
                self.notification_service.mark_as_unread(notification_id)
            else:
                self.notification_service.mark_as_read(notification_id)
            
            self._update_display()
            if self.is_expanded:
                self._refresh_notifications()
    
    def _remove_notification(self, notification_id: str):
        """
        Remove a specific notification.
        
        Args:
            notification_id: The notification ID to remove
        """
        # Since the service doesn't have a remove method, we'll mark as read
        # In a full implementation, you'd add a remove method to the service
        self.notification_service.mark_as_read(notification_id)
        self._update_display()
        if self.is_expanded:
            self._refresh_notifications()
    
    def get_notifications_by_category(self, category: NotificationType) -> List[Notification]:
        """
        Get notifications filtered by category.
        
        Args:
            category: The notification type to filter by
            
        Returns:
            List of notifications of the specified type
        """
        return self.notification_service.get_notifications(notification_type=category)
    
    def get_unread_notifications_by_category(self, category: NotificationType) -> List[Notification]:
        """
        Get unread notifications filtered by category.
        
        Args:
            category: The notification type to filter by
            
        Returns:
            List of unread notifications of the specified type
        """
        return self.notification_service.get_notifications(
            unread_only=True, 
            notification_type=category
        )
    
    def _on_layout_change(self, breakpoint: str, width: float) -> None:
        """Handle responsive layout changes."""
        if layout_manager.is_mobile():
            # Mobile layout optimizations
            self.notification_panel.width = min(320, width - 16)
            self.notification_panel.content.controls[2].height = 250  # Smaller height on mobile
        elif layout_manager.is_tablet():
            # Tablet layout optimizations
            self.notification_panel.width = min(360, width - 32)
            self.notification_panel.content.controls[2].height = 280
        else:
            # Desktop layout (default)
            self.notification_panel.width = 380
            self.notification_panel.content.controls[2].height = 300
        
        if self.page:
            self.page.update()
    
    def cleanup(self) -> None:
        """Clean up resources to prevent memory leaks."""
        # Clear notification cache
        self._notification_cache.clear()
        
        # Remove observer from notification service
        if hasattr(self.notification_service, 'remove_observer'):
            self.notification_service.remove_observer(self._on_new_notification)
        
        # Clean up lifecycle manager
        lifecycle_manager.cleanup_component(self)    
    
    def _create_fallback_component(self, error_message: str) -> ft.Control:
        """Create a fallback component when notification center fails."""
        return ft.Container(
            content=ft.Column([
                ft.Icon(
                    ft.Icons.NOTIFICATIONS_OFF_OUTLINED,
                    size=32,
                    color=ft.Colors.GREY_400
                ),
                ft.Text(
                    "Notifications Unavailable",
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.GREY_600,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    error_message,
                    size=12,
                    color=ft.Colors.GREY_500,
                    text_align=ft.TextAlign.CENTER,
                    max_lines=2
                ),
                ft.ElevatedButton(
                    "Retry",
                    icon=ft.Icons.REFRESH,
                    on_click=self._retry_notification_center,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE_100,
                        color=ft.Colors.BLUE_800
                    )
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8
            ),
            padding=ft.padding.all(16),
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.GREY_50,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_200),
            width=300,
            height=200
        )
    
    def _retry_notification_center(self, e) -> None:
        """Retry initializing the notification center."""
        def retry_operation():
            # Reinitialize the notification center
            self.__init__(self.page, self.notification_service)
            if self.page:
                self.page.update()
        
        safe_execute(
            retry_operation,
            "NotificationCenter",
            "retry_initialization",
            self.page
        )
    
    def _safe_toggle_panel(self, e) -> None:
        """Safely toggle the notification panel."""
        def toggle_operation():
            self._toggle_panel(e)
        
        safe_execute(
            toggle_operation,
            "NotificationCenter",
            "toggle_panel",
            self.page,
            fallback_result=None
        )
    
    def _safe_refresh_notifications(self) -> None:
        """Safely refresh notifications with error handling."""
        def refresh_operation():
            self._refresh_notifications()
        
        result = safe_execute(
            refresh_operation,
            "NotificationCenter",
            "refresh_notifications",
            self.page,
            fallback_result=False
        )
        
        if result is False:
            # Show fallback content
            self._show_error_state("Failed to load notifications")
    
    def _show_error_state(self, error_message: str) -> None:
        """Show error state in the notification panel."""
        try:
            notification_list = self.notification_panel.content.controls[2].content
            notification_list.controls.clear()
            
            error_content = ft.Container(
                content=ft.Column([
                    ft.Icon(
                        ft.Icons.ERROR_OUTLINE,
                        size=32,
                        color=ft.Colors.RED_400
                    ),
                    ft.Text(
                        "Error Loading Notifications",
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.RED_600,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        error_message,
                        size=12,
                        color=ft.Colors.RED_500,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.ElevatedButton(
                        "Retry",
                        icon=ft.Icons.REFRESH,
                        on_click=lambda e: self._safe_refresh_notifications(),
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.RED_100,
                            color=ft.Colors.RED_800
                        )
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8
                ),
                alignment=ft.alignment.center,
                padding=ft.padding.all(20)
            )
            
            notification_list.controls.append(error_content)
            
            if self.page:
                self.page.update()
                
        except Exception as e:
            logging.error(f"Failed to show error state: {e}")
    
    def _safe_mark_notification_as_read(self, notification_id: str) -> None:
        """Safely mark a notification as read."""
        def mark_read_operation():
            self._mark_notification_as_read(notification_id)
        
        safe_execute(
            mark_read_operation,
            "NotificationCenter",
            "mark_as_read",
            self.page,
            user_data={"notification_id": notification_id}
        )
    
    def _safe_mark_all_as_read(self, e) -> None:
        """Safely mark all notifications as read."""
        def mark_all_operation():
            self._mark_all_as_read(e)
        
        safe_execute(
            mark_all_operation,
            "NotificationCenter",
            "mark_all_as_read",
            self.page
        )
    
    def _safe_clear_read_notifications(self, e) -> None:
        """Safely clear read notifications."""
        def clear_operation():
            self._clear_read_notifications(e)
        
        safe_execute(
            clear_operation,
            "NotificationCenter",
            "clear_read_notifications",
            self.page
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get the health status of the notification center."""
        try:
            return {
                "component": "NotificationCenter",
                "status": "healthy",
                "notifications_count": len(self.notification_service.get_notifications()),
                "unread_count": self.notification_service.get_unread_count(),
                "is_expanded": self.is_expanded,
                "last_update": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "component": "NotificationCenter",
                "status": "error",
                "error": str(e),
                "last_update": datetime.now().isoformat()
            }