## Why

Na varredura da Palver (`reports/2026-09-30_160133-palver`), 11 das 14 tentativas de página falharam com `Page.goto: Download is starting`. Eram links sem extensão (`/api/surveys/.../report`, `/press-release`) que servem arquivos para download; o filtro `SKIP_EXTENSIONS` só olha a extensão do caminho e não os pegou. Os downloads eram registrados como `falha`, poluindo os dados brutos, e consumiam o orçamento de `max_pages` (15), o que podia deixar páginas HTML de fora em sites com muitos anexos. Na Palver as páginas HTML relevantes já tinham sido todas visitadas (3), então o impacto ali foi só o ruído e a perda de visibilidade dos arquivos.

## What Changes

- O coletor de site passa a reconhecer um link que responde com download (evento `download` do Playwright) e a tratá-lo como **arquivo para download**, não como falha de página.
- Arquivos para download **não contam** para `max_pages`: o orçamento é gasto só com páginas HTML.
- Cada arquivo encontrado é registrado nos dados brutos como fonte `site` com status `nao_coletada` e o motivo "arquivo para download", sem ler o conteúdo, para que o consultor saiba que existe material a baixar à mão.
- Sem mudança em `versao_formato`: usa os campos e status já existentes em `Source`.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `web-discovery`: o requisito "Varredura do site oficial" passa a definir o tratamento de links que servem arquivos para download (não contam no limite de páginas e ficam registrados como não coletados).

## Impact

- Código: `src/discovery/collectors/site.py` (`collect_site`) e seus testes em `tests/` (servidor HTTP local com um endpoint que envia `Content-Disposition: attachment`).
- Dados brutos: novas entradas `nao_coletada` no lugar de `falha` para downloads; nenhuma mudança de formato.
- Skill `/discovery`: o relatório pode listar esses arquivos como próximo passo manual (já previsto nas regras para links não coletados); sem alteração obrigatória.