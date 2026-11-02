## MODIFIED Requirements

### Requirement: Comando de varredura parametrizado por cliente
O sistema SHALL oferecer o comando `discovery scan` que recebe as informações do cliente (nome, site oficial, CNPJ opcional, queries de busca e idioma da coleta) por parâmetros de linha de comando ou por um arquivo de configuração do cliente, sem depender de valores fixos de nenhum cliente específico. O idioma da coleta SHALL ter padrão `pt-BR` e SHALL aceitar qualquer idioma no formato `ll-CC`.

#### Scenario: Execução por arquivo de configuração
- **WHEN** o usuário executa `discovery scan --client haix` e existe `clients/haix.yaml`
- **THEN** o sistema usa nome, site, CNPJ, idioma e queries definidos nesse arquivo

#### Scenario: Execução por parâmetros
- **WHEN** o usuário executa `discovery scan --name "Cliente X" --site https://exemplo.com.br`
- **THEN** o sistema realiza a varredura sem exigir arquivo de configuração

#### Scenario: Cliente sem site informado
- **WHEN** o usuário executa o comando sem site nem configuração de cliente
- **THEN** o sistema encerra com erro e mensagem indicando os parâmetros obrigatórios

#### Scenario: Idioma padrão
- **WHEN** o cliente não define idioma
- **THEN** a coleta usa `pt-BR` no navegador, nos buscadores e no feed de notícias

#### Scenario: Idioma diferente do português
- **WHEN** o cliente define `locale: en-US`
- **THEN** o navegador, o parâmetro de idioma dos buscadores e o feed de notícias usam inglês dos Estados Unidos

#### Scenario: Idioma inválido
- **WHEN** o cliente define um idioma que não segue o formato `ll-CC`
- **THEN** o sistema encerra com erro indicando o campo e o valor recebido

### Requirement: Varredura do site oficial
O sistema SHALL visitar a página inicial do site oficial e as páginas internas relevantes do mesmo domínio (como institucional, serviços, contato, política de privacidade e termos), em português e em inglês, e registrar título, URL e texto de cada página visitada. Links que respondem com um arquivo para download em vez de uma página SHALL ser registrados como não coletados, com o motivo indicado, e SHALL NOT contar para o limite de páginas da varredura. Quando o acesso ao site ao vivo for recusado de forma persistente, o sistema SHALL tentar a coleta pelo arquivo público antes de encerrar a fonte, conforme o requisito de coleta pelo arquivo público.

#### Scenario: Site acessível
- **WHEN** o site oficial responde com sucesso
- **THEN** os dados brutos incluem as páginas visitadas com URL, título e texto extraído

#### Scenario: Site inacessível
- **WHEN** o site oficial não responde ou retorna erro que não é recusa de acesso
- **THEN** o sistema registra a falha nos dados brutos e continua com as demais fontes

#### Scenario: Limite ao domínio do cliente
- **WHEN** uma página do site contém links para outros domínios
- **THEN** o sistema não visita esses links durante a varredura do site oficial

#### Scenario: Link que serve arquivo para download
- **WHEN** uma página do site contém um link que responde com um arquivo para download (por exemplo um relatório em PDF sem extensão na URL)
- **THEN** os dados brutos registram essa URL como fonte do site com status `nao_coletada` e o motivo "arquivo para download", sem ler o conteúdo do arquivo, e a varredura continua

#### Scenario: Downloads não consomem o limite de páginas
- **WHEN** a varredura encontra vários links de download antes de esgotar as páginas HTML relevantes
- **THEN** o limite de páginas é consumido apenas por páginas HTML, e as demais páginas relevantes ainda são visitadas até o limite

#### Scenario: Site que recusa o acesso e não tem captura pública
- **WHEN** o site recusa o acesso e o arquivo público não tem captura do domínio
- **THEN** a fonte é registrada como falha com o motivo de bloqueio e a execução continua

#### Scenario: Site em inglês
- **WHEN** o site está em inglês e publica páginas como "about", "services" e "contact"
- **THEN** essas páginas entram na varredura com a mesma prioridade que as equivalentes em português

### Requirement: Buscas complementares na web
O sistema SHALL executar buscas na web a partir das queries configuradas para o cliente (o padrão é o nome do cliente entre aspas; o arquivo do cliente pode acrescentar outras), usando buscadores que não exigem chave nem conta, em ordem de tentativa, e registrar título, URL de destino, trecho e o buscador usado para cada resultado. As queries padrão SHALL usar o nome do cliente entre aspas. O idioma dos resultados SHALL seguir o idioma de coleta do cliente.

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

#### Scenario: Resultados no idioma do cliente
- **WHEN** o cliente tem idioma de coleta `en-US`
- **THEN** os buscadores recebem o parâmetro de idioma correspondente e os resultados são registrados com o idioma usado

### Requirement: Notícias por feed
O sistema SHALL consultar um feed público de notícias com o nome do cliente, sem navegador e sem chave, no idioma de coleta do cliente, e registrar título, URL, data e veículo apenas das notícias que citam o cliente (nome completo, sem considerar maiúsculas e acentos), informando quantos itens foram descartados por não citá-lo.

#### Scenario: Notícias encontradas
- **WHEN** o feed retorna itens que citam o nome do cliente
- **THEN** os dados brutos listam cada notícia relevante com título, URL, data e veículo

#### Scenario: Notícias sem relação com o cliente
- **WHEN** o feed retorna itens, mas nenhum cita o nome do cliente
- **THEN** a fonte é registrada como coletada com lista vazia e a contagem de itens descartados, sem gravar esses itens

#### Scenario: Nenhuma notícia
- **WHEN** o feed responde sem itens
- **THEN** a fonte é registrada como coletada com lista vazia, sem erro

#### Scenario: Feed indisponível
- **WHEN** a consulta ao feed falha
- **THEN** o sistema registra a falha da fonte e continua com as demais

#### Scenario: Feed no idioma do cliente
- **WHEN** o cliente tem idioma de coleta `en-US`
- **THEN** o feed é consultado com os parâmetros de idioma e região dos Estados Unidos, e a fonte registra o idioma usado

### Requirement: Estimativa de catálogo pelo sitemap
O sistema SHALL ler o `robots.txt` do site oficial em busca de sitemaps e, na ausência, tentar `/sitemap.xml`, seguindo índices de sitemap até um limite, e registrar o total de URLs e a distribuição por tipo de página (agrupada pelo primeiro segmento do caminho ou por padrão de URL), sem visitar as páginas listadas.

#### Scenario: Sitemap encontrado
- **WHEN** o site publica um sitemap acessível
- **THEN** os dados brutos registram o total de URLs, a distribuição por tipo de página e uma amostra de URLs

#### Scenario: Índice de sitemaps
- **WHEN** o sitemap é um índice que aponta para outros sitemaps
- **THEN** o sistema lê os sitemaps filhos até o limite configurado e soma as URLs

#### Scenario: Site sem sitemap
- **WHEN** o `robots.txt` não indica sitemap e `/sitemap.xml` não existe
- **THEN** a fonte é registrada como não coletada com o motivo, e a execução continua

#### Scenario: Sitemap bloqueado
- **WHEN** o acesso ao `robots.txt` e ao `/sitemap.xml` é recusado de forma persistente
- **THEN** a fonte é registrada como não coletada com o motivo de bloqueio, e a execução continua

## ADDED Requirements

### Requirement: Tentativas com espera progressiva e classificação de falha
O sistema SHALL repetir uma requisição que falhar por motivo transitório (HTTP 429 ou 503, tempo esgotado, erro de conexão) um número limitado de vezes, com espera progressiva entre as tentativas, antes de registrar falha. Esgotadas as tentativas, o sistema SHALL registrar no dado bruto, para a fonte afetada, se o acesso foi **recusado** (403/429), se o servidor **falhou** (5xx) ou se **não houve resposta**, com o código HTTP e a URL. Nenhuma repetição SHALL contar como página visitada nem consumir o limite de páginas.

#### Scenario: Instabilidade passageira
- **WHEN** uma página responde 429 na primeira tentativa e 200 na seguinte
- **THEN** a página é registrada como coletada, sem falha e sem consumir página extra do limite

#### Scenario: Recusa persistente
- **WHEN** todas as tentativas de uma página recebem 403 ou 429
- **THEN** a fonte registra a falha com o código HTTP e a indicação de acesso recusado

#### Scenario: Servidor fora do ar
- **WHEN** todas as tentativas recebem 5xx ou esgotam o tempo
- **THEN** a fonte registra a falha com o código ou o tipo de erro, sem indicar recusa de acesso

#### Scenario: Falha em uma fonte não interrompe as demais
- **WHEN** uma fonte esgota as tentativas
- **THEN** as demais fontes continuam a ser coletadas e a execução termina com sucesso

### Requirement: Coleta pelo arquivo público quando o site está bloqueado
Quando o acesso ao site oficial for recusado de forma persistente, o sistema SHALL tentar a captura mais recente do domínio no arquivo público, coletando a página inicial e as páginas internas relevantes do mesmo domínio até o limite de páginas, e SHALL registrar para cada página a URL do snapshot, a data da captura e a indicação de que o conteúdo veio de arquivo. O sistema SHALL NOT usar o arquivo público quando o site ao vivo responde, SHALL NOT gravar conteúdo arquivado sem esse metadado e SHALL registrar em `raw.md` e no console a origem arquivada e a data da captura.

#### Scenario: Site bloqueado com captura disponível
- **WHEN** o site recusa o acesso e o arquivo público tem capturas do domínio
- **THEN** os dados brutos trazem as páginas com texto, a URL do snapshot e a data da captura de cada uma

#### Scenario: Metadado de origem arquivada
- **WHEN** uma página é coletada pelo arquivo público
- **THEN** o conteúdo registra a origem arquivada e a data da captura, distinguindo-a de uma leitura ao vivo

#### Scenario: Site ao vivo disponível
- **WHEN** o site ao vivo responde com sucesso
- **THEN** o arquivo público não é consultado e nenhuma página é marcada como arquivada

#### Scenario: Arquivo indisponível
- **WHEN** o site está bloqueado e o arquivo público falha ou não tem captura
- **THEN** a fonte fica registrada como falha por bloqueio, com o motivo, e a execução continua
