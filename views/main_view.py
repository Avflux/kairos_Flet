import flet as ft

class MainView(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.route = "/"
        self.page.theme_mode = ft.ThemeMode.DARK

        # --- Sidebar State ---
        self.sidebar_expanded = True

        # --- Main Content Area ---
        self.main_content = ft.Column(
            [ft.Text("Bem-vindo à tela principal!", size=20)],
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

        # --- Sidebar Helper Methods ---
        def create_nav_item(icon, text, selected=False, is_button=False, is_link=False):
            controls = [ft.Icon(icon), ft.Text(text, visible=self.sidebar_expanded)]
            if is_link:
                controls.append(ft.Icon('open_in_new', size=16))
            
            return ft.Container(
                ft.Row(controls, spacing=15),
                bgcolor='primary' if selected else ('surface_variant' if is_button else None),
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                border_radius=ft.border_radius.all(20),
            )

        def create_section_header(text, expanded, on_click):
            icon = 'arrow_drop_up' if expanded else 'arrow_drop_down'
            return ft.Row(
                [
                    ft.Text(text, weight="bold", visible=self.sidebar_expanded),
                    ft.IconButton(icon=icon, on_click=on_click, data=text.lower()),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                height=40,
            )

        # --- Sidebar Content ---
        self.nav_items = {
            "studio_header": create_section_header("Atividades", True, self.toggle_section),
            "studio_items": ft.Column([
                create_nav_item("chat_bubble_outline", "Chat"),
                create_nav_item("stream", "Stream"),
                create_nav_item("photo_library_outlined", "Generate media"),
                create_nav_item("construction_outlined", "Build", selected=True),
            ], spacing=4, tight=True),

            "history_header": create_section_header("Arquivos", False, self.toggle_section),
            "history_items": ft.Column([], spacing=4, tight=True, visible=False),

            "dashboard_header": create_section_header("Dashboard", False, self.toggle_section),
            "dashboard_items": ft.Column([], spacing=4, tight=True, visible=False),

            "doc_item": create_nav_item("description_outlined", "Documentation", is_link=True),
        }
        
        self.bottom_items = ft.Column([
            ft.Text("Google AI models may make mistakes, so double-check outputs.", size=10, color='on_surface_variant', visible=self.sidebar_expanded),
            create_nav_item("key_outlined", "Get API key", is_button=True),
            create_nav_item("settings_outlined", "Configurações"),
            ft.Row([ft.Icon('account_circle'), ft.Text("6331683@gmail.c...", visible=self.sidebar_expanded)], spacing=15)
        ], spacing=10)


        # --- Sidebar Structure ---
        self.sidebar = ft.Container(
            content=ft.Column([
                ft.Row(
                    [
                        ft.Text("Kairos", weight="bold", size=18, visible=self.sidebar_expanded),
                        ft.IconButton(icon='menu', on_click=self.toggle_sidebar),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Column(
                    controls=list(self.nav_items.values()),
                    expand=True,
                    spacing=0,
                    tight=True,
                ),
                self.bottom_items
            ]),
            width=250,
            padding=ft.padding.symmetric(vertical=10, horizontal=15),
            bgcolor='rgba(255, 255, 255, 0.03)',
            border_radius=ft.border_radius.all(10),
            animate=ft.Animation(300, "ease"),
        )

        # --- Page Structure ---
        self.controls = [
            ft.Row(
                [self.sidebar, ft.VerticalDivider(width=1, color="transparent"), self.main_content],
                expand=True,
            )
        ]
        self.appbar = None

    def toggle_sidebar(self, e):
        self.sidebar_expanded = not self.sidebar_expanded
        self.sidebar.width = 250 if self.sidebar_expanded else 80
        
        # Helper to update visibility
        def update_visibility(container, visibility):
            for ctrl in container.controls:
                if isinstance(ctrl, ft.Row):
                    for item in ctrl.controls:
                        if isinstance(item, ft.Text): item.visible = visibility
                elif isinstance(ctrl, ft.Container):
                     if len(ctrl.content.controls) > 1 and isinstance(ctrl.content.controls[1], ft.Text):
                        ctrl.content.controls[1].visible = visibility

        # Top title
        self.sidebar.content.controls[0].controls[0].visible = self.sidebar_expanded
        
        # Nav sections
        for key, item in self.nav_items.items():
            if "header" in key:
                item.controls[0].visible = self.sidebar_expanded
            elif "items" in key:
                update_visibility(item, self.sidebar_expanded)
            elif "item" in key:
                if len(item.content.controls) > 1 and isinstance(item.content.controls[1], ft.Text):
                    item.content.controls[1].visible = self.sidebar_expanded

        # Bottom items
        self.bottom_items.controls[0].visible = self.sidebar_expanded
        update_visibility(self.bottom_items, self.sidebar_expanded)
        
        self.page.update()

    def toggle_section(self, e):
        section_name = e.control.data
        header = self.nav_items[f"{section_name}_header"]
        items = self.nav_items[f"{section_name}_items"]
        
        items.visible = not items.visible
        header.controls[1].icon = 'arrow_drop_up' if items.visible else 'arrow_drop_down'
        self.page.update()
