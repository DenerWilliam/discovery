"""Varredura do site oficial, restrita ao mesmo domínio."""

from __future__ import annotations

import re
from urllib.parse import urldefrag, urlparse

from playwright.sync_api import BrowserContext, Error as PlaywrightError

from discovery.models import FALHA, NAO_COLETADA, OK, Source, now_iso

PAGE_TIMEOUT_MS = 20_000

PRIORITY_KEYWORDS = (
    "sobre", "quem-somos", "quem somos", "institucional", "empresa",
    "servico", "serviço", "solucao", "solução", "produto", "locacao", "locação",
    "aluguel", "frota", "equipamento", "contato", "fale-conosco",
    "privacidade", "termo", "politica", "política", "lgpd",
)

SKIP_EXTENSIONS = re.compile(
    r"\.(pdf|jpe?g|png|gif|svg|webp|zip|rar|docx?|xlsx?|pptx?|mp4|mp3|css|js|ico)$", re.I
)
LOGIN_PATH = re.compile(r"/(login|signin|sign-in|entrar|auth)(/|$|\?)", re.I)

_EXTRACT_LINKS = "Array.from(document.querySelectorAll('a[href]')).map(a => [a.href, a.innerText || ''])"


def _host(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def _normalize(url: str) -> str:
    url, _ = urldefrag(url)
    return url.rstrip("/") if urlparse(url).path not in ("", "/") else url.rstrip("/") + "/"


def _score(url: str, anchor: str) -> int:
    text = f"{url} {anchor}".lower()
    return sum(1 for kw in PRIORITY_KEYWORDS if kw in text)


def _clean_text(text: str) -> str:
    lines, previous = [], None
    for line in (l.strip() for l in text.splitlines()):
        if line and line != previous:
            lines.append(line)
        previous = line or previous
    return "\n".join(lines)


def _is_login_redirect(requested: str, final: str) -> bool:
    if LOGIN_PATH.search(urlparse(final).path + "/"):
        return True
    return False


def collect_site(context: BrowserContext, site: str, max_pages: int) -> list[Source]:
    """Visita a home e as páginas internas mais relevantes; devolve uma fonte por página."""
    domain = _host(site)
    start = _normalize(site)
    sources: list[Source] = []
    visited: set[str] = set()
    frontier: dict[str, int] = {start: 100}
    page = context.new_page()
    page.set_default_timeout(PAGE_TIMEOUT_MS)

    try:
        while frontier and len(visited) < max_pages:
            url = max(frontier, key=lambda u: (frontier[u], -len(u)))
            frontier.pop(url)
            if url in visited:
                continue
            visited.add(url)
            is_home = url == start

            try:
                response = page.goto(url, wait_until="load")
                try:
                    page.wait_for_load_state("networkidle", timeout=3_000)
                except PlaywrightError:
                    pass
                final_url = page.url
                if response is not None and response.status >= 400:
                    raise PlaywrightError(f"HTTP {response.status}")
                if _host(final_url) != domain:
                    sources.append(Source("site", url, NAO_COLETADA,
                                          erro=f"redirecionou para outro domínio: {final_url}"))
                    if is_home:
                        break
                    continue
                if _is_login_redirect(url, final_url):
                    sources.append(Source("site", url, NAO_COLETADA,
                                          erro=f"redirecionou para login: {final_url}"))
                    continue
                title = page.title()
                text = _clean_text(page.inner_text("body"))
                links = page.evaluate(_EXTRACT_LINKS)
            except PlaywrightError as exc:
                sources.append(Source("site", url, FALHA, erro=str(exc).splitlines()[0]))
                if is_home:
                    break
                continue

            sources.append(Source(
                "site", final_url, OK, coletado_em=now_iso(),
                conteudo={"titulo": title, "texto": text},
            ))
            visited.add(_normalize(final_url))

            for href, anchor in links:
                parsed = urlparse(href)
                if parsed.scheme not in ("http", "https") or _host(href) != domain:
                    continue
                if SKIP_EXTENSIONS.search(parsed.path) or LOGIN_PATH.search(parsed.path + "/"):
                    continue
                link = _normalize(href)
                if link in visited:
                    continue
                frontier[link] = max(frontier.get(link, 0), _score(link, anchor))
    finally:
        page.close()
    return sources
