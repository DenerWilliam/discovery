import httpx

from discovery.collectors.cnpj import is_valid_cnpj
from discovery.collectors.filiais import build_cnpj, check_digits, collect_filiais
from discovery.models import AMBIGUA, FALHA, NAO_COLETADA, OK, Source

ROOT = "11222333"
MATRIZ = build_cnpj(ROOT, 1)


def cnpj_source(status=OK, cnpj=MATRIZ, dados=None):
    dados = dados or {"identificador_matriz_filial": 1, "municipio": "UBERLANDIA", "uf": "MG",
                      "cnae_fiscal": 4530701, "descricao_situacao_cadastral": "ATIVA"}
    conteudo = {"cnpj": cnpj, "dados": dados} if status == OK else None
    return Source("cnpj", "https://x", status, conteudo=conteudo)


def client(existing: dict, status_for_others=404, log=None):
    def handler(request):
        cnpj = request.url.path.rsplit("/", 1)[-1]
        if log is not None:
            log.append(cnpj)
        if cnpj in existing:
            return httpx.Response(200, json=existing[cnpj])
        return httpx.Response(status_for_others)

    return httpx.Client(transport=httpx.MockTransport(handler))


def branch(city, uf="MG"):
    return {"identificador_matriz_filial": 2, "municipio": city, "uf": uf, "cnae_fiscal": 4530701,
            "cnae_fiscal_descricao": "Comércio", "descricao_situacao_cadastral": "ATIVA",
            "data_inicio_atividade": "2015-01-01", "nome_fantasia": "ACME"}


def test_check_digits_generate_valid_cnpjs():
    assert MATRIZ == "11222333000181"  # CNPJ de exemplo válido
    assert check_digits("112223330001") == "81"
    assert all(is_valid_cnpj(build_cnpj(ROOT, n)) for n in range(1, 30))


def test_lists_branches_and_stops_after_three_missing():
    log = []
    existing = {build_cnpj(ROOT, 2): branch("BELO HORIZONTE"), build_cnpj(ROOT, 3): branch("GOIANIA", "GO")}
    src = collect_filiais(cnpj_source(), client(existing, log=log), pause=0)
    assert src.status == OK
    estabs = src.conteudo["estabelecimentos"]
    assert [(e["municipio"], e["uf"]) for e in estabs] == [("UBERLANDIA", "MG"), ("BELO HORIZONTE", "MG"), ("GOIANIA", "GO")]
    assert estabs[0]["tipo"] == "matriz" and estabs[1]["tipo"] == "filial"
    assert log == [build_cnpj(ROOT, n) for n in (2, 3, 4, 5, 6)]  # 0001 já é conhecido; para após 3 inexistentes (4,5,6)


def test_no_other_establishments_lists_only_known():
    log = []
    src = collect_filiais(cnpj_source(), client({}, log=log), pause=0)
    assert src.status == OK and len(src.conteudo["estabelecimentos"]) == 1
    assert len(log) == 3


def test_informed_cnpj_can_be_a_branch():
    filial = build_cnpj(ROOT, 2)
    existing = {MATRIZ: {**branch("UBERLANDIA"), "identificador_matriz_filial": 1}}
    src = collect_filiais(cnpj_source(cnpj=filial, dados=branch("BELO HORIZONTE")), client(existing), pause=0)
    assert {e["cnpj"] for e in src.conteudo["estabelecimentos"]} == {MATRIZ, filial}


def test_rate_limit_keeps_partial_results():
    existing = {build_cnpj(ROOT, 2): branch("BELO HORIZONTE")}

    def handler(request):
        cnpj = request.url.path.rsplit("/", 1)[-1]
        if cnpj in existing:
            return httpx.Response(200, json=existing[cnpj])
        return httpx.Response(429)

    src = collect_filiais(cnpj_source(), httpx.Client(transport=httpx.MockTransport(handler)), pause=0)
    assert src.status == FALHA and "429" in src.erro
    assert len(src.conteudo["estabelecimentos"]) == 2  # a matriz e a filial já obtida


def test_network_error_is_partial_failure():
    def boom(request):
        raise httpx.ConnectError("sem rede")

    src = collect_filiais(cnpj_source(), httpx.Client(transport=httpx.MockTransport(boom)), pause=0)
    assert src.status == FALHA and len(src.conteudo["estabelecimentos"]) == 1


def test_unresolved_cnpj_is_not_collected_without_calling_the_api():
    log = []
    for status in (NAO_COLETADA, AMBIGUA, FALHA):
        src = collect_filiais(cnpj_source(status=status), client({}, log=log), pause=0)
        assert src.status == NAO_COLETADA and status in src.erro
    assert log == []


def test_summary_keeps_full_registration_data():
    dados = {**branch("BELO HORIZONTE"), "razao_social": "ACME LTDA", "logradouro": "RUA A",
             "numero": "10", "cep": "30110000", "ddd_telefone_1": "3133334444",
             "email": "a@acme.com.br", "capital_social": 1000.0,
             "cnaes_secundarios": [{"codigo": 4321500, "descricao": "Instalação elétrica"}]}
    existing = {build_cnpj(ROOT, 2): dados}
    src = collect_filiais(cnpj_source(), client(existing), pause=0)
    cadastro = src.conteudo["estabelecimentos"][1]["cadastro"]
    assert cadastro["razao_social"] == "ACME LTDA" and cadastro["cep"] == "30110000"
    assert cadastro["cnaes_secundarios"][0]["codigo"] == 4321500
    assert cadastro["complemento"] is None
