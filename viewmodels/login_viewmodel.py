
from models.user import User

class LoginViewModel:
    def __init__(self):
        self.user = User(username="", password="")
        self.remember_credentials = False

    def set_username(self, username):
        self.user.username = username

    def set_password(self, password):
        self.user.password = password

    def set_remember(self, remember: bool):
        self.remember_credentials = bool(remember)

    def get_remember(self) -> bool:
        return self.remember_credentials

    def login(self):
        # Lógica de autenticação com banco de dados a ser implementada
        # Por enquanto, usando valores fixos para teste
        if self.user.username == "admin" and self.user.password == "admin":
            return True
        return False
