from PyQt6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QAbstractButton,
    QScrollArea,
    QWidget,
    QLineEdit,
    QPushButton
)
from PyQt6.QtGui import QIntValidator
from Widgets.base import BaseWidget, LabeledLineEdit
from dotenv import load_dotenv
import keyring
import requests
import os

load_dotenv()

HOST = os.environ.get("HOST")
PORT = os.environ.get("PORT")


class SubChannelConfig(QWidget):
    def __init__(self, sub_channel, configs):
        super().__init__()
        self.initUI(sub_channel, configs)

    def initUI(self, sub_channel, configs):
        sub_channel_title = QLabel(sub_channel)
        sub_channel_title.setObjectName('subtitle')

        password_row = QHBoxLayout()
        self.enable_password = QPushButton("Enable password")
        self.enable_password.setCheckable(True)
        self.enable_password.setFixedWidth(200)
        self.enable_password.setFixedHeight(50)
        password_row.addWidget(self.enable_password)
        password_row.addStretch()
        self.password = LabeledLineEdit("Password")
        self.password.setFixedWidth(300)
        self.password.line_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setEnabled(False)
        password_row.addWidget(self.password)

        capacity_row = QHBoxLayout()
        self.limit_users = QPushButton("Limit Users")
        self.limit_users.setCheckable(True)
        self.limit_users.setFixedWidth(200)
        self.limit_users.setFixedHeight(50)
        capacity_row.addWidget(self.limit_users)
        capacity_row.addStretch()
        self.number_of_users = LabeledLineEdit("Number of Users")
        self.number_of_users.setFixedWidth(300)
        self.number_of_users.setEnabled(False)
        self.number_of_users.line_edit.setValidator(QIntValidator(2, 99))
        capacity_row.addWidget(self.number_of_users)

        users_row = QHBoxLayout()
        self.only_logged_in_users = QPushButton("Only Logged In Users")
        self.only_logged_in_users.setCheckable(True)
        self.only_logged_in_users.setFixedWidth(200)
        self.only_logged_in_users.setFixedHeight(50)
        users_row.addWidget(self.only_logged_in_users)
        users_row.addStretch()

        master = QVBoxLayout()
        master.addWidget(sub_channel_title)
        master.addLayout(password_row)
        master.addLayout(capacity_row)
        master.addLayout(users_row)
        self.setLayout(master)


class ChannelUpdate(BaseWidget):
    def __init__(self, channel, sub_channels, base_path, screen_size):
        super().__init__()
        self.base_path = base_path

        self.settings(screen_size)
        self.initUI(channel, sub_channels)
        self.setStyleCSS(base_path / "Static/CSS/channels.css")

    def settings(self, screen_size):
        self.setWindowTitle('Channel Update')
        self.set_geometry_center(700, 500, screen_size, fixed=True)

    def initUI(self, channel, sub_channels):
        title = QLabel(channel)
        title.setObjectName('title')

        sub_channels_layout = QVBoxLayout()
        for sub_channel, configs in sub_channels.items():
            sub_channel_widget = SubChannelConfig(sub_channel, configs)
            sub_channels_layout.addWidget(sub_channel_widget)

        container = QWidget()
        container.setLayout(sub_channels_layout)

        sub_channels_scroll = QScrollArea()
        sub_channels_scroll.setWidget(container)
        sub_channels_scroll.setWidgetResizable(True)

        master = QVBoxLayout()
        master.addWidget(title)
        master.addWidget(sub_channels_scroll)

        self.setLayout(master)


class ChannelButton(QAbstractButton, BaseWidget):
    def __init__(self, channel, sub_channels, base_path):
        super().__init__()

        self.channel = channel
        self.sub_channels = sub_channels

        self.settings()
        self.initUI(channel, sub_channels.keys())
        self.setStyleCSS(base_path / "Static/CSS/channels.css")

    def settings(self):
        self.setContentsMargins(0, 0, 0, 20)

    def initUI(self, channel, sub_channels):
        channel_layout = QVBoxLayout()
        channel_label = QLabel(channel)
        channel_label.setObjectName('subtitle')
        channel_layout.addWidget(channel_label)

        items_count = 0
        sub_channels_layout = QHBoxLayout()
        for sub_channel in sub_channels:
            sub_channel_label = QLabel(sub_channel)
            sub_channel_label.setObjectName('subtitle2')
            sub_channels_layout.addWidget(sub_channel_label)
            items_count += 1
            if items_count == 3:
                channel_layout.addLayout(sub_channels_layout)
                sub_channels_layout = QHBoxLayout()
                items_count = 0
        if items_count > 0:
            channel_layout.addLayout(sub_channels_layout)

        self.setLayout(channel_layout)

    def paintEvent(self, a0, QPaintEvent=None):
        pass


class MyChannels(BaseWidget):
    update_channel_window = None

    def __init__(self, base_path, screen_size):
        super().__init__()
        self.base_path = base_path
        self.screen_size = screen_size

        self.settings(screen_size)
        self.initUI()
        self.setStyleCSS(base_path / "Static/CSS/channels.css")

    def settings(self, screen_size):
        self.setWindowTitle('My Channels')
        self.set_geometry_center(700, 500, screen_size, fixed=True)

    def initUI(self):
        title = QLabel('Channels')
        title.setFixedHeight(30)
        title.setObjectName('title')
        self.channels_layout = QVBoxLayout()
        container = QWidget()
        container.setLayout(self.channels_layout)

        channels_scroll = QScrollArea()
        channels_scroll.setWidget(container)
        channels_scroll.setWidgetResizable(True)

        master = QVBoxLayout()
        master.addWidget(title)
        master.addWidget(channels_scroll)

        self.setLayout(master)

    def show(self) -> None:
        super().show()
        self.set_channels()

    def set_channels(self):
        token = keyring.get_password('system', 'token')
        headers = {
            'Authorization': token
        }
        response = requests.get(f'{HOST}:{PORT}/retrieve_channels/', headers=headers)
        if response.status_code == 200:
            self.channels = response.json()
            for channel, sub_channels in self.channels.items():
                channel_button = ChannelButton(channel, sub_channels, self.base_path)
                channel_button.clicked.connect(self.open_channel_config)
                self.channels_layout.addWidget(channel_button)

    def open_channel_config(self):
        clicked_button = self.sender()
        self.update_channel_window = ChannelUpdate(clicked_button.channel,
                                                   clicked_button.sub_channels,
                                                   self.base_path,
                                                   self.screen_size)
        self.update_channel_window.show()

