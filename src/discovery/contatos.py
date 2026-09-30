"""Exporta o CSV de contatos (res.partner) no formato de importação do Odoo.

Lê só o ``raw.json`` de uma execução (e, opcionalmente, um arquivo de ajustes); não acessa a web.
"""

from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from discovery.collectors.cnpj import only_digits
from discovery.models import OK
from discovery.storage import TIMESTAMP_FORMAT

COLUMNS = [
    "Razão Social", "ID do Imposto", "Endereço", "Cidade", "Estado", "CEP", "País", "Telefone",
    "E-mail", "Site", "Idioma", "Vendedor", "Indústria principal", "Indústrias Secundárias",
    "Perfil Fiscal do Parceiro", "Natureza Jurídica", "CNAE Principal", "CNAE Secundário",
    "Capital Social", "Conta de Pagamento", "Conta de Recebimento", "Latitude Geográfica",
    "Longitude Geográfica", "CNAE Principal/ID", "CNAE Principal/Nome", "CNAE Secundário/ID",
    "CNAE Secundário/Nome",
]

IDIOMA = "pt_BR"
PAIS = "Brasil"
CONTA_PAGAMENTO = "2.1.1.01 Fornecedor"
CONTA_RECEBIMENTO = "1.1.2.01 Clientes"
CNAE_TEXT_LIMIT = 75  # o Odoo trunca o texto exibido do CNAE e termina com "..."

# Ajuste (chave do YAML) -> coluna do CSV. Só estas colunas aceitam ajuste.
ADJUSTABLE = {
    "vendedor": "Vendedor",
    "industria_principal": "Indústria principal",
    "industrias_secundarias": "Indústrias Secundárias",
    "telefone": "Telefone",
    "email": "E-mail",
    "site": "Site",
    "latitude": "Latitude Geográfica",
    "longitude": "Longitude Geográfica",
}

UF_NAMES = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais",
    "PA": "Pará", "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul",
    "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo",
    "SE": "Sergipe", "TO": "Tocantins",
}


class ContatosError(Exception):
    """Falha que impede a exportação (mensagem para o usuário)."""


@dataclass
class Resultado:
    rows: list[list[str]]
    avisos: list[str] = field(default_factory=list)
    contatos: int = 0


# ---------------------------------------------------------------- normalizações


def mask_cnpj(cnpj: str) -> str:
    d = only_digits(cnpj)
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"


def format_phone(value: str | None) -> str:
    d = only_digits(value or "")
    if len(d) == 11:
        return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    if len(d) == 10:
        return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    return (value or "").strip()


def format_cep(value: str | None) -> str:
    d = only_digits(value or "")
    return f"{d[:5]}-{d[5:]}" if len(d) == 8 else (value or "")


def format_state(uf: str | None) -> str:
    uf = (uf or "").upper()
    return f"{UF_NAMES[uf]} (BR)" if uf in UF_NAMES else ""


def format_cnae_code(code: Any) -> str:
    d = str(code or "").zfill(7)
    return f"{d[:4]}-{d[4]}/{d[5:]}"


def cnae_id(code: Any) -> str:
    return f"l10n_br_fiscal.cnae_{str(code).zfill(7)}"


def cnae_text(code: Any, name: str) -> str:
    text = f"{format_cnae_code(code)} - {name}"
    if len(text) > CNAE_TEXT_LIMIT:
        text = text[: CNAE_TEXT_LIMIT - 3] + "..."
    return text


def format_natureza(code: Any, name: str | None) -> str:
    d = str(code or "").zfill(4)
    if not code or not name:
        return ""
    return f"{d[:3]}-{d[3]} - {name}"


def perfil_fiscal(cadastro: dict) -> str:
    if cadastro.get("opcao_pelo_simples") or cadastro.get("opcao_pelo_mei"):
        return "Contribuinte Simples Nacional"
    return ""


def _title(value: str | None) -> str:
    return (value or "").strip().title()


def _address(cadastro: dict) -> str:
    street = " ".join(
        p for p in (cadastro.get("descricao_tipo_de_logradouro"), cadastro.get("logradouro")) if p
    )
    number = (cadastro.get("numero") or "").strip()
    if number.upper() in ("S/N", "SN"):
        number = "S/N"
    return ", ".join(p for p in (_title(street), number) if p)


# ---------------------------------------------------------------- leitura do raw.json


def find_latest_run(reports_dir: Path, client_id: str) -> Path:
    pattern = re.compile(rf"^\d{{4}}-\d{{2}}-\d{{2}}_\d{{6}}-{re.escape(client_id)}$")
    runs = sorted(p for p in Path(reports_dir).glob("*") if p.is_dir() and pattern.match(p.name))
    if not runs:
        raise ContatosError(f"Nenhuma execução de '{client_id}' em {reports_dir}.")
    return runs[-1]


def _source(raw: dict, tipo: str) -> dict | None:
    return next((s for s in raw.get("fontes", []) if s.get("tipo") == tipo), None)


def establishments(raw: dict, avisos: list[str]) -> list[dict]:
    """Matriz e filiais com seus dados cadastrais completos: ``{cnpj, tipo, cadastro}``."""
    cnpj_src = _source(raw, "cnpj")
    if not cnpj_src or cnpj_src.get("status") != OK or not cnpj_src.get("conteudo"):
        motivo = (cnpj_src or {}).get("erro") or "fonte de CNPJ ausente"
        raise ContatosError(f"A fonte 'cnpj' da execução não está ok: {motivo}")
    known = only_digits(cnpj_src["conteudo"]["cnpj"])
    known_data = cnpj_src["conteudo"]["dados"]
    known_tipo = {1: "matriz", 2: "filial"}.get(known_data.get("identificador_matriz_filial"), "")
    found = {known: {"cnpj": known, "tipo": known_tipo, "cadastro": known_data}}

    fil_src = _source(raw, "filiais")
    usable = fil_src and fil_src.get("conteudo") and fil_src["conteudo"].get("estabelecimentos")
    if not usable:
        avisos.append("Fonte de filiais ausente ou não coletada: o CSV contém só o estabelecimento "
                      "informado.")
    else:
        if fil_src.get("status") != OK:
            avisos.append(f"Fonte de filiais parcial ({fil_src.get('erro')}): pode faltar filial.")
        for est in fil_src["conteudo"]["estabelecimentos"]:
            cnpj = only_digits(est["cnpj"])
            if cnpj == known:
                continue
            if not est.get("cadastro"):
                avisos.append(f"Filial {mask_cnpj(cnpj)} sem dados cadastrais completos "
                              "(execução antiga): não incluída.")
                continue
            found[cnpj] = {"cnpj": cnpj, "tipo": est.get("tipo", ""), "cadastro": est["cadastro"]}
    return sorted(found.values(), key=lambda e: (e["tipo"] != "matriz", e["cnpj"]))


# ---------------------------------------------------------------- ajustes


def find_latest_ajustes(out_dir: Path) -> Path | None:
    files = sorted(Path(out_dir).glob("contatos-ajustes-*.yaml"))
    return files[-1] if files else None


def load_ajustes(path: Path, avisos: list[str]) -> dict[str, dict[str, str]]:
    """Ajustes válidos: ``{cnpj_digitos: {coluna: valor}}``; o restante é ignorado com aviso."""
    try:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise ContatosError(f"Arquivo de ajustes ilegível ({path}): {exc}") from exc
    if not isinstance(data, dict):
        raise ContatosError(f"Arquivo de ajustes inválido ({path}): esperado um mapa por CNPJ.")
    result: dict[str, dict[str, str]] = {}
    for cnpj, campos in data.items():
        digits = only_digits(str(cnpj))
        if not isinstance(campos, dict):
            avisos.append(f"Ajuste de {cnpj} ignorado: formato inválido.")
            continue
        for campo, item in campos.items():
            if campo not in ADJUSTABLE:
                avisos.append(f"Ajuste '{campo}' de {cnpj} ignorado: coluna não ajustável.")
                continue
            valor = item.get("valor") if isinstance(item, dict) else None
            fonte = item.get("fonte") if isinstance(item, dict) else None
            if valor in (None, "") or not fonte:
                avisos.append(f"Ajuste '{campo}' de {cnpj} ignorado: falta valor ou fonte.")
                continue
            result.setdefault(digits, {})[ADJUSTABLE[campo]] = str(valor)
    return result


# ---------------------------------------------------------------- montagem do CSV


def _contact_rows(est: dict, site: str, overrides: dict[str, str]) -> list[list[str]]:
    cad = est["cadastro"]
    principal = cad.get("cnae_fiscal")
    secundarios = [c for c in (cad.get("cnaes_secundarios") or []) if c.get("codigo")]
    cap = cad.get("capital_social")

    main = dict.fromkeys(COLUMNS, "")
    main.update({
        "Razão Social": _title(cad.get("razao_social")),
        "ID do Imposto": mask_cnpj(est["cnpj"]),
        "Endereço": _address(cad),
        "Cidade": _title(cad.get("municipio")),
        "Estado": format_state(cad.get("uf")),
        "CEP": format_cep(cad.get("cep")),
        "País": PAIS,
        "Telefone": format_phone(cad.get("ddd_telefone_1")),
        "E-mail": (cad.get("email") or "").strip().lower(),
        "Site": site if est["tipo"] == "matriz" else "",
        "Idioma": IDIOMA,
        "Perfil Fiscal do Parceiro": perfil_fiscal(cad),
        "Natureza Jurídica": format_natureza(
            cad.get("codigo_natureza_juridica"), cad.get("natureza_juridica")),
        "Capital Social": "" if cap is None else str(float(cap)),
        "Conta de Pagamento": CONTA_PAGAMENTO,
        "Conta de Recebimento": CONTA_RECEBIMENTO,
    })
    if principal:
        main["CNAE Principal"] = cnae_text(principal, cad.get("cnae_fiscal_descricao") or "")
        main["CNAE Principal/ID"] = cnae_id(principal)
        main["CNAE Principal/Nome"] = cad.get("cnae_fiscal_descricao") or ""
    main.update(overrides)

    rows = []
    for index in range(max(1, len(secundarios))):
        row = main if index == 0 else dict.fromkeys(COLUMNS, "")
        if index < len(secundarios):
            cnae = secundarios[index]
            row["CNAE Secundário"] = cnae_text(cnae["codigo"], cnae.get("descricao") or "")
            row["CNAE Secundário/ID"] = cnae_id(cnae["codigo"])
            row["CNAE Secundário/Nome"] = cnae.get("descricao") or ""
        rows.append([row[c] for c in COLUMNS])
    return rows


def build_rows(raw: dict, ajustes: dict[str, dict[str, str]] | None = None) -> Resultado:
    avisos: list[str] = []
    ests = establishments(raw, avisos)
    site = (raw.get("cliente") or {}).get("site") or ""
    ajustes = ajustes or {}
    rows: list[list[str]] = []
    for est in ests:
        rows += _contact_rows(est, site, ajustes.get(est["cnpj"], {}))
    for cnpj in ajustes:
        if cnpj not in {e["cnpj"] for e in ests}:
            avisos.append(f"Ajuste para {mask_cnpj(cnpj)} ignorado: CNPJ não está no CSV.")
    return Resultado(rows=rows, avisos=avisos, contatos=len(ests))


def render_csv(rows: list[list[str]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_ALL, lineterminator="\n")
    writer.writerow(COLUMNS)
    writer.writerows(rows)
    return buffer.getvalue()


def write_contatos(out_dir: Path, rows: list[list[str]], now: datetime) -> Path:
    """Grava ``contatos-<carimbo>.csv`` sem sobrescrever: avança o carimbo se já existir."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    while True:
        path = out_dir / f"contatos-{now.strftime(TIMESTAMP_FORMAT)}.csv"
        if not path.exists():
            break
        now += timedelta(seconds=1)
    path.write_text(render_csv(rows), encoding="utf-8")
    return path


def export(
    run_path: Path, out_dir: Path, ajustes_path: Path | None = None, now: datetime | None = None
) -> tuple[Path, Resultado]:
    raw_file = Path(run_path) / "raw.json"
    try:
        raw = json.loads(raw_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContatosError(f"raw.json ilegível em {run_path}: {exc}") from exc
    avisos: list[str] = []
    ajustes = load_ajustes(ajustes_path, avisos) if ajustes_path else None
    result = build_rows(raw, ajustes)
    result.avisos = avisos + result.avisos
    return write_contatos(out_dir, result.rows, now or datetime.now()), result
