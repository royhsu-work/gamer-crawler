# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class GamerItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class ForumItem(scrapy.Item):
    forum_id = scrapy.Field()
    forum_name = scrapy.Field()


class TopicItem(scrapy.Item):
    forum_id = scrapy.Field()
    topic_id = scrapy.Field()
    topic_name = scrapy.Field()
    topic_author = scrapy.Field()
    topic_last_time = scrapy.Field()


class PostItem(scrapy.Item):
    forum_id = scrapy.Field()
    topic_id = scrapy.Field()
    post_id = scrapy.Field()
    post_floor = scrapy.Field()
    post_author = scrapy.Field()
    post_content = scrapy.Field()
    post_time = scrapy.Field()


class CommendItem(scrapy.Item):
    forum_id = scrapy.Field()
    post_id = scrapy.Field()
    commend_id = scrapy.Field()
    commend_floor = scrapy.Field()
    commend_author = scrapy.Field()
    commend_content = scrapy.Field()
    commend_time = scrapy.Field()
