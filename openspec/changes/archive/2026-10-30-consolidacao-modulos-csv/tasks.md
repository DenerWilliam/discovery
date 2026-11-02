## 1. Módulo de consolidação

- [x] 1.1 Criar `src/discovery/consolidar.py` com função `consolidar_modulos()` que lê descobertas e retorna `(output_file, count)`. Verificar: função existe, importável, signature correta
- [x] 1.2 Implementar parsing regex de `discovery/*/scraping-*.md` para extrair fases e tabelas de módulos. Verificar: `extract_modules_from_discovery()` funciona com exemplo real (Americanas)
- [x] 1.3 Implementar mapeamento de horas (3 níveis: exato, substring, fallback). Verificar: `get_horas()` retorna "40" para "Contatos", "320" para "eCommerce"
- [x] 1.4 Implementar estimativa de complexidade por palavras-chave. Verificar: `estimate_complexity()` retorna "Alta" para "múltiplos", "Média" por padrão
- [x] 1.5 Implementar escrita de CSV consolidado com 7 colunas (cliente, modulo, enterprise, fase, evidencia, complexidade, horas_padrao). Verificar: CSV válido (RFC 4180), headers corretos

## 2. Script standalone

- [x] 2.1 Criar `scripts/consolidar-modulos.py` que importa de `src/discovery/consolidar.py` e expõe CLI via argparse com flags `--client`, `--output`. Verificar: `python3 scripts/consolidar-modulos.py --help` exibe ajuda, --client e --output listados
- [x] 2.2 Implementar lógica de erro handling (arquivo não encontrado, escrita falha). Verificar: `python3 scripts/consolidar-modulos.py` sem descobertas exibe erro e exit code 1

## 3. Integração com CLI discovery

- [x] 3.1 Adicionar subcomando `consolidar-modulos` ao parser em `src/discovery/cli.py`. Verificar: `uv run discovery consolidar-modulos --help` exibe ajuda
- [x] 3.2 Implementar função `run_consolidar_modulos()` que chama `consolidar_modulos()`. Verificar: `uv run discovery consolidar-modulos` roda sem erro e gera CSV em current dir
- [x] 3.3 Integrar com main() para rotear comando `consolidar-modulos`. Verificar: `uv run discovery consolidar-modulos --client americanas` consolida apenas Americanas (20 módulos)

## 4. Testes

- [x] 4.1 Testar consolidação com descobertas reais: rodar `uv run discovery consolidar-modulos` sem argumento e validar CSV contém 134+ módulos de 4+ clientes. Verificar: descoberta-modulos-consolidado-*.csv existe, 134+ linhas (header + data)
- [x] 4.2 Testar filtro por cliente: rodar `discovery consolidar-modulos --client americanas` e validar 20 módulos. Verificar: CSV tem 21 linhas (header + 20 dados), todos com cliente="americanas"
- [x] 4.3 Testar mapeamento de horas: validar que módulos têm valores em horas_padrao. Verificar: coluna `horas_padrao` tem valores para 80%+ dos módulos (fallback funciona)
- [x] 4.4 Testar complexidade estimada: validar distribuição (Média > Alta > Baixa). Verificar: CSV mostra Alta=6, Média=128, Baixa=0 (proporções esperadas)
- [x] 4.5 Testar Enterprise flag: validar que módulos com "(E)" têm enterprise="Sim". Verificar: eCommerce, Contabilidade, Pagamentos têm enterprise="Sim" (49 módulos)
- [x] 4.6 Testar edge cases: descoberta sem módulos, cliente inexistente, arquivo corrompido. Verificar: erro reportado, exit code apropriado, nenhum crash

## 5. Documentação

- [x] 5.1 Atualizar `CLAUDE.md` com novo comando `consolidar-modulos` e exemplos de uso. Verificar: CLAUDE.md listado no git, comandos documentados
- [x] 5.2 Criar exemplos de uso no README ou em comentários do script (docstring). Verificar: help text contém exemplos, módulo tem docstring descritivo

## 6. Código cleanup e validação

- [x] 6.1 Validar que `consolidar.py` e `cli.py` seguem conventions do projeto (imports, type hints, docstrings). Verificar: `pytest -xvs` passa sem novos problemas de lint (se houver linter configurado)
- [x] 6.2 Validar que não há imports desnecessários, nomes descritivos, funções < 50 linhas. Verificar: código é legível por usuário novo, não há dead code
- [x] 6.3 Executar testes unitários se existentes (mock de files, regex). Verificar: testes passam, cobertura 80%+ para funções públicas

## 7. Commit e integração

- [x] 7.1 Fazer commit com mensagem clara descrevendo feature (consolidação de módulos em CSV). Verificar: `git log --oneline` mostra commit novo
- [x] 7.2 Validar que feature está pronta para produção: rodar `uv run discovery consolidar-modulos` e `uv run discovery consolidar-modulos --client americanas` sem erro. Verificar: ambos geram CSVs válidos, mensagens claras ao usuário
