## Context

O CSV-modelo (`contatoexemplo/Contato (res.partner).csv`) é uma exportação do Odoo com 27 colunas, campos de lista em linhas extras e identificadores `l10n_br_fiscal.cnae_<dígitos>`. A matriz tem os dados completos da BrasilAPI em `cnpj.dados`; as filiais só têm um resumo em `filiais` (`collectors/filiais.py::_summarize`). Ver proposal.md para a motivação.

## Goals / Non-Goals

**Goals:**
- Gerar, cliente a cliente, um CSV que o Odoo importe sem ajuste manual de colunas.
- Permitir que valores vindos das atas entrem no CSV sem que a IA toque no formato.

**Non-Goals:**
- Outros modelos do Odoo (produtos, plano de contas) e contatos que não sejam cliente e filiais.
- Geocodificação, validação do vendedor ou da indústria contra o Odoo do cliente, e hierarquia matriz/filial (`parent_id`).

## Decisions

**1. Exportação em Python, subcomando `discovery contatos`.** A transformação é determinística e o formato é rígido; em código ela é testável e, se o Odoo mudar o formato, muda só o script. Alternativa: a skill gerar o CSV, rejeitada por risco de quebrar aspas, colunas e linhas extras.

**2. Ajustes em arquivo separado (opção B).** A skill grava `contatos-ajustes-*.yaml` e o Python o aplica, de modo que o formato do CSV é responsabilidade só do script e cada valor tem fonte auditável. Alternativa: a skill editar o CSV (opção A), rejeitada pelo mesmo risco. O YAML é indexado por CNPJ:

```yaml
"07.294.692/0001-77":
  vendedor: {valor: "Fernando Colus", fonte: "docs-internos/2026-09-30-ata-kickoff.md: 'o comercial é o Fernando'"}
```

Só as colunas Vendedor, Indústrias, Telefone, E-mail, Site e coordenadas são ajustáveis; identidade fiscal (razão social, CNPJ, CNAE) sempre vem da Receita.

**3. Ampliar `filiais` em vez de reconsultar a API no subcomando.** `discovery contatos` não acessa a web, conforme o contrato de dois estágios. O coletor passa a guardar, por estabelecimento, os campos completos e `FORMAT_VERSION` sobe para 2. Alternativa: guardar o JSON inteiro da API por filial, rejeitada por inchar o `raw.json`; guardam-se só os campos usados pelo CSV.

**4. Valores fixos no código.** Idioma, país e as duas contas ficam como constantes do módulo. Alternativa: configuração no `clients/<id>.yaml`; adiada até haver um cliente com plano de contas diferente.

**5. Normalizações.** Telefone sem a aspa de planilha; CNPJ sempre mascarado; estado por tabela UF→nome + " (BR)"; descrição do CNAE no texto com o mesmo truncamento do exemplo (~70 caracteres com "..."), mas a coluna `/Nome` com a descrição completa. Latitude/Longitude vazias por padrão em vez do `0.0` do exemplo.

**6. Perfil fiscal.** Mapeado de `opcao_pelo_simples`/`opcao_pelo_mei` para os textos do Odoo ("Contribuinte Simples Nacional", "Não Contribuinte"); regimes não cobertos saem vazios.

## Risks / Trade-offs

- [Vendedor/Indústria não existirem no Odoo do cliente e a importação falhar] → só valores explícitos nas atas, com fonte; o comando lista o que aplicou.
- [Dado da Receita desatualizado (telefone, e-mail)] → os ajustes das atas corrigem Telefone e E-mail; o CSV cita a base.
- [Execuções antigas sem dados completos de filiais] → o CSV sai só com a matriz e o comando avisa.
- [Nome exato do perfil fiscal ou da natureza jurídica divergir do Odoo] → tabelas pequenas e cobertas por teste contra o CSV-modelo.
- [Mais chamadas à BrasilAPI no scan] → nenhuma: a mesma resposta já consultada passa a ser guardada por inteiro (nos campos usados).

## Migration Plan

`raw.json` antigos continuam legíveis; a leitura trata a ausência dos campos novos. Sem rollback necessário: os campos novos são aditivos.

## Open Questions

- As contas `2.1.1.01` e `1.1.2.01` são as mesmas em todos os bancos da Escodoo? Se variarem, passam a vir de `clients/<id>.yaml` sem mudar os specs.
- O Odoo aceita o campo `Natureza Jurídica` e o `Perfil Fiscal` pelo texto exato do exemplo em todos os casos? Validar importando o CSV de um cliente real.
