# CLAUDE.md - THÉRÈSE V2

> Contexte projet pour Claude Code - Ne pas supprimer

## Projet

**THÉRÈSE v2** - Assistant IA desktop souverain pour solopreneurs et TPE français.
Alternative à Cowork (Anthropic) avec mémoire persistante, UX premium dark mode, et données 100% locales.
Créateur : Ludo Sanchez (Synoptïa) - "Ta mémoire, tes données, ton business."

- **Repo** : `github.com/ludovicsanchez38-creator/Synoptia-THERESE` - branche `main`
- **Open source, gratuit** - alpha en cours (lancée fév 2026)
- **Source VPS** : `/home/ubuntu/therese-v2/` (VPS Agents 51.178.16.63)
- **Source locale** : `~/Desktop/Dev Synoptia/THERESE V2/`
- **CI** : GitHub Actions - workflow CI (lint + tests) + workflow Release (build Tauri macOS/Windows/Linux)

## Stack technique

- **Frontend** : Tauri 2.0 + React 19 + TailwindCSS 4 + Framer Motion + Zustand 5
- **Backend** : Python FastAPI + UV + SQLModel + Alembic (migrations)
- **Database** : SQLite (données) + Qdrant (embeddings vectoriels, nomic-embed-text-v1.5, 768 dim)
- **LLM** : Multi-provider (Anthropic, OpenAI, Gemini, Mistral, Grok, OpenRouter, Ollama)
- **Skills Office** : python-docx, python-pptx, openpyxl (sandbox code-execution)
- **Desktop** : Tauri 2.0 (Rust) avec sidecar PyInstaller
- **Sécurité** : Fernet/Keychain, anti-injection prompt, rate limiting, CORS restrictif
- **MCP** : 19 presets (transport stdio, JSON-RPC)
- **Tests** : Vitest (frontend), pytest (backend), Playwright (E2E)

## Commandes essentielles

```bash
# Développement
make dev                  # Backend + Tauri simultanés
make dev-backend          # Backend seul (uvicorn :17293)
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
cd src/backend && uv run uvicorn app.main:app --reload --port 17293
cd src/frontend && npm run tauri dev
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

- `docs/CHANGELOG.md` - Historique structuré par version
- `docs/DEVLOG.md` - Journal de développement complet
- `docs/architecture.md` - Architecture technique détaillée
- `docs/API.md` - Documentation API
- `docs/prd-therese.md` - PRD complet
- `docs/stories/` - 35 user stories, 5 epics

---

## État du projet (màj 18 fév 2026)

### Chiffres clés
- **Code** : ~62 200 lignes (31 600 frontend + 30 600 backend)
- **Tests** : ~10 350 lignes (pytest + Vitest + Playwright E2E)
- **Endpoints API** : 170+ (22 routers FastAPI)
- **Tables SQL** : 16 (SQLite) + Qdrant vectoriel
- **Version actuelle** : v0.2.6-alpha (18 fév 2026)
- **Tests de non-régression** : `tests/test_regression.py` (141 tests couvrant BUG-002 à BUG-040 + XSS + scroll + UX + OpenRouter + Fal + Ollama + upload + skill_id + raccourci + calendrier + CRM + pricing + streaming + email + stop)

### Modules fonctionnels
Chat multi-LLM, Mémoire (contacts/projets/recherche sémantique), Skills Office (DOCX/PPTX/XLSX), Email (Gmail OAuth + IMAP/SMTP + classification IA), Calendrier (Google + CalDAV + local), CRM (pipeline, scoring, sync Google Sheets, import/export), Facturation (devis/facture/avoir, PDF conforme, TVA franchise en base), Board de décision IA (5 conseillers), Génération d'images (DALL-E 3 + Gemini), Transcription vocale (Groq Whisper), MCP (19 presets), RGPD (export, anonymisation), Calculateurs (ROI, ICE, RICE, NPV)

---

## Bugs

### Bugs corrigés (v0.1.1 à v0.2.6)
- v0.1.2 : Port 8000 hardcodé (port dynamique auto)
- v0.1.3 : Verrou Qdrant non libéré (nettoyage auto du .lock)
- v0.1.4 : Crash DLL Windows (strip=False + upx=False), quarantaine macOS (suppression auto), build Tauri (use tauri::Emitter)
- v0.1.5 : Zombies backend non tués au redémarrage (pkill/taskkill), port mismatch panel windows
- v0.1.6 : Load failed module PyInstaller (resource_tracker patch + freeze_support), landing 404 corrigé
- v0.1.7 : Audit contradictoire (XSS emails DOMPurify, singleton API_BASE, polyfill Safari, Error Boundary PanelWindow, tests), BUG-009 sidecar Windows (protection stdio + parent PID exclusion + diagnostic)
- v0.1.8 : Fix crash sidecar toutes plateformes - retrait des excludes torch du backend.spec
- v0.1.9 : Fix CRM Google Sheets 401 (refresh token), Keychain au démarrage (allow_decrypt=False)
- v0.1.10 : Fix IPC Mac M1 (initApiBase retry 10x 300ms)
- v0.1.11 : Fix crash Mac M4 Max (device='cpu' embeddings), Keychain lazy init (pas de prompt au boot)
- v0.1.12 : Splash timeout 60s→120s (premier lancement), tests de non-régression (19 tests)
- v0.1.13 : Fix clés API envoyées chiffrées aux providers (blob Fernet), cache clés corrompues, CRM sync NoneType
- v0.1.14 : Fix BUG-009 lock Qdrant Windows (retry backoff), SMTP/IMAP config, CRM Google Sheets auto-création, compatibilité Windows 11 25H2+
- v0.1.15 : BUG-015 port mismatch panels CRM/Email (port via URL), zombie killer Rust tasklist fallback Windows 11 25H2+, scroll streaming instantané, 31 tests
- v0.1.16 : BUG-017 redirection TEMP sidecar Windows (Defender bloque PyInstaller), CRM address manquant (ContactResponse), probeHealth accepte degraded, productName sans accent (deb Linux)
- v0.1.17 : BUG-020 timeout splash Windows (120s → 600s/10 min), polling 2s, messages adaptatifs, progression logarithmique, 41 tests
- v0.1.18 : Démarrage rapide backend (preload non-bloquant), scroll streaming throttlé rAF, sidebar visible, renommage "Mémoire", tooltip tokens/EUR, logo cliquable, bouton déconnecter email, 51 tests
- v0.1.19 : Port fixe 17293 (suppression port dynamique find_free_port), simplification chaîne IPC
- v0.1.20 : BUG-022 CORS Windows (http://tauri.localhost ajouté), diagnostics probeHealth verbeux (timeout 5s, console.error dans catch), middleware PNA (WebView2 143+), middleware CORS debug, 56 tests
- v0.2.0 : OpenRouter provider (200+ modèles LLM via API OpenAI-compatible), Fal Flux Pro (images), BUG-023 race condition email (AbortController + isLoadingRef + getState()), fix version À propos (checkHealth dans panels), 74 tests
- v0.2.2 : BUG-024 templates DOCX/PPTX manquants PyInstaller (collect_data_files docx + pptx), streaming par blocs (flush 300ms), bouton Image IA (Fal) prompts guidés, bump versions synchronisées, 81 tests
- v0.2.3 : BUG-025 Ollama 404 (system prompt dans messages), BUG-026 profil save (WHERE clause user_id vs name), streaming phrase-par-phrase (flush ponctuation), upload fichiers projets, macOS 13.3 min, 89 tests
- v0.2.4 : Skills enrichis (skill_id dans chat, system prompt injecté), sauvegarder comme raccourci (Bookmark chat → CreateCommandForm), BUG-029 email reconnexion 401, BUG-033 accent répertoire, BUG-034 micro pluginReady, image bouton Utiliser, calendrier vues Semaine+Jour, CRM suppression Projets + activités globales, 108 tests
- v0.2.5 : BUG-028 prix EUR (stripping préfixe provider OpenRouter), BUG-035 templates DOCX/PPTX (runtime hook PyInstaller), fix streaming partiel (texte brut pendant streaming, minHeight progressive, CSS containment), 121 tests
- v0.2.6 : BUG-025 Ollama fix définitif (role: system dans messages, rstrip trailing slash), BUG-036 XLSX/DOCX/PPTX code tronqué (_ensure_save_call avec regex + load_workbook), BUG-038 bouton Stop streaming (AbortController), BUG-039 bouton email MessageBubble (mailto:), BUG-040 DOCX page blanche (ensure save), system prompt anti-tableaux, contraste dropdown, 141 tests

### Matrice de traçabilité bugs (18 fév 2026)

| Bug | Description | Statut | Confirmé par |
|-----|-------------|--------|-------------|
| BUG-001 | Bug de test (pas de prod) | Résolu | N/A |
| BUG-002 | Port 8000 hardcodé | Fixé v0.1.2 | Julien |
| BUG-003 | Verrou Qdrant | Fixé v0.1.3 | Julien |
| BUG-004a | Landing 404 | Fixé v0.1.6 | Oui |
| BUG-004b | Quarantaine macOS | Fixé v0.1.4 | Oui |
| BUG-005 | DLL Windows | Fixé v0.1.4 | Julien |
| BUG-006 | Load failed | Fixé v0.1.6 | **Attente Julien** |
| BUG-007 | Zombies backend | Fixé v0.1.5 | Denis (11 fév) |
| BUG-008 | Port mismatch | Fixé v0.1.5 | Oui |
| BUG-009 | Coralie Windows | Fixé v0.1.7 | **Attente WebPadawan** |
| BUG-010 | torch.cuda/distributed exclu du bundle | Fixé v0.1.8 | Ludo (12 fév) |
| BUG-011 | IPC Tauri pas prêt sur Mac M1 | Fixé v0.1.10 | Denis (12 fév) |
| BUG-012 | Crash silencieux Mac M4 Max (MPS) | Fixé v0.1.11 | **Attente Richard** |
| BUG-013 | Keychain bloque démarrage 20+s | Fixé v0.1.11 | Denis + Ludo (13 fév) |
| BUG-014 | Splash timeout 60s premier lancement | Fixé v0.1.12 | Ludo (13 fév) |
| BUG-015 | Port mismatch panels (CRM, Email) | Fixé v0.1.15 | Ludo (13 fév) |
| BUG-016 | CRM address manquant ContactResponse | Fixé v0.1.16 | Zézette (14 fév) |
| BUG-017 | Sidecar crash Windows (Defender TEMP) | Fixé v0.1.16 | **Attente testeurs Windows** |
| BUG-019 | Raccourci bureau dupliqué (NSIS Windows) | Cosmétique | Non fixable en code (packaging NSIS) |
| BUG-020 | Timeout splash Windows (backend 2min27s) | Fixé v0.1.17 | **Attente Dr_logic-3D (Jérôme)** |
| BUG-021 | Backend ne répond jamais (Laroll, Ryzen 5) | Fixé v0.1.18 | **Attente Laroll** |
| BUG-022 | CORS Windows (http://tauri.localhost absent) | Fixé v0.1.20 | **Attente testeurs Windows** |
| BUG-023 | Race condition email (loadMessages concurrent) | Fixé v0.2.0 | **Attente test** |
| BUG-024 | Templates DOCX/PPTX manquants dans PyInstaller | Fixé v0.2.2 | **Attente test** |
| BUG-029 | Email "Impossible de charger" sans reconnexion | Fixé v0.2.4 | **Attente test** |
| BUG-030 | Suppression email dit "impossible" mais supprime | Fixé v0.2.4 | **Attente test** |
| BUG-031 | Bouton "Utiliser" manquant ImageGenerationPanel | Fixé v0.2.4 | **Attente test** |
| BUG-033 | Sidebar "repertoire" sans accent + erreur lecture | Fixé v0.2.4 | **Attente test** |
| BUG-034 | Microphone ne marche plus (plugin async) | Fixé v0.2.4 | **Attente test** |
| BUG-035 | Templates DOCX/PPTX manquants (runtime hook) | Fixé v0.2.5 | Ludo (16 fév) |
| BUG-036 | XLSX échoue (code LLM tronqué, fallback vide) | Fixé v0.2.6 | Zézette (17 fév) |
| BUG-037 | Saut streaming résiduel (réduit mais pas éliminé) | Ouvert | Ludo (16 fév) |
| BUG-038 | Impossible d'interrompre un output en cours | Fixé v0.2.6 | Zézette (17 fév) |
| BUG-039 | Pas d'action après génération email dans chat | Fixé v0.2.6 | Zézette (18 fév) |
| BUG-040 | DOCX page blanche (code tronqué sans .save) | Fixé v0.2.6 | Zézette (18 fév) |

---

## Audits

### Audit alpha (8 fév 2026)
- **14 agents** déployés (4 inventaire + 5 testeurs virtuels + 5 correcteurs)
- **3 murs unanimes** identifiés : clé API incompréhensible pour le public cible, GitHub Releases inadapté, aucune release existante (corrigé)
- **Corrections appliquées** : bug release.yml Windows, Linux ajouté au build, doc vulgarisée (5 fichiers), api.ts monolithique supprimé (-3030 lignes), facturation améliorée (devis/avoir/TVA auto/mentions légales), 84 fichiers commités
- **Rapport** : `~/Desktop/Rapport-Audit-Alpha-THERESE-2026-02-08.docx`

### Audit contradictoire v0.1.7 (11 fév 2026)
- **9 agents** déployés en 3 vagues : exploration bugs/logs, audit backend (31 issues), audit frontend/Tauri (13 issues), devil's advocate, matrice traçabilité, audit sécurité Rust/Tauri, recherche web bugs connus, audit couverture tests, synthèse contradictoire
- **Verdict** : v0.1.6 à 82% prête - 38% faux positifs, 40% théoriques, 22% dette technique, 1 P0
- **Fixes appliqués sur branche `fix/audit-v017`** :
  1. **P0 XSS emails** : DOMPurify ajouté dans `EmailDetail.tsx` (sanitizeEmailHtml avec ALLOWED_TAGS/ATTR restrictifs)
  2. **P1 Singleton API_BASE** : `initApiBase()` transformé en singleton Promise partagée dans `core.ts`
  3. **P1 Polyfill AbortSignal.timeout** : `createTimeoutSignal()` dans `SplashScreen.tsx` (Safari <17.4)
  4. **P1 Error Boundary** : `PanelErrorBoundary` class component ajouté dans `PanelWindow.tsx`
  5. **P1 Tests** : 3 fichiers créés (PanelWindow.test.tsx 7 tests, test_main_startup.py 9 tests, test_qdrant_lock.py 4 tests)
  6. **P2 Taille binaire** : torch CPU-only dans release.yml pour Windows/Linux (skip macOS)
  - **ATTENTION** : les excludes torch (torch.cuda, torch.distributed, torch.testing, torch.utils.tensorboard) ajoutés dans le point 6 ont cassé le sidecar sur toutes les plateformes. Retirés en v0.1.8.
- **Issues restantes non traitées** :
  - P2 : Async lock singleton Qdrant, memory leak rate limiter
  - P3 : Apple Developer Program (99 USD/an), migration torch → fastembed (ONNX), sécurisation exec() code_executor

---

## CI & Releases

### CI GitHub Actions
- **CI THÉRÈSE V2** : lint Ruff + pytest backend + vitest frontend. Le lint Python échoue actuellement (erreurs de style, PAS bloquant pour les testeurs). Les 10 warnings frontend sont des dépendances manquantes dans les hooks React.
- **Release THÉRÈSE** : build Tauri (macOS ARM64 + Windows x64 + Linux x64). Se déclenche sur push de tag. v0.2.2-alpha build 3/3 success (15 fév).
- **Leçon v0.1.7** : NE JAMAIS exclure de sous-modules torch dans backend.spec - torch les importe tous à l'init.

### Releases GitHub

| Version | Date | Statut | Contenu clé |
|---------|------|--------|-------------|
| v0.1.0-alpha | 9 fév | Pre-release | Première release |
| v0.1.1-alpha | 9 fév | Draft | Version initiale, liens 404 |
| v0.1.2-alpha | 10 fév | Pre-release | Fix port dynamique |
| v0.1.3-alpha | 10 fév | Pre-release | Fix verrou Qdrant |
| v0.1.4-alpha | 10 fév | Pre-release | Fix DLL Windows + quarantaine macOS (.dmg, .exe, .msi, Linux) |
| v0.1.5-alpha | 10 fév | Pre-release | Fix zombies + port mismatch |
| v0.1.6-alpha | 11 fév | Pre-release | Fix Load failed + landing 404 |
| v0.1.7-alpha | 12 fév | **CASSÉE** | Excludes torch - audit XSS + singleton + polyfill + tests |
| v0.1.8-alpha | 12 fév | Pre-release | Fix crash sidecar (retrait excludes torch). macOS smoke test OK |
| v0.1.9-alpha | 12 fév | Pre-release | Fix CRM Google Sheets 401 + Keychain |
| v0.1.10-alpha | 12 fév | Pre-release | Fix IPC Mac M1 (initApiBase retry) |
| v0.1.11-alpha | 13 fév | Pre-release | Fix crash Mac M4 Max (MPS) + Keychain lazy init |
| v0.1.12-alpha | 13 fév | Pre-release | Splash timeout 120s + 19 tests |
| v0.1.13-alpha | 13 fév | Pre-release | Fix clés API chiffrées envoyées aux providers |
| v0.1.14-alpha | 13 fév | Pre-release | Fix lock Qdrant Windows + SMTP + CRM auto + Windows 11 25H2+ (.dmg, .exe, .msi, .deb) |
| v0.1.15-alpha | 13 fév | Pre-release | Fix port mismatch panels + zombie killer Rust + scroll streaming |
| v0.1.16-alpha | 14 fév | Pre-release | PRs Zézette : BUG-017 TEMP sidecar + CRM address + degraded status |
| v0.1.17-alpha | 14 fév | Pre-release | BUG-020 timeout splash Windows 10 min + 41 tests |
| v0.1.18-alpha | 15 fév | Pre-release | Démarrage rapide backend + scroll rAF + sidebar + tooltip + 51 tests |
| v0.1.19-alpha | 15 fév | Pre-release | Port fixe 17293, simplification IPC |
| v0.1.20-alpha | 15 fév | Pre-release | BUG-022 CORS Windows + diagnostics probeHealth + middleware PNA + 56 tests |
| v0.2.0-alpha | 15 fév | Pre-release | OpenRouter (200+ LLM) + Fal Flux Pro + BUG-023 email + 74 tests |
| v0.2.2-alpha | 15 fév | Pre-release | BUG-024 templates DOCX/PPTX + streaming blocs + Image IA + 81 tests (.dmg, .exe, .msi, .deb) |
| v0.2.3-alpha | 16 fév | Pre-release | BUG-025 Ollama + BUG-026 profil + streaming phrase + upload + 89 tests (.dmg, .exe, .msi, .deb) |
| v0.2.4-alpha | 16 fév | Pre-release | Skills enrichis + raccourcis + calendrier + CRM + 6 bug fixes + 108 tests |
| v0.2.5-alpha | 16 fév | Pre-release | BUG-028 prix + BUG-035 templates runtime hook + streaming partiel + 121 tests |
| v0.2.6-alpha | 18 fév | Pre-release | BUG-036 XLSX + BUG-038 stop + BUG-039 email + BUG-040 DOCX + Ollama fix + 141 tests |

---

## Alpha - Communauté

### Discord - Serveur therese-alpha (guild 1468547481662132386)

| Channel | ID | Usage |
|---------|----|----|
| #bienvenue | 1468547482660241574 | Accueil des nouveaux |
| #annonces | 1468549611034771613 | Missions hebdomadaires |
| #roadmap | 1468549879004397701 | Roadmap produit |
| #discussion | 1468550844118073425 | Discussion libre |
| #presentations | 1468551121797910609 | Présentations testeurs |
| #bugs | 1468552203789930662 | Signalement bugs |
| #suggestions | 1468552716925272084 | Suggestions |
| #admin | 1468554061359091816 | Salon privé Ludo |

### Testeurs (16 inscrits, 10 fév 2026)
Laroll (Yoan), Julien, Arnolhn, Alb, Flo'Houx (Florent), Psychedelic_Mayhem (Paulin), Capov (Richard), Denis38, Gilles, Dr_logic-3D (Jérôme), Dominique, Camille, WebPadawan, Ydelyn (Lorris), Sara, CBR_75 (Charles)

### Programme alpha (7 semaines, S0 à S6)
- S0 : Installation + config (Ollama + clé API Mistral)
- S1 : Chat + onboarding
- S2 : Skills Office (PPTX/DOCX/XLSX)
- S3 : Mémoire + contacts
- S4 : CRM + facturation
- S5 : Edge cases + stress
- S6 : Parcours complet + feedback

---

## Roadmap

### v0.2.4-alpha (16 fév 2026) - FAIT
- [x] Skills enrichis : skill_id dans le chat endpoint, injection du system prompt du skill pour Comprendre/Organiser
- [x] Sauvegarder comme raccourci : bouton Bookmark dans le chat, modal CreateCommandForm pré-rempli
- [x] BUG-029 Email reconnexion 401 (détection token expiré, bouton reconnecter)
- [x] BUG-030 Suppression email race condition (confirmé déjà fixé)
- [x] BUG-031 Image bouton "Utiliser" (ImageGenerationPanel)
- [x] BUG-033 FileBrowser accent "répertoire" + fallback home
- [x] BUG-034 Microphone pluginReady (désactiver bouton micro tant que plugin pas chargé)
- [x] Calendrier vues Semaine (grille 7 colonnes 8h-20h) et Jour (créneaux 30min 6h-22h)
- [x] CRM suppression onglet Projets, activités globales avec filtres, ajout manuel d'activité
- [x] 108 tests de non-régression (19 nouveaux)

### v0.2.5-alpha (16 fév 2026) - FAIT
- [x] **BUG-028** : Fix prix EUR 0.0000 - stripping préfixe provider dans `estimate_cost()` (OpenRouter `anthropic/model` → `model`)
- [x] **BUG-035** : Templates DOCX/PPTX - runtime hook PyInstaller pour embarquer XML (python-docx, python-pptx)
- [x] **Fix streaming (partiel)** : texte brut pendant streaming (plus de re-parse ReactMarkdown), min-height progressive, CSS containment. Réduit les sauts mais ne les élimine pas totalement.
- [x] Landing page : badge v0.2.5, liens téléchargement, notes d'installation (macOS quarantaine + 13.3, Windows Defender, Linux .deb)
- [x] 121 tests de non-régression (+13 : 4 BUG-028, 3 streaming, 6 BUG-035)

### v0.2.6-alpha (18 fév 2026) - FAIT
- [x] **BUG-036** : Fix XLSX/DOCX/PPTX code tronqué - `_ensure_save_call()` avec regex + détection `load_workbook()`, aussi appelé sur le chemin code valide dans `repair_truncated_code()`
- [x] **BUG-038** : Bouton Stop streaming - `AbortController` côté frontend, bouton carré rouge pendant le streaming, AbortError capturé proprement (contenu partiel affiché)
- [x] **BUG-039** : Bouton email dans MessageBubble - `mailto:` avec limite 500 chars, clipboard fallback en try/catch, masqué pendant le streaming
- [x] **BUG-040** : DOCX page blanche - `_ensure_save_call()` détecte `Document()` et `Presentation()`, protection sur le chemin code valide
- [x] **BUG-025** : Ollama fix définitif - `role: "system"` dans messages array (plus de champ top-level), `rstrip("/")` sur base_url
- [x] System prompt anti-tableaux/anti-emojis pour réponses plus légères
- [x] Contraste dropdown LLM (classes CSS sur `<option>`)
- [x] 141 tests de non-régression (+20 : Ollama, XLSX, email, stop, DOCX/PPTX save)

### TODO v0.2.7-alpha (prochaine version)
- [ ] **BUG-037** : Saut streaming résiduel - le fix v0.2.5 (texte brut + minHeight) réduit les sauts mais ne les élimine pas complètement. **Piste** : évaluer `use-stick-to-bottom` (lib StackBlitz, ResizeObserver + spring animations) ou utiliser `scrollIntoView` avec `behavior: smooth` sur le dernier élément
- [ ] **BUG-027** : Compteur tokens faux - le backend estime avec `len(text)//4` au lieu d'utiliser les vrais compteurs renvoyés par les API. Ajouter champ `usage` dans `StreamEvent` (base.py), récupérer `input_tokens`/`output_tokens` de chaque provider
- [ ] **UX** : File d'attente de messages visible - quand l'IA répond, permettre d'envoyer un message suivant qui s'affiche en attente et sera traité après la réponse en cours
- [ ] Filtrage `<think>...</think>` pour les modèles raisonnement (DeepSeek R1, Qwen QwQ, etc.) - cacher le raisonnement interne ou l'afficher dans un bloc dépliable
- [ ] Paramètres commandes utilisateur (Phase 3 : `{{param}}` dans les templates)

### Backlog
- [ ] Attendre confirmation Julien sur BUG-006 (v0.1.6)
- [ ] Attendre confirmation WebPadawan sur BUG-009 (Windows v0.1.8)
- [ ] Attendre confirmation Richard sur BUG-012 (Mac M4 Max)
- [ ] Communiquer v0.2.4 sur Discord #annonces (priorité : Jérôme/Dr_logic-3D pour test Windows)
- [ ] Corriger le lint Python (ruff) pour que la CI passe au vert
- [ ] Envisager clé API partagée ou proxy pour testeurs non-techniques
- [ ] Code signing Apple (99 USD/an) + Windows (70-300 EUR/an)
- [ ] Tuto vidéo installation (3 min YouTube)
- [ ] Templates métier pré-faits (devis consultant, facture artisan, PV d'AG)
- [ ] Mise à jour automatique (tauri-plugin-updater)
- [ ] Async lock singleton Qdrant (P2)
- [ ] Memory leak rate limiter - ajouter GC ou TTL dict (P2)
- [ ] Migration torch → fastembed ONNX (~1.8 Go gagné sur binaire) (P3)
- [ ] Sécuriser exec() dans code_executor.py pour v1.0 (P3)

---

## Agents IA (màj 13 fév 2026)

### OpenClaw 2026.2.12 (VPS 51.178.16.63)

3 agents sur le même VPS, même gateway :
```
openclaw agents    # voir les 3 agents
openclaw health    # vérifier la santé du gateway
```

**State dir** : `~/.openclaw/` (NE PLUS utiliser `/opt/clawdbot/.clawdbot/`, archivé)
**Service** : `systemctl --user status openclaw-gateway.service` (PAS le service système `/etc/systemd/system/openclaw.service` qui est disabled)
**Config** : `/home/ubuntu/.openclaw/openclaw.json`
**Logs** : `/tmp/openclaw/openclaw-YYYY-MM-DD.log`

#### Bug connu v2026.2.12 - agents non-default
`resolveSessionFilePath()` ne passe pas `{ agentId }` pour les agents non-main (therese, zezette), causant "Session file path must be within sessions directory". **Patch appliqué** sur `/usr/lib/node_modules/openclaw/dist/reply-B5GoyKpI.js` (lignes 63597 et 58627). Backup : `reply-B5GoyKpI.js.bak-20260213`. Le patch sera écrasé à la prochaine MAJ OpenClaw (le bug devrait être corrigé upstream). En complément : champs `sessionFile` supprimés de tous les `sessions.json`.

#### Optimisations identifiées (non appliquées)
- Thérèse sur Sonnet 4.5 au lieu d'Opus (conversation, pas besoin de raisonnement fort)
- Heartbeat à 55 min (cache prompt Anthropic expire après 1h) + activeHours 07:00-23:00
- Sous-agents Zézette sur Sonnet 4.5 (recherche + challenger)
- `subagents.maxConcurrent: 2` au lieu de 8 (bug contention locks #4355)
- `compaction.memoryFlush.enabled: true` (sauvegarde MEMORY.md avant compression contexte)

### Thérèse (bot Discord 24/7)
- **Rôle** : communauté alpha, accueil testeurs, récolte bugs, guide installation
- **Modèle** : claude-opus-4-6 (envisager Sonnet 4.5)
- **Workspace** : `/opt/clawdbot/workspace-therese/`
- **Clone THÉRÈSE** : `/opt/clawdbot/workspace-therese/therese-src/` (git pull auto 6h UTC)
- **Mémoire** : `workspace-therese/memory/` (26 fichiers : BUGS.md, TESTEURS.md, FAQ.md, CHANGELOG.md, notes quotidiennes...)
- **HEARTBEAT** : résumé quotidien 18h + vérification fixes Zézette à chaque session
- **Routing** : Discord default (serveur therese-alpha)
- **Ack reactions** : désactivées (`ackReactionScope` supprimé de la config, SOUL.md dit ZERO EMOJI)

### Zézette (agent dev nocturne)
- **Rôle** : corriger bugs, écrire tests, refacto ciblé, créer des PR
- **Modèle** : claude-opus-4-6
- **Workspace** : `/opt/clawdbot/workspace-zezette/`
- **Clone THÉRÈSE** : `/home/ubuntu/therese-v2/` (git stash + git pull dans son workflow)
- **Cron** : 2h UTC lun-ven via `/home/ubuntu/zezette-nuit.sh` (timeout 1h, retry 1x si API down)
- **Skills OpenClaw** : github (gh CLI), healthcheck, skill-creator, tmux, weather
- **Sous-agents** :
  - Spawn recherche (avant de coder) : cherche doc/solutions via web
  - Spawn challenger (après le fix) : review adversariale du diff
  - Spawn testeur (optionnel) : tests en arrière-plan
- **Workflow** : fiche bug -> recherche -> analyse -> branche -> fix -> tests -> review challenger -> itérer (max 3) -> commit -> push -> PR -> notification
- **Escalade** : après 3 tentatives, déplace en `bug-queue/escalated/` avec analyse détaillée
- **Fichiers** : SOUL.md (8.3k), TOOLS.md (4.9k), AGENTS.md (5.2k), IDENTITY.md, MEMORY.md, USER.md ~ 15.7k/20k chars
- **Git exclude** : fichiers OpenClaw workspace ignorés via `.git/info/exclude`
- **Lancer manuellement** : `ssh ubuntu@51.178.16.63 "openclaw agent --agent zezette --message '...' --timeout 600"`

### Clawdine (agent main)
- **Rôle** : agent par défaut, WhatsApp + Discord
- **Workspace** : `/opt/clawdbot/workspace/`

### Communication Thérèse <-> Zézette
```
Testeur Discord -> Thérèse -> bug-queue/pending/fiche.md -> Zézette (nuit)
                                                               |
Testeur Discord <- Thérèse <- memory/BUGS.md             <- bug-queue/done/
                                                          <- bug-queue/escalated/ (si non corrigeable)
```
- Thérèse crée les fiches bug dans `/home/ubuntu/bug-queue/pending/`
- Zézette les traite, déplace en `done/` (ou `escalated/`), et met à jour le `memory/BUGS.md` de Thérèse
- Thérèse vérifie `bug-queue/done/` à chaque session (HEARTBEAT) et informe les testeurs
- Pas de communication directe entre agents (fichiers partagés uniquement)
- Template fiche bug : `/home/ubuntu/bug-queue/TEMPLATE.md`
- Bug-queue dossiers : `pending/`, `in-progress/`, `done/`, `escalated/`

### TODO agents
- [ ] Créer webhook Discord sur #dev-log et l'ajouter dans `/home/ubuntu/zezette-nuit.sh`
- [ ] Donner permission SendMessages au bot Thérèse sur #changelog (ID 1468552955937689622)
- [ ] Envisager bot Thérèse sur Sonnet 4.5 au lieu d'Opus (économie ~80% réponses)
- [ ] Envisager sous-agents Zézette sur Sonnet 4.5 (recherche + challenger)
- [ ] Configurer heartbeat bot Thérèse avec activeHours 07:00-23:00 Europe/Paris
- [ ] Réduire subagents.maxConcurrent de 8 à 2 (bug contention locks #4355)

---

## Tests de non-régression (OBLIGATOIRE)

Avant chaque release :
1. **Lancer les tests de non-régression** : `uv run pytest tests/test_regression.py -v`
2. **Lancer tous les tests backend** : `uv run pytest tests/ --ignore=tests/e2e -q --timeout=30`
3. Si un test de régression échoue, **NE PAS publier** la release tant que le test n'est pas corrigé ou le fix confirmé
4. Quand un nouveau bug est corrigé, **ajouter un test dans `tests/test_regression.py`** avec la convention `TestBUGXXX_description`

Fichier de tests : `tests/test_regression.py`
- Couvre BUG-002 (port dynamique) à BUG-040 (DOCX page blanche) + XSS
- Chaque test vérifie que le fix est toujours présent dans le code source
- Un test qui passe = le fix n'a pas régressé

**Règle : chaque fix critique = un test de régression. Pas de fix sans test.**

---

## Fichiers de référence

- Kit alpha : `~/Desktop/ALPHA-THERESE/`
  - `discord/` : charte, message bienvenue, missions (S1-S6)
  - `documents/` : guides (installation, clé API Mistral, Ollama), FAQ, charte testeur, rapport audit
  - `presentations/` : 01-Bienvenue, 02-Guide-Lancement, 03-Missions-Hebdo
  - `suivi/` : Planning-Missions.xlsx, Suivi-Testeurs.xlsx
- Landing page alpha : `/tmp/synoptia-seo/site/therese/alpha/index.html` (deploy VPS `/var/www/synoptia.fr/therese/alpha/`)
- Rapport audit : `~/Desktop/Rapport-Audit-Alpha-THERESE-2026-02-08.docx`
