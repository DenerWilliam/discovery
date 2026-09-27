import httpx

from discovery.collectors.sitemap import collect_sitemap
from discovery.models import FALHA, NAO_COLETADA, OK

NS = 'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'


def urlset(*urls):
    return f'<?xml version="1.0"?><urlset {NS}>' + "".join(f"<url><loc>{u}</loc></url>" for u in urls) + "</urlset>"


def index(*urls):
    return f'<?xml version="1.0"?><sitemapindex {NS}>' + "".join(f"<sitemap><loc>{u}</loc></sitemap>" for u in urls) + "</sitemapindex>"


def client(routes):
    def handler(request):
        body = routes.get(request.url.path)
        if body is None:
            return httpx.Response(404)
        return httpx.Response(200, text=body)

    return httpx.Client(transport=httpx.MockTransport(handler))


B = "https://loja.com.br"


def test_simple_sitemap_from_robots():
    src = collect_sitemap(B + "/", client({
        "/robots.txt": f"User-agent: *\nSitemap: {B}/mapa.xml\n",
        "/mapa.xml": urlset(f"{B}/termostato-x/p", f"{B}/termostato-y/p", f"{B}/sistema-ac/c", f"{B}/blog/post-1", f"{B}/"),
    }))
    assert src.status == OK
    c = src.conteudo
    assert c["total_urls"] == 5
    assert c["por_sufixo"] == {"*/p": 2, "*/c": 1}
    assert c["por_secao"]["/blog"] == 1 and len(c["amostra"]) == 5


def test_falls_back_to_sitemap_xml():
    src = collect_sitemap(B, client({"/sitemap.xml": urlset(f"{B}/a/p")}))
    assert src.status == OK and src.conteudo["total_urls"] == 1


def test_sitemap_index_sums_children():
    src = collect_sitemap(B, client({
        "/sitemap.xml": index(f"{B}/s1.xml", f"{B}/s2.xml"),
        "/s1.xml": urlset(f"{B}/a/p", f"{B}/b/p"),
        "/s2.xml": urlset(f"{B}/c/p"),
    }))
    assert src.conteudo["total_urls"] == 3 and len(src.conteudo["sitemaps_lidos"]) == 3


def test_no_sitemap_is_not_collected():
    src = collect_sitemap(B, client({}))
    assert src.status == NAO_COLETADA and "sitemap" in src.erro.lower()


def test_invalid_xml_is_failure():
    src = collect_sitemap(B, client({"/sitemap.xml": "<html>nada"}))
    assert src.status == FALHA and "XML" in src.erro


def test_network_error_is_not_collected():
    def boom(request):
        raise httpx.ConnectError("sem rede")

    src = collect_sitemap(B, httpx.Client(transport=httpx.MockTransport(boom)))
    assert src.status == NAO_COLETADA
