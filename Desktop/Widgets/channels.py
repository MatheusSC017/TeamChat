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
from PyQt6.QtGui import QIntValidator, QPixmap, QIcon
from Widgets.base import BaseWidget, LabeledLineEdit
from PIL.ImageQt import ImageQt
from PIL import Image
from dotenv import load_dotenv
import keyring
import requests
import os

load_dotenv()

HOST = os.environ.get("HOST")
PORT = os.environ.get("PORT")


class SubChannelConfig(QWidget):
    def __init__(self, sub_channel, configs, base_path):
        super().__init__()

        self.base_path = base_path

        self.sub_channel = sub_channel
        self.initUI(sub_channel, configs)

    def initUI(self, sub_channel, configs):
        sub_channel_row = QHBoxLayout()
        sub_channel_title = QLabel(sub_channel)
        sub_channel_title.setObjectName('subtitle')
        sub_channel_row.addWidget(sub_channel_title)

        delete_sub_channel = QPushButton()
        delete_sub_channel.setCheckable(True)
        image = Image.open(self.base_path / "Static/Images/trash.png")
        pixmap = QPixmap.fromImage(ImageQt(image))
        delete_sub_channel.setIcon(QIcon(pixmap))
        delete_sub_channel.setFixedHeight(32)
        delete_sub_channel.setFixedWidth(32)

        sub_channel_row.addWidget(delete_sub_channel)

        password_row = QHBoxLayout()
        self.enable_password = QPushButton("Enable password")
        self.enable_password.clicked.connect(self.enable_password_field)
        self.enable_password.setCheckable(True)
        self.enable_password.setFixedWidth(200)
        self.enable_password.setFixedHeight(50)
        self.enable_password.setChecked(configs.get('enable_password', 0))
        password_row.addWidget(self.enable_password)
        password_row.addStretch()
        self.password = LabeledLineEdit("Password")
        self.password.setFixedWidth(300)
        self.password.line_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setEnabled(self.enable_password.isChecked())
        password_row.addWidget(self.password)

        capacity_row = QHBoxLayout()
        self.limit_users = QPushButton("Limit Users")
        self.limit_users.clicked.connect(self.enable_number_of_users_field)
        self.limit_users.setCheckable(True)
        self.limit_users.setFixedWidth(200)
        self.limit_users.setFixedHeight(50)
        self.limit_users.setChecked(configs.get('limit_users', 0))
        capacity_row.addWidget(self.limit_users)
        capacity_row.addStretch()
        self.number_of_users = LabeledLineEdit("Number of Users")
        self.number_of_users.setFixedWidth(300)
        self.number_of_users.setEnabled(self.limit_users.isChecked())
        self.number_of_users.line_edit.setValidator(QIntValidator(2, 99))
        self.number_of_users.line_edit.setText(str(configs.get('number_of_users', 0)))
        capacity_row.addWidget(self.number_of_users)

        users_row = QHBoxLayout()
        self.only_logged_in_users = QPushButton("Only Logged In Users")
        self.only_logged_in_users.setCheckable(True)
        self.only_logged_in_users.setFixedWidth(200)
        self.only_logged_in_users.setFixedHeight(50)
        self.only_logged_in_users.setChecked(configs.get('only_logged_in_users', 0))
        users_row.addWidget(self.only_logged_in_users)
        users_row.addStretch()

        master = QVBoxLayout()
        master.addLayout(sub_channel_row)
        master.addLayout(password_row)
        master.addLayout(capacity_row)
        master.addLayout(users_row)
        self.setLayout(master)

    def enable_password_field(self):
        if self.enable_password.isChecked():
            self.password.setEnabled(True)
        else:
            self.password.setEnabled(False)

    def enable_number_of_users_field(self):
        if self.limit_users.isChecked():
            self.number_of_users.setEnabled(True)
        else:
            self.number_of_users.setEnabled(False)

    def get_sub_channel_data(self):
        sub_channel_config = {
            'enable_password': self.enable_password.isChecked(),
            'limit_users': self.limit_users.isChecked(),
            'only_logged_in_users': self.only_logged_in_users.isChecked(),
        }
        if sub_channel_config['enable_password']:
            sub_channel_config['password'] = self.password.line_edit.text()

        if sub_channel_config['limit_users']:
            try:
                sub_channel_config['number_of_users'] = int(self.number_of_users.line_edit.text())
            except ValueError:
                sub_channel_config['number_of_users'] = 2

        return self.sub_channel, sub_channel_config


class ChannelUpdate(BaseWidget):
    def __init__(self, channel, sub_channels, base_path, screen_size):
        super().__init__()
        self.base_path = base_path

        self.channel = channel
        self.settings(screen_size)
        self.initUI(channel, sub_channels)
        self.setStyleCSS(base_path / "Static/CSS/channels.css")

    def settings(self, screen_size):
        self.setWindowTitle('Channel Update')
        self.set_geometry_center(700, 500, screen_size, fixed=True)

    def initUI(self, channel, sub_channels):
        title = QLabel(channel)
        title.setObjectName('title')

        self.sub_channels_layout = QVBoxLayout()
        for sub_channel, configs in sub_channels.items():
            sub_channel_widget = SubChannelConfig(sub_channel, configs, self.base_path)
            self.sub_channels_layout.addWidget(sub_channel_widget)

        container = QWidget()
        container.setLayout(self.sub_channels_layout)

        sub_channels_scroll = QScrollArea()
        sub_channels_scroll.setWidget(container)
        sub_channels_scroll.setWidgetResizable(True)

        options_row = QHBoxLayout()
        update_button = QPushButton('Update')
        update_button.clicked.connect(self.update_channel)
        options_row.addWidget(update_button)
        delete_button = QPushButton('Delete')
        options_row.addWidget(delete_button)

        master = QVBoxLayout()
        master.addWidget(title)
        master.addWidget(sub_channels_scroll)
        master.addLayout(options_row)

        self.setLayout(master)

    def update_channel(self):
        channel_configs = {
            'channel': self.channel,
            'sub_channels': {}
        }
        for i in range(self.sub_channels_layout.count()):
            sub_channel_widget = self.sub_channels_layout.itemAt(i).widget()
            sub_channel, config = sub_channel_widget.get_sub_channel_data()
            channel_configs['sub_channels'][sub_channel] = config

        token = keyring.get_password('system', 'token')
        headers = {
            'Authorization': token
        }
        response = requests.put(f'{HOST}:{PORT}/channel/update/', headers=headers, json=channel_configs)


class ChannelButton(QAbstractButton, BaseWidget):
    def __init__(self, channel, sub_channels, base_path):
        super().__init__()

        self.base_path = base_path
        self.channel = channel
        self.sub_channels = sub_channels

        self.settings()
        self.initUI(channel, sub_channels.keys())
        self.setStyleCSS(base_path / "Static/CSS/channels.css")

    def settings(self):
        self.setContentsMargins(0, 0, 0, 20)

    def initUI(self, channel, sub_channels):
        channel_layout = QVBoxLayout()

        channel_header = QHBoxLayout()
        channel_label = QLabel(channel)
        channel_label.setObjectName('subtitle')
        channel_header.addWidget(channel_label)

        delete_channel = QPushButton()
        delete_channel.setCheckable(True)
        image = Image.open(self.base_path / "Static/Images/trash.png")
        pixmap = QPixmap.fromImage(ImageQt(image))
        delete_channel.setIcon(QIcon(pixmap))
        delete_channel.setFixedHeight(32)
        delete_channel.setFixedWidth(32)
        channel_header.addWidget(delete_channel)

        channel_layout.addLayout(channel_header)

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
        response = requests.get(f'{HOST}:{PORT}/channel/retrieve/', headers=headers)
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

