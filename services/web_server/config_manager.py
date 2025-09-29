"""
Gerenciador de configurações do servidor web integrado.

Este módulo fornece funcionalidades para gerenciar configurações
do servidor web, incluindo carregamento automático, validação
e monitoramento de mudanças em arquivos de configuração.
"""

import logging
import os
import threading
import time
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .config import (
    ConfiguracaoServidorWeb,
    ErroConfiguracaoServidorWeb,
    ErroCarregamentoConfiguracao
)


class ConfigFileHandler(FileSystemEventHandler):
    """Handler para monitorar mudanças em arquivos de configuração."""
    
    def __init__(self, config_manager: 'ConfigManager'):
        self.config_manager = config_manager
        self.logger = logging.getLogger('servidor_web_integrado.config')
    
    def on_modified(self, event):
        """Chamado quando um arquivo é modificado."""
        if not event.is_directory and event.src_path == str(self.config_manager.caminho_config):
            self.logger.info("Arquivo de configuração modificado, recarregando...")
            self.config_manager.recarregar_configuracao()


class ConfigManager:
    """
    Gerenciador centralizado de configurações do servidor web.
    
    Esta classe gerencia o carregamento, validação e monitoramento
    de configurações, fornecendo uma interface única para acesso
    às configurações do sistema.
    """
    
    def __init__(
        self,
        caminho_config: Optional[str] = None,
        monitorar_mudancas: bool = True,
        callback_mudanca: Optional[Callable[[ConfiguracaoServidorWeb], None]] = None
    ):
        """
        Inicializa o gerenciador de configurações.
        
        Args:
            caminho_config: Caminho do arquivo de configuração
            monitorar_mudancas: Se deve monitorar mudanças no arquivo
            callback_mudanca: Callback chamado quando configuração muda
        """
        self.logger = logging.getLogger('servidor_web_integrado.config')
        
        # Definir caminho padrão se não fornecido
        if caminho_config is None:
            caminho_config = os.path.join("services", "web_server", "config.json")
        
        self.caminho_config = Path(caminho_config)
        self.monitorar_mudancas = monitorar_mudancas
        self.callback_mudanca = callback_mudanca
        
        # Estado interno
        self._config: Optional[ConfiguracaoServidorWeb] = None
        self._observer: Optional[Observer] = None
        self._lock = threading.RLock()
        
        # Carregar configuração inicial
        self._carregar_configuracao_inicial()
        
        # Iniciar monitoramento se solicitado
        if self.monitorar_mudancas:
            self._iniciar_monitoramento()
    
    def _carregar_configuracao_inicial(self) -> None:
        """Carrega a configuração inicial."""
        try:
            if self.caminho_config.exists():
                self._config = ConfiguracaoServidorWeb.carregar_arquivo(self.caminho_config)
                self.logger.info(f"Configuração carregada de {self.caminho_config}")
            else:
                self._config = ConfiguracaoServidorWeb()
                self.logger.info("Usando configuração padrão")
                
                # Criar arquivo de configuração padrão
                try:
                    self._config.salvar_arquivo(self.caminho_config)
                    self.logger.info(f"Arquivo de configuração padrão criado em {self.caminho_config}")
                except Exception as e:
                    self.logger.warning(f"Não foi possível criar arquivo de configuração: {e}")
            
            # Configurar logging baseado na configuração carregada
            self._config.configurar_logging()
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar configuração inicial: {e}")
            self._config = ConfiguracaoServidorWeb()
            self._config.configurar_logging()
    
    def _iniciar_monitoramento(self) -> None:
        """Inicia o monitoramento de mudanças no arquivo de configuração."""
        try:
            if self._observer is not None:
                self._observer.stop()
                self._observer.join()
            
            self._observer = Observer()
            handler = ConfigFileHandler(self)
            
            # Monitorar o diretório do arquivo de configuração
            diretorio = self.caminho_config.parent
            if not diretorio.exists():
                diretorio.mkdir(parents=True, exist_ok=True)
            
            self._observer.schedule(handler, str(diretorio), recursive=False)
            self._observer.start()
            
            self.logger.debug(f"Monitoramento de configuração iniciado para {diretorio}")
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar monitoramento de configuração: {e}")
    
    def recarregar_configuracao(self) -> bool:
        """
        Recarrega a configuração do arquivo.
        
        Returns:
            True se a configuração foi recarregada com sucesso
        """
        with self._lock:
            try:
                if not self.caminho_config.exists():
                    self.logger.warning("Arquivo de configuração não existe, mantendo configuração atual")
                    return False
                
                nova_config = ConfiguracaoServidorWeb.carregar_arquivo(self.caminho_config)
                config_anterior = self._config
                self._config = nova_config
                
                # Reconfigurar logging
                self._config.configurar_logging()
                
                self.logger.info("Configuração recarregada com sucesso")
                
                # Chamar callback se fornecido
                if self.callback_mudanca:
                    try:
                        self.callback_mudanca(self._config)
                    except Exception as e:
                        self.logger.error(f"Erro no callback de mudança de configuração: {e}")
                
                return True
                
            except Exception as e:
                self.logger.error(f"Erro ao recarregar configuração: {e}")
                return False
    
    def obter_configuracao(self) -> ConfiguracaoServidorWeb:
        """
        Obtém a configuração atual.
        
        Returns:
            Instância atual de ConfiguracaoServidorWeb
        """
        with self._lock:
            if self._config is None:
                self._config = ConfiguracaoServidorWeb()
            return self._config
    
    def atualizar_configuracao(self, **kwargs) -> bool:
        """
        Atualiza configurações específicas.
        
        Args:
            **kwargs: Parâmetros de configuração para atualizar
            
        Returns:
            True se a atualização foi bem-sucedida
        """
        with self._lock:
            try:
                config_dict = self._config.para_dict()
                config_dict.update(kwargs)
                
                # Criar nova configuração com valores atualizados
                nova_config = ConfiguracaoServidorWeb(**config_dict)
                
                # Salvar no arquivo
                nova_config.salvar_arquivo(self.caminho_config)
                
                self._config = nova_config
                self._config.configurar_logging()
                
                self.logger.info("Configuração atualizada com sucesso")
                
                # Chamar callback se fornecido
                if self.callback_mudanca:
                    try:
                        self.callback_mudanca(self._config)
                    except Exception as e:
                        self.logger.error(f"Erro no callback de mudança de configuração: {e}")
                
                return True
                
            except Exception as e:
                self.logger.error(f"Erro ao atualizar configuração: {e}")
                return False
    
    def validar_configuracao_atual(self) -> bool:
        """
        Valida a configuração atual.
        
        Returns:
            True se a configuração é válida
        """
        try:
            self._config.validar()
            return True
        except Exception as e:
            self.logger.error(f"Configuração inválida: {e}")
            return False
    
    def obter_info_configuracao(self) -> Dict[str, Any]:
        """
        Obtém informações sobre a configuração atual.
        
        Returns:
            Dicionário com informações da configuração
        """
        with self._lock:
            return {
                'caminho_arquivo': str(self.caminho_config),
                'arquivo_existe': self.caminho_config.exists(),
                'monitoramento_ativo': self._observer is not None and self._observer.is_alive(),
                'configuracao_valida': self.validar_configuracao_atual(),
                'modo_debug': self._config.modo_debug if self._config else False,
                'porta_preferencial': self._config.porta_preferencial if self._config else None,
            }
    
    def parar_monitoramento(self) -> None:
        """Para o monitoramento de mudanças no arquivo."""
        if self._observer is not None:
            try:
                self._observer.stop()
                self._observer.join(timeout=5)
                self.logger.debug("Monitoramento de configuração parado")
            except Exception as e:
                self.logger.error(f"Erro ao parar monitoramento: {e}")
            finally:
                self._observer = None
    
    def __enter__(self):
        """Suporte para context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup ao sair do context manager."""
        self.parar_monitoramento()


# Instância global do gerenciador de configurações
_config_manager: Optional[ConfigManager] = None


def obter_config_manager(
    caminho_config: Optional[str] = None,
    monitorar_mudancas: bool = True,
    callback_mudanca: Optional[Callable[[ConfiguracaoServidorWeb], None]] = None
) -> ConfigManager:
    """
    Obtém a instância global do gerenciador de configurações.
    
    Args:
        caminho_config: Caminho do arquivo de configuração
        monitorar_mudancas: Se deve monitorar mudanças no arquivo
        callback_mudanca: Callback chamado quando configuração muda
        
    Returns:
        Instância do ConfigManager
    """
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager(
            caminho_config=caminho_config,
            monitorar_mudancas=monitorar_mudancas,
            callback_mudanca=callback_mudanca
        )
    
    return _config_manager


def obter_configuracao() -> ConfiguracaoServidorWeb:
    """
    Obtém a configuração atual do sistema.
    
    Returns:
        Instância atual de ConfiguracaoServidorWeb
    """
    return obter_config_manager().obter_configuracao()


def recarregar_configuracao() -> bool:
    """
    Recarrega a configuração do arquivo.
    
    Returns:
        True se a configuração foi recarregada com sucesso
    """
    return obter_config_manager().recarregar_configuracao()


def atualizar_configuracao(**kwargs) -> bool:
    """
    Atualiza configurações específicas.
    
    Args:
        **kwargs: Parâmetros de configuração para atualizar
        
    Returns:
        True se a atualização foi bem-sucedida
    """
    return obter_config_manager().atualizar_configuracao(**kwargs)