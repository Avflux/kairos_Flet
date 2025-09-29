"""
Testes avançados de cenários de erro para o sistema de servidor web integrado.

Este módulo complementa os testes de erro existentes com cenários mais específicos
e complexos, incluindo falhas em cascata, recuperação parcial e edge cases.
"""

import unittest
import tempfile
import shutil
import json
import socket
import time
import threading
import os
import signal
import subprocess
import psutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta
from queue import Queue, Empty
from contextlib import contextmanager

# Importar componentes do sistema
from services.web_server.server_manager import WebServerManager
from services.web_server.sync_manager import DataSyncManager
from services.web_server.data_provider import JSONDataProvider
from services.web_server.models import ConfiguracaoServidorWeb
from services.web_server.exceptions import (
    ServidorWebError, WebViewError, SincronizacaoError,
    RecursoIndisponivelError, ConfiguracaoInvalidaError, CodigosErro
)
from views.components.webview_component import WebViewComponent


class TestCenariosErroAvancados(unittest.TestCase):
    """Testes avançados de cenários de erro."""
    
    def setUp(self):
        """Configuração inicial."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        
        # Criar estrutura básica
        (Path(self.temp_dir) / "index.html").write_text(
            "<html><body>Teste Erro Avançado</body></html>",
            encoding='utf-8'
        )
        
        self.config = ConfiguracaoServidorWeb(
            porta_preferencial=8400,
            portas_alternativas=[8401, 8402, 8403],
            diretorio_html=self.temp_dir,
            arquivo_sincronizacao=str(Path(self.temp_dir) / "sync_erro.json"),
            modo_debug=True,
            max_tentativas_retry=3,
            delay_retry=0.1,
            timeout_servidor=5
        )
        
        # Criar arquivo de sincronização inicial
        with open(self.config.arquivo_sincronizacao, 'w') as f:
            json.dump({"dados": {}}, f)
        
        self.mock_page = Mock()
        self.mock_page.update = Mock()
    
    @contextmanager
    def simular_falha_temporaria(self, arquivo, duracao=0.5):
        """Context manager para simular falha temporária em arquivo."""
        backup_path = arquivo + ".backup"
        
        try:
            # Fazer backup
            if os.path.exists(arquivo):
                shutil.copy2(arquivo, backup_path)
            
            # Simular falha
            if os.path.exists(arquivo):
                os.unlink(arquivo)
            
            yield
            
            # Aguardar duração da falha
            time.sleep(duracao)
            
        finally:
            # Restaurar arquivo
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, arquivo)
                os.unlink(backup_path)
    
    def test_falha_cascata_servidor_sync_webview(self):
        """Testa falha em cascata: servidor → sync → WebView."""
        print("🔥 Testando falha em cascata...")
        
        # 1. Inicializar sistema funcionando
        server_manager = WebServerManager(self.config)
        url_servidor = server_manager.iniciar_servidor()
        
        json_provider = JSONDataProvider(arquivo_json=self.config.arquivo_sincronizacao)
        sync_manager = DataSyncManager(json_provider)
        
        with patch('views.components.webview_component.ft.WebView') as mock_webview:
            mock_webview_instance = Mock()
            mock_webview.return_value = mock_webview_instance
            
            webview = WebViewComponent(
                page=self.mock_page,
                url_servidor=url_servidor
            )
            
            # Verificar funcionamento normal
            dados_teste = {"teste": "normal"}
            sync_manager.atualizar_dados(dados_teste)
            time.sleep(0.2)
            webview.notificar_atualizacao_dados(dados_teste)
            
            self.assertTrue(server_manager.esta_ativo())
            mock_webview_instance.evaluate_javascript.assert_called()
            
            # 2. Simular falha do servidor (forçar parada)
            server_manager.parar_servidor()
            self.assertFalse(server_manager.esta_ativo())
            
            # 3. Tentar sincronização (deve continuar funcionando)
            dados_teste2 = {"teste": "apos_falha_servidor"}
            sync_manager.atualizar_dados(dados_teste2)
            time.sleep(0.2)
            
            # Verificar se dados foram salvos (sync ainda funciona)
            with open(self.config.arquivo_sincronizacao, 'r') as f:
                dados_salvos = json.load(f)
            self.assertEqual(dados_salvos['dados']['teste'], "apos_falha_servidor")
            
            # 4. Simular falha na sincronização
            os.unlink(self.config.arquivo_sincronizacao)
            
            with self.assertRaises(SincronizacaoError):
                sync_manager.atualizar_dados({"teste": "falha_sync"})
                time.sleep(0.2)
            
            # 5. Simular falha no WebView
            mock_webview_instance.evaluate_javascript.side_effect = Exception("WebView falhou")
            
            # WebView deve tratar erro graciosamente
            try:
                webview.notificar_atualizacao_dados({"teste": "falha_webview"})
            except Exception as e:
                self.fail(f"WebView não tratou erro graciosamente: {e}")
            
            # 6. Recuperação gradual
            # Restaurar arquivo de sincronização
            with open(self.config.arquivo_sincronizacao, 'w') as f:
                json.dump({"dados": {}}, f)
            
            # Restaurar WebView
            mock_webview_instance.evaluate_javascript.side_effect = None
            
            # Reiniciar servidor
            server_manager = WebServerManager(self.config)
            url_servidor = server_manager.iniciar_servidor()
            
            # Testar funcionamento após recuperação
            dados_recuperacao = {"teste": "recuperado", "timestamp": datetime.now().isoformat()}
            sync_manager.atualizar_dados(dados_recuperacao)
            time.sleep(0.2)
            webview.notificar_atualizacao_dados(dados_recuperacao)
            
            # Verificar recuperação completa
            self.assertTrue(server_manager.esta_ativo())
            mock_webview_instance.evaluate_javascript.assert_called()
            
            with open(self.config.arquivo_sincronizacao, 'r') as f:
                dados_finais = json.load(f)
            self.assertEqual(dados_finais['dados']['teste'], "recuperado")
            
            server_manager.parar_servidor()
            sync_manager.finalizar()
        
        print("   ✅ Falha em cascata e recuperação testadas")
    
    def test_erro_concorrencia_extrema_com_falhas(self):
        """Testa erros sob concorrência extrema com falhas intermitentes."""
        print("🔥 Testando erros sob concorrência extrema...")
        
        server_manager = WebServerManager(self.config)
        url_servidor = server_manager.iniciar_servidor()
        
        json_provider = JSONDataProvider(arquivo_json=self.config.arquivo_sincronizacao)
        sync_manager = DataSyncManager(json_provider)
        
        # Métricas de erro
        operacoes_totais = 0
        operacoes_sucesso = 0
        operacoes_erro = 0
        tipos_erro = {}
        lock = threading.Lock()
        
        def worker_com_falhas_intermitentes(worker_id, num_ops):
            nonlocal operacoes_totais, operacoes_sucesso, operacoes_erro
            
            for i in range(num_ops):
                with lock:
                    operacoes_totais += 1
                
                try:
                    dados = {
                        "worker_id": worker_id,
                        "operation": i,
                        "timestamp": datetime.now().isoformat(),
                        "data": f"worker_{worker_id}_data_{i}" * 20
                    }
                    
                    # Simular falhas intermitentes (20% das operações)
                    if i % 5 == 0:
                        # Simular diferentes tipos de falha
                        if i % 15 == 0:
                            # Corromper arquivo temporariamente
                            with open(self.config.arquivo_sincronizacao, 'w') as f:
                                f.write("{ invalid json }")
                            time.sleep(0.01)
                            with open(self.config.arquivo_sincronizacao, 'w') as f:
                                json.dump({"dados": {}}, f)
                        elif i % 10 == 0:
                            # Remover arquivo temporariamente
                            if os.path.exists(self.config.arquivo_sincronizacao):
                                os.unlink(self.config.arquivo_sincronizacao)
                            time.sleep(0.01)
                            with open(self.config.arquivo_sincronizacao, 'w') as f:
                                json.dump({"dados": {}}, f)
                    
                    sync_manager.atualizar_dados(dados)
                    time.sleep(0.01)
                    
                    with lock:
                        operacoes_sucesso += 1
                        
                except Exception as e:
                    with lock:
                        operacoes_erro += 1
                        tipo_erro = type(e).__name__
                        tipos_erro[tipo_erro] = tipos_erro.get(tipo_erro, 0) + 1
                
                # Pequena pausa variável
                time.sleep(0.005 + (i % 3) * 0.002)
        
        try:
            # Executar 8 workers com falhas intermitentes
            threads = []
            for worker_id in range(8):
                thread = threading.Thread(
                    target=worker_com_falhas_intermitentes,
                    args=(worker_id, 15)
                )
                threads.append(thread)
                thread.start()
            
            # Aguardar conclusão
            for thread in threads:
                thread.join()
            
            # Aguardar estabilização
            time.sleep(0.5)
            
            # Analisar resultados
            taxa_sucesso = operacoes_sucesso / operacoes_totais if operacoes_totais > 0 else 0
            taxa_erro = operacoes_erro / operacoes_totais if operacoes_totais > 0 else 0
            
            # Verificar que sistema se mantém funcional mesmo com falhas
            self.assertGreater(taxa_sucesso, 0.6, f"Taxa de sucesso muito baixa: {taxa_sucesso:.2%}")
            self.assertLess(taxa_erro, 0.4, f"Taxa de erro muito alta: {taxa_erro:.2%}")
            
            # Verificar que arquivo final é válido
            self.assertTrue(os.path.exists(self.config.arquivo_sincronizacao))
            with open(self.config.arquivo_sincronizacao, 'r') as f:
                dados_finais = json.load(f)
            self.assertIn('dados', dados_finais)
            
            print(f"   📊 Concorrência extrema: {operacoes_sucesso}/{operacoes_totais} sucessos ({taxa_sucesso:.1%})")
            print(f"   🔍 Tipos de erro: {tipos_erro}")
            
        finally:
            server_manager.parar_servidor()
            sync_manager.finalizar()
    
    def test_recuperacao_apos_corrupcao_total_sistema(self):
        """Testa recuperação após corrupção total do sistema."""
        print("🔥 Testando recuperação após corrupção total...")
        
        # 1. Sistema funcionando normalmente
        server_manager = WebServerManager(self.config)
        url_servidor = server_manager.iniciar_servidor()
        
        json_provider = JSONDataProvider(arquivo_json=self.config.arquivo_sincronizacao)
        sync_manager = DataSyncManager(json_provider)
        
        # Dados importantes
        dados_importantes = {
            "dados_criticos": True,
            "configuracao": {"versao": "1.0.0", "modo": "producao"},
            "historico": [
                {"data": "2024-01-01", "evento": "inicio"},
                {"data": "2024-01-02", "evento": "configuracao"},
                {"data": "2024-01-03", "evento": "dados_importantes"}
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        sync_manager.atualizar_dados(dados_importantes)
        time.sleep(0.2)
        
        # Verificar funcionamento normal
        with open(self.config.arquivo_sincronizacao, 'r') as f:
            dados_salvos = json.load(f)
        self.assertTrue(dados_salvos['dados']['dados_criticos'])
        
        # 2. Simular corrupção total
        print("   💥 Simulando corrupção total do sistema...")
        
        # Corromper arquivo de sincronização
        with open(self.config.arquivo_sincronizacao, 'w') as f:
            f.write("ARQUIVO TOTALMENTE CORROMPIDO - NÃO É JSON")
        
        # Corromper arquivos HTML
        for html_file in Path(self.temp_dir).glob("*.html"):
            html_file.write_text("ARQUIVO HTML CORROMPIDO", encoding='utf-8')
        
        # Parar servidor abruptamente
        server_manager.parar_servidor()
        
        # 3. Tentar usar sistema corrompido
        with self.assertRaises((json.JSONDecodeError, SincronizacaoError)):
            json_provider_corrompido = JSONDataProvider(arquivo_json=self.config.arquivo_sincronizacao)
            json_provider_corrompido.carregar_dados()
        
        # 4. Processo de recuperação
        print("   🔧 Iniciando processo de recuperação...")
        
        # Detectar corrupção e criar backup
        backup_path = self.config.arquivo_sincronizacao + ".corrupted_backup"
        shutil.copy2(self.config.arquivo_sincronizacao, backup_path)
        
        # Recriar arquivo de sincronização
        dados_recuperacao = {
            "dados": {
                "sistema_recuperado": True,
                "timestamp_recuperacao": datetime.now().isoformat(),
                "dados_perdidos": "Dados anteriores foram perdidos devido à corrupção",
                "status": "recuperado_com_perda_de_dados"
            },
            "timestamp": datetime.now().isoformat(),
            "versao": 1
        }
        
        with open(self.config.arquivo_sincronizacao, 'w') as f:
            json.dump(dados_recuperacao, f, indent=2, ensure_ascii=False)
        
        # Recriar arquivos HTML básicos
        (Path(self.temp_dir) / "index.html").write_text("""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>Sistema Recuperado</title>
        </head>
        <body>
            <h1>Sistema Recuperado</h1>
            <p>O sistema foi recuperado após corrupção total.</p>
            <div id="status">Recuperado</div>
        </body>
        </html>
        """, encoding='utf-8')
        
        # 5. Reinicializar sistema
        server_manager_recuperado = WebServerManager(self.config)
        url_recuperado = server_manager_recuperado.iniciar_servidor()
        
        json_provider_recuperado = JSONDataProvider(arquivo_json=self.config.arquivo_sincronizacao)
        sync_manager_recuperado = DataSyncManager(json_provider_recuperado)
        
        # 6. Testar funcionamento após recuperação
        dados_teste_pos_recuperacao = {
            "teste_pos_recuperacao": True,
            "timestamp": datetime.now().isoformat(),
            "funcionalidade": "testando_apos_recuperacao"
        }
        
        sync_manager_recuperado.atualizar_dados(dados_teste_pos_recuperacao)
        time.sleep(0.2)
        
        # Verificar se sistema está funcionando
        self.assertTrue(server_manager_recuperado.esta_ativo())
        
        with open(self.config.arquivo_sincronizacao, 'r') as f:
            dados_pos_recuperacao = json.load(f)
        
        self.assertTrue(dados_pos_recuperacao['dados']['teste_pos_recuperacao'])
        self.assertTrue(dados_pos_recuperacao['dados']['sistema_recuperado'])
        
        # 7. Testar acesso ao servidor recuperado
        import urllib.request
        try:
            with urllib.request.urlopen(f"{url_recuperado}/index.html", timeout=5) as response:
                content = response.read().decode('utf-8')
                self.assertIn("Sistema Recuperado", content)
        except Exception as e:
            self.fail(f"Servidor não está respondendo após recuperação: {e}")
        
        # Cleanup
        server_manager_recuperado.parar_servidor()
        sync_manager_recuperado.finalizar()
        
        # Verificar se backup da corrupção foi mantido
        self.assertTrue(os.path.exists(backup_path))
        
        print("   ✅ Sistema recuperado com sucesso após corrupção total")
    
    def test_erro_limite_recursos_sistema(self):
        """Testa comportamento quando recursos do sistema estão no limite."""
        print("🔥 Testando comportamento no limite de recursos...")
        
        server_manager = WebServerManager(self.config)
        url_servidor = server_manager.iniciar_servidor()
        
        json_provider = JSONDataProvider(arquivo_json=self.config.arquivo_sincronizacao)
        sync_manager = DataSyncManager(json_provider)
        
        try:
            # 1. Simular pressão de memória
            print("   💾 Simulando pressão de memória...")
            arrays_memoria = []
            
            # Alocar memória até um limite razoável (~100MB)
            for i in range(20):
                try:
                    array_grande = [j for j in range(250000)]  # ~5MB cada
                    arrays_memoria.append(array_grande)
                except MemoryError:
                    break
            
            # Testar sincronização sob pressão de memória
            dados_memoria = {
                "teste_memoria": True,
                "pressao_memoria": True,
                "timestamp": datetime.now().isoformat(),
                "dados_grandes": "x" * 50000  # 50KB
            }
            
            try:
                sync_manager.atualizar_dados(dados_memoria)
                time.sleep(0.2)
                
                # Verificar se dados foram salvos
                with open(self.config.arquivo_sincronizacao, 'r') as f:
                    dados_salvos = json.load(f)
                self.assertTrue(dados_salvos['dados']['teste_memoria'])
                
            except Exception as e:
                # Sistema deve degradar graciosamente, não falhar completamente
                self.assertIsInstance(e, (MemoryError, SincronizacaoError))
                print(f"   ⚠️ Sistema degradou graciosamente: {type(e).__name__}")
            
            # 2. Simular muitos arquivos abertos
            print("   📁 Simulando muitos arquivos abertos...")
            arquivos_abertos = []
            
            try:
                # Abrir muitos arquivos temporários
                for i in range(100):
                    arquivo_temp = tempfile.NamedTemporaryFile(mode='w', delete=False)
                    arquivo_temp.write(f"arquivo_temp_{i}")
                    arquivos_abertos.append(arquivo_temp)
                
                # Testar sincronização com muitos arquivos abertos
                dados_arquivos = {
                    "teste_arquivos": True,
                    "arquivos_abertos": len(arquivos_abertos),
                    "timestamp": datetime.now().isoformat()
                }
                
                sync_manager.atualizar_dados(dados_arquivos)
                time.sleep(0.2)
                
                # Verificar funcionamento
                with open(self.config.arquivo_sincronizacao, 'r') as f:
                    dados_salvos = json.load(f)
                self.assertTrue(dados_salvos['dados']['teste_arquivos'])
                
            except Exception as e:
                print(f"   ⚠️ Limite de arquivos atingido: {type(e).__name__}")
            
            finally:
                # Fechar arquivos temporários
                for arquivo in arquivos_abertos:
                    try:
                        arquivo.close()
                        os.unlink(arquivo.name)
                    except:
                        pass
            
            # 3. Simular alta carga de CPU
            print("   🔥 Simulando alta carga de CPU...")
            
            def cpu_intensive_task():
                # Tarefa intensiva de CPU por 2 segundos
                end_time = time.time() + 2.0
                while time.time() < end_time:
                    _ = sum(i * i for i in range(1000))
            
            # Iniciar tarefas intensivas em threads separadas
            cpu_threads = []
            for _ in range(4):  # 4 threads intensivas
                thread = threading.Thread(target=cpu_intensive_task)
                cpu_threads.append(thread)
                thread.start()
            
            # Testar sincronização durante alta carga de CPU
            dados_cpu = {
                "teste_cpu": True,
                "alta_carga_cpu": True,
                "timestamp": datetime.now().isoformat(),
                "threads_cpu": len(cpu_threads)
            }
            
            start_time = time.time()
            sync_manager.atualizar_dados(dados_cpu)
            time.sleep(0.2)
            end_time = time.time()
            
            tempo_sincronizacao = end_time - start_time
            
            # Aguardar threads de CPU
            for thread in cpu_threads:
                thread.join()
            
            # Verificar se sincronização funcionou (pode estar mais lenta)
            with open(self.config.arquivo_sincronizacao, 'r') as f:
                dados_salvos = json.load(f)
            self.assertTrue(dados_salvos['dados']['teste_cpu'])
            
            # Sincronização pode estar mais lenta, mas deve funcionar
            self.assertLess(tempo_sincronizacao, 5.0, "Sincronização muito lenta mesmo sob carga")
            
            print(f"   ⏱️ Sincronização sob carga de CPU: {tempo_sincronizacao:.2f}s")
            
        finally:
            # Liberar recursos
            arrays_memoria.clear()
            import gc
            gc.collect()
            
            server_manager.parar_servidor()
            sync_manager.finalizar()
        
        print("   ✅ Sistema manteve funcionalidade básica sob pressão de recursos")
    
    def test_erro_rede_intermitente_webview(self):
        """Testa comportamento com problemas de rede intermitentes no WebView."""
        print("🔥 Testando erros de rede intermitentes no WebView...")
        
        server_manager = WebServerManager(self.config)
        url_servidor = server_manager.iniciar_servidor()
        
        json_provider = JSONDataProvider(arquivo_json=self.config.arquivo_sincronizacao)
        sync_manager = DataSyncManager(json_provider)
        
        with patch('views.components.webview_component.ft.WebView') as mock_webview:
            mock_webview_instance = Mock()
            mock_webview.return_value = mock_webview_instance
            
            webview = WebViewComponent(
                page=self.mock_page,
                url_servidor=url_servidor,
                modo_debug=True
            )
            
            # Simular falhas intermitentes de rede no WebView
            call_count = 0
            
            def simulate_network_issues(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                
                # Falhar a cada 3 chamadas (simular rede intermitente)
                if call_count % 3 == 0:
                    raise Exception("Network timeout")
                
                return None
            
            mock_webview_instance.evaluate_javascript.side_effect = simulate_network_issues
            
            # Testar múltiplas notificações com falhas intermitentes
            sucessos = 0
            falhas = 0
            
            for i in range(20):
                dados = {
                    "teste_rede": True,
                    "notification_id": i,
                    "timestamp": datetime.now().isoformat(),
                    "data": f"notification_{i}"
                }
                
                # Sincronizar dados (deve sempre funcionar)
                sync_manager.atualizar_dados(dados)
                time.sleep(0.1)
                
                # Tentar notificar WebView (pode falhar)
                try:
                    webview.notificar_atualizacao_dados(dados)
                    sucessos += 1
                except Exception:
                    falhas += 1
                
                time.sleep(0.05)
            
            # Verificar que sincronização continuou funcionando
            with open(self.config.arquivo_sincronizacao, 'r') as f:
                dados_finais = json.load(f)
            self.assertTrue(dados_finais['dados']['teste_rede'])
            
            # Verificar que algumas notificações falharam (rede intermitente)
            self.assertGreater(falhas, 0, "Deveria ter havido algumas falhas de rede")
            self.assertGreater(sucessos, 0, "Deveria ter havido alguns sucessos")
            
            # Verificar que WebView tentou se recuperar
            self.assertEqual(mock_webview_instance.evaluate_javascript.call_count, 20)
            
            print(f"   📊 Rede intermitente: {sucessos} sucessos, {falhas} falhas")
            
        server_manager.parar_servidor()
        sync_manager.finalizar()
        
        print("   ✅ Sistema manteve sincronização mesmo com falhas de rede no WebView")
    
    def test_erro_configuracao_invalida_recuperacao(self):
        """Testa recuperação de configurações inválidas."""
        print("🔥 Testando recuperação de configurações inválidas...")
        
        # 1. Configuração completamente inválida
        config_invalida = ConfiguracaoServidorWeb(
            porta_preferencial=-1,  # Porta inválida
            portas_alternativas=[],  # Sem alternativas
            diretorio_html="/diretorio/inexistente/impossivel",
            arquivo_sincronizacao="",  # Arquivo vazio
            intervalo_debounce=-1,  # Intervalo negativo
            max_tentativas_retry=0,  # Sem retry
            timeout_servidor=0  # Timeout zero
        )
        
        # Tentar usar configuração inválida
        with self.assertRaises((ConfiguracaoInvalidaError, ValueError, OSError)):
            server_manager = WebServerManager(config_invalida)
            server_manager.iniciar_servidor()
        
        # 2. Configuração parcialmente inválida com recuperação
        config_parcial = ConfiguracaoServidorWeb(
            porta_preferencial=8404,
            portas_alternativas=[8405, 8406],
            diretorio_html=self.temp_dir,
            arquivo_sincronizacao=str(Path(self.temp_dir) / "sync_parcial.json"),
            intervalo_debounce=0.01,
            max_tentativas_retry=3,
            timeout_servidor=5
        )
        
        # Corromper diretório HTML após criação
        html_file = Path(self.temp_dir) / "index.html"
        html_file.unlink()  # Remover arquivo HTML
        
        # Sistema deve se recuperar criando arquivo básico ou usando fallback
        try:
            server_manager = WebServerManager(config_parcial)
            url_servidor = server_manager.iniciar_servidor()
            
            # Verificar se servidor está funcionando
            self.assertTrue(server_manager.esta_ativo())
            
            # Tentar acessar (pode retornar 404, mas servidor deve responder)
            import urllib.request
            import urllib.error
            
            try:
                with urllib.request.urlopen(f"{url_servidor}/index.html", timeout=5) as response:
                    self.assertEqual(response.getcode(), 200)
            except urllib.error.HTTPError as e:
                # 404 é aceitável se arquivo não existe
                self.assertEqual(e.code, 404)
            
            server_manager.parar_servidor()
            
        except Exception as e:
            # Se falhar, deve ser com erro específico e informativo
            self.assertIsInstance(e, (ServidorWebError, OSError))
            print(f"   ⚠️ Falha esperada com configuração parcialmente inválida: {type(e).__name__}")
        
        # 3. Recuperação automática com configuração válida
        config_recuperada = ConfiguracaoServidorWeb(
            porta_preferencial=8407,
            diretorio_html=self.temp_dir,
            arquivo_sincronizacao=str(Path(self.temp_dir) / "sync_recuperado.json"),
            modo_debug=True
        )
        
        # Recriar arquivo HTML
        (Path(self.temp_dir) / "index.html").write_text(
            "<html><body>Recuperado</body></html>",
            encoding='utf-8'
        )
        
        # Sistema deve funcionar normalmente
        server_manager_recuperado = WebServerManager(config_recuperada)
        url_recuperado = server_manager_recuperado.iniciar_servidor()
        
        self.assertTrue(server_manager_recuperado.esta_ativo())
        
        # Testar funcionamento completo
        json_provider = JSONDataProvider(arquivo_json=config_recuperada.arquivo_sincronizacao)
        sync_manager = DataSyncManager(json_provider)
        
        dados_teste = {
            "configuracao_recuperada": True,
            "timestamp": datetime.now().isoformat()
        }
        
        sync_manager.atualizar_dados(dados_teste)
        time.sleep(0.2)
        
        with open(config_recuperada.arquivo_sincronizacao, 'r') as f:
            dados_salvos = json.load(f)
        self.assertTrue(dados_salvos['dados']['configuracao_recuperada'])
        
        server_manager_recuperado.parar_servidor()
        sync_manager.finalizar()
        
        print("   ✅ Sistema se recuperou de configurações inválidas")


if __name__ == '__main__':
    print("🔥 Executando Testes Avançados de Cenários de Erro")
    print("=" * 55)
    
    # Configurar logging para capturar erros
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Executar testes
    unittest.main(verbosity=2)