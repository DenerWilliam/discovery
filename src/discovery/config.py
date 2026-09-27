"""Configuração por cliente: ``clients/<id>.yaml`` com sobreposição por parâmetros de CLI."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import yaml

DEFAULT_MAX_PAGES = 15

# Bing/DuckDuckGo automatizados degradam com termos extras (retornam resultados
# aleatórios); o padrão é só o nome entre aspas. Queries extras: clients/<id>.yaml.
DEFAULT_QUERIES = ['"{name}"']


class ConfigError(Exception):
    pass


@dataclass
class ClientConfig:
    id: str
    name: str
    site: str
    cnpj: str | None = None
    queries: list[str] = field(default_factory=list)
    max_pages: int = DEFAULT_MAX_PAGES


def slugify(value: str) -> str:
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def load_config(
    *,
    client: str | None = None,
    name: str | None = None,
    site: str | None = None,
    cnpj: str | None = None,
    queries: list[str] | None = None,
    max_pages: int | None = None,
    clients_dir: Path = Path("clients"),
) -> ClientConfig:
    data: dict = {}
    if client:
        path = Path(clients_dir) / f"{client}.yaml"
        if not path.is_file():
            raise ConfigError(f"Arquivo de configuração não encontrado: {path}")
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    final_name = name or data.get("name") or client
    final_site = site or data.get("site")
    if not final_site:
        raise ConfigError(
            "Informe o site do cliente com --site ou por um arquivo em clients/ (--client)."
        )
    if not final_name:
        raise ConfigError("Informe o nome do cliente com --name ou --client.")

    final_queries = queries or data.get("queries") or DEFAULT_QUERIES
    final_queries = [q.replace("{name}", final_name) for q in final_queries]

    raw_cnpj = cnpj or data.get("cnpj")
    return ClientConfig(
        id=client or slugify(final_name),
        name=final_name,
        site=final_site,
        cnpj=str(raw_cnpj) if raw_cnpj else None,
        queries=final_queries,
        max_pages=int(max_pages or data.get("max_pages") or DEFAULT_MAX_PAGES),
    )
