from PyQt6.QtWidgets import QWidget


class BaseWidget(QWidget):
    def setStyleCSS(self, css_file_path):
        with open(css_file_path, "r") as css:
            self.setStyleSheet(css.read())

    def set_geometry_center(self, width, height, screen_size):
        window_center_x = (screen_size.width() - width) // 2
        window_center_y = (screen_size.height() - height) // 2
        self.setGeometry(window_center_x, window_center_y, width, height)


