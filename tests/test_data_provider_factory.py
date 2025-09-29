"""
Testes para DataProviderFactory.

Este módulo contém testes para o factory pattern de provedores de dados,
incluindo seleção automática e validação de configurações.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from services.web_server.data_provider_factory import (
    DataProviderFactory,
    TipoProvedor,
    factory_provedor_dados,
    criar_provedor_dados,
    migrar_json_para_mysql
)
from services.web_server.data_provider import JSONDataProvider
from services.web_server.mysql_provider import MySQLDataProvider
from services.web_server.exceptions import SincronizacaoError


class TestTipoProvedor:
    """Testes para enum TipoProvedor."""
    
    def test_valores_enum(self):
        """Testa valores do enum."""
        assert TipoProvedor.JSON.value == "json"
        assert TipoProvedor.MYSQL.value == "mysql"
    
    def test_comparacao_enum(self):
        """Testa comparação de valores enum."""
        assert TipoProvedor.JSON != TipoProvedor.MYSQL
        assert TipoProvedor.JSON == TipoProvedor.JSON


class TestDataProviderFactory:
    """Testes para DataProviderFactory."""
    
    @pytest.fixture
    def factory(self):
        """Fixture com factory para testes."""
        return DataProviderFactory()
    
    def test_inicializacao(self, factory):
        """Testa inicialização da factory."""
        assert factory.logger is not None
        assert len(factory._provedores_registrados) == 2
        assert TipoProvedor.JSON in factory._provedores_registrados
        assert TipoProvedor.MYSQL in factory._provedores_registrados
    
    def test_criar_provedor_json(self, factory):
        """Testa criação de provedor JSON."""
        config = {
            "caminho_arquivo": "data/test.json",
            "intervalo_observacao": 2.0,
            "debounce_delay": 1.0
        }
        
        provider = factory.criar_provedor(TipoProvedor.JSON, config)
        
        assert isinstance(provider, JSONDataProvider)
        assert provider.arquivo_json == "data/test.json"
    
    def test_criar_provedor_mysql(self, factory):
        """Testa criação de provedor MySQL."""
        config = {
            "host": "mysql.exemplo.com",
            "porta": 3307,
            "usuario": "test_user",
            "senha": "test_pass",
            "banco_dados": "test_db"
        }
        
        provider = factory.criar_provedor(TipoProvedor.MYSQL, config)
        
        assert isinstance(provider, MySQLDataProvider)
        assert provider.configuracao.host == "mysql.exemplo.com"
        assert provider.configuracao.porta == 3307
        assert provider.configuracao.usuario == "test_user"
    
    def test_criar_provedor_tipo_invalido(self, factory):
        """Testa criação com tipo inválido."""
        # Criar tipo inválido
        tipo_invalido = Mock()
        tipo_invalido.value = "invalido"
        
        with pytest.raises(SincronizacaoError) as exc_info:
            factory.criar_provedor(tipo_invalido, {})
        
        assert "Tipo de provedor não suportado: invalido" in str(exc_info.value)
    
    def test_criar_provedor_automatico_json(self, factory):
        """Testa criação automática de provedor JSON."""
        config = {
            "tipo_provedor": "json",
            "json": {
                "caminho_arquivo": "data/auto_test.json"
            }
        }
        
        provider = factory.criar_provedor_automatico(config)
        
        assert isinstance(provider, JSONDataProvider)
        assert provider.arquivo_json == "data/auto_test.json"
    
    def test_criar_provedor_automatico_mysql(self, factory):
        """Testa criação automática de provedor MySQL."""
        config = {
            "tipo_provedor": "mysql",
            "mysql": {
                "host": "auto.mysql.com",
                "usuario": "auto_user"
            }
        }
        
        provider = factory.criar_provedor_automatico(config)
        
        assert isinstance(provider, MySQLDataProvider)
        assert provider.configuracao.host == "auto.mysql.com"
        assert provider.configuracao.usuario == "auto_user"
    
    def test_criar_provedor_automatico_padrao(self, factory):
        """Testa criação automática com configuração padrão."""
        config = {}
        
        provider = factory.criar_provedor_automatico(config)
        
        # Deve usar JSON como padrão
        assert isinstance(provider, JSONDataProvider)
    
    def test_criar_provedor_automatico_fallback(self, factory):
        """Testa fallback para JSON em caso de erro."""
        config = {
            "tipo_provedor": "mysql",
            "mysql": {
                "host": "",  # Host inválido que causará erro
                "usuario": ""
            }
        }
        
        provider = factory.criar_provedor_automatico(config)
        
        # Deve fazer fallback para JSON
        assert isinstance(provider, JSONDataProvider)
    
    def test_registrar_provedor_customizado(self, factory):
        """Testa registro de provedor customizado."""
        # Criar tipo customizado
        tipo_custom = Mock()
        tipo_custom.value = "custom"
        
        criador_mock = Mock(return_value=Mock())
        
        factory.registrar_provedor(tipo_custom, criador_mock)
        
        assert tipo_custom in factory._provedores_registrados
        assert factory._provedores_registrados[tipo_custom] == criador_mock
    
    def test_listar_provedores_disponiveis(self, factory):
        """Testa listagem de provedores disponíveis."""
        provedores = factory.listar_provedores_disponiveis()
        
        assert "json" in provedores
        assert "mysql" in provedores
        assert len(provedores) == 2
    
    def test_validar_configuracao_json_valida(self, factory):
        """Testa validação de configuração JSON válida."""
        config = {
            "caminho_arquivo": "test.json",
            "intervalo_observacao": 1.5
        }
        
        assert factory.validar_configuracao(TipoProvedor.JSON, config) is True
    
    def test_validar_configuracao_json_invalida(self, factory):
        """Testa validação de configuração JSON inválida."""
        config = {
            "caminho_arquivo": 123,  # Deve ser string
            "intervalo_observacao": -1  # Deve ser positivo
        }
        
        assert factory.validar_configuracao(TipoProvedor.JSON, config) is False
    
    def test_validar_configuracao_mysql_valida(self, factory):
        """Testa validação de configuração MySQL válida."""
        config = {
            "host": "localhost",
            "porta": 3306,
            "usuario": "test_user"
        }
        
        assert factory.validar_configuracao(TipoProvedor.MYSQL, config) is True
    
    def test_validar_configuracao_mysql_invalida(self, factory):
        """Testa validação de configuração MySQL inválida."""
        config = {
            "host": "",  # Host vazio
            "porta": 70000,  # Porta inválida
            "usuario": ""  # Usuário vazio
        }
        
        assert factory.validar_configuracao(TipoProvedor.MYSQL, config) is False
    
    def test_validar_configuracao_tipo_invalido(self, factory):
        """Testa validação com tipo inválido."""
        tipo_invalido = Mock()
        tipo_invalido.value = "invalido"
        
        assert factory.validar_configuracao(tipo_invalido, {}) is False


class TestFuncoesPadrao:
    """Testes para funções de conveniência."""
    
    def test_criar_provedor_dados_json(self):
        """Testa função de conveniência para JSON."""
        config = {
            "tipo_provedor": "json",
            "json": {"caminho_arquivo": "data/convenience_test.json"}
        }
        
        provider = criar_provedor_dados(config)
        
        assert isinstance(provider, JSONDataProvider)
        assert provider.arquivo_json == "data/convenience_test.json"
    
    def test_criar_provedor_dados_mysql(self):
        """Testa função de conveniência para MySQL."""
        config = {
            "tipo_provedor": "mysql",
            "mysql": {
                "host": "convenience.mysql.com",
                "usuario": "convenience_user"
            }
        }
        
        provider = criar_provedor_dados(config)
        
        assert isinstance(provider, MySQLDataProvider)
        assert provider.configuracao.host == "convenience.mysql.com"
    
    @patch('services.web_server.data_provider_factory.factory_provedor_dados')
    def test_migrar_json_para_mysql_sucesso(self, mock_factory):
        """Testa migração bem-sucedida de JSON para MySQL."""
        # Configurar mocks
        mock_json_provider = Mock()
        mock_mysql_provider = Mock()
        
        dados_teste = {"teste": "migracao", "usuarios": [1, 2, 3]}
        mock_json_provider.carregar_dados.return_value = dados_teste
        mock_mysql_provider.carregar_dados.return_value = dados_teste
        
        mock_factory.criar_provedor.side_effect = [mock_json_provider, mock_mysql_provider]
        
        # Executar migração
        config_json = {"caminho_arquivo": "source.json"}
        config_mysql = {"host": "localhost", "usuario": "test"}
        
        migrar_json_para_mysql(config_json, config_mysql)
        
        # Verificar chamadas
        assert mock_factory.criar_provedor.call_count == 2
        mock_json_provider.carregar_dados.assert_called_once()
        mock_mysql_provider.criar_tabelas.assert_called_once()
        mock_mysql_provider.salvar_dados.assert_called_once_with(dados_teste)
        mock_mysql_provider.carregar_dados.assert_called_once()
    
    @patch('services.web_server.data_provider_factory.factory_provedor_dados')
    def test_migrar_json_para_mysql_falha_integridade(self, mock_factory):
        """Testa migração com falha na verificação de integridade."""
        # Configurar mocks
        mock_json_provider = Mock()
        mock_mysql_provider = Mock()
        
        dados_originais = {"teste": "migracao", "count": 100, "extra": "campo"}
        dados_mysql = {"teste": "migracao", "count": 99}  # Dados com menos campos
        
        mock_json_provider.carregar_dados.return_value = dados_originais
        mock_mysql_provider.carregar_dados.return_value = dados_mysql
        
        mock_factory.criar_provedor.side_effect = [mock_json_provider, mock_mysql_provider]
        
        # Executar migração - deve falhar
        with pytest.raises(SincronizacaoError) as exc_info:
            migrar_json_para_mysql({}, {})
        
        assert "Falha na verificação de integridade" in str(exc_info.value)
    
    @patch('services.web_server.data_provider_factory.factory_provedor_dados')
    def test_migrar_json_para_mysql_erro_geral(self, mock_factory):
        """Testa migração com erro geral."""
        # Configurar mock para lançar exceção
        mock_factory.criar_provedor.side_effect = Exception("Erro de conexão")
        
        # Executar migração - deve falhar
        with pytest.raises(SincronizacaoError) as exc_info:
            migrar_json_para_mysql({}, {})
        
        assert "Erro na migração JSON para MySQL" in str(exc_info.value)


class TestInstanciaGlobal:
    """Testes para instância global da factory."""
    
    def test_instancia_global_existe(self):
        """Testa se instância global existe."""
        assert factory_provedor_dados is not None
        assert isinstance(factory_provedor_dados, DataProviderFactory)
    
    def test_instancia_global_funcional(self):
        """Testa se instância global é funcional."""
        provedores = factory_provedor_dados.listar_provedores_disponiveis()
        
        assert "json" in provedores
        assert "mysql" in provedores
    
    def test_criar_provedor_via_instancia_global(self):
        """Testa criação de provedor via instância global."""
        config = {"caminho_arquivo": "data/global_test.json"}
        
        provider = factory_provedor_dados.criar_provedor(TipoProvedor.JSON, config)
        
        assert isinstance(provider, JSONDataProvider)
        assert provider.arquivo_json == "data/global_test.json"


class TestIntegracaoFactory:
    """Testes de integração para DataProviderFactory."""
    
    def test_fluxo_completo_json(self):
        """Testa fluxo completo com provedor JSON."""
        factory = DataProviderFactory()
        
        # Validar configuração
        config = {
            "caminho_arquivo": "data/integration_test.json",
            "intervalo_observacao": 0.5
        }
        
        assert factory.validar_configuracao(TipoProvedor.JSON, config) is True
        
        # Criar provedor
        provider = factory.criar_provedor(TipoProvedor.JSON, config)
        
        assert isinstance(provider, JSONDataProvider)
        assert provider.arquivo_json == "data/integration_test.json"
    
    def test_fluxo_completo_mysql(self):
        """Testa fluxo completo com provedor MySQL."""
        factory = DataProviderFactory()
        
        # Validar configuração
        config = {
            "host": "integration.mysql.com",
            "porta": 3306,
            "usuario": "integration_user",
            "banco_dados": "integration_db"
        }
        
        assert factory.validar_configuracao(TipoProvedor.MYSQL, config) is True
        
        # Criar provedor
        provider = factory.criar_provedor(TipoProvedor.MYSQL, config)
        
        assert isinstance(provider, MySQLDataProvider)
        assert provider.configuracao.host == "integration.mysql.com"
        assert provider.configuracao.usuario == "integration_user"
        assert provider.configuracao.banco_dados == "integration_db"
    
    def test_selecao_automatica_baseada_em_config(self):
        """Testa seleção automática baseada em configuração."""
        factory = DataProviderFactory()
        
        # Configuração para JSON
        config_json = {
            "tipo_provedor": "json",
            "json": {"caminho_arquivo": "auto_json.json"}
        }
        
        provider_json = factory.criar_provedor_automatico(config_json)
        assert isinstance(provider_json, JSONDataProvider)
        
        # Configuração para MySQL
        config_mysql = {
            "tipo_provedor": "mysql",
            "mysql": {
                "host": "auto.mysql.com",
                "usuario": "auto_user"
            }
        }
        
        provider_mysql = factory.criar_provedor_automatico(config_mysql)
        assert isinstance(provider_mysql, MySQLDataProvider)
    
    def test_extensibilidade_factory(self):
        """Testa extensibilidade da factory com novos provedores."""
        factory = DataProviderFactory()
        
        # Criar provedor customizado
        class CustomProvider:
            def __init__(self, config):
                self.config = config
        
        def criar_custom_provider(config):
            return CustomProvider(config)
        
        # Registrar novo tipo
        tipo_custom = Mock()
        tipo_custom.value = "custom"
        
        factory.registrar_provedor(tipo_custom, criar_custom_provider)
        
        # Verificar registro
        assert tipo_custom in factory._provedores_registrados
        assert "custom" in factory.listar_provedores_disponiveis()
        
        # Criar instância do provedor customizado
        provider = factory.criar_provedor(tipo_custom, {"test": "config"})
        assert isinstance(provider, CustomProvider)
        assert provider.config == {"test": "config"}