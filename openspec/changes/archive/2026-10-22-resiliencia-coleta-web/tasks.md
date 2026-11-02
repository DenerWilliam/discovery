## 1. Contrato de dados e configuração

- [x] 1.1 Adicionar `motivo: str | None = None` a `Source` em `src/discovery/models.py` e serializá-lo em `to_dict`; verificar com `uv run pytest tests/test_storage.py` que execuções antigas (sem o campo) continuam legíveis
- [x] 1.2 Adicionar `locale: str = "pt-BR"` à configuração do cliente em `src/discovery/config.py`, validar com `^[a-z]{2}-[A-Z]{2}$` e expor em `--dry-run`; verificar com um teste em `tests/test_config.py` para ausente, válido e inválido (`en_US`, `pt`)
- [x] 1.3 Documentar `locale` no `CLAUDE.md` e no cabeçalho de exemplo de `clients/<id>.yaml`, se existir; verificar por leitura do arquivo

## 2. Tentativas e classificação

- [x] 2.1 Criar `src/discovery/collectors/resiliencia.py` com a política de tentativas (3 tentativas, esperas 1 s e 3 s, repetir só 429/502/503/504/timeout/conexão) devolvendo o motivo classificado; verificar com teste unitário que 403 e 404 não são repetidos e que 429 seguido de 200 retorna sucesso
- [x] 2.2 Aplicar o helper em `collectors/site.py`, mantendo o limite de páginas intacto entre tentativas; verificar com teste em `tests/test_site.py` em que o servidor local responde 429 na primeira requisição e 200 na segunda, checando `status == ok` e a contagem de páginas
- [x] 2.3 Aplicar o helper em `collectors/tecnologia.py` e `collectors/sitemap.py`; verificar com teste de servidor local que responde 503 e depois 200, checando `status == ok` e `motivo is None`
- [x] 2.4 Aplicar o helper em `collectors/news.py` (429/5xx/timeout) sem tratar 4xx como transitório; verificar com `httpx.MockTransport` em `tests/test_news.py`
- [x] 2.5 Registrar `motivo` e a mensagem com código HTTP e URL quando as tentativas se esgotam; verificar com teste de 403 persistente em `tests/test_site.py` (`status == falha`, `motivo == "recusado"`) e de timeout (`motivo == "sem_resposta"`)

## 3. Arquivo público

- [x] 3.1 Criar `src/discovery/collectors/arquivo.py` com consulta ao índice CDX (respostas 200, colapso por URL, captura mais recente) usando `httpx` e cabeçalho identificável; verificar com `MockTransport` lendo um JSON de fixture e conferindo URL e timestamp escolhidos
- [x] 3.2 Implementar a extração de texto do HTML arquivado com parser da biblioteca padrão, descartando `script`, `style`, `noscript` e `template`; verificar com fixture HTML que o texto não contém o conteúdo de `script` nem marcação
- [x] 3.3 Ordenar as URLs do snapshot com o mesmo `_score` da varredura ao vivo e respeitar `max_pages`; verificar por teste que a ordem e o teto batem com a lista de prioridade
- [x] 3.4 Gravar `conteudo` com `origem`, `captura` e `url_snapshot` em cada página arquivada e acionar o fallback só quando a home falhar com `motivo == "recusado"`; verificar com teste de integração do `collect_site` contra servidor local que responde 403 e `MockTransport` do arquivo, checando `status == ok` e os metadados
- [x] 3.5 Não acionar o arquivo quando o site ao vivo responde; verificar com teste que o `MockTransport` do arquivo não recebe requisição
- [x] 3.6 Tratar falha do arquivo (sem captura, erro HTTP) como `falha` com `motivo == "recusado"`; verificar com teste de arquivo vazio

## 4. Idioma e ranking

- [x] 4.1 Propagar o `locale` para `browser.new_context` em `src/discovery/cli.py`; verificar com teste que o contexto recebe o idioma do cliente (ou por asserção no `run_scan` com duplo do Playwright)
- [x] 4.2 Usar o `locale` no `setlang` do Bing e registrar `conteudo["locale"]` na fonte `busca`; verificar em `tests/test_search.py` que `pt-BR` e `en-US` produzem URLs distintas e o campo correto
- [x] 4.3 Derivar `hl`/`gl`/`ceid` do Google News a partir do `locale`, com mapa explícito para `pt-BR` e `en-US` e padrão seguro para os demais; verificar em `tests/test_news.py` que a URL e o `conteudo["locale"]` batem nos dois casos
- [x] 4.4 Acrescentar os termos em inglês a `PRIORITY_KEYWORDS` sem remover nem reordenar os de português; verificar com teste que uma URL `about`/`services` pontua igual à equivalente `sobre`/`servicos`

## 5. Saída bruta e documentação

- [x] 5.1 Mostrar `motivo` e origem arquivada com a data da captura no `raw.md` e no resumo do console; verificar com `tests/test_storage.py` e por leitura do `raw.md` de uma execução de teste
- [x] 5.2 Registrar no `raw.md` e no console o aviso de que a fonte veio de arquivo; verificar por asserção no teste de storage
- [x] 5.3 Atualizar `CLAUDE.md` (seção de fontes e de falhas) e a skill em `.claude/skills/discovery/` e `.opencode/skills/discovery/` com a regra de citar a data da captura; verificar que as duas cópias da skill ficam idênticas (`diff`)
- [x] 5.4 Rodar a suíte completa (`uv run pytest`) e uma varredura de fumaça com `--dry-run` em um cliente existente; verificar saída sem erro e `locale` exibido

## 6. Validação de ponta a ponta

- [x] 6.1 Rodar `uv run discovery scan --client <cliente bloqueado>` e conferir no `raw.json` que a fonte `site` veio com `origem == "arquivo"`, `captura` preenchida e o restante das fontes coletado; verificar por leitura do `raw.json`
- [x] 6.2 Rodar `/discovery <cliente>` sobre essa execução e conferir que o relatório cita a data da captura e declara o conteúdo como arquivado; verificar por leitura do relatório
