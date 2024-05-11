from datetime import datetime
import logging

from aiohttp import web
import aiohttp

from utils import local_broadcast, global_broadcast

log = logging.getLogger(__name__)
actions = {'connect', 'disconnect', 'chat_message', 'get_channels', 'get_sub_channels', 'join', 'update_username',
           'user_list'}


async def index(request):
    username = None
    ws_current = web.WebSocketResponse()
    ws_ready = ws_current.can_prepare(request)
    if not ws_ready.ok:
        return web.Response(text="Connection Error")

    await ws_current.prepare(request)

    try:
        async for message in ws_current:
            if message.type == aiohttp.WSMsgType.text:
                message_json = message.json()
                action = message_json.get('action')

                if action not in actions:
                    continue

                if username not in request.app['user_list'].keys():
                    if action == 'connect':
                        username = message_json.get('user')
                        await connect(request, ws_current, username)

                else:

                    if action == 'chat_message':
                        await chat_message(request,
                                           ws_current,
                                           username,
                                           message_json.get('datetime'),
                                           message_json.get('message'))

                    elif action == 'get_channels':
                        await get_channels(request, ws_current)

                    elif action == 'get_sub_channels':
                        await get_sub_channels(request, ws_current, message_json.get('channel'))

                    elif action == 'user_list':
                        await ws_current.send_json({'action': 'user_list',
                                                    'user_list': list(request.app['user_list'].keys())})

                    elif action == 'join':
                        await join(request, ws_current, username, message_json.get('channel'), message_json.get('sub_channel'))

                    elif action == 'update_username':
                        new_username = await update_username(request, ws_current, username, message_json.get('username'))
                        if new_username is not None:
                            username = new_username

                    elif action == 'disconnect':
                        await ws_current.close()
                        await disconnect(request, ws_current, username)

    finally:
        await disconnect(request, ws_current, username)

    return ws_current


async def connect(request, ws_current, username):
    if len(username) and username not in request.app['user_list'].keys():
        log.info('%s connected', username)

        content = {
            'action': 'connect',
            'user': username,
            'datetime': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        }
        await global_broadcast(request, ws_current, content)
        await get_sub_channels(request, ws_current, 'Global')

        request.app['websockets']['Global']['Logs'][username] = ws_current
        request.app['user_list'][username] = ('Global', 'Logs')


async def disconnect(request, ws_current, username):
    if username is not None and username in request.app['user_list'].keys():
        channel, sub_channel = request.app['user_list'].get(username)
        del request.app['websockets'][channel][sub_channel][username]

        log.info('%s disconnected.', username)

        content = {
            'action': 'disconnect',
            'user': username,
            'datetime': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        }
        await global_broadcast(request, ws_current, content)

        del request.app['user_list'][username]


async def get_channels(request, ws_current):
    channels = list(request.app['websockets'].keys())
    await ws_current.send_json({'action': 'get_channels',
                                'channels': channels})


async def get_sub_channels(request, ws_current, channel):
    sub_channels = list(request.app['websockets'][channel].keys())
    sub_channels = {sub_channel: list(request.app['websockets'][channel][sub_channel].keys())
                    for sub_channel in sub_channels}
    await ws_current.send_json({'action': 'get_sub_channels',
                                'sub_channels': sub_channels})


async def join(request, ws_current, username, channel, sub_channel):
    if request.app['user_list'][username] != (channel, sub_channel) and \
       channel in request.app['websockets'].keys() and \
       sub_channel in request.app['websockets'][channel].keys():
        old_channel, old_sub_channel = request.app['user_list'][username]

        del request.app['websockets'][old_channel][old_sub_channel][username]

        request.app['websockets'][channel][sub_channel][username] = ws_current
        request.app['user_list'][username] = (channel, sub_channel)

        log.info('%s joined the %s / %s ', username, channel, sub_channel)
        content = {
            'action': 'join',
            'user': username,
            'channel': channel,
            'sub_channel': sub_channel,
            'datetime': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        }
        await local_broadcast(request, ws_current, channel, sub_channel, content)


async def update_username(request, ws_current, old_username, new_username):
    if new_username is not None and \
       old_username != new_username and \
       new_username not in request.app['user_list'].keys():
        log.info('%s updated your name to %s.', old_username, new_username)

        channel, sub_channel = request.app['user_list'][old_username]

        request.app['user_list'][new_username] = (channel, sub_channel)
        del request.app['user_list'][old_username]

        del request.app['websockets'][channel][sub_channel][old_username]
        request.app['websockets'][channel][sub_channel][new_username] = ws_current

        content = {
            'action': 'update_username',
            'old_username': old_username,
            'new_username': new_username,
        }
        await global_broadcast(request, ws_current, content)

        return new_username


async def chat_message(request, ws_current, username, datetime, message):
    channel, sub_channel = request.app['user_list'].get(username)
    if username is not None and request.app['websockets'][channel][sub_channel].get(username) is not None:
        content = {
            'action': 'chat_message',
            'user': username,
            'datetime': datetime,
            'message': message
        }

        await local_broadcast(request, ws_current, channel, sub_channel, content)
