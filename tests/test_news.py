from pathlib import Path

import httpx

from discovery.collectors.news import collect_news, parse_feed
from discovery.models import FALHA, OK

XML = (Path(__file__).parent / "fixtures" / "news.xml").read_text()


def client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_parse_feed():
    items = parse_feed(XML)
    assert items[0] == {"titulo": "Acme expande frota - Jornal X", "url": "https://news.example/1",
                        "data": "Wed, 24 Sep 2026 10:00:00 GMT", "veiculo": "Jornal X"}
    assert items[1]["veiculo"] == ""


def test_collect_news_quotes_the_name():
    seen = []

    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200, text=XML)

    src = collect_news("Acme", client(handler))
    assert src.status == OK and len(src.conteudo["itens"]) == 2
    assert src.conteudo["motor"] == "google-news" and src.conteudo["descartados"] == 0
    assert "%22Acme%22" in seen[0]


def test_empty_feed_is_success():
    empty = '<?xml version="1.0"?><rss version="2.0"><channel><title>x</title></channel></rss>'
    src = collect_news("Acme", client(lambda r: httpx.Response(200, text=empty)))
    assert src.status == OK and src.conteudo["itens"] == []


def test_http_error_is_failure():
    assert collect_news("Acme", client(lambda r: httpx.Response(503))).status == FALHA


def test_network_error_is_failure():
    def boom(request):
        raise httpx.ConnectError("sem rede")

    src = collect_news("Acme", client(boom))
    assert src.status == FALHA and "sem rede" in src.erro


def test_invalid_xml_is_failure():
    assert collect_news("Acme", client(lambda r: httpx.Response(200, text="<html>"))).status == FALHA


MIXED = (
    '<?xml version="1.0"?><rss version="2.0"><channel><title>x</title>'
    "<item><title>ÉSTILO Ar abre filial - Jornal</title><link>https://n/1</link></item>"
    "<item><title>Fuzil AR-15 e o massacre</title><link>https://n/2</link></item>"
    "<item><title>Estilo de vida: ar puro</title><link>https://n/3</link></item>"
    "</channel></rss>"
)


def test_irrelevant_items_are_discarded_and_counted():
    src = collect_news("Estilo Ar", client(lambda r: httpx.Response(200, text=MIXED)))
    assert [i["url"] for i in src.conteudo["itens"]] == ["https://n/1"]  # sem acento e sem caixa
    assert src.conteudo["descartados"] == 2 and src.status == OK


def test_all_irrelevant_is_empty_with_count_and_no_junk_stored():
    src = collect_news("Haix Rental", client(lambda r: httpx.Response(200, text=MIXED)))
    assert src.status == OK and src.conteudo["itens"] == []
    assert src.conteudo["descartados"] == 3
