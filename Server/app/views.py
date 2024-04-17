import logging

import aiohttp
from aiohttp import web
import random

log = logging.getLogger(__name__)


async def index(request):
    ws_current = web.WebSocketResponse()
    ws_ready = ws_current.can_prepare(request)
    if not ws_ready.ok:
        return web.Response(text="Connection Error")

    await ws_current.prepare(request)

    name = f"user{random.randint(0, 9999999)}"
    log.info('')

    await ws_current.send_json({'action': 'connect', 'name': name})

    for ws in request.app['websockets'].values():
        await ws.send_json({'action': 'join', 'name': name})
    request.app['websockets'][name] = ws_current

    while True:
        msg = await ws_current.receive()

        if msg.type == aiohttp.WSMsgType.text:
            for ws in request['websockets'].values():
                if ws is not ws_current:
                    await ws.send_json(
                        {'action': 'sent', 'name': name, 'text': msg.data}
                    )
        else:
            break

    del request.app['websockets'][name]
    log.info('%s disconnected.', name)
    for ws in request.app['websockets'].values():
        await ws.send_json({'action': 'disconnect', 'name': name})

    return ws_current
