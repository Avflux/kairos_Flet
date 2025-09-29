"""
Gerenciador de sincronização de dados para o servidor web integrado.

Este módulo implementa o DataSyncManager, responsável por coordenar a
sincronização de dados entre a aplicação Flet e o WebView, incluindo
sistema de callbacks, tratamento de erros e retry automático.
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
import json

from .data_provider import DataProvider
from .models import EstadoSincronizacao, StatusSincronizacao, DadosTopSidebar
from .exceptions import (
    SincronizacaoError, 
    ConfiguracaoError,
    CodigosErro
)
from .audit_logger import (
    registrar_evento_auditoria,
    TipoEvento,
    NivelSeveridade
)


@dataclass
class ConfiguracaoRetry:
    """Configuração para sistema de retry automático."""
    
    max_tentativas: int = 3
    delay_inicial: float = 1.0  # segundos
    multiplicador_backoff: float = 2.0
    delay_maximo: float = 30.0  # segundos
    jitter: bool = True  # adiciona aleatoriedade ao delay


class DataSyncManager:
    """
    Gerenciador de sincronização de dados entre aplicação Flet e WebView.
    
    Esta classe coordena a sincronização de dados, gerencia callbacks para
    notificação de mudanças, implementa retry automático e mantém logs
    detalhados em português para debug.
    """
    
    def __init__(
        self, 
        provedor_dados: DataProvider,
        config_retry: Optional[ConfiguracaoRetry] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Inicializa o gerenciador de sincronização.
        
        Args:
            provedor_dados: Provedor de dados (JSON ou MySQL)
            config_retry: Configuração do sistema de retry
            logger: Logger personalizado (opcional)
        """
        self.provedor_dados = provedor_dados
        self.config_retry = config_retry or ConfiguracaoRetry()
        
        # Configurar logger
        self.logger = logger or self._configurar_logger()
        
        # Estado interno
        self.estado = EstadoSincronizacao()
        self._callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._callbacks_erro: List[Callable[[str, str], None]] = []
        self._lock = threading.RLock()
        self._thread_retry: Optional[threading.Thread] = None
        self._parar_retry = threading.Event()
        self._dados_cache: Optional[Dict[str, Any]] = None
        
        # Configurar observador do provedor de dados
        self._configurar_observador_dados()
        
        self.logger.info("DataSyncManager inicializado com sucesso")
        
        # Registrar inicialização na auditoria
        registrar_evento_auditoria(
            tipo_evento=TipoEvento.SYNC_INICIADA,
            severidade=NivelSeveridade.INFO,
            componente="DataSyncManager",
            mensagem="Gerenciador de sincronização inicializado",
            detalhes={
                "provedor_dados": type(self.provedor_dados).__name__,
                "max_tentativas": self.config_retry.max_tentativas,
                "delay_inicial": self.config_retry.delay_inicial
            }
        )
    
    def _configurar_logger(self) -> logging.Logger:
        """Configura logger com formatação em português."""
        logger = logging.getLogger(f"{__name__}.DataSyncManager")
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - [SYNC] %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        
        return logger
    
    def _configurar_observador_dados(self) -> None:
        """Configura observador para mudanças nos dados do provedor."""
        try:
            self.provedor_dados.configurar_observador(self._callback_mudanca_dados)
            self.logger.info("Observador de dados configurado com sucesso")
        except Exception as e:
            self.logger.error(f"Erro ao configurar observador de dados: {str(e)}")
            raise SincronizacaoError(
                f"Falha ao configurar observador de dados: {str(e)}",
                codigo_erro=CodigosErro.SYNC_TIMEOUT
            )
    
    def _callback_mudanca_dados(self, dados: Dict[str, Any]) -> None:
        """
        Callback chamado quando os dados do provedor mudam.
        
        Args:
            dados: Novos dados recebidos do provedor
        """
        with self._lock:
            try:
                self.logger.debug(f"Mudança detectada nos dados: {len(dados)} chaves")
                
                # Atualizar cache
                self._dados_cache = dados.copy()
                
                # Notificar callbacks registrados
                self._notificar_callbacks(dados)
                
                self.logger.debug("Callback de mudança de dados processado")
                
            except Exception as e:
                self.logger.error(f"Erro no callback de mudança de dados: {str(e)}")
                self._tratar_erro_sincronizacao(str(e), CodigosErro.SYNC_DADOS_CORROMPIDOS)
    
    def atualizar_dados(self, dados: Dict[str, Any]) -> None:
        """
        Atualiza os dados e notifica o WebView.
        
        Args:
            dados: Dicionário com os dados atualizados
            
        Raises:
            SincronizacaoError: Se houver erro na atualização
        """
        with self._lock:
            self.logger.debug(f"Iniciando atualização de dados com {len(dados)} chaves")
            
            # Validar dados
            self._validar_dados(dados)
            
            # Tentar salvar com retry automático
            self._salvar_com_retry(dados)
            
            self.logger.info("Dados atualizados com sucesso")
    
    def _validar_dados(self, dados: Dict[str, Any]) -> None:
        """
        Valida os dados antes da sincronização.
        
        Args:
            dados: Dados a serem validados
            
        Raises:
            SincronizacaoError: Se os dados forem inválidos
        """
        if not isinstance(dados, dict):
            raise SincronizacaoError(
                "Dados devem ser um dicionário",
                codigo_erro=CodigosErro.SYNC_FORMATO_INVALIDO
            )
        
        # Verificar se é possível serializar para JSON
        try:
            json.dumps(dados)
        except (TypeError, ValueError) as e:
            raise SincronizacaoError(
                f"Dados não são serializáveis para JSON: {str(e)}",
                codigo_erro=CodigosErro.SYNC_FORMATO_INVALIDO
            )
        
        self.logger.debug("Validação de dados concluída com sucesso")
    
    def _salvar_com_retry(self, dados: Dict[str, Any]) -> None:
        """
        Salva dados com sistema de retry automático.
        
        Args:
            dados: Dados a serem salvos
            
        Raises:
            SincronizacaoError: Se todas as tentativas falharem
        """
        ultima_excecao = None
        delay = self.config_retry.delay_inicial
        
        for tentativa in range(1, self.config_retry.max_tentativas + 1):
            try:
                tempo_inicio = time.time()
                
                self.logger.debug(f"Tentativa {tentativa} de salvamento de dados")
                self.provedor_dados.salvar_dados(dados)
                
                # Sucesso - atualizar cache e estado
                self._dados_cache = dados.copy()
                tempo_ms = (time.time() - tempo_inicio) * 1000
                self.estado.registrar_sucesso(tempo_ms)
                
                self.logger.info(f"Dados salvos com sucesso na tentativa {tentativa}")
                
                # Registrar sucesso na auditoria
                registrar_evento_auditoria(
                    tipo_evento=TipoEvento.SYNC_SUCESSO,
                    severidade=NivelSeveridade.INFO,
                    componente="DataSyncManager",
                    mensagem=f"Sincronização bem-sucedida na tentativa {tentativa}",
                    detalhes={
                        "tentativa": tentativa,
                        "tempo_ms": tempo_ms,
                        "total_chaves": len(dados),
                        "delay_usado": delay if tentativa > 1 else 0
                    }
                )
                return
                
            except Exception as e:
                ultima_excecao = e
                self.logger.warning(
                    f"Tentativa {tentativa} falhou: {str(e)}. "
                    f"Tentativas restantes: {self.config_retry.max_tentativas - tentativa}"
                )
                
                # Se não é a última tentativa, aguardar antes de tentar novamente
                if tentativa < self.config_retry.max_tentativas:
                    delay_atual = min(delay, self.config_retry.delay_maximo)
                    
                    # Adicionar jitter se configurado
                    if self.config_retry.jitter:
                        import random
                        delay_atual *= (0.5 + random.random() * 0.5)
                    
                    self.logger.debug(f"Aguardando {delay_atual:.2f}s antes da próxima tentativa")
                    time.sleep(delay_atual)
                    
                    # Aumentar delay para próxima tentativa (backoff exponencial)
                    delay *= self.config_retry.multiplicador_backoff
        
        # Todas as tentativas falharam
        erro_msg = f"Falha ao salvar dados após {self.config_retry.max_tentativas} tentativas: {str(ultima_excecao)}"
        self.logger.error(erro_msg)
        
        # Registrar erro na auditoria
        registrar_evento_auditoria(
            tipo_evento=TipoEvento.SYNC_ERRO,
            severidade=NivelSeveridade.ERROR,
            componente="DataSyncManager",
            mensagem="Falha na sincronização após múltiplas tentativas",
            detalhes={
                "max_tentativas": self.config_retry.max_tentativas,
                "ultimo_erro": str(ultima_excecao),
                "total_chaves": len(dados),
                "config_retry": {
                    "delay_inicial": self.config_retry.delay_inicial,
                    "multiplicador_backoff": self.config_retry.multiplicador_backoff,
                    "delay_maximo": self.config_retry.delay_maximo
                }
            }
        )
        
        # Registrar erro apenas uma vez
        with self._lock:
            self.estado.registrar_erro(erro_msg, CodigosErro.SYNC_TIMEOUT)
            self._notificar_callbacks_erro(erro_msg, CodigosErro.SYNC_TIMEOUT)
        
        raise SincronizacaoError(erro_msg, codigo_erro=CodigosErro.SYNC_TIMEOUT)
    
    def obter_dados(self) -> Dict[str, Any]:
        """
        Obtém os dados atuais.
        
        Returns:
            Dicionário com os dados atuais
            
        Raises:
            SincronizacaoError: Se houver erro ao carregar os dados
        """
        with self._lock:
            try:
                # Tentar usar cache primeiro
                if self._dados_cache is not None:
                    self.logger.debug("Retornando dados do cache")
                    return self._dados_cache.copy()
                
                # Carregar do provedor
                self.logger.debug("Carregando dados do provedor")
                dados = self.provedor_dados.carregar_dados()
                
                # Atualizar cache
                self._dados_cache = dados.copy()
                
                self.logger.info(f"Dados carregados com sucesso: {len(dados)} chaves")
                return dados
                
            except Exception as e:
                self.logger.error(f"Erro ao obter dados: {str(e)}")
                self._tratar_erro_sincronizacao(str(e), CodigosErro.SYNC_ARQUIVO_NAO_ENCONTRADO)
                raise SincronizacaoError(
                    f"Erro ao carregar dados: {str(e)}",
                    codigo_erro=CodigosErro.SYNC_ARQUIVO_NAO_ENCONTRADO
                )
    
    def registrar_callback_mudanca(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Registra callback para mudanças nos dados.
        
        Args:
            callback: Função a ser chamada quando os dados mudarem
                     Deve aceitar um dicionário como parâmetro
        """
        if not callable(callback):
            raise ConfiguracaoError(
                "Callback deve ser uma função chamável",
                parametro="callback",
                codigo_erro=CodigosErro.CONFIG_VALOR_INVALIDO
            )
        
        with self._lock:
            self._callbacks.append(callback)
            self.logger.info(f"Callback registrado. Total de callbacks: {len(self._callbacks)}")
    
    def remover_callback_mudanca(self, callback: Callable[[Dict[str, Any]], None]) -> bool:
        """
        Remove um callback de mudanças.
        
        Args:
            callback: Callback a ser removido
            
        Returns:
            True se o callback foi removido, False se não foi encontrado
        """
        with self._lock:
            try:
                self._callbacks.remove(callback)
                self.logger.info(f"Callback removido. Total de callbacks: {len(self._callbacks)}")
                return True
            except ValueError:
                self.logger.warning("Tentativa de remover callback não registrado")
                return False
    
    def registrar_callback_erro(self, callback: Callable[[str, str], None]) -> None:
        """
        Registra callback para notificação de erros.
        
        Args:
            callback: Função a ser chamada quando houver erro
                     Deve aceitar mensagem de erro e código como parâmetros
        """
        if not callable(callback):
            raise ConfiguracaoError(
                "Callback de erro deve ser uma função chamável",
                parametro="callback_erro",
                codigo_erro=CodigosErro.CONFIG_VALOR_INVALIDO
            )
        
        with self._lock:
            self._callbacks_erro.append(callback)
            self.logger.info(f"Callback de erro registrado. Total: {len(self._callbacks_erro)}")
    
    def _notificar_callbacks(self, dados: Dict[str, Any]) -> None:
        """
        Notifica todos os callbacks registrados sobre mudanças nos dados.
        
        Args:
            dados: Dados atualizados
        """
        callbacks_com_erro = []
        
        for callback in self._callbacks:
            try:
                callback(dados)
            except Exception as e:
                self.logger.error(f"Erro em callback: {str(e)}")
                callbacks_com_erro.append(callback)
        
        # Remove callbacks que falharam consistentemente
        if callbacks_com_erro:
            self.logger.warning(f"Removendo {len(callbacks_com_erro)} callbacks com erro")
            for callback in callbacks_com_erro:
                self._callbacks.remove(callback)
    
    def _notificar_callbacks_erro(self, mensagem: str, codigo: str) -> None:
        """
        Notifica callbacks de erro.
        
        Args:
            mensagem: Mensagem de erro
            codigo: Código do erro
        """
        for callback in self._callbacks_erro:
            try:
                callback(mensagem, codigo)
            except Exception as e:
                self.logger.error(f"Erro em callback de erro: {str(e)}")
    
    def _tratar_erro_sincronizacao(self, mensagem: str, codigo: str) -> None:
        """
        Trata erros de sincronização e atualiza estado.
        
        Args:
            mensagem: Mensagem de erro
            codigo: Código do erro
        """
        with self._lock:
            self.estado.registrar_erro(mensagem, codigo)
            self._notificar_callbacks_erro(mensagem, codigo)
            
            # Iniciar retry automático se configurado
            if (self.estado.tentativas_falha_consecutivas < self.config_retry.max_tentativas and
                not self._thread_retry or not self._thread_retry.is_alive()):
                self._iniciar_retry_automatico()
    
    def _iniciar_retry_automatico(self) -> None:
        """Inicia thread de retry automático."""
        if self._thread_retry and self._thread_retry.is_alive():
            return
        
        self._parar_retry.clear()
        self._thread_retry = threading.Thread(
            target=self._executar_retry_automatico,
            name="DataSyncManager-Retry",
            daemon=True
        )
        self._thread_retry.start()
        self.logger.info("Thread de retry automático iniciada")
    
    def _executar_retry_automatico(self) -> None:
        """Executa retry automático em thread separada."""
        delay = self.config_retry.delay_inicial
        
        while (not self._parar_retry.is_set() and 
               self.estado.status == StatusSincronizacao.ERRO and
               self.estado.tentativas_falha_consecutivas < self.config_retry.max_tentativas):
            
            try:
                self.logger.info(f"Tentativa de recuperação automática em {delay:.2f}s")
                
                if self._parar_retry.wait(delay):
                    break  # Parada solicitada
                
                # Tentar recarregar dados
                dados = self.provedor_dados.carregar_dados()
                self._dados_cache = dados.copy()
                
                # Se chegou aqui, a recuperação foi bem-sucedida
                tempo_ms = 0  # Não medimos tempo para recuperação
                self.estado.registrar_sucesso(tempo_ms)
                self.logger.info("Recuperação automática bem-sucedida")
                
                # Registrar recuperação na auditoria
                registrar_evento_auditoria(
                    tipo_evento=TipoEvento.SYNC_RECUPERADA,
                    severidade=NivelSeveridade.INFO,
                    componente="DataSyncManager",
                    mensagem="Sincronização recuperada automaticamente",
                    detalhes={
                        "tentativas_falha_anteriores": self.estado.tentativas_falha_consecutivas,
                        "delay_usado": delay,
                        "total_chaves_recuperadas": len(dados)
                    }
                )
                
                # Notificar callbacks com dados recuperados
                self._notificar_callbacks(dados)
                break
                
            except Exception as e:
                self.logger.warning(f"Tentativa de recuperação falhou: {str(e)}")
                delay = min(delay * self.config_retry.multiplicador_backoff, 
                           self.config_retry.delay_maximo)
        
        self.logger.info("Thread de retry automático finalizada")
    
    def obter_estado_sincronizacao(self) -> EstadoSincronizacao:
        """
        Obtém o estado atual da sincronização.
        
        Returns:
            Cópia do estado atual de sincronização
        """
        with self._lock:
            # Retorna uma cópia para evitar modificações externas
            import copy
            return copy.deepcopy(self.estado)
    
    def pausar_sincronizacao(self) -> None:
        """Pausa a sincronização de dados."""
        with self._lock:
            if self.estado.status != StatusSincronizacao.PAUSADO:
                self.estado.status = StatusSincronizacao.PAUSADO
                self._parar_retry.set()
                self.logger.info("Sincronização pausada")
    
    def retomar_sincronizacao(self) -> None:
        """Retoma a sincronização de dados."""
        with self._lock:
            if self.estado.status == StatusSincronizacao.PAUSADO:
                self.estado.status = StatusSincronizacao.ATIVO
                self._parar_retry.clear()
                self.logger.info("Sincronização retomada")
    
    def limpar_cache(self) -> None:
        """Limpa o cache de dados."""
        with self._lock:
            self._dados_cache = None
            self.logger.info("Cache de dados limpo")
    
    def atualizar_dados_topsidebar(self, dados_topsidebar: DadosTopSidebar) -> None:
        """
        Atualiza dados específicos do TopSidebarContainer.
        
        Args:
            dados_topsidebar: Dados estruturados do TopSidebarContainer
        """
        try:
            dados_dict = dados_topsidebar.to_dict()
            self.atualizar_dados(dados_dict)
            self.logger.info("Dados do TopSidebarContainer atualizados com sucesso")
        except Exception as e:
            self.logger.error(f"Erro ao atualizar dados do TopSidebarContainer: {str(e)}")
            raise
    
    def obter_dados_topsidebar(self) -> Optional[DadosTopSidebar]:
        """
        Obtém dados estruturados do TopSidebarContainer.
        
        Returns:
            Instância de DadosTopSidebar ou None se não houver dados
        """
        try:
            dados = self.obter_dados()
            if not dados:
                return None
            
            return DadosTopSidebar.from_dict(dados)
        except Exception as e:
            self.logger.error(f"Erro ao obter dados do TopSidebarContainer: {str(e)}")
            return None
    
    def finalizar(self) -> None:
        """Finaliza o gerenciador de sincronização."""
        with self._lock:
            self.logger.info("Finalizando DataSyncManager")
            
            # Parar retry automático
            self._parar_retry.set()
            if self._thread_retry and self._thread_retry.is_alive():
                self._thread_retry.join(timeout=5.0)
            
            # Parar observador do provedor
            try:
                self.provedor_dados.parar_observador()
            except Exception as e:
                self.logger.warning(f"Erro ao parar observador: {str(e)}")
            
            # Limpar callbacks
            self._callbacks.clear()
            self._callbacks_erro.clear()
            
            # Atualizar estado
            self.estado.status = StatusSincronizacao.INATIVO
            
            self.logger.info("DataSyncManager finalizado")
    
    def __enter__(self):
        """Suporte para context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Suporte para context manager."""
        self.finalizar()