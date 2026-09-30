"""Interface de linha de comando: ``discovery scan``."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

from discovery.collectors.cnpj import collect_cnpj
from discovery.collectors.filiais import collect_filiais
from discovery.collectors.news import collect_news
from discovery.collectors.search import collect_searches
from discovery.collectors.site import collect_site
from discovery.collectors.sitemap import collect_sitemap
from discovery.collectors.tecnologia import collect_tecnologia
from discovery.config import ConfigError, load_config
from discovery.contatos import ContatosError, export, find_latest_ajustes, find_latest_run
from discovery.models import OK
from discovery.storage import write_run


# O UA padrão do Chromium headless ("HeadlessChrome") faz os buscadores devolverem
# resultados aleatórios; um UA de Chrome comum evita isso.
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="discovery", description="Discovery web de clientes.")
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan", help="Coleta dados públicos e grava os dados brutos.")
    scan.add_argument("--client", help="id do cliente (clients/<id>.yaml)")
    scan.add_argument("--name", help="nome do cliente")
    scan.add_argument("--site", help="site oficial do cliente")
    scan.add_argument("--cnpj", help="CNPJ do cliente (evita a busca no site)")
    scan.add_argument("--query", action="append", help="query de busca (repetível; {name} = nome)")
    scan.add_argument("--max-pages", type=int, help="máximo de páginas do site")
    scan.add_argument("--clients-dir", type=Path, default=Path("clients"))
    scan.add_argument("--reports-dir", type=Path, default=Path("reports"))
    scan.add_argument("--dry-run", action="store_true", help="só resolve a configuração e sai")
    contatos = sub.add_parser(
        "contatos", help="Gera o CSV de contatos (res.partner) para importar no Odoo.")
    contatos.add_argument("--client", required=True, help="id do cliente")
    contatos.add_argument("--run", type=Path, help="pasta da execução (padrão: a mais recente)")
    contatos.add_argument("--ajustes", type=Path,
                          help="arquivo de ajustes (padrão: o contatos-ajustes-*.yaml mais recente)")
    contatos.add_argument("--reports-dir", type=Path, default=Path("reports"))
    contatos.add_argument("--out-dir", type=Path, default=Path("discovery"),
                          help="pasta base dos materiais (saída em <out-dir>/<cliente>/)")
    return parser


def run_contatos(args: argparse.Namespace) -> int:
    out_dir = args.out_dir / args.client
    try:
        run = args.run or find_latest_run(args.reports_dir, args.client)
        ajustes = args.ajustes or find_latest_ajustes(out_dir)
        path, result = export(run, out_dir, ajustes)
    except ContatosError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    for aviso in result.avisos:
        print(f"Aviso: {aviso}", file=sys.stderr)
    print(f"{path} ({result.contatos} contatos; base: {run}; "
          f"ajustes: {ajustes if ajustes else 'nenhum'})")
    return 0


def run_scan(args: argparse.Namespace) -> int:
    try:
        config = load_config(
            client=args.client, name=args.name, site=args.site, cnpj=args.cnpj,
            queries=args.query, max_pages=args.max_pages, clients_dir=args.clients_dir,
        )
    except ConfigError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2

    if args.dry_run:
        print(f"cliente={config.id} nome={config.name!r} site={config.site} "
              f"cnpj={config.cnpj} max_pages={config.max_pages}")
        for query in config.queries:
            print(f"query: {query}")
        return 0

    started = datetime.now()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(locale="pt-BR", user_agent=USER_AGENT)
        try:
            print(f"Varrendo site {config.site} ...", file=sys.stderr)
            sources = collect_site(context, config.site, config.max_pages)
            print("Lendo sitemap ...", file=sys.stderr)
            sources.append(collect_sitemap(config.site))
            print("Detectando tecnologias ...", file=sys.stderr)
            sources.append(collect_tecnologia(context, config.site))
            print("Consultando CNPJ ...", file=sys.stderr)
            cnpj_source = collect_cnpj(config.cnpj, sources)
            sources.append(cnpj_source)
            print("Consultando filiais ...", file=sys.stderr)
            sources.append(collect_filiais(cnpj_source))
            print(f"Executando {len(config.queries)} buscas ...", file=sys.stderr)
            sources += collect_searches(context, config.queries, keyword=config.name.split()[0])
            print("Buscando notícias ...", file=sys.stderr)
            sources.append(collect_news(config.name))
        finally:
            browser.close()

    path = write_run(
        args.reports_dir,
        {"id": config.id, "name": config.name, "site": config.site},
        {"cnpj": config.cnpj, "queries": config.queries, "max_pages": config.max_pages},
        sources, started, datetime.now(),
    )
    ok = sum(s.status == OK for s in sources)
    print(f"{path} ({ok}/{len(sources)} fontes ok)")
    return 0


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    sys.exit(run_contatos(args) if args.command == "contatos" else run_scan(args))
