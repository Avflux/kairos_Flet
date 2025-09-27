# Exemplos de Uso - Interface Moderna Kairos

## Visão Geral

Este documento fornece exemplos práticos de como usar os componentes da interface moderna do Kairos em diferentes cenários de desenvolvimento e uso.

## Índice

1. [Configuração Inicial](#configuração-inicial)
2. [Exemplos Básicos](#exemplos-básicos)
3. [Integração Completa](#integração-completa)
4. [Personalização Avançada](#personalização-avançada)
5. [Casos de Uso Específicos](#casos-de-uso-específicos)
6. [Troubleshooting](#troubleshooting)

---

## Configuração Inicial

### Instalação de Dependências

```bash
# Instalar dependências principais
pip install flet
pip install pytest
pip install coverage

# Para desenvolvimento
pip install pytest-mock
pip install pytest-cov
```

### Estrutura de Projeto

```
projeto/
├── views/
│   ├── components/
│   │   ├── time_tracker_widget.py
│   │   ├── flowchart_widget.py
│   │   ├── notification_center.py
│   │   ├── modern_sidebar.py
│   │   └── top_sidebar_container.py
│   └── main_view.py
├── services/
│   ├── time_tracking_service.py
│   ├── notification_service.py
│   └── workflow_service.py
├── models/
│   ├── activity.py
│   ├── notification.py
│   └── workflow_state.py
└── tests/
    ├── test_comprehensive_ui_components.py
    ├── test_performance_benchmarks.py
    └── test_user_interactions.py
```

---

## Exemplos Básicos

### 1. Aplicação Mínima com Rastreador de Tempo

```python
import flet as ft
from views.components.time_tracker_widget import TimeTrackerWidget
from models.activity import Activity

def main(page: ft.Page):
    page.title = "Kairos - Rastreador de Tempo"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Criar o rastreador de tempo
    time_tracker = TimeTrackerWidget(page)
    
    # Adicionar algumas atividades pré-definidas
    activities = [
        Activity("Desenvolvimento Frontend", "Desenvolvimento"),
        Activity("Reunião de Equipe", "Reuniões"),
        Activity("Documentação", "Documentação"),
        Activity("Testes e QA", "Qualidade")
    ]
    
    for activity in activities:
        time_tracker.add_activity(activity)
    
    # Layout simples
    page.add(
        ft.Container(
            content=ft.Column([
                ft.Text("Rastreador de Tempo Kairos", 
                       style=ft.TextStyle(size=24, weight=ft.FontWeight.BOLD)),
                ft.Divider(),
                time_tracker
            ]),
            padding=20
        )
    )
    
    page.update()

ft.app(target=main)
```

### 2. Centro de Notificações Standalone

```python
import flet as ft
from views.components.notification_center import NotificationCenter
from models.notification import NotificationType

def main(page: ft.Page):
    page.title = "Centro de Notificações"
    
    # Criar centro de notificações
    notification_center = NotificationCenter(page)
    
    # Função para adicionar notificação de exemplo
    def add_sample_notification(notification_type):
        titles = {
            NotificationType.INFO: "Informação",
            NotificationType.SUCCESS: "Sucesso",
            NotificationType.WARNING: "Aviso",
            NotificationType.ERROR: "Erro"
        }
        
        messages = {
            NotificationType.INFO: "Esta é uma notificação informativa",
            NotificationType.SUCCESS: "Operação realizada com sucesso",
            NotificationType.WARNING: "Atenção: verifique esta situação",
            NotificationType.ERROR: "Ocorreu um erro no sistema"
        }
        
        notification_center.add_notification(
            titles[notification_type],
            messages[notification_type],
            notification_type
        )
    
    # Botões para testar diferentes tipos de notificação
    buttons = ft.Row([
        ft.ElevatedButton(
            "Info", 
            on_click=lambda _: add_sample_notification(NotificationType.INFO),
            bgcolor=ft.colors.BLUE
        ),
        ft.ElevatedButton(
            "Sucesso", 
            on_click=lambda _: add_sample_notification(NotificationType.SUCCESS),
            bgcolor=ft.colors.GREEN
        ),
        ft.ElevatedButton(
            "Aviso", 
            on_click=lambda _: add_sample_notification(NotificationType.WARNING),
            bgcolor=ft.colors.ORANGE
        ),
        ft.ElevatedButton(
            "Erro", 
            on_click=lambda _: add_sample_notification(NotificationType.ERROR),
            bgcolor=ft.colors.RED
        )
    ])
    
    # Layout
    page.add(
        ft.Column([
            ft.Text("Centro de Notificações - Teste", size=20),
            buttons,
            ft.Divider(),
            notification_center
        ])
    )
    
    page.update()

ft.app(target=main)
```

### 3. Fluxograma de Workflow Interativo

```python
import flet as ft
from views.components.flowchart_widget import FlowchartWidget

def main(page: ft.Page):
    page.title = "Fluxograma de Workflow"
    
    # Criar widget de fluxograma
    flowchart = FlowchartWidget(page)
    
    # Criar workflow de exemplo
    workflow_id = "exemplo_001"
    flowchart.create_workflow(workflow_id, "Projeto de Exemplo")
    
    # Função para mostrar informações do workflow
    def show_workflow_info():
        current_stage = flowchart.get_current_stage(workflow_id)
        progress = flowchart.get_progress_percentage(workflow_id)
        
        info_text.value = f"""
        Estágio Atual: {current_stage.name if current_stage else 'N/A'}
        Progresso: {progress:.1f}%
        Status: {current_stage.status.value if current_stage else 'N/A'}
        """
        page.update()
    
    # Botões de controle
    def advance_stage():
        stages = ["Verificação", "Aprovação", "Emissão", "Comentários Cliente"]
        current = flowchart.get_current_stage(workflow_id)
        if current and current.name in stages:
            next_index = stages.index(current.name) + 1
            if next_index < len(stages):
                flowchart.advance_stage(workflow_id, stages[next_index])
        show_workflow_info()
    
    def reset_workflow():
        flowchart.reset_workflow(workflow_id)
        show_workflow_info()
    
    # Elementos da interface
    info_text = ft.Text("", size=14)
    
    controls = ft.Row([
        ft.ElevatedButton("Avançar Estágio", on_click=lambda _: advance_stage()),
        ft.ElevatedButton("Resetar", on_click=lambda _: reset_workflow()),
        ft.ElevatedButton("Atualizar Info", on_click=lambda _: show_workflow_info())
    ])
    
    # Layout
    page.add(
        ft.Column([
            ft.Text("Fluxograma de Workflow Interativo", size=20),
            controls,
            ft.Divider(),
            flowchart,
            ft.Divider(),
            ft.Text("Informações do Workflow:", weight=ft.FontWeight.BOLD),
            info_text
        ])
    )
    
    # Mostrar informações iniciais
    show_workflow_info()

ft.app(target=main)
```

---

## Integração Completa

### Aplicação Completa com Todos os Componentes

```python
import flet as ft
from views.components.top_sidebar_container import TopSidebarContainer
from views.components.modern_sidebar import ModernSidebar
from models.activity import Activity
from models.notification import NotificationType

class KairosApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.setup_page()
        self.create_components()
        self.setup_callbacks()
        self.create_layout()
        
    def setup_page(self):
        """Configurar propriedades da página."""
        self.page.title = "Kairos - Interface Moderna Completa"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0
        self.page.spacing = 0
        
    def create_components(self):
        """Criar todos os componentes principais."""
        # Componentes principais
        self.sidebar = ModernSidebar(self.page)
        self.top_container = TopSidebarContainer(self.page)
        
        # Área de conteúdo principal
        self.main_content = ft.Container(
            content=ft.Column([
                ft.Text("Área de Conteúdo Principal", 
                       style=ft.TextStyle(size=24, weight=ft.FontWeight.BOLD)),
                ft.Text("Aqui seria exibido o conteúdo específico de cada seção"),
                ft.Divider(),
                self.create_dashboard_content()
            ]),
            padding=20,
            expand=True,
            bgcolor=ft.colors.GREY_50
        )
        
    def create_dashboard_content(self):
        """Criar conteúdo do dashboard."""
        # Estatísticas rápidas
        stats = ft.Row([
            self.create_stat_card("Tempo Hoje", "2h 30m", ft.colors.BLUE),
            self.create_stat_card("Projetos Ativos", "3", ft.colors.GREEN),
            self.create_stat_card("Tarefas Pendentes", "7", ft.colors.ORANGE),
            self.create_stat_card("Concluídas", "12", ft.colors.PURPLE)
        ])
        
        # Atividades recentes
        recent_activities = ft.Container(
            content=ft.Column([
                ft.Text("Atividades Recentes", 
                       style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD)),
                ft.ListTile(
                    leading=ft.Icon(ft.icons.CODE),
                    title=ft.Text("Desenvolvimento Frontend"),
                    subtitle=ft.Text("45 minutos"),
                    trailing=ft.Text("Concluído")
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.icons.MEETING_ROOM),
                    title=ft.Text("Reunião de Equipe"),
                    subtitle=ft.Text("30 minutos"),
                    trailing=ft.Text("Concluído")
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.icons.DESCRIPTION),
                    title=ft.Text("Documentação"),
                    subtitle=ft.Text("Em andamento"),
                    trailing=ft.Text("Ativo")
                )
            ]),
            padding=20,
            bgcolor=ft.colors.WHITE,
            border_radius=10,
            margin=ft.margin.only(top=20)
        )
        
        return ft.Column([stats, recent_activities])
        
    def create_stat_card(self, title, value, color):
        """Criar card de estatística."""
        return ft.Container(
            content=ft.Column([
                ft.Text(value, 
                       style=ft.TextStyle(size=24, weight=ft.FontWeight.BOLD, color=color)),
                ft.Text(title, style=ft.TextStyle(size=12, color=ft.colors.GREY_600))
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20,
            bgcolor=ft.colors.WHITE,
            border_radius=10,
            width=150,
            height=100
        )
        
    def setup_callbacks(self):
        """Configurar callbacks entre componentes."""
        # Callback para toggle da sidebar
        def on_sidebar_toggle():
            is_expanded = self.sidebar.toggle_expansion()
            self.top_container.update_layout(sidebar_expanded=is_expanded)
            
        # Callback para navegação
        def on_navigation(section, item):
            self.top_container.notifications.add_notification(
                "Navegação",
                f"Acessando: {section} > {item}",
                NotificationType.INFO
            )
            self.update_main_content(section, item)
            
        # Callback para rastreamento de tempo
        def on_time_tracking_start(activity):
            self.top_container.notifications.add_notification(
                "Rastreamento Iniciado",
                f"Iniciado: {activity.name}",
                NotificationType.SUCCESS
            )
            
        def on_time_tracking_stop(time_entry):
            duration_str = str(time_entry.duration).split('.')[0]
            self.top_container.notifications.add_notification(
                "Tempo Registrado",
                f"Registrado {duration_str}",
                NotificationType.SUCCESS
            )
            
        # Conectar callbacks
        self.sidebar.on_toggle = on_sidebar_toggle
        self.sidebar.on_navigation = on_navigation
        self.top_container.time_tracker.on_tracking_start = on_time_tracking_start
        self.top_container.time_tracker.on_tracking_stop = on_time_tracking_stop
        
    def update_main_content(self, section, item):
        """Atualizar conteúdo principal baseado na navegação."""
        content_map = {
            "Gerenciamento de Tempo": {
                "Timer Ativo": "Interface do Timer Ativo",
                "Relatórios": "Relatórios de Tempo",
                "Atividades": "Gerenciamento de Atividades"
            },
            "Fluxos de Projeto": {
                "Workflows Ativos": "Lista de Workflows Ativos",
                "Templates": "Templates de Workflow",
                "Histórico": "Histórico de Projetos"
            },
            "Vídeos Educacionais": {
                "Biblioteca": "Biblioteca de Vídeos",
                "Favoritos": "Vídeos Favoritos",
                "Progresso": "Progresso de Aprendizado"
            }
        }
        
        content_text = content_map.get(section, {}).get(item, "Conteúdo não encontrado")
        
        self.main_content.content = ft.Column([
            ft.Text(f"{section} > {item}", 
                   style=ft.TextStyle(size=24, weight=ft.FontWeight.BOLD)),
            ft.Text(content_text, size=16),
            ft.Divider(),
            ft.Text("Aqui seria exibido o conteúdo específico desta seção.")
        ])
        
        self.page.update()
        
    def create_layout(self):
        """Criar layout principal da aplicação."""
        # Layout principal com sidebar e conteúdo
        main_layout = ft.Row([
            self.sidebar,
            ft.Column([
                self.top_container,
                self.main_content
            ], expand=True)
        ], expand=True, spacing=0)
        
        self.page.add(main_layout)
        
        # Configurar layout inicial
        self.top_container.update_layout(sidebar_expanded=True)
        
        # Adicionar algumas atividades de exemplo
        sample_activities = [
            Activity("Desenvolvimento Frontend", "Desenvolvimento"),
            Activity("Reunião de Equipe", "Reuniões"),
            Activity("Documentação", "Documentação"),
            Activity("Testes e QA", "Qualidade"),
            Activity("Planejamento", "Gestão")
        ]
        
        for activity in sample_activities:
            self.top_container.time_tracker.add_activity(activity)
            
        # Criar workflow de exemplo
        self.top_container.flowchart.create_workflow("projeto_001", "Projeto Principal")
        
        # Adicionar notificações de boas-vindas
        welcome_notifications = [
            ("Bem-vindo ao Kairos!", "Sistema iniciado com sucesso", NotificationType.SUCCESS),
            ("Dica", "Use o rastreador de tempo para registrar suas atividades", NotificationType.INFO),
            ("Lembrete", "Não esqueça de avançar os workflows dos seus projetos", NotificationType.INFO)
        ]
        
        for title, message, ntype in welcome_notifications:
            self.top_container.notifications.add_notification(title, message, ntype)
            
        self.page.update()

def main(page: ft.Page):
    app = KairosApp(page)

ft.app(target=main)
```

---

## Personalização Avançada

### Tema Personalizado

```python
import flet as ft
from views.components.design_system import ColorPalette, Typography

# Definir tema personalizado
CUSTOM_THEME = {
    "primary": "#6366f1",
    "secondary": "#8b5cf6", 
    "accent": "#f59e0b",
    "success": "#10b981",
    "warning": "#f59e0b",
    "error": "#ef4444",
    "info": "#3b82f6",
    "background": "#0f172a",
    "surface": "#1e293b",
    "text_primary": "#f1f5f9",
    "text_secondary": "#94a3b8"
}

def apply_dark_theme(page: ft.Page):
    """Aplicar tema escuro personalizado."""
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = CUSTOM_THEME["background"]
    
    # Personalizar cores globalmente
    ColorPalette.PRIMARY = CUSTOM_THEME["primary"]
    ColorPalette.SECONDARY = CUSTOM_THEME["secondary"]
    ColorPalette.BACKGROUND = CUSTOM_THEME["background"]
    ColorPalette.SURFACE = CUSTOM_THEME["surface"]
    ColorPalette.TEXT_PRIMARY = CUSTOM_THEME["text_primary"]

def create_themed_component(page: ft.Page):
    """Criar componente com tema personalizado."""
    return ft.Container(
        content=ft.Column([
            ft.Text("Componente Temático", 
                   style=ft.TextStyle(
                       size=Typography.HEADING_2["size"],
                       weight=ft.FontWeight.BOLD,
                       color=CUSTOM_THEME["text_primary"]
                   )),
            ft.Text("Este componente usa o tema personalizado",
                   style=ft.TextStyle(color=CUSTOM_THEME["text_secondary"]))
        ]),
        bgcolor=CUSTOM_THEME["surface"],
        padding=20,
        border_radius=10,
        border=ft.border.all(1, CUSTOM_THEME["primary"])
    )
```

### Componente Personalizado

```python
import flet as ft
from views.components.design_system import DesignSystem

class CustomDashboardWidget(ft.Container):
    """Widget personalizado para dashboard."""
    
    def __init__(self, page: ft.Page, title: str, data: list):
        super().__init__()
        self.page = page
        self.title = title
        self.data = data
        self.design_system = DesignSystem()
        
        self.setup_styling()
        self.create_content()
        
    def setup_styling(self):
        """Configurar estilização usando sistema de design."""
        self.bgcolor = self.design_system.colors.SURFACE
        self.border_radius = self.design_system.border_radius.MD
        self.padding = self.design_system.spacing.LG
        self.border = ft.border.all(1, self.design_system.colors.SECONDARY)
        
    def create_content(self):
        """Criar conteúdo do widget."""
        # Cabeçalho
        header = ft.Row([
            ft.Text(self.title, 
                   style=ft.TextStyle(
                       size=self.design_system.typography.HEADING_3["size"],
                       weight=ft.FontWeight.BOLD
                   )),
            ft.IconButton(
                icon=ft.icons.REFRESH,
                on_click=self.refresh_data,
                tooltip="Atualizar dados"
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        # Lista de dados
        data_list = ft.Column([
            self.create_data_item(item) for item in self.data
        ])
        
        self.content = ft.Column([header, ft.Divider(), data_list])
        
    def create_data_item(self, item):
        """Criar item de dados."""
        return ft.ListTile(
            leading=ft.Icon(item.get("icon", ft.icons.CIRCLE)),
            title=ft.Text(item.get("title", "Item")),
            subtitle=ft.Text(item.get("subtitle", "")),
            trailing=ft.Text(item.get("value", ""))
        )
        
    def refresh_data(self, e):
        """Atualizar dados do widget."""
        # Lógica de atualização aqui
        self.page.show_snack_bar(
            ft.SnackBar(content=ft.Text(f"{self.title} atualizado!"))
        )

# Uso do componente personalizado
def main(page: ft.Page):
    sample_data = [
        {"icon": ft.icons.TIMER, "title": "Tempo Hoje", "value": "4h 30m"},
        {"icon": ft.icons.TASK_ALT, "title": "Tarefas Concluídas", "value": "8"},
        {"icon": ft.icons.TRENDING_UP, "title": "Produtividade", "value": "+15%"}
    ]
    
    dashboard_widget = CustomDashboardWidget(page, "Resumo Diário", sample_data)
    
    page.add(dashboard_widget)
    page.update()

ft.app(target=main)
```

---

## Casos de Uso Específicos

### 1. Aplicação para Freelancers

```python
import flet as ft
from datetime import datetime, timedelta
from views.components.time_tracker_widget import TimeTrackerWidget
from views.components.notification_center import NotificationCenter
from models.activity import Activity
from models.notification import NotificationType

class FreelancerTimeTracker:
    """Aplicação específica para freelancers."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.setup_freelancer_app()
        
    def setup_freelancer_app(self):
        """Configurar aplicação para freelancers."""
        self.page.title = "Kairos Freelancer - Controle de Tempo"
        
        # Componentes principais
        self.time_tracker = TimeTrackerWidget(self.page)
        self.notifications = NotificationCenter(self.page)
        
        # Projetos/clientes do freelancer
        self.setup_client_projects()
        
        # Metas diárias
        self.daily_goal = timedelta(hours=8)
        self.setup_daily_tracking()
        
        # Layout específico para freelancer
        self.create_freelancer_layout()
        
    def setup_client_projects(self):
        """Configurar projetos de clientes."""
        client_projects = [
            Activity("Cliente A - Website", "Desenvolvimento Web"),
            Activity("Cliente B - App Mobile", "Desenvolvimento Mobile"),
            Activity("Cliente C - Consultoria", "Consultoria"),
            Activity("Administração", "Administrativo"),
            Activity("Prospecção", "Vendas")
        ]
        
        for project in client_projects:
            self.time_tracker.add_activity(project)
            
    def setup_daily_tracking(self):
        """Configurar rastreamento diário."""
        def check_daily_progress():
            daily_total = self.time_tracker.time_service.get_daily_total()
            progress_percentage = (daily_total.total_seconds() / self.daily_goal.total_seconds()) * 100
            
            if progress_percentage >= 100:
                self.notifications.add_notification(
                    "Meta Diária Atingida! 🎉",
                    "Parabéns! Você atingiu sua meta de 8 horas hoje.",
                    NotificationType.SUCCESS
                )
            elif progress_percentage >= 75:
                self.notifications.add_notification(
                    "Quase lá! 💪",
                    f"Você já completou {progress_percentage:.0f}% da sua meta diária.",
                    NotificationType.INFO
                )
                
        # Verificar progresso a cada hora
        self.time_tracker.on_hour_completed = check_daily_progress
        
    def create_freelancer_layout(self):
        """Criar layout específico para freelancer."""
        # Cabeçalho com informações do dia
        header = self.create_daily_header()
        
        # Área principal com timer
        main_area = ft.Row([
            ft.Column([
                self.time_tracker,
                self.create_daily_summary()
            ], expand=2),
            ft.Column([
                self.notifications,
                self.create_client_summary()
            ], expand=1)
        ])
        
        self.page.add(
            ft.Column([
                header,
                ft.Divider(),
                main_area
            ])
        )
        
    def create_daily_header(self):
        """Criar cabeçalho com informações do dia."""
        today = datetime.now().strftime("%d/%m/%Y")
        
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("Kairos Freelancer", 
                           style=ft.TextStyle(size=24, weight=ft.FontWeight.BOLD)),
                    ft.Text(f"Hoje: {today}", style=ft.TextStyle(size=14))
                ]),
                ft.Column([
                    ft.Text("Meta Diária: 8h", 
                           style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.Text("Progresso será atualizado automaticamente")
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=20,
            bgcolor=ft.colors.BLUE_50,
            border_radius=10
        )
        
    def create_daily_summary(self):
        """Criar resumo diário."""
        return ft.Container(
            content=ft.Column([
                ft.Text("Resumo do Dia", 
                       style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD)),
                ft.Text("Tempo total: Será calculado automaticamente"),
                ft.Text("Projeto mais trabalhado: Será atualizado"),
                ft.Text("Valor estimado: R$ 0,00")
            ]),
            padding=20,
            bgcolor=ft.colors.GREEN_50,
            border_radius=10,
            margin=ft.margin.only(top=20)
        )
        
    def create_client_summary(self):
        """Criar resumo por cliente."""
        return ft.Container(
            content=ft.Column([
                ft.Text("Tempo por Cliente", 
                       style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD)),
                ft.Text("Cliente A: 0h 0m"),
                ft.Text("Cliente B: 0h 0m"),
                ft.Text("Cliente C: 0h 0m"),
                ft.Text("Administrativo: 0h 0m")
            ]),
            padding=20,
            bgcolor=ft.colors.ORANGE_50,
            border_radius=10,
            margin=ft.margin.only(top=20)
        )

def main(page: ft.Page):
    app = FreelancerTimeTracker(page)
    page.update()

ft.app(target=main)
```

### 2. Dashboard de Equipe

```python
import flet as ft
from views.components.flowchart_widget import FlowchartWidget
from views.components.notification_center import NotificationCenter

class TeamDashboard:
    """Dashboard para gerenciamento de equipe."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.setup_team_dashboard()
        
    def setup_team_dashboard(self):
        """Configurar dashboard de equipe."""
        self.page.title = "Kairos Team - Dashboard da Equipe"
        
        # Componentes
        self.flowchart = FlowchartWidget(self.page)
        self.notifications = NotificationCenter(self.page)
        
        # Dados da equipe
        self.team_members = [
            {"name": "Ana Silva", "role": "Frontend", "status": "Ativo"},
            {"name": "João Santos", "role": "Backend", "status": "Ativo"},
            {"name": "Maria Costa", "role": "Designer", "status": "Ausente"},
            {"name": "Pedro Lima", "role": "QA", "status": "Ativo"}
        ]
        
        # Projetos da equipe
        self.setup_team_projects()
        self.create_team_layout()
        
    def setup_team_projects(self):
        """Configurar projetos da equipe."""
        projects = [
            "projeto_website_cliente_a",
            "projeto_app_mobile_cliente_b", 
            "projeto_sistema_interno"
        ]
        
        for i, project_id in enumerate(projects):
            self.flowchart.create_workflow(project_id, f"Projeto {i+1}")
            
    def create_team_layout(self):
        """Criar layout do dashboard de equipe."""
        # Cabeçalho da equipe
        header = ft.Container(
            content=ft.Row([
                ft.Text("Dashboard da Equipe", 
                       style=ft.TextStyle(size=24, weight=ft.FontWeight.BOLD)),
                ft.Text(f"Membros ativos: {len([m for m in self.team_members if m['status'] == 'Ativo'])}")
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=20,
            bgcolor=ft.colors.PURPLE_50,
            border_radius=10
        )
        
        # Área principal
        main_content = ft.Row([
            # Coluna esquerda - Projetos
            ft.Column([
                ft.Text("Projetos Ativos", 
                       style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD)),
                self.flowchart,
                self.create_project_summary()
            ], expand=2),
            
            # Coluna direita - Equipe e notificações
            ft.Column([
                self.create_team_status(),
                self.notifications
            ], expand=1)
        ])
        
        self.page.add(
            ft.Column([
                header,
                ft.Divider(),
                main_content
            ])
        )
        
    def create_team_status(self):
        """Criar status da equipe."""
        team_items = []
        for member in self.team_members:
            status_color = ft.colors.GREEN if member["status"] == "Ativo" else ft.colors.RED
            
            team_items.append(
                ft.ListTile(
                    leading=ft.Icon(ft.icons.PERSON, color=status_color),
                    title=ft.Text(member["name"]),
                    subtitle=ft.Text(member["role"]),
                    trailing=ft.Text(member["status"], color=status_color)
                )
            )
            
        return ft.Container(
            content=ft.Column([
                ft.Text("Status da Equipe", 
                       style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD)),
                *team_items
            ]),
            padding=20,
            bgcolor=ft.colors.BLUE_50,
            border_radius=10,
            margin=ft.margin.only(bottom=20)
        )
        
    def create_project_summary(self):
        """Criar resumo de projetos."""
        return ft.Container(
            content=ft.Column([
                ft.Text("Resumo de Projetos", 
                       style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                ft.Text("• Projeto 1: Em desenvolvimento"),
                ft.Text("• Projeto 2: Em revisão"),
                ft.Text("• Projeto 3: Planejamento")
            ]),
            padding=20,
            bgcolor=ft.colors.GREY_50,
            border_radius=10,
            margin=ft.margin.only(top=20)
        )

def main(page: ft.Page):
    dashboard = TeamDashboard(page)
    page.update()

ft.app(target=main)
```

---

## Troubleshooting

### Problemas Comuns e Soluções

#### 1. Erro de Importação de Módulos

```python
# Problema: ModuleNotFoundError
# Solução: Verificar estrutura de diretórios e PYTHONPATH

import sys
import os

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Agora importar os módulos
from views.components.time_tracker_widget import TimeTrackerWidget
```

#### 2. Performance Lenta com Muitas Notificações

```python
# Problema: Interface lenta com muitas notificações
# Solução: Implementar paginação e limpeza automática

class OptimizedNotificationCenter(NotificationCenter):
    def __init__(self, page, max_notifications=50):
        super().__init__(page)
        self.max_notifications = max_notifications
        
    def add_notification(self, title, message, notification_type):
        # Adicionar notificação
        notification = super().add_notification(title, message, notification_type)
        
        # Limpar notificações antigas se exceder o limite
        notifications = self.notification_service.get_notifications()
        if len(notifications) > self.max_notifications:
            oldest = notifications[-10:]  # Remover 10 mais antigas
            for old_notification in oldest:
                self.notification_service.remove_notification(old_notification.id)
                
        return notification
```

#### 3. Timer Não Atualiza Corretamente

```python
# Problema: Timer não atualiza em tempo real
# Solução: Verificar thread de atualização

import threading
import time

class FixedTimeTracker(TimeTrackerWidget):
    def __init__(self, page):
        super().__init__(page)
        self.update_thread = None
        self.should_update = False
        
    def start_tracking(self, activity):
        result = super().start_tracking(activity)
        
        # Iniciar thread de atualização
        self.should_update = True
        self.update_thread = threading.Thread(target=self._update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        return result
        
    def stop_tracking(self):
        # Parar thread de atualização
        self.should_update = False
        if self.update_thread:
            self.update_thread.join(timeout=1)
            
        return super().stop_tracking()
        
    def _update_loop(self):
        """Loop de atualização em thread separada."""
        while self.should_update:
            try:
                self._update_timer_display()
                self.page.update()
                time.sleep(1)
            except Exception as e:
                print(f"Erro na atualização do timer: {e}")
                break
```

#### 4. Layout Quebrado em Telas Pequenas

```python
# Problema: Layout não responsivo
# Solução: Implementar breakpoints adaptativos

class ResponsiveLayout:
    def __init__(self, page):
        self.page = page
        self.current_breakpoint = self.get_breakpoint()
        
    def get_breakpoint(self):
        """Determinar breakpoint atual baseado na largura da página."""
        width = self.page.width or 1200
        
        if width < 576:
            return "xs"
        elif width < 768:
            return "sm"
        elif width < 992:
            return "md"
        elif width < 1200:
            return "lg"
        else:
            return "xl"
            
    def create_responsive_layout(self, components):
        """Criar layout responsivo baseado no breakpoint."""
        breakpoint = self.get_breakpoint()
        
        if breakpoint in ["xs", "sm"]:
            # Layout vertical para telas pequenas
            return ft.Column(components)
        else:
            # Layout horizontal para telas maiores
            return ft.Row(components)
            
    def on_page_resize(self, e):
        """Callback para redimensionamento da página."""
        new_breakpoint = self.get_breakpoint()
        if new_breakpoint != self.current_breakpoint:
            self.current_breakpoint = new_breakpoint
            self.rebuild_layout()
            
    def rebuild_layout(self):
        """Reconstruir layout para novo breakpoint."""
        # Implementar lógica de reconstrução
        pass
```

### Debugging e Logs

```python
import logging

# Configurar logging para debug
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kairos_debug.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DebuggableComponent:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def debug_method(self, method_name, *args, **kwargs):
        """Método auxiliar para debug."""
        self.logger.debug(f"Executando {method_name} com args={args}, kwargs={kwargs}")
        
        try:
            result = getattr(self, method_name)(*args, **kwargs)
            self.logger.debug(f"{method_name} executado com sucesso: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Erro em {method_name}: {e}")
            raise
```

---

## Conclusão

Este guia de exemplos fornece uma base sólida para implementar e personalizar os componentes da interface moderna do Kairos. Os exemplos cobrem desde uso básico até implementações avançadas e casos de uso específicos.

### Próximos Passos

1. **Experimentar os Exemplos**: Execute os códigos fornecidos para entender o funcionamento
2. **Personalizar**: Adapte os exemplos às suas necessidades específicas
3. **Integrar**: Combine diferentes componentes para criar aplicações completas
4. **Otimizar**: Use as técnicas de troubleshooting para resolver problemas
5. **Contribuir**: Compartilhe suas implementações e melhorias

### Recursos Adicionais

- **Documentação Técnica**: `docs/componentes_ui_moderna.md`
- **Guia de Testes**: `docs/guia_de_testes.md`
- **Código Fonte**: `views/components/`
- **Testes**: `tests/`

Para suporte adicional ou dúvidas, consulte a documentação técnica ou examine os testes unitários para entender melhor o comportamento esperado dos componentes.