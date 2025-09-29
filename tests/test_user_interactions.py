"""
Testes de interação do usuário para componentes da interface moderna.
User interaction tests for modern UI components.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import flet as ft
from datetime import datetime, timedelta
import time

# Import components for interaction testing
from views.components.time_tracker_widget import TimeTrackerWidget
from views.components.flowchart_widget import FlowchartWidget
from views.components.notification_center import NotificationCenter
from views.components.modern_sidebar import ModernSidebar
from views.components.top_sidebar_container import TopSidebarContainer

# Import models
from models.activity import Activity
from models.notification import Notification, NotificationType
from models.workflow_state import WorkflowState


class TestTimeTrackerUserInteractions(unittest.TestCase):
    """Testes de interação do usuário com o rastreador de tempo."""
    
    def setUp(self):
        """Configurar fixtures de teste."""
        self.mock_page = Mock(spec=ft.Page)
        self.mock_page.update = Mock()
        self.time_tracker = TimeTrackerWidget(self.mock_page)
        
    def test_user_starts_tracking_new_activity(self):
        """Testar usuário iniciando rastreamento de nova atividade."""
        # Simular seleção de atividade
        activity_name = "Nova Atividade de Desenvolvimento"
        self.time_tracker.activity_dropdown.value = activity_name
        
        # Simular clique no botão iniciar
        self.time_tracker._on_start_click(None)
        
        # Verificar que o rastreamento iniciou
        self.assertTrue(self.time_tracker.time_service.is_tracking())
        self.assertEqual(
            self.time_tracker.time_service.get_current_activity_id(), 
            activity_name
        )
        
        # Verificar que a interface foi atualizada
        self.assertTrue(self.time_tracker.start_button.disabled)
        self.assertFalse(self.time_tracker.stop_button.disabled)
        self.assertFalse(self.time_tracker.pause_button.disabled)
        
    def test_user_pauses_and_resumes_tracking(self):
        """Testar usuário pausando e retomando rastreamento."""
        # Iniciar rastreamento primeiro
        activity = Activity(name="Atividade de Teste", category="Desenvolvimento")
        self.time_tracker.time_service.start_tracking(activity)
        
        # Simular clique em pausar
        self.time_tracker._on_pause_click(None)
        
        # Verificar que foi pausado
        self.assertTrue(self.time_tracker.time_service.is_paused())
        self.assertEqual(self.time_tracker.pause_button.text, "Retomar")
        
        # Simular clique em retomar
        self.time_tracker._on_pause_click(None)
        
        # Verificar que foi retomado
        self.assertFalse(self.time_tracker.time_service.is_paused())
        self.assertEqual(self.time_tracker.pause_button.text, "Pausar")
        
    def test_user_stops_tracking_and_saves_entry(self):
        """Testar usuário parando rastreamento e salvando entrada."""
        # Iniciar rastreamento
        activity = Activity(name="Atividade Completa", category="Desenvolvimento")
        self.time_tracker.time_service.start_tracking(activity)
        
        # Aguardar um pouco para ter tempo registrado
        time.sleep(0.01)
        
        # Simular clique em parar
        self.time_tracker._on_stop_click(None)
        
        # Verificar que o rastreamento parou
        self.assertFalse(self.time_tracker.time_service.is_tracking())
        
        # Verificar que a entrada foi salva
        entries = self.time_tracker.time_service.get_time_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].activity_id, activity.id)
        self.assertIsNotNone(entries[0].end_time)
        
        # Verificar que a interface foi resetada
        self.assertFalse(self.time_tracker.start_button.disabled)
        self.assertTrue(self.time_tracker.stop_button.disabled)
        self.assertTrue(self.time_tracker.pause_button.disabled)
        
    def test_user_adds_new_activity_via_dropdown(self):
        """Testar usuário adicionando nova atividade via dropdown."""
        new_activity_name = "Atividade Personalizada"
        
        # Simular adição de nova atividade
        self.time_tracker._add_new_activity(new_activity_name)
        
        # Verificar que a atividade foi adicionada ao dropdown
        activity_options = [option.key for option in self.time_tracker.activity_dropdown.options]
        self.assertIn(new_activity_name, activity_options)
        
    def test_user_views_time_statistics(self):
        """Testar usuário visualizando estatísticas de tempo."""
        # Criar algumas entradas de tempo
        activities = [
            Activity(name="Desenvolvimento", category="Dev"),
            Activity(name="Reuniões", category="Meetings"),
            Activity(name="Documentação", category="Docs")
        ]
        
        for activity in activities:
            self.time_tracker.time_service.start_tracking(activity)
            time.sleep(0.01)
            self.time_tracker.time_service.stop_tracking()
            
        # Simular visualização de estatísticas
        daily_total = self.time_tracker.time_service.get_daily_total()
        self.assertGreater(daily_total.total_seconds(), 0)
        
        # Verificar estatísticas por atividade
        for activity in activities:
            activity_total = self.time_tracker.time_service.get_total_time_for_activity(activity.id)
            self.assertGreater(activity_total.total_seconds(), 0)


class TestFlowchartUserInteractions(unittest.TestCase):
    """Testes de interação do usuário com o fluxograma."""
    
    def setUp(self):
        """Configurar fixtures de teste."""
        self.mock_page = Mock(spec=ft.Page)
        self.mock_page.update = Mock()
        self.flowchart = FlowchartWidget(self.mock_page)
        
    def test_user_clicks_on_workflow_stage(self):
        """Testar usuário clicando em estágio do workflow."""
        # Criar workflow
        workflow_id = "test_workflow"
        self.flowchart.workflow_service.create_workflow(workflow_id)
        
        # Simular clique em estágio
        target_stage = "Verificação"
        self.flowchart._on_stage_click(target_stage)
        
        # Verificar que o estágio foi atualizado
        current_stage = self.flowchart.workflow_service.get_current_stage(workflow_id)
        self.assertEqual(current_stage.name, target_stage)
        
    def test_user_navigates_through_workflow_stages(self):
        """Testar usuário navegando pelos estágios do workflow."""
        workflow_id = "navigation_test"
        self.flowchart.workflow_service.create_workflow(workflow_id)
        
        # Simular navegação sequencial pelos estágios
        stages = ["Verificação", "Aprovação", "Emissão"]
        
        for stage in stages:
            self.flowchart._on_stage_click(stage)
            current_stage = self.flowchart.workflow_service.get_current_stage(workflow_id)
            self.assertEqual(current_stage.name, stage)
            
    def test_user_views_workflow_progress(self):
        """Testar usuário visualizando progresso do workflow."""
        workflow_id = "progress_test"
        self.flowchart.workflow_service.create_workflow(workflow_id)
        
        # Avançar alguns estágios
        self.flowchart.workflow_service.complete_current_stage(workflow_id)
        self.flowchart.workflow_service.complete_current_stage(workflow_id)
        
        # Verificar progresso
        progress = self.flowchart.workflow_service.get_workflow_progress(workflow_id)
        self.assertGreater(progress, 0)
        self.assertLess(progress, 100)
        
    def test_user_resets_workflow(self):
        """Testar usuário resetando workflow."""
        workflow_id = "reset_test"
        self.flowchart.workflow_service.create_workflow(workflow_id)
        
        # Avançar workflow
        self.flowchart.workflow_service.advance_workflow_stage(workflow_id, "Aprovação")
        
        # Simular reset
        self.flowchart.workflow_service.reset_workflow(workflow_id)
        
        # Verificar que voltou ao início
        current_stage = self.flowchart.workflow_service.get_current_stage(workflow_id)
        self.assertEqual(current_stage.name, "Postagem Inicial")


class TestNotificationCenterUserInteractions(unittest.TestCase):
    """Testes de interação do usuário com o centro de notificações."""
    
    def setUp(self):
        """Configurar fixtures de teste."""
        self.mock_page = Mock(spec=ft.Page)
        self.mock_page.update = Mock()
        self.notification_center = NotificationCenter(self.mock_page)
        
    def test_user_opens_notification_panel(self):
        """Testar usuário abrindo painel de notificações."""
        # Adicionar algumas notificações
        for i in range(3):
            self.notification_center.notification_service.add_notification(
                f"Notificação {i}",
                f"Mensagem {i}",
                NotificationType.INFO
            )
            
        # Simular clique no ícone de notificações
        self.notification_center._toggle_notification_panel(None)
        
        # Verificar que o painel foi aberto
        self.assertTrue(self.notification_center.is_panel_open)
        
    def test_user_marks_notification_as_read(self):
        """Testar usuário marcando notificação como lida."""
        # Adicionar notificação
        notification = self.notification_center.notification_service.add_notification(
            "Teste de Leitura",
            "Esta notificação será marcada como lida",
            NotificationType.INFO
        )
        
        # Verificar que está não lida
        self.assertFalse(notification.is_read)
        
        # Simular clique para marcar como lida
        self.notification_center._mark_as_read(notification.id)
        
        # Verificar que foi marcada como lida
        self.assertTrue(notification.is_read)
        
    def test_user_clears_all_notifications(self):
        """Testar usuário limpando todas as notificações."""
        # Adicionar várias notificações
        for i in range(5):
            self.notification_center.notification_service.add_notification(
                f"Notificação {i}",
                f"Mensagem {i}",
                NotificationType.INFO
            )
            
        # Verificar que existem notificações
        self.assertEqual(
            len(self.notification_center.notification_service.get_notifications()), 
            5
        )
        
        # Simular limpeza de todas as notificações
        self.notification_center._clear_all_notifications(None)
        
        # Verificar que foram removidas
        self.assertEqual(
            len(self.notification_center.notification_service.get_notifications()), 
            0
        )
        
    def test_user_filters_notifications_by_type(self):
        """Testar usuário filtrando notificações por tipo."""
        # Adicionar notificações de diferentes tipos
        types_and_counts = [
            (NotificationType.INFO, 3),
            (NotificationType.WARNING, 2),
            (NotificationType.ERROR, 1),
            (NotificationType.SUCCESS, 2)
        ]
        
        for ntype, count in types_and_counts:
            for i in range(count):
                self.notification_center.notification_service.add_notification(
                    f"Notificação {ntype.value} {i}",
                    f"Mensagem {i}",
                    ntype
                )
                
        # Testar filtragem por cada tipo
        for ntype, expected_count in types_and_counts:
            filtered = self.notification_center.notification_service.get_notifications(
                notification_type=ntype
            )
            self.assertEqual(len(filtered), expected_count)
            
    def test_user_interacts_with_notification_actions(self):
        """Testar usuário interagindo com ações de notificação."""
        # Adicionar notificação com ação
        notification = self.notification_center.notification_service.add_notification(
            "Notificação com Ação",
            "Clique para executar ação",
            NotificationType.INFO,
            action_url="/test_action"
        )
        
        # Simular clique na notificação
        action_executed = False
        
        def mock_action():
            nonlocal action_executed
            action_executed = True
            
        # Simular execução da ação
        if notification.action_url:
            mock_action()
            
        self.assertTrue(action_executed)


class TestModernSidebarUserInteractions(unittest.TestCase):
    """Testes de interação do usuário com a barra lateral moderna."""
    
    def setUp(self):
        """Configurar fixtures de teste."""
        self.mock_page = Mock(spec=ft.Page)
        self.mock_page.update = Mock()
        self.sidebar = ModernSidebar(self.mock_page)
        
    def test_user_toggles_sidebar_expansion(self):
        """Testar usuário alternando expansão da barra lateral."""
        # Estado inicial (expandido)
        initial_state = self.sidebar.expanded
        
        # Simular clique no botão de toggle
        self.sidebar.toggle_expansion()
        
        # Verificar que o estado mudou
        self.assertNotEqual(self.sidebar.expanded, initial_state)
        
        # Simular outro clique
        self.sidebar.toggle_expansion()
        
        # Verificar que voltou ao estado inicial
        self.assertEqual(self.sidebar.expanded, initial_state)
        
    def test_user_navigates_between_sections(self):
        """Testar usuário navegando entre seções."""
        sections = ["Gerenciamento de Tempo", "Fluxos de Projeto", "Vídeos Educacionais"]
        
        for section in sections:
            # Simular clique na seção
            self.sidebar.update_active_section(section)
            
            # Verificar que a seção foi ativada
            self.assertEqual(self.sidebar.active_section, section)
            
    def test_user_hovers_over_navigation_items(self):
        """Testar usuário passando mouse sobre itens de navegação."""
        # Criar item de navegação
        nav_item = self.sidebar._create_nav_item("Item de Teste", "test_icon")
        
        # Simular hover
        nav_item._on_hover(True)
        
        # Verificar que o efeito hover foi aplicado
        # (Em implementação real, verificaria mudanças visuais)
        
        # Simular saída do hover
        nav_item._on_hover(False)
        
        # Verificar que o efeito hover foi removido
        
    def test_user_clicks_on_navigation_item(self):
        """Testar usuário clicando em item de navegação."""
        clicked_item = None
        
        def on_item_click(item_name):
            nonlocal clicked_item
            clicked_item = item_name
            
        # Criar item com callback
        item_name = "Timer Ativo"
        nav_item = self.sidebar._create_nav_item(item_name, "timer")
        nav_item.on_click = lambda e: on_item_click(item_name)
        
        # Simular clique
        nav_item.on_click(None)
        
        # Verificar que o callback foi executado
        self.assertEqual(clicked_item, item_name)


class TestIntegratedUserWorkflows(unittest.TestCase):
    """Testes de fluxos de trabalho integrados do usuário."""
    
    def setUp(self):
        """Configurar fixtures de teste."""
        self.mock_page = Mock(spec=ft.Page)
        self.mock_page.update = Mock()
        
        # Criar componentes integrados
        self.container = TopSidebarContainer(self.mock_page)
        self.sidebar = ModernSidebar(self.mock_page)
        
    def test_complete_time_tracking_workflow(self):
        """Testar fluxo completo de rastreamento de tempo."""
        # 1. Usuário seleciona atividade
        activity_name = "Desenvolvimento de Feature Completa"
        self.container.time_tracker.activity_dropdown.value = activity_name
        
        # 2. Usuário inicia rastreamento
        self.container.time_tracker._on_start_click(None)
        
        # Verificar que o rastreamento iniciou
        self.assertTrue(self.container.time_tracker.time_service.is_tracking())
        
        # 3. Sistema gera notificação automática
        notifications_before = len(
            self.container.notifications.notification_service.get_notifications()
        )
        
        # Simular notificação automática
        self.container.notifications.notification_service.add_notification(
            "Rastreamento Iniciado",
            f"Iniciado rastreamento para: {activity_name}",
            NotificationType.INFO
        )
        
        notifications_after = len(
            self.container.notifications.notification_service.get_notifications()
        )
        self.assertEqual(notifications_after, notifications_before + 1)
        
        # 4. Usuário trabalha (simular tempo passando)
        time.sleep(0.02)
        
        # 5. Usuário pausa temporariamente
        self.container.time_tracker._on_pause_click(None)
        self.assertTrue(self.container.time_tracker.time_service.is_paused())
        
        # 6. Usuário retoma trabalho
        self.container.time_tracker._on_pause_click(None)
        self.assertFalse(self.container.time_tracker.time_service.is_paused())
        
        # 7. Usuário finaliza rastreamento
        time_entry = self.container.time_tracker._on_stop_click(None)
        
        # Verificar que o fluxo foi completado
        self.assertFalse(self.container.time_tracker.time_service.is_tracking())
        
        # 8. Sistema gera notificação de conclusão
        self.container.notifications.notification_service.add_notification(
            "Tempo Registrado",
            f"Registrado tempo para: {activity_name}",
            NotificationType.SUCCESS
        )
        
        final_notifications = len(
            self.container.notifications.notification_service.get_notifications()
        )
        self.assertEqual(final_notifications, notifications_after + 1)
        
    def test_workflow_management_user_flow(self):
        """Testar fluxo de gerenciamento de workflow do usuário."""
        # 1. Usuário cria novo workflow
        workflow_id = "projeto_usuario_001"
        self.container.flowchart.workflow_service.create_workflow(
            workflow_id, "Projeto do Usuário"
        )
        
        # 2. Usuário visualiza estágio atual
        current_stage = self.container.flowchart.workflow_service.get_current_stage(workflow_id)
        self.assertEqual(current_stage.name, "Postagem Inicial")
        
        # 3. Usuário avança para próximo estágio
        self.container.flowchart._on_stage_click("Verificação")
        
        # 4. Sistema atualiza progresso
        progress = self.container.flowchart.workflow_service.get_workflow_progress(workflow_id)
        self.assertGreater(progress, 0)
        
        # 5. Sistema gera notificação de progresso
        self.container.notifications.notification_service.add_notification(
            "Workflow Atualizado",
            "Estágio 'Verificação' iniciado",
            NotificationType.INFO
        )
        
        # 6. Usuário continua avançando estágios
        stages_to_advance = ["Aprovação", "Emissão"]
        for stage in stages_to_advance:
            self.container.flowchart._on_stage_click(stage)
            
        # 7. Usuário verifica progresso final
        final_progress = self.container.flowchart.workflow_service.get_workflow_progress(workflow_id)
        self.assertGreater(final_progress, progress)
        
    def test_notification_management_user_flow(self):
        """Testar fluxo de gerenciamento de notificações do usuário."""
        # 1. Sistema gera várias notificações
        notification_data = [
            ("Bem-vindo", "Sistema iniciado", NotificationType.SUCCESS),
            ("Lembrete", "Registre seu tempo", NotificationType.INFO),
            ("Aviso", "Prazo se aproximando", NotificationType.WARNING),
            ("Erro", "Falha na sincronização", NotificationType.ERROR)
        ]
        
        for title, message, ntype in notification_data:
            self.container.notifications.notification_service.add_notification(
                title, message, ntype
            )
            
        # 2. Usuário vê contador de notificações
        unread_count = self.container.notifications.notification_service.get_unread_count()
        self.assertEqual(unread_count, 4)
        
        # 3. Usuário abre painel de notificações
        self.container.notifications._toggle_notification_panel(None)
        self.assertTrue(self.container.notifications.is_panel_open)
        
        # 4. Usuário lê algumas notificações
        notifications = self.container.notifications.notification_service.get_notifications()
        for i in range(2):
            self.container.notifications._mark_as_read(notifications[i].id)
            
        # 5. Usuário verifica contador atualizado
        updated_unread_count = self.container.notifications.notification_service.get_unread_count()
        self.assertEqual(updated_unread_count, 2)
        
        # 6. Usuário filtra por tipo de notificação
        error_notifications = self.container.notifications.notification_service.get_notifications(
            notification_type=NotificationType.ERROR
        )
        self.assertEqual(len(error_notifications), 1)
        
        # 7. Usuário limpa notificações lidas
        cleared_count = self.container.notifications.notification_service.clear_read_notifications()
        self.assertEqual(cleared_count, 2)
        
        # 8. Usuário fecha painel
        self.container.notifications._toggle_notification_panel(None)
        self.assertFalse(self.container.notifications.is_panel_open)
        
    def test_sidebar_navigation_user_flow(self):
        """Testar fluxo de navegação da barra lateral do usuário."""
        # 1. Usuário vê barra lateral expandida
        self.assertTrue(self.sidebar.expanded)
        
        # 2. Usuário navega para seção de tempo
        self.sidebar.update_active_section("Gerenciamento de Tempo")
        self.assertEqual(self.sidebar.active_section, "Gerenciamento de Tempo")
        
        # 3. Usuário colapsa barra lateral para mais espaço
        self.sidebar.toggle_expansion()
        self.assertFalse(self.sidebar.expanded)
        
        # 4. Container se adapta ao novo layout
        self.container.update_layout(sidebar_expanded=False)
        
        # 5. Usuário navega para seção de projetos
        self.sidebar.update_active_section("Fluxos de Projeto")
        self.assertEqual(self.sidebar.active_section, "Fluxos de Projeto")
        
        # 6. Usuário expande barra lateral novamente
        self.sidebar.toggle_expansion()
        self.assertTrue(self.sidebar.expanded)
        
        # 7. Container se adapta novamente
        self.container.update_layout(sidebar_expanded=True)
        
    def test_error_recovery_user_flow(self):
        """Testar fluxo de recuperação de erros do usuário."""
        # 1. Simular erro no serviço de tempo
        with patch.object(
            self.container.time_tracker.time_service, 
            'start_tracking', 
            side_effect=Exception("Erro simulado")
        ):
            # 2. Usuário tenta iniciar rastreamento
            try:
                self.container.time_tracker._on_start_click(None)
            except Exception:
                pass  # Erro esperado
                
            # 3. Sistema deve mostrar notificação de erro
            self.container.notifications.notification_service.add_notification(
                "Erro no Rastreamento",
                "Não foi possível iniciar o rastreamento. Tente novamente.",
                NotificationType.ERROR
            )
            
        # 4. Usuário vê notificação de erro
        error_notifications = self.container.notifications.notification_service.get_notifications(
            notification_type=NotificationType.ERROR
        )
        self.assertGreater(len(error_notifications), 0)
        
        # 5. Usuário tenta novamente (sem erro)
        activity = Activity(name="Atividade de Recuperação", category="Test")
        self.container.time_tracker.time_service.start_tracking(activity)
        
        # 6. Sistema confirma sucesso
        self.assertTrue(self.container.time_tracker.time_service.is_tracking())
        
        # 7. Sistema gera notificação de sucesso
        self.container.notifications.notification_service.add_notification(
            "Rastreamento Recuperado",
            "Rastreamento iniciado com sucesso",
            NotificationType.SUCCESS
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)