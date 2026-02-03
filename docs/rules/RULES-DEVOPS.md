# Règles DevOps et Déploiement - THÉRÈSE V2

## Environnements

### Développement (local)
- **Backend** : `uv run uvicorn app.main:app --reload --port 8000`
- **Frontend** : `npm run dev` (Vite, port 1420)
- **Tauri** : `npm run tauri:dev` (backend + frontend + desktop)
- **Base de données** : ~/.therese/therese.db (SQLite)
- **Qdrant** : Embarqué (local, pas de serveur séparé)
- **Variables** : THERESE_ENV=development

### Production (desktop)
- **Build** : `npm run tauri:build` (crée .app + .dmg)
- **Backend** : Sidecar Python embarqué dans le bundle Tauri
- **Frontend** : Build Vite statique dans le WebView
- **Variables** : THERESE_ENV=production
- **CORS** : Restreint aux origines Tauri

## Gestionnaires de paquets

### Python (UV)
- **Fichier** : pyproject.toml + uv.lock
- **Installation** : `uv sync`
- **Ajout** : `uv add package`
- **Suppression** : `uv remove package`
- **Lock** : Automatique (uv.lock généré)
- **Environnement** : .venv/ (créé automatiquement)
- **Python** : 3.11+ requis

### Node.js (npm)
- **Fichier** : src/frontend/package.json + package-lock.json
- **Installation** : `cd src/frontend && npm install`
- **Ajout** : `npm install package`
- **Lock** : package-lock.json

### Rust (Cargo)
- **Fichier** : src/frontend/src-tauri/Cargo.toml
- **Géré par Tauri** (pas de manipulation directe)

## Commandes Makefile

```bash
# Développement
make dev                  # Backend + Frontend + Tauri
make dev-backend         # Backend seul (hot-reload)
make dev-frontend        # Frontend seul (Vite)

# Installation
make install             # Toutes les dépendances
make install-backend     # Python (uv sync)
make install-frontend    # Node (npm install)
make install-e2e         # Playwright browsers

# Tests
make test                # Tous les tests
make test-backend        # Backend pytest
make test-frontend       # Frontend vitest
make test-e2e            # E2E Playwright (headless)
make test-e2e-headed     # E2E Playwright (visible)

# Qualité de code
make lint                # Ruff (Python) + ESLint (TypeScript)
make typecheck           # TypeScript type checking
make format              # Auto-format (Ruff + Prettier)

# Base de données
make db-migrate          # Appliquer les migrations Alembic
make db-revision msg="x" # Créer une nouvelle migration

# Build
make build               # Build production (Tauri)
make clean               # Nettoyage des artefacts
```

## Migrations de base de données (Alembic)

### Créer une migration
```bash
make db-revision msg="Ajouter champ score au contact"
# Crée : src/backend/alembic/versions/xxxx_ajouter_champ_score.py
```

### Appliquer les migrations
```bash
make db-migrate
# Applique toutes les migrations en attente
```

### Règles de migration
- Toujours créer une migration pour les changements de schéma
- Jamais de modification manuelle de la DB
- Tester la migration sur une copie avant commit
- Messages de migration en français
- Migrations réversibles (inclure downgrade)
- Une migration par changement logique (pas de méga-migration)

## Git et versioning

### Conventions de commit
- Messages en français
- Format : `type: description courte`
- Types : feat, fix, refactor, test, docs, perf, style, chore
- Exemples :
  - `feat: ajouter la génération de factures PDF`
  - `fix: corriger le streaming SSE pour Gemini`
  - `refactor: modulariser les providers LLM`
  - `test: ajouter tests E2E pour l'onboarding`
  - `docs: mettre à jour l'architecture`
  - `perf: optimiser le pool HTTP client`

### Branches
- `main` : Version stable
- `feature/xxx` : Développement de fonctionnalité
- `fix/xxx` : Correction de bug
- `refactor/xxx` : Refactoring

### Fichiers ignorés (.gitignore)
- `node_modules/`, `.venv/`, `__pycache__/`
- `~/.therese/` (données utilisateur)
- `.env` (variables d'environnement)
- `*.db` (bases SQLite)
- `dist/`, `build/`, `target/`
- `.DS_Store`

## Configuration Tauri

### tauri.conf.json (points clés)
- **Identifier** : fr.synoptia.therese
- **Fenêtre** : 1200x800, transparente, sans décoration (natif macOS)
- **CSP** : localhost:8000 + api.anthropic.com autorisés
- **Plugins** : shell, fs (avec restrictions)
- **macOS minimum** : 10.15 (Catalina)
- **Cible** : Safari 14 (macOS), Chrome 105 (fallback)

### Build production
```bash
cd src/frontend
npm run build              # Build Vite (static files)
npm run tauri:build        # Package .app + .dmg
```

**Artefacts** :
- `src/frontend/src-tauri/target/release/bundle/macos/THÉRÈSE.app`
- `src/frontend/src-tauri/target/release/bundle/dmg/THÉRÈSE.dmg`

## Monitoring et logs

### Backend (Python)
- **Framework** : logging standard Python
- **Niveau** : INFO en production, DEBUG en développement
- **Format** : `[%(asctime)s] %(levelname)s %(name)s: %(message)s`
- **Pas de print()** - toujours logger
- **Pas de données sensibles** dans les logs

### Frontend (TypeScript)
- **Console** : console.log en dev, silencieux en production
- **Erreurs** : Capturées par error boundary React
- **Réseau** : Erreurs API loggées dans statusStore

### Health check
- **Endpoint** : GET /health
- **Intervalle** : 30 secondes (frontend)
- **Retry** : Backoff exponentiel (2s, max 5 tentatives)
- **Status** : connected | connecting | disconnected | error

## Performance

### Objectifs
- **Cold start** : < 2 secondes
- **First token** : < 500ms (hors latence LLM)
- **Recherche mémoire** : < 200ms P95
- **Bundle** : < 50 MB
- **Mémoire RAM** : < 500 MB en utilisation normale

### Optimisations en place
- HTTP client pool (20 keepalive, 100 max connections)
- Embeddings en arrière-plan (asyncio.to_thread)
- Sessions DB async (aiosqlite)
- Code splitting frontend (React, UI, Markdown, Tauri en chunks séparés)
- Lazy loading des messages de conversation
- Debouncing des événements SSE côté frontend

## Sécurité de déploiement

### Checklist pré-release
- [ ] Tous les tests passent (backend + frontend + E2E)
- [ ] Lint propre (zéro warning)
- [ ] Pas de secrets dans le code source
- [ ] CORS configuré pour production
- [ ] Rate limiting actif
- [ ] Headers de sécurité en place
- [ ] Sandbox de code opérationnel
- [ ] Migrations appliquées
- [ ] Version bumped dans config.py et package.json

### Signature et distribution macOS
- Code signing avec certificat Apple Developer (TODO)
- Notarization Apple (TODO)
- Distribution via .dmg
- Auto-update via Tauri updater (TODO)

## Anti-patterns DevOps à éviter
- Jamais de `rm` - utiliser `mv vers ~/.Trash/`
- Jamais de push force sur main
- Jamais de migration destructive sans backup
- Jamais de build sans tests passés
- Jamais de secrets en variables d'environnement dans le code
- Jamais de node_modules ou .venv dans le commit
- Pas de tirets longs dans les messages de commit
