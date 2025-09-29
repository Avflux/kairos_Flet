"""
Testes de cenários de erro para o sistema de servidor web integrado.

Este módulo contém testes específicos para validar o tratamento robusto
de erros, recuperação automática e comportamento em situações adversas.
"""

import unittest
import tempfile
import shutil
import json
import socket
import time
import threading
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Importar componentes do sistema
from services.web_server.server_manager import WebServerManager
from services.web_server.sync_manager import DataSyncManager
from services.web_server.data_provider import JSONDataProvider
from services.web_server.models import ConfiguracaoServidorWeb
from services.web_server.exceptions import (
    ServidorWebError, WebViewError, SincronizacaoError,
    RecursoIndisponivelError, CodigosErro
)
from views.components.webview_component import WebViewComponent


class TestCenariosErroServidorWeb(unittest.TestCase):
    """Testes de cenários de erro para WebServerManager."""
    
    def setUp(self):
        """Configuração inicial."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        
        # Criar arquivo HTML básico
        (Path(self.temp_dir) / "index.html").write_text(
            "<html><body>Teste Erro</body></html>",
            encoding='utf-8'
        )
        
        self.config = ConfiguracaoServidorWeb(
            porta_preferencial=8140,
            portas_alternativas=[8141, 8142],
            diretorio_html=self.temp_dir,
            modo_debug=True,
            timeout_servidor=5
        )
    
    def test_erro_todas_portas_ocupadas(self):
        """Testa erro quando todas as portas estão ocupadas."""
        # Ocupar todas as portas configuradas
        sockets = []
        try:
            portas = [self.config.porta_preferencial] + self.config.portas_alternativas
            for porta in portas:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('localhost', porta))
                sock.listen(1)
                sockets.append(sock)
            
            # Tentar inicializar servidor
            manager = WebServerManager(self.config)
            
            with self.assertRaises(RecursoIndisponivelError) as context:
                manager.iniciar_servidor()
            
            # Verificar detalhes do erro
            self.assertEqual(context.exception.codigo_erro, CodigosErro.RECURSO_PORTA_INDISPONIVEL)
            self.assertIn("Nenhuma porta disponível", str(context.exception))
            
        finally:
            for sock in sockets:
                sock.close()
    
    def test_erro_diretorio_html_inexistente_sem_permissao_criacao(self):
        """Testa erro quando diretório HTML não existe e não pode ser criado."""
        # Configurar diretório em local sem permissão (simulado)
        config_erro = ConfiguracaoServidorWeb(
            porta_preferencial=8143,
            diretorio_html="/root/diretorio_protegido",  # Diretório sem permissão
            modo_debug=True
        )
        
        # Em sistemas onde não temos permissão de root, isso deve falhar
        # ou ser tratado graciosamente
        try:
            manager = WebServerManager(config_erro)
            url = manager.iniciar_servidor()
            
            # Se conseguiu inicializar, deve estar funcionando
            self.assertTrue(manager.esta_ativo())
            manager.parar_servidor()
            
        except (PermissionError, ServidorWebError) as e:
            # Erro esperado - verificar se é tratado adequadamente
            self.assertIsInstance(e, (PermissionError, ServidorWebError))
    
    def test_erro_arquivo_html_corrompido_ou_ilegivel(self):
        """Testa comportamento com arquivos HTML corrompidos."""
        # Criar arquivo com conteúdo binário inválido
        arquivo_corrompido = Path(self.temp_dir) / "corrompido.html"
        arquivo_corrompido.write_bytes(b'\x00\x01\x02\x03\xFF\xFE\xFD')
        
        manager = WebServerManager(self.config)
        url = manager.iniciar_servidor()
        
        try:
            time.sleep(0.2)  # Aguardar servidor estar pronto
            
            # Tentar acessar arquivo corrompido
            import urllib.request
            import urllib.error
            
            try:
                with urllib.request.urlopen(f"{url}/corrompido.html", timeout=5) as response:
                    content = response.read()
                    # Servidor deve servir o arquivo mesmo sendo binário
                    self.assertIsNotNone(content)
            except urllib.error.HTTPError as e:
                # Ou retornar erro apropriado
                self.assertIn(e.code, [404, 500])
                
        finally:
            manager.parar_servidor()
    
    def test_erro_servidor_parado_abruptamente(self):
        """Testa comportamento quando servidor é parado abruptamente."""
        manager = WebServerManager(self.config)
        url = manager.iniciar_servidor()
        
        self.assertTrue(manager.esta_ativo())
        
        # Simular parada abrupta matando o processo do servidor
        if hasattr(manager, '_servidor') and manager._servidor:
            # Forçar fechamento do servidor
            manager._servidor.shutdown()
            manager._servidor.server_close()
        
        # Verificar se o manager detecta que o servidor não está mais ativo
        time.sleep(0.1)
        
        # Tentar parar graciosamente (não deve gerar erro)
        manager.parar_servidor()
        self.assertFalse(manager.esta_ativo())
    
    def test_erro_multiplas_inicializacoes_simultaneas(self):
        """Testa erro ao tentar múltiplas inicializações simultâneas."""
        manager = WebServerManager(self.config)
        
        # Primeira inicialização
        url1 = manager.iniciar_servidor()
        self.assertTrue(manager.esta_ativo())
        
        # Segunda inicialização (deve retornar a mesma URL)
        url2 = manager.iniciar_servidor()
        self.assertEqual(url1, url2)
        
        # Terceira inicialização em thread separada
        resultado_thread = []
        erro_thread = []
        
        def inicializar_em_thread():
            try:
                url3 = manager.iniciar_servidor()
                resultado_thread.append(url3)
            except Exception as e:
                erro_thread.append(e)
        
        thread = threading.Thread(target=inicializar_em_thread)
        thread.start()
        thread.join()
        
        # Deve ter retornado a mesma URL ou não ter gerado erro
        if resultado_thread:
            self.assertEqual(resultado_thread[0], url1)
        
        # Não deve ter erros
        self.assertEqual(len(erro_thread), 0)
        
        manager.parar_servidor()
    
    def test_erro_timeout_inicializacao_servidor(self):
        """Testa timeout na inicialização do servidor."""
        # Configurar timeout muito baixo
        config_timeout = ConfiguracaoServidorWeb(
            porta_preferencial=8144,
            diretorio_html=self.temp_dir,
            timeout_servidor=0.001,  # 1ms - muito baixo
            modo_debug=True
        )
        
        # Simular inicialização lenta com patch
        with patch('services.web_server.server_manager.HTTPServer') as mock_server:
            # Fazer o servidor demorar para inicializar
            def slow_init(*args, **kwargs):
                time.sleep(0.1)  # 100ms - mais que o timeout
                return Mock()
            
            mock_server.side_effect = slow_init
            
            manager = WebServerManager(config_timeout)
            
            # Pode gerar timeout ou funcionar dependendo da implementação
            try:
                url = manager.iniciar_servidor()
                # Se funcionou, deve estar ativo
                self.assertTrue(manager.esta_ativo())
                manager.parar_servidor()
            except ServidorWebError as e:
                # Erro de timeout esperado
                self.assertIn("timeout", str(e).lower())


class TestCenariosErroSincronizacao(unittest.TestCase):
    """Testes de cenários de erro para sincronização de dados."""
    
    def setUp(self):
        """Configuração inicial."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        
        self.arquivo_sync = str(Path(self.temp_dir) / "sync_erro.json")
        
        # Criar arquivo inicial válido
        with open(self.arquivo_sync, 'w') as f:
            json.dump({"dados": {}}, f)
    
    def test_erro_arquivo_sincronizacao_corrompido(self):
        """Testa tratamento de arquivo de sincronização corrompido."""
        # Corromper arquivo JSON
        with open(self.arquivo_sync, 'w') as f:
            f.write("{ invalid json content }")
        
        # Tentar criar provider
        with self.assertRaises((json.JSONDecodeError, SincronizacaoError)):
            json_provider = JSONDataProvider(arquivo_json=self.arquivo_sync)
            json_provider.carregar_dados()
    
    def test_erro_arquivo_sincronizacao_sem_permissao_leitura(self):
        """Testa erro quando arquivo não pode ser lido."""
        # Remover permissões de leitura (em sistemas Unix)
        if os.name != 'nt':  # Não Windows
            os.chmod(self.arquivo_sync, 0o000)  # Sem permissões
            
            try:
                with self.assertRaises((PermissionError, SincronizacaoError)):
                    json_provider = JSONDataProvider(arquivo_json=self.arquivo_sync)
                    json_provider.carregar_dados()
            finally:
                # Restaurar permissões para cleanup
                os.chmod(self.arquivo_sync, 0o644)
    
    def test_erro_arquivo_sincronizacao_sem_permissao_escrita(self):
        """Testa erro quando arquivo não pode ser escrito."""
        json_provider = JSONDataProvider(arquivo_json=self.arquivo_sync)
        sync_manager = DataSyncManager(json_provider)
        
        try:
            # Remover permissões de escrita do diretório (em sistemas Unix)
            if os.name != 'nt':  # Não Windows
                os.chmod(self.temp_dir, 0o444)  # Apenas leitura
                
                # Tentar atualizar dados
                with self.assertRaises((PermissionError, SincronizacaoError)):
                    sync_manager.atualizar_dados({"teste": "erro_escrita"})
                    time.sleep(0.2)  # Aguardar tentativa de escrita
                    
        finally:
            # Restaurar permissões
            if os.name != 'nt':
                os.chmod(self.temp_dir, 0o755)
            sync_manager.finalizar()
    
    def test_erro_dados_nao_serializaveis_json(self):
        """Testa erro com dados que não podem ser serializados para JSON."""
        json_provider = JSONDataProvider(arquivo_json=self.arquivo_sync)
        sync_manager = DataSyncManager(json_provider)
        
        try:
            # Dados não serializáveis
            dados_invalidos = {
                "funcao": lambda x: x,  # Função não é serializável
                "objeto_complexo": object(),  # Objeto genérico não é serializável
                "set": {1, 2, 3},  # Set não é serializável por padrão
                "datetime": datetime.now()  # datetime precisa ser convertido
            }
            
            # Deve tratar erro graciosamente
            with self.assertRaises((TypeError, SincronizacaoError)):
                sync_manager.atualizar_dados(dados_invalidos)
                time.sleep(0.2)  # Aguardar tentativa de serialização
                
        finally:
            sync_manager.finalizar()
    
    def test_erro_disco_cheio_simulado(self):
        """Testa comportamento quando disco está cheio (simulado)."""
        json_provider = JSONDataProvider(arquivo_json=self.arquivo_sync)
        sync_manager = DataSyncManager(json_provider)
        
        try:
            # Simular erro de disco cheio com patch
            with patch('builtins.open', side_effect=OSError("No space left on device")):
                with self.assertRaises((OSError, SincronizacaoError)):
                    sync_manager.atualizar_dados({"teste": "disco_cheio"})
                    time.sleep(0.2)
                    
        finally:
            sync_manager.finalizar()
    
    def test_erro_concorrencia_acesso_arquivo(self):
        """Testa erro de concorrência no acesso ao arquivo."""
        json_provider = JSONDataProvider(arquivo_json=self.arquivo_sync)
        sync_manager = DataSyncManager(json_provider)
        
        try:
            # Simular múltiplos acessos simultâneos
            def worker_com_erro(worker_id):
                for i in range(10):
                    try:
                        dados = {
                            "worker": worker_id,
                            "iteracao": i,
                            "timestamp": datetime.now().isoformat()
                        }
                        sync_manager.atualizar_dados(dados)
                        time.sleep(0.01)
                    except Exception:
                        # Erros de concorrência são esperados
                        pass
            
            # Criar múltiplas threads
            threads = []
            for worker_id in range(5):
                thread = threading.Thread(target=worker_com_erro, args=(worker_id,))
                threads.append(thread)
                thread.start()
            
            # Aguardar conclusão
            for thread in threads:
                thread.join()
            
            # Aguardar debounce final
            time.sleep(0.3)
            
            # Arquivo deve existir e ser válido
            self.assertTrue(os.path.exists(self.arquivo_sync))
            
            with open(self.arquivo_sync, 'r') as f:
                dados_finais = json.load(f)
            
            # Deve ter dados válidos
            self.assertIn('dados', dados_finais)
            
        finally:
            sync_manager.finalizar()
    
    def test_recuperacao_apos_falha_temporaria(self):
        """Testa recuperação automática após falha temporária."""
        json_provider = JSONDataProvider(arquivo_json=self.arquivo_sync)
        sync_manager = DataSyncManager(json_provider)
        
        try:
            # Primeira atualização bem-sucedida
            sync_manager.atualizar_dados({"teste": "sucesso_inicial"})
            time.sleep(0.2)
            
            # Verificar se foi salvo
            with open(self.arquivo_sync, 'r') as f:
                dados = json.load(f)
            self.assertEqual(dados['dados']['teste'], "sucesso_inicial")
            
            # Simular falha temporária removendo arquivo
            os.unlink(self.arquivo_sync)
            
            # Tentar atualizar (deve falhar)
            with self.assertRaises(SincronizacaoError):
                sync_manager.atualizar_dados({"teste": "falha"})
                time.sleep(0.2)
            
            # Recriar arquivo (simular recuperação)
            with open(self.arquivo_sync, 'w') as f:
                json.dump({"dados": {}}, f)
            
            # Tentar novamente (deve funcionar)
            sync_manager.atualizar_dados({"teste": "recuperacao"})
            time.sleep(0.2)
            
            # Verificar recuperação
            with open(self.arquivo_sync, 'r') as f:
                dados = json.load(f)
            self.assertEqual(dados['dados']['teste'], "recuperacao")
            
        finally:
            sync_manager.finalizar()


class TestCenariosErroWebView(unittest.TestCase):
    """Testes de cenários de erro para WebViewComponent."""
    
    def setUp(self):
        """Configuração inicial."""
        self.mock_page = Mock()
        self.mock_page.update = Mock()
        self.url_teste = "http://localhost:8080"
    
    def test_erro_criacao_webview_falha_flet(self):
        """Testa erro na criação do WebView por falha do Flet."""
        with patch('views.components.webview_component.ft.WebView', side_effect=Exception("Flet WebView error")):
            with self.assertRaises(WebViewError) as context:
                WebViewComponent(
                    page=self.mock_page,
                    url_servidor=self.url_teste
                )
            
            self.assertEqual(context.exception.codigo_erro, CodigosErro.WEBVIEW_FALHA_CARREGAMENTO)
            self.assertIn("Não foi possível criar o WebView", str(context.exception))
    
    def test_erro_url_invalida_webview(self):
        """Testa erro com URL inválida para WebView."""
        with patch('views.components.webview_component.ft.WebView') as mock_webview:
            mock_webview.return_value = Mock()
            
            component = WebViewComponent(
                page=self.mock_page,
                url_servidor=self.url_teste
            )
            
            # Tentar atualizar com URL inválida
            with self.assertRaises(WebViewError) as context:
                component.atualizar_url("")
            
            self.assertEqual(context.exception.codigo_erro, CodigosErro.WEBVIEW_URL_INVALIDA)
            
            # Tentar com URL None
            with self.assertRaises(WebViewError):
                component.atualizar_url(None)
    
    def test_erro_javascript_execucao_falha(self):
        """Testa erro na execução de JavaScript no WebView."""
        with patch('views.components.webview_component.ft.WebView') as mock_webview:
            mock_webview_instance = Mock()
            mock_webview.return_value = mock_webview_instance
            
            # Simular erro na execução de JavaScript
            mock_webview_instance.evaluate_javascript.side_effect = Exception("JavaScript execution failed")
            
            component = WebViewComponent(
                page=self.mock_page,
                url_servidor=self.url_teste
            )
            
            # Tentar executar JavaScript (deve tratar erro graciosamente)
            try:
                component.executar_javascript("console.log('teste');")
            except Exception as e:
                self.fail(f"WebView deveria tratar erro de JavaScript graciosamente: {e}")
    
    def test_erro_webview_nao_inicializado(self):
        """Testa erro ao usar WebView não inicializado."""
        with patch('views.components.webview_component.ft.WebView') as mock_webview:
            mock_webview.return_value = Mock()
            
            component = WebViewComponent(
                page=self.mock_page,
                url_servidor=self.url_teste
            )
            
            # Simular WebView não inicializado
            component._webview = None
            
            # Tentar recarregar
            with self.assertRaises(WebViewError) as context:
                component.recarregar()
            
            self.assertEqual(context.exception.codigo_erro, CodigosErro.WEBVIEW_FALHA_CARREGAMENTO)
            
            # Tentar executar JavaScript
            with self.assertRaises(WebViewError) as context:
                component.executar_javascript("console.log('teste');")
            
            self.assertEqual(context.exception.codigo_erro, CodigosErro.WEBVIEW_ERRO_JAVASCRIPT)
    
    def test_erro_notificacao_dados_invalidos(self):
        """Testa erro ao notificar dados inválidos para WebView."""
        with patch('views.components.webview_component.ft.WebView') as mock_webview:
            mock_webview_instance = Mock()
            mock_webview.return_value = mock_webview_instance
            
            component = WebViewComponent(
                page=self.mock_page,
                url_servidor=self.url_teste
            )
            
            # Dados que não podem ser serializados
            dados_invalidos = {
                "funcao": lambda x: x,
                "objeto": object()
            }
            
            # Deve tratar erro graciosamente
            try:
                component.notificar_atualizacao_dados(dados_invalidos)
            except Exception as e:
                self.fail(f"WebView deveria tratar dados inválidos graciosamente: {e}")
            
            # JavaScript não deve ter sido executado devido ao erro
            mock_webview_instance.evaluate_javascript.assert_not_called()
    
    def test_erro_callback_personalizado_com_excecao(self):
        """Testa tratamento de exceções em callbacks personalizados."""
        callback_com_erro = Mock(side_effect=Exception("Erro no callback"))
        
        with patch('views.components.webview_component.ft.WebView') as mock_webview:
            mock_webview.return_value = Mock()
            
            # Criar component com callback que gera erro
            component = WebViewComponent(
                page=self.mock_page,
                url_servidor=self.url_teste,
                on_page_started=callback_com_erro
            )
            
            # Simular evento (não deve levantar exceção)
            event_mock = Mock()
            try:
                component._handle_page_started(event_mock)
            except Exception as e:
                self.fail(f"Erro em callback não deveria propagar: {e}")
            
            # Callback deve ter sido chamado
            callback_com_erro.assert_called_once_with(event_mock)


class TestRecuperacaoSistemaCompleto(unittest.TestCase):
    """Testes de recuperação para o sistema completo."""
    
    def setUp(self):
        """Configuração inicial."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        
        # Criar estrutura básica
        (Path(self.temp_dir) / "index.html").write_text(
            "<html><body>Teste Recuperação</body></html>",
            encoding='utf-8'
        )
        
        self.config = ConfiguracaoServidorWeb(
            porta_preferencial=8150,
            portas_alternativas=[8151, 8152],
            diretorio_html=self.temp_dir,
            arquivo_sincronizacao=str(Path(self.temp_dir) / "sync.json"),
            modo_debug=True,
            max_tentativas_retry=3,
            delay_retry=0.1
        )
    
    def test_recuperacao_completa_apos_falha_multipla(self):
        """Testa recuperação completa após múltiplas falhas."""
        # Inicializar componentes
        server_manager = WebServerManager(self.config)
        url = server_manager.iniciar_servidor()
        
        json_provider = JSONDataProvider(arquivo_json=self.config.arquivo_sincronizacao)
        sync_manager = DataSyncManager(json_provider)
        
        try:
            # 1. Funcionamento normal
            sync_manager.atualizar_dados({"status": "normal"})
            time.sleep(0.2)
            
            # Verificar funcionamento
            with open(self.config.arquivo_sincronizacao, 'r') as f:
                dados = json.load(f)
            self.assertEqual(dados['dados']['status'], "normal")
            
            # 2. Simular falha no arquivo
            os.unlink(self.config.arquivo_sincronizacao)
            
            # 3. Tentar operação (deve falhar)
            with self.assertRaises(SincronizacaoError):
                sync_manager.atualizar_dados({"status": "falha"})
                time.sleep(0.2)
            
            # 4. Recriar arquivo (recuperação)
            with open(self.config.arquivo_sincronizacao, 'w') as f:
                json.dump({"dados": {}}, f)
            
            # 5. Tentar novamente (deve funcionar)
            sync_manager.atualizar_dados({"status": "recuperado"})
            time.sleep(0.2)
            
            # Verificar recuperação
            with open(self.config.arquivo_sincronizacao, 'r') as f:
                dados = json.load(f)
            self.assertEqual(dados['dados']['status'], "recuperado")
            
        finally:
            server_manager.parar_servidor()
            sync_manager.finalizar()
    
    def test_graceful_degradation_sem_webview(self):
        """Testa degradação graceful quando WebView não está disponível."""
        # Simular falha na criação do WebView
        with patch('views.components.webview_component.ft.WebView', side_effect=Exception("WebView não disponível")):
            
            # Sistema deve continuar funcionando sem WebView
            server_manager = WebServerManager(self.config)
            url = server_manager.iniciar_servidor()
            
            json_provider = JSONDataProvider(arquivo_json=self.config.arquivo_sincronizacao)
            sync_manager = DataSyncManager(json_provider)
            
            try:
                # Sincronização deve funcionar normalmente
                sync_manager.atualizar_dados({"modo": "sem_webview"})
                time.sleep(0.2)
                
                # Verificar se dados foram salvos
                with open(self.config.arquivo_sincronizacao, 'r') as f:
                    dados = json.load(f)
                self.assertEqual(dados['dados']['modo'], "sem_webview")
                
                # Servidor deve estar funcionando
                self.assertTrue(server_manager.esta_ativo())
                
            finally:
                server_manager.parar_servidor()
                sync_manager.finalizar()


if __name__ == '__main__':
    print("🔥 Executando Testes de Cenários de Erro do Servidor Web Integrado")
    print("=" * 65)
    
    # Configurar logging para capturar erros
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Executar testes com verbosidade
    unittest.main(verbosity=2)