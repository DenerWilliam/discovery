## Purpose

Fornecer uma skill que estrutura os dados brutos de uma execução de garimpo em um relatório voltado para o planejamento de um projeto Odoo, podendo ser repetida sobre a mesma coleta sem nova varredura na web.

## ADDED Requirements

### Requirement: Invocação da skill sobre uma execução
O sistema SHALL disponibilizar a skill `/discovery` que recebe o cliente e opera sobre uma execução existente em `reports/`, usando a mais recente do cliente por padrão ou a indicada pelo usuário.

#### Scenario: Estruturar a execução mais recente
- **WHEN** o usuário executa `/discovery haix` e existem execuções do cliente em `reports/`
- **THEN** a skill lê os dados brutos da execução mais recente sem executar nova coleta

#### Scenario: Estruturar uma execução específica
- **WHEN** o usuário indica uma execução (por exemplo pelo carimbo)
- **THEN** a skill usa os dados brutos dessa execução

#### Scenario: Nenhuma execução existente
- **WHEN** não há execução do cliente em `reports/`
- **THEN** a skill informa isso e oferece executar a coleta antes de estruturar

### Requirement: Coleta nova sob demanda
A skill SHALL executar `discovery scan` somente quando o usuário pedir uma coleta nova, solicitando os parâmetros faltantes (cliente, site) quando não houver configuração do cliente.

#### Scenario: Coleta nova pedida
- **WHEN** o usuário pede uma coleta nova informando cliente e site
- **THEN** a skill executa o CLI com esses parâmetros e depois estrutura a execução gerada

#### Scenario: Parâmetros ausentes na coleta nova
- **WHEN** o usuário pede coleta nova sem site e não existe configuração do cliente
- **THEN** a skill solicita as informações faltantes antes de executar o CLI

### Requirement: Relatório estruturado por estruturação
A skill SHALL gravar cada estruturação como um arquivo `discovery/<cliente>/scraping-<AAAA-MM-DD_HHMMSS>.md`, com o carimbo de data e hora da estruturação, fora da pasta `reports/` e sem alterar `raw.json` nem `raw.md`. O relatório SHALL indicar a execução de origem (pasta em `reports/`) e ter seções fixas (visão geral, dados cadastrais, modelo de negócio e serviços, sistemas e tecnologia citados, notícias e reputação, escopo de módulos Odoo, lacunas e fontes não concluídas, resumo das perguntas para o cliente).

#### Scenario: Primeira estruturação
- **WHEN** a skill conclui a estruturação de uma execução
- **THEN** existe `discovery/<cliente>/scraping-<carimbo>.md` com todas as seções fixas, citando a execução de origem, e os dados brutos permanecem inalterados

#### Scenario: Reestruturação da mesma execução
- **WHEN** o usuário pede uma nova estruturação da mesma execução
- **THEN** um novo arquivo `scraping-<carimbo>.md` com carimbo distinto é gravado em `discovery/<cliente>/` e os anteriores são preservados

### Requirement: Escopo de módulos Odoo
O relatório SHALL conter uma proposta fechada de módulos Odoo, definida pelo consultor e não escolhida pelo cliente, organizada em fases (núcleo operacional e fiscal; canais, produção e pós-venda; crescimento e gestão), com cada módulo ligado a uma evidência do negócio, uma lista separada de personalizações prováveis e o aviso de que edição (Community ou Enterprise) e versão devem ser confirmadas na proposta.

#### Scenario: Módulos ligados a evidências
- **WHEN** o relatório é gerado
- **THEN** cada módulo proposto indica o motivo com base em um dado coletado ou em uma inferência marcada como tal

#### Scenario: Módulo sem evidência
- **WHEN** um módulo comum não tem evidência nos dados brutos
- **THEN** ele só aparece se houver justificativa e é marcado como inferência

### Requirement: Roteiro de reunião
A skill SHALL gerar, por padrão, um roteiro de reunião com cerca de 60 perguntas em `discovery/<cliente>/reuniao-<AAAA-MM-DD_HHMMSS>.md`, organizadas em blocos temáticos, começando pelas lacunas e evidências do relatório e completando com temas padrão, marcando a origem de cada pergunta (dado coletado ou padrão), indicando o que a resposta destrava e oferecendo um campo de resposta por pergunta. O usuário SHALL poder dispensá-lo ou pedir só ele.

#### Scenario: Roteiro gerado junto com o relatório
- **WHEN** a skill estrutura uma execução sem `--sem-perguntas`
- **THEN** existe `reuniao-<carimbo>.md` com as perguntas numeradas, a origem de cada uma e um campo de resposta

#### Scenario: Perguntas guiadas pelos dados
- **WHEN** o relatório registra lacunas ou divergências (por exemplo ERP desconhecido ou datas conflitantes)
- **THEN** o roteiro inclui perguntas sobre elas, marcadas como originadas de dado coletado

#### Scenario: Sem roteiro
- **WHEN** o usuário pede `--sem-perguntas`
- **THEN** somente o relatório é gerado

### Requirement: Fidelidade aos dados coletados
A skill SHALL basear cada afirmação do relatório nos dados brutos, indicando a fonte, e SHALL declarar explicitamente as lacunas em vez de inventar informação.

#### Scenario: Síntese com evidências
- **WHEN** os dados brutos contêm informação suficiente
- **THEN** cada afirmação relevante do relatório referencia a fonte registrada

#### Scenario: Dados insuficientes
- **WHEN** os dados brutos não têm informação sobre um tema
- **THEN** o relatório declara a lacuna na seção correspondente e não a preenche com suposições

#### Scenario: Fontes com falha
- **WHEN** os dados brutos registram falhas em algumas fontes
- **THEN** o relatório é gerado com o que existe e lista as fontes que falharam

### Requirement: Disponibilidade nos dois ambientes
A skill SHALL existir em `.claude/` e em `.opencode/` com conteúdo consistente entre as duas cópias.

#### Scenario: Cópias consistentes
- **WHEN** a skill é adicionada ou alterada
- **THEN** as cópias em `.claude/` e `.opencode/` têm o mesmo comportamento descrito
