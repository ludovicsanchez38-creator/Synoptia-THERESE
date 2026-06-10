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

### Depuis v0.22.0-alpha (10/06/2026, Sprint 0 remédiation audit)
- [ ] **US-016 (perf, issu d'US-001)** : la sandbox d'exécution de code tourne désormais dans un sous-process `spawn` (sécurité). Le child ré-importe `app.services` (donc torch) à chaque génération de document → surcoût de démarrage. À régler par l'import paresseux de torch (retirer la réexport `app/services/__init__.py` + import dans la property `model` d'`embeddings.py`). Voir plan de remédiation Sprint 3.
- [ ] **CSRF `/api/shutdown` (US-005)** : l'endpoint est exempté de l'auth (sinon le shutdown graceful ne s'exécutait jamais). Risque CSRF accepté (ferme l'app, récupérable ; atténué par Private Network Access navigateur). Durcissement possible : faire signer l'appel par les 2 appelants (token lu depuis `~/.therese/.session_token`) — nécessite un changement Rust (`lib.rs`) testé au build.
- [ ] **Reste du plan de remédiation** (`~/Desktop/Plan-remediation-THERESE-2026-06-09.md`) : Sprint 1 (US-006 défenses API rate limit/MCP/fs, US-007 signature binaires + updater, US-008 résilience, US-011 backup complet) puis P2 (chiffrement DB au repos, migrations Alembic unifiées, CI bloquante).

### Dette issue de la vue Accueil (09/06/2026, branche `feat/dashboard-accueil`)
- [ ] **`setup-status` `has_email`** (`dashboard.py`) : teste la simple existence d'une ligne `EmailAccount`, pas la validité du token. Un compte dont l'OAuth a expiré reste compté « branché » et la carte de mise en route disparaît. Acceptable pour l'onboarding ; raffiner si on veut distinguer « configuré » de « connecté valide » (réutiliser la logique de `email auth status`).

### Dette issue de la revue adversariale des correctifs 0.20 (09/06/2026, branche `fix/bugs-post-0.20`)
Findings non-bloquants relevés par la revue 3 agents (les bloquants F1/F2/F3 ont été corrigés dans le commit `fix(review)`). À traiter plus tard :
- [ ] **Valider le fuseau IANA côté backend** (`calendar.py` `_create_event_google` + `update_event`) : `request.timezone` est passé tel quel à Google sans contrôle, alors que le chemin local (`local_provider.py`) le valide via `pytz` avec fallback `Europe/Paris`. Parité à rétablir (un fuseau invalide d'un client mal codé → 400 Google remonté en 500 générique). Valider via `zoneinfo.ZoneInfo(tz)`, fallback Paris.
- [ ] **Sanitiser le `body_html` des mails côté backend** au moment du cache (`email.py get_message`), comme c'est déjà fait pour les signatures (`nh3`). Aujourd'hui la sanitisation est 100 % côté front (`sanitizeEmailHtml` dans `EmailDetail`) : sûr tant que c'est le seul point de rendu, mais fragile si un futur écran affiche le corps sans repasser par le sanitizer. Défense en profondeur.
- [ ] **Contraste des libellés de statut du Kanban projets en thème clair** (`ProjectsKanban.tsx:38-43`) : couleurs Tailwind brutes `text-{green,yellow,blue,red}-400` (surtout `yellow-400`) sous le seuil WCAG AA sur fond clair. Préexistant (pattern partagé CRM/Mémoire) mais plus visible depuis le passage en vue plein écran. Remplacer par les tokens sémantiques theme-aware `text-{success,warning,info,error}`.
- [ ] **Citation des mails HTML-only** (`EmailDetail.tsx` `buildQuotedReply` + `handleForward`) : si `body_plain` est null (mail HTML pur, fréquent), la citation retombe sur le `snippet` tronqué. Dériver un texte du HTML sanitizé (helper `htmlToText`) pour citer le corps complet.
- [ ] **Re-fetch d'un mail réellement vide** (`EmailDetail.tsx`) : un message sans corps (`body_html` ET `body_plain` null : pièce jointe seule, ou erreur serveur) re-déclenche un fetch à chaque ouverture (le garde `if (body_html || body_plain) return` reste faux). Sans effet de bord néfaste, mais inutile. Un flag `bodyFetched` par message l'éliminerait.

### Depuis v0.20.0 (revue produit, 06/06/2026)
- [ ] **Quick-add calendrier local en langage naturel** : la route `POST /api/calendar/events/quick-add` ne fait du parsing NL que via l'API Google quickAdd (Google uniquement). Pour un calendrier local/CalDAV, on renvoie désormais un 400 explicite (au lieu d'un 404 "Account not found" trompeur). Feature à implémenter : un parser de dates FR souverain (stdlib ou dépendance `dateparser`) pour le quick-add local. Tant que ce n'est pas fait, l'événement local se crée via le formulaire.
- [ ] **Boucle d'outils manquante sur Grok / Gemini / Ollama** : leur `stream()` n'émet pas de `tool_call` et `continue_with_tool_results` est un stub (`yield done end_turn`). Conséquence : avec ces fournisseurs, le chat répond en texte mais ne peut pas appeler les outils (CRM, génération de documents, calendrier...). Pas de bug "réponse vide" (le stub n'est jamais atteint puisque le stream n'émet pas d'appel d'outil), contrairement à Mistral qui, lui, émettait des `tool_call` sans relance (corrigé en 0.20.0 en s'alignant sur `openai.py`). À implémenter : parsing tool_calls + continuation pour Grok (format OpenAI, port direct de `openai.py`), Ollama (format Ollama `tools`), Gemini (functionDeclarations/functionResponse).

### Depuis v0.13.2-alpha (04/06/2026)
- [ ] **`config.py:47`** (`ollama_model = "mistral:7b"`) : réglage mort (aucun usage dans le backend, confirmé au grep). À supprimer pour éviter la confusion avec le défaut Ollama dynamique (`detect_default_ollama_model`).
- [ ] **Onboarding `LLMStep.tsx`** : le plafond `max-h-48` a été retiré (BUG-100, masquait Ollama sur macOS). Si la liste des providers devient trop longue sur petit écran, préférer un défilement avec indicateur visible (gradient/affordance) plutôt qu'un conteneur court sans repère.

### Depuis v0.11.8-alpha (29/05/2026)
- [ ] **Mocker** `test_select_openai_provider` / `test_select_gemini_provider` (`tests/test_routers_images.py`, actuellement `@pytest.mark.skip`) : ils déclenchaient une génération d'image réelle (appel externe) -> hang/timeout CI. Rétablir la couverture provider via un mock du service `image_generator`.
- [ ] **27 warnings ESLint** préexistants (`react-hooks/exhaustive-deps`, `react-refresh/only-export-components`) : seuil `--max-warnings` rehaussé 26 -> 27 dans `src/frontend/package.json`. Correction = revue des dépendances de hooks composant par composant (risque de régression, à faire posément).
- [ ] Harmoniser le ton du message de confirmation `/rdv` (délègue à `execute_workspace_tool` -> format "Evenement cree : ..." sans accent et différent de `/contact`/`/projet`). Idéalement wrapper le retour calendrier + accentuer dans `workspace_tools.py`.
- [ ] Découvrabilité de la syntaxe `clé=valeur` des commandes déterministes : `handleSlashCommandSelect` (ChatInput.tsx) n'insère que le préfixe ; envisager un template/placeholder.
- Note infra : hook `pytest_sessionfinish` ajouté dans `tests/conftest.py` (force `os._exit` après la suite) pour contrer le hang de sortie dû aux threads orphelins des tests async (CI tuée à 5 min sinon).

## Backlog fonctionnel (suggestions testeurs 22/03/2026)

### P1
- [ ] Découplage données lourdes : retranscriptions hors champ description SQLite (stocker dans Qdrant ou fichiers, preview dans DB) - risque perf

### P2
- [ ] Export tâches en .ics (vEvent) + envoi par mail
- [ ] Import/export contacts VCard (.vcf) depuis fichier local ou téléphone
- [ ] UX CRM drag & drop : déplacer un contact ne doit pas forcer la création d'une activité
- [ ] Doc : pré-requis matériels SSD (DWPD/TBW) pour IA locale

### P3
- [ ] Import .ics depuis mail ou fichier local (parser icalendar)

### Refusé
- BYOS (connexion via compte ChatGPT/Claude sans API) : violation ToS, fragile, non maintenable

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
