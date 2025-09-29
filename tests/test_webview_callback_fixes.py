"""
Testes para as correções do sistema de callbacks e indicador de carregamento do WebView.

Este módulo testa as correções implementadas para resolver problemas com:
- Indicador de carregamento infinito
- Callbacks de carregamento não funcionando corretamente
- Gerenciamento inadequado de estado de erro
"""

import pytest
import flet as ft
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import time

from views.components.webview_component import WebViewComponent


class TestWebViewCallbackFixes:
    """Testes para as correções dos callbacks do WebView."""
    
    @pytest.fixture
    def mock_page(self):
        """Cria uma página mock para testes."""
        page = Mock(spec=ft.Page)
        page.update = Mock()
        page.show_snack_bar = Mock()
        return page
    
    @pytest.fixture
    def webview_component(self, mock_page):
        """Cria um componente WebView para testes."""
        return WebViewComponent(
            page=mock_page,
            url_servidor="http://localhost:8000",
            modo_debug=True
        )
    
    def test_configurar_layout_cria_referencias_diretas(self, webview_component):
        """Testa se _configurar_layout cria referências diretas aos containers."""
        # Verificar se o container de carregamento foi criado com referência direta
        assert hasattr(webview_component, '_container_carregamento')
        assert webview_component._container_carregamento is not None
        assert isinstance(webview_component._container_carregamento, ft.Container)
        
        # Verificar se o container está inicialmente visível
        assert webview_component._container_carregamento.visible is True
        
        # Verificar se o container de erro também existe
        assert hasattr(webview_component, '_container_erro')
        assert webview_component._container_erro is not None
        
        # Verificar se o indicador de carregamento existe
        assert hasattr(webview_component, '_indicador_carregamento')
        assert webview_component._indicador_carregamento is not None
    
    def test_handle_page_started_mostra_indicador(self, webview_component, mock_page):
        """Testa se _handle_page_started mostra o indicador corretamente."""
        # Simular evento de início de carregamento
        mock_event = Mock()
        
        # Executar callback
        webview_component._handle_page_started(mock_event)
        
        # Verificar estado interno
        assert webview_component._carregando is True
        assert webview_component._erro_atual is None
        
        # Verificar se o container de carregamento está visível
        assert webview_component._container_carregamento.visible is True
        
        # Verificar se o container de erro está escondido
        assert webview_component._container_erro.visible is False
        
        # Verificar se a página foi atualizada
        mock_page.update.assert_called_once()
    
    def test_handle_page_ended_esconde_indicador(self, webview_component, mock_page):
        """Testa se _handle_page_ended esconde o indicador corretamente."""
        # Configurar estado inicial (carregando)
        webview_component._carregando = True
        webview_component._container_carregamento.visible = True
        
        # Simular evento de fim de carregamento
        mock_event = Mock()
        
        # Executar callback
        webview_component._handle_page_ended(mock_event)
        
        # Verificar estado interno
        assert webview_component._carregando is False
        assert isinstance(webview_component._ultima_atualizacao, datetime)
        
        # Verificar se o container de carregamento está escondido
        assert webview_component._container_carregamento.visible is False
        
        # Verificar se a página foi atualizada
        mock_page.update.assert_called_once()
    
    def test_handle_web_resource_error_gerencia_estado(self, webview_component, mock_page):
        """Testa se _handle_web_resource_error gerencia o estado adequadamente."""
        # Configurar estado inicial (carregando)
        webview_component._carregando = True
        webview_component._container_carregamento.visible = True
        webview_component._tentativas_recuperacao = 0
        
        # Simular evento de erro
        mock_event = Mock()
        mock_event.description = "Erro de rede"
        
        # Executar callback
        webview_component._handle_web_resource_error(mock_event)
        
        # Verificar estado interno
        assert webview_component._carregando is False
        assert webview_component._erro_atual is not None
        assert "Erro de rede" in webview_component._erro_atual
        assert webview_component._tentativas_recuperacao == 1
        
        # Verificar se o container de carregamento está escondido
        assert webview_component._container_carregamento.visible is False
        
        # Verificar se a página foi atualizada
        mock_page.update.assert_called_once()
    
    def test_recarregar_mostra_indicador_corretamente(self, webview_component, mock_page):
        """Testa se o método recarregar mostra o indicador corretamente."""
        # Configurar estado inicial (com erro)
        webview_component._erro_atual = "Erro anterior"
        webview_component._container_erro.visible = True
        webview_component._container_carregamento.visible = False
        
        # Executar recarregamento
        webview_component.recarregar()
        
        # Verificar se o erro foi limpo
        assert webview_component._erro_atual is None
        
        # Verificar se o container de erro foi escondido
        assert webview_component._container_erro.visible is False
        
        # Verificar se o container de carregamento foi mostrado
        assert webview_component._container_carregamento.visible is True
        
        # Verificar se a página foi atualizada
        mock_page.update.assert_called_once()
    
    def test_callbacks_personalizados_sao_chamados(self, mock_page):
        """Testa se os callbacks personalizados são chamados corretamente."""
        # Criar callbacks mock
        mock_on_page_started = Mock()
        mock_on_page_ended = Mock()
        mock_on_web_resource_error = Mock()
        
        # Criar componente com callbacks
        webview_component = WebViewComponent(
            page=mock_page,
            url_servidor="http://localhost:8000",
            on_page_started=mock_on_page_started,
            on_page_ended=mock_on_page_ended,
            on_web_resource_error=mock_on_web_resource_error
        )
        
        # Simular eventos
        mock_event = Mock()
        
        # Testar callback de início
        webview_component._handle_page_started(mock_event)
        mock_on_page_started.assert_called_once_with(mock_event)
        
        # Testar callback de fim
        webview_component._handle_page_ended(mock_event)
        mock_on_page_ended.assert_called_once_with(mock_event)
        
        # Testar callback de erro
        mock_event.description = "Erro de teste"
        webview_component._handle_web_resource_error(mock_event)
        mock_on_web_resource_error.assert_called_once_with(mock_event)
    
    def test_callbacks_com_excecao_nao_quebram_fluxo(self, webview_component, mock_page):
        """Testa se exceções nos callbacks personalizados não quebram o fluxo."""
        # Criar callback que gera exceção
        def callback_com_erro(e):
            raise Exception("Erro no callback")
        
        # Configurar callback
        webview_component._on_page_ended = callback_com_erro
        
        # Simular evento (não deve gerar exceção)
        mock_event = Mock()
        webview_component._handle_page_ended(mock_event)
        
        # Verificar se o estado foi atualizado normalmente
        assert webview_component._carregando is False
        assert webview_component._container_carregamento.visible is False
        mock_page.update.assert_called_once()
    
    def test_ciclo_completo_carregamento(self, webview_component, mock_page):
        """Testa o ciclo completo de carregamento."""
        # Estado inicial
        assert webview_component._container_carregamento.visible is True
        assert webview_component._carregando is False
        
        # Simular início de carregamento
        webview_component._handle_page_started(Mock())
        assert webview_component._carregando is True
        assert webview_component._container_carregamento.visible is True
        assert webview_component._container_erro.visible is False
        
        # Simular fim de carregamento
        webview_component._handle_page_ended(Mock())
        assert webview_component._carregando is False
        assert webview_component._container_carregamento.visible is False
        
        # Verificar se a página foi atualizada nas duas operações
        assert mock_page.update.call_count == 2
    
    def test_multiplos_erros_incrementam_tentativas(self, webview_component, mock_page):
        """Testa se múltiplos erros incrementam as tentativas de recuperação."""
        initial_attempts = webview_component._tentativas_recuperacao
        
        # Simular múltiplos erros
        mock_event = Mock()
        mock_event.description = "Erro 1"
        webview_component._handle_web_resource_error(mock_event)
        assert webview_component._tentativas_recuperacao == initial_attempts + 1
        
        mock_event.description = "Erro 2"
        webview_component._handle_web_resource_error(mock_event)
        assert webview_component._tentativas_recuperacao == initial_attempts + 2
        
        # Verificar se o container de carregamento foi escondido em ambos os casos
        assert webview_component._container_carregamento.visible is False
    
    def test_referencias_diretas_nao_sao_none(self, webview_component):
        """Testa se as referências diretas não são None após inicialização."""
        # Verificar se todas as referências diretas foram criadas
        assert webview_component._container_carregamento is not None
        assert webview_component._container_erro is not None
        assert webview_component._indicador_carregamento is not None
        
        # Verificar se são do tipo correto
        assert isinstance(webview_component._container_carregamento, ft.Container)
        assert isinstance(webview_component._container_erro, ft.Container)
        assert isinstance(webview_component._indicador_carregamento, ft.ProgressRing)
    
    def test_layout_stack_contem_todos_componentes(self, webview_component):
        """Testa se o layout Stack contém todos os componentes necessários."""
        # Verificar se o conteúdo é um Stack
        assert isinstance(webview_component.content, ft.Stack)
        
        # Verificar se o Stack contém os componentes esperados
        stack = webview_component.content
        assert len(stack.controls) == 3  # WebView, Container de carregamento, Container de erro
        
        # Verificar se os componentes estão na ordem correta
        assert webview_component._webview in stack.controls
        assert webview_component._container_carregamento in stack.controls
        assert webview_component._container_erro in stack.controls


if __name__ == "__main__":
    pytest.main([__file__, "-v"])