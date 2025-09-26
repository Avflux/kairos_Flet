
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

        # Inputs
        self.username_field = ft.TextField(
            label="Usuário",
            on_change=self.update_username,
            prefix_icon=ft.Icons.PERSON_OUTLINE,
            width=320,
            autofocus=True,
        )
        self.password_field = ft.TextField(
            label="Senha",
            password=True,
            can_reveal_password=True,
            on_change=self.update_password,
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            width=320,
        )
        self.remember_checkbox = ft.Checkbox(
            label="Lembrar credenciais",
            value=self.viewmodel.get_remember(),
            on_change=self.update_remember,
        )
        self.login_button = ft.ElevatedButton(
            text="Entrar",
            icon=ft.Icons.LOGIN,
            on_click=self.login,
            style=ft.ButtonStyle(
                shape={"": ft.RoundedRectangleBorder(radius=12)},
                padding=ft.padding.symmetric(horizontal=20, vertical=14),
            ),
            width=320,
            height=46,
        )

        # Floating Card
        card_content = ft.Column(
            [
                ft.Text("Bem-vindo", weight="bold", size=22),
                ft.Text("Acesse sua conta para continuar", size=12, color="on_surface_variant"),
                self.username_field,
                self.password_field,
                ft.Row([self.remember_checkbox], alignment=ft.MainAxisAlignment.START),
                self.login_button,
            ],
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        card = ft.Container(
            content=card_content,
            bgcolor="surface",
            padding=ft.padding.all(24),
            border_radius=16,
            width=380,
            shadow=ft.BoxShadow(blur_radius=24, spread_radius=2, color="rgba(0,0,0,0.25)"),
        )

        # Background and layout: center-floating card (inherits theme)
        background = ft.Container(
            expand=True,
            bgcolor="background",
            padding=20,
            content=ft.Row([
                ft.Container(width=1, expand=True),
                card,
                ft.Container(width=1, expand=True),
            ], alignment=ft.MainAxisAlignment.CENTER),
        )

        self.controls = [background]

    def update_username(self, e):
        self.viewmodel.set_username(e.control.value)

    def update_password(self, e):
        self.viewmodel.set_password(e.control.value)

    def update_remember(self, e):
        self.viewmodel.set_remember(e.control.value)

    def login(self, e):
        if self.viewmodel.login():
            self.page.go("/")
        else:
            # Adicionar feedback de erro para o usuário
            self.page.snack_bar = ft.SnackBar(ft.Text("Usuário ou senha inválidos"))
            self.page.snack_bar.open = True
            self.page.update()
