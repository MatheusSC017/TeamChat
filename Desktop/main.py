from qasync import QApplication, QEventLoop
from Widgets.window import Home
import pathlib
import asyncio

BASE_PATH = pathlib.Path(__file__).resolve().parent

if __name__ == "__main__":
    app = QApplication([])

    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    main = Home(app.primaryScreen().size(), BASE_PATH)
    main.show()

    with event_loop:
        event_loop.run_until_complete(app_close_event.wait())
