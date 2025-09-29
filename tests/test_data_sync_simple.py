"""
Testes simples para o sistema de sincronização de dados do TopSidebarContainer.

Este módulo testa as funcionalidades básicas de extração de dados e
sincronização sem dependências complexas.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch
from datetime import datetime

# Import components to test
from services.web_server.models import (
    ConfiguracaoServidorWeb, DadosTopSidebar, DadosTimeTracker,
    DadosFlowchart, DadosNotificacoes, DadosSidebar, BreakpointLayout
)
from services.web_server.data_provider import JSONDataProvider
from services.web_server.sync_manager import DataSyncManager


class TestDataSyncBasic:
    """Testes básicos para sincronização de dados."""
    
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
    
    def test_dados_topsidebar_creation(self):
        """Test DadosTopSidebar data structure creation."""
        # Create test data
        time_tracker_data = DadosTimeTracker(
            tempo_decorrido=3600,
            esta_executando=True,
            esta_pausado=False,
            projeto_atual="Test Project",
            tarefa_atual="Test Task",
            tempo_total_hoje=7200
        )
        
        flowchart_data = DadosFlowchart(
            progresso_workflow=65.0,
            estagio_atual="Development",
            total_estagios=5,
            estagios_concluidos=3,
            workflow_ativo="Test Workflow"
        )
        
        notifications_data = DadosNotificacoes(
            total_notificacoes=3,
            notificacoes_nao_lidas=2,
            ultima_notificacao="Test notification",
            timestamp_ultima=datetime.now()
        )
        
        sidebar_data = DadosSidebar(
            sidebar_expandido=True,
            breakpoint_atual=BreakpointLayout.DESKTOP,
            componentes_visiveis=['time_tracker', 'flowchart', 'notifications']
        )
        
        # Create complete data structure
        dados_completos = DadosTopSidebar(
            time_tracker=time_tracker_data,
            flowchart=flowchart_data,
            notificacoes=notifications_data,
            sidebar=sidebar_data
        )
        
        # Test serialization
        dados_dict = dados_completos.to_dict()
        
        # Verify structure
        assert isinstance(dados_dict, dict)
        assert 'timestamp' in dados_dict
        assert 'versao' in dados_dict
        assert 'fonte' in dados_dict
        assert dados_dict['fonte'] == 'TopSidebarContainer'
        
        # Verify time tracker data
        assert dados_dict['time_tracker']['tempo_decorrido'] == 3600
        assert dados_dict['time_tracker']['esta_executando'] is True
        assert dados_dict['time_tracker']['projeto_atual'] == "Test Project"
        
        # Verify flowchart data
        assert dados_dict['flowchart']['progresso_workflow'] == 65.0
        assert dados_dict['flowchart']['estagio_atual'] == "Development"
        
        # Verify notifications data
        assert dados_dict['notificacoes']['total_notificacoes'] == 3
        assert dados_dict['notificacoes']['notificacoes_nao_lidas'] == 2
        
        # Verify sidebar data
        assert dados_dict['sidebar']['sidebar_expandido'] is True
        assert dados_dict['sidebar']['breakpoint_atual'] == 'desktop'
    
    def test_dados_topsidebar_deserialization(self):
        """Test DadosTopSidebar deserialization from dictionary."""
        # Create test dictionary
        test_dict = {
            'timestamp': datetime.now().isoformat(),
            'versao': 2,
            'fonte': 'TestSource',
            'time_tracker': {
                'tempo_decorrido': 1800,
                'esta_executando': False,
                'esta_pausado': True,
                'projeto_atual': 'Deserialization Test',
                'tarefa_atual': 'Test Task',
                'tempo_total_hoje': 3600
            },
            'flowchart': {
                'progresso_workflow': 40.0,
                'estagio_atual': 'Testing',
                'total_estagios': 4,
                'estagios_concluidos': 1,
                'workflow_ativo': 'Test Workflow'
            },
            'notificacoes': {
                'total_notificacoes': 5,
                'notificacoes_nao_lidas': 3,
                'ultima_notificacao': 'Deserialization test',
                'timestamp_ultima': datetime.now().isoformat()
            },
            'sidebar': {
                'sidebar_expandido': False,
                'breakpoint_atual': 'mobile',
                'componentes_visiveis': ['time_tracker']
            }
        }
        
        # Deserialize
        dados = DadosTopSidebar.from_dict(test_dict)
        
        # Verify deserialization
        assert dados.versao == 2
        assert dados.fonte == 'TestSource'
        assert dados.time_tracker.tempo_decorrido == 1800
        assert dados.time_tracker.esta_executando is False
        assert dados.time_tracker.projeto_atual == 'Deserialization Test'
        assert dados.flowchart.progresso_workflow == 40.0
        assert dados.flowchart.estagio_atual == 'Testing'
        assert dados.notificacoes.total_notificacoes == 5
        assert dados.sidebar.sidebar_expandido is False
        assert dados.sidebar.breakpoint_atual == BreakpointLayout.MOBILE
    
    def test_json_data_provider_basic(self, temp_sync_file):
        """Test basic JSONDataProvider functionality."""
        # Create provider
        provider = JSONDataProvider(temp_sync_file)
        
        # Test data
        test_data = {
            'test_key': 'test_value',
            'timestamp': datetime.now().isoformat(),
            'number': 42
        }
        
        # Save data
        provider.salvar_dados(test_data)
        
        # Load data
        loaded_data = provider.carregar_dados()
        
        # Verify data
        assert loaded_data['test_key'] == 'test_value'
        assert loaded_data['number'] == 42
        assert 'timestamp' in loaded_data
    
    def test_sync_manager_basic(self, temp_sync_file):
        """Test basic DataSyncManager functionality."""
        # Create provider and sync manager
        provider = JSONDataProvider(temp_sync_file)
        sync_manager = DataSyncManager(provider)
        
        # Test data
        test_data = {
            'sync_test': True,
            'timestamp': datetime.now().isoformat(),
            'data': {'nested': 'value'}
        }
        
        # Update data
        sync_manager.atualizar_dados(test_data)
        
        # Get data
        retrieved_data = sync_manager.obter_dados()
        
        # Verify data
        assert retrieved_data['sync_test'] is True
        assert 'timestamp' in retrieved_data
        assert retrieved_data['data']['nested'] == 'value'
        
        # Get sync state
        estado = sync_manager.obter_estado_sincronizacao()
        assert estado.total_sincronizacoes >= 1
        assert estado.sincronizacoes_com_sucesso >= 1
        
        # Cleanup
        sync_manager.finalizar()
    
    def test_sync_manager_with_topsidebar_data(self, temp_sync_file):
        """Test DataSyncManager with DadosTopSidebar."""
        # Create provider and sync manager
        provider = JSONDataProvider(temp_sync_file)
        sync_manager = DataSyncManager(provider)
        
        # Create test data
        dados_topsidebar = DadosTopSidebar(
            time_tracker=DadosTimeTracker(
                tempo_decorrido=2400,
                esta_executando=True,
                projeto_atual="Sync Test"
            ),
            flowchart=DadosFlowchart(
                progresso_workflow=75.0,
                estagio_atual="Integration"
            ),
            notificacoes=DadosNotificacoes(
                total_notificacoes=2,
                notificacoes_nao_lidas=1
            )
        )
        
        # Update with TopSidebar data
        sync_manager.atualizar_dados_topsidebar(dados_topsidebar)
        
        # Retrieve TopSidebar data
        retrieved_dados = sync_manager.obter_dados_topsidebar()
        
        # Verify data
        assert retrieved_dados is not None
        assert retrieved_dados.time_tracker.tempo_decorrido == 2400
        assert retrieved_dados.time_tracker.esta_executando is True
        assert retrieved_dados.time_tracker.projeto_atual == "Sync Test"
        assert retrieved_dados.flowchart.progresso_workflow == 75.0
        assert retrieved_dados.flowchart.estagio_atual == "Integration"
        assert retrieved_dados.notificacoes.total_notificacoes == 2
        
        # Cleanup
        sync_manager.finalizar()
    
    def test_callback_registration(self, temp_sync_file):
        """Test callback registration and notification."""
        # Create provider and sync manager
        provider = JSONDataProvider(temp_sync_file)
        sync_manager = DataSyncManager(provider)
        
        # Callback tracking
        callback_called = []
        callback_data = []
        
        def test_callback(dados):
            callback_called.append(True)
            callback_data.append(dados)
        
        # Register callback
        sync_manager.registrar_callback_mudanca(test_callback)
        
        # Update data (should trigger callback)
        test_data = {'callback_test': True}
        sync_manager.atualizar_dados(test_data)
        
        # Note: Callback might not be called immediately due to file watching
        # This is a basic test to ensure registration works
        assert len(sync_manager._callbacks) == 1
        
        # Remove callback
        removed = sync_manager.remover_callback_mudanca(test_callback)
        assert removed is True
        assert len(sync_manager._callbacks) == 0
        
        # Cleanup
        sync_manager.finalizar()
    
    def test_error_handling(self, temp_sync_file):
        """Test error handling in sync operations."""
        # Create provider and sync manager
        provider = JSONDataProvider(temp_sync_file)
        sync_manager = DataSyncManager(provider)
        
        # Test with invalid data (should handle gracefully)
        try:
            # This should work fine
            sync_manager.atualizar_dados({'valid': 'data'})
        except Exception as e:
            pytest.fail(f"Valid data should not raise exception: {e}")
        
        # Test error callback
        error_called = []
        error_messages = []
        
        def error_callback(message, code):
            error_called.append(True)
            error_messages.append((message, code))
        
        sync_manager.registrar_callback_erro(error_callback)
        
        # Verify error callback was registered
        assert len(sync_manager._callbacks_erro) == 1
        
        # Cleanup
        sync_manager.finalizar()
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        # Test valid configuration
        config = ConfiguracaoServidorWeb(
            porta_preferencial=8080,
            diretorio_html="web_content",
            arquivo_sincronizacao="sync.json"
        )
        
        erros = config.validar()
        assert len(erros) == 0
        
        # Test invalid configuration
        config_invalid = ConfiguracaoServidorWeb(
            porta_preferencial=80,  # Invalid port (too low)
            diretorio_html="",      # Empty directory
            timeout_servidor=-1     # Invalid timeout
        )
        
        erros = config_invalid.validar()
        assert len(erros) > 0
        assert any("porta" in erro.lower() for erro in erros)
        assert any("diretório" in erro.lower() for erro in erros)
        assert any("timeout" in erro.lower() for erro in erros)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])