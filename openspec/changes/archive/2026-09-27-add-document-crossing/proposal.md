## Why

Conforme as reuniões acontecem, surgem atas, transcrições, documentos e desenhos de fluxo do cliente. Hoje a skill parte só do que a web mostrou, então as hipóteses do relatório (fato, provável, palpite) e o roteiro de perguntas não se atualizam com o que o cliente diz. Cruzar esse material com o scraping fecha o ciclo: confirma ou corrige hipóteses, responde o roteiro e recalcula escopo, dimensionamento e riscos com dados reais.

## What Changes

- **Pasta de documentos internos por cliente:** `discovery/<cliente>/docs-internos/`, fora do git (herda `discovery/`), com arquivos imutáveis e nome sugerido `AAAA-MM-DD-<tipo>-<assunto>.<ext>`. Formatos: `.md`, `.txt`, PDF, `.docx`, imagens (`.png`, `.jpg`) e, se aparecerem, `.xlsx`.
- **Novo modo da skill `/discovery <cliente> --cruzar`:** lê os documentos, o relatório mais recente (ou o último cruzamento, para encadear) e o roteiro, e grava um **novo documento** `discovery/<cliente>/cruzamento-<AAAA-MM-DD_HHMMSS>.md`, sem alterar o relatório, o roteiro, os documentos nem os dados brutos.
- **Conteúdo do cruzamento:** hipóteses atualizadas (antes e depois, com a nova confiança), roteiro respondido, contradições entre o scraping e os documentos, impacto no escopo de módulos, no dimensionamento e nos riscos, e novas lacunas e perguntas.
- **Rastreabilidade:** cada afirmação cita o arquivo e o trecho ou a página. O conteúdo lido de imagens é marcado como interpretação, por poder estar errado.
- Sem alteração de código Python: a mudança é na skill, nas specs e na estrutura de pastas.

## Capabilities

### New Capabilities
<!-- Nenhuma: estende a capacidade existente da skill. -->

### Modified Capabilities
- `discovery-skill`: pasta de documentos internos, modo de cruzamento e o documento de cruzamento.

## Impact

- Skill: `.claude/skills/discovery/` e o espelho em `.opencode/`.
- Estrutura: nova subpasta `docs-internos/` por cliente, dentro de `discovery/<cliente>/`.
- Dependências: nenhuma nova. Leitura via `pdftotext`, `pandoc` e LibreOffice (já instalados nesta máquina) e leitura direta de imagens pelo Claude.
- Docs: `README.md` e `CLAUDE.md`.
