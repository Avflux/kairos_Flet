"""
Sistema de fallback para quando o WebView não estiver disponível.

Este módulo implementa alternativas quando o WebView não pode ser usado,
incluindo modo texto, notificações e logs detalhados em português.
"""

import logging
import flet as ft
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from dataclasses import dataclass

from .exceptions import WebViewError, CodigosErro


@dataclass
class ConfiguracaoFallback:
    """Configuração do sistema de fallback."""
    
    mostrar_notificacoes: bool = True
    salvar_logs_arquivo: bool = True
    arquivo_log: str = "web_server_fallback.log"
    modo_texto_habilitado: bool = True
    intervalo_atualizacao_segundos: int = 5


class FallbackHandler:
    """
    Manipulador de fallback para quando WebView não está disponível.
    
    Fornece alternativas como modo texto, notificações e logs
    quando o WebView não pode ser usado.
    """
    
    def __init__(
        self,
        page: ft.Page,
        config: Optional[ConfiguracaoFallback] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Inicializa o manipulador de fallback.
        
        Args:
            page: Instância da página Flet
            config: Configuração do fallback
            logger: Logger personalizado
        """
        self.page = page
        self.config = config or ConfiguracaoFallback()
        self.logger = logger or self._configurar_logger()
        
        # Estado interno
        self._ativo = False
        self._dados_atuais: Dict[str, Any] = {}
        self._ultima_atualizacao: Optional[datetime] = None
        self._callbacks_atualizacao: list[Callable] = []
        
        # Componentes UI
        self._container_fallback: Optional[ft.Container] = None
        self._texto_status: Optional[ft.Text] = None
        self._lista_dados: Optional[ft.Column] = None
        
        self.logger.info("FallbackHandler inicializado")
    
    def _configurar_logger(self) -> logging.Logger:
        """Configura logger para o fallback."""
        logger = logging.getLogger(f"{__name__}.FallbackHandler")
        
        if not logger.handlers:
            # Handler para console
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - [FALLBACK] %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # Handler para arquivo se configurado
            if self.config.salvar_logs_arquivo:
                try:
                    file_handler = logging.FileHandler(
                        self.config.arquivo_log, 
                        encoding='utf-8'
                    )
                    file_formatter = logging.Formatter(
                        '%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S'
                    )
                    file_handler.setFormatter(file_formatter)
                    logger.addHandler(file_handler)
                except Exception as e:
                    logger.warning(f"Não foi possível configurar log em arquivo: {e}")
            
            logger.setLevel(logging.INFO)
        
        return logger
    
    def ativar_fallback(self, motivo: str = "WebView indisponível") -> ft.Container:
        """
        Ativa o modo fallback e retorna o componente de substituição.
        
        Args:
            motivo: Motivo para ativação do fallback
            
        Returns:
            Container com interface de fallback
        """
        self._ativo = True
        self.logger.warning(f"Modo fallback ativado: {motivo}")
        
        # Mostrar notificação se configurado
        if self.config.mostrar_notificacoes and self.page:
            self._mostrar_notificacao_fallback(motivo)
        
        # Criar interface de fallback
        self._criar_interface_fallback(motivo)
        
        return self._container_fallback
    
    def _mostrar_notificacao_fallback(self, motivo: str) -> None:
        """Mostra notificação sobre ativação do fallback."""
        try:
            snack_bar = ft.SnackBar(
                content=ft.Row(
                    controls=[
                        ft.Icon(
                            name=ft.Icons.WARNING_AMBER,
                            color=ft.Colors.ORANGE_400
                        ),
                        ft.Text(
                            f"Modo alternativo ativado: {motivo}",
                            color=ft.Colors.WHITE
                        )
                    ]
                ),
                bgcolor=ft.Colors.ORANGE_600,
                duration=5000
            )
            
            self.page.overlay.append(snack_bar)
            snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            self.logger.warning(f"Erro ao mostrar notificação: {e}")
    
    def _criar_interface_fallback(self, motivo: str) -> None:
        """Cria a interface de fallback."""
        # Texto de status
        self._texto_status = ft.Text(
            f"WebView não disponível: {motivo}",
            size=16,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.ORANGE_600,
            text_align=ft.TextAlign.CENTER
        )
        
        # Lista para exibir dados
        self._lista_dados = ft.Column(
            controls=[],
            spacing=8,
            scroll=ft.ScrollMode.AUTO
        )
        
        # Container principal
        self._container_fallback = ft.Container(
            content=ft.Column(
                controls=[
                    # Cabeçalho
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(
                                    name=ft.Icons.INFO_OUTLINE,
                                    color=ft.Colors.BLUE_400,
                                    size=24
                                ),
                                ft.Text(
                                    "Modo Alternativo - Visualização de Dados",
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.BLUE_600
                                )
                            ],
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        padding=ft.padding.all(16),
                        bgcolor=ft.Colors.BLUE_50,
                        border_radius=8
                    ),
                    
                    # Status
                    ft.Container(
                        content=self._texto_status,
                        padding=ft.padding.all(12),
                        bgcolor=ft.Colors.ORANGE_50,
                        border_radius=8,
                        border=ft.border.all(1, ft.Colors.ORANGE_200)
                    ),
                    
                    # Dados
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    "Dados Sincronizados:",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.GREY_700
                                ),
                                self._lista_dados
                            ]
                        ),
                        padding=ft.padding.all(16),
                        bgcolor=ft.Colors.GREY_50,
                        border_radius=8,
                        expand=True
                    ),
                    
                    # Rodapé com informações
                    ft.Container(
                        content=ft.Text(
                            f"Última atualização: {datetime.now().strftime('%H:%M:%S')}",
                            size=12,
                            color=ft.Colors.GREY_600,
                            text_align=ft.TextAlign.CENTER
                        ),
                        padding=ft.padding.all(8)
                    )
                ],
                spacing=12
            ),
            padding=ft.padding.all(16),
            expand=True,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_300),
            bgcolor=ft.Colors.WHITE
        )
    
    def atualizar_dados(self, dados: Dict[str, Any]) -> None:
        """
        Atualiza os dados exibidos no modo fallback.
        
        Args:
            dados: Novos dados para exibir
        """
        if not self._ativo:
            return
        
        self._dados_atuais = dados.copy()
        self._ultima_atualizacao = datetime.now()
        
        self.logger.debug(f"Atualizando dados no fallback: {len(dados)} chaves")
        
        # Atualizar interface
        self._atualizar_interface_dados()
        
        # Notificar callbacks
        for callback in self._callbacks_atualizacao:
            try:
                callback(dados)
            except Exception as e:
                self.logger.warning(f"Erro em callback de atualização: {e}")
    
    def _atualizar_interface_dados(self) -> None:
        """Atualiza a interface com os dados atuais."""
        if not self._lista_dados or not self._dados_atuais:
            return
        
        try:
            # Limpar lista atual
            self._lista_dados.controls.clear()
            
            # Adicionar dados formatados
            for chave, valor in self._dados_atuais.items():
                self._adicionar_item_dado(chave, valor)
            
            # Atualizar timestamp
            if self._container_fallback and len(self._container_fallback.content.controls) > 3:
                rodape = self._container_fallback.content.controls[3]
                if hasattr(rodape, 'content') and hasattr(rodape.content, 'value'):
                    rodape.content.value = f"Última atualização: {self._ultima_atualizacao.strftime('%H:%M:%S')}"
            
            # Atualizar página
            if self.page:
                self.page.update()
                
        except Exception as e:
            self.logger.error(f"Erro ao atualizar interface de dados: {e}")
    
    def _adicionar_item_dado(self, chave: str, valor: Any) -> None:
        """Adiciona um item de dado à lista."""
        try:
            # Formatar valor
            if isinstance(valor, dict):
                valor_str = self._formatar_dict(valor)
            elif isinstance(valor, list):
                valor_str = f"Lista com {len(valor)} itens"
            elif isinstance(valor, bool):
                valor_str = "Sim" if valor else "Não"
            elif isinstance(valor, (int, float)):
                valor_str = str(valor)
            else:
                valor_str = str(valor)
            
            # Criar item visual
            item = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(
                            f"{chave}:",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_700,
                            width=150
                        ),
                        ft.Text(
                            valor_str,
                            size=14,
                            color=ft.Colors.GREY_800,
                            expand=True
                        )
                    ]
                ),
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                bgcolor=ft.Colors.WHITE,
                border_radius=4,
                border=ft.border.all(1, ft.Colors.GREY_200)
            )
            
            self._lista_dados.controls.append(item)
            
        except Exception as e:
            self.logger.warning(f"Erro ao adicionar item de dado '{chave}': {e}")
    
    def _formatar_dict(self, dados: dict, max_items: int = 3) -> str:
        """Formata um dicionário para exibição."""
        if not dados:
            return "Vazio"
        
        items = list(dados.items())[:max_items]
        formatted_items = []
        
        for k, v in items:
            if isinstance(v, (dict, list)):
                formatted_items.append(f"{k}: {type(v).__name__}")
            else:
                formatted_items.append(f"{k}: {str(v)[:30]}")
        
        result = ", ".join(formatted_items)
        if len(dados) > max_items:
            result += f" ... (+{len(dados) - max_items} mais)"
        
        return result
    
    def registrar_callback_atualizacao(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Registra callback para atualizações de dados.
        
        Args:
            callback: Função a ser chamada quando dados forem atualizados
        """
        if callable(callback):
            self._callbacks_atualizacao.append(callback)
            self.logger.debug("Callback de atualização registrado")
    
    def desativar_fallback(self) -> None:
        """Desativa o modo fallback."""
        if self._ativo:
            self._ativo = False
            self.logger.info("Modo fallback desativado")
            
            # Mostrar notificação de recuperação
            if self.config.mostrar_notificacoes and self.page:
                self._mostrar_notificacao_recuperacao()
    
    def _mostrar_notificacao_recuperacao(self) -> None:
        """Mostra notificação sobre recuperação do WebView."""
        try:
            snack_bar = ft.SnackBar(
                content=ft.Row(
                    controls=[
                        ft.Icon(
                            name=ft.Icons.CHECK_CIRCLE,
                            color=ft.Colors.GREEN_400
                        ),
                        ft.Text(
                            "WebView recuperado com sucesso!",
                            color=ft.Colors.WHITE
                        )
                    ]
                ),
                bgcolor=ft.Colors.GREEN_600,
                duration=3000
            )
            
            self.page.overlay.append(snack_bar)
            snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            self.logger.warning(f"Erro ao mostrar notificação de recuperação: {e}")
    
    @property
    def esta_ativo(self) -> bool:
        """Retorna se o fallback está ativo."""
        return self._ativo
    
    @property
    def dados_atuais(self) -> Dict[str, Any]:
        """Retorna os dados atuais."""
        return self._dados_atuais.copy()
    
    def obter_status(self) -> Dict[str, Any]:
        """Retorna status do fallback."""
        return {
            "ativo": self._ativo,
            "ultima_atualizacao": self._ultima_atualizacao.isoformat() if self._ultima_atualizacao else None,
            "total_dados": len(self._dados_atuais),
            "callbacks_registrados": len(self._callbacks_atualizacao)
        }