## MODIFIED Requirements

### Requirement: Fidelidade aos dados coletados
A skill SHALL basear cada afirmação do relatório nos dados brutos, indicando a fonte, e SHALL declarar explicitamente as lacunas em vez de inventar informação. Quando uma página do site foi coletada pelo arquivo público, a skill SHALL indicar a data da captura e a natureza de conteúdo arquivado, em vez de tratá-la como leitura ao vivo.

#### Scenario: Síntese com evidências
- **WHEN** os dados brutos contêm informação suficiente
- **THEN** cada afirmação relevante do relatório referencia a fonte registrada

#### Scenario: Dados insuficientes
- **WHEN** os dados brutos não têm informação sobre um tema
- **THEN** o relatório declara a lacuna na seção correspondente e não a preenche com suposições

#### Scenario: Fontes com falha
- **WHEN** os dados brutos registram falhas em algumas fontes
- **THEN** o relatório é gerado com o que existe e lista as fontes que falharam

#### Scenario: Página vinda do arquivo público
- **WHEN** os dados brutos registram páginas do site com origem arquivada e data de captura
- **THEN** o relatório cita a data da captura e declara que o conteúdo não veio do site ao vivo
