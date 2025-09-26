import flet as ft

class MainView(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.route = "/"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = "#141218"
        self.page.padding = 10

        # --- State ---
        self.sidebar_expanded = True
        self.sidebar_texts = [] # List to hold all text controls that toggle visibility

        # --- Helper Methods ---
        def create_nav_item(icon, text_value, selected=False, is_button=False, is_link=False):
            # Create the Text control and add it to our list
            text_control = ft.Text(text_value, visible=self.sidebar_expanded)
            self.sidebar_texts.append(text_control)

            controls = [ft.Icon(icon), text_control]
            if is_link:
                controls.append(ft.Icon('open_in_new', size=16))
            
            return ft.Container(
                ft.Row(controls, spacing=15),
                bgcolor='primary' if selected else ('surface_variant' if is_button else None),
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                border_radius=ft.border_radius.all(20),
            )

        def create_section_header(text_value, expanded, on_click):
            # Create the Text control and add it to our list
            text_control = ft.Text(text_value, weight="bold", visible=self.sidebar_expanded)
            self.sidebar_texts.append(text_control)
            
            icon = 'arrow_drop_up' if expanded else 'arrow_drop_down'
            return ft.Row(
                [
                    text_control,
                    ft.IconButton(icon=icon, on_click=on_click, data=text_value.lower()),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                height=40,
            )

        # --- Top Bar ---
        self.top_bar_left = ft.Container(
            height=48,
            bgcolor='rgba(255, 255, 255, 0.03)',
            border_radius=ft.border_radius.all(10),
            padding=ft.padding.symmetric(horizontal=20),
            content=ft.Row([ft.Text("Painel", weight="bold")])
        )
        self.top_bar_right = ft.Container(
            expand=True,
            height=48,
            bgcolor='rgba(255, 255, 255, 0.03)',
            border_radius=ft.border_radius.all(10),
            padding=ft.padding.symmetric(horizontal=20),
            content=ft.Row([ft.Text("Conteúdo Superior Direito")], alignment=ft.MainAxisAlignment.END)
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

        # Create bottom items and add their texts to the list
        bottom_text_1 = ft.Text("Google AI models may make mistakes...", size=10, color='on_surface_variant', visible=self.sidebar_expanded)
        self.sidebar_texts.append(bottom_text_1)
        # We need to manually create the text for the account row to add it to the list
        account_text = ft.Text("6331683@gmail.c...", visible=self.sidebar_expanded)
        self.sidebar_texts.append(account_text)
        
        self.bottom_items = ft.Column([
            bottom_text_1,
            create_nav_item("key_outlined", "Get API key", is_button=True),
            create_nav_item("settings_outlined", "Configurações"),
            ft.Row([ft.Icon('account_circle'), account_text], spacing=15)
        ], spacing=10)

        # --- Main Title for Sidebar ---
        kairos_title = ft.Text("Kairos", weight="bold", size=18, visible=self.sidebar_expanded)
        self.sidebar_texts.append(kairos_title)

        # --- Structures ---
        sidebar_content_column = ft.Column([
            ft.Row(
                [
                    kairos_title,
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
        ])

        # This is the animating container for the sidebar
        self.sidebar_container = ft.Container(
            width=250,
            padding=ft.padding.symmetric(vertical=10, horizontal=15),
            bgcolor='rgba(255, 255, 255, 0.03)',
            border_radius=ft.border_radius.all(10),
            animate=ft.Animation(300, "ease"),
            content=sidebar_content_column,
            expand=True,
        )

        self.main_content = ft.Container(
            expand=True,
            content=ft.Column(
                [ft.Text("Bem-vindo à tela principal!", size=20)],
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            bgcolor='rgba(255, 255, 255, 0.03)',
            border_radius=ft.border_radius.all(10),
            padding=20
        )
        
        # --- Final Page Layout ---
        sidebar_column_wrapper = ft.Column(
            spacing=10,
            controls=[
                self.top_bar_left,
                self.sidebar_container
            ]
        )
        
        # This container holds the sidebar and controls its animated width
        self.animating_sidebar_container = ft.Container(
            width=250,
            animate=ft.Animation(300, "ease"),
            content=sidebar_column_wrapper
        )

        main_column = ft.Column(
            expand=True,
            spacing=10,
            controls=[
                self.top_bar_right,
                self.main_content
            ]
        )

        self.controls = [
            ft.Row(
                expand=True,
                spacing=10,
                controls=[
                    self.animating_sidebar_container,
                    main_column
                ]
            )
        ]

    def toggle_sidebar(self, e):
        self.sidebar_expanded = not self.sidebar_expanded
        self.animating_sidebar_container.width = 250 if self.sidebar_expanded else 80
        
        # Simple, robust loop to toggle visibility
        for text_control in self.sidebar_texts:
            text_control.visible = self.sidebar_expanded
        
        self.page.update()

    def toggle_section(self, e):
        section_name = e.control.data
        header = self.nav_items[f"{section_name}_header"]
        items = self.nav_items[f"{section_name}_items"]
        
        items.visible = not items.visible
        header.controls[1].icon = 'arrow_drop_up' if items.visible else 'arrow_drop_down'
        self.page.update()
