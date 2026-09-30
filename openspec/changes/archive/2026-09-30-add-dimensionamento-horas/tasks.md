## 1. Skill

- [x] 1.1 Em `.claude/skills/discovery/SKILL.md`, adicionar a subseção "Dimensionamento em horas" na seção "Seções do documento de cruzamento" (régua em `referencia/horas.csv`, escala 1.0-3.0 provisória, fator anterior/novo, fora da régua, totais, pauta de negociação, sem R$); verificar com `grep -n "fora da régua" .claude/skills/discovery/SKILL.md`
- [x] 1.2 Acrescentar às "Regras do cruzamento" que fator só muda com documento ou **[informado por você]** e que problemas na régua são reportados sem alterar os CSVs; verificar relendo a seção
- [x] 1.3 Em "Outros materiais estruturados", registrar que proposta/cotação parte da tabela de horas do cruzamento mais recente, sem recalcular e sem R$, e que sem tabela a skill oferece `--cruzar`; verificar relendo a seção
- [x] 1.4 Atualizar a descrição do front matter da skill para citar o dimensionamento em horas; verificar que a linha `description:` menciona horas
- [x] 1.5 Espelhar a edição em `.opencode/skills/discovery/SKILL.md`; verificar com `diff .claude/skills/discovery/SKILL.md .opencode/skills/discovery/SKILL.md` sem saída

## 2. Régua e documentação

- [x] 2.1 Propor ao usuário a lista de códigos a padronizar (`data_migration_ldm` duplicado, `aggrement`, `vertical-rental`, `Req_Est`) e aguardar confirmação; verificar com a confirmação registrada na conversa
- [x] 2.2 Gerar `referencia/horas.csv` a partir de `tabelasHoras/*.csv` (colunas `tipo,codigo,nome,categoria,horas_padrao`, sem descrição, códigos únicos); verificar que o número de linhas bate com a soma dos originais e que nenhuma hora difere (comparação por nome)
- [x] 2.3 Adicionar `tabelasHoras/` ao `.gitignore` (original só local, decisão do usuário) e garantir que `referencia/horas.csv` não é ignorado; verificar com `git check-ignore tabelasHoras` (ignorado) e `git check-ignore referencia/horas.csv` (sem saída)
- [x] 2.4 Atualizar `CLAUDE.md` (estrutura de pastas e etapa 3) citando `referencia/horas.csv` como régua versionada, `tabelasHoras/` como original local e a tabela de horas do cruzamento; verificar que o texto descreve o novo fluxo

## 3. Validação

- [x] 3.1 Em um cruzamento real futuro (`/discovery <cliente> --cruzar`), verificar que o novo `cruzamento-*.md` traz a tabela de horas, os itens fora da régua e os totais, sem R$
- [x] 3.2 Registrar no `design.md` que a calibração dos fatores é feita cliente a cliente, na negociação, e não nesta change; verificar que a nota existe em Decisions
- [x] 3.3 Rodar `openspec validate add-dimensionamento-horas` e verificar que passa
