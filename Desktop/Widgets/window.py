from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QTextEdit,
    QLineEdit,
    QScrollArea,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QGroupBox,
)
from PyQt6.QtCore import pyqtSlot
from threading import Thread
import faker
import asyncio
from random import choice
from datetime import datetime
from Widgets import buttons, chat
faker_instance = faker.Faker()


class Home(QMainWindow):
    def __init__(self, screen_size, base_path):
        super().__init__()
        self.base_path = base_path

        self.settings(screen_size)
        self.initUI()
        self.setStyleCSS(base_path / "static/css/style.css")

        self.message_handler = chat.MessageHandler()
        self.message_handler.messageReceived.connect(self.on_message_received)

    def start_chat(self):
        chat_thread = Thread(target=asyncio.run, args=(self.message_handler.handler(),))
        chat_thread.start()

    @pyqtSlot(str)
    def on_message_received(self, message):
        self.chat.append(message)

    def initUI(self):
        self.master = QHBoxLayout()
        self.master.addLayout(self.get_channels_ui(), 50)
        self.master.addLayout(self.get_messages_ui(), 50)

        central_widget = QWidget()
        central_widget.setLayout(self.master)
        self.setCentralWidget(central_widget)

    def get_messages_ui(self):
        self.chat = QTextEdit()
        self.chat.setReadOnly(True)

        self.message = QLineEdit()
        self.message.setFixedHeight(40)
        self.message.returnPressed.connect(self.send_message)
        # self.message.setEnabled(False)

        self.button_send_message = QPushButton("Send")
        self.button_send_message.setFixedHeight(40)
        self.button_send_message.clicked.connect(self.send_message)
        # self.button_send_message.setEnabled(False)

        message_group = QHBoxLayout()
        message_group.addWidget(self.message)
        message_group.addWidget(self.button_send_message)

        column = QVBoxLayout()
        column.addWidget(self.chat)
        column.addLayout(message_group)
        return column

    def get_channels_ui(self):
        # Header
        title = QLabel("TeamChat")
        title.setObjectName("title")

        self.users_online = QLabel("512 users online")
        self.users_online.setFixedHeight(30)
        self.users_online.setFixedWidth(150)

        self.channels_availables = QLabel("127 channels")
        self.channels_availables.setFixedHeight(30)
        self.channels_availables.setFixedWidth(150)

        header_subpartition = QVBoxLayout()
        header_subpartition.addWidget(self.users_online)
        header_subpartition.addWidget(self.channels_availables)

        header = QHBoxLayout()
        header.addWidget(title)
        header.addLayout(header_subpartition)

        # Channels
        self.channels = QVBoxLayout()
        self.get_channels()

        container = QWidget()
        container.setContentsMargins(0, 0, 0, 0)
        container.setLayout(self.channels)

        channels_scroll = QScrollArea()
        channels_scroll.setWidget(container)
        channels_scroll.setWidgetResizable(True)

        # Users
        self.group_channel_layout = QVBoxLayout()
        self.group_channel_layout.setContentsMargins(20, 10, 10, 10)

        self.get_sub_channel("Sub-Channel")
        self.get_sub_channel("Sub-Channel 2")
        self.get_sub_channel("Sub-Channel 3")

        group_channel = QGroupBox("Channel opened")
        group_channel.setLayout(self.group_channel_layout)

        self.user_opened_channel = QVBoxLayout()
        self.user_opened_channel.addWidget(group_channel)

        opened_channel = QWidget()
        opened_channel.setLayout(self.user_opened_channel)

        self.users_scroll = QScrollArea()
        self.users_scroll.setWidget(opened_channel)
        self.users_scroll.setWidgetResizable(True)

        column = QVBoxLayout()
        column.addLayout(header)
        column.addWidget(channels_scroll)
        column.addWidget(self.users_scroll)
        return column

    def setStyleCSS(self, css_file_path):
        with open(css_file_path, "r") as css:
            self.setStyleSheet(css.read())

    def settings(self, screen_size):
        self.setWindowTitle("TeamChat")
        self.set_geometry_center(1000, 700, screen_size)

    def set_geometry_center(self, width, height, screen_size):
        window_center_x = (screen_size.width() - width) // 2
        window_center_y = (screen_size.height() - height) // 2
        self.setGeometry(window_center_x, window_center_y, width, height)

    def get_channels(self):
        for i in range(30):
            channel_info = {
                'name': faker_instance.first_name(),
                'protected': choice([True, False])
            }

            channel_button = buttons.PushButtonChannel(channel_info['name'], channel_info['protected'], self.base_path)
            self.channels.addWidget(channel_button)

    def get_sub_channel(self, name):
        group_sub_channel_layout = QVBoxLayout()
        group_sub_channel_layout.setContentsMargins(30, 5, 5, 5)

        self.get_users(group_sub_channel_layout)

        group_sub_channel = QGroupBox(name)
        group_sub_channel.setLayout(group_sub_channel_layout)

        self.group_channel_layout.addWidget(group_sub_channel)

    def get_users(self, layout):
        layout.addWidget(QLabel(faker_instance.first_name()))
        layout.addWidget(QLabel(faker_instance.first_name()))
        layout.addWidget(QLabel(faker_instance.first_name()))
        layout.addWidget(QLabel(faker_instance.first_name()))
        layout.addWidget(QLabel(faker_instance.first_name()))

    def send_message(self):
        self.chat.setPlainText(f"{self.chat.toPlainText()}\n{datetime.now().strftime('%d/%m/%y %H:%M:%S')} - username: {self.message.text()}")
        self.message.setText("")
