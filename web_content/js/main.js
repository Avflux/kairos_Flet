/**
 * Script principal da aplicação WebView
 * Gerencia a interface e integração com o sistema de sincronização
 */

// Namespace principal da aplicação
window.App = {
    
    // Estado da aplicação
    state: {
        initialized: false,
        currentData: null,
        lastUpdate: null,
        elements: {}
    },
    
    // Logger
    logger: Utils.createLogger('App'),
    
    /**
     * Inicializa a aplicação
     */
    init: function() {
        if (this.state.initialized) {
            this.logger.warn('Aplicação já foi inicializada');
            return;
        }
        
        this.logger.info('Inicializando aplicação...');
        
        // Cachear elementos DOM
        this._cacheElements();
        
        // Configurar listeners
        this._setupEventListeners();
        
        // Registrar callback de sincronização
        DataSync.onDataChange('main-app', this._onDataUpdate.bind(this));
        
        // Configurar atualizações de tempo
        this._setupTimeUpdates();
        
        // Configurar responsividade
        this._setupResponsiveHandlers();
        
        // Inicializar com dados padrão
        this._initializeWithDefaults();
        
        this.state.initialized = true;
        this.logger.info('Aplicação inicializada com sucesso');
    },
    
    /**
     * Cacheia elementos DOM importantes
     * @private
     */
    _cacheElements: function() {
        const elements = {
            // Header
            syncIndicator: document.getElementById('sync-indicator'),
            syncText: document.getElementById('sync-text'),
            
            // Containers
            mainContent: document.getElementById('main-content'),
            appContainer: document.getElementById('app-container'),
            flowchartContainer: document.getElementById('flowchart-container')
        };
        
        // Verificar se todos os elementos foram encontrados
        Object.keys(elements).forEach(key => {
            if (!elements[key]) {
                this.logger.warn(`Elemento não encontrado: ${key}`);
            }
        });
        
        this.state.elements = elements;
    },
    
    /**
     * Configura event listeners
     * @private
     */
    _setupEventListeners: function() {
        // Listener para mudanças de tamanho da janela
        window.addEventListener('resize', Utils.debounce(() => {
            this._updateBreakpointStatus();
        }, 250));
        
        // Listener para cliques (futuras interações)
        document.addEventListener('click', this._handleClick.bind(this));
        
        // Listener para teclas (futuras funcionalidades)
        document.addEventListener('keydown', this._handleKeydown.bind(this));
        
        // Listener para foco/blur da janela
        window.addEventListener('focus', () => {
            this.logger.debug('Janela ganhou foco');
            DataSync.forceSync();
        });
        
        window.addEventListener('blur', () => {
            this.logger.debug('Janela perdeu foco');
        });
    },
    
    /**
     * Callback para atualizações de dados
     * @param {Object} data - Novos dados
     * @private
     */
    _onDataUpdate: function(data) {
        this.logger.debug('Recebidos novos dados:', data);
        
        this.state.currentData = data;
        this.state.lastUpdate = new Date();
        
        // Atualizar apenas o fluxograma e status de sincronização
        this._updateWorkflowStatus(data);
        this._updateSyncStatus(data);
        
        // Adicionar animação de atualização
        this._animateUpdate();
    },
    
    /**
     * Atualiza status do workflow (apenas informações de progresso)
     * @param {Object} data - Dados do sistema
     * @private
     */
    _updateWorkflowStatus: function(data) {
        // Atualizar título da seção com informações do workflow
        const flowchartSection = document.querySelector('#flowchart-section h2');
        if (flowchartSection && data.flowchart) {
            const progress = data.flowchart.progresso_workflow || 0;
            const stage = data.flowchart.estagio_atual || 'Aguardando';
            flowchartSection.textContent = `Fluxo de Documentos - ${stage} (${progress.toFixed(0)}%)`;
        }
        
        // Log do progresso para debug
        if (data.flowchart) {
            this.logger.debug(`Workflow: ${data.flowchart.estagio_atual} - ${data.flowchart.progresso_workflow}%`);
        }
    },
    
    /**
     * Atualiza status de sincronização
     * @param {Object} data - Dados do sistema
     * @private
     */
    _updateSyncStatus: function(data) {
        const { syncIndicator, syncText } = this.state.elements;
        
        if (syncIndicator && syncText) {
            // Atualizar indicador de sincronização
            syncIndicator.className = 'sync-indicator online';
            syncText.textContent = 'Fluxo Sincronizado';
            
            // Adicionar animação de sincronização
            Utils.addClassWithAnimation(syncIndicator, 'pulse', 1000);
        }
    },
    
    /**
     * Configura atualizações automáticas
     * @private
     */
    _setupTimeUpdates: function() {
        // Atualizar status de sincronização periodicamente
        setInterval(() => {
            if (this.state.currentData) {
                this._updateSyncStatus(this.state.currentData);
            }
        }, 30000); // A cada 30 segundos
    },
    
    /**
     * Configura handlers responsivos
     * @private
     */
    _setupResponsiveHandlers: function() {
        // Listener para mudanças de orientação (para futuras funcionalidades)
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.logger.debug('Orientação alterada');
            }, 100);
        });
    },
    
    /**
     * Inicializa com dados padrão
     * @private
     */
    _initializeWithDefaults: function() {
        const defaultData = {
            flowchart: {
                progresso_workflow: 0,
                estagio_atual: 'Aguardando início',
                total_estagios: 0
            }
        };
        
        this._onDataUpdate(defaultData);
    },
    
    /**
     * Adiciona animação de atualização
     * @private
     */
    _animateUpdate: function() {
        const { mainContent } = this.state.elements;
        
        if (mainContent) {
            Utils.addClassWithAnimation(mainContent, 'fade-in', 300);
        }
    },
    
    /**
     * Handler para cliques
     * @param {Event} event - Evento de clique
     * @private
     */
    _handleClick: function(event) {
        // Futuras interações podem ser adicionadas aqui
        this.logger.debug('Clique detectado:', event.target);
    },
    
    /**
     * Handler para teclas
     * @param {Event} event - Evento de teclado
     * @private
     */
    _handleKeydown: function(event) {
        // Atalhos de teclado futuros
        if (event.ctrlKey || event.metaKey) {
            switch (event.key) {
                case 'r':
                    // Ctrl+R: Forçar sincronização
                    event.preventDefault();
                    DataSync.forceSync();
                    this.logger.info('Sincronização forçada via teclado');
                    break;
            }
        }
    },
    
    /**
     * Obtém dados atuais da aplicação
     * @returns {Object} Dados atuais
     */
    getCurrentData: function() {
        return this.state.currentData;
    },
    
    /**
     * Obtém estatísticas da aplicação
     * @returns {Object} Estatísticas
     */
    getStats: function() {
        return {
            initialized: this.state.initialized,
            lastUpdate: this.state.lastUpdate,
            syncStats: DataSync.getStats(),
            breakpoint: Utils.getCurrentBreakpoint(),
            elementsFound: Object.keys(this.state.elements).length
        };
    }
};

// Inicialização automática
document.addEventListener('DOMContentLoaded', function() {
    App.init();
});

// Exportar para uso global
window.App = App;

// Debug helpers (apenas em modo debug)
if (window.DEBUG_MODE) {
    window.debugApp = function() {
        console.log('=== DEBUG INFO ===');
        console.log('App Stats:', App.getStats());
        console.log('Current Data:', App.getCurrentData());
        console.log('Utils:', Utils);
        console.log('DataSync:', DataSync);
    };
    
    console.log('Modo debug ativo. Use debugApp() para informações de debug.');
}