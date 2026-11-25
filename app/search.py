"""Descoberta de URLs; Bing HTML (best effort) ou Google Programmable Search API."""
import os
from urllib.parse import urlparse
import requests
from .core import parse_search_results, clean_url

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SchoolResearch/1.0)"}

def find_sites(query, max_results=20):
    max_results = min(max(1, int(max_results)), 100)
    provider = os.getenv("SEARCH_ENGINE", "bing")
    urls = []
    if provider == "google_api":
        key = os.getenv("SEARCH_API_KEY")
        cx = os.getenv("SEARCH_CX")
        if not key or not cx:
            raise RuntimeError("Faltam SEARCH_API_KEY e SEARCH_CX no .env")
        for start in range(1, max_results + 1, 10):
            r = requests.get("https://www.googleapis.com/customsearch/v1", params={"q":query, "key":key, "cx":cx, "start":start, "num":min(10,max_results-start+1)}, timeout=20)
            r.raise_for_status()
            urls.extend(item["link"] for item in r.json().get("items", []) if item.get("link"))
    elif provider == "bing":
        for first in range(1, max_results + 1, 10):
            r = requests.get("https://www.bing.com/search", params={"q": query, "first": first, "count": min(10, max_results-first+1)}, headers=HEADERS, timeout=20)
            r.raise_for_status()
            urls.extend(parse_search_results(r.text))
    else:
        raise ValueError("SEARCH_ENGINE deve ser bing ou google_api")
    out, hosts = [], set()
    excluded = {"google.com", "www.google.com", "bing.com", "www.bing.com", "facebook.com", "www.facebook.com", "instagram.com", "www.instagram.com", "linkedin.com", "www.linkedin.com"}
    for raw in urls:
        u = clean_url(raw)
        if not u:
            continue
        host = urlparse(u).hostname
        if host in excluded or host in hosts:
            continue
        hosts.add(host)
        out.append(u)
        if len(out) >= max_results:
            break
    return out
