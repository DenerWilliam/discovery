# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## State of the project

Python package `discovery` (`src/` layout, `uv`, `uv_build`) that does web discovery for new Odoo clients (Escodoo). It works in **two stages** with a file contract between them:

1. **Garimpo (CLI, no AI):** `discovery scan` collects public data (site via Playwright; sitemap, CNPJ, same-root establishments and news via `httpx`; technology detection via Playwright; searches via Bing/DuckDuckGo) and writes raw data only, without interpreting it.
2. **Estruturação (skill `/discovery`, with AI):** reads a run's raw data and writes a structured report, without touching the web. It can be repeated over the same run.

```
reports/<AAAA-MM-DD_HHMMSS>-<client>/   # gitignored (client data)
  raw.json                              # stage 1, immutable, versioned format (versao_formato)
  raw.md                                # stage 1, readable copy
discovery/<client>/                     # gitignored; the readable deliverable
  scraping-<AAAA-MM-DD_HHMMSS>.md       # stage 2 report (hypotheses with confidence, Odoo module scope, sizing, risks), cites its source run
  reuniao-<AAAA-MM-DD_HHMMSS>.md        # stage 2 meeting script (~60 questions, hypothesis-validating ones first)
  docs-internos/                        # meeting material dropped by hand: minutes, transcripts, PDF/docx/images, spreadsheets
    AAAA-MM-DD-<tipo>-<assunto>.<ext>   # suggested name (tipo: ata|transcricao|fluxo|planilha|email|proposta); files are immutable
  cruzamento-<AAAA-MM-DD_HHMMSS>.md     # `/discovery <client> --cruzar`: docs-internos crossed with the scraping (new file each time, chained)
  <tipo-descritivo>-<AAAA-MM-DD_HHMMSS>.md  # any other structured material (quote, exec summary, ...); same rules: timestamped, immutable, cites its base
clients/<id>.yaml                       # per-client config (name, site, cnpj?, queries?, max_pages?)
```

Code layout in `src/discovery/`: `cli.py` (argparse), `config.py`, `models.py` (`Source`, statuses `ok|falha|nao_coletada|ambigua`), `storage.py`, `collectors/{site,sitemap,tecnologia,signatures,cnpj,filiais,search,news}.py`. Stage 3 (`/discovery <client> --cruzar`, skill only, no Python code) crosses `docs-internos/` with the latest report or previous crossing and writes a new `cruzamento-*.md`; it reads PDF with `pdftotext`, docx with `pandoc`, spreadsheets with `soffice`, and images visually (marked as image interpretation). The skill lives in `.claude/skills/discovery/` and is mirrored in `.opencode/skills/discovery/` (keep both identical).

Sources (`tipo` in `raw.json`): `site`, `sitemap` (URL count and catalog size estimate), `tecnologia` (platform, marketing, chat, payments and CDN from HTML/headers/cookies/domains; the signature table in `collectors/signatures.py` is small and meant to be extended), `cnpj`, `filiais` (BrasilAPI establishments of the same 8-digit root, only when the CNPJ is resolved), `busca` and `noticias` (only items that cite the client; discarded ones are counted).

Searches are keyless and best-effort: Bing first, then DuckDuckGo (which usually blocks automated access), each with an isolated parser; news come from the Google News RSS via `httpx`. If all engines fail, the query is recorded as `nao_coletada`. Bing returns irrelevant results for automated multi-term queries, so the default query is just the quoted client name; stage 2 filters relevance.

## Commands

- Sync environment: `uv sync`; install the browser once: `uv run playwright install chromium`
- Scan a client: `uv run discovery scan --client haix` (or `--name "X" --site https://x.com.br [--cnpj ...]`); `--dry-run` only resolves the config
- Tests: `uv run pytest` (site tests use a local HTTP server and real Chromium; CNPJ tests use `httpx.MockTransport`; no network needed)
- Build: `uv build`
- Python version is pinned to 3.10 (`.python-version`; `requires-python >=3.10`).

No lint tooling is configured yet; add it to `pyproject.toml` before documenting commands for it here.

## Spec-driven workflow (OpenSpec)

Development is organized with OpenSpec (`openspec/config.yaml`, schema `spec-driven`):

- `openspec/specs/` holds the main specs; `openspec/changes/` holds in-flight changes, and `openspec/changes/archive/` the completed ones.
- Workflow is driven by skills/commands available in both `.claude/` (`/opsx:propose`, `/opsx:explore`, `/opsx:apply`, `/opsx:update`, `/opsx:sync`, `/opsx:archive`) and mirrored in `.opencode/` for OpenCode. Keep the two copies consistent if you edit one.
- Typical flow: propose a change (proposal, design, specs, tasks) → apply its tasks → sync delta specs into main specs → archive.
- `openspec/config.yaml` has project context and per-artifact rules commented out; populate `context:` there (tech stack, conventions) so it is fed to artifact generation.
