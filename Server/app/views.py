from datetime import datetime
import logging
import random

import aiohttp
from aiohttp import web

log = logging.getLogger(__name__)


async def index(request):
    username = None
    ws_current = web.WebSocketResponse()
    ws_ready = ws_current.can_prepare(request)
    if not ws_ready.ok:
        return web.Response(text="Connection Error")

    await ws_current.prepare(request)

    while True:
        message = await ws_current.receive()

        if message.type == aiohttp.WSMsgType.text:
            message_json = message.json()
            action = message_json.get('action')

            if action == 'chat_message':
                if username is not None and request.app['websockets'].get(username) is not None:
                    for ws in request.app['websockets'].values():
                        if ws is not ws_current:
                            await ws.send_json(
                                {'action': 'chat_message',
                                 'user': username,
                                 'datetime': message_json.get('datetime'),
                                 'message': message_json.get('message')}
                            )

            elif action == 'connect':
                username = message_json.get('user')
                await connect(request, ws_current, username)

            elif action == 'disconnect':
                await disconnect(request, username)

            elif action == 'user_list':
                user_list = request.app['websockets'].keys()
                await current_websocket.send_json(user_list)

        else:
            break

    await disconnect(request, username)

    return ws_current


async def connect(request, ws_current, username):
    log.info('%s connected', username)

    if request.app['websockets'].get(username):
        return ws_current
    else:
        for ws in request.app['websockets'].values():
            await ws.send_json({'action': 'connect',
                                'user': username,
                                'datetime': datetime.now().strftime('%d/%m/%y %H:%M:%S')})
        request.app['websockets'][username] = ws_current


async def disconnect(request, username):
    if username is not None and request.app['websockets'].get(username) is not None:
        del request.app['websockets'][username]

        log.info('%s disconnected.', username)
        for ws in request.app['websockets'].values():
            await ws.send_json({'action': 'disconnect',
                                'user': username,
                                'datetime': datetime.now().strftime('%d/%m/%y %H:%M:%S')})
