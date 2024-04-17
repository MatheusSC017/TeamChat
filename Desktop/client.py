import asyncio
import logging

from aioconsole import ainput
from aiohttp import ClientSession, ClientWebSocketResponse
from aiohttp.http_websocket import WSMessage
from aiohttp.web import WSMsgType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('client')


async def subscribe_to_messages(websocket: ClientWebSocketResponse) -> None:
    async for message in websocket:
        if isinstance(message, WSMessage):
            if message.type == WSMsgType.text:
                message_json = message.json()
                if message_json.get('action') == 'chat_message' and not message_json.get('sucess'):
                    print(f'>>>{message_json["user"]}: {message_json["message"]}')
                logger.info('> Message from server received: %s', message_json)


async def send_input_message(websocket: ClientWebSocketResponse) -> None:
    while True:
        message = await ainput('<<<')
        if message == 'command close':
            await websocket.close()
        else:
            logger.info('\n< Sending message: %s', message)
            await websocket.send_json({'action': 'chat_message', 'message': message})


async def handler() -> None:
    async with ClientSession() as session:
        async with session.ws_connect('http://127.0.0.1:8080/', ssl=False) as ws:
            read_message_task = asyncio.create_task(subscribe_to_messages(websocket=ws))

            send_input_message_task = asyncio.create_task(send_input_message(websocket=ws))

            done, pending = await asyncio.wait(
                [read_message_task, send_input_message_task], return_when=asyncio.FIRST_COMPLETED,
            )

            if not ws.closed:
                await ws.close()
            for task in pending:
                task.cancel()


if __name__ == '__main__':
    asyncio.run(handler())
