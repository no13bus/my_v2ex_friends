from celery import Celery,platforms
import time 
import settings
import requests
import json
from db import ConnectDB
from models import Users, Nodes, Replies, Topics
import datetime


celery = Celery('v2ex',broker='redis://localhost:6379/0',backend='redis://localhost')
celery.config_from_object('settings')
session = ConnectDB()


@celery.task
def test(strs):
    time.sleep(5)
    return strs
    
@celery.task
def users_tasks():
    pass

@celery.task
def nodes_tasks():
    url = 'http://v2ex.com/api/nodes/all.json'
    r = requests.get(url)
    j = json.loads(r.content)
    for item in j:
        nodetime = datetime.datetime.fromtimestamp(item['created'])
        node = Nodes(nodeid=item['id'], name=item['name'], url=item['url'], title=item['title'], 
            title_alternative=item['title_alternative'],topics=item['topics'], 
            header=item['header'], footer=item['footer'], node_created=nodetime)
        session.add(node)
        print item['name']
    session.commit()


@celery.task
def topics_tasks():
    pass

@celery.task
def replies_tasks():
    pass

@celery.task
def proxy_tasks():
    pass

# celery -A tasks worker -l info -c 100 -P gevent