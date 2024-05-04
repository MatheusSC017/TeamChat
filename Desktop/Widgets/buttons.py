from PyQt6.QtWidgets import (
    QWidget,
    QAbstractButton,
    QLabel,
    QHBoxLayout,
    QVBoxLayout
)
from PyQt6.QtGui import QPixmap
from PIL.ImageQt import ImageQt
from PIL import Image
from Widgets.base import BaseWidget


class PushButtonChannel(QAbstractButton, BaseWidget):
    def __init__(self, name, protected, base_path):
        super().__init__()
        self.channel_name = name

        self.initUI(name, protected, base_path)
        self.setStyleCSS(base_path / "Static/CSS/button.css")

    def initUI(self, name, protected, base_path):
        self.setContentsMargins(0, 0, 0, 0)

        channel_name = QLabel(name)
        channel_name.setFixedHeight(30)

        padlock_icon = base_path / "Static/Images/padlock.png"
        open_padlock_icon = base_path / "Static/Images/open_padlock.png"

        image = Image.open(padlock_icon if protected else open_padlock_icon)
        image = image.resize((15, 15))
        image_qt = ImageQt(image)

        channel_protected = QLabel("")
        channel_protected.setPixmap(QPixmap.fromImage(image_qt))
        channel_protected.setFixedHeight(30)
        channel_protected.setFixedWidth(30)

        channel = QHBoxLayout()
        channel.addWidget(channel_name)
        channel.addWidget(channel_protected)
        channel.setObjectName("channel")

        self.setLayout(channel)

    def paintEvent(self, a0, QPaintEvent=None):
        pass


class PushButtonSubChannel(QAbstractButton, BaseWidget):
    def __init__(self, name, users, base_path):
        super().__init__()
        self.sub_channel_name = name

        self.initUI(name, users)
        self.setStyleCSS(base_path / "Static/CSS/button.css")

    def initUI(self, name, users):
        self.user_layout = QVBoxLayout()
        self.set_users(self.user_layout, users)

        user_list = QWidget()
        user_list.setLayout(self.user_layout)

        sub_channel = QVBoxLayout()
        sub_channel.addWidget(QLabel(name))
        sub_channel.addWidget(user_list)
        sub_channel.setObjectName("sub_channel")

        self.setLayout(sub_channel)

    def set_users(self, layout, users):
        self.user_widgets = {}

        for user in users:
            self.user_widgets[user] = QLabel(user)
            layout.addWidget(self.user_widgets[user])

    def paintEvent(self, a0, QPaintEvent=None):
        pass
