## 1. Coletor de site

- [x] 1.1 Em `collect_site`, tratar o evento `download` (e o erro "Download is starting" como reserva): cancelar o download, registrar `Source("site", url, NAO_COLETADA, erro="arquivo para download")` e seguir para o próximo link
- [x] 1.2 Contar no limite de `max_pages` apenas as páginas HTML tentadas; manter `visited` para não repetir URLs
- [x] 1.3 Limitar o número de downloads registrados por execução (teto separado)

## 2. Testes

- [x] 2.1 Em `tests/test_site.py`, acrescentar ao servidor HTTP local um endpoint sem extensão com `Content-Disposition: attachment` e uma página que o linka
- [x] 2.2 Teste: o download vira `nao_coletada` com motivo "arquivo para download", não `falha`
- [x] 2.3 Teste: downloads não consomem `max_pages` (com `max_pages` pequeno, as páginas HTML seguintes ainda são visitadas)
- [x] 2.4 Rodar `uv run pytest` inteiro

## 3. Verificação

- [x] 3.1 Refazer `uv run discovery scan --client palver` e conferir que os relatórios aparecem como `nao_coletada` (verificado em `reports/2026-09-30_160740-palver`; produtos e FAQ são seções da mesma página, não páginas separadas)
- [x] 3.2 Sincronizar o delta em `openspec/specs/web-discovery/spec.md` e arquivar a change
