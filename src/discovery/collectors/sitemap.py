"""Estimativa do tamanho do site pelo sitemap (sem visitar as páginas listadas)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import Counter
from urllib.parse import urlparse

import httpx

from discovery.models import FALHA, NAO_COLETADA, OK, Source

MAX_SITEMAPS = 20
MAX_URLS = 50_000
SAMPLE_SIZE = 20
_HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) discovery/0.1"}


def _tag(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _locs(root: ET.Element, parent: str) -> list[str]:
    return [
        (child.text or "").strip()
        for item in root if _tag(item) == parent
        for child in item if _tag(child) == "loc" and (child.text or "").strip()
    ]


def _sitemaps_from_robots(text: str) -> list[str]:
    return [line.split(":", 1)[1].strip() for line in text.splitlines()
            if line.lower().startswith("sitemap:")]


def _breakdown(urls: list[str]) -> tuple[dict, dict]:
    """Distribuição por primeiro segmento do caminho e por sufixo curto (ex.: ``/p`` e ``/c``)."""
    sections: Counter = Counter()
    suffixes: Counter = Counter()
    for url in urls:
        parts = [p for p in urlparse(url).path.split("/") if p]
        sections[("/" + parts[0]) if len(parts) > 1 else "/"] += 1
        if parts and len(parts[-1]) <= 2:
            suffixes["*/" + parts[-1]] += 1
    return dict(sections.most_common(15)), dict(suffixes.most_common(10))


def collect_sitemap(site: str, client: httpx.Client | None = None) -> Source:
    parsed = urlparse(site)
    base = f"{parsed.scheme}://{parsed.netloc}"
    own_client = client is None
    client = client or httpx.Client(headers=_HEADERS, follow_redirects=True, timeout=20)
    try:
        return _collect(base, client)
    finally:
        if own_client:
            client.close()


def _get(client: httpx.Client, url: str) -> httpx.Response | None:
    try:
        return client.get(url)
    except httpx.HTTPError:
        return None


def _collect(base: str, client: httpx.Client) -> Source:
    robots = _get(client, base + "/robots.txt")
    queue = _sitemaps_from_robots(robots.text) if robots is not None and robots.status_code == 200 else []
    queue = queue or [base + "/sitemap.xml"]

    urls: list[str] = []
    fetched: list[str] = []
    found_any = False
    while queue and len(fetched) < MAX_SITEMAPS and len(urls) < MAX_URLS:
        current = queue.pop(0)
        response = _get(client, current)
        if response is None or response.status_code != 200:
            continue
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as exc:
            return Source("sitemap", current, FALHA, erro=f"XML inválido: {exc}")
        found_any = True
        fetched.append(current)
        if _tag(root) == "sitemapindex":
            queue += _locs(root, "sitemap")
        else:
            urls += _locs(root, "url")

    if not found_any:
        return Source("sitemap", base, NAO_COLETADA,
                      erro="Nenhum sitemap encontrado em robots.txt nem em /sitemap.xml.")
    urls = urls[:MAX_URLS]
    sections, suffixes = _breakdown(urls)
    return Source("sitemap", fetched[0], OK, conteudo={
        "sitemaps_lidos": fetched,
        "total_urls": len(urls),
        "por_secao": sections,
        "por_sufixo": suffixes,
        "amostra": urls[:SAMPLE_SIZE],
    })
