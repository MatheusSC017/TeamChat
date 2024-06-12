from PyQt6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QAbstractButton,
    QScrollArea,
    QWidget
)
from Widgets.base import BaseWidget
from dotenv import load_dotenv
import keyring
import requests
import os

load_dotenv()

HOST = os.environ.get("HOST")
PORT = os.environ.get("PORT")


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
        for sub_channel in sub_channels:
            sub_channel_widget = QLabel(sub_channel)
            sub_channel_widget.setObjectName('subtitle')
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
        self.initUI(channel, sub_channels)
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
                channel_button = ChannelButton(channel, sub_channels['SubChannels'].keys(), self.base_path)
                channel_button.clicked.connect(self.open_channel_config)
                self.channels_layout.addWidget(channel_button)

    def open_channel_config(self):
        clicked_button = self.sender()
        self.update_channel_window = ChannelUpdate(clicked_button.channel,
                                                   clicked_button.sub_channels,
                                                   self.base_path,
                                                   self.screen_size)
        self.update_channel_window.show()

