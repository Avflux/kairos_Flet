/**
 * Sistema de sincronização de dados em tempo real
 * Gerencia a comunicação entre o WebView e a aplicação Flet
 */

// Namespace para sincronização
window.DataSync = {
    
    // Configurações
    config: {
        syncInterval: 1000,        // Intervalo de polling em ms
        retryInterval: 5000,       // Intervalo para retry em caso de erro
        maxRetries: 3,             // Máximo de tentativas
        debounceDelay: 300,        // Delay para debounce de atualizações
        syncEndpoint: 'data/sync.json', // Endpoint para dados
        enableWebSocket: false,    // WebSocket (futuro)
        enablePolling: true        // Polling HTTP
    },
    
    // Estado interno
    state: {
        isConnected: false,
        isPolling: false,
        lastSync: null,
        retryCount: 0,
        currentData: null,
        dataVersion: 0,
        callbacks: new Map(),
        pollInterval: null,
        wsConnection: null
    },
    
    // Logger específico
    logger: Utils.createLogger('DataSync'),
    
    /**
     * Inicializa o sistema de sincronização
     * @param {Object} options - Opções de configuração
     */
    init: function(options = {}) {
        // Merge configurações
        Object.assign(this.config, options);
        
        this.logger.info('Inicializando sistema de sincronização...');
        
        // Configurar debounced update
        this.debouncedUpdate = Utils.debounce(
            this._updateUI.bind(this), 
            this.config.debounceDelay
        );
        
        // Iniciar sincronização
        this.start();
        
        // Configurar listeners de visibilidade
        this._setupVisibilityHandlers();
        
        // Configurar listeners de rede
        this._setupNetworkHandlers();
        
        this.logger.info('Sistema de sincronização inicializado');
    },
    
    /**
     * Inicia a sincronização
     */
    start: function() {
        if (this.state.isPolling) {
            this.logger.warn('Sincronização já está ativa');
            return;
        }
        
        this.logger.info('Iniciando sincronização...');
        
        // Tentar WebSocket primeiro (se habilitado)
        if (this.config.enableWebSocket) {
            this._initWebSocket();
        }
        
        // Iniciar polling como fallback ou método principal
        if (this.config.enablePolling) {
            this._startPolling();
        }
        
        // Primeira sincronização imediata
        this._syncData();
    },
    
    /**
     * Para a sincronização
     */
    stop: function() {
        this.logger.info('Parando sincronização...');
        
        this.state.isPolling = false;
        
        if (this.state.pollInterval) {
            clearInterval(this.state.pollInterval);
            this.state.pollInterval = null;
        }
        
        if (this.state.wsConnection) {
            this.state.wsConnection.close();
            this.state.wsConnection = null;
        }
        
        this._updateConnectionStatus(false);
        this.logger.info('Sincronização parada');
    },
    
    /**
     * Registra callback para mudanças nos dados
     * @param {string} key - Chave única para o callback
     * @param {Function} callback - Função callback
     */
    onDataChange: function(key, callback) {
        if (typeof callback !== 'function') {
            this.logger.error('Callback deve ser uma função');
            return;
        }
        
        this.state.callbacks.set(key, callback);
        this.logger.debug(`Callback registrado: ${key}`);
        
        // Se já temos dados, chamar callback imediatamente
        if (this.state.currentData) {
            try {
                callback(this.state.currentData);
            } catch (error) {
                this.logger.error(`Erro ao executar callback ${key}:`, error);
            }
        }
    },
    
    /**
     * Remove callback
     * @param {string} key - Chave do callback
     */
    offDataChange: function(key) {
        this.state.callbacks.delete(key);
        this.logger.debug(`Callback removido: ${key}`);
    },
    
    /**
     * Força uma sincronização imediata
     */
    forceSync: function() {
        this.logger.info('Forçando sincronização...');
        this._syncData();
    },
    
    /**
     * Obtém os dados atuais
     * @returns {Object|null} Dados atuais
     */
    getCurrentData: function() {
        return this.state.currentData;
    },
    
    /**
     * Verifica se está conectado
     * @returns {boolean} Status de conexão
     */
    isConnected: function() {
        return this.state.isConnected;
    },
    
    /**
     * Obtém estatísticas de sincronização
     * @returns {Object} Estatísticas
     */
    getStats: function() {
        return {
            isConnected: this.state.isConnected,
            isPolling: this.state.isPolling,
            lastSync: this.state.lastSync,
            dataVersion: this.state.dataVersion,
            retryCount: this.state.retryCount,
            callbackCount: this.state.callbacks.size
        };
    },
    
    // Métodos privados
    
    /**
     * Inicia o polling
     * @private
     */
    _startPolling: function() {
        if (this.state.pollInterval) {
            clearInterval(this.state.pollInterval);
        }
        
        this.state.isPolling = true;
        this.state.pollInterval = setInterval(() => {
            this._syncData();
        }, this.config.syncInterval);
        
        this.logger.debug(`Polling iniciado com intervalo de ${this.config.syncInterval}ms`);
    },
    
    /**
     * Sincroniza dados via HTTP
     * @private
     */
    _syncData: async function() {
        try {
            const response = await fetch(this.config.syncEndpoint, {
                method: 'GET',
                cache: 'no-cache',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Validar estrutura dos dados
            if (!this._validateData(data)) {
                throw new Error('Dados recebidos são inválidos');
            }
            
            // Verificar se houve mudança
            const newVersion = data.version || Date.now();
            if (newVersion !== this.state.dataVersion) {
                this.state.currentData = data;
                this.state.dataVersion = newVersion;
                this.state.lastSync = new Date();
                
                this.logger.debug('Dados atualizados, versão:', newVersion);
                
                // Notificar mudança
                this.debouncedUpdate(data);
            }
            
            // Resetar contador de retry
            this.state.retryCount = 0;
            
            // Atualizar status de conexão
            if (!this.state.isConnected) {
                this._updateConnectionStatus(true);
            }
            
        } catch (error) {
            this.logger.error('Erro na sincronização:', error);
            
            this.state.retryCount++;
            
            // Atualizar status de conexão
            if (this.state.isConnected) {
                this._updateConnectionStatus(false);
            }
            
            // Tentar reconectar se não excedeu o limite
            if (this.state.retryCount <= this.config.maxRetries) {
                this.logger.info(`Tentativa de reconexão ${this.state.retryCount}/${this.config.maxRetries}`);
                setTimeout(() => {
                    this._syncData();
                }, this.config.retryInterval);
            } else {
                this.logger.error('Máximo de tentativas excedido, parando sincronização');
                this.stop();
            }
        }
    },
    
    /**
     * Valida estrutura dos dados recebidos
     * @param {Object} data - Dados para validar
     * @returns {boolean} True se válido
     * @private
     */
    _validateData: function(data) {
        if (!data || typeof data !== 'object') {
            return false;
        }
        
        // Validar estrutura esperada
        const requiredFields = [
            'tempo_decorrido',
            'esta_executando',
            'esta_pausado',
            'projeto_atual',
            'progresso_workflow',
            'estagio_atual',
            'total_estagios',
            'total_notificacoes',
            'notificacoes_nao_lidas',
            'sidebar_expandido',
            'breakpoint_atual'
        ];
        
        return Utils.validateObject(data, requiredFields);
    },
    
    /**
     * Atualiza a interface com novos dados
     * @param {Object} data - Dados para atualizar
     * @private
     */
    _updateUI: function(data) {
        this.logger.debug('Atualizando interface com novos dados');
        
        // Executar todos os callbacks registrados
        this.state.callbacks.forEach((callback, key) => {
            try {
                callback(data);
            } catch (error) {
                this.logger.error(`Erro ao executar callback ${key}:`, error);
            }
        });
    },
    
    /**
     * Atualiza status de conexão na UI
     * @param {boolean} connected - Status de conexão
     * @private
     */
    _updateConnectionStatus: function(connected) {
        this.state.isConnected = connected;
        
        const indicator = document.getElementById('sync-indicator');
        const text = document.getElementById('sync-text');
        
        if (indicator && text) {
            if (connected) {
                indicator.className = 'sync-indicator online';
                text.textContent = 'Conectado';
            } else {
                indicator.className = 'sync-indicator offline';
                text.textContent = 'Desconectado';
            }
        }
        
        this.logger.info(`Status de conexão: ${connected ? 'Conectado' : 'Desconectado'}`);
    },
    
    /**
     * Configura handlers de visibilidade da página
     * @private
     */
    _setupVisibilityHandlers: function() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.logger.debug('Página oculta, reduzindo frequência de sync');
                // Reduzir frequência quando página não está visível
                if (this.state.pollInterval) {
                    clearInterval(this.state.pollInterval);
                    this.state.pollInterval = setInterval(() => {
                        this._syncData();
                    }, this.config.syncInterval * 3); // 3x mais lento
                }
            } else {
                this.logger.debug('Página visível, restaurando frequência normal');
                // Restaurar frequência normal
                this._startPolling();
                // Sync imediato ao voltar
                this._syncData();
            }
        });
    },
    
    /**
     * Configura handlers de rede
     * @private
     */
    _setupNetworkHandlers: function() {
        window.addEventListener('online', () => {
            this.logger.info('Conexão de rede restaurada');
            this.state.retryCount = 0;
            this.start();
        });
        
        window.addEventListener('offline', () => {
            this.logger.warn('Conexão de rede perdida');
            this._updateConnectionStatus(false);
        });
    },
    
    /**
     * Inicializa WebSocket (futuro)
     * @private
     */
    _initWebSocket: function() {
        // Implementação futura para WebSocket
        this.logger.info('WebSocket não implementado ainda, usando polling');
    }
};

// Inicialização automática quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Configurar modo debug baseado na URL
    const urlParams = new URLSearchParams(window.location.search);
    window.DEBUG_MODE = urlParams.get('debug') === 'true';
    
    // Inicializar sincronização
    DataSync.init({
        syncInterval: window.DEBUG_MODE ? 500 : 1000, // Mais rápido em debug
        enablePolling: true
    });
});

// Exportar para uso global
window.DataSync = DataSync;