"""Extração de CNPJ do texto do site e consulta cadastral por API pública."""

from __future__ import annotations

import re

import httpx

from discovery.models import AMBIGUA, FALHA, NAO_COLETADA, OK, Source

API_URL = "https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
_CNPJ_RE = re.compile(r"(?<!\d)\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}(?!\d)")


def only_digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def is_valid_cnpj(value: str) -> bool:
    digits = only_digits(value)
    if len(digits) != 14 or len(set(digits)) == 1:
        return False
    for size in (12, 13):
        weights = list(range(size - 7, 1, -1)) + list(range(9, 1, -1))
        total = sum(int(d) * w for d, w in zip(digits[:size], weights))
        check = 11 - total % 11
        if check >= 10:
            check = 0
        if int(digits[size]) != check:
            return False
    return True


def find_cnpjs(site_sources: list[Source]) -> dict[str, dict]:
    """CNPJs válidos no texto das páginas: ``{cnpj: {ocorrencias, paginas}}``."""
    found: dict[str, dict] = {}
    for source in site_sources:
        if source.status != OK or not source.conteudo:
            continue
        for match in _CNPJ_RE.findall(source.conteudo.get("texto", "")):
            if not is_valid_cnpj(match):
                continue
            entry = found.setdefault(only_digits(match), {"ocorrencias": 0, "paginas": []})
            entry["ocorrencias"] += 1
            if source.origem not in entry["paginas"]:
                entry["paginas"].append(source.origem)
    return found


def _query(cnpj: str, client: httpx.Client, extra: dict | None = None) -> Source:
    url = API_URL.format(cnpj=cnpj)
    try:
        response = client.get(url, timeout=20)
    except httpx.HTTPError as exc:
        return Source("cnpj", url, FALHA, erro=f"{type(exc).__name__}: {exc}")
    if response.status_code != 200:
        return Source("cnpj", url, FALHA, erro=f"HTTP {response.status_code}: {response.text[:200]}")
    content = {"cnpj": cnpj, "dados": response.json()}
    content.update(extra or {})
    return Source("cnpj", url, OK, conteudo=content)


def collect_cnpj(
    informed: str | None, site_sources: list[Source], client: httpx.Client | None = None
) -> Source:
    """Resolve o CNPJ (informado, do site ou ambíguo) e consulta a API quando possível."""
    own_client = client is None
    client = client or httpx.Client()
    try:
        if informed:
            if not is_valid_cnpj(informed):
                return Source("cnpj", "informado", FALHA, erro=f"CNPJ informado inválido: {informed}")
            return _query(only_digits(informed), client, {"origem_cnpj": "informado"})

        candidates = find_cnpjs(site_sources)
        if not candidates:
            return Source("cnpj", "site", NAO_COLETADA,
                          erro="Nenhum CNPJ informado nem encontrado no site.")
        if len(candidates) > 1:
            return Source("cnpj", "site", AMBIGUA,
                          erro="Vários CNPJs válidos no site; informe --cnpj para consultar.",
                          conteudo={"candidatos": candidates})
        cnpj, info = next(iter(candidates.items()))
        return _query(cnpj, client, {"origem_cnpj": "site", "paginas": info["paginas"]})
    finally:
        if own_client:
            client.close()
