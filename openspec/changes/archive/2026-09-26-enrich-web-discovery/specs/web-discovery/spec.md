## ADDED Requirements

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

### Requirement: Detecção de tecnologias do site
O sistema SHALL identificar tecnologias usadas pelo site oficial (plataforma de e-commerce ou CMS, ferramentas de marketing e analytics, chat e WhatsApp, meios de pagamento e CDN) a partir do HTML, dos cabeçalhos, dos cookies e dos domínios contatados durante o carregamento da página inicial, registrando para cada detecção o nome, a categoria e a evidência que a originou.

#### Scenario: Tecnologia detectada
- **WHEN** a página inicial carrega um script, cookie ou cabeçalho característico de uma tecnologia conhecida
- **THEN** os dados brutos listam a tecnologia com categoria e a evidência

#### Scenario: Nada detectado
- **WHEN** nenhuma tecnologia conhecida é identificada
- **THEN** a fonte é registrada como coletada com lista vazia, sem erro

#### Scenario: Página inicial inacessível
- **WHEN** a página inicial não carrega
- **THEN** a fonte é registrada como falha e a execução continua

### Requirement: Estabelecimentos da mesma raiz de CNPJ
O sistema SHALL, quando houver um CNPJ resolvido e consultado com sucesso, consultar por API pública os estabelecimentos que compartilham a raiz de 8 dígitos (sufixos sequenciais com dígitos verificadores válidos), até um limite e parando após vários sufixos consecutivos inexistentes, e registrar para cada um o CNPJ, a cidade, a UF, o CNAE, a situação cadastral e a data de início.

#### Scenario: Filiais encontradas
- **WHEN** existem estabelecimentos além do informado
- **THEN** os dados brutos listam cada estabelecimento com cidade, UF, CNAE e situação

#### Scenario: Sem outros estabelecimentos
- **WHEN** nenhum outro sufixo existe
- **THEN** a fonte é registrada como coletada listando somente o estabelecimento conhecido

#### Scenario: Limite de taxa da API
- **WHEN** a API sinaliza limite de taxa ou falha durante a busca
- **THEN** o sistema registra os estabelecimentos já obtidos, marca a fonte como falha parcial com o motivo e continua

#### Scenario: CNPJ não resolvido
- **WHEN** o CNPJ não foi informado nem encontrado, ou é ambíguo
- **THEN** a fonte de estabelecimentos é registrada como não coletada, sem consultar a API

## MODIFIED Requirements

### Requirement: Notícias por feed
O sistema SHALL consultar um feed público de notícias com o nome do cliente, sem navegador e sem chave, e registrar título, URL, data e veículo apenas das notícias que citam o cliente (nome completo, sem considerar maiúsculas e acentos), informando quantos itens foram descartados por não citá-lo.

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
