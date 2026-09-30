# dimensionamento-horas Specification

## Purpose

Define como a skill de discovery transforma as tabelas de horas padrão da Escodoo em um dimensionamento em horas do projeto, com fator de complexidade rastreável e revisável ao longo das negociações, sem valores em R$.

## Requirements

### Requirement: Régua de horas padrão
A skill SHALL usar como régua de horas padrão o arquivo versionado `referencia/horas.csv`, que reúne módulos, integrações e atividades gerais em um só arquivo com as colunas `tipo`, `codigo`, `nome`, `categoria` e `horas_padrao`, com código único por linha. A skill SHALL casar cada item do escopo pelo código e, na falta dele, pelo nome, e SHALL reportar problemas encontrados na régua (código duplicado, arquivo ausente ou ilegível) sem alterar o arquivo e sem interromper o dimensionamento.

#### Scenario: Item do escopo presente na régua
- **WHEN** um módulo, integração ou atividade do escopo tem linha na régua
- **THEN** o dimensionamento usa as horas padrão dessa linha

#### Scenario: Régua ausente ou ilegível
- **WHEN** `referencia/horas.csv` não existe ou não pode ser lido
- **THEN** a skill informa a falta, dimensiona tratando todos os itens como fora da régua e não grava horas padrão inventadas

#### Scenario: Código duplicado na régua
- **WHEN** um código aparece em mais de uma linha da régua
- **THEN** a skill casa pelo nome, avisa a duplicidade e não altera o arquivo

### Requirement: Fator de complexidade em escala provisória
O dimensionamento SHALL aplicar a cada item da régua um fator de complexidade escolhido da escala 1.0, 1.5, 2.0, 2.5 e 3.0, e SHALL calcular as horas ajustadas como horas padrão multiplicadas pelo fator. Todo fator acima de 1.0 SHALL vir com a justificativa e a evidência (arquivo e trecho, ou **[informado por você]**); sem evidência o fator SHALL ser 1.0. A escala SHALL ser apresentada como provisória e sujeita a mudança na negociação.

#### Scenario: Fator com evidência
- **WHEN** um documento sustenta que um módulo é mais complexo que o padrão
- **THEN** a linha mostra horas padrão, fator, horas ajustadas, o motivo e a fonte

#### Scenario: Fator sem evidência
- **WHEN** não há documento nem informação do usuário que justifique complexidade maior
- **THEN** o fator do item é 1.0 e as horas ajustadas são iguais às padrão

#### Scenario: Fator fora da escala
- **WHEN** o consultor pede um fator que não está na escala
- **THEN** a skill aceita, registra como **[informado por você]** e marca a linha como fora da escala provisória

### Requirement: Fatores encadeados entre cruzamentos
A tabela de horas SHALL mostrar, para cada item, o fator anterior e o fator novo, e SHALL partir dos fatores do cruzamento mais recente, quando existir. Um fator SHALL mudar somente por documento (por exemplo a ata de uma reunião de negociação) ou por informação do usuário marcada como **[informado por você]**, citando a fonte da mudança.

#### Scenario: Primeiro dimensionamento
- **WHEN** não existe cruzamento anterior com tabela de horas
- **THEN** o fator anterior de cada item consta como inexistente e o fator novo é o definido agora

#### Scenario: Fator alterado na negociação
- **WHEN** uma ata em `docs-internos/` registra que o fator de um item mudou
- **THEN** o novo cruzamento mostra o fator anterior, o novo e cita a ata e o trecho, e o cruzamento anterior permanece intacto

### Requirement: Itens fora da régua
Itens do escopo sem linha na régua SHALL constar em bloco à parte, "fora da régua", com horas estimadas marcadas como **[inferência]**, com a base da estimativa, e com subtotal separado do subtotal da régua.

#### Scenario: Item sem correspondência
- **WHEN** um item do escopo (por exemplo custos de importação ou operações intercompany) não existe na régua
- **THEN** ele aparece em "fora da régua" com horas **[inferência]** e a base da estimativa, e não entra no subtotal da régua

### Requirement: Totais e pauta de negociação
O dimensionamento SHALL apresentar totais por fase e geral em três colunas (horas padrão, horas ajustadas e fora da régua), sem qualquer valor em R$, e SHALL listar como pauta de negociação os itens com fator acima de 1.0.

#### Scenario: Totais por fase
- **WHEN** o escopo está dividido em fases
- **THEN** a tabela traz o total de cada fase e o total geral nas três colunas

#### Scenario: Pauta de negociação
- **WHEN** existem itens com fator acima de 1.0
- **THEN** o documento lista esses itens com o fator e o motivo como pauta a debater

#### Scenario: Sem valores monetários
- **WHEN** o dimensionamento é gerado
- **THEN** nenhuma tabela ou total contém preço por hora ou valor em R$
