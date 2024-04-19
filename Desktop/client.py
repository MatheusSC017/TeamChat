import asyncio
import os
from aiohttp import ClientSession
from actions import send_input_message, subscribe_to_messages
from dotenv import load_dotenv

load_dotenv()

HOST = os.environ.get("HOST")
PORT = os.environ.get("PORT")
SSL = bool(os.environ.get("SSL"))


async def handler() -> None:
    if HOST is None or PORT is None:
        raise Exception("Server URL or SSL config not setted.")

    async with ClientSession() as session:
        async with session.ws_connect(f'{HOST}:{PORT}', ssl=SSL) as ws:
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
