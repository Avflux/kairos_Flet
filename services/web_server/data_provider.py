"""
Provedores de dados para sincronização do servidor web integrado.

Este módulo define a interface abstrata DataProvider e suas implementações
para diferentes backends de armazenamento (JSON, MySQL).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, Optional
import json
import os
from datetime import datetime
import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class DataProvider(ABC):
    """
    Interface abstrata para provedores de dados.
    
    Esta interface define os métodos que devem ser implementados por
    diferentes backends de armazenamento para sincronização de dados.
    """
    
    @abstractmethod
    def salvar_dados(self, dados: Dict[str, Any]) -> None:
        """
        Salva os dados no armazenamento.
        
        Args:
            dados: Dicionário com os dados a serem salvos
            
        Raises:
            SincronizacaoError: Se houver erro ao salvar os dados
        """
        pass
    
    @abstractmethod
    def carregar_dados(self) -> Dict[str, Any]:
        """
        Carrega os dados do armazenamento.
        
        Returns:
            Dicionário com os dados carregados
            
        Raises:
            SincronizacaoError: Se houver erro ao carregar os dados
        """
        pass
    
    @abstractmethod
    def configurar_observador(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Configura observador para mudanças nos dados.
        
        Args:
            callback: Função a ser chamada quando os dados mudarem
        """
        pass
    
    @abstractmethod
    def parar_observador(self) -> None:
        """Para o observador de mudanças nos dados."""
        pass


class JSONFileHandler(FileSystemEventHandler):
    """Handler para observar mudanças em arquivos JSON."""
    
    def __init__(self, arquivo_json: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Inicializa o handler.
        
        Args:
            arquivo_json: Caminho para o arquivo JSON
            callback: Função a ser chamada quando o arquivo mudar
        """
        self.arquivo_json = arquivo_json
        self.callback = callback
        self._debounce_timer: Optional[threading.Timer] = None
        self._debounce_delay = 0.5  # 500ms de debounce
    
    def on_modified(self, event):
        """Chamado quando um arquivo é modificado."""
        if not event.is_directory and event.src_path.endswith(os.path.basename(self.arquivo_json)):
            self._debounce_callback()
    
    def _debounce_callback(self):
        """Implementa debouncing para evitar múltiplas chamadas."""
        if self._debounce_timer:
            self._debounce_timer.cancel()
        
        self._debounce_timer = threading.Timer(self._debounce_delay, self._executar_callback)
        self._debounce_timer.start()
    
    def _executar_callback(self):
        """Executa o callback carregando os dados atualizados."""
        try:
            with open(self.arquivo_json, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            self.callback(dados)
        except Exception:
            # Ignora erros de leitura durante a escrita do arquivo
            pass


class JSONDataProvider(DataProvider):
    """
    Implementação do DataProvider usando arquivos JSON.
    
    Esta implementação armazena dados em arquivos JSON e observa
    mudanças no arquivo para notificar callbacks registrados.
    """
    
    def __init__(self, arquivo_json: str = "web_content/data/sync.json"):
        """
        Inicializa o provedor de dados JSON.
        
        Args:
            arquivo_json: Caminho para o arquivo JSON de sincronização
        """
        self.arquivo_json = arquivo_json
        self._callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self._observer: Optional[Observer] = None
        self._handler: Optional[JSONFileHandler] = None
        self._lock = threading.Lock()
        
        # Cria o diretório se não existir
        os.makedirs(os.path.dirname(self.arquivo_json), exist_ok=True)
        
        # Cria o arquivo inicial se não existir
        if not os.path.exists(self.arquivo_json):
            self._criar_arquivo_inicial()
    
    def _criar_arquivo_inicial(self) -> None:
        """Cria o arquivo JSON inicial com estrutura básica."""
        dados_iniciais = {
            "timestamp": datetime.now().isoformat(),
            "versao": 1,
            "dados": {}
        }
        
        with open(self.arquivo_json, 'w', encoding='utf-8') as f:
            json.dump(dados_iniciais, f, indent=2, ensure_ascii=False)
    
    def salvar_dados(self, dados: Dict[str, Any]) -> None:
        """
        Salva os dados no arquivo JSON.
        
        Args:
            dados: Dicionário com os dados a serem salvos
            
        Raises:
            SincronizacaoError: Se houver erro ao salvar os dados
        """
        from .exceptions import SincronizacaoError
        
        try:
            with self._lock:
                # Carrega dados existentes para preservar metadados
                dados_existentes = {}
                if os.path.exists(self.arquivo_json):
                    try:
                        with open(self.arquivo_json, 'r', encoding='utf-8') as f:
                            dados_existentes = json.load(f)
                    except (json.JSONDecodeError, FileNotFoundError):
                        pass
                
                # Atualiza com novos dados
                dados_completos = {
                    "timestamp": datetime.now().isoformat(),
                    "versao": dados_existentes.get("versao", 0) + 1,
                    "dados": dados
                }
                
                # Salva no arquivo
                with open(self.arquivo_json, 'w', encoding='utf-8') as f:
                    json.dump(dados_completos, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            raise SincronizacaoError(f"Erro ao salvar dados JSON: {str(e)}")
    
    def carregar_dados(self) -> Dict[str, Any]:
        """
        Carrega os dados do arquivo JSON.
        
        Returns:
            Dicionário com os dados carregados
            
        Raises:
            SincronizacaoError: Se houver erro ao carregar os dados
        """
        from .exceptions import SincronizacaoError
        
        try:
            with self._lock:
                if not os.path.exists(self.arquivo_json):
                    return {}
                
                with open(self.arquivo_json, 'r', encoding='utf-8') as f:
                    dados_completos = json.load(f)
                
                return dados_completos.get("dados", {})
                
        except Exception as e:
            raise SincronizacaoError(f"Erro ao carregar dados JSON: {str(e)}")
    
    def configurar_observador(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Configura observador para mudanças no arquivo JSON.
        
        Args:
            callback: Função a ser chamada quando os dados mudarem
        """
        self._callback = callback
        
        if self._observer:
            self.parar_observador()
        
        # Configura o observador de arquivos
        self._handler = JSONFileHandler(self.arquivo_json, callback)
        self._observer = Observer()
        self._observer.schedule(
            self._handler,
            os.path.dirname(self.arquivo_json),
            recursive=False
        )
        self._observer.start()
    
    def parar_observador(self) -> None:
        """Para o observador de mudanças nos dados."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
        
        if self._handler and hasattr(self._handler, '_debounce_timer'):
            if self._handler._debounce_timer:
                self._handler._debounce_timer.cancel()
        
        self._handler = None


class MySQLDataProvider(DataProvider):
    """
    Implementação do DataProvider usando MySQL.
    
    Esta é uma implementação placeholder para futura integração com MySQL.
    Atualmente levanta NotImplementedError para todos os métodos.
    """
    
    def __init__(self, config_conexao: Dict[str, Any]):
        """
        Inicializa o provedor de dados MySQL.
        
        Args:
            config_conexao: Configurações de conexão com MySQL
        """
        self.config_conexao = config_conexao
        # TODO: Implementar conexão MySQL
    
    def salvar_dados(self, dados: Dict[str, Any]) -> None:
        """Placeholder para implementação MySQL."""
        raise NotImplementedError("MySQLDataProvider será implementado em versão futura")
    
    def carregar_dados(self) -> Dict[str, Any]:
        """Placeholder para implementação MySQL."""
        raise NotImplementedError("MySQLDataProvider será implementado em versão futura")
    
    def configurar_observador(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Placeholder para implementação MySQL."""
        raise NotImplementedError("MySQLDataProvider será implementado em versão futura")
    
    def parar_observador(self) -> None:
        """Placeholder para implementação MySQL."""
        raise NotImplementedError("MySQLDataProvider será implementado em versão futura")