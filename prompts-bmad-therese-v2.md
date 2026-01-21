# Prompts BMAD - THÉRÈSE v2

> Cowork souverain + mémoire persistante + UX premium
> 
> "Ta mémoire, tes données, ton business."

---

## Table des matières

1. [Prompt 0 : Setup initial (Claude Code)](#prompt-0--setup-initial-claude-code)
2. [Prompt 1 : Benchmark Cowork (Agent Analyst)](#prompt-1--benchmark-cowork-agent-analyst)
3. [Prompt 2 : Analyse mémoire et contexte (Agent Analyst)](#prompt-2--analyse-mémoire-et-contexte-agent-analyst)
4. [Prompt 3 : Benchmark UX/UI (Agent UX Designer)](#prompt-3--benchmark-uxui-agent-ux-designer)
5. [Prompt 4 : PRD THÉRÈSE (Agent PM)](#prompt-4--prd-thérèse-agent-pm)
6. [Prompt 5 : Architecture technique (Agent Architect)](#prompt-5--architecture-technique-agent-architect)
7. [Prompt 6 : Génération des Stories (Agent Scrum Master)](#prompt-6--génération-des-stories-agent-scrum-master)
8. [Récap et ordre d'exécution](#récap-et-ordre-dexécution)

---

## Prompt 0 : Setup initial (Claude Code)

```markdown
# MISSION: Initialiser le projet THÉRÈSE v2

## Contexte du projet

**THÉRÈSE** est une alternative souveraine à Cowork d'Anthropic.
- Créateur : Ludo Sanchez (Synoptïa)
- Positionnement : Cowork + mémoire persistante + meilleure UX/UI
- Cible : solopreneurs et TPE français
- Tagline : "Ta mémoire, tes données, ton business."

### Historique
- THÉRÈSE CLI v1 : prototype Mistral Large, post viral LinkedIn (140k impressions, 90k vues, 1050 likes)
- THÉRÈSE v2 : version desktop complète, projet actuel

### Différenciateurs vs Cowork
1. Mémoire persistante (Cowork n'en a pas)
2. UX/UI premium dark mode
3. Souveraineté des données (local first)
4. Pensé pour le marché français

## Ta mission

### 1. Créer la structure du projet

therese-v2/
├── .bmad-core/          # Config BMAD (généré par l'installateur)
├── docs/
│   ├── benchmark-cowork.md
│   ├── benchmark-memoire.md
│   ├── benchmark-ux.md
│   ├── prd-therese.md
│   ├── architecture.md
│   └── stories/
├── src/
│   ├── frontend/        # Tauri + React
│   ├── backend/         # Python FastAPI
│   ├── memory/          # Module mémoire (SQLite + Qdrant)
│   └── llm/             # Abstraction LLM (Claude API, puis local)
├── tests/
├── assets/
│   └── design/          # Maquettes, assets visuels
├── .gitignore
├── README.md
├── pyproject.toml       # Config Python (UV)
├── package.json         # Config Node (frontend)
└── Makefile             # Commandes dev

### 2. Initialiser Git

git init
git add .
git commit -m "feat: initialisation projet THÉRÈSE v2"

### 3. Installer BMAD

npx bmad-method@alpha install

Lors de l'installation, choisis :
- IDE : Claude Code
- Modules : BMM (BMad Method) + CIS (Creative Intelligence Suite)
- Team : fullstack

### 4. Créer le README.md

# THÉRÈSE v2

> L'assistante souveraine des entrepreneurs français

## Vision

THÉRÈSE = Cowork (Anthropic) + mémoire persistante + meilleure UX/UI + souveraineté des données.

## Statut

🚧 En développement (Phase: Discovery)

## Stack technique

- **Frontend**: Tauri + React + TailwindCSS
- **Backend**: Python (FastAPI) + UV
- **Database**: SQLite (données) + Qdrant (embeddings)
- **LLM**: Claude API (v1), puis Mistral/local (v2)

## Identité visuelle

| Élément | Valeur |
|---------|--------|
| Background | #0B1226 |
| Surface | #131B35 |
| Text | #E6EDF7 |
| Accent Cyan | #22D3EE |
| Accent Magenta | #E11D8D |

Style : Dark premium, glassmorphism subtil, glow néon discret.

## Développement

### Prérequis
- Node.js 20+
- Python 3.11+ (via UV)
- Rust (pour Tauri)

### Installation

# Backend
cd src/backend
uv sync

# Frontend
cd src/frontend
npm install

### Lancer le dev

make dev

## Méthodologie

Projet développé avec BMAD Method (Breakthrough Method for Agile AI-Driven Development).

## Auteur

Ludo Sanchez - [Synoptïa](https://synoptia.fr)

### 5. Créer le .gitignore

# Python
__pycache__/
*.py[cod]
.venv/
.uv/
*.egg-info/
dist/

# Node
node_modules/
.next/
.nuxt/

# Tauri
src-tauri/target/

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db

# Env
.env
.env.local
*.local

# BMAD
.bmad-core/cache/

# Data (ne pas commiter les données utilisateur)
data/
*.db
*.sqlite

### 6. Créer le Makefile

.PHONY: dev install test lint clean

# Développement
dev:
	@echo "🚀 Lancement THÉRÈSE en mode dev..."
	cd src/backend && uv run uvicorn main:app --reload &
	cd src/frontend && npm run dev

# Installation
install:
	@echo "📦 Installation des dépendances..."
	cd src/backend && uv sync
	cd src/frontend && npm install

# Tests
test:
	@echo "🧪 Lancement des tests..."
	cd src/backend && uv run pytest
	cd src/frontend && npm test

# Lint
lint:
	@echo "🔍 Vérification du code..."
	cd src/backend && uv run ruff check .
	cd src/frontend && npm run lint

# Clean
clean:
	@echo "🧹 Nettoyage..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name node_modules -exec rm -rf {} +
	find . -type d -name .venv -exec rm -rf {} +

### 7. Créer les fichiers placeholder dans docs/

Crée des fichiers vides avec un header pour chaque doc :

**docs/benchmark-cowork.md**

# Benchmark Cowork (Anthropic)

> Document généré par l'agent Analyst (BMAD)

## Statut
🔴 À rédiger

---

**docs/benchmark-memoire.md**

# Benchmark Mémoire - État de l'art

> Document généré par l'agent Analyst (BMAD)

## Statut
🔴 À rédiger

---

**docs/benchmark-ux.md**

# Benchmark UX/UI

> Document généré par l'agent UX Designer (BMAD)

## Statut
🔴 À rédiger

---

**docs/prd-therese.md**

# PRD - THÉRÈSE v2

> Document généré par l'agent PM (BMAD)

## Statut
🔴 À rédiger

---

**docs/architecture.md**

# Architecture Technique - THÉRÈSE v2

> Document généré par l'agent Architect (BMAD)

## Statut
🔴 À rédiger

---

### 8. Commit final

git add .
git commit -m "feat: structure projet + BMAD installé + docs placeholder"

## Output attendu
- Projet initialisé et fonctionnel
- BMAD installé et configuré
- Structure de dossiers créée
- README complet
- Prêt pour lancer les agents BMAD

## Vérification
Après setup, tu dois pouvoir lancer :

*workflow-init

Et BMAD doit reconnaître le projet.
```

---

## Prompt 1 : Benchmark Cowork (Agent Analyst)

```markdown
# MISSION: Benchmark exhaustif de Cowork (Anthropic)

## Contexte
Je développe THÉRÈSE, une alternative souveraine à Cowork d'Anthropic.
Positionnement : Cowork + mémoire persistante + meilleure UX/UI.
Cible : solopreneurs et TPE français.

## Ta mission

### 1. Recherche toutes les sources sur Cowork
- Documentation officielle Anthropic (docs.anthropic.com, support)
- Articles tech : The Verge, TechCrunch, Ars Technica, blogs IA
- Retours utilisateurs : Twitter/X, Reddit r/ClaudeAI, HackerNews
- Vidéos démo YouTube
- Posts LinkedIn de beta testeurs

### 2. Documente chaque fonctionnalité
Pour chaque feature, note :
| Champ | Description |
|-------|-------------|
| Nom | Nom de la fonctionnalité |
| Description | Ce que ça fait concrètement |
| Déclencheur | Comment l'utilisateur l'active |
| Output | Ce que l'utilisateur obtient |
| Limitation | Ce qui manque ou frustre |

### 3. Focus particulier sur
- Gestion des fichiers (quels formats, quelles actions)
- Automatisation desktop (quelles apps, quelles actions)
- Mémoire/contexte (comment ça marche, ce qui manque)
- Onboarding (premiers pas utilisateur)
- Permissions et sécurité

### 4. Identifie les GAPS
- Fonctionnalités absentes
- Frustrations utilisateurs récurrentes
- Cas d'usage non couverts
- Problèmes de confidentialité/souveraineté mentionnés

## Output attendu
Fichier `docs/benchmark-cowork.md` structuré :
1. Vue d'ensemble Cowork
2. Liste exhaustive des features (tableau)
3. Parcours utilisateur type
4. Forces à répliquer
5. Faiblesses à exploiter
6. Opportunités pour THÉRÈSE

## Contraintes
- Sources de moins de 3 mois en priorité
- Distinguer faits vs suppositions
- Citer les sources
```

---

## Prompt 2 : Analyse mémoire et contexte (Agent Analyst)

```markdown
# MISSION: Deep dive sur la mémoire dans les assistants IA

## Contexte
La mémoire persistante est LE différenciateur de THÉRÈSE vs Cowork.
Je dois comprendre l'état de l'art et les attentes utilisateurs.

## Ta mission

### 1. Benchmark des implémentations mémoire existantes

#### ChatGPT Memory
- Comment ça fonctionne techniquement
- Ce que les utilisateurs peuvent contrôler
- Limitations connues
- Retours utilisateurs (positifs et négatifs)

#### Claude Memory (claude.ai)
- Fonctionnement actuel
- Différences avec ChatGPT
- Ce qui manque

#### Autres outils avec mémoire
- Mem.ai
- Reflect Notes
- Notion AI
- Granola (meeting notes)
- Rewind AI

### 2. Identifie les patterns de mémoire utiles pour un solopreneur
- Mémoire des contacts/clients (CRM-like)
- Mémoire des projets en cours
- Mémoire des préférences utilisateur
- Mémoire des conversations passées
- Mémoire des fichiers/documents

### 3. Problèmes techniques à anticiper
- Stockage (local vs cloud)
- Recherche/retrieval (RAG, embeddings)
- Mise à jour (quand rafraîchir la mémoire)
- Oubli (comment supprimer, RGPD)
- Performance (latence acceptable)

## Output attendu
Fichier `docs/benchmark-memoire.md` :
1. Tableau comparatif des solutions existantes
2. Patterns de mémoire à implémenter (priorisés)
3. Architecture technique suggérée
4. Risques et mitigations
5. Spécifications fonctionnelles pour THÉRÈSE

## Stack technique de référence
- SQLite pour données structurées
- Qdrant pour embeddings/recherche sémantique
- LLM : Claude API (puis Mistral/local)
```

---

## Prompt 3 : Benchmark UX/UI (Agent UX Designer)

```markdown
# MISSION: Benchmark UX/UI pour THÉRÈSE

## Contexte
THÉRÈSE = Cowork souverain + mémoire + meilleure UX/UI.
On veut un effet "wahou" dès l'ouverture, pas une interface générique.

## Outils à analyser en priorité

### Assistants Desktop
- Cowork (Anthropic) - notre référence directe
- Raycast (macOS) - exemplaire en UX minimaliste
- Alfred (macOS) - efficacité brute
- Pieces for Developers - gestion contexte/snippets

### Apps avec excellente UX dark mode
- Linear (gestion projet)
- Warp (terminal)
- Arc Browser
- Figma (dark mode)
- Obsidian (thèmes dark)

### CRM/Productivité élégants
- Attio
- Folk CRM
- Notion
- Coda

## Ta mission

### 1. Pour chaque outil, capture
- Premier écran (onboarding/home)
- Navigation principale
- Comment ils affichent le contexte/mémoire
- Micro-interactions remarquables
- Gestion des raccourcis clavier
- Feedback visuel (loading, success, error)

### 2. Patterns gagnants à identifier
- Comment réduire le time-to-value (première action utile)
- Comment afficher beaucoup d'info sans surcharger
- Comment rendre la mémoire/contexte visible et utile
- Comment gérer le mode "chat" vs mode "action"
- Animations subtiles qui font premium

### 3. Anti-patterns à éviter
- Sidebars surchargées
- Trop de clics pour une action simple
- Onboarding interminable
- Mode sombre mal contrasté

## Output attendu
Fichier `docs/benchmark-ux.md` :
1. Galerie des meilleures interfaces (avec liens/screenshots)
2. Top 10 patterns à adopter pour THÉRÈSE
3. Top 5 anti-patterns à éviter
4. Wireframes suggérés (ASCII/texte ok) pour :
   - Écran principal
   - Panneau mémoire/contexte
   - Vue contacts/CRM
5. Recommandations animations/micro-interactions

## Contraintes design THÉRÈSE (identité Synoptïa)

palette:
  background: "#0B1226"
  surface: "#131B35"
  text_primary: "#E6EDF7"
  text_muted: "#B6C7DA"
  accent_cyan: "#22D3EE"
  accent_magenta: "#E11D8D"
  
style:
  - Dark premium
  - Glassmorphism subtil
  - Glow néon discret (pas criard)
  - Coins arrondis (8-12px)
  - Ombres douces
  
tone:
  - Pro mais pas corporate
  - Efficace, pas de fluff
  - Chaleureux (c'est THÉRÈSE, pas "Assistant Bot 3000")
```

---

## Prompt 4 : PRD THÉRÈSE (Agent PM)

```markdown
# MISSION: Rédiger le PRD de THÉRÈSE v2

## Inputs
- docs/benchmark-cowork.md
- docs/benchmark-memoire.md
- docs/benchmark-ux.md

## Vision produit

**THÉRÈSE** - L'assistante souveraine des entrepreneurs français

### Positionnement
Cowork d'Anthropic, mais :
- Avec mémoire persistante
- Avec meilleure UX/UI
- Souverain (API FR/EU d'abord, 100% local à terme)
- Pensé pour les solopreneurs français

### Tagline
"Ta mémoire, tes données, ton business."

## Ta mission

### 1. Executive Summary (10 lignes max)
- Problème
- Solution
- Différenciateurs
- Cible

### 2. Persona principal
**Ludo, 40 ans, consultant IA/automation**
- Ex-directeur d'agence bancaire
- Gère seul sa SARL
- Jongle entre prospection, delivery, admin
- Stack : Google Workspace, n8n, Claude
- Frustration : perd du contexte entre les outils
- Besoin : UN assistant qui sait tout de son business

### 3. User Stories MVP

#### Must-have (v1.0)
- En tant que Ludo, je veux discuter avec THÉRÈSE pour obtenir de l'aide sur mes tâches quotidiennes
- En tant que Ludo, je veux que THÉRÈSE se souvienne de mes clients et projets sans que je répète tout
- En tant que Ludo, je veux que THÉRÈSE accède à mes fichiers locaux pour les analyser
- En tant que Ludo, je veux voir le contexte/mémoire actif pour savoir ce que THÉRÈSE "sait"
- En tant que Ludo, je veux que mes données restent sur ma machine

#### Should-have (v1.1)
- Intégration Google Drive
- Rappels et tâches
- Export mémoire (backup)

#### Nice-to-have (v2.0)
- 100% local (LLM local)
- Automatisations n8n intégrées
- Vue CRM contacts

### 4. Fonctionnalités MVP détaillées

#### Chat intelligent
- Interface chat principale
- Support markdown dans les réponses
- Copier/coller facile
- Historique conversations

#### Mémoire persistante
- Entités : contacts, projets, préférences
- Stockage local SQLite + Qdrant
- Panneau "contexte actif" visible
- CRUD sur la mémoire (voir, éditer, supprimer)
- Recherche dans la mémoire

#### Accès fichiers
- Parcourir fichiers locaux
- Lire PDF, DOCX, TXT, MD, images
- Résumer, analyser, extraire

#### UX premium
- Dark mode natif (palette Synoptïa)
- Raccourcis clavier
- Onboarding < 2 minutes
- Responsive (desktop first)

### 5. Hors scope MVP
- Mobile app
- Collaboration multi-utilisateurs
- Intégrations tierces (sauf Google Drive en v1.1)
- LLM local (v2.0)
- Automatisations complexes

### 6. Stack technique

frontend: Tauri + React (ou Electron fallback)
backend: Python (FastAPI)
llm: Claude API (Anthropic) via clé utilisateur
database: SQLite (données) + Qdrant (embeddings)
storage: 100% local par défaut

### 7. Métriques de succès
- Time to first value < 2 min
- Rétention J7 > 50%
- NPS > 40
- Données : 0 envoyées hors LLM API

### 8. Risques
| Risque | Impact | Mitigation |
|--------|--------|------------|
| UX pas assez différenciante | Adoption faible | Tests utilisateurs early |
| Mémoire trop complexe | Confusion | Design simple, progressive disclosure |
| Performance Qdrant local | Latence | Benchmarks early, fallback SQLite FTS |
| Dépendance API Claude | Lock-in | Architecture LLM-agnostic |

## Output
Fichier `docs/prd-therese.md` complet, prêt pour l'agent Architect
```

---

## Prompt 5 : Architecture technique (Agent Architect)

```markdown
# MISSION: Définir l'architecture technique de THÉRÈSE v2

## Inputs
- docs/prd-therese.md (PRD validé)
- docs/benchmark-cowork.md
- docs/benchmark-memoire.md

## Contexte technique

### Contraintes imposées
- Desktop app (pas web-only)
- 100% données locales (sauf appels LLM API)
- Performance : réponse mémoire < 200ms
- Compatible macOS, Windows, Linux
- Code Python (backend) + TypeScript/React (frontend)
- Gestionnaire Python : UV (pas pip/poetry)

### Stack pressentie

frontend:
  framework: Tauri 2.0 (Rust + WebView)
  ui: React 18 + TypeScript
  styling: TailwindCSS
  state: Zustand ou Jotai
  
backend:
  runtime: Python 3.11+
  framework: FastAPI
  package_manager: UV
  
database:
  structured: SQLite (via SQLModel ou raw)
  vectors: Qdrant (mode embedded/local)
  
llm:
  primary: Claude API (Anthropic)
  fallback: Mistral API (EU)
  future: Ollama (100% local)

## Ta mission

### 1. Valider ou challenger la stack
- La stack proposée est-elle cohérente ?
- Y a-t-il des alternatives meilleures ?
- Risques techniques identifiés ?

### 2. Définir l'architecture globale

#### Diagramme de composants

┌─────────────────────────────────────────────────────────┐
│                    THÉRÈSE Desktop                       │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │   Tauri Shell   │  │      React Frontend         │  │
│  │   (Rust)        │  │  - Chat UI                  │  │
│  │   - File access │  │  - Memory Panel             │  │
│  │   - System tray │  │  - Settings                 │  │
│  │   - Shortcuts   │  │  - File Browser             │  │
│  └────────┬────────┘  └──────────────┬──────────────┘  │
│           │                          │                  │
│           └──────────┬───────────────┘                  │
│                      │ IPC                              │
│           ┌──────────▼───────────┐                      │
│           │   Python Backend     │                      │
│           │   (FastAPI sidecar)  │                      │
│           └──────────┬───────────┘                      │
│                      │                                  │
│  ┌───────────────────┼───────────────────┐             │
│  │                   │                   │             │
│  ▼                   ▼                   ▼             │
│ ┌─────────┐   ┌─────────────┐   ┌─────────────┐       │
│ │ SQLite  │   │   Qdrant    │   │  LLM API    │       │
│ │ (data)  │   │ (embeddings)│   │ (Claude/    │       │
│ │         │   │             │   │  Mistral)   │       │
│ └─────────┘   └─────────────┘   └─────────────┘       │
└─────────────────────────────────────────────────────────┘

### 3. Détailler chaque composant

#### Frontend (React + Tauri)
- Structure des dossiers
- Composants principaux
- Gestion du state
- Communication IPC avec backend
- Thème dark mode (tokens CSS)

#### Backend (Python FastAPI)
- Structure des dossiers
- Endpoints API
- Services métier
- Gestion des erreurs
- Logging

#### Module Mémoire
- Schéma SQLite (tables, relations)
- Stratégie d'embedding (quel modèle, quelle dimension)
- Pipeline d'indexation Qdrant
- Recherche hybride (keyword + semantic)
- CRUD mémoire
- Politique de rétention/oubli

#### Module LLM
- Abstraction multi-provider
- Gestion des tokens/coûts
- Streaming des réponses
- Injection du contexte mémoire
- Gestion des erreurs API

#### Module Fichiers
- Formats supportés
- Extraction de texte
- Indexation dans la mémoire
- Limites (taille, nb fichiers)

### 4. Flux de données principaux

#### Flux 1 : Conversation simple

User input → Frontend → Backend → LLM API → Response → Frontend

#### Flux 2 : Conversation avec mémoire

User input → Frontend → Backend → Memory Query (Qdrant) 
    → Context enriched → LLM API → Response 
    → Memory Update (si nouvelle info) → Frontend

#### Flux 3 : Analyse de fichier

File drop → Frontend → Backend → File Parser 
    → Text extraction → Embedding → Qdrant index 
    → SQLite metadata → Confirmation → Frontend

### 5. Sécurité et données

- Où sont stockées les données ? (chemin local)
- Chiffrement au repos ?
- Clé API LLM : où et comment stockée ?
- Logs : que logger, que ne pas logger ?
- RGPD : export/suppression des données

### 6. Performance

- Cibles de latence par opération
- Stratégie de cache
- Lazy loading
- Pagination mémoire

### 7. Évolutivité

- Comment ajouter un nouveau provider LLM ?
- Comment ajouter un nouveau type de fichier ?
- Comment ajouter des intégrations (Google Drive, etc.) ?
- Architecture plugin-ready ?

### 8. ADRs (Architecture Decision Records)

Pour chaque décision importante, documente :

## ADR-001: Choix de Tauri vs Electron

### Contexte
Besoin d'une app desktop cross-platform.

### Options considérées
1. Electron
2. Tauri
3. Flutter

### Décision
Tauri 2.0

### Justification
- Bundle plus léger (5-10 Mo vs 150+ Mo Electron)
- Meilleure perf (Rust vs Node)
- Accès filesystem natif
- Communauté active

### Conséquences
- Nécessite Rust installé pour le dev
- Moins de libs JS natives disponibles

Crée des ADRs pour :
- Tauri vs Electron
- SQLite vs autre DB
- Qdrant embedded vs server
- UV vs pip/poetry
- FastAPI sidecar vs Tauri Rust backend

## Output attendu
Fichier `docs/architecture.md` complet avec :
1. Vue d'ensemble (diagramme)
2. Stack technique validée
3. Détail de chaque composant
4. Schémas de données
5. Flux principaux
6. Considérations sécurité/perf
7. ADRs
8. Questions ouvertes pour le dev

## Format
- Markdown avec diagrammes ASCII (ou Mermaid si supporté)
- Tables pour les specs
- Code blocks pour les exemples
```

---

## Prompt 6 : Génération des Stories (Agent Scrum Master)

```markdown
# MISSION: Générer les User Stories pour THÉRÈSE v2

## Inputs
- docs/prd-therese.md (PRD validé)
- docs/architecture.md (Architecture validée)

## Contexte

### Rappel vision
THÉRÈSE = Cowork souverain + mémoire persistante + UX premium
Cible : solopreneurs français
MVP : Chat + Mémoire + Fichiers + UX dark mode

### Stack technique (résumé)
- Frontend : Tauri + React + TailwindCSS
- Backend : Python FastAPI + UV
- Data : SQLite + Qdrant
- LLM : Claude API

## Ta mission

### 1. Découper le MVP en Epics

#### Epic 1 : Infrastructure & Setup
Mise en place de la stack technique de base.

#### Epic 2 : Chat Core
Interface de conversation avec le LLM.

#### Epic 3 : Mémoire Persistante
Stockage, retrieval et affichage du contexte.

#### Epic 4 : Gestion des Fichiers
Accès, lecture et indexation des fichiers locaux.

#### Epic 5 : UX/UI Premium
Thème dark, animations, raccourcis, onboarding.

### 2. Pour chaque Epic, génère les Stories

Format de chaque story :

# Story [EPIC]-[NUM]: [Titre court]

## Description
En tant que [persona],
Je veux [action],
Afin de [bénéfice].

## Contexte technique
- Composants impactés : [liste]
- Dépendances : [stories prérequises]
- Fichiers concernés : [chemins]

## Critères d'acceptation
- [ ] [Critère 1 - testable]
- [ ] [Critère 2 - testable]
- [ ] [Critère 3 - testable]

## Notes techniques
[Détails d'implémentation, edge cases, etc.]

## Estimation
- Complexité : [S/M/L/XL]
- Points : [1/2/3/5/8/13]

## Maquette / Wireframe
[ASCII ou description si pertinent]

### 3. Stories attendues par Epic

#### Epic 1 : Infrastructure & Setup
- E1-01 : Initialiser le projet Tauri + React
- E1-02 : Configurer le backend Python FastAPI
- E1-03 : Mettre en place SQLite avec schéma initial
- E1-04 : Intégrer Qdrant en mode embedded
- E1-05 : Créer la communication IPC Tauri ↔ Backend
- E1-06 : Configurer le build cross-platform

#### Epic 2 : Chat Core
- E2-01 : Créer l'interface chat (input + messages)
- E2-02 : Intégrer l'API Claude (envoi/réception)
- E2-03 : Implémenter le streaming des réponses
- E2-04 : Gérer l'historique de conversation (session)
- E2-05 : Ajouter le support Markdown dans les réponses
- E2-06 : Implémenter copier/coller et actions sur messages

#### Epic 3 : Mémoire Persistante
- E3-01 : Définir le schéma mémoire (entités, relations)
- E3-02 : Créer le service d'embedding (texte → vecteur)
- E3-03 : Implémenter l'indexation dans Qdrant
- E3-04 : Créer la recherche hybride (keyword + semantic)
- E3-05 : Injecter le contexte mémoire dans les prompts LLM
- E3-06 : Créer le panneau "Contexte actif" (UI)
- E3-07 : Implémenter CRUD mémoire (voir, éditer, supprimer)
- E3-08 : Ajouter l'extraction auto d'entités depuis les conversations

#### Epic 4 : Gestion des Fichiers
- E4-01 : Créer le file browser (navigation dossiers)
- E4-02 : Implémenter la lecture PDF
- E4-03 : Implémenter la lecture DOCX
- E4-04 : Implémenter la lecture TXT/MD
- E4-05 : Ajouter le drag & drop de fichiers
- E4-06 : Indexer les fichiers dans la mémoire
- E4-07 : Permettre l'analyse de fichier via chat ("résume ce PDF")

#### Epic 5 : UX/UI Premium
- E5-01 : Implémenter le thème dark Synoptïa
- E5-02 : Créer les composants UI de base (boutons, inputs, cards)
- E5-03 : Ajouter les raccourcis clavier globaux
- E5-04 : Créer l'écran d'onboarding (première utilisation)
- E5-05 : Ajouter les micro-animations (transitions, feedback)
- E5-06 : Implémenter le system tray + raccourci global
- E5-07 : Créer l'écran Settings (clé API, préférences)
- E5-08 : Optimiser la responsive (redimensionnement fenêtre)

### 4. Priorisation

Ordonne les stories pour un développement incrémental :
1. D'abord ce qui permet de tester (infra + chat basique)
2. Ensuite le différenciateur (mémoire)
3. Puis les enrichissements (fichiers, UX polish)

### 5. Dépendances

Crée un graphe de dépendances :

E1-01 ─┬─► E1-02 ─┬─► E1-05 ─► E2-01
       │          │
       │          └─► E1-03 ─► E3-01
       │
       └─► E1-04 ─► E3-02

### 6. Sprint Planning suggéré

#### Sprint 1 (2 semaines) : Fondations
- E1-01 à E1-06
- E2-01, E2-02

#### Sprint 2 (2 semaines) : Chat fonctionnel
- E2-03 à E2-06
- E5-01, E5-02

#### Sprint 3 (2 semaines) : Mémoire
- E3-01 à E3-05
- E3-06

#### Sprint 4 (2 semaines) : Fichiers + Polish
- E4-01 à E4-07
- E3-07, E3-08
- E5-03 à E5-08

## Output attendu

### Structure des fichiers

docs/
├── epics/
│   ├── epic-1-infrastructure.md
│   ├── epic-2-chat-core.md
│   ├── epic-3-memoire.md
│   ├── epic-4-fichiers.md
│   └── epic-5-ux-ui.md
├── stories/
│   ├── E1-01-init-tauri-react.md
│   ├── E1-02-setup-backend-python.md
│   ├── ... (toutes les stories)
└── planning/
    ├── sprint-1.md
    ├── sprint-2.md
    ├── sprint-3.md
    └── sprint-4.md

### Chaque fichier Epic contient
- Vision de l'epic
- Liste des stories
- Critères de succès de l'epic
- Risques identifiés

### Chaque fichier Story contient
- Le format complet défini ci-dessus
- Prêt à être implémenté par l'agent Dev

## Contraintes
- Stories atomiques (1 story = 1 PR max)
- Pas de story > 8 points
- Chaque story testable indépendamment
- Nommage cohérent : E[epic]-[num]-[slug]
```

---

## Récap et ordre d'exécution

### Tableau récapitulatif

| # | Fichier output | Agent BMAD | Objectif |
|---|----------------|------------|----------|
| 0 | Structure projet | Claude Code | Créer structure, installer BMAD |
| 1 | `docs/benchmark-cowork.md` | Analyst | Comprendre Cowork |
| 2 | `docs/benchmark-memoire.md` | Analyst | État de l'art mémoire IA |
| 3 | `docs/benchmark-ux.md` | UX Designer | Inspiration interfaces |
| 4 | `docs/prd-therese.md` | PM | Specs fonctionnelles |
| 5 | `docs/architecture.md` | Architect | Specs techniques |
| 6 | `docs/stories/*.md` | Scrum Master | User stories dev |

### Ordre d'exécution recommandé

```bash
# 1. Setup (Prompt 0)
# Copie le prompt 0 dans Claude Code et exécute

# 2. Lance BMAD
*workflow-init

# 3. Benchmarks en parallèle (Prompts 1, 2, 3)
*analyst  # Puis colle prompt 1, puis prompt 2
*ux       # Puis colle prompt 3

# 4. PRD (Prompt 4)
*pm       # Après avoir les benchmarks

# 5. Architecture (Prompt 5)
*architect  # Après avoir le PRD

# 6. Stories (Prompt 6)
*sm       # Génère les stories depuis PRD + Archi
```

### Commandes BMAD utiles

| Commande | Agent | Usage |
|----------|-------|-------|
| `*workflow-init` | Master | Analyse le projet et recommande un track |
| `*analyst` | Analyst | Recherche et benchmark |
| `*pm` | Product Manager | Crée/modifie le PRD |
| `*ux` | UX Designer | Design et wireframes |
| `*architect` | Architect | Crée/modifie l'architecture |
| `*sm` | Scrum Master | Génère les stories |
| `*dev` | Developer | Implémente le code |
| `*qa` | QA | Valide et teste |
| `*help` | - | Liste toutes les commandes |

---

## Infos projet

- **Nom** : THÉRÈSE v2
- **Créateur** : Ludo Sanchez (Synoptïa)
- **Repo** : À créer
- **Méthodologie** : BMAD Method
- **Stack** : Tauri + React + Python FastAPI + SQLite + Qdrant
- **Cible** : Solopreneurs français

---

*Document généré le 21 janvier 2026*
*Synoptïa - "Humain d'abord, IA en soutien"*
