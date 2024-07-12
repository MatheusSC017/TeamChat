import sys
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QLabel, QDialogButtonBox


class WarningDialog(QDialog):
    def __init__(self, parent=None, message="Warning", items=[]):
        super().__init__()

        self.setWindowTitle("Warning")

        self.setFixedHeight(100)
        self.setMinimumWidth(200)

        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel(message))

        for item in items:
            self.layout.addWidget(QLabel(item))

        self.setLayout(self.layout)


class UpdatePasswordDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Update Password')

        layout = QVBoxLayout()

        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(QLabel('Password:'))
        layout.addWidget(self.new_password)
        layout.addWidget(QLabel('Confirm the Password:'))
        layout.addWidget(self.confirm_password)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def getInputs(self):
        return self.new_password.text(), self.confirm_password.text()
