from discovery.collectors.site import collect_site
from discovery.models import FALHA, NAO_COLETADA, OK

HOME = """<title>Home</title><body><h1>Bem-vindo</h1>
<a href="/sobre">Sobre nós</a> <a href="/contato">Contato</a>
<a href="/privacidade">Privacidade</a> <a href="/restrito">Área restrita</a>
<a href="https://outro-dominio.example/x">Externo</a> <a href="/catalogo.pdf">PDF</a>
<a href="/lixo1">l1</a><a href="/lixo2">l2</a><a href="/lixo3">l3</a></body>"""


def routes():
    page = lambda t: f"<title>{t}</title><body><p>Texto {t}</p><p>Texto {t}</p></body>"
    return {
        "/": HOME,
        "/sobre": page("Sobre"),
        "/contato": page("Contato"),
        "/privacidade": page("Privacidade"),
        "/restrito": ("redirect", "/login"),
        "/login": page("Login"),
        "/lixo1": page("l1"), "/lixo2": page("l2"), "/lixo3": page("l3"),
    }


def by_url(sources):
    return {s.origem.split("/", 3)[-1]: s for s in sources}


def test_crawls_same_domain_and_prioritizes(browser_context, serve):
    base = serve(routes())
    sources = collect_site(browser_context, base + "/", max_pages=4)
    urls = [s.origem.removeprefix(base) for s in sources]
    assert urls[0] == "/"
    assert set(urls[1:]) <= {"/sobre", "/contato", "/privacidade", "/restrito"}
    assert all(u.startswith("/") for u in urls)  # nada de outro domínio
    assert not any("pdf" in u or "lixo" in u for u in urls)
    home = sources[0]
    assert home.status == OK and home.conteudo["titulo"] == "Home"


def test_page_limit_is_respected(browser_context, serve):
    base = serve(routes())
    assert len(collect_site(browser_context, base + "/", max_pages=2)) == 2


def test_text_is_deduplicated(browser_context, serve):
    base = serve(routes())
    sobre = [s for s in collect_site(browser_context, base + "/", 5) if s.origem.endswith("/sobre")][0]
    assert sobre.conteudo["texto"].count("Texto Sobre") == 1


def test_unreachable_site_is_recorded_as_failure(browser_context):
    sources = collect_site(browser_context, "http://127.0.0.1:1/", max_pages=3)
    assert len(sources) == 1
    assert sources[0].status == FALHA and sources[0].erro


def test_login_redirect_is_discarded(browser_context, serve):
    base = serve(routes())
    sources = collect_site(browser_context, base + "/", max_pages=10)
    restrito = [s for s in sources if s.origem.endswith("/restrito")][0]
    assert restrito.status == NAO_COLETADA
    assert restrito.conteudo is None
    assert "login" in restrito.erro
