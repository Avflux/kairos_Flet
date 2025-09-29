"""
Testes avançados de fluxo completo para o sistema de servidor web integrado.

Este módulo complementa os testes existentes com cenários mais complexos
e específicos, incluindo testes de stress, concorrência avançada e
integração com componentes reais do sistema.
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
import asyncio
import concurrent.futures
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta
from queue import Queue, Empty

import flet as ft

# Importar componentes do sistema
from services.web_server.server_manager import WebServerManager
from services.web_server.sync_manager import DataSyncManager
from services.web_server.data_provider import JSONDataProvider
from services.web_server.models import ConfiguracaoServidorWeb, DadosTopSidebar
from services.web_server.exceptions import ServidorWebError, WebViewError, SincronizacaoError
from services.web_server.config import (
    criar_configuracao_desenvolvimento,
    criar_configuracao_producao,
    diagnosticar_configuracao
)
from views.components.webview_component import WebViewComponent
from views.components.top_sidebar_container import TopSidebarContainer


class TestFluxoCompletoAvancado(unittest.TestCase):
    """Testes avançados de fluxo completo do sistema."""
    
    def setUp(self):
        """Configuração inicial para cada teste."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        
        # Criar estrutura web completa
        self.criar_estrutura_web_completa()
        
        # Configuração avançada
        self.config = ConfiguracaoServidorWeb(
            porta_preferencial=8200,
            portas_alternativas=[8201, 8202, 8203, 8204],
            diretorio_html=self.temp_dir,
            arquivo_sincronizacao=str(Path(self.temp_dir) / "data" / "sync.json"),
            modo_debug=True,
            intervalo_debounce=0.05,  # Muito rápido para testes
            intervalo_sincronizacao=0.1,
            max_tentativas_retry=5,
            delay_retry=0.1,
            timeout_servidor=10,
            cache_habilitado=True,
            compressao_habilitada=False,  # Desabilitar para testes
            pool_threads=2
        )
        
        self.mock_page = Mock(spec=ft.Page)
        self.mock_page.update = Mock()
        
        # Componentes
        self.server_manager = None
        self.sync_manager = None
        self.webview_component = None
        self.container = None
        
        # Métricas de teste
        self.metricas = {
            'tempos_resposta': [],
            'erros_encontrados': [],
            'atualizacoes_realizadas': 0,
            'bytes_transferidos': 0
        }
    
    def tearDown(self):
        """Limpeza após cada teste."""
        if self.server_manager and self.server_manager.esta_ativo():
            self.server_manager.parar_servidor()
        
        if self.sync_manager:
            self.sync_manager.finalizar()
    
    def criar_estrutura_web_completa(self):
        """Cria estrutura web completa para testes avançados."""
        # Diretórios
        (Path(self.temp_dir) / "css").mkdir(exist_ok=True)
        (Path(self.temp_dir) / "js").mkdir(exist_ok=True)
        (Path(self.temp_dir) / "data").mkdir(exist_ok=True)
        (Path(self.temp_dir) / "assets").mkdir(exist_ok=True)
        
        # HTML principal com recursos avançados
        html_content = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Teste Avançado</title>
    <link rel="stylesheet" href="css/styles.css">
</head>
<body>
    <div id="app">
        <header>
            <h1>Teste Fluxo Completo Avançado</h1>
            <div id="status" class="status-ok">Carregando...</div>
        </header>
        
        <main>
            <section id="metricas">
                <h2>Métricas em Tempo Real</h2>
                <div id="contador-updates">0</div>
                <div id="latencia-atual">0ms</div>
                <div id="throughput">0 ops/s</div>
                <div id="memoria-uso">0MB</div>
            </section>
            
            <section id="dados-complexos">
                <h2>Dados Complexos</h2>
                <div id="dados-json"></div>
                <div id="historico-mudancas"></div>
            </section>
            
            <section id="testes-interativos">
                <h2>Testes Interativos</h2>
                <button id="btn-stress-test">Teste de Stress</button>
                <button id="btn-clear-data">Limpar Dados</button>
                <button id="btn-simulate-error">Simular Erro</button>
                <div id="resultados-testes"></div>
            </section>
        </main>
    </div>
    
    <script src="js/advanced-sync.js"></script>
    <script src="js/test-utils.js"></script>
</body>
</html>"""
        
        (Path(self.temp_dir) / "index.html").write_text(html_content, encoding='utf-8')
        
        # CSS avançado
        css_content = """
body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
#app { max-width: 1200px; margin: 0 auto; }
header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
.status-ok { color: #28a745; font-weight: bold; }
.status-error { color: #dc3545; font-weight: bold; }
.status-warning { color: #ffc107; font-weight: bold; }
section { background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
button { padding: 10px 20px; margin: 5px; border: none; border-radius: 4px; background: #007bff; color: white; cursor: pointer; }
button:hover { background: #0056b3; }
#dados-json { background: #f8f9fa; padding: 15px; border-radius: 4px; font-family: monospace; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }
.metric { display: inline-block; margin: 10px; padding: 15px; background: #e9ecef; border-radius: 4px; min-width: 100px; text-align: center; }
.metric-value { font-size: 1.5em; font-weight: bold; color: #495057; }
.metric-label { font-size: 0.9em; color: #6c757d; }
"""
        
        (Path(self.temp_dir) / "css" / "styles.css").write_text(css_content, encoding='utf-8')
        
        # JavaScript avançado para sincronização
        js_sync_content = """
class AdvancedSyncManager {
    constructor() {
        this.dados = {};
        this.metricas = {
            updates: 0,
            latencias: [],
            erros: 0,
            startTime: Date.now()
        };
        this.historico = [];
        this.maxHistorico = 50;
        this.intervalo = 500; // 500ms para testes rápidos
        this.iniciar();
    }
    
    iniciar() {
        this.syncInterval = setInterval(() => this.sincronizar(), this.intervalo);
        this.metricsInterval = setInterval(() => this.atualizarMetricas(), 1000);
        console.log('AdvancedSyncManager iniciado');
    }
    
    async sincronizar() {
        const startTime = performance.now();
        
        try {
            const response = await fetch('/data/sync.json?t=' + Date.now());
            const dados = await response.json();
            
            const endTime = performance.now();
            const latencia = endTime - startTime;
            
            this.metricas.latencias.push(latencia);
            if (this.metricas.latencias.length > 100) {
                this.metricas.latencias.shift();
            }
            
            if (JSON.stringify(dados.dados) !== JSON.stringify(this.dados)) {
                this.dados = dados.dados || {};
                this.metricas.updates++;
                
                this.historico.unshift({
                    timestamp: new Date().toISOString(),
                    dados: JSON.parse(JSON.stringify(this.dados)),
                    latencia: latencia
                });
                
                if (this.historico.length > this.maxHistorico) {
                    this.historico.pop();
                }
                
                this.atualizarInterface();
            }
            
            this.atualizarStatus('ok', 'Conectado');
            
        } catch (error) {
            this.metricas.erros++;
            this.atualizarStatus('error', 'Erro: ' + error.message);
            console.error('Erro na sincronização:', error);
        }
    }
    
    atualizarInterface() {
        // Atualizar dados JSON
        const dadosElement = document.getElementById('dados-json');
        if (dadosElement) {
            dadosElement.textContent = JSON.stringify(this.dados, null, 2);
        }
        
        // Atualizar histórico
        const historicoElement = document.getElementById('historico-mudancas');
        if (historicoElement) {
            const ultimasChanges = this.historico.slice(0, 5);
            historicoElement.innerHTML = ultimasChanges.map(item => 
                `<div class="historico-item">
                    <strong>${new Date(item.timestamp).toLocaleTimeString()}</strong>
                    (${item.latencia.toFixed(1)}ms)
                </div>`
            ).join('');
        }
    }
    
    atualizarMetricas() {
        const contadorElement = document.getElementById('contador-updates');
        if (contadorElement) {
            contadorElement.textContent = this.metricas.updates;
        }
        
        const latenciaElement = document.getElementById('latencia-atual');
        if (latenciaElement && this.metricas.latencias.length > 0) {
            const latenciaMedia = this.metricas.latencias.reduce((a, b) => a + b, 0) / this.metricas.latencias.length;
            latenciaElement.textContent = latenciaMedia.toFixed(1) + 'ms';
        }
        
        const throughputElement = document.getElementById('throughput');
        if (throughputElement) {
            const tempoDecorrido = (Date.now() - this.metricas.startTime) / 1000;
            const throughput = this.metricas.updates / tempoDecorrido;
            throughputElement.textContent = throughput.toFixed(2) + ' ops/s';
        }
        
        const memoriaElement = document.getElementById('memoria-uso');
        if (memoriaElement && performance.memory) {
            const memoriaUsada = performance.memory.usedJSHeapSize / 1024 / 1024;
            memoriaElement.textContent = memoriaUsada.toFixed(1) + 'MB';
        }
    }
    
    atualizarStatus(tipo, mensagem) {
        const statusElement = document.getElementById('status');
        if (statusElement) {
            statusElement.textContent = mensagem;
            statusElement.className = 'status-' + tipo;
        }
    }
    
    pararTestes() {
        if (this.syncInterval) clearInterval(this.syncInterval);
        if (this.metricsInterval) clearInterval(this.metricsInterval);
    }
}

// Inicializar quando página carregar
document.addEventListener('DOMContentLoaded', () => {
    window.advancedSync = new AdvancedSyncManager();
    
    // Adicionar event listeners para botões de teste
    document.getElementById('btn-stress-test')?.addEventListener('click', () => {
        console.log('Iniciando teste de stress...');
        // Implementar teste de stress
    });
    
    document.getElementById('btn-clear-data')?.addEventListener('click', () => {
        window.advancedSync.dados = {};
        window.advancedSync.atualizarInterface();
    });
    
    document.getElementById('btn-simulate-error')?.addEventListener('click', () => {
        throw new Error('Erro simulado para teste');
    });
});
"""
        
        (Path(self.temp_dir) / "js" / "advanced-sync.js").write_text(js_sync_content, encoding='utf-8')
        
        # Utilitários de teste em JavaScript
        js_utils_content = """
// Utilitários para testes
window.testUtils = {
    medirPerformance: function(funcao, iteracoes = 100) {
        const tempos = [];
        for (let i = 0; i < iteracoes; i++) {
            const start = performance.now();
            funcao();
            const end = performance.now();
            tempos.push(end - start);
        }
        
        return {
            media: tempos.reduce((a, b) => a + b, 0) / tempos.length,
            min: Math.min(...tempos),
            max: Math.max(...tempos),
            total: tempos.reduce((a, b) => a + b, 0)
        };
    },
    
    simularCarga: function(requests = 100, intervalo = 10) {
        let completados = 0;
        const resultados = [];
        
        for (let i = 0; i < requests; i++) {
            setTimeout(async () => {
                try {
                    const start = performance.now();
                    const response = await fetch('/data/sync.json?load_test=' + i);
                    const end = performance.now();
                    
                    resultados.push({
                        id: i,
                        tempo: end - start,
                        status: response.status,
                        sucesso: response.ok
                    });
                    
                    completados++;
                    if (completados === requests) {
                        console.log('Teste de carga concluído:', resultados);
                    }
                } catch (error) {
                    resultados.push({
                        id: i,
                        erro: error.message,
                        sucesso: false
                    });
                    completados++;
                }
            }, i * intervalo);
        }
        
        return resultados;
    },
    
    verificarMemoria: function() {
        if (performance.memory) {
            return {
                usada: performance.memory.usedJSHeapSize,
                total: performance.memory.totalJSHeapSize,
                limite: performance.memory.jsHeapSizeLimit
            };
        }
        return null;
    }
};
"""
        
        (Path(self.temp_dir) / "js" / "test-utils.js").write_text(js_utils_content, encoding='utf-8')
        
        # Arquivo de sincronização inicial
        dados_iniciais = {
            "dados": {
                "teste_avancado": True,
                "timestamp_inicio": datetime.now().isoformat(),
                "configuracao": {
                    "modo": "teste_avancado",
                    "versao": "1.0.0"
                },
                "metricas": {
                    "contador": 0,
                    "operacoes_realizadas": 0
                }
            },
            "timestamp": datetime.now().isoformat(),
            "versao": 1
        }
        
        (Path(self.temp_dir) / "data" / "sync.json").write_text(
            json.dumps(dados_iniciais, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
    
    def test_fluxo_completo_com_multiplos_clientes_simultaneos(self):
        """Testa fluxo completo com múltiplos clientes WebView simultâneos."""
        # Inicializar servidor
        self.server_manager = WebServerManager(self.config)
        url_servidor = self.server_manager.iniciar_servidor()
        
        # Inicializar sincronização
        json_provider = JSONDataProvider(arquivo_json=self.config.arquivo_sincronizacao)
        self.sync_manager = DataSyncManager(json_provider)
        
        # Criar múltiplos WebViews simulados
        webviews = []
        with patch('views.components.webview_component.ft.WebView') as mock_webview:
            for i in range(5):
                mock_instance = Mock()
                mock_webview.return_value = mock_instance
                
                webview = WebViewComponent(
                    page=self.mock_page,
                    url_servidor=url_servidor,
                    modo_debug=True
                )
                webviews.append((webview, mock_instance))
        
        # Simular múltiplas atualizações simultâneas
        def worker_atualizacoes(worker_id, num_updates):
            for i in range(num_updates):
                dados = {
                    "worker_id": worker_id,
                    "update_number": i,
                    "timestamp": datetime.now().isoformat(),
                    "dados_complexos": {
                        "lista": list(range(i * 10, (i + 1) * 10)),
                        "mapa": {f"chave_{j}": f"valor_{j}" for j in range(5)},
                        "aninhado": {
                            "nivel1": {
                                "nivel2": {
                                    "valor": i * worker_id
                                }
                            }
                        }
                    }
                }
                
                self.sync_manager.atualizar_dados(dados)
                time.sleep(0.02)  # 20ms entre atualizações
        
        # Executar workers em paralelo
        threads = []
        start_time = time.perf_counter()
        
        for worker_id in range(3):
            thread = threading.Thread(
                target=worker_atualizacoes,
                args=(worker_id, 20)
            )
            threads.append(thread)
            thread.start()
        
        # Aguardar conclusão
        for thread in threads:
            thread.join()
        
        # Aguardar debounce final
        time.sleep(0.3)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Verificar resultados
        self.assertLess(total_time, 5.0, f"Tempo total muito alto: {total_time:.2f}s")
        
        # Verificar se dados finais foram salvos
        with open(self.config.arquivo_sincronizacao, 'r') as f:
            dados_finais = json.load(f)
        
        self.assertIn('dados', dados_finais)
        self.assertIn('worker_id', dados_finais['dados'])
        
        # Notificar todos os WebViews
        dados_notificacao = dados_finais['dados']
        for webview, mock_instance in webviews:
            webview.notificar_atualizacao_dados(dados_notificacao)
            mock_instance.evaluate_javascript.assert_called()
        
        print(f"✅ Teste múltiplos clientes: {total_time:.2f}s, {len(webviews)} WebViews")
    
    def test_stress_test_alta_frequencia_atualizacoes(self):
        """Teste de stress com alta frequência de atualizações."""
        # Configuração otimizada para stress test
        config_stress = ConfiguracaoServidorWeb(
            porta_preferencial=8205,
            diretorio_html=self.temp_dir,
            arquivo_sincronizacao=str(Path(self.temp_dir) / "data" / "sync_stress.json"),
            intervalo_debounce=0.01,  # 10ms - muito rápido
            max_tentativas_retry=10,
            pool_threads=4
        )
        
        # Inicializar componentes
        self.server_manager = WebServerManager(config_stress)
        url_servidor = self.server_manager.iniciar_servidor()
        
        json_provider = JSONDataProvider(arquivo_json=config_stress.arquivo_sincronizacao)
        self.sync_manager = DataSyncManager(json_provider)
        
        # Métricas do teste
        total_updates = 500
        updates_realizados = 0
        erros_encontrados = []
        tempos_resposta = []
        
        def stress_worker():
            nonlocal updates_realizados
            
            for i in range(total_updates // 5):  # 5 workers, 100 updates cada
                try:
                    start_time = time.perf_counter()
                    
                    dados = {
                        "stress_test": True,
                        "update_id": updates_realizados,
                        "timestamp": datetime.now().isoformat(),
                        "payload": {
                            "dados_grandes": "x" * 1000,  # 1KB por update
                            "array_numeros": list(range(100)),
                            "objeto_complexo": {
                                f"prop_{j}": f"valor_{j}_{i}" for j in range(20)
                            }
                        }
                    }
                    
                    self.sync_manager.atualizar_dados(dados)
                    
                    end_time = time.perf_counter()
                    tempo_resposta = (end_time - start_time) * 1000  # ms
                    tempos_resposta.append(tempo_resposta)
                    
                    updates_realizados += 1
                    
                    # Pequena pausa para não sobrecarregar
                    time.sleep(0.001)  # 1ms
                    
                except Exception as e:
                    erros_encontrados.append(str(e))
        
        # Executar stress test
        start_time = time.perf_counter()
        
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=stress_worker)
            threads.append(thread)
            thread.start()
        
        # Aguardar conclusão
        for thread in threads:
            thread.join()
        
        # Aguardar debounce final
        time.sleep(0.5)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Análise dos resultados
        throughput = updates_realizados / total_time
        latencia_media = sum(tempos_resposta) / len(tempos_resposta) if tempos_resposta else 0
        latencia_p95 = sorted(tempos_resposta)[int(len(tempos_resposta) * 0.95)] if tempos_resposta else 0
        
        # Verificações
        self.assertGreater(updates_realizados, total_updates * 0.9, "Muitos updates falharam")
        self.assertLess(len(erros_encontrados), total_updates * 0.1, "Muitos erros encontrados")
        self.assertGreater(throughput, 50, f"Throughput muito baixo: {throughput:.1f} ops/s")
        self.assertLess(latencia_media, 100, f"Latência média muito alta: {latencia_media:.1f}ms")
        
        # Verificar se arquivo final é válido
        with open(config_stress.arquivo_sincronizacao, 'r') as f:
            dados_finais = json.load(f)
        
        self.assertIn('dados', dados_finais)
        self.assertTrue(dados_finais['dados'].get('stress_test', False))
        
        print(f"📊 Stress Test Results:")
        print(f"   Updates realizados: {updates_realizados}/{total_updates}")
        print(f"   Throughput: {throughput:.1f} ops/s")
        print(f"   Latência média: {latencia_media:.1f}ms")
        print(f"   Latência P95: {latencia_p95:.1f}ms")
        print(f"   Erros: {len(erros_encontrados)}")
        print(f"   Tempo total: {total_time:.2f}s")
    
    def test_integracao_completa_com_top_sidebar_container_real(self):
        """Testa integração completa com TopSidebarContainer real."""
        # Mock dos serviços necessários
        mock_time_service = Mock()
        mock_workflow_service = Mock()
        mock_notification_service = Mock()
        
        # Configurar mocks com dados realistas
        mock_time_service.get_current_time.return_value = 3600  # 1 hora
        mock_time_service.is_running.return_value = True
        mock_time_service.is_paused.return_value = False
        mock_time_service.get_current_project.return_value = "Projeto Teste"
        
        mock_workflow_service.get_current_workflow.return_value = "Desenvolvimento"
        mock_workflow_service.get_progress.return_value = 65.5
        mock_workflow_service.get_current_stage.return_value = "Implementação"
        mock_workflow_service.get_total_stages.return_value = 5
        
        mock_notification_service.get_unread_count.return_value = 3
        mock_notification_service.get_total_count.return_value = 15
        mock_notification_service.get_notifications.return_value = [
            {"id": 1, "titulo": "Notificação 1", "lida": False, "data": datetime.now().isoformat()},
            {"id": 2, "titulo": "Notificação 2", "lida": True, "data": datetime.now().isoformat()},
            {"id": 3, "titulo": "Notificação 3", "lida": False, "data": datetime.now().isoformat()}
        ]
        
        # Patches necessários para TopSidebarContainer
        with patch('views.components.top_sidebar_container.WebServerManager') as mock_server_manager:
            with patch('views.components.top_sidebar_container.WebViewComponent') as mock_webview_comp:
                with patch('views.components.top_sidebar_container.DataSyncManager') as mock_sync_manager:
                    
                    # Configurar mocks
                    mock_server_instance = Mock()
                    mock_server_manager.return_value = mock_server_instance
                    mock_server_instance.iniciar_servidor.return_value = "http://localhost:8200"
                    mock_server_instance.esta_ativo.return_value = True
                    mock_server_instance.obter_url.return_value = "http://localhost:8200"
                    
                    mock_webview_instance = Mock()
                    mock_webview_comp.return_value = mock_webview_instance
                    
                    mock_sync_instance = Mock()
                    mock_sync_manager.return_value = mock_sync_instance
                    
                    # Criar TopSidebarContainer
                    container = TopSidebarContainer(
                        page=self.mock_page,
                        time_tracking_service=mock_time_service,
                        workflow_service=mock_workflow_service,
                        notification_service=mock_notification_service,
                        habilitar_webview=True,
                        config_servidor=self.config
                    )
                    
                    # Verificar inicialização
                    mock_server_manager.assert_called_once()
                    mock_server_instance.iniciar_servidor.assert_called_once()
                    mock_webview_comp.assert_called_once()
                    mock_sync_manager.assert_called_once()
                    
                    # Testar extração de dados
                    dados_extraidos = container._extrair_dados_para_sincronizacao()
                    
                    # Verificar estrutura dos dados
                    self.assertIsInstance(dados_extraidos, dict)
                    self.assertIn('fonte', dados_extraidos)
                    self.assertEqual(dados_extraidos['fonte'], 'TopSidebarContainer')
                    self.assertIn('timestamp', dados_extraidos)
                    
                    # Verificar dados específicos
                    if 'time_tracker' in dados_extraidos:
                        time_data = dados_extraidos['time_tracker']
                        self.assertIn('tempo_decorrido', time_data)
                        self.assertIn('esta_executando', time_data)
                        self.assertIn('projeto_atual', time_data)
                    
                    if 'notificacoes' in dados_extraidos:
                        notif_data = dados_extraidos['notificacoes']
                        self.assertIn('total', notif_data)
                        self.assertIn('nao_lidas', notif_data)
                    
                    # Simular atualização de dados
                    container._atualizar_dados_webview()
                    
                    # Verificar se sincronização foi chamada
                    mock_sync_instance.atualizar_dados.assert_called()
                    
                    # Testar responsividade
                    container._atualizar_layout_responsivo(800)  # Tablet
                    container._atualizar_layout_responsivo(1200)  # Desktop
                    container._atualizar_layout_responsivo(400)  # Mobile
                    
                    # Verificar se WebView se adapta
                    self.assertTrue(mock_webview_instance.visible)
                    
                    print("✅ Integração completa com TopSidebarContainer testada")
    
    def test_recuperacao_automatica_apos_falhas_multiplas(self):
        """Testa recuperação automática após múltiplas falhas consecutivas."""
        # Inicializar sistema
        self.server_manager = WebServerManager(self.config)
        url_servidor = self.server_manager.iniciar_servidor()
        
        json_provider = JSONDataProvider(arquivo_json=self.config.arquivo_sincronizacao)
        self.sync_manager = DataSyncManager(json_provider)
        
        # Dados de teste
        dados_teste = {"teste_recuperacao": True, "contador": 0}
        
        # 1. Funcionamento normal
        self.sync_manager.atualizar_dados(dados_teste)
        time.sleep(0.2)
        
        # Verificar funcionamento normal
        with open(self.config.arquivo_sincronizacao, 'r') as f:
            dados = json.load(f)
        self.assertTrue(dados['dados']['teste_recuperacao'])
        
        # 2. Simular múltiplas falhas
        falhas_simuladas = 0
        max_falhas = 3
        
        for i in range(max_falhas):
            # Corromper arquivo
            with open(self.config.arquivo_sincronizacao, 'w') as f:
                f.write("{ invalid json }")
            
            # Tentar atualizar (deve falhar)
            try:
                dados_teste["contador"] = i + 1
                self.sync_manager.atualizar_dados(dados_teste)
                time.sleep(0.2)
            except SincronizacaoError:
                falhas_simuladas += 1
            
            # Simular recuperação gradual
            if i < max_falhas - 1:
                # Restaurar arquivo parcialmente corrompido
                with open(self.config.arquivo_sincronizacao, 'w') as f:
                    f.write('{"dados": {}}')
                time.sleep(0.1)
        
        # 3. Recuperação final
        with open(self.config.arquivo_sincronizacao, 'w') as f:
            json.dump({"dados": {}}, f)
        
        # Tentar operação final (deve funcionar)
        dados_recuperacao = {"teste_recuperacao": True, "recuperado": True, "contador": 999}
        self.sync_manager.atualizar_dados(dados_recuperacao)
        time.sleep(0.2)
        
        # Verificar recuperação
        with open(self.config.arquivo_sincronizacao, 'r') as f:
            dados_finais = json.load(f)
        
        self.assertTrue(dados_finais['dados']['recuperado'])
        self.assertEqual(dados_finais['dados']['contador'], 999)
        
        print(f"✅ Recuperação após {falhas_simuladas} falhas testada")
    
    def test_performance_com_dados_muito_grandes(self):
        """Testa performance com datasets muito grandes."""
        # Inicializar sistema
        self.server_manager = WebServerManager(self.config)
        url_servidor = self.server_manager.iniciar_servidor()
        
        json_provider = JSONDataProvider(arquivo_json=self.config.arquivo_sincronizacao)
        self.sync_manager = DataSyncManager(json_provider)
        
        # Criar dataset muito grande (aproximadamente 1MB)
        dados_grandes = {
            "dataset_grande": True,
            "arrays": {
                f"array_{i}": list(range(1000)) for i in range(10)
            },
            "strings": {
                f"string_{i}": "x" * 10000 for i in range(10)  # 10KB cada
            },
            "objetos_aninhados": {
                f"nivel1_{i}": {
                    f"nivel2_{j}": {
                        f"nivel3_{k}": f"valor_{i}_{j}_{k}"
                        for k in range(10)
                    } for j in range(10)
                } for i in range(5)
            },
            "metadata": {
                "tamanho_estimado": "~1MB",
                "timestamp": datetime.now().isoformat(),
                "versao": "1.0.0"
            }
        }
        
        # Medir performance da sincronização
        start_time = time.perf_counter()
        
        self.sync_manager.atualizar_dados(dados_grandes)
        
        # Aguardar sincronização completa
        time.sleep(0.5)
        
        end_time = time.perf_counter()
        tempo_sincronizacao = end_time - start_time
        
        # Verificar se dados foram salvos corretamente
        with open(self.config.arquivo_sincronizacao, 'r') as f:
            dados_salvos = json.load(f)
        
        self.assertTrue(dados_salvos['dados']['dataset_grande'])
        self.assertEqual(len(dados_salvos['dados']['arrays']), 10)
        self.assertEqual(len(dados_salvos['dados']['strings']), 10)
        
        # Medir tamanho do arquivo
        tamanho_arquivo = Path(self.config.arquivo_sincronizacao).stat().st_size
        tamanho_mb = tamanho_arquivo / 1024 / 1024
        
        # Verificar performance
        self.assertLess(tempo_sincronizacao, 2.0, f"Sincronização muito lenta: {tempo_sincronizacao:.2f}s")
        self.assertGreater(tamanho_mb, 0.5, f"Arquivo muito pequeno: {tamanho_mb:.2f}MB")
        self.assertLess(tamanho_mb, 5.0, f"Arquivo muito grande: {tamanho_mb:.2f}MB")
        
        # Testar múltiplas atualizações com dados grandes
        for i in range(5):
            dados_grandes["metadata"]["iteracao"] = i
            dados_grandes["timestamp_update"] = datetime.now().isoformat()
            
            start_update = time.perf_counter()
            self.sync_manager.atualizar_dados(dados_grandes)
            time.sleep(0.1)
            end_update = time.perf_counter()
            
            tempo_update = end_update - start_update
            self.assertLess(tempo_update, 1.0, f"Update {i} muito lento: {tempo_update:.2f}s")
        
        print(f"📊 Performance dados grandes:")
        print(f"   Tempo sincronização inicial: {tempo_sincronizacao:.2f}s")
        print(f"   Tamanho arquivo: {tamanho_mb:.2f}MB")
        print(f"   5 updates adicionais concluídos")
    
    def test_concorrencia_extrema_com_locks(self):
        """Testa concorrência extrema com múltiplas threads e processos."""
        # Configuração para concorrência extrema
        config_concurrent = ConfiguracaoServidorWeb(
            porta_preferencial=8206,
            diretorio_html=self.temp_dir,
            arquivo_sincronizacao=str(Path(self.temp_dir) / "data" / "sync_concurrent.json"),
            intervalo_debounce=0.02,
            max_tentativas_retry=10,
            pool_threads=8
        )
        
        # Inicializar sistema
        self.server_manager = WebServerManager(config_concurrent)
        url_servidor = self.server_manager.iniciar_servidor()
        
        json_provider = JSONDataProvider(arquivo_json=config_concurrent.arquivo_sincronizacao)
        self.sync_manager = DataSyncManager(json_provider)
        
        # Métricas de concorrência
        total_operations = 200
        operations_completed = 0
        operations_failed = 0
        lock = threading.Lock()
        results_queue = Queue()
        
        def concurrent_worker(worker_id, operations_per_worker):
            nonlocal operations_completed, operations_failed
            
            for i in range(operations_per_worker):
                try:
                    # Dados únicos por worker e operação
                    dados = {
                        "worker_id": worker_id,
                        "operation_id": i,
                        "timestamp": datetime.now().isoformat(),
                        "thread_name": threading.current_thread().name,
                        "data_payload": {
                            "values": list(range(i * 10, (i + 1) * 10)),
                            "metadata": {
                                "worker": worker_id,
                                "iteration": i,
                                "random_data": f"data_{worker_id}_{i}"
                            }
                        }
                    }
                    
                    # Sincronizar com pequena variação de timing
                    self.sync_manager.atualizar_dados(dados)
                    
                    with lock:
                        operations_completed += 1
                    
                    results_queue.put({
                        "worker_id": worker_id,
                        "operation_id": i,
                        "success": True,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Variação no timing para simular condições reais
                    time.sleep(0.001 + (i % 3) * 0.001)
                    
                except Exception as e:
                    with lock:
                        operations_failed += 1
                    
                    results_queue.put({
                        "worker_id": worker_id,
                        "operation_id": i,
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
        
        # Executar teste de concorrência
        num_workers = 10
        operations_per_worker = total_operations // num_workers
        
        start_time = time.perf_counter()
        
        # Usar ThreadPoolExecutor para controle melhor
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            
            for worker_id in range(num_workers):
                future = executor.submit(concurrent_worker, worker_id, operations_per_worker)
                futures.append(future)
            
            # Aguardar conclusão de todas as threads
            concurrent.futures.wait(futures)
        
        # Aguardar debounce final
        time.sleep(0.5)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Coletar resultados
        results = []
        while not results_queue.empty():
            try:
                result = results_queue.get_nowait()
                results.append(result)
            except Empty:
                break
        
        # Análise dos resultados
        successful_operations = len([r for r in results if r['success']])
        failed_operations = len([r for r in results if not r['success']])
        
        throughput = successful_operations / total_time
        success_rate = successful_operations / len(results) if results else 0
        
        # Verificações
        self.assertGreater(success_rate, 0.9, f"Taxa de sucesso muito baixa: {success_rate:.2%}")
        self.assertGreater(throughput, 20, f"Throughput muito baixo: {throughput:.1f} ops/s")
        self.assertLess(total_time, 15.0, f"Tempo total muito alto: {total_time:.2f}s")
        
        # Verificar integridade do arquivo final
        with open(config_concurrent.arquivo_sincronizacao, 'r') as f:
            dados_finais = json.load(f)
        
        self.assertIn('dados', dados_finais)
        self.assertIn('worker_id', dados_finais['dados'])
        
        print(f"🔄 Teste Concorrência Extrema:")
        print(f"   Operações realizadas: {successful_operations}/{len(results)}")
        print(f"   Taxa de sucesso: {success_rate:.2%}")
        print(f"   Throughput: {throughput:.1f} ops/s")
        print(f"   Tempo total: {total_time:.2f}s")
        print(f"   Workers: {num_workers}")


if __name__ == '__main__':
    print("🚀 Executando Testes Avançados de Fluxo Completo")
    print("=" * 55)
    
    # Configurar logging mínimo
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Executar testes
    unittest.main(verbosity=2)