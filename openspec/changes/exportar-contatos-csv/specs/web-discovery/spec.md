## MODIFIED Requirements

### Requirement: Estabelecimentos da mesma raiz de CNPJ
O sistema SHALL, quando houver um CNPJ resolvido e consultado com sucesso, consultar por API pública os estabelecimentos que compartilham a raiz de 8 dígitos (sufixos sequenciais com dígitos verificadores válidos), até um limite e parando após vários sufixos consecutivos inexistentes, e registrar para cada um o CNPJ, a cidade, a UF, o CNAE, a situação cadastral e a data de início, além dos dados cadastrais completos retornados pela API (razão social, endereço, CEP, telefone, e-mail, natureza jurídica, capital social, regime tributário e CNAEs secundários).

#### Scenario: Filiais encontradas
- **WHEN** existem estabelecimentos além do informado
- **THEN** os dados brutos listam cada estabelecimento com cidade, UF, CNAE, situação e os dados cadastrais completos

#### Scenario: Sem outros estabelecimentos
- **WHEN** nenhum outro sufixo existe
- **THEN** a fonte é registrada como coletada listando somente o estabelecimento conhecido

#### Scenario: Limite de taxa da API
- **WHEN** a API sinaliza limite de taxa ou falha durante a busca
- **THEN** o sistema registra os estabelecimentos já obtidos, marca a fonte como falha parcial com o motivo e continua

#### Scenario: CNPJ não resolvido
- **WHEN** o CNPJ não foi informado nem encontrado, ou é ambíguo
- **THEN** a fonte de estabelecimentos é registrada como não coletada, sem consultar a API
