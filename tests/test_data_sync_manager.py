"""
Testes unitários para o DataSyncManager.

Este módulo contém testes abrangentes para o gerenciador de sincronização
de dados, incluindo cenários de sucesso, falha, retry automático e
callbacks.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import threading
import time
import json
from datetime import datetime
from typing import Dict, Any

from services.web_server.sync_manager import DataSyncManager, ConfiguracaoRetry
from services.web_server.data_provider import DataProvider
from services.web_server.models import (
    EstadoSincronizacao, 
    StatusSincronizacao, 
    DadosTopSidebar,
    DadosTimeTracker,
    DadosFlowchart,
    DadosNotificacoes,
    DadosSidebar,
    BreakpointLayout
)
from services.web_server.exceptions import (
    SincronizacaoError, 
    ConfiguracaoError,
    CodigosErro
)


class MockDataProvider(DataProvider):
    """Mock do DataProvider para testes."""
    
    def __init__(self):
        self.dados = {}
        self.callback = None
        self.deve_falhar = False
        self.contador_chamadas = 0
        self.observador_ativo = False
    
    def salvar_dados(self, dados: Dict[str, Any]) -> None:
        self.contador_chamadas += 1
        if self.deve_falhar:
            raise Exception("Erro simulado no provedor")
        self.dados = dados.copy()
        
        # Simular callback de mudança apenas em caso de sucesso
        if self.callback and self.observador_ativo:
            threading.Thread(
                target=lambda: self.callback(dados),
                daemon=True
            ).start()
    
    def carregar_dados(self) -> Dict[str, Any]:
        self.contador_chamadas += 1
        if self.deve_falhar:
            raise Exception("Erro simulado no provedor")
        return self.dados.copy()
    
    def configurar_observador(self, callback) -> None:
        self.callback = callback
        self.observador_ativo = True
    
    def parar_observador(self) -> None:
        self.observador_ativo = False
        self.callback = None


class TestDataSyncManager(unittest.TestCase):
    """Testes para a classe DataSyncManager."""
    
    def setUp(self):
        """Configuração inicial para cada teste."""
        self.config_retry = ConfiguracaoRetry(
            max_tentativas=3,
            delay_inicial=0.1,  # Delay pequeno para testes rápidos
            multiplicador_backoff=2.0,
            delay_maximo=1.0,
            jitter=False  # Desabilitar jitter para testes determinísticos
        )
    
    def _criar_sync_manager(self):
        """Cria um novo DataSyncManager para cada teste."""
        mock_provider = MockDataProvider()
        
        # Mock do logger para evitar output durante testes
        with patch('services.web_server.sync_manager.logging.getLogger'):
            sync_manager = DataSyncManager(mock_provider, self.config_retry)
        
        return sync_manager, mock_provider
    
    def tearDown(self):
        """Limpeza após cada teste."""
        pass  # Cada teste gerencia seu próprio sync_manager
    
    def test_inicializacao_basica(self):
        """Testa inicialização básica do DataSyncManager."""
        sync_manager, mock_provider = self._criar_sync_manager()
        
        try:
            self.assertIsNotNone(sync_manager)
            self.assertEqual(sync_manager.provedor_dados, mock_provider)
            self.assertEqual(sync_manager.config_retry, self.config_retry)
            self.assertTrue(mock_provider.observador_ativo)
        finally:
            sync_manager.finalizar()
    
    def test_atualizar_dados_sucesso(self):
        """Testa atualização de dados com sucesso."""
        sync_manager, mock_provider = self._criar_sync_manager()
        
        try:
            dados_teste = {
                "timestamp": datetime.now().isoformat(),
                "teste": "valor",
                "numero": 123
            }
            
            # Atualizar dados
            sync_manager.atualizar_dados(dados_teste)
            
            # Verificar se os dados foram salvos
            self.assertEqual(mock_provider.dados, dados_teste)
            self.assertEqual(mock_provider.contador_chamadas, 1)
            
            # Verificar estado
            estado = sync_manager.obter_estado_sincronizacao()
            self.assertEqual(estado.status, StatusSincronizacao.ATIVO)
            self.assertEqual(estado.sincronizacoes_com_sucesso, 1)
            self.assertEqual(estado.tentativas_falha_consecutivas, 0)
        finally:
            sync_manager.finalizar()
    
    def test_atualizar_dados_com_retry(self):
        """Testa atualização de dados com retry automático."""
        sync_manager, mock_provider = self._criar_sync_manager()
        
        try:
            dados_teste = {"teste": "retry"}
            
            # Simular falha seguida de sucesso
            def falhar_duas_vezes(dados):
                mock_provider.contador_chamadas += 1
                if mock_provider.contador_chamadas < 2:
                    raise Exception("Erro simulado")
                # Sucesso na segunda tentativa
                mock_provider.dados = dados.copy()
            
            mock_provider.salvar_dados = falhar_duas_vezes
            
            # Atualizar dados (deve ter sucesso após retry)
            sync_manager.atualizar_dados(dados_teste)
            
            # Verificar que houve múltiplas tentativas
            self.assertEqual(mock_provider.contador_chamadas, 2)
        finally:
            sync_manager.finalizar()
    
    def test_atualizar_dados_falha_total(self):
        """Testa falha total após esgotar tentativas de retry."""
        sync_manager, mock_provider = self._criar_sync_manager()
        
        try:
            dados_teste = {"teste": "falha"}
            
            # Configurar para sempre falhar
            mock_provider.deve_falhar = True
            
            # Deve levantar exceção após esgotar tentativas
            with self.assertRaises(SincronizacaoError) as context:
                sync_manager.atualizar_dados(dados_teste)
            
            # Verificar código de erro
            self.assertEqual(context.exception.codigo_erro, CodigosErro.SYNC_TIMEOUT)
            
            # Verificar número de tentativas
            self.assertEqual(mock_provider.contador_chamadas, self.config_retry.max_tentativas)
            
            # Verificar estado de erro
            estado = sync_manager.obter_estado_sincronizacao()
            self.assertEqual(estado.status, StatusSincronizacao.ERRO)
            self.assertEqual(estado.sincronizacoes_com_erro, 1)
        finally:
            sync_manager.finalizar()
    
    def test_obter_dados_sucesso(self):
        """Testa obtenção de dados com sucesso."""
        sync_manager, mock_provider = self._criar_sync_manager()
        
        try:
            dados_teste = {"chave": "valor", "numero": 456}
            mock_provider.dados = dados_teste
            
            # Obter dados
            dados_obtidos = sync_manager.obter_dados()
            
            # Verificar dados
            self.assertEqual(dados_obtidos, dados_teste)
            self.assertEqual(mock_provider.contador_chamadas, 1)
        finally:
            sync_manager.finalizar()
    
    def test_obter_dados_com_cache(self):
        """Testa obtenção de dados usando cache."""
        sync_manager, mock_provider = self._criar_sync_manager()
        
        try:
            dados_teste = {"cache": "teste"}
            
            # Primeiro, atualizar dados (popula cache)
            sync_manager.atualizar_dados(dados_teste)
            contador_inicial = mock_provider.contador_chamadas
            
            # Obter dados (deve usar cache)
            dados_obtidos = sync_manager.obter_dados()
            
            # Verificar que não houve chamada adicional ao provedor
            self.assertEqual(mock_provider.contador_chamadas, contador_inicial)
            self.assertEqual(dados_obtidos, dados_teste)
        finally:
            sync_manager.finalizar()
    
    def test_callback_mudanca_dados(self):
        """Testa sistema de callbacks para mudanças de dados."""
        sync_manager, mock_provider = self._criar_sync_manager()
        
        try:
            callback_chamado = threading.Event()
            dados_recebidos = {}
            
            def callback_teste(dados):
                nonlocal dados_recebidos
                dados_recebidos = dados
                callback_chamado.set()
            
            # Registrar callback
            sync_manager.registrar_callback_mudanca(callback_teste)
            
            # Simular mudança de dados
            dados_teste = {"callback": "teste"}
            mock_provider.callback(dados_teste)
            
            # Aguardar callback
            self.assertTrue(callback_chamado.wait(timeout=1.0))
            self.assertEqual(dados_recebidos, dados_teste)
        finally:
            sync_manager.finalizar()
    
    def test_callback_erro(self):
        """Testa sistema de callbacks para erros."""
        sync_manager, mock_provider = self._criar_sync_manager()
        
        try:
            callback_erro_chamado = threading.Event()
            erro_recebido = {}
            
            def callback_erro_teste(mensagem, codigo):
                nonlocal erro_recebido
                erro_recebido = {"mensagem": mensagem, "codigo": codigo}
                callback_erro_chamado.set()
            
            # Registrar callback de erro
            sync_manager.registrar_callback_erro(callback_erro_teste)
            
            # Forçar erro
            mock_provider.deve_falhar = True
            
            try:
                sync_manager.atualizar_dados({"teste": "erro"})
            except SincronizacaoError:
                pass  # Esperado
            
            # Aguardar callback de erro
            self.assertTrue(callback_erro_chamado.wait(timeout=2.0))
            self.assertIn("mensagem", erro_recebido)
            self.assertIn("codigo", erro_recebido)
        finally:
            sync_manager.finalizar()
    
    def test_remover_callback(self):
        """Testa remoção de callbacks."""
        sync_manager, mock_provider = self._criar_sync_manager()
        
        try:
            def callback_teste(dados):
                pass
            
            # Registrar e remover callback
            sync_manager.registrar_callback_mudanca(callback_teste)
            self.assertEqual(len(sync_manager._callbacks), 1)
            
            removido = sync_manager.remover_callback_mudanca(callback_teste)
            self.assertTrue(removido)
            self.assertEqual(len(sync_manager._callbacks), 0)
            
            # Tentar remover callback inexistente
            removido = sync_manager.remover_callback_mudanca(callback_teste)
            self.assertFalse(removido)
        finally:
            sync_manager.finalizar()
    
    def test_validacao_dados_invalidos(self):
        """Testa validação de dados inválidos."""
        sync_manager, mock_provider = self._criar_sync_manager()
        
        try:
            # Dados não serializáveis
            dados_invalidos = {"funcao": lambda x: x}
            
            with self.assertRaises(SincronizacaoError) as context:
                sync_manager.atualizar_dados(dados_invalidos)
            
            self.assertEqual(context.exception.codigo_erro, CodigosErro.SYNC_FORMATO_INVALIDO)
        finally:
            sync_manager.finalizar()
    
    def test_pausar_retomar_sincronizacao(self):
        """Testa pausar e retomar sincronização."""
        sync_manager, mock_provider = self._criar_sync_manager()
        
        try:
            # Pausar
            sync_manager.pausar_sincronizacao()
            estado = sync_manager.obter_estado_sincronizacao()
            self.assertEqual(estado.status, StatusSincronizacao.PAUSADO)
            
            # Retomar
            sync_manager.retomar_sincronizacao()
            estado = sync_manager.obter_estado_sincronizacao()
            self.assertEqual(estado.status, StatusSincronizacao.ATIVO)
        finally:
            sync_manager.finalizar()
    
    def test_limpar_cache(self):
        """Testa limpeza de cache."""
        sync_manager, mock_provider = self._criar_sync_manager()
        
        try:
            # Popula cache
            sync_manager.atualizar_dados({"cache": "teste"})
            self.assertIsNotNone(sync_manager._dados_cache)
            
            # Limpar cache
            sync_manager.limpar_cache()
            self.assertIsNone(sync_manager._dados_cache)
        finally:
            sync_manager.finalizar()
    
    def test_dados_topsidebar_integracao(self):
        """Testa integração com DadosTopSidebar."""
        sync_manager, mock_provider = self._criar_sync_manager()
        
        try:
            # Criar dados estruturados
            dados_topsidebar = DadosTopSidebar()
            dados_topsidebar.time_tracker.tempo_decorrido = 3600
            dados_topsidebar.time_tracker.esta_executando = True
            dados_topsidebar.time_tracker.projeto_atual = "Projeto Teste"
            
            dados_topsidebar.flowchart.progresso_workflow = 0.75
            dados_topsidebar.flowchart.estagio_atual = "Implementação"
            
            dados_topsidebar.notificacoes.total_notificacoes = 5
            dados_topsidebar.notificacoes.notificacoes_nao_lidas = 2
            
            dados_topsidebar.sidebar.sidebar_expandido = True
            dados_topsidebar.sidebar.breakpoint_atual = BreakpointLayout.DESKTOP
            
            # Atualizar dados
            sync_manager.atualizar_dados_topsidebar(dados_topsidebar)
            
            # Obter dados de volta
            dados_recuperados = sync_manager.obter_dados_topsidebar()
            
            # Verificar dados
            self.assertIsNotNone(dados_recuperados)
            self.assertEqual(dados_recuperados.time_tracker.tempo_decorrido, 3600)
            self.assertTrue(dados_recuperados.time_tracker.esta_executando)
            self.assertEqual(dados_recuperados.time_tracker.projeto_atual, "Projeto Teste")
            self.assertEqual(dados_recuperados.flowchart.progresso_workflow, 0.75)
            self.assertEqual(dados_recuperados.flowchart.estagio_atual, "Implementação")
            self.assertEqual(dados_recuperados.notificacoes.total_notificacoes, 5)
            self.assertEqual(dados_recuperados.notificacoes.notificacoes_nao_lidas, 2)
            self.assertTrue(dados_recuperados.sidebar.sidebar_expandido)
            self.assertEqual(dados_recuperados.sidebar.breakpoint_atual, BreakpointLayout.DESKTOP)
        finally:
            sync_manager.finalizar()
    
    def test_callback_invalido(self):
        """Testa registro de callback inválido."""
        sync_manager, mock_provider = self._criar_sync_manager()
        
        try:
            with self.assertRaises(ConfiguracaoError) as context:
                sync_manager.registrar_callback_mudanca("não é função")
            
            self.assertEqual(context.exception.codigo_erro, CodigosErro.CONFIG_VALOR_INVALIDO)
            
            with self.assertRaises(ConfiguracaoError) as context:
                sync_manager.registrar_callback_erro(123)
            
            self.assertEqual(context.exception.codigo_erro, CodigosErro.CONFIG_VALOR_INVALIDO)
        finally:
            sync_manager.finalizar()
    
    def test_context_manager(self):
        """Testa uso como context manager."""
        mock_provider = MockDataProvider()
        
        with patch('services.web_server.sync_manager.logging.getLogger'):
            with DataSyncManager(mock_provider, self.config_retry) as sync_manager:
                self.assertIsNotNone(sync_manager)
                self.assertTrue(mock_provider.observador_ativo)
            
            # Após sair do context, deve estar finalizado
            self.assertFalse(mock_provider.observador_ativo)
    
    def test_retry_automatico_recuperacao(self):
        """Testa recuperação automática após erro."""
        sync_manager, mock_provider = self._criar_sync_manager()
        
        try:
            # Configurar para falhar inicialmente
            mock_provider.deve_falhar = True
            
            # Forçar erro
            try:
                sync_manager.atualizar_dados({"teste": "retry_auto"})
            except SincronizacaoError:
                pass
            
            # Verificar que está em estado de erro
            estado = sync_manager.obter_estado_sincronizacao()
            self.assertEqual(estado.status, StatusSincronizacao.ERRO)
            
            # Simular recuperação manual (teste simplificado)
            mock_provider.deve_falhar = False
            mock_provider.dados = {"recuperado": True}
            
            # Tentar operação novamente (simula recuperação)
            sync_manager.atualizar_dados({"teste": "recuperado"})
            
            # Verificar que recuperou
            estado = sync_manager.obter_estado_sincronizacao()
            self.assertEqual(estado.status, StatusSincronizacao.ATIVO)
        finally:
            sync_manager.finalizar()
    
    def test_metricas_performance(self):
        """Testa coleta de métricas de performance."""
        sync_manager, mock_provider = self._criar_sync_manager()
        
        try:
            # Realizar algumas sincronizações
            for i in range(3):
                sync_manager.atualizar_dados({"iteracao": i})
            
            # Verificar métricas
            estado = sync_manager.obter_estado_sincronizacao()
            self.assertEqual(estado.total_sincronizacoes, 3)
            self.assertEqual(estado.sincronizacoes_com_sucesso, 3)
            self.assertEqual(estado.sincronizacoes_com_erro, 0)
            self.assertIsNotNone(estado.tempo_ultima_sincronizacao_ms)
            self.assertIsNotNone(estado.tempo_medio_sincronizacao_ms)
            self.assertEqual(estado.calcular_taxa_sucesso(), 1.0)
        finally:
            sync_manager.finalizar()


class TestConfiguracaoRetry(unittest.TestCase):
    """Testes para a classe ConfiguracaoRetry."""
    
    def test_configuracao_padrao(self):
        """Testa configuração padrão do retry."""
        config = ConfiguracaoRetry()
        
        self.assertEqual(config.max_tentativas, 3)
        self.assertEqual(config.delay_inicial, 1.0)
        self.assertEqual(config.multiplicador_backoff, 2.0)
        self.assertEqual(config.delay_maximo, 30.0)
        self.assertTrue(config.jitter)
    
    def test_configuracao_personalizada(self):
        """Testa configuração personalizada do retry."""
        config = ConfiguracaoRetry(
            max_tentativas=5,
            delay_inicial=0.5,
            multiplicador_backoff=1.5,
            delay_maximo=10.0,
            jitter=False
        )
        
        self.assertEqual(config.max_tentativas, 5)
        self.assertEqual(config.delay_inicial, 0.5)
        self.assertEqual(config.multiplicador_backoff, 1.5)
        self.assertEqual(config.delay_maximo, 10.0)
        self.assertFalse(config.jitter)


if __name__ == '__main__':
    unittest.main()