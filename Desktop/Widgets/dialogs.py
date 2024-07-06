from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel


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
