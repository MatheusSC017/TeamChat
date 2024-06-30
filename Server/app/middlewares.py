from aiohttp import web
import base64
import functools


@web.middleware
async def is_authenticated(request, handler):
    access_token = request.headers.get('Authorization', None)
    if access_token is not None:
        username, authenticated = request.app['tokens'].authenticate(base64.b64decode(access_token))
        request['is_authenticated'] = authenticated
        request['username'] = username
    else:
        request['is_authenticated'] = False

    response = await handler(request)

    return response
