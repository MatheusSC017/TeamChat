from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
)
from dotenv import load_dotenv
import secretstorage
import requests
import os

from Widgets.base import BaseWidget, BaseFormWindow
from Widgets.dialogs import WarningDialog

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


class UserForm(BaseWidget):
    form_name = ""
    url = ""
    success_message = "Success"
    fail_message = "Fail"

    def __init__(self, base_path, screen_size):
        super().__init__()

        self.settings(screen_size)
        self.initUI()
        self.setStyleCSS(base_path / "Static/CSS/users.css")

    def settings(self, screen_size):
        self.setWindowTitle(self.form_name)
        self.set_geometry_center(400, 150, screen_size, fixed=True)

    def initUI(self):
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.send_form = QPushButton(self.form_name)
        self.send_form.clicked.connect(self.send_request)

        master = QVBoxLayout()
        master.addWidget(QLabel("Username"))
        master.addWidget(self.username)
        master.addWidget(QLabel("Password"))
        master.addWidget(self.password)
        master.addWidget(self.send_form)

        self.setLayout(master)

    def send_request(self):
        user_data = {
            'username': self.username.text(),
            'password': self.password.text(),
        }
        response = requests.post(self.url, data=user_data)
        if response.status_code in [200, 201]:
            self.username.clear()
            self.password.clear()
            self.hide()
            dlg = WarningDialog(self, self.success_message)
        else:
            dlg = WarningDialog(self, self.fail_message, response.json().get('errors') or [] if response.content else [])

        dlg.exec()

        return response.json() if response.content else {}


class RegisterUser(UserForm):
    def __init__(self, *args, **kwargs):
        self.form_name = "Register"
        self.url = f'{HOST}:{PORT}/register_user/'
        self.success_message = "User registered"
        self.fail_message = "User register error"
        super().__init__(*args, **kwargs)


class LogIn(UserForm):
    def __init__(self, *args, **kwargs):
        self.form_name = "Log In"
        self.url = f'{HOST}:{PORT}/login/'
        super().__init__(*args, **kwargs)

    def send_request(self):
        response_content = super().send_request()

        connection = secretstorage.dbus_init()
        collection = secretstorage.get_default_collection(connection)
        attributes = {'application': 'teamchat', }

        item = collection.create_item('token', attributes, response_content['token'].encode())
        return item
