## Purpose

Gera, a partir dos dados brutos de uma execução, um CSV de contatos no formato de importação do Odoo (`res.partner` com `l10n_br_fiscal`), para cadastrar o cliente e suas filiais sem digitação e incorporar o que as reuniões descobrirem.

## ADDED Requirements

### Requirement: Subcomando de exportação de contatos
O sistema SHALL oferecer o subcomando `discovery contatos`, que lê o `raw.json` de uma execução (a mais recente do cliente, ou a indicada) e grava `discovery/<cliente>/contatos-<AAAA-MM-DD_HHMMSS>.csv`, sem alterar a execução nem arquivos existentes e sem acessar a web.

#### Scenario: Exportação a partir da execução mais recente
- **WHEN** o usuário executa `discovery contatos --client <cliente>` e existe uma execução com o CNPJ consultado com sucesso
- **THEN** é gravado um novo `contatos-<carimbo>.csv` e nenhum arquivo existente é alterado

#### Scenario: Execução indicada
- **WHEN** o usuário indica uma execução específica
- **THEN** o CSV é gerado a partir dessa execução e cita qual foi a base na saída do comando

#### Scenario: Sem CNPJ consultado
- **WHEN** a fonte `cnpj` da execução não está ok
- **THEN** o comando informa o motivo, não grava CSV e termina com código de erro

### Requirement: Formato idêntico ao da exportação do Odoo
O CSV SHALL ter as colunas, na ordem e com os nomes exatos da exportação de contatos do Odoo usada como modelo, codificação UTF-8 e todos os valores entre aspas. Cada contato SHALL ocupar uma linha principal; cada CNAE secundário além do primeiro SHALL ocupar uma linha extra, com as demais colunas vazias, no padrão de campos de lista do Odoo.

#### Scenario: Contato com vários CNAEs secundários
- **WHEN** um estabelecimento tem três CNAEs secundários
- **THEN** o CSV tem uma linha principal com o primeiro CNAE secundário e duas linhas extras com só as colunas de CNAE secundário preenchidas

#### Scenario: Estabelecimento sem CNAE secundário
- **WHEN** o estabelecimento não tem CNAE secundário
- **THEN** o CSV tem só a linha principal, com as colunas de CNAE secundário vazias

### Requirement: Um contato por estabelecimento
O CSV SHALL conter um contato para a matriz e um para cada filial da mesma raiz de CNPJ registrada na execução, cada um com o CNPJ completo de 14 dígitos formatado com máscara.

#### Scenario: Cliente com filiais
- **WHEN** a execução lista a matriz e duas filiais
- **THEN** o CSV tem três contatos, cada um com seu CNPJ mascarado e seu endereço

#### Scenario: Só a matriz conhecida
- **WHEN** a execução não tem dados completos de filiais (execução antiga ou fonte de filiais não coletada)
- **THEN** o CSV contém apenas a matriz e o comando avisa que as filiais não puderam ser incluídas

### Requirement: Origem e derivação dos valores
O sistema SHALL preencher as colunas somente com dados da execução: razão social, CNPJ, endereço, cidade, estado (nome da UF seguido de " (BR)"), CEP, telefone, e-mail, natureza jurídica, capital social e CNAEs vêm do cadastro público; o site vem do site oficial do cliente; o perfil fiscal é deduzido do regime tributário do cadastro. O identificador de cada CNAE SHALL seguir `l10n_br_fiscal.cnae_<código só com dígitos>`. Valores ausentes na origem SHALL ficar vazios, sem inventar dado.

#### Scenario: Cliente optante pelo Simples Nacional
- **WHEN** o cadastro indica opção pelo Simples Nacional
- **THEN** o perfil fiscal sai como "Contribuinte Simples Nacional"

#### Scenario: Telefone sem marcador de planilha
- **WHEN** o cadastro traz um telefone
- **THEN** o CSV o grava como texto limpo, sem a aspa inicial usada por planilhas

#### Scenario: Dado ausente no cadastro
- **WHEN** o cadastro não traz e-mail
- **THEN** a coluna E-mail fica vazia

### Requirement: Valores fixos e colunas reservadas à reunião
O sistema SHALL preencher com valores fixos o idioma (`pt_BR`), o país (`Brasil`), a conta de pagamento (`2.1.1.01 Fornecedor`) e a conta de recebimento (`1.1.2.01 Clientes`), e SHALL deixar vazias, salvo ajuste, as colunas Vendedor, Indústria principal, Indústrias Secundárias, Latitude Geográfica e Longitude Geográfica.

#### Scenario: Colunas reservadas sem ajuste
- **WHEN** não há arquivo de ajustes
- **THEN** Vendedor, Indústria principal, Indústrias Secundárias, Latitude e Longitude saem vazias

### Requirement: Arquivo de ajustes
O sistema SHALL aceitar um arquivo de ajustes `discovery/<cliente>/contatos-ajustes-<AAAA-MM-DD_HHMMSS>.yaml` (o mais recente por padrão, ou o indicado) que associa a um CNPJ valores para as colunas Vendedor, Indústria principal, Indústrias Secundárias, Telefone, E-mail, Site, Latitude e Longitude, cada valor com a fonte de onde veio. O sistema SHALL aplicar o ajuste sobre o valor da origem apenas nessas colunas, SHALL ignorar (avisando) ajustes para qualquer outra coluna ou para CNPJ que não esteja no CSV, e SHALL gravar o resultado em um novo CSV citando o arquivo de ajustes usado.

#### Scenario: Vendedor vindo de ata
- **WHEN** o arquivo de ajustes traz o vendedor de um CNPJ com a ata como fonte
- **THEN** o novo CSV preenche Vendedor para esse contato e os demais valores permanecem como na origem

#### Scenario: Ajuste em coluna protegida
- **WHEN** o arquivo de ajustes tenta alterar razão social, CNPJ ou CNAE
- **THEN** o ajuste é ignorado, o comando avisa e o valor da origem é mantido

#### Scenario: Ajuste sem fonte
- **WHEN** um valor do ajuste não traz fonte
- **THEN** o valor é ignorado e o comando avisa

#### Scenario: CNPJ desconhecido
- **WHEN** o ajuste cita um CNPJ que não está no CSV
- **THEN** o ajuste é ignorado e o comando avisa

### Requirement: Imutabilidade dos arquivos gerados
Cada execução do subcomando SHALL gravar um novo CSV com carimbo próprio, e o sistema SHALL NOT sobrescrever CSV, arquivo de ajustes ou dados brutos existentes.

#### Scenario: Nova exportação após novo ajuste
- **WHEN** o usuário executa o subcomando de novo com um arquivo de ajustes mais recente
- **THEN** um novo CSV é gravado e o anterior permanece intacto
