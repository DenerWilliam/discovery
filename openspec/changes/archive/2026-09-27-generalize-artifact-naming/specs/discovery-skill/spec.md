## ADDED Requirements

### Requirement: Nomenclatura geral de materiais estruturados
Todo material que a skill estruturar para um cliente, além do relatório, do roteiro e do cruzamento já especificados, SHALL seguir o padrão `discovery/<cliente>/<tipo-descritivo>-<AAAA-MM-DD_HHMMSS>.md`, com `<tipo-descritivo>` livre e sem lista fechada de tipos, SHALL ser imutável (uma versão nova é sempre um arquivo novo, nunca uma sobrescrita) e SHALL citar no topo a base de que partiu (relatório, cruzamento ou outro material anterior).

#### Scenario: Material novo com carimbo e base citada
- **WHEN** a skill estrutura um material que não é o relatório, o roteiro nem o cruzamento (por exemplo, uma cotação complementar)
- **THEN** o arquivo é gravado em `discovery/<cliente>/` com carimbo de data e hora no nome e cita no topo o documento em que se baseou

#### Scenario: Nova versão do mesmo material
- **WHEN** o usuário pede uma nova versão de um material já estruturado antes
- **THEN** um novo arquivo com carimbo distinto é gravado, e a versão anterior é preservada

#### Scenario: Evolução visível no histórico
- **WHEN** vários materiais de um cliente existem em `discovery/<cliente>/`
- **THEN** os nomes dos arquivos, ordenados, mostram a ordem cronológica em que foram produzidos
