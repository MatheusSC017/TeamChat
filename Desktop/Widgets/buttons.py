from PyQt6.QtWidgets import (
    QWidget,
    QAbstractButton,
    QLabel,
    QHBoxLayout,
    QVBoxLayout
)
from Widgets.base import BaseWidget, IconWidget


class PushButtonChannel(QAbstractButton, BaseWidget):
    def __init__(self, name, protected, base_path):
        super().__init__()
        self.channel_name = name

        self.initUI(name, protected, base_path)
        self.setStyleCSS(base_path / "Static/CSS/button.css")

    def initUI(self, name, protected, base_path):
        self.setContentsMargins(0, 0, 0, 0)

        channel_name = QLabel(name)
        channel_name.setFixedHeight(30)

        channel = QHBoxLayout()
        channel.addWidget(channel_name)
        channel.setObjectName("channel")

        self.setLayout(channel)

    def paintEvent(self, a0, QPaintEvent=None):
        pass


class PushButtonSubChannel(QAbstractButton, BaseWidget):
    def __init__(self, name, users, base_path):
        super().__init__()
        self.sub_channel_name = name

        self.initUI(name, users, base_path)
        self.setStyleCSS(base_path / "Static/CSS/button.css")

    def initUI(self, name, configs, base_path):
        self.user_layout = QVBoxLayout()
        self.set_users(self.user_layout, configs['Users'])

        sub_channel_header = QHBoxLayout()
        sub_channel_header.addWidget(QLabel(name))

        if configs.get('enable_password'):
            sub_channel_header.addWidget(IconWidget('padlock', base_path))
        if configs.get('only_logged_in_users'):
            sub_channel_header.addWidget(IconWidget('only_logged_in', base_path))
        if configs.get('limit_users'):
            sub_channel_header.addWidget(IconWidget('limit_users', base_path))
            limit_of_users = configs.get('number_of_users', 2)
            number_of_users = QLabel(f' {limit_of_users} ')
            number_of_users.setMaximumWidth(25)
            sub_channel_header.addWidget(number_of_users)

        user_list = QWidget()
        user_list.setLayout(self.user_layout)

        sub_channel = QVBoxLayout()
        sub_channel.addLayout(sub_channel_header)
        sub_channel.addWidget(user_list)
        sub_channel.setObjectName("sub_channel")

        self.setLayout(sub_channel)

    def set_users(self, layout, users):
        self.user_widgets = {}

        for user in users:
            self.user_widgets[user] = QLabel(user)
            layout.addWidget(self.user_widgets[user])

    def paintEvent(self, a0, QPaintEvent=None):
        pass


class PushButtonUser(QAbstractButton, BaseWidget):
    def __init__(self, name, base_path):
        super().__init__()
        self.username = name

        self.initUI(name)
        self.setStyleCSS(base_path / "Static/CSS/button.css")

    def initUI(self, name):
        user = QHBoxLayout()
        user.addWidget(QLabel(name))

        self.setLayout(user)

    def paintEvent(self, a0, QPaintEvent=None):
        pass
