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
                if username is not None and request.app['websockets']['Global'].get(username) is not None:
                    for ws in request.app['websockets']['Global'].values():
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

            elif action == 'get_channels':
                await get_channels(request, ws_current)

            elif action == 'get_sub_channels':
                await get_sub_channels(request, ws_current, message_json.get('channel'))

            elif action == 'user_list':
                await current_websocket.send_json(request.app['user_list'])

        else:
            break

    await disconnect(request, username)

    return ws_current


async def connect(request, ws_current, username):
    if username not in request.app['user_list']:
        log.info('%s connected', username)
        for ws in request.app['websockets']['Global'].values():
            await ws.send_json({'action': 'connect',
                                'user': username,
                                'datetime': datetime.now().strftime('%d/%m/%y %H:%M:%S')})
        request.app['websockets']['Global'][username] = ws_current
        request.app['user_list'].append(username)


async def disconnect(request, username):
    if username is not None and username in request.app['user_list']:
        del request.app['websockets']['Global'][username]

        log.info('%s disconnected.', username)
        for ws in request.app['websockets']['Global'].values():
            await ws.send_json({'action': 'disconnect',
                                'user': username,
                                'datetime': datetime.now().strftime('%d/%m/%y %H:%M:%S')})
        request.app['user_list'].pop(request.app['user_list'].index(username))


async def get_channels(request, ws):
    channels = list(request.app['websockets'].keys())
    channels.pop(channels.index('Global'))
    await ws.send_json({'action': 'get_channels',
                        'channels': channels})


async def get_sub_channels(request, ws, channel):
    sub_channels = list(request.app['websockets'][channel].keys())
    sub_channels = {sub_channel: list(request.app['websockets'][channel][sub_channel].keys())
                    for sub_channel in sub_channels}
    await ws.send_json({'action': 'get_sub_channels',
                        'sub_channels': sub_channels})

async def join():
    pass
