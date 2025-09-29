"""
Testes de integração completa para o sistema de servidor web integrado.

Este módulo contém testes abrangentes que verificam o fluxo completo
desde a inicialização do servidor até a sincronização com o WebView,
incluindo cenários de erro e recuperação.
"""

import pytest
import unittest
import tempfile
import shutil
import json
import time
import threading
import socket
import urllib.request
import urllib.error
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import flet as ft

# Importar componentes do sistema
from services.web_server.server_manager import WebServerManager
from services.web_server.sync_manager import DataSyncManager
from services.web_server.data_provider import JSONDataProvider
from services.web_server.models import ConfiguracaoServidorWeb, DadosTopSidebar
from services.web_server.exceptions import ServidorWebError, WebViewError, SincronizacaoError
from views.components.webview_component import WebViewComponent
from views.components.top_sidebar_container import TopSidebarContainer


class TestIntegracaoServidorWebCompleta(unittest.TestCase):
    """Testes de integração para o fluxo completo servidor → WebView → sincronização."""
    
    def setUp(self):
        """Configuração inicial para cada teste."""
        # Criar diretório temporário
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        
        # Criar estrutura de arquivos web
        self.criar_estrutura_web()
        
        # Configuração do servidor
        self.config = ConfiguracaoServidorWeb(
            porta_preferencial=8100,  # Porta específica para testes
            portas_alternativas=[8101, 8102, 8103],
            diretorio_html=self.temp_dir,
            arquivo_sincronizacao=str(Path(self.temp_dir) / "sync.json"),
            modo_debug=True,
            intervalo_debounce=0.1,
            timeout_servidor=10
        )
        
        # Mock da página Flet
        self.mock_page = Mock(spec=ft.Page)
        self.mock_page.update = Mock()
        
        # Componentes para teste
        self.server_manager = None
        self.sync_manager = None
        self.webview_component = None
    
    def tearDown(self):
        """Limpeza após cada teste."""
        if self.server_manager and self.server_manager.esta_ativo():
            self.server_manager.parar_servidor()
        
        if self.sync_manager:
            self.sync_manager.finalizar()
    
    def criar_estrutura_web(self):
        """Cria estrutura de arquivos web para testes."""
        # Página principal
        (Path(self.temp_dir) / "index.html").write_text("""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>Teste Integração</title>
            <script>
                let dadosAtuais = {};
                
                function atualizarDados(dados) {
                    dadosAtuais = dados;
                    document.getElementById('dados').textContent = JSON.stringify(dados, null, 2);
                    document.getElementById('timestamp').textContent = new Date().toLocaleString();
                }
                
                function obterDados() {
                    return dadosAtuais;
                }
                
                // Simular polling para sincronização
                setInterval(() => {
                    fetch('/data/sync.json')
                        .then(response => response.json())
                        .then(data => {
                            if (data.dados) {
                                atualizarDados(data.dados);
                            }
                        })
                        .catch(error => console.log('Sync error:', error));
                }, 1000);
            </script>
        </head>
        <body>
            <h1>Teste de Integração</h1>
            <div id="status">Carregando...</div>
            <div id="timestamp"></div>
            <pre id="dados">{}</pre>
        </body>
        </html>
        """, encoding='utf-8')
        
        # Diretório de dados
        data_dir = Path(self.temp_dir) / "data"
        data_dir.mkdir(exist_ok=True)
        
        # Arquivo de sincronização inicial
        (data_dir / "sync.json").write_text('{"dados": {}}', encoding='utf-8')
    
    def test_fluxo_completo_inicializacao_servidor_webview_sync(self):
        """Testa o fluxo completo: servidor → WebView → sincronização."""
        # 1. Inicializar servidor web
        self.server_manager = WebServerManager(self.config)
        url_servidor = self.server_manager.iniciar_servidor()
        
        self.assertTrue(self.server_manager.esta_ativo())
        self.assertIsNotNone(url_servidor)
        
        # Aguardar servidor estar pronto
        time.sleep(0.2)
        
        # 2. Verificar se servidor responde
        with urllib.request.urlopen(f"{url_servidor}/index.html", timeout=5) as response:
            self.assertEqual(response.getcode(), 200)
            content = response.read().decode('utf-8')
            self.assertIn("Teste de Integração", content)
        
        # 3. Criar WebView component
        with patch('views.components.webview_component.ft.WebView') as mock_webview:
            mock_webview_instance = Mock()
            mock_webview.return_value = mock_webview_instance
            
            self.webview_component = WebViewComponent(
                page=self.mock_page,
                url_servidor=url_servidor,
                modo_debug=True
            )
            
            # Verificar se WebView foi criado com URL correta
            mock_webview.assert_called_once()
            call_kwargs = mock_webview.call_args[1]
            self.assertEqual(call_kwargs['url'], url_servidor)
        
        # 4. Inicializar sincronização de dados
        json_provider = JSONDataProvider(arquivo_json=self.config.arquivo_sincronizacao)
        self.sync_manager = DataSyncManager(json_provider)
        
        # 5. Testar sincronização de dados
        dados_teste = {
            "time_tracker": {
                "tempo_decorrido": 3600,
                "esta_executando": True,
                "projeto_atual": "Teste Integração"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        self.sync_manager.atualizar_dados(dados_teste)
        
        # Aguardar sincronização
        time.sleep(0.2)
        
        # 6. Verificar se dados foram salvos
        with open(self.config.arquivo_sincronizacao, 'r') as f:
            dados_salvos = json.load(f)
        
        self.assertIn('dados', dados_salvos)
        self.assertEqual(dados_salvos['dados']['time_tracker']['projeto_atual'], "Teste Integração")
        
        # 7. Simular atualização do WebView
        self.webview_component.notificar_atualizacao_dados(dados_teste)
        
        # Verificar se JavaScript foi executado
        mock_webview_instance.evaluate_javascript.assert_called_once()
        js_code = mock_webview_instance.evaluate_javascript.call_args[0][0]
        self.assertIn("atualizarDados", js_code)
        self.assertIn("Teste Integração", js_code)
    
    def test_cenario_erro_porta_ocupada_recuperacao(self):
        """Testa cenário de erro quando porta está ocupada e recuperação."""
        # Ocupar a porta preferencial
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('localhost', self.config.porta_preferencial))
        sock.listen(1)
        
        try:
            # Tentar inicializar servidor (deve usar porta alternativa)
            self.server_manager = WebServerManager(self.config)
            url_servidor = self.server_manager.iniciar_servidor()
            
            # Verificar se usou porta alternativa
            porta_usada = self.server_manager.obter_porta()
            self.assertNotEqual(porta_usada, self.config.porta_preferencial)
            self.assertIn(porta_usada, self.config.portas_alternativas)
            
            # Verificar se servidor está funcionando
            self.assertTrue(self.server_manager.esta_ativo())
            
            time.sleep(0.2)
            
            # Testar se responde
            with urllib.request.urlopen(f"{url_servidor}/index.html", timeout=5) as response:
                self.assertEqual(response.getcode(), 200)
                
        finally:
            sock.close()
    
    def test_cenario_erro_arquivo_nao_encontrado(self):
        """Testa cenário de erro quando arquivo não é encontrado."""
        # Inicializar servidor
        self.server_manager = WebServerManager(self.config)
        url_servidor = self.server_manager.iniciar_servidor()
        
        time.sleep(0.2)
        
        # Tentar acessar arquivo inexistente
        try:
            with urllib.request.urlopen(f"{url_servidor}/arquivo_inexistente.html", timeout=5):
                self.fail("Deveria ter retornado 404")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 404)
    
    def test_cenario_erro_falha_sincronizacao_retry(self):
        """Testa cenário de falha na sincronização com retry automático."""
        # Criar arquivo de sincronização em diretório protegido (simulando erro)
        arquivo_protegido = "/root/sync_protegido.json"  # Arquivo que não pode ser escrito
        
        config_erro = ConfiguracaoServidorWeb(
            arquivo_sincronizacao=arquivo_protegido,
            max_tentativas_retry=3,
            delay_retry=0.1
        )
        
        # Tentar criar provider com arquivo protegido
        with self.assertRaises((PermissionError, OSError, SincronizacaoError)):
            json_provider = JSONDataProvider(arquivo_json=arquivo_protegido)
            sync_manager = DataSyncManager(json_provider)
            
            dados_teste = {"teste": "erro"}
            sync_manager.atualizar_dados(dados_teste)
    
    def test_performance_multiplas_atualizacoes_simultaneas(self):
        """Testa performance com múltiplas atualizações simultâneas."""
        # Inicializar componentes
        self.server_manager = WebServerManager(self.config)
        url_servidor = self.server_manager.iniciar_servidor()
        
        json_provider = JSONDataProvider(arquivo_json=self.config.arquivo_sincronizacao)
        self.sync_manager = DataSyncManager(json_provider)
        
        # Função para atualizar dados em thread separada
        def atualizar_dados_thread(thread_id, num_updates):
            for i in range(num_updates):
                dados = {
                    "thread_id": thread_id,
                    "update_number": i,
                    "timestamp": datetime.now().isoformat()
                }
                self.sync_manager.atualizar_dados(dados)
                time.sleep(0.01)  # Pequeno delay entre atualizações
        
        # Criar múltiplas threads
        threads = []
        start_time = time.time()
        
        for thread_id in range(5):
            thread = threading.Thread(
                target=atualizar_dados_thread,
                args=(thread_id, 10)
            )
            threads.append(thread)
            thread.start()
        
        # Aguardar conclusão de todas as threads
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verificar performance (50 atualizações em menos de 5 segundos)
        self.assertLess(total_time, 5.0, f"Performance inadequada: {total_time:.2f}s")
        
        # Aguardar debounce final
        time.sleep(0.2)
        
        # Verificar se dados finais foram salvos
        with open(self.config.arquivo_sincronizacao, 'r') as f:
            dados_finais = json.load(f)
        
        self.assertIn('dados', dados_finais)
        self.assertIn('thread_id', dados_finais['dados'])
    
    def test_latencia_sincronizacao_tempo_real(self):
        """Testa latência da sincronização em tempo real."""
        # Inicializar componentes
        json_provider = JSONDataProvider(arquivo_json=self.config.arquivo_sincronizacao)
        self.sync_manager = DataSyncManager(json_provider)
        
        # Medir latência de sincronização
        dados_teste = {
            "teste_latencia": True,
            "timestamp_inicio": datetime.now().isoformat()
        }
        
        start_time = time.perf_counter()
        self.sync_manager.atualizar_dados(dados_teste)
        
        # Aguardar sincronização
        time.sleep(0.15)  # Aguardar debounce
        
        end_time = time.perf_counter()
        latencia = (end_time - start_time) * 1000  # Converter para ms
        
        # Verificar se dados foram salvos
        with open(self.config.arquivo_sincronizacao, 'r') as f:
            dados_salvos = json.load(f)
        
        self.assertIn('dados', dados_salvos)
        self.assertTrue(dados_salvos['dados']['teste_latencia'])
        
        # Latência deve ser menor que 200ms
        self.assertLess(latencia, 200, f"Latência muito alta: {latencia:.2f}ms")
    
    def test_recuperacao_apos_erro_webview(self):
        """Testa recuperação após erro no WebView."""
        # Inicializar servidor
        self.server_manager = WebServerManager(self.config)
        url_servidor = self.server_manager.iniciar_servidor()
        
        # Criar WebView com erro simulado
        with patch('views.components.webview_component.ft.WebView') as mock_webview:
            mock_webview_instance = Mock()
            mock_webview.return_value = mock_webview_instance
            
            self.webview_component = WebViewComponent(
                page=self.mock_page,
                url_servidor=url_servidor
            )
            
            # Simular erro no WebView
            mock_webview_instance.evaluate_javascript.side_effect = Exception("Erro JavaScript")
            
            # Tentar atualizar dados (não deve levantar exceção)
            dados_teste = {"teste": "recuperacao"}
            
            try:
                self.webview_component.notificar_atualizacao_dados(dados_teste)
            except Exception as e:
                self.fail(f"WebView deveria tratar erro graciosamente: {e}")
            
            # Simular recuperação
            mock_webview_instance.evaluate_javascript.side_effect = None
            
            # Tentar novamente (deve funcionar)
            self.webview_component.notificar_atualizacao_dados(dados_teste)
            mock_webview_instance.evaluate_javascript.assert_called()
    
    def test_integracao_com_top_sidebar_container(self):
        """Testa integração completa com TopSidebarContainer."""
        # Mock dos serviços
        mock_time_service = Mock()
        mock_workflow_service = Mock()
        mock_notification_service = Mock()
        
        # Configurar mocks
        mock_notification_service.get_unread_count.return_value = 3
        mock_notification_service.get_notifications.return_value = []
        
        # Criar TopSidebarContainer com WebView habilitado
        with patch('views.components.top_sidebar_container.WebServerManager') as mock_server_manager:
            with patch('views.components.top_sidebar_container.WebViewComponent') as mock_webview_comp:
                # Configurar mocks
                mock_server_instance = Mock()
                mock_server_manager.return_value = mock_server_instance
                mock_server_instance.iniciar_servidor.return_value = "http://localhost:8100"
                mock_server_instance.esta_ativo.return_value = True
                
                mock_webview_instance = Mock()
                mock_webview_comp.return_value = mock_webview_instance
                
                # Criar container
                container = TopSidebarContainer(
                    page=self.mock_page,
                    time_tracking_service=mock_time_service,
                    workflow_service=mock_workflow_service,
                    notification_service=mock_notification_service,
                    habilitar_webview=True,
                    config_servidor=self.config
                )
                
                # Verificar se servidor foi inicializado
                mock_server_manager.assert_called_once()
                mock_server_instance.iniciar_servidor.assert_called_once()
                
                # Verificar se WebView foi criado
                mock_webview_comp.assert_called_once()
                
                # Testar extração de dados
                dados = container._extrair_dados_para_sincronizacao()
                
                self.assertIsInstance(dados, dict)
                self.assertIn('fonte', dados)
                self.assertEqual(dados['fonte'], 'TopSidebarContainer')
                self.assertIn('timestamp', dados)
    
    def test_cleanup_recursos_apos_finalizacao(self):
        """Testa limpeza adequada de recursos após finalização."""
        # Inicializar todos os componentes
        self.server_manager = WebServerManager(self.config)
        url_servidor = self.server_manager.iniciar_servidor()
        
        json_provider = JSONDataProvider(arquivo_json=self.config.arquivo_sincronizacao)
        self.sync_manager = DataSyncManager(json_provider)
        
        with patch('views.components.webview_component.ft.WebView'):
            self.webview_component = WebViewComponent(
                page=self.mock_page,
                url_servidor=url_servidor
            )
        
        # Verificar se componentes estão ativos
        self.assertTrue(self.server_manager.esta_ativo())
        self.assertIsNotNone(self.sync_manager)
        self.assertIsNotNone(self.webview_component)
        
        # Finalizar componentes
        self.server_manager.parar_servidor()
        self.sync_manager.finalizar()
        
        # Verificar se recursos foram liberados
        self.assertFalse(self.server_manager.esta_ativo())
        
        # Resetar para evitar double cleanup no tearDown
        self.server_manager = None
        self.sync_manager = None


class TestCenariosErroEspecificos(unittest.TestCase):
    """Testes específicos para cenários de erro e recuperação."""
    
    def setUp(self):
        """Configuração inicial."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        
        self.config = ConfiguracaoServidorWeb(
            porta_preferencial=8110,
            portas_alternativas=[8111, 8112],
            diretorio_html=self.temp_dir,
            modo_debug=True
        )
    
    def test_erro_todas_portas_ocupadas(self):
        """Testa erro quando todas as portas estão ocupadas."""
        # Ocupar todas as portas
        sockets = []
        try:
            for porta in [8110, 8111, 8112]:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('localhost', porta))
                sock.listen(1)
                sockets.append(sock)
            
            # Tentar inicializar servidor
            manager = WebServerManager(self.config)
            
            with self.assertRaises(ServidorWebError):
                manager.iniciar_servidor()
                
        finally:
            for sock in sockets:
                sock.close()
    
    def test_erro_diretorio_html_sem_permissao(self):
        """Testa erro quando diretório HTML não tem permissão."""
        # Criar configuração com diretório protegido
        config_erro = ConfiguracaoServidorWeb(
            porta_preferencial=8113,
            diretorio_html="/root/protected_dir",  # Diretório sem permissão
            modo_debug=True
        )
        
        manager = WebServerManager(config_erro)
        
        # Deve conseguir inicializar (cria diretório se não existir)
        # ou falhar graciosamente
        try:
            url = manager.iniciar_servidor()
            # Se conseguiu inicializar, deve estar funcionando
            self.assertTrue(manager.esta_ativo())
            manager.parar_servidor()
        except (PermissionError, ServidorWebError):
            # Erro esperado devido a permissões
            pass
    
    def test_erro_arquivo_sincronizacao_corrompido(self):
        """Testa tratamento de arquivo de sincronização corrompido."""
        # Criar arquivo JSON corrompido
        arquivo_sync = Path(self.temp_dir) / "sync_corrompido.json"
        arquivo_sync.write_text("{ invalid json content", encoding='utf-8')
        
        # Tentar criar provider
        with self.assertRaises((json.JSONDecodeError, SincronizacaoError)):
            json_provider = JSONDataProvider(arquivo_json=str(arquivo_sync))
            json_provider.carregar_dados()
    
    def test_recuperacao_automatica_apos_falha_temporaria(self):
        """Testa recuperação automática após falha temporária."""
        arquivo_sync = Path(self.temp_dir) / "sync_temp.json"
        arquivo_sync.write_text('{"dados": {}}', encoding='utf-8')
        
        json_provider = JSONDataProvider(arquivo_json=str(arquivo_sync))
        sync_manager = DataSyncManager(json_provider)
        
        try:
            # Simular falha temporária removendo arquivo
            arquivo_sync.unlink()
            
            # Tentar atualizar dados (deve falhar)
            with self.assertRaises(SincronizacaoError):
                sync_manager.atualizar_dados({"teste": "falha"})
            
            # Recriar arquivo (simular recuperação)
            arquivo_sync.write_text('{"dados": {}}', encoding='utf-8')
            
            # Tentar novamente (deve funcionar)
            sync_manager.atualizar_dados({"teste": "recuperacao"})
            
            # Verificar se dados foram salvos
            with open(arquivo_sync, 'r') as f:
                dados = json.load(f)
            
            self.assertEqual(dados['dados']['teste'], "recuperacao")
            
        finally:
            sync_manager.finalizar()


if __name__ == '__main__':
    # Configurar logging para testes
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Executar testes
    unittest.main(verbosity=2)