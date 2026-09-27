## Why

Nas duas primeiras coletas reais (Haix e Estilo Ar) as mesmas lacunas se repetiram: plataforma da loja, tamanho do catálogo, número real de unidades e, nas notícias, resultados sem relação com o cliente. Além disso, o relatório afirma coisas com pesos diferentes (fato, provável, palpite) sem deixar isso explícito, e a proposta comercial precisa de uma estimativa de esforço e de riscos. Este change fecha essas lacunas com fontes simples e sem chave e enriquece a análise da etapa 2.

## What Changes

- **Coleta (etapa 1, CLI):**
  - Nova fonte `sitemap`: lê `robots.txt` e o(s) sitemap(s) do site e registra o total de URLs e a distribuição por tipo de página, como estimativa do tamanho do catálogo.
  - Nova fonte `tecnologia`: identifica plataforma de e-commerce/CMS, ferramentas de marketing e analytics, chat/WhatsApp, meios de pagamento e CDN a partir do HTML, cabeçalhos, cookies e domínios contatados pela home, registrando a evidência de cada detecção.
  - Nova fonte `filiais`: com o CNPJ resolvido, consulta os estabelecimentos da mesma raiz na BrasilAPI e lista cidade, UF, CNAE e situação de cada um.
  - Notícias passam a registrar apenas itens que citam o cliente, informando quantos foram descartados.
- **Análise (etapa 2, skill `/discovery`):**
  - Seção de hipóteses com nível de confiança (fato, provável, palpite), e o roteiro de reunião passa a priorizar as de menor confiança.
  - Seção de dimensionamento preliminar (usuários, complexidade por módulo, faixa de esforço por fase) e de riscos do projeto com mitigação, sempre como estimativa a validar.
- Fora do escopo: páginas de vagas, domínios adicionais do cliente, Mercado Livre, screenshots, histórico do site e exportação para apresentação (ficam para um próximo change).

## Capabilities

### New Capabilities
<!-- Nenhuma: as capacidades já existem em openspec/specs/. -->

### Modified Capabilities
- `web-discovery`: novas fontes (sitemap, tecnologia, filiais) e notícias apenas relevantes.
- `discovery-skill`: seção de hipóteses com confiança, dimensionamento e riscos, e priorização do roteiro por confiança.

## Impact

- Código: novos coletores em `src/discovery/collectors/` (`sitemap`, `tecnologia`, `filiais`), ajuste em `news`, gravação e renderização no `storage`, e ligação no `cli`.
- Skill: `.claude/skills/discovery/` e o espelho em `.opencode/`.
- Rede: mais requisições por coleta (sitemap, uma visita extra à home, e algumas consultas por filial à BrasilAPI); sujeitas a limite de taxa.
- Formato do `raw.json`: novos valores de `tipo` (`sitemap`, `tecnologia`, `filiais`); a versão do formato permanece compatível.
