## 1. Coleta das filiais

- [x] 1.1 Ampliar `_summarize` em `collectors/filiais.py` com razão social, endereço, CEP, telefone, e-mail, natureza jurídica, capital social, regime tributário e CNAEs secundários, e verificar com teste que os campos aparecem com `httpx.MockTransport`
- [x] 1.2 Subir `FORMAT_VERSION` para 2 em `models.py` e verificar que os testes de `storage` e `cli` passam (`uv run pytest`)

## 2. Exportação do CSV

- [x] 2.1 Criar o módulo de exportação com as 27 colunas na ordem do modelo e teste que compara o cabeçalho com `contatoexemplo/Contato (res.partner).csv`
- [x] 2.2 Implementar matriz e filiais do `raw.json` com linhas extras de CNAE secundário e verificar com teste de contato com 3 CNAEs secundários
- [x] 2.3 Implementar as normalizações (CNPJ mascarado, telefone limpo, UF→nome + " (BR)", ID e texto do CNAE, perfil fiscal, constantes) e verificar com testes unitários por regra
- [x] 2.4 Tratar execução antiga sem dados completos de filiais (só a matriz, com aviso) e fonte `cnpj` sem sucesso (erro sem gravar) e verificar com testes

## 3. Arquivo de ajustes

- [x] 3.1 Ler `contatos-ajustes-*.yaml` (mais recente ou indicado) e aplicar apenas nas colunas permitidas, ignorando com aviso colunas protegidas, valores sem fonte e CNPJ desconhecido, e verificar com testes de cada caso
- [x] 3.2 Gravar o CSV novo com carimbo, citando base e ajustes, sem sobrescrever arquivos, e verificar que duas execuções geram dois arquivos

## 4. CLI

- [x] 4.1 Registrar `discovery contatos` (`--client`, `--run`, `--ajustes`) em `cli.py` e verificar com teste de ponta a ponta que lê um `raw.json` de fixture e grava o CSV em `discovery/<cliente>/`
- [ ] 4.2 Rodar `uv run discovery contatos --client haix` sobre uma execução real e importar o CSV no Odoo de teste para confirmar o formato

## 5. Skill

- [x] 5.1 Acrescentar ao modo `--cruzar` a geração de `contatos-ajustes-*.yaml` (valores explícitos com fonte, pendências no cruzamento) em `.claude/skills/discovery/` e espelhar em `.opencode/skills/discovery/`, verificando com `diff -r` que são idênticos
- [x] 5.2 Atualizar o `CLAUDE.md` e o README com o subcomando, o layout de `discovery/<cliente>/` e verificar que descrevem `contatos-*.csv` e `contatos-ajustes-*.yaml`
