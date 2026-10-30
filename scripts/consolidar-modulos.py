#!/usr/bin/env python3
"""
Consolidar módulos Odoo propostos de todos os discoveries em um CSV único.

Uso:
  python3 scripts/consolidar-modulos.py [--output <arquivo>] [--client <cliente>]

Exemplos:
  python3 scripts/consolidar-modulos.py
    → Consolida todos os clientes em descoberta-modulos-consolidado-<timestamp>.csv

  python3 scripts/consolidar-modulos.py --client haix
    → Consolida apenas haix

Saída:
  cliente,modulo,enterprise,fase,evidencia,complexidade,horas_padrao
"""

import re
import sys
import argparse
import csv
from pathlib import Path
from datetime import datetime


def load_horas_padrao():
    """Carrega tabela de horas padrão de referencia/horas.csv"""
    horas_map = {}
    horas_file = Path('referencia/horas.csv')

    if not horas_file.exists():
        print("⚠️  referencia/horas.csv não encontrado. Horas padrão vazias.", file=sys.stderr)
        return horas_map

    try:
        with open(horas_file, 'r', encoding='utf-8') as f:
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
        print(f"⚠️  Erro lendo referencia/horas.csv: {e}", file=sys.stderr)

    return horas_map


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


def get_horas(modulo_name, horas_map):
    """Busca horas padrão para um módulo"""
    clean_name = modulo_name.lower().replace('**', '').replace('(e)', '').strip()

    # Busca exata no mapa
    if clean_name in horas_map:
        return horas_map[clean_name]

    # Busca por substring
    for key, val in horas_map.items():
        if key and (key in clean_name or clean_name in key):
            return val

    # Fallback manual
    for key, val in HORAS_FALLBACK.items():
        if key in clean_name or clean_name in key:
            return val

    return ''


def estimate_complexity(evidencia):
    """Estima complexidade do módulo baseado na evidência"""
    evidencia_lower = evidencia.lower()

    if any(w in evidencia_lower for w in ['múltiplos', 'complexa', 'advanced', 'integração com', 'migração', 'alta']):
        return 'Alta'
    elif any(w in evidencia_lower for w in ['simples', 'básica', 'baixa']):
        return 'Baixa'

    return 'Média'


def extract_modules_from_discovery(scraping_file, horas_map):
    """Extrai módulos Odoo de um arquivo scraping-*.md"""
    modules = []
    cliente = scraping_file.parent.name

    try:
        content = scraping_file.read_text(encoding='utf-8')
    except Exception as e:
        print(f"⚠️  Erro lendo {scraping_file}: {e}", file=sys.stderr)
        return modules

    # Extrair fases e tabelas de módulos
    fases = re.findall(
        r'### (Fase \d+[^|]*?)\n\n\| Módulo \| Por que \|(.*?)(?=###|## [^#]|\Z)',
        content,
        re.DOTALL
    )

    seen = set()

    for fase_header, table_content in fases:
        fase = fase_header.replace('**', '').strip()

        # Parse linhas da tabela
        rows = table_content.strip().split('\n')
        for row in rows:
            if not row.startswith('|') or 'Módulo' in row or '---' in row:
                continue

            cells = [c.strip() for c in row.split('|')[1:-1]]
            if len(cells) < 2:
                continue

            modulo_raw = cells[0]
            evidencia = cells[1] if len(cells) > 1 else ''

            # Limpar formatação markdown
            is_enterprise = '(E)' in modulo_raw
            modulo = re.sub(r'\*\*|\(E\)', '', modulo_raw).strip()
            evidencia = re.sub(r'\*\*', '', evidencia).strip()

            # Evitar duplicatas
            key = (cliente, modulo, fase)
            if key in seen:
                continue
            seen.add(key)

            # Montar resultado
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


def main():
    parser = argparse.ArgumentParser(
        description='Consolidar módulos Odoo de todos os discoveries em um CSV'
    )
    parser.add_argument(
        '--output', '-o',
        help='Arquivo de saída (padrão: descoberta-modulos-consolidado-<timestamp>.csv)'
    )
    parser.add_argument(
        '--client', '-c',
        help='Consolidar apenas um cliente (padrão: todos)'
    )

    args = parser.parse_args()

    # Carregar tabela de horas
    horas_map = load_horas_padrao()

    # Encontrar todos os scraping-*.md
    scraping_files = sorted(Path('discovery').glob('*/scraping-*.md'))

    if not scraping_files:
        print("❌ Nenhum discovery encontrado em discovery/*/scraping-*.md", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(scraping_files)} discovery reports")

    # Extrair módulos
    all_modules = []
    for scraping_file in scraping_files:
        cliente = scraping_file.parent.name

        # Filtrar por cliente se especificado
        if args.client and cliente != args.client:
            continue

        modules = extract_modules_from_discovery(scraping_file, horas_map)
        all_modules.extend(modules)
        print(f"  {cliente}: {len(modules)} módulos")

    if not all_modules:
        print("❌ Nenhum módulo foi extraído", file=sys.stderr)
        sys.exit(1)

    # Sort
    all_modules.sort(key=lambda x: (x['cliente'], x['fase']))

    # Escrever CSV
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    output_file = args.output or f'descoberta-modulos-consolidado-{timestamp}.csv'

    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['cliente', 'modulo', 'enterprise', 'fase', 'evidencia', 'complexidade', 'horas_padrao']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_modules)

        print(f"\n✅ CSV gerado: {output_file}")
        print(f"Total de módulos: {len(all_modules)}")

        # Estatísticas
        clientes_unicos = set(m['cliente'] for m in all_modules)
        print(f"Clientes: {len(clientes_unicos)}")

        enterprise_count = len([m for m in all_modules if m['enterprise'] == 'Sim'])
        print(f"Enterprise (E): {enterprise_count}")
        print(f"Community: {len(all_modules) - enterprise_count}")

        # Distribuição por complexidade
        print(f"\nDistribuição por complexidade:")
        for comp in ['Baixa', 'Média', 'Alta']:
            count = len([m for m in all_modules if m['complexidade'] == comp])
            if count > 0:
                print(f"  {comp}: {count}")

    except Exception as e:
        print(f"❌ Erro escrevendo {output_file}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
