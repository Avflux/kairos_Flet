"""
Gerenciador do servidor web HTTP local.

Este módulo implementa o WebServerManager, responsável por inicializar,
gerenciar e parar um servidor HTTP local para servir arquivos HTML estáticos
com descoberta automática de portas disponíveis.
"""

import os
import socket
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Optional, List
import logging

from .exceptions import ServidorWebError, RecursoIndisponivelError, CodigosErro
from .models import ConfiguracaoServidorWeb
from .audit_logger import (
    registrar_evento_auditoria,
    TipoEvento,
    NivelSeveridade
)


class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    """
    Handler HTTP customizado para servir arquivos com configurações específicas.
    
    Esta classe estende o SimpleHTTPRequestHandler para adicionar funcionalidades
    como CORS, validação de caminhos e logs em português.
    """
    
    def __init__(self, *args, diretorio_base: str = None, config: ConfiguracaoServidorWeb = None, **kwargs):
        """
        Inicializa o handler HTTP.
        
        Args:
            diretorio_base: Diretório base para servir arquivos
            config: Configuração do servidor web
        """
        self.diretorio_base = diretorio_base or "web_content"
        self.config = config or ConfiguracaoServidorWeb()
        super().__init__(*args, directory=self.diretorio_base, **kwargs)
    
    def end_headers(self):
        """Adiciona headers CORS se habilitado."""
        if self.config.cors_habilitado:
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', ', '.join(self.config.cors_metodos))
            self.send_header('Access-Control-Allow-Headers', ', '.join(self.config.cors_headers))
        
        if self.config.cache_habilitado:
            self.send_header('Cache-Control', f'max-age={self.config.cache_max_idade}')
        
        super().end_headers()
    
    def do_OPTIONS(self):
        """Trata requisições OPTIONS para CORS."""
        if self.config.cors_habilitado:
            self.send_response(200)
            self.end_headers()
        else:
            super().do_OPTIONS()
    
    def log_message(self, format, *args):
        """Personaliza logs do servidor em português."""
        if self.config.modo_debug:
            logging.info(f"[Servidor Web] {format % args}")
    
    def translate_path(self, path):
        """
        Traduz o caminho da URL para caminho do sistema de arquivos.
        
        Adiciona validação de segurança para prevenir directory traversal.
        """
        path = super().translate_path(path)
        
        if self.config.validar_caminhos:
            # Normaliza o caminho e verifica se está dentro do diretório base
            try:
                caminho_normalizado = Path(path).resolve()
                diretorio_base_absoluto = Path(self.diretorio_base).resolve()
                
                # Verifica se o caminho está dentro do diretório base
                caminho_normalizado.relative_to(diretorio_base_absoluto)
                
            except (ValueError, OSError):
                # Caminho inválido ou fora do diretório base
                return None
        
        return path


class WebServerManager:
    """
    Gerenciador do servidor web local para hospedar conteúdo HTML.
    
    Esta classe é responsável por inicializar, gerenciar e parar um servidor
    HTTP local que serve arquivos HTML estáticos. Inclui descoberta automática
    de portas disponíveis e tratamento robusto de erros.
    """
    
    def __init__(self, config: Optional[ConfiguracaoServidorWeb] = None):
        """
        Inicializa o gerenciador do servidor web.
        
        Args:
            config: Configuração do servidor web (usa padrão se None)
        """
        self.config = config or ConfiguracaoServidorWeb()
        self.servidor: Optional[HTTPServer] = None
        self.thread_servidor: Optional[threading.Thread] = None
        self.porta_atual: Optional[int] = None
        self.url_atual: Optional[str] = None
        self._servidor_ativo = False
        self._lock = threading.Lock()
        
        # Configurar logging
        self._configurar_logging()
        
        # Validar configuração
        erros_config = self.config.validar()
        if erros_config:
            raise ServidorWebError(
                f"Configuração inválida: {'; '.join(erros_config)}",
                codigo_erro=CodigosErro.SERVIDOR_FALHA_INICIALIZACAO
            )
    
    def _configurar_logging(self) -> None:
        """Configura o sistema de logging."""
        if self.config.modo_debug:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
    
    def _verificar_porta_disponivel(self, porta: int) -> bool:
        """
        Verifica se uma porta está disponível para uso.
        
        Args:
            porta: Número da porta a verificar
            
        Returns:
            True se a porta estiver disponível, False caso contrário
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                resultado = sock.connect_ex((self.config.host, porta))
                return resultado != 0
        except Exception:
            return False
    
    def _encontrar_porta_disponivel(self) -> int:
        """
        Encontra uma porta disponível para o servidor.
        
        Tenta primeiro a porta preferencial, depois as alternativas,
        e finalmente faz uma busca automática em um range de portas.
        
        Returns:
            Número da porta disponível
            
        Raises:
            RecursoIndisponivelError: Se nenhuma porta estiver disponível
        """
        # Tentar porta preferencial primeiro
        if self._verificar_porta_disponivel(self.config.porta_preferencial):
            if self.config.modo_debug:
                logging.info(f"Usando porta preferencial: {self.config.porta_preferencial}")
            return self.config.porta_preferencial
        
        if self.config.modo_debug:
            logging.warning(f"Porta preferencial {self.config.porta_preferencial} não disponível")
        
        # Tentar portas alternativas
        for porta in self.config.portas_alternativas:
            if self._verificar_porta_disponivel(porta):
                if self.config.modo_debug:
                    logging.info(f"Usando porta alternativa: {porta}")
                return porta
        
        if self.config.modo_debug:
            logging.warning(f"Portas alternativas não disponíveis: {self.config.portas_alternativas}")
        
        # Busca automática em range de portas (último recurso)
        range_inicio = max(8080, self.config.porta_preferencial)
        range_fim = range_inicio + 100  # Tentar 100 portas
        
        if self.config.modo_debug:
            logging.info(f"Iniciando busca automática de porta no range {range_inicio}-{range_fim}")
        
        for porta in range(range_inicio, range_fim):
            if porta not in [self.config.porta_preferencial] + self.config.portas_alternativas:
                if self._verificar_porta_disponivel(porta):
                    if self.config.modo_debug:
                        logging.info(f"Porta encontrada automaticamente: {porta}")
                    return porta
        
        # Se chegou aqui, nenhuma porta está disponível
        portas_tentadas = [self.config.porta_preferencial] + self.config.portas_alternativas
        raise RecursoIndisponivelError(
            f"Nenhuma porta disponível após busca extensiva. "
            f"Portas específicas tentadas: {portas_tentadas}. "
            f"Range automático: {range_inicio}-{range_fim}",
            recurso="porta_rede",
            codigo_erro=CodigosErro.RECURSO_PORTA_INDISPONIVEL
        )
    
    def _criar_handler_factory(self):
        """
        Cria uma factory para o handler HTTP customizado.
        
        Returns:
            Classe handler configurada
        """
        diretorio_base = self.config.diretorio_html
        config = self.config
        
        class ConfiguredHandler(CustomHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, diretorio_base=diretorio_base, config=config, **kwargs)
        
        return ConfiguredHandler
    
    def _executar_servidor(self) -> None:
        """
        Executa o servidor HTTP em thread separada.
        
        Este método é executado em uma thread separada e mantém o servidor
        rodando até que seja solicitada a parada.
        """
        try:
            if self.config.modo_debug:
                logging.info(f"Iniciando servidor na porta {self.porta_atual}")
            
            self.servidor.serve_forever()
            
        except Exception as e:
            if self.config.modo_debug:
                logging.error(f"Erro no servidor: {e}")
            
            with self._lock:
                self._servidor_ativo = False
    
    def iniciar_servidor(self) -> str:
        """
        Inicia o servidor web e retorna a URL.
        
        Returns:
            URL do servidor (ex: "http://localhost:8080")
            
        Raises:
            ServidorWebError: Se não conseguir iniciar o servidor
            RecursoIndisponivelError: Se nenhuma porta estiver disponível
        """
        with self._lock:
            if self._servidor_ativo:
                return self.url_atual
            
            try:
                # Verificar se o diretório HTML existe
                diretorio_html = Path(self.config.diretorio_html)
                if not diretorio_html.exists():
                    if self.config.modo_debug:
                        logging.info(f"Criando diretório HTML: {diretorio_html}")
                    diretorio_html.mkdir(parents=True, exist_ok=True)
                
                # Encontrar porta disponível
                self.porta_atual = self._encontrar_porta_disponivel()
                
                # Criar servidor HTTP
                handler_class = self._criar_handler_factory()
                self.servidor = HTTPServer((self.config.host, self.porta_atual), handler_class)
                
                # Configurar timeout do servidor
                self.servidor.timeout = self.config.timeout_servidor
                
                # Iniciar servidor em thread separada
                self.thread_servidor = threading.Thread(
                    target=self._executar_servidor,
                    daemon=True,
                    name=f"WebServer-{self.porta_atual}"
                )
                self.thread_servidor.start()
                
                # Aguardar um pouco para garantir que o servidor iniciou
                time.sleep(0.1)
                
                # Verificar se o servidor realmente está rodando
                if not self._verificar_servidor_ativo():
                    raise ServidorWebError(
                        "Servidor falhou ao inicializar corretamente",
                        porta=self.porta_atual,
                        codigo_erro=CodigosErro.SERVIDOR_FALHA_INICIALIZACAO
                    )
                
                # Construir URL
                self.url_atual = f"http://{self.config.host}:{self.porta_atual}"
                self._servidor_ativo = True
                
                if self.config.modo_debug:
                    logging.info(f"Servidor iniciado com sucesso: {self.url_atual}")
                
                # Registrar inicialização na auditoria
                registrar_evento_auditoria(
                    tipo_evento=TipoEvento.SERVIDOR_INICIADO,
                    severidade=NivelSeveridade.INFO,
                    componente="WebServerManager",
                    mensagem=f"Servidor web iniciado com sucesso na porta {self.porta_atual}",
                    detalhes={
                        "porta": self.porta_atual,
                        "url": self.url_atual,
                        "host": self.config.host,
                        "diretorio_html": self.config.diretorio_html,
                        "porta_preferencial": self.config.porta_preferencial,
                        "foi_porta_alternativa": self.porta_atual != self.config.porta_preferencial
                    }
                )
                
                return self.url_atual
                
            except (RecursoIndisponivelError, ServidorWebError) as e:
                # Registrar erro na auditoria
                registrar_evento_auditoria(
                    tipo_evento=TipoEvento.SERVIDOR_ERRO,
                    severidade=NivelSeveridade.ERROR,
                    componente="WebServerManager",
                    mensagem=f"Falha ao iniciar servidor: {str(e)}",
                    detalhes={
                        "porta_tentada": self.porta_atual,
                        "tipo_erro": type(e).__name__,
                        "codigo_erro": getattr(e, 'codigo_erro', None),
                        "portas_alternativas_tentadas": self.config.portas_alternativas
                    }
                )
                # Re-raise exceções conhecidas
                raise
                
            except Exception as e:
                # Registrar erro inesperado na auditoria
                registrar_evento_auditoria(
                    tipo_evento=TipoEvento.SERVIDOR_ERRO,
                    severidade=NivelSeveridade.CRITICAL,
                    componente="WebServerManager",
                    mensagem=f"Erro inesperado ao iniciar servidor: {str(e)}",
                    detalhes={
                        "porta_tentada": self.porta_atual,
                        "tipo_erro": type(e).__name__,
                        "stack_trace": str(e)
                    }
                )
                
                # Capturar outras exceções e converter para ServidorWebError
                raise ServidorWebError(
                    f"Erro inesperado ao iniciar servidor: {str(e)}",
                    porta=self.porta_atual,
                    codigo_erro=CodigosErro.SERVIDOR_FALHA_INICIALIZACAO
                ) from e
    
    def _verificar_servidor_ativo(self) -> bool:
        """
        Verifica se o servidor está realmente ativo e respondendo.
        
        Returns:
            True se o servidor estiver ativo, False caso contrário
        """
        if not self.servidor or not self.thread_servidor:
            return False
        
        # Verificar se a thread está viva
        if not self.thread_servidor.is_alive():
            return False
        
        # Tentar conectar na porta para verificar se está respondendo
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                resultado = sock.connect_ex((self.config.host, self.porta_atual))
                return resultado == 0
        except Exception:
            return False
    
    def parar_servidor(self) -> None:
        """
        Para o servidor web graciosamente.
        
        Raises:
            ServidorWebError: Se houver erro ao parar o servidor
        """
        with self._lock:
            if not self._servidor_ativo:
                return
            
            try:
                if self.config.modo_debug:
                    logging.info("Parando servidor web...")
                
                # Parar o servidor
                if self.servidor:
                    self.servidor.shutdown()
                    self.servidor.server_close()
                
                # Aguardar a thread terminar
                if self.thread_servidor and self.thread_servidor.is_alive():
                    self.thread_servidor.join(timeout=5)
                    
                    # Se a thread não terminou, forçar
                    if self.thread_servidor.is_alive():
                        if self.config.modo_debug:
                            logging.warning("Thread do servidor não terminou graciosamente")
                
                # Limpar estado
                self.servidor = None
                self.thread_servidor = None
                self.porta_atual = None
                self.url_atual = None
                self._servidor_ativo = False
                
                if self.config.modo_debug:
                    logging.info("Servidor parado com sucesso")
                
                # Registrar parada na auditoria
                registrar_evento_auditoria(
                    tipo_evento=TipoEvento.SERVIDOR_PARADO,
                    severidade=NivelSeveridade.INFO,
                    componente="WebServerManager",
                    mensagem="Servidor web parado com sucesso",
                    detalhes={
                        "porta": self.porta_atual,
                        "url": self.url_atual,
                        "tempo_ativo": "calculado_externamente"  # Poderia calcular se mantivesse timestamp de início
                    }
                )
                
            except Exception as e:
                raise ServidorWebError(
                    f"Erro ao parar servidor: {str(e)}",
                    porta=self.porta_atual,
                    codigo_erro=CodigosErro.SERVIDOR_FALHA_PARADA
                ) from e
    
    def esta_ativo(self) -> bool:
        """
        Verifica se o servidor está ativo.
        
        Returns:
            True se o servidor estiver ativo, False caso contrário
        """
        with self._lock:
            if not self._servidor_ativo:
                return False
            
            # Verificação mais robusta
            return self._verificar_servidor_ativo()
    
    def obter_url(self) -> str:
        """
        Retorna a URL atual do servidor.
        
        Returns:
            URL do servidor ou string vazia se não estiver ativo
            
        Raises:
            ServidorWebError: Se o servidor não estiver ativo
        """
        with self._lock:
            if not self._servidor_ativo or not self.url_atual:
                raise ServidorWebError(
                    "Servidor não está ativo",
                    codigo_erro=CodigosErro.SERVIDOR_NAO_RESPONSIVO
                )
            
            return self.url_atual
    
    def obter_porta(self) -> Optional[int]:
        """
        Retorna a porta atual do servidor.
        
        Returns:
            Número da porta ou None se não estiver ativo
        """
        with self._lock:
            return self.porta_atual if self._servidor_ativo else None
    
    def obter_estatisticas(self) -> dict:
        """
        Retorna estatísticas do servidor.
        
        Returns:
            Dicionário com estatísticas do servidor
        """
        with self._lock:
            return {
                "ativo": self._servidor_ativo,
                "porta": self.porta_atual,
                "url": self.url_atual,
                "host": self.config.host,
                "diretorio_html": self.config.diretorio_html,
                "thread_ativa": self.thread_servidor.is_alive() if self.thread_servidor else False,
                "modo_debug": self.config.modo_debug
            }
    
    def __enter__(self):
        """Suporte para context manager."""
        self.iniciar_servidor()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Suporte para context manager."""
        self.parar_servidor()
    
    def __del__(self):
        """Destructor para garantir limpeza de recursos."""
        try:
            if self._servidor_ativo:
                self.parar_servidor()
        except Exception:
            # Ignorar erros no destructor
            pass