from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QTextEdit,
    QScrollArea,
    QPushButton,
    QAbstractButton,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QSizePolicy
)
from PyQt6.QtGui import QPixmap
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


class Home(QWidget):
    def __init__(self, screen_size):
        super().__init__()
        self.settings(screen_size)
        self.initUI()
        self.setStyleCSS(style_css)

    def initUI(self):
        self.master = QHBoxLayout()
        self.master.addLayout(self.get_channels_ui(), 50)
        self.master.addLayout(self.get_messages_ui(), 50)

        self.setLayout(self.master)

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
        self.get_channels()

        width_size_policy = QSizePolicy()
        width_size_policy.setHorizontalStretch(1)

        container = QWidget()
        container.setLayout(self.channels)
        container.setSizePolicy(width_size_policy)

        channels_scroll = QScrollArea()
        channels_scroll.setWidget(container)

        column = QVBoxLayout()
        column.addLayout(header)
        column.addWidget(channels_scroll)
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

            name = QLabel(channel_info['name'])
            name.setFixedHeight(50)
            password = QLabel("")
            image = Image.open(padlock_icon if channel_info['protected'] else open_padlock_icon)
            image = image.resize((15, 15))
            image_qt = ImageQt(image)
            password.setPixmap(QPixmap.fromImage(image_qt))
            password.setFixedHeight(50)
            password.setFixedWidth(30)

            channel = QHBoxLayout()
            channel.addWidget(name)
            channel.addWidget(password)
            channel.setObjectName("channel")

            self.channels.addLayout(channel)


if __name__ == "__main__":
    app = QApplication([])
    main = Home(app.primaryScreen().size())
    main.show()
    app.exec()
