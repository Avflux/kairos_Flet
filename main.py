
import flet as ft
from views.login_view import LoginView
from views.main_view import MainView

def main(page: ft.Page):
    page.title = "Controlador de Atividades"

    def route_change(route):
        page.views.clear()
        if page.route == "/login":
            page.views.append(LoginView(page))
        elif page.route == "/":
            page.views.append(MainView(page))
        page.update()

    def view_pop(view):
        page.views.pop()
        if page.views:
            top_view = page.views[-1]
            page.go(top_view.route)
        else:
            page.window_destroy()

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go("/login")

if __name__ == "__main__":
    ft.app(
        target=main,
        port=8552,
        view=ft.AppView.WEB_BROWSER
    )
