"""
Componente WebView para integração com servidor web local.

Este módulo implementa o WebViewComponent que encapsula o WebView do Flet
para exibição de conteúdo HTML servido pelo servidor web integrado.
Inclui tratamento de erros, execução de JavaScript e adaptação responsiva.
"""

import logging
import flet as ft
from typing import Optional, Callable, Dict, Any
from datetime import datetime
import asyncio
import json

from services.web_server.exceptions import (
    WebViewError, 
    CodigosErro,
    RecursoIndisponivelError
)
from services.web_server.fallback_handler import FallbackHandler, ConfiguracaoFallback


class WebViewComponent(ft.Container):
    """
    Componente que encapsula o WebView para exibição de conteúdo HTML.
    
    Este componente integra o WebView do Flet com o servidor web local,
    fornecendo funcionalidades para carregamento de conteúdo, execução
    de JavaScript, tratamento de erros e adaptação responsiva.
    """
    
    def __init__(
        self,
        page: ft.Page,
        url_servidor: str,
        largura: Optional[int] = None,
        altura: Optional[int] = None,
        on_page_started: Optional[Callable] = None,
        on_page_ended: Optional[Callable] = None,
        on_web_resource_error: Optional[Callable] = None,
        timeout_carregamento: int = 30,
        modo_debug: bool = False,
        habilitar_fallback: bool = True,
        config_fallback: Optional[ConfiguracaoFallback] = None
    ):
        """
        Inicializa o componente WebView.
        
        Args:
            page: Instância da página Flet
            url_servidor: URL do servidor web local
            largura: Largura do WebView (opcional)
            altura: Altura do WebView (opcional)
            on_page_started: Callback quando página inicia carregamento
            on_page_ended: Callback quando página termina carregamento
            on_web_resource_error: Callback para erros de recursos web
            timeout_carregamento: Timeout para carregamento em segundos
            modo_debug: Habilita logs detalhados
        """
        super().__init__()
        
        self.page = page
        self._url_servidor = url_servidor
        self._largura = largura
        self._altura = altura
        self._timeout_carregamento = timeout_carregamento
        self._modo_debug = modo_debug
        self._habilitar_fallback = habilitar_fallback
        
        # Configurar logging
        self._logger = logging.getLogger(__name__)
        if modo_debug:
            self._logger.setLevel(logging.DEBUG)
        
        # Estado interno
        self._webview: Optional[ft.WebView] = None
        self._carregando = False
        self._erro_atual: Optional[str] = None
        self._ultima_atualizacao = datetime.now()
        self._webview_disponivel = True
        self._tentativas_recuperacao = 0
        self._max_tentativas_recuperacao = 3
        
        # Callbacks
        self._on_page_started = on_page_started
        self._on_page_ended = on_page_ended
        self._on_web_resource_error = on_web_resource_error
        
        # Componentes de UI
        self._container_erro: Optional[ft.Container] = None
        self._container_carregamento: Optional[ft.Container] = None
        self._indicador_carregamento: Optional[ft.ProgressRing] = None
        
        # Sistema de fallback
        self._fallback_handler: Optional[FallbackHandler] = None
        if self._habilitar_fallback:
            self._fallback_handler = FallbackHandler(
                page=page,
                config=config_fallback,
                logger=self._logger
            )
        
        # Inicializar componente
        self._inicializar_componente()
    
    def _inicializar_componente(self) -> None:
        """Inicializa os componentes internos do WebView."""
        try:
            self._logger.debug("Inicializando WebViewComponent")
            
            # Criar indicador de carregamento
            self._indicador_carregamento = ft.ProgressRing(
                width=50,
                height=50,
                stroke_width=4,
                color=ft.Colors.BLUE_400
            )
            
            # Criar container de erro
            self._container_erro = self._criar_container_erro()
            
            # Criar WebView
            self._criar_webview()
            
            # Configurar layout inicial
            self._configurar_layout()
            
            self._logger.debug("WebViewComponent inicializado com sucesso")
            
        except Exception as e:
            self._logger.error(f"Erro ao inicializar WebViewComponent: {e}")
            raise WebViewError(
                f"Falha na inicialização do WebView: {str(e)}",
                url=self._url_servidor,
                codigo_erro=CodigosErro.WEBVIEW_FALHA_CARREGAMENTO
            )
    
    def _criar_webview(self) -> None:
        """Cria e configura o componente WebView do Flet."""
        try:
            self._webview = ft.WebView(
                url=self._url_servidor,
                width=self._largura,
                height=self._altura,
                on_page_started=self._handle_page_started,
                on_page_ended=self._handle_page_ended,
                on_web_resource_error=self._handle_web_resource_error,
                prevent_link=False
            )
            
            self._logger.debug(f"WebView criado para URL: {self._url_servidor}")
            
        except Exception as e:
            self._logger.error(f"Erro ao criar WebView: {e}")
            raise WebViewError(
                f"Não foi possível criar o WebView: {str(e)}",
                url=self._url_servidor,
                codigo_erro=CodigosErro.WEBVIEW_FALHA_CARREGAMENTO
            )
    
    def _criar_container_erro(self) -> ft.Container:
        """Cria o container para exibição de erros."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        name=ft.Icons.ERROR_OUTLINE,
                        size=48,
                        color=ft.Colors.RED_400
                    ),
                    ft.Text(
                        "Erro ao carregar conteúdo",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_400,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        "Verifique a conexão e tente novamente",
                        size=14,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.ElevatedButton(
                        text="Tentar Novamente",
                        icon=ft.Icons.REFRESH,
                        on_click=lambda _: self.recarregar(),
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.BLUE_400
                        )
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16
            ),
            alignment=ft.alignment.center,
            padding=20,
            visible=False
        )
    
    def _configurar_layout(self) -> None:
        """Configura o layout do componente com referências diretas aos containers."""
        # Criar container de carregamento com referência direta (OCULTO)
        self._container_carregamento = ft.Container(
            content=ft.Column(
                controls=[
                    self._indicador_carregamento,
                    ft.Text(
                        "Carregando...",
                        size=14,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8
            ),
            alignment=ft.alignment.center,
            visible=False  # OCULTO - não mostra o indicador de carregamento
        )
        
        # Stack para sobrepor componentes
        stack_content = ft.Stack(
            controls=[
                # WebView (fundo)
                self._webview,
                # Container de carregamento (centro) - com referência direta
                self._container_carregamento,
                # Container de erro (sobreposto)
                self._container_erro
            ]
        )
        
        # Configurar container principal
        self.content = stack_content
        self.expand = True
        self.border_radius = 8
        self.border = ft.border.all(1, ft.Colors.GREY_300)
        self.bgcolor = ft.Colors.WHITE
    
    def _handle_page_started(self, e) -> None:
        """Manipula o evento de início de carregamento da página."""
        self._logger.debug("Carregamento da página iniciado")
        self._carregando = True
        self._erro_atual = None
        
        # NÃO mostrar indicador de carregamento - manter oculto
        if hasattr(self, '_container_carregamento') and self._container_carregamento:
            self._container_carregamento.visible = False  # SEMPRE OCULTO
        
        # Esconder container de erro
        if self._container_erro:
            self._container_erro.visible = False
        
        # Atualizar página
        if self.page:
            self.page.update()
        
        # Chamar callback personalizado
        if self._on_page_started:
            try:
                self._on_page_started(e)
            except Exception as ex:
                self._logger.warning(f"Erro no callback page_started: {ex}")
    
    def _handle_page_ended(self, e) -> None:
        """Manipula o evento de fim de carregamento da página."""
        self._logger.debug("Carregamento da página concluído")
        self._carregando = False
        self._ultima_atualizacao = datetime.now()
        
        # Esconder indicador de carregamento usando referência direta
        if hasattr(self, '_container_carregamento') and self._container_carregamento:
            self._container_carregamento.visible = False
        
        # Atualizar página imediatamente
        if self.page:
            self.page.update()
        
        # Chamar callback personalizado
        if self._on_page_ended:
            try:
                self._on_page_ended(e)
            except Exception as ex:
                self._logger.warning(f"Erro no callback page_ended: {ex}")
    
    def _handle_web_resource_error(self, e) -> None:
        """Manipula erros de recursos web com recuperação automática."""
        erro_msg = f"Erro ao carregar recurso web: {getattr(e, 'description', 'Erro desconhecido')}"
        self._logger.error(erro_msg)
        self._erro_atual = erro_msg
        self._carregando = False
        
        # Incrementar tentativas de recuperação
        self._tentativas_recuperacao += 1
        
        # Esconder indicador de carregamento usando referência direta
        if hasattr(self, '_container_carregamento') and self._container_carregamento:
            self._container_carregamento.visible = False
        
        # Verificar se deve ativar fallback
        if (self._tentativas_recuperacao >= self._max_tentativas_recuperacao and 
            self._habilitar_fallback and self._fallback_handler):
            self._ativar_modo_fallback(f"Múltiplas falhas de carregamento: {erro_msg}")
        else:
            # Mostrar container de erro com opção de recuperação
            self._mostrar_erro_com_recuperacao(erro_msg)
            
            # Tentar recuperação automática se ainda há tentativas
            if self._tentativas_recuperacao < self._max_tentativas_recuperacao:
                self._agendar_recuperacao_automatica()
        
        # Atualizar página imediatamente
        if self.page:
            self.page.update()
        
        # Chamar callback personalizado
        if self._on_web_resource_error:
            try:
                self._on_web_resource_error(e)
            except Exception as ex:
                self._logger.warning(f"Erro no callback web_resource_error: {ex}")
    
    def atualizar_url(self, nova_url: str) -> None:
        """
        Atualiza a URL do WebView.
        
        Args:
            nova_url: Nova URL para carregar
            
        Raises:
            WebViewError: Se a URL for inválida ou houver erro no carregamento
        """
        try:
            if not nova_url or not nova_url.strip():
                raise WebViewError(
                    "URL não pode estar vazia",
                    codigo_erro=CodigosErro.WEBVIEW_URL_INVALIDA
                )
            
            self._logger.debug(f"Atualizando URL do WebView: {nova_url}")
            
            self._url_servidor = nova_url.strip()
            
            if self._webview:
                self._webview.url = self._url_servidor
                if self.page:
                    self.page.update()
            
            self._logger.debug("URL do WebView atualizada com sucesso")
            
        except Exception as e:
            self._logger.error(f"Erro ao atualizar URL: {e}")
            raise WebViewError(
                f"Falha ao atualizar URL do WebView: {str(e)}",
                url=nova_url,
                codigo_erro=CodigosErro.WEBVIEW_URL_INVALIDA
            )
    
    def recarregar(self) -> None:
        """Recarrega o conteúdo do WebView."""
        try:
            self._logger.debug("Recarregando WebView")
            
            if not self._webview:
                raise WebViewError(
                    "WebView não foi inicializado",
                    codigo_erro=CodigosErro.WEBVIEW_FALHA_CARREGAMENTO
                )
            
            # Resetar estado de erro
            self._erro_atual = None
            
            # Esconder container de erro
            if self._container_erro:
                self._container_erro.visible = False
            
            # NÃO mostrar indicador de carregamento - manter oculto
            if hasattr(self, '_container_carregamento') and self._container_carregamento:
                self._container_carregamento.visible = False  # SEMPRE OCULTO
            
            # Recarregar WebView
            self._webview.url = self._url_servidor
            
            if self.page:
                self.page.update()
            
            self._logger.debug("WebView recarregado com sucesso")
            
        except Exception as e:
            self._logger.error(f"Erro ao recarregar WebView: {e}")
            raise WebViewError(
                f"Falha ao recarregar WebView: {str(e)}",
                url=self._url_servidor,
                codigo_erro=CodigosErro.WEBVIEW_FALHA_CARREGAMENTO
            )
    
    def executar_javascript(self, codigo: str) -> None:
        """
        Executa código JavaScript no WebView.
        
        Args:
            codigo: Código JavaScript para executar
            
        Raises:
            WebViewError: Se houver erro na execução do JavaScript
        """
        try:
            if not codigo or not codigo.strip():
                raise WebViewError(
                    "Código JavaScript não pode estar vazio",
                    codigo_erro=CodigosErro.WEBVIEW_ERRO_JAVASCRIPT
                )
            
            if not self._webview:
                raise WebViewError(
                    "WebView não foi inicializado",
                    codigo_erro=CodigosErro.WEBVIEW_FALHA_CARREGAMENTO
                )
            
            self._logger.debug(f"Executando JavaScript: {codigo[:100]}...")
            
            # Executar JavaScript no WebView (Flet usa run_javascript)
            if hasattr(self._webview, 'run_javascript'):
                self._webview.run_javascript(codigo.strip())
            elif hasattr(self._webview, 'evaluate_javascript'):
                self._webview.evaluate_javascript(codigo.strip())
            else:
                # Fallback: log o código que seria executado
                self._logger.debug(f"JavaScript que seria executado: {codigo.strip()}")
            
            self._logger.debug("JavaScript executado com sucesso")
            
        except Exception as e:
            self._logger.error(f"Erro ao executar JavaScript: {e}")
            raise WebViewError(
                f"Falha na execução do JavaScript: {str(e)}",
                codigo_erro=CodigosErro.WEBVIEW_ERRO_JAVASCRIPT
            )
    
    def notificar_atualizacao_dados(self, dados: Dict[str, Any]) -> None:
        """
        Notifica o WebView sobre atualização de dados.
        
        Args:
            dados: Dados atualizados para sincronizar
        """
        try:
            # Converter dados para JSON
            dados_json = json.dumps(dados, ensure_ascii=False, indent=2)
            
            # Criar código JavaScript para atualizar dados
            js_code = f"""
            if (typeof window.atualizarDados === 'function') {{
                window.atualizarDados({dados_json});
            }} else if (typeof window.onDataUpdate === 'function') {{
                window.onDataUpdate({dados_json});
            }} else {{
                console.log('Dados atualizados:', {dados_json});
            }}
            """
            
            # Executar JavaScript
            self.executar_javascript(js_code)
            
            self._logger.debug("Notificação de atualização de dados enviada")
            
        except Exception as e:
            self._logger.warning(f"Erro ao notificar atualização de dados: {e}")
    
    def definir_tamanho(self, largura: Optional[int] = None, altura: Optional[int] = None) -> None:
        """
        Define o tamanho do WebView.
        
        Args:
            largura: Nova largura (opcional)
            altura: Nova altura (opcional)
        """
        try:
            if largura is not None:
                self._largura = largura
                if self._webview:
                    self._webview.width = largura
            
            if altura is not None:
                self._altura = altura
                if self._webview:
                    self._webview.height = altura
            
            if self.page and (largura is not None or altura is not None):
                self.page.update()
            
            self._logger.debug(f"Tamanho do WebView atualizado: {largura}x{altura}")
            
        except Exception as e:
            self._logger.warning(f"Erro ao definir tamanho do WebView: {e}")
    
    @property
    def url_atual(self) -> str:
        """Retorna a URL atual do WebView."""
        return self._url_servidor
    
    @property
    def esta_carregando(self) -> bool:
        """Retorna se o WebView está carregando."""
        return self._carregando
    
    @property
    def tem_erro(self) -> bool:
        """Retorna se há erro no WebView."""
        return self._erro_atual is not None
    
    @property
    def erro_atual(self) -> Optional[str]:
        """Retorna o erro atual, se houver."""
        return self._erro_atual
    
    @property
    def ultima_atualizacao(self) -> datetime:
        """Retorna o timestamp da última atualização."""
        return self._ultima_atualizacao
    
    def _mostrar_erro_com_recuperacao(self, erro_msg: str) -> None:
        """Mostra erro com opções de recuperação."""
        if self._container_erro:
            self._container_erro.visible = True
            
            # Atualizar mensagem de erro específica
            if len(self._container_erro.content.controls) > 2:
                self._container_erro.content.controls[2].value = f"{erro_msg} (Tentativa {self._tentativas_recuperacao}/{self._max_tentativas_recuperacao})"
            
            # Adicionar informação sobre recuperação automática
            if len(self._container_erro.content.controls) > 3:
                btn_container = self._container_erro.content.controls[3]
                if hasattr(btn_container, 'text'):
                    btn_container.text = f"Recuperação automática em andamento... ({self._tentativas_recuperacao}/{self._max_tentativas_recuperacao})"
    
    def _agendar_recuperacao_automatica(self) -> None:
        """Agenda tentativa de recuperação automática."""
        delay = min(5 * self._tentativas_recuperacao, 30)  # Backoff até 30 segundos
        
        self._logger.info(f"Agendando recuperação automática em {delay} segundos (tentativa {self._tentativas_recuperacao})")
        
        # Usar threading para não bloquear a UI
        import threading
        def recuperar():
            import time
            time.sleep(delay)
            try:
                self._logger.info("Executando recuperação automática do WebView")
                self.recarregar()
            except Exception as e:
                self._logger.error(f"Erro na recuperação automática: {e}")
        
        thread = threading.Thread(target=recuperar, daemon=True)
        thread.start()
    
    def _ativar_modo_fallback(self, motivo: str) -> None:
        """Ativa o modo fallback quando WebView falha."""
        if not self._fallback_handler:
            self._logger.warning("Fallback handler não disponível")
            return
        
        self._logger.warning(f"Ativando modo fallback: {motivo}")
        self._webview_disponivel = False
        
        try:
            # Ativar fallback e substituir conteúdo
            container_fallback = self._fallback_handler.ativar_fallback(motivo)
            
            # Substituir conteúdo do componente
            self.content = container_fallback
            
            if self.page:
                self.page.update()
                
        except Exception as e:
            self._logger.error(f"Erro ao ativar modo fallback: {e}")
    
    def tentar_recuperar_webview(self) -> bool:
        """
        Tenta recuperar o WebView do modo fallback.
        
        Returns:
            True se a recuperação foi bem-sucedida
        """
        if self._webview_disponivel:
            return True
        
        try:
            self._logger.info("Tentando recuperar WebView do modo fallback")
            
            # Resetar estado
            self._tentativas_recuperacao = 0
            self._erro_atual = None
            
            # Recriar WebView
            self._criar_webview()
            self._configurar_layout()
            
            # Desativar fallback
            if self._fallback_handler:
                self._fallback_handler.desativar_fallback()
            
            self._webview_disponivel = True
            
            if self.page:
                self.page.update()
            
            self._logger.info("WebView recuperado com sucesso")
            return True
            
        except Exception as e:
            self._logger.error(f"Erro ao recuperar WebView: {e}")
            return False
    
    def atualizar_dados_fallback(self, dados: Dict[str, Any]) -> None:
        """
        Atualiza dados no modo fallback.
        
        Args:
            dados: Dados para atualizar no fallback
        """
        if self._fallback_handler and not self._webview_disponivel:
            self._fallback_handler.atualizar_dados(dados)
    
    def carregar_pagina_erro(self, tipo_erro: str, detalhes: Optional[str] = None) -> None:
        """
        Carrega página de erro personalizada.
        
        Args:
            tipo_erro: Tipo do erro (servidor, carregamento, sincronizacao)
            detalhes: Detalhes adicionais do erro
        """
        try:
            # Mapear tipos de erro para páginas
            paginas_erro = {
                'servidor': 'erro_servidor.html',
                'carregamento': 'erro_carregamento.html',
                'sincronizacao': 'erro_sincronizacao.html'
            }
            
            pagina = paginas_erro.get(tipo_erro, 'erro_carregamento.html')
            
            # Construir URL com parâmetros
            base_url = self._url_servidor.rsplit('/', 1)[0] if '/' in self._url_servidor else self._url_servidor
            url_erro = f"{base_url}/{pagina}"
            
            if detalhes:
                import urllib.parse
                url_erro += f"?erro={urllib.parse.quote(detalhes)}&codigo={tipo_erro.upper()}"
            
            self._logger.info(f"Carregando página de erro: {url_erro}")
            self.atualizar_url(url_erro)
            
        except Exception as e:
            self._logger.error(f"Erro ao carregar página de erro: {e}")
    
    @property
    def webview_disponivel(self) -> bool:
        """Retorna se o WebView está disponível."""
        return self._webview_disponivel
    
    @property
    def modo_fallback_ativo(self) -> bool:
        """Retorna se o modo fallback está ativo."""
        return self._fallback_handler and self._fallback_handler.esta_ativo if self._fallback_handler else False
    
    @property
    def tentativas_recuperacao(self) -> int:
        """Retorna o número de tentativas de recuperação."""
        return self._tentativas_recuperacao
    
    def obter_status(self) -> Dict[str, Any]:
        """
        Obtém o status atual do WebView.
        
        Returns:
            Dicionário com informações de status
        """
        status = {
            "url": self._url_servidor,
            "carregando": self._carregando,
            "tem_erro": self.tem_erro,
            "erro": self._erro_atual,
            "ultima_atualizacao": self._ultima_atualizacao.isoformat(),
            "largura": self._largura,
            "altura": self._altura,
            "modo_debug": self._modo_debug,
            "webview_disponivel": self._webview_disponivel,
            "tentativas_recuperacao": self._tentativas_recuperacao,
            "max_tentativas": self._max_tentativas_recuperacao,
            "fallback_habilitado": self._habilitar_fallback,
            "modo_fallback_ativo": self.modo_fallback_ativo
        }
        
        # Adicionar status do fallback se disponível
        if self._fallback_handler:
            status["fallback_status"] = self._fallback_handler.obter_status()
        
        return status