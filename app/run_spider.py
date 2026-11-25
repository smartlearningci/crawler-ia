import json
import sys
from scrapy.crawler import CrawlerProcess
from .spider import SchoolsSpider

if __name__ == "__main__":
    urls, query, depth, pages = json.loads(sys.argv[1]), sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    process = CrawlerProcess(settings={"LOG_ENABLED": True})
    process.crawl(SchoolsSpider, urls=urls, pesquisa=query, profundidade=depth, max_pages=pages)
    process.start()
