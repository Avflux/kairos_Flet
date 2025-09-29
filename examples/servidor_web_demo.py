#!/usr/bin/env python3
"""
Demonstração completa do Sistema de Servidor Web Integrado.

Este exemplo mostra como usar todos os componentes do sistema:
- WebServerManager para servidor HTTP local
- DataSyncManager para sincronização de dados
- WebViewComponent para exibição integrada
- TopSidebarContainer com WebView habilitado

Execute este script para ver o sistema funcionando na prática.
"""

import flet as ft
import json
import time
import threading
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

# Importar componentes do sistema
from services.web_server.server_manager import WebServerManager
from services.web_server.sync_manager import DataSyncManager
from services.web_server.data_provider import JSONDataProvider
from services.web_server.models import ConfiguracaoServidorWeb, DadosTopSidebar
from services.web_server.config import (
    criar_configuracao_desenvolvimento,
    diagnosticar_configuracao,
    gerar_relatorio_configuracao
)
from views.components.webview_component import WebViewComponent
from views.components.top_sidebar_container import TopSidebarContainer


class ServidorWebDemo:
    """Classe principal da demonstração."""
    
    def __init__(self):
        """Inicializa a demonstração."""
        self.temp_dir = None
        self.server_manager = None
        self.sync_manager = None
        self.webview_component = None
        self.container = None
        self.dados_simulados = {
            "contador": 0,
            "time_tracker": {
                "tempo_decorrido": 0,
                "esta_executando": False,
                "esta_pausado": False,
                "projeto_atual": "Demonstração WebView"
            },
            "flowchart": {
                "progresso": 0.0,
                "estagio_atual": "Inicialização",
                "total_estagios": 5
            },
            "notificacoes": {
                "total": 0,
                "nao_lidas": 0,
                "lista": []
            }
        }
        self.simulacao_ativa = False
        self.thread_simulacao = None
    
    def criar_estrutura_web(self):
        """Cria estrutura de arquivos web para demonstração."""
        print("📁 Criando estrutura de arquivos web...")
        
        # Criar diretórios
        css_dir = Path(self.temp_dir) / "css"
        js_dir = Path(self.temp_dir) / "js"
        data_dir = Path(self.temp_dir) / "data"
        
        css_dir.mkdir(exist_ok=True)
        js_dir.mkdir(exist_ok=True)
        data_dir.mkdir(exist_ok=True)
        
        # Página principal HTML
        html_content = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Demonstração Servidor Web Integrado</title>
    <link rel="stylesheet" href="css/styles.css">
</head>
<body>
    <div id="app">
        <header>
            <h1>🚀 Demonstração WebView Integrado</h1>
            <div id="status-conexao" class="conectado">Conectado</div>
            <div id="timestamp">Carregando...</div>
        </header>
        
        <main>
            <div class="grid-container">
                <section class="card" id="time-tracker">
                    <h2>⏱️ Rastreamento de Tempo</h2>
                    <div class="metric-large" id="tempo-decorrido">00:00:00</div>
                    <div class="info-row">
                        <span class="label">Projeto:</span>
                        <span id="projeto-atual">Nenhum projeto</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Status:</span>
                        <span id="status-execucao" class="status-parado">Parado</span>
                    </div>
                </section>
                
                <section class="card" id="flowchart">
                    <h2>📊 Progresso do Workflow</h2>
                    <div class="progress-container">
                        <div class="progress-bar">
                            <div id="progresso-atual" class="progress-fill" style="width: 0%"></div>
                        </div>
                        <div class="progress-text" id="progresso-percentual">0%</div>
                    </div>
                    <div class="info-row">
                        <span class="label">Estágio:</span>
                        <span id="estagio-atual">Nenhum workflow ativo</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Total:</span>
                        <span id="total-estagios">0 estágios</span>
                    </div>
                </section>
                
                <section class="card" id="notificacoes">
                    <h2>🔔 Notificações</h2>
                    <div class="metric-container">
                        <div class="metric-item">
                            <div class="metric-value" id="total-notificacoes">0</div>
                            <div class="metric-label">Total</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-value" id="nao-lidas" class="highlight">0</div>
                            <div class="metric-label">Não Lidas</div>
                        </div>
                    </div>
                    <div id="lista-notificacoes" class="notifications-list">
                        <div class="no-notifications">Nenhuma notificação</div>
                    </div>
                </section>
                
                <section class="card" id="estatisticas">
                    <h2>📈 Estatísticas da Demo</h2>
                    <div class="info-row">
                        <span class="label">Atualizações:</span>
                        <span id="contador-atualizacoes">0</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Latência Média:</span>
                        <span id="latencia-media">0ms</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Última Sync:</span>
                        <span id="ultima-sincronizacao">Nunca</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Status Sistema:</span>
                        <span id="status-sistema" class="status-ok">OK</span>
                    </div>
                </section>
            </div>
        </main>
        
        <footer>
            <p>Demonstração do Sistema de Servidor Web Integrado</p>
            <p>Dados atualizados automaticamente via sincronização JSON</p>
        </footer>
    </div>
    
    <script src="js/sync.js"></script>
    <script src="js/main.js"></script>
</body>
</html>"""
        
        (Path(self.temp_dir) / "index.html").write_text(html_content, encoding='utf-8')
        
        # CSS Styles
        css_content = """/* Estilos para demonstração do WebView */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #333;
    min-height: 100vh;
}

#app {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

header {
    background: rgba(255, 255, 255, 0.95);
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
}

header h1 {
    color: #4a5568;
    font-size: 1.8rem;
    font-weight: 600;
}

#status-conexao {
    padding: 8px 16px;
    border-radius: 20px;
    font-weight: 500;
    font-size: 0.9rem;
    transition: all 0.3s ease;
}

#status-conexao.conectado {
    background: #48bb78;
    color: white;
}

#status-conexao.erro-conexao {
    background: #f56565;
    color: white;
    animation: pulse 2s infinite;
}

#timestamp {
    color: #718096;
    font-size: 0.9rem;
}

.grid-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    margin-bottom: 20px;
}

.card {
    background: rgba(255, 255, 255, 0.95);
    padding: 24px;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}

.card h2 {
    color: #4a5568;
    margin-bottom: 16px;
    font-size: 1.3rem;
    font-weight: 600;
}

.metric-large {
    font-size: 2.5rem;
    font-weight: 700;
    color: #2d3748;
    margin-bottom: 16px;
    font-family: 'Courier New', monospace;
}

.metric-container {
    display: flex;
    gap: 20px;
    margin-bottom: 16px;
}

.metric-item {
    text-align: center;
    flex: 1;
}

.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: #2d3748;
    margin-bottom: 4px;
}

.metric-value.highlight {
    color: #e53e3e;
}

.metric-label {
    font-size: 0.9rem;
    color: #718096;
    font-weight: 500;
}

.info-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    padding: 8px 0;
    border-bottom: 1px solid #e2e8f0;
}

.info-row:last-child {
    border-bottom: none;
    margin-bottom: 0;
}

.label {
    font-weight: 600;
    color: #4a5568;
}

.status-executando {
    color: #38a169;
    font-weight: 600;
}

.status-pausado {
    color: #ed8936;
    font-weight: 600;
}

.status-parado {
    color: #718096;
    font-weight: 600;
}

.status-ok {
    color: #38a169;
    font-weight: 600;
}

.progress-container {
    margin-bottom: 16px;
}

.progress-bar {
    width: 100%;
    height: 12px;
    background: #e2e8f0;
    border-radius: 6px;
    overflow: hidden;
    margin-bottom: 8px;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #48bb78, #38a169);
    transition: width 0.5s ease;
    border-radius: 6px;
}

.progress-text {
    text-align: center;
    font-weight: 600;
    color: #4a5568;
}

.notifications-list {
    max-height: 200px;
    overflow-y: auto;
}

.notificacao {
    padding: 12px;
    margin-bottom: 8px;
    border-radius: 8px;
    border-left: 4px solid #4299e1;
    background: #ebf8ff;
    transition: all 0.2s ease;
}

.notificacao.nao-lida {
    border-left-color: #e53e3e;
    background: #fed7d7;
}

.notificacao.lida {
    border-left-color: #38a169;
    background: #f0fff4;
    opacity: 0.8;
}

.notificacao .titulo {
    font-weight: 600;
    color: #2d3748;
    margin-bottom: 4px;
}

.notificacao .data {
    font-size: 0.8rem;
    color: #718096;
}

.no-notifications {
    text-align: center;
    color: #a0aec0;
    font-style: italic;
    padding: 20px;
}

footer {
    background: rgba(255, 255, 255, 0.95);
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    color: #718096;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

footer p {
    margin-bottom: 4px;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

/* Responsividade */
@media (max-width: 768px) {
    #app {
        padding: 10px;
    }
    
    header {
        flex-direction: column;
        gap: 10px;
        text-align: center;
    }
    
    header h1 {
        font-size: 1.5rem;
    }
    
    .grid-container {
        grid-template-columns: 1fr;
    }
    
    .metric-large {
        font-size: 2rem;
    }
    
    .metric-container {
        flex-direction: column;
        gap: 10px;
    }
}

/* Animações suaves */
.card, .metric-value, .progress-fill, .status-conexao {
    transition: all 0.3s ease;
}

/* Efeitos de hover */
.card:hover .metric-value {
    transform: scale(1.05);
}

/* Indicadores visuais */
.tem-notificacoes {
    animation: bounce 1s infinite;
}

@keyframes bounce {
    0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
    40% { transform: translateY(-3px); }
    60% { transform: translateY(-2px); }
}
"""
        
        (css_dir / "styles.css").write_text(css_content, encoding='utf-8')
        
        # JavaScript para sincronização
        js_sync_content = """// Sistema de sincronização para demonstração
class DemoSyncManager {
    constructor() {
        this.dados = {};
        this.ultimaAtualizacao = null;
        this.intervaloSync = 1000; // 1 segundo
        this.contadorAtualizacoes = 0;
        this.latencias = [];
        this.iniciarSincronizacao();
        
        console.log('🚀 DemoSyncManager inicializado');
    }
    
    iniciarSincronizacao() {
        setInterval(() => {
            this.buscarDados();
        }, this.intervaloSync);
        
        // Primeira busca imediata
        this.buscarDados();
    }
    
    async buscarDados() {
        const startTime = performance.now();
        
        try {
            const response = await fetch('/data/sync.json?t=' + Date.now());
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const dados = await response.json();
            const endTime = performance.now();
            const latencia = endTime - startTime;
            
            this.latencias.push(latencia);
            if (this.latencias.length > 10) {
                this.latencias.shift(); // Manter apenas as últimas 10
            }
            
            if (dados.timestamp !== this.ultimaAtualizacao) {
                this.dados = dados.dados || {};
                this.ultimaAtualizacao = dados.timestamp;
                this.contadorAtualizacoes++;
                this.atualizarInterface();
                
                console.log('📊 Dados sincronizados:', {
                    timestamp: dados.timestamp,
                    latencia: `${latencia.toFixed(1)}ms`,
                    contador: this.contadorAtualizacoes
                });
            }
            
            this.mostrarConexaoOk();
            
        } catch (error) {
            console.error('❌ Erro na sincronização:', error);
            this.mostrarErroConexao();
        }
    }
    
    atualizarInterface() {
        // Atualizar timestamp
        const timestampElement = document.getElementById('timestamp');
        if (timestampElement) {
            timestampElement.textContent = `Última atualização: ${new Date().toLocaleTimeString('pt-BR')}`;
        }
        
        // Atualizar time tracker
        if (this.dados.time_tracker) {
            this.atualizarTimeTracker(this.dados.time_tracker);
        }
        
        // Atualizar flowchart
        if (this.dados.flowchart) {
            this.atualizarFlowchart(this.dados.flowchart);
        }
        
        // Atualizar notificações
        if (this.dados.notificacoes) {
            this.atualizarNotificacoes(this.dados.notificacoes);
        }
        
        // Atualizar estatísticas
        this.atualizarEstatisticas();
    }
    
    atualizarTimeTracker(dados) {
        const tempoElement = document.getElementById('tempo-decorrido');
        const projetoElement = document.getElementById('projeto-atual');
        const statusElement = document.getElementById('status-execucao');
        
        if (tempoElement) {
            tempoElement.textContent = this.formatarTempo(dados.tempo_decorrido || 0);
        }
        
        if (projetoElement) {
            projetoElement.textContent = dados.projeto_atual || 'Nenhum projeto';
        }
        
        if (statusElement) {
            let status, className;
            
            if (dados.esta_executando) {
                status = 'Executando';
                className = 'status-executando';
            } else if (dados.esta_pausado) {
                status = 'Pausado';
                className = 'status-pausado';
            } else {
                status = 'Parado';
                className = 'status-parado';
            }
            
            statusElement.textContent = status;
            statusElement.className = className;
        }
    }
    
    atualizarFlowchart(dados) {
        const progressoElement = document.getElementById('progresso-atual');
        const percentualElement = document.getElementById('progresso-percentual');
        const estagioElement = document.getElementById('estagio-atual');
        const totalElement = document.getElementById('total-estagios');
        
        const progresso = dados.progresso || 0;
        
        if (progressoElement) {
            progressoElement.style.width = `${progresso}%`;
        }
        
        if (percentualElement) {
            percentualElement.textContent = `${progresso.toFixed(1)}%`;
        }
        
        if (estagioElement) {
            estagioElement.textContent = dados.estagio_atual || 'Nenhum workflow ativo';
        }
        
        if (totalElement) {
            const total = dados.total_estagios || 0;
            totalElement.textContent = `${total} estágio${total !== 1 ? 's' : ''}`;
        }
    }
    
    atualizarNotificacoes(dados) {
        const totalElement = document.getElementById('total-notificacoes');
        const naoLidasElement = document.getElementById('nao-lidas');
        const listaElement = document.getElementById('lista-notificacoes');
        
        const total = dados.total || 0;
        const naoLidas = dados.nao_lidas || 0;
        
        if (totalElement) {
            totalElement.textContent = total;
        }
        
        if (naoLidasElement) {
            naoLidasElement.textContent = naoLidas;
            naoLidasElement.className = naoLidas > 0 ? 'metric-value highlight tem-notificacoes' : 'metric-value';
        }
        
        if (listaElement) {
            const lista = dados.lista || [];
            
            if (lista.length === 0) {
                listaElement.innerHTML = '<div class="no-notifications">Nenhuma notificação</div>';
            } else {
                listaElement.innerHTML = lista
                    .slice(0, 5) // Mostrar apenas as 5 mais recentes
                    .map(notif => `
                        <div class="notificacao ${notif.lida ? 'lida' : 'nao-lida'}">
                            <div class="titulo">${this.escapeHtml(notif.titulo || 'Sem título')}</div>
                            <div class="data">${this.formatarData(notif.data || new Date().toISOString())}</div>
                        </div>
                    `).join('');
            }
        }
    }
    
    atualizarEstatisticas() {
        const contadorElement = document.getElementById('contador-atualizacoes');
        const latenciaElement = document.getElementById('latencia-media');
        const ultimaSyncElement = document.getElementById('ultima-sincronizacao');
        const statusSistemaElement = document.getElementById('status-sistema');
        
        if (contadorElement) {
            contadorElement.textContent = this.contadorAtualizacoes;
        }
        
        if (latenciaElement && this.latencias.length > 0) {
            const latenciaMedia = this.latencias.reduce((a, b) => a + b, 0) / this.latencias.length;
            latenciaElement.textContent = `${latenciaMedia.toFixed(1)}ms`;
        }
        
        if (ultimaSyncElement) {
            ultimaSyncElement.textContent = new Date().toLocaleTimeString('pt-BR');
        }
        
        if (statusSistemaElement) {
            statusSistemaElement.textContent = 'OK';
            statusSistemaElement.className = 'status-ok';
        }
    }
    
    formatarTempo(segundos) {
        const horas = Math.floor(segundos / 3600);
        const minutos = Math.floor((segundos % 3600) / 60);
        const segs = segundos % 60;
        
        return `${horas.toString().padStart(2, '0')}:${minutos.toString().padStart(2, '0')}:${segs.toString().padStart(2, '0')}`;
    }
    
    formatarData(timestamp) {
        try {
            return new Date(timestamp).toLocaleString('pt-BR', {
                day: '2-digit',
                month: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (e) {
            return 'Data inválida';
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    mostrarConexaoOk() {
        const statusElement = document.getElementById('status-conexao');
        if (statusElement) {
            statusElement.textContent = 'Conectado';
            statusElement.className = 'conectado';
        }
    }
    
    mostrarErroConexao() {
        const statusElement = document.getElementById('status-conexao');
        if (statusElement) {
            statusElement.textContent = 'Erro de Conexão';
            statusElement.className = 'erro-conexao';
        }
    }
}

// Inicializar quando a página carregar
document.addEventListener('DOMContentLoaded', () => {
    console.log('🌐 Página carregada, inicializando sincronização...');
    window.demoSyncManager = new DemoSyncManager();
});

// Adicionar alguns logs úteis para debug
window.addEventListener('beforeunload', () => {
    console.log('👋 Página sendo fechada');
});

// Detectar mudanças de visibilidade
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        console.log('👁️ Página oculta');
    } else {
        console.log('👁️ Página visível');
    }
});
"""
        
        (js_dir / "sync.js").write_text(js_sync_content, encoding='utf-8')
        
        # JavaScript principal
        js_main_content = """// JavaScript principal para demonstração
console.log('🎯 Script principal carregado');

// Adicionar interatividade extra
document.addEventListener('DOMContentLoaded', () => {
    // Adicionar efeitos visuais aos cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        // Animação de entrada escalonada
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
    
    // Adicionar tooltip para elementos com informações
    const infoElements = document.querySelectorAll('[data-tooltip]');
    infoElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
    
    // Adicionar funcionalidade de clique nos cards
    cards.forEach(card => {
        card.addEventListener('click', () => {
            card.style.transform = 'scale(0.98)';
            setTimeout(() => {
                card.style.transform = '';
            }, 150);
        });
    });
    
    console.log('✨ Interatividade adicionada aos elementos');
});

function showTooltip(event) {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = event.target.getAttribute('data-tooltip');
    tooltip.style.cssText = `
        position: absolute;
        background: #2d3748;
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 0.8rem;
        z-index: 1000;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.2s ease;
    `;
    
    document.body.appendChild(tooltip);
    
    const rect = event.target.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
    
    setTimeout(() => {
        tooltip.style.opacity = '1';
    }, 10);
    
    event.target._tooltip = tooltip;
}

function hideTooltip(event) {
    if (event.target._tooltip) {
        event.target._tooltip.remove();
        delete event.target._tooltip;
    }
}

// Função para mostrar notificação temporária
function mostrarNotificacao(mensagem, tipo = 'info') {
    const notificacao = document.createElement('div');
    notificacao.className = `notificacao-temp ${tipo}`;
    notificacao.textContent = mensagem;
    notificacao.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${tipo === 'error' ? '#f56565' : tipo === 'success' ? '#48bb78' : '#4299e1'};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        z-index: 1001;
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
        max-width: 300px;
        word-wrap: break-word;
    `;
    
    document.body.appendChild(notificacao);
    
    // Animar entrada
    setTimeout(() => {
        notificacao.style.opacity = '1';
        notificacao.style.transform = 'translateX(0)';
    }, 10);
    
    // Remover após 3 segundos
    setTimeout(() => {
        notificacao.style.opacity = '0';
        notificacao.style.transform = 'translateX(100%)';
        setTimeout(() => {
            notificacao.remove();
        }, 300);
    }, 3000);
}

// Detectar erros JavaScript e mostrar notificação
window.addEventListener('error', (event) => {
    console.error('❌ Erro JavaScript:', event.error);
    mostrarNotificacao('Erro detectado no JavaScript', 'error');
});

// Detectar problemas de rede
window.addEventListener('online', () => {
    console.log('🌐 Conexão restaurada');
    mostrarNotificacao('Conexão com a internet restaurada', 'success');
});

window.addEventListener('offline', () => {
    console.log('📡 Conexão perdida');
    mostrarNotificacao('Conexão com a internet perdida', 'error');
});

// Adicionar atalhos de teclado úteis
document.addEventListener('keydown', (event) => {
    // Ctrl+R ou F5 para recarregar
    if ((event.ctrlKey && event.key === 'r') || event.key === 'F5') {
        console.log('🔄 Recarregando página...');
        mostrarNotificacao('Recarregando página...', 'info');
    }
    
    // Ctrl+Shift+I para mostrar informações de debug
    if (event.ctrlKey && event.shiftKey && event.key === 'I') {
        event.preventDefault();
        console.log('🔍 Informações de debug:', {
            syncManager: window.demoSyncManager,
            dados: window.demoSyncManager?.dados,
            atualizacoes: window.demoSyncManager?.contadorAtualizacoes,
            latencias: window.demoSyncManager?.latencias
        });
        mostrarNotificacao('Informações de debug no console', 'info');
    }
});

console.log('🎉 JavaScript principal inicializado com sucesso');
"""
        
        (js_dir / "main.js").write_text(js_main_content, encoding='utf-8')
        
        # Arquivo de sincronização inicial
        sync_data = {
            "dados": self.dados_simulados,
            "timestamp": datetime.now().isoformat(),
            "versao": 1,
            "fonte": "ServidorWebDemo"
        }
        
        (data_dir / "sync.json").write_text(
            json.dumps(sync_data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        
        print("✅ Estrutura de arquivos web criada com sucesso!")
    
    def configurar_sistema(self):
        """Configura o sistema de servidor web."""
        print("⚙️ Configurando sistema de servidor web...")
        
        # Criar configuração de desenvolvimento
        self.config = criar_configuracao_desenvolvimento()
        self.config.porta_preferencial = 8090  # Porta específica para demo
        self.config.portas_alternativas = [8091, 8092, 8093]
        self.config.diretorio_html = self.temp_dir
        self.config.arquivo_sincronizacao = str(Path(self.temp_dir) / "data" / "sync.json")
        self.config.intervalo_debounce = 0.1  # Resposta rápida para demo
        self.config.modo_debug = True
        
        # Executar diagnóstico
        print("\n🔍 Executando diagnóstico da configuração...")
        diagnostico = diagnosticar_configuracao(self.config)
        
        print(f"   Configuração válida: {'✅' if diagnostico['configuracao_valida'] else '❌'}")
        print(f"   Erros: {len(diagnostico['erros'])}")
        print(f"   Avisos: {len(diagnostico['avisos'])}")
        
        if diagnostico['avisos']:
            for aviso in diagnostico['avisos'][:3]:  # Mostrar apenas os 3 primeiros
                print(f"   ⚠️ {aviso}")
        
        print("✅ Sistema configurado!")
    
    def inicializar_componentes(self):
        """Inicializa todos os componentes do sistema."""
        print("🚀 Inicializando componentes...")
        
        # 1. Inicializar servidor web
        print("   📡 Iniciando servidor web...")
        self.server_manager = WebServerManager(self.config)
        self.url_servidor = self.server_manager.iniciar_servidor()
        print(f"   ✅ Servidor iniciado em: {self.url_servidor}")
        
        # 2. Inicializar sincronização
        print("   🔄 Configurando sincronização...")
        json_provider = JSONDataProvider(arquivo_json=self.config.arquivo_sincronizacao)
        self.sync_manager = DataSyncManager(json_provider)
        print("   ✅ Sincronização configurada!")
        
        # 3. Atualização inicial dos dados
        print("   📊 Enviando dados iniciais...")
        self.sync_manager.atualizar_dados(self.dados_simulados)
        time.sleep(0.2)  # Aguardar sincronização
        print("   ✅ Dados iniciais sincronizados!")
        
        print("🎉 Todos os componentes inicializados com sucesso!")
    
    def iniciar_simulacao_dados(self):
        """Inicia simulação de dados em tempo real."""
        print("🎭 Iniciando simulação de dados em tempo real...")
        
        self.simulacao_ativa = True
        self.thread_simulacao = threading.Thread(target=self._loop_simulacao, daemon=True)
        self.thread_simulacao.start()
        
        print("✅ Simulação iniciada!")
    
    def _loop_simulacao(self):
        """Loop principal da simulação de dados."""
        contador_ciclos = 0
        
        while self.simulacao_ativa:
            try:
                contador_ciclos += 1
                
                # Atualizar time tracker
                if contador_ciclos % 2 == 0:  # A cada 2 ciclos
                    self.dados_simulados["time_tracker"]["tempo_decorrido"] += 1
                    
                    # Alternar status ocasionalmente
                    if contador_ciclos % 20 == 0:
                        self.dados_simulados["time_tracker"]["esta_executando"] = not self.dados_simulados["time_tracker"]["esta_executando"]
                
                # Atualizar progresso do workflow
                if contador_ciclos % 5 == 0:  # A cada 5 ciclos
                    progresso_atual = self.dados_simulados["flowchart"]["progresso"]
                    novo_progresso = min(100, progresso_atual + 1.5)
                    self.dados_simulados["flowchart"]["progresso"] = novo_progresso
                    
                    # Atualizar estágio baseado no progresso
                    if novo_progresso < 20:
                        self.dados_simulados["flowchart"]["estagio_atual"] = "Inicialização"
                    elif novo_progresso < 40:
                        self.dados_simulados["flowchart"]["estagio_atual"] = "Desenvolvimento"
                    elif novo_progresso < 60:
                        self.dados_simulados["flowchart"]["estagio_atual"] = "Testes"
                    elif novo_progresso < 80:
                        self.dados_simulados["flowchart"]["estagio_atual"] = "Revisão"
                    else:
                        self.dados_simulados["flowchart"]["estagio_atual"] = "Finalização"
                
                # Adicionar notificações ocasionalmente
                if contador_ciclos % 15 == 0:  # A cada 15 ciclos
                    nova_notificacao = {
                        "id": len(self.dados_simulados["notificacoes"]["lista"]) + 1,
                        "titulo": f"Notificação de Demo #{contador_ciclos // 15}",
                        "data": datetime.now().isoformat(),
                        "lida": False
                    }
                    
                    self.dados_simulados["notificacoes"]["lista"].insert(0, nova_notificacao)
                    self.dados_simulados["notificacoes"]["total"] += 1
                    self.dados_simulados["notificacoes"]["nao_lidas"] += 1
                    
                    # Manter apenas as 10 notificações mais recentes
                    if len(self.dados_simulados["notificacoes"]["lista"]) > 10:
                        self.dados_simulados["notificacoes"]["lista"] = self.dados_simulados["notificacoes"]["lista"][:10]
                
                # Marcar algumas notificações como lidas ocasionalmente
                if contador_ciclos % 25 == 0 and self.dados_simulados["notificacoes"]["nao_lidas"] > 0:
                    for notif in self.dados_simulados["notificacoes"]["lista"]:
                        if not notif["lida"] and len([n for n in self.dados_simulados["notificacoes"]["lista"] if not n["lida"]]) > 1:
                            notif["lida"] = True
                            self.dados_simulados["notificacoes"]["nao_lidas"] -= 1
                            break
                
                # Atualizar contador geral
                self.dados_simulados["contador"] = contador_ciclos
                
                # Sincronizar dados
                self.sync_manager.atualizar_dados(self.dados_simulados)
                
                # Aguardar próximo ciclo
                time.sleep(1.0)  # 1 segundo entre atualizações
                
            except Exception as e:
                print(f"❌ Erro na simulação: {e}")
                time.sleep(1.0)
    
    def parar_simulacao(self):
        """Para a simulação de dados."""
        print("⏹️ Parando simulação...")
        self.simulacao_ativa = False
        
        if self.thread_simulacao and self.thread_simulacao.is_alive():
            self.thread_simulacao.join(timeout=2.0)
        
        print("✅ Simulação parada!")
    
    def criar_aplicacao_flet(self, page: ft.Page):
        """Cria a aplicação Flet com WebView integrado."""
        print("🎨 Criando aplicação Flet...")
        
        # Configurar página
        page.title = "Demonstração - Servidor Web Integrado"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 20
        page.bgcolor = ft.colors.GREY_100
        
        # Criar WebView component
        self.webview_component = WebViewComponent(
            page=page,
            url_servidor=self.url_servidor,
            modo_debug=True
        )
        
        # Criar controles da demonstração
        controles = ft.Column([
            ft.Text(
                "🚀 Demonstração do Sistema de Servidor Web Integrado",
                size=24,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.BLUE_800
            ),
            ft.Text(
                f"Servidor ativo em: {self.url_servidor}",
                size=14,
                color=ft.colors.GREY_700
            ),
            ft.Divider(),
            
            ft.Row([
                ft.ElevatedButton(
                    "🔄 Recarregar WebView",
                    on_click=lambda _: self.webview_component.recarregar(),
                    bgcolor=ft.colors.BLUE_500,
                    color=ft.colors.WHITE
                ),
                ft.ElevatedButton(
                    "📊 Forçar Sincronização",
                    on_click=lambda _: self._forcar_sincronizacao(),
                    bgcolor=ft.colors.GREEN_500,
                    color=ft.colors.WHITE
                ),
                ft.ElevatedButton(
                    "🎭 Toggle Simulação",
                    on_click=lambda _: self._toggle_simulacao(),
                    bgcolor=ft.colors.ORANGE_500,
                    color=ft.colors.WHITE
                ),
            ], wrap=True),
            
            ft.Divider(),
            
            # Container para o WebView
            ft.Container(
                content=self.webview_component,
                width=1000,
                height=600,
                border=ft.border.all(2, ft.colors.GREY_400),
                border_radius=12,
                bgcolor=ft.colors.WHITE,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=10,
                    color=ft.colors.with_opacity(0.3, ft.colors.GREY_400),
                    offset=ft.Offset(0, 4)
                )
            )
        ], spacing=10)
        
        page.add(controles)
        page.update()
        
        print("✅ Aplicação Flet criada!")
    
    def _forcar_sincronizacao(self):
        """Força uma sincronização imediata."""
        print("🔄 Forçando sincronização...")
        self.dados_simulados["timestamp_forcado"] = datetime.now().isoformat()
        self.sync_manager.atualizar_dados(self.dados_simulados)
        print("✅ Sincronização forçada!")
    
    def _toggle_simulacao(self):
        """Alterna o estado da simulação."""
        if self.simulacao_ativa:
            self.parar_simulacao()
        else:
            self.iniciar_simulacao_dados()
    
    def executar_demo(self):
        """Executa a demonstração completa."""
        print("🎬 INICIANDO DEMONSTRAÇÃO DO SERVIDOR WEB INTEGRADO")
        print("=" * 60)
        
        try:
            # 1. Criar diretório temporário
            self.temp_dir = tempfile.mkdtemp(prefix="servidor_web_demo_")
            print(f"📁 Diretório temporário: {self.temp_dir}")
            
            # 2. Criar estrutura web
            self.criar_estrutura_web()
            
            # 3. Configurar sistema
            self.configurar_sistema()
            
            # 4. Inicializar componentes
            self.inicializar_componentes()
            
            # 5. Iniciar simulação
            self.iniciar_simulacao_dados()
            
            # 6. Criar aplicação Flet
            print("\n🎨 Iniciando aplicação Flet...")
            print("   (Uma janela do navegador será aberta)")
            print("   Pressione Ctrl+C para parar a demonstração")
            
            ft.app(
                target=self.criar_aplicacao_flet,
                view=ft.WEB_BROWSER,
                port=8000,
                web_renderer=ft.WebRenderer.HTML
            )
            
        except KeyboardInterrupt:
            print("\n⏹️ Demonstração interrompida pelo usuário")
        except Exception as e:
            print(f"\n❌ Erro durante demonstração: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Limpa recursos utilizados."""
        print("\n🧹 Limpando recursos...")
        
        # Parar simulação
        if self.simulacao_ativa:
            self.parar_simulacao()
        
        # Parar servidor
        if self.server_manager:
            self.server_manager.parar_servidor()
            print("   ✅ Servidor web parado")
        
        # Finalizar sincronização
        if self.sync_manager:
            self.sync_manager.finalizar()
            print("   ✅ Sincronização finalizada")
        
        # Remover diretório temporário
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
            print(f"   ✅ Diretório temporário removido: {self.temp_dir}")
        
        print("🎉 Limpeza concluída!")


def main():
    """Função principal."""
    print("🚀 DEMONSTRAÇÃO COMPLETA DO SISTEMA DE SERVIDOR WEB INTEGRADO")
    print("=" * 70)
    print()
    print("Esta demonstração mostra:")
    print("  • Servidor web local com arquivos HTML/CSS/JS")
    print("  • Sincronização de dados em tempo real via JSON")
    print("  • WebView integrado ao Flet")
    print("  • Interface responsiva e interativa")
    print("  • Simulação de dados dinâmicos")
    print()
    print("Instruções:")
    print("  • Uma janela do navegador será aberta automaticamente")
    print("  • Os dados serão atualizados automaticamente a cada segundo")
    print("  • Use os botões para controlar a demonstração")
    print("  • Pressione Ctrl+C para parar")
    print()
    input("Pressione Enter para continuar...")
    print()
    
    # Executar demonstração
    demo = ServidorWebDemo()
    demo.executar_demo()


if __name__ == '__main__':
    main()