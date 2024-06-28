from datetime import datetime
import logging
from utils import local_broadcast, global_broadcast

log = logging.getLogger(__name__)


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
        structure[channel] = {}
        for sub_channel in request.app['websockets'][channel].keys():
            structure[channel][sub_channel] = {}
            for config, values in request.app['websockets'][channel][sub_channel].items():
                structure[channel][sub_channel]['Users'] = list(values.keys()) if config == 'Users' else values
    await ws_current.send_json({'action': 'get_structure', 'structure': structure})


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
