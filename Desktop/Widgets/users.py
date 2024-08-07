from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
)
from dotenv import load_dotenv
import requests
import os
import keyring

from Widgets.base import BaseWidget, BaseFormWindow
from Widgets.dialogs import WarningDialog, UpdatePasswordDialog

load_dotenv()

HOST = os.environ.get("HOST")
PORT = os.environ.get("PORT")


class UpdateUsername(BaseFormWindow):
    updateUsername = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        self.window_name = "Change username"

        super().__init__(*args, **kwargs)

        self.form_button.clicked.connect(self.connect_request)
        self.username_edit.returnPressed.connect(self.connect_request)

    def connect_request(self):
        user = self.username_edit.text()
        self.updateUsername.emit(user)


class UsersOnline(BaseWidget):
    def __init__(self, base_path, screen_size):
        super().__init__()

        self.settings(screen_size)
        self.initUI()
        self.setStyleCSS(base_path / "Static/CSS/users.css")

    def settings(self, screen_size):
        self.set_geometry_center(300, 700, screen_size, width_modifier=650, fixed=True)

    def initUI(self):
        title = QLabel("Users online")
        title.setFixedHeight(30)
        title.setObjectName("title")

        self.users_online_layout = QVBoxLayout()

        users_online = QWidget()
        users_online.setLayout(self.users_online_layout)

        master = QVBoxLayout()
        master.addWidget(title)
        master.addWidget(users_online)

        self.setLayout(master)


class RegisterUser(BaseWidget):
    def __init__(self, base_path, screen_size):
        super().__init__()

        self.settings(screen_size)
        self.initUI()
        self.setStyleCSS(base_path / "Static/CSS/users.css")

    def settings(self, screen_size):
        self.setWindowTitle("Register")
        self.set_geometry_center(400, 300, screen_size, fixed=True)

    def initUI(self):
        self.username = QLineEdit()
        self.username.returnPressed.connect(self.register_user)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.returnPressed.connect(self.register_user)
        self.nickname = QLineEdit()
        self.email = QLineEdit()
        self.register = QPushButton("Register")
        self.register.clicked.connect(self.register_user)

        master = QVBoxLayout()
        master.addWidget(QLabel("Username"))
        master.addWidget(self.username)
        master.addWidget(QLabel("Password"))
        master.addWidget(self.password)
        master.addWidget(QLabel("Nickname"))
        master.addWidget(self.nickname)
        master.addWidget(QLabel("E-mail"))
        master.addWidget(self.email)
        master.addWidget(self.register)

        self.setLayout(master)

    def register_user(self):
        user_data = {
            'username': self.username.text(),
            'password': self.password.text(),
            'nickname': self.nickname.text(),
            'email': self.email.text(),
        }
        response = requests.post(f'{HOST}:{PORT}/user/', data=user_data)
        if response.status_code == 201:
            self.username.clear()
            self.password.clear()
            self.nickname.clear()
            self.email.clear()
            self.hide()
            dlg = WarningDialog(self, "User registered")
        else:
            dlg = WarningDialog(self, "User register error", response.json().get('errors') or [] if response.content else [])

        dlg.exec()

        return response.json() if response.content else {}


class LogIn(BaseWidget):
    logged_in_user = pyqtSignal()

    def __init__(self, base_path, screen_size):
        super().__init__()
        self.settings(screen_size)
        self.initUI()
        self.setStyleCSS(base_path / "Static/CSS/users.css")

    def settings(self, screen_size):
        self.setWindowTitle('Log In')
        self.set_geometry_center(400, 200, screen_size, fixed=True)

    def initUI(self):
        self.username = QLineEdit()
        self.username.returnPressed.connect(self.send_request)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.returnPressed.connect(self.send_request)
        self.login = QPushButton('Log In')
        self.login.clicked.connect(self.send_request)

        self.form_layout = QVBoxLayout()
        self.form_layout.setContentsMargins(5, 5, 5, 20)
        self.form_layout.addWidget(QLabel("Username"))
        self.form_layout.addWidget(self.username)
        self.form_layout.addWidget(QLabel("Password"))
        self.form_layout.addWidget(self.password)

        master = QVBoxLayout()
        master.addLayout(self.form_layout)
        master.addWidget(self.login)

        self.setLayout(master)

    def send_request(self):
        user_data = {
            'username': self.username.text(),
            'password': self.password.text(),
        }
        response = requests.post(f'{HOST}:{PORT}/login/', data=user_data)
        if response.status_code == 200:
            if response.content:
                keyring.set_password('system', 'TeamChatToken', response.json().get('token'))
                self.logged_in_user.emit()

            self.username.clear()
            self.password.clear()
            self.hide()
            dlg = WarningDialog(self, "User logged in")
        else:
            dlg = WarningDialog(self, "Check username and password and try again")

        dlg.exec()


class AccountConfig(BaseWidget):
    def __init__(self, base_path, screen_size):
        super().__init__()

        self.settings(screen_size)
        self.initUI()
        self.setStyleCSS(base_path / "Static/CSS/users.css")

    def settings(self, screen_size):
        self.setWindowTitle('My Account')
        self.set_geometry_center(500, 300, screen_size, fixed=True)

    def initUI(self):
        self.username = QLineEdit()
        self.nickname = QLineEdit()
        self.email = QLineEdit()
        self.update_account_button = QPushButton('Update account')
        self.update_account_button.clicked.connect(self.update_account)
        self.update_password_button = QPushButton('Update password')
        self.update_password_button.clicked.connect(self.update_password)

        master = QVBoxLayout()
        master.addWidget(QLabel("Username"))
        master.addWidget(self.username)
        master.addWidget(QLabel("Nickname"))
        master.addWidget(self.nickname)
        master.addWidget(QLabel("E-mail"))
        master.addWidget(self.email)
        master.addWidget(self.update_account_button)
        master.addWidget(self.update_password_button)

        self.setLayout(master)

    def update_account(self):
        token = keyring.get_password('system', 'TeamChatToken')
        headers = {
            'Authorization': token
        }
        user_data = {
            'username': self.username.text(),
            'nickname': self.nickname.text(),
            'email': self.email.text(),
        }
        response = requests.put(f'{HOST}:{PORT}/user/', data=user_data, headers=headers)
        if response.status_code == 202:
            self.hide()
            dlg = WarningDialog(self, "User updated")
        else:
            dlg = WarningDialog(self, "Fail")

        dlg.exec()

    def update_password(self):
        update_password_dialog = UpdatePasswordDialog()
        if update_password_dialog.exec():
            new_password, confirm_password = update_password_dialog.getInputs()
            if new_password == confirm_password:
                token = keyring.get_password('system', 'TeamChatToken')
                headers = {
                    'Authorization': token
                }
                requests.post(f'{HOST}:{PORT}/user/update_password', headers=headers, data={'password': new_password})

    def show(self) -> None:
        super().show()
        token = keyring.get_password('system', 'TeamChatToken')
        headers = {
            'Authorization': token
        }
        response = requests.get(f'{HOST}:{PORT}/user/', headers=headers)
        if response.status_code == 200:
            data = response.json()
            self.username.setText(data.get('username', ''))
            self.nickname.setText(data.get('nickname', ''))
            self.email.setText(data.get('email', ''))
