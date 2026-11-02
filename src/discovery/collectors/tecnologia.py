"""Detecção de tecnologias do site a partir da página inicial (HTML, cabeçalhos, cookies, domínios)."""

from __future__ import annotations

from urllib.parse import urlparse

from playwright.sync_api import BrowserContext, Error as PlaywrightError

from discovery.collectors import arquivo
from discovery.collectors.resiliencia import (
    FalhaTemporaria,
    motivo_de_excecao,
    tentar,
)
from discovery.collectors.signatures import SIGNATURES
from discovery.models import FALHA, OK, RECUSADO, Source

PAGE_TIMEOUT_MS = 20_000
MAX_REQUESTS = 500


def detect(html: str, request_urls: list[str], cookies: list[str], headers: dict[str, str],
           signatures: list[dict] = SIGNATURES) -> list[dict]:
    """Casa as assinaturas; cada detecção guarda nome, categoria e as evidências."""
    html_l = html.lower()
    urls_l = [u.lower() for u in request_urls]
    cookies_l = [c.lower() for c in cookies]
    headers_l = {k.lower(): v.lower() for k, v in headers.items()}
    found = []
    for sig in signatures:
        evidence: list[str] = []
        for needle in sig.get("html", []):
            if needle and needle in html_l:
                evidence.append(f"html: {needle}")
        for needle in sig.get("urls", []):
            hit = next((u for u in urls_l if needle in u), None)
            if hit:
                evidence.append(f"url: {needle}")
        for prefix in sig.get("cookies", []):
            hit = next((c for c in cookies_l if c.startswith(prefix)), None)
            if hit:
                evidence.append(f"cookie: {hit}")
        for header, needle in sig.get("headers", {}).items():
            if header in headers_l and needle in headers_l[header]:
                evidence.append(f"cabeçalho: {header}" + (f"={needle}" if needle else ""))
        if evidence:
            found.append({"nome": sig["nome"], "categoria": sig["categoria"], "evidencia": evidence})
    return found


def _capturar(context: BrowserContext, site: str,
              requested: list[str]) -> tuple[dict[str, str], str]:
    # Uma página por tentativa: reutilizar a página depois de uma navegação que
    # falhou trava o fechamento no Playwright síncrono.
    page = context.new_page()
    page.set_default_timeout(PAGE_TIMEOUT_MS)
    page.on("request", lambda request: requested.append(request.url) if len(requested) < MAX_REQUESTS else None)
    navegou = False
    try:
        # "load" pode nunca disparar em sites com muitos recursos externos; o DOM mais
        # uma janela curta de rede ociosa bastam para ver scripts, cookies e cabeçalhos.
        response = page.goto(site, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=6_000)
        except PlaywrightError:
            pass
        if response is None:
            raise PlaywrightError("sem resposta")
        if response.status >= 400:
            raise FalhaTemporaria(response.status)
        navegou = True
        return response.all_headers(), page.content()
    finally:
        if navegou:
            page.close()


def collect_tecnologia(context: BrowserContext, site: str) -> Source:
    host = (urlparse(site).hostname or "").lower().removeprefix("www.")
    requested: list[str] = []
    captura, falha = tentar(lambda: _capturar(context, site, requested))
    if falha is not None:
        motivo = motivo_de_excecao(falha)
        if motivo == RECUSADO:
            achado = arquivo.home(host)
            if achado is not None:
                data_captura, html_arquivado = achado
                return Source("tecnologia", site, OK, conteudo={
                    "detectadas": detect(html_arquivado, [], [], {}),
                    "dominios_contatados": [],
                    "origem": "arquivo",
                    "captura": data_captura,
                })
        return Source("tecnologia", site, FALHA,
                      erro=str(falha).splitlines()[0], motivo=motivo)
    headers, html = captura
    cookies = [c["name"] for c in context.cookies()
               if c["domain"].lstrip(".").removeprefix("www.").endswith(host) or host.endswith(c["domain"].lstrip("."))]

    domains = sorted({urlparse(u).netloc for u in requested if urlparse(u).scheme in ("http", "https")})
    return Source("tecnologia", site, OK, conteudo={
        "detectadas": detect(html, requested, cookies, headers),
        "dominios_contatados": domains[:100],
    })
