from aiohttp import ClientSession
from PyQt6.QtCore import pyqtSignal
from dotenv import load_dotenv
from aiohttp.http_websocket import WSMessage
from aiohttp.web import WSMsgType
import json
import asyncio
import os

from Client.chat import ChatHandler
from Client.voice import VoiceHandler
from Widgets.dialogs import WarningDialog

load_dotenv()

HOST = os.environ.get("HOST")
PORT = os.environ.get("PORT")
SSL = bool(os.environ.get("SSL"))


class ClientHandler(ChatHandler, VoiceHandler):
    usersOnline = pyqtSignal(list)
    messageReceived = pyqtSignal(str, str)
    setChannels = pyqtSignal(list)
    setSubChannels = pyqtSignal(dict)
    joinAccepted = pyqtSignal(str, str)
    websocket = None
    user = None
    current_channel = 'Global'
    current_sub_channel = 'Logs'
    structure = None

    async def handler(self) -> None:
        if not HOST or not PORT:
            raise Exception("Server URL or SSL config not set.")

        async with ClientSession() as session:
            async with session.ws_connect(f'{HOST}:{PORT}', ssl=SSL) as ws:
                self.websocket = ws

                read_message_task = asyncio.create_task(self.subscribe_to_messages())
                server_update_task = asyncio.create_task(self.get_updates())
                record_audio_task = asyncio.create_task(self.record_audio())

                try:
                    await asyncio.gather(record_audio_task, read_message_task, server_update_task)
                except asyncio.CancelledError:
                    pass
                finally:
                    if not ws.closed:
                        await ws.close()

    async def subscribe_to_messages(self) -> None:
        actions = {
            'connect': self.connect_action,
            'disconnect': self.disconnect_action,
            'join': self.join_action,
            'join_accepted': self.join_accepted_action,
            'join_refused': self.join_refused_action,
            'update_username': self.update_username_action,
            'updated_username': self.updated_username_action,
            'invalid_username': self.invalid_username_action,
            'user_list': self.user_list_action,
            'get_structure': self.get_structure_action,
            'chat_message': self.chat_message_action,
            'direct_message': self.direct_message_action,
            'voice': self.listen_audio,
        }

        async for message in self.websocket:
            try:
                if not isinstance(message, WSMessage) or message.type != WSMsgType.text:
                    continue

                message_json = message.json()
                action = message_json.get('action')

                if action in actions.keys():
                    actions[action](message_json)
                else:
                    print(f"Unknown action received: {action}")

            except (json.JSONDecodeError, KeyError) as e:
                self.logger.error(f"Error processing message: {e}")

    async def connect(self, username) -> None:
        self.user = username
        await self.websocket.send_json({'action': 'connect', 'user': self.user})

        await self.get_user_list()
        await self.get_structure()

    async def disconnect(self) -> None:
        await self.websocket.send_json({'action': 'disconnect', })

    async def get_updates(self) -> None:
        while True:
            await asyncio.sleep(2)
            await self.get_user_list()

    async def get_user_list(self) -> None:
        await self.websocket.send_json({'action': 'user_list', })

    async def get_structure(self) -> None:
        await self.websocket.send_json({'action': 'get_structure'})

    def get_sub_channels(self, channel: str) -> None:
        self.setSubChannels.emit(self.structure[channel])

    async def join(self, channel: str, sub_channel: str, **kwargs):
        await self.websocket.send_json({'action': 'join', 'channel': channel, 'sub_channel': sub_channel, **kwargs})

    async def update_username(self, username: str) -> None:
        await self.websocket.send_json({'action': 'update_username', 'username': username})

    def connect_action(self, message_json):
        self.messageReceived.emit(f'{message_json["datetime"]} - {message_json["user"]} connected',
                                  'Global')
        self.structure['Global']['Logs']['Users'].append(message_json['user'])
        if self.current_channel == 'Global':
            self.setSubChannels.emit(self.structure['Global'])

    def disconnect_action(self, message_json):
        self.messageReceived.emit(f'{message_json["datetime"]} - {message_json["user"]} disconnected',
                                  'Global')
        channel, sub_channel = self.get_user_position(message_json["user"])
        self.structure[channel][sub_channel]['Users'].remove(message_json['user'])
        if self.current_channel == channel:
            self.setSubChannels.emit(self.structure[channel])

    def join_action(self, message_json):
        self.messageReceived.emit(f'{message_json["user"]} joined {message_json["channel"]} / '
                                  f'{message_json["sub_channel"]}',
                                  'Global')
        if self.current_channel == message_json["channel"] and \
                self.current_sub_channel == message_json["sub_channel"]:
            self.messageReceived.emit(f'{message_json["user"]} joined {message_json["channel"]} / '
                                      f'{message_json["sub_channel"]}',
                                      'Local')
        self.update_structure(message_json["channel"], message_json["sub_channel"], message_json["user"])

    def join_accepted_action(self, message_json):
        self.update_structure(message_json['channel'], message_json['sub_channel'], self.user)
        self.joinAccepted.emit(message_json['channel'], message_json['sub_channel'])

    def join_refused_action(self, message_json):
        dlg = WarningDialog(self, message_json['error'])
        dlg.exec()

    def update_username_action(self, message_json):
        self.messageReceived.emit(f'{message_json["old_username"]} updated your name to '
                                  f'{message_json["new_username"]}',
                                  'Local')
        self.update_username_structure(message_json['old_username'], message_json['new_username'])

    def updated_username_action(self, message_json):
        self.update_username_structure(self.user, message_json['username'])
        self.user = message_json['username']

    def invalid_username_action(self, message_json):
        print("Username already in use")

    def user_list_action(self, message_json):
        self.usersOnline.emit(message_json['user_list'])

    def get_structure_action(self, message_json):
        self.structure = message_json["structure"]
        self.setChannels.emit(list(self.structure.keys()))
        self.get_sub_channels('Global')


    def update_username_structure(self, old_username, new_username):
        channel, sub_channel = self.get_user_position(old_username)
        self.structure[channel][sub_channel]['Users'].remove(old_username)
        self.structure[channel][sub_channel]['Users'].append(new_username)
        if self.current_channel == channel:
            self.setSubChannels.emit(self.structure[channel])

    def update_structure(self, new_channel, new_sub_channel, user):
        channel, sub_channel = self.get_user_position(user)
        self.structure[channel][sub_channel]['Users'].remove(user)

        self.structure[new_channel][new_sub_channel]['Users'].append(user)
        if self.current_channel in (channel, new_channel):
            self.setSubChannels.emit(self.structure[new_channel])

    def get_user_position(self, user):
        for channel in self.structure.keys():
            for sub_channel in self.structure[channel].keys():
                if user in self.structure[channel][sub_channel]['Users']:
                    return channel, sub_channel
