# discovery

Ferramenta de *discovery* de clientes novos para projetos Odoo (Escodoo). Levanta informações públicas na web, estrutura um relatório com escopo de módulos e roteiro de reunião, e depois cruza esse material com o que sai das próprias reuniões (atas, PDFs, planilhas, desenhos de fluxo) — tudo ficando registrado com carimbo de data e hora, para acompanhar a evolução do projeto.

O fluxo tem três etapas:

1. **Garimpo** (`discovery scan`, CLI Python, sem IA): coleta dados públicos e grava dados brutos, sem interpretar.
2. **Estruturação** (skill `/discovery`, no Claude Code, com IA): lê os dados brutos e escreve o relatório, o roteiro de reunião e (sob pedido) outros materiais.
3. **Cruzamento** (`/discovery <cliente> --cruzar`): cruza os documentos das reuniões com o que a web mostrou.

## Passo a passo

### 1. Instalar

```bash
uv sync
uv run playwright install chromium
```

Precisa também de `pdftotext`, `pandoc` e `soffice` (LibreOffice) instalados no sistema — usados na etapa 3 para ler PDF, `.docx` e planilhas dos documentos de reunião.

### 2. Configurar o cliente (opcional, mas recomendado)

Copie `clients/exemplo.yaml` para `clients/<id>.yaml` (o `<id>` é o nome do arquivo, sem extensão — vira o valor de `--client <id>` e de `/discovery <id>`) e preencha com o que você já sabe do cliente:

```bash
cp clients/exemplo.yaml clients/cliente-x.yaml
```

```yaml
name: Cliente X
site: https://www.clientex.com.br/
cnpj: "00.000.000/0001-00"   # opcional; se ausente, o CLI procura no site
queries:                     # opcional; {name} vira o nome do cliente (padrão: só "{name}")
  - '"{name}" reclame aqui'
max_pages: 15                # opcional
```

`clients/exemplo.yaml` tem cada campo comentado, com o motivo de preencher ou não. Sem arquivo de cliente, dá para passar tudo por parâmetro na hora de rodar (passo 3).

### 3. Rodar a coleta (garimpo)

```bash
# Com arquivo de cliente
uv run discovery scan --client cliente-x

# Sem arquivo
uv run discovery scan --name "Cliente X" --site https://exemplo.com.br [--cnpj 11.222.333/0001-81]

# Só conferir a configuração resolvida, sem coletar
uv run discovery scan --client cliente-x --dry-run
```

Outras opções: `--query '"{name}" vagas'` (repetível), `--max-pages N`, `--reports-dir`, `--clients-dir`.

Isso cria `reports/<AAAA-MM-DD_HHMMSS>-<cliente>/` com:
- **`raw.json`**: dados por fonte (origem, momento da coleta, status, erro, conteúdo), para leitura por máquina.
- **`raw.md`**: a mesma coisa, em texto legível.

Fontes coletadas: páginas do site oficial, **sitemap** (tamanho do catálogo), **tecnologia** do site (plataforma de loja/CMS, marketing, chat, pagamentos, CDN — com a evidência de cada detecção), **CNPJ** (BrasilAPI), **filiais** (estabelecimentos da mesma raiz de CNPJ, só quando o CNPJ é resolvido), **buscas** (Bing, com DuckDuckGo como reserva) e **notícias** (Google News, só as que citam o cliente). Se o site cita vários CNPJs válidos, a fonte fica `ambigua` e nada é consultado até você informar `--cnpj`. Uma fonte que falha não derruba a execução: ela fica registrada como `falha` ou `nao_coletada` e o resto segue.

Essa etapa não interpreta nada — quem faz isso é a etapa 2, no Claude Code.

### 4. Estruturar (no Claude Code)

Dentro deste repositório, no Claude Code:

```
/discovery cliente-x
```

Isso lê a coleta mais recente do cliente (sem acessar a web de novo) e grava, em `discovery/<cliente>/`:
- **`scraping-<carimbo>.md`**: o relatório — visão geral, dados cadastrais, modelo de negócio, sistemas e tecnologia, notícias, **hipóteses com nível de confiança** (fato / provável / palpite), **escopo de módulos Odoo em fases**, **dimensionamento preliminar** e **riscos do projeto**.
- **`reuniao-<carimbo>.md`**: o roteiro de reunião, com cerca de 60 perguntas, começando pelas que validam as hipóteses mais fracas, com campo de resposta para preencher ao vivo.

Use `--sem-perguntas` se quiser só o relatório. Peça "só o roteiro" se quiser gerar de novo apenas o roteiro a partir do relatório mais recente.

Se ainda não rodou a coleta, peça para o Claude coletar (`/discovery cliente-x --nova`, ou diga o nome e o site do cliente em linguagem natural, inclusive o CNPJ se tiver).

### 5. Levar o roteiro para a reunião

Imprima ou abra `reuniao-<carimbo>.md` e preencha o campo **Resposta** de cada pergunta durante a conversa com o cliente.

### 6. Guardar os documentos da reunião e cruzar

Depois da reunião, jogue o material recebido (ata, gravação transcrita, PDF, `.docx`, planilha, foto de um quadro com o fluxo desenhado) em:

```
discovery/<cliente>/docs-internos/
```

Nome sugerido (não obrigatório): `AAAA-MM-DD-<tipo>-<assunto>.<ext>`, com tipo em `ata`, `transcricao`, `fluxo`, `planilha`, `email` ou `proposta`. Essa pasta fica fora do git e os arquivos nela nunca são alterados.

Depois, no Claude Code:

```
/discovery cliente-x --cruzar
```

Isso gera `discovery/<cliente>/cruzamento-<carimbo>.md` — **sempre um arquivo novo**, sem tocar no relatório, no roteiro nem nos documentos. O documento traz:
- os arquivos considerados e os que não puderam ser lidos (com o motivo);
- as **hipóteses atualizadas** (nível antes e depois, com o trecho do documento que sustenta a mudança);
- as perguntas do roteiro que os documentos já responderam, e as que continuam em aberto;
- **contradições** entre a web e os documentos (ou entre documentos), sem a IA arbitrar quem está certo;
- o impacto no escopo de módulos, no dimensionamento e nos riscos;
- novas lacunas e perguntas para a próxima agenda.

Cada cruzamento novo parte do anterior (ou do relatório, se for o primeiro), então as hipóteses evoluem — palpite, provável, fato — sem perder o histórico. Repita este passo a cada reunião nova, sempre com `--cruzar`.

Leitura por formato: texto e Markdown direto; PDF via `pdftotext`; `.docx` via `pandoc`; planilhas via LibreOffice (convertidas para CSV); imagens lidas visualmente. Conteúdo vindo de imagem sempre aparece marcado como **[interpretação de imagem]**, para conferir com o cliente antes de dar como certo.

### 7. Contatos para importar no Odoo

Com um scan que resolveu o CNPJ, gere o CSV de contatos (matriz e filiais) no formato de importação do `res.partner`:

```bash
uv run discovery contatos --client cliente-x
```

Opções: `--run <pasta da execução>` (padrão: a mais recente), `--ajustes <arquivo>` (padrão: o `contatos-ajustes-*.yaml` mais recente), `--reports-dir`, `--out-dir`. Grava `discovery/<cliente>/contatos-<carimbo>.csv`, sempre um arquivo novo, sem acessar a web. Vendedor, Indústria, latitude e longitude saem vazios: o `--cruzar` grava um `contatos-ajustes-<carimbo>.yaml` com os valores que as atas afirmam (cada um com a fonte), e rodar `discovery contatos` de novo gera o CSV atualizado. Execuções anteriores a essa funcionalidade só têm a matriz completa; refaça o `scan` para incluir as filiais.

### 8. Outros materiais (cotação, resumo, apresentação...)

Peça ao Claude o que precisar — por exemplo, "gera uma cotação atualizada com os itens que faltam". Qualquer material assim segue a mesma disciplina dos demais:

```
discovery/<cliente>/<tipo-descritivo>-<AAAA-MM-DD_HHMMSS>.md
```

Carimbado, nunca sobrescrito (nova versão é sempre um arquivo novo) e citando no topo o documento em que se baseou. Com isso, o conteúdo de `discovery/<cliente>/`, listado em ordem, mostra a evolução completa do projeto com aquele cliente.

## Estrutura de pastas

```
clients/exemplo.yaml                    # modelo, versionado
clients/<id>.yaml                       # configuração de cada cliente real (gitignored)

reports/<carimbo>-<cliente>/            # etapa 1: dados brutos (gitignored)
  raw.json
  raw.md

discovery/<cliente>/                    # etapas 2 e 3: o que se lê e se compartilha (gitignored)
  scraping-<carimbo>.md                 # relatório
  reuniao-<carimbo>.md                  # roteiro de reunião
  docs-internos/                        # documentos das reuniões (você coloca aqui)
    AAAA-MM-DD-<tipo>-<assunto>.<ext>
  cruzamento-<carimbo>.md               # cruzamento (um por agenda, encadeado)
  contatos-<carimbo>.csv                # contatos para importar no Odoo (res.partner)
  contatos-ajustes-<carimbo>.yaml       # valores vindos das atas, aplicados no próximo CSV
  <tipo-descritivo>-<carimbo>.md        # outros materiais (cotação, resumo, ...)
```

`reports/`, `discovery/` e `clients/*.yaml` (exceto `exemplo.yaml`) ficam fora do git — contêm dados de clientes, inclusive nomes de sócios e CNPJ.

## Testes

```bash
uv run pytest
```

## Evoluindo a ferramenta

Mudanças de comportamento (novo coletor, nova seção do relatório, nova regra da skill) passam pelo fluxo OpenSpec deste repositório: `/opsx:explore` para pensar, `/opsx:propose` ou os passos manuais de `openspec new change` para criar um change, `/opsx:apply` para implementar e `/opsx:archive` para fechar. As specs vigentes ficam em `openspec/specs/` (`web-discovery` e `discovery-skill`).