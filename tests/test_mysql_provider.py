"""
Testes para MySQLDataProvider.

Este módulo contém testes mock para o provedor de dados MySQL,
preparando a infraestrutura para futura integração real.
"""

import pytest
import json
import logging
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from services.web_server.mysql_provider import MySQLDataProvider
from services.web_server.config import ConfiguracaoMySQL
from services.web_server.exceptions import SincronizacaoError


class TestConfiguracaoMySQL:
    """Testes para configuração MySQL."""
    
    def test_configuracao_padrao(self):
        """Testa criação de configuração com valores padrão."""
        config = ConfiguracaoMySQL()
        
        assert config.host == "localhost"
        assert config.porta == 3306
        assert config.usuario == "root"
        assert config.senha == ""
        assert config.banco_dados == "servidor_web_integrado"
        assert config.charset == "utf8mb4"
        assert config.pool_size == 5
        assert config.ssl_habilitado is False
    
    def test_configuracao_personalizada(self):
        """Testa criação de configuração personalizada."""
        config = ConfiguracaoMySQL(
            host="mysql.exemplo.com",
            porta=3307,
            usuario="app_user",
            senha="senha123",
            banco_dados="meu_banco",
            pool_size=10,
            ssl_habilitado=True
        )
        
        assert config.host == "mysql.exemplo.com"
        assert config.porta == 3307
        assert config.usuario == "app_user"
        assert config.senha == "senha123"
        assert config.banco_dados == "meu_banco"
        assert config.pool_size == 10
        assert config.ssl_habilitado is True
    
    def test_validacao_configuracao_valida(self):
        """Testa validação de configuração válida."""
        config = ConfiguracaoMySQL()
        # Não deve lançar exceção
        config.validar()
    
    def test_validacao_host_invalido(self):
        """Testa validação com host inválido."""
        config = ConfiguracaoMySQL(host="")
        
        with pytest.raises(Exception) as exc_info:
            config.validar()
        
        assert "Host MySQL deve ser uma string não vazia" in str(exc_info.value)
    
    def test_validacao_porta_invalida(self):
        """Testa validação com porta inválida."""
        config = ConfiguracaoMySQL(porta=0)
        
        with pytest.raises(Exception) as exc_info:
            config.validar()
        
        assert "Porta MySQL deve estar entre 1 e 65535" in str(exc_info.value)
    
    def test_validacao_usuario_invalido(self):
        """Testa validação com usuário inválido."""
        config = ConfiguracaoMySQL(usuario="")
        
        with pytest.raises(Exception) as exc_info:
            config.validar()
        
        assert "Usuário MySQL deve ser uma string não vazia" in str(exc_info.value)
    
    def test_obter_url_conexao_sem_senha(self):
        """Testa geração de URL de conexão sem senha."""
        config = ConfiguracaoMySQL(
            host="localhost",
            porta=3306,
            usuario="root",
            banco_dados="test_db"
        )
        
        url = config.obter_url_conexao(incluir_senha=False)
        assert url == "mysql://root@localhost:3306/test_db"
    
    def test_obter_url_conexao_com_senha(self):
        """Testa geração de URL de conexão com senha."""
        config = ConfiguracaoMySQL(
            host="localhost",
            porta=3306,
            usuario="root",
            senha="senha123",
            banco_dados="test_db"
        )
        
        url = config.obter_url_conexao(incluir_senha=True)
        assert url == "mysql://root:senha123@localhost:3306/test_db"
    
    def test_para_dict(self):
        """Testa conversão para dicionário."""
        config = ConfiguracaoMySQL(
            host="localhost",
            porta=3306,
            usuario="test_user"
        )
        
        dict_config = config.para_dict()
        
        assert isinstance(dict_config, dict)
        assert dict_config["host"] == "localhost"
        assert dict_config["porta"] == 3306
        assert dict_config["usuario"] == "test_user"


class TestMySQLDataProvider:
    """Testes para MySQLDataProvider."""
    
    @pytest.fixture
    def config_mysql(self):
        """Fixture com configuração MySQL para testes."""
        return ConfiguracaoMySQL(
            host="localhost",
            porta=3306,
            usuario="test_user",
            senha="test_pass",
            banco_dados="test_db"
        )
    
    @pytest.fixture
    def provider(self, config_mysql):
        """Fixture com provider MySQL para testes."""
        return MySQLDataProvider(config_mysql)
    
    def test_inicializacao(self, config_mysql):
        """Testa inicialização do provider."""
        provider = MySQLDataProvider(config_mysql)
        
        assert provider.configuracao == config_mysql
        assert provider.conexao is None
        assert provider.pool_conexoes is None
        assert provider.callbacks_mudanca == []
        assert provider._dados_cache == {}
        assert provider._versao_atual == 0
    
    def test_conectar_simulado(self, provider):
        """Testa conexão simulada."""
        provider.conectar()
        
        assert provider.conexao is not None
        assert provider.conexao["simulado"] is True
        assert provider.conexao["host"] == "localhost"
        assert provider.pool_conexoes is not None
        assert provider.pool_conexoes["simulado"] is True
    
    def test_desconectar(self, provider):
        """Testa desconexão."""
        # Primeiro conectar
        provider.conectar()
        assert provider.conexao is not None
        
        # Depois desconectar
        provider.desconectar()
        assert provider.conexao is None
        assert provider.pool_conexoes is None
    
    def test_salvar_dados_simulado(self, provider):
        """Testa salvamento de dados simulado."""
        dados_teste = {
            "usuario": "João",
            "tempo_decorrido": 3600,
            "projeto": "Teste"
        }
        
        provider.salvar_dados(dados_teste)
        
        assert provider._dados_cache == dados_teste
        assert provider._versao_atual == 1
    
    def test_carregar_dados_simulado(self, provider):
        """Testa carregamento de dados simulado."""
        # Primeiro salvar alguns dados
        dados_teste = {"chave": "valor", "numero": 42}
        provider.salvar_dados(dados_teste)
        
        # Depois carregar
        dados_carregados = provider.carregar_dados()
        
        assert dados_carregados == dados_teste
    
    def test_configurar_observador(self, provider):
        """Testa configuração de observador."""
        callback_mock = Mock()
        
        provider.configurar_observador(callback_mock)
        
        assert callback_mock in provider.callbacks_mudanca
    
    def test_remover_observador(self, provider):
        """Testa remoção de observador."""
        callback_mock = Mock()
        
        # Primeiro adicionar
        provider.configurar_observador(callback_mock)
        assert callback_mock in provider.callbacks_mudanca
        
        # Depois remover
        provider.remover_observador(callback_mock)
        assert callback_mock not in provider.callbacks_mudanca
    
    def test_callback_chamado_ao_salvar(self, provider):
        """Testa se callback é chamado ao salvar dados."""
        callback_mock = Mock()
        provider.configurar_observador(callback_mock)
        
        dados_teste = {"teste": "dados"}
        provider.salvar_dados(dados_teste)
        
        callback_mock.assert_called_once_with(dados_teste)
    
    def test_callback_com_erro_nao_interrompe(self, provider, caplog):
        """Testa que erro em callback não interrompe operação."""
        callback_com_erro = Mock(side_effect=Exception("Erro no callback"))
        callback_normal = Mock()
        
        provider.configurar_observador(callback_com_erro)
        provider.configurar_observador(callback_normal)
        
        dados_teste = {"teste": "dados"}
        
        # Não deve lançar exceção
        provider.salvar_dados(dados_teste)
        
        # Ambos callbacks devem ter sido chamados
        callback_com_erro.assert_called_once_with(dados_teste)
        callback_normal.assert_called_once_with(dados_teste)
        
        # Deve ter logado o erro
        assert "Erro ao executar callback" in caplog.text
    
    def test_obter_versao_dados(self, provider):
        """Testa obtenção da versão dos dados."""
        assert provider.obter_versao_dados() == 0
        
        provider.salvar_dados({"teste": "dados"})
        assert provider.obter_versao_dados() == 1
        
        provider.salvar_dados({"teste": "dados2"})
        assert provider.obter_versao_dados() == 2
    
    def test_verificar_conexao_sem_conexao(self, provider):
        """Testa verificação de conexão sem estar conectado."""
        assert provider.verificar_conexao() is False
    
    def test_verificar_conexao_com_conexao(self, provider):
        """Testa verificação de conexão estando conectado."""
        provider.conectar()
        assert provider.verificar_conexao() is True
    
    def test_criar_tabelas_simulado(self, provider):
        """Testa criação de tabelas simulada."""
        # Não deve lançar exceção
        provider.criar_tabelas()
    
    def test_migrar_de_json_simulado(self, provider):
        """Testa migração de JSON simulada."""
        caminho_json = "test_data.json"
        
        # Não deve lançar exceção
        provider.migrar_de_json(caminho_json)
    
    def test_erro_ao_conectar(self, provider):
        """Testa tratamento de erro ao conectar."""
        # Simular erro na conexão
        with patch.object(provider, '_simular_conexao', side_effect=Exception("Erro de conexão")):
            with pytest.raises(SincronizacaoError) as exc_info:
                provider.conectar()
            
            assert "Erro ao conectar ao MySQL" in str(exc_info.value)
    
    def test_erro_ao_salvar_dados(self, provider):
        """Testa tratamento de erro ao salvar dados."""
        # Simular erro no salvamento
        with patch.object(provider, '_simular_salvamento', side_effect=Exception("Erro de salvamento")):
            with pytest.raises(SincronizacaoError) as exc_info:
                provider.salvar_dados({"teste": "dados"})
            
            assert "Erro ao salvar dados no MySQL" in str(exc_info.value)
    
    def test_erro_ao_carregar_dados(self, provider):
        """Testa tratamento de erro ao carregar dados."""
        # Simular erro no carregamento
        with patch.object(provider, '_simular_carregamento', side_effect=Exception("Erro de carregamento")):
            with pytest.raises(SincronizacaoError) as exc_info:
                provider.carregar_dados()
            
            assert "Erro ao carregar dados do MySQL" in str(exc_info.value)
    
    def test_logging_configurado(self, provider):
        """Testa se logging está configurado corretamente."""
        assert provider.logger is not None
        assert provider.logger.name == "services.web_server.mysql_provider"


class TestIntegracaoMySQLProvider:
    """Testes de integração para MySQLDataProvider."""
    
    def test_fluxo_completo_simulado(self):
        """Testa fluxo completo de uso do provider."""
        config = ConfiguracaoMySQL(
            host="localhost",
            usuario="test_user",
            banco_dados="test_db"
        )
        
        provider = MySQLDataProvider(config)
        
        # Conectar
        provider.conectar()
        assert provider.verificar_conexao() is True
        
        # Configurar callback
        callback_mock = Mock()
        provider.configurar_observador(callback_mock)
        
        # Salvar dados
        dados_teste = {
            "usuarios": [
                {"id": 1, "nome": "João"},
                {"id": 2, "nome": "Maria"}
            ],
            "configuracoes": {
                "tema": "escuro",
                "idioma": "pt-BR"
            }
        }
        
        provider.salvar_dados(dados_teste)
        
        # Verificar callback foi chamado
        callback_mock.assert_called_once_with(dados_teste)
        
        # Carregar dados
        dados_carregados = provider.carregar_dados()
        assert dados_carregados == dados_teste
        
        # Verificar versão
        assert provider.obter_versao_dados() == 1
        
        # Desconectar
        provider.desconectar()
        assert provider.verificar_conexao() is False
    
    def test_multiplas_operacoes_sequenciais(self):
        """Testa múltiplas operações sequenciais."""
        config = ConfiguracaoMySQL()
        provider = MySQLDataProvider(config)
        
        provider.conectar()
        
        # Salvar dados múltiplas vezes
        for i in range(5):
            dados = {"iteracao": i, "timestamp": f"2024-01-{i+1:02d}"}
            provider.salvar_dados(dados)
            
            # Verificar versão incrementa
            assert provider.obter_versao_dados() == i + 1
            
            # Verificar dados foram salvos
            dados_carregados = provider.carregar_dados()
            assert dados_carregados["iteracao"] == i
    
    def test_multiplos_callbacks(self):
        """Testa múltiplos callbacks registrados."""
        config = ConfiguracaoMySQL()
        provider = MySQLDataProvider(config)
        
        # Registrar múltiplos callbacks
        callbacks = [Mock() for _ in range(3)]
        for callback in callbacks:
            provider.configurar_observador(callback)
        
        # Salvar dados
        dados_teste = {"teste": "multiplos_callbacks"}
        provider.salvar_dados(dados_teste)
        
        # Verificar todos callbacks foram chamados
        for callback in callbacks:
            callback.assert_called_once_with(dados_teste)
    
    @patch('services.web_server.mysql_provider.logging.getLogger')
    def test_logging_detalhado(self, mock_get_logger):
        """Testa logging detalhado das operações."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        config = ConfiguracaoMySQL()
        provider = MySQLDataProvider(config)
        
        # Operações que devem gerar logs
        provider.conectar()
        provider.salvar_dados({"teste": "logging"})
        provider.carregar_dados()
        provider.desconectar()
        
        # Verificar se logs foram chamados
        assert mock_logger.info.call_count >= 3
        assert mock_logger.debug.call_count >= 2