## ADDED Requirements

### Requirement: Ajustes de contatos a partir dos documentos
No modo `--cruzar`, quando existir ao menos um CSV de contatos do cliente e os documentos de `docs-internos/` trouxerem valores explícitos para Vendedor, Indústria, Telefone, E-mail, Site ou coordenadas de um estabelecimento, a skill SHALL gravar um novo `discovery/<cliente>/contatos-ajustes-<AAAA-MM-DD_HHMMSS>.yaml` com esses valores, cada um com o arquivo e o trecho de origem, e SHALL orientar a executar `discovery contatos` para gerar o CSV atualizado. A skill SHALL NOT editar o CSV, SHALL NOT propor valores para colunas fora da lista acima e SHALL NOT registrar valores inferidos: o que os documentos não afirmarem explicitamente fica de fora e é listado no cruzamento como pendente.

#### Scenario: Ata cita o vendedor responsável
- **WHEN** uma ata afirma quem é o vendedor de um cliente já presente no CSV
- **THEN** a skill grava o ajuste com o vendedor, o nome do arquivo e o trecho da ata, e não altera o CSV

#### Scenario: Valor apenas sugerido
- **WHEN** um documento só sugere ou deixa implícita a indústria
- **THEN** a skill não grava o valor no ajuste e o lista como pendente de confirmação

#### Scenario: Sem CSV de contatos
- **WHEN** não existe CSV de contatos do cliente
- **THEN** a skill não grava ajustes e informa que `discovery contatos` deve ser executado antes
