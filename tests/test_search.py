from pathlib import Path

from playwright.sync_api import Error as PlaywrightError

from discovery.collectors.search import (
    ENGINES, _decode_bing_url, parse_bing, parse_ddg, search_query,
)
from discovery.models import NAO_COLETADA, OK

FIX = Path(__file__).parent / "fixtures"
read = lambda name: (FIX / name).read_text()


def fake_fetch(responses):
    """responses: {trecho_da_url: (status, html) | Exception}"""
    calls = []

    def fetch(url):
        calls.append(url)
        for key, value in responses.items():
            if key in url:
                if isinstance(value, Exception):
                    raise value
                return value
        raise AssertionError(f"URL inesperada: {url}")

    fetch.calls = calls
    return fetch


def test_parse_ddg():
    assert parse_ddg(read("ddg_results.html")) == [
        {"titulo": "Notícia sobre a Acme", "url": "https://exemplo.com/noticia",
         "trecho": "A Acme expande frota em 2026."},
        {"titulo": "Vaga de TI", "url": "https://outro.com/vaga",
         "trecho": "Analista de sistemas ERP."},
    ]


def test_parse_bing_decodes_redirect_links():
    assert parse_bing(read("bing_results.html")) == [
        {"titulo": "Vaga Analista de ERP - Acme", "url": "https://exemplo.com/vaga-analista-erp",
         "trecho": "Procuramos analista de ERP para a Acme."},
        {"titulo": "Link direto", "url": "https://outro.com/direto", "trecho": "Sem redirecionamento."},
    ]


def test_decode_bing_url_keeps_unknown_links():
    assert _decode_bing_url("https://x.com/a") == "https://x.com/a"
    assert _decode_bing_url("https://www.bing.com/ck/a?u=zzzz") == "https://www.bing.com/ck/a?u=zzzz"


def test_first_engine_wins_and_records_motor():
    fetch = fake_fetch({"bing.com": (200, read("bing_results.html"))})
    src = search_query('"Acme" vagas', fetch)
    assert src.status == OK and src.conteudo["motor"] == "bing"
    assert len(src.conteudo["resultados"]) == 2
    assert len(fetch.calls) == 1  # DuckDuckGo nem foi tentado


def test_falls_back_when_first_engine_is_blocked():
    fetch = fake_fetch({
        "bing.com": (200, read("bing_blocked.html")),
        "duckduckgo.com": (200, read("ddg_results.html")),
    })
    src = search_query("Acme", fetch)
    assert src.status == OK and src.conteudo["motor"] == "duckduckgo"


def test_falls_back_on_navigation_error():
    fetch = fake_fetch({"bing.com": PlaywrightError("net::ERR_ABORTED"),
                        "duckduckgo.com": (200, read("ddg_results.html"))})
    assert search_query("Acme", fetch).conteudo["motor"] == "duckduckgo"


def test_all_engines_blocked_is_not_collected():
    fetch = fake_fetch({"bing.com": (200, read("bing_blocked.html")),
                        "duckduckgo.com": (403, "")})
    src = search_query("Acme", fetch)
    assert src.status == NAO_COLETADA
    assert "bing" in src.erro and "duckduckgo" in src.erro
    assert src.conteudo == {"query": "Acme"}


def test_engine_without_block_and_no_results_is_ok_but_empty():
    fetch = fake_fetch({"bing.com": (200, "<html><body>nada</body></html>"),
                        "duckduckgo.com": (200, "<html><body>nada</body></html>")})
    src = search_query("Acme", fetch)
    assert src.status == OK and src.conteudo["resultados"] == []


def test_engine_order():
    assert [e.name for e in ENGINES] == ["bing", "duckduckgo"]


IRRELEVANT = ('<li class="b_algo"><h2><a href="https://lixo.com/x">Fórum de jogos</a></h2>'
              '<p>Nada a ver</p></li>')


def test_irrelevant_results_are_discarded_and_next_engine_is_tried():
    fetch = fake_fetch({"bing.com": (200, IRRELEVANT),
                        "duckduckgo.com": (200, read("ddg_results.html"))})
    src = search_query("Acme", fetch, keyword="acme")
    assert src.conteudo["motor"] == "duckduckgo"


def test_all_irrelevant_is_not_collected_and_junk_is_not_stored():
    fetch = fake_fetch({"bing.com": (200, IRRELEVANT), "duckduckgo.com": (403, "")})
    src = search_query("Acme", fetch, keyword="acme")
    assert src.status == NAO_COLETADA and "sem relação" in src.erro
    assert "resultados" not in src.conteudo


def test_bing_is_retried_once_before_falling_back():
    calls = {"n": 0}

    def fetch(url):
        if "bing.com" in url:
            calls["n"] += 1
            return (200, IRRELEVANT if calls["n"] == 1 else read("bing_results.html"))
        raise AssertionError("não deveria chegar ao DuckDuckGo")

    src = search_query("Acme", fetch, keyword="acme")
    assert src.conteudo["motor"] == "bing" and calls["n"] == 2
