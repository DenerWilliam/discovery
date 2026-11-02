"""Varredura do site oficial, restrita ao mesmo domínio."""

from __future__ import annotations

import re
from urllib.parse import urldefrag, urlparse

from playwright.sync_api import BrowserContext, Error as PlaywrightError

from discovery.collectors import arquivo
from discovery.collectors.prioridade import pontuar
from discovery.collectors.resiliencia import (
    FalhaTemporaria,
    erro_transitorio,
    motivo_de_excecao,
    tentar,
)
from discovery.models import FALHA, NAO_COLETADA, OK, RECUSADO, Source, now_iso

PAGE_TIMEOUT_MS = 20_000
MAX_DOWNLOADS = 50  # teto de arquivos para download registrados por execução
MOTIVO_DOWNLOAD = "arquivo para download"

SKIP_EXTENSIONS = re.compile(
    r"\.(pdf|jpe?g|png|gif|svg|webp|zip|rar|docx?|xlsx?|pptx?|mp4|mp3|css|js|ico)$", re.I
)
LOGIN_PATH = re.compile(r"/(login|signin|sign-in|entrar|auth)(/|$|\?)", re.I)

_EXTRACT_LINKS = "Array.from(document.querySelectorAll('a[href]')).map(a => [a.href, a.innerText || ''])"


def _host(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def _normalize(url: str) -> str:
    url, _ = urldefrag(url)
    return url.rstrip("/") if urlparse(url).path not in ("", "/") else url.rstrip("/") + "/"


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


def _is_download_error(exc: BaseException) -> bool:
    return "Download is starting" in str(exc)


def _repetivel(exc: BaseException) -> bool:
    """Download é intencional na varredura: não deve ser repetido."""
    return not _is_download_error(exc) and erro_transitorio(exc)


def _visitar(page, url: str) -> None:
    response = page.goto(url, wait_until="load")
    try:
        page.wait_for_load_state("networkidle", timeout=3_000)
    except PlaywrightError:
        pass
    if response is not None and response.status >= 400:
        raise FalhaTemporaria(response.status)


def _explorar(context: BrowserContext, site: str, max_pages: int) -> list[Source]:
    domain = _host(site)
    start = _normalize(site)
    sources: list[Source] = []
    visited: set[str] = set()
    frontier: dict[str, int] = {start: 100}
    attempts = 0  # só páginas HTML contam para max_pages; downloads não
    downloads = 0
    falhou_navegacao = False  # fechar uma página assim trava o Playwright síncrono
    page = context.new_page()
    page.set_default_timeout(PAGE_TIMEOUT_MS)
    page.on("download", lambda download: download.cancel())

    try:
        while frontier and attempts < max_pages:
            url = max(frontier, key=lambda u: (frontier[u], -len(u)))
            frontier.pop(url)
            if url in visited:
                continue
            visited.add(url)
            is_home = url == start
            attempts += 1

            _, falha = tentar(lambda u=url: _visitar(page, u), repetir=_repetivel)
            if falha is not None:
                if _is_download_error(falha):
                    attempts -= 1
                    if downloads < MAX_DOWNLOADS:
                        downloads += 1
                        sources.append(Source("site", url, NAO_COLETADA, erro=MOTIVO_DOWNLOAD))
                    if is_home:
                        break
                    continue
                falhou_navegacao = falhou_navegacao or not _is_download_error(falha)
                sources.append(Source(
                    "site", url, FALHA,
                    erro=str(falha).splitlines()[0],
                    motivo=motivo_de_excecao(falha),
                ))
                if is_home:
                    break
                continue

            final_url = page.url
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
            try:
                title = page.title()
                text = _clean_text(page.inner_text("body"))
                links = page.evaluate(_EXTRACT_LINKS)
            except PlaywrightError as exc:
                sources.append(Source("site", url, FALHA,
                                      erro=str(exc).splitlines()[0],
                                      motivo=motivo_de_excecao(exc)))
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
                frontier[link] = max(frontier.get(link, 0), pontuar(link, anchor))
    finally:
        if not falhou_navegacao:
            page.close()
    return sources


def collect_site(context: BrowserContext, site: str, max_pages: int) -> list[Source]:
    """Visita a home e as páginas internas mais relevantes; devolve uma fonte por página.

    Se a home for recusada de forma persistente (403/429), tenta o arquivo público
    antes de encerrar a fonte. Conteúdo arquivado carrega a data da captura.
    """
    sources = _explorar(context, site, max_pages)
    if not sources:
        return sources
    home = sources[0]
    if home.status == FALHA and home.motivo == RECUSADO:
        archived = arquivo.coletar(_host(site), max_pages)
        if any(source.status == OK for source in archived):
            return archived
    return sources
