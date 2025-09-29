"""
Testes para o sistema robusto de tratamento de erros e recuperação.

Este módulo testa todas as funcionalidades implementadas na tarefa 10:
- Tratamento de falha na inicialização do servidor com portas alternativas
- Modo fallback quando WebView não estiver disponível
- Sistema de retry com backoff exponencial para sincronização
- Páginas de erro personalizadas em português
- Logs de auditoria para operações críticas
"""

import pytest
import tempfile
import shutil
import json
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Imports do sistema
from services.web_server.server_manager import WebServerManager
from services.web_server.sync_manager import DataSyncManager, ConfiguracaoRetry
from services.web_server.fallback_handler import FallbackHandler, ConfiguracaoFallback
from services.web_server.audit_logger import (
    AuditLogger, TipoEvento, NivelSeveridade, EventoAuditoria
)
from services.web_server.models import ConfiguracaoServidorWeb
from services.web_server.exceptions import (
    ServidorWebError, RecursoIndisponivelError, SincronizacaoError, CodigosErro
)
# from services.web_server.json_provider import JSONDataProvider


class TestServidorPortasAlternativas:
    """Testa o tratamento de falha na inicialização com portas alternativas."""
    
    def setup_method(self):
        """Configuração para cada teste."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = ConfiguracaoServidorWeb(
            porta_preferencial=8080,
            portas_alternativas=[8081, 8082, 8083],
            diretorio_html=self.temp_dir,
            modo_debug=True
        )
    
    def teardown_method(self):
        """Limpeza após cada teste."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_porta_preferencial_disponivel(self):
        """Testa uso da porta preferencial quando disponível."""
        with patch('socket.socket') as mock_socket:
            mock_socket.return_value.__enter__.return_value.connect_ex.return_value = 1  # Porta disponível
            
            manager = WebServerManager(self.config)
            porta = manager._encontrar_porta_disponivel()
            
            assert porta == 8080
    
    def test_fallback_para_portas_alternativas(self):
        """Testa fallback para portas alternativas."""
        with patch('socket.socket') as mock_socket:
            # Simular porta preferencial ocupada, primeira alternativa disponível
            mock_socket.return_value.__enter__.return_value.connect_ex.side_effect = [0, 1, 1, 1]
            
            manager = WebServerManager(self.config)
            porta = manager._encontrar_porta_disponivel()
            
            assert porta == 8081
    
    def test_busca_automatica_quando_todas_ocupadas(self):
        """Testa busca automática quando todas as portas configuradas estão ocupadas."""
        with patch('socket.socket') as mock_socket:
            # Simular todas as portas configuradas ocupadas, mas 8084 disponível
            def mock_connect_ex(address):
                host, port = address
                if port in [8080, 8081, 8082, 8083]:
                    return 0  # Ocupada
                elif port == 8084:
                    return 1  # Disponível
                else:
                    return 0  # Outras ocupadas
            
            mock_socket.return_value.__enter__.return_value.connect_ex.side_effect = mock_connect_ex
            
            manager = WebServerManager(self.config)
            porta = manager._encontrar_porta_disponivel()
            
            assert porta == 8084
    
    def test_excecao_quando_nenhuma_porta_disponivel(self):
        """Testa exceção quando nenhuma porta está disponível."""
        with patch('socket.socket') as mock_socket:
            # Simular todas as portas ocupadas
            mock_socket.return_value.__enter__.return_value.connect_ex.return_value = 0
            
            manager = WebServerManager(self.config)
            
            with pytest.raises(RecursoIndisponivelError) as exc_info:
                manager._encontrar_porta_disponivel()
            
            assert "Nenhuma porta disponível" in str(exc_info.value)
            assert exc_info.value.codigo_erro == CodigosErro.RECURSO_PORTA_INDISPONIVEL


class TestFallbackHandler:
    """Testa o sistema de fallback quando WebView não está disponível."""
    
    def setup_method(self):
        """Configuração para cada teste."""
        self.mock_page = Mock()
        self.mock_page.overlay = []
        self.config = ConfiguracaoFallback(
            mostrar_notificacoes=True,
            modo_texto_habilitado=True
        )
    
    def test_ativacao_fallback(self):
        """Testa ativação do modo fallback."""
        handler = FallbackHandler(self.mock_page, self.config)
        
        container = handler.ativar_fallback("WebView não disponível")
        
        assert handler.esta_ativo
        assert container is not None
        assert hasattr(container, 'content')
    
    def test_atualizacao_dados_fallback(self):
        """Testa atualização de dados no modo fallback."""
        handler = FallbackHandler(self.mock_page, self.config)
        handler.ativar_fallback("Teste")
        
        dados_teste = {
            "tempo_decorrido": 300,
            "esta_executando": True,
            "projeto_atual": "Teste"
        }
        
        handler.atualizar_dados(dados_teste)
        
        assert handler.dados_atuais == dados_teste
        assert handler._ultima_atualizacao is not None
    
    def test_desativacao_fallback(self):
        """Testa desativação do modo fallback."""
        handler = FallbackHandler(self.mock_page, self.config)
        handler.ativar_fallback("Teste")
        
        assert handler.esta_ativo
        
        handler.desativar_fallback()
        
        assert not handler.esta_ativo
    
    def test_callback_atualizacao(self):
        """Testa registro e execução de callbacks."""
        handler = FallbackHandler(self.mock_page, self.config)
        handler.ativar_fallback("Teste")
        
        callback_executado = False
        dados_recebidos = None
        
        def callback(dados):
            nonlocal callback_executado, dados_recebidos
            callback_executado = True
            dados_recebidos = dados
        
        handler.registrar_callback_atualizacao(callback)
        
        dados_teste = {"teste": "valor"}
        handler.atualizar_dados(dados_teste)
        
        assert callback_executado
        assert dados_recebidos == dados_teste


class TestRetryComBackoff:
    """Testa o sistema de retry com backoff exponencial."""
    
    def setup_method(self):
        """Configuração para cada teste."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_retry = ConfiguracaoRetry(
            max_tentativas=3,
            delay_inicial=0.1,  # Delay pequeno para testes
            multiplicador_backoff=2.0,
            delay_maximo=1.0,
            jitter=False  # Desabilitar para testes determinísticos
        )
    
    def teardown_method(self):
        """Limpeza após cada teste."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_retry_com_sucesso_na_segunda_tentativa(self):
        """Testa retry bem-sucedido na segunda tentativa."""
        # Criar provedor que falha na primeira tentativa
        mock_provider = Mock()
        mock_provider.salvar_dados.side_effect = [Exception("Falha temporária"), None]
        mock_provider.configurar_observador = Mock()
        
        manager = DataSyncManager(mock_provider, self.config_retry)
        
        dados_teste = {"teste": "valor"}
        manager.atualizar_dados(dados_teste)
        
        # Verificar que foi chamado duas vezes
        assert mock_provider.salvar_dados.call_count == 2
    
    def test_retry_falha_apos_max_tentativas(self):
        """Testa falha após esgotar todas as tentativas."""
        # Criar provedor que sempre falha
        mock_provider = Mock()
        mock_provider.salvar_dados.side_effect = Exception("Falha persistente")
        mock_provider.configurar_observador = Mock()
        
        manager = DataSyncManager(mock_provider, self.config_retry)
        
        dados_teste = {"teste": "valor"}
        
        with pytest.raises(SincronizacaoError):
            manager.atualizar_dados(dados_teste)
        
        # Verificar que tentou o máximo de vezes
        assert mock_provider.salvar_dados.call_count == self.config_retry.max_tentativas
    
    def test_backoff_exponencial(self):
        """Testa se o delay aumenta exponencialmente."""
        mock_provider = Mock()
        mock_provider.salvar_dados.side_effect = [
            Exception("Falha 1"),
            Exception("Falha 2"),
            None  # Sucesso na terceira
        ]
        mock_provider.configurar_observador = Mock()
        
        manager = DataSyncManager(mock_provider, self.config_retry)
        
        start_time = time.time()
        dados_teste = {"teste": "valor"}
        manager.atualizar_dados(dados_teste)
        end_time = time.time()
        
        # Verificar que levou tempo suficiente para os delays
        # Delay esperado: 0.1 + 0.2 = 0.3 segundos mínimo
        assert end_time - start_time >= 0.25  # Margem para processamento
    
    def test_recuperacao_automatica(self):
        """Testa recuperação automática após falhas."""
        mock_provider = Mock()
        mock_provider.configurar_observador = Mock()
        mock_provider.carregar_dados.side_effect = [
            Exception("Falha"),
            {"dados": "recuperados"}  # Sucesso na segunda tentativa
        ]
        
        manager = DataSyncManager(mock_provider, self.config_retry)
        
        # Simular erro inicial
        manager._tratar_erro_sincronizacao("Erro teste", CodigosErro.SYNC_TIMEOUT)
        
        # Aguardar um pouco para a thread de retry
        time.sleep(0.2)
        
        # Verificar se tentou recuperar
        assert mock_provider.carregar_dados.call_count >= 1


class TestPaginasErroPersonalizadas:
    """Testa as páginas de erro personalizadas em português."""
    
    def test_pagina_erro_servidor_existe(self):
        """Testa se a página de erro do servidor existe."""
        caminho = Path("web_content/erro_servidor.html")
        assert caminho.exists()
        
        conteudo = caminho.read_text(encoding='utf-8')
        assert "Servidor Temporariamente Indisponível" in conteudo
        assert "lang=\"pt-BR\"" in conteudo
    
    def test_pagina_erro_carregamento_existe(self):
        """Testa se a página de erro de carregamento existe."""
        caminho = Path("web_content/erro_carregamento.html")
        assert caminho.exists()
        
        conteudo = caminho.read_text(encoding='utf-8')
        assert "Falha no Carregamento" in conteudo
        assert "lang=\"pt-BR\"" in conteudo
    
    def test_pagina_erro_sincronizacao_existe(self):
        """Testa se a página de erro de sincronização existe."""
        caminho = Path("web_content/erro_sincronizacao.html")
        assert caminho.exists()
        
        conteudo = caminho.read_text(encoding='utf-8')
        assert "Erro de Sincronização" in conteudo
        assert "lang=\"pt-BR\"" in conteudo
    
    def test_conteudo_em_portugues(self):
        """Testa se o conteúdo está em português."""
        paginas = [
            "web_content/erro_servidor.html",
            "web_content/erro_carregamento.html",
            "web_content/erro_sincronizacao.html"
        ]
        
        for pagina in paginas:
            conteudo = Path(pagina).read_text(encoding='utf-8')
            
            # Verificar elementos em português
            assert any(palavra in conteudo.lower() for palavra in [
                "erro", "falha", "servidor", "carregamento", "sincronização",
                "tentar novamente", "recarregar", "recuperação"
            ])
            
            # Verificar que não há texto em inglês comum
            assert "error" not in conteudo.lower() or "erro" in conteudo.lower()


class TestAuditLogger:
    """Testa o sistema de logs de auditoria."""
    
    def setup_method(self):
        """Configuração para cada teste."""
        self.temp_dir = tempfile.mkdtemp()
        self.audit_logger = AuditLogger(
            diretorio_logs=self.temp_dir,
            arquivo_base="teste_auditoria",
            rotacao_diaria=False,
            buffer_size=5,
            flush_interval=1
        )
    
    def teardown_method(self):
        """Limpeza após cada teste."""
        self.audit_logger.finalizar()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_registro_evento_simples(self):
        """Testa registro de evento simples."""
        self.audit_logger.registrar_evento(
            tipo_evento=TipoEvento.SERVIDOR_INICIADO,
            severidade=NivelSeveridade.INFO,
            componente="Teste",
            mensagem="Evento de teste",
            detalhes={"chave": "valor"}
        )
        
        # Forçar flush
        self.audit_logger.flush()
        
        # Verificar se arquivo foi criado
        arquivo_log = Path(self.temp_dir) / "teste_auditoria.json"
        assert arquivo_log.exists()
        
        # Verificar conteúdo
        eventos = json.loads(arquivo_log.read_text(encoding='utf-8'))
        assert len(eventos) >= 1  # Pelo menos o evento de teste
        
        evento_teste = next((e for e in eventos if e['mensagem'] == 'Evento de teste'), None)
        assert evento_teste is not None
        assert evento_teste['tipo_evento'] == TipoEvento.SERVIDOR_INICIADO.value
        assert evento_teste['severidade'] == NivelSeveridade.INFO.value
    
    def test_flush_automatico_por_buffer_cheio(self):
        """Testa flush automático quando buffer fica cheio."""
        # Registrar eventos até encher o buffer
        for i in range(6):  # Buffer size é 5
            self.audit_logger.registrar_evento(
                tipo_evento=TipoEvento.SYNC_SUCESSO,
                severidade=NivelSeveridade.INFO,
                componente="Teste",
                mensagem=f"Evento {i}",
                detalhes={"numero": i}
            )
        
        # Aguardar um pouco para flush
        time.sleep(0.1)
        
        # Verificar se arquivo foi criado
        arquivo_log = Path(self.temp_dir) / "teste_auditoria.json"
        assert arquivo_log.exists()
        
        # Verificar que eventos foram escritos
        eventos = json.loads(arquivo_log.read_text(encoding='utf-8'))
        assert len(eventos) >= 5
    
    def test_flush_automatico_evento_critico(self):
        """Testa flush automático para eventos críticos."""
        self.audit_logger.registrar_evento(
            tipo_evento=TipoEvento.SERVIDOR_ERRO,
            severidade=NivelSeveridade.CRITICAL,
            componente="Teste",
            mensagem="Evento crítico",
            detalhes={"critico": True}
        )
        
        # Aguardar um pouco para flush
        time.sleep(0.1)
        
        # Verificar se arquivo foi criado imediatamente
        arquivo_log = Path(self.temp_dir) / "teste_auditoria.json"
        assert arquivo_log.exists()
    
    def test_filtro_por_severidade(self):
        """Testa filtro por nível de severidade."""
        # Criar logger que só registra WARNING e acima
        audit_logger_filtrado = AuditLogger(
            diretorio_logs=self.temp_dir,
            arquivo_base="teste_filtrado",
            nivel_minimo=NivelSeveridade.WARNING,
            buffer_size=1
        )
        
        try:
            # Registrar eventos de diferentes severidades
            audit_logger_filtrado.registrar_evento(
                tipo_evento=TipoEvento.SYNC_SUCESSO,
                severidade=NivelSeveridade.INFO,  # Deve ser ignorado
                componente="Teste",
                mensagem="Info ignorado"
            )
            
            audit_logger_filtrado.registrar_evento(
                tipo_evento=TipoEvento.SERVIDOR_ERRO,
                severidade=NivelSeveridade.WARNING,  # Deve ser registrado
                componente="Teste",
                mensagem="Warning registrado"
            )
            
            audit_logger_filtrado.flush()
            
            # Verificar arquivo
            arquivo_log = Path(self.temp_dir) / "teste_filtrado.json"
            if arquivo_log.exists():
                eventos = json.loads(arquivo_log.read_text(encoding='utf-8'))
                # Deve ter apenas eventos WARNING e acima (mais o de inicialização)
                eventos_warning = [e for e in eventos if e['severidade'] == 'WARNING']
                assert len(eventos_warning) >= 1
                
                eventos_info = [e for e in eventos if e['mensagem'] == 'Info ignorado']
                assert len(eventos_info) == 0
        
        finally:
            audit_logger_filtrado.finalizar()
    
    def test_obtencao_eventos_com_filtros(self):
        """Testa obtenção de eventos com filtros."""
        # Registrar eventos variados
        eventos_teste = [
            (TipoEvento.SERVIDOR_INICIADO, NivelSeveridade.INFO, "Servidor", "Servidor iniciado"),
            (TipoEvento.SYNC_ERRO, NivelSeveridade.ERROR, "Sync", "Erro de sync"),
            (TipoEvento.WEBVIEW_CARREGADO, NivelSeveridade.INFO, "WebView", "WebView carregado")
        ]
        
        for tipo, sev, comp, msg in eventos_teste:
            self.audit_logger.registrar_evento(
                tipo_evento=tipo,
                severidade=sev,
                componente=comp,
                mensagem=msg
            )
        
        self.audit_logger.flush()
        
        # Testar filtro por tipo
        eventos_servidor = self.audit_logger.obter_eventos(
            tipo_evento=TipoEvento.SERVIDOR_INICIADO
        )
        assert len(eventos_servidor) >= 1
        assert all(e['tipo_evento'] == TipoEvento.SERVIDOR_INICIADO.value for e in eventos_servidor)
        
        # Testar filtro por severidade
        eventos_erro = self.audit_logger.obter_eventos(
            severidade=NivelSeveridade.ERROR
        )
        assert len(eventos_erro) >= 1
        assert all(e['severidade'] == NivelSeveridade.ERROR.value for e in eventos_erro)
        
        # Testar filtro por componente
        eventos_sync = self.audit_logger.obter_eventos(
            componente="Sync"
        )
        assert len(eventos_sync) >= 1
        assert all("sync" in e['componente'].lower() for e in eventos_sync)
    
    def test_estatisticas(self):
        """Testa obtenção de estatísticas."""
        # Registrar alguns eventos
        self.audit_logger.registrar_evento(
            tipo_evento=TipoEvento.SERVIDOR_INICIADO,
            severidade=NivelSeveridade.INFO,
            componente="Teste",
            mensagem="Teste 1"
        )
        
        self.audit_logger.registrar_evento(
            tipo_evento=TipoEvento.SYNC_ERRO,
            severidade=NivelSeveridade.ERROR,
            componente="Teste",
            mensagem="Teste 2"
        )
        
        self.audit_logger.flush()
        
        # Obter estatísticas
        stats = self.audit_logger.obter_estatisticas()
        
        assert "total_eventos" in stats
        assert "por_tipo" in stats
        assert "por_severidade" in stats
        assert "por_componente" in stats
        assert stats["total_eventos"] >= 2


class TestIntegracaoCompleta:
    """Testa integração completa do sistema de tratamento de erros."""
    
    def setup_method(self):
        """Configuração para cada teste."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Limpeza após cada teste."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_fluxo_completo_erro_e_recuperacao(self):
        """Testa fluxo completo de erro e recuperação."""
        # Configurar componentes
        config_servidor = ConfiguracaoServidorWeb(
            porta_preferencial=8080,
            portas_alternativas=[8081, 8082],
            diretorio_html=self.temp_dir,
            modo_debug=True
        )
        
        config_retry = ConfiguracaoRetry(
            max_tentativas=2,
            delay_inicial=0.1,
            multiplicador_backoff=2.0
        )
        
        # Simular cenário onde primeira porta falha, segunda funciona
        with patch('socket.socket') as mock_socket:
            mock_socket.return_value.__enter__.return_value.connect_ex.side_effect = [0, 1]  # Primeira ocupada, segunda livre
            
            # Simular HTTPServer funcionando
            with patch('services.web_server.server_manager.HTTPServer') as mock_http_server:
                mock_server_instance = Mock()
                mock_http_server.return_value = mock_server_instance
                
                # Criar e iniciar servidor
                manager = WebServerManager(config_servidor)
                
                with patch.object(manager, '_verificar_servidor_ativo', return_value=True):
                    url = manager.iniciar_servidor()
                
                # Verificar que usou porta alternativa
                assert manager.porta_atual == 8081
                assert "8081" in url
                
                # Simular parada
                manager.parar_servidor()
    
    @patch('flet.Page')
    def test_webview_com_fallback(self, mock_page):
        """Testa WebView com ativação de fallback."""
        from views.components.webview_component import WebViewComponent
        
        # Configurar mock da página
        mock_page.overlay = []
        
        # Criar componente WebView
        webview = WebViewComponent(
            page=mock_page,
            url_servidor="http://localhost:8080",
            habilitar_fallback=True,
            modo_debug=True
        )
        
        # Simular múltiplas falhas para ativar fallback
        for i in range(4):  # Mais que max_tentativas_recuperacao
            mock_error = Mock()
            mock_error.description = f"Erro {i}"
            webview._handle_web_resource_error(mock_error)
        
        # Verificar que fallback foi ativado
        assert not webview.webview_disponivel
        assert webview.modo_fallback_ativo
        
        # Testar atualização de dados no fallback
        dados_teste = {"teste": "fallback"}
        webview.atualizar_dados_fallback(dados_teste)
        
        # Verificar status
        status = webview.obter_status()
        assert not status["webview_disponivel"]
        assert status["modo_fallback_ativo"]
        assert status["tentativas_recuperacao"] >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])