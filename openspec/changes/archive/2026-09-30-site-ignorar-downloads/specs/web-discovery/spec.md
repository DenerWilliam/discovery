## MODIFIED Requirements

### Requirement: Varredura do site oficial
O sistema SHALL visitar a página inicial do site oficial e as páginas internas relevantes do mesmo domínio (como institucional, serviços, contato, política de privacidade e termos), e registrar título, URL e texto de cada página visitada. Links que respondem com um arquivo para download em vez de uma página SHALL ser registrados como não coletados, com o motivo indicado, e SHALL NOT contar para o limite de páginas da varredura.

#### Scenario: Site acessível
- **WHEN** o site oficial responde com sucesso
- **THEN** os dados brutos incluem as páginas visitadas com URL, título e texto extraído

#### Scenario: Site inacessível
- **WHEN** o site oficial não responde ou retorna erro
- **THEN** o sistema registra a falha nos dados brutos e continua com as demais fontes

#### Scenario: Limite ao domínio do cliente
- **WHEN** uma página do site contém links para outros domínios
- **THEN** o sistema não visita esses links durante a varredura do site oficial

#### Scenario: Link que serve arquivo para download
- **WHEN** uma página do site contém um link que responde com um arquivo para download (por exemplo um relatório em PDF sem extensão na URL)
- **THEN** os dados brutos registram essa URL como fonte do site com status `nao_coletada` e o motivo "arquivo para download", sem ler o conteúdo do arquivo, e a varredura continua

#### Scenario: Downloads não consomem o limite de páginas
- **WHEN** a varredura encontra vários links de download antes de esgotar as páginas HTML relevantes
- **THEN** o limite de páginas é consumido apenas por páginas HTML, e as demais páginas relevantes ainda são visitadas até o limite
