## MODIFIED Requirements

### Requirement: Conteúdo do documento de cruzamento
O cruzamento SHALL conter: a lista de documentos considerados e não lidos; as hipóteses atualizadas, com o nível anterior, o nível novo (fato, provável ou palpite) e o documento que sustenta a mudança; as perguntas do roteiro respondidas pelos documentos e as que continuam em aberto; as contradições entre o scraping e os documentos; o impacto no escopo de módulos, no dimensionamento e nos riscos, sendo que o dimensionamento SHALL incluir a tabela de horas da capability `dimensionamento-horas`; e as novas lacunas e perguntas.

#### Scenario: Hipótese confirmada ou corrigida
- **WHEN** um documento confirma, contradiz ou esclarece uma hipótese
- **THEN** o cruzamento mostra a hipótese com o nível anterior e o novo, e cita o documento que a sustenta

#### Scenario: Pergunta respondida
- **WHEN** um documento responde uma pergunta do roteiro
- **THEN** o cruzamento registra a resposta com a fonte, e a pergunta deixa de constar como em aberto

#### Scenario: Contradição
- **WHEN** um documento diverge de um dado coletado na web
- **THEN** o cruzamento lista a divergência com as duas fontes, sem decidir qual está certa

#### Scenario: Impacto no projeto
- **WHEN** os documentos trazem dados que alteram o escopo, o dimensionamento ou os riscos (por exemplo o número real de usuários)
- **THEN** o cruzamento indica o que muda e a nova estimativa, com as premissas

#### Scenario: Tabela de horas no cruzamento
- **WHEN** a skill grava um cruzamento
- **THEN** a seção de dimensionamento traz a tabela de horas padrão, fator e horas ajustadas, os itens fora da régua, os totais e a pauta de negociação

## ADDED Requirements

### Requirement: Proposta parte da tabela de horas do cruzamento
Quando o usuário pedir um material de proposta ou cotação, a skill SHALL partir da tabela de horas do cruzamento mais recente, sem recalcular horas nem fatores, e SHALL citar esse cruzamento como base. Sem cruzamento com tabela de horas, a skill SHALL informar e oferecer executar `--cruzar` antes. O material não SHALL conter valores em R$ enquanto a taxa horária não fizer parte do fluxo.

#### Scenario: Proposta com cruzamento disponível
- **WHEN** existe um cruzamento com tabela de horas e o usuário pede a proposta
- **THEN** o material replica horas padrão, fator e horas ajustadas desse cruzamento e cita-o no topo

#### Scenario: Proposta sem tabela de horas
- **WHEN** não existe cruzamento com tabela de horas
- **THEN** a skill informa a falta, oferece rodar `--cruzar` e não grava a proposta
