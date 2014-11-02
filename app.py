__author__ = 'no13bus'

from tornado import web, ioloop, httpserver
from tornado.options import options, define
import handlers
import tornadoredis
import os


define('port', default=8000, type=int, help='server port')
define('template_path', default=os.path.join(os.path.dirname(__file__), "templates"), type=str, help='template path')
# define('redis_host', default='127.0.0.1', type=str, help='Redis server host')
# define('redis_port', default=6379, type=int, help='Redis server port')
define('static_path', default=os.path.join(os.path.dirname(__file__), "static"), help='Redis server port')

class V2exapp(web.Application):
    def __init__(self):
        routes = [
            (r'/.*', handlers.IndexHandler),
            (r"/login", handlers.LoginHandler),
        ]
        # connection_pool = tornadoredis.ConnectionPool(max_connections=500, wait_for_available=True)
        # db_client = tornadoredis.Client(host=options.redis_host, port=options.redis_port)
        # db_client.connect()

        settings = {
            'gzip': True,
            'autoescape': 'xhtml_escape',
            'static_path': static_path,
            'template_path': options.template_path,
            "xsrf_cookies": True,
            "cookie_secret": "61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            "login_url": "/login",
            'debug': True,
        }

        web.Application.__init__(self, routes, **settings)


if __name__ == '__main__':
    options.parse_command_line()
    app = V2exapp()
    server = httpserver.HTTPServer(app)
    server.listen(options.port)
    print "port:%s" % options.port

    # server.bind(options.port, address=options.host)

    # start(0) starts a subprocess for each CPU core
    # server.start(1 if options.debug else 0)

    loop = ioloop.IOLoop.instance()

    loop.start()