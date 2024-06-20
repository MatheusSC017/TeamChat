async def global_broadcast(request, ws_current, content):
    for channel in request.app['websockets'].keys():
        for sub_channel in request.app['websockets'][channel].keys():
            await local_broadcast(request, ws_current, channel, sub_channel, content)


async def local_broadcast(request, ws_current, channel, sub_channel, content):
    for ws in request.app['websockets'][channel][sub_channel]['Users'].values():
        if ws is not ws_current:
            await ws.send_json(content)
