url = 'http://v2ex.com/member/%s/topics?p=1' % username
    r = requests.get(url, timeout=60*4)
    c = r.content
    b = BeautifulSoup(c)
    page_num = b.select('.inner')[2].select('.fade')[0].text
    page_num = int(page_num.replace('1/',''))
    for page in xrange(1,page_num+1):
        url = 'http://v2ex.com/member/%s/topics?p=%s' % (username, page)
        r = requests.get(url, timeout=60*4)
        c = r.content
        b = BeautifulSoup(c)
        topics = b.select('.cell.item')
        for topic in topics:
            title = topic.select('span')[0].string
            repies_count = int(topic.select('.count_livid')[0]) if topic.select('.count_livid') else 0
            topic_info = topic.select('span')[1].text.split(u'\xa0\u2022\xa0')
            topic_node_name = topic_info[0].replace(' ','')
            topic_url = 'http://v2ex.com%s' % topic.select('span')[0].a['href']
            patt = re.compile(u'.*?t/(\d+)#.*')
            topicid = int(re.findall(patt,topic_url)[0])

            topic_r = requests.get(topic_url, headers=headers, timeout=60*4)
            topic_c = topic_r.content
            topic_b = BeautifulSoup(topic_c)
            ## 帖子不一定有内容
            tc = topic_b.select('.topic_content')
            topic_content = u''
            if tc:
                for i in topic_b.select('.topic_content'):
                    topic_content = topic_content + i.text

            topic_info2 = topic_b.select('small.gray')[0].text.split(u'\xb7')
            topic_created = topic_info2[1].replace(' ','')
            topic_clicks = topic_info2[2].replace(' ','').replace(u'\u6b21\u70b9\u51fb', '')
            topic_clicks = int(topic_clicks)
            member = session.query(Users).filter(Users.username=username).first()
            node = session.query(Nodes).filter(Nodes.name=topic_node_name).first()
            Topics(topicid=topicid, title=title, url=topic_url, content=topic_content,
                repies=repies_count, member=member, node=node, topic_created=topic_created)