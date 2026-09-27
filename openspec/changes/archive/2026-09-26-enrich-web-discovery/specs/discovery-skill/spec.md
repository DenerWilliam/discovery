## ADDED Requirements

### Requirement: Hipóteses com nível de confiança
O relatório SHALL conter uma seção de hipóteses em que cada afirmação relevante do relatório é classificada como fato (comprovado por dado coletado), provável (inferência sustentada por evidência) ou palpite (inferência sem evidência direta), com a fonte ou o raciocínio que a sustenta.

#### Scenario: Classificação por confiança
- **WHEN** o relatório é gerado
- **THEN** cada hipótese indica seu nível de confiança e a evidência ou o raciocínio

#### Scenario: Informação dada pelo usuário
- **WHEN** uma informação foi passada pelo usuário na conversa
- **THEN** ela aparece marcada como informada pelo usuário, e não como fato coletado

### Requirement: Priorização do roteiro por confiança
O roteiro de reunião SHALL priorizar perguntas que validem as hipóteses de menor confiança e as lacunas mais críticas, colocando-as no início de seus blocos e indicando a hipótese ou lacuna que cada uma valida.

#### Scenario: Pergunta ligada a hipótese fraca
- **WHEN** existe uma hipótese classificada como palpite ou provável
- **THEN** o roteiro contém uma pergunta marcada como validação dessa hipótese

### Requirement: Dimensionamento preliminar
O relatório SHALL conter um dimensionamento preliminar do projeto com estimativa de usuários, complexidade por módulo proposto (baixa, média ou alta) e faixa de esforço por fase, explicitando as premissas usadas e que se trata de estimativa inicial a validar, e não de orçamento.

#### Scenario: Estimativa com premissas
- **WHEN** o dimensionamento é apresentado
- **THEN** cada estimativa lista as premissas e os dados que a sustentam, e as lacunas que a tornam incerta

#### Scenario: Dados insuficientes
- **WHEN** faltam dados essenciais para estimar (por exemplo número de funcionários)
- **THEN** o relatório declara a lacuna e apresenta a faixa como condicional, sem inventar o dado

### Requirement: Riscos do projeto
O relatório SHALL conter uma seção de riscos do projeto (por exemplo migração de dados, regras fiscais, integrações e dependência de sistemas legados) com probabilidade, impacto e mitigação proposta, ligados às evidências do negócio.

#### Scenario: Risco ligado a evidência
- **WHEN** um risco é listado
- **THEN** ele indica a evidência ou a lacuna que o motivou e a mitigação proposta

### Requirement: Uso das novas fontes na estruturação
A skill SHALL usar as fontes de sitemap, tecnologia e estabelecimentos, quando presentes nos dados brutos, para embasar o relatório (tamanho do catálogo, plataforma e ferramentas, número e localização das unidades), citando a fonte de cada dado.

#### Scenario: Fonte de tecnologia presente
- **WHEN** os dados brutos contêm tecnologias detectadas
- **THEN** a seção de sistemas e tecnologia cita as detecções com a evidência

#### Scenario: Fonte ausente ou com falha
- **WHEN** uma das novas fontes não foi coletada
- **THEN** o relatório a lista como lacuna e não presume o dado
