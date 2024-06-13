import logging

from aiohttp import web
import views
from db import ChatCollection, UserCollection
from tokens import UserToken

channels = {
    "Global": {
        'Logs': {}
    }
}


async def init_app():
    app = web.Application()

    app['tokens'] = UserToken()

    app['user_collection'] = UserCollection()
    app['chat_collection'] = ChatCollection()

    channels.update(await app['chat_collection'].get_channels())
    for channel in channels.keys():
        for sub_channel in channels[channel].keys():
            channels[channel][sub_channel]['Users'] = {}

    app['websockets'] = channels
    app['user_list'] = {}

    set_routes(app)

    app.on_shutdown.append(shutdown)

    return app


def set_routes(app):
    app.router.add_get('/', views.index)
    app.router.add_post('/register_user/', views.register_user)
    app.router.add_post('/update_user/', views.update_user)
    app.router.add_post('/login/', views.log_in)
    app.router.add_post('/logout/', views.log_out)
    app.router.add_get('/retrieve_user/', views.retrieve_user)
    app.router.add_get('/retrieve_channels/', views.retrieve_channels)


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
