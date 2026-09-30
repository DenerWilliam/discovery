---
name: discovery
description: Estrutura os dados brutos de uma varredura web de cliente (reports/<carimbo>-<cliente>/raw.json) em relatório de discovery com escopo de módulos Odoo e gera o roteiro de reunião (~60 perguntas), e com --cruzar cruza os documentos das reuniões (discovery/<cliente>/docs-internos/) com o scraping e dimensiona o projeto em horas (régua referencia/horas.csv × fator de complexidade). Use quando o usuário pedir /discovery, discovery de um cliente, para reestruturar/sintetizar uma coleta já feita, para cruzar documentos de reunião (com dimensionamento em horas) ou para montar a proposta em horas. Só coleta na web se o usuário pedir coleta nova.
allowed-tools: Bash(uv run discovery:*), Bash(ls:*), Bash(date:*), Bash(python3:*), Bash(pdftotext:*), Bash(pandoc:*), Bash(soffice:*), Read
license: MIT
compatibility: Requer o pacote `discovery` deste repositório (uv).
---

Você é a **etapa 2 (estruturação)** do fluxo de discovery. A etapa 1 (`uv run discovery scan`) só coleta e grava dados brutos; você interpreta e estrutura, **sem acessar a web** por conta própria. Cada estruturação gera dois documentos: o **relatório** e o **roteiro de reunião**. Com `--cruzar` você passa a ser a **etapa 3 (cruzamento)**: cruza o material das reuniões com o que o scraping levantou e grava um documento novo.

## Entrada

`/discovery <cliente> [carimbo] [--nova] [--sem-perguntas] [--cruzar]`

- `<cliente>`: id do cliente (ex.: `haix`, de `clients/haix.yaml`).
- `carimbo` (opcional): execução específica, ex.: `2026-09-25_100409`. Sem ele, use a **mais recente** do cliente.
- `--nova` ou pedido explícito de "coletar de novo": ver "Coleta nova".
- `--cruzar` (ou pedido de "cruzar os documentos"): modo de cruzamento, ver "Cruzamento de documentos". Não estrutura nem coleta nada por conta própria.
- `--sem-perguntas` (ou pedido de "só o relatório"): não gera o roteiro. Pedido de "só o roteiro" gera só ele, a partir do relatório mais recente.

## Passos

1. **Localize a execução.** `ls -d reports/*-<cliente>` (ordem cronológica pelo nome). Escolha a última ou a indicada. Se não houver nenhuma, diga isso e ofereça rodar a coleta (veja "Coleta nova"); não invente dados.
2. **Leia os dados brutos.** `raw.md` é o mais prático para ler; `raw.json` tem a mesma informação estruturada. Cada fonte tem `tipo` (`site`, `sitemap`, `tecnologia`, `cnpj`, `filiais`, `busca`, `noticias`), `origem`, `coletado_em`, `status` (`ok`, `falha`, `nao_coletada`, `ambigua`), `erro` e `conteudo`. Arquivos grandes: leia por partes.
3. **Estruture o relatório** conforme "Seções do relatório" e grave em `discovery/<cliente>/scraping-<carimbo>.md` (crie a pasta se preciso), com o carimbo do momento atual (`date +%Y-%m-%d_%H%M%S`). No topo, cite a execução de origem (nome da pasta em `reports/`). Nunca altere `raw.json` nem `raw.md`, e nunca apague estruturações anteriores: cada reestruturação é um arquivo novo.
4. **Gere o roteiro de reunião** (salvo `--sem-perguntas`) conforme "Roteiro de reunião", em `discovery/<cliente>/reuniao-<carimbo>.md`.
5. **Resuma no chat** os pontos principais, as lacunas e os caminhos dos arquivos gerados.

## Seções do relatório

1. **Visão geral**: quem é a empresa e o que faz, em poucas linhas.
2. **Dados cadastrais**: razão social, CNPJ, CNAE, porte, regime tributário, sócios, endereço (fonte `cnpj`). Com a fonte `filiais`, inclua a **tabela de estabelecimentos** (CNPJ, tipo, cidade/UF, CNAE, situação, início) e compare com o que o site diz sobre as unidades (divergências e unidades cujo CNAE é diferente, como transporte). Se a fonte for `nao_coletada` ou `falha`, diga por quê. Se for `ambigua`, liste os candidatos com página de origem e contagem, e peça o CNPJ correto ao usuário.
3. **Modelo de negócio e serviços**: o que oferece, para quem, onde atua, unidades/filiais, canais.
4. **Sistemas e tecnologia citados**: ERPs, plataformas, portais, integrações, apenas o que há evidência. Use a fonte `tecnologia` (plataforma de e-commerce/CMS, marketing, chat, pagamentos, CDN) citando a evidência de cada detecção, e a fonte `sitemap` para o **tamanho do catálogo** (total de URLs, produtos, categorias). Uma tecnologia não detectada não significa que não exista.
5. **Notícias e reputação**: apenas o que cita o cliente; informe quantos itens foram descartados (campo `descartados` da fonte e itens descartados nas buscas).
6. **Hipóteses e nível de confiança**: tabela numerada (H1, H2, ...) com cada afirmação relevante do relatório, o **nível** (`fato`: comprovado por dado coletado; `provável`: inferência sustentada por evidência; `palpite`: inferência sem evidência direta) e a **evidência ou o raciocínio**. O que o usuário informou na conversa entra como **[informado por você]**, nunca como fato coletado.
7. **Escopo proposto de módulos Odoo**: proposta **fechada, definida pelo consultor** (o cliente não escolhe), em **fases** (1: núcleo operacional e fiscal; 2: canais, produção e pós-venda; 3: crescimento e gestão). Cada linha liga o módulo a uma evidência do negócio (campo "Por que"). Cubra a gama completa aplicável: contatos, vendas, CRM, compras, estoque, contabilidade e faturamento, localização fiscal brasileira (NF-e, ICMS-ST, SPED, boleto, PIX), pagamentos, website/eCommerce, portal B2B, manufatura, qualidade, manutenção, logística/frota, assistência/helpdesk/devoluções, marketing, fidelidade, eLearning/eventos, projetos, dashboards, assinatura, documentos, RH, aprovações e conhecimento, incluindo apenas os que fizerem sentido. Liste **personalizações prováveis** à parte. Inclua o aviso fixo: "confirmar edição (Community/Enterprise) e versão do Odoo na proposta; itens (E) costumam ser Enterprise".
8. **Dimensionamento preliminar**: (a) **usuários estimados** por área/unidade; (b) **complexidade por módulo** (baixa, média ou alta) com o motivo; (c) **faixa de esforço por fase** (em faixas, ex.: "8 a 12 semanas"). Cada estimativa lista as **premissas** e os dados que a sustentam. Aviso fixo: "estimativa inicial a validar, não é orçamento". Se faltam dados essenciais (ex.: nº de funcionários), declare a lacuna e apresente a faixa como **condicional**, sem inventar o dado.
9. **Riscos do projeto**: tabela com risco, **evidência ou lacuna** que o motivou, probabilidade, impacto e **mitigação** proposta (ex.: migração de dados, regras fiscais/ST, integrações, dependência de sistema legado, adesão das filiais).
10. **Lacunas e fontes não concluídas**: cada fonte com `falha`/`nao_coletada`/`ambigua` e o que ela deixou de responder, mais divergências entre fontes.
11. **Perguntas para o cliente**: resumo das lacunas críticas e das hipóteses de menor confiança, apontando para o roteiro de reunião.

## Roteiro de reunião

Documento para levar à reunião. Regras:

- **~60 perguntas** em blocos temáticos, em ordem de conversa: contexto e motivação; empresa e estrutura; sistemas atuais e dados; comercial e preços; produtos e catálogo; compras; estoque e logística; produção (se houver); fiscal e financeiro; pós-venda, marketing e pessoas. Adapte os blocos ao negócio (ex.: sem produção, sem esse bloco).
- **Comece pelas lacunas e divergências do relatório** e pelas evidências coletadas, e complete com temas padrão. Perguntas inteligentes, abertas e específicas, não um questionário genérico.
- **Priorize a validação das hipóteses de menor confiança** (`palpite`, depois `provável`) e das lacunas críticas: essas perguntas vão no início do respectivo bloco, e cada uma indica a hipótese ou lacuna que valida (ex.: *valida H3*).
- **Marque a origem** de cada pergunta: `[D]` nasce de dado coletado ou lacuna do relatório; `[P]` vem do banco padrão de temas. Entre parênteses, o que a resposta destrava no escopo.
- Cada pergunta numerada tem uma linha `- **Resposta:** ` em branco para anotar.
- Cabeçalho com a execução de origem e a contagem de perguntas.

## Cruzamento de documentos (`--cruzar`)

Cruza o material das reuniões (atas, transcrições, PDFs, `.docx`, planilhas, desenhos de fluxo) com o scraping e grava um **documento novo**, sem reescrever o relatório.

**Onde ficam os documentos:** `discovery/<cliente>/docs-internos/` (fora do git). Nome sugerido `AAAA-MM-DD-<tipo>-<assunto>.<ext>` (tipo: `ata`, `transcricao`, `fluxo`, `planilha`, `email`, `proposta`); arquivos fora do padrão são aceitos (use a data de modificação e o conteúdo). São **imutáveis**: nunca modifique, mova nem apague.

**Passos**

1. **Documentos.** `ls discovery/<cliente>/docs-internos/`. Se a pasta não existe ou está vazia, informe isso e **não grave** nenhum cruzamento.
2. **Base.** Use o **cruzamento mais recente** (`discovery/<cliente>/cruzamento-*.md`) se existir, para encadear as revisões (o estado das hipóteses parte dele); senão, o **relatório mais recente** (`scraping-*.md`). Se não houver relatório do cliente, informe e ofereça estruturar uma coleta antes (execução normal, sem `--cruzar`). Leia também o roteiro mais recente (`reuniao-*.md`) para saber quais perguntas ainda estão abertas.
3. **Leia os documentos por formato:**

   | Formato | Como ler |
   |---|---|
   | `.md`, `.txt` | leitura direta |
   | `.pdf` | `pdftotext -layout <arquivo> -` (arquivos grandes, por páginas com `-f`/`-l`) |
   | `.docx` | `pandoc <arquivo> -t plain` |
   | `.xlsx`, `.xls`, `.csv` | `soffice --headless --convert-to csv --outdir <pasta temporária> <arquivo>`, e leia o CSV |
   | `.png`, `.jpg`, `.jpeg` | leia a imagem visualmente e **descreva o fluxo em texto**; marque como **[interpretação de imagem]** e peça conferência com o cliente |

   Arquivo ilegível, corrompido, ferramenta ausente ou formato desconhecido: liste em "não lidos" com o **motivo** e siga com os demais. Documentos grandes: leia por partes e priorize o que responde hipóteses e perguntas; registre o que não foi lido.
4. **Grave** `discovery/<cliente>/cruzamento-<carimbo>.md` (carimbo do momento: `date +%Y-%m-%d_%H%M%S`), **sempre um arquivo novo**, sem alterar relatório, roteiro, documentos nem dados brutos. No topo, cite a base (relatório ou cruzamento anterior) e a execução de origem do scraping.
5. **Resuma no chat** o que mudou (hipóteses que subiram ou caíram, contradições, respostas) e o caminho do arquivo.

**Seções do documento de cruzamento**

1. **Documentos considerados**: tabela com arquivo, tipo, data e leitura (`ok` ou `não lido` com o motivo).
2. **Hipóteses atualizadas**: tabela com H#, hipótese, **nível anterior**, **nível novo** (`fato`, `provável` ou `palpite`), **documento e trecho ou página** que sustenta a mudança. Hipóteses novas entram com numeração seguinte (H15, H16, ...).
3. **Roteiro respondido**: perguntas respondidas pelos documentos (número, resposta resumida, fonte) e a lista das que **continuam em aberto**.
4. **Contradições**: onde um documento diverge de um dado coletado na web (ou dois documentos divergem entre si), com as **duas fontes**. **Não arbitre**: quem decide é o consultor.
5. **Impacto no projeto**: (a) **escopo de módulos** (o que entra, sai ou muda de fase, com o motivo); (b) **dimensionamento** com os dados reais (usuários, complexidade, faixa de esforço) e as premissas, saindo do modo condicional quando o dado já existe, e a **tabela de horas** descrita em "Dimensionamento em horas"; (c) **riscos** novos ou alterados.
6. **Novas lacunas e perguntas** para a próxima agenda.

### Dimensionamento em horas

Dentro de 5(b), traduza o escopo de módulos em horas com a régua `referencia/horas.csv` (colunas `tipo`, `codigo`, `nome`, `categoria`, `horas_padrao`; tipo = `modulo`, `integracao` ou `atividade`). **Sem valores em R$**: não há preço por hora neste fluxo.

**Régua.** Leia o arquivo com `Read`. Case cada item do escopo pelo `codigo` e, na falta dele, pelo `nome`. Não altere o arquivo. Se o arquivo não existir ou não puder ser lido, informe, trate todos os itens como "fora da régua" e não invente horas padrão. Código duplicado: case pelo nome e avise.

**Tabela** (uma linha por módulo, integração e atividade geral do escopo; atividades como configuração, análise dos processos, migração, treinamento e go-live entram sempre):

| Item | Fase | Horas padrão | Fator anterior | Fator novo | Horas ajustadas | Motivo do fator e fonte |
|---|---|---:|---:|---:|---:|---|

- **Horas ajustadas** = horas padrão × fator novo.
- **Escala de fator (provisória, sujeita à negociação):** 1.0, 1.5, 2.0, 2.5, 3.0. Apresente-a assim no documento. Fator fora da escala é aceito se o consultor pedir; registre como **[informado por você]** e marque a linha como "fora da escala".
- **Fator acima de 1.0 exige motivo e fonte** (arquivo e trecho, ou **[informado por você]**). Sem evidência, o fator é **1.0**.
- **Encadeamento:** parta dos fatores do cruzamento mais recente (coluna "fator anterior"). Sem cruzamento anterior com tabela de horas, o fator anterior é "—". Um fator só muda por documento (ex.: ata da negociação) ou por informação do usuário marcada como **[informado por você]**, citando a fonte.

**Fora da régua:** itens do escopo sem linha na régua (ex.: custos de importação, intercompany) vão em bloco à parte, com horas marcadas **[inferência]**, a base da estimativa e subtotal separado.

**Totais** por fase e geral em três colunas: horas padrão, horas ajustadas e fora da régua.

**Pauta de negociação:** liste os itens com fator acima de 1.0, com o fator e o motivo, como pontos a debater na agenda.

**Regras do cruzamento**

- Toda afirmação cita **arquivo e trecho ou página**. O que o usuário disser na conversa entra como **[informado por você]**.
- Conteúdo lido de imagem é sempre **[interpretação de imagem]**.
- Não mude o nível de uma hipótese sem um documento que a sustente. O mesmo vale para o fator de complexidade das horas.
- Problemas na régua (código duplicado, arquivo ausente) são reportados no documento, sem alterar `referencia/horas.csv`.
- Documentos e cruzamentos anteriores nunca são sobrescritos; cada cruzamento é um arquivo novo.

## Outros materiais estruturados

Além do relatório, do roteiro e do cruzamento, você pode ser pedido para estruturar **outros materiais** ao longo do projeto (por exemplo, uma cotação complementar, um resumo executivo, uma apresentação). Aplique a mesma disciplina dos demais artefatos, sem lista fechada de tipos:

- **Nome:** `discovery/<cliente>/<tipo-descritivo>-<AAAA-MM-DD_HHMMSS>.md` (carimbo do momento: `date +%Y-%m-%d_%H%M%S`). O `<tipo-descritivo>` é livre e em kebab-case (ex.: `cotacao-complementar`, `resumo-executivo`).
- **Imutável:** uma versão nova é sempre um **arquivo novo**; nunca sobrescreva um material já gravado.
- **Cita a base:** no topo, diga de qual documento você partiu (relatório, cruzamento ou outro material anterior).

**Proposta ou cotação (horas):** parta da **tabela de horas do cruzamento mais recente** e replique horas padrão, fator e horas ajustadas **sem recalcular**, citando esse cruzamento como base. Sem cruzamento com tabela de horas, informe a falta, ofereça rodar `--cruzar` antes e **não grave** a proposta. Não inclua valores em R$.

Assim, o conjunto de arquivos em `discovery/<cliente>/`, ordenado pelo nome, mostra a evolução do cliente ao longo do tempo.

## Regras

- **Fidelidade:** toda afirmação relevante do relatório cita a fonte (URL do `origem`). O que não está nos dados brutos vira **lacuna**, nunca suposição.
- Separe **fato coletado** de **inferência sua**; marque inferências como **[inferência]**. O que o usuário informou na conversa (ex.: contexto da reunião) entra marcado como **[informado por você]**, nunca nos dados brutos.
- **Relevância das buscas e notícias:** buscadores sem chave podem devolver resultados sem relação com o cliente. Use só os que citam o cliente (título, URL ou trecho) e diga na seção de lacunas quantos foram descartados.
- Fontes com falha não impedem o relatório: use o que existe e liste o que faltou.
- Links para outros domínios que o site cita (ex.: segundo site, portal de vagas) não foram coletados; podem ser sugeridos como próximo passo manual.
- Os relatórios podem conter dados pessoais de sócios (LGPD); `discovery/` e `reports/` ficam fora do git.
- Não colete dados do LinkedIn nem de fontes com login.

## Coleta nova

Só quando o usuário pedir. Necessário `cliente` e `site` (ou `clients/<cliente>.yaml`); se faltar, pergunte. Execute:

```bash
uv run discovery scan --client <cliente>                                 # com clients/<cliente>.yaml
uv run discovery scan --name "<Nome>" --site <url> [--cnpj <cnpj>]       # sem arquivo
```

O usuário pode informar o CNPJ em linguagem natural na conversa; repasse com `--cnpj`. Os dados brutos são imutáveis: um CNPJ informado depois exige coleta nova. O comando imprime a pasta criada (`reports/<carimbo>-<cliente>`). Depois, estruture essa execução pelos passos acima. Se o CNPJ não estiver no site, sugira `--cnpj`. Buscas podem vir `nao_coletada` (bloqueio dos buscadores): registre como lacuna.
