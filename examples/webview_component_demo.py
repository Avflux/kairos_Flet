"""
Demonstração do WebViewComponent.

Este exemplo mostra como usar o WebViewComponent para integrar
conteúdo web em uma aplicação Flet, incluindo execução de JavaScript
e sincronização de dados.
"""

import flet as ft
import asyncio
import json
import time
from datetime import datetime

from views.components.webview_component import WebViewComponent
from services.web_server.exceptions import WebViewError


def main(page: ft.Page):
    """Função principal da demonstração."""
    
    # Configurar página
    page.title = "Demonstração WebViewComponent"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1200
    page.window_height = 800
    
    # URL de exemplo (pode ser qualquer servidor web)
    url_exemplo = "https://httpbin.org/html"
    
    # Estado da demonstração
    contador = {"valor": 0}
    
    # Criar WebViewComponent
    try:
        webview = WebViewComponent(
            page=page,
            url_servidor=url_exemplo,
            largura=800,
            altura=500,
            on_page_started=lambda e: print("Página iniciou carregamento"),
            on_page_ended=lambda e: print("Página terminou carregamento"),
            on_web_resource_error=lambda e: print(f"Erro no recurso: {e}"),
            modo_debug=True
        )
    except WebViewError as e:
        print(f"Erro ao criar WebView: {e}")
        return
    
    # Controles de demonstração
    url_input = ft.TextField(
        label="URL do WebView",
        value=url_exemplo,
        width=400
    )
    
    def atualizar_url(e):
        """Atualiza a URL do WebView."""
        try:
            webview.atualizar_url(url_input.value)
            status_text.value = f"URL atualizada: {url_input.value}"
            status_text.color = ft.Colors.GREEN_600
        except WebViewError as ex:
            status_text.value = f"Erro ao atualizar URL: {ex}"
            status_text.color = ft.Colors.RED_600
        page.update()
    
    def recarregar_webview(e):
        """Recarrega o WebView."""
        try:
            webview.recarregar()
            status_text.value = "WebView recarregado"
            status_text.color = ft.Colors.BLUE_600
        except WebViewError as ex:
            status_text.value = f"Erro ao recarregar: {ex}"
            status_text.color = ft.Colors.RED_600
        page.update()
    
    def executar_js_simples(e):
        """Executa JavaScript simples."""
        try:
            js_code = "alert('Olá do Flet!');"
            webview.executar_javascript(js_code)
            status_text.value = "JavaScript executado"
            status_text.color = ft.Colors.GREEN_600
        except WebViewError as ex:
            status_text.value = f"Erro ao executar JS: {ex}"
            status_text.color = ft.Colors.RED_600
        page.update()
    
    def executar_js_personalizado(e):
        """Executa JavaScript personalizado."""
        try:
            js_code = js_input.value
            if js_code.strip():
                webview.executar_javascript(js_code)
                status_text.value = "JavaScript personalizado executado"
                status_text.color = ft.Colors.GREEN_600
            else:
                status_text.value = "Digite código JavaScript primeiro"
                status_text.color = ft.Colors.ORANGE_600
        except WebViewError as ex:
            status_text.value = f"Erro ao executar JS: {ex}"
            status_text.color = ft.Colors.RED_600
        page.update()
    
    def sincronizar_dados(e):
        """Sincroniza dados com o WebView."""
        try:
            contador["valor"] += 1
            dados = {
                "contador": contador["valor"],
                "timestamp": datetime.now().isoformat(),
                "usuario": "Demonstração",
                "status": "ativo"
            }
            webview.notificar_atualizacao_dados(dados)
            status_text.value = f"Dados sincronizados (contador: {contador['valor']})"
            status_text.color = ft.Colors.BLUE_600
        except Exception as ex:
            status_text.value = f"Erro na sincronização: {ex}"
            status_text.color = ft.Colors.RED_600
        page.update()
    
    def mostrar_status(e):
        """Mostra status do WebView."""
        status = webview.obter_status()
        status_json = json.dumps(status, indent=2, ensure_ascii=False)
        
        # Criar diálogo com status
        dialog = ft.AlertDialog(
            title=ft.Text("Status do WebView"),
            content=ft.Container(
                content=ft.Text(
                    status_json,
                    selectable=True,
                    size=12
                ),
                width=500,
                height=300,
                padding=10
            ),
            actions=[
                ft.TextButton("Fechar", on_click=lambda e: fechar_dialog())
            ]
        )
        
        def fechar_dialog():
            dialog.open = False
            page.update()
        
        page.dialog = dialog
        dialog.open = True
        page.update()
    
    # Controles da interface
    js_input = ft.TextField(
        label="Código JavaScript",
        value="console.log('Teste do Flet');",
        multiline=True,
        min_lines=3,
        max_lines=5,
        width=400
    )
    
    status_text = ft.Text(
        "WebView pronto para uso",
        color=ft.Colors.GREEN_600,
        size=14
    )
    
    # Layout da aplicação
    controles = ft.Column([
        ft.Text("Controles do WebView", size=18, weight=ft.FontWeight.BOLD),
        
        ft.Row([
            url_input,
            ft.ElevatedButton("Atualizar URL", on_click=atualizar_url)
        ]),
        
        ft.Row([
            ft.ElevatedButton("Recarregar", on_click=recarregar_webview),
            ft.ElevatedButton("JS Simples", on_click=executar_js_simples),
            ft.ElevatedButton("Sincronizar", on_click=sincronizar_dados),
            ft.ElevatedButton("Status", on_click=mostrar_status)
        ]),
        
        js_input,
        ft.ElevatedButton("Executar JS", on_click=executar_js_personalizado),
        
        ft.Divider(),
        status_text,
        
        ft.Text("Propriedades do WebView:", weight=ft.FontWeight.BOLD),
        ft.Text(f"URL: {webview.url_atual}"),
        ft.Text(f"Carregando: {webview.esta_carregando}"),
        ft.Text(f"Tem erro: {webview.tem_erro}"),
    ], spacing=10)
    
    # Layout principal
    layout_principal = ft.Row([
        ft.Container(
            content=controles,
            width=450,
            padding=20,
            bgcolor=ft.Colors.GREY_50,
            border_radius=10
        ),
        ft.VerticalDivider(),
        ft.Container(
            content=webview,
            expand=True,
            padding=10
        )
    ], expand=True)
    
    page.add(layout_principal)


if __name__ == "__main__":
    # Executar aplicação
    print("Iniciando demonstração do WebViewComponent...")
    print("Use os controles à esquerda para interagir com o WebView")
    
    ft.app(target=main)