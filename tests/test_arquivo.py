import httpx
import pytest

from discovery.collectors import arquivo
from discovery.models import FALHA, OK, RECUSADO

INDICE = [
    ["timestamp", "original", "statuscode"],
    ["20240101000000", "https://loja.com.br/", "200"],
    ["20250101000000", "https://loja.com.br/", "200"],
    ["20240202000000", "https://loja.com.br/sobre", "200"],
    ["20240303000000", "https://outro.com/x", "200"],
    ["20240404000000", "https://loja.com.br/foto.jpg", "200"],
    ["20240505000000", "https://loja.com.br/velho", "301"],
]

HTML = {
    "https://loja.com.br/": "<html><head><title>Home</title><script>x()</script></head>"
                            "<body><h1>Bem-vindo</h1><p>Bem-vindo</p></body></html>",
    "https://loja.com.br/sobre": "<html><head><title>Sobre</title></head><body>Sobre nós</body></html>",
}


@pytest.fixture(autouse=True)
def cache_limpo():
    arquivo.limpar_cache()
    yield
    arquivo.limpar_cache()


def client(registro=None):
    def handler(request):
        url = str(request.url)
        if registro is not None:
            registro.append(url)
        if "web.archive.org/cdx/" in url:
            return httpx.Response(200, json=INDICE)
        for original, html in HTML.items():
            if url.endswith(original):
                return httpx.Response(200, text=html)
        return httpx.Response(404)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_capturas_keeps_latest_only_and_ignores_non_200():
    mapa = arquivo.capturas("loja.com.br", client())
    assert mapa["https://loja.com.br/"] == "20250101000000"
    assert mapa["https://loja.com.br/sobre"] == "20240202000000"
    assert "https://loja.com.br/velho" not in mapa


def test_capturas_is_cached_per_domain():
    registro = []
    c = client(registro)
    arquivo.capturas("loja.com.br", c)
    arquivo.capturas("loja.com.br", c)
    assert sum("cdx" in url for url in registro) == 1


def test_extrair_title_and_text_without_script():
    titulo, texto = arquivo.extrair(HTML["https://loja.com.br/"])
    assert titulo == "Home"
    assert texto.splitlines() == ["Bem-vindo"]


def test_coletar_uses_home_first_and_marks_capture():
    fontes = arquivo.coletar("loja.com.br", 2, client=client(), pausa=0)
    assert [f.origem for f in fontes] == ["https://loja.com.br/", "https://loja.com.br/sobre"]
    home = fontes[0]
    assert home.status == OK and home.conteudo["origem"] == "arquivo"
    assert home.conteudo["captura"] == "20250101000000"
    assert home.conteudo["url_snapshot"].endswith("id_/https://loja.com.br/")
    assert home.conteudo["titulo"] == "Home"


def test_coletar_skips_binary_and_other_domains():
    fontes = arquivo.coletar("loja.com.br", 10, client=client(), pausa=0)
    origens = [f.origem for f in fontes]
    assert not any("foto.jpg" in u or "outro.com" in u for u in origens)


def test_home_returns_capture_and_html():
    captura, html = arquivo.home("loja.com.br", client=client())
    assert captura == "20250101000000" and "Bem-vindo" in html


def test_capturas_retries_when_archive_throttles():
    tentativas = []

    def handler(request):
        tentativas.append(str(request.url))
        if len(tentativas) == 1:
            return httpx.Response(429)
        return httpx.Response(200, json=INDICE)

    mapa = arquivo.capturas("loja.com.br", httpx.Client(transport=httpx.MockTransport(handler)))
    assert len(tentativas) == 2
    assert mapa["https://loja.com.br/"] == "20250101000000"


def test_coletar_deduplicates_root_variants():
    indice = [
        ["timestamp", "original", "statuscode"],
        ["20090207090222", "http://loja.com.br:80/", "200"],
        ["20160109173950", "http://loja.com.br/", "200"],
        ["20240101000000", "https://www.loja.com.br/", "200"],
        ["20240202000000", "https://loja.com.br/sobre", "200"],
    ]

    def handler(request):
        url = str(request.url)
        if "web.archive.org/cdx/" in url:
            return httpx.Response(200, json=indice)
        return httpx.Response(200, text="<html><head><title>P</title></head></html>")

    fontes = arquivo.coletar(
        "loja.com.br", 10, client=httpx.Client(transport=httpx.MockTransport(handler)), pausa=0
    )
    origens = [f.origem for f in fontes]
    assert origens == ["https://www.loja.com.br/", "https://loja.com.br/sobre"]
    assert fontes[0].conteudo["captura"] == "20240101000000"


def test_home_prefers_plain_https_root_over_campaign_link():
    indice = [
        ["timestamp", "original", "statuscode"],
        ["20250101000000", "https://loja.com.br/?trk=campanha", "200"],
        ["20240101000000", "https://loja.com.br/", "200"],
        ["20060101000000", "http://www.loja.com.br:80/", "200"],
    ]
    paginas = {
        "20250101000000": "<html><head><title>Campanha</title></head></html>",
        "20240101000000": "<html><head><title>Home</title></head></html>",
        "20060101000000": "<html><head><title>Index of /</title></head></html>",
    }

    def handler(request):
        url = str(request.url)
        if "web.archive.org/cdx/" in url:
            return httpx.Response(200, json=indice)
        for captura, html in paginas.items():
            if f"/{captura}id_" in url:
                return httpx.Response(200, text=html)
        return httpx.Response(404)

    achado = arquivo.home("loja.com.br", client=httpx.Client(transport=httpx.MockTransport(handler)))
    assert achado is not None
    assert achado[0] == "20240101000000" and "Home" in achado[1]


def test_coletar_reports_throttled_archive_as_recusado():
    def handler(request):
        if "web.archive.org/cdx/" in str(request.url):
            return httpx.Response(200, json=INDICE)
        return httpx.Response(429)

    fontes = arquivo.coletar(
        "loja.com.br", 5, client=httpx.Client(transport=httpx.MockTransport(handler)), pausa=0
    )
    assert len(fontes) == 1
    assert fontes[0].status == FALHA and fontes[0].motivo == RECUSADO


def test_missing_index_returns_empty():
    c = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(404)))
    assert arquivo.capturas("nada.com.br", c) == {}
    assert arquivo.home("nada.com.br", client=c) is None
