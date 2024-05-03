from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal
from aiohttp import ClientSession
from aiohttp.http_websocket import WSMessage
from aiohttp.web import WSMsgType
from dotenv import load_dotenv
from datetime import datetime
import json
import random
import asyncio
import os

load_dotenv()

HOST = os.environ.get("HOST")
PORT = os.environ.get("PORT")
SSL = bool(os.environ.get("SSL"))


class ChatHandler(QWidget):
    messageReceived = pyqtSignal(str)
    setChannels = pyqtSignal(list)
    setSubChannels = pyqtSignal(dict)
    websocket = None
    user = None
    channel = None
    sub_channel = None

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
        self.user = f'user{random.randint(1111111, 9999999)}'
        await self.websocket.send_json({'action': 'connect',
                                        'user': self.user})

        await self.get_channels()

    async def disconnect(self) -> None:
        await self.websocket.send_json({'action': 'disconnect', })

    async def get_user_list(self) -> None:
        await self.websocket.send_json({'action': 'user_list', })

    async def get_channels(self) -> None:
        await self.websocket.send_json({'action': 'get_channels'})

    async def get_sub_channels(self, channel: str) -> None:
        await self.websocket.send_json(({'action': 'get_sub_channels', 'channel': channel}))

    async def join(self, channel: str, sub_channel: str):
        await self.websocket.send_json(({'action': 'join', 'channel': channel, 'sub_channel': sub_channel}))

    async def send_input_message(self, message: str) -> None:
        await self.websocket.send_json({'action': 'chat_message',
                                        'user': self.user,
                                        'message': message,
                                        'datetime': datetime.now().strftime('%d/%m/%y %H:%M:%S')})

    async def subscribe_to_messages(self) -> None:
        async for message in self.websocket:
            try:
                if not isinstance(message, WSMessage) or message.type != WSMsgType.text:
                    continue

                message_json = message.json()
                action = message_json.get('action')
                if action == 'connect':
                    self.messageReceived.emit(f'{message_json["datetime"]} - {message_json["user"]} connected')

                elif action == 'disconnect':
                    self.messageReceived.emit(f'{message_json["datetime"]} - {message_json["user"]} disconnected')

                elif action == 'get_channels':
                    self.setChannels.emit(message_json["channels"])

                elif action == 'get_sub_channels':
                    self.setSubChannels.emit(message_json["sub_channels"])

                elif action == 'chat_message':
                    self.messageReceived.emit(f'{message_json["datetime"]} - '
                                              f'{message_json["user"]}: {message_json["message"]}')

                else:
                    print(f"Unknown action received: {action}")

            except (json.JSONDecodeError, KeyError) as e:
                self.logger.error(f"Error processing message: {e}")
