from pyaudio import PyAudio, paInt16
from dotenv import load_dotenv
import os
from aiohttp import ClientSession
from aiohttp.http_websocket import WSMessage
from aiohttp.web import WSMsgType
from threading import Thread
import asyncio
import json
import base64

load_dotenv()

HOST = os.environ.get("HOST")
PORT = os.environ.get("PORT")
SSL = bool(os.environ.get("SSL"))


class Client:
    def __init__(self):
        py_audio = PyAudio()
        self.buffer = 1024

        self.output_stream = py_audio.open(format=paInt16, output=True, rate=44100,
                                           channels=2, frames_per_buffer=self.buffer)

        self.input_stream = py_audio.open(format=paInt16, input=True, rate=44100,
                                          channels=2, frames_per_buffer=self.buffer)

    async def handler(self) -> None:
        if not HOST or not PORT:
            raise Exception("Server URL or SSL config not set.")

        async with ClientSession() as session:
            async with session.ws_connect(f'{HOST}:{PORT}', ssl=SSL, params={"username": "teste"}) as ws:
                self.websocket = ws

                audio_received_task = asyncio.create_task(self.audio_received())
                record_audio_task = asyncio.create_task(self.record_audio())

                try:
                    await asyncio.gather(record_audio_task, audio_received_task)
                except asyncio.CancelledError:
                    pass
                finally:
                    if not ws.closed:
                        await ws.close()

    async def record_audio(self):
        while True:
            data = self.input_stream.read(self.buffer)
            if self.websocket.closed:
                break
            await self.websocket.send_str(json.dumps(base64.b64encode(data).decode('ascii')))
            await asyncio.sleep(0.01)

    async def audio_received(self):
        async for message in self.websocket:
            try:
                if not isinstance(message, WSMessage) or message.type != WSMsgType.text:
                    continue

                audio = message.json()
                self.output_stream.write(base64.b64decode(audio))

            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error processing message: {e}")



client = Client()
chat_thread = Thread(target=asyncio.run, args=(client.handler(),))
chat_thread.start()
