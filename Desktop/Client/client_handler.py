from aiohttp import ClientSession
from dotenv import load_dotenv
from aiohttp.http_websocket import WSMessage
from aiohttp.web import WSMsgType
import json
import asyncio
import os

from Client.chat import ChatHandler
from Client.voice import VoiceHandler

load_dotenv()

HOST = os.environ.get("HOST")
PORT = os.environ.get("PORT")
SSL = bool(os.environ.get("SSL"))


class ClientHandler(ChatHandler, VoiceHandler):
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
