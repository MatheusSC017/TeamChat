from PyQt6.QtWidgets import (
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)
from PyQt6.QtCore import pyqtSignal
from Widgets.base import BaseWidget
import random


class Connect(BaseWidget):
    connectRequest = pyqtSignal(str)

    def __init__(self, base_path, screen_size):
        super().__init__()

        self.settings(screen_size)
        self.initUI()
        self.setStyleCSS(base_path / "Static/CSS/main.css")

    def settings(self, screen_size):
        self.setWindowTitle("Connect")
        self.set_geometry_center(200, 100, screen_size)

    def initUI(self):
        username_edit = QLineEdit()
        connect_button = QPushButton("Conectar")

        connect_button.clicked.connect(self.connect_request)

        master = QVBoxLayout()
        master.addWidget(QLabel("Connection"))
        master.addWidget(username_edit)
        master.addWidget(connect_button)

        self.setLayout(master)

    def connect_request(self):
        user = f'user{random.randint(1111111, 9999999)}'
        self.connectRequest.emit(user)
