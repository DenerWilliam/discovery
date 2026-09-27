"""Buscas complementares sem chave: Bing, depois DuckDuckGo (melhor esforço)."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Callable
from urllib.parse import parse_qs, quote_plus, urlparse

from playwright.sync_api import BrowserContext, Error as PlaywrightError

from discovery.models import FALHA, NAO_COLETADA, OK, Source

_BLOCK_MARKERS = ("anomaly-modal", "captcha", "unusual traffic")


def _clean(text: str) -> str:
    return " ".join(text.split())


def _decode_bing_url(href: str) -> str:
    """Links do Bing são redirecionamentos; o destino vem em ``u=a1<base64url>``."""
    if "bing.com/ck/a" not in href:
        return href
    token = parse_qs(urlparse(href).query).get("u", [""])[0]
    if token.startswith("a1"):
        try:
            padded = token[2:] + "=" * (-len(token[2:]) % 4)
            return base64.urlsafe_b64decode(padded).decode()
        except (ValueError, UnicodeDecodeError):
            pass
    return href


def _real_ddg_url(href: str) -> str:
    if "uddg=" in href:
        return parse_qs(urlparse(href).query).get("uddg", [href])[0]
    return "https:" + href if href.startswith("//") else href


class _BingParser(HTMLParser):
    """Resultado = ``li.b_algo``; título e destino vêm do link dentro do ``h2``."""

    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict] = []
        self._in_item = False
        self._in_h2 = False
        self._field: str | None = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = (attrs.get("class") or "").split()
        if tag == "li" and "b_algo" in classes:
            self._in_item = True
            self.results.append({"titulo": "", "url": "", "trecho": ""})
        elif not self._in_item:
            return
        elif tag == "h2":
            self._in_h2 = True
        elif tag == "a" and self._in_h2 and not self.results[-1]["url"]:
            self.results[-1]["url"] = _decode_bing_url(attrs.get("href", ""))
            self._field = "titulo"
        elif tag == "p" and not self._in_h2 and not self.results[-1]["trecho"]:
            self._field = "trecho"

    def handle_endtag(self, tag):
        if tag == "h2":
            self._in_h2 = False
        if tag in ("a", "p"):
            self._field = None

    def handle_data(self, data):
        if self._in_item and self._field and self.results:
            self.results[-1][self._field] += data


class _DdgParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict] = []
        self._field: str | None = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = (attrs.get("class") or "").split()
        if tag == "a" and "result__a" in classes:
            self.results.append({"titulo": "", "url": _real_ddg_url(attrs.get("href", "")), "trecho": ""})
            self._field = "titulo"
        elif "result__snippet" in classes and self.results:
            self._field = "trecho"

    def handle_endtag(self, tag):
        if tag in ("a", "div", "td") and self._field:
            self._field = None

    def handle_data(self, data):
        if self._field and self.results:
            self.results[-1][self._field] += data


def _parse(parser: HTMLParser, html: str) -> list[dict]:
    parser.feed(html)
    return [{k: _clean(v) for k, v in r.items()} for r in parser.results if r["url"]]


def parse_bing(html: str) -> list[dict]:
    return _parse(_BingParser(), html)


def parse_ddg(html: str) -> list[dict]:
    return _parse(_DdgParser(), html)


def looks_blocked(html: str) -> bool:
    lowered = html.lower()
    return any(marker in lowered for marker in _BLOCK_MARKERS)


@dataclass(frozen=True)
class Engine:
    name: str
    url: str  # com {q}
    parse: Callable[[str], list[dict]]
    attempts: int = 1  # buscadores automatizados respondem de forma intermitente


ENGINES = (
    Engine("bing", "https://www.bing.com/search?q={q}&setlang=pt-BR", parse_bing, attempts=2),
    Engine("duckduckgo", "https://html.duckduckgo.com/html/?q={q}", parse_ddg),
)

Fetch = Callable[[str], "tuple[int, str]"]  # url -> (status HTTP, html)


def _mentions(results: list[dict], keyword: str | None) -> bool:
    if not keyword:
        return bool(results)
    keyword = keyword.lower()
    return any(keyword in f"{r['titulo']} {r['url']} {r['trecho']}".lower() for r in results)


def search_query(query: str, fetch: Fetch, engines=ENGINES, keyword: str | None = None) -> Source:
    """Tenta cada buscador em ordem; o primeiro com resultados que citam ``keyword`` vence.

    Sem nenhum resultado relacionado ao cliente (ex.: o buscador devolveu lixo), o
    buscador é descartado e a query só é registrada como coletada se algum
    buscador respondeu sem bloqueio e sem resultados.
    """
    problems: list[str] = []
    answered: str | None = None  # respondeu sem bloqueio, mas sem resultados
    for engine in engines:
        url = engine.url.format(q=quote_plus(query))
        for _ in range(engine.attempts):
            try:
                status, html = fetch(url)
            except PlaywrightError as exc:
                problems.append(f"{engine.name}: {str(exc).splitlines()[0]}")
                continue
            results = engine.parse(html) if status < 400 else []
            if _mentions(results, keyword):
                return Source("busca", url, OK, conteudo={
                    "query": query, "motor": engine.name, "resultados": results})
            if results:
                problems.append(f"{engine.name}: resultados sem relação com o cliente")
            elif status >= 400 or status == 202 or looks_blocked(html):
                problems.append(f"{engine.name}: bloqueado (HTTP {status})")
            else:
                answered = answered or engine.name
    first_url = engines[0].url.format(q=quote_plus(query))
    if answered and not problems:
        return Source("busca", first_url, OK, conteudo={
            "query": query, "motor": answered, "resultados": []})
    return Source("busca", first_url, NAO_COLETADA, erro="; ".join(problems) or "sem resultados",
                  conteudo={"query": query})


def collect_searches(context: BrowserContext, queries: list[str], keyword: str | None = None) -> list[Source]:
    page = context.new_page()
    page.set_default_timeout(20_000)

    def fetch(url: str) -> tuple[int, str]:
        response = page.goto(url, wait_until="load")
        return (response.status if response else 0), page.content()

    try:
        return [search_query(query, fetch, keyword=keyword) for query in queries]
    finally:
        page.close()
