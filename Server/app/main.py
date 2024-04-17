import logging
import asyncio

from aiohttp import web
from views import index


async def init_app():
    app = web.Application()

    app['websockets'] = {}

    app.router.add_get('/', index)

    app.on_shutdown.append(shutdown)

    return app


async def shutdown(app):
    for ws in app['websockets'].values():
        await ws.close()
    app['websockets'].clear()


def main():
    logging.basicConfig(level=logging.DEBUG)

    app = init_app()
    web.run_app(app)


if __name__ == '__main__':
    main()
