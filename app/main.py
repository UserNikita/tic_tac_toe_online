import logging

import jinja2

import aiohttp_jinja2
from aiohttp import web
from views import index


async def init_app():
    app = web.Application()
    app['ws'] = {}
    # app.on_shutdown.append(shutdown)
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./templates'))
    app.router.add_get('/', index)
    return app


# async def shutdown(app):
#     for ws in app['ws'].values():
#         await ws.close()
#     app['ws'].clear()


def main():
    logging.basicConfig(level=logging.DEBUG)
    app = init_app()
    web.run_app(app)


if __name__ == '__main__':
    main()
