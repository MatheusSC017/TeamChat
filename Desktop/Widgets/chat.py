from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal
from aiohttp import ClientSession
from aiohttp.http_websocket import WSMessage
from aiohttp import ClientWebSocketResponse
from aiohttp.web import WSMsgType
from dotenv import load_dotenv
from datetime import datetime
import random
import asyncio
import os

load_dotenv()

HOST = os.environ.get("HOST")
PORT = os.environ.get("PORT")
SSL = bool(os.environ.get("SSL"))


class MessageHandler(QWidget):
    messageReceived = pyqtSignal(str)
    websocket = None
    username = None

    async def handler(self) -> None:
        if HOST is None or PORT is None:
            raise Exception("Server URL or SSL config not setted.")

        async with ClientSession() as session:
            async with session.ws_connect(f'{HOST}:{PORT}', ssl=SSL) as ws:
                self.websocket = ws

                await self.connect()

                read_message_task = asyncio.create_task(self.subscribe_to_messages())

                done, pending = await asyncio.wait(
                    [read_message_task, ], return_when=asyncio.FIRST_COMPLETED,
                )

                if not ws.closed:
                    await ws.close()
                for task in pending:
                    task.cancel()

    async def connect(self) -> None:
        self.username = f'user{random.randint(1111111, 9999999)}'
        await self.websocket.send_json({'action': 'connect',
                                        'username': self.username})

    async def disconnect(self) -> None:
        await self.websocket.send_json({'action': 'disconnect', })

    async def send_input_message(self, message: str) -> None:
        await self.websocket.send_json({'action': 'chat_message',
                                        'user': self.user,
                                        'message': message,
                                        'datetime': datetime.now().strftime('%d/%m/%y %H:%M:%S')})

    async def subscribe_to_messages(self) -> None:
        while True:
            async for message in self.websocket:
                if isinstance(message, WSMessage) and message.type == WSMsgType.text:
                    message_json = message.json()
                    action = message_json.get('action')
                    if action == 'connect':
                        self.user = message_json.get('user')
                        self.messageReceived.emit(f'{message_json["datetime"]} - You are connected with the name: {self.user}')
                    elif action == 'disconnect':
                        self.messageReceived.emit(f'{message_json["datetime"]} - {message_json["user"]} disconnected')
                    elif action == 'join':
                        self.messageReceived.emit(f'{message_json["datetime"]} - {message_json["user"]} connected')
                    elif action == 'chat_message':
                        self.messageReceived.emit(f'{message_json["datetime"]} - {message_json["user"]}: {message_json["message"]}')
