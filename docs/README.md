# THÉRÈSE V2

> **L'assistante souveraine des entrepreneurs français**

**"Ta mémoire, tes données, ton business."**

---

## Présentation

THÉRÈSE est une application desktop intelligente conçue pour les **solopreneurs et TPE français**. Alternative souveraine à [Cowork d'Anthropic](https://www.anthropic.com), elle combine la puissance des grands modèles de langage avec une **mémoire persistante** et une **souveraineté totale des données**.

Contrairement à Cowork - qui repart de zéro à chaque session - THÉRÈSE se souvient de vos clients, de vos projets, de vos préférences. Toutes vos données restent sur votre machine, chiffrées et sous votre contrôle.

### Pourquoi THÉRÈSE ?

- **Mémoire persistante** - Le point faible de Cowork. THÉRÈSE connaît vos clients, projets et préférences entre les sessions
- **100% souveraineté des données** - Stockage local (SQLite + Qdrant), aucune donnée envoyée à un tiers (sauf les requêtes LLM)
- **Multi-providers LLM** - 6 fournisseurs supportés (Anthropic, OpenAI, Google Gemini, Mistral, Grok, Ollama)
- **Interface premium dark mode** - Design soigné, glassmorphism, animations fluides
- **Pensée pour le marché français** - Guided prompts adaptés aux solopreneurs et TPE

---

## Points forts vs Cowork

| Critère | THÉRÈSE V2 | Cowork (Anthropic) |
|---------|------------|-------------------|
| **Mémoire persistante** | Oui - contacts, projets, fichiers indexés | Non - chaque session repart de zéro |
| **Multi-providers LLM** | 6 providers (Claude, GPT, Gemini, Mistral, Grok, Ollama) | Claude uniquement |
| **Données** | 100% local, chiffrement Fernet + Trousseau macOS | Cloud Anthropic |
| **Interface** | Dark mode premium, animations Framer Motion, guided prompts | Interface standard |
| **Sécurité** | Chiffrement AES-128-CBC, détection injection prompt, sandbox code | Vulnérabilité prompt injection connue (PromptArmor) |
| **Plateforme** | macOS (Windows/Linux prévu) | macOS uniquement |
| **Prix** | Gratuit (vos propres clés API) | 20-200 $/mois |
| **Conformité RGPD** | Oui - export, suppression, audit | Non garanti |
| **Mode offline** | Oui (via Ollama) | Non |
| **Skills Office** | DOCX, PPTX, XLSX via sandbox code-execution | Non |

---

## Stack technique

### Frontend

| Technologie | Version | Rôle |
|-------------|---------|------|
| **Tauri** | 2.0 | Shell desktop (Rust + WebView) |
| **React** | 19 | Interface utilisateur |
| **TypeScript** | 5+ | Typage statique |
| **TailwindCSS** | 4 | Stylisation utility-first |
| **Framer Motion** | 11 | Animations et transitions |
| **Zustand** | 5 | Gestion d'état |
| **Lucide** | - | Icônes |

### Backend

| Technologie | Version | Rôle |
|-------------|---------|------|
| **Python** | 3.11+ | Langage backend |
| **FastAPI** | 0.109+ | Framework API |
| **UV** | - | Gestionnaire de paquets Python |
| **SQLModel** | 0.0.22+ | ORM (SQLAlchemy + Pydantic) |
| **SQLite** | - | Base de données structurée |
| **Qdrant** | 1.7+ | Base de données vectorielle |
| **sentence-transformers** | 2.3+ | Embeddings (nomic-embed-text v1.5) |
| **Alembic** | 1.13+ | Migrations de base de données |

### Providers LLM

| Provider | Modèles disponibles | Notes |
|----------|---------------------|-------|
| **Anthropic** | claude-opus-4-5, claude-sonnet-4-5, claude-haiku-4-5 | Recommandé |
| **OpenAI** | gpt-4o, gpt-4-turbo, o3, o4-mini | GPT Image 1.5 pour les images |
| **Google Gemini** | gemini-3-pro-preview, gemini-3-flash-preview, gemini-2.5-pro | Google Search Grounding natif |
| **Mistral** | mistral-large-latest, codestral-latest, mistral-small-latest | IA française |
| **Grok (xAI)** | grok-3, grok-3-fast | API compatible OpenAI |
| **Ollama** | Dynamique (modèles locaux) | 100% offline |

---

## Architecture

```
+---------------------------------------------------------------------------+
|                         THÉRÈSE Desktop App                               |
+-------------------------------------+-------------------------------------+
|                                     |                                     |
|   +-----------------------------+   |   +-----------------------------+   |
|   |    Tauri 2.0 (Rust Shell)   |   |   |   React 19 Frontend        |   |
|   |                             |   |   |                             |   |
|   |  - Accès fichiers natif     |<->|   |  - Chat UI + Streaming      |   |
|   |  - Fenêtres indépendantes   |   |   |  - Panneau Mémoire          |   |
|   |  - Raccourcis globaux       |   |   |  - Navigateur fichiers      |   |
|   |  - Drag region macOS        |   |   |  - Board de décision        |   |
|   |  - WebviewWindow panels     |   |   |  - Palette de commandes     |   |
|   +-----------------------------+   |   |  - Guided Prompts           |   |
|                                     |   |  - Onboarding Wizard        |   |
|                                     |   +-----------------------------+   |
|                                     |                                     |
+-------------------------------------+-------------------------------------+
                                      |
                              HTTP + SSE (localhost:8000)
                                      |
+-------------------------------------v-------------------------------------+
|                      Python FastAPI Backend (Sidecar)                     |
|                                                                           |
|   +----------------+  +----------------+  +-------------------+           |
|   |   Services     |  |   Routers      |  |   Providers LLM   |          |
|   |                |  |                |  |                   |           |
|   |  - Chat        |  |  /api/chat     |  |  - Anthropic      |          |
|   |  - Mémoire     |  |  /api/memory   |  |  - OpenAI         |          |
|   |  - Fichiers    |  |  /api/files    |  |  - Gemini         |          |
|   |  - Skills      |  |  /api/skills   |  |  - Mistral        |          |
|   |  - Board       |  |  /api/board    |  |  - Grok           |          |
|   |  - Images      |  |  /api/images   |  |  - Ollama         |          |
|   |  - MCP         |  |  /api/mcp      |  +-------------------+          |
|   |  - Email       |  |  /api/email    |                                  |
|   |  - Calendrier  |  |  /api/calendar |  +-------------------+          |
|   |  - Tâches      |  |  /api/tasks    |  |   Stockage local  |          |
|   |  - Factures    |  |  /api/invoices |  |                   |          |
|   |  - CRM         |  |  /api/crm      |  |  - SQLite         |          |
|   |  - Calculs     |  |  /api/calc     |  |  - Qdrant         |          |
|   |  - Sécurité    |  |  /api/config   |  |  - ~/.therese/    |          |
|   +----------------+  +----------------+  +-------------------+          |
+---------------------------------------------------------------------------+
```

---

## Fonctionnalités

### Chat intelligent

- **Streaming SSE** - Réponses en temps réel via Server-Sent Events
- **Tool Calling** - Le LLM peut appeler automatiquement des outils MCP et internes
- **Commandes slash** - `/fichier [chemin]` pour inclure un fichier, `/analyse [chemin]` pour une analyse détaillée
- **Conversations persistées** - Historique SQLite avec groupement par date
- **Conversations éphémères** - Mode temporaire sans persistance
- **Rendu Markdown** - Coloration syntaxique, tableaux, listes
- **Annulation** - Possibilité d'interrompre une génération en cours

### Mémoire persistante

- **Contacts** - CRUD complet (nom, email, entreprise, téléphone, notes, tags)
- **Projets** - CRUD complet (nom, description, statut, budget, contact lié, tags)
- **Recherche hybride** - BM25 (mots-clés) + recherche sémantique (Qdrant, nomic-embed-text 768 dims)
- **Injection de contexte automatique** - THÉRÈSE enrichit chaque requête avec le contexte pertinent
- **Scope** - Mémoire globale, par projet, ou par conversation
- **Extraction automatique d'entités** - Détection de contacts et projets dans les messages avec suggestion de sauvegarde
- **Oubli sélectif** - Suppression en cascade avec confirmation

### Skills Office (génération de documents)

- **Document Word (.docx)** - Via python-docx avec styles Synoptïa
- **Présentation PowerPoint (.pptx)** - Via python-pptx (format 16:9, dark theme)
- **Tableur Excel (.xlsx)** - Via openpyxl avec formules, multi-onglets, graphiques
- **Architecture code-execution** - Le LLM génère du code Python exécuté dans une sandbox sécurisée
- **Fallback legacy** - Si le LLM ne génère pas de code, le parseur Markdown/JSON prend le relais

### Board de décision stratégique

- **5 conseillers IA** - L'Analyste, Le Stratège, L'Avocat du Diable, Le Pragmatique, Le Visionnaire
- **Multi-LLM par conseiller** - Chaque conseiller utilise un provider différent (Claude, GPT, Gemini, Mistral)
- **Synthèse automatique** - Consensus, divergences, recommandation finale, niveau de confiance
- **Historique** - Décisions sauvegardées en SQLite, consultables à tout moment
- **Raccourci** - Cmd+D pour ouvrir le board

### Génération d'images

- **GPT Image 1.5** (OpenAI) - Résolutions 1024x1024, 1536x1024, 1024x1536
- **Nano Banana Pro** (Gemini) - Résolutions 1K, 2K, 4K
- **Clés API séparées** - Clés dédiées pour la génération d'images (indépendantes des clés LLM)
- **Téléchargement et prévisualisation**

### Saisie vocale

- **Groq Whisper** - Transcription via whisper-large-v3-turbo
- **Prompt optimisé pour le français**
- **Intégration dans la zone de saisie** - Bouton micro avec animation pulse

### Intégration MCP (Model Context Protocol)

- **19 presets organisés en 8 catégories** - Essentiels, Productivité, Recherche, Marketing, CRM, Finance, Communication, Avancé
- **Transport stdio** - Communication JSON-RPC avec les serveurs MCP
- **Auto-discovery des tools** - Détection automatique des outils disponibles
- **Tool Calling LLM intégré** - Le LLM peut utiliser les outils MCP pendant la conversation
- **Chaînages de tools** - Jusqu'à 5 itérations consécutives
- **Chiffrement des clés API MCP** - Fernet AES-128-CBC + Trousseau macOS
- **UI dédiée** - Onglet Tools dans les paramètres avec recherche, catégories, badges

### Email

- **Gmail OAuth** - Connexion sécurisée via OAuth 2.0
- **IMAP/SMTP** - Support local-first pour d'autres fournisseurs
- **Classification intelligente** - Tri automatique des emails
- **Génération de réponses** - Assistance à la rédaction

### Calendrier

- **Google Calendar** - Synchronisation via API Google
- **CalDAV** - Support local-first pour calendriers standards
- **Vue mensuelle/hebdomadaire** - Navigation et gestion d'événements

### Gestion de tâches

- **CRUD complet** - Création, édition, complétion, suppression
- **Intégration chat** - Les tâches peuvent être créées depuis la conversation

### Facturation

- **Génération PDF** - Factures professionnelles via ReportLab
- **Gestion clients** - Lié aux contacts en mémoire

### CRM (sync Google Sheets)

- **Synchronisation bidirectionnelle** - Google Sheets comme source de vérité
- **Clients, Projets, Livrables** - Trois entités synchronisées
- **OAuth Google Sheets** - Authentification sécurisée
- **Import direct** - Via endpoint API pour bypass OAuth

### Calculateurs financiers

| Calculateur | Description |
|-------------|-------------|
| **ROI** | Return on Investment (retour sur investissement) |
| **ICE** | Impact x Confidence x Ease (priorisation) |
| **RICE** | (Reach x Impact x Confidence) / Effort (priorisation produit) |
| **VAN (NPV)** | Valeur Actuelle Nette (investissement) |
| **Seuil de rentabilité** | Break-even point |

### Recherche web

- **Gemini** - Google Search Grounding natif (threshold 0.3)
- **Autres LLMs** - Tool DuckDuckGo (gratuit, sans clé API)
- **Toggle on/off** dans les paramètres

### Conformité RGPD

- **Export complet** - Droit de portabilité (JSON)
- **Suppression totale** - Droit à l'effacement
- **Sanitization** - Aucun secret dans les exports
- **Backup automatique quotidien** - Sauvegarde et restauration

### Accessibilité WCAG 2.1 AA

- **Contraste** - 7:1 sur le texte principal
- **Navigation clavier** - Complète avec focus visible
- **Screen reader** - ARIA labels, rôles, modals accessibles
- **Reduced motion** - Respect de `prefers-reduced-motion`

### Palette de commandes (Cmd+K)

- **Recherche globale** - Actions, contacts, projets, fichiers, paramètres
- **Actions rapides** - Nouvelle conversation, toggle mémoire, paramètres

---

## Installation

### Prérequis

- **Node.js** 20+
- **Python** 3.11+ (via [UV](https://github.com/astral-sh/uv))
- **Rust** (pour Tauri 2.0) - [rustup.rs](https://rustup.rs)
- **Qdrant** (base de données vectorielle) - `docker run -p 6333:6333 qdrant/qdrant`

### Installation backend

```bash
# Cloner le projet
git clone https://github.com/ludovicsanchez38-creator/therese-v2.git
cd therese-v2

# Installer les dépendances Python
uv sync

# Appliquer les migrations
cd src/backend
uv run alembic upgrade head
```

### Installation frontend

```bash
# Installer les dépendances Node.js
cd src/frontend
npm install
```

### Lancement en développement

```bash
# Méthode 1 : Makefile (recommandé)
make dev

# Méthode 2 : Manuel (2 terminaux)

# Terminal 1 - Backend
cd src/backend
uv run uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend Tauri
cd src/frontend
npm run tauri dev
```

### Build de production

```bash
make build
```

### URLs de développement

| Service | URL |
|---------|-----|
| Frontend Tauri | http://localhost:1420 |
| Backend API | http://localhost:8000 |
| Documentation API | http://localhost:8000/docs |

---

## Structure du projet

```
therese-v2/
|
|-- docs/                           # Documentation projet
|   |-- architecture.md             # Architecture technique
|   |-- prd-therese.md              # Product Requirements Document
|   |-- benchmark-cowork.md         # Analyse comparative Cowork
|   |-- benchmark-memoire.md        # Benchmark mémoire IA
|   |-- benchmark-ux.md             # Benchmark UX/UI
|   |-- epics/                      # Epics BMAD
|   |-- stories/                    # User stories
|   +-- planning/                   # Sprint planning
|
|-- src/
|   |-- frontend/                   # Application Tauri + React
|   |   |-- src/
|   |   |   |-- components/
|   |   |   |   |-- chat/           # ChatLayout, MessageBubble, ChatInput, etc.
|   |   |   |   |-- memory/         # MemoryPanel, ContactModal, ProjectModal
|   |   |   |   |-- board/          # BoardPanel, AdvisorCard, SynthesisCard
|   |   |   |   |-- guided/         # GuidedPrompts, ActionCard, SubOptionsPanel
|   |   |   |   |-- onboarding/     # OnboardingWizard (6 étapes)
|   |   |   |   |-- settings/       # SettingsModal, ToolsPanel, CRMSyncPanel
|   |   |   |   |-- sidebar/        # ConversationSidebar
|   |   |   |   |-- email/          # EmailPanel
|   |   |   |   |-- calendar/       # CalendarPanel
|   |   |   |   |-- tasks/          # TasksPanel
|   |   |   |   |-- invoices/       # InvoicesPanel
|   |   |   |   |-- crm/            # CRMPanel
|   |   |   |   |-- files/          # FileBrowser, DropZone, FileChip
|   |   |   |   |-- panels/         # PanelWindow (fenêtres indépendantes)
|   |   |   |   +-- ui/             # SideToggle, TypingIndicator, etc.
|   |   |   |-- services/
|   |   |   |   +-- api/            # Modules API (chat, memory, config, etc.)
|   |   |   |-- stores/             # Zustand stores (chat, email, calendar, etc.)
|   |   |   +-- hooks/              # useKeyboardShortcuts, useVoiceRecorder, etc.
|   |   +-- src-tauri/              # Configuration Tauri (Rust)
|   |
|   +-- backend/                    # API Python FastAPI
|       +-- app/
|           |-- main.py             # Point d'entrée FastAPI
|           |-- config.py           # Configuration application
|           |-- models/             # SQLModel entities + Pydantic schemas
|           |-- routers/            # 24 routers API
|           |   |-- chat.py         # Chat + streaming SSE
|           |   |-- memory.py       # Contacts/Projets CRUD
|           |   |-- board.py        # Board de décision
|           |   |-- skills.py       # Génération documents Office
|           |   |-- images.py       # Génération images
|           |   |-- mcp.py          # Serveurs MCP
|           |   |-- email.py        # Email Gmail/IMAP
|           |   |-- calendar.py     # Calendrier Google/CalDAV
|           |   |-- tasks.py        # Gestion tâches
|           |   |-- invoices.py     # Facturation PDF
|           |   |-- crm.py          # CRM sync Google Sheets
|           |   |-- calculators.py  # Calculateurs financiers
|           |   +-- ...             # config, data, files, voice, etc.
|           +-- services/           # Logique métier
|               |-- providers/      # Providers LLM (anthropic, openai, gemini, etc.)
|               |-- skills/         # Générateurs Office (docx, pptx, xlsx)
|               |-- encryption.py   # Chiffrement Fernet + Trousseau macOS
|               |-- mcp_service.py  # Gestion serveurs MCP
|               |-- qdrant.py       # Base vectorielle
|               |-- embeddings.py   # Embeddings nomic-embed-text
|               +-- ...             # 40+ modules de services
|
|-- tests/                          # Suite de tests
|   |-- test_routers_*.py           # Tests unitaires routers (17 fichiers)
|   |-- test_services_*.py          # Tests unitaires services (5 fichiers)
|   +-- e2e/                        # Tests end-to-end Playwright
|       |-- test_onboarding.py      # 5 tests wizard
|       |-- test_chat.py            # 7 tests chat/messages
|       +-- test_guided_prompts.py  # 6 tests navigation
|
|-- Makefile                        # Commandes projet (dev, test, build, etc.)
|-- pyproject.toml                  # Configuration Python (UV, pytest, ruff)
+-- package.json                    # Configuration Node.js
```

---

## Raccourcis clavier

### Navigation globale

| Raccourci | Action |
|-----------|--------|
| `Cmd+K` | Palette de commandes |
| `Cmd+N` | Nouvelle conversation |
| `Cmd+B` | Toggle sidebar conversations |
| `Cmd+M` | Toggle panneau mémoire |
| `Cmd+D` | Ouvrir le Board de décision |
| `Cmd+,` | Paramètres |
| `Cmd+/` | Afficher les raccourcis |

### Chat

| Raccourci | Action |
|-----------|--------|
| `Entrée` | Envoyer le message |
| `Shift+Entrée` | Nouvelle ligne |
| `Escape` | Annuler la génération |

### Mémoire

| Raccourci | Action |
|-----------|--------|
| `Cmd+Shift+C` | Nouveau contact |
| `Cmd+Shift+P` | Nouveau projet |

### Fenêtres indépendantes

| Raccourci | Action |
|-----------|--------|
| `Cmd+E` | Ouvrir le panneau Email |
| `Cmd+L` | Ouvrir le panneau Calendrier |
| `Cmd+T` | Ouvrir le panneau Tâches |
| `Cmd+I` | Ouvrir le panneau Factures |
| `Cmd+R` | Ouvrir le panneau CRM |

---

## Sécurité

### Chiffrement des données

- **Fernet (AES-128-CBC + HMAC-SHA256)** - Chiffrement de toutes les clés API et secrets
- **Trousseau macOS (Keychain)** - La clé de chiffrement est stockée dans le trousseau système via `keyring`
- **Migration automatique** - Passage fichier vers Keychain sans perte de données
- **Fallback** - Si le Keychain est indisponible, stockage fichier avec permissions restrictives

### Authentification

- **Token de session éphémère** - Généré à chaque démarrage, invalidé à la fermeture
- **Middleware d'authentification** - Toutes les routes API protégées (sauf health et options CORS)

### Protection réseau

- **Rate limiting** - 60 requêtes par minute via SlowAPI
- **Headers de sécurité** - CSP, X-Frame-Options, X-Content-Type-Options
- **CORS configuré** - Origines autorisées uniquement

### Protection contre les injections

- **Détection d'injection de prompt** - Patterns OWASP LLM Top 10
- **Niveaux de menace** - NONE, LOW, MEDIUM, HIGH, CRITICAL
- **Blocage automatique** - Les requêtes HIGH et CRITICAL sont rejetées

### Sandbox d'exécution de code

- **Imports restreints** - Whitelist par format (openpyxl, python-docx, python-pptx)
- **Builtins limités** - Pas de `getattr`, `setattr`, `eval`, `exec`, `compile`
- **Patterns bloqués** - os, sys, subprocess, shutil, socket, requests, urllib
- **Timeout** - 30 secondes maximum via `asyncio.wait_for`

---

## Tests

### Backend (pytest)

```bash
# Tous les tests backend
make test-backend

# Tests spécifiques
uv run pytest tests/test_routers_chat.py -v
uv run pytest tests/test_services_llm.py -v
```

**118+ tests unitaires** répartis en :
- 17 fichiers de tests routers (chat, memory, board, skills, images, mcp, email, calendar, tasks, invoices, crm, etc.)
- 5 fichiers de tests services (encryption, llm, mcp, oauth, web_search)

### Tests E2E (Playwright)

```bash
# Installation
make install-e2e

# Tests headless (CI)
make test-e2e

# Tests avec navigateur visible (debug)
make test-e2e-headed
```

**18 tests end-to-end** :
- `test_onboarding.py` - 5 tests (wizard 6 étapes, validation, navigation)
- `test_chat.py` - 7 tests (envoi/réception, streaming, raccourcis, persistance)
- `test_guided_prompts.py` - 6 tests (navigation actions, sous-options, animations)

### Frontend (Vitest)

```bash
# Tests frontend
make test-frontend
# ou
cd src/frontend && npm test
```

**32 tests** : chatStore (15) + utilitaires (17)

---

## Commandes Makefile

| Commande | Description |
|----------|-------------|
| `make dev` | Lancer backend + frontend Tauri |
| `make dev-backend` | Lancer le backend seul |
| `make dev-frontend` | Lancer le frontend seul (Vite) |
| `make tauri` | Lancer Tauri uniquement |
| `make install` | Installer toutes les dépendances |
| `make install-e2e` | Installer dépendances E2E (Playwright) |
| `make db-migrate` | Appliquer les migrations Alembic |
| `make test` | Lancer tous les tests |
| `make test-backend` | Tests backend uniquement |
| `make test-frontend` | Tests frontend uniquement |
| `make test-e2e` | Tests E2E headless |
| `make test-e2e-headed` | Tests E2E avec navigateur visible |
| `make lint` | Vérifier le code (ruff + eslint) |
| `make lint-fix` | Corriger le code automatiquement |
| `make typecheck` | Vérification TypeScript |
| `make build` | Build de production (Tauri .app) |
| `make clean` | Nettoyer les fichiers générés |
| `make clean-all` | Nettoyage complet (node_modules, venv) |
| `make reset-sandbox` | Reset environnement test E2E |
| `make reset-onboarding` | Reset wizard onboarding |

---

## Identité visuelle

```yaml
palette:
  background: "#0B1226"       # Fond principal (bleu très sombre)
  surface: "#131B35"           # Surfaces (cartes, panels)
  text_primary: "#E6EDF7"      # Texte principal (blanc cassé)
  text_muted: "#B6C7DA"        # Texte secondaire (gris-bleu)
  accent_cyan: "#22D3EE"       # Accent principal (cyan lumineux)
  accent_magenta: "#E11D8D"    # Accent secondaire (magenta)

style:
  thème: Dark premium
  effets:
    - Glassmorphism subtil (backdrop-blur-xl bg-white/5)
    - Glow néon discret (shadow cyan 0.15)
    - Bordures transparentes (border-white/10)
  coins: Arrondis (8-12px)
  typographie:
    sans: "Inter, system-ui"
    mono: "JetBrains Mono"
  animations:
    bibliothèque: Framer Motion 11
    spring: "500ms, damping 30"
    easing: "[0.4, 0, 0.2, 1]"
```

---

## Guided Prompts

L'écran d'accueil propose 3 actions principales avec 24 sous-options :

| Action | Icône | Sous-options |
|--------|-------|-------------|
| **Produire** | Sparkles | Email pro, Post LinkedIn, Proposition commerciale, Document Word, Présentation PPT, Tableur Excel, Image IA GPT, Image IA Gemini |
| **Comprendre** | Brain | Fichier Excel, Document PDF, Site web, Marché, Outil IA, Concept, Best practices |
| **Organiser** | GitBranch | Réunion, Projet, Semaine, Objectifs, Workflow n8n, Apps Script, Make, Zapier, Processus |

---

## Presets MCP (19 connecteurs)

| Catégorie | Presets |
|-----------|--------|
| **Essentiels** | Filesystem, Fetch, Time |
| **Productivité** | Google Workspace, Notion, Airtable, Todoist, Trello |
| **Recherche** | Brave Search, Perplexity |
| **Marketing** | Brevo |
| **CRM et Ventes** | HubSpot CRM, Pipedrive |
| **Finance** | Stripe |
| **Communication** | WhatsApp Business |
| **Avancé** | Sequential Thinking, Slack, Playwright |

---

## Historique des versions

| Version | Date | Description |
|---------|------|-------------|
| v1.0 | 21/01/2026 | MVP Chat - Chat, mémoire, fichiers, dark mode |
| v1.1 | 21/01/2026 | Guided Prompts (3 actions x 24 options) |
| v1.2 | 22/01/2026 | Multi-Provider LLM (6 providers) |
| v1.3 | 22/01/2026 | Skills Office (DOCX, PPTX, XLSX) |
| v1.4 | 22/01/2026 | Side Toggles latéraux |
| v1.5 | 22/01/2026 | Saisie vocale (Groq Whisper) |
| v1.6 | 22/01/2026 | Génération d'images (GPT Image + Gemini) |
| v1.7 | 23/01/2026 | Extraction automatique d'entités |
| v1.8 | 23/01/2026 | Onboarding Wizard (5 étapes) |
| v1.9 | 23/01/2026 | Polish Onboarding (accessibilité) |
| v2.0 | 24/01/2026 | Board de décision stratégique |
| v2.1 | 24/01/2026 | Calculateurs financiers (ROI, ICE, RICE, VAN) |
| v2.2 | 24/01/2026 | Provider Grok + corrections UX |
| v2.3 | 24/01/2026 | Intégration MCP (8 presets) |
| v2.4 | 24/01/2026 | Tool Calling LLM intégré |
| v2.5 | 24/01/2026 | Corrections UX |
| v2.6 | 24/01/2026 | Clés API images séparées |
| v2.7 | 24/01/2026 | Recherche web intégrée |
| v2.8 | 24/01/2026 | 30 User Stories Qualité (erreurs, backup, sécurité, perf) |
| v2.9 | 26/01/2026 | Tests E2E + Sécurité Onboarding |
| v3.0 | 27/01/2026 | MCP Enrichment (chiffrement, 13 presets) |
| v3.1 | 28/01/2026 | CRM Sync Google Sheets |
| v3.2 | 29/01/2026 | Sprint Architecture + Performance (refactoring) |
| v3.3 | 30/01/2026 | Fenêtres indépendantes pour panels |
| v3.4 | 30/01/2026 | Persistance Email/Calendrier |
| v3.5 | 02/02/2026 | 19 presets MCP organisés par catégories |
| v3.6 | 02/02/2026 | Skills Office v2 code-execution (sandbox) |

---

## Auteur

**Synoptïa** - [synoptia.fr](https://synoptia.fr)

Créé par **Ludovic Sanchez** - ludo@synoptia.fr

*"Humain d'abord - IA en soutien."*

---

*Projet initié le 21 janvier 2026 - Dernière mise à jour : 3 février 2026*
