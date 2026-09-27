import json
from datetime import datetime

from discovery.models import FALHA, OK, Source
from discovery.storage import write_run

CLIENT = {"id": "acme", "name": "Acme", "site": "https://acme.com.br/"}
T0 = datetime(2026, 9, 25, 14, 30, 12)


def sources():
    return [
        Source("site", "https://acme.com.br/", OK, conteudo={"titulo": "Home", "texto": "Olá"}),
        Source("cnpj", "https://brasilapi.com.br/api/cnpj/v1/1", FALHA, erro="HTTP 500"),
        Source("busca", "https://ddg/?q=a", OK, conteudo={
            "query": "a", "motor": "bing", "resultados": [{"titulo": "T", "url": "https://x", "trecho": "s"}]}),
    ]


def test_writes_raw_json_and_md(tmp_path):
    path = write_run(tmp_path / "reports", CLIENT, {"queries": ["a"]}, sources(), T0, T0)
    assert path.name == "2026-09-25_143012-acme"
    raw = json.loads((path / "raw.json").read_text())
    assert raw["versao_formato"] == 1 and raw["cliente"]["id"] == "acme"
    assert {s["tipo"] for s in raw["fontes"]} == {"site", "cnpj", "busca"}
    for fonte in raw["fontes"]:
        assert {"origem", "coletado_em", "status", "erro", "conteudo"} <= fonte.keys()
    md = (path / "raw.md").read_text()
    assert "Olá" in md and "https://x" in md


def test_failures_appear_in_both_files(tmp_path):
    failing = [Source("site", "https://a/", FALHA, erro="timeout"),
               Source("cnpj", "site", "nao_coletada", erro="sem cnpj")]
    path = write_run(tmp_path, CLIENT, {}, failing, T0, T0)
    raw = json.loads((path / "raw.json").read_text())
    assert [f["status"] for f in raw["fontes"]] == ["falha", "nao_coletada"]
    md = (path / "raw.md").read_text()
    assert "timeout" in md and "sem cnpj" in md


def test_two_runs_same_second_get_distinct_dirs(tmp_path):
    a = write_run(tmp_path, CLIENT, {}, sources(), T0, T0)
    b = write_run(tmp_path, CLIENT, {}, sources(), T0, T0)
    assert a != b and a.exists() and b.exists()


def test_existing_run_is_untouched(tmp_path):
    a = write_run(tmp_path, CLIENT, {}, sources(), T0, T0)
    before = (a / "raw.json").read_bytes()
    write_run(tmp_path, CLIENT, {}, [], T0, T0)
    assert (a / "raw.json").read_bytes() == before


def test_new_source_types_are_rendered_in_raw_md(tmp_path):
    new = [
        Source("sitemap", "https://a/sitemap.xml", OK, conteudo={
            "sitemaps_lidos": ["https://a/sitemap.xml"], "total_urls": 1234,
            "por_secao": {"/blog": 10}, "por_sufixo": {"*/p": 900}, "amostra": ["https://a/x/p"]}),
        Source("tecnologia", "https://a/", OK, conteudo={
            "detectadas": [{"nome": "VTEX", "categoria": "e-commerce/CMS", "evidencia": ["url: vtexassets.com"]}],
            "dominios_contatados": ["a.com", "vtexassets.com"]}),
        Source("filiais", "https://api/*", OK, conteudo={"raiz": "11222333", "estabelecimentos": [
            {"cnpj": "11222333000181", "tipo": "matriz", "municipio": "UBERLANDIA", "uf": "MG",
             "cnae_descricao": "Comércio", "situacao": "ATIVA", "inicio_atividade": "2012-04-04"}]}),
        Source("noticias", "https://news", OK, conteudo={
            "query": '"Acme"', "motor": "google-news", "itens": [], "descartados": 17}),
    ]
    path = write_run(tmp_path, CLIENT, {}, new, T0, T0)
    md = (path / "raw.md").read_text()
    assert "total de URLs: 1234" in md and "`*/p`=900" in md
    assert "**VTEX** (e-commerce/CMS): url: vtexassets.com" in md
    assert "11222333000181 (matriz): UBERLANDIA/MG" in md
    assert "descartados por não citar o cliente: 17" in md
    assert json.loads((path / "raw.json").read_text())["fontes"][1]["tipo"] == "tecnologia"
