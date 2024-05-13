from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
)

from Widgets.base import BaseWidget


class UsersOnline(BaseWidget):
    def __init__(self, base_path, screen_size):
        super().__init__()

        self.settings(screen_size)
        self.initUI()
        self.setStyleCSS(base_path / "Static/CSS/users.css")

    def settings(self, screen_size):
        self.setFixedWidth(300)
        self.setFixedHeight(700)
        self.set_geometry_center(300, 700, screen_size, width_modifier=650)

    def initUI(self):
        self.users_online_layout = QVBoxLayout()

        users_online = QWidget()
        users_online.setLayout(self.users_online_layout)

        master = QVBoxLayout()
        master.addWidget(QLabel("Users online"))
        master.addWidget(users_online)

        self.setLayout(master)
