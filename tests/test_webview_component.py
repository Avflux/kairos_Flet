"""
Testes de integração para WebViewComponent.

Este módulo contém testes abrangentes para o componente WebView,
incluindo inicialização, carregamento de conteúdo, execução de JavaScript,
tratamento de erros e funcionalidades de sincronização.
"""

import pytest
import flet as ft
import asyncio
import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from views.components.webview_component import WebViewComponent
from services.web_server.exceptions import (
    WebViewError,
    CodigosErro,
    RecursoIndisponivelError
)


class TestWebViewComponent:
    """Testes para o componente WebViewComponent."""
    
    @pytest.fixture
    def mock_page(self):
        """Fixture para página Flet mockada."""
        page = Mock(spec=ft.Page)
        page.update = Mock()
        return page
    
    @pytest.fixture
    def url_teste(self):
        """URL de teste para o servidor web."""
        return "http://localhost:8080"
    
    @pytest.fixture
    def webview_component(self, mock_page, url_teste):
        """Fixture para WebViewComponent."""
        with patch('views.components.webview_component.ft.WebView') as mock_webview:
            mock_webview_instance = Mock()
            mock_webview.return_value = mock_webview_instance
            
            component = WebViewComponent(
                page=mock_page,
                url_servidor=url_teste,
                modo_debug=True
            )
            component._webview = mock_webview_instance
            return component
    
    def test_inicializacao_basica(self, mock_page, url_teste):
        """Testa inicialização básica do WebViewComponent."""
        with patch('views.components.webview_component.ft.WebView'):
            component = WebViewComponent(
                page=mock_page,
                url_servidor=url_teste
            )
            
            assert component.url_atual == url_teste
            assert not component.esta_carregando
            assert not component.tem_erro
            assert component.erro_atual is None
            assert isinstance(component.ultima_atualizacao, datetime)
    
    def test_inicializacao_com_parametros_opcionais(self, mock_page, url_teste):
        """Testa inicialização com parâmetros opcionais."""
        callback_started = Mock()
        callback_ended = Mock()
        callback_error = Mock()
        
        with patch('views.components.webview_component.ft.WebView'):
            component = WebViewComponent(
                page=mock_page,
                url_servidor=url_teste,
                largura=800,
                altura=600,
                on_page_started=callback_started,
                on_page_ended=callback_ended,
                on_web_resource_error=callback_error,
                timeout_carregamento=60,
                modo_debug=True
            )
            
            assert component._largura == 800
            assert component._altura == 600
            assert component._timeout_carregamento == 60
            assert component._modo_debug is True
            assert component._on_page_started == callback_started
            assert component._on_page_ended == callback_ended
            assert component._on_web_resource_error == callback_error
    
    def test_criacao_webview_com_sucesso(self, mock_page, url_teste):
        """Testa criação bem-sucedida do WebView."""
        with patch('views.components.webview_component.ft.WebView') as mock_webview:
            mock_instance = Mock()
            mock_webview.return_value = mock_instance
            
            component = WebViewComponent(
                page=mock_page,
                url_servidor=url_teste,
                largura=800,
                altura=600
            )
            
            # Verificar se WebView foi criado com parâmetros corretos
            mock_webview.assert_called_once()
            call_kwargs = mock_webview.call_args[1]
            
            assert call_kwargs['url'] == url_teste
            assert call_kwargs['width'] == 800
            assert call_kwargs['height'] == 600
            assert call_kwargs['javascript_enabled'] is True
            assert call_kwargs['prevent_link'] is False
    
    def test_falha_na_criacao_webview(self, mock_page, url_teste):
        """Testa tratamento de falha na criação do WebView."""
        with patch('views.components.webview_component.ft.WebView', side_effect=Exception("Erro de criação")):
            with pytest.raises(WebViewError) as exc_info:
                WebViewComponent(
                    page=mock_page,
                    url_servidor=url_teste
                )
            
            assert "Não foi possível criar o WebView" in str(exc_info.value)
            assert exc_info.value.codigo_erro == CodigosErro.WEBVIEW_FALHA_CARREGAMENTO
            assert exc_info.value.url == url_teste
    
    def test_handle_page_started(self, webview_component):
        """Testa manipulação do evento de início de carregamento."""
        # Simular evento
        event = Mock()
        
        # Executar handler
        webview_component._handle_page_started(event)
        
        # Verificar estado
        assert webview_component._carregando is True
        assert webview_component._erro_atual is None
        
        # Verificar se página foi atualizada
        webview_component.page.update.assert_called()
    
    def test_handle_page_ended(self, webview_component):
        """Testa manipulação do evento de fim de carregamento."""
        # Definir estado inicial
        webview_component._carregando = True
        timestamp_inicial = webview_component._ultima_atualizacao
        
        # Simular evento
        event = Mock()
        
        # Executar handler
        webview_component._handle_page_ended(event)
        
        # Verificar estado
        assert webview_component._carregando is False
        assert webview_component._ultima_atualizacao > timestamp_inicial
        
        # Verificar se página foi atualizada
        webview_component.page.update.assert_called()
    
    def test_handle_web_resource_error(self, webview_component):
        """Testa manipulação de erros de recursos web."""
        # Simular evento de erro
        event = Mock()
        event.description = "Recurso não encontrado"
        
        # Executar handler
        webview_component._handle_web_resource_error(event)
        
        # Verificar estado
        assert webview_component._carregando is False
        assert webview_component._erro_atual is not None
        assert "Recurso não encontrado" in webview_component._erro_atual
        
        # Verificar se container de erro está visível
        assert webview_component._container_erro.visible is True
        
        # Verificar se página foi atualizada
        webview_component.page.update.assert_called()
    
    def test_atualizar_url_valida(self, webview_component):
        """Testa atualização de URL válida."""
        nova_url = "http://localhost:8081/nova-pagina"
        
        # Atualizar URL
        webview_component.atualizar_url(nova_url)
        
        # Verificar se URL foi atualizada
        assert webview_component.url_atual == nova_url
        assert webview_component._webview.url == nova_url
        
        # Verificar se página foi atualizada
        webview_component.page.update.assert_called()
    
    def test_atualizar_url_vazia(self, webview_component):
        """Testa tratamento de URL vazia."""
        with pytest.raises(WebViewError) as exc_info:
            webview_component.atualizar_url("")
        
        assert "URL não pode estar vazia" in str(exc_info.value)
        assert exc_info.value.codigo_erro == CodigosErro.WEBVIEW_URL_INVALIDA
    
    def test_atualizar_url_none(self, webview_component):
        """Testa tratamento de URL None."""
        with pytest.raises(WebViewError) as exc_info:
            webview_component.atualizar_url(None)
        
        assert "URL não pode estar vazia" in str(exc_info.value)
        assert exc_info.value.codigo_erro == CodigosErro.WEBVIEW_URL_INVALIDA
    
    def test_recarregar_com_sucesso(self, webview_component):
        """Testa recarregamento bem-sucedido."""
        # Definir estado de erro
        webview_component._erro_atual = "Erro anterior"
        webview_component._container_erro.visible = True
        
        # Recarregar
        webview_component.recarregar()
        
        # Verificar se erro foi limpo
        assert webview_component._erro_atual is None
        assert webview_component._container_erro.visible is False
        
        # Verificar se WebView foi recarregado
        assert webview_component._webview.url == webview_component._url_servidor
        
        # Verificar se página foi atualizada
        webview_component.page.update.assert_called()
    
    def test_recarregar_sem_webview(self, mock_page, url_teste):
        """Testa recarregamento sem WebView inicializado."""
        with patch('views.components.webview_component.ft.WebView'):
            component = WebViewComponent(
                page=mock_page,
                url_servidor=url_teste
            )
            component._webview = None
            
            with pytest.raises(WebViewError) as exc_info:
                component.recarregar()
            
            assert "WebView não foi inicializado" in str(exc_info.value)
            assert exc_info.value.codigo_erro == CodigosErro.WEBVIEW_FALHA_CARREGAMENTO
    
    def test_executar_javascript_valido(self, webview_component):
        """Testa execução de JavaScript válido."""
        codigo_js = "console.log('Teste');"
        
        # Executar JavaScript
        webview_component.executar_javascript(codigo_js)
        
        # Verificar se foi chamado no WebView
        webview_component._webview.evaluate_javascript.assert_called_once_with(codigo_js)
    
    def test_executar_javascript_vazio(self, webview_component):
        """Testa execução de JavaScript vazio."""
        with pytest.raises(WebViewError) as exc_info:
            webview_component.executar_javascript("")
        
        assert "Código JavaScript não pode estar vazio" in str(exc_info.value)
        assert exc_info.value.codigo_erro == CodigosErro.WEBVIEW_ERRO_JAVASCRIPT
    
    def test_executar_javascript_sem_webview(self, mock_page, url_teste):
        """Testa execução de JavaScript sem WebView."""
        with patch('views.components.webview_component.ft.WebView'):
            component = WebViewComponent(
                page=mock_page,
                url_servidor=url_teste
            )
            component._webview = None
            
            with pytest.raises(WebViewError) as exc_info:
                component.executar_javascript("console.log('teste');")
            
            assert "WebView não foi inicializado" in str(exc_info.value)
            assert exc_info.value.codigo_erro == CodigosErro.WEBVIEW_ERRO_JAVASCRIPT
    
    def test_notificar_atualizacao_dados(self, webview_component):
        """Testa notificação de atualização de dados."""
        dados_teste = {
            "tempo_decorrido": 3600,
            "esta_executando": True,
            "projeto_atual": "Teste"
        }
        
        # Notificar atualização
        webview_component.notificar_atualizacao_dados(dados_teste)
        
        # Verificar se JavaScript foi executado
        webview_component._webview.evaluate_javascript.assert_called_once()
        
        # Verificar se dados estão no código JavaScript
        call_args = webview_component._webview.evaluate_javascript.call_args[0][0]
        assert "atualizarDados" in call_args or "onDataUpdate" in call_args
        assert "3600" in call_args
        assert "true" in call_args.lower()
        assert "Teste" in call_args
    
    def test_definir_tamanho(self, webview_component):
        """Testa definição de tamanho do WebView."""
        nova_largura = 1024
        nova_altura = 768
        
        # Definir tamanho
        webview_component.definir_tamanho(nova_largura, nova_altura)
        
        # Verificar se tamanho foi atualizado
        assert webview_component._largura == nova_largura
        assert webview_component._altura == nova_altura
        assert webview_component._webview.width == nova_largura
        assert webview_component._webview.height == nova_altura
        
        # Verificar se página foi atualizada
        webview_component.page.update.assert_called()
    
    def test_definir_tamanho_parcial(self, webview_component):
        """Testa definição parcial de tamanho."""
        nova_largura = 800
        
        # Definir apenas largura
        webview_component.definir_tamanho(largura=nova_largura)
        
        # Verificar se apenas largura foi atualizada
        assert webview_component._largura == nova_largura
        assert webview_component._webview.width == nova_largura
        
        # Altura deve permanecer inalterada
        assert webview_component._altura is None
    
    def test_propriedades_status(self, webview_component):
        """Testa propriedades de status do componente."""
        # Estado inicial
        assert webview_component.url_atual == "http://localhost:8080"
        assert not webview_component.esta_carregando
        assert not webview_component.tem_erro
        assert webview_component.erro_atual is None
        assert isinstance(webview_component.ultima_atualizacao, datetime)
        
        # Simular carregamento
        webview_component._carregando = True
        assert webview_component.esta_carregando
        
        # Simular erro
        webview_component._erro_atual = "Erro de teste"
        assert webview_component.tem_erro
        assert webview_component.erro_atual == "Erro de teste"
    
    def test_obter_status(self, webview_component):
        """Testa obtenção de status completo."""
        # Definir estado conhecido
        webview_component._carregando = True
        webview_component._erro_atual = "Erro de teste"
        webview_component._largura = 800
        webview_component._altura = 600
        
        # Obter status
        status = webview_component.obter_status()
        
        # Verificar campos do status
        assert status["url"] == "http://localhost:8080"
        assert status["carregando"] is True
        assert status["tem_erro"] is True
        assert status["erro"] == "Erro de teste"
        assert status["largura"] == 800
        assert status["altura"] == 600
        assert status["modo_debug"] is True
        assert "ultima_atualizacao" in status
    
    def test_callbacks_personalizados(self, mock_page, url_teste):
        """Testa execução de callbacks personalizados."""
        callback_started = Mock()
        callback_ended = Mock()
        callback_error = Mock()
        
        with patch('views.components.webview_component.ft.WebView'):
            component = WebViewComponent(
                page=mock_page,
                url_servidor=url_teste,
                on_page_started=callback_started,
                on_page_ended=callback_ended,
                on_web_resource_error=callback_error
            )
            
            # Simular eventos
            event_mock = Mock()
            
            component._handle_page_started(event_mock)
            callback_started.assert_called_once_with(event_mock)
            
            component._handle_page_ended(event_mock)
            callback_ended.assert_called_once_with(event_mock)
            
            component._handle_web_resource_error(event_mock)
            callback_error.assert_called_once_with(event_mock)
    
    def test_callback_com_excecao(self, mock_page, url_teste):
        """Testa tratamento de exceções em callbacks."""
        callback_com_erro = Mock(side_effect=Exception("Erro no callback"))
        
        with patch('views.components.webview_component.ft.WebView'):
            component = WebViewComponent(
                page=mock_page,
                url_servidor=url_teste,
                on_page_started=callback_com_erro
            )
            
            # Simular evento - não deve levantar exceção
            event_mock = Mock()
            component._handle_page_started(event_mock)
            
            # Callback deve ter sido chamado
            callback_com_erro.assert_called_once_with(event_mock)
    
    def test_container_erro_configuracao(self, webview_component):
        """Testa configuração do container de erro."""
        container_erro = webview_component._container_erro
        
        # Verificar estrutura do container
        assert container_erro is not None
        assert not container_erro.visible  # Inicialmente invisível
        assert container_erro.content is not None
        
        # Verificar conteúdo do container
        coluna = container_erro.content
        assert len(coluna.controls) >= 4  # Ícone, título, descrição, botão
        
        # Verificar se tem botão de retry
        botao_retry = coluna.controls[-1]
        assert hasattr(botao_retry, 'on_click')
        assert botao_retry.text == "Tentar Novamente"
    
    def test_indicador_carregamento(self, webview_component):
        """Testa indicador de carregamento."""
        indicador = webview_component._indicador_carregamento
        
        # Verificar configuração do indicador
        assert indicador is not None
        assert indicador.width == 50
        assert indicador.height == 50
        assert indicador.stroke_width == 4
    
    def test_layout_responsivo(self, webview_component):
        """Testa configuração do layout responsivo."""
        # Verificar estrutura do layout
        assert webview_component.content is not None
        assert webview_component.expand is True
        assert webview_component.border_radius == 8
        assert webview_component.border is not None
        assert webview_component.bgcolor == ft.Colors.WHITE
        
        # Verificar stack de componentes
        stack = webview_component.content
        assert len(stack.controls) == 3  # WebView, carregamento, erro


class TestWebViewComponentIntegracao:
    """Testes de integração mais complexos."""
    
    @pytest.fixture
    def servidor_mock(self):
        """Mock de servidor web para testes de integração."""
        return Mock()
    
    @pytest.fixture
    def mock_page(self):
        """Fixture para página Flet mockada."""
        page = Mock(spec=ft.Page)
        page.update = Mock()
        return page
    
    @pytest.fixture
    def url_teste(self):
        """URL de teste para o servidor web."""
        return "http://localhost:8080"
    
    @pytest.fixture
    def webview_component(self, mock_page, url_teste):
        """Fixture para WebViewComponent."""
        with patch('views.components.webview_component.ft.WebView') as mock_webview:
            mock_webview_instance = Mock()
            mock_webview.return_value = mock_webview_instance
            
            component = WebViewComponent(
                page=mock_page,
                url_servidor=url_teste,
                modo_debug=True
            )
            component._webview = mock_webview_instance
            return component
    
    def test_fluxo_carregamento_completo(self, mock_page, url_teste):
        """Testa fluxo completo de carregamento."""
        with patch('views.components.webview_component.ft.WebView'):
            component = WebViewComponent(
                page=mock_page,
                url_servidor=url_teste
            )
            
            # Simular início do carregamento
            component._handle_page_started(Mock())
            assert component.esta_carregando
            
            # Simular fim do carregamento
            component._handle_page_ended(Mock())
            assert not component.esta_carregando
            
            # Verificar se página foi atualizada múltiplas vezes
            assert mock_page.update.call_count >= 2
    
    def test_fluxo_erro_e_recuperacao(self, mock_page, url_teste):
        """Testa fluxo de erro e recuperação."""
        with patch('views.components.webview_component.ft.WebView'):
            component = WebViewComponent(
                page=mock_page,
                url_servidor=url_teste
            )
            
            # Simular erro
            event_erro = Mock()
            event_erro.description = "Conexão recusada"
            component._handle_web_resource_error(event_erro)
            
            assert component.tem_erro
            assert component._container_erro.visible
            
            # Simular recuperação via reload
            component.recarregar()
            
            assert not component.tem_erro
            assert not component._container_erro.visible
    
    def test_sincronizacao_dados_complexa(self, webview_component):
        """Testa sincronização com dados complexos."""
        dados_complexos = {
            "usuario": {
                "nome": "João Silva",
                "email": "joao@exemplo.com"
            },
            "projetos": [
                {"id": 1, "nome": "Projeto A", "ativo": True},
                {"id": 2, "nome": "Projeto B", "ativo": False}
            ],
            "configuracoes": {
                "tema": "escuro",
                "idioma": "pt-BR",
                "notificacoes": True
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Notificar dados complexos
        webview_component.notificar_atualizacao_dados(dados_complexos)
        
        # Verificar se JavaScript foi executado
        webview_component._webview.evaluate_javascript.assert_called_once()
        
        # Verificar se dados estão presentes no JavaScript
        call_args = webview_component._webview.evaluate_javascript.call_args[0][0]
        assert "João Silva" in call_args
        assert "Projeto A" in call_args
        assert "pt-BR" in call_args
    
    def test_performance_multiplas_atualizacoes(self, webview_component):
        """Testa performance com múltiplas atualizações rápidas."""
        # Simular múltiplas atualizações
        for i in range(10):
            dados = {"contador": i, "timestamp": time.time()}
            webview_component.notificar_atualizacao_dados(dados)
        
        # Verificar se todas as chamadas foram feitas
        assert webview_component._webview.evaluate_javascript.call_count == 10
    
    def test_tratamento_dados_invalidos(self, webview_component):
        """Testa tratamento de dados inválidos para sincronização."""
        # Dados que não podem ser serializados para JSON
        dados_invalidos = {
            "funcao": lambda x: x,  # Função não é serializável
            "data": datetime.now()  # datetime precisa ser convertido
        }
        
        # Deve tratar graciosamente sem levantar exceção
        try:
            webview_component.notificar_atualizacao_dados(dados_invalidos)
        except Exception:
            # Se houver exceção, deve ser capturada internamente
            pass
        
        # WebView não deve ter sido chamado devido ao erro
        webview_component._webview.evaluate_javascript.assert_not_called()