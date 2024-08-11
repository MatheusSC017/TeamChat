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


class VoiceHandler:
    def __init__(self):
        py_audio = PyAudio()
        self.buffer = 1024

        self.output_stream = py_audio.open(format=paInt16, output=True, rate=44100,
                                           channels=2, frames_per_buffer=self.buffer)

        self.input_stream = py_audio.open(format=paInt16, input=True, rate=44100,
                                          channels=2, frames_per_buffer=self.buffer)

    async def record_audio(self):
        while True:
            audio = self.input_stream.read(self.buffer)
            if self.websocket.closed:
                break
            await self.websocket.send_str(json.dumps({
                "action": "voice",
                "audio": base64.b64encode(audio).decode('ascii'),
                "channel": self.current_channel,
                "sub_channel": self.current_sub_channel,
            }))
            await asyncio.sleep(0.01)

    def listen_audio(self, message_json):
        audio = message_json.get('audio')
        self.output_stream.write(base64.b64decode(audio))
