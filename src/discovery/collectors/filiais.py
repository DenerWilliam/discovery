"""Estabelecimentos que compartilham a raiz de CNPJ do cliente (matriz e filiais)."""

from __future__ import annotations

import time

import httpx

from discovery.collectors.cnpj import API_URL, only_digits
from discovery.models import FALHA, NAO_COLETADA, OK, Source

MAX_SUFFIX = 20
STOP_AFTER_MISSING = 3
PAUSE_SECONDS = 0.3


def check_digits(base12: str) -> str:
    """Dois dígitos verificadores de um CNPJ a partir dos 12 primeiros dígitos."""
    digits = base12
    for size in (12, 13):
        weights = list(range(size - 7, 1, -1)) + list(range(9, 1, -1))
        total = sum(int(d) * w for d, w in zip(digits[:size], weights))
        check = 11 - total % 11
        digits += str(0 if check >= 10 else check)
    return digits[12:]


def build_cnpj(root: str, suffix: int) -> str:
    base = f"{root}{suffix:04d}"
    return base + check_digits(base)


def _summarize(cnpj: str, data: dict) -> dict:
    return {
        "cnpj": cnpj,
        "tipo": {1: "matriz", 2: "filial"}.get(data.get("identificador_matriz_filial"), ""),
        "nome_fantasia": data.get("nome_fantasia") or "",
        "municipio": data.get("municipio") or "",
        "uf": data.get("uf") or "",
        "cnae_fiscal": data.get("cnae_fiscal"),
        "cnae_descricao": data.get("cnae_fiscal_descricao") or "",
        "situacao": data.get("descricao_situacao_cadastral") or "",
        "inicio_atividade": data.get("data_inicio_atividade") or "",
    }


def collect_filiais(
    cnpj_source: Source,
    client: httpx.Client | None = None,
    max_suffix: int = MAX_SUFFIX,
    stop_after: int = STOP_AFTER_MISSING,
    pause: float = PAUSE_SECONDS,
) -> Source:
    """Só consulta quando a fonte de CNPJ está ok; para após vários sufixos inexistentes."""
    if cnpj_source.status != OK or not cnpj_source.conteudo:
        return Source("filiais", "site", NAO_COLETADA,
                      erro=f"CNPJ não resolvido (fonte cadastral: {cnpj_source.status}).")
    known = only_digits(cnpj_source.conteudo["cnpj"])
    root = known[:8]
    known_data = cnpj_source.conteudo["dados"]
    found = {known: _summarize(known, known_data)}

    own_client = client is None
    client = client or httpx.Client(timeout=20)
    missing = 0
    try:
        for suffix in range(1, max_suffix + 1):
            cnpj = build_cnpj(root, suffix)
            if cnpj == known:
                missing = 0
                continue
            if pause:
                time.sleep(pause)
            try:
                response = client.get(API_URL.format(cnpj=cnpj))
            except httpx.HTTPError as exc:
                return _partial(root, found, f"{type(exc).__name__}: {exc}")
            if response.status_code == 404:
                missing += 1
                if missing >= stop_after:
                    break
                continue
            if response.status_code != 200:
                return _partial(root, found, f"HTTP {response.status_code} em {cnpj}")
            missing = 0
            found[cnpj] = _summarize(cnpj, response.json())
    finally:
        if own_client:
            client.close()
    return Source("filiais", API_URL.format(cnpj=f"{root}*"), OK, conteudo=_content(root, found))


def _content(root: str, found: dict) -> dict:
    return {"raiz": root, "estabelecimentos": sorted(found.values(), key=lambda e: e["cnpj"])}


def _partial(root: str, found: dict, reason: str) -> Source:
    return Source("filiais", API_URL.format(cnpj=f"{root}*"), FALHA,
                  erro=f"Busca interrompida (resultado parcial): {reason}",
                  conteudo=_content(root, found))
