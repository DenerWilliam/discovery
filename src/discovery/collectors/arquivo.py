"""Coleta pelo arquivo público (Wayback) quando o site recusa o acesso.

Só é acionada quando o site ao vivo está bloqueado. Cada página guarda a data da
captura e a URL do snapshot, para que o dado bruto distinga arquivo de leitura ao
vivo. O índice (CDX) é consultado uma vez por domínio e memorizado no processo.
"""

from __future__ import annotations

import json
import re
import time
from html.parser import HTMLParser
from urllib.parse import urldefrag, urlparse

import httpx

from discovery.collectors.prioridade import pontuar
from discovery.collectors.resiliencia import buscar, motivo_de_excecao
from discovery.models import FALHA, OK, Source, now_iso

CDX_URL = "https://web.archive.org/cdx/search/cdx"
SNAPSHOT_URL = "https://web.archive.org/web/{captura}id_/{url}"
LIMITE_INDICE = 5_000
PAUSA = 1.0
ESPERAS = (5.0, 15.0)
TEMPO_LIMITE = 60.0
FALHAS_SEGUIDAS = 3
_HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) discovery/0.1"}

IGNORAR = frozenset({"script", "style", "noscript", "template"})
EXTENSOES = re.compile(
    r"\.(pdf|jpe?g|png|gif|svg|webp|zip|rar|docx?|xlsx?|pptx?|mp4|mp3|css|js|ico|xml)$", re.I
)

_cache: dict[str, dict[str, str]] = {}


def limpar_cache() -> None:
    _cache.clear()


def _host(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def _unicas(mapa: dict[str, str], dominio: str) -> list[str]:
    """Uma URL por caminho+consulta, preferindo a captura mais recente (https em empate)."""
    vistas: dict[tuple[str, str], str] = {}
    for url in mapa:
        if _host(url) != dominio or EXTENSOES.search(urlparse(url).path):
            continue
        partes = urlparse(url)
        chave = (partes.path or "/", partes.query)
        atual = vistas.get(chave)
        candidata = (mapa[url], partes.scheme == "https")
        if atual is None or candidata > (mapa[atual], urlparse(atual).scheme == "https"):
            vistas[chave] = url
    return list(vistas.values())


def _normalizar(url: str) -> str:
    url, _ = urldefrag(url)
    return url.rstrip("/") if urlparse(url).path not in ("", "/") else url.rstrip("/") + "/"


def capturas(
    dominio: str,
    client: httpx.Client | None = None,
    *,
    dormir=time.sleep,
) -> dict[str, str]:
    """Mapa URL original -> captura mais recente, a partir do índice público."""
    if dominio in _cache:
        return _cache[dominio]
    proprio = client is None
    client = client or httpx.Client(headers=_HEADERS, follow_redirects=True, timeout=TEMPO_LIMITE)
    parametros = [
        ("url", dominio),
        ("matchType", "domain"),
        ("output", "json"),
        ("fl", "timestamp,original,statuscode"),
        ("filter", "statuscode:200"),
        ("filter", "mimetype:text/html"),
        ("limit", str(LIMITE_INDICE)),
    ]
    try:
        resposta, falha = buscar(
            client, f"{CDX_URL}?{httpx.QueryParams(parametros)}",
            esperas=ESPERAS, dormir=dormir,
        )
        if falha is not None or resposta is None or resposta.status_code != 200:
            return {}
        linhas = json.loads(resposta.text)
    except (httpx.HTTPError, ValueError):
        return {}
    finally:
        if proprio:
            client.close()

    resultado: dict[str, str] = {}
    for linha in linhas:
        if not isinstance(linha, list) or len(linha) < 3 or linha[0] == "timestamp":
            continue
        captura, original, status = linha[0], linha[1], linha[2]
        if not all(isinstance(valor, str) for valor in (captura, original, status)):
            continue
        if status != "200":
            continue
        if urlparse(original).scheme not in ("http", "https"):
            continue
        atual = resultado.get(original)
        if atual is None or captura > atual:
            resultado[original] = captura
    _cache[dominio] = resultado
    return resultado


class _Extrator(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._pular = 0
        self._no_titulo = False
        self.titulo: list[str] = []
        self.partes: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in IGNORAR:
            self._pular += 1
        elif tag == "title":
            self._no_titulo = True

    def handle_endtag(self, tag: str) -> None:
        if tag in IGNORAR and self._pular:
            self._pular -= 1
        elif tag == "title":
            self._no_titulo = False

    def handle_data(self, data: str) -> None:
        if self._pular:
            return
        if self._no_titulo:
            self.titulo.append(data)
            return
        linha = " ".join(data.split())
        if linha:
            self.partes.append(linha)


def extrair(html: str) -> tuple[str, str]:
    """Título e texto visível do HTML, sem depender de navegador."""
    extrator = _Extrator()
    extrator.feed(html)
    extrator.close()
    titulo = " ".join(" ".join(extrator.titulo).split())
    linhas: list[str] = []
    anterior = None
    for linha in extrator.partes:
        if linha != anterior:
            linhas.append(linha)
        anterior = linha
    return titulo, "\n".join(linhas)


def _cliente(client: httpx.Client | None) -> tuple[httpx.Client, bool]:
    if client is not None:
        return client, False
    return httpx.Client(headers=_HEADERS, follow_redirects=True, timeout=TEMPO_LIMITE), True


def _snapshot(
    url: str, captura: str, client: httpx.Client, *, dormir=time.sleep
) -> tuple[str | None, str | None]:
    destino = SNAPSHOT_URL.format(captura=captura, url=url)
    resposta, falha = buscar(client, destino, esperas=ESPERAS, dormir=dormir)
    if falha is not None or resposta is None or resposta.status_code != 200:
        return None, falha
    return resposta.text, None


def _fonte(url: str, captura: str, html: str) -> Source:
    titulo, texto = extrair(html)
    return Source("site", url, OK, coletado_em=now_iso(), conteudo={
        "titulo": titulo,
        "texto": texto,
        "origem": "arquivo",
        "captura": captura,
        "url_snapshot": SNAPSHOT_URL.format(captura=captura, url=url),
    })


def coletar(
    dominio: str,
    max_pages: int,
    *,
    client: httpx.Client | None = None,
    pausa: float = PAUSA,
    dormir=time.sleep,
) -> list[Source]:
    """Páginas do domínio, da captura mais recente de cada URL, até o limite."""
    client, proprio = _cliente(client)
    try:
        mapa = capturas(dominio, client, dormir=dormir)
        candidatas = _unicas(mapa, dominio)
        candidatas.sort(key=lambda u: (urlparse(u).path not in ("", "/"),
                                       bool(urlparse(u).query), -pontuar(u, ""), len(u)))
        fontes: list[Source] = []
        seguidas = 0
        falha: BaseException | None = None
        for url in candidatas[:max_pages]:
            html, falha = _snapshot(url, mapa[url], client, dormir=dormir)
            if html is None:
                seguidas += 1
                if seguidas >= FALHAS_SEGUIDAS:
                    break
                continue
            seguidas = 0
            fontes.append(_fonte(url, mapa[url], html))
            if pausa:
                dormir(pausa)
        if not fontes and candidatas:
            fontes.append(Source("site", candidatas[0], FALHA,
                                 erro="arquivo público sem resposta",
                                 motivo=motivo_de_excecao(falha) if falha else None))
        return fontes
    finally:
        if proprio:
            client.close()


def home(
    dominio: str, *, client: httpx.Client | None = None, dormir=time.sleep
) -> tuple[str, str] | None:
    """Captura e HTML da página inicial arquivada, para a detecção de tecnologias."""
    client, proprio = _cliente(client)
    try:
        mapa = capturas(dominio, client, dormir=dormir)
        urls = _unicas(mapa, dominio)
        if not urls:
            return None
        # Home de verdade primeiro: sem query (links de campanha poluem), https e caminho raiz.
        urls.sort(key=lambda u: (bool(urlparse(u).query), urlparse(u).scheme != "https",
                                 urlparse(u).path not in ("", "/"), -pontuar(u, ""), len(u)))
        for url in urls[:3]:
            html, _ = _snapshot(url, mapa[url], client, dormir=dormir)
            if html is not None:
                return mapa[url], html
        return None
    finally:
        if proprio:
            client.close()
