/**
 * Utilitários JavaScript para o sistema integrado
 * Funções auxiliares para manipulação de dados, formatação e helpers gerais
 */

// Namespace para utilitários
window.Utils = {

    /**
     * Formata tempo em segundos para formato HH:MM:SS
     * @param {number} seconds - Tempo em segundos
     * @returns {string} Tempo formatado
     */
    formatTime: function (seconds) {
        if (typeof seconds !== 'number' || seconds < 0 || isNaN(seconds)) return '00:00:00';

        const totalSeconds = Math.floor(seconds);
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const secs = totalSeconds % 60;

        return [hours, minutes, secs]
            .map(val => val.toString().padStart(2, '0'))
            .join(':');
    },

    /**
     * Formata data/hora para exibição
     * @param {Date|string} date - Data para formatar
     * @returns {string} Data formatada
     */
    formatDateTime: function (date) {
        if (!date) return '--:--';

        const d = new Date(date);
        if (isNaN(d.getTime())) return '--:--';

        return d.toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    /**
     * Formata data completa para exibição
     * @param {Date|string} date - Data para formatar
     * @returns {string} Data formatada
     */
    formatFullDateTime: function (date) {
        if (!date) return 'Nunca';

        const d = new Date(date);
        if (isNaN(d.getTime())) return 'Nunca';

        return d.toLocaleString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    /**
     * Calcula progresso em porcentagem
     * @param {number} current - Valor atual
     * @param {number} total - Valor total
     * @returns {number} Porcentagem (0-100)
     */
    calculateProgress: function (current, total) {
        if (!total || total <= 0) return 0;
        if (!current || current < 0) return 0;
        if (current >= total) return 100;

        return Math.round((current / total) * 100);
    },

    /**
     * Debounce para otimizar chamadas de função
     * @param {Function} func - Função para fazer debounce
     * @param {number} wait - Tempo de espera em ms
     * @returns {Function} Função com debounce
     */
    debounce: function (func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Throttle para limitar chamadas de função
     * @param {Function} func - Função para fazer throttle
     * @param {number} limit - Limite de tempo em ms
     * @returns {Function} Função com throttle
     */
    throttle: function (func, limit) {
        let inThrottle;
        return function (...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /**
     * Sanitiza string para exibição segura
     * @param {string} str - String para sanitizar
     * @returns {string} String sanitizada
     */
    sanitizeString: function (str) {
        if (!str) return '';

        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    /**
     * Trunca texto com reticências
     * @param {string} text - Texto para truncar
     * @param {number} maxLength - Comprimento máximo
     * @returns {string} Texto truncado
     */
    truncateText: function (text, maxLength = 50) {
        if (!text) return '';
        if (text.length <= maxLength) return text;

        return text.substring(0, maxLength - 3) + '...';
    },

    /**
     * Detecta breakpoint atual baseado na largura da tela
     * @returns {string} Nome do breakpoint (mobile, tablet, desktop)
     */
    getCurrentBreakpoint: function () {
        const width = window.innerWidth;

        if (width <= 768) return 'mobile';
        if (width <= 1024) return 'tablet';
        return 'desktop';
    },

    /**
     * Adiciona classe CSS com animação
     * @param {HTMLElement} element - Elemento DOM
     * @param {string} className - Nome da classe
     * @param {number} duration - Duração em ms (opcional)
     */
    addClassWithAnimation: function (element, className, duration = 300) {
        if (!element) return;

        element.classList.add(className);

        if (duration > 0) {
            setTimeout(() => {
                element.classList.remove(className);
            }, duration);
        }
    },

    /**
     * Remove classe CSS com fade out
     * @param {HTMLElement} element - Elemento DOM
     * @param {string} className - Nome da classe
     */
    removeClassWithFade: function (element, className) {
        if (!element) return;

        element.style.transition = 'opacity 0.3s ease';
        element.style.opacity = '0';

        setTimeout(() => {
            element.classList.remove(className);
            element.style.opacity = '';
            element.style.transition = '';
        }, 300);
    },

    /**
     * Cria elemento DOM com atributos
     * @param {string} tag - Tag do elemento
     * @param {Object} attributes - Atributos do elemento
     * @param {string} content - Conteúdo do elemento
     * @returns {HTMLElement} Elemento criado
     */
    createElement: function (tag, attributes = {}, content = '') {
        if (!tag || typeof tag !== 'string') {
            throw new Error('Tag do elemento é obrigatória e deve ser uma string');
        }

        const element = document.createElement(tag);

        Object.keys(attributes).forEach(key => {
            if (key === 'className') {
                element.className = attributes[key];
            } else if (key === 'dataset') {
                Object.keys(attributes[key]).forEach(dataKey => {
                    element.dataset[dataKey] = attributes[key][dataKey];
                });
            } else {
                element.setAttribute(key, attributes[key]);
            }
        });

        if (content) {
            // Usar textContent para segurança, a menos que seja HTML confiável
            if (content.includes('<') && content.includes('>')) {
                element.innerHTML = content; // HTML confiável
            } else {
                element.textContent = content; // Texto simples
            }
        }

        return element;
    },

    /**
     * Valida se um objeto tem as propriedades necessárias
     * @param {Object} obj - Objeto para validar
     * @param {Array} requiredProps - Propriedades obrigatórias
     * @returns {boolean} True se válido
     */
    validateObject: function (obj, requiredProps) {
        if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return false;
        if (!Array.isArray(requiredProps)) return false;

        return requiredProps.every(prop =>
            Object.prototype.hasOwnProperty.call(obj, prop) && obj[prop] !== undefined && obj[prop] !== null
        );
    },

    /**
     * Cria um logger com níveis
     * @param {string} prefix - Prefixo para logs
     * @returns {Object} Objeto logger
     */
    createLogger: function (prefix = 'WebView') {
        return {
            debug: (msg, ...args) => {
                if (window.DEBUG_MODE) {
                    console.log(`[${prefix}] ${msg}`, ...args);
                }
            },
            info: (msg, ...args) => {
                console.info(`[${prefix}] ${msg}`, ...args);
            },
            warn: (msg, ...args) => {
                console.warn(`[${prefix}] ${msg}`, ...args);
            },
            error: (msg, ...args) => {
                console.error(`[${prefix}] ${msg}`, ...args);
            }
        };
    },

    /**
     * Converte objeto para query string
     * @param {Object} obj - Objeto para converter
     * @returns {string} Query string
     */
    objectToQueryString: function (obj) {
        if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return '';

        return Object.keys(obj)
            .filter(key => obj[key] !== undefined && obj[key] !== null)
            .map(key => {
                const value = typeof obj[key] === 'object' ? JSON.stringify(obj[key]) : obj[key];
                return `${encodeURIComponent(key)}=${encodeURIComponent(value)}`;
            })
            .join('&');
    },

    /**
     * Converte query string para objeto
     * @param {string} queryString - Query string para converter
     * @returns {Object} Objeto convertido
     */
    queryStringToObject: function (queryString) {
        if (!queryString) return {};

        const params = new URLSearchParams(queryString);
        const result = {};

        for (const [key, value] = params) {
            result[key] = value;
        }
        
        return result;
},

    /**
     * Copia texto para clipboard
     * @param {string} text - Texto para copiar
     * @returns {Promise<boolean>} Promise com resultado
     */
    copyToClipboard: async function(text) {
        try {
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(text);
                return true;
            } else {
                // Fallback para navegadores mais antigos
                const textArea = document.createElement('textarea');
                textArea.value = text;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                textArea.style.top = '-999999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();

                const result = document.execCommand('copy');
                document.body.removeChild(textArea);
                return result;
            }
        } catch (error) {
            console.error('Erro ao copiar para clipboard:', error);
            return false;
        }
    },

/**
 * Gera ID único
 * @param {string} prefix - Prefixo opcional
 * @returns {string} ID único
 */
generateId: function(prefix = 'id') {
    return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
},

/**
 * Verifica se está em modo mobile
 * @returns {boolean} True se mobile
 */
isMobile: function() {
    return window.innerWidth <= 768;
},

/**
 * Verifica se está em modo tablet
 * @returns {boolean} True se tablet
 */
isTablet: function() {
    const width = window.innerWidth;
    return width > 768 && width <= 1024;
},

/**
 * Verifica se está em modo desktop
 * @returns {boolean} True se desktop
 */
isDesktop: function() {
    return window.innerWidth > 1024;
}
};

// Configurações globais
window.DEBUG_MODE = false;

// Logger global
window.Logger = Utils.createLogger('Sistema');

// Exportar para uso em módulos (se necessário)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Utils;
}