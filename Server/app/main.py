import logging
import asyncio

from aiohttp import web
from views import index


rooms = {
    "Global": {
        "Logs": {}
    },
    "League of Legends": {
        "Arena": {},
        "ARAM": {},
        "Clash": {},
    },
    "Age of empires III": {
        "Duel": {},
        "Casual Games": {},
        "Ranked": {},
    },
    "Age of mitology": {
        "Duel": {},
        "Casual Games": {},
    },
    "Lethal Company": {
        "Team 1": {},
        "Team 2": {},
        "Team 3": {},
    }
}


async def init_app():
    app = web.Application()

    app['websockets'] = rooms
    app['user_list'] = {}

    app.router.add_get('/', index)

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
