## Why

O dimensionamento do relatório e do cruzamento hoje é uma "faixa de esforço" sem números, e as propostas usam horas que são estimativas do consultor, sem régua. A Escodoo já mantém tabelas de horas padrão por módulo, integração e atividade geral (`tabelasHoras/`), mas elas não entram no fluxo. Agora que existe cruzamento encadeado e material de proposta, é o momento de ligar a régua a eles.

## What Changes

- Adicionar ao **documento de cruzamento** uma subseção de **dimensionamento em horas**, dentro do "Impacto no projeto": para cada módulo, integração e atividade geral do escopo, horas padrão × fator de complexidade = horas ajustadas, com o motivo do fator e a evidência.
- Fator de complexidade em **escala provisória** (1.0, 1.5, 2.0, 2.5, 3.0), sujeita à negociação. Sem evidência, o fator é 1.0.
- Fatores são **encadeados como as hipóteses**: a tabela mostra fator anterior e fator novo, e só muda com documento (ex.: ata da negociação) ou informação do usuário marcada como **[informado por você]**.
- Itens do escopo **sem linha na régua** entram à parte, "fora da régua", com horas marcadas **[inferência]** e subtotal separado.
- Totais por fase e geral em três colunas: padrão, ajustado e fora da régua. **Sem valores em R$** nesta etapa.
- Itens com fator acima de 1.0 são listados como **pauta de negociação**.
- O material de **proposta** passa a partir da última tabela de horas do cruzamento, sem recalcular.
- Criar `referencia/horas.csv`, **versionado no git**: as três tabelas de `tabelasHoras/` unificadas em um só arquivo e limpas (só formato: códigos únicos e padronizados, mesmas horas), para que todo clone tenha a régua. É a fonte que a skill lê e reporta divergências (código sem correspondência).
- Skill atualizada em `.claude/skills/discovery/` e espelhada em `.opencode/skills/discovery/`.

## Capabilities

### New Capabilities
- `dimensionamento-horas`: régua de horas padrão (`referencia/horas.csv`), escala de fator de complexidade, cálculo das horas ajustadas, itens fora da régua, totais e encadeamento dos fatores entre cruzamentos.

### Modified Capabilities
- `discovery-skill`: o requisito "Conteúdo do documento de cruzamento" ganha a subseção de horas, e o material de proposta passa a partir dela.

## Impact

- `.claude/skills/discovery/SKILL.md` e o espelho em `.opencode/skills/discovery/SKILL.md` (mesmo conteúdo nos dois).
- `referencia/horas.csv` (novo, versionado): dependência da skill.
- `tabelasHoras/*.csv`: continua como original **só local**, adicionada ao `.gitignore`; não é lida pela skill.
- Nenhum código Python em `src/discovery/` muda (a skill não tem código).
- Fora de escopo: preço por hora e valores em R$; revisar valores de horas (a limpeza não altera nenhuma hora).
