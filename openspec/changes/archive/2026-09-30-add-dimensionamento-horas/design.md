## Context

A skill `discovery` é só instruções (`SKILL.md`), sem código Python; o cruzamento (etapa 3) já encadeia hipóteses com "nível anterior → nível novo". As tabelas de horas originais estão em `tabelasHoras/` (3 CSVs: módulos, integrações, atividades gerais; local, fora do git), com problemas conhecidos: `data_migration_ldm` duplicado, `aggrement`, `vertical-rental` e `Req_Est` fora do padrão de código. Ver proposal.md para a motivação.

A escala de fator é provisória e ainda não foi calibrada com dados reais de cotação; a calibração fica para depois, com uma base neutra.

## Goals / Non-Goals

**Goals:**
- Dar ao cruzamento e à proposta uma régua de horas rastreável, com o julgamento do consultor (fator) separado do dado padrão.
- Permitir que fatores mudem na negociação sem perder o histórico.

**Non-Goals:**
- Preço por hora e valores em R$.
- Alterar horas ao gerar `referencia/horas.csv` (só formato) ou criar código Python para lê-lo.
- Definir critérios escritos por nível de complexidade (fica para depois da negociação).

## Decisions

- **Só instruções na skill, sem código.** A skill lê os CSVs com Read/`cat`, como já faz com outros formatos. Alternativa: um comando `discovery horas` em Python; rejeitado por ora porque o cálculo é uma multiplicação e a skill já interpreta o resto. Reavaliar se a régua crescer.
- **Régua versionada em `referencia/horas.csv`, gerada dos originais.** Um CSV único (`tipo,codigo,nome,categoria,horas_padrao`), sem a descrição longa, com códigos únicos e padronizados. A limpeza é só de formato: nenhuma hora muda. Assim todo clone tem a régua e a manutenção passa a ter histórico no git. Alternativas: manter os 3 CSVs locais (clone novo fica sem régua) ou versionar os originais com os erros (aviso permanente). O original em `tabelasHoras/` continua local e a skill não o lê.
- **Casar por código, com o nome como reserva.** Mesmo com o código único, o nome cobre itens que o escopo cita sem código. A skill avisa divergências, não corrige o arquivo.
- **Escala discreta 1.0/1.5/2.0/2.5/3.0, provisória.** Serve como ponto de partida para a negociação; fator fora da escala é aceito e marcado. Alternativa: fator livre; rejeitada por ser difícil de defender e de comparar entre clientes.
- **Encadeamento igual ao das hipóteses.** Tabela com "fator anterior" e "fator novo" e a fonte da mudança, partindo do cruzamento mais recente. Reaproveita o padrão que o consultor já conhece, e a ata da negociação vira a fonte natural.
- **Calibração por cliente.** A escala 1.0-3.0 é um ponto de partida; os fatores de cada item são definidos e revisados cliente a cliente, na negociação, com a ata como fonte (fator anterior/novo no cruzamento). Não há calibração global nesta change.
- **Itens fora da régua em bloco separado, com [inferência].** Evita misturar estimativa própria no subtotal da régua.
- **Proposta consome o cruzamento.** A proposta é um "outro material estruturado" e não recalcula; uma única fonte de verdade evita divergência entre cruzamento e proposta.
- **Dois arquivos de skill.** `.claude/skills/discovery/SKILL.md` e `.opencode/skills/discovery/SKILL.md` recebem a mesma edição.

## Risks / Trade-offs

- [Escala sem calibração com dados reais] → rótulo "provisória", revisão após a negociação e calibração posterior com base neutra.
- [CSVs com erros geram casamento errado] → aviso da skill e casamento por nome; correção dos arquivos fica com o dono da régua.
- [Horas padrão passam a estar no git] → decisão do usuário: só as horas padrão por item sobem; descrições, fatores e cotações de clientes continuam fora (fatores ficam no cruzamento, em `discovery/`, gitignored). O original em `tabelasHoras/` continua local.
- [Correção de códigos pode divergir da intenção original] → a lista de códigos renomeados é confirmada com o usuário antes de gravar o arquivo (ver tasks).
- [Sem valores em R$, a proposta é menos completa] → intencional; a taxa entra em uma change futura.
