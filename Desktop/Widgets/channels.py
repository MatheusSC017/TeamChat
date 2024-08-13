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
from PyQt6.QtCore import pyqtSlot, pyqtSignal
from Widgets.base import BaseWidget, LabeledLineEdit
from Widgets.dialogs import WarningDialog
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
        master = QVBoxLayout()
        master.addLayout(self.get_sub_channel_form_ui(sub_channel))
        master.addLayout(self.get_password_form_ui(configs))
        master.addLayout(self.get_capacity_form_ui(configs))
        master.addLayout(self.get_users_form_ui(configs))
        self.setLayout(master)

    def get_sub_channel_form_ui(self, sub_channel):
        master = QHBoxLayout()
        sub_channel_title = QLabel(sub_channel)
        sub_channel_title.setObjectName('subtitle')
        master.addWidget(sub_channel_title)

        self.delete_sub_channel = QPushButton()
        self.delete_sub_channel.setCheckable(True)
        image = Image.open(self.base_path / "Static/Images/trash.png")
        pixmap = QPixmap.fromImage(ImageQt(image))
        self.delete_sub_channel.setIcon(QIcon(pixmap))
        self.delete_sub_channel.setFixedHeight(32)
        self.delete_sub_channel.setFixedWidth(32)

        master.addWidget(self.delete_sub_channel)
        return master

    def get_password_form_ui(self, configs):
        master = QHBoxLayout()
        self.enable_password = QPushButton("Enable password")
        self.enable_password.clicked.connect(self.enable_password_field)
        self.enable_password.setCheckable(True)
        self.enable_password.setFixedWidth(200)
        self.enable_password.setFixedHeight(50)
        self.enable_password.setChecked(configs.get('enable_password', 0))
        master.addWidget(self.enable_password)
        master.addStretch()
        self.password = LabeledLineEdit("Password")
        self.password.setFixedWidth(300)
        self.password.line_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setEnabled(self.enable_password.isChecked())
        master.addWidget(self.password)
        return master

    def get_capacity_form_ui(self, configs):
        master = QHBoxLayout()
        self.limit_users = QPushButton("Limit Users")
        self.limit_users.clicked.connect(self.enable_number_of_users_field)
        self.limit_users.setCheckable(True)
        self.limit_users.setFixedWidth(200)
        self.limit_users.setFixedHeight(50)
        self.limit_users.setChecked(configs.get('limit_users', 0))
        master.addWidget(self.limit_users)
        master.addStretch()
        self.number_of_users = LabeledLineEdit("Number of Users")
        self.number_of_users.setFixedWidth(300)
        self.number_of_users.setEnabled(self.limit_users.isChecked())
        self.number_of_users.line_edit.setValidator(QIntValidator(2, 99))
        self.number_of_users.line_edit.setText(str(configs.get('number_of_users', 0)))
        master.addWidget(self.number_of_users)
        return master

    def get_users_form_ui(self, configs):
        master = QHBoxLayout()
        self.only_logged_in_users = QPushButton("Only Logged In Users")
        self.only_logged_in_users.setCheckable(True)
        self.only_logged_in_users.setFixedWidth(200)
        self.only_logged_in_users.setFixedHeight(50)
        self.only_logged_in_users.setChecked(configs.get('only_logged_in_users', 0))
        master.addWidget(self.only_logged_in_users)
        master.addStretch()
        return master

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


class NewSubChannel(BaseWidget):
    subChannelRegistered = pyqtSignal(str)

    def __init__(self, base_path, screen_size, channel):
        super().__init__()
        self.base_path = base_path
        self.screen_size = screen_size

        self.channel = channel
        self.settings(screen_size)
        self.initUI()
        self.setStyleCSS(base_path / "Static/CSS/channels.css")

    def settings(self, screen_size):
        self.setWindowTitle('New Channel')
        self.set_geometry_center(250, 100, screen_size, fixed=True)

    def initUI(self):
        self.sub_channel_name = QLineEdit()
        register_sub_channel = QPushButton('Register')
        register_sub_channel.clicked.connect(self.register_sub_channel)

        master = QVBoxLayout()
        master.addWidget(QLabel('Name'))
        master.addWidget(self.sub_channel_name)
        master.addWidget(register_sub_channel)
        self.setLayout(master)

    def register_sub_channel(self):
        channel_data = {
            'channel': self.channel,
            'sub_channel': self.sub_channel_name.text(),
        }
        token = keyring.get_password('system', 'TeamChatToken')
        headers = {
            'Authorization': token
        }
        response = requests.post(f'{HOST}:{PORT}/channel/sub_channels/', headers=headers, json=channel_data)
        if response.status_code == 201:
            dlg = WarningDialog(self, f'{self.sub_channel_name.text()} registered')
            dlg.exec()
            self.subChannelRegistered.emit(self.sub_channel_name.text())
            self.sub_channel_name.setText('')
            self.close()
        else:
            dlg = WarningDialog(self, f'{self.sub_channel_name.text()} not registered')
            dlg.exec()


class SubChannelUpdate(BaseWidget):
    subChannelsDeleted = pyqtSignal(str, list)
    subChannelsInserted = pyqtSignal(str, str)
    new_sub_channel_window = None

    def __init__(self, channel, sub_channels, base_path, screen_size):
        super().__init__()
        self.base_path = base_path

        self.channel = channel
        self.screen_size = screen_size
        self.settings(screen_size)
        self.initUI(channel, sub_channels)
        self.setStyleCSS(base_path / "Static/CSS/channels.css")

    def settings(self, screen_size):
        self.setWindowTitle('Channel Update')
        self.set_geometry_center(700, 500, screen_size, fixed=True)

    def initUI(self, channel, sub_channels):
        title = QLabel(channel)
        title.setObjectName('title')

        master = QVBoxLayout()
        master.addWidget(title)
        master.addWidget(self.get_sub_channels_area_ui(sub_channels))
        master.addLayout(self.get_options_menu_ui())

        self.setLayout(master)

    def get_sub_channels_area_ui(self, sub_channels):
        self.sub_channels_layout = QVBoxLayout()
        for sub_channel, configs in sub_channels.items():
            sub_channel_widget = SubChannelConfig(sub_channel, configs, self.base_path)
            self.sub_channels_layout.addWidget(sub_channel_widget)

        container = QWidget()
        container.setLayout(self.sub_channels_layout)

        sub_channels_scroll = QScrollArea()
        sub_channels_scroll.setWidget(container)
        sub_channels_scroll.setWidgetResizable(True)
        return sub_channels_scroll

    def get_options_menu_ui(self):
        master = QHBoxLayout()

        insert_button = QPushButton('Insert')
        insert_button.clicked.connect(self.open_new_sub_channel_window)
        master.addWidget(insert_button)

        update_button = QPushButton('Update')
        update_button.clicked.connect(self.update_sub_channels)
        master.addWidget(update_button)

        delete_button = QPushButton('Delete')
        delete_button.clicked.connect(self.delete_sub_channels)
        master.addWidget(delete_button)

        return master

    def open_new_sub_channel_window(self):
        if self.new_sub_channel_window is None:
            self.new_sub_channel_window = NewSubChannel(self.base_path, self.screen_size, self.channel)
            self.new_sub_channel_window.subChannelRegistered.connect(self.update_sub_channels_list)

        self.new_sub_channel_window.show()

    @pyqtSlot(str)
    def update_sub_channels_list(self, sub_channel):
        sub_channel_widget = SubChannelConfig(sub_channel, {}, self.base_path)
        self.sub_channels_layout.addWidget(sub_channel_widget)
        self.subChannelsInserted.emit(self.channel, sub_channel)

    def update_sub_channels(self):
        channel_configs = {
            'channel': self.channel,
            'sub_channels': {}
        }
        for i in range(self.sub_channels_layout.count()):
            sub_channel_widget = self.sub_channels_layout.itemAt(i).widget()
            sub_channel, config = sub_channel_widget.get_sub_channel_data()
            channel_configs['sub_channels'][sub_channel] = config

        token = keyring.get_password('system', 'TeamChatToken')
        headers = {
            'Authorization': token
        }
        requests.put(f'{HOST}:{PORT}/channel/sub_channels/', headers=headers, json=channel_configs)

    def delete_sub_channels(self):
        request_data = {
            'channel': self.channel,
            'sub_channels': []
        }
        token = keyring.get_password('system', 'TeamChatToken')
        headers = {
            'Authorization': token
        }
        for i in reversed(range(self.sub_channels_layout.count())):
            sub_channel_widget = self.sub_channels_layout.itemAt(i).widget()
            if sub_channel_widget.delete_sub_channel.isChecked():
                request_data['sub_channels'].append(sub_channel_widget.sub_channel)

        response = requests.delete(f'{HOST}:{PORT}/channel/sub_channels/', headers=headers, json=request_data)

        if response.status_code == 200:
            for i in reversed(range(self.sub_channels_layout.count())):
                sub_channel_widget = self.sub_channels_layout.itemAt(i).widget()
                if sub_channel_widget.delete_sub_channel.isChecked():
                    self.sub_channels_layout.removeWidget(sub_channel_widget)
                    sub_channel_widget.setParent(None)
            self.subChannelsDeleted.emit(self.channel, request_data['sub_channels'])


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
        channel_layout.addLayout(self.get_header_ui(channel))

        self.sub_channels_layout = QVBoxLayout()
        self.set_sub_channels(sub_channels)
        channel_layout.addLayout(self.sub_channels_layout)

        channel_layout.addLayout(self.get_update_button_ui())

        self.setLayout(channel_layout)

    def get_header_ui(self, channel):
        master = QHBoxLayout()
        self.channel_form = QLineEdit(channel)
        self.channel_form.setEnabled(False)
        self.channel_form.setObjectName('subtitle')
        master.addWidget(self.channel_form)

        self.update_channel_icon = QPushButton()
        image = Image.open(self.base_path / "Static/Images/pencil.png")
        self.update_channel_icon.clicked.connect(self.update_channel_form)
        pixmap = QPixmap.fromImage(ImageQt(image))
        self.update_channel_icon.setIcon(QIcon(pixmap))
        self.update_channel_icon.setFixedHeight(32)
        self.update_channel_icon.setFixedWidth(32)
        master.addWidget(self.update_channel_icon)

        delete_channel = QPushButton()
        delete_channel.clicked.connect(self.delete_channel)
        image = Image.open(self.base_path / "Static/Images/trash.png")
        pixmap = QPixmap.fromImage(ImageQt(image))
        delete_channel.setIcon(QIcon(pixmap))
        delete_channel.setFixedHeight(32)
        delete_channel.setFixedWidth(32)
        master.addWidget(delete_channel)
        return master

    def get_update_button_ui(self):
        update_layout = QHBoxLayout()
        update_layout.setContentsMargins(0, 25, 0, 0)
        update_layout.addStretch()
        self.update_button = QPushButton("Update")
        self.update_button.clicked.connect(self.update_channel)
        self.update_button.setVisible(False)
        self.update_button.setFixedHeight(25)
        self.update_button.setFixedWidth(200)
        update_layout.addWidget(self.update_button)
        return update_layout

    def update_channel_form(self):
        self.update_button.setVisible(True)
        self.channel_form.setEnabled(True)
        self.update_channel_icon.setEnabled(False)

    def update_channel(self):
        channel_data = {
            'old_channel_name': self.channel,
            'new_channel_name': self.channel_form.text(),
        }
        token = keyring.get_password('system', 'TeamChatToken')
        headers = {
            'Authorization': token
        }
        response = requests.put(f'{HOST}:{PORT}/channel/', headers=headers, json=channel_data)
        if response.status_code == 200:
            dlg = WarningDialog(self, f'{self.channel_form.text()} updated')
            dlg.exec()
            self.update_button.setVisible(False)
            self.channel_form.setEnabled(False)
            self.update_channel_icon.setEnabled(True)
        else:
            dlg = WarningDialog(self, f'{self.channel_form.text()} not updated')
            dlg.exec()

    def delete_channel(self):
        channel_data = {
            'channel': self.channel,
        }
        token = keyring.get_password('system', 'TeamChatToken')
        headers = {
            'Authorization': token
        }
        response = requests.delete(f'{HOST}:{PORT}/channel/', headers=headers, json=channel_data)
        if response.status_code == 200:
            self.setParent(None)

    def set_sub_channels(self, sub_channels):
        self.clear_layout(self.sub_channels_layout)
        items_count = 0
        sub_channels_sub_layout = QHBoxLayout()
        for sub_channel in sub_channels:
            sub_channel_label = QLabel(sub_channel)
            sub_channel_label.setObjectName('subtitle2')
            sub_channels_sub_layout.addWidget(sub_channel_label)
            items_count += 1
            if items_count == 3:
                self.sub_channels_layout.addLayout(sub_channels_sub_layout)
                sub_channels_sub_layout = QHBoxLayout()
                items_count = 0
        if items_count > 0:
            self.sub_channels_layout.addLayout(sub_channels_sub_layout)

    def paintEvent(self, a0, QPaintEvent=None):
        pass


class NewChannel(BaseWidget):
    channelRegistered = pyqtSignal(str)

    def __init__(self, base_path, screen_size):
        super().__init__()
        self.base_path = base_path
        self.screen_size = screen_size

        self.settings(screen_size)
        self.initUI()
        self.setStyleCSS(base_path / "Static/CSS/channels.css")

    def settings(self, screen_size):
        self.setWindowTitle('New Channel')
        self.set_geometry_center(250, 100, screen_size, fixed=True)

    def initUI(self):
        self.channel_name = QLineEdit()
        register_channel = QPushButton('Register')
        register_channel.clicked.connect(self.register_channel)

        master = QVBoxLayout()
        master.addWidget(QLabel('Name'))
        master.addWidget(self.channel_name)
        master.addWidget(register_channel)
        self.setLayout(master)

    def register_channel(self):
        channel_data = {
            'channel': self.channel_name.text(),
        }
        token = keyring.get_password('system', 'TeamChatToken')
        headers = {
            'Authorization': token
        }
        response = requests.post(f'{HOST}:{PORT}/channel/', headers=headers, json=channel_data)
        if response.status_code == 201:
            dlg = WarningDialog(self, f'{self.channel_name.text()} registered')
            dlg.exec()
            self.channelRegistered.emit(self.channel_name.text())
            self.channel_name.setText('')
            self.close()
        else:
            dlg = WarningDialog(self, f'{self.channel_name.text()} not registered')
            dlg.exec()


class MyChannels(BaseWidget):
    update_channel_window = None
    new_channel_window = None

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

        new_channel = QPushButton('New Channel')
        new_channel.clicked.connect(self.open_new_channel_window)

        master = QVBoxLayout()
        master.addWidget(title)
        master.addWidget(self.get_channels_area_ui())
        master.addWidget(new_channel)

        self.setLayout(master)

    def get_channels_area_ui(self):
        self.channels_layout = QVBoxLayout()
        container = QWidget()
        container.setLayout(self.channels_layout)

        channels_scroll = QScrollArea()
        channels_scroll.setWidget(container)
        channels_scroll.setWidgetResizable(True)
        return channels_scroll

    def show(self) -> None:
        super().show()
        self.set_channels()

    def set_channels(self):
        token = keyring.get_password('system', 'TeamChatToken')
        headers = {
            'Authorization': token
        }
        response = requests.get(f'{HOST}:{PORT}/channel/', headers=headers)
        if response.status_code == 200:
            self.clear_layout(self.channels_layout)
            self.channels = response.json()
            for channel, sub_channels in self.channels.items():
                channel_button = ChannelButton(channel, sub_channels, self.base_path)
                channel_button.clicked.connect(self.open_channel_config)
                self.channels_layout.addWidget(channel_button)

    def open_new_channel_window(self):
        if self.new_channel_window is None:
            self.new_channel_window = NewChannel(self.base_path, self.screen_size)
            self.new_channel_window.channelRegistered.connect(self.update_channels_list)

        self.new_channel_window.show()

    @pyqtSlot(str)
    def update_channels_list(self, channel):
        channel_button = ChannelButton(channel, {}, self.base_path)
        channel_button.clicked.connect(self.open_channel_config)
        self.channels_layout.addWidget(channel_button)

    def open_channel_config(self):
        clicked_button = self.sender()
        self.update_channel_window = SubChannelUpdate(clicked_button.channel,
                                                      clicked_button.sub_channels,
                                                      self.base_path,
                                                      self.screen_size)
        self.update_channel_window.subChannelsDeleted.connect(self.sub_channels_deleted)
        self.update_channel_window.subChannelsInserted.connect(self.sub_channels_inserted)
        self.update_channel_window.show()

    @pyqtSlot(str, list)
    def sub_channels_deleted(self, channel, sub_channels):
        for i in reversed(range(self.channels_layout.count())):
            channel_button = self.channels_layout.itemAt(i).widget()
            if channel_button.channel == channel:
                for sub_channel in sub_channels:
                    del channel_button.sub_channels[sub_channel]

                channel_button.set_sub_channels(channel_button.sub_channels)
                break

    @pyqtSlot(str, str)
    def sub_channels_inserted(self, channel, sub_channel):
        for i in reversed(range(self.channels_layout.count())):
            channel_button = self.channels_layout.itemAt(i).widget()
            if channel_button.channel == channel:
                channel_button.sub_channels[sub_channel] = {}

                channel_button.set_sub_channels(channel_button.sub_channels)
