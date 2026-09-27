## Purpose

Coletar informações públicas sobre uma empresa cliente (site oficial, cadastro de CNPJ e buscas na web) e gravá-las como dados brutos rastreáveis por execução, sem interpretá-las, para serem estruturadas em uma etapa posterior e reutilizáveis para qualquer cliente.

## ADDED Requirements

### Requirement: Comando de varredura parametrizado por cliente
O sistema SHALL oferecer o comando `discovery scan` que recebe as informações do cliente (nome, site oficial, CNPJ opcional e queries de busca) por parâmetros de linha de comando ou por um arquivo de configuração do cliente, sem depender de valores fixos de nenhum cliente específico.

#### Scenario: Execução por arquivo de configuração
- **WHEN** o usuário executa `discovery scan --client haix` e existe `clients/haix.yaml`
- **THEN** o sistema usa nome, site, CNPJ e queries definidos nesse arquivo

#### Scenario: Execução por parâmetros
- **WHEN** o usuário executa `discovery scan --name "Cliente X" --site https://exemplo.com.br`
- **THEN** o sistema realiza a varredura sem exigir arquivo de configuração

#### Scenario: Cliente sem site informado
- **WHEN** o usuário executa o comando sem site nem configuração de cliente
- **THEN** o sistema encerra com erro e mensagem indicando os parâmetros obrigatórios

### Requirement: Varredura do site oficial
O sistema SHALL visitar a página inicial do site oficial e as páginas internas relevantes do mesmo domínio (como institucional, serviços, contato, política de privacidade e termos), e registrar título, URL e texto de cada página visitada.

#### Scenario: Site acessível
- **WHEN** o site oficial responde com sucesso
- **THEN** os dados brutos incluem as páginas visitadas com URL, título e texto extraído

#### Scenario: Site inacessível
- **WHEN** o site oficial não responde ou retorna erro
- **THEN** o sistema registra a falha nos dados brutos e continua com as demais fontes

#### Scenario: Limite ao domínio do cliente
- **WHEN** uma página do site contém links para outros domínios
- **THEN** o sistema não visita esses links durante a varredura do site oficial

### Requirement: Obtenção e consulta do CNPJ
O sistema SHALL usar o CNPJ informado pelo usuário ou, na ausência dele, procurar um CNPJ válido no texto das páginas do site, e consultar os dados cadastrais (razão social, CNAE, porte, sócios, endereço) por API pública HTTP, sem uso de navegador.

#### Scenario: CNPJ informado
- **WHEN** o usuário informa `--cnpj`
- **THEN** o sistema consulta a API com esse valor e não procura CNPJ no site

#### Scenario: CNPJ encontrado no site
- **WHEN** nenhum CNPJ foi informado e o texto de uma página contém um CNPJ válido
- **THEN** o sistema usa esse CNPJ e registra nos dados brutos a página onde foi encontrado

#### Scenario: Vários CNPJs válidos no site
- **WHEN** nenhum CNPJ foi informado e o site contém mais de um CNPJ válido (por exemplo de parceiros ou do grupo econômico)
- **THEN** o sistema registra todos os CNPJs encontrados com a página de origem e a quantidade de ocorrências de cada um, sinaliza a ambiguidade e não consulta a API automaticamente com um deles

#### Scenario: CNPJ não encontrado
- **WHEN** nenhum CNPJ foi informado nem encontrado no site
- **THEN** os dados brutos indicam que a fonte cadastral não pôde ser consultada e a execução termina com sucesso

#### Scenario: API de CNPJ indisponível
- **WHEN** a consulta à API falha ou retorna erro
- **THEN** o sistema registra a falha na fonte cadastral e continua com as demais fontes

### Requirement: Buscas complementares na web
O sistema SHALL executar buscas na web a partir das queries configuradas para o cliente (o padrão é o nome do cliente entre aspas; o arquivo do cliente pode acrescentar outras), usando buscadores que não exigem chave nem conta, em ordem de tentativa, e registrar título, URL de destino, trecho e o buscador usado para cada resultado. As queries padrão SHALL usar o nome do cliente entre aspas.

#### Scenario: Queries configuradas
- **WHEN** o cliente possui queries definidas
- **THEN** os dados brutos listam os resultados de cada query separadamente, com o buscador que os retornou

#### Scenario: Primeiro buscador bloqueado
- **WHEN** o primeiro buscador bloqueia a requisição, exibe CAPTCHA ou falha
- **THEN** o sistema tenta o próximo buscador da ordem e registra qual deles respondeu

#### Scenario: Resultados sem relação com o cliente
- **WHEN** um buscador responde, mas nenhum resultado cita o cliente (respostas aleatórias de buscadores automatizados)
- **THEN** o sistema descarta esses resultados, tenta novamente ou passa ao próximo buscador e nunca os grava como resultados da query

#### Scenario: Todos os buscadores indisponíveis
- **WHEN** todos os buscadores bloqueiam ou falham para uma query
- **THEN** o sistema registra a query como não concluída e continua com as demais

#### Scenario: Queries padrão
- **WHEN** o cliente não define queries
- **THEN** a query padrão é o nome do cliente entre aspas

### Requirement: Notícias por feed
O sistema SHALL consultar um feed público de notícias com o nome do cliente, sem navegador e sem chave, e registrar título, URL, data e veículo de cada notícia encontrada.

#### Scenario: Notícias encontradas
- **WHEN** o feed retorna itens para o nome do cliente
- **THEN** os dados brutos listam cada notícia com título, URL, data e veículo

#### Scenario: Nenhuma notícia
- **WHEN** o feed responde sem itens
- **THEN** a fonte é registrada como coletada com lista vazia, sem erro

#### Scenario: Feed indisponível
- **WHEN** a consulta ao feed falha
- **THEN** o sistema registra a falha da fonte e continua com as demais

### Requirement: Dados brutos por execução
O sistema SHALL gravar cada execução em uma pasta própria `reports/<AAAA-MM-DD_HHMMSS>-<cliente>/` contendo `raw.json` (dados organizados por fonte, com URL, conteúdo coletado, momento da coleta e falhas) e `raw.md` (o mesmo conteúdo em texto legível para conferência), sem interpretar nem resumir o conteúdo coletado.

#### Scenario: Execução concluída
- **WHEN** a varredura termina
- **THEN** a pasta da execução existe com `raw.json` e `raw.md`, mesmo que alguma fonte tenha falhado

#### Scenario: Várias execuções no mesmo dia
- **WHEN** o mesmo cliente é varrido mais de uma vez no mesmo dia
- **THEN** cada execução gera uma pasta distinta, sem sobrescrever execuções anteriores

#### Scenario: Pasta de saída inexistente
- **WHEN** a pasta `reports/` não existe
- **THEN** o sistema a cria antes de gravar a execução

#### Scenario: Rastreabilidade das fontes
- **WHEN** um conteúdo é gravado nos dados brutos
- **THEN** a fonte (URL ou API) e o momento da coleta desse conteúdo estão indicados

#### Scenario: Reuso sem nova coleta
- **WHEN** uma execução já existe em `reports/`
- **THEN** seus dados brutos permanecem inalterados e podem ser lidos por etapas posteriores sem executar nova coleta

### Requirement: Restrição a fontes públicas
O sistema SHALL acessar somente páginas e APIs públicas, sem autenticação, e SHALL NOT coletar dados do LinkedIn nem de outras fontes que exijam login.

#### Scenario: Fonte que exige login
- **WHEN** uma página acessada redireciona para uma tela de login
- **THEN** o sistema descarta o conteúdo e registra a fonte como não coletada
