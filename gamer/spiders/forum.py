from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re
import scrapy


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
            print("看板ID:{},看板名稱:{}".format(
                forum_id,
                forum_name))
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
                topic_datetime = topic.find('p', {'class': 'b-list__time__edittime'}).get_text().strip()
                if '今日' in topic_datetime:
                    topic_datetime = topic_datetime.replace('今日', self.today.strftime('%Y/%m/%d'))
                    topic_datetime = datetime.strptime(topic_datetime, '%Y/%m/%d %H:%M')
                elif '昨日' in topic_datetime:
                    topic_datetime = topic_datetime.replace('昨日', self.yesterday.strftime('%Y/%m/%d'))
                    topic_datetime = datetime.strptime(topic_datetime, '%Y/%m/%d %H:%M')
                else:
                    continue
                topic_id = topic.find('td', {'class': 'b-list__summary'}).a['name']
                topic_name = topic.find('td', {'class': 'b-list__main'}).find(['p', 'a'], {'class': 'b-list__main__title'}).get_text()
                topic_author = topic.find('td', {'class': 'b-list__count'}).find('p', {'class': 'b-list__count__user'}).get_text().strip()
                topic_reply_count = topic.find('td', {'class': 'b-list__count'}).find_all('span')[0]['title'].split('：')[1]
                topic_view_count = topic.find('td', {'class': 'b-list__count'}).find_all('span')[1]['title'].split('：')[1]
                topic_multi_page = topic.find('span', {'class': 'b-list__main__pages'})
                topic_first_page = response.urljoin(topic.find('td', {'class': 'b-list__main'}).a['href'])
                same_forum = re.match(".*(bsn={})".format(forum_id), topic_first_page)
                if topic_datetime > self.before and same_forum:
                    catch_count += 1
                    print("主題ID:{},主題標題:{},主題作者:{},主題互動:{},主題人氣:{},最新回覆時間:{}".format(
                        topic_id,
                        topic_name,
                        topic_author,
                        topic_reply_count,
                        topic_view_count,
                        topic_datetime))
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
        topic_has_prev = soup.find('a', {'class': 'prev'}).get('href')
        post_list = soup.find_all('section', {'class': 'c-section'}, id=re.compile(r'^post_\d+$'))
        catch_count = 0
        total_count = 0
        for post in post_list:
            total_count += 1
            post_datetime = post.find('a', {'class': 'edittime tippy-post-info'}).get('data-mtime')
            post_datetime = datetime.strptime(post_datetime, '%Y-%m-%d %H:%M:%S')
            post_id = post['id'].split('_')[1]
            post_floor = post.find('a', {'class': 'floor'})['data-floor']
            post_author = post.find('a', {'class': 'userid'}).get_text()
            post_content = post.find('div', {'class': 'c-article__content'}).get_text().strip()
            post_has_commend = post.find('div', {'class': 'c-reply__item'}, id=re.compile(r'^Commendcontent_\d+$'))
            if post_datetime > self.before:
                catch_count += 1
                print("文章ID:{},文章樓層:{},文章作者:{},文章內容:{},文章時間:{}".format(
                    post_id,
                    post_floor,
                    post_author,
                    post_content,
                    post_datetime))
                if post_has_commend:
                    commend_url = "https://forum.gamer.com.tw/ajax/moreCommend.php?bsn={}&snB={}&returnHtml=0".format(forum_id, post_id)
                    headers = dict(self.headers)
                    headers.update({'referer': response.url})
                    yield scrapy.Request(url=commend_url,
                                         headers=headers,
                                         callback=self.commend_parse,
                                         cb_kwargs={
                                             'bsn': forum_id,
                                             'snA': topic_id,
                                             'snB': post_id
                                         })
        if catch_count == total_count and topic_has_prev:
            post_url = response.urljoin(topic_has_prev)
            headers = dict(self.headers)
            headers.update({'referer': response.url})
            yield scrapy.Request(url=post_url,
                                 headers=headers,
                                 callback=self.post_parse,
                                 cb_kwargs={
                                     'bsn': forum_id,
                                     'snA': topic_id
                                 })

    def commend_parse(self, response, bsn, snA, snB):
        res = response.json()
        forum_id = bsn
        topic_id = snA
        post_id = snB
        for key, value in res.items():
            if key.isdigit():
                if value['mtime'] == '0000-00-00 00:00:00':
                    commend_datetime = datetime.strptime(value['wtime'], '%Y-%m-%d %H:%M:%S')
                else:
                    commend_datetime = datetime.strptime(value['mtime'], '%Y-%m-%d %H:%M:%S')
                commend_id = value['sn']
                commend_floor = int(key) + 1
                commend_author = value['userid']
                commend_content = value['content']
                if commend_datetime > self.before:
                    print("評論ID:{},評論樓層:{},評論作者:{},評論內容:{},評論時間:{}".format(
                        commend_id,
                        commend_floor,
                        commend_author,
                        commend_content,
                        commend_datetime))
