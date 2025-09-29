import flet as ft
from typing import Optional
from views.components.top_sidebar_container import TopSidebarContainer
from views.components.modern_sidebar import ModernSidebar
from services.time_tracking_service import TimeTrackingService
from services.workflow_service import WorkflowService
from services.notification_service import NotificationService

class MainView(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.route = "/"
        self.page.padding = 2  # Padding mínimo

        # --- State ---
        self.sidebar_expanded = True
        self.sidebar_texts = [] # List to hold all text controls that toggle visibility
        
        # --- Enhanced Components Flag ---
        self.use_enhanced_components = True  # Flag to enable/disable enhanced components
        
        # --- Initialize Services ---
        self.time_tracking_service = TimeTrackingService()
        self.workflow_service = WorkflowService()
        self.notification_service = NotificationService()
        
        # --- Initialize Web Server ---
        self.web_server_manager = None
        self.web_server_url = None
        if self.use_enhanced_components:
            self._initialize_web_server()
        
        # --- Enhanced Components ---
        self.top_sidebar_container: Optional[TopSidebarContainer] = None
        self.modern_sidebar: Optional[ModernSidebar] = None

        # --- Helper Methods ---
        def create_nav_item(icon, text_value, selected=False, is_button=False, is_link=False):
            # Create the Text control and add it to our list
            text_control = ft.Text(text_value, visible=self.sidebar_expanded)
            self.sidebar_texts.append(text_control)

            controls = [ft.Icon(icon), text_control]
            if is_link:
                controls.append(ft.Icon('open_in_new', size=16))
            
            return ft.Container(
                ft.Row(controls, spacing=15),
                bgcolor='primary' if selected else ('surface_variant' if is_button else None),
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                border_radius=ft.border_radius.all(20),
            )

        def create_section_header(text_value, expanded, on_click):
            # Create the Text control and add it to our list
            text_control = ft.Text(text_value, weight="bold", visible=self.sidebar_expanded)
            self.sidebar_texts.append(text_control)
            
            icon = 'arrow_drop_up' if expanded else 'arrow_drop_down'
            return ft.Row(
                [
                    text_control,
                    ft.IconButton(icon=icon, on_click=on_click, data=text_value.lower()),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                height=40,
            )

        # --- Top Bar ---
        if self.use_enhanced_components:
            # Enhanced top sidebar container with integrated components
            self.top_sidebar_container = TopSidebarContainer(
                page=self.page,
                time_tracking_service=self.time_tracking_service,
                workflow_service=self.workflow_service,
                notification_service=self.notification_service,
                habilitar_webview=bool(self.web_server_url),  # Habilitar WebView apenas se servidor iniciou
                url_servidor_web=self.web_server_url  # URL do servidor web iniciado
            )
            # Garantir que TopBar ocupe toda largura disponível
            self.top_sidebar_container.expand = True
            self.top_bar_left = self.top_sidebar_container
        else:
            # Original top bar for fallback
            self.top_bar_left = ft.Container(
                height=48,
                bgcolor='rgba(255, 255, 255, 0.03)',
                border_radius=ft.border_radius.all(10),
                padding=ft.padding.symmetric(horizontal=20),
                content=ft.Row([ft.Text("Painel", weight="bold")])
            )
        


        # --- Sidebar Content ---
        if self.use_enhanced_components:
            # Enhanced modern sidebar
            self.modern_sidebar = ModernSidebar(
                page=self.page,
                on_navigation=self._handle_navigation
            )
            self.sidebar_container = self.modern_sidebar
        else:
            # Original sidebar for fallback
            self.nav_items = {
                "studio_header": create_section_header("Atividades", True, self.toggle_section),
                "studio_items": ft.Column([
                    create_nav_item("chat_bubble_outline", "Chat"),
                    create_nav_item("stream", "Stream"),
                    create_nav_item("photo_library_outlined", "Generate media"),
                    create_nav_item("construction_outlined", "Build", selected=True),
                ], spacing=4, tight=True),

                "history_header": create_section_header("Arquivos", False, self.toggle_section),
                "history_items": ft.Column([], spacing=4, tight=True, visible=False),

                "dashboard_header": create_section_header("Dashboard", False, self.toggle_section),
                "dashboard_items": ft.Column([], spacing=4, tight=True, visible=False),

                "doc_item": create_nav_item("description_outlined", "Vídeos", is_link=True),
            }

            # Create bottom items and add their texts to the list
            bottom_text_1 = ft.Text("Google AI models may make mistakes...", size=10, color='on_surface_variant', visible=self.sidebar_expanded)
            self.sidebar_texts.append(bottom_text_1)
            # We need to manually create the text for the account row to add it to the list
            account_text = ft.Text("6331683@gmail.c...", visible=self.sidebar_expanded)
            self.sidebar_texts.append(account_text)
            
            self.bottom_items = ft.Column([
                bottom_text_1,
                create_nav_item("key_outlined", "Get API key", is_button=True),
                create_nav_item("settings_outlined", "Configurações"),
                ft.Row([ft.Icon('account_circle'), account_text], spacing=15)
            ], spacing=10)

            # --- Main Title for Sidebar ---
            kairos_title = ft.Text("Kairos", weight="bold", size=18, visible=self.sidebar_expanded)
            self.sidebar_texts.append(kairos_title)

            # --- Structures ---
            sidebar_content_column = ft.Column([
                ft.Row(
                    [
                        kairos_title,
                        ft.IconButton(icon='menu', on_click=self.toggle_sidebar),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Column(
                    controls=list(self.nav_items.values()),
                    expand=True,
                    spacing=0,
                    tight=True,
                ),
                self.bottom_items
            ])

            # This is the animating container for the sidebar
            self.sidebar_container = ft.Container(
                width=350,  # Largura muito aumentada
                padding=ft.padding.symmetric(vertical=8, horizontal=12),  # Padding reduzido
                bgcolor=None,  # Remove fundo
                border_radius=None,  # Remove bordas
                animate=ft.Animation(300, "ease"),
                content=sidebar_content_column,
                expand=True,
            )

        self.main_content = ft.Container(
            expand=True,
            content=ft.Column(
                [ft.Text("Bem-vindo à tela principal!", size=20)],
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            bgcolor=None,  # Remove fundo
            border_radius=None,  # Remove bordas
            padding=12  # Padding reduzido
        )
        
        # --- Final Page Layout ---
        # Sidebar apenas com navegação (sem top bar)
        if self.use_enhanced_components:
            # Use the modern sidebar's width management - muito aumentada
            self.animating_sidebar_container = ft.Container(
                width=400,  # Largura muito aumentada
                animate=ft.Animation(300, "ease"),
                content=self.sidebar_container
            )
        else:
            # Original width for fallback - muito aumentada
            self.animating_sidebar_container = ft.Container(
                width=350,  # Largura muito aumentada
                animate=ft.Animation(300, "ease"),
                content=self.sidebar_container
            )

        # Área principal com espaçamento mínimo
        main_column = ft.Column(
            expand=True,
            spacing=2,  # Espaçamento mínimo
            controls=[
                self.main_content
            ]
        )

        self.controls = [
            ft.Column(
                expand=True,
                spacing=2,  # Espaçamento mínimo
                controls=[
                    # Top bar no topo da aplicação (Time | WebView | Tema+Notificações)
                    self.top_bar_left,
                    # Layout principal com sidebar e conteúdo
                    ft.Row(
                        expand=True,
                        spacing=4,  # Espaçamento mínimo
                        controls=[
                            self.animating_sidebar_container,
                            main_column
                        ]
                    )
                ]
            )
        ]

    def toggle_sidebar(self, e=None):
        """Toggle sidebar visibility and update layout accordingly."""
        self.sidebar_expanded = not self.sidebar_expanded
        
        if self.use_enhanced_components and self.modern_sidebar:
            # Enhanced sidebar handles its own toggle
            self.modern_sidebar._toggle_sidebar(e)
            # Ajustar largura baseado no estado
            new_width = self.modern_sidebar.width if self.sidebar_expanded else 60
            self.animating_sidebar_container.width = new_width
            
            # Update top sidebar container layout
            if self.top_sidebar_container:
                self.top_sidebar_container.update_layout(self.sidebar_expanded)
        else:
            # Original sidebar behavior with much improved widths
            if self.sidebar_expanded:
                self.animating_sidebar_container.width = 400  # Largura muito expandida
            else:
                self.animating_sidebar_container.width = 60   # Largura colapsada (muito compacta)
            
            # Simple, robust loop to toggle visibility
            for text_control in self.sidebar_texts:
                text_control.visible = self.sidebar_expanded
        
        # Show feedback message
        status = "expandida" if self.sidebar_expanded else "recolhida"
        if hasattr(self.page, 'show_snack_bar'):
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Sidebar {status}"),
                    duration=1000
                )
            )
        
        self.page.update()

    def toggle_section(self, e):
        if not self.use_enhanced_components:
            # Original section toggle behavior
            section_name = e.control.data
            header = self.nav_items[f"{section_name}_header"]
            items = self.nav_items[f"{section_name}_items"]
            
            items.visible = not items.visible
            header.controls[1].icon = 'arrow_drop_up' if items.visible else 'arrow_drop_down'
            self.page.update()
    
    def _handle_navigation(self, route: str):
        """Handle navigation from the modern sidebar"""
        # Update main content based on route
        self._update_main_content(route)
        
        # Show navigation feedback
        if self.page:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Navigated to: {route}"),
                    duration=2000
                )
            )
    
    def _update_main_content(self, route: str):
        """Update the main content area based on the selected route"""
        # This is where you would implement route-specific content
        # For now, we'll just update the welcome message
        route_content_map = {
            "time-tracker": "Time Tracker - Track your activities and manage time efficiently",
            "time-history": "Time History - View your past time tracking records",
            "time-analytics": "Time Analytics - Analyze your productivity patterns",
            "activity-categories": "Activity Categories - Manage your activity types",
            "workflow-overview": "Workflow Overview - Monitor project workflow stages",
            "active-projects": "Active Projects - View and manage ongoing projects",
            "approval-queue": "Approval Queue - Review items pending approval",
            "completed-projects": "Completed Projects - Browse finished projects",
            "video-library": "Video Library - Access educational content",
            "saved-videos": "Saved Videos - Your bookmarked video content",
            "trending-topics": "Trending Topics - Popular educational topics",
            "external-resources": "External Resources - Links to external learning materials",
            "api-key": "API Key Management - Configure your API access",
            "settings": "Settings - Configure application preferences"
        }
        
        content_text = route_content_map.get(route, "Welcome to Kairos!")
        
        self.main_content.content = ft.Column(
            [
                ft.Text(content_text, size=20, weight=ft.FontWeight.BOLD),
                ft.Text(f"Route: /{route}", size=14, color='on_surface_variant')
            ],
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        
        if self.page:
            self.page.update()
    
    def get_enhanced_components(self):
        """Get references to enhanced components for external access"""
        return {
            'top_sidebar_container': self.top_sidebar_container,
            'modern_sidebar': self.modern_sidebar,
            'time_tracking_service': self.time_tracking_service,
            'workflow_service': self.workflow_service,
            'notification_service': self.notification_service
        }
    
    def set_enhanced_components_enabled(self, enabled: bool):
        """Enable or disable enhanced components (for testing/fallback)"""
        self.use_enhanced_components = enabled
        # Note: This would require rebuilding the view to take effect
    
    def _initialize_web_server(self):
        """Initialize web server with proper error handling."""
        try:
            from services.web_server.server_manager import WebServerManager
            from services.web_server.models import ConfiguracaoServidorWeb
            
            # Criar configuração com parâmetros corretos
            config = ConfiguracaoServidorWeb(
                porta_preferencial=8080,
                diretorio_html="web_content",
                cors_habilitado=True,
                modo_debug=False
            )
            
            # Validar configuração
            erros = config.validar()
            if erros:
                print(f"Aviso: Configuração do servidor tem problemas: {erros}")
                return
            
            # Inicializar servidor
            self.web_server_manager = WebServerManager(config)
            self.web_server_url = self.web_server_manager.iniciar_servidor()
            # Adicionar cache-busting para forçar reload
            import time
            cache_buster = int(time.time())
            self.web_server_url = f"{self.web_server_url}?v={cache_buster}"
            print(f"Servidor web iniciado em: {self.web_server_url}")
            
        except ImportError as e:
            print(f"Aviso: Módulos do servidor web não encontrados: {e}")
        except AttributeError as e:
            print(f"Aviso: Erro nos parâmetros do servidor web: {e}")
        except Exception as e:
            print(f"Aviso: Não foi possível inicializar servidor web: {e}")
            self.web_server_manager = None
            self.web_server_url = None
    
    def restart_web_server(self):
        """Restart web server to clear cache"""
        if self.web_server_manager:
            try:
                print("Reiniciando servidor web para limpar cache...")
                self.web_server_manager.parar_servidor()
                import time
                time.sleep(1)  # Wait for server to stop
                self.web_server_url = self.web_server_manager.iniciar_servidor()
                # Add cache buster
                cache_buster = int(time.time())
                self.web_server_url = f"{self.web_server_url}?v={cache_buster}"
                print(f"Servidor web reiniciado em: {self.web_server_url}")
                
                # WebView will automatically load the new URL
                    
            except Exception as e:
                print(f"Erro ao reiniciar servidor web: {e}")
    
    def cleanup(self):
        """Clean up resources when view is destroyed"""
        # Stop web server if running
        if self.web_server_manager:
            try:
                self.web_server_manager.parar_servidor()
            except Exception as e:
                print(f"Erro ao parar servidor web: {e}")
            finally:
                self.web_server_manager = None
                self.web_server_url = None
        
        # Clean up enhanced components
        if self.top_sidebar_container and hasattr(self.top_sidebar_container, 'cleanup'):
            self.top_sidebar_container.cleanup()
    
    def add_test_notification(self):
        """Add a test notification (for demonstration)"""
        if self.top_sidebar_container:
            self.top_sidebar_container.add_test_notification()
    
    def advance_workflow_stage(self, stage_name: str) -> bool:
        """Advance workflow to a specific stage"""
        if self.top_sidebar_container:
            return self.top_sidebar_container.advance_workflow_stage(stage_name)
        return False
    
    def toggle_topbar(self) -> None:
        """Toggle TopBar expansion to gain more area below."""
        if self.top_sidebar_container:
            self.top_sidebar_container.toggle_topbar_expansion()
    
    def is_topbar_expanded(self) -> bool:
        """Check if TopBar is currently expanded."""
        if self.top_sidebar_container:
            return self.top_sidebar_container.is_topbar_expanded()
        return True
