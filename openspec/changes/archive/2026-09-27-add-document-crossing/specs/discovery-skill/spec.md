## ADDED Requirements

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
O cruzamento SHALL conter: a lista de documentos considerados e não lidos; as hipóteses atualizadas, com o nível anterior, o nível novo (fato, provável ou palpite) e o documento que sustenta a mudança; as perguntas do roteiro respondidas pelos documentos e as que continuam em aberto; as contradições entre o scraping e os documentos; o impacto no escopo de módulos, no dimensionamento e nos riscos; e as novas lacunas e perguntas.

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

### Requirement: Rastreabilidade e interpretação de imagens
Toda afirmação do cruzamento SHALL citar o arquivo de origem e o trecho ou a página, e o conteúdo obtido de imagens SHALL ser marcado como interpretação de imagem a ser conferida.

#### Scenario: Afirmação com fonte
- **WHEN** o cruzamento apresenta uma informação vinda de um documento
- **THEN** ele indica o arquivo e o trecho ou a página

#### Scenario: Fluxo desenhado em imagem
- **WHEN** a informação vem de um desenho de fluxo em imagem
- **THEN** ela é descrita em texto e marcada como interpretação de imagem, com a indicação de conferir com o cliente
