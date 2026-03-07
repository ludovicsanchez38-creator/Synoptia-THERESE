# CLAUDE.md - THERESE V2

> Contexte projet pour Claude Code

## Projet

**THERESE v2** - Assistant IA desktop souverain pour solopreneurs et TPE francais.
Memoire persistante, UX premium dark mode, donnees 100% locales.

- **Repo** : `github.com/ludovicsanchez38-creator/Synoptia-THERESE` - branche `main`
- **Open source, gratuit** - alpha en cours
- **CI** : GitHub Actions - workflow CI (lint + tests) + workflow Release (build Tauri macOS/Windows/Linux)

## Stack technique

- **Frontend** : Tauri 2.0 + React 19 + TailwindCSS 4 + Framer Motion + Zustand 5
- **Backend** : Python FastAPI + UV + SQLModel + Alembic (migrations)
- **Database** : SQLite (donnees) + Qdrant (embeddings vectoriels, nomic-embed-text-v1.5, 768 dim)
- **LLM** : Multi-provider (Anthropic, OpenAI, Gemini, Mistral, Grok, OpenRouter, Ollama) + Brave Search (web)
- **Skills Office** : python-docx, python-pptx, openpyxl (sandbox code-execution)
- **Desktop** : Tauri 2.0 (Rust) avec sidecar PyInstaller
- **Securite** : Fernet/Keychain, anti-injection prompt, rate limiting, CORS restrictif
- **MCP** : 19 presets (transport stdio, JSON-RPC)
- **Tests** : Vitest (frontend), pytest (backend), Playwright (E2E)

## Commandes essentielles

```bash
make dev                  # Backend + Tauri simultanes
make dev-backend          # Backend seul (uvicorn :17293)
make dev-frontend         # Frontend seul (Vite :1420)
make test                 # Tous les tests
make test-backend         # pytest (hors E2E)
make lint                 # Ruff (Python) + ESLint (TS)
make build                # Production (Tauri .app)
make build-release        # Build complete (sidecar + Tauri)
make install              # uv sync + npm install
make db-migrate           # Alembic upgrade head
```

**URLs** : Backend http://localhost:17293 | Frontend http://localhost:1420 | Docs http://localhost:17293/docs

## Architecture

```
src/backend/app/
  main.py              # FastAPI app avec lifespan
  models/              # entities.py (SQLModel), schemas.py (Pydantic), board.py
  routers/             # chat, memory, config, skills, images, board, mcp, files, data, crm, email, calendar...
  services/            # llm.py (orchestrateur), providers/ (7 LLM), skills/ (code_executor, generators)
                       # qdrant.py, embeddings.py, mcp_service.py, encryption.py, prompt_security.py...

src/frontend/src/
  App.tsx              # Entry point (onboarding check, panel routing)
  components/          # chat/, guided/, board/, memory/, settings/, onboarding/, sidebar/, panels/, ui/
  services/api/        # 14 modules (chat, memory, config, mcp, skills, images, board, etc.)
  stores/              # Zustand (chatStore, emailStore, calendarStore, etc.)
  hooks/               # useKeyboardShortcuts, useVoiceRecorder, etc.

src/frontend/src-tauri/ # Configuration Tauri 2.0 (Rust)
```

## Conventions de code

- **Python** : UV pour dependances, type hints obligatoires, ruff pour lint
- **TypeScript** : ESLint, composants React fonctionnels
- **Git** : Commits en francais avec accents
- **PPTX/DOCX** : Ne PAS generer de preview LibreOffice
- **Fenetres Tauri** : Ne PAS utiliser `onCloseRequested`, utiliser `once('tauri://destroyed')`

## Donnees utilisateur

- **Repertoire** : `~/.therese/` (DB, images, backups, mcp_servers.json)
- **Sandbox tests** : `~/.therese-test-sandbox/`
- **Cles API** : chiffrees Fernet (cle dans macOS Keychain via `keyring`)

## Identite visuelle

```yaml
palette:
  background: "#0B1226"
  surface: "#131B35"
  text_primary: "#E6EDF7"
  text_muted: "#B6C7DA"
  accent_cyan: "#22D3EE"
  accent_magenta: "#E11D8D"
```

## Modules fonctionnels

Chat multi-LLM, Memoire (contacts/projets/recherche semantique), Skills Office (DOCX/PPTX/XLSX), Email (Gmail OAuth + IMAP/SMTP), Calendrier (Google + CalDAV + local), CRM (pipeline, scoring, sync Google Sheets), Facturation (devis/facture/avoir, PDF conforme), Board de decision IA (5 conseillers), Generation d'images, Transcription vocale, MCP (19 presets), RGPD (export, anonymisation)

## Dette technique

(Section maintenue par le workflow /release-therese et Zezette)

## Tests de non-regression

Avant chaque release :
1. `uv run pytest tests/test_regression.py -v`
2. `uv run pytest tests/ --ignore=tests/e2e -q --timeout=30`
3. Si un test echoue, NE PAS publier
4. Chaque fix critique = un test de regression

## Documentation

- `docs/CHANGELOG.md` - Historique structure par version
- `docs/DEVLOG.md` - Journal de developpement
- `docs/architecture.md` - Architecture technique detaillee
- `docs/API.md` - Documentation API
- `docs/prd-therese.md` - PRD complet
- `docs/stories/` - User stories et epics
