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

DB_CONNECT_STRING = 'mysql+mysqldb://root:root@localhost/v2exfriends?charset=utf8&use_unicode=0'

#celery settings
CELERYD_POOL_RESTARTS = True


from datetime import timedelta
CELERYBEAT_SCHEDULE = {
    'trade-every-6-seconds': {
        'task': 'btc.tasks.user_trade',
        'schedule': timedelta(seconds=4),
    },
    'trade-ok2btcchina': {
        'task': 'btc.tasks.okcoin2btcchina_trade',
        'schedule': timedelta(seconds=4),
    },
    'trade-date': {
        'task': 'btc.tasks.tradedate',
        'schedule': timedelta(seconds=10),
    },
    'trade-date-analysis': {
        'task': 'btc.tasks.tradedate_analysis',
        'schedule': timedelta(seconds=60),
    },
    'settings_bool_tasks_every_8hours': {
        'task': 'btc.tasks.set_bool_task',
        'schedule': timedelta(seconds=3600*8),
    },
}