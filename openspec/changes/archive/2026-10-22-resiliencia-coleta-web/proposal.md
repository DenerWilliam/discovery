## Why

A coleta da Salcas (2026-10-22) perdeu o site inteiro: o host respondeu 429/403 a todas as tentativas do Playwright e do `httpx`, e as fontes `site`, `tecnologia` e `sitemap` ficaram `falha`/`nao_coletada`. O conteúdo só foi obtido à mão, pelo arquivo público do Wayback, fora do contrato do `raw.json` — ou seja, o dado usado no relatório não é reprodutível nem rastreável pela execução. Ao mesmo tempo, o `locale` está fixo em `pt-BR` no navegador, no Bing e no feed de notícias, e o ranking de páginas internas só reconhece palavras em português, o que degrada a coleta de qualquer cliente cujo site seja em inglês (caso da Kestrel).

## What Changes

- **Tentativas com espera progressiva** nas fontes `site`, `tecnologia`, `sitemap` e `noticias`: erro transitório (429, 503, timeout, conexão) é repetido um número limitado de vezes antes de virar falha, consumindo a mesma fonte e não o limite de páginas.
- **Falha classificada**: quando o site rejeita de forma persistente (403/429), a fonte registra no dado bruto que o acesso foi bloqueado, com o código HTTP e a URL, separando "bloqueado" de "fora do ar" e de "sem resposta".
- **Arquivo público como fallback**: se a página inicial não puder ser lida ao vivo por bloqueio, a execução coleta a captura mais recente do site no arquivo público (Wayback), página a página, gravando para cada uma a URL do snapshot e a data da captura, e marcando o conteúdo como vindo de arquivo. O fallback só entra quando o site ao vivo falha — nunca substitui conteúdo coletado ao vivo.
- **Aviso explícito no dado bruto e no console** quando uma fonte veio de arquivo, para que a etapa de estruturação trate o conteúdo com a data correta.
- **`locale` por cliente** (`clients/<id>.yaml`, padrão `pt-BR`), aplicado ao contexto do navegador, ao parâmetro de idioma do Bing e ao feed do Google News (`hl`/`gl`/`ceid`).
- **Ranking de páginas internas bilíngue**: as palavras-chave de prioridade passam a cobrir português e inglês, sem alterar a ordem para sites em português.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `web-discovery`: varredura do site oficial (tentativas, classificação de bloqueio, fallback de arquivo público, aviso de origem), detecção de tecnologias (tentativas), sitemap (tentativas), buscas complementares e notícias (idioma por cliente), e parametrização por cliente (`locale`).
- `discovery-skill`: a estruturação passa a citar, para páginas vindas de arquivo, a data da captura e a natureza do conteúdo, em vez de tratá-las como leitura ao vivo.

## Impact

- `src/discovery/collectors/site.py` (tentativas, classificação, ranking bilíngue, orquestração do fallback), `collectors/tecnologia.py`, `collectors/sitemap.py`, `collectors/news.py`, `collectors/search.py`.
- Novo módulo de arquivo público (consulta ao índice e leitura de snapshots) e um cliente `httpx` compartilhado.
- `src/discovery/config.py` (campo `locale`, validação), `src/discovery/cli.py` (aplicação do locale ao contexto do navegador), `src/discovery/models.py` (metadados de origem/captura na fonte), `src/discovery/storage.py` (`raw.md` mostra a origem arquivada).
- `src/discovery/collectors/signatures.py` não muda; a detecção de tecnologia passa a poder rodar sobre o HTML arquivado quando o site ao vivo está bloqueado.
- Testes: `tests/test_site.py` e `tests/test_tecnologia.py` ganham casos de retry e de bloqueio; novo teste de arquivo público com `httpx.MockTransport`; teste de `locale` no `config` e no feed de notícias.
- Sem mudança no formato `versao_formato` além dos metadados aditivos dentro de `conteudo`; execuções antigas continuam legíveis.
- Custo: uma ou duas requisições extras por fonte em caso de falha transitória; consulta ao arquivo público apenas quando o site ao vivo está bloqueado.
