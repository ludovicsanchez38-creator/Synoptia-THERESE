# CLAUDE.md - THÉRÈSE V2

> Contexte projet pour Claude Code - Ne pas supprimer

## Projet

**THÉRÈSE v2** - Assistant IA desktop souverain pour solopreneurs et TPE français.
Alternative à Cowork (Anthropic) avec mémoire persistante, UX premium dark mode, et données 100% locales.
Créateur : Ludo Sanchez (Synoptïa) - "Ta mémoire, tes données, ton business."

## Stack technique

- **Frontend** : Tauri 2.0 + React + TailwindCSS + Framer Motion + Zustand
- **Backend** : Python FastAPI + UV + Alembic (migrations)
- **Database** : SQLite (données) + Qdrant (embeddings vectoriels)
- **LLM** : Multi-provider (Anthropic, OpenAI, Gemini, Mistral, Grok, Ollama)
- **Skills Office** : python-docx, python-pptx, openpyxl (sandbox code-execution)
- **MCP** : 19 presets (transport stdio, JSON-RPC)
- **Tests** : Vitest (frontend), pytest (backend), Playwright (E2E)

## Commandes essentielles

```bash
# Développement
make dev                  # Backend + Tauri simultanés
make dev-backend          # Backend seul (uvicorn :8000)
make dev-frontend         # Frontend seul (Vite :1420)
make tauri                # Tauri uniquement

# Tests
make test                 # Tous les tests
make test-backend         # pytest (hors E2E)
make test-e2e             # Playwright headless
make test-e2e-headed      # Playwright avec navigateur visible

# Qualité
make lint                 # Ruff (Python) + ESLint (TS)
make lint-fix             # Correction automatique
make typecheck            # TypeScript --noEmit

# Build & DB
make build                # Production (Tauri .app)
make build-sidecar        # Build sidecar backend (PyInstaller)
make build-release        # Build complète (sidecar + Tauri)
make install              # uv sync + npm install
make db-migrate           # Alembic upgrade head
make db-revision MSG='x'  # Nouvelle migration

# Lancement manuel
cd src/backend && uv run uvicorn app.main:app --reload --port 8000
cd src/frontend && npm run tauri dev
```

**URLs** : Backend http://localhost:8000 | Frontend http://localhost:1420 | Docs http://localhost:8000/docs

## Architecture

```
src/backend/app/
  main.py              # FastAPI app avec lifespan
  models/              # entities.py (SQLModel), schemas.py (Pydantic), board.py
  routers/             # chat, memory, config, skills, images, board, mcp, files, data, crm, email, calendar...
  services/            # llm.py (orchestrateur), providers/ (6 LLM), skills/ (code_executor, generators)
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

- **Python** : UV pour dépendances, type hints obligatoires, ruff pour lint
- **TypeScript** : ESLint, composants React fonctionnels
- **Git** : Commits en français avec accents
- **Accents obligatoires** : écrire en français correct (é, è, ê, à, ù, ô, ç, î, etc.)
- **PPTX/DOCX** : Ne PAS générer de preview LibreOffice
- **Fenêtres Tauri** : Ne PAS utiliser `onCloseRequested` (bloque la croix macOS), utiliser `once('tauri://destroyed')`

## Données utilisateur

- **Répertoire** : `~/.therese/` (DB, images, backups, mcp_servers.json)
- **Sandbox tests** : `~/.therese-test-sandbox/`
- **Clés API** : chiffrées Fernet (clé dans macOS Keychain via `keyring`)

## Identité visuelle

```yaml
palette:
  background: "#0B1226"
  surface: "#131B35"
  text_primary: "#E6EDF7"
  text_muted: "#B6C7DA"
  accent_cyan: "#22D3EE"
  accent_magenta: "#E11D8D"
```

## Documentation

- `docs/CHANGELOG.md` - Historique structuré par version (v1.0 à v3.7)
- `docs/DEVLOG.md` - Journal de développement complet
- `docs/architecture.md` - Architecture technique détaillée
- `docs/API.md` - Documentation API
- `docs/prd-therese.md` - PRD complet
- `docs/stories/` - 35 user stories, 5 epics

## Version actuelle : v0.1.18-alpha (15 février 2026)

Voir `docs/CHANGELOG.md` pour le détail des fonctionnalités par version.
