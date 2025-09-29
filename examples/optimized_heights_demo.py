#!/usr/bin/env python3
"""
Demo script to showcase optimized TopBar heights for different devices.
This demonstrates the implementation of task 3: "Otimizar alturas da TopBar para diferentes dispositivos"
"""

import flet as ft
from unittest.mock import Mock
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from views.components.top_sidebar_container import TopSidebarContainer
from services.time_tracking_service import TimeTrackingService
from services.workflow_service import WorkflowService
from services.notification_service import NotificationService


def main(page: ft.Page):
    """Main demo function."""
    page.title = "Optimized TopBar Heights Demo"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    
    # Create mock services for demo
    time_service = Mock(spec=TimeTrackingService)
    workflow_service = Mock(spec=WorkflowService)
    notification_service = Mock(spec=NotificationService)
    
    # Set up mock behaviors
    time_service.is_tracking.return_value = False
    time_service.is_paused.return_value = False
    notification_service.get_unread_count.return_value = 0
    notification_service.get_notifications.return_value = []
    notification_service.add_observer = Mock()
    
    # Create containers for different device simulations
    containers = {}
    device_info = {}
    
    def create_device_container(device_type, is_mobile, is_tablet):
        """Create a container simulating a specific device type."""
        # Mock the layout manager for this device
        from views.components.top_sidebar_container import layout_manager
        original_is_mobile = layout_manager.is_mobile
        original_is_tablet = layout_manager.is_tablet
        
        layout_manager.is_mobile = lambda: is_mobile
        layout_manager.is_tablet = lambda: is_tablet
        
        try:
            container = TopSidebarContainer(
                page,
                time_service,
                workflow_service,
                notification_service
            )
            
            # Get height information
            altura_expandida, altura_recolhida = container._get_optimized_heights()
            device_info[device_type] = {
                'expanded': altura_expandida,
                'collapsed': altura_recolhida,
                'space_saved': altura_expandida - altura_recolhida
            }
            
            return container
        finally:
            # Restore original methods
            layout_manager.is_mobile = original_is_mobile
            layout_manager.is_tablet = original_is_tablet
    
    # Create device simulation controls
    current_device = ft.Ref[ft.Text]()
    current_heights = ft.Ref[ft.Text]()
    current_container = ft.Ref[ft.Container]()
    
    def switch_device(device_type, is_mobile, is_tablet):
        """Switch to a different device simulation."""
        # Update layout manager
        from views.components.top_sidebar_container import layout_manager
        layout_manager.is_mobile = lambda: is_mobile
        layout_manager.is_tablet = lambda: is_tablet
        
        # Create new container
        container = TopSidebarContainer(
            page,
            time_service,
            workflow_service,
            notification_service
        )
        
        # Get height information
        altura_expandida, altura_recolhida = container._get_optimized_heights()
        space_saved = altura_expandida - altura_recolhida
        
        # Update display
        current_device.current.value = f"Dispositivo Atual: {device_type}"
        current_heights.current.value = (
            f"Alturas: {altura_expandida}px (expandida) / {altura_recolhida}px (recolhida)\n"
            f"Espaço liberado: {space_saved}px"
        )
        
        # Update container
        current_container.current.content = ft.Column([
            ft.Text(f"TopBar - {device_type}", size=16, weight=ft.FontWeight.BOLD),
            container,
            ft.Text(f"Altura atual: {container.height}px", size=12, color=ft.Colors.GREY_400)
        ])
        
        page.update()
    
    # Device selection buttons
    device_buttons = ft.Row([
        ft.ElevatedButton(
            "Mobile (40px/28px)",
            on_click=lambda _: switch_device("Mobile", True, False),
            bgcolor=ft.Colors.BLUE_700
        ),
        ft.ElevatedButton(
            "Tablet (41px/30px)",
            on_click=lambda _: switch_device("Tablet", False, True),
            bgcolor=ft.Colors.GREEN_700
        ),
        ft.ElevatedButton(
            "Desktop (42px/32px)",
            on_click=lambda _: switch_device("Desktop", False, False),
            bgcolor=ft.Colors.PURPLE_700
        ),
    ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
    
    # Information display
    info_section = ft.Column([
        ft.Text(ref=current_device, size=18, weight=ft.FontWeight.BOLD),
        ft.Text(ref=current_heights, size=14, color=ft.Colors.GREY_300),
    ])
    
    # Container display area
    container_display = ft.Container(
        ref=current_container,
        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        border_radius=10,
        padding=20,
        width=800,
        height=200
    )
    
    # Instructions
    instructions = ft.Container(
        content=ft.Column([
            ft.Text("Demonstração de Alturas Otimizadas da TopBar", 
                   size=24, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            ft.Text(
                "Esta demonstração mostra como a TopBar se adapta a diferentes dispositivos:\n"
                "• Mobile: Alturas mais compactas (40px/28px) para maximizar espaço\n"
                "• Tablet: Alturas intermediárias (41px/30px) para equilibrar usabilidade\n"
                "• Desktop: Alturas padrão otimizadas (42px/32px)\n"
                "• Padding vertical mínimo (2px) em todos os dispositivos\n"
                "• Animações suaves de 300ms para transições",
                size=14,
                text_align=ft.TextAlign.CENTER,
                color=ft.Colors.GREY_300
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=20,
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
        border_radius=10,
        margin=ft.margin.only(bottom=20)
    )
    
    # Layout
    page.add(
        instructions,
        ft.Text("Selecione um tipo de dispositivo:", size=16, weight=ft.FontWeight.BOLD),
        device_buttons,
        ft.Divider(height=20),
        info_section,
        ft.Divider(height=20),
        container_display
    )
    
    # Initialize with desktop view
    switch_device("Desktop", False, False)


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8080)