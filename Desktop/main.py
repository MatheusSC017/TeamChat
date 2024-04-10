from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QTextEdit,
    QScrollArea,
    QPushButton,
    QAbstractButton,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QGroupBox,
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QSize
from PIL.ImageQt import ImageQt
from PIL import Image
import pathlib
import faker
from random import choice


faker_instance = faker.Faker()
BASE_PATH = pathlib.Path(__file__).resolve().parent
CSS_PATH = BASE_PATH / "static/css"
style_css = CSS_PATH / "style.css"
IMAGE_PATH = BASE_PATH / "static/images"
padlock_icon = IMAGE_PATH / "padlock.png"
open_padlock_icon = IMAGE_PATH / "open_padlock.png"


class Home(QMainWindow):
    def __init__(self, screen_size):
        super().__init__()
        self.settings(screen_size)
        self.initUI()
        self.setStyleCSS(style_css)

    def initUI(self):
        self.master = QHBoxLayout()
        self.master.addLayout(self.get_channels_ui(), 50)
        self.master.addLayout(self.get_messages_ui(), 50)

        central_widget = QWidget()
        central_widget.setLayout(self.master)
        self.setCentralWidget(central_widget)

    def get_messages_ui(self):
        self.chat = QTextEdit()
        self.chat.setEnabled(False)

        self.message = QTextEdit()
        self.message.setFixedHeight(40)

        send_message = QPushButton("Send")
        send_message.setFixedHeight(40)

        message_group = QHBoxLayout()
        message_group.addWidget(self.message)
        message_group.addWidget(send_message)

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
        self.setGeometryCenter(1000, 700, screen_size)

    def setGeometryCenter(self, width, height, screen_size):
        window_center_x = (screen_size.width() - width) // 2
        window_center_y = (screen_size.height() - height) // 2
        self.setGeometry(window_center_x, window_center_y, width, height)

    def get_channels(self):
        for i in range(30):
            channel_info = {
                'name': faker_instance.first_name(),
                'protected': choice([True, False])
            }

            channel_button = PushButtonChannel(channel_info['name'], channel_info['protected'])
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

class PushButtonChannel(QWidget):
    def __init__(self, name, protected):
        super(PushButtonChannel, self).__init__()
        self.setContentsMargins(0, 0, 0, 0)

        channel_name = QLabel(name)
        channel_name.setFixedHeight(30)

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


if __name__ == "__main__":
    app = QApplication([])
    main = Home(app.primaryScreen().size())
    main.show()
    app.exec()
