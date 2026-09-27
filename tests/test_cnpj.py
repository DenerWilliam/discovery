import httpx

from discovery.collectors.cnpj import collect_cnpj, find_cnpjs, is_valid_cnpj
from discovery.models import AMBIGUA, FALHA, NAO_COLETADA, OK, Source

VALID_A = "11.222.333/0001-81"
VALID_B = "11.444.777/0001-61"


def site(text, origem="https://x.com/"):
    return Source("site", origem, OK, conteudo={"titulo": "t", "texto": text})


def client(status=200, payload=None):
    calls = []

    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(status, json=payload or {"razao_social": "ACME LTDA"})

    return httpx.Client(transport=httpx.MockTransport(handler)), calls


def test_validation():
    assert is_valid_cnpj(VALID_A)
    assert is_valid_cnpj("11222333000181")  # sem formatação
    assert not is_valid_cnpj("11.222.333/0001-82")  # dígito errado
    assert not is_valid_cnpj("00000000000000")
    assert not is_valid_cnpj("123")


def test_find_in_text_ignores_invalid():
    found = find_cnpjs([site(f"CNPJ {VALID_A}. Outro 11.222.333/0001-82"), site(VALID_A, "https://x.com/b")])
    assert list(found) == ["11222333000181"]
    assert found["11222333000181"]["ocorrencias"] == 2
    assert len(found["11222333000181"]["paginas"]) == 2


def test_informed_cnpj_skips_site_search():
    http, calls = client()
    src = collect_cnpj(VALID_B, [site(VALID_A)], http)
    assert src.status == OK
    assert calls == ["https://brasilapi.com.br/api/cnpj/v1/11444777000161"]
    assert src.conteudo["dados"]["razao_social"] == "ACME LTDA"


def test_cnpj_found_on_site_is_used_and_records_origin():
    http, _ = client()
    src = collect_cnpj(None, [site(f"CNPJ: {VALID_A}", "https://x.com/privacidade")], http)
    assert src.status == OK
    assert src.conteudo["paginas"] == ["https://x.com/privacidade"]


def test_multiple_cnpjs_are_ambiguous_and_not_queried():
    http, calls = client()
    src = collect_cnpj(None, [site(f"{VALID_A} e {VALID_B}")], http)
    assert src.status == AMBIGUA
    assert set(src.conteudo["candidatos"]) == {"11222333000181", "11444777000161"}
    assert calls == []


def test_informed_resolves_ambiguity():
    http, calls = client()
    src = collect_cnpj(VALID_A, [site(f"{VALID_A} e {VALID_B}")], http)
    assert src.status == OK and len(calls) == 1


def test_no_cnpj_is_not_collected():
    http, calls = client()
    src = collect_cnpj(None, [site("sem número")], http)
    assert src.status == NAO_COLETADA and calls == []


def test_api_error_is_failure():
    http, _ = client(status=500, payload={"message": "erro"})
    assert collect_cnpj(VALID_A, [], http).status == FALHA


def test_api_network_error_is_failure():
    def boom(request):
        raise httpx.ConnectError("sem rede")

    http = httpx.Client(transport=httpx.MockTransport(boom))
    src = collect_cnpj(VALID_A, [], http)
    assert src.status == FALHA and "sem rede" in src.erro


def test_invalid_informed_cnpj_is_failure():
    http, calls = client()
    assert collect_cnpj("123", [], http).status == FALHA and calls == []
