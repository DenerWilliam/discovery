## 1. Estrutura de pastas

- [x] 1.1 Verificar que `discovery/<cliente>/docs-internos/` é ignorada pelo git (`git check-ignore`) e documentar a pasta e a convenção de nomes `AAAA-MM-DD-<tipo>-<assunto>.<ext>`; verificar com `git check-ignore -v` em um caminho de exemplo

## 2. Skill

- [x] 2.1 Acrescentar o modo `--cruzar` à skill (entrada, passos, base = relatório mais recente ou último cruzamento, casos sem documentos e sem relatório); verificar invocando `/discovery <cliente> --cruzar` sem `docs-internos/` e conferindo que nada é gravado
- [x] 2.2 Documentar na skill a leitura por formato (texto, PDF por `pdftotext`, `.docx` por `pandoc`, planilhas por LibreOffice para CSV, imagens por leitura visual) e a listagem de arquivos não lidos com o motivo; verificar com um arquivo ilegível e um formato desconhecido
- [x] 2.3 Definir na skill o documento de cruzamento (seções fixas, hipóteses antes e depois, roteiro respondido, contradições sem arbitrar, impacto, novas lacunas, rastreabilidade e marca de interpretação de imagem), gravado em `discovery/<cliente>/cruzamento-<carimbo>.md`; verificar que relatório, roteiro e documentos permanecem inalterados (hash)
- [x] 2.4 Espelhar a skill em `.opencode/` e verificar com `diff` que as duas cópias são idênticas

## 3. Verificação com documentos de exemplo

- [x] 3.1 Criar documentos de exemplo sintéticos (ata `.md`, PDF, `.docx` e imagem de um fluxo) em um cliente de teste, executar `--cruzar` e verificar hipóteses atualizadas, roteiro respondido, contradição e imagem marcada como interpretação
- [x] 3.2 Executar `--cruzar` uma segunda vez e verificar que o novo cruzamento parte do anterior, que o primeiro é preservado e que os documentos seguem inalterados; remover em seguida o cliente de teste

## 4. Documentação

- [x] 4.1 Atualizar `CLAUDE.md` e `README.md` com a pasta `docs-internos/`, o modo `--cruzar` e o documento de cruzamento; verificar que os comandos documentados existem na skill
