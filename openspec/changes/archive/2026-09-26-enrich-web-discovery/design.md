## Context

Continua o change arquivado `add-web-discovery-cli`: o pipeline é `site` → `cnpj` → buscas → notícias → gravação em `raw.json`/`raw.md`, e a etapa 2 (skill) lê esses dados. Motivação e escopo em proposal.md; comportamento esperado nas specs `web-discovery` e `discovery-skill`. Coletores devolvem uma lista de `Source` com status, sem interpretar dados.

## Goals / Non-Goals

**Goals:**
- Novas fontes baratas, sem chave e sem depender de buscadores, que respondam às lacunas recorrentes.
- Manter o contrato: o CLI só coleta e a interpretação fica na etapa 2.
- Falha de uma fonte nunca derruba a execução.

**Non-Goals:**
- Vagas, domínios adicionais, Mercado Livre, screenshots, histórico do site e exportação de apresentação (próximo change).
- Detecção de tecnologia exaustiva: uma tabela enxuta e editável, não um Wappalyzer completo.

## Decisions

**1. Sitemap por `httpx`, sem navegador.**
Lê `robots.txt` (linhas `Sitemap:`), senão `/sitemap.xml`; segue índices até 20 sitemaps e 50.000 URLs no total. Registra `total_urls`, distribuição por primeiro segmento do caminho e por sufixo de tipo (padrões como `/p` e `/c` de lojas) e 20 URLs de amostra, não a lista completa. Alternativa descartada: visitar as páginas, lento e desnecessário para estimar tamanho.

**2. Tecnologia por uma visita extra à home com Playwright.**
Uma página nova escuta as requisições e respostas: registra o HTML final, cabeçalhos da resposta principal, cookies e os domínios contatados. Uma tabela de assinaturas (nome, categoria, padrões em HTML, script/domínio, cookie e cabeçalho) fica em módulo próprio e é fácil de estender. A saída guarda nome, categoria e a evidência que casou. Alternativa descartada: reaproveitar o HTML da varredura do site, que hoje só guarda o texto; a visita extra custa uma página e mantém os coletores independentes.

**3. Estabelecimentos da mesma raiz pela BrasilAPI.**
Só roda se a fonte `cnpj` está `ok`. Gera os CNPJs `raiz + 0001..0020` com dígitos verificadores calculados, consulta em sequência com pequena pausa entre chamadas e para após 3 inexistentes (HTTP 404) seguidos. Um 429 ou erro de rede interrompe a busca e grava o que já veio como falha parcial. A lista é limitada a 20 sufixos, suficiente para redes de porte médio; o limite fica configurável.

**4. Notícias: relevância no coletor, com contagem.**
O feed busca pelo nome entre aspas, mas retorna itens sem relação (nomes curtos e comuns colidem). O coletor mantém só itens cujo título contém o nome completo do cliente sem acentos e sem distinção de maiúsculas, e grava `descartados: N`. Coerente com a decisão das buscas de não gravar lixo como resultado. Alternativa descartada: guardar tudo e filtrar só na etapa 2, que deixaria o `raw.json` cheio de ruído.

**5. Integração no pipeline e no `raw.md`.**
Ordem: site → sitemap → tecnologia → cnpj → filiais → buscas → notícias. Cada fonte nova tem `tipo` próprio (`sitemap`, `tecnologia`, `filiais`), e o `raw.md` ganha uma renderização legível por tipo. `versao_formato` permanece 1: só há novos valores de `tipo`, sem mudar campos.

**6. Análise na skill: hipóteses com confiança, dimensionamento e riscos.**
Três novas seções no relatório e uma regra no roteiro. Confiança em três níveis (fato, provável, palpite) com a evidência ou o raciocínio. O dimensionamento sempre traz premissas e o aviso de estimativa a validar, e vira condicional quando faltam dados (ex.: nº de funcionários). O roteiro põe no início de cada bloco as perguntas que validam as hipóteses de menor confiança e diz qual validam. Ficam em texto da skill, sem código novo.

## Risks / Trade-offs

- [Tabela de assinaturas de tecnologia fica desatualizada ou tem falsos positivos] → Guardar a evidência de cada detecção para conferência, e manter a tabela pequena e editável.
- [Muitas consultas à BrasilAPI por cliente] → Limite de sufixos, parada após 3 inexistentes, pausa entre chamadas e falha parcial em caso de 429.
- [Sitemap grande ou malformado] → Limites de sitemaps e URLs, tratamento de XML inválido como falha da fonte.
- [Filtro de notícias descarta variantes do nome (sigla, nome fantasia)] → Contagem de descartados visível no raw e comparação por nome completo; ajuste por cliente fica para depois se necessário.
- [Estimativas de esforço lidas como orçamento] → Premissas explícitas e aviso fixo de estimativa inicial.
- [Uma visita extra à home aumenta o tempo] → Uma página só, com timeout curto.
