""
import flet as ft

class MainView(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.route = "/"
        self.appbar = ft.AppBar(
            leading=ft.Icon("TIMER"),
            leading_width=40,
            title=ft.Text("Controlador de Atividades"),
            center_title=False,
            bgcolor="SURFACE_VARIANT",
            actions=[
                ft.IconButton("EXIT_TO_APP", on_click=self.exit_app),
            ],
        )

        self.controls = [
            ft.Text("Bem-vindo à tela principal!")
        ]

    def exit_app(self, e):
        self.page.window_destroy()
