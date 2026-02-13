# Changelog - THÉRÈSE V2

Toutes les versions notables du projet sont documentées ici.
Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).

> Pour le journal de développement détaillé, voir [DEVLOG.md](./DEVLOG.md).

---

## [v0.1.12-alpha] - 13 février 2026 - Splash timeout + tests non-régression

### Fixed
- **Splash "backend ne répond pas" au premier lancement** : timeout du SplashScreen passé de 60s à 120s. Le premier lancement extrait PyInstaller + télécharge le modèle d'embeddings (~250 Mo), ce qui peut dépasser 60s sur certaines machines.

### Added
- **Tests de non-régression** (`tests/test_regression.py`) : 19 tests couvrant tous les bugs critiques (BUG-002 à BUG-013 + XSS). Chaque fix a désormais un test dédié qui empêche la régression.
- Tests encryption adaptés au lazy init (v0.1.11)

---

## [v0.1.11-alpha] - 13 février 2026 - Fix crash Mac M4 Max + Keychain UX

### Fixed
- **BUG-012 Crash silencieux Mac M4 Max** : forcer `device='cpu'` pour sentence-transformers. PyTorch détectait automatiquement MPS (Metal Performance Shaders) et crashait silencieusement sur certains Mac Apple Silicon (M4 Max). Les embeddings texte sont aussi rapides en CPU.
- **Keychain bloque le démarrage 20+ secondes** : l'init du service de chiffrement est maintenant lazy (au premier encrypt/decrypt, pas au boot). Le health endpoint répond en ~4s au lieu de ~26s. Le prompt Trousseau macOS n'apparaît que quand l'utilisateur a besoin d'une clé API.

---

## [v0.1.10-alpha] - 12 février 2026 - Fix port IPC Mac M1

### Fixed
- **BUG-011 "Backend ne répond pas" sur Mac M1** : `initApiBase()` retry jusqu'à 10 fois (300ms entre chaque) si l'IPC Tauri échoue ou retourne le port par défaut. Le bridge IPC n'était pas prêt au chargement du WebView sur certains Mac, causant un fallback sur port 8000 alors que le backend tournait sur un port dynamique.
- Version backend/frontend synchronisées à 0.1.10

---

## [v0.1.9-alpha] - 12 février 2026 - Fix CRM Sync + Keychain startup

### Fixed
- **CRM Google Sheets 401** : ajout du refresh automatique du token OAuth avant chaque sync (le refresh token était stocké mais jamais utilisé)
- **Keychain au démarrage** : le chargement du profil utilisateur ne déclenche plus de prompt trousseau macOS au boot (`allow_decrypt=False` au preload)
- **Bouton Reconnecter** : le bouton "Connecter Google Sheets" est désormais toujours visible (renommé "Reconnecter" quand un token existe), même si le token est expiré

### Changed
- Le callback OAuth CRM stocke maintenant les `client_id`/`client_secret` pour permettre le refresh automatique
- `set_crm_tokens()` accepte les credentials client en paramètres optionnels
- `ensure_valid_crm_token()` : nouvelle fonction qui refresh le token via refresh_token + credentials (EmailAccount Gmail ou stockés)

### Added
- Tests startup keychain safety (`test_main_startup.py`)

---

## [v0.1.8-alpha] - 12 février 2026 - Fix torch excludes PyInstaller

### Fixed
- **BUG-010 torch excludes** : retrait de tous les excludes torch du bundle PyInstaller (`torch.cuda`, `torch.distributed`, `torch.testing`, `torch.utils.tensorboard`). torch les importe à l'init et crash si ils manquent.
- torch CPU-only skip sur macOS (PyPI torch macOS est déjà CPU-only)

---

## [v0.1.7-alpha] - 12 février 2026 - CASSÉE

> Version cassée - le sidecar crash au démarrage sur toutes les plateformes (torch excludes ajoutés par erreur dans l'audit). Utiliser v0.1.8+.

---

## [v3.7] - 3 février 2026 - Skills Multi-Modèle + Fix Opus

### Added
- Détection capacité modèle (`model_capability.py`) : code vs markdown selon provider/modèle
- Prompt adaptatif par generator (DOCX, PPTX, XLSX) pour modèles markdown-only
- Extraction de titres améliorée avec 24 préfixes FR/EN

### Fixed
- Réponses tronquées Opus : `repair_truncated_code()` pour blocs Python incomplets
- `max_tokens=8192` pour skills FILE (était 4096, causait troncature)
- Imports autorisés élargis (time, random, copy, string, textwrap, itertools, collections)

## [v3.6] - 2 février 2026 - Skills Office v2 Code-Execution

### Changed
- Pipeline skills Office refait : LLM -> code Python -> sandbox -> fichier (au lieu de regex parser)
- `code_executor.py` : extraction, validation AST, sandbox sécurisée, timeout 30s
- `CodeGenSkill(BaseSkill)` : classe abstraite avec fallback automatique vers legacy parser
- Sandbox bloque os, sys, subprocess, socket, requests, eval, exec, compile

## [v3.5] - 2 février 2026 - MCP Connectors Brainstorm

### Added
- 10 nouveaux presets MCP (Brave Search, Brevo, Stripe, HubSpot, Todoist, Trello, Perplexity, Pipedrive, WhatsApp Business, Playwright)
- UI presets par catégories (8 sections), recherche, badges "Populaire"

### Removed
- 5 presets dev-only supprimés (git, linear, github, zapier, make)

## [v3.4] - 30 janvier 2026 - Persistance Email/Calendrier

### Fixed
- PanelWindow pré-charge les comptes email avant montage
- CalendarStore/EmailStore persistent les données entre fenêtres
- CalendarPanel utilise selectedDate au lieu de new Date()

## [v3.3] - 30 janvier 2026 - Fenêtres indépendantes

### Added
- 5 panels (Email, Calendrier, Tâches, Factures, CRM) s'ouvrent en fenêtres macOS séparées
- `windowManager.ts` : singleton WebviewWindow par panel
- `PanelWindow.tsx` : wrapper standalone avec auth + chargement données

## [v3.2] - 29 janvier 2026 - Sprint 2 Architecture + Performance

### Changed
- Découpage `api.ts` en 14 modules (`src/frontend/src/services/api/`)
- Découpage `llm.py` (1558 -> 417 lignes) en 6 providers séparés
- Pool global `httpx.AsyncClient` (20 keepalive, 100 max)

### Added
- Prompt injection mitigation (`prompt_security.py`) - OWASP LLM Top 10
- macOS Keychain pour clé de chiffrement via `keyring`
- 118 tests services passent

### Fixed
- CORS OPTIONS bloqué par auth middleware
- Race condition auth au démarrage (initializeAuth)
- Image download + health endpoint ajoutés aux exempt_paths

## [v3.1] - 28 janvier 2026 - CRM Sync Google Sheets

### Added
- Sync bidirectionnelle CRM depuis Google Sheets (Clients, Projects, Deliverables)
- 3 modes auth : OAuth Google Sheets, clé API Gemini (fallback), import direct JSON
- `CRMSyncPanel.tsx` dans Settings -> Données

## [v3.0] - 27 janvier 2026 - MCP Enrichment

### Added
- Chiffrement clés API MCP (Fernet AES-128-CBC + HMAC)
- 13 presets MCP (Tier 1/2/3)
- `EnvVarModal.tsx` : modal saisie clés API avec validation préfixe

## [v2.9] - 26 janvier 2026 - Security Onboarding + Tests E2E

### Added
- SecurityStep dans onboarding (6 étapes au lieu de 5)
- 18 tests E2E Playwright (onboarding, chat, guided prompts)
- Sandbox isolé `~/.therese-test-sandbox`
- Commandes Makefile : `make install-e2e`, `make test-e2e`, `make test-e2e-headed`

## [v2.8] - 24 janvier 2026 - 30 User Stories Qualité

### Added
- Gestion d'erreurs centralisée (messages FR, retry backoff, mode dégradé, annulation)
- Backup & export (conversations JSON/Markdown, export RGPD, backup quotidien)
- Chiffrement clés API Fernet
- Performance monitoring (first token latency, memory management, battery saver)
- Personnalisation (prompt templates, comportement LLM, feature visibility)
- Suivi consommation tokens + estimation coûts EUR
- 103 tests backend

## [v2.7] - 24 janvier 2026 - Recherche Web

### Added
- Gemini : Google Search Grounding natif
- Autres LLMs : tool DuckDuckGo (gratuit, sans API key)
- Toggle on/off dans Settings

## [v2.6] - 24 janvier 2026 - Clés API Images Séparées

### Added
- Clés API dédiées pour génération d'images (distinctes des clés LLM)

## [v2.5] - 24 janvier 2026 - Corrections UX

### Fixed
- FileBrowser charge le dossier configuré au démarrage
- Sidebar "Mémoire" renommée "Espace de travail"
- Messages d'erreur audio améliorés pour Tauri
- Indicateurs clés API images dans Settings

## [v2.4] - 24 janvier 2026 - MCP Tool Calling

### Added
- Tool calling LLM intégré (Claude + OpenAI function calling)
- Auto-discovery tools MCP dans le chat
- Chaînage de tools (max 5 itérations)
- Affichage statut exécution tools dans l'UI

## [v2.3] - 24 janvier 2026 - MCP

### Added
- Service MCP (start/stop/restart serveurs, transport stdio, JSON-RPC)
- Auto-discovery tools, presets prédéfinis
- API complète `/api/mcp/*`
- Onglet "Tools" dans SettingsModal

## [v2.2] - 24 janvier 2026 - Grok + UX

### Added
- Provider Grok (xAI) : grok-3, grok-3-fast, grok-2
- Conversations éphémères (non persistées)
- Bouton + désactivé si conversation vide

### Fixed
- GPT Image 1.5 : paramètre `response_format` retiré
- Clé Gemini : chargement depuis SQLite
- Modèle OpenAI par défaut corrigé

## [v2.1] - 24 janvier 2026 - Calculateurs Financiers

### Added
- 5 calculateurs : ROI, ICE, RICE, NPV, Break-even

## [v2.0] - 24 janvier 2026 - Board de Décision

### Added
- Board de 5 conseillers IA (Analyste, Stratège, Avocat du Diable, Pragmatique, Visionnaire)
- Multi-LLM par conseiller avec fallback automatique
- Synthèse automatique (consensus, divergences, recommandation, confiance)
- Historique SQLite des décisions
- Raccourci Cmd+D

## [v1.9] - 23 janvier 2026 - Onboarding Polish

### Fixed
- 12 user stories d'audit implémentées (UX, accessibilité, types nullable, validation clés API)
- Tous les accents français corrigés dans l'onboarding

## [v1.8] - 23 janvier 2026 - Onboarding Wizard

### Added
- Wizard 5 étapes au premier lancement (Bienvenue, Profil, LLM, Dossier, Terminé)
- Import profil depuis CLAUDE.md
- Check onboarding status au démarrage

## [v1.7] - 23 janvier 2026 - Entity Extraction

### Added
- Extraction automatique contacts/projets depuis les messages via LLM
- Event SSE `entities_detected` + UI suggestion sous les messages
- Seuil de confiance configurable (MIN_CONFIDENCE = 0.6)

## [v1.6] - 22 janvier 2026 - Image Generation

### Added
- GPT Image 1.5 (OpenAI) + Nano Banana Pro (Gemini)
- Génération simple + avec image de référence
- UI sélection provider image

## [v1.5] - 22 janvier 2026 - Voice Input

### Added
- Dictée vocale via Groq Whisper (whisper-large-v3-turbo)
- Bouton micro dans ChatInput avec animation pulse

## [v1.4] - 22 janvier 2026 - Side Toggles

### Added
- Rails latéraux pour ouvrir/fermer ConversationSidebar (gauche) et MemoryPanel (droite)
- Animation spring Framer Motion

## [v1.3] - 22 janvier 2026 - Skills Office

### Added
- Génération DOCX, PPTX, XLSX avec style Synoptïa
- `app/services/skills/` - Generators + registry
- UI `SkillExecutionPanel.tsx`

## [v1.2] - 21-22 janvier 2026 - Multi-Provider LLM

### Added
- Support 6 providers : Anthropic, OpenAI, Gemini, Mistral, Grok, Ollama
- Identité utilisateur (profil, import CLAUDE.md)
- Sélecteur dossier de travail

## [v1.1] - 21 janvier 2026 - Guided Prompts

### Added
- Interface guidée écran vide : 3 actions (Produire, Comprendre, Organiser) x 24 sous-options
- Module `src/frontend/src/components/guided/`

## [v1.0] - 21 janvier 2026 - MVP Chat

### Added
- Chat LLM avec streaming SSE
- Conversations persistées SQLite + sidebar groupée par date
- Mémoire : Contacts/Projets CRUD + embeddings Qdrant + recherche hybride BM25/sémantique
- Fichiers : Drag & Drop + indexation Qdrant
- Animations Framer Motion (messages, modals, sidebars, stagger)
- Tests Vitest (32 tests) + code splitting (-75% bundle)
- Frontend Tauri 2.0 + React + TailwindCSS
- Backend FastAPI + UV + Alembic
