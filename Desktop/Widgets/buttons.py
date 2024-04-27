from PyQt6.QtWidgets import (
    QAbstractButton,
    QLabel,
    QHBoxLayout,
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QPixmap
from PIL.ImageQt import ImageQt
from PIL import Image


class PushButtonChannel(QAbstractButton):
    def __init__(self, name, protected, base_path):
        super(PushButtonChannel, self).__init__()
        self.setContentsMargins(0, 0, 0, 0)

        self.channel_name = QLabel(name)
        self.channel_name.setFixedHeight(30)

        padlock_icon = base_path / "static/images/padlock.png"
        open_padlock_icon = base_path / "static/images/open_padlock.png"

        image = Image.open(padlock_icon if protected else open_padlock_icon)
        image = image.resize((15, 15))
        image_qt = ImageQt(image)

        channel_protected = QLabel("")
        channel_protected.setPixmap(QPixmap.fromImage(image_qt))
        channel_protected.setFixedHeight(30)
        channel_protected.setFixedWidth(30)

        channel = QHBoxLayout()
        channel.addWidget(self.channel_name)
        channel.addWidget(channel_protected)
        channel.setObjectName("channel")

        self.setLayout(channel)

    def paintEvent(self, a0, QPaintEvent=None):
        pass
