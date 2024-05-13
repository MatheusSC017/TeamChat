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
import time
import faker
import asyncio
from Widgets import buttons, chat, base, connect, username, users
faker_instance = faker.Faker()


class Home(QMainWindow, base.BaseWidget):
    connected = False

    def __init__(self, screen_size, base_path):
        super().__init__()
        self.screen_size = screen_size
        self.base_path = base_path

        self.channels = []
        self.current_channel = 'Global'
        self.current_sub_channel = 'Logs'
        self.sub_channels_layouts = {}

        self.settings(screen_size)
        self.initUI()
        self.setStyleCSS(base_path / "Static/CSS/main.css")
        self.create_chat()

    def settings(self, screen_size):
        self.setWindowTitle("TeamChat")
        self.set_geometry_center(1000, 700, screen_size)

    def initUI(self):
        self.connect_window = connect.Connect(self.base_path, self.screen_size)
        self.connect_window.connectRequest.connect(self.start_chat)
        self.connect_window.closeSign.connect(self.close_connect_window)

        self.username_window = username.UpdateUsername(self.base_path, self.screen_size)
        self.username_window.updateUsername.connect(self.update_username)

        self.users_online_window = users.UsersOnline(self.base_path, self.screen_size)

        self.get_menu_ui()

        self.master = QHBoxLayout()
        self.master.addLayout(self.get_channels_ui(), 50)
        self.master.addLayout(self.get_messages_ui(), 50)

        central_widget = QWidget()
        central_widget.setLayout(self.master)
        self.setCentralWidget(central_widget)

    def get_menu_ui(self):
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        main_menu = QMenu("Main", self)
        menubar.addMenu(main_menu)

        self.connect_menu = QAction("Connect", self)
        self.username_menu = QAction("Change Username")
        self.users_online_menu = QAction("Users")
        self.username_menu.setDisabled(True)

        main_menu.addAction(self.connect_menu)
        main_menu.addAction(self.username_menu)
        main_menu.addAction(self.users_online_menu)

        self.connect_menu.triggered.connect(self.start_end_connection)
        self.username_menu.triggered.connect(self.update_username_ui)
        self.users_online_menu.triggered.connect(self.open_users_online_window)

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

        self.users_online = QLabel("0 users online")
        self.users_online.setFixedHeight(30)
        self.users_online.setFixedWidth(150)

        self.channels_availables = QLabel("0 channels")
        self.channels_availables.setFixedHeight(30)
        self.channels_availables.setFixedWidth(150)

        header_subpartition = QVBoxLayout()
        header_subpartition.addWidget(self.users_online)
        header_subpartition.addWidget(self.channels_availables)

        header = QHBoxLayout()
        header.addWidget(title)
        header.addLayout(header_subpartition)

        self.channels_layout = QVBoxLayout()

        container = QWidget()
        container.setContentsMargins(0, 0, 0, 0)
        container.setLayout(self.channels_layout)

        channels_scroll = QScrollArea()
        channels_scroll.setWidget(container)
        channels_scroll.setWidgetResizable(True)

        # Users
        self.sub_channels_layout = QVBoxLayout()
        self.sub_channels_layout.setContentsMargins(20, 10, 10, 10)

        self.sub_channels_groupbox = QGroupBox("Global")
        self.sub_channels_groupbox.setLayout(self.sub_channels_layout)

        self.user_opened_channel = QVBoxLayout()
        self.user_opened_channel.addWidget(self.sub_channels_groupbox)

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

    def create_chat(self):
        self.chat_handler = chat.ChatHandler()
        self.chat_handler.messageReceived.connect(self.on_message_received)
        self.chat_handler.setChannels.connect(self.set_channels)
        self.chat_handler.setSubChannels.connect(self.set_sub_channels)
        self.chat_handler.usersOnline.connect(self.set_users_online)
        self.chat_thread = Thread(target=asyncio.run, args=(self.chat_handler.handler(),))

    def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)
        if self.connected:
            self.end_chat()

    def start_end_connection(self):
        self.create_connect_window() if not self.connected else self.end_chat()

    def create_connect_window(self):
        self.connect_window.show()
        self.setEnabled(False)

    @pyqtSlot(str)
    def start_chat(self, username):
        self.chat_thread.start()
        while self.chat_handler.websocket is None:
            time.sleep(0.1)
        self.connected = True
        asyncio.run(self.chat_handler.connect(username))

        self.started_chat_ui()

    def end_chat(self):
        asyncio.run(self.chat_handler.disconnect())
        self.chat_thread.kill = True
        self.connected = False

        self.ended_chat_ui()

    def started_chat_ui(self):
        self.connect_menu.setText('Disconnect')
        self.chat.setPlainText('You connected to the server')

        self.username_menu.setDisabled(False)
        self.setEnabled(True)

        self.connect_window.username_edit.clear()
        self.connect_window.hide()

    def ended_chat_ui(self):
        self.connect_menu.setText('Connect')
        self.chat.append('You have disconnected from the server')

        self.username_menu.setDisabled(True)
        self.message.setEnabled(False)
        self.button_send_message.setEnabled(False)

    def close_connect_window(self):
        self.setEnabled(True)

    def join(self):
        clicked_button = self.sender()
        if self.current_sub_channel != clicked_button.sub_channel_name:
            old_sub_channel = self.current_sub_channel
            self.current_sub_channel = clicked_button.sub_channel_name
            asyncio.run(self.chat_handler.join(self.current_channel, self.current_sub_channel))

            user_label = self.sub_channels_layouts[(self.current_channel, old_sub_channel)].user_widgets[self.chat_handler.user]
            del self.sub_channels_layouts[(self.current_channel, old_sub_channel)].user_widgets[self.chat_handler.user]
            self.sub_channels_layouts[(self.current_channel, self.current_sub_channel)].user_widgets[self.chat_handler.user] = user_label
            self.sub_channels_layouts[(self.current_channel, old_sub_channel)].user_layout.removeWidget(user_label)
            self.sub_channels_layouts[(self.current_channel, self.current_sub_channel)].user_layout.addWidget(user_label)

            self.chat.setPlainText(f"You have joined {self.current_channel} / {self.current_sub_channel}")

            self.enable_send_message()

    def update_username_ui(self):
        self.username_window.show()

    @pyqtSlot(str)
    def update_username(self, username):
        asyncio.run(self.chat_handler.update_username(username))
        self.username_window.username_edit.clear()
        self.username_window.hide()

    def open_users_online_window(self):
        self.users_online_window.show()

    @pyqtSlot(list)
    def set_users_online(self, users_online):
        self.users_online.setText(f'{len(users_online)} users online')
        self.clear_layout(self.users_online_window.users_online_layout)
        for user in users_online:
            self.users_online_window.users_online_layout.addWidget(QLabel(user))

    def get_channels(self):
        asyncio.run(self.chat_handler.get_channels())

    @pyqtSlot(list)
    def set_channels(self, channels):
        self.channels_availables.setText(f'{len(channels)} channels')

        if self.channels == channels:
            return

        self.channels = channels
        self.clear_layout(self.channels_layout)

        for channel in channels:
            channel_button = buttons.PushButtonChannel(channel, False, self.base_path)
            channel_button.clicked.connect(self.get_sub_channels)
            self.channels_layout.addWidget(channel_button)

    def get_sub_channels(self):
        clicked_button = self.sender()
        if self.current_channel != clicked_button.channel_name:
            self.current_channel = clicked_button.channel_name
            self.sub_channels_groupbox.setTitle(self.current_channel)
            self.enable_send_message()
            asyncio.run(self.chat_handler.get_sub_channels(channel=self.current_channel))

    @pyqtSlot(dict)
    def set_sub_channels(self, sub_channels):
        self.clear_layout(self.sub_channels_layout)
        self.sub_channels_layouts = {}

        for sub_channel, users in sub_channels.items():
            sub_channel_widget = buttons.PushButtonSubChannel(sub_channel, users, self.base_path)
            sub_channel_widget.clicked.connect(self.join)
            self.sub_channels_layouts[(self.current_channel, sub_channel)] = sub_channel_widget

            self.sub_channels_layout.addWidget(sub_channel_widget)

        self.current_sub_channel = list(sub_channels.keys())[0]
        asyncio.run(self.chat_handler.join(channel=self.current_channel, sub_channel=self.current_sub_channel))

        user_label = QLabel(self.chat_handler.user)
        self.sub_channels_layouts[(self.current_channel, self.current_sub_channel)].user_widgets[self.chat_handler.user] = user_label
        self.sub_channels_layouts[(self.current_channel, self.current_sub_channel)].user_layout.addWidget(user_label)

        self.chat.setPlainText(f"You have joined {self.current_channel} / {self.current_sub_channel}")

    def send_message(self):
        asyncio.run(self.chat_handler.send_input_message(self.message.text()))
        self.chat.setPlainText(f"{self.chat.toPlainText()}\n"
                               f"{datetime.now().strftime('%d/%m/%y %H:%M:%S')} - {self.chat_handler.user}: "
                               f"{self.message.text()}")
        self.message.clear()

    @pyqtSlot(str)
    def on_message_received(self, message):
        self.chat.append(message)

    def enable_send_message(self):
        if self.current_channel == 'Global':
            self.message.setEnabled(False)
            self.button_send_message.setEnabled(False)
        else:
            self.message.setEnabled(True)
            self.button_send_message.setEnabled(True)

    @staticmethod
    def clear_layout(layout):
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            widget = item.widget()
            widget.setParent(None)
            layout.removeWidget(widget)
