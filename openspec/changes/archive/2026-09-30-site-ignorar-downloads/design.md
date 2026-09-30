## Context

`collect_site` mantém uma fronteira de URLs priorizadas e visita até `max_pages`, contando `visited` a cada tentativa. `SKIP_EXTENSIONS` descarta links por extensão do caminho, mas endpoints como `/api/surveys/<id>/report` não têm extensão e só revelam que são downloads quando o navegador os abre: o Playwright lança `Page.goto: Download is starting`, hoje gravado como `falha`. Ver proposal.md (Why) para o caso da Palver.

## Goals / Non-Goals

**Goals:**
- Distinguir download de falha real e não gastar o orçamento de páginas com ele.
- Deixar rastro dos arquivos encontrados nos dados brutos.

**Non-Goals:**
- Baixar ou interpretar os arquivos (PDF, planilhas): é passo manual do consultor.
- Mudar `versao_formato` ou criar novo tipo de fonte.
- Filtrar links por heurística de URL (`/api/`, `report`): frágil e específica de um cliente.

## Decisions

1. **Detectar pelo evento `download` do Playwright**, não por heurística de URL. Em `page.goto`, o erro "Download is starting" (ou `page.expect_download`/handler `page.on("download")`) é o sinal confiável. Alternativa descartada: HEAD prévio com `httpx` para ler `Content-Disposition`/`Content-Type`, que dobra as requisições e ignora cookies da sessão do navegador.
2. **Não contar download em `max_pages`.** O laço passa a comparar o teto com o número de páginas HTML tentadas, não com `len(visited)`. `visited` continua evitando repetir URLs (inclusive as de download). Como o laço depende de `frontier` esgotar, o total de tentativas permanece limitado pelo tamanho da fronteira; acrescentar um teto separado e generoso de downloads registrados (por exemplo 50) evita listas enormes em sites com muitos anexos.
3. **Registrar como `Source("site", url, NAO_COLETADA, erro="arquivo para download")`.** Reaproveita o modelo e o status existentes; `raw.md` já exibe o motivo.
4. **Fechar o download sem salvar o arquivo.** O handler cancela o download do Playwright para não deixar arquivos temporários.

## Risks / Trade-offs

- [Mensagem de erro do Playwright muda entre versões] → Preferir o handler do evento `download`; manter a checagem do texto como reserva e cobri-la em teste com Chromium real.
- [Muitos downloads enchem `raw.md`] → Teto separado de downloads registrados (decisão 2).
- [Um link que só parece download pode ser uma página com `Content-Disposition` indevido] → Aceito: o registro indica a URL e o consultor confere à mão.
