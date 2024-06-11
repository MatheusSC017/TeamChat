from PyQt6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QHBoxLayout
)
from Widgets.base import BaseWidget
from dotenv import load_dotenv
import keyring
import requests
import os

load_dotenv()

HOST = os.environ.get("HOST")
PORT = os.environ.get("PORT")


class MyChannels(BaseWidget):
    def __init__(self, base_path, screen_size):
        super().__init__()

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
        self.channels = QVBoxLayout()

        master = QVBoxLayout()
        master.addWidget(title)
        master.addLayout(self.channels)

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
            channels = response.json()
            for channel, sub_channels in channels.items():
                sub_channels_layout = QHBoxLayout()
                sub_channels_layout.setContentsMargins(20, 0, 0, 0)
                for sub_channel in sub_channels:
                    sub_channel_label = QLabel(sub_channel)
                    sub_channel_label.setObjectName('sub_channel')
                    sub_channels_layout.addWidget(sub_channel_label)

                channel_layout = QVBoxLayout()
                channel_label = QLabel(channel)
                channel_label.setObjectName('channel')
                channel_layout.addWidget(channel_label)
                channel_layout.addLayout(sub_channels_layout)

                self.channels.addLayout(channel_layout)

