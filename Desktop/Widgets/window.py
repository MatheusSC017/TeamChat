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
    QTabWidget
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import pyqtSlot
from threading import Thread
from datetime import datetime
import time
import asyncio
from Widgets import buttons, chat, base, connect, username, users


class MainWindow(QMainWindow, base.BaseWidget):
    def __init__(self, screen_size, base_path):
        super().__init__()
        self.screen_size = screen_size
        self.base_path = base_path

        self.settings(screen_size)
        self.initUI()
        self.setStyleCSS(base_path / "Static/CSS/main.css")

    def settings(self, screen_size):
        self.setWindowTitle("TeamChat")
        self.set_geometry_center(1000, 700, screen_size)

    def initUI(self):
        self.connect_window = connect.Connect(self.base_path, self.screen_size)
        self.username_window = username.UpdateUsername(self.base_path, self.screen_size)
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
        self.users_online_menu.setDisabled(True)

        main_menu.addAction(self.connect_menu)
        main_menu.addAction(self.username_menu)
        main_menu.addAction(self.users_online_menu)

    def get_messages_ui(self):
        self.log_chat = QTextEdit()
        self.log_chat.setReadOnly(True)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.log_chat, 'Logs')

        self.message = QLineEdit()
        self.message.setFixedHeight(40)
        self.message.setEnabled(False)

        self.button_send_message = QPushButton("Send")
        self.button_send_message.setFixedHeight(40)
        self.button_send_message.setEnabled(False)

        message_group = QHBoxLayout()
        message_group.addWidget(self.message)
        message_group.addWidget(self.button_send_message)

        column = QVBoxLayout()
        column.addWidget(self.tabs)
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


class Home(MainWindow):
    connected = False
    chat_handler = None
    chat_thread = None

    chats = {}
    log_chat = None
    sub_channel_chat = None

    current_channel = 'Global'
    current_sub_channel = 'Logs'
    sub_channels_layouts = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.create_chat()
        self.create_widgets_connections()

    def create_chat(self):
        self.chat_handler = chat.ChatHandler()
        self.chat_thread = Thread(target=asyncio.run, args=(self.chat_handler.handler(),))

    def create_widgets_connections(self):
        # Menu components
        self.connect_menu.triggered.connect(self.start_end_connection)
        self.username_menu.triggered.connect(self.update_username_ui)
        self.users_online_menu.triggered.connect(self.open_users_online_window)

        # Sub window components
        self.connect_window.closeSign.connect(self.close_connect_window)
        self.connect_window.connectRequest.connect(self.start_chat)
        self.username_window.updateUsername.connect(self.update_username)

        # Message components
        self.message.returnPressed.connect(self.send_message)
        self.button_send_message.clicked.connect(self.send_message)

        # Chat handler
        self.chat_handler.messageReceived.connect(self.on_message_received)
        self.chat_handler.setChannels.connect(self.set_channels)
        self.chat_handler.setSubChannels.connect(self.set_sub_channels)
        self.chat_handler.usersOnline.connect(self.set_users_online)

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
        self.log_chat.setPlainText('You connected to the server')

        self.username_menu.setDisabled(False)
        self.users_online_menu.setDisabled(False)
        self.setEnabled(True)

        self.connect_window.username_edit.clear()
        self.connect_window.hide()

    def ended_chat_ui(self):
        self.connect_menu.setText('Connect')
        self.log_chat.append('You have disconnected from the server')

        self.username_menu.setDisabled(True)
        self.users_online_menu.setDisabled(True)
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

            self.set_sub_channel_chat()
            self.sub_channel_chat.setPlainText(f"You have joined {self.current_channel} / {self.current_sub_channel}")

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
        self.users_online.setText(f'{len(users_online) + 1} users online')
        self.clear_layout(self.users_online_window.users_online_layout)
        for user in users_online:
            user_button = buttons.PushButtonUser(user, self.base_path)
            user_button.clicked.connect(self.start_direct_chat)
            self.users_online_window.users_online_layout.addWidget(user_button)

    def get_channels(self):
        asyncio.run(self.chat_handler.get_channels())

    @pyqtSlot(list)
    def set_channels(self, channels):
        self.channels_availables.setText(f'{len(channels)} channels')

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

        self.set_sub_channel_chat()

    def set_sub_channel_chat(self):
        if self.sub_channel_chat is not None:
            self.tabs.removeTab(1)
            self.sub_channel_chat = None

        if self.current_sub_channel != 'Logs':
            self.sub_channel_chat = QTextEdit()
            self.sub_channel_chat.setReadOnly(True)

            self.tabs.insertTab(1, self.sub_channel_chat, self.current_sub_channel)
            self.tabs.setCurrentIndex(1)
            self.sub_channel_chat.setPlainText(f"You have joined {self.current_channel} / {self.current_sub_channel}")
        else:
            self.log_chat.setPlainText(f"You have joined {self.current_channel} / {self.current_sub_channel}")

    def send_message(self):
        recipient = self.tabs.tabText(self.tabs.currentIndex())

        if self.current_sub_channel != 'Logs':
            if self.current_sub_channel == recipient:
                recipient = None
                recipient_widget = self.sub_channel_chat
            else:
                recipient_widget = self.chats[recipient]
            asyncio.run(self.chat_handler.send_input_message(self.message.text(), recipient=recipient))
            recipient_widget.setPlainText(f"{recipient_widget.toPlainText()}\n"
                                          f"{datetime.now().strftime('%d/%m/%y %H:%M:%S')} - {self.chat_handler.user}: "
                                          f"{self.message.text()}")
            self.message.clear()

    @pyqtSlot(str, str)
    def on_message_received(self, message, recipient):
        if recipient == 'Global':
            self.log_chat.append(message)
        elif recipient == 'Local':
            self.sub_channel_chat.append(message)
        else:
            if recipient not in self.chats.keys():
                self.chats[recipient] = QTextEdit()
                self.chats[recipient].setReadOnly(True)

                index = self.tabs.addTab(self.chats[recipient], recipient)
                self.tabs.setCurrentIndex(index)
            self.chats[recipient].append(message)

    def start_direct_chat(self):
        clicked_button = self.sender()
        username = clicked_button.username
        if username not in self.chats.keys():
            self.chats[username] = QTextEdit()
            self.chats[username].setReadOnly(True)

            self.tabs.addTab(self.chats[username], username)
        self.tabs.setCurrentIndex(self.tabs.indexOf(self.chats[username]))

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

    def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)
        if self.connected:
            self.end_chat()
