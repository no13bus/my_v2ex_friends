#coding=utf8
from celery import Celery,platforms
import time 
import settings
import requests
import json
from db import ConnectDB
from models import Users, Nodes, Replies, Topics
import datetime

import re
import random
from bs4 import BeautifulSoup
import redis
import logging
import logging.handlers

celery = Celery('v2ex',broker='redis://localhost:6379/0',backend='redis://localhost')
celery.config_from_object('settings')
session = ConnectDB()

LOG_FILE = 'v2ex.log'
handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes = 1024*1024, backupCount = 5)
fmt = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'
formatter = logging.Formatter(fmt)
handler.setFormatter(formatter)
logger = logging.getLogger('crawlog')
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

@celery.task
def users_tasks():
    # http://v2ex.com/api/members/show.json?id=79988
    proxy_ports = settings.RD.lrange('ip_port',2,19)
    for xx in proxy_ports:
        last = session.query(Users).order_by('-userid')
        last = last[0].userid if last else 1
        for id in xrange(last,last+105):
            print id
            url = 'http://v2ex.com/api/members/show.json?id=%s' % id
            if id>79988:
                return
            proxies = {'http':xx}
            print proxies
            for x in xrange(1,5):
                try:
                    r = requests.get(url, proxies=proxies, timeout=60*4)
                    print 'seccess'
                    break
                except Exception as p2:
                    print p2
                    time.sleep(1)
                    print 'next try'
                    if x>=4:
                        logger.debug('userid=%s' % id)
                        print p2
                        return

            # try:
            #     r = requests.get(url, proxies=proxies, timeout=60*4)
            # except:
            #     logger.debug('userid=%s' % id)
            #     continue
            try:
                item = json.loads(r.content)
            except:
                continue
            print item
            usertime = datetime.datetime.fromtimestamp(item['created'])
            useritem = session.query(Users).filter_by(userid=item['id']).first()
            if not useritem:
                user = Users(userid=item['id'], status=item['status'], url=item['url'],
                    username=item['username'], website=item['website'], twitter=item['twitter'],
                    psn=item['psn'], github=item['github'], btc=item['btc'],
                    location=item['location'], tagline=item['tagline'],bio=item['bio'],
                    avatar_normal=item['avatar_normal'],user_created=usertime)
                session.add(user)
                print item['username']
            session.commit()

@celery.task
def nodes_tasks():
    url = 'http://v2ex.com/api/nodes/all.json'
    r = requests.get(url)
    j = json.loads(r.content)
    for item in j:
        nodetime = datetime.datetime.fromtimestamp(item['created'])
        nodeitem = session.query(Nodes).filter_by(nodeid=item['id']).first()
        if not nodeitem:
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

def getport(resultstring):
    exec('port = %s' % resultstring)
    port = eval('port')
    return port


def testproxy(ip_port):
    mysession = requests.Session()
    url = 'http://v2ex.com/api/nodes/all.json'
    proxies = {'http':ip_port}
    try:
        r = mysession.get(url, proxies=proxies, timeout=60*4)
    except:
        return -1

@celery.task
def proxy_task():
    # ip_lists = proxy_iplist.objects.filter(worked=True).order_by('-created')[0:5]
    # pool = redis.ConnectionPool(host='localhost', port=6379, db=1)
    # rd = redis.Redis(connection_pool=pool)
    # # rd = settings.RD
    ip_nums = settings.RD.llen('ip_port')
    if settings.RD.llen('ip_port') >= 6:
        settings.RD.ltrim('ip_port',0,0)
        print '1 step done'

    proxyurl= 'http://www.pachong.org/'
    headers = {
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding':'gzip,deflate,sdch',
    'Accept-Language':'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
    'Cache-Control':'max-age=0',
    'Connection':'keep-alive',
    'Host':'pachong.org',
    'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.101 Safari/537.36'
    }
    proxysession = requests.Session()
    try:
        r = proxysession.get(proxyurl,timeout=60*4)
    except:
        print 'I can not get the date of pachong.org'
    if r.status_code != 200:
        print 'the status is not good. status_code is %s' % r.status_code
        return
    ht = BeautifulSoup(r.content)
    animals = str(ht.head.find_all('script')[-1].text)
    for item in animals.split(';'):
        exec(item.replace('var','').strip())

    table = ht.find_all('tbody')
    if not table:
        return
    table = table[0]
    trs = table.find_all('tr',attrs={'data-type':'high'})
    

    for tr in trs:
        idlestring = tr.find_all('td')[5].text
        idlestring = idlestring.replace('\n','').replace(' ','')
        if idlestring == u'空闲':
            ip = tr.find_all('td')[1].text
            portstring = tr.find_all('td')[2].text

            patt = re.compile(u'document.write\((.*?)\);')

            if re.findall(patt,portstring):
                resultstring = re.findall(patt,portstring)[0]
            else:
                continue

            exec('port = %s' % resultstring)
            port = eval('port')
            ip_port = '%s:%s' % (ip, port)
            print 'ip_port is %s' % ip_port
            if testproxy(ip_port) == -1:
                continue
            if settings.RD.llen('ip_port')<=6:
                settings.RD.lpush('ip_port', ip_port)
            else:
                print 'it is done ip_port'
                break

    print 'it is done'
# {u'status': u'error', u'message': u'Rate Limit Exceeded', u'rate_limit': {u'hourly_remaining': 0, u'used': 120, u'hourly_quota': 120}}
# celery -A tasks worker -l info -c 100 -P gevent