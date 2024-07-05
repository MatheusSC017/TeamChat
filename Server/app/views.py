from aiohttp import web
from bson import json_util
import aiohttp
import json
import base64
from actions import *

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
    if not request['is_authenticated']:
        return web.Response(status=401)
    user_data = await request.post()
    updated, _ = await request.app['user_collection'].update_user(request['username'], user_data)
    if updated:
        return web.Response(status=202)
    return web.Response(status=500)


async def retrieve_user(request):
    if not request['is_authenticated']:
        return web.Response(status=401)
    user = await request.app['user_collection'].get_user(request['username'])
    del user['password']
    return web.Response(body=json_util.dumps(user), status=200)


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

    logged_out = request.app['tokens'].del_user(base64.b64decode(access_token))
    if logged_out:
        return web.Response(status=200)
    return web.Response(status=401)


async def retrieve_channels(request):
    if not request['is_authenticated']:
        return web.Response(status=401)
    if request['is_authenticated']:
        channels = await request.app['chat_collection'].get_channels(owner=request['username'])
        for channel in channels.keys():
            for sub_channel in channels[channel].keys():
                if 'password' in channels[channel][sub_channel].keys():
                    del channels[channel][sub_channel]['password']
        return web.Response(body=json_util.dumps(channels), status=200)
    return web.Response(status=401)


async def register_channel(request):
    if not request['is_authenticated']:
        return web.Response(status=401)

    channel_data = await request.json()
    inserted, result = await request.app['chat_collection'].register_channel(channel_data['channel'], request['username'])

    if inserted:
        return web.Response(status=201)

    return web.Response(body=json.dumps({'errors': result}), status=400)


async def update_channel(request):
    if not request['is_authenticated']:
        return web.Response(status=401)

    channel_data = await request.json()
    updated = await request.app['chat_collection'].update_channel(channel_data['old_channel_name'],
                                                                  channel_data['new_channel_name'],
                                                                  request['username'])
    if updated:
        return web.Response(status=200)

    return web.Response(status=400)


async def delete_channel(request):
    if not request['is_authenticated']:
        return web.Response(status=401)

    channel = await request.json()
    deleted = await request.app['chat_collection'].delete_channel(channel['channel'],
                                                                  request['username'])
    if deleted:
        return web.Response(status=200)
    return web.Response(status=500)


async def register_sub_channel(request):
    if not request['is_authenticated']:
        return web.Response(status=401)

    channel_data = await request.json()
    inserted, result = await request.app['chat_collection'].register_sub_channel(channel_data['channel'],
                                                                                 channel_data['sub_channel'],
                                                                                 request['username'])
    if inserted:
        return web.Response(status=201)
    return web.Response(body=json.dumps({'errors': result}), status=400)


async def update_sub_channels(request):
    if not request['is_authenticated']:
        return web.Response(status=401)

    channel_data = await request.json()
    updated, result = await request.app['chat_collection'].update_sub_channels(channel_data['channel'],
                                                                               channel_data['sub_channels'],
                                                                               request['username'])
    if updated:
        return web.Response(status=202)
    return web.Response(status=500, body=json.dumps({'errors': result}))


async def delete_sub_channels(request):
    if not request['is_authenticated']:
        return web.Response(status=401)

    channel = await request.json()
    deleted = await request.app['chat_collection'].delete_sub_channels(channel['channel'],
                                                                       channel['sub_channels'],
                                                                       request['username'])
    if deleted:
        return web.Response(status=200)
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
                        await join(request, ws_current, username, **message_json)

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
