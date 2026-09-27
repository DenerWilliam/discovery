"""Notícias pelo feed RSS do Google News (sem navegador, sem chave)."""

from __future__ import annotations

import unicodedata
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

import httpx

from discovery.models import FALHA, OK, Source

FEED_URL = "https://news.google.com/rss/search?q={q}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
_HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) discovery/0.1"}


def _norm(text: str) -> str:
    """Minúsculas e sem acentos, para comparar nomes."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


def parse_feed(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    items = []
    for item in root.iter("item"):
        source = item.find("source")
        items.append({
            "titulo": (item.findtext("title") or "").strip(),
            "url": (item.findtext("link") or "").strip(),
            "data": (item.findtext("pubDate") or "").strip(),
            "veiculo": (source.text or "").strip() if source is not None else "",
        })
    return items


def collect_news(name: str, client: httpx.Client | None = None) -> Source:
    query = f'"{name}"'
    url = FEED_URL.format(q=quote_plus(query))
    own_client = client is None
    client = client or httpx.Client(headers=_HEADERS, follow_redirects=True)
    try:
        response = client.get(url, timeout=20)
        if response.status_code != 200:
            return Source("noticias", url, FALHA, erro=f"HTTP {response.status_code}",
                          conteudo={"query": query, "motor": "google-news"})
        items = parse_feed(response.text)
        wanted = _norm(name)
        relevant = [i for i in items if wanted in _norm(i["titulo"])]
        return Source("noticias", url, OK, conteudo={
            "query": query, "motor": "google-news", "itens": relevant,
            "descartados": len(items) - len(relevant)})
    except (httpx.HTTPError, ET.ParseError) as exc:
        return Source("noticias", url, FALHA, erro=f"{type(exc).__name__}: {exc}",
                      conteudo={"query": query, "motor": "google-news"})
    finally:
        if own_client:
            client.close()
