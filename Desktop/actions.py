from aioconsole import ainput
from aiohttp import ClientWebSocketResponse
from aiohttp.http_websocket import WSMessage
from datetime import datetime
from aiohttp.web import WSMsgType


async def subscribe_to_messages(websocket: ClientWebSocketResponse) -> None:
    async for message in websocket:
        if isinstance(message, WSMessage):
            if message.type == WSMsgType.text:
                message_json = message.json()
                if message_json.get('action') == 'chat_message':
                    print(f'>>>{message_json["datetime"]} - {message_json["user"]}: {message_json["message"]}')


async def send_input_message(websocket: ClientWebSocketResponse) -> None:
    while True:
        message = await ainput('<<<')
        if message == 'command close':
            await websocket.close()
        else:
            await websocket.send_json({'action': 'chat_message',
                                       'message': message,
                                       'datetime': datetime.now().strftime('%d/%m/%y %H:%M:%S')})
