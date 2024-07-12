import logging

from aiohttp import web
import views
from db import ChatCollection, UserCollection
from tokens import UserToken
from middlewares import is_authenticated

channels = {
    "Global": {
        'Logs': {}
    }
}


async def init_app():
    app = web.Application(middlewares=[is_authenticated, ])

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
    app.router.add_post('/user/', views.register_user)
    app.router.add_put('/user/', views.update_user)
    app.router.add_get('/user/', views.retrieve_user)
    app.router.add_post('/user/update_password', views.update_password)
    app.router.add_post('/login/', views.log_in)
    app.router.add_post('/logout/', views.log_out)
    app.router.add_post('/channel/', views.register_channel)
    app.router.add_put('/channel/', views.update_channel)
    app.router.add_get('/channel/', views.retrieve_channels)
    app.router.add_delete('/channel/', views.delete_channel)
    app.router.add_post('/channel/sub_channels/', views.register_sub_channel)
    app.router.add_put('/channel/sub_channels/', views.update_sub_channels)
    app.router.add_delete('/channel/sub_channels/', views.delete_sub_channels)


async def shutdown(app):
    for channel in app['websockets'].keys():
        for sub_channel in app['websockets'][channel].keys():
            for ws in app['websockets'][channel][sub_channel]['Users'].values():
                await ws.close()
    app['websockets'].clear()


def main():
    logging.basicConfig(level=logging.DEBUG)

    app = init_app()
    web.run_app(app)


if __name__ == '__main__':
    main()
