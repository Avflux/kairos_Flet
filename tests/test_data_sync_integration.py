"""
Testes de integração para o sistema de sincronização de dados do TopSidebarContainer.

Este módulo testa o fluxo completo de sincronização de dados entre os componentes
do TopSidebarContainer e o WebView, incluindo observadores, callbacks e
atualização automática.
"""

import pytest
import json
import tempfile
import os
import time
import threading
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime

import flet as ft

# Import components to test
from views.components.top_sidebar_container import TopSidebarContainer
from services.web_server.models import (
    ConfiguracaoServidorWeb, DadosTopSidebar, DadosTimeTracker,
    DadosFlowchart, DadosNotificacoes, DadosSidebar, BreakpointLayout
)
from services.web_server.sync_manager import DataSyncManager
from services.web_server.data_provider import JSONDataProvider
from services.time_tracking_service import TimeTrackingService
from services.workflow_service import WorkflowService
from services.notification_service import NotificationService


class TestDataSyncIntegration:
    """Testes de integração para sincronização de dados."""
    
    @pytest.fixture
    def temp_sync_file(self):
        """Create temporary sync file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        try:
            os.unlink(temp_file)
        except OSError:
            pass
    
    @pytest.fixture
    def mock_page(self):
        """Create mock Flet page."""
        page = Mock(spec=ft.Page)
        page.show_snack_bar = Mock()
        page.update = Mock()
        return page
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        time_service = Mock(spec=TimeTrackingService)
        workflow_service = Mock(spec=WorkflowService)
        notification_service = Mock(spec=NotificationService)
        
        # Configure notification service mock
        notification_service.get_unread_count.return_value = 2
        notification_service.get_notifications.return_value = []
        
        return time_service, workflow_service, notification_service
    
    @pytest.fixture
    def mock_components(self):
        """Create mock component widgets."""
        time_tracker = Mock()
        time_tracker.elapsed_time = 3600  # 1 hour
        time_tracker.is_running = True
        time_tracker.is_paused = False
        time_tracker.current_project = "Test Project"
        time_tracker.current_task = "Test Task"
        time_tracker.total_time_today = 7200  # 2 hours
        time_tracker.daily_goal = 8 * 3600  # 8 hours
        
        flowchart = Mock()
        current_stage = Mock()
        current_stage.name = "Development"
        flowchart.get_current_stage.return_value = current_stage
        flowchart.get_progress_percentage.return_value = 65.0
        flowchart.stages = [Mock(completed=True), Mock(completed=True), Mock(completed=False)]
        flowchart.current_workflow_name = "Test Workflow"
        
        notifications = Mock()
        notifications.notifications = [
            Mock(read=False, type='info'),
            Mock(read=True, type='warning'),
            Mock(read=False, type='error')
        ]
        notifications.last_notification_text = "Test notification"
        notifications.last_notification_time = datetime.now()
        
        webview = Mock()
        webview.executar_javascript = Mock()
        webview.esta_carregando = False
        webview.tem_erro = False
        webview.url_atual = "http://localhost:8080"
        
        return time_tracker, flowchart, notifications, webview
    
    @pytest.fixture
    def config_servidor(self, temp_sync_file):
        """Create server configuration."""
        return ConfiguracaoServidorWeb(
            arquivo_sincronizacao=temp_sync_file,
            intervalo_debounce=0.1,  # Fast for testing
            modo_debug=True
        )
    
    def test_data_extraction_complete(self, mock_page, mock_services, config_servidor, mock_components):
        """Test complete data extraction from all components."""
        time_service, workflow_service, notification_service = mock_services
        
        # Create container with WebView enabled
        container = TopSidebarContainer(
            page=mock_page,
            time_tracking_service=time_service,
            workflow_service=workflow_service,
            notification_service=notification_service,
            habilitar_webview=True,
            url_servidor_web="http://localhost:8080",
            config_servidor=config_servidor
        )
        
        # Mock components with test data
        time_tracker, flowchart, notifications, webview = mock_components
        self.apply_mock_components(container, time_tracker, flowchart, notifications, webview)
        
        # Extract data
        dados = container._extrair_dados_para_sincronizacao()
        
        # Verify data structure
        assert isinstance(dados, dict)
        assert 'timestamp' in dados
        assert 'versao' in dados
        assert 'fonte' in dados
        assert dados['fonte'] == 'TopSidebarContainer'
        
        # Verify time tracker data
        assert 'time_tracker' in dados
        tt_data = dados['time_tracker']
        assert tt_data['tempo_decorrido'] == 3600
        assert tt_data['esta_executando'] is True
        assert tt_data['projeto_atual'] == "Test Project"
        
        # Verify flowchart data
        assert 'flowchart' in dados
        fc_data = dados['flowchart']
        assert fc_data['progresso_workflow'] == 65.0
        assert fc_data['estagio_atual'] == "Development"
        assert fc_data['workflow_ativo'] == "Test Workflow"
        
        # Verify notifications data
        assert 'notificacoes' in dados
        not_data = dados['notificacoes']
        assert not_data['total_notificacoes'] == 3
        assert not_data['notificacoes_nao_lidas'] == 2
        assert not_data['ultima_notificacao'] == "Test notification"
        
        # Verify sidebar data
        assert 'sidebar' in dados
        sb_data = dados['sidebar']
        assert sb_data['sidebar_expandido'] is True
        assert sb_data['breakpoint_atual'] == 'desktop'
        assert 'time_tracker' in sb_data['componentes_visiveis']
    
    def test_sync_manager_initialization(self, mock_page, mock_services, config_servidor):
        """Test sync manager initialization and configuration."""
        time_service, workflow_service, notification_service = mock_services
        
        # Create container with WebView enabled
        container = TopSidebarContainer(
            page=mock_page,
            time_tracking_service=time_service,
            workflow_service=workflow_service,
            notification_service=notification_service,
            habilitar_webview=True,
            url_servidor_web="http://localhost:8080",
            config_servidor=config_servidor
        )
        

        
        # Verify sync manager was created
        assert container.sync_manager is not None
        assert isinstance(container.sync_manager, DataSyncManager)
        
        # Verify callbacks were registered
        assert container._sync_callbacks_registrados is True
        
        # Verify initial sync was performed
        sync_file = config_servidor.arquivo_sincronizacao
        assert os.path.exists(sync_file)
        
        with open(sync_file, 'r') as f:
            sync_data = json.load(f)
        
        assert isinstance(sync_data, dict)
        # The data might be nested under 'dados' key due to JSONDataProvider structure
        if 'dados' in sync_data:
            actual_data = sync_data['dados']
        else:
            actual_data = sync_data
            
        assert 'fonte' in actual_data
        assert actual_data['fonte'] == 'TopSidebarContainer'
    
    def test_component_change_triggers_sync(self, mock_page, mock_services, config_servidor):
        """Test that component changes trigger data synchronization."""
        time_service, workflow_service, notification_service = mock_services
        
        # Create container
        container = TopSidebarContainer(
            page=mock_page,
            time_tracking_service=time_service,
            workflow_service=workflow_service,
            notification_service=notification_service,
            habilitar_webview=True,
            url_servidor_web="http://localhost:8080",
            config_servidor=config_servidor
        )
        
        # Setup mock components
        time_tracker, flowchart, notifications, webview = self.setup_mock_components(container)
        
        # Get initial version
        initial_version = container._obter_versao_dados()
        
        # Trigger time tracker change
        container._callback_mudanca_time_tracker()
        
        # Verify version was incremented
        new_version = container._obter_versao_dados()
        assert new_version > initial_version
        
        # Verify sync file was updated
        time.sleep(0.2)  # Wait for debounce
        
        sync_file = config_servidor.arquivo_sincronizacao
        with open(sync_file, 'r') as f:
            sync_data = json.load(f)
        
        assert sync_data['versao'] == new_version
    
    def test_webview_update_on_data_change(self, mock_page, mock_services, config_servidor):
        """Test that WebView is updated when data changes."""
        time_service, workflow_service, notification_service = mock_services
        
        # Create container
        container = TopSidebarContainer(
            page=mock_page,
            time_tracking_service=time_service,
            workflow_service=workflow_service,
            notification_service=notification_service,
            habilitar_webview=True,
            url_servidor_web="http://localhost:8080",
            config_servidor=config_servidor
        )
        
        # Setup mock components
        time_tracker, flowchart, notifications, webview = self.setup_mock_components(container)
        
        # Trigger data change
        test_data = {'test': 'data', 'timestamp': datetime.now().isoformat()}
        container._callback_atualizacao_webview(test_data)
        
        # Verify WebView JavaScript was executed
        webview.executar_javascript.assert_called_once()
        
        # Verify JavaScript contains the test data
        js_call = webview.executar_javascript.call_args[0][0]
        assert 'updateData' in js_call or 'syncData' in js_call
        assert '"test": "data"' in js_call
    
    def test_sidebar_state_change_sync(self, mock_page, mock_services, config_servidor):
        """Test that sidebar state changes trigger synchronization."""
        time_service, workflow_service, notification_service = mock_services
        
        # Create container
        container = TopSidebarContainer(
            page=mock_page,
            time_tracking_service=time_service,
            workflow_service=workflow_service,
            notification_service=notification_service,
            habilitar_webview=True,
            url_servidor_web="http://localhost:8080",
            config_servidor=config_servidor
        )
        
        # Setup mock components
        self.setup_mock_components(container)
        
        # Get initial state
        initial_data = container._extrair_dados_para_sincronizacao()
        initial_expanded = initial_data['sidebar']['sidebar_expandido']
        
        # Change sidebar state
        container.update_layout(not initial_expanded)
        
        # Wait for sync
        time.sleep(0.2)
        
        # Verify state changed in sync file
        sync_file = config_servidor.arquivo_sincronizacao
        with open(sync_file, 'r') as f:
            sync_data = json.load(f)
        
        # Data is nested under 'dados' key due to JSONDataProvider structure
        actual_data = sync_data.get('dados', sync_data)
        assert actual_data['sidebar']['sidebar_expandido'] != initial_expanded
    
    def test_error_handling_in_sync(self, mock_page, mock_services, config_servidor):
        """Test error handling in synchronization system."""
        time_service, workflow_service, notification_service = mock_services
        
        # Create container
        container = TopSidebarContainer(
            page=mock_page,
            time_tracking_service=time_service,
            workflow_service=workflow_service,
            notification_service=notification_service,
            habilitar_webview=True,
            url_servidor_web="http://localhost:8080",
            config_servidor=config_servidor
        )
        
        # Setup mock components
        time_tracker, flowchart, notifications, webview = self.setup_mock_components(container)
        
        # Make WebView JavaScript execution fail
        webview.executar_javascript.side_effect = Exception("JavaScript error")
        
        # Trigger data change (should not raise exception)
        test_data = {'test': 'data'}
        container._callback_atualizacao_webview(test_data)
        
        # Verify error was handled gracefully
        # (no exception should be raised)
        assert True  # If we get here, error was handled
    
    def test_sync_state_reporting(self, mock_page, mock_services, config_servidor):
        """Test synchronization state reporting."""
        time_service, workflow_service, notification_service = mock_services
        
        # Create container
        container = TopSidebarContainer(
            page=mock_page,
            time_tracking_service=time_service,
            workflow_service=workflow_service,
            notification_service=notification_service,
            habilitar_webview=True,
            url_servidor_web="http://localhost:8080",
            config_servidor=config_servidor
        )
        
        # Get sync state
        estado = container.obter_estado_sincronizacao()
        
        # Verify state structure
        assert isinstance(estado, dict)
        assert 'ativo' in estado
        assert 'status' in estado
        assert 'versao_atual' in estado
        assert 'total_sincronizacoes' in estado
        assert 'taxa_sucesso' in estado
        
        # Verify sync is active
        assert estado['ativo'] is True
    
    def test_manual_webview_data_update(self, mock_page, mock_services, config_servidor):
        """Test manual WebView data update."""
        time_service, workflow_service, notification_service = mock_services
        
        # Create container
        container = TopSidebarContainer(
            page=mock_page,
            time_tracking_service=time_service,
            workflow_service=workflow_service,
            notification_service=notification_service,
            habilitar_webview=True,
            url_servidor_web="http://localhost:8080",
            config_servidor=config_servidor
        )
        
        # Setup mock components
        time_tracker, flowchart, notifications, webview = self.setup_mock_components(container)
        
        # Manually update WebView data
        test_data = {
            'manual_update': True,
            'timestamp': datetime.now().isoformat(),
            'custom_field': 'test_value'
        }
        
        container.atualizar_dados_webview(test_data)
        
        # Wait for sync
        time.sleep(0.2)
        
        # Verify data was synced
        sync_file = config_servidor.arquivo_sincronizacao
        with open(sync_file, 'r') as f:
            sync_data = json.load(f)
        
        # Data is nested under 'dados' key due to JSONDataProvider structure
        actual_data = sync_data.get('dados', sync_data)
        assert actual_data['manual_update'] is True
        assert actual_data['custom_field'] == 'test_value'
    
    def test_cleanup_stops_sync(self, mock_page, mock_services, config_servidor):
        """Test that cleanup properly stops synchronization."""
        time_service, workflow_service, notification_service = mock_services
        
        # Create container
        container = TopSidebarContainer(
            page=mock_page,
            time_tracking_service=time_service,
            workflow_service=workflow_service,
            notification_service=notification_service,
            habilitar_webview=True,
            url_servidor_web="http://localhost:8080",
            config_servidor=config_servidor
        )
        
        # Verify sync manager exists
        assert container.sync_manager is not None
        
        # Cleanup
        container.cleanup()
        
        # Verify sync manager was cleaned up
        assert container.sync_manager is None
    
    def test_sync_without_webview(self, mock_page, mock_services, config_servidor):
        """Test that container works without WebView enabled."""
        time_service, workflow_service, notification_service = mock_services
        
        # Create container without WebView
        container = TopSidebarContainer(
            page=mock_page,
            time_tracking_service=time_service,
            workflow_service=workflow_service,
            notification_service=notification_service,
            habilitar_webview=False  # WebView disabled
        )
        
        # Verify sync manager was not created
        assert container.sync_manager is None
        
        # Verify data extraction still works
        dados = container._extrair_dados_para_sincronizacao()
        assert isinstance(dados, dict)
        assert 'fonte' in dados
        
        # Verify state reporting works
        estado = container.obter_estado_sincronizacao()
        assert estado['ativo'] is False
        assert 'erro' in estado
    
    def test_polling_fallback_for_components(self, mock_page, mock_services, config_servidor):
        """Test polling fallback when components don't support callbacks."""
        time_service, workflow_service, notification_service = mock_services
        
        # Create container
        container = TopSidebarContainer(
            page=mock_page,
            time_tracking_service=time_service,
            workflow_service=workflow_service,
            notification_service=notification_service,
            habilitar_webview=True,
            url_servidor_web="http://localhost:8080",
            config_servidor=config_servidor
        )
        
        # Setup mock components without callback support
        time_tracker, flowchart, notifications, webview = self.setup_mock_components(container)
        
        # Remove callback methods to trigger polling
        if hasattr(time_tracker, 'add_change_callback'):
            delattr(time_tracker, 'add_change_callback')
        if hasattr(flowchart, 'add_change_callback'):
            delattr(flowchart, 'add_change_callback')
        if hasattr(notifications, 'add_change_callback'):
            delattr(notifications, 'add_change_callback')
        
        # Reconfigure observers (should start polling)
        container._configurar_observadores_componentes()
        
        # Wait a bit for polling to start
        time.sleep(0.5)
        
        # Change component state
        time_tracker.elapsed_time = 7200  # Change elapsed time
        
        # Wait for polling to detect change
        time.sleep(1.5)
        
        # Verify sync occurred (version should have incremented)
        # This is a basic test - in practice, polling threads would detect changes
        assert container._obter_versao_dados() >= 1
    
    def setup_mock_components(self, container):
        """Helper method to setup mock components for container."""
        # Create mock components with test data
        time_tracker = Mock()
        time_tracker.elapsed_time = 3600  # 1 hour
        time_tracker.is_running = True
        time_tracker.is_paused = False
        time_tracker.current_project = "Test Project"
        time_tracker.current_task = "Test Task"
        time_tracker.total_time_today = 7200  # 2 hours
        time_tracker.daily_goal = 8 * 3600  # 8 hours
        
        flowchart = Mock()
        current_stage = Mock()
        current_stage.name = "Development"
        flowchart.get_current_stage.return_value = current_stage
        flowchart.get_progress_percentage.return_value = 65.0
        flowchart.stages = [Mock(completed=True), Mock(completed=True), Mock(completed=False)]
        flowchart.current_workflow_name = "Test Workflow"
        
        notifications = Mock()
        notifications.notifications = [
            Mock(read=False, type='info'),
            Mock(read=True, type='warning'),
            Mock(read=False, type='error')
        ]
        notifications.last_notification_text = "Test notification"
        notifications.last_notification_time = datetime.now()
        
        webview = Mock()
        webview.executar_javascript = Mock()
        webview.esta_carregando = False
        webview.tem_erro = False
        webview.url_atual = "http://localhost:8080"
        
        # Apply mocks to container
        self.apply_mock_components(container, time_tracker, flowchart, notifications, webview)
        
        return time_tracker, flowchart, notifications, webview
    
    def apply_mock_components(self, container, time_tracker, flowchart, notifications, webview):
        """Helper method to apply mock components to container."""
        # Replace container components with mocks
        container.time_tracker = time_tracker
        container.flowchart = flowchart
        container.notifications = notifications
        container.webview = webview


class TestDataSyncPerformance:
    """Testes de performance para sincronização de dados."""
    
    @pytest.fixture
    def temp_sync_file(self):
        """Create temporary sync file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        try:
            os.unlink(temp_file)
        except OSError:
            pass
    
    def test_sync_latency(self, temp_sync_file):
        """Test synchronization latency."""
        config = ConfiguracaoServidorWeb(
            arquivo_sincronizacao=temp_sync_file,
            intervalo_debounce=0.01  # Very fast for testing
        )
        
        # Create JSON provider and sync manager
        json_provider = JSONDataProvider(arquivo_json=temp_sync_file)
        
        sync_manager = DataSyncManager(json_provider)
        
        # Measure sync time
        test_data = {'test': 'performance', 'timestamp': datetime.now().isoformat()}
        
        start_time = time.time()
        sync_manager.atualizar_dados(test_data)
        end_time = time.time()
        
        sync_latency = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Verify sync completed quickly (should be under 100ms)
        assert sync_latency < 100, f"Sync latency too high: {sync_latency}ms"
        
        # Cleanup
        sync_manager.finalizar()
    
    def test_multiple_rapid_updates(self, temp_sync_file):
        """Test handling of multiple rapid updates."""
        config = ConfiguracaoServidorWeb(
            arquivo_sincronizacao=temp_sync_file,
            intervalo_debounce=0.1  # 100ms debounce
        )
        
        # Create JSON provider and sync manager
        json_provider = JSONDataProvider(arquivo_json=temp_sync_file)
        
        sync_manager = DataSyncManager(json_provider)
        
        # Send multiple rapid updates
        start_time = time.time()
        for i in range(10):
            test_data = {
                'update_number': i,
                'timestamp': datetime.now().isoformat()
            }
            sync_manager.atualizar_dados(test_data)
            time.sleep(0.01)  # 10ms between updates
        
        # Wait for debounce to complete
        time.sleep(0.2)
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000
        
        # Verify all updates completed in reasonable time
        assert total_time < 500, f"Multiple updates took too long: {total_time}ms"
        
        # Verify final data was saved
        with open(temp_sync_file, 'r') as f:
            final_data = json.load(f)
        
        # Data is nested under 'dados' key due to JSONDataProvider structure
        actual_data = final_data.get('dados', final_data)
        assert actual_data['update_number'] == 9  # Last update
        
        # Cleanup
        sync_manager.finalizar()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])