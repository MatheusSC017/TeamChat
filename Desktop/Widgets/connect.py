from PyQt6.QtWidgets import (
    QApplication,
    QWidget
)
from Widgets.base import BaseWidget


class Connect(BaseWidget):
    def __init__(self, base_path, screen_size):
        self.settings(screen_size)
        self.initUI()
        self.setStyleCSS(base_path / "Static/CSS/main.css")

    def settings(self, screen_size):
        self.setWindowTitle("Connect")
        self.set_geometry_center(200, 100, screen_size)

    def initUI(self):
        pass


if __name__ == "__main__":
    app = QApplication([])
    main = Connect()
    main.show()
    app.exec()
