import logging

from aiohttp import web
from views import index, add_user
from db import ChatCollection, UserCollection

channels = {
    "Global": {
        'Logs': {}
    }
}


async def init_app():
    app = web.Application()

    app['user_collection'] = UserCollection()
    app['chat_collection'] = ChatCollection()
    channels.update(await app['chat_collection'].get_channels())
    app['websockets'] = channels
    app['user_list'] = {}

    app.router.add_get('/', index)
    app.router.add_post('/register_user/', add_user)

    app.on_shutdown.append(shutdown)

    return app


async def shutdown(app):
    for channel in app['websockets'].keys():
        for sub_channel in app['websockets'][channel].keys():
            for ws in app['websockets'][channel][sub_channel].values():
                await ws.close()
    app['websockets'].clear()


def main():
    logging.basicConfig(level=logging.DEBUG)

    app = init_app()
    web.run_app(app)


if __name__ == '__main__':
    main()
