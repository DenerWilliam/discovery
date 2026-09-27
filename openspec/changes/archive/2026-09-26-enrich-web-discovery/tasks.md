## 1. Notícias relevantes

- [x] 1.1 Filtrar as notícias que não citam o nome completo do cliente (sem acentos e sem distinção de maiúsculas) e gravar `descartados: N`; verificar com testes de feed misto, feed 100% irrelevante (lista vazia com contagem) e feed vazio

## 2. Sitemap

- [x] 2.1 Implementar o coletor de sitemap (`robots.txt`, fallback `/sitemap.xml`, índices com limites, total de URLs, distribuição por tipo de página e amostra); verificar com testes usando `httpx.MockTransport` para sitemap simples, índice e XML inválido
- [x] 2.2 Registrar site sem sitemap como não coletado com o motivo, sem interromper a execução; verificar com teste de 404 no `robots.txt` e no `/sitemap.xml`

## 3. Tecnologia do site

- [x] 3.1 Criar a tabela de assinaturas (plataformas de e-commerce e CMS, marketing e analytics, chat e WhatsApp, pagamentos, CDN) em módulo próprio e o detector que casa HTML, scripts/domínios, cookies e cabeçalhos, guardando a evidência; verificar com testes unitários sobre entradas de exemplo, incluindo nenhum casamento
- [x] 3.2 Implementar o coletor que visita a home com Playwright registrando HTML, cabeçalhos, cookies e domínios contatados; verificar com teste contra página local de fixture com scripts e cookies conhecidos, e com teste de home inacessível registrada como falha

## 4. Estabelecimentos da mesma raiz

- [x] 4.1 Implementar o cálculo dos dígitos verificadores para gerar `raiz + sufixo` e validar com CNPJs conhecidos; verificar com testes unitários
- [x] 4.2 Implementar a consulta sequencial via BrasilAPI (limite de 20 sufixos, parada após 3 inexistentes, pausa entre chamadas, cidade/UF/CNAE/situação/início); verificar com `httpx.MockTransport` para filiais encontradas, sem outras filiais e 429 no meio (falha parcial preservando o já obtido)
- [x] 4.3 Só executar quando a fonte de CNPJ está `ok`; registrar `nao_coletada` nos demais casos; verificar com testes de CNPJ ambíguo, não encontrado e com falha

## 5. Integração no CLI e nos dados brutos

- [x] 5.1 Ligar sitemap, tecnologia e filiais no `discovery scan` na ordem site, sitemap, tecnologia, CNPJ, filiais, buscas e notícias; verificar com execução real contra a Estilo Ar mostrando as novas fontes no `raw.json`
- [x] 5.2 Renderizar as novas fontes (`sitemap`, `tecnologia`, `filiais`) e a contagem de descartados das notícias no `raw.md`; verificar com teste de conteúdo e leitura do `raw.md` gerado

## 6. Skill

- [x] 6.1 Acrescentar ao relatório as seções de hipóteses com confiança (fato, provável, palpite), dimensionamento preliminar (usuários, complexidade por módulo, faixa por fase, premissas, aviso de estimativa) e riscos (probabilidade, impacto, mitigação), e o uso das novas fontes; verificar gerando o relatório da Estilo Ar
- [x] 6.2 Priorizar no roteiro as perguntas que validam as hipóteses de menor confiança, indicando a hipótese validada; verificar no roteiro gerado da Estilo Ar
- [x] 6.3 Espelhar a skill em `.opencode/` e verificar com `diff` que as duas cópias são idênticas

## 7. Documentação e validação real

- [x] 7.1 Atualizar `CLAUDE.md` e `README.md` com as novas fontes e seções; verificar que os comandos documentados executam
- [x] 7.2 Rodar a coleta real para Haix e Estilo Ar e conferir que sitemap, tecnologia e filiais trazem dados úteis (ou falham de forma registrada), e que `uv run pytest` passa por inteiro
