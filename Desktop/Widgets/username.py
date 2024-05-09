from PyQt6.QtCore import pyqtSignal
from Widgets.base import BaseFormWindow


class UpdateUsername(BaseFormWindow):
    updateUsername = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        self.window_name = "Change username"

        super().__init__(*args, **kwargs)

        self.connect_button.clicked.connect(self.connect_request)
        self.username_edit.returnPressed.connect(self.connect_request)

    def connect_request(self):
        user = self.username_edit.text()
        self.updateUsername.emit(user)
