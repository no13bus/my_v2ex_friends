#!/usr/bin/env python
#coding=utf8

import os
settings = {
    'gzip': True,
    'autoescape': 'xhtml_escape',
    'static_path':os.path.join(os.path.dirname(__file__), 'static'),
    'template_path':os.path.join(os.path.dirname(__file__), 'templates'),
    "xsrf_cookies": True,
    "cookie_secret": "61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
    "login_url": "/login",
    'debug': True,
}

# DB_CONNECT_STRING = 'mysql+mysqldb://root:root@localhost/v2exfriends?charset=utf8'
import redis
pool = redis.ConnectionPool(host='localhost', port=6379, db=1)
RD = redis.Redis(connection_pool=pool)


#celery settings
CELERYD_POOL_RESTARTS = True
CELERYD_FORCE_EXECV = True

from datetime import timedelta
CELERYBEAT_SCHEDULE = {
    'users_chain_3600': {
        'task': 'tasks.users_chain',
        'schedule': timedelta(seconds=4500),
    },
    
}
