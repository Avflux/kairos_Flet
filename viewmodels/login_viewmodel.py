
from models.user import User

class LoginViewModel:
    def __init__(self):
        self.user = User(username="", password="")

    def set_username(self, username):
        self.user.username = username

    def set_password(self, password):
        self.user.password = password

    def login(self):
        # Lógica de autenticação com banco de dados a ser implementada
        # Por enquanto, usando valores fixos para teste
        if self.user.username == "admin" and self.user.password == "admin":
            return True
        return False
