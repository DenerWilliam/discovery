import pytest

from discovery.config import ConfigError, load_config


@pytest.fixture
def clients_dir(tmp_path):
    (tmp_path / "acme.yaml").write_text(
        "name: Acme Rental\nsite: https://acme.com.br/\ncnpj: '11.222.333/0001-81'\n"
        "queries:\n  - '{name} sistemas'\nmax_pages: 5\n",
        encoding="utf-8",
    )
    return tmp_path


def test_loads_client_file(clients_dir):
    cfg = load_config(client="acme", clients_dir=clients_dir)
    assert (cfg.id, cfg.name, cfg.site) == ("acme", "Acme Rental", "https://acme.com.br/")
    assert cfg.cnpj == "11.222.333/0001-81"
    assert cfg.queries == ["Acme Rental sistemas"]
    assert cfg.max_pages == 5


def test_cli_params_override_file(clients_dir):
    cfg = load_config(client="acme", site="https://outro.com", max_pages=3, clients_dir=clients_dir)
    assert cfg.site == "https://outro.com"
    assert cfg.max_pages == 3


def test_params_without_file_use_default_queries(tmp_path):
    cfg = load_config(name="Cliente X", site="https://exemplo.com.br", clients_dir=tmp_path)
    assert cfg.id == "cliente-x"
    assert cfg.queries == ['"Cliente X"']
    assert all('"Cliente X"' in q for q in cfg.queries)  # nome entre aspas


def test_missing_site_is_error(tmp_path):
    with pytest.raises(ConfigError, match="site"):
        load_config(name="Cliente X", clients_dir=tmp_path)


def test_missing_client_file_is_error(tmp_path):
    with pytest.raises(ConfigError, match="não encontrado"):
        load_config(client="nada", clients_dir=tmp_path)
