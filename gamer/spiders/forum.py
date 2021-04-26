from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re
import scrapy
from ..items import ForumItem, TopicItem, PostItem, CommendItem


class ForumCrawler(scrapy.Spider):
    name = 'forum'
    start_urls = [
        "https://forum.gamer.com.tw/ajax/rank.php?c=21&page={}".format(x)
        for x in range(2, 35)
    ]
    start_urls.insert(0, 'https://forum.gamer.com.tw/')
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36'}
    now = datetime.today()
    today = now.date()
    yesterday = today - timedelta(days=1)
    before = now - timedelta(days=2)

    def start_requests(self):
        for start_url in self.start_urls:
            if start_url == 'https://forum.gamer.com.tw/':
                headers = dict(self.headers)
                headers.update({'referer': 'https://www.gamer.com.tw/'})
            else:
                headers = dict(self.headers)
                headers.update({'referer': 'https://forum.gamer.com.tw/'})
            yield scrapy.Request(url=start_url,
                                 headers=headers,
                                 callback=self.start_parse)

    def start_parse(self, response):
        if response.url == 'https://forum.gamer.com.tw/':
            pattern = re.compile(r'_data\ =\ \[\{.*\}\]')
            _data = pattern.findall(response.text)[0].split(' = ')[1]
            res = json.loads(_data)
        else:
            res = response.json()
        for forum in res:
            forum_id = forum['bsn']
            forum_name = forum['title']
            Forum = ForumItem()
            Forum['forum_id'] = forum_id
            Forum['forum_name'] = forum_name
            yield(Forum)
            headers = dict(self.headers)
            headers.update({'referer': "https://forum.gamer.com.tw/A.php?bsn={}".format(forum_id)})
            forum_url = "https://forum.gamer.com.tw/B.php?&bsn={}".format(forum_id)
            yield scrapy.Request(url=forum_url,
                                 headers=headers,
                                 callback=self.forum_parse,
                                 cb_kwargs={'bsn': forum_id})

    def forum_parse(self, response, bsn):
        soup = BeautifulSoup(response.body, 'lxml')
        forum_id = bsn
        forum_has_next = soup.find('a', {'class': 'next'})
        topic_list_exist = soup.find('table', {'class': 'b-list'})
        catch_count = 0
        total_count = 0
        if topic_list_exist:
            for topic in topic_list_exist.find_all(
                    'tr', {'class': ['b-list__row b-list-item b-imglist-item', 'b-list__row b-list__row--sticky b-list-item b-imglist-item']}):
                total_count += 1
                topic_last_time = topic.find('p', {'class': 'b-list__time__edittime'}).get_text().strip()
                if '今日' in topic_last_time:
                    topic_last_time = topic_last_time.replace('今日', self.today.strftime('%Y/%m/%d'))
                    topic_last_time = datetime.strptime(topic_last_time, '%Y/%m/%d %H:%M')
                elif '昨日' in topic_last_time:
                    topic_last_time = topic_last_time.replace('昨日', self.yesterday.strftime('%Y/%m/%d'))
                    topic_last_time = datetime.strptime(topic_last_time, '%Y/%m/%d %H:%M')
                else:
                    continue
                topic_id = int(topic.find('td', {'class': 'b-list__summary'}).a['name'])
                topic_name = topic.find('td', {'class': 'b-list__main'}).find(['p', 'a'], {'class': 'b-list__main__title'}).get_text()
                topic_author = topic.find('td', {'class': 'b-list__count'}).find('p', {'class': 'b-list__count__user'}).get_text().strip()
                topic_multi_page = topic.find('span', {'class': 'b-list__main__pages'})
                topic_first_page = response.urljoin(topic.find('td', {'class': 'b-list__main'}).a['href'])
                same_forum = re.match(r".*(bsn={})".format(forum_id), topic_first_page)
                if topic_last_time > self.before and same_forum:
                    catch_count += 1
                    Topic = TopicItem()
                    Topic['forum_id'] = forum_id
                    Topic['topic_id'] = topic_id
                    Topic['topic_name'] = topic_name
                    Topic['topic_author'] = topic_author
                    Topic['topic_last_time'] = topic_last_time
                    yield(Topic)
                    if topic_multi_page:
                        if topic_multi_page.find_all('span', {'class': 'b-list__page'}):
                            topic_last_page = response.urljoin(topic_multi_page.find_all('span', {'class': 'b-list__page'})[-1]['data-page'])
                        else:
                            topic_last_page = response.urljoin(topic_multi_page.find_all('a')[-1]['href'])
                        post_url = topic_last_page
                    else:
                        post_url = topic_first_page
                    headers = dict(self.headers)
                    headers.update({'referer': response.url})
                    yield scrapy.Request(url=post_url,
                                         headers=headers,
                                         callback=self.post_parse,
                                         cb_kwargs={
                                             'bsn': forum_id,
                                             'snA': topic_id
                                         })
        if catch_count == total_count and forum_has_next:
            next_page = response.urljoin(forum_has_next.get('href'))
            forum_url = next_page
            headers = dict(self.headers)
            headers.update({'referer': response.url})
            yield scrapy.Request(url=forum_url,
                                 headers=headers,
                                 callback=self.forum_parse,
                                 cb_kwargs={'bsn': forum_id})

    def post_parse(self, response, bsn, snA):
        soup = BeautifulSoup(response.body, 'lxml')
        forum_id = bsn
        topic_id = snA
        topic_has_prev = soup.find('a', {'class': 'prev'})
        post_list = soup.find_all('section', {'class': 'c-section'}, id=re.compile(r'^post_\d+$'))
        catch_count = 0
        total_count = 0
        for post in post_list:
            total_count += 1
            post_time = post.find('a', {'class': 'edittime tippy-post-info'}).get('data-mtime')
            post_time = datetime.strptime(post_time, '%Y-%m-%d %H:%M:%S')
            post_id = int(post['id'].split('_')[1])
            post_floor = int(post.find('a', {'class': 'floor'})['data-floor'])
            post_author = post.find('a', {'class': 'userid'}).get_text()
            post_content = post.find('div', {'class': 'c-article__content'}).get_text().strip()
            post_has_commend = post.find('div', {'class': 'c-reply__item'}, id=re.compile(r'^Commendcontent_\d+$'))
            if post_time > self.before:
                catch_count += 1
                Post = PostItem()
                Post['forum_id'] = forum_id
                Post['topic_id'] = topic_id
                Post['post_id'] = post_id
                Post['post_floor'] = post_floor
                Post['post_author'] = post_author
                Post['post_content'] = post_content
                Post['post_time'] = post_time
                yield(Post)
                if post_has_commend:
                    commend_url = "https://forum.gamer.com.tw/ajax/moreCommend.php?bsn={}&snB={}&returnHtml=0".format(forum_id, post_id)
                    headers = dict(self.headers)
                    headers.update({'referer': response.url})
                    yield scrapy.Request(url=commend_url,
                                         headers=headers,
                                         callback=self.commend_parse,
                                         cb_kwargs={
                                             'bsn': forum_id,
                                             'snB': post_id
                                         })
        if catch_count == total_count and topic_has_prev:
            post_url = response.urljoin(topic_has_prev.get('href'))
            headers = dict(self.headers)
            headers.update({'referer': response.url})
            yield scrapy.Request(url=post_url,
                                 headers=headers,
                                 callback=self.post_parse,
                                 cb_kwargs={
                                     'bsn': forum_id,
                                     'snA': topic_id
                                 })

    def commend_parse(self, response, bsn, snB):
        res = response.json()
        forum_id = bsn
        post_id = snB
        for key, value in res.items():
            if key.isdigit():
                if value['mtime'] == '0000-00-00 00:00:00':
                    commend_time = datetime.strptime(value['wtime'], '%Y-%m-%d %H:%M:%S')
                else:
                    commend_time = datetime.strptime(value['mtime'], '%Y-%m-%d %H:%M:%S')
                commend_id = int(value['sn'])
                commend_floor = int(key) + 1
                commend_author = value['userid']
                commend_content = value['content']
                if commend_time > self.before:
                    Commend = CommendItem()
                    Commend['forum_id'] = forum_id
                    Commend['post_id'] = post_id
                    Commend['commend_id'] = commend_id
                    Commend['commend_floor'] = commend_floor
                    Commend['commend_author'] = commend_author
                    Commend['commend_content'] = commend_content
                    Commend['commend_time'] = commend_time
                    yield(Commend)
