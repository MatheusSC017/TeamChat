from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal
from aiohttp import ClientSession
from aiohttp.http_websocket import WSMessage
from aiohttp.web import WSMsgType
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()

HOST = os.environ.get("HOST")
PORT = os.environ.get("PORT")
SSL = bool(os.environ.get("SSL"))


class MessageHandler(QWidget):
    messageReceived = pyqtSignal(str)

    async def handler(self):
        if HOST is None or PORT is None:
            raise Exception("Server URL or SSL config not setted.")

        async with ClientSession() as session:
            async with session.ws_connect(f'{HOST}:{PORT}', ssl=SSL) as ws:
                read_message_task = asyncio.create_task(self.subscribe_to_messages(websocket=ws))

                # send_input_message_task = asyncio.create_task(send_input_message(websocket=ws))

                done, pending = await asyncio.wait(
                    [read_message_task, ], return_when=asyncio.FIRST_COMPLETED,
                )

                if not ws.closed:
                    await ws.close()
                for task in pending:
                    task.cancel()

    async def subscribe_to_messages(self, websocket):
        while True:
            async for message in websocket:
                if isinstance(message, WSMessage) and message.type == WSMsgType.text:
                    message_json = message.json()
                    if message_json.get('action') == 'chat_message':
                        self.messageReceived.emit(f'{message_json["user"]}: {message_json["message"]}')