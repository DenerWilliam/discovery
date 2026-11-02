## Context

Ver `proposal.md` — Why. O estado atual que molda a solução:

- `collectors/site.py` faz uma única tentativa por página; falha da home encerra a varredura (`break`) e a fonte inteira vira `falha`.
- `collectors/tecnologia.py` e `collectors/sitemap.py` também fazem tentativa única; `sitemap` usa `httpx` direto, sem cabeçalhos de navegador.
- `collectors/search.py` fixa `setlang=pt-BR`; `collectors/news.py` fixa `hl=pt-BR&gl=BR&ceid=BR:pt-419`; `cli.py` fixa `locale="pt-BR"` no contexto do navegador.
- `PRIORITY_KEYWORDS` em `site.py` cobre só português; `_score` soma ocorrências, então acrescentar termos não altera a ordem relativa de páginas em português.
- `Source` (`models.py`) tem `tipo, origem, status, coletado_em, conteudo, erro`; `to_dict` é explícito, então qualquer campo novo é uma decisão consciente. `FORMAT_VERSION = 2`.
- Testes de site sobem um servidor HTTP local e usam Chromium real; CNPJ/filiais usam `httpx.MockTransport`. Não há teste de Wayback hoje.

## Goals / Non-Goals

**Goals:**

- Nenhuma fonte ser perdida por instabilidade passageira (429/503/timeout), só por recusa ou indisponibilidade persistente.
- Quando a recusa for persistente, obter o conteúdo do site pelo arquivo público, com data de captura por página, sem confundir com leitura ao vivo.
- Coletar no idioma do cliente (navegador, buscadores, feed) sem tocar no comportamento padrão em português.
- Manter o contrato de dados: `raw.json` legível por execuções antigas e pelo `discovery contatos`.

**Non-Goals:**

- Não contornar bloqueio: nada de UA de buscador, rotação de proxy, resolução de CAPTCHA ou reprodução de cookies de sessão. A recusa é registrada; o arquivo público é a única alternativa, por ser fonte pública.
- Não usar o arquivo público quando o site responde, nem para "completar" páginas que falharam isoladamente.
- Não mudar `FORMAT_VERSION`, não mudar `versao_formato` no arquivo do cliente, não alterar o CSV de contatos.
- Não interpretar o conteúdo arquivado (continua sendo dado bruto).

## Decisions

### 1. Um helper de tentativas, aplicado por fonte

Novo módulo `collectors/resiliencia.py` com uma função de tentativa (3 tentativas, espera 1 s e 3 s) que recebe uma chamada e devolve resultado ou um erro classificado (`recusado` para 403/429, `falhou` para 5xx, `sem_resposta` para timeout/conexão). Só 429, 502, 503, 504, timeout e erro de conexão são repetidos; **403 e 404 não são** (repetir não muda o resultado e aumenta a carga).

- *Alternativa descartada:* retry dentro de cada coletor — duplicaria a classificação e divergiria com o tempo.
- *Alternativa descartada:* biblioteca externa (`tenacity`) — uma dependência a mais para uma política de três linhas.

### 2. Classificação de falha em campo próprio, não no texto do erro

`Source` ganha `motivo: str | None` (`recusado`, `falhou`, `sem_resposta`), serializado junto com os demais campos. `erro` continua com a mensagem legível (inclui código HTTP e URL). Assim a etapa de estruturação e os testes leem o motivo sem interpretar string.

- *Alternativa descartada:* convenção de prefixo em `erro` — frágil e some na tradução do relatório.
- *Alternativa descartada:* novo `status` (`bloqueado`) — quebraria `discovery contatos`, o `raw.md` e a skill, que já tratam `falha`/`nao_coletada`.

### 3. Arquivo público como fonte de substituição, com metadado por página

Novo `collectors/arquivo.py`:

1. Consulta o índice público do Wayback (CDX) para o domínio, filtrando respostas 200 e colapsando por URL, e pega a captura mais recente de cada URL.
2. Ordena as URLs com o mesmo `_score` da varredura ao vivo e respeita o mesmo `max_pages`.
3. Baixa o HTML da captura com `httpx` (poucas requisições, com pausa) e extrai o texto com um parser da biblioteca padrão que descarta `script`, `style`, `noscript` e `template`.
4. Grava `conteudo = {"titulo", "texto", "origem": "arquivo", "captura": "<timestamp>", "url_snapshot": "<url>"}`.

Dispara **somente** quando a home falha com `motivo=recusado` após as tentativas. Falha do próprio arquivo registra `falha` com `motivo=recusado` e segue.

- *Alternativa descartada:* carregar a URL do snapshot no Playwright — mais lento, e o Wayback costuma responder com HTML estático que não precisa de JS.
- *Alternativa descartada:* BeautifulSoup — nova dependência para uma extração simples.
- *Alternativa descartada:* acionar o fallback sempre que qualquer página interna falhar — multiplicaria requisições e misturaria origens dentro da mesma fonte.

### 4. Idioma como dado do cliente, propagado por três caminhos

`clients/<id>.yaml` ganha `locale: pt-BR` (padrão), validado por `^[a-z]{2}-[A-Z]{2}$` em `config.py`. O valor vai para: `browser.new_context(locale=...)`, parâmetro `setlang` do Bing (`pt-BR` → `pt-BR`, `en-US` → `en-US`) e `hl/gl/ceid` do Google News (`en-US` → `hl=en-US&gl=US&ceid=US:en`). O idioma usado fica registrado em `conteudo["locale"]` nas fontes `busca` e `noticias`.

- *Alternativa descartada:* detectar o idioma do site — o cliente sabe o idioma do material que quer ler; detecção adicionaria ruído e falharia em sites bilíngues.

### 5. Ranking bilíngue por acumulação

`PRIORITY_KEYWORDS` recebe equivalentes em inglês (`about`, `company`, `services`, `solutions`, `products`, `contact`, `privacy`, `terms`). Como `_score` soma ocorrências, páginas em português mantêm a ordem atual e páginas em inglês ganham prioridade equivalente.

## Risks / Trade-offs

- **Conteúdo arquivado desatualizado** → metadado `captura` por página, aviso no `raw.md`/console, e a skill passa a citar a data (delta em `discovery-skill`).
- **Wayback instável ou com limite de taxa** → teto de requisições, pausa entre elas, tentativa única por snapshot, falha não aborta a execução.
- **Retry encarece execuções contra sites mortos** → 3 tentativas, esperas curtas, e só para códigos transitórios; o limite de páginas não é consumido por tentativa.
- **Falso positivo de "bloqueado"** (403 legítimo de área restrita) → o fallback só age na home; se o arquivo público também não tiver captura, a fonte fica `falha` com `recusado` e o relatório trata como lacuna.
- **Extração de texto sem navegador difere da extração ao vivo** → o texto arquivado é marcado como tal; a etapa de estruturação não compara os dois como iguais.
- **Custo de manutenção do parser de arquivo** → API do CDX é estável e o formato de snapshot (`id_`) é documentado; o teste usa `MockTransport` com fixtures, sem rede.

## Migration Plan

Aditivo e sem migração de dados: execuções antigas continuam legíveis (campos novos são opcionais e `motivo` vem nulo). O `locale` default preserva o comportamento de todos os clientes existentes. Não há rollback especial: remover o campo e o módulo de arquivo restaura o comportamento anterior, e o `raw.json` gerado no intervalo continua válido.

## Open Questions

Nenhuma que mude as specs ou o plano de tarefas.
