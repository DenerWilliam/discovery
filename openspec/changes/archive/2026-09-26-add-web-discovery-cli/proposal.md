## Why

Ao começar com um cliente novo, a Escodoo precisa entender rápido como a empresa opera (modelo de negócio, porte, sistemas atuais, dores) para preparar o projeto Odoo. Hoje essa pesquisa é manual e não se repete de forma padronizada. A Haix Rental é o primeiro cliente, mas o mesmo levantamento será necessário para os próximos.

A coleta na web é a parte lenta e sujeita a bloqueios; a interpretação é a parte que se quer refazer várias vezes. Separar as duas permite raspar uma vez e reestruturar quantas vezes for preciso.

## What Changes

- Fluxo em duas etapas com contrato claro entre elas:
  - **Etapa 1, garimpo (CLI, sem IA):** `discovery scan` coleta dados públicos e grava os dados brutos e as fontes, sem interpretá-los.
  - **Etapa 2, estruturação (skill, com IA):** `/discovery` lê os dados brutos de uma execução e gera o relatório estruturado, podendo ser repetida sobre a mesma execução sem nova coleta.
- CLI genérico e parametrizado por cliente (nome, site, CNPJ opcional, queries de busca), sem nada específico da Haix no código.
- Coleta com Playwright apenas onde há necessidade (site oficial e buscas); cadastro de CNPJ via API HTTP pública, sem navegador.
- Descoberta híbrida: parte do site oficial do cliente (incluindo extração do CNPJ do rodapé/páginas legais) e complementa com buscas de queries pré-definidas, sem depender de API paga nem de chave (buscadores em cadeia e notícias por RSS).
- Cada execução grava uma pasta `reports/<AAAA-MM-DD_HHMMSS>-<cliente>/` com `raw.json` (dados por fonte, para máquina) e `raw.md` (texto bruto legível, para conferência). Cada estruturação grava um relatório `discovery/<cliente>/scraping-<AAAA-MM-DD_HHMMSS>.md`, em pasta separada dos dados brutos, por ser o documento de leitura e compartilhamento.
- Arquivo de configuração por cliente (ex.: `clients/haix.yaml`), com a Haix como primeiro cliente de teste.
- Skill `/discovery` em `.claude/skills/` (espelhada em `.opencode/`) que faz a etapa 2 e também aciona a etapa 1 quando o usuário pede uma coleta nova.
- Com vários CNPJs válidos no site, o CLI registra todos e sinaliza a ambiguidade em vez de escolher um; `reports/` fica fora do git por conter dados de clientes.
- Fora do escopo: LinkedIn e qualquer fonte que exija login, e chamadas a LLM dentro do script.

## Capabilities

### New Capabilities
- `web-discovery`: CLI (etapa 1) que coleta informações públicas sobre um cliente (site, CNPJ, buscas) e grava os dados brutos por execução.
- `discovery-skill`: skill (etapa 2) que estrutura os dados brutos de uma execução em relatório voltado para o contexto de um projeto Odoo.

### Modified Capabilities
<!-- Nenhuma: não há specs existentes. -->

## Impact

- Código: `src/discovery/` (CLI, coletores, gravação dos dados brutos); novas pastas `clients/` e `reports/`.
- Dependências: `playwright`, um cliente HTTP (ex.: `httpx`) e `pyyaml` em `pyproject.toml`; instalação dos navegadores do Playwright.
- Skills: `.claude/skills/discovery/` e o espelho em `.opencode/`.
- Rede: acesso a sites públicos e à API de CNPJ; sujeito a bloqueios anti-bot e limites de taxa.
