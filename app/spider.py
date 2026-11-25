"""Scrapy sobre sites descobertos por pesquisas; sem recolha de dados privados."""
import logging
from urllib.parse import urlparse
import scrapy
from .core import contact_links, emails_from_html, school_name, greeting
from .database import connection

LOG = logging.getLogger(__name__)

class SchoolsSpider(scrapy.Spider):
    name = "schools"
    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 4,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_DELAY": 1.5,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 2,
        "AUTOTHROTTLE_MAX_DELAY": 20,
        "DOWNLOAD_TIMEOUT": 15,
        "USER_AGENT": "CrawlerIA/0.1 (+contactos institucionais públicos; respeita robots.txt)",
        "LOG_LEVEL": "WARNING",
    }

    def __init__(self, urls=None, pesquisa="", profundidade=2, max_pages=60, **kwargs):
        super().__init__(**kwargs)
        self.urls = urls or []
        self.pesquisa = pesquisa
        self.profundidade = max(0, min(int(profundidade), 4))
        self.max_pages = max(1, min(int(max_pages), 500))
        self.seen_count = 0
        self.site_names = {}
        self.saved = 0

    def start_requests(self):
        for url in self.urls:
            host = urlparse(url).hostname
            if host:
                yield scrapy.Request(url, callback=self.parse, cb_kwargs={"host": host, "depth": 0}, dont_filter=False)

    def parse(self, response, host, depth):
        if self.seen_count >= self.max_pages:
            return
        self.seen_count += 1
        if not response.headers.get("Content-Type", b"").lower().startswith(b"text/html"):
            return
        if response.url.split("/")[2].lower() != host.lower():
            return
        html = response.text
        if host not in self.site_names:
            self.site_names[host] = school_name(html, host)
        name = self.site_names[host]
        for email in emails_from_html(html):
            try:
                with connection() as db:
                    inserted = db.execute("""INSERT INTO contacts
                     (email, escola, saudacao, website, fonte, pesquisa) VALUES (%s,%s,%s,%s,%s,%s)
                     ON CONFLICT (email) DO NOTHING RETURNING id""",
                     (email, name, greeting(name), f"{urlparse(response.url).scheme}://{host}", response.url, self.pesquisa)).fetchone()
                    db.commit()
                    self.saved += bool(inserted)
            except Exception as exc:
                LOG.warning("Erro ao guardar email: %s", exc)
        if depth >= self.profundidade or self.seen_count >= self.max_pages:
            return
        for href in contact_links(html, response.url, host):
            if self.seen_count >= self.max_pages:
                break
            yield scrapy.Request(href, callback=self.parse, cb_kwargs={"host":host, "depth":depth+1})
