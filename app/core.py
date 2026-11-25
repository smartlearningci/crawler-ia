"""Pesquisa inicial e extração prudente de contactos institucionais públicos."""
import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
BLOCKED = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".pdf", ".css", ".js", ".zip")
CONTACT_WORDS = ("contact", "contacto", "contato", "direcao", "direção", "secretaria", "equipa", "sobre", "quem-somos", "institucional")
EXCLUDED_EMAILS = ("example.com", "example.org", "wixpress.com", "sentry.io")

def clean_url(url):
    url = (url or "").strip()
    if url.startswith("//"):
        url = "https:" + url
    p = urlparse(url)
    if p.scheme not in ("https", "http") or not p.hostname:
        return None
    if p.username or p.password:
        return None
    if p.port and p.port not in (80, 443):
        return None
    return p._replace(fragment="").geturl()

def emails_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    visible = soup.get_text(" ", strip=True)
    mailto = " ".join(a.get("href", "")[7:].split("?")[0] for a in soup.select('a[href^="mailto:"]'))
    items = {m.group(0).lower().strip(".,;:") for m in EMAIL.finditer(visible + " " + mailto)}
    return sorted(e for e in items if e.split("@")[-1] not in EXCLUDED_EMAILS and not e.endswith(BLOCKED))

def school_name(html, hostname):
    soup = BeautifulSoup(html, "html.parser")
    for tag in (soup.find("h1"), soup.find("title")):
        if tag and tag.get_text(strip=True):
            return re.split(r"\s+[|–—]\s+", tag.get_text(" ", strip=True))[0][:180]
    return hostname

def contact_links(html, page_url, hostname):
    soup = BeautifulSoup(html, "html.parser")
    candidates = []
    for a in soup.find_all("a", href=True):
        href = clean_url(urljoin(page_url, a["href"]))
        if not href or urlparse(href).hostname != hostname:
            continue
        if urlparse(href).path.lower().endswith(BLOCKED):
            continue
        label = (a.get_text(" ", strip=True) + " " + href).lower()
        score = int(any(word in label for word in CONTACT_WORDS))
        candidates.append((1-score, href))
    return [u for _, u in sorted(set(candidates))]

def greeting(name):
    return f"Exmos. Senhores da {name}" if name else "Exmos. Senhores"

def parse_search_results(html):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.select("li.b_algo h2 a[href], h2 a[href]"):
        link = clean_url(a.get("href"))
        if link and urlparse(link).hostname not in ("bing.com", "www.bing.com"):
            links.append(link)
    return list(dict.fromkeys(links))
