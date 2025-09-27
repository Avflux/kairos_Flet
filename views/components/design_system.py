"""
Modern Design System for Kairos Application

This module provides a comprehensive design system with consistent color palette,
typography, spacing, and animation definitions following Material Design 3 principles.
"""

import flet as ft
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ColorTokens:
    """Semantic color tokens for consistent theming across the application."""
    
    # Primary colors
    PRIMARY = ft.Colors.BLUE_600
    PRIMARY_CONTAINER = ft.Colors.BLUE_50
    ON_PRIMARY = ft.Colors.WHITE
    ON_PRIMARY_CONTAINER = ft.Colors.BLUE_900
    
    # Secondary colors
    SECONDARY = ft.Colors.INDIGO_600
    SECONDARY_CONTAINER = ft.Colors.INDIGO_50
    ON_SECONDARY = ft.Colors.WHITE
    ON_SECONDARY_CONTAINER = ft.Colors.INDIGO_900
    
    # Surface colors
    SURFACE = ft.Colors.WHITE
    SURFACE_VARIANT = ft.Colors.GREY_50
    SURFACE_CONTAINER = ft.Colors.GREY_100
    SURFACE_CONTAINER_HIGH = ft.Colors.GREY_200
    ON_SURFACE = ft.Colors.GREY_900
    ON_SURFACE_VARIANT = ft.Colors.GREY_600
    
    # Outline colors
    OUTLINE = ft.Colors.GREY_300
    OUTLINE_VARIANT = ft.Colors.GREY_200
    
    # State colors
    SUCCESS = ft.Colors.GREEN_600
    SUCCESS_CONTAINER = ft.Colors.GREEN_50
    ON_SUCCESS = ft.Colors.WHITE
    ON_SUCCESS_CONTAINER = ft.Colors.GREEN_900
    
    WARNING = ft.Colors.ORANGE_600
    WARNING_CONTAINER = ft.Colors.ORANGE_50
    ON_WARNING = ft.Colors.WHITE
    ON_WARNING_CONTAINER = ft.Colors.ORANGE_900
    
    ERROR = ft.Colors.RED_600
    ERROR_CONTAINER = ft.Colors.RED_50
    ON_ERROR = ft.Colors.WHITE
    ON_ERROR_CONTAINER = ft.Colors.RED_900
    
    INFO = ft.Colors.BLUE_600
    INFO_CONTAINER = ft.Colors.BLUE_50
    ON_INFO = ft.Colors.WHITE
    ON_INFO_CONTAINER = ft.Colors.BLUE_900
    
    # Background colors
    BACKGROUND = ft.Colors.WHITE
    ON_BACKGROUND = ft.Colors.GREY_900
    
    # Shadow colors
    SHADOW = ft.Colors.with_opacity(0.1, ft.Colors.BLACK)
    SHADOW_ELEVATED = ft.Colors.with_opacity(0.15, ft.Colors.BLACK)


class Typography:
    """Typography scale with consistent font weights and sizes."""
    
    # Display styles
    DISPLAY_LARGE = ft.TextStyle(size=57, weight=ft.FontWeight.W_400)
    DISPLAY_MEDIUM = ft.TextStyle(size=45, weight=ft.FontWeight.W_400)
    DISPLAY_SMALL = ft.TextStyle(size=36, weight=ft.FontWeight.W_400)
    
    # Headline styles
    HEADLINE_LARGE = ft.TextStyle(size=32, weight=ft.FontWeight.W_400)
    HEADLINE_MEDIUM = ft.TextStyle(size=28, weight=ft.FontWeight.W_400)
    HEADLINE_SMALL = ft.TextStyle(size=24, weight=ft.FontWeight.W_400)
    
    # Title styles
    TITLE_LARGE = ft.TextStyle(size=22, weight=ft.FontWeight.W_500)
    TITLE_MEDIUM = ft.TextStyle(size=16, weight=ft.FontWeight.W_600)
    TITLE_SMALL = ft.TextStyle(size=14, weight=ft.FontWeight.W_600)
    
    # Label styles
    LABEL_LARGE = ft.TextStyle(size=14, weight=ft.FontWeight.W_500)
    LABEL_MEDIUM = ft.TextStyle(size=12, weight=ft.FontWeight.W_500)
    LABEL_SMALL = ft.TextStyle(size=11, weight=ft.FontWeight.W_500)
    
    # Body styles
    BODY_LARGE = ft.TextStyle(size=16, weight=ft.FontWeight.W_400)
    BODY_MEDIUM = ft.TextStyle(size=14, weight=ft.FontWeight.W_400)
    BODY_SMALL = ft.TextStyle(size=12, weight=ft.FontWeight.W_400)


class Spacing:
    """Consistent spacing system using 8px grid principles."""
    
    # Base unit (8px)
    BASE = 8
    
    # Spacing scale
    XS = BASE // 2      # 4px
    SM = BASE           # 8px
    MD = BASE * 2       # 16px
    LG = BASE * 3       # 24px
    XL = BASE * 4       # 32px
    XXL = BASE * 6      # 48px
    XXXL = BASE * 8     # 64px
    
    # Padding shortcuts
    @staticmethod
    def padding_all(size: int) -> ft.Padding:
        """Create padding for all sides."""
        return ft.padding.all(size)
    
    @staticmethod
    def padding_symmetric(horizontal: int = 0, vertical: int = 0) -> ft.Padding:
        """Create symmetric padding."""
        return ft.padding.symmetric(horizontal=horizontal, vertical=vertical)
    
    @staticmethod
    def padding_only(left: int = 0, top: int = 0, right: int = 0, bottom: int = 0) -> ft.Padding:
        """Create padding for specific sides."""
        return ft.padding.only(left=left, top=top, right=right, bottom=bottom)
    
    # Margin shortcuts
    @staticmethod
    def margin_all(size: int) -> ft.Margin:
        """Create margin for all sides."""
        return ft.margin.all(size)
    
    @staticmethod
    def margin_symmetric(horizontal: int = 0, vertical: int = 0) -> ft.Margin:
        """Create symmetric margin."""
        return ft.margin.symmetric(horizontal=horizontal, vertical=vertical)
    
    @staticmethod
    def margin_only(left: int = 0, top: int = 0, right: int = 0, bottom: int = 0) -> ft.Margin:
        """Create margin for specific sides."""
        return ft.margin.only(left=left, top=top, right=right, bottom=bottom)


class BorderRadius:
    """Consistent border radius values for modern UI components."""
    
    NONE = 0
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 20
    XXL = 24
    FULL = 999  # For circular elements
    
    @staticmethod
    def all(radius: int) -> ft.BorderRadius:
        """Create border radius for all corners."""
        return ft.border_radius.all(radius)
    
    @staticmethod
    def only(
        top_left: int = 0,
        top_right: int = 0,
        bottom_left: int = 0,
        bottom_right: int = 0
    ) -> ft.BorderRadius:
        """Create border radius for specific corners."""
        return ft.BorderRadius(
            top_left=top_left,
            top_right=top_right,
            bottom_left=bottom_left,
            bottom_right=bottom_right
        )


class Shadows:
    """Consistent shadow definitions for depth and elevation."""
    
    @staticmethod
    def elevation_1() -> ft.BoxShadow:
        """Low elevation shadow."""
        return ft.BoxShadow(
            spread_radius=0,
            blur_radius=2,
            color=ColorTokens.SHADOW,
            offset=ft.Offset(0, 1)
        )
    
    @staticmethod
    def elevation_2() -> ft.BoxShadow:
        """Medium elevation shadow."""
        return ft.BoxShadow(
            spread_radius=0,
            blur_radius=4,
            color=ColorTokens.SHADOW,
            offset=ft.Offset(0, 2)
        )
    
    @staticmethod
    def elevation_3() -> ft.BoxShadow:
        """High elevation shadow."""
        return ft.BoxShadow(
            spread_radius=0,
            blur_radius=8,
            color=ColorTokens.SHADOW_ELEVATED,
            offset=ft.Offset(0, 4)
        )
    
    @staticmethod
    def elevation_4() -> ft.BoxShadow:
        """Very high elevation shadow."""
        return ft.BoxShadow(
            spread_radius=1,
            blur_radius=12,
            color=ColorTokens.SHADOW_ELEVATED,
            offset=ft.Offset(0, 6)
        )


class Animations:
    """Consistent animation definitions for smooth user experience."""
    
    # Duration constants (in milliseconds)
    FAST = 150
    NORMAL = 200
    SLOW = 300
    SLOWER = 500
    
    # Easing curves
    EASE_IN = ft.AnimationCurve.EASE_IN
    EASE_OUT = ft.AnimationCurve.EASE_OUT
    EASE_IN_OUT = ft.AnimationCurve.EASE_IN_OUT
    EASE_OUT_BACK = ft.AnimationCurve.EASE_OUT_BACK
    
    @staticmethod
    def fast_ease_out() -> ft.Animation:
        """Fast animation with ease out curve."""
        return ft.Animation(Animations.FAST, Animations.EASE_OUT)
    
    @staticmethod
    def normal_ease_in_out() -> ft.Animation:
        """Normal animation with ease in out curve."""
        return ft.Animation(Animations.NORMAL, Animations.EASE_IN_OUT)
    
    @staticmethod
    def slow_ease_out() -> ft.Animation:
        """Slow animation with ease out curve."""
        return ft.Animation(Animations.SLOW, Animations.EASE_OUT)
    
    @staticmethod
    def bounce() -> ft.Animation:
        """Bounce animation for interactive elements."""
        return ft.Animation(Animations.NORMAL, Animations.EASE_OUT_BACK)


class ComponentStyles:
    """Pre-defined styles for common UI components."""
    
    @staticmethod
    def card_container(
        elevated: bool = False,
        interactive: bool = False
    ) -> Dict[str, Any]:
        """Style for card containers."""
        shadow = Shadows.elevation_2() if elevated else Shadows.elevation_1()
        
        style = {
            'bgcolor': ColorTokens.SURFACE,
            'border_radius': BorderRadius.all(BorderRadius.MD),
            'border': ft.border.all(1, ColorTokens.OUTLINE_VARIANT),
            'shadow': shadow,
            'padding': Spacing.padding_all(Spacing.MD)
        }
        
        if interactive:
            style['animate'] = Animations.fast_ease_out()
        
        return style
    
    @staticmethod
    def primary_button() -> ft.ButtonStyle:
        """Style for primary buttons."""
        return ft.ButtonStyle(
            color=ColorTokens.ON_PRIMARY,
            bgcolor=ColorTokens.PRIMARY,
            elevation=2,
            shape=ft.RoundedRectangleBorder(radius=BorderRadius.SM),
            padding=Spacing.padding_symmetric(horizontal=Spacing.MD, vertical=Spacing.SM),
            text_style=Typography.LABEL_LARGE
        )
    
    @staticmethod
    def secondary_button() -> ft.ButtonStyle:
        """Style for secondary buttons."""
        return ft.ButtonStyle(
            color=ColorTokens.ON_SECONDARY,
            bgcolor=ColorTokens.SECONDARY,
            elevation=2,
            shape=ft.RoundedRectangleBorder(radius=BorderRadius.SM),
            padding=Spacing.padding_symmetric(horizontal=Spacing.MD, vertical=Spacing.SM),
            text_style=Typography.LABEL_LARGE
        )
    
    @staticmethod
    def outlined_button() -> ft.ButtonStyle:
        """Style for outlined buttons."""
        return ft.ButtonStyle(
            color=ColorTokens.PRIMARY,
            bgcolor=ColorTokens.SURFACE,
            elevation=0,
            shape=ft.RoundedRectangleBorder(radius=BorderRadius.SM),
            side=ft.BorderSide(1, ColorTokens.OUTLINE),
            padding=Spacing.padding_symmetric(horizontal=Spacing.MD, vertical=Spacing.SM),
            text_style=Typography.LABEL_LARGE
        )
    
    @staticmethod
    def text_button() -> ft.ButtonStyle:
        """Style for text buttons."""
        return ft.ButtonStyle(
            color=ColorTokens.PRIMARY,
            bgcolor=ft.Colors.TRANSPARENT,
            elevation=0,
            shape=ft.RoundedRectangleBorder(radius=BorderRadius.SM),
            padding=Spacing.padding_symmetric(horizontal=Spacing.MD, vertical=Spacing.SM),
            text_style=Typography.LABEL_LARGE
        )
    
    @staticmethod
    def icon_button(variant: str = 'standard') -> ft.ButtonStyle:
        """Style for icon buttons."""
        if variant == 'filled':
            return ft.ButtonStyle(
                color=ColorTokens.ON_PRIMARY,
                bgcolor=ColorTokens.PRIMARY,
                shape=ft.CircleBorder(),
                padding=Spacing.padding_all(Spacing.SM)
            )
        elif variant == 'tonal':
            return ft.ButtonStyle(
                color=ColorTokens.ON_PRIMARY_CONTAINER,
                bgcolor=ColorTokens.PRIMARY_CONTAINER,
                shape=ft.CircleBorder(),
                padding=Spacing.padding_all(Spacing.SM)
            )
        else:  # standard
            return ft.ButtonStyle(
                color=ColorTokens.ON_SURFACE_VARIANT,
                bgcolor=ft.Colors.TRANSPARENT,
                shape=ft.CircleBorder(),
                padding=Spacing.padding_all(Spacing.SM)
            )
    
    @staticmethod
    def input_field() -> Dict[str, Any]:
        """Style for input fields."""
        return {
            'border_radius': BorderRadius.SM,
            'filled': True,
            'bgcolor': ColorTokens.SURFACE_VARIANT,
            'border_color': ColorTokens.OUTLINE,
            'focused_border_color': ColorTokens.PRIMARY,
            'text_style': Typography.BODY_MEDIUM
        }
    
    @staticmethod
    def dropdown() -> Dict[str, Any]:
        """Style for dropdown components."""
        return {
            'border_radius': BorderRadius.SM,
            'filled': True,
            'bgcolor': ColorTokens.SURFACE_VARIANT,
            'border_color': ColorTokens.OUTLINE,
            'focused_border_color': ColorTokens.PRIMARY,
            'text_style': Typography.BODY_MEDIUM
        }


class StateColors:
    """Color utilities for different component states."""
    
    @staticmethod
    def get_notification_colors(notification_type: str) -> Dict[str, str]:
        """Get colors for notification types."""
        colors = {
            'info': {
                'bg_color': ColorTokens.INFO_CONTAINER,
                'border_color': ColorTokens.INFO,
                'text_color': ColorTokens.ON_INFO_CONTAINER,
                'icon_color': ColorTokens.INFO
            },
            'success': {
                'bg_color': ColorTokens.SUCCESS_CONTAINER,
                'border_color': ColorTokens.SUCCESS,
                'text_color': ColorTokens.ON_SUCCESS_CONTAINER,
                'icon_color': ColorTokens.SUCCESS
            },
            'warning': {
                'bg_color': ColorTokens.WARNING_CONTAINER,
                'border_color': ColorTokens.WARNING,
                'text_color': ColorTokens.ON_WARNING_CONTAINER,
                'icon_color': ColorTokens.WARNING
            },
            'error': {
                'bg_color': ColorTokens.ERROR_CONTAINER,
                'border_color': ColorTokens.ERROR,
                'text_color': ColorTokens.ON_ERROR_CONTAINER,
                'icon_color': ColorTokens.ERROR
            }
        }
        return colors.get(notification_type, colors['info'])
    
    @staticmethod
    def get_workflow_stage_colors(status: str) -> Dict[str, str]:
        """Get colors for workflow stage statuses."""
        colors = {
            'completed': {
                'bg_color': ColorTokens.SUCCESS_CONTAINER,
                'border_color': ColorTokens.SUCCESS,
                'text_color': ColorTokens.ON_SUCCESS_CONTAINER,
                'icon_color': ColorTokens.SUCCESS
            },
            'in_progress': {
                'bg_color': ColorTokens.INFO_CONTAINER,
                'border_color': ColorTokens.INFO,
                'text_color': ColorTokens.ON_INFO_CONTAINER,
                'icon_color': ColorTokens.INFO
            },
            'blocked': {
                'bg_color': ColorTokens.ERROR_CONTAINER,
                'border_color': ColorTokens.ERROR,
                'text_color': ColorTokens.ON_ERROR_CONTAINER,
                'icon_color': ColorTokens.ERROR
            },
            'pending': {
                'bg_color': ColorTokens.SURFACE_VARIANT,
                'border_color': ColorTokens.OUTLINE,
                'text_color': ColorTokens.ON_SURFACE_VARIANT,
                'icon_color': ColorTokens.ON_SURFACE_VARIANT
            }
        }
        return colors.get(status, colors['pending'])


class HoverEffects:
    """Utilities for creating consistent hover effects."""
    
    @staticmethod
    def create_hover_handler(
        normal_color: str,
        hover_color: str,
        animate: bool = True
    ):
        """Create a hover event handler with color transitions."""
        def handle_hover(e):
            if e.data == "true":  # Mouse enter
                e.control.bgcolor = hover_color
            else:  # Mouse leave
                e.control.bgcolor = normal_color
            
            if animate and hasattr(e.control, 'update'):
                try:
                    e.control.update()
                except (AssertionError, AttributeError):
                    # Widget not attached to page, skip update
                    pass
        
        return handle_hover
    
    @staticmethod
    def create_scale_hover_handler(
        normal_scale: float = 1.0,
        hover_scale: float = 1.05,
        animate: bool = True
    ):
        """Create a hover handler with scale effects."""
        def handle_hover(e):
            if e.data == "true":  # Mouse enter
                e.control.scale = hover_scale
            else:  # Mouse leave
                e.control.scale = normal_scale
            
            if animate and hasattr(e.control, 'update'):
                try:
                    e.control.update()
                except (AssertionError, AttributeError):
                    # Widget not attached to page, skip update
                    pass
        
        return handle_hover


class MicroAnimations:
    """Utilities for creating micro-animations and transitions."""
    
    @staticmethod
    def pulse_animation(control: ft.Control, duration: int = 1000):
        """Create a pulsing animation effect."""
        control.animate_scale = ft.Animation(duration, ft.AnimationCurve.EASE_IN_OUT)
        # Note: Actual pulsing would require a timer or animation controller
    
    @staticmethod
    def fade_in(control: ft.Control, duration: int = 300):
        """Create a fade-in animation."""
        control.opacity = 0
        control.animate_opacity = ft.Animation(duration, ft.AnimationCurve.EASE_OUT)
        # Set opacity to 1 after a brief delay to trigger animation
    
    @staticmethod
    def slide_in_from_right(control: ft.Control, duration: int = 300):
        """Create a slide-in from right animation."""
        control.offset = ft.transform.Offset(1, 0)
        control.animate_offset = ft.Animation(duration, ft.AnimationCurve.EASE_OUT)
        # Set offset to (0, 0) to trigger animation
    
    @staticmethod
    def bounce_in(control: ft.Control, duration: int = 400):
        """Create a bounce-in animation."""
        control.scale = 0.3
        control.animate_scale = ft.Animation(duration, ft.AnimationCurve.EASE_OUT_BACK)
        # Set scale to 1 to trigger animation


# Utility functions for applying design system
def apply_card_style(container: ft.Container, elevated: bool = False, interactive: bool = False):
    """Apply card styling to a container."""
    style = ComponentStyles.card_container(elevated, interactive)
    for key, value in style.items():
        setattr(container, key, value)


def apply_button_style(button: ft.ElevatedButton, variant: str = 'primary'):
    """Apply button styling based on variant."""
    if variant == 'primary':
        button.style = ComponentStyles.primary_button()
    elif variant == 'secondary':
        button.style = ComponentStyles.secondary_button()
    elif variant == 'outlined':
        button.style = ComponentStyles.outlined_button()
    elif variant == 'text':
        button.style = ComponentStyles.text_button()


def create_styled_text(
    text: str,
    style_type: str = 'body_medium',
    color: Optional[str] = None
) -> ft.Text:
    """Create a text widget with consistent styling."""
    style_map = {
        'display_large': Typography.DISPLAY_LARGE,
        'display_medium': Typography.DISPLAY_MEDIUM,
        'display_small': Typography.DISPLAY_SMALL,
        'headline_large': Typography.HEADLINE_LARGE,
        'headline_medium': Typography.HEADLINE_MEDIUM,
        'headline_small': Typography.HEADLINE_SMALL,
        'title_large': Typography.TITLE_LARGE,
        'title_medium': Typography.TITLE_MEDIUM,
        'title_small': Typography.TITLE_SMALL,
        'label_large': Typography.LABEL_LARGE,
        'label_medium': Typography.LABEL_MEDIUM,
        'label_small': Typography.LABEL_SMALL,
        'body_large': Typography.BODY_LARGE,
        'body_medium': Typography.BODY_MEDIUM,
        'body_small': Typography.BODY_SMALL,
    }
    
    text_style = style_map.get(style_type, Typography.BODY_MEDIUM)
    
    return ft.Text(
        text,
        size=text_style.size,
        weight=text_style.weight,
        color=color or ColorTokens.ON_SURFACE
    )


def create_styled_container(
    content: ft.Control,
    variant: str = 'surface',
    padding: Optional[ft.Padding] = None,
    margin: Optional[ft.Margin] = None,
    border_radius: Optional[int] = None
) -> ft.Container:
    """Create a container with consistent styling."""
    container = ft.Container(content=content)
    
    # Apply variant styling
    if variant == 'surface':
        container.bgcolor = ColorTokens.SURFACE
        container.border = ft.border.all(1, ColorTokens.OUTLINE_VARIANT)
    elif variant == 'surface_variant':
        container.bgcolor = ColorTokens.SURFACE_VARIANT
    elif variant == 'primary_container':
        container.bgcolor = ColorTokens.PRIMARY_CONTAINER
    elif variant == 'secondary_container':
        container.bgcolor = ColorTokens.SECONDARY_CONTAINER
    
    # Apply padding
    if padding:
        container.padding = padding
    else:
        container.padding = Spacing.padding_all(Spacing.MD)
    
    # Apply margin
    if margin:
        container.margin = margin
    
    # Apply border radius
    if border_radius is not None:
        container.border_radius = BorderRadius.all(border_radius)
    else:
        container.border_radius = BorderRadius.all(BorderRadius.MD)
    
    return container