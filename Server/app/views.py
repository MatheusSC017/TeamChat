from datetime import datetime
from aiohttp import web
import logging
import aiohttp
import json
import base64

from bson import json_util
from utils import local_broadcast, global_broadcast

log = logging.getLogger(__name__)
actions = {'connect', 'disconnect', 'chat_message', 'get_structure', 'join', 'update_username', 'user_list',
           'direct_message'}


async def register_user(request):
    user_credentials = await request.post()
    if 'username' not in user_credentials.keys() or 'password' not in user_credentials.keys():
        return web.Response(status=400)

    inserted, result = await request.app['user_collection'].add_user(user_credentials['username'],
                                                                     user_credentials['password'])
    if inserted:
        return web.Response(status=201)

    return web.Response(body=json.dumps({'errors': result}), status=400)


async def update_user(request):
    access_token = request.headers.get('Authorization', None)
    if access_token is None:
        return web.Response(status=400)
    username, authenticated = request.app['tokens'].authenticate(base64.b64decode(access_token))
    if not authenticated:
        return web.Response(status=401)

    user_data = await request.post()
    updated, _ = await request.app['user_collection'].update_user(username, user_data)
    if updated:
        return web.Response(status=202)
    return web.Response(status=500)


async def log_in(request):
    user_credentials = await request.post()
    if 'username' not in user_credentials.keys() or 'password' not in user_credentials.keys():
        return web.Response(status=400)

    authenticated = await request.app['user_collection'].authenticate(user_credentials['username'],
                                                                      user_credentials['password'])
    if authenticated:
        token = request.app['tokens'].add_user(user_credentials['username'])
        return web.Response(body=json.dumps({'token': base64.b64encode(token).decode('ascii')}), status=200)

    return web.Response(status=401)


async def log_out(request):
    access_token = request.headers.get('Authorization', None)
    if access_token is None:
        return web.Response(status=400)

    logged_out = request.app['tokens'].del_user(user_credentials['token'])
    if logged_out:
        return web.Response(status=200)
    return web.Response(status=401)


async def retrieve_user(request):
    access_token = request.headers.get('Authorization', None)
    if access_token is None:
        return web.Response(status=400)
    username, authenticated = request.app['tokens'].authenticate(base64.b64decode(access_token))
    if authenticated:
        user = await request.app['user_collection'].get_user(username)
        del user['password']
        return web.Response(body=json_util.dumps(user), status=200)
    return web.Response(status=401)


async def retrieve_channels(request):
    access_token = request.headers.get('Authorization', None)
    if access_token is None:
        return web.Response(status=400)
    username, authenticated = request.app['tokens'].authenticate(base64.b64decode(access_token))
    if authenticated:
        channels = await request.app['chat_collection'].get_channels(owner=username)
        for channel in channels.keys():
            for sub_channel in channels[channel].keys():
                if 'password' in channels[channel][sub_channel].keys():
                    del channels[channel][sub_channel]['password']
        return web.Response(body=json_util.dumps(channels), status=200)
    return web.Response(status=401)


async def delete_channel(request):
    access_token = request.headers.get('Authorization', None)
    if access_token is None:
        return web.Response(status=400)
    username, authenticated = request.app['tokens'].authenticate(base64.b64decode(access_token))
    if not authenticated:
        return web.Response(status=401)

    channel = await request.json()
    deleted = await request.app['chat_collection'].delete_channel(channel['channel'],
                                                                  username)
    if deleted:
        return web.Response(status=202)
    return web.Response(status=500)


async def update_sub_channels(request):
    access_token = request.headers.get('Authorization', None)
    if access_token is None:
        return web.Response(status=400)
    username, authenticated = request.app['tokens'].authenticate(base64.b64decode(access_token))
    if not authenticated:
        return web.Response(status=401)

    channel_data = await request.json()
    updated = await request.app['chat_collection'].update_sub_channels(channel_data['channel'],
                                                                       channel_data['sub_channels'],
                                                                       username)
    if updated:
        return web.Response(status=202)
    return web.Response(status=500)


async def delete_sub_channels(request):
    access_token = request.headers.get('Authorization', None)
    if access_token is None:
        return web.Response(status=400)
    username, authenticated = request.app['tokens'].authenticate(base64.b64decode(access_token))
    if not authenticated:
        return web.Response(status=401)

    channel = await request.json()
    deleted = await request.app['chat_collection'].delete_sub_channels(channel['channel'],
                                                                       channel['sub_channels'],
                                                                       username)
    if deleted:
        return web.Response(status=202)
    return web.Response(status=400)


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

                    if action == 'direct_message':
                        await direct_message(request,
                                             username,
                                             message_json.get('recipient'),
                                             message_json.get('datetime'),
                                             message_json.get('message'))

                    elif action == 'get_structure':
                        await get_structure(request, ws_current)

                    elif action == 'user_list':
                        await get_user_list(request, ws_current, username)

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

        request.app['websockets']['Global']['Logs']['Users'][username] = ws_current
        request.app['user_list'][username] = ('Global', 'Logs')


async def disconnect(request, ws_current, username):
    if username is not None and username in request.app['user_list'].keys():
        channel, sub_channel = request.app['user_list'].get(username)
        del request.app['websockets'][channel][sub_channel]['Users'][username]

        log.info('%s disconnected.', username)

        content = {
            'action': 'disconnect',
            'user': username,
            'datetime': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        }
        await global_broadcast(request, ws_current, content)

        del request.app['user_list'][username]


# Obsolete, will be removed
async def get_structure(request, ws_current):
    structure = {}
    for channel in request.app['websockets'].keys():
        structure[channel] = {sub_channel: list(request.app['websockets'][channel][sub_channel]['Users'].keys())
                              for sub_channel in request.app['websockets'][channel].keys()}
    await ws_current.send_json({'action': 'get_structure',
                                'structure': structure})


async def get_user_list(request, ws_current, username):
    user_list = sorted(list(request.app['user_list'].keys()))
    user_list.pop(user_list.index(username))
    await ws_current.send_json({'action': 'user_list',
                                'user_list': user_list})


async def join(request, ws_current, username, channel, sub_channel):
    if request.app['user_list'][username] != (channel, sub_channel) and \
       channel in request.app['websockets'].keys() and \
       sub_channel in request.app['websockets'][channel].keys():
        old_channel, old_sub_channel = request.app['user_list'][username]

        del request.app['websockets'][old_channel][old_sub_channel]['Users'][username]

        request.app['websockets'][channel][sub_channel]['Users'][username] = ws_current
        request.app['user_list'][username] = (channel, sub_channel)

        log.info('%s joined the %s / %s ', username, channel, sub_channel)
        content = {
            'action': 'join',
            'user': username,
            'old_channel': old_channel,
            'old_sub_channel': old_sub_channel,
            'channel': channel,
            'sub_channel': sub_channel,
            'datetime': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        }
        await global_broadcast(request, ws_current, content)


async def update_username(request, ws_current, old_username, new_username):
    if new_username is not None and \
       old_username != new_username and \
       new_username not in request.app['user_list'].keys():
        log.info('%s updated your name to %s.', old_username, new_username)

        channel, sub_channel = request.app['user_list'][old_username]

        request.app['user_list'][new_username] = (channel, sub_channel)
        del request.app['user_list'][old_username]

        del request.app['websockets'][channel][sub_channel]['Users'][old_username]
        request.app['websockets'][channel][sub_channel]['Users'][new_username] = ws_current

        content = {
            'action': 'update_username',
            'old_username': old_username,
            'new_username': new_username,
        }
        await global_broadcast(request, ws_current, content)
        await ws_current.send_json({'action': 'updated_username',
                                    'username': new_username})

        return new_username

    await ws_current.send_json({'action': 'invalid_username'})


async def chat_message(request, ws_current, username, datetime, message):
    channel, sub_channel = request.app['user_list'].get(username)
    if username is not None and request.app['websockets'][channel][sub_channel]['Users'].get(username) is not None:
        content = {
            'action': 'chat_message',
            'user': username,
            'datetime': datetime,
            'message': message
        }

        await local_broadcast(request, ws_current, channel, sub_channel, content)


async def direct_message(request, username, recipient, datetime, message):
    channel, sub_channel = request.app['user_list'].get(recipient)
    ws = request.app['websockets'][channel][sub_channel]['Users'].get(recipient)

    content = {
        'action': 'direct_message',
        'user': username,
        'datetime': datetime,
        'message': message
    }
    await ws.send_json(content)
