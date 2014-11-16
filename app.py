# coding=utf8
__author__ = 'no13bus'

from tornado import web, ioloop, httpserver
from settings import settings
from tornado.options import options, define
import tornadoredis
import os
import handlers
from db import ConnectDB

define('port', default=8000, type=int, help='server port')
define('template_path', default=os.path.join(
    os.path.dirname(__file__), "templates"), type=str, help='template path')
define('static_path', default=os.path.join(
    os.path.dirname(__file__), "static"), help='static file path')


class V2exapp(web.Application):

    def __init__(self):
        routes = [
            (r'/', handlers.IndexHandler),
            (r'/u/(.*)', handlers.UsersHandler),

        ]
        web.Application.__init__(self, routes, **settings)
        self.session = ConnectDB()


if __name__ == '__main__':
    options.parse_command_line()
    app = V2exapp()
    server = httpserver.HTTPServer(app)
    server.listen(options.port)
    print "port:%s" % options.port
    loop = ioloop.IOLoop.instance()

    loop.start()
