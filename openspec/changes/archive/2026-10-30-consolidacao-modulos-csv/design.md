## Context

A estrutura `discovery/*/scraping-*.md` contém tabelas de módulos Odoo propostos organizadas por fase (Fase 1, 2, 3). Cada célula contém `| Módulo | Por que |` com markdown (negrito, Enterprise flag `(E)`). Queremos consolidar estes dados sem tocar nos reports (leitura apenas) e sem parser HTML - apenas regex + string.

## Goals / Non-Goals

**Goals**:
- Consolidar 134+ módulos de 4+ clientes em um CSV consistente
- Suportar uso via CLI (`discovery consolidar-modulos`) e script standalone (`scripts/consolidar-modulos.py`)
- Mapear horas padrão e estimar complexidade automaticamente
- Permitir filtro por cliente
- Rodar offline, sem rede

**Non-Goals**:
- Validar correção das propostas de módulos (garbage in, garbage out OK)
- Editar ou atualizar descobertas originais
- Integração com spreadsheets/Google Sheets
- Revalidação de dados contra `web-discovery` ou `discovery-skill` specs

## Decisions

### Decision 1: Parsing via regex em vez de markdown parser

**Chosen**: Regex simples para extrair blocos de fase + tabelas

**Rationale**: 
- Tabelas markdown são simples: `| cell | cell |` com headers e separador `|---|---|`
- Regex é mais leve que importar `markdown` ou `mistune`
- Reporta bem falhas (nada encontrado vs. erro de parser)

**Alternatives**:
- Usar lib markdown (Mistune, Python-Markdown): overkill, mais dependências
- Manual line-by-line split: mais código, menos legível

**Regex usado**:
```python
r'### (Fase \d+[^|]*?)\n\n\| Módulo \| Por que \|(.*?)(?=###|## [^#]|\Z)'
```
Captura fase header + conteúdo da tabela até próxima seção/fim.

### Decision 2: Mapeamento de horas em três níveis (exato + substring + fallback)

**Chosen**: Hierarquia exato → substring → fallback manual dict

**Rationale**:
- Nível 1 (exato): rápido, trata nomes idênticos (`Contatos` → "40")
- Nível 2 (substring): flexível para variações (`Contatos e Clientes` → encontra `contatos`)
- Nível 3 (fallback): robusto quando régua ausente ou incompleta

**Alternativas**:
- Fuzzy matching (difflib): mais preciso mas mais lento, dependência extra
- Só fallback: perde mapping exato, muito genérico
- Error if not found: strict mas quebra em mudanças na régua

### Decision 3: Estimativa de complexidade por palavras-chave

**Chosen**: Busca case-insensitive em evidência por palavras ['múltiplos', 'complexa', 'integração com', 'migração']

**Rationale**:
- Veloz (string search)
- Captura intenção da evidência coletada (text que diz "complexa" = complexa)
- Sem ML/NN, determinístico

**Alternativa**:
- Consultar spec de cada módulo: complexo, fora de escopo

### Decision 4: CLI integration via subcomando argparse vs. script isolado

**Chosen**: Ambos (CLI + script). Lógica compartilhada em `src/discovery/consolidar.py`

**Rationale**:
- Usuários podem rodar `uv run discovery consolidar-modulos` (integrado)
- Ou `python3 scripts/consolidar-modulos.py` (standalone, útil em automação/CI)
- DRY: lógica uma só vez em módulo Python reutilizável

**Estrutura**:
- `src/discovery/consolidar.py`: função `consolidar_modulos()` + helpers
- `scripts/consolidar-modulos.py`: CLI argparse thin wrapper que chama função
- `src/discovery/cli.py`: integração com `discovery` main parser

## Risks / Trade-offs

| Risk | Impacto | Mitigação |
|------|---------|-----------|
| **Regex frágil se formato scraping mudar** | Alto | Manter spec de formato (requirements descrevem tabelas markdown com `\| Módulo \| Por que \|`) e atualizar regex se mudança ocorrer |
| **Régua `referencia/horas.csv` pode estar incompleta** | Médio | Fallback manual dict cobre 90% dos módulos; CSV final mostra campos vazios onde não mapeou |
| **Grandes discoveries (18k+ URLs no sitemap)** | Baixo | Não processamos sitemap neste comando, apenas scraping-*.md (10-20 KB típico) |
| **Unicode/encoding em evidência** | Baixo | Python 3.10+ trata UTF-8 bem; CSV module trata escaping de aspas/quebras |
| **Duplicação de clientes/módulos por período** | Baixo | Deduplicação por tupla `(cliente, modulo, fase)` evita linhas repetidas |

## Migration Plan

1. **Deploy**: Commit `src/discovery/consolidar.py`, `scripts/consolidar-modulos.py`, `cli.py` atualizado
2. **Testing**: Executar `uv run discovery consolidar-modulos` localmente e validar CSV
3. **Documentation**: Atualizar `CLAUDE.md` com comando (já feito)
4. **Rollback**: Deletar ficheiros novos e revert `cli.py` (nenhuma mudança de dados)

Não há mudança de estado, banco de dados ou formato existente - apenas leitura de scraping-*.md.

## Open Questions

Nenhuma bloqueante. Perguntas que podem ser respondidas sem mudar specs/design/tasks:
- **Q**: Qual é a escala esperada? (200 módulos? 10k?)  
  **A**: ~134 módulos atuais, mas escalável com novos clientes descobertos
- **Q**: Precisa de caching do CSV?  
  **A**: Não; cada execução é rápido (~100ms), sem I/O pesado
