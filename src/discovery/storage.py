"""Gravação dos dados brutos de uma execução em ``reports/<carimbo>-<cliente>/``."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from discovery.models import FORMAT_VERSION, OK, Source

TIMESTAMP_FORMAT = "%Y-%m-%d_%H%M%S"


def run_dir(reports_dir: Path, client_id: str, now: datetime) -> Path:
    """Pasta nova da execução; avança o carimbo se já existir, sem sobrescrever."""
    while True:
        path = Path(reports_dir) / f"{now.strftime(TIMESTAMP_FORMAT)}-{client_id}"
        if not path.exists():
            return path
        now += timedelta(seconds=1)


def _render_source_md(source: Source) -> str:
    lines = [
        f"### [{source.tipo}] {source.origem}",
        f"- status: {source.status}",
        f"- coletado_em: {source.coletado_em}",
    ]
    if source.erro:
        lines.append(f"- erro: {source.erro}")
    content = source.conteudo
    if source.tipo == "site" and source.status == OK and content:
        lines += ["", f"**{content['titulo']}**", "", content["texto"]]
    elif source.tipo == "busca" and content:
        lines += ["", f"query: `{content['query']}` (motor: {content.get('motor', '-')})"]
        for item in content.get("resultados", []):
            lines.append(f"- [{item['titulo']}]({item['url']}) — {item['trecho']}")
    elif source.tipo == "noticias" and content:
        lines += ["", f"query: `{content['query']}` (motor: {content.get('motor', '-')}; "
                      f"descartados por não citar o cliente: {content.get('descartados', 0)})"]
        for item in content.get("itens", []):
            lines.append(f"- [{item['titulo']}]({item['url']}) — {item['veiculo']}, {item['data']}")
    elif source.tipo == "sitemap" and content:
        lines += ["", f"total de URLs: {content['total_urls']} (sitemaps lidos: {len(content['sitemaps_lidos'])})", "",
                  "por seção: " + ", ".join(f"`{k}`={v}" for k, v in content["por_secao"].items())]
        if content["por_sufixo"]:
            lines.append("por sufixo: " + ", ".join(f"`{k}`={v}" for k, v in content["por_sufixo"].items()))
        lines += ["", "amostra:"] + [f"- {u}" for u in content["amostra"]]
    elif source.tipo == "tecnologia" and content:
        if not content["detectadas"]:
            lines += ["", "nenhuma tecnologia conhecida detectada"]
        for tech in content["detectadas"]:
            lines.append(f"- **{tech['nome']}** ({tech['categoria']}): {'; '.join(tech['evidencia'])}")
        lines += ["", "domínios contatados: " + ", ".join(content["dominios_contatados"])]
    elif source.tipo == "filiais" and content:
        lines += ["", f"raiz do CNPJ: {content['raiz']}"]
        for e in content["estabelecimentos"]:
            lines.append(f"- {e['cnpj']} ({e['tipo'] or '-'}): {e['municipio']}/{e['uf']}, "
                         f"{e['cnae_descricao']}, {e['situacao']}, início {e['inicio_atividade']}")
    elif content:
        lines += ["", "```json", json.dumps(content, ensure_ascii=False, indent=2), "```"]
    return "\n".join(lines)


def render_raw_md(meta: dict[str, Any], sources: list[Source]) -> str:
    lines = [
        f"# Dados brutos: {meta['cliente']['nome']}",
        "",
        f"- site: {meta['cliente']['site']}",
        f"- início: {meta['inicio']}",
        f"- fim: {meta['fim']}",
        f"- fontes: {len(sources)} ({sum(s.status == OK for s in sources)} ok)",
        "",
        "## Fontes",
    ]
    for source in sources:
        lines += ["", _render_source_md(source)]
    return "\n".join(lines) + "\n"


def write_run(
    reports_dir: Path,
    client: dict[str, Any],
    params: dict[str, Any],
    sources: list[Source],
    started: datetime,
    finished: datetime,
) -> Path:
    path = run_dir(reports_dir, client["id"], started)
    path.mkdir(parents=True)
    meta = {
        "versao_formato": FORMAT_VERSION,
        "cliente": {"id": client["id"], "nome": client["name"], "site": client["site"]},
        "parametros": params,
        "inicio": started.astimezone().isoformat(timespec="seconds"),
        "fim": finished.astimezone().isoformat(timespec="seconds"),
    }
    raw = {**meta, "fontes": [s.to_dict() for s in sources]}
    (path / "raw.json").write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    (path / "raw.md").write_text(render_raw_md(meta, sources), encoding="utf-8")
    return path
