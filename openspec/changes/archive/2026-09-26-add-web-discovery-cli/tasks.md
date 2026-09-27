## 1. Setup

- [x] 1.1 Adicionar `playwright`, `httpx`, `pyyaml` e `pytest` ao `pyproject.toml` e verificar que `uv sync` conclui sem erro
- [x] 1.2 Instalar o Chromium do Playwright (`uv run playwright install chromium`) e verificar que um script mínimo abre uma página
- [x] 1.3 Adicionar `reports/` e `discovery/` ao `.gitignore` e verificar com `git check-ignore reports/x discovery/x` que os caminhos são ignorados e que `clients/` não é
- [x] 1.4 Criar a estrutura de módulos em `src/discovery/` (cli, config, collectors, storage) e verificar que `uv run discovery --help` lista o subcomando `scan`

## 2. Configuração e CLI

- [x] 2.1 Implementar carregamento de `clients/<id>.yaml` com sobreposição por parâmetros de CLI e queries padrão; verificar com testes unitários dos cenários das specs (arquivo, parâmetros, site ausente com erro)
- [x] 2.2 Criar `clients/haix.yaml` com nome, site `https://www.haixrental.com.br/` e verificar que `discovery scan --client haix` resolve a configuração

## 3. Coletor do site

- [x] 3.1 Implementar a varredura do site restrita ao domínio, com priorização de páginas (sobre, serviços, contato, privacidade, termos) e teto de páginas; verificar com teste contra páginas HTML locais de fixture
- [x] 3.2 Registrar falha do site (timeout/erro) sem interromper a execução; verificar com teste que simula site inacessível
- [x] 3.3 Descartar páginas que redirecionam para login e registrar a fonte como não coletada; verificar com teste de fixture

## 4. Coletor de CNPJ

- [x] 4.1 Implementar extração de CNPJ do texto com validação de dígitos verificadores; verificar com testes de CNPJs válidos, inválidos e sem formatação
- [x] 4.2 Implementar consulta à BrasilAPI via `httpx`, com uso do `--cnpj` quando informado; verificar com testes usando resposta simulada e caso de erro da API
- [x] 4.3 Tratar múltiplos CNPJs válidos no site registrando todos com origem e contagem, marcando a fonte cadastral como ambígua e não consultando a API; verificar com teste de fixture com dois CNPJs e com teste de que `--cnpj` resolve a ambiguidade
- [x] 4.4 Tratar ausência de CNPJ registrando a fonte cadastral como não consultada; verificar com teste que a execução termina com sucesso

## 5. Coletor de buscas e notícias

- [x] 5.1 Implementar o parser do DuckDuckGo (título, URL, trecho) e a detecção de bloqueio/CAPTCHA; verificar com testes de fixture de resultados e de página bloqueada
- [x] 5.2 Implementar o parser do Bing com decodificação do link de redirecionamento para a URL de destino; verificar com teste de fixture e teste da decodificação
- [x] 5.3 Implementar a cadeia de buscadores (Bing com uma nova tentativa, depois DuckDuckGo) registrando o motor usado, descartando resultados que não citam o cliente e marcando a query como não concluída se todos falharem; verificar com testes com buscadores simulados (bloqueado, irrelevante, todos falhando, nova tentativa)
- [x] 5.4 Implementar a coleta de notícias pelo RSS do Google News via `httpx` (título, URL, data, veículo; lista vazia é sucesso; falha é registrada); verificar com testes usando `httpx.MockTransport`
- [x] 5.5 Passar as queries padrão a usar o nome entre aspas e ligar a coleta de notícias no `discovery scan`; verificar com teste da config e com execução real contra a Haix mostrando resultados de busca

## 6. Dados brutos por execução

- [x] 6.1 Definir o formato do `raw.json` (metadados com versão do formato e lista de fontes com tipo, origem, momento, status, erro e conteúdo) e verificar com teste de validação do esquema
- [x] 6.2 Implementar a gravação de `reports/<AAAA-MM-DD_HHMMSS>-<id>/` com `raw.json` e `raw.md`, criando `reports/` se necessário; verificar com testes do conteúdo dos dois arquivos e de duas execuções seguidas gerando pastas distintas
- [x] 6.3 Garantir que fontes com falha apareçam com status e erro nos dois arquivos, sem interromper a gravação; verificar com teste em que todas as fontes falham
- [x] 6.4 Executar `discovery scan --client haix` contra o site real e verificar que a pasta da execução é gerada com `raw.json` e `raw.md` legíveis

## 7. Skill de estruturação

- [x] 7.1 Criar `.claude/skills/discovery/SKILL.md` que, por padrão, lê `raw.json` da execução mais recente do cliente (ou da indicada) sem nova coleta; verificar invocando `/discovery haix` após a tarefa 6.4 e confirmando que nenhuma requisição à web é feita
- [x] 7.2 Definir na skill o relatório com seções fixas (incluindo perguntas para o cliente), fontes citadas e lacunas explícitas, gravado como `discovery/<cliente>/scraping-<carimbo>.md` citando a execução de origem; verificar que `raw.json` e `raw.md` permanecem inalterados (comparação de hash)
- [x] 7.3 Cobrir na skill reestruturação repetida (novo arquivo sem apagar os anteriores), ausência de execução (oferece coleta) e coleta nova sob demanda pedindo parâmetros faltantes; verificar com invocações de cada caso
- [x] 7.4 Espelhar a skill em `.opencode/` e verificar que o conteúdo das duas cópias é equivalente (`diff`)

- [x] 7.5 Acrescentar à skill a seção de escopo de módulos Odoo em fases (com evidências, personalizações e aviso de edição) e o roteiro de reunião (~60 perguntas, origem D/P, campo de resposta, `--sem-perguntas`); verificar gerando os documentos de um cliente real (Estilo Ar) e conferindo que as duas cópias da skill continuam idênticas (`diff`)

## 8. Documentação

- [x] 8.1 Atualizar `CLAUDE.md` (comandos, `pytest`, estrutura `clients/` e `reports/`, fluxo em duas etapas) e adicionar uso no `README.md`; verificar que os comandos documentados executam
- [x] 8.2 Preencher `context:` em `openspec/config.yaml` com stack e convenções; verificar que o arquivo continua válido com `openspec validate add-web-discovery-cli`
