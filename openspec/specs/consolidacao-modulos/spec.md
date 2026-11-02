# Consolidação de Módulos Odoo em CSV

## Purpose

Consolidar módulos Odoo propostos de múltiplos descobertas web de clientes em um CSV único, destravando análises de escopo, portfolio e estimativas de horas entre projetos.

## Requirements

### Requirement: Consolidar módulos de múltiplos descobertas

O sistema SHALL ler todos os arquivos `discovery/*/scraping-*.md`, extrair as tabelas de módulos Odoo propostos, e consolidar em um CSV único, preservando cliente, módulo, fase, evidência, complexidade e horas padrão.

#### Scenario: Consolidação bem-sucedida
- **WHEN** usuário executa `discovery consolidar-modulos`
- **THEN** sistema lê todos `discovery/*/scraping-*.md`, extrai módulos de cada cliente, e grava CSV com 134+ módulos de 4+ clientes

#### Scenario: Sem descobertas encontradas
- **WHEN** não há arquivos `discovery/*/scraping-*.md`
- **THEN** sistema exibe erro "Nenhum discovery encontrado" e retorna exit code 1

### Requirement: Mapear horas padrão via régua

O sistema SHALL mapear cada módulo consolidado contra a tabela de horas padrão em `referencia/horas.csv`, usando fallback manual para módulos não encontrados.

#### Scenario: Módulo com horas mapeadas
- **WHEN** módulo "Contatos" é consolidado
- **THEN** sistema mapeia contra `referencia/horas.csv` e preenche coluna `horas_padrao` com valor (ex.: "40")

#### Scenario: Módulo sem mapeamento direto
- **WHEN** módulo não existe em `referencia/horas.csv`
- **THEN** sistema tenta fallback manual por substring (ex.: "ecommerce" → "320") e preenche coluna `horas_padrao`

#### Scenario: Módulo sem mapeamento
- **WHEN** módulo não existe em régua nem em fallback
- **THEN** coluna `horas_padrao` fica vazia

### Requirement: Estimar complexidade automaticamente

O sistema SHALL estimar a complexidade de cada módulo (Baixa/Média/Alta) baseado em palavras-chave presentes na evidência.

#### Scenario: Complexidade Alta detectada
- **WHEN** evidência contém palavras "múltiplos", "complexa", "integração com", "migração"
- **THEN** coluna `complexidade` recebe valor "Alta"

#### Scenario: Complexidade Média por padrão
- **WHEN** nenhuma palavra-chave de Alta ou Baixa detectada
- **THEN** coluna `complexidade` recebe valor "Média"

#### Scenario: Complexidade Baixa detectada
- **WHEN** evidência contém palavras "simples", "básica"
- **THEN** coluna `complexidade` recebe valor "Baixa"

### Requirement: Suportar filtro por cliente

O sistema SHALL permitir consolidar apenas um cliente específico via flag `--client <id>`.

#### Scenario: Filtro por cliente aplicado
- **WHEN** usuário executa `discovery consolidar-modulos --client americanas`
- **THEN** sistema consolida apenas módulos do cliente "americanas" (20 módulos)

#### Scenario: Cliente inexistente
- **WHEN** usuário executa `discovery consolidar-modulos --client inexistente`
- **THEN** sistema exibe mensagem (0 módulos encontrados) mas não falha

### Requirement: Integração com CLI

O sistema SHALL fornecer subcomando `discovery consolidar-modulos` com flags `--client` e `--output`.

#### Scenario: Execução via CLI
- **WHEN** usuário executa `uv run discovery consolidar-modulos`
- **THEN** sistema roda consolidação e salva em `descoberta-modulos-consolidado-<timestamp>.csv`

#### Scenario: Output customizado
- **WHEN** usuário executa `discovery consolidar-modulos --output meus-modulos.csv`
- **THEN** sistema salva em `meus-modulos.csv` (sem timestamp)

#### Scenario: Help disponível
- **WHEN** usuário executa `discovery consolidar-modulos --help`
- **THEN** sistema exibe ajuda com opções `--client` e `--output`

### Requirement: Formato do CSV consolidado

O sistema SHALL produzir CSV com 7 colunas em ordem: cliente, modulo, enterprise, fase, evidencia, complexidade, horas_padrao.

#### Scenario: CSV bem-formado
- **WHEN** consolidação é concluída
- **THEN** CSV contém cabeçalho e linhas com campos quoted/unquoted apropriados (RFC 4180 compliant)

#### Scenario: Caracteres especiais escapados
- **WHEN** evidência contém aspas ou quebras de linha
- **THEN** campos são quoted e caracteres escapados (aspas duplicadas)

#### Scenario: Módulos Enterprise marcados
- **WHEN** módulo original tem "(E)" na descrição
- **THEN** coluna `enterprise` recebe "Sim", senão "Não"

### Requirement: Tratamento de erros

O sistema SHALL capturar e reportar erros de forma clara sem interromper a consolidação para outros clientes.

#### Scenario: Arquivo scraping-*.md ilegível
- **WHEN** `discovery/cliente/scraping-*.md` não pode ser lido
- **THEN** sistema exibe aviso em stderr e continua com próximo cliente

#### Scenario: referencia/horas.csv ausente
- **WHEN** `referencia/horas.csv` não existe
- **THEN** sistema exibe aviso e usa fallback manual para todos os módulos

#### Scenario: Escrita de CSV falha
- **WHEN** permissão de escrita negada no arquivo de saída
- **THEN** sistema exibe erro e retorna exit code 1
