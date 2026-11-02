"""Notícias pelo feed RSS do Google News (sem navegador, sem chave)."""

from __future__ import annotations

import unicodedata
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

import httpx

from discovery.collectors.resiliencia import buscar, motivo_de_excecao, motivo_de_status
from discovery.config import DEFAULT_LOCALE
from discovery.models import FALHA, OK, Source

FEED_URL = "https://news.google.com/rss/search?q={q}&hl={locale}&gl={gl}&ceid={ceid}"
# Google News usa o código de país na edição e um idioma de interface; pt-BR tem
# edição própria (419), por isso não sai da derivação genérica.
EDICOES = {
    "pt-BR": ("pt-BR", "BR", "BR:pt-419"),
    "en-US": ("en-US", "US", "US:en"),
}
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


def feed_url(query: str, locale: str = DEFAULT_LOCALE) -> str:
    """URL do feed no idioma pedido; ``ceid`` é ``PAÍS:idioma``."""
    hl, gl, ceid = EDICOES.get(locale) or _edicao_generica(locale)
    return FEED_URL.format(q=quote_plus(query), locale=hl, gl=gl, ceid=ceid)


def _edicao_generica(locale: str) -> tuple[str, str, str]:
    idioma, _, pais = locale.partition("-")
    pais = pais or idioma.upper()
    return locale, pais, f"{pais}:{idioma}"


def collect_news(name: str, client: httpx.Client | None = None,
                 locale: str = DEFAULT_LOCALE) -> Source:
    query = f'"{name}"'
    url = feed_url(query, locale)
    conteudo = {"query": query, "motor": "google-news", "locale": locale}
    own_client = client is None
    client = client or httpx.Client(headers=_HEADERS, follow_redirects=True)
    try:
        response, falha = buscar(client, url)
        if response is None:
            return Source("noticias", url, FALHA,
                          erro=str(falha).splitlines()[0] if falha else "sem resposta",
                          motivo=motivo_de_excecao(falha) if falha else None,
                          conteudo=conteudo)
        if response.status_code != 200:
            return Source("noticias", url, FALHA, erro=f"HTTP {response.status_code}",
                          motivo=motivo_de_status(response.status_code), conteudo=conteudo)
        items = parse_feed(response.text)
        wanted = _norm(name)
        relevant = [i for i in items if wanted in _norm(i["titulo"])]
        return Source("noticias", url, OK, conteudo={
            **conteudo, "itens": relevant, "descartados": len(items) - len(relevant)})
    except ET.ParseError as exc:
        return Source("noticias", url, FALHA, erro=f"{type(exc).__name__}: {exc}",
                      conteudo=conteudo)
    finally:
        if own_client:
            client.close()
