import flet as ft
import json
from typing import Optional
from views.components.time_tracker_widget import TimeTrackerWidget
from views.components.flowchart_widget import FlowchartWidget
from views.components.notification_center import NotificationCenter
from views.components.webview_component import WebViewComponent
from services.time_tracking_service import TimeTrackingService
from services.workflow_service import WorkflowService
from services.notification_service import NotificationService
from services.web_server.models import ConfiguracaoServidorWeb
from services.web_server.sync_manager import DataSyncManager
from services.web_server.data_provider import JSONDataProvider
from views.components.performance_utils import (
    performance_tracked, throttled, debounced, lifecycle_manager,
    layout_manager, animation_manager
)


class TopSidebarContainer(ft.Container):
    """
    Container that houses time tracker, flowchart, and notification center
    in a responsive horizontal layout that adapts to sidebar expansion state.
    """
    
    def __init__(
        self, 
        page: ft.Page,
        time_tracking_service: Optional[TimeTrackingService] = None,
        workflow_service: Optional[WorkflowService] = None,
        notification_service: Optional[NotificationService] = None,
        habilitar_webview: bool = False,
        url_servidor_web: Optional[str] = None,
        config_servidor: Optional[ConfiguracaoServidorWeb] = None
    ):
        """
        Initialize the top sidebar container.
        
        Args:
            page: The Flet page instance
            time_tracking_service: Service for time tracking functionality
            workflow_service: Service for workflow management
            notification_service: Service for notification management
            habilitar_webview: Whether to enable WebView integration
            url_servidor_web: URL of the local web server for WebView
            config_servidor: Configuration for the web server
        """
        super().__init__()
        
        self.page = page
        self.sidebar_expanded = True  # Track sidebar state
        self._topbar_expanded = True  # Estado da TopBar (expandida por padrão)
        
        # WebView configuration
        self.habilitar_webview = habilitar_webview
        self.url_servidor_web = url_servidor_web
        self.config_servidor = config_servidor or ConfiguracaoServidorWeb()
        self.webview_expandido = True  # Track WebView expansion state
        
        # Performance optimization: Register with lifecycle manager
        lifecycle_manager.register_component(self)
        
        # Initialize services with defaults if not provided
        self.time_tracking_service = time_tracking_service or TimeTrackingService()
        self.workflow_service = workflow_service or WorkflowService()
        self.notification_service = notification_service or NotificationService()
        
        # Responsive layout state
        self._current_breakpoint = 'lg'
        layout_manager.register_layout_callback('top_sidebar', self._on_layout_change)
        
        # Initialize component widgets
        self.time_tracker = TimeTrackerWidget(page, self.time_tracking_service)
        self.flowchart = FlowchartWidget(page, self.workflow_service)
        self.notifications = NotificationCenter(page, self.notification_service)
        
        # Initialize WebView component if enabled
        self.webview: Optional[WebViewComponent] = None
        if self.habilitar_webview and self.url_servidor_web:
            self._inicializar_webview()
        
        # Initialize data synchronization system
        self.sync_manager: Optional[DataSyncManager] = None
        self._sync_callbacks_registrados = False
        if self.habilitar_webview:
            self._inicializar_sistema_sincronizacao()
        
        # Initialize default workflow for demonstration (only if not already loaded)
        if not self.flowchart.workflow_state:
            try:
                self.flowchart.create_default_workflow("default_project")
            except Exception as e:
                # Log error but don't fail initialization
                print(f"Info: Workflow já existe ou erro na criação: {e}")
        
        # WebView carrega automaticamente - não precisa de reload manual
        
        # Setup component observers for data synchronization
        if self.sync_manager:
            self._configurar_observadores_componentes()
        
        # Build the container layout
        self._build_layout()
    
    def _inicializar_webview(self) -> None:
        """Initialize the WebView component."""
        try:
            self.webview = WebViewComponent(
                page=self.page,
                url_servidor=self.url_servidor_web,
                modo_debug=self.config_servidor.modo_debug,
                timeout_carregamento=self.config_servidor.timeout_conexao
            )
        except Exception as e:
            # Log error but don't fail initialization
            if hasattr(self.page, 'show_snack_bar'):
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(f"Erro ao inicializar WebView: {str(e)}"),
                        duration=3000
                    )
                )
            # Disable WebView on error
            self.habilitar_webview = False
            self.webview = None
    
    @performance_tracked("top_sidebar_layout_build")
    def _build_layout(self):
        """Build the responsive horizontal layout with performance optimization."""
        # Check if TopBar is collapsed
        topbar_expanded = getattr(self, '_topbar_expanded', True)
        
        if not topbar_expanded:
            # TopBar recolhida - mostrar apenas botão de expansão
            layout = self._create_collapsed_topbar_layout()
        else:
            # TopBar expandida - layout normal
            # Determine layout based on both sidebar state and screen size
            is_mobile = layout_manager.is_mobile()
            is_tablet = layout_manager.is_tablet()
            
            if is_mobile:
                # Mobile layout - stack vertically or show minimal components
                layout = self._create_mobile_layout()
            elif is_tablet:
                # Tablet layout - compact horizontal layout
                layout = self._create_tablet_layout()
            elif self.sidebar_expanded:
                # Desktop expanded layout
                layout = self._create_desktop_expanded_layout()
            else:
                # Desktop collapsed layout
                layout = self._create_desktop_collapsed_layout()
        
        # Apply clean styling without excessive borders
        self.content = layout
        
        # Dynamic height adjustment based on expansion state using optimized heights
        altura_expandida, altura_recolhida = self._get_optimized_heights()
        
        if not topbar_expanded:
            # Collapsed state - minimal height to maximize available space
            self.height = altura_recolhida
            self.padding = ft.padding.all(0)  # Zero padding for maximum space efficiency
        else:
            # Expanded state - optimized height based on device with minimal padding
            self.height = altura_expandida
            # Minimal vertical padding (2px) to maximize space while maintaining usability
            if layout_manager.is_mobile():
                self.padding = ft.padding.symmetric(horizontal=8, vertical=2)  # 2px vertical padding
            else:
                self.padding = ft.padding.symmetric(horizontal=12, vertical=2)  # 2px vertical padding
        
        # Estilo completamente limpo - sem bordas ou fundos para maximizar espaço
        self.bgcolor = None  # Remove fundo
        self.border_radius = None  # Remove bordas arredondadas
        self.border = None  # Garantir que não há bordas
        
        # Enable smooth transitions (300ms) for topbar collapse/expand
        self.animate = ft.Animation(300, "ease")
    
    def _create_mobile_layout(self) -> ft.Row:
        """Create mobile-optimized layout: Time | WebView/Fluxo | Tema + Notificações."""
        
        # 1. TIME TRACKER (esquerda) - largura otimizada
        time_section = ft.Container(
            content=self._create_compact_time_tracker(),
            width=100,  # Largura otimizada (reduzida de 120px)
            alignment=ft.alignment.center,
            padding=ft.padding.symmetric(horizontal=2, vertical=1)
        )
        
        # 2. WEBVIEW/FLUXO (centro) - compacto
        if self.habilitar_webview and self.webview:
            center_content = self._create_compact_webview()
        else:
            center_content = self._create_compact_flowchart()
            
        webview_section = ft.Container(
            content=center_content,
            expand=True,
            alignment=ft.alignment.center,
            padding=ft.padding.symmetric(horizontal=2),
            bgcolor='rgba(255, 255, 255, 0.05)',
            border_radius=ft.border_radius.all(6)
        )
        
        # 3. TEMA + NOTIFICAÇÕES (direita) - compacto
        right_controls = [self._create_theme_toggle_button(), self.notifications]
        # Always show topbar toggle button (not dependent on WebView)
        right_controls.insert(1, self._create_topbar_toggle_button())
        
        theme_notifications_section = ft.Container(
            content=ft.Row(right_controls, spacing=4, alignment=ft.MainAxisAlignment.CENTER),
            width=110,  # Largura fixa para acomodar tema + toggle + notificações
            alignment=ft.alignment.center,
            padding=ft.padding.symmetric(horizontal=2, vertical=1)
        )
        
        return ft.Row(
            controls=[
                time_section,
                webview_section,
                theme_notifications_section
            ],
            spacing=4,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )
    
    def _create_tablet_layout(self) -> ft.Row:
        """Create tablet-optimized layout: Time | WebView/Fluxo | Tema + Notificações."""
        
        # 1. TIME TRACKER (esquerda) - largura otimizada
        time_section = ft.Container(
            content=self._create_compact_time_tracker(),
            width=140,  # Largura otimizada (reduzida de 180px)
            alignment=ft.alignment.center,
            padding=ft.padding.symmetric(horizontal=4, vertical=2)
        )
        
        # 2. WEBVIEW/FLUXO (centro)
        if self.habilitar_webview and self.webview and self.webview_expandido:
            center_content = self._create_compact_webview()
        elif self.habilitar_webview and self.webview:
            center_content = self._create_compact_webview()
        else:
            center_content = self._create_compact_flowchart()
            
        webview_section = ft.Container(
            content=center_content,
            expand=True,
            alignment=ft.alignment.center,
            padding=ft.padding.symmetric(horizontal=4),
            bgcolor='rgba(255, 255, 255, 0.05)',
            border_radius=ft.border_radius.all(8)
        )
        
        # 3. TEMA + NOTIFICAÇÕES (direita)
        right_controls = [self._create_theme_toggle_button(), self.notifications]
        # Always show topbar toggle button (not dependent on WebView)
        right_controls.insert(1, self._create_topbar_toggle_button())
        
        theme_notifications_section = ft.Container(
            content=ft.Row(right_controls, spacing=6, alignment=ft.MainAxisAlignment.CENTER),
            width=130,  # Largura aumentada para acomodar toggle do TopBar
            alignment=ft.alignment.center,
            padding=ft.padding.symmetric(horizontal=4, vertical=2)
        )
        
        return ft.Row(
            controls=[
                time_section,
                webview_section,
                theme_notifications_section
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )
    
    def _create_desktop_expanded_layout(self) -> ft.Row:
        """Create desktop expanded layout: Time Tracker | WebView (fluxo) | Tema + Notificações."""
        
        # 1. TIME TRACKER (esquerda) - largura otimizada
        time_section = ft.Container(
            content=self.time_tracker,
            width=280,  # Largura otimizada (reduzida de 350px)
            padding=ft.padding.symmetric(horizontal=12, vertical=4),
            alignment=ft.alignment.center_left
        )
        
        # 2. WEBVIEW/FLUXO (centro) - expansível
        if self.habilitar_webview and self.webview and self.webview_expandido:
            center_content = self.webview
        elif self.habilitar_webview and self.webview:
            center_content = self._create_compact_webview()
        else:
            center_content = self.flowchart
            
        webview_section = ft.Container(
            content=center_content,
            expand=True,  # Pega todo espaço disponível
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            alignment=ft.alignment.center
        )
        
        # 3. TEMA + NOTIFICAÇÕES + TOPBAR TOGGLE (direita)
        theme_notifications_section = ft.Container(
            content=ft.Row([
                self._create_theme_toggle_button(),
                self.notifications,
                self._create_topbar_toggle_button()
            ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
            width=120,  # Largura ajustada para tema + notificações + toggle
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            alignment=ft.alignment.center_right
        )
        
        return ft.Row(
            controls=[
                time_section,
                webview_section, 
                theme_notifications_section
            ],
            spacing=0,  # Sem espaçamento entre seções
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )
    
    def _create_desktop_collapsed_layout(self) -> ft.Row:
        """Create desktop collapsed layout: Time | WebView/Fluxo | Tema + Notificações."""
        
        # 1. TIME TRACKER (esquerda) - largura otimizada
        time_section = ft.Container(
            content=self._create_compact_time_tracker(),
            width=120,  # Largura otimizada (reduzida de 150px)
            alignment=ft.alignment.center,
            padding=ft.padding.symmetric(horizontal=4, vertical=2)
        )
        
        # 2. WEBVIEW/FLUXO (centro) - compacto mas expansível
        if self.habilitar_webview and self.webview:
            center_content = self._create_compact_webview()
        else:
            center_content = self._create_compact_flowchart()
            
        webview_section = ft.Container(
            content=center_content,
            expand=True,
            alignment=ft.alignment.center,
            padding=ft.padding.symmetric(horizontal=4, vertical=2)
        )
        
        # 3. TEMA + NOTIFICAÇÕES + TOPBAR TOGGLE (direita) - compacto
        theme_notifications_section = ft.Container(
            content=ft.Row([
                self._create_theme_toggle_button(),
                self.notifications,
                self._create_topbar_toggle_button()
            ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
            width=110,  # Largura otimizada para incluir toggle do TopBar
            alignment=ft.alignment.center,
            padding=ft.padding.symmetric(horizontal=4, vertical=2)
        )
        
        return ft.Row(
            controls=[
                time_section,
                webview_section,
                theme_notifications_section
            ],
            spacing=0,  # Sem espaçamento entre seções
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )
    
    def _create_collapsed_topbar_layout(self) -> ft.Container:
        """
        Create layout for collapsed TopBar - minimal height with only expand button.
        Uses optimized heights based on device type to maximize available space.
        """
        _, altura_recolhida = self._get_optimized_heights()
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(expand=True),  # Espaço vazio para empurrar botão para direita
                    ft.Container(
                        content=self._create_topbar_toggle_button(),
                        alignment=ft.alignment.center,
                        padding=ft.padding.symmetric(horizontal=8, vertical=2)  # Padding mínimo
                    )
                ],
                alignment=ft.MainAxisAlignment.END,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            height=altura_recolhida,  # Altura otimizada baseada no dispositivo
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.ON_SURFACE_VARIANT),
            border_radius=ft.border_radius.only(bottom_left=8, bottom_right=8),
            animate=ft.Animation(300, "ease")  # Animação suave de 300ms
        )
    
    def _create_compact_time_tracker(self) -> ft.Control:
        """Create a compact version of the time tracker for collapsed sidebar."""
        # Get current state from the time tracker
        try:
            is_running = self.time_tracker.is_running
            # Handle mock objects in tests
            if not isinstance(is_running, bool):
                is_running = False
        except:
            is_running = False
        
        try:
            elapsed_time = self.time_tracker.elapsed_time
            # Handle mock objects in tests
            if not isinstance(elapsed_time, (int, float)):
                elapsed_time = 0
        except:
            elapsed_time = 0
        
        # Choose icon and color based on state
        if is_running:
            try:
                is_paused = self.time_tracker.is_paused
                if not isinstance(is_paused, bool):
                    is_paused = False
            except:
                is_paused = False
                
            if is_paused:
                icon = ft.Icons.PAUSE_CIRCLE_FILLED
                color = 'warning'
            else:
                icon = ft.Icons.PLAY_CIRCLE_FILLED
                color = 'primary'
        else:
            icon = ft.Icons.TIMER_OUTLINED
            color = 'on_surface_variant'
        
        # Format time safely
        try:
            formatted_time = self.time_tracker._format_time(elapsed_time)
            if not isinstance(formatted_time, str):
                formatted_time = "00:00:00"
        except:
            formatted_time = "00:00:00"
        
        return ft.IconButton(
            icon=icon,
            icon_color=color,
            icon_size=24,
            tooltip=f"Time Tracker - {formatted_time}",
            on_click=self._on_compact_timer_click
        )
    
    def _create_compact_flowchart(self) -> ft.Control:
        """Create a compact version of the flowchart for collapsed sidebar."""
        # Get current workflow progress
        try:
            progress = self.flowchart.get_progress_percentage()
            # Handle mock objects in tests
            if not isinstance(progress, (int, float)):
                progress = 0.0
        except:
            progress = 0.0
        
        try:
            current_stage = self.flowchart.get_current_stage()
            # Handle mock objects in tests
            stage_name = getattr(current_stage, 'name', None) if current_stage else "No workflow"
            if not isinstance(stage_name, str):
                stage_name = "No workflow"
        except:
            stage_name = "No workflow"
        
        # Create progress indicator
        progress_bar = ft.ProgressBar(
            value=max(0.0, min(1.0, progress / 100.0)) if progress else 0.0,
            width=40,
            height=4,
            color='primary',
            bgcolor='surface_variant'
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.ACCOUNT_TREE,
                        size=16,
                        color='primary'
                    ),
                    progress_bar
                ],
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            tooltip=f"Workflow: {stage_name} ({progress:.0f}%)",
            on_click=self._on_compact_flowchart_click
        )
    
    def _create_compact_webview(self) -> ft.Control:
        """Create a compact version of the WebView for collapsed state."""
        if not self.webview:
            return ft.Container()
        
        # Determine icon and color based on WebView state
        if self.webview.esta_carregando:
            icon = ft.Icons.HOURGLASS_EMPTY
            color = 'warning'
            tooltip = "WebView carregando..."
        elif self.webview.tem_erro:
            icon = ft.Icons.ERROR_OUTLINE
            color = 'error'
            tooltip = f"Erro no WebView: {self.webview.erro_atual}"
        else:
            icon = ft.Icons.WEB
            color = 'primary'
            tooltip = f"WebView: {self.webview.url_atual}"
        
        return ft.IconButton(
            icon=icon,
            icon_color=color,
            icon_size=20,
            tooltip=tooltip,
            on_click=self._on_compact_webview_click
        )
    
    def _get_optimized_heights(self) -> tuple[int, int]:
        """
        Retorna alturas otimizadas (expandida, recolhida) baseadas no dispositivo.
        
        Implementa detecção de dispositivo para otimizar alturas da TopBar:
        - Mobile: 40px expandida, 28px recolhida (máximo compacto)
        - Tablet: 41px expandida, 30px recolhida (intermediário)
        - Desktop: 42px expandida, 32px recolhida (padrão otimizado)
        
        Returns:
            tuple[int, int]: (altura_expandida, altura_recolhida)
        """
        if layout_manager.is_mobile():
            return (40, 28)  # Mobile: mais compacto para maximizar espaço
        elif layout_manager.is_tablet():
            return (41, 30)  # Tablet: intermediário
        else:
            return (42, 32)  # Desktop: padrão otimizado
    
    def _create_topbar_toggle_button(self) -> ft.Control:
        """Create a toggle button for TopBar collapse/expand."""
        icon = ft.Icons.EXPAND_LESS if self._topbar_expanded else ft.Icons.EXPAND_MORE
        tooltip = "Recolher TopBar (ganhar espaço)" if self._topbar_expanded else "Expandir TopBar"
        
        return ft.IconButton(
            icon=icon,
            icon_color='primary',
            icon_size=18,
            tooltip=tooltip,
            on_click=self._on_topbar_toggle_click
        )
    
    def _create_theme_toggle_button(self) -> ft.Control:
        """Create a theme toggle button."""
        # Get current theme from page
        current_theme = getattr(self.page, 'theme_mode', ft.ThemeMode.DARK)
        is_dark = current_theme == ft.ThemeMode.DARK
        
        icon = ft.Icons.LIGHT_MODE if is_dark else ft.Icons.DARK_MODE
        tooltip = "Alternar para tema claro" if is_dark else "Alternar para tema escuro"
        
        return ft.IconButton(
            icon=icon,
            icon_color='primary',
            icon_size=22,  # Tamanho ligeiramente aumentado
            tooltip=tooltip,
            on_click=self._on_theme_toggle_click
        )
    

    

    

    
    def _on_compact_timer_click(self, e):
        """Handle click on compact timer icon."""
        # In a full implementation, this could open a timer dialog
        # For now, we'll just show a simple message
        if self.page:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Expand sidebar to access full time tracker"),
                    duration=2000
                )
            )
    
    def _on_compact_flowchart_click(self, e):
        """Handle click on compact flowchart indicator."""
        # In a full implementation, this could open a workflow dialog
        # For now, we'll just show a simple message
        if self.page:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Expand sidebar to access full workflow view"),
                    duration=2000
                )
            )
    
    def _on_compact_webview_click(self, e):
        """Handle click on compact WebView indicator."""
        # Simply toggle WebView expansion - no manual reload needed
        self.toggle_webview_expansion()
    
    def _on_topbar_toggle_click(self, e):
        """Handle TopBar toggle button click."""
        # Alternar estado
        self._topbar_expanded = not self._topbar_expanded
        
        # Reconstruir layout com novo estado
        self._build_layout()
        
        # Atualizar página
        if self.page:
            self.page.update()
        
        # Mostrar feedback
        status = "expandida" if self._topbar_expanded else "recolhida"
        message = f"TopBar {status}"
        if not self._topbar_expanded:
            message += " - mais área disponível"
        
        if hasattr(self.page, 'show_snack_bar'):
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(message),
                    duration=1500
                )
            )
    
    def _on_theme_toggle_click(self, e):
        """Handle theme toggle button click."""
        if not self.page:
            return
        
        # Get current theme
        current_theme = getattr(self.page, 'theme_mode', ft.ThemeMode.DARK)
        
        # Toggle theme
        new_theme = ft.ThemeMode.LIGHT if current_theme == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        self.page.theme_mode = new_theme
        
        # Save theme preference
        if hasattr(self.page, 'client_storage'):
            theme_value = "dark" if new_theme == ft.ThemeMode.DARK else "light"
            self.page.client_storage.set("theme", theme_value)
        
        # Rebuild layout to update the icon
        self._build_layout()
        
        # Update page
        self.page.update()
        
        # Show feedback
        theme_name = "escuro" if new_theme == ft.ThemeMode.DARK else "claro"
        if hasattr(self.page, 'show_snack_bar'):
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Tema alterado para {theme_name}"),
                    duration=1500
                )
            )
    

        
        # Show feedback
        status = "expandida" if new_state else "recolhida"
        if hasattr(self.page, 'show_snack_bar'):
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"TopBar {status}"),
                    duration=1000
                )
            )
    


    
    def update_layout(self, sidebar_expanded: bool):
        """
        Update the layout based on sidebar expansion state.
        
        Args:
            sidebar_expanded: Whether the sidebar is expanded
        """
        # Only update if state actually changed
        if self.sidebar_expanded != sidebar_expanded:
            self.sidebar_expanded = sidebar_expanded
            self._sidebar_expanded = sidebar_expanded  # Atualizar estado interno
            
            # Auto-collapse WebView when sidebar is collapsed on smaller screens
            if not sidebar_expanded and (layout_manager.is_mobile() or layout_manager.is_tablet()):
                self.webview_expandido = False
            
            self._build_layout()
            
            # Trigger data synchronization for sidebar state change
            if self.sync_manager:
                self._callback_mudanca_sidebar()
            
            # Update the page if available
            if self.page:
                self.page.update()
    

    
    def toggle_webview_expansion(self):
        """Toggle WebView expansion state."""
        if not self.habilitar_webview:
            # Show message that WebView is not enabled
            if self.page and hasattr(self.page, 'show_snack_bar'):
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("WebView não está habilitado"),
                        duration=2000
                    )
                )
            return
        
        if not self.webview:
            # Try to initialize WebView if it failed before
            if self.url_servidor_web:
                self._inicializar_webview()
            
            if not self.webview:
                if self.page and hasattr(self.page, 'show_snack_bar'):
                    self.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text("WebView não pôde ser inicializado"),
                            duration=2000
                        )
                    )
                return
        
        self.webview_expandido = not self.webview_expandido
        self._build_layout()
        
        # Show feedback message
        if self.page and hasattr(self.page, 'show_snack_bar'):
            message = "WebView expandido" if self.webview_expandido else "WebView recolhido"
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(message),
                    duration=1500
                )
            )
            self.page.update()
    
    def toggle_topbar_expansion(self):
        """Toggle TopBar expansion state to gain more area below."""
        # Alternar estado
        self._topbar_expanded = not self._topbar_expanded
        
        # Reconstruir layout com novo estado
        self._build_layout()
        
        # Atualizar página
        if self.page:
            self.page.update()
        
        # Mostrar feedback
        status = "expandida" if self._topbar_expanded else "recolhida"
        message = f"TopBar {status}"
        if not self._topbar_expanded:
            message += " - mais área disponível"
        
        if hasattr(self.page, 'show_snack_bar'):
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(message),
                    duration=1500
                )
            )
    
    def is_topbar_expanded(self) -> bool:
        """Check if TopBar is currently expanded."""
        return self._topbar_expanded
    
    def set_topbar_expanded(self, expanded: bool) -> None:
        """Set TopBar expansion state programmatically."""
        if self._topbar_expanded != expanded:
            self.toggle_topbar_expansion()
    
    def atualizar_url_webview(self, nova_url: str):
        """
        Update WebView URL.
        
        Args:
            nova_url: New URL for the WebView
        """
        if self.webview:
            try:
                self.webview.atualizar_url(nova_url)
                self.url_servidor_web = nova_url
            except Exception as e:
                if self.page:
                    self.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text(f"Erro ao atualizar URL do WebView: {str(e)}"),
                            duration=3000
                        )
                    )
    

    
    def _on_layout_change(self, breakpoint: str, width: float) -> None:
        """Handle responsive layout changes."""
        if self._current_breakpoint != breakpoint:
            self._current_breakpoint = breakpoint
            self._build_layout()
            
            if self.page:
                self.page.update()
    
    def cleanup(self) -> None:
        """Clean up resources to prevent memory leaks."""
        # Clean up sync manager first
        if self.sync_manager:
            try:
                self.sync_manager.finalizar()
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.error(f"Erro ao finalizar sync manager: {str(e)}")
            finally:
                self.sync_manager = None
        
        # Clean up child components
        if hasattr(self.time_tracker, 'cleanup'):
            self.time_tracker.cleanup()
        if hasattr(self.flowchart, 'cleanup'):
            self.flowchart.cleanup()
        if hasattr(self.notifications, 'cleanup'):
            self.notifications.cleanup()
        if self.webview and hasattr(self.webview, 'cleanup'):
            self.webview.cleanup()
        
        # Clean up lifecycle manager
        lifecycle_manager.cleanup_component(self)
    
    def refresh_components(self):
        """Refresh all child components."""
        # Refresh time tracker
        if hasattr(self.time_tracker, 'refresh'):
            self.time_tracker.refresh()
        
        # Refresh flowchart
        if hasattr(self.flowchart, '_refresh_display'):
            self.flowchart._refresh_display()
        
        # Refresh notifications (update display)
        if hasattr(self.notifications, '_update_display'):
            self.notifications._update_display()
        
        # WebView não precisa de refresh manual - atualiza automaticamente
        
        # Update compact views if in collapsed mode
        if not self.sidebar_expanded:
            self._build_layout()
        
        # Update the page if available
        if self.page:
            self.page.update()
    
    def get_time_tracker(self) -> TimeTrackerWidget:
        """Get the time tracker widget instance."""
        return self.time_tracker
    
    def get_flowchart(self) -> FlowchartWidget:
        """Get the flowchart widget instance."""
        return self.flowchart
    
    def get_notifications(self) -> NotificationCenter:
        """Get the notification center instance."""
        return self.notifications
    
    def get_webview(self) -> Optional[WebViewComponent]:
        """Get the WebView component instance."""
        return self.webview
    
    def is_webview_enabled(self) -> bool:
        """Check if WebView is enabled."""
        return self.habilitar_webview and self.webview is not None
    
    def is_webview_expanded(self) -> bool:
        """Check if WebView is expanded."""
        return self.webview_expandido
    
    def add_test_notification(self):
        """Add a test notification for demonstration purposes."""
        self.notifications.add_test_notification()
    
    def advance_workflow_stage(self, stage_name: str) -> bool:
        """
        Advance the workflow to a specific stage.
        
        Args:
            stage_name: Name of the stage to advance to
            
        Returns:
            True if successful, False otherwise
        """
        return self.flowchart.advance_to_stage(stage_name)
    
    def complete_current_workflow_stage(self) -> bool:
        """
        Complete the current workflow stage and advance to next.
        
        Returns:
            True if successful, False otherwise
        """
        return self.flowchart.complete_current_stage()
    
    def _extrair_dados_para_sincronizacao(self) -> dict:
        """
        Extract data from all components for synchronization with WebView.
        
        Returns:
            Dictionary with all component data for synchronization
        """
        from services.web_server.models import DadosTopSidebar, DadosTimeTracker, DadosFlowchart, DadosNotificacoes, DadosSidebar, BreakpointLayout
        from datetime import datetime
        
        try:
            # Extract time tracker data safely
            elapsed_time = getattr(self.time_tracker, 'elapsed_time', 0)
            # Convert timedelta to seconds if needed
            if hasattr(elapsed_time, 'total_seconds'):
                elapsed_time = int(elapsed_time.total_seconds())
            elif not isinstance(elapsed_time, (int, float)):
                elapsed_time = 0
            
            total_time_today = getattr(self.time_tracker, 'total_time_today', 0)
            if hasattr(total_time_today, 'total_seconds'):
                total_time_today = int(total_time_today.total_seconds())
            elif not isinstance(total_time_today, (int, float)):
                total_time_today = 0
            
            time_tracker_data = DadosTimeTracker(
                tempo_decorrido=elapsed_time,
                esta_executando=bool(getattr(self.time_tracker, 'is_running', False)),
                esta_pausado=bool(getattr(self.time_tracker, 'is_paused', False)),
                projeto_atual=str(getattr(self.time_tracker, 'current_project', '')),
                tarefa_atual=str(getattr(self.time_tracker, 'current_task', '')),
                tempo_total_hoje=total_time_today,
                meta_diaria=int(getattr(self.time_tracker, 'daily_goal', 8 * 3600))
            )
            
            # Extract flowchart data safely
            try:
                current_stage = self.flowchart.get_current_stage()
                progress = self.flowchart.get_progress_percentage()
                stages = getattr(self.flowchart, 'stages', [])
                workflow_name = getattr(self.flowchart, 'current_workflow_name', '')
            except Exception:
                current_stage = None
                progress = 0.0
                stages = []
                workflow_name = ''
            
            # Ensure progress is a valid number
            if not isinstance(progress, (int, float)) or hasattr(progress, '_mock_name'):
                progress = 0.0
            
            # Ensure stage name is a string
            stage_name = ""
            if current_stage and hasattr(current_stage, 'name'):
                name_value = current_stage.name
                # Handle mock objects
                if hasattr(name_value, '_mock_name') or str(name_value).startswith("<Mock"):
                    stage_name = ""
                else:
                    stage_name = str(name_value)
            
            # Ensure workflow name is a string
            if not isinstance(workflow_name, str) or hasattr(workflow_name, '_mock_name'):
                workflow_name = ""
            
            flowchart_data = DadosFlowchart(
                progresso_workflow=float(progress),
                estagio_atual=stage_name,
                total_estagios=len(stages),
                estagios_concluidos=sum(1 for stage in stages if getattr(stage, 'completed', False)),
                workflow_ativo=workflow_name,
                tempo_estimado_restante=self._calcular_tempo_estimado_restante(stages)
            )
            
            # Extract notifications data safely
            try:
                notifications_list = getattr(self.notifications, 'notifications', [])
                last_notification = getattr(self.notifications, 'last_notification_text', None)
                last_time = getattr(self.notifications, 'last_notification_time', None)
                notification_types = list(set(getattr(n, 'type', 'info') for n in notifications_list))
            except Exception:
                notifications_list = []
                last_notification = None
                last_time = None
                notification_types = []
            
            notifications_data = DadosNotificacoes(
                total_notificacoes=len(notifications_list),
                notificacoes_nao_lidas=len([n for n in notifications_list if not getattr(n, 'read', True)]),
                ultima_notificacao=last_notification,
                timestamp_ultima=last_time,
                tipos_notificacao=notification_types
            )
            
            # Extract sidebar data
            breakpoint_map = {
                'sm': BreakpointLayout.MOBILE,
                'md': BreakpointLayout.TABLET,
                'lg': BreakpointLayout.DESKTOP,
                'xl': BreakpointLayout.DESKTOP
            }
            
            # Determine visible components based on current layout
            componentes_visiveis = []
            if hasattr(self, 'time_tracker') and self.time_tracker:
                componentes_visiveis.append('time_tracker')
            if hasattr(self, 'flowchart') and self.flowchart:
                componentes_visiveis.append('flowchart')
            if hasattr(self, 'notifications') and self.notifications:
                componentes_visiveis.append('notifications')
            if hasattr(self, 'webview') and self.webview and self.habilitar_webview:
                componentes_visiveis.append('webview')
            
            sidebar_data = DadosSidebar(
                sidebar_expandido=self.sidebar_expanded,
                breakpoint_atual=breakpoint_map.get(self._current_breakpoint, BreakpointLayout.DESKTOP),
                largura_atual=getattr(self, 'width', 0) or 0,
                altura_atual=getattr(self, 'height', 0) or 0,
                componentes_visiveis=componentes_visiveis
            )
            
            # Create complete data structure
            dados_completos = DadosTopSidebar(
                timestamp=datetime.now(),
                time_tracker=time_tracker_data,
                flowchart=flowchart_data,
                notificacoes=notifications_data,
                sidebar=sidebar_data,
                versao=self._obter_versao_dados(),
                fonte="TopSidebarContainer"
            )
            
            return dados_completos.to_dict()
            
        except Exception as e:
            # Log error but return minimal data structure to prevent sync failures
            if hasattr(self, 'logger'):
                self.logger.error(f"Erro ao extrair dados para sincronização: {str(e)}")
            
            # Return minimal safe data
            return DadosTopSidebar().to_dict()
    
    def _calcular_tempo_estimado_restante(self, stages: list) -> int:
        """
        Calculate estimated remaining time based on stages.
        
        Args:
            stages: List of workflow stages
            
        Returns:
            Estimated remaining time in minutes
        """
        try:
            remaining_stages = [s for s in stages if not getattr(s, 'completed', False)]
            # Estimate 30 minutes per remaining stage (can be made configurable)
            return len(remaining_stages) * 30
        except Exception:
            return 0
    
    def _obter_versao_dados(self) -> int:
        """
        Get current data version for synchronization.
        
        Returns:
            Current data version number
        """
        if not hasattr(self, '_versao_dados'):
            self._versao_dados = 1
        return self._versao_dados
    
    def _incrementar_versao_dados(self) -> None:
        """Increment data version when changes occur."""
        if not hasattr(self, '_versao_dados'):
            self._versao_dados = 1
        else:
            self._versao_dados += 1
    
    def _inicializar_sistema_sincronizacao(self) -> None:
        """Initialize the data synchronization system."""
        try:
            # Create JSON data provider
            arquivo_sync = self.config_servidor.arquivo_sincronizacao
            json_provider = JSONDataProvider(arquivo_json=arquivo_sync)
            
            # Create sync manager
            self.sync_manager = DataSyncManager(
                provedor_dados=json_provider,
                logger=getattr(self, 'logger', None)
            )
            
            # Register callback for WebView updates
            self.sync_manager.registrar_callback_mudanca(self._callback_atualizacao_webview)
            self.sync_manager.registrar_callback_erro(self._callback_erro_sincronizacao)
            
            # Perform initial data sync
            self._sincronizar_dados_inicial()
            
            if hasattr(self, 'logger'):
                self.logger.info("Sistema de sincronização inicializado com sucesso")
                
        except Exception as e:
            error_msg = f"Erro ao inicializar sistema de sincronização: {str(e)}"
            if hasattr(self, 'logger'):
                self.logger.error(error_msg)
            
            # Show error to user if page is available
            if self.page and hasattr(self.page, 'show_snack_bar'):
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(f"Erro na sincronização: {str(e)}"),
                        duration=3000
                    )
                )
            
            # Disable sync manager on error
            self.sync_manager = None
    
    def _configurar_observadores_componentes(self) -> None:
        """Configure observers for component changes."""
        if not self.sync_manager or self._sync_callbacks_registrados:
            return
        
        try:
            # Setup time tracker observers
            self._configurar_observador_time_tracker()
            
            # Setup flowchart observers  
            self._configurar_observador_flowchart()
            
            # Setup notifications observers
            self._configurar_observador_notifications()
            
            # Setup sidebar state observers
            self._configurar_observador_sidebar()
            
            self._sync_callbacks_registrados = True
            
            if hasattr(self, 'logger'):
                self.logger.info("Observadores de componentes configurados")
                
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Erro ao configurar observadores: {str(e)}")
    
    def _configurar_observador_time_tracker(self) -> None:
        """Configure time tracker change observer."""
        if not hasattr(self.time_tracker, 'add_change_callback'):
            # If component doesn't support callbacks, use polling
            self._iniciar_polling_time_tracker()
            return
        
        # Register callback if supported
        self.time_tracker.add_change_callback(self._callback_mudanca_time_tracker)
    
    def _configurar_observador_flowchart(self) -> None:
        """Configure flowchart change observer."""
        if not hasattr(self.flowchart, 'add_change_callback'):
            # If component doesn't support callbacks, use polling
            self._iniciar_polling_flowchart()
            return
        
        # Register callback if supported
        self.flowchart.add_change_callback(self._callback_mudanca_flowchart)
    
    def _configurar_observador_notifications(self) -> None:
        """Configure notifications change observer."""
        if not hasattr(self.notifications, 'add_change_callback'):
            # If component doesn't support callbacks, use polling
            self._iniciar_polling_notifications()
            return
        
        # Register callback if supported
        self.notifications.add_change_callback(self._callback_mudanca_notifications)
    
    def _configurar_observador_sidebar(self) -> None:
        """Configure sidebar state change observer."""
        # Sidebar changes are handled directly in update_layout method
        pass
    
    def _iniciar_polling_time_tracker(self) -> None:
        """Start polling for time tracker changes if callbacks not supported."""
        import threading
        import time
        
        def poll_time_tracker():
            last_state = None
            while hasattr(self, 'sync_manager') and self.sync_manager:
                try:
                    current_state = {
                        'elapsed_time': getattr(self.time_tracker, 'elapsed_time', 0),
                        'is_running': getattr(self.time_tracker, 'is_running', False),
                        'is_paused': getattr(self.time_tracker, 'is_paused', False),
                        'current_project': getattr(self.time_tracker, 'current_project', ''),
                        'current_task': getattr(self.time_tracker, 'current_task', '')
                    }
                    
                    if current_state != last_state:
                        self._callback_mudanca_time_tracker()
                        last_state = current_state.copy()
                    
                    time.sleep(5.0)  # Poll every 5 seconds to reduce WebView loading indicators
                    
                except Exception as e:
                    if hasattr(self, 'logger'):
                        self.logger.error(f"Erro no polling do time tracker: {str(e)}")
                    break
        
        thread = threading.Thread(target=poll_time_tracker, daemon=True)
        thread.start()
    
    def _iniciar_polling_flowchart(self) -> None:
        """Start polling for flowchart changes if callbacks not supported."""
        import threading
        import time
        
        def poll_flowchart():
            last_state = None
            while hasattr(self, 'sync_manager') and self.sync_manager:
                try:
                    current_stage = self.flowchart.get_current_stage()
                    current_state = {
                        'progress': self.flowchart.get_progress_percentage(),
                        'current_stage': current_stage.name if current_stage and hasattr(current_stage, 'name') else "",
                        'workflow_name': getattr(self.flowchart, 'current_workflow_name', '')
                    }
                    
                    if current_state != last_state:
                        self._callback_mudanca_flowchart()
                        last_state = current_state.copy()
                    
                    time.sleep(10.0)  # Poll every 10 seconds to reduce WebView loading indicators
                    
                except Exception as e:
                    if hasattr(self, 'logger'):
                        self.logger.error(f"Erro no polling do flowchart: {str(e)}")
                    break
        
        thread = threading.Thread(target=poll_flowchart, daemon=True)
        thread.start()
    
    def _iniciar_polling_notifications(self) -> None:
        """Start polling for notifications changes if callbacks not supported."""
        import threading
        import time
        
        def poll_notifications():
            last_state = None
            while hasattr(self, 'sync_manager') and self.sync_manager:
                try:
                    notifications_list = getattr(self.notifications, 'notifications', [])
                    current_state = {
                        'total': len(notifications_list),
                        'unread': len([n for n in notifications_list if not getattr(n, 'read', True)]),
                        'last_notification': getattr(self.notifications, 'last_notification_text', None)
                    }
                    
                    if current_state != last_state:
                        self._callback_mudanca_notifications()
                        last_state = current_state.copy()
                    
                    time.sleep(15.0)  # Poll every 15 seconds to reduce WebView loading indicators
                    
                except Exception as e:
                    if hasattr(self, 'logger'):
                        self.logger.error(f"Erro no polling das notificações: {str(e)}")
                    break
        
        thread = threading.Thread(target=poll_notifications, daemon=True)
        thread.start()
    
    def _callback_mudanca_time_tracker(self) -> None:
        """Callback for time tracker changes with throttling."""
        # Throttle to avoid excessive WebView updates
        import time
        current_time = time.time()
        if not hasattr(self, '_last_time_tracker_sync'):
            self._last_time_tracker_sync = 0
        
        if current_time - self._last_time_tracker_sync >= 3.0:  # Minimum 3 seconds between syncs
            self._sincronizar_dados_componente('time_tracker')
            self._last_time_tracker_sync = current_time
    
    def _callback_mudanca_flowchart(self) -> None:
        """Callback for flowchart changes with throttling."""
        # Throttle to avoid excessive WebView updates
        import time
        current_time = time.time()
        if not hasattr(self, '_last_flowchart_sync'):
            self._last_flowchart_sync = 0
        
        if current_time - self._last_flowchart_sync >= 5.0:  # Minimum 5 seconds between syncs
            self._sincronizar_dados_componente('flowchart')
            self._last_flowchart_sync = current_time
    
    def _callback_mudanca_notifications(self) -> None:
        """Callback for notifications changes with throttling."""
        # Throttle to avoid excessive WebView updates
        import time
        current_time = time.time()
        if not hasattr(self, '_last_notifications_sync'):
            self._last_notifications_sync = 0
        
        if current_time - self._last_notifications_sync >= 10.0:  # Minimum 10 seconds between syncs
            self._sincronizar_dados_componente('notifications')
            self._last_notifications_sync = current_time
    
    def _callback_mudanca_sidebar(self) -> None:
        """Callback for sidebar changes."""
        self._sincronizar_dados_componente('sidebar')
    
    def _sincronizar_dados_componente(self, componente: str) -> None:
        """
        Synchronize data when a specific component changes.
        Includes throttling to prevent excessive WebView updates.
        
        Args:
            componente: Name of the component that changed
        """
        if not self.sync_manager:
            return
        
        # Global throttle for all component synchronization
        import time
        current_time = time.time()
        if not hasattr(self, '_last_component_sync'):
            self._last_component_sync = {}
        
        if componente in self._last_component_sync:
            if current_time - self._last_component_sync[componente] < 2.0:  # Minimum 2 seconds between syncs per component
                return
        
        try:
            # Increment version to indicate change
            self._incrementar_versao_dados()
            
            # Extract current data
            dados_atuais = self._extrair_dados_para_sincronizacao()
            
            # Update sync manager
            self.sync_manager.atualizar_dados(dados_atuais)
            self._last_component_sync[componente] = current_time
            
            if hasattr(self, 'logger'):
                self.logger.debug(f"Dados sincronizados após mudança em {componente}")
                
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Erro ao sincronizar dados do componente {componente}: {str(e)}")
    
    def _sincronizar_dados_inicial(self) -> None:
        """Perform initial data synchronization."""
        if not self.sync_manager:
            return
        
        try:
            dados_iniciais = self._extrair_dados_para_sincronizacao()
            self.sync_manager.atualizar_dados(dados_iniciais)
            
            if hasattr(self, 'logger'):
                self.logger.info("Sincronização inicial de dados concluída")
                
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Erro na sincronização inicial: {str(e)}")
    
    def _callback_atualizacao_webview(self, dados: dict) -> None:
        """
        Callback called when data changes and WebView needs to be updated.
        Includes throttling to prevent excessive updates that cause loading indicators.
        
        Args:
            dados: Updated data dictionary
        """
        if not self.webview:
            return
        
        # Throttle WebView updates to prevent loading indicator loops
        import time
        current_time = time.time()
        if not hasattr(self, '_last_webview_update'):
            self._last_webview_update = 0
        
        if current_time - self._last_webview_update < 5.0:  # Minimum 5 seconds between WebView updates
            return
        
        try:
            # Execute JavaScript to update WebView with new data
            js_code = f"""
            if (window.updateData) {{
                window.updateData({json.dumps(dados)});
            }} else if (window.syncData) {{
                window.syncData({json.dumps(dados)});
            }} else {{
                console.log('Dados atualizados:', {json.dumps(dados)});
            }}
            """
            
            self.webview.executar_javascript(js_code)
            self._last_webview_update = current_time
            
            if hasattr(self, 'logger'):
                self.logger.debug("WebView atualizado com novos dados")
                
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Erro ao atualizar WebView: {str(e)}")
    
    def _callback_erro_sincronizacao(self, mensagem: str, codigo: str) -> None:
        """
        Callback called when synchronization error occurs.
        
        Args:
            mensagem: Error message
            codigo: Error code
        """
        if hasattr(self, 'logger'):
            self.logger.error(f"Erro de sincronização [{codigo}]: {mensagem}")
        
        # Show error to user if page is available
        if self.page and hasattr(self.page, 'show_snack_bar'):
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Erro de sincronização: {mensagem}"),
                    duration=3000
                )
            )
    
    def atualizar_dados_webview(self, dados: dict) -> None:
        """
        Manually update WebView with specific data.
        
        Args:
            dados: Data dictionary to send to WebView
        """
        if self.sync_manager:
            try:
                self.sync_manager.atualizar_dados(dados)
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.error(f"Erro ao atualizar dados do WebView: {str(e)}")
        else:
            # Direct update if sync manager not available
            self._callback_atualizacao_webview(dados)
    
    def obter_estado_sincronizacao(self) -> dict:
        """
        Get current synchronization state.
        
        Returns:
            Dictionary with synchronization state information
        """
        if not self.sync_manager:
            return {
                'ativo': False,
                'erro': 'Sistema de sincronização não inicializado'
            }
        
        try:
            estado = self.sync_manager.obter_estado_sincronizacao()
            return {
                'ativo': estado.status.value != 'inativo',
                'status': estado.status.value,
                'ultima_atualizacao': estado.ultima_atualizacao.isoformat() if estado.ultima_atualizacao else None,
                'versao_atual': estado.versao_atual,
                'total_sincronizacoes': estado.total_sincronizacoes,
                'taxa_sucesso': estado.calcular_taxa_sucesso(),
                'ultimo_erro': estado.ultimo_erro
            }
        except Exception as e:
            return {
                'ativo': False,
                'erro': f'Erro ao obter estado: {str(e)}'
            }