"""
Testes específicos de performance e latência para sincronização de dados.

Este módulo foca especificamente em medir e validar a latência de sincronização
em diferentes cenários, complementando os testes de performance existentes.
"""

import unittest
import time
import threading
import tempfile
import shutil
import json
import statistics
import psutil
import os
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass
from typing import List, Dict, Optional

# Importar componentes do sistema
from services.web_server.server_manager import WebServerManager
from services.web_server.sync_manager import DataSyncManager
from services.web_server.data_provider import JSONDataProvider
from services.web_server.models import ConfiguracaoServidorWeb
from views.components.webview_component import WebViewComponent


@dataclass
class MedicaoLatencia:
    """Classe para armazenar medições de latência."""
    timestamp: datetime
    latencia_ms: float
    tamanho_dados_bytes: int
    tipo_operacao: str
    sucesso: bool
    erro: Optional[str] = None


class LatencyMeasurementTestCase(unittest.TestCase):
    """Classe base para testes de medição de latência."""
    
    def setUp(self):
        """Configuração inicial."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        
        # Configuração otimizada para medições precisas
        self.config = ConfiguracaoServidorWeb(
            porta_preferencial=8300,
            portas_alternativas=[8301, 8302, 8303],
            diretorio_html=self.temp_dir,
            arquivo_sincronizacao=str(Path(self.temp_dir) / "sync_latency.json"),
            intervalo_debounce=0.01,  # 10ms - muito baixo para medições precisas
            intervalo_sincronizacao=0.05,  # 50ms
            modo_debug=False,  # Desabilitar para performance
            cache_habilitado=True,
            pool_threads=1  # Single thread para medições consistentes
        )
        
        # Criar arquivo inicial
        with open(self.config.arquivo_sincronizacao, 'w') as f:
            json.dump({"dados": {}}, f)
        
        self.medicoes: List[MedicaoLatencia] = []
        self.sync_manager = None
    
    def tearDown(self):
        """Limpeza."""
        if self.sync_manager:
            self.sync_manager.finalizar()
    
    def medir_latencia_operacao(self, dados: dict, tipo_operacao: str) -> MedicaoLatencia:
        """Mede a latência de uma operação de sincronização."""
        tamanho_dados = len(json.dumps(dados, ensure_ascii=False).encode('utf-8'))
        
        start_time = time.perf_counter()
        sucesso = True
        erro = None
        
        try:
            self.sync_manager.atualizar_dados(dados)
            # Aguardar debounce
            time.sleep(self.config.intervalo_debounce + 0.01)
        except Exception as e:
            sucesso = False
            erro = str(e)
        
        end_time = time.perf_counter()
        latencia_ms = (end_time - start_time) * 1000
        
        medicao = MedicaoLatencia(
            timestamp=datetime.now(),
            latencia_ms=latencia_ms,
            tamanho_dados_bytes=tamanho_dados,
            tipo_operacao=tipo_operacao,
            sucesso=sucesso,
            erro=erro
        )
        
        self.medicoes.append(medicao)
        return medicao
    
    def calcular_estatisticas_latencia(self, medicoes: List[MedicaoLatencia]) -> Dict:
        """Calcula estatísticas das medições de latência."""
        if not medicoes:
            return {}
        
        latencias = [m.latencia_ms for m in medicoes if m.sucesso]
        
        if not latencias:
            return {"erro": "Nenhuma medição bem-sucedida"}
        
        return {
            "count": len(latencias),
            "mean": statistics.mean(latencias),
            "median": statistics.median(latencias),
            "min": min(latencias),
            "max": max(latencias),
            "std_dev": statistics.stdev(latencias) if len(latencias) > 1 else 0,
            "p95": sorted(latencias)[int(len(latencias) * 0.95)],
            "p99": sorted(latencias)[int(len(latencias) * 0.99)],
            "success_rate": len(latencias) / len(medicoes)
        }
    
    def assert_latencia_threshold(self, stats: Dict, max_mean: float, max_p95: float, min_success_rate: float = 0.95):
        """Verifica se as estatísticas de latência estão dentro dos limites."""
        self.assertLessEqual(
            stats['mean'], max_mean,
            f"Latência média muito alta: {stats['mean']:.2f}ms > {max_mean}ms"
        )
        
        self.assertLessEqual(
            stats['p95'], max_p95,
            f"Latência P95 muito alta: {stats['p95']:.2f}ms > {max_p95}ms"
        )
        
        self.assertGreaterEqual(
            stats['success_rate'], min_success_rate,
            f"Taxa de sucesso muito baixa: {stats['success_rate']:.2%} < {min_success_rate:.2%}"
        )


class TestLatenciaSincronizacaoBasica(LatencyMeasurementTestCase):
    """Testes de latência para sincronização básica."""
    
    def setUp(self):
        """Configuração específica."""
        super().setUp()
        
        json_provider = JSONDataProvider(arquivo_json=self.config.arquivo_sincronizacao)
        self.sync_manager = DataSyncManager(json_provider)
    
    def test_latencia_dados_pequenos(self):
        """Testa latência com dados pequenos (< 1KB)."""
        print("📊 Testando latência com dados pequenos...")
        
        # Dados pequenos variados
        dados_pequenos = [
            {"contador": i, "timestamp": datetime.now().isoformat()}
            for i in range(50)
        ]
        
        # Medir latências
        for i, dados in enumerate(dados_pequenos):
            self.medir_latencia_operacao(dados, f"pequeno_{i}")
            time.sleep(0.02)  # Pequena pausa entre medições
        
        # Calcular estatísticas
        stats = self.calcular_estatisticas_latencia(self.medicoes)
        
        # Verificar limites para dados pequenos
        self.assert_latencia_threshold(stats, max_mean=50.0, max_p95=100.0)
        
        print(f"   ✅ Dados pequenos - Média: {stats['mean']:.1f}ms, P95: {stats['p95']:.1f}ms")
    
    def test_latencia_dados_medios(self):
        """Testa latência com dados médios (1-10KB)."""
        print("📊 Testando latência com dados médios...")
        
        # Dados médios
        for i in range(30):
            dados = {
                "id": i,
                "timestamp": datetime.now().isoformat(),
                "payload": {
                    "array": list(range(100)),  # ~400 bytes
                    "strings": [f"string_{j}" * 10 for j in range(20)],  # ~2KB
                    "metadata": {
                        "version": "1.0.0",
                        "description": "Dados de teste médios" * 20,  # ~500 bytes
                        "tags": [f"tag_{k}" for k in range(50)]  # ~300 bytes
                    }
                }
            }
            
            self.medir_latencia_operacao(dados, f"medio_{i}")
            time.sleep(0.03)
        
        stats = self.calcular_estatisticas_latencia(self.medicoes)
        
        # Limites mais relaxados para dados médios
        self.assert_latencia_threshold(stats, max_mean=100.0, max_p95=200.0)
        
        print(f"   ✅ Dados médios - Média: {stats['mean']:.1f}ms, P95: {stats['p95']:.1f}ms")
    
    def test_latencia_dados_grandes(self):
        """Testa latência com dados grandes (10-100KB)."""
        print("📊 Testando latência com dados grandes...")
        
        # Dados grandes
        for i in range(20):
            dados = {
                "id": i,
                "timestamp": datetime.now().isoformat(),
                "large_payload": {
                    "big_array": list(range(2000)),  # ~8KB
                    "big_strings": [f"large_string_{j}" * 100 for j in range(50)],  # ~25KB
                    "nested_data": {
                        f"level1_{k}": {
                            f"level2_{l}": f"value_{k}_{l}" * 20
                            for l in range(20)
                        } for k in range(10)
                    },  # ~20KB
                    "binary_like": "x" * 10000  # 10KB
                }
            }
            
            self.medir_latencia_operacao(dados, f"grande_{i}")
            time.sleep(0.05)
        
        stats = self.calcular_estatisticas_latencia(self.medicoes)
        
        # Limites mais relaxados para dados grandes
        self.assert_latencia_threshold(stats, max_mean=300.0, max_p95=500.0)
        
        print(f"   ✅ Dados grandes - Média: {stats['mean']:.1f}ms, P95: {stats['p95']:.1f}ms")
    
    def test_latencia_atualizacoes_incrementais(self):
        """Testa latência de atualizações incrementais."""
        print("📊 Testando latência de atualizações incrementais...")
        
        # Dados base
        dados_base = {
            "base_data": True,
            "counters": {},
            "arrays": {},
            "metadata": {
                "created": datetime.now().isoformat(),
                "version": "1.0.0"
            }
        }
        
        # Primeira sincronização (dados base)
        self.medir_latencia_operacao(dados_base, "base")
        time.sleep(0.1)
        
        # Atualizações incrementais
        for i in range(40):
            # Adicionar dados incrementalmente
            dados_base["counters"][f"counter_{i}"] = i
            dados_base["arrays"][f"array_{i}"] = list(range(i * 5, (i + 1) * 5))
            dados_base["metadata"]["last_update"] = datetime.now().isoformat()
            dados_base["metadata"]["update_count"] = i + 1
            
            self.medir_latencia_operacao(dados_base.copy(), f"incremental_{i}")
            time.sleep(0.02)
        
        # Analisar apenas as atualizações incrementais
        medicoes_incrementais = [m for m in self.medicoes if m.tipo_operacao.startswith("incremental_")]
        stats = self.calcular_estatisticas_latencia(medicoes_incrementais)
        
        # Verificar se latência não cresce muito com o tamanho
        primeiras_10 = medicoes_incrementais[:10]
        ultimas_10 = medicoes_incrementais[-10:]
        
        latencia_inicial = statistics.mean([m.latencia_ms for m in primeiras_10 if m.sucesso])
        latencia_final = statistics.mean([m.latencia_ms for m in ultimas_10 if m.sucesso])
        
        # Latência não deve crescer mais que 3x
        self.assertLess(
            latencia_final / latencia_inicial, 3.0,
            f"Latência cresceu muito: {latencia_inicial:.1f}ms → {latencia_final:.1f}ms"
        )
        
        print(f"   ✅ Incrementais - Inicial: {latencia_inicial:.1f}ms, Final: {latencia_final:.1f}ms")


class TestLatenciaConcorrencia(LatencyMeasurementTestCase):
    """Testes de latência sob condições de concorrência."""
    
    def setUp(self):
        """Configuração para testes de concorrência."""
        super().setUp()
        
        # Configuração otimizada para concorrência
        self.config.pool_threads = 4
        self.config.intervalo_debounce = 0.02
        
        json_provider = JSONDataProvider(arquivo_json=self.config.arquivo_sincronizacao)
        self.sync_manager = DataSyncManager(json_provider)
        
        self.medicoes_por_thread = {}
        self.lock = threading.Lock()
    
    def worker_latencia(self, worker_id: int, num_operations: int):
        """Worker para medir latência em thread separada."""
        medicoes_worker = []
        
        for i in range(num_operations):
            dados = {
                "worker_id": worker_id,
                "operation": i,
                "timestamp": datetime.now().isoformat(),
                "thread_name": threading.current_thread().name,
                "data": f"worker_{worker_id}_data_{i}" * 10
            }
            
            start_time = time.perf_counter()
            
            try:
                self.sync_manager.atualizar_dados(dados)
                time.sleep(self.config.intervalo_debounce + 0.005)
                sucesso = True
                erro = None
            except Exception as e:
                sucesso = False
                erro = str(e)
            
            end_time = time.perf_counter()
            latencia_ms = (end_time - start_time) * 1000
            
            medicao = MedicaoLatencia(
                timestamp=datetime.now(),
                latencia_ms=latencia_ms,
                tamanho_dados_bytes=len(json.dumps(dados).encode()),
                tipo_operacao=f"worker_{worker_id}_op_{i}",
                sucesso=sucesso,
                erro=erro
            )
            
            medicoes_worker.append(medicao)
            
            # Pequena variação no timing
            time.sleep(0.01 + (i % 3) * 0.005)
        
        with self.lock:
            self.medicoes_por_thread[worker_id] = medicoes_worker
            self.medicoes.extend(medicoes_worker)
    
    def test_latencia_com_2_threads_concorrentes(self):
        """Testa latência com 2 threads concorrentes."""
        print("📊 Testando latência com 2 threads concorrentes...")
        
        threads = []
        for worker_id in range(2):
            thread = threading.Thread(
                target=self.worker_latencia,
                args=(worker_id, 25)
            )
            threads.append(thread)
            thread.start()
        
        # Aguardar conclusão
        for thread in threads:
            thread.join()
        
        # Analisar resultados
        stats_geral = self.calcular_estatisticas_latencia(self.medicoes)
        
        # Comparar latências entre threads
        stats_thread_0 = self.calcular_estatisticas_latencia(self.medicoes_por_thread[0])
        stats_thread_1 = self.calcular_estatisticas_latencia(self.medicoes_por_thread[1])
        
        # Verificar limites
        self.assert_latencia_threshold(stats_geral, max_mean=150.0, max_p95=300.0)
        
        # Verificar que as threads têm latências similares (diferença < 50%)
        diff_media = abs(stats_thread_0['mean'] - stats_thread_1['mean'])
        media_geral = (stats_thread_0['mean'] + stats_thread_1['mean']) / 2
        
        self.assertLess(
            diff_media / media_geral, 0.5,
            f"Latências muito diferentes entre threads: {stats_thread_0['mean']:.1f}ms vs {stats_thread_1['mean']:.1f}ms"
        )
        
        print(f"   ✅ 2 threads - Geral: {stats_geral['mean']:.1f}ms, Thread0: {stats_thread_0['mean']:.1f}ms, Thread1: {stats_thread_1['mean']:.1f}ms")
    
    def test_latencia_com_5_threads_alta_concorrencia(self):
        """Testa latência com 5 threads (alta concorrência)."""
        print("📊 Testando latência com 5 threads (alta concorrência)...")
        
        threads = []
        for worker_id in range(5):
            thread = threading.Thread(
                target=self.worker_latencia,
                args=(worker_id, 15)
            )
            threads.append(thread)
            thread.start()
        
        # Aguardar conclusão
        for thread in threads:
            thread.join()
        
        # Analisar resultados
        stats_geral = self.calcular_estatisticas_latencia(self.medicoes)
        
        # Com alta concorrência, limites mais relaxados
        self.assert_latencia_threshold(stats_geral, max_mean=250.0, max_p95=500.0, min_success_rate=0.9)
        
        # Verificar distribuição de latências por thread
        latencias_por_thread = {}
        for worker_id in range(5):
            stats_thread = self.calcular_estatisticas_latencia(self.medicoes_por_thread[worker_id])
            latencias_por_thread[worker_id] = stats_thread['mean']
        
        # Verificar que nenhuma thread tem latência muito superior às outras
        max_latencia = max(latencias_por_thread.values())
        min_latencia = min(latencias_por_thread.values())
        
        self.assertLess(
            max_latencia / min_latencia, 2.0,
            f"Latências muito desbalanceadas: {min_latencia:.1f}ms - {max_latencia:.1f}ms"
        )
        
        print(f"   ✅ 5 threads - Geral: {stats_geral['mean']:.1f}ms, Range: {min_latencia:.1f}-{max_latencia:.1f}ms")


class TestLatenciaWebView(LatencyMeasurementTestCase):
    """Testes de latência específicos para WebView."""
    
    def setUp(self):
        """Configuração para testes de WebView."""
        super().setUp()
        
        json_provider = JSONDataProvider(arquivo_json=self.config.arquivo_sincronizacao)
        self.sync_manager = DataSyncManager(json_provider)
        
        self.mock_page = Mock()
        self.mock_page.update = Mock()
    
    def test_latencia_notificacao_webview(self):
        """Testa latência de notificação para WebView."""
        print("📊 Testando latência de notificação WebView...")
        
        with patch('views.components.webview_component.ft.WebView') as mock_webview:
            mock_webview_instance = Mock()
            mock_webview.return_value = mock_webview_instance
            
            # Criar WebView
            webview = WebViewComponent(
                page=self.mock_page,
                url_servidor="http://localhost:8300"
            )
            
            # Medir latência de notificações
            for i in range(30):
                dados = {
                    "webview_test": True,
                    "notification_id": i,
                    "timestamp": datetime.now().isoformat(),
                    "payload": {
                        "message": f"Notificação {i}",
                        "data": list(range(i * 5, (i + 1) * 5))
                    }
                }
                
                # Medir tempo total: sincronização + notificação WebView
                start_time = time.perf_counter()
                
                # 1. Sincronizar dados
                self.sync_manager.atualizar_dados(dados)
                time.sleep(self.config.intervalo_debounce + 0.01)
                
                # 2. Notificar WebView
                webview.notificar_atualizacao_dados(dados)
                
                end_time = time.perf_counter()
                latencia_ms = (end_time - start_time) * 1000
                
                medicao = MedicaoLatencia(
                    timestamp=datetime.now(),
                    latencia_ms=latencia_ms,
                    tamanho_dados_bytes=len(json.dumps(dados).encode()),
                    tipo_operacao=f"webview_notification_{i}",
                    sucesso=True
                )
                
                self.medicoes.append(medicao)
                time.sleep(0.02)
            
            # Verificar se JavaScript foi executado
            self.assertEqual(mock_webview_instance.evaluate_javascript.call_count, 30)
            
            # Analisar latências
            stats = self.calcular_estatisticas_latencia(self.medicoes)
            
            # Limites para fluxo completo (sync + WebView)
            self.assert_latencia_threshold(stats, max_mean=100.0, max_p95=200.0)
            
            print(f"   ✅ WebView notifications - Média: {stats['mean']:.1f}ms, P95: {stats['p95']:.1f}ms")
    
    def test_latencia_multiplos_webviews(self):
        """Testa latência com múltiplos WebViews."""
        print("📊 Testando latência com múltiplos WebViews...")
        
        webviews = []
        
        with patch('views.components.webview_component.ft.WebView') as mock_webview:
            # Criar 3 WebViews
            for i in range(3):
                mock_instance = Mock()
                mock_webview.return_value = mock_instance
                
                webview = WebViewComponent(
                    page=self.mock_page,
                    url_servidor=f"http://localhost:830{i}"
                )
                webviews.append((webview, mock_instance))
            
            # Medir latência de broadcast para todos os WebViews
            for i in range(20):
                dados = {
                    "broadcast_test": True,
                    "message_id": i,
                    "timestamp": datetime.now().isoformat(),
                    "content": f"Broadcast message {i}" * 10
                }
                
                start_time = time.perf_counter()
                
                # 1. Sincronizar dados
                self.sync_manager.atualizar_dados(dados)
                time.sleep(self.config.intervalo_debounce + 0.01)
                
                # 2. Notificar todos os WebViews
                for webview, _ in webviews:
                    webview.notificar_atualizacao_dados(dados)
                
                end_time = time.perf_counter()
                latencia_ms = (end_time - start_time) * 1000
                
                medicao = MedicaoLatencia(
                    timestamp=datetime.now(),
                    latencia_ms=latencia_ms,
                    tamanho_dados_bytes=len(json.dumps(dados).encode()),
                    tipo_operacao=f"broadcast_{i}",
                    sucesso=True
                )
                
                self.medicoes.append(medicao)
                time.sleep(0.03)
            
            # Verificar se todos os WebViews receberam as notificações
            for _, mock_instance in webviews:
                self.assertEqual(mock_instance.evaluate_javascript.call_count, 20)
            
            # Analisar latências
            stats = self.calcular_estatisticas_latencia(self.medicoes)
            
            # Limites para broadcast (deve ser proporcional ao número de WebViews)
            self.assert_latencia_threshold(stats, max_mean=150.0, max_p95=300.0)
            
            print(f"   ✅ Múltiplos WebViews - Média: {stats['mean']:.1f}ms, P95: {stats['p95']:.1f}ms")


class TestLatenciaMemoriaRecursos(LatencyMeasurementTestCase):
    """Testes de latência relacionados ao uso de memória e recursos."""
    
    def setUp(self):
        """Configuração para testes de recursos."""
        super().setUp()
        
        json_provider = JSONDataProvider(arquivo_json=self.config.arquivo_sincronizacao)
        self.sync_manager = DataSyncManager(json_provider)
        
        self.process = psutil.Process(os.getpid())
        self.memoria_inicial = self.process.memory_info().rss / 1024 / 1024  # MB
    
    def test_latencia_vs_uso_memoria(self):
        """Testa correlação entre latência e uso de memória."""
        print("📊 Testando correlação latência vs uso de memória...")
        
        medicoes_memoria = []
        
        for i in range(50):
            # Dados que crescem progressivamente
            dados = {
                "memory_test": True,
                "iteration": i,
                "timestamp": datetime.now().isoformat(),
                "growing_data": {
                    "array": list(range(i * 100)),  # Cresce com i
                    "strings": [f"string_{j}" * (i + 1) for j in range(50)],  # Cresce com i
                    "nested": {
                        f"level_{k}": f"data_{k}" * (i + 1)
                        for k in range(min(i + 1, 20))
                    }
                }
            }
            
            # Medir memória antes
            memoria_antes = self.process.memory_info().rss / 1024 / 1024
            
            # Medir latência
            medicao = self.medir_latencia_operacao(dados, f"memory_{i}")
            
            # Medir memória depois
            memoria_depois = self.process.memory_info().rss / 1024 / 1024
            
            medicoes_memoria.append({
                "iteracao": i,
                "latencia_ms": medicao.latencia_ms,
                "memoria_antes_mb": memoria_antes,
                "memoria_depois_mb": memoria_depois,
                "delta_memoria_mb": memoria_depois - memoria_antes,
                "tamanho_dados_kb": medicao.tamanho_dados_bytes / 1024
            })
            
            time.sleep(0.02)
        
        # Analisar correlações
        latencias = [m["latencia_ms"] for m in medicoes_memoria]
        tamanhos = [m["tamanho_dados_kb"] for m in medicoes_memoria]
        memoria_final = medicoes_memoria[-1]["memoria_depois_mb"]
        
        # Verificar que latência não cresce exponencialmente com o tamanho
        latencia_inicial = statistics.mean(latencias[:10])
        latencia_final = statistics.mean(latencias[-10:])
        
        self.assertLess(
            latencia_final / latencia_inicial, 5.0,
            f"Latência cresceu muito com tamanho dos dados: {latencia_inicial:.1f}ms → {latencia_final:.1f}ms"
        )
        
        # Verificar uso de memória
        delta_memoria_total = memoria_final - self.memoria_inicial
        self.assertLess(
            delta_memoria_total, 100.0,
            f"Uso de memória muito alto: {delta_memoria_total:.1f}MB"
        )
        
        print(f"   ✅ Memória vs Latência - Inicial: {latencia_inicial:.1f}ms, Final: {latencia_final:.1f}ms")
        print(f"   📈 Uso de memória: +{delta_memoria_total:.1f}MB")
    
    def test_latencia_com_pressao_memoria(self):
        """Testa latência sob pressão de memória."""
        print("📊 Testando latência sob pressão de memória...")
        
        # Criar pressão de memória alocando arrays grandes
        arrays_pressao = []
        try:
            # Alocar ~50MB em arrays
            for i in range(10):
                array_grande = [j for j in range(500000)]  # ~5MB cada
                arrays_pressao.append(array_grande)
            
            memoria_com_pressao = self.process.memory_info().rss / 1024 / 1024
            print(f"   💾 Memória com pressão: {memoria_com_pressao:.1f}MB")
            
            # Medir latências sob pressão
            for i in range(30):
                dados = {
                    "pressure_test": True,
                    "iteration": i,
                    "timestamp": datetime.now().isoformat(),
                    "data": f"test_data_{i}" * 100
                }
                
                self.medir_latencia_operacao(dados, f"pressure_{i}")
                time.sleep(0.02)
            
            # Analisar resultados
            stats = self.calcular_estatisticas_latencia(self.medicoes)
            
            # Sob pressão de memória, limites mais relaxados
            self.assert_latencia_threshold(stats, max_mean=200.0, max_p95=400.0, min_success_rate=0.9)
            
            print(f"   ✅ Sob pressão - Média: {stats['mean']:.1f}ms, P95: {stats['p95']:.1f}ms")
            
        finally:
            # Liberar memória
            arrays_pressao.clear()
            import gc
            gc.collect()


if __name__ == '__main__':
    print("⚡ Executando Testes Específicos de Latência de Sincronização")
    print("=" * 65)
    
    # Configurar logging mínimo para performance
    import logging
    logging.basicConfig(level=logging.ERROR)
    
    # Executar testes com verbosidade
    unittest.main(verbosity=2)