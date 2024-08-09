from aiohttp import web
from pyaudio import PyAudio, paInt16
import aiohttp
import json
import base64


async def index(request):
    username = request.query.get("username")
    if username in request.app['clients'].keys():
        return web.Response(text="Username already in use")

    ws_current = web.WebSocketResponse()
    ws_ready = ws_current.can_prepare(request)
    if not ws_ready.ok:
        return web.Response(text="Connection Error")

    await ws_current.prepare(request)

    request.app['clients'][username] = ws_current

    py_audio = PyAudio()
    output_stream = py_audio.open(format=paInt16, output=True, rate=44100,
                                  channels=2, frames_per_buffer=1024)

    try:
        async for message in ws_current:
            if message.type == aiohttp.WSMsgType.text:
                audio = message.json()
                output_stream.write(base64.b64decode(audio))
                # for ws in request.app['clients'].values():
                #     if ws is not ws_current:
                #         await ws.send_json(json.dumps(audio))
    finally:
        del request.app['clients'][username]

    return ws_current


if __name__ == "__main__":
    app = web.Application()
    app['clients'] = {}
    app['buffer'] = 1024
    app.router.add_get('/', index)

    web.run_app(app)
