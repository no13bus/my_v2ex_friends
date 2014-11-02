from urlparse import urlparse
from tornado import web, gen
import models

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.session = models.DB_Session()

    def on_finish(self):
        self.session.close()

class IndexHandler(BaseHandler):
    def get(self):
        self.get_argument('oo')
        self.render('index.html')

    def post(self):
        noun1 = self.get_argument('noun1')
        noun2 = self.get_argument('noun2')
        verb = self.get_argument('verb')
        noun3 = self.get_argument('noun3')
        self.render('poem.html', roads=noun1, wood=noun2, made=verb, difference=noun3)

class LoginHandler(BaseHandler):
    def get(self):
        pass
    def post(self):
        pass
        