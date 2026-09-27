## Context

A skill `/discovery` já usa carimbo de data e hora, imutabilidade e citação da base para três artefatos fixos: relatório (`scraping-*.md`), roteiro (`reuniao-*.md`) e cruzamento (`cruzamento-*.md`), todos em `discovery/<cliente>/`. Motivação em proposal.md; comportamento esperado na spec `discovery-skill`. Não há mudança de código Python.

## Goals / Non-Goals

**Goals:**
- Estender o mesmo padrão a qualquer material novo, sem fechar a lista de tipos.

**Non-Goals:**
- Definir o conteúdo ou as seções de materiais futuros (cada tipo terá seu próprio formato, conforme a necessidade).

## Decisions

**1. Regra geral em vez de lista fechada de tipos.**
Um requisito novo na spec `discovery-skill`, aplicável a "todo material além dos três já especificados", com `<tipo-descritivo>` livre. Alternativa descartada: especificar cada tipo (cotação, resumo, apresentação) à medida que surgir, o que exigiria um change a cada novo tipo de documento.

**2. Reaproveita as regras já existentes.**
Carimbo `AAAA-MM-DD_HHMMSS`, imutabilidade e citação da base já valem para os três artefatos fixos; a regra geral só estende esse mesmo comportamento, sem introduzir mecanismo novo.

## Risks / Trade-offs

- [Nome de tipo inconsistente entre materiais parecidos] → Aceito: `<tipo-descritivo>` livre prioriza flexibilidade; um glossário informal pode surgir na prática (ex.: `cotacao-*`, `resumo-*`).
