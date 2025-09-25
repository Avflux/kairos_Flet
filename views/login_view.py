
import flet as ft
from viewmodels.login_viewmodel import LoginViewModel

class LoginView(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.viewmodel = LoginViewModel()
        self.route = "/login"
        self.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        self.username_field = ft.TextField(label="Usuário", on_change=self.update_username)
        self.password_field = ft.TextField(label="Senha", password=True, on_change=self.update_password)

        self.controls = [
            ft.Column(
                [
                    ft.Text("Login", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                    self.username_field,
                    self.password_field,
                    ft.ElevatedButton("Entrar", on_click=self.login),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            )
        ]

    def update_username(self, e):
        self.viewmodel.set_username(e.control.value)

    def update_password(self, e):
        self.viewmodel.set_password(e.control.value)

    def login(self, e):
        if self.viewmodel.login():
            self.page.go("/")
        else:
            # Adicionar feedback de erro para o usuário
            print("Login failed")
