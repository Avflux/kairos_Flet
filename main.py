
import flet as ft
import os
from views.login_view import LoginView
from views.main_view import MainView

def main(page: ft.Page):
    page.title = "Kairos"
    # Maximize window when running as desktop app
    if os.getenv("KAIROS_VIEW", "WEB_BROWSER").upper() == "FLET_APP":
        try:
            page.window_maximized = True
        except Exception:
            pass

    # --- Theme initialization & toggle ---
    def apply_theme(theme_value: str):
        page.theme_mode = ft.ThemeMode.DARK if theme_value == "dark" else ft.ThemeMode.LIGHT
        # Update the toggle icon
        if isinstance(page.appbar, ft.AppBar):
            icon = ft.Icons.LIGHT_MODE if theme_value == "dark" else ft.Icons.DARK_MODE
            page.appbar.actions = [
                ft.IconButton(icon=icon, tooltip="Alternar tema", on_click=toggle_theme)
            ]
        page.update()

    def toggle_theme(e=None):
        current = page.client_storage.get("theme") or "dark"
        new_value = "light" if current == "dark" else "dark"
        page.client_storage.set("theme", new_value)
        apply_theme(new_value)

    # Load and apply persisted theme
    persisted_theme = page.client_storage.get("theme") or "dark"
    apply_theme(persisted_theme)

    # Global app bar with theme toggle
    page.appbar = ft.AppBar(
        title=ft.Text("Kairos"),
        center_title=False,
        actions=[
            ft.IconButton(
                icon=ft.Icons.LIGHT_MODE if persisted_theme == "dark" else ft.Icons.DARK_MODE,
                tooltip="Alternar tema",
                on_click=toggle_theme,
            )
        ],
    )

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
            # Navigate back to the login screen when the last view is popped
            page.go("/login")

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go("/login")

if __name__ == "__main__":
    # Read port from environment variable with default to 8552
    port = int(os.getenv("KAIROS_PORT", "8552"))
    # Select view from environment variable, default WEB_BROWSER
    view_env = os.getenv("KAIROS_VIEW", "WEB_BROWSER").upper()
    view = ft.AppView.FLET_APP if view_env == "FLET_APP" else ft.AppView.WEB_BROWSER
    ft.app(
        target=main,
        port=port,
        view=view
    )
