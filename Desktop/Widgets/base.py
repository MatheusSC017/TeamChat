from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class BaseWidget(QWidget):
    def setStyleCSS(self, css_file_path):
        with open(css_file_path, "r") as css:
            self.setStyleSheet(css.read())

    def set_geometry_center(self, width, height, screen_size):
        window_center_x = (screen_size.width() - width) // 2
        window_center_y = (screen_size.height() - height) // 2
        self.setGeometry(window_center_x, window_center_y, width, height)


class BaseFormWindow(BaseWidget):
    window_name = None

    def __init__(self, base_path, screen_size):
        super().__init__()

        self.settings(screen_size)
        self.initUI()
        self.setStyleCSS(base_path / "Static/CSS/popup.css")

    def settings(self, screen_size):
        self.setWindowTitle(self.window_name)
        self.setFixedWidth(300)
        self.setFixedHeight(100)
        self.set_geometry_center(300, 100, screen_size)

    def initUI(self):
        self.username_edit = QLineEdit()
        self.connect_button = QPushButton(self.window_name)

        master = QVBoxLayout()
        master.addWidget(QLabel("Nome de usuário"))
        master.addWidget(self.username_edit)
        master.addWidget(self.connect_button)

        self.setLayout(master)
