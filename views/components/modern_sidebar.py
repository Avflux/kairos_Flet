import flet as ft
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from views.components.performance_utils import (
    performance_tracked, throttled, debounced, lifecycle_manager,
    layout_manager, animation_manager
)


@dataclass
class NavItem:
    """Represents a navigation item in the sidebar"""
    icon: str
    text: str
    route: Optional[str] = None
    is_selected: bool = False
    is_button: bool = False
    is_link: bool = False
    on_click: Optional[Callable] = None
    badge_count: Optional[int] = None


class SidebarSection(ft.Container):
    """A collapsible section in the sidebar containing navigation items"""
    
    def __init__(
        self,
        title: str,
        items: List[NavItem],
        expanded: bool = True,
        on_toggle: Optional[Callable] = None
    ):
        super().__init__()
        self.title = title
        self.items = items
        self.expanded = expanded
        self.on_toggle = on_toggle
        self._sidebar_expanded = True
        
        # Create header
        self.header = self._create_header()
        
        # Create items container
        self.items_container = self._create_items_container()
        
        # Set up the container
        self.content = ft.Column([
            self.header,
            self.items_container
        ], spacing=8, tight=True)
        
        self.padding = ft.padding.symmetric(vertical=8)
    
    def _create_header(self) -> ft.Container:
        """Create the section header with toggle functionality"""
        self.title_text = ft.Text(
            self.title,
            weight=ft.FontWeight.W_600,
            size=14,
            color='on_surface_variant',
            visible=self._sidebar_expanded
        )
        
        self.toggle_icon = ft.IconButton(
            icon=ft.Icons.KEYBOARD_ARROW_DOWN if self.expanded else ft.Icons.KEYBOARD_ARROW_RIGHT,
            icon_size=20,
            on_click=self._toggle_section,
            tooltip=f"Toggle {self.title} section"
        )
        
        return ft.Container(
            content=ft.Row([
                self.title_text,
                self.toggle_icon
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=12, vertical=4)
        )
    
    def _create_items_container(self) -> ft.Container:
        """Create the container for navigation items"""
        nav_controls = []
        
        for item in self.items:
            nav_control = self._create_nav_item(item)
            nav_controls.append(nav_control)
        
        return ft.Container(
            content=ft.Column(nav_controls, spacing=2, tight=True),
            visible=self.expanded,
            animate_opacity=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT)
        )
    
    def _create_nav_item(self, item: NavItem) -> ft.Container:
        """Create a navigation item with modern styling"""
        # Create text with visibility control
        item_text = ft.Text(
            item.text,
            size=14,
            weight=ft.FontWeight.W_500 if item.is_selected else ft.FontWeight.W_400,
            color='on_primary' if item.is_selected else 'on_surface',
            visible=self._sidebar_expanded
        )
        
        # Create icon
        item_icon = ft.Icon(
            item.icon,
            size=20,
            color='on_primary' if item.is_selected else 'on_surface_variant'
        )
        
        # Create row content
        row_controls = [item_icon, item_text]
        
        # Add badge if present
        if item.badge_count and item.badge_count > 0:
            badge = ft.Container(
                content=ft.Text(
                    str(item.badge_count),
                    size=10,
                    weight=ft.FontWeight.BOLD,
                    color='on_error'
                ),
                bgcolor='error',
                border_radius=ft.border_radius.all(10),
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                margin=ft.margin.only(left=8)
            )
            row_controls.append(badge)
        
        # Add external link icon if needed
        if item.is_link:
            row_controls.append(ft.Icon(
                ft.Icons.OPEN_IN_NEW,
                size=16,
                color='on_surface_variant'
            ))
        
        # Create the main row
        item_row = ft.Row(
            row_controls,
            spacing=12,
            alignment=ft.MainAxisAlignment.START
        )
        
        # Determine background color and styling
        if item.is_selected:
            bgcolor = 'primary'
            hover_color = 'surface_variant'
        elif item.is_button:
            bgcolor = 'surface_variant'
            hover_color = 'surface_variant'
        else:
            bgcolor = None
            hover_color = 'surface_variant'
        
        return ft.Container(
            content=item_row,
            bgcolor=bgcolor,
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            border_radius=ft.border_radius.all(12),
            ink=True,
            on_click=item.on_click,
            animate=ft.Animation(150, ft.AnimationCurve.EASE_IN_OUT),
            on_hover=lambda e: self._handle_hover(e, hover_color)
        )
    
    def _handle_hover(self, e, hover_color):
        """Handle hover effects for navigation items"""
        if e.data == "true":  # Mouse enter
            e.control.bgcolor = hover_color
        else:  # Mouse leave
            # Reset to original color based on item state
            # This is a simplified approach - in a real implementation,
            # you'd want to track the original state
            e.control.bgcolor = None
        e.control.update()
    
    def _toggle_section(self, e):
        """Toggle the section expanded state"""
        self.expanded = not self.expanded
        self.items_container.visible = self.expanded
        self.toggle_icon.icon = (
            ft.Icons.KEYBOARD_ARROW_DOWN if self.expanded 
            else ft.Icons.KEYBOARD_ARROW_RIGHT
        )
        
        if self.on_toggle:
            self.on_toggle(self.title, self.expanded)
        
        # Only update if we have a page (not in tests)
        if hasattr(self, 'page') and self.page:
            self.update()
    
    def update_sidebar_expansion(self, expanded: bool):
        """Update visibility of text elements based on sidebar expansion"""
        self._sidebar_expanded = expanded
        self.title_text.visible = expanded
        
        # Update all item texts
        for control in self.items_container.content.controls:
            if isinstance(control, ft.Container) and control.content:
                row = control.content
                if isinstance(row, ft.Row) and len(row.controls) > 1:
                    text_control = row.controls[1]
                    if isinstance(text_control, ft.Text):
                        text_control.visible = expanded
        
        # Only update if we have a page (not in tests)
        if hasattr(self, 'page') and self.page:
            self.update()
    
    def set_selected_item(self, item_text: str):
        """Set the selected navigation item"""
        for i, item in enumerate(self.items):
            item.is_selected = (item.text == item_text)
        
        # Recreate items container to reflect selection changes
        self.items_container = self._create_items_container()
        self.content.controls[1] = self.items_container
        
        # Only update if we have a page (not in tests)
        if hasattr(self, 'page') and self.page:
            self.update()


class ModernSidebar(ft.Container):
    """Modern sidebar component with improved navigation and styling"""
    
    def __init__(self, page: ft.Page, on_navigation: Optional[Callable] = None):
        super().__init__()
        self.page = page
        self.on_navigation = on_navigation
        self.expanded = True
        self.sections: Dict[str, SidebarSection] = {}
        
        # Performance optimization: Register with lifecycle manager
        lifecycle_manager.register_component(self)
        
        # Responsive layout state
        self._current_breakpoint = 'lg'
        layout_manager.register_layout_callback('modern_sidebar', self._on_layout_change)
        
        # Initialize sections
        self._create_sections()
        
        # Create sidebar header
        self.header = self._create_header()
        
        # Create main content
        self.main_content = self._create_main_content()
        
        # Create footer
        self.footer = self._create_footer()
        
        # Set up container properties with responsive design
        self._update_responsive_properties()
        self.bgcolor = 'rgba(255, 255, 255, 0.03)'
        self.border_radius = ft.border_radius.all(16)
        self.animate = animation_manager.create_slide_animation()
        
        # Set content
        self.content = ft.Column([
            self.header,
            self.main_content,
            self.footer
        ], spacing=16, expand=True)
    
    def _create_sections(self):
        """Create the three main sections with their navigation items"""
        
        # Time Management Section
        time_management_items = [
            NavItem(
                icon=ft.Icons.TIMER_OUTLINED,
                text="Time Tracker",
                route="/time-tracker",
                on_click=lambda e: self._handle_navigation("time-tracker")
            ),
            NavItem(
                icon=ft.Icons.HISTORY,
                text="Time History",
                route="/time-history",
                on_click=lambda e: self._handle_navigation("time-history")
            ),
            NavItem(
                icon=ft.Icons.ANALYTICS_OUTLINED,
                text="Time Analytics",
                route="/time-analytics",
                on_click=lambda e: self._handle_navigation("time-analytics")
            ),
            NavItem(
                icon=ft.Icons.CATEGORY_OUTLINED,
                text="Activity Categories",
                route="/activity-categories",
                on_click=lambda e: self._handle_navigation("activity-categories")
            )
        ]
        
        # Project Workflows Section
        project_workflow_items = [
            NavItem(
                icon=ft.Icons.ACCOUNT_TREE_OUTLINED,
                text="Workflow Overview",
                route="/workflow-overview",
                is_selected=True,  # Default selected
                on_click=lambda e: self._handle_navigation("workflow-overview")
            ),
            NavItem(
                icon=ft.Icons.TASK_OUTLINED,
                text="Active Projects",
                route="/active-projects",
                badge_count=3,  # Example badge
                on_click=lambda e: self._handle_navigation("active-projects")
            ),
            NavItem(
                icon=ft.Icons.APPROVAL_OUTLINED,
                text="Approval Queue",
                route="/approval-queue",
                badge_count=7,
                on_click=lambda e: self._handle_navigation("approval-queue")
            ),
            NavItem(
                icon=ft.Icons.ARCHIVE_OUTLINED,
                text="Completed Projects",
                route="/completed-projects",
                on_click=lambda e: self._handle_navigation("completed-projects")
            )
        ]
        
        # Educational Videos Section
        educational_videos_items = [
            NavItem(
                icon=ft.Icons.PLAY_CIRCLE_OUTLINE,
                text="Video Library",
                route="/video-library",
                on_click=lambda e: self._handle_navigation("video-library")
            ),
            NavItem(
                icon=ft.Icons.BOOKMARK_OUTLINE,
                text="Saved Videos",
                route="/saved-videos",
                on_click=lambda e: self._handle_navigation("saved-videos")
            ),
            NavItem(
                icon=ft.Icons.TRENDING_UP,
                text="Trending Topics",
                route="/trending-topics",
                on_click=lambda e: self._handle_navigation("trending-topics")
            ),
            NavItem(
                icon=ft.Icons.OPEN_IN_NEW,
                text="External Resources",
                route="/external-resources",
                is_link=True,
                on_click=lambda e: self._handle_navigation("external-resources")
            )
        ]
        
        # Create sections
        self.sections["time_management"] = SidebarSection(
            "Time Management",
            time_management_items,
            expanded=True,
            on_toggle=self._handle_section_toggle
        )
        
        self.sections["project_workflows"] = SidebarSection(
            "Project Workflows",
            project_workflow_items,
            expanded=True,
            on_toggle=self._handle_section_toggle
        )
        
        self.sections["educational_videos"] = SidebarSection(
            "Educational Videos",
            educational_videos_items,
            expanded=False,
            on_toggle=self._handle_section_toggle
        )
    
    def _create_header(self) -> ft.Container:
        """Create the sidebar header with title and toggle button"""
        self.title_text = ft.Text(
            "Kairos",
            size=20,
            weight=ft.FontWeight.BOLD,
            color='on_surface',
            visible=self.expanded
        )
        
        self.toggle_button = ft.IconButton(
            icon=ft.Icons.MENU,
            icon_size=24,
            on_click=self._toggle_sidebar,
            tooltip="Toggle sidebar"
        )
        
        return ft.Container(
            content=ft.Row([
                self.title_text,
                self.toggle_button
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=4, vertical=8)
        )
    
    def _create_main_content(self) -> ft.Container:
        """Create the main content area with sections"""
        section_controls = list(self.sections.values())
        
        return ft.Container(
            content=ft.Column(
                section_controls,
                spacing=12,
                tight=True,
                scroll=ft.ScrollMode.AUTO
            ),
            expand=True
        )
    
    def _create_footer(self) -> ft.Container:
        """Create the sidebar footer with settings and user info"""
        footer_items = [
            NavItem(
                icon=ft.Icons.KEY_OUTLINED,
                text="Get API Key",
                is_button=True,
                on_click=lambda e: self._handle_navigation("api-key")
            ),
            NavItem(
                icon=ft.Icons.SETTINGS_OUTLINED,
                text="Settings",
                on_click=lambda e: self._handle_navigation("settings")
            )
        ]
        
        footer_controls = []
        for item in footer_items:
            nav_control = self._create_footer_nav_item(item)
            footer_controls.append(nav_control)
        
        # Add user account info
        self.user_text = ft.Text(
            "user@example.com",
            size=12,
            color='on_surface_variant',
            visible=self.expanded
        )
        
        user_row = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=20),
                self.user_text
            ], spacing=12),
            padding=ft.padding.symmetric(horizontal=12, vertical=8)
        )
        
        footer_controls.append(user_row)
        
        # Add disclaimer text
        self.disclaimer_text = ft.Text(
            "AI models may make mistakes. Verify important information.",
            size=10,
            color='on_surface_variant',
            visible=self.expanded
        )
        
        disclaimer_container = ft.Container(
            content=self.disclaimer_text,
            padding=ft.padding.symmetric(horizontal=12, vertical=4)
        )
        
        footer_controls.append(disclaimer_container)
        
        return ft.Container(
            content=ft.Column(footer_controls, spacing=8, tight=True),
            padding=ft.padding.symmetric(vertical=8)
        )
    
    def _create_footer_nav_item(self, item: NavItem) -> ft.Container:
        """Create a footer navigation item"""
        item_text = ft.Text(
            item.text,
            size=14,
            weight=ft.FontWeight.W_400,
            color='on_surface',
            visible=self.expanded
        )
        
        item_icon = ft.Icon(
            item.icon,
            size=20,
            color='on_surface_variant'
        )
        
        item_row = ft.Row([item_icon, item_text], spacing=12)
        
        bgcolor = 'surface_variant' if item.is_button else None
        hover_color = 'surface_variant'
        
        return ft.Container(
            content=item_row,
            bgcolor=bgcolor,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border_radius=ft.border_radius.all(12),
            ink=True,
            on_click=item.on_click,
            animate=ft.Animation(150, ft.AnimationCurve.EASE_IN_OUT),
            on_hover=lambda e: self._handle_footer_hover(e, hover_color)
        )
    
    def _handle_footer_hover(self, e, hover_color):
        """Handle hover effects for footer items"""
        if e.data == "true":
            e.control.bgcolor = hover_color
        else:
            e.control.bgcolor = None
        e.control.update()
    
    @debounced(delay=0.1)  # Debounce sidebar toggle
    @performance_tracked("sidebar_toggle")
    def _toggle_sidebar(self, e):
        """Toggle sidebar expanded/collapsed state with performance optimization"""
        self.expanded = not self.expanded
        self._update_responsive_properties()
        
        # Update text visibility
        self.title_text.visible = self.expanded
        self.user_text.visible = self.expanded
        self.disclaimer_text.visible = self.expanded
        
        # Update sections
        for section in self.sections.values():
            section.update_sidebar_expansion(self.expanded)
        
        # Update footer items
        for control in self.footer.content.controls:
            if isinstance(control, ft.Container) and control.content:
                if isinstance(control.content, ft.Row) and len(control.content.controls) > 1:
                    text_control = control.content.controls[1]
                    if isinstance(text_control, ft.Text):
                        text_control.visible = self.expanded
        
        # Only update if we have a page (not in tests)
        if hasattr(self, 'page') and self.page:
            self.update()
    
    def _update_responsive_properties(self):
        """Update sidebar properties based on screen size and expansion state."""
        if layout_manager.is_mobile():
            # Mobile: Full width when expanded, hidden when collapsed
            if self.expanded:
                self.width = min(280, layout_manager.layout_manager.current_breakpoint * 0.8)
                self.padding = ft.padding.all(12)
            else:
                self.width = 0  # Hidden on mobile when collapsed
                self.padding = ft.padding.all(0)
        elif layout_manager.is_tablet():
            # Tablet: Responsive width
            self.width = 240 if self.expanded else 60
            self.padding = ft.padding.all(14)
        else:
            # Desktop: Standard width
            self.width = 280 if self.expanded else 80
            self.padding = ft.padding.all(16)
    
    def _on_layout_change(self, breakpoint: str, width: float) -> None:
        """Handle responsive layout changes."""
        if self._current_breakpoint != breakpoint:
            self._current_breakpoint = breakpoint
            self._update_responsive_properties()
            
            # Auto-collapse on mobile for better UX
            if layout_manager.is_mobile() and self.expanded:
                self.expanded = False
                self._update_responsive_properties()
            
            if self.page:
                self.update()
    
    def cleanup(self) -> None:
        """Clean up resources to prevent memory leaks."""
        # Clean up sections
        for section in self.sections.values():
            if hasattr(section, 'cleanup'):
                section.cleanup()
        
        # Clean up lifecycle manager
        lifecycle_manager.cleanup_component(self)
    
    def _handle_navigation(self, route: str):
        """Handle navigation item clicks"""
        if self.on_navigation:
            self.on_navigation(route)
        
        # Update selected state
        self._update_selected_item(route)
    
    def _handle_section_toggle(self, section_name: str, expanded: bool):
        """Handle section toggle events"""
        # This can be used for analytics or state persistence
        pass
    
    def _update_selected_item(self, route: str):
        """Update the selected navigation item across all sections"""
        for section in self.sections.values():
            for item in section.items:
                item.is_selected = (item.route == f"/{route}")
            
            # Recreate the section to reflect changes
            section.items_container = section._create_items_container()
            section.content.controls[1] = section.items_container
            
            # Only update if we have a page (not in tests)
            if hasattr(section, 'page') and section.page:
                section.update()
    
    def get_selected_route(self) -> Optional[str]:
        """Get the currently selected route"""
        for section in self.sections.values():
            for item in section.items:
                if item.is_selected:
                    return item.route
        return None
    
    def set_selected_route(self, route: str):
        """Set the selected route programmatically"""
        route_without_slash = route.lstrip('/')
        self._update_selected_item(route_without_slash)