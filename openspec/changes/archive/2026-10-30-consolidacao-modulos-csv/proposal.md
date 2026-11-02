## Why

Os reports de discovery (scraping-*.md) já propõem módulos Odoo estruturados em tabelas por fase. Atualmente, para analisar e comparar propostas de módulos entre clientes, precisa-se ler manualmente cada discovery ou exportar as tabelas. Uma consolidação automática em CSV unifica todos os módulos propostos de todos os clientes em um arquivo, destravando análises de escopo, portfolio de módulos, estimativas de horas e comparação entre projetos.

## What Changes

- **Novo comando CLI**: `uv run discovery consolidar-modulos` que consolida módulos Odoo propostos de todos os descobertas em um CSV único
  - Suporta filtro por cliente: `--client <id>`
  - Suporta saída customizada: `--output <arquivo>`
  - Automático: lê `discovery/*/scraping-*.md` e mapeia horas via `referencia/horas.csv`
- **Novo módulo Python**: `src/discovery/consolidar.py` com funções de consolidação
- **Novo script standalone**: `scripts/consolidar-modulos.py` para uso direto sem CLI
- **Integração com CLI existente**: subcomando `consolidar-modulos` adicionado ao `discovery` argparse
- **CSV com 7 colunas**: cliente, modulo, enterprise, fase, evidencia, complexidade, horas_padrao
  - Estima automaticamente complexidade baseada em palavras-chave na evidência
  - Mapeia horas padrão pela régua `referencia/horas.csv` e fallback manual

## Capabilities

### New Capabilities

- `consolidacao-modulos`: Consolidar módulos Odoo propostos de múltiplos descobertas em um CSV único, com mapeamento de horas padrão e estimativa de complexidade

### Modified Capabilities

- (nenhuma)

## Impact

**Código afetado**:
- CLI: `src/discovery/cli.py` (novo subcomando)
- Novo módulo: `src/discovery/consolidar.py`
- Novo script: `scripts/consolidar-modulos.py`

**APIs**:
- Função pública: `consolidar_modulos(discovery_dir, referencia_file, client_filter, output_file)` → `(output_file, module_count)`
- CLI: `discovery consolidar-modulos [--client <id>] [--output <file>]`

**Dependências**:
- Nenhuma nova (usa stdlib csv, pathlib, datetime, re; existentes no projeto)

**Sistemas**:
- Lê: `discovery/*/scraping-*.md` (glob), `referencia/horas.csv`
- Escreve: CSV consolidado em current dir (padrão) ou arquivo customizado

**Casos de uso destravados**:
- Análise de escopo: quais módulos propostos aparecem mais frequentemente?
- Portfolio: mapeamento de módulos Enterprise vs Community por cliente
- Estimativa: total de horas padrão por cliente/fase
- Comparação: quais módulos há em comum entre clientes?
