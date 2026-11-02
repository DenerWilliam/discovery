"""Política de tentativas para falhas transitórias de acesso.

Erros que não mudam de resultado (403, 404) não são repetidos; 429, 502, 503,
504, tempo esgotado e erro de conexão são. A classificação do motivo fica aqui
para que todos os coletores gravem o mesmo vocabulário no dado bruto.
"""

from __future__ import annotations

import time
from typing import Callable, TypeVar

import httpx
from playwright.sync_api import Error as PlaywrightError

from discovery.models import FALHOU, RECUSADO, SEM_RESPOSTA

TENTATIVAS = 3
ESPERAS = (1.0, 3.0)
TRANSITORIOS = frozenset({429, 502, 503, 504})

T = TypeVar("T")


class FalhaTemporaria(Exception):
    """Resposta HTTP que representa falha de acesso, com o código preservado."""

    def __init__(self, status: int) -> None:
        super().__init__(f"HTTP {status}")
        self.status = status


def transitorio(status: int) -> bool:
    return status in TRANSITORIOS


def motivo_de_status(status: int) -> str | None:
    """Motivo classificado de uma resposta HTTP, ou None quando não é falha de acesso."""
    if status in (403, 429):
        return RECUSADO
    if 500 <= status <= 599:
        return FALHOU
    return None


def motivo_de_excecao(exc: BaseException) -> str:
    if isinstance(exc, FalhaTemporaria):
        return motivo_de_status(exc.status) or FALHOU
    return SEM_RESPOSTA


def erro_transitorio(exc: BaseException) -> bool:
    return isinstance(exc, (httpx.HTTPError, PlaywrightError, TimeoutError, ConnectionError))


def tentar(
    chamada: Callable[[], T],
    *,
    repetir: Callable[[BaseException], bool] = erro_transitorio,
    tentativas: int = TENTATIVAS,
    esperas: tuple[float, ...] | None = None,
    dormir: Callable[[float], None] = time.sleep,
) -> tuple[T | None, BaseException | None]:
    """Executa ``chamada`` e repete só falhas transitórias; devolve (valor, falha)."""
    esperas = ESPERAS if esperas is None else esperas
    falha: BaseException | None = None
    for indice in range(tentativas):
        try:
            return chamada(), None
        except FalhaTemporaria as exc:
            falha = exc
            if not transitorio(exc.status):
                return None, exc
        except Exception as exc:  # noqa: BLE001 - quem decide é o predicado do chamador
            falha = exc
            if not repetir(exc):
                return None, exc
        if indice < len(esperas):
            dormir(esperas[indice])
    return None, falha


def buscar(
    client: httpx.Client,
    url: str,
    *,
    esperas: tuple[float, ...] | None = None,
    dormir: Callable[[float], None] = time.sleep,
) -> tuple[httpx.Response | None, BaseException | None]:
    """GET com tentativas: status transitório vira repetição, o resto volta como resposta."""

    def chamada() -> httpx.Response:
        resposta = client.get(url)
        if transitorio(resposta.status_code):
            raise FalhaTemporaria(resposta.status_code)
        return resposta

    return tentar(chamada, esperas=esperas, dormir=dormir)
