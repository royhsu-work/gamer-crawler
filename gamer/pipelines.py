# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from .items import ForumItem, TopicItem, PostItem, CommendItem
from .models import db_connect, create_table, Forum, User, Topic, Post, Commend
from sqlalchemy.orm import sessionmaker


class GamerPipeline:
    def open_spider(self, spider):
        engine = db_connect()
        create_table(engine)
        self.Session = sessionmaker(bind=engine)

    def close_spider(self, spider):
        session = self.Session()
        session.close()

    def process_item(self, item, spider):
        if isinstance(item, ForumItem):
            return self.handle_forum(item, spider)
        if isinstance(item, TopicItem):
            return self.handle_topic(item, spider)
        if isinstance(item, PostItem):
            return self.handle_post(item, spider)
        if isinstance(item, CommendItem):
            return self.handle_commend(item, spider)

    def handle_forum(self, item, spider):
        session = self.Session()
        forum = Forum()
        forum.id = item['forum_id']
        forum.name = item['forum_name']
        exists = session.query(Forum).filter_by(id=forum.id).first()
        if not exists:
            try:
                session.add(forum)
                session.commit()
            except:
                session.rollback()
                raise
        return item

    def handle_topic(self, item, spider):
        session = self.Session()
        user = session.query(User).filter_by(name=item['topic_author']).first()
        if not user:
            try:
                user = User(name=item['topic_author'])
                session.add(user)
                session.commit()
            except:
                session.rollback()
                raise
        topic = Topic()
        topic.id = item['topic_id']
        topic.name = item['topic_name']
        topic.last_time = item['topic_last_time']
        topic.user_id = user.id
        topic.forum_id = item['forum_id']
        exists = session.query(Topic).filter_by(id=topic.id, forum_id=topic.forum_id).first()
        if not exists:
            try:
                session.add(topic)
                session.commit()
            except:
                session.rollback()
                raise
        else:
            if topic.last_time > exists.last_time:
                try:
                    exists.name = topic.name
                    exists.last_time = topic.last_time
                    session.commit()
                except:
                    session.rollback()
                    raise
        return item

    def handle_post(self, item, spider):
        session = self.Session()
        user = session.query(User).filter_by(name=item['post_author']).first()
        if not user:
            try:
                user = User(name=item['post_author'])
                session.add(user)
                session.commit()
            except:
                session.rollback()
                raise
        post = Post()
        post.id = item['post_id']
        post.floor = item['post_floor']
        post.content = item['post_content']
        post.time = item['post_time']
        post.user_id = user.id
        post.forum_id = item['forum_id']
        post.topic_id = item['topic_id']
        exists = session.query(Post).filter_by(id=post.id, forum_id=post.forum_id, topic_id=post.topic_id).first()
        if not exists:
            try:
                session.add(post)
                session.commit()
            except:
                session.rollback()
                raise
        else:
            if post.time > exists.time:
                try:
                    exists.content = post.content
                    exists.time = post.time
                    session.commit()
                except:
                    session.rollback()
                    raise
        return item

    def handle_commend(self, item, spider):
        session = self.Session()
        user = session.query(User).filter_by(name=item['commend_author']).first()
        if not user:
            try:
                user = User(name=item['commend_author'])
                session.add(user)
                session.commit()
            except:
                session.rollback()
                raise
        commend = Commend()
        commend.id = item['commend_id']
        commend.floor = item['commend_floor']
        commend.content = item['commend_content']
        commend.time = item['commend_time']
        commend.user_id = user.id
        commend.forum_id = item['forum_id']
        commend.post_id = item['post_id']
        exists = session.query(Commend).filter_by(id=commend.id, forum_id=commend.forum_id, post_id=commend.post_id).first()
        if not exists:
            try:
                session.add(commend)
                session.commit()
            except:
                session.rollback()
                raise
        else:
            if commend.time > exists.time:
                try:
                    exists.content = commend.content
                    exists.time = commend.time
                    session.commit()
                except:
                    session.rollback()
                    raise
        return item
