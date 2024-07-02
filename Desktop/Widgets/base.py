from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)
from PyQt6.QtGui import QPixmap
from PIL.ImageQt import ImageQt
from PIL import Image


class LabeledLineEdit(QWidget):
    def __init__(self, label):
        super().__init__()

        self.initUI(label)

    def initUI(self, label):
        master = QVBoxLayout()

        self.label = QLabel(label)
        master.addWidget(self.label)
        self.line_edit = QLineEdit()
        master.addWidget(self.line_edit)

        self.setLayout(master)


class BaseWidget(QWidget):
    def setStyleCSS(self, css_file_path):
        with open(css_file_path, "r") as css:
            self.setStyleSheet(css.read())

    def set_geometry_center(self, width, height, screen_size, width_modifier=0, height_modifier=0, fixed=False):
        if fixed:
            self.setFixedWidth(width)
            self.setFixedHeight(height)

        window_center_x = (screen_size.width() - width) // 2
        window_center_y = (screen_size.height() - height) // 2
        self.setGeometry(window_center_x + width_modifier, window_center_y + height_modifier, width, height)

    def clear_layout(self, main_layout):
        for i in reversed(range(main_layout.count())):
            item = main_layout.itemAt(i)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                main_layout.removeWidget(widget)
            else:
                self.clear_layout(item.layout())


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
        self.form_button = QPushButton(self.window_name)

        master = QVBoxLayout()
        master.addWidget(QLabel("Username"))
        master.addWidget(self.username_edit)
        master.addWidget(self.form_button)

        self.setLayout(master)


class IconWidget(QLabel):
    def __init__(self, name, base_path):
        super().__init__()
        self.initUI(name, base_path)

    def initUI(self, name, base_path):
        padlock_icon = base_path / f"Static/Images/{name}.png"

        image = Image.open(padlock_icon)
        image = image.resize((15, 15))
        image_qt = ImageQt(image)

        self.setPixmap(QPixmap.fromImage(image_qt))
        self.setFixedHeight(30)
        self.setFixedWidth(30)
