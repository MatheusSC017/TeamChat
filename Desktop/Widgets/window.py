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
    QTabWidget,
    QInputDialog,
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import pyqtSlot
from qasync import asyncSlot
from threading import Thread
from datetime import datetime
from dotenv import load_dotenv
import time
import asyncio
import keyring
import requests
import os
from Widgets import buttons, chat, base, connect, users, channels

load_dotenv()

HOST = os.environ.get("HOST")
PORT = os.environ.get("PORT")


class MainWindowUI(QMainWindow, base.BaseWidget):
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
        self.username_window = users.UpdateUsername(self.base_path, self.screen_size)
        self.users_online_window = users.UsersOnline(self.base_path, self.screen_size)
        self.user_register_window = users.RegisterUser(self.base_path, self.screen_size)
        self.login_window = users.LogIn(self.base_path, self.screen_size)
        self.account_config_window = users.AccountConfig(self.base_path, self.screen_size)
        self.my_channels_window = channels.MyChannels(self.base_path, self.screen_size)

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

        self.connect_menu = QAction("Connect")
        self.username_menu = QAction("Change Username")
        self.users_online_menu = QAction("Users")
        self.username_menu.setDisabled(True)
        self.users_online_menu.setDisabled(True)

        main_menu.addAction(self.connect_menu)
        main_menu.addAction(self.username_menu)
        main_menu.addAction(self.users_online_menu)

        user_menu = QMenu("User", self)
        menubar.addMenu(user_menu)
        self.register_menu = QAction("Register")
        self.login_menu = QAction("Login")
        self.account_menu = QAction("Account")
        self.my_channels_menu = QAction("My channels")
        self.logout_menu = QAction("Logout")
        token = keyring.get_password('system', 'TeamChatToken')
        if token is not None:
            self.logged_in_user_menu()
        else:
            self.logged_out_user_menu()

        user_menu.addAction(self.register_menu)
        user_menu.addAction(self.login_menu)
        user_menu.addAction(self.account_menu)
        user_menu.addAction(self.my_channels_menu)
        user_menu.addAction(self.logout_menu)

    def get_messages_ui(self):
        self.log_chat = self.create_chat_widget()

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

    def logged_in_user_menu(self):
        self.register_menu.setVisible(False)
        self.login_menu.setVisible(False)
        self.account_menu.setVisible(True)
        self.my_channels_menu.setVisible(True)
        self.logout_menu.setVisible(True)

    def logged_out_user_menu(self):
        self.register_menu.setVisible(True)
        self.login_menu.setVisible(True)
        self.account_menu.setVisible(False)
        self.my_channels_menu.setVisible(False)
        self.logout_menu.setVisible(False)


class Home(MainWindowUI):
    connected = False
    chat_handler = None
    chat_thread = None

    current_channel_ui = 'Global'

    direct_chats = {}
    log_chat = None
    sub_channel_chat = None

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
        self.register_menu.triggered.connect(self.open_user_register_ui)
        self.login_menu.triggered.connect(self.open_login_ui)
        self.account_menu.triggered.connect(self.open_account_window)
        self.my_channels_menu.triggered.connect(self.open_my_channels_window)
        self.logout_menu.triggered.connect(self.logout_user)

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
        self.chat_handler.joinAccepted.connect(self.join_ui)

        # Login
        self.login_window.logged_in_user.connect(self.logged_in_user_menu)

    def start_end_connection(self):
        self.create_connect_window() if not self.connected else self.end_chat()

    def create_connect_window(self):
        self.connect_window.show()
        self.setEnabled(False)

    @asyncSlot(str)
    async def start_chat(self, username):
        self.chat_thread.start()
        while self.chat_handler.websocket is None:
            time.sleep(0.1)
        self.connected = True
        await self.chat_handler.connect(username)

        self.started_chat_ui()

    @asyncSlot()
    async def end_chat(self):
        await self.chat_handler.disconnect()
        self.chat_thread.kill = True
        self.connected = False

        self.ended_chat_ui()

    def started_chat_ui(self):
        self.connect_menu.setText('Disconnect')
        self.log_chat.append('You connected to the server')

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

    def update_username_ui(self):
        self.username_window.show()

    @asyncSlot(str)
    async def update_username(self, username):
        await self.chat_handler.update_username(username)
        self.username_window.username_edit.clear()
        self.username_window.hide()

    def open_users_online_window(self):
        self.users_online_window.show()

    def open_user_register_ui(self):
        self.user_register_window.show()

    def open_login_ui(self):
        self.login_window.show()

    def logout_user(self):
        token = keyring.get_password('system', 'TeamChatToken')
        headers = {
            'Authorization': token
        }
        response = requests.post(f'{HOST}:{PORT}/logout/', headers=headers)
        if response.status_code == 200:
            keyring.delete_password('system', 'TeamChatToken')
            self.logged_out_user_menu()

    def open_account_window(self):
        self.account_config_window.show()

    def open_my_channels_window(self):
        self.my_channels_window.show()

    @pyqtSlot(list)
    def set_users_online(self, users_online):
        self.users_online.setText(f'{len(users_online) + 1} users online')
        self.clear_layout(self.users_online_window.users_online_layout)
        for user in users_online:
            user_button = buttons.PushButtonUser(user, self.base_path)
            user_button.clicked.connect(self.start_direct_chat)
            self.users_online_window.users_online_layout.addWidget(user_button)

    @pyqtSlot(list)
    def set_channels(self, channels):
        self.channels_availables.setText(f'{len(channels)} channels')

        self.clear_layout(self.channels_layout)

        for channel in channels:
            channel_button = buttons.PushButtonChannel(channel, False, self.base_path)
            channel_button.clicked.connect(self.get_sub_channels)
            self.channels_layout.addWidget(channel_button)

    @pyqtSlot()
    def get_sub_channels(self):
        clicked_button = self.sender()
        self.current_channel_ui = clicked_button.channel_name
        self.sub_channels_groupbox.setTitle(self.current_channel_ui)
        self.chat_handler.get_sub_channels(channel=clicked_button.channel_name)

    @asyncSlot(dict)
    async def set_sub_channels(self, sub_channels):
        self.clear_layout(self.sub_channels_layout)
        self.sub_channels_layouts = {}

        for sub_channel, configs in sub_channels.items():
            sub_channel_widget = buttons.PushButtonSubChannel(sub_channel, configs, self.base_path)
            sub_channel_widget.clicked.connect(self.join)
            self.sub_channels_layouts[(self.chat_handler.current_channel, sub_channel)] = sub_channel_widget

            self.sub_channels_layout.addWidget(sub_channel_widget)

    @pyqtSlot()
    def join(self):
        clicked_button = self.sender()
        new_channel = self.current_channel_ui
        new_sub_channel = clicked_button.sub_channel_name
        if self.chat_handler.current_channel != new_channel or self.chat_handler.current_sub_channel != new_sub_channel:
            if self.chat_handler.structure[new_channel][new_sub_channel].get('enable_password', False):
                password_input_dialog = QInputDialog(self)
                password_input_dialog.setWindowTitle("Password")
                password_input_dialog.setLabelText("Enter the password:")
                password_input_dialog.setTextEchoMode(QLineEdit.EchoMode.Password)
                if password_input_dialog.exec():
                    asyncio.create_task(self.chat_handler.join(new_channel, new_sub_channel, password_input_dialog.textValue()))
                return
            asyncio.create_task(self.chat_handler.join(new_channel, new_sub_channel))

    @pyqtSlot(str, str)
    def join_ui(self, channel, sub_channel):
        self.chat_handler.current_channel = channel
        self.chat_handler.current_sub_channel = sub_channel

        self.set_sub_channel_chat()
        self.enable_send_message()

    def set_sub_channel_chat(self):
        if self.sub_channel_chat is not None:
            self.tabs.removeTab(1)
            self.sub_channel_chat = None

        if self.chat_handler.current_channel != 'Global':
            self.sub_channel_chat = self.create_chat_widget()

            self.tabs.insertTab(1, self.sub_channel_chat, self.chat_handler.current_sub_channel)
            self.tabs.setCurrentIndex(1)
            self.sub_channel_chat.setPlainText(f"You have joined {self.chat_handler.current_channel} / "
                                               f"{self.chat_handler.current_sub_channel}")
        else:
            self.log_chat.append(f"You have joined {self.chat_handler.current_channel} / "
                                 f"{self.chat_handler.current_sub_channel}")

    @asyncSlot()
    async def send_message(self):
        recipient = self.tabs.tabText(self.tabs.currentIndex())

        if self.chat_handler.current_sub_channel != 'Logs':
            if self.chat_handler.current_sub_channel == recipient:
                recipient = None
                recipient_widget = self.sub_channel_chat
            else:
                recipient_widget = self.direct_chats[recipient]
            await self.chat_handler.send_input_message(self.message.text(), recipient=recipient)
            recipient_widget.append(f"{datetime.now().strftime('%d/%m/%y %H:%M:%S')} - {self.chat_handler.user}: "
                                    f"{self.message.text()}")
            self.message.clear()

    @pyqtSlot(str, str)
    def on_message_received(self, message, recipient):
        if recipient == 'Global':
            self.log_chat.append(message)
        elif recipient == 'Local':
            self.sub_channel_chat.append(message)
        else:
            if recipient not in self.direct_chats.keys():
                self.direct_chats[recipient] = self.create_chat_widget()

                index = self.tabs.addTab(self.direct_chats[recipient], recipient)
                self.tabs.setCurrentIndex(index)
            self.direct_chats[recipient].append(message)

    def start_direct_chat(self):
        username = self.sender().username
        if username not in self.direct_chats.keys():
            self.direct_chats[username] = self.create_chat_widget()

            self.tabs.addTab(self.direct_chats[username], username)
        self.tabs.setCurrentIndex(self.tabs.indexOf(self.direct_chats[username]))

    def create_chat_widget(self):
        chat = QTextEdit()
        chat.setReadOnly(True)
        return chat

    def enable_send_message(self):
        if self.chat_handler.current_channel == 'Global':
            self.message.setEnabled(False)
            self.button_send_message.setEnabled(False)
        else:
            self.message.setEnabled(True)
            self.button_send_message.setEnabled(True)

    def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)
        if self.connected:
            self.end_chat()
