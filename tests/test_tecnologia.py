from discovery.collectors.tecnologia import collect_tecnologia, detect
from discovery.models import FALHA, OK

HTML = """<html><head><title>Loja</title>
<script src="https://cdn.shopify.com/s/files/theme.js"></script>
<script src="https://www.googletagmanager.com/gtag/js?id=G-1"></script>
</head><body><a href="https://api.whatsapp.com/send?phone=5511">Fale</a></body></html>"""


def test_detect_matches_html_urls_cookies_headers_with_evidence():
    found = detect(
        html='<a href="https://wa.me/5511">zap</a>',
        request_urls=["https://cdn.shopify.com/x.js", "https://connect.facebook.net/pt/fbevents.js"],
        cookies=["_ga", "_fbp", "session"],
        headers={"Server": "cloudflare", "X-Other": "1"},
    )
    by_name = {d["nome"]: d for d in found}
    assert {"Shopify", "Meta Pixel", "Google Analytics", "Cloudflare", "WhatsApp (link/botão)"} <= by_name.keys()
    assert "url: cdn.shopify.com" in by_name["Shopify"]["evidencia"]
    assert "cookie: _fbp" in by_name["Meta Pixel"]["evidencia"]
    assert by_name["Cloudflare"]["categoria"] == "CDN e infraestrutura"
    assert "cabeçalho: server=cloudflare" in by_name["Cloudflare"]["evidencia"]


def test_detect_nothing():
    assert detect("<html>simples</html>", ["http://x/a.css"], [], {"Server": "nginx"}) == []


def test_collect_reads_home_scripts_cookies_and_headers(browser_context, serve):
    browser_context.clear_cookies()
    browser_context.route("https://cdn.shopify.com/**", lambda route: route.fulfill(body="", content_type="text/javascript"))
    browser_context.route("https://www.googletagmanager.com/**", lambda route: route.fulfill(body="", content_type="text/javascript"))
    base = serve({"/": ("page", HTML, {"Set-Cookie": "_fbp=abc; Path=/", "Server": "cloudflare"})})
    src = collect_tecnologia(browser_context, base + "/")
    assert src.status == OK
    names = {d["nome"] for d in src.conteudo["detectadas"]}
    assert {"Shopify", "Google Analytics", "Cloudflare", "Meta Pixel", "WhatsApp (link/botão)"} <= names
    assert "cdn.shopify.com" in src.conteudo["dominios_contatados"]


def test_collect_home_with_nothing_known_is_ok_and_empty(browser_context, serve):
    browser_context.clear_cookies()  # o contexto é compartilhado entre testes
    base = serve({"/": "<html><body>Oi</body></html>"})
    src = collect_tecnologia(browser_context, base + "/")
    assert src.status == OK and src.conteudo["detectadas"] == []


def test_collect_unreachable_home_is_failure(browser_context):
    src = collect_tecnologia(browser_context, "http://127.0.0.1:1/")
    assert src.status == FALHA and src.erro


def test_detects_jet_platform_by_header_and_asset_domain():
    found = detect("<html></html>", ["https://estiloar.jetassets.com.br/a.js", "https://googleads.g.doubleclick.net/x"],
                   [], {"Powered": "jet-neo", "Content-Security-Policy": "frame-ancestors *.plataformaneo.com.br"})
    by_name = {d["nome"]: d for d in found}
    assert "Jet e-commerce (Plataforma Neo)" in by_name and "Google Ads / DoubleClick" in by_name
    assert "cabeçalho: powered=jet-neo" in by_name["Jet e-commerce (Plataforma Neo)"]["evidencia"]
