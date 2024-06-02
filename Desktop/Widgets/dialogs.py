from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel


class WarningDialog(QDialog):
    def __init__(self, parent=None, message="Warning"):
        super().__init__()

        self.setWindowTitle("Warning")

        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel(message))

        self.setLayout(self.layout)
