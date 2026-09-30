# discovery-skill Specification

## Purpose

Fornecer uma skill que estrutura os dados brutos de uma execução de garimpo em um relatório voltado para o planejamento de um projeto Odoo, podendo ser repetida sobre a mesma coleta sem nova varredura na web.

## Requirements

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

### Requirement: Hipóteses com nível de confiança
O relatório SHALL conter uma seção de hipóteses em que cada afirmação relevante do relatório é classificada como fato (comprovado por dado coletado), provável (inferência sustentada por evidência) ou palpite (inferência sem evidência direta), com a fonte ou o raciocínio que a sustenta.

#### Scenario: Classificação por confiança
- **WHEN** o relatório é gerado
- **THEN** cada hipótese indica seu nível de confiança e a evidência ou o raciocínio

#### Scenario: Informação dada pelo usuário
- **WHEN** uma informação foi passada pelo usuário na conversa
- **THEN** ela aparece marcada como informada pelo usuário, e não como fato coletado

### Requirement: Priorização do roteiro por confiança
O roteiro de reunião SHALL priorizar perguntas que validem as hipóteses de menor confiança e as lacunas mais críticas, colocando-as no início de seus blocos e indicando a hipótese ou lacuna que cada uma valida.

#### Scenario: Pergunta ligada a hipótese fraca
- **WHEN** existe uma hipótese classificada como palpite ou provável
- **THEN** o roteiro contém uma pergunta marcada como validação dessa hipótese

### Requirement: Dimensionamento preliminar
O relatório SHALL conter um dimensionamento preliminar do projeto com estimativa de usuários, complexidade por módulo proposto (baixa, média ou alta) e faixa de esforço por fase, explicitando as premissas usadas e que se trata de estimativa inicial a validar, e não de orçamento.

#### Scenario: Estimativa com premissas
- **WHEN** o dimensionamento é apresentado
- **THEN** cada estimativa lista as premissas e os dados que a sustentam, e as lacunas que a tornam incerta

#### Scenario: Dados insuficientes
- **WHEN** faltam dados essenciais para estimar (por exemplo número de funcionários)
- **THEN** o relatório declara a lacuna e apresenta a faixa como condicional, sem inventar o dado

### Requirement: Riscos do projeto
O relatório SHALL conter uma seção de riscos do projeto (por exemplo migração de dados, regras fiscais, integrações e dependência de sistemas legados) com probabilidade, impacto e mitigação proposta, ligados às evidências do negócio.

#### Scenario: Risco ligado a evidência
- **WHEN** um risco é listado
- **THEN** ele indica a evidência ou a lacuna que o motivou e a mitigação proposta

### Requirement: Uso das novas fontes na estruturação
A skill SHALL usar as fontes de sitemap, tecnologia e estabelecimentos, quando presentes nos dados brutos, para embasar o relatório (tamanho do catálogo, plataforma e ferramentas, número e localização das unidades), citando a fonte de cada dado.

#### Scenario: Fonte de tecnologia presente
- **WHEN** os dados brutos contêm tecnologias detectadas
- **THEN** a seção de sistemas e tecnologia cita as detecções com a evidência

#### Scenario: Fonte ausente ou com falha
- **WHEN** uma das novas fontes não foi coletada
- **THEN** o relatório a lista como lacuna e não presume o dado

### Requirement: Pasta de documentos internos por cliente
O sistema SHALL reservar `discovery/<cliente>/docs-internos/` para os documentos que surgem ao longo das reuniões (atas, transcrições, planilhas, fluxos, e-mails e propostas), fora do controle de versão, e a skill SHALL tratar esses arquivos como imutáveis, sem alterá-los nem apagá-los.

#### Scenario: Documentos fora do git
- **WHEN** um arquivo é colocado em `discovery/<cliente>/docs-internos/`
- **THEN** ele é ignorado pelo controle de versão

#### Scenario: Documentos preservados
- **WHEN** a skill lê ou cruza os documentos
- **THEN** nenhum arquivo de `docs-internos/` é modificado, movido ou removido

### Requirement: Cruzamento de documentos com o scraping
A skill SHALL oferecer o modo `/discovery <cliente> --cruzar`, que lê os documentos de `docs-internos/`, o relatório de scraping mais recente (ou o cruzamento mais recente, quando existir, para encadear as revisões) e o roteiro de reunião, e grava um novo arquivo `discovery/<cliente>/cruzamento-<AAAA-MM-DD_HHMMSS>.md`, sem alterar o relatório, o roteiro, os documentos nem os dados brutos.

#### Scenario: Primeiro cruzamento
- **WHEN** existem documentos e um relatório do cliente e o usuário executa `--cruzar`
- **THEN** a skill grava `cruzamento-<carimbo>.md` usando o relatório como base, e nenhum arquivo existente é alterado

#### Scenario: Cruzamento encadeado
- **WHEN** já existe um cruzamento anterior e o usuário executa `--cruzar` de novo
- **THEN** o novo cruzamento parte do estado das hipóteses do cruzamento mais recente e um novo arquivo é gravado, preservando os anteriores

#### Scenario: Sem documentos
- **WHEN** `docs-internos/` não existe ou está vazia
- **THEN** a skill informa isso e não grava cruzamento

#### Scenario: Sem relatório
- **WHEN** não existe relatório de scraping do cliente
- **THEN** a skill informa e oferece estruturar uma coleta antes de cruzar

### Requirement: Leitura de documentos por formato
A skill SHALL ler documentos em texto (`.md`, `.txt`), PDF, `.docx`, planilhas e imagens (`.png`, `.jpg`), convertendo cada formato para texto quando necessário e interpretando as imagens visualmente, e SHALL listar como não lido qualquer arquivo ilegível ou de formato desconhecido, sem interromper o cruzamento.

#### Scenario: Formatos suportados
- **WHEN** a pasta contém arquivos em texto, PDF, `.docx` e imagem
- **THEN** a skill usa o conteúdo de todos eles no cruzamento

#### Scenario: Arquivo não lido
- **WHEN** um arquivo não pode ser lido ou tem formato desconhecido
- **THEN** ele é listado na seção de arquivos não lidos, com o motivo, e o cruzamento continua com os demais

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

### Requirement: Rastreabilidade e interpretação de imagens
Toda afirmação do cruzamento SHALL citar o arquivo de origem e o trecho ou a página, e o conteúdo obtido de imagens SHALL ser marcado como interpretação de imagem a ser conferida.

#### Scenario: Afirmação com fonte
- **WHEN** o cruzamento apresenta uma informação vinda de um documento
- **THEN** ele indica o arquivo e o trecho ou a página

#### Scenario: Fluxo desenhado em imagem
- **WHEN** a informação vem de um desenho de fluxo em imagem
- **THEN** ela é descrita em texto e marcada como interpretação de imagem, com a indicação de conferir com o cliente

### Requirement: Nomenclatura geral de materiais estruturados
Todo material que a skill estruturar para um cliente, além do relatório, do roteiro e do cruzamento já especificados, SHALL seguir o padrão `discovery/<cliente>/<tipo-descritivo>-<AAAA-MM-DD_HHMMSS>.md`, com `<tipo-descritivo>` livre e sem lista fechada de tipos, SHALL ser imutável (uma versão nova é sempre um arquivo novo, nunca uma sobrescrita) e SHALL citar no topo a base de que partiu (relatório, cruzamento ou outro material anterior).

#### Scenario: Material novo com carimbo e base citada
- **WHEN** a skill estrutura um material que não é o relatório, o roteiro nem o cruzamento (por exemplo, uma cotação complementar)
- **THEN** o arquivo é gravado em `discovery/<cliente>/` com carimbo de data e hora no nome e cita no topo o documento em que se baseou

#### Scenario: Nova versão do mesmo material
- **WHEN** o usuário pede uma nova versão de um material já estruturado antes
- **THEN** um novo arquivo com carimbo distinto é gravado, e a versão anterior é preservada

#### Scenario: Evolução visível no histórico
- **WHEN** vários materiais de um cliente existem em `discovery/<cliente>/`
- **THEN** os nomes dos arquivos, ordenados, mostram a ordem cronológica em que foram produzidos

### Requirement: Proposta parte da tabela de horas do cruzamento
Quando o usuário pedir um material de proposta ou cotação, a skill SHALL partir da tabela de horas do cruzamento mais recente, sem recalcular horas nem fatores, e SHALL citar esse cruzamento como base. Sem cruzamento com tabela de horas, a skill SHALL informar e oferecer executar `--cruzar` antes. O material não SHALL conter valores em R$ enquanto a taxa horária não fizer parte do fluxo.

#### Scenario: Proposta com cruzamento disponível
- **WHEN** existe um cruzamento com tabela de horas e o usuário pede a proposta
- **THEN** o material replica horas padrão, fator e horas ajustadas desse cruzamento e cita-o no topo

#### Scenario: Proposta sem tabela de horas
- **WHEN** não existe cruzamento com tabela de horas
- **THEN** a skill informa a falta, oferece rodar `--cruzar` e não grava a proposta
