from crochet import setup
import logging
import schedule
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
import time

LOGGING_FORMAT = '%(asctime)s [%(name)s.%(funcName)s] %(levelname)s: %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT, datefmt=DATE_FORMAT)


def job():
    runner = CrawlerRunner(get_project_settings())
    runner.crawl('forum')


def main():
    setup()
    schedule.every().hour.do(job)
    schedule.run_all()
    count = 0
    while True:
        if count == 60:
            logging.info("下次執行時間：{}，還要等待：{}秒".format(
                schedule.next_run().strftime('%Y-%m-%d %H:%M:%S'),
                int(schedule.idle_seconds())
                ))
            count = 0
        else:
            count += 1
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    main()
