## Context

Pacote `discovery` (layout `src/`, `uv`, Python >=3.10) com apenas um `main()` placeholder e sem dependências. Motivação e escopo em proposal.md. O comportamento esperado está nas specs `web-discovery` e `discovery-skill`.

## Goals / Non-Goals

**Goals:**
- Núcleo reutilizável para qualquer cliente, testável sem IA e sem rede (coletores isolados e substituíveis).
- Coleta e estruturação desacopladas: raspar uma vez e reestruturar várias, sem nova ida à web.
- Falha em uma fonte não derruba a execução: os dados brutos registram o que falhou.

**Non-Goals:**
- Crawler genérico de larga escala, autenticação, burla de anti-bot ou CAPTCHA.
- Interpretação semântica dentro do CLI (fica na etapa 2).

## Decisions

**1. Duas etapas com contrato em arquivos.**
```
 discovery scan  ->  reports/<carimbo>-<id>/raw.json + raw.md
 /discovery      ->  discovery/<id>/scraping-<carimbo2>.md
```
A etapa 1 nunca interpreta; a etapa 2 nunca acessa a web por conta própria. O `raw.json` é o contrato: quem o lê pode ser a skill hoje, outro modelo ou um template amanhã. Alternativa descartada: CLI já renderizando seções interpretativas por palavras-chave, que ficam rasas e obrigam nova coleta para mudar o formato.

**2. Pasta por execução, com tudo dentro.**
`reports/<AAAA-MM-DD_HHMMSS>-<id>/` guarda só `raw.json` e `raw.md`. As estruturações vão para `discovery/<id>/scraping-<carimbo2>.md`: pasta separada porque o dado bruto é material de trabalho e o relatório é o documento de leitura e compartilhamento, e o prefixo `scraping-` identifica sua origem. O relatório cita no cabeçalho a execução de origem, o que mantém o vínculo entre as duas pastas. Ambas as pastas ficam no `.gitignore` (dados de clientes). O carimbo no prefixo preserva o histórico, ordena no `ls` e evita colisão em várias execuções no mesmo dia. Sem `:` no carimbo, por compatibilidade com sistemas de arquivos. Os dados brutos são tratados como imutáveis após gravados.

**3. `raw.json` organizado por fonte.**
Estrutura: metadados da execução (cliente, site, parâmetros, versão do formato, início/fim) e uma lista de fontes, cada uma com `tipo` (`site`, `cnpj`, `busca`), `origem` (URL ou API), `coletado_em`, `status` (`ok`, `falha`, `nao_coletada`), `erro` opcional e `conteudo` (páginas com título/URL/texto; dados cadastrais; resultados por query). O `raw.md` é gerado a partir do mesmo objeto, sem informação extra.

**4. Playwright (sync API) apenas para site e buscas; `httpx` para CNPJ.**
A API de CNPJ é JSON estável, então navegador seria custo sem ganho. Alternativa descartada: Playwright em tudo, mais lento e frágil.

**5. Pipeline de coletores independentes que devolvem um resultado comum.**
`site` → `cnpj` (depende do texto do site quando não informado) → `search` → gravação. Cada coletor retorna conteúdo mais status/falha, e o gravador monta `raw.json` e `raw.md` sem conhecer a origem. Facilita testar com fixtures e adicionar fontes depois.

**6. Varredura do site limitada ao mesmo domínio, com teto de páginas.**
Parte da home, segue links internos priorizando palavras-chave (sobre, serviços, contato, privacidade, termos), com limite configurável (padrão 15 páginas). Evita varredura ilimitada e cobre onde o CNPJ costuma aparecer.

**7. CNPJ: regex mais validação de dígitos verificadores; consulta à BrasilAPI.**
A validação evita falsos positivos em números aleatórios. ReceitaWS tem limite de taxa mais restrito e fica como fallback futuro, não neste change.
Como o site pode citar CNPJs de terceiros, a validação de dígitos não basta: com um único candidato, ele é usado; com vários, todos são registrados (origem e contagem) e a fonte cadastral fica como ambígua, sem consulta automática. O usuário resolve informando `--cnpj` (ou o campo `cnpj` do cliente) e a etapa 2 pode apontar a ambiguidade no relatório. Escolher o mais frequente foi descartado por poder errar em silêncio.

**7.1. `reports/` fora do git.**
Os relatórios contêm dados de clientes e nomes de sócios (dados pessoais, ainda que públicos, sob a LGPD) e não devem ser versionados junto com a ferramenta. `reports/` entra no `.gitignore`; `clients/` continua versionado, por conter apenas configuração sem dados coletados.

**8. Buscas sem chave, em cadeia: Bing, depois DuckDuckGo; notícias por RSS.**
O projeto será usado por outras pessoas, então nada de API paga nem chave por usuário. Testado: o DuckDuckGo HTML bloqueia (202/403) e o Bing responde sem CAPTCHA, então o Bing é o principal e o DuckDuckGo o plano B; se todos falharem, a query fica não concluída. Cada buscador tem um parser pequeno e isolado (com teste de fixture), pois o HTML muda; os links de redirecionamento do Bing são decodificados para a URL de destino. Notícias vêm do RSS do Google News via `httpx`, sem navegador (zero itens é resultado válido). Testado com a Haix: o Bing automatizado só devolve resultados relevantes para o nome entre aspas; com termos extras (vagas, ERP, CNPJ) degrada para resultados aleatórios. Por isso a query padrão é só o nome entre aspas (queries extras ficam a critério do arquivo do cliente) e o filtro de relevância fica na etapa 2, que descarta e declara o que não cita o cliente. Raspagem de buscador é melhor esforço: falha vira registro nos dados brutos. Como o Bing automatizado às vezes responde com resultados aleatórios sem bloquear, um resultado só vale se algum item citar o cliente (marca = primeira palavra do nome); caso contrário é descartado, o Bing é tentado uma segunda vez e depois vem o DuckDuckGo. Alternativas descartadas: API de busca com chave (fricção para quem usa) e parser do DuckDuckGo principal (JS, sem contrato).

**9. Configuração por cliente em `clients/<id>.yaml`, com parâmetros de CLI sobrepondo o arquivo.**
Campos: `name`, `site`, `cnpj` (opcional), `queries` (lista), `max_pages` (opcional). Query padrão embutida (só o nome do cliente entre aspas) usada quando o arquivo não define; queries extras ficam no arquivo do cliente.

**9.1. Escopo de módulos e roteiro de reunião como saídas fixas da etapa 2.**
Além do relatório, cada estruturação gera `discovery/<id>/reuniao-<carimbo>.md` (~60 perguntas). O relatório inclui uma seção de escopo de módulos Odoo em fases, definida pelo consultor e ligada a evidências. O roteiro fica em arquivo próprio por ser o documento levado à reunião e preenchido, e as perguntas partem das lacunas e divergências do relatório (marcadas como dado coletado), completadas com temas padrão. A skill não afirma edição por módulo com certeza: deixa o aviso para confirmar edição e versão.

**10. Skill fina em `.claude/skills/discovery/`, espelhada em `.opencode/`.**
Por padrão estrutura a execução mais recente do cliente; só chama `discovery scan` quando o usuário pede coleta nova. Uma versão global (`~/.claude/skills/`) fica para quando houver mais de um cliente em uso.

## Risks / Trade-offs

- [Anti-bot ou mudança de HTML nas buscas quebra a coleta] → Cadeia de buscadores, parser isolado por buscador e falha registrada por query; site, CNPJ e notícias seguem funcionando.
- [Site pesado em JS ou lento] → Timeouts por página e espera de carregamento configurados; falha registrada.
- [Extração de texto traz ruído (menus, rodapés repetidos)] → Extrair conteúdo principal e deduplicar linhas; guardar também o necessário para conferência em `raw.md`.
- [Formato do `raw.json` evolui e quebra estruturações antigas] → Campo de versão do formato nos metadados.
- [Volume de disco com muitas execuções] → Aceito; texto puro é pequeno.
- [CNPJ de terceiro tomado como o do cliente] → Vários candidatos geram ambiguidade explícita, sem escolha automática.
- [Vazamento de discovery de um cliente ao trabalhar com outro] → `reports/` no `.gitignore`.
- [Uso indevido de dados de terceiros] → Somente fontes públicas, sem login; LinkedIn fora do escopo.
- [Skill diverge entre `.claude/` e `.opencode/`] → Tarefa explícita de espelhamento e verificação.
