## Context

A skill `/discovery` (etapa 2) hoje lê `reports/<carimbo>-<cliente>/raw.*` e escreve em `discovery/<cliente>/` o relatório `scraping-<carimbo>.md` e o roteiro `reuniao-<carimbo>.md`. O relatório traz hipóteses numeradas (H1, H2, ...) com nível de confiança, e o roteiro tem perguntas numeradas. Motivação e escopo em proposal.md; comportamento esperado na spec `discovery-skill`. Não há mudança de código Python.

## Goals / Non-Goals

**Goals:**
- Cruzar material de reuniões com o scraping sem perder a rastreabilidade.
- Manter o relatório do scraping como "o que a web mostrou" e registrar a revisão em documento novo.

**Non-Goals:**
- Indexar, versionar ou organizar automaticamente os documentos do cliente.
- OCR automático de imagens: a leitura de imagens é visual, feita pelo Claude.
- Outras pastas (por exemplo `docs-cliente/`), que ficam para depois.

## Decisions

**1. Documentos em `discovery/<cliente>/docs-internos/`.**
Dentro da pasta do cliente, junto do relatório e do roteiro, e já coberto pelo `.gitignore` de `discovery/`. O nome `docs-internos` deixa espaço para outras pastas no futuro. Alternativa descartada: pasta na raiz (`documentos/<cliente>/`), que separaria o material do cliente do restante do discovery.

**2. Nome sugerido, não obrigatório.**
`AAAA-MM-DD-<tipo>-<assunto>.<ext>` ordena o histórico e ajuda a inferir como ler cada arquivo (ata, transcricao, fluxo, planilha, email, proposta). A skill não rejeita arquivos fora do padrão: usa a data de modificação e o conteúdo.

**3. Cruzamento como novo arquivo, encadeado.**
`cruzamento-<carimbo>.md` é sempre um arquivo novo. O primeiro parte do relatório de scraping mais recente; os seguintes partem do último cruzamento, de modo que as hipóteses evoluem (H3: palpite → provável → fato) sem reescrever nada. Alternativa descartada: reescrever o relatório, que misturaria "o que a web mostrou" com "o que o cliente disse" e perderia o histórico.

**4. Leitura por formato com ferramentas já disponíveis.**
Texto e Markdown: leitura direta. PDF: `pdftotext`. `.docx`: `pandoc` para texto. Planilhas: conversão para CSV com LibreOffice. Imagens: leitura visual pelo Claude, descrevendo o fluxo em texto e marcando como **[interpretação de imagem]**. Não se adiciona dependência ao projeto. Alternativa descartada: bibliotecas Python de leitura (`python-docx`, `pypdf`) e OCR, que acrescentariam dependências para um trabalho que a skill já faz.

**5. Conteúdo do cruzamento em seções fixas.**
Documentos considerados e não lidos; hipóteses atualizadas (antes → depois, com o documento); roteiro respondido e em aberto; contradições (sem arbitrar); impacto em escopo, dimensionamento e riscos; novas lacunas e perguntas. As contradições listam as duas fontes e não escolhem, porque quem decide é o consultor.

**6. Regras de fidelidade herdadas.**
Toda afirmação cita arquivo e trecho ou página. O que o usuário disser na conversa entra como informado por ele. Documentos são imutáveis, como os dados brutos.

## Risks / Trade-offs

- [Desenho à mão interpretado errado] → Marcar como interpretação de imagem e pedir conferência com o cliente.
- [Documento grande estoura o contexto] → Ler por partes, priorizar o que responde hipóteses e perguntas, e registrar o que não foi lido.
- [Conteúdo sensível de clientes vazar] → Pasta dentro de `discovery/`, ignorada pelo git.
- [Documentos com informações conflitantes entre si] → Listar como contradição entre documentos, sem escolher.
- [Ferramentas de conversão ausentes em outra máquina] → Listar o arquivo como não lido com o motivo, sem abortar; documentar as ferramentas usadas.
