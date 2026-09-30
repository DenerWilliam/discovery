## Why

O discovery já levanta os dados cadastrais do cliente e de suas filiais, mas a Escodoo precisa cadastrá-los à mão no Odoo (`res.partner`, com `l10n_br_fiscal`). Um CSV pronto para importação, gerado durante o processo, elimina a digitação e leva para o Odoo o que a reunião descobrir (vendedor, indústria).

## What Changes

- Novo subcomando `discovery contatos` que lê o `raw.json` de uma execução e grava um único CSV de importação de contatos do cliente (matriz e filiais), com as colunas, a ordem e os nomes exatos da exportação do Odoo (modelo em `contatoexemplo/`).
- Formato Odoo de um contato por linha principal, com linhas extras contendo só o CNAE secundário.
- Coluna derivada dos dados públicos (razão social, CNPJ, endereço, contato, natureza jurídica, regime fiscal, CNAEs, capital); constantes no código (idioma, país, contas); vazias quando só a reunião sabe (vendedor, indústria, coordenadas).
- Arquivo de ajustes `contatos-ajustes-<carimbo>.yaml`, escrito pela skill `/discovery --cruzar` a partir de `docs-internos/`, com a fonte de cada valor; o subcomando o lê junto com o `raw.json` e grava um novo CSV, sem nunca alterar o anterior.
- A coleta de `filiais` passa a guardar, por estabelecimento, os dados cadastrais completos necessários ao CSV (hoje guarda só um resumo). **BREAKING** só para o conteúdo de `filiais` em `raw.json`: campos são acrescentados e o `versao_formato` é incrementado; nenhum campo existente é removido.

## Capabilities

### New Capabilities
- `contatos-import`: geração do CSV de contatos no formato de importação do Odoo a partir do `raw.json`, e aplicação do arquivo de ajustes.

### Modified Capabilities
- `web-discovery`: a fonte de estabelecimentos da mesma raiz de CNPJ passa a registrar os dados cadastrais completos de cada estabelecimento.
- `discovery-skill`: o modo `--cruzar` passa a gravar o arquivo de ajustes de contatos quando as atas sustentam valores explícitos.

## Impact

- Código: novo módulo de exportação e registro do subcomando em `src/discovery/cli.py`; ampliação de `collectors/filiais.py` e do `FORMAT_VERSION` em `models.py`.
- Skill: `.claude/skills/discovery/` e `.opencode/skills/discovery/` (manter idênticas).
- Saídas novas em `discovery/<cliente>/` (gitignorado): `contatos-*.csv` e `contatos-ajustes-*.yaml`.
- Sem novas dependências (CSV e YAML já cobertos por `csv` e PyYAML).
- Execuções antigas, sem os dados completos das filiais, continuam legíveis; o CSV delas sai só com a matriz e avisa da limitação.
