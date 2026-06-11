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

### Depuis chantier UX/DA (11/06/2026, commits 203b752..254321a)
- [ ] **window-state et moniteur debranche** : le plugin restaure la POSITION brute sans verifier que le moniteur existe encore (limitation connue tauri-plugin-window-state) - fenetre potentiellement hors ecran apres debranchement d'un externe. Garde possible : post-restore, re-center si hors bornes de `available_monitors()` (lib.rs setup).
- [ ] **bump-version.sh ne regenere pas uv.lock** : la 0.23 est partie avec un uv.lock en 0.22.0 (rattrape commit a1b7422). Ajouter `uv lock` au script (ou a l'etape bump du skill /release-therese, comme le `npm install --package-lock-only` deja prevu).
- [ ] **Doublons macOS dans tests/protocols/app/personas/** : `A1-sophie-freelance 2.md`, `A2-marc-consultant 2.md`, `A3-lea-power-user 2.md` (copies accidentelles, non annotees sidebar-fermee). A supprimer apres confirmation Ludo.
- [ ] **DA brutaliste partielle** : Button.tsx + home + badges PARTOUT (lot 2 badges fait le 11/06, commits a88e127/0031b67 : tous les badges d'etat en tags carres rounded-[6px], restent ronds compteur cloche/toggles/radios/avatars). Pastilles d'icones duotone bordees partout (1d90de7, fin des degrades cyan-magenta - lanceur guide, skills, settings, board, sidebar). Cartes de panneaux, inputs, modales, bulles de message, SideToggle gardent l'ancien style doux - lot 3 eventuel. Balayage final c7cf627 : 37 pastilles degradees converties (panels, settings, modales, wizard email, About, avatars) - PLUS AUCUNE pastille gradient dans l'app. Conserves volontairement : orbe decorative GuidedPrompts, barres de progression gradient, titres gradient-text de marque, rails SideToggle.

### Depuis Sprint 3 (11/06/2026)
- [ ] **E2E Playwright hors CI** : tests/e2e toujours exclus (`--ignore=tests/e2e`) - ils exigent Vite + uvicorn + navigateur, flaky en CI. US-018 a durci le reste (audits bloquants, clippy -D warnings, mypy baseline) ; un job e2e nightly (pas par PR) reste à concevoir.
- [ ] **mypy baseline 1059 erreurs** (ci.yml job mypy) : gate anti-régression seulement. Faire baisser le compteur module par module et mettre à jour MYPY_BASELINE à chaque baisse.
- [ ] **torch 2.9.1 épinglé avec 3 CVE ignorées** (ci.yml security-audit) : bump vers 2.10 à planifier (PyInstaller 3 OS + release.yml à mettre à jour ensemble). transformers 4.57.6 : attendre la 5.0 stable.

### Depuis Sprint 2 (11/06/2026, findings minor de la revue adversariale, non bloquants)
- [ ] **Multi-tours d'outils** : `_execute_tools_and_continue` (chat.py) rappelle `continue_with_tool_results` avec le contexte ORIGINAL : les functionCall/résultats du tour précédent disparaissent de l'historique envoyé au modèle (qui peut re-demander un outil déjà exécuté). Pattern partagé par TOUS les providers (pas introduit par US-009, mais désormais atteignable sur Grok/Ollama/Gemini). Garde-fous existants : cap de créations, max 5 itérations, dédup par nom. Fix : accumuler les tours d'outils dans le contexte de la récursion.
- [ ] **Gemini 2.x + tools = grounding perdu silencieusement** : dès que des tools sont fournis (toujours en chat), google_search est écarté sur gemini-2.x (combinaison non documentée hors Gemini 3) et chat.py n'ajoute pas WEB_SEARCH_TOOL en compensation (commentaire chat.py:866 devenu faux). Impact limité : l'UI ne propose plus que du 3.x. Fix : ajouter WEB_SEARCH_TOOL aux tools Gemini quand le grounding est écarté.
- [ ] **Protocoles de test manuels vs virtualisation** : les personas (tests/protocols/app/personas/*.md) comptent les messages via querySelectorAll('[data-testid="chat-message-item"]') - avec react-virtuoso, seuls les items de la fenêtre de rendu sont dans le DOM. Mettre à jour les protocoles (compter via useChatStore.getState() ou scroller avant de cibler).
- [ ] **debouncedStorage** : wrapper testé isolément mais pas de test d'intégration avec le persist/rehydrate Zustand réel. Le flush de fermeture repose sur beforeunload+pagehide+visibilitychange ; un flush explicite déclenché côté Rust avant destruction de la fenêtre serait plus sûr (à câbler avec lib.rs au prochain chantier Rust).
- [ ] **Arguments d'outils JSON invalides → {} silencieux** : openai.py:135 (hérité par grok/deepseek/openrouter/perplexity/infomaniak) et ollama.py retombent sur des arguments vides en cas de JSONDecodeError - l'outil est exécuté sans arguments au lieu de signaler. Comportement figé par test (test_grok_arguments_invalides_comportement_fige) ; à reconsidérer si un cas réel montre qu'un échec explicite serait préférable.

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
