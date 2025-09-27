# Documentação dos Componentes da Interface Moderna

## Visão Geral

Esta documentação descreve todos os componentes da interface moderna do Kairos, incluindo funcionalidades, uso e exemplos práticos. Os componentes foram desenvolvidos seguindo princípios de design moderno, acessibilidade e performance.

## Índice

1. [Sistema de Design](#sistema-de-design)
2. [Rastreador de Tempo](#rastreador-de-tempo)
3. [Widget de Fluxograma](#widget-de-fluxograma)
4. [Centro de Notificações](#centro-de-notificações)
5. [Barra Lateral Moderna](#barra-lateral-moderna)
6. [Contêiner da Barra Superior](#contêiner-da-barra-superior)
7. [Exemplos de Uso](#exemplos-de-uso)
8. [Guia de Personalização](#guia-de-personalização)

---

## Sistema de Design

### Paleta de Cores

O sistema utiliza uma paleta de cores semântica e consistente:

```python
# Cores Primárias
PRIMARY = "#2563eb"      # Azul principal
SECONDARY = "#64748b"    # Cinza secundário
ACCENT = "#f59e0b"       # Amarelo de destaque

# Cores Semânticas
SUCCESS = "#10b981"      # Verde para sucesso
WARNING = "#f59e0b"      # Amarelo para avisos
ERROR = "#ef4444"        # Vermelho para erros
INFO = "#3b82f6"         # Azul para informações

# Cores Neutras
BACKGROUND = "#f8fafc"   # Fundo principal
SURFACE = "#ffffff"      # Superfície de componentes
TEXT_PRIMARY = "#1e293b" # Texto principal
TEXT_SECONDARY = "#64748b" # Texto secundário
```

### Tipografia

Sistema tipográfico baseado em escala harmônica:

```python
# Cabeçalhos
HEADING_1 = {"size": 32, "weight": "bold"}
HEADING_2 = {"size": 24, "weight": "bold"}
HEADING_3 = {"size": 20, "weight": "semibold"}

# Texto do Corpo
BODY_LARGE = {"size": 16, "weight": "normal"}
BODY_MEDIUM = {"size": 14, "weight": "normal"}
BODY_SMALL = {"size": 12, "weight": "normal"}

# Elementos Especiais
CAPTION = {"size": 11, "weight": "normal"}
LABEL = {"size": 12, "weight": "medium"}
```

### Espaçamento

Sistema de espaçamento baseado em grid de 8px:

```python
XS = 4    # Extra pequeno
SM = 8    # Pequeno
MD = 16   # Médio
LG = 24   # Grande
XL = 32   # Extra grande
XXL = 48  # Extra extra grande
```

---

## Rastreador de Tempo

### Descrição

O `TimeTrackerWidget` é um componente para rastreamento de tempo em atividades, oferecendo controles intuitivos e feedback visual em tempo real.

### Funcionalidades Principais

- **Rastreamento em Tempo Real**: Timer que atualiza a cada segundo
- **Controles de Atividade**: Iniciar, pausar, retomar e parar
- **Seleção de Atividades**: Dropdown para escolher ou criar atividades
- **Indicador Visual**: Progresso circular e display digital
- **Persistência de Dados**: Salva entradas de tempo automaticamente

### Uso Básico

```python
import flet as ft
from views.components.time_tracker_widget import TimeTrackerWidget

def main(page: ft.Page):
    # Criar o widget de rastreamento
    time_tracker = TimeTrackerWidget(page)
    
    # Adicionar à página
    page.add(time_tracker)
    
    # Atualizar a página
    page.update()

ft.app(target=main)
```

### Métodos Principais

#### `start_tracking(activity_name: str)`
Inicia o rastreamento de tempo para uma atividade específica.

```python
# Iniciar rastreamento
time_tracker.start_tracking("Desenvolvimento de Feature")
```

#### `stop_tracking()`
Para o rastreamento atual e salva a entrada de tempo.

```python
# Parar rastreamento
time_entry = time_tracker.stop_tracking()
print(f"Tempo registrado: {time_entry.duration}")
```

#### `pause_tracking()` / `resume_tracking()`
Pausa ou retoma o rastreamento atual.

```python
# Pausar
time_tracker.pause_tracking()

# Retomar
time_tracker.resume_tracking()
```

### Eventos e Callbacks

```python
# Configurar callback para quando o tempo é atualizado
def on_time_update(elapsed_time):
    print(f"Tempo decorrido: {elapsed_time}")

time_tracker.on_time_update = on_time_update

# Callback para quando uma atividade é concluída
def on_activity_completed(time_entry):
    print(f"Atividade concluída: {time_entry.activity_name}")
    print(f"Duração: {time_entry.duration}")

time_tracker.on_activity_completed = on_activity_completed
```

### Personalização Visual

```python
# Personalizar cores do timer
time_tracker.timer_color = "#2563eb"
time_tracker.progress_color = "#10b981"

# Personalizar tamanho
time_tracker.width = 300
time_tracker.height = 200

# Personalizar estilo dos botões
time_tracker.button_style = {
    "bgcolor": "#f59e0b",
    "color": "#ffffff",
    "border_radius": 8
}
```

---

## Widget de Fluxograma

### Descrição

O `FlowchartWidget` visualiza o fluxo de trabalho de documentos, mostrando estágios, progresso e permitindo interação com o processo.

### Funcionalidades Principais

- **Visualização de Estágios**: Mostra todos os estágios do workflow
- **Indicador de Progresso**: Destaca o estágio atual e progresso
- **Interatividade**: Clique nos estágios para navegar
- **Layout Responsivo**: Adapta-se a diferentes tamanhos de tela
- **Animações Suaves**: Transições visuais elegantes

### Estágios do Workflow

O sistema inclui os seguintes estágios padrão:

1. **Postagem Inicial** - Início do processo
2. **Verificação** - Revisão inicial
3. **Aprovação** - Aprovação do documento
4. **Emissão** - Emissão oficial
5. **Comentários Cliente** - Feedback do cliente
6. **Análise Cliente** - Análise do feedback
7. **Comentários Proprietário** - Feedback do proprietário
8. **Análise Técnica** - Revisão técnica
9. **Revisão Aprovado** - Revisão final
10. **Emissão Aprovado** - Emissão aprovada
11. **Postagem Concluída** - Processo finalizado

### Uso Básico

```python
import flet as ft
from views.components.flowchart_widget import FlowchartWidget

def main(page: ft.Page):
    # Criar o widget de fluxograma
    flowchart = FlowchartWidget(page)
    
    # Criar um workflow
    workflow_id = "projeto_001"
    flowchart.create_workflow(workflow_id, "Projeto de Exemplo")
    
    # Adicionar à página
    page.add(flowchart)
    page.update()

ft.app(target=main)
```

### Métodos Principais

#### `create_workflow(workflow_id: str, project_name: str)`
Cria um novo workflow.

```python
flowchart.create_workflow("proj_001", "Projeto Alpha")
```

#### `advance_stage(stage_name: str)`
Avança para um estágio específico.

```python
flowchart.advance_stage("Verificação")
```

#### `get_current_stage()`
Obtém o estágio atual do workflow.

```python
current_stage = flowchart.get_current_stage()
print(f"Estágio atual: {current_stage.name}")
```

#### `get_progress_percentage()`
Obtém a porcentagem de progresso do workflow.

```python
progress = flowchart.get_progress_percentage()
print(f"Progresso: {progress}%")
```

### Eventos de Interação

```python
# Callback para clique em estágio
def on_stage_click(stage_name):
    print(f"Estágio clicado: {stage_name}")
    # Lógica personalizada aqui

flowchart.on_stage_click = on_stage_click

# Callback para mudança de estágio
def on_stage_change(old_stage, new_stage):
    print(f"Mudança: {old_stage} → {new_stage}")

flowchart.on_stage_change = on_stage_change
```

### Personalização Visual

```python
# Personalizar cores dos estágios
flowchart.stage_colors = {
    "pending": "#e2e8f0",
    "in_progress": "#3b82f6",
    "completed": "#10b981",
    "blocked": "#ef4444"
}

# Personalizar layout
flowchart.stage_spacing = 16
flowchart.connector_width = 2
flowchart.stage_border_radius = 8
```

---

## Centro de Notificações

### Descrição

O `NotificationCenter` gerencia e exibe notificações do sistema, oferecendo categorização, filtragem e interações intuitivas.

### Funcionalidades Principais

- **Tipos de Notificação**: Info, Sucesso, Aviso e Erro
- **Contador de Não Lidas**: Badge visual com contagem
- **Painel Dropdown**: Interface expansível para visualização
- **Filtragem**: Por tipo, status de leitura e data
- **Ações em Lote**: Marcar todas como lidas, limpar todas
- **Timestamps**: Exibição de data e hora das notificações

### Tipos de Notificação

```python
from models.notification import NotificationType

# Tipos disponíveis
NotificationType.INFO     # Informações gerais
NotificationType.SUCCESS  # Operações bem-sucedidas
NotificationType.WARNING  # Avisos importantes
NotificationType.ERROR    # Erros e falhas
```

### Uso Básico

```python
import flet as ft
from views.components.notification_center import NotificationCenter
from models.notification import NotificationType

def main(page: ft.Page):
    # Criar o centro de notificações
    notification_center = NotificationCenter(page)
    
    # Adicionar algumas notificações
    notification_center.add_notification(
        "Bem-vindo!",
        "Sistema iniciado com sucesso",
        NotificationType.SUCCESS
    )
    
    notification_center.add_notification(
        "Atualização Disponível",
        "Nova versão disponível para download",
        NotificationType.INFO
    )
    
    # Adicionar à página
    page.add(notification_center)
    page.update()

ft.app(target=main)
```

### Métodos Principais

#### `add_notification(title: str, message: str, type: NotificationType)`
Adiciona uma nova notificação.

```python
notification_center.add_notification(
    "Tarefa Concluída",
    "O relatório foi gerado com sucesso",
    NotificationType.SUCCESS
)
```

#### `mark_as_read(notification_id: str)`
Marca uma notificação específica como lida.

```python
notification_center.mark_as_read("notif_123")
```

#### `mark_all_as_read()`
Marca todas as notificações como lidas.

```python
notification_center.mark_all_as_read()
```

#### `clear_all_notifications()`
Remove todas as notificações.

```python
notification_center.clear_all_notifications()
```

#### `get_unread_count()`
Obtém o número de notificações não lidas.

```python
unread_count = notification_center.get_unread_count()
print(f"Notificações não lidas: {unread_count}")
```

### Filtragem e Busca

```python
# Obter notificações por tipo
error_notifications = notification_center.get_notifications_by_type(
    NotificationType.ERROR
)

# Obter apenas não lidas
unread_notifications = notification_center.get_unread_notifications()

# Obter notificações por período
from datetime import datetime, timedelta
today = datetime.now()
yesterday = today - timedelta(days=1)

recent_notifications = notification_center.get_notifications_by_date_range(
    start_date=yesterday,
    end_date=today
)
```

### Eventos e Callbacks

```python
# Callback para nova notificação
def on_new_notification(notification):
    print(f"Nova notificação: {notification.title}")

notification_center.on_new_notification = on_new_notification

# Callback para notificação lida
def on_notification_read(notification):
    print(f"Notificação lida: {notification.title}")

notification_center.on_notification_read = on_notification_read

# Callback para clique em notificação
def on_notification_click(notification):
    print(f"Clicou em: {notification.title}")
    # Navegar para página relacionada
    if notification.action_url:
        page.go(notification.action_url)

notification_center.on_notification_click = on_notification_click
```

### Personalização de Aparência

```python
# Personalizar ícones por tipo
notification_center.type_icons = {
    NotificationType.INFO: "info",
    NotificationType.SUCCESS: "check_circle",
    NotificationType.WARNING: "warning",
    NotificationType.ERROR: "error"
}

# Personalizar cores
notification_center.type_colors = {
    NotificationType.INFO: "#3b82f6",
    NotificationType.SUCCESS: "#10b981",
    NotificationType.WARNING: "#f59e0b",
    NotificationType.ERROR: "#ef4444"
}

# Personalizar layout do painel
notification_center.panel_width = 400
notification_center.panel_max_height = 500
notification_center.animation_duration = 200
```

---

## Barra Lateral Moderna

### Descrição

A `ModernSidebar` oferece navegação organizada em três seções principais: Gerenciamento de Tempo, Fluxos de Projeto e Vídeos Educacionais.

### Funcionalidades Principais

- **Três Seções Organizadas**: Navegação clara e intuitiva
- **Expansão/Colapso**: Alterna entre modo expandido e ícones
- **Efeitos Visuais**: Hover, seleção e animações suaves
- **Responsividade**: Adapta-se a diferentes tamanhos de tela
- **Personalização**: Temas e estilos configuráveis

### Seções da Barra Lateral

#### 1. Gerenciamento de Tempo
- Rastreamento de atividades
- Relatórios de tempo
- Configurações de timer
- Histórico de atividades

#### 2. Fluxos de Projeto
- Visualização de workflows
- Gerenciamento de estágios
- Progresso de projetos
- Templates de fluxo

#### 3. Vídeos Educacionais
- Biblioteca de vídeos
- Categorias de conteúdo
- Progresso de visualização
- Favoritos e playlists

### Uso Básico

```python
import flet as ft
from views.components.modern_sidebar import ModernSidebar

def main(page: ft.Page):
    # Criar a barra lateral
    sidebar = ModernSidebar(page)
    
    # Configurar callback de navegação
    def on_navigation(section, item):
        print(f"Navegando para: {section} > {item}")
        # Lógica de navegação aqui
    
    sidebar.on_navigation = on_navigation
    
    # Adicionar à página
    page.add(sidebar)
    page.update()

ft.app(target=main)
```

### Métodos Principais

#### `toggle_expansion()`
Alterna entre modo expandido e colapsado.

```python
sidebar.toggle_expansion()
```

#### `set_active_section(section_name: str)`
Define a seção ativa.

```python
sidebar.set_active_section("Gerenciamento de Tempo")
```

#### `add_custom_item(section: str, item_name: str, icon: str, callback)`
Adiciona um item personalizado a uma seção.

```python
def custom_action():
    print("Ação personalizada executada")

sidebar.add_custom_item(
    section="Gerenciamento de Tempo",
    item_name="Relatório Personalizado",
    icon="assessment",
    callback=custom_action
)
```

#### `update_badge(section: str, item: str, count: int)`
Atualiza o badge de contagem de um item.

```python
# Mostrar 5 notificações pendentes
sidebar.update_badge("Fluxos de Projeto", "Pendentes", 5)
```

### Personalização de Seções

```python
# Personalizar itens da seção de tempo
time_management_items = [
    {"name": "Timer Ativo", "icon": "timer", "action": start_timer},
    {"name": "Relatórios", "icon": "assessment", "action": show_reports},
    {"name": "Atividades", "icon": "list", "action": manage_activities},
    {"name": "Configurações", "icon": "settings", "action": show_settings}
]

sidebar.customize_section("Gerenciamento de Tempo", time_management_items)

# Personalizar seção de projetos
project_items = [
    {"name": "Workflows Ativos", "icon": "account_tree", "badge": 3},
    {"name": "Templates", "icon": "content_copy", "action": show_templates},
    {"name": "Histórico", "icon": "history", "action": show_history}
]

sidebar.customize_section("Fluxos de Projeto", project_items)
```

### Eventos de Navegação

```python
# Callback detalhado de navegação
def on_detailed_navigation(event_data):
    section = event_data["section"]
    item = event_data["item"]
    action = event_data["action"]
    
    print(f"Seção: {section}")
    print(f"Item: {item}")
    print(f"Ação: {action}")
    
    # Lógica de roteamento
    if section == "Gerenciamento de Tempo":
        if item == "Timer Ativo":
            page.go("/timer")
        elif item == "Relatórios":
            page.go("/reports")
    elif section == "Fluxos de Projeto":
        if item == "Workflows Ativos":
            page.go("/workflows")

sidebar.on_detailed_navigation = on_detailed_navigation
```

### Temas e Estilos

```python
# Tema escuro
dark_theme = {
    "background_color": "#1e293b",
    "surface_color": "#334155",
    "text_primary": "#f1f5f9",
    "text_secondary": "#94a3b8",
    "accent_color": "#3b82f6",
    "hover_color": "#475569"
}

sidebar.apply_theme(dark_theme)

# Tema claro (padrão)
light_theme = {
    "background_color": "#ffffff",
    "surface_color": "#f8fafc",
    "text_primary": "#1e293b",
    "text_secondary": "#64748b",
    "accent_color": "#2563eb",
    "hover_color": "#e2e8f0"
}

sidebar.apply_theme(light_theme)
```

---

## Contêiner da Barra Superior

### Descrição

O `TopSidebarContainer` organiza horizontalmente os componentes principais: rastreador de tempo, fluxograma e centro de notificações.

### Funcionalidades Principais

- **Layout Horizontal**: Organização otimizada dos componentes
- **Responsividade**: Adapta-se ao estado da barra lateral
- **Sincronização**: Coordena atualizações entre componentes
- **Performance**: Otimizado para atualizações frequentes

### Uso Básico

```python
import flet as ft
from views.components.top_sidebar_container import TopSidebarContainer

def main(page: ft.Page):
    # Criar o contêiner superior
    top_container = TopSidebarContainer(page)
    
    # Configurar estado inicial
    top_container.update_layout(sidebar_expanded=True)
    
    # Adicionar à página
    page.add(top_container)
    page.update()

ft.app(target=main)
```

### Métodos Principais

#### `update_layout(sidebar_expanded: bool)`
Atualiza o layout baseado no estado da barra lateral.

```python
# Barra lateral expandida
top_container.update_layout(sidebar_expanded=True)

# Barra lateral colapsada
top_container.update_layout(sidebar_expanded=False)
```

#### `refresh_components()`
Atualiza todos os componentes filhos.

```python
top_container.refresh_components()
```

#### `get_component(component_name: str)`
Obtém referência a um componente específico.

```python
# Obter o rastreador de tempo
time_tracker = top_container.get_component("time_tracker")

# Obter o centro de notificações
notifications = top_container.get_component("notifications")

# Obter o fluxograma
flowchart = top_container.get_component("flowchart")
```

### Configuração de Layout

```python
# Configurar espaçamento entre componentes
top_container.component_spacing = 16

# Configurar proporções dos componentes
top_container.component_ratios = {
    "time_tracker": 0.3,    # 30% da largura
    "flowchart": 0.5,       # 50% da largura
    "notifications": 0.2    # 20% da largura
}

# Configurar altura mínima
top_container.min_height = 120
```

### Responsividade Avançada

```python
# Configurar breakpoints responsivos
top_container.breakpoints = {
    "mobile": 480,
    "tablet": 768,
    "desktop": 1024
}

# Configurar layouts por breakpoint
top_container.responsive_layouts = {
    "mobile": {
        "direction": "vertical",
        "component_ratios": {"time_tracker": 1, "flowchart": 1, "notifications": 1}
    },
    "tablet": {
        "direction": "horizontal",
        "component_ratios": {"time_tracker": 0.4, "flowchart": 0.6, "notifications": 0}
    },
    "desktop": {
        "direction": "horizontal",
        "component_ratios": {"time_tracker": 0.3, "flowchart": 0.5, "notifications": 0.2}
    }
}
```

---

## Exemplos de Uso

### Exemplo 1: Aplicação Completa

```python
import flet as ft
from views.components.top_sidebar_container import TopSidebarContainer
from views.components.modern_sidebar import ModernSidebar
from models.notification import NotificationType

def main(page: ft.Page):
    page.title = "Kairos - Interface Moderna"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Criar componentes principais
    sidebar = ModernSidebar(page)
    top_container = TopSidebarContainer(page)
    
    # Configurar callbacks
    def on_sidebar_toggle():
        is_expanded = sidebar.toggle_expansion()
        top_container.update_layout(sidebar_expanded=is_expanded)
    
    def on_navigation(section, item):
        # Adicionar notificação de navegação
        top_container.notifications.add_notification(
            f"Navegação",
            f"Acessando {section} > {item}",
            NotificationType.INFO
        )
    
    # Conectar eventos
    sidebar.on_toggle = on_sidebar_toggle
    sidebar.on_navigation = on_navigation
    
    # Layout principal
    main_layout = ft.Row([
        sidebar,
        ft.Column([
            top_container,
            ft.Container(
                content=ft.Text("Área de conteúdo principal"),
                expand=True,
                bgcolor="#f8fafc",
                padding=20
            )
        ], expand=True)
    ], expand=True)
    
    page.add(main_layout)
    page.update()

ft.app(target=main)
```

### Exemplo 2: Integração com Dados Reais

```python
import flet as ft
from datetime import datetime, timedelta
from views.components.time_tracker_widget import TimeTrackerWidget
from views.components.notification_center import NotificationCenter
from models.activity import Activity
from models.notification import NotificationType

def main(page: ft.Page):
    # Criar componentes
    time_tracker = TimeTrackerWidget(page)
    notifications = NotificationCenter(page)
    
    # Dados de exemplo
    activities = [
        Activity("Desenvolvimento Frontend", "Desenvolvimento"),
        Activity("Reunião de Equipe", "Reuniões"),
        Activity("Documentação", "Documentação"),
        Activity("Testes", "QA")
    ]
    
    # Configurar atividades no tracker
    for activity in activities:
        time_tracker.add_activity(activity)
    
    # Simular notificações do sistema
    def simulate_notifications():
        notifications.add_notification(
            "Sistema Iniciado",
            "Kairos foi iniciado com sucesso",
            NotificationType.SUCCESS
        )
        
        notifications.add_notification(
            "Lembrete",
            "Não esqueça de registrar seu tempo",
            NotificationType.INFO
        )
        
        notifications.add_notification(
            "Backup",
            "Backup automático realizado",
            NotificationType.SUCCESS
        )
    
    # Configurar callbacks de integração
    def on_time_tracking_start(activity):
        notifications.add_notification(
            "Rastreamento Iniciado",
            f"Iniciando rastreamento para: {activity.name}",
            NotificationType.INFO
        )
    
    def on_time_tracking_stop(time_entry):
        duration_str = str(time_entry.duration).split('.')[0]  # Remove microsegundos
        notifications.add_notification(
            "Tempo Registrado",
            f"Registrado {duration_str} para {time_entry.activity_name}",
            NotificationType.SUCCESS
        )
    
    # Conectar eventos
    time_tracker.on_tracking_start = on_time_tracking_start
    time_tracker.on_tracking_stop = on_time_tracking_stop
    
    # Simular notificações iniciais
    simulate_notifications()
    
    # Layout
    layout = ft.Column([
        ft.Row([time_tracker, notifications]),
        ft.Divider(),
        ft.Text("Área de conteúdo adicional")
    ])
    
    page.add(layout)
    page.update()

ft.app(target=main)
```

### Exemplo 3: Personalização Avançada

```python
import flet as ft
from views.components.modern_sidebar import ModernSidebar
from views.components.design_system import ColorPalette, Typography

def main(page: ft.Page):
    # Criar sidebar personalizada
    sidebar = ModernSidebar(page)
    
    # Tema personalizado
    custom_theme = {
        "primary_color": "#6366f1",
        "secondary_color": "#8b5cf6",
        "background_color": "#0f172a",
        "surface_color": "#1e293b",
        "text_primary": "#f1f5f9",
        "text_secondary": "#94a3b8"
    }
    
    # Aplicar tema
    sidebar.apply_theme(custom_theme)
    
    # Adicionar seção personalizada
    custom_items = [
        {
            "name": "Dashboard Executivo",
            "icon": "dashboard",
            "action": lambda: print("Dashboard aberto"),
            "badge": 2
        },
        {
            "name": "Análise Avançada",
            "icon": "analytics",
            "action": lambda: print("Análise aberta"),
            "premium": True
        },
        {
            "name": "Exportar Dados",
            "icon": "download",
            "action": lambda: print("Exportação iniciada")
        }
    ]
    
    sidebar.add_custom_section("Ferramentas Avançadas", custom_items)
    
    # Configurar animações personalizadas
    sidebar.animation_config = {
        "hover_duration": 150,
        "selection_duration": 200,
        "expansion_duration": 300,
        "easing": "ease-out"
    }
    
    # Layout com sidebar personalizada
    main_content = ft.Container(
        content=ft.Column([
            ft.Text("Conteúdo Principal", 
                   style=ft.TextStyle(size=24, weight=ft.FontWeight.BOLD)),
            ft.Text("Interface personalizada com tema escuro"),
            ft.ElevatedButton("Ação de Exemplo", 
                            bgcolor=custom_theme["primary_color"])
        ]),
        padding=20,
        bgcolor=custom_theme["background_color"],
        expand=True
    )
    
    layout = ft.Row([
        sidebar,
        main_content
    ], expand=True)
    
    page.add(layout)
    page.update()

ft.app(target=main)
```

---

## Guia de Personalização

### Modificando Cores

```python
# Personalizar paleta de cores globalmente
from views.components.design_system import ColorPalette

# Sobrescrever cores padrão
ColorPalette.PRIMARY = "#your_primary_color"
ColorPalette.SECONDARY = "#your_secondary_color"
ColorPalette.ACCENT = "#your_accent_color"

# Ou criar tema personalizado
custom_colors = {
    "primary": "#6366f1",
    "secondary": "#8b5cf6",
    "success": "#10b981",
    "warning": "#f59e0b",
    "error": "#ef4444",
    "info": "#3b82f6"
}
```

### Modificando Tipografia

```python
# Personalizar escala tipográfica
from views.components.design_system import Typography

Typography.HEADING_1["size"] = 36
Typography.BODY_MEDIUM["weight"] = "medium"

# Ou definir fonte personalizada
custom_typography = {
    "font_family": "Inter, sans-serif",
    "heading_1": {"size": 32, "weight": "bold", "line_height": 1.2},
    "body_medium": {"size": 14, "weight": "normal", "line_height": 1.5}
}
```

### Criando Componentes Personalizados

```python
import flet as ft
from views.components.design_system import DesignSystem

class CustomWidget(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.design_system = DesignSystem()
        
        # Aplicar estilos do sistema de design
        self.bgcolor = self.design_system.colors.SURFACE
        self.border_radius = self.design_system.border_radius.MD
        self.padding = self.design_system.spacing.MD
        
        # Conteúdo personalizado
        self.content = ft.Column([
            ft.Text("Widget Personalizado", 
                   style=self.design_system.typography.HEADING_3),
            ft.Text("Usando o sistema de design", 
                   style=self.design_system.typography.BODY_MEDIUM)
        ])
    
    def custom_action(self):
        # Lógica personalizada
        pass
```

### Configuração de Responsividade

```python
# Configurar breakpoints personalizados
responsive_config = {
    "breakpoints": {
        "xs": 0,
        "sm": 576,
        "md": 768,
        "lg": 992,
        "xl": 1200,
        "xxl": 1400
    },
    "layouts": {
        "xs": {"sidebar_width": 0, "container_padding": 8},
        "sm": {"sidebar_width": 60, "container_padding": 12},
        "md": {"sidebar_width": 240, "container_padding": 16},
        "lg": {"sidebar_width": 280, "container_padding": 20},
        "xl": {"sidebar_width": 320, "container_padding": 24}
    }
}
```

---

## Conclusão

Esta documentação fornece uma visão abrangente dos componentes da interface moderna do Kairos. Cada componente foi projetado para ser flexível, performático e fácil de usar, seguindo as melhores práticas de design de interface.

Para mais informações ou suporte, consulte:
- Código fonte dos componentes em `views/components/`
- Testes em `tests/`
- Exemplos práticos em `examples/`

### Recursos Adicionais

- **Guia de Contribuição**: Como contribuir com novos componentes
- **API Reference**: Documentação detalhada da API
- **Changelog**: Histórico de mudanças e atualizações
- **FAQ**: Perguntas frequentes e soluções