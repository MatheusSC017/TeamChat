import time

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QMenuBar,
    QMenu,
    QTextEdit,
    QLineEdit,
    QScrollArea,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QGroupBox,
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import pyqtSlot
from threading import Thread
from datetime import datetime
import faker
import asyncio
from Widgets import buttons, chat
faker_instance = faker.Faker()


class Home(QMainWindow):
    connected = False

    def __init__(self, screen_size, base_path):
        super().__init__()
        self.base_path = base_path

        self.channel = None
        self.sub_channel = None
        self.sub_channels_layouts = {}

        self.settings(screen_size)
        self.initUI()
        self.setStyleCSS(base_path / "static/css/main.css")

        self.chat_handler = chat.ChatHandler()
        self.chat_handler.messageReceived.connect(self.on_message_received)
        self.chat_handler.setChannels.connect(self.set_channels)
        self.chat_handler.setSubChannels.connect(self.set_sub_channels)
        self.chat_thread = Thread(target=asyncio.run, args=(self.chat_handler.handler(),))

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

    def initUI(self):
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        main_menu = QMenu("Main", self)
        menubar.addMenu(main_menu)

        self.connect_action = QAction("Connect", self)
        main_menu.addAction(self.connect_action)

        self.connect_action.triggered.connect(self.start_end_connection)

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
        self.message.setEnabled(False)

        self.button_send_message = QPushButton("Send")
        self.button_send_message.setFixedHeight(40)
        self.button_send_message.clicked.connect(self.send_message)
        self.button_send_message.setEnabled(False)

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

        self.channels = QVBoxLayout()

        container = QWidget()
        container.setContentsMargins(0, 0, 0, 0)
        container.setLayout(self.channels)

        channels_scroll = QScrollArea()
        channels_scroll.setWidget(container)
        channels_scroll.setWidgetResizable(True)

        # Users
        self.group_channel_layout = QVBoxLayout()
        self.group_channel_layout.setContentsMargins(20, 10, 10, 10)

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

    def closeEvent(self):
        if self.connected:
            self.end_chat()

    def start_end_connection(self):
        self.start_chat() if not (self.connected) else self.end_chat()

    def start_chat(self):
        self.chat_thread.start()
        self.connected = True
        self.connect_action.setText('Disconnect')
        self.chat.setPlainText('You connected to the server')
        self.message.setEnabled(True)
        self.button_send_message.setEnabled(True)

    def end_chat(self):
        asyncio.run(self.chat_handler.disconnect())
        self.chat_thread.kill = True
        self.connected = False
        self.connect_action.setText('Connect')
        self.chat.append('You have disconnected from the server')
        self.message.setEnabled(False)
        self.button_send_message.setEnabled(False)

    def join(self):
        pass

    def get_channels(self):
        asyncio.run(self.chat_handler.get_channels())

    @pyqtSlot(list)
    def set_channels(self, channels):
        for channel in channels:
            channel_button = buttons.PushButtonChannel(channel, False, self.base_path)
            channel_button.clicked.connect(self.get_sub_channels)
            self.channels.addWidget(channel_button)

    def get_sub_channels(self):
        clicked_button = self.sender()
        self.channel = clicked_button.channel_name.text()
        asyncio.run(self.chat_handler.get_sub_channels(channel=self.channel))

    @pyqtSlot(dict)
    def set_sub_channels(self, sub_channels):
        self.clear_layout(self.group_channel_layout)

        for sub_channel, users in sub_channels.items():
            group_sub_channel_layout = QVBoxLayout()
            group_sub_channel_layout.setContentsMargins(30, 5, 5, 5)
            self.sub_channels_layouts[(self.channel, sub_channel)] = group_sub_channel_layout

            self.set_users(group_sub_channel_layout, users)

            group_sub_channel = QGroupBox(sub_channel)
            group_sub_channel.setLayout(group_sub_channel_layout)

            self.group_channel_layout.addWidget(group_sub_channel)

        self.sub_channel = list(sub_channels.keys())[0]
        asyncio.run(self.chat_handler.join(channel=self.channel, sub_channel=self.sub_channel))
        self.sub_channels_layouts[(self.channel, self.sub_channel)].addWidget(QLabel(self.chat_handler.user))
    def set_users(self, layout, users):
        for user in users:
            layout.addWidget(QLabel(user))

    def send_message(self):
        asyncio.run(self.chat_handler.send_input_message(self.message.text()))
        self.chat.setPlainText(f"{self.chat.toPlainText()}\n"
                               f"{datetime.now().strftime('%d/%m/%y %H:%M:%S')} - {self.chat_handler.user}: "
                               f"{self.message.text()}")
        self.message.clear()

    @pyqtSlot(str)
    def on_message_received(self, message):
        self.chat.append(message)

    @staticmethod
    def clear_layout(layout):
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            widget = item.widget()
            widget.setParent(None)
            layout.removeWidget(widget)
