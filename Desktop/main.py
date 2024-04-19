from PyQt6.QtWidgets import QApplication
from Widgets.window import Home
import pathlib

BASE_PATH = pathlib.Path(__file__).resolve().parent

if __name__ == "__main__":
    app = QApplication([])
    main = Home(app.primaryScreen().size(), BASE_PATH)
    main.show()
    main.start_chat()
    app.exec()
