from PyQt6.QtWidgets import (
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)
from PyQt6.QtCore import pyqtSignal
from Widgets.base import BaseFormWindow


class Connect(BaseFormWindow):
    connectRequest = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        self.window_name = "Conectar"

        super().__init__(*args, **kwargs)

        self.connect_button.clicked.connect(self.connect_request)

    def connect_request(self):
        user = self.username_edit.text()
        self.connectRequest.emit(user)
