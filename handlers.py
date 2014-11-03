from urlparse import urlparse
import tornado
from models import *
from db import ConnectDB
from datetime import datetime

from tornado.gen import coroutine
from tasks import *
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.httpclient


# class BaseHandler(tornado.web.RequestHandler):
#     def initialize(self):
#         self.session = ConnectDB()

#     def on_finish(self):
#         self.session.close()

class BaseHandler(tornado.web.RequestHandler):
    @property
    def session(self):
        return self.application.session
    def get_current_user(self):
        return self.get_secure_cookie("username")

class IndexHandler(BaseHandler):
    @tornado.web.asynchronous
    def get(self):
        # user = Users(userid=1,username='jqh')
        # self.session.add(user)
        # self.session.commit()
        test.delay('sss')
        self.render('index.html')

    def post(self):
        pass


##example

# class LoginHandler(BaseHandler):
#     def post(self):
#         self.set_secure_cookie("username", self.get_argument("username"))
#         self.redirect("/")

# class LogoutHandler(BaseHandler):
#     def get(self):
#         self.clear_cookie("username")
#         self.redirect("/")

# class WelcomeHandler(BaseHandler):
#     @tornado.web.authenticated
#     def get(self):
#         self.render('index.html', user=self.current_user)