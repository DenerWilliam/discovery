import httpx
import pytest

from discovery.collectors.resiliencia import (
    FalhaTemporaria,
    buscar,
    motivo_de_excecao,
    motivo_de_status,
    tentar,
)
from discovery.models import FALHOU, RECUSADO, SEM_RESPOSTA


def falhar(status):
    chamadas = []

    def chamada():
        chamadas.append(status)
        raise FalhaTemporaria(status)

    return chamada, chamadas


@pytest.mark.parametrize("status", [403, 404])
def test_status_terminal_nao_repete(status):
    chamada, chamadas = falhar(status)
    valor, falha = tentar(chamada, dormir=lambda _: None)
    assert valor is None and isinstance(falha, FalhaTemporaria)
    assert chamadas == [status]


def test_429_repetido_vira_sucesso():
    respostas = iter([429, 429, 200])
    esperas = []

    def chamada():
        status = next(respostas)
        if status != 200:
            raise FalhaTemporaria(status)
        return "ok"

    valor, falha = tentar(chamada, esperas=(1.0, 3.0), dormir=esperas.append)
    assert (valor, falha) == ("ok", None)
    assert esperas == [1.0, 3.0]


def test_503_esgota_as_tentativas_e_devolve_ultima_falha():
    chamada, chamadas = falhar(503)
    valor, falha = tentar(chamada, dormir=lambda _: None)
    assert valor is None and falha.status == 503 and len(chamadas) == 3


def test_erro_nao_repetivel_encerra_na_primeira():
    chamadas = []

    def chamada():
        chamadas.append(1)
        raise RuntimeError("quebrou")

    valor, falha = tentar(chamada, repetir=lambda _: False, dormir=lambda _: None)
    assert valor is None and isinstance(falha, RuntimeError)
    assert chamadas == [1]


def test_buscar_repete_status_transitorio():
    vistos = []

    def handler(request):
        vistos.append(1)
        return httpx.Response(200, text="ok") if len(vistos) == 3 else httpx.Response(503)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    resposta, falha = buscar(client, "https://exemplo.com/sitemap.xml", dormir=lambda _: None)
    assert falha is None and resposta.status_code == 200 and len(vistos) == 3


def test_motivo_de_status():
    assert motivo_de_status(403) == RECUSADO
    assert motivo_de_status(429) == RECUSADO
    assert motivo_de_status(502) == FALHOU
    assert motivo_de_status(404) is None
    assert motivo_de_status(200) is None


def test_motivo_de_excecao():
    assert motivo_de_excecao(FalhaTemporaria(429)) == RECUSADO
    assert motivo_de_excecao(FalhaTemporaria(500)) == FALHOU
    assert motivo_de_excecao(TimeoutError()) == SEM_RESPOSTA
    assert motivo_de_excecao(httpx.ConnectError("sem rede")) == SEM_RESPOSTA
