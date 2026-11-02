import json

from discovery import cli
from discovery.models import NAO_COLETADA, OK, Source


class FakeChromium:
    def __init__(self, registro):
        self.registro = registro

    def launch(self):
        return self

    def new_context(self, **kwargs):
        self.registro.append(kwargs)
        return object()

    def close(self):
        pass


class FakePlaywright:
    def __init__(self, registro):
        self.chromium = FakeChromium(registro)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_scan_passes_locale_to_browser_and_raw(tmp_path, monkeypatch):
    registro = []
    def stub(tipo):
        return Source(tipo, "x", NAO_COLETADA, erro="stub")

    fonte = stub("cnpj")
    monkeypatch.setattr(cli, "sync_playwright", lambda: FakePlaywright(registro))
    monkeypatch.setattr(cli, "collect_site", lambda *a, **k: [
        Source("site", "https://acme.com.br/", OK, conteudo={"titulo": "Home", "texto": "oi"})])
    monkeypatch.setattr(cli, "collect_sitemap", lambda *a, **k: stub("sitemap"))
    monkeypatch.setattr(cli, "collect_tecnologia", lambda *a, **k: stub("tecnologia"))
    monkeypatch.setattr(cli, "collect_cnpj", lambda *a, **k: fonte)
    monkeypatch.setattr(cli, "collect_filiais", lambda *a, **k: stub("filiais"))
    monkeypatch.setattr(cli, "collect_searches", lambda *a, **k: [])
    monkeypatch.setattr(cli, "collect_news", lambda *a, **k: stub("noticias"))

    parser = cli.build_parser()
    args = parser.parse_args([
        "scan", "--name", "Acme", "--site", "https://acme.com.br", "--locale", "en-US",
        "--clients-dir", str(tmp_path), "--reports-dir", str(tmp_path)])
    assert cli.run_scan(args) == 0

    assert registro[0]["locale"] == "en-US"
    run = next(tmp_path.glob("*-acme"))
    raw = json.loads((run / "raw.json").read_text(encoding="utf-8"))
    assert raw["parametros"]["locale"] == "en-US"
