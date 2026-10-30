"""Consolidar módulos Odoo propostos de todos os discoveries em um CSV único."""

from __future__ import annotations

import csv
import re
import sys
from datetime import datetime
from pathlib import Path


HORAS_FALLBACK = {
    'contatos': '40', 'clientes': '40',
    'vendas': '80', 'crm': '60',
    'ecommerce': '320', 'website': '200',
    'estoque': '160', 'compras': '80',
    'contabilidade': '200', 'faturamento': '200',
    'localização fiscal': '120',
    'pagamentos': '120',
    'marketplace': '240', 'seller portal': '240',
    'logística': '160', 'frota': '80',
    'assistência': '80', 'helpdesk': '80',
    'devolução': '80', 'troca': '80',
    'notificações': '60',
    'loja física': '100', 'pos': '100',
    'marketing automation': '160',
    'fidelidade': '120', 'programa de pontos': '120',
    'rh': '120', 'funcionários': '80',
    'aprovações': '60', 'conhecimento': '40',
    'dashboards': '100', 'analytics': '100',
}


def load_horas_padrao(referencia_file: Path) -> dict[str, str]:
    """Carrega tabela de horas padrão de referencia/horas.csv"""
    horas_map = {}

    if not referencia_file.exists():
        print(f"⚠️  {referencia_file} não encontrado. Usando fallback.", file=sys.stderr)
        return horas_map

    try:
        with open(referencia_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                codigo = (row.get('codigo', '') or '').strip().lower()
                nome = (row.get('nome', '') or '').strip().lower()
                horas = (row.get('horas_padrao', '') or '').strip()

                if codigo:
                    horas_map[codigo] = horas
                if nome:
                    horas_map[nome] = horas
    except Exception as e:
        print(f"⚠️  Erro lendo {referencia_file}: {e}", file=sys.stderr)

    return horas_map


def get_horas(modulo_name: str, horas_map: dict[str, str]) -> str:
    """Busca horas padrão para um módulo"""
    clean_name = modulo_name.lower().replace('**', '').replace('(e)', '').strip()

    if clean_name in horas_map:
        return horas_map[clean_name]

    for key, val in horas_map.items():
        if key and (key in clean_name or clean_name in key):
            return val

    for key, val in HORAS_FALLBACK.items():
        if key in clean_name or clean_name in key:
            return val

    return ''


def estimate_complexity(evidencia: str) -> str:
    """Estima complexidade do módulo baseado na evidência"""
    evidencia_lower = evidencia.lower()

    if any(w in evidencia_lower for w in ['múltiplos', 'complexa', 'advanced', 'integração com', 'migração', 'alta']):
        return 'Alta'
    elif any(w in evidencia_lower for w in ['simples', 'básica', 'baixa']):
        return 'Baixa'

    return 'Média'


def extract_modules_from_discovery(scraping_file: Path, horas_map: dict[str, str]) -> list[dict]:
    """Extrai módulos Odoo de um arquivo scraping-*.md"""
    modules = []
    cliente = scraping_file.parent.name

    try:
        content = scraping_file.read_text(encoding='utf-8')
    except Exception as e:
        print(f"⚠️  Erro lendo {scraping_file}: {e}", file=sys.stderr)
        return modules

    fases = re.findall(
        r'### (Fase \d+[^|]*?)\n\n\| Módulo \| Por que \|(.*?)(?=###|## [^#]|\Z)',
        content,
        re.DOTALL
    )

    seen = set()

    for fase_header, table_content in fases:
        fase = fase_header.replace('**', '').strip()

        rows = table_content.strip().split('\n')
        for row in rows:
            if not row.startswith('|') or 'Módulo' in row or '---' in row:
                continue

            cells = [c.strip() for c in row.split('|')[1:-1]]
            if len(cells) < 2:
                continue

            modulo_raw = cells[0]
            evidencia = cells[1] if len(cells) > 1 else ''

            is_enterprise = '(E)' in modulo_raw
            modulo = re.sub(r'\*\*|\(E\)', '', modulo_raw).strip()
            evidencia = re.sub(r'\*\*', '', evidencia).strip()

            key = (cliente, modulo, fase)
            if key in seen:
                continue
            seen.add(key)

            modules.append({
                'cliente': cliente,
                'modulo': modulo,
                'enterprise': 'Sim' if is_enterprise else 'Não',
                'fase': fase,
                'evidencia': evidencia[:80],
                'complexidade': estimate_complexity(evidencia),
                'horas_padrao': get_horas(modulo, horas_map)
            })

    return modules


def consolidar_modulos(discovery_dir: Path, referencia_file: Path,
                       client_filter: str | None = None,
                       output_file: str | None = None) -> tuple[str, int]:
    """Consolida módulos Odoo de todos os discoveries em um CSV.

    Returns:
        (output_file_path, module_count)
    """
    scraping_files = sorted(discovery_dir.glob('*/scraping-*.md'))

    if not scraping_files:
        raise ValueError(f"Nenhum discovery encontrado em {discovery_dir}/*/scraping-*.md")

    horas_map = load_horas_padrao(referencia_file)

    print(f"Found {len(scraping_files)} discovery reports")

    all_modules = []
    for scraping_file in scraping_files:
        cliente = scraping_file.parent.name

        if client_filter and cliente != client_filter:
            continue

        modules = extract_modules_from_discovery(scraping_file, horas_map)
        all_modules.extend(modules)
        print(f"  {cliente}: {len(modules)} módulos")

    if not all_modules:
        raise ValueError("Nenhum módulo foi extraído")

    all_modules.sort(key=lambda x: (x['cliente'], x['fase']))

    if output_file is None:
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        output_file = f'descoberta-modulos-consolidado-{timestamp}.csv'

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['cliente', 'modulo', 'enterprise', 'fase', 'evidencia', 'complexidade', 'horas_padrao']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_modules)

    return output_file, len(all_modules)
