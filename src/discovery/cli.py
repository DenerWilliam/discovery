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
from discovery.consolidar import consolidar_modulos
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
    scan.add_argument("--locale", help="idioma da coleta (padrão pt-BR; ex.: en-US)")
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
    consolidar = sub.add_parser(
        "consolidar-modulos", help="Consolida módulos Odoo propostos de todos os discoveries em um CSV.")
    consolidar.add_argument("--client", help="consolidar apenas um cliente")
    consolidar.add_argument("--output", "-o", help="arquivo de saída (padrão: descoberta-modulos-consolidado-<timestamp>.csv)")
    consolidar.add_argument("--discovery-dir", type=Path, default=Path("discovery"),
                           help="pasta base dos discoveries")
    consolidar.add_argument("--referencia", type=Path, default=Path("referencia/horas.csv"),
                           help="arquivo de referência de horas")
    return parser


def run_consolidar_modulos(args: argparse.Namespace) -> int:
    try:
        output_file, count = consolidar_modulos(
            args.discovery_dir, args.referencia,
            client_filter=args.client, output_file=args.output
        )

        # Exibir estatísticas
        all_data = []
        with open(output_file) as f:
            import csv
            all_data = list(csv.DictReader(f))

        clientes = set(m['cliente'] for m in all_data)
        enterprise = len([m for m in all_data if m['enterprise'] == 'Sim'])

        print(f"{output_file} ({count} módulos; {len(clientes)} clientes)")
        print(f"  Enterprise: {enterprise}, Community: {count - enterprise}")

        return 0
    except (ValueError, OSError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1


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
            queries=args.query, max_pages=args.max_pages, locale=args.locale,
            clients_dir=args.clients_dir,
        )
    except ConfigError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2

    if args.dry_run:
        print(f"cliente={config.id} nome={config.name!r} site={config.site} "
              f"cnpj={config.cnpj} max_pages={config.max_pages} locale={config.locale}")
        for query in config.queries:
            print(f"query: {query}")
        return 0

    started = datetime.now()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(locale=config.locale, user_agent=USER_AGENT)
        try:
            print(f"Varrendo site {config.site} ...", file=sys.stderr)
            sources = collect_site(context, config.site, config.max_pages)
            arquivadas = [s for s in sources if (s.conteudo or {}).get("origem") == "arquivo"]
            if arquivadas:
                capturas = sorted({s.conteudo["captura"] for s in arquivadas})
                periodo = (f"capturas de {capturas[0]} a {capturas[-1]}" if len(capturas) > 1
                           else f"captura de {capturas[0]}")
                print(f"Aviso: site recusou o acesso; usando o arquivo público "
                      f"({len(arquivadas)} páginas; {periodo}).", file=sys.stderr)
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
            sources += collect_searches(context, config.queries,
                                        keyword=config.name.split()[0], locale=config.locale)
            print("Buscando notícias ...", file=sys.stderr)
            sources.append(collect_news(config.name, locale=config.locale))
        finally:
            browser.close()

    path = write_run(
        args.reports_dir,
        {"id": config.id, "name": config.name, "site": config.site},
        {"cnpj": config.cnpj, "queries": config.queries, "max_pages": config.max_pages,
         "locale": config.locale},
        sources, started, datetime.now(),
    )
    ok = sum(s.status == OK for s in sources)
    print(f"{path} ({ok}/{len(sources)} fontes ok)")
    for source in sources:
        if source.status == OK:
            continue
        detalhe = f" [{source.motivo}]" if source.motivo else ""
        print(f"  {source.tipo} {source.origem}: {source.erro}{detalhe}", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "contatos":
        sys.exit(run_contatos(args))
    elif args.command == "consolidar-modulos":
        sys.exit(run_consolidar_modulos(args))
    else:
        sys.exit(run_scan(args))
