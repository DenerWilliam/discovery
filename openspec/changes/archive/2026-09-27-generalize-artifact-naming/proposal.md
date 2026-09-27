## Why

Conforme as agendas avançam, novos tipos de material surgem além do relatório, do roteiro e do cruzamento (por exemplo, uma cotação complementar já foi gerada ad hoc). O padrão de carimbo de data e hora, imutabilidade e citação da base, já usado nesses três artefatos, precisa valer para qualquer material novo, para dar visibilidade da evolução do cliente ao longo do tempo sem formalizar uma lista fechada de tipos.

## What Changes

- Regra geral na skill: todo material que a etapa 2/3 estruturar para um cliente, além dos três artefatos já especificados, segue `discovery/<cliente>/<tipo-descritivo>-<AAAA-MM-DD_HHMMSS>.md`, imutável (nunca sobrescreve), citando no topo a base de que partiu (relatório, cruzamento ou outro material anterior).
- `<tipo-descritivo>` é livre (por exemplo `cotacao-complementar`, `resumo-executivo`, `apresentacao`), sem lista fechada de tipos.
- Sem mudança de código Python; a regra é comportamento da skill.

## Capabilities

### New Capabilities
<!-- Nenhuma: estende a capacidade existente da skill. -->

### Modified Capabilities
- `discovery-skill`: regra geral de nomenclatura, imutabilidade e rastreabilidade para qualquer material novo estruturado para um cliente.

## Impact

- Skill: `.claude/skills/discovery/` e o espelho em `.opencode/`.
- Docs: `README.md` e `CLAUDE.md`.
