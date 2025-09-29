"""
Testes de performance para o sistema de servidor web integrado.

Este módulo contém testes específicos para medir e validar a performance
do sistema de sincronização, latência de comunicação e uso de recursos.
"""

import unittest
import time
import threading
import tempfile
import shutil
import json
import psutil
import os
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime
from statistics import mean, median, stdev

# Importar componentes do sistema
from services.web_server.server_manager import WebServerManager
from services.web_server.sync_manager import DataSyncManager
from services.web_server.data_provider import JSONDataProvider
from services.web_server.models import ConfiguracaoServidorWeb
from views.components.webview_component import WebViewComponent


class PerformanceTestCase(unittest.TestCase):
    """Classe base para testes de performance."""
    
    def measure_execution_time(self, func, *args, **kwargs):
        """Mede o tempo de execução de uma função."""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        return result, execution_time
    
    def measure_multiple_executions(self, func, iterations=10, *args, **kwargs):
        """Mede múltiplas execuções e retorna estatísticas."""
        times = []
        results = []
        
        for _ in range(iterations):
            result, exec_time = self.measure_execution_time(func, *args, **kwargs)
            times.append(exec_time)
            results.append(result)
        
        stats = {
            'times': times,
            'results': results,
            'mean': mean(times),
            'median': median(times),
            'min': min(times),
            'max': max(times),
            'std_dev': stdev(times) if len(times) > 1 else 0,
            'total': sum(times)
        }
        
        return stats
    
    def assert_performance_threshold(self, execution_time, threshold, message=""):
        """Verifica se o tempo de execução está dentro do limite."""
        self.assertLess(
            execution_time,
            threshold,
            f"Limite de performance excedido: {execution_time:.4f}s > {threshold}s. {message}"
        )
    
    def measure_memory_usage(self, func, *args, **kwargs):
        """Mede o uso de memória durante execução de uma função."""
        process = psutil.Process(os.getpid())
        
        # Memória inicial
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Executar função
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        
        # Memória final
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            'result': result,
            'execution_time': end_time - start_time,
            'memory_before_mb': mem_before,
            'memory_after_mb': mem_after,
            'memory_delta_mb': mem_after - mem_before
        }


class TestPerformanceServidorWeb(PerformanceTestCase):
    """Testes de performance para o WebServerManager."""
    
    def setUp(self):
        """Configuração inicial."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        
        # Criar arquivo HTML simples
        (Path(self.temp_dir) / "index.html").write_text(
            "<html><body><h1>Teste Performance</h1></body></html>",
            encoding='utf-8'
        )
        
        self.config = ConfiguracaoServidorWeb(
            porta_preferencial=8120,
            portas_alternativas=[8121, 8122, 8123],
            diretorio_html=self.temp_dir,
            modo_debug=False  # Desabilitar debug para performance
        )
    
    def test_performance_inicializacao_servidor(self):
        """Testa performance da inicialização do servidor."""
        def inicializar_servidor():
            manager = WebServerManager(self.config)
            url = manager.iniciar_servidor()
            manager.parar_servidor()
            return url
        
        # Medir múltiplas inicializações
        stats = self.measure_multiple_executions(inicializar_servidor, iterations=5)
        
        # Inicialização deve ser rápida (< 1 segundo)
        self.assert_performance_threshold(
            stats['mean'], 1.0,
            f"Inicialização muito lenta. Média: {stats['mean']:.3f}s"
        )
        
        # Variabilidade deve ser baixa
        self.assertLess(stats['std_dev'], 0.5, "Variabilidade muito alta na inicialização")
        
        print(f"📊 Performance Inicialização Servidor:")
        print(f"   Média: {stats['mean']:.3f}s")
        print(f"   Mediana: {stats['median']:.3f}s")
        print(f"   Min/Max: {stats['min']:.3f}s / {stats['max']:.3f}s")
        print(f"   Desvio Padrão: {stats['std_dev']:.3f}s")
    
    def test_performance_descoberta_porta(self):
        """Testa performance da descoberta de portas disponíveis."""
        manager = WebServerManager(self.config)
        
        def encontrar_porta():
            return manager._encontrar_porta_disponivel()
        
        # Medir descoberta de porta
        stats = self.measure_multiple_executions(encontrar_porta, iterations=20)
        
        # Descoberta deve ser muito rápida (< 100ms)
        self.assert_performance_threshold(
            stats['mean'], 0.1,
            f"Descoberta de porta muito lenta. Média: {stats['mean']:.3f}s"
        )
        
        print(f"📊 Performance Descoberta de Porta:")
        print(f"   Média: {stats['mean']*1000:.1f}ms")
        print(f"   Mediana: {stats['median']*1000:.1f}ms")
        print(f"   Min/Max: {stats['min']*1000:.1f}ms / {stats['max']*1000:.1f}ms")
    
    def test_performance_servir_arquivos_concorrente(self):
        """Testa performance ao servir arquivos com múltiplas requisições."""
        manager = WebServerManager(self.config)
        url = manager.iniciar_servidor()
        
        try:
            time.sleep(0.2)  # Aguardar servidor estar pronto
            
            def fazer_requisicao():
                import urllib.request
                with urllib.request.urlopen(f"{url}/index.html", timeout=5) as response:
                    return response.read()
            
            # Teste sequencial
            stats_seq = self.measure_multiple_executions(fazer_requisicao, iterations=10)
            
            # Teste concorrente
            def teste_concorrente():
                threads = []
                results = []
                start_time = time.perf_counter()
                
                def worker():
                    try:
                        result = fazer_requisicao()
                        results.append(len(result))
                    except Exception as e:
                        results.append(0)
                
                # Criar 10 threads simultâneas
                for _ in range(10):
                    thread = threading.Thread(target=worker)
                    threads.append(thread)
                    thread.start()
                
                # Aguardar conclusão
                for thread in threads:
                    thread.join()
                
                end_time = time.perf_counter()
                return end_time - start_time, len([r for r in results if r > 0])
            
            total_time, successful_requests = teste_concorrente()
            
            # Verificar performance
            self.assertEqual(successful_requests, 10, "Nem todas as requisições foram bem-sucedidas")
            self.assertLess(total_time, 2.0, f"Requisições concorrentes muito lentas: {total_time:.2f}s")
            
            print(f"📊 Performance Servir Arquivos:")
            print(f"   Sequencial - Média: {stats_seq['mean']*1000:.1f}ms")
            print(f"   Concorrente - Total: {total_time:.2f}s para 10 requisições")
            print(f"   Concorrente - Média por requisição: {total_time/10*1000:.1f}ms")
            
        finally:
            manager.parar_servidor()
    
    def test_uso_memoria_servidor(self):
        """Testa uso de memória do servidor."""
        def criar_e_usar_servidor():
            manager = WebServerManager(self.config)
            url = manager.iniciar_servidor()
            
            # Simular uso por um tempo
            time.sleep(0.5)
            
            manager.parar_servidor()
            return url
        
        # Medir uso de memória
        memory_stats = self.measure_memory_usage(criar_e_usar_servidor)
        
        # Uso de memória deve ser razoável (< 50MB de delta)
        self.assertLess(
            memory_stats['memory_delta_mb'], 50,
            f"Uso de memória muito alto: {memory_stats['memory_delta_mb']:.1f}MB"
        )
        
        print(f"📊 Uso de Memória Servidor:")
        print(f"   Antes: {memory_stats['memory_before_mb']:.1f}MB")
        print(f"   Depois: {memory_stats['memory_after_mb']:.1f}MB")
        print(f"   Delta: {memory_stats['memory_delta_mb']:.1f}MB")


class TestPerformanceSincronizacao(PerformanceTestCase):
    """Testes de performance para sincronização de dados."""
    
    def setUp(self):
        """Configuração inicial."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        
        self.arquivo_sync = str(Path(self.temp_dir) / "sync_performance.json")
        
        # Criar arquivo inicial
        with open(self.arquivo_sync, 'w') as f:
            json.dump({"dados": {}}, f)
        
        self.json_provider = JSONDataProvider(arquivo_json=self.arquivo_sync)
        self.sync_manager = DataSyncManager(self.json_provider)
    
    def tearDown(self):
        """Limpeza."""
        if hasattr(self, 'sync_manager'):
            self.sync_manager.finalizar()
    
    def test_latencia_sincronizacao_simples(self):
        """Testa latência de sincronização para dados simples."""
        def sincronizar_dados_simples():
            dados = {
                "timestamp": datetime.now().isoformat(),
                "contador": 1,
                "status": "ativo"
            }
            self.sync_manager.atualizar_dados(dados)
            time.sleep(0.05)  # Aguardar debounce mínimo
        
        # Medir latência
        stats = self.measure_multiple_executions(sincronizar_dados_simples, iterations=20)
        
        # Latência deve ser baixa (< 100ms incluindo debounce)
        self.assert_performance_threshold(
            stats['mean'], 0.1,
            f"Latência de sincronização muito alta. Média: {stats['mean']*1000:.1f}ms"
        )
        
        print(f"📊 Latência Sincronização Simples:")
        print(f"   Média: {stats['mean']*1000:.1f}ms")
        print(f"   Mediana: {stats['median']*1000:.1f}ms")
        print(f"   Min/Max: {stats['min']*1000:.1f}ms / {stats['max']*1000:.1f}ms")
    
    def test_performance_dados_complexos(self):
        """Testa performance com dados complexos."""
        def sincronizar_dados_complexos():
            dados = {
                "time_tracker": {
                    "tempo_decorrido": 3600,
                    "esta_executando": True,
                    "projeto_atual": "Projeto Complexo",
                    "historico": [
                        {"data": "2024-01-01", "tempo": 7200},
                        {"data": "2024-01-02", "tempo": 6400},
                        {"data": "2024-01-03", "tempo": 8100}
                    ]
                },
                "flowchart": {
                    "workflow_ativo": "Desenvolvimento",
                    "progresso": 65.5,
                    "estagios": [
                        {"nome": "Planejamento", "concluido": True, "tempo": 1800},
                        {"nome": "Desenvolvimento", "concluido": False, "tempo": 5400},
                        {"nome": "Testes", "concluido": False, "tempo": 0}
                    ]
                },
                "notificacoes": {
                    "total": 15,
                    "nao_lidas": 3,
                    "lista": [
                        {"id": 1, "titulo": "Notificação 1", "lida": False},
                        {"id": 2, "titulo": "Notificação 2", "lida": True},
                        {"id": 3, "titulo": "Notificação 3", "lida": False}
                    ]
                },
                "metadata": {
                    "versao": "1.0.0",
                    "timestamp": datetime.now().isoformat(),
                    "fonte": "TopSidebarContainer"
                }
            }
            self.sync_manager.atualizar_dados(dados)
            time.sleep(0.05)  # Aguardar debounce
        
        # Medir performance com dados complexos
        stats = self.measure_multiple_executions(sincronizar_dados_complexos, iterations=10)
        
        # Mesmo com dados complexos, deve ser rápido (< 200ms)
        self.assert_performance_threshold(
            stats['mean'], 0.2,
            f"Performance com dados complexos inadequada. Média: {stats['mean']*1000:.1f}ms"
        )
        
        print(f"📊 Performance Dados Complexos:")
        print(f"   Média: {stats['mean']*1000:.1f}ms")
        print(f"   Tamanho médio do arquivo: {self._get_file_size_kb():.1f}KB")
    
    def test_performance_multiplas_atualizacoes_rapidas(self):
        """Testa performance com múltiplas atualizações rápidas (debouncing)."""
        def multiplas_atualizacoes():
            start_time = time.perf_counter()
            
            # Fazer 50 atualizações rápidas
            for i in range(50):
                dados = {
                    "contador": i,
                    "timestamp": datetime.now().isoformat()
                }
                self.sync_manager.atualizar_dados(dados)
                time.sleep(0.001)  # 1ms entre atualizações
            
            # Aguardar debounce final
            time.sleep(0.2)
            
            end_time = time.perf_counter()
            return end_time - start_time
        
        # Medir performance
        total_time = multiplas_atualizacoes()
        
        # Debouncing deve otimizar para menos de 1 segundo total
        self.assertLess(total_time, 1.0, f"Debouncing ineficiente: {total_time:.2f}s")
        
        # Verificar se apenas a última atualização foi salva
        with open(self.arquivo_sync, 'r') as f:
            dados_finais = json.load(f)
        
        self.assertEqual(dados_finais['dados']['contador'], 49)  # Última atualização
        
        print(f"📊 Performance Múltiplas Atualizações:")
        print(f"   Tempo total para 50 atualizações: {total_time:.2f}s")
        print(f"   Tempo médio por atualização: {total_time/50*1000:.1f}ms")
    
    def test_performance_concorrencia_sincronizacao(self):
        """Testa performance com sincronização concorrente."""
        def worker_thread(thread_id, num_updates):
            for i in range(num_updates):
                dados = {
                    "thread_id": thread_id,
                    "update": i,
                    "timestamp": datetime.now().isoformat()
                }
                self.sync_manager.atualizar_dados(dados)
                time.sleep(0.01)  # 10ms entre atualizações
        
        # Teste concorrente
        start_time = time.perf_counter()
        
        threads = []
        for thread_id in range(5):
            thread = threading.Thread(target=worker_thread, args=(thread_id, 10))
            threads.append(thread)
            thread.start()
        
        # Aguardar conclusão
        for thread in threads:
            thread.join()
        
        # Aguardar debounce final
        time.sleep(0.2)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # 50 atualizações concorrentes devem completar em tempo razoável
        self.assertLess(total_time, 3.0, f"Sincronização concorrente muito lenta: {total_time:.2f}s")
        
        print(f"📊 Performance Sincronização Concorrente:")
        print(f"   Tempo total: {total_time:.2f}s")
        print(f"   50 atualizações em 5 threads")
    
    def test_uso_memoria_sincronizacao(self):
        """Testa uso de memória durante sincronização."""
        def sincronizacao_intensiva():
            # Fazer muitas sincronizações
            for i in range(100):
                dados = {
                    "iteracao": i,
                    "dados_grandes": "x" * 1000,  # 1KB de dados por iteração
                    "timestamp": datetime.now().isoformat()
                }
                self.sync_manager.atualizar_dados(dados)
                
                if i % 10 == 0:
                    time.sleep(0.01)  # Pequena pausa a cada 10 iterações
            
            # Aguardar debounce final
            time.sleep(0.2)
        
        # Medir uso de memória
        memory_stats = self.measure_memory_usage(sincronizacao_intensiva)
        
        # Uso de memória deve ser controlado (< 20MB de delta)
        self.assertLess(
            memory_stats['memory_delta_mb'], 20,
            f"Vazamento de memória detectado: {memory_stats['memory_delta_mb']:.1f}MB"
        )
        
        print(f"📊 Uso de Memória Sincronização:")
        print(f"   Delta: {memory_stats['memory_delta_mb']:.1f}MB")
        print(f"   Tempo execução: {memory_stats['execution_time']:.2f}s")
    
    def _get_file_size_kb(self):
        """Obtém o tamanho do arquivo de sincronização em KB."""
        try:
            return os.path.getsize(self.arquivo_sync) / 1024
        except OSError:
            return 0


class TestPerformanceWebView(PerformanceTestCase):
    """Testes de performance para WebViewComponent."""
    
    def setUp(self):
        """Configuração inicial."""
        self.mock_page = Mock()
        self.mock_page.update = Mock()
        self.url_teste = "http://localhost:8080"
    
    def test_performance_criacao_webview(self):
        """Testa performance da criação do WebView."""
        def criar_webview():
            with patch('views.components.webview_component.ft.WebView') as mock_webview:
                mock_webview.return_value = Mock()
                component = WebViewComponent(
                    page=self.mock_page,
                    url_servidor=self.url_teste
                )
                return component
        
        # Medir criação
        stats = self.measure_multiple_executions(criar_webview, iterations=10)
        
        # Criação deve ser rápida (< 100ms)
        self.assert_performance_threshold(
            stats['mean'], 0.1,
            f"Criação do WebView muito lenta. Média: {stats['mean']*1000:.1f}ms"
        )
        
        print(f"📊 Performance Criação WebView:")
        print(f"   Média: {stats['mean']*1000:.1f}ms")
    
    def test_performance_atualizacao_dados_webview(self):
        """Testa performance da atualização de dados no WebView."""
        with patch('views.components.webview_component.ft.WebView') as mock_webview:
            mock_webview_instance = Mock()
            mock_webview.return_value = mock_webview_instance
            
            component = WebViewComponent(
                page=self.mock_page,
                url_servidor=self.url_teste
            )
            
            def atualizar_dados():
                dados = {
                    "time_tracker": {"tempo": 3600, "ativo": True},
                    "notificacoes": {"total": 5, "nao_lidas": 2},
                    "timestamp": datetime.now().isoformat()
                }
                component.notificar_atualizacao_dados(dados)
            
            # Medir atualizações
            stats = self.measure_multiple_executions(atualizar_dados, iterations=50)
            
            # Atualizações devem ser muito rápidas (< 10ms)
            self.assert_performance_threshold(
                stats['mean'], 0.01,
                f"Atualização de dados muito lenta. Média: {stats['mean']*1000:.1f}ms"
            )
            
            print(f"📊 Performance Atualização Dados WebView:")
            print(f"   Média: {stats['mean']*1000:.1f}ms")
            print(f"   Total de chamadas JavaScript: {mock_webview_instance.evaluate_javascript.call_count}")


class TestPerformanceIntegracaoCompleta(PerformanceTestCase):
    """Testes de performance para integração completa do sistema."""
    
    def setUp(self):
        """Configuração inicial."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        
        # Criar estrutura web básica
        (Path(self.temp_dir) / "index.html").write_text(
            "<html><body>Performance Test</body></html>",
            encoding='utf-8'
        )
        
        self.config = ConfiguracaoServidorWeb(
            porta_preferencial=8130,
            portas_alternativas=[8131, 8132],
            diretorio_html=self.temp_dir,
            arquivo_sincronizacao=str(Path(self.temp_dir) / "sync.json"),
            intervalo_debounce=0.05,  # Debounce rápido para testes
            modo_debug=False
        )
    
    def test_performance_fluxo_completo(self):
        """Testa performance do fluxo completo servidor → sync → WebView."""
        def fluxo_completo():
            # 1. Inicializar servidor
            server_manager = WebServerManager(self.config)
            url = server_manager.iniciar_servidor()
            
            # 2. Inicializar sincronização
            json_provider = JSONDataProvider(arquivo_json=self.config.arquivo_sincronizacao)
            sync_manager = DataSyncManager(json_provider)
            
            # 3. Criar WebView (mockado)
            with patch('views.components.webview_component.ft.WebView') as mock_webview:
                mock_webview.return_value = Mock()
                webview = WebViewComponent(
                    page=Mock(),
                    url_servidor=url
                )
                
                # 4. Simular ciclo completo de atualização
                dados = {
                    "teste_performance": True,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Sincronizar dados
                sync_manager.atualizar_dados(dados)
                time.sleep(0.1)  # Aguardar debounce
                
                # Atualizar WebView
                webview.notificar_atualizacao_dados(dados)
                
                # 5. Cleanup
                server_manager.parar_servidor()
                sync_manager.finalizar()
                
                return url
        
        # Medir fluxo completo
        stats = self.measure_multiple_executions(fluxo_completo, iterations=3)
        
        # Fluxo completo deve ser razoavelmente rápido (< 2 segundos)
        self.assert_performance_threshold(
            stats['mean'], 2.0,
            f"Fluxo completo muito lento. Média: {stats['mean']:.2f}s"
        )
        
        print(f"📊 Performance Fluxo Completo:")
        print(f"   Média: {stats['mean']:.2f}s")
        print(f"   Min/Max: {stats['min']:.2f}s / {stats['max']:.2f}s")
    
    def test_throughput_sistema_completo(self):
        """Testa throughput do sistema completo."""
        # Inicializar componentes
        server_manager = WebServerManager(self.config)
        url = server_manager.iniciar_servidor()
        
        json_provider = JSONDataProvider(arquivo_json=self.config.arquivo_sincronizacao)
        sync_manager = DataSyncManager(json_provider)
        
        try:
            # Medir throughput de atualizações
            start_time = time.perf_counter()
            num_updates = 100
            
            for i in range(num_updates):
                dados = {
                    "update_id": i,
                    "timestamp": datetime.now().isoformat(),
                    "data": f"update_{i}"
                }
                sync_manager.atualizar_dados(dados)
                
                # Pequena pausa para não sobrecarregar
                if i % 10 == 0:
                    time.sleep(0.01)
            
            # Aguardar debounce final
            time.sleep(0.2)
            
            end_time = time.perf_counter()
            total_time = end_time - start_time
            
            throughput = num_updates / total_time
            
            # Throughput deve ser razoável (> 50 updates/segundo)
            self.assertGreater(
                throughput, 50,
                f"Throughput muito baixo: {throughput:.1f} updates/s"
            )
            
            print(f"📊 Throughput Sistema Completo:")
            print(f"   {num_updates} atualizações em {total_time:.2f}s")
            print(f"   Throughput: {throughput:.1f} updates/segundo")
            
        finally:
            server_manager.parar_servidor()
            sync_manager.finalizar()


if __name__ == '__main__':
    print("🚀 Executando Testes de Performance do Servidor Web Integrado")
    print("=" * 60)
    
    # Configurar logging mínimo para performance
    import logging
    logging.basicConfig(level=logging.ERROR)
    
    # Executar testes com verbosidade
    unittest.main(verbosity=2)