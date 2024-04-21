from datetime import datetime
import logging
import random

import aiohttp
from aiohttp import web

log = logging.getLogger(__name__)


async def index(request):
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
                for ws in request.app['websockets'].values():
                    if ws is not ws_current:
                        await ws.send_json(
                            {'action': 'chat_message',
                             'user': username,
                             'datetime': message_json.get('datetime'),
                             'message': message_json.get('message')}
                        )
            elif action == 'connect':
                username = message_json.get('username')
                await connect(request, ws_current, username)

            elif action == 'user_list':
                user_list = request.app['websockets'].keys()
                await current_websocket.send_json(user_list)

        else:
            break

    del request.app['websockets'][username]

    # Broadcast message about disconnected user
    log.info('%s disconnected.', username)
    for ws in request.app['websockets'].values():
        await ws.send_json({'action': 'disconnect',
                            'user': username,
                            'datetime': datetime.now().strftime('%d/%m/%y %H:%M:%S')})

    return ws_current


async def connect(request, ws_current, username):
    log.info('%s connected', username)

    await ws_current.send_json({'action': 'connect',
                                'user': username,
                                'datetime': datetime.now().strftime('%d/%m/%y %H:%M:%S')})

    if request.app['websockets'].get(username):
        return ws_current
    else:
        for ws in request.app['websockets'].values():
            await ws.send_json({'action': 'join',
                                'user': username,
                                'datetime': datetime.now().strftime('%d/%m/%y %H:%M:%S')})
        request.app['websockets'][username] = ws_current
