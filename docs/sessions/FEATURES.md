# THÉRÈSE V2 - Features

> "Ta mémoire, tes données, ton business."

**Version** : 2.7
**Date** : 24 janvier 2026
**Auteur** : Synoptïa (Ludo Sanchez)

---

## Vue d'ensemble

THÉRÈSE V2 est une application desktop d'assistant IA souverain, alternative française à Claude Desktop/Cowork.

### Stack Technique

| Composant | Technologie |
|-----------|-------------|
| Frontend | Tauri 2.0 + React + TypeScript + TailwindCSS |
| Backend | Python FastAPI + UV |
| Base de données | SQLite (conversations, mémoire) + Qdrant (embeddings) |
| LLM | Multi-provider (6 providers supportés) |

---

## Fonctionnalités

### 1. Chat Multi-Provider

Support de 6 providers LLM avec streaming SSE.

| Provider | Modèles | Notes |
|----------|---------|-------|
| **Anthropic** | Claude 4.5 Sonnet/Haiku/Opus | Recommandé |
| **OpenAI** | GPT-4o, GPT-4 Turbo, o3, o4-mini | Multimodal |
| **Gemini** | 3 Pro/Flash, 2.5 Pro/Flash | 1M tokens context |
| **Mistral** | Large, Codestral, Small | IA française |
| **Grok** | 3, 3 Fast | xAI |
| **Ollama** | Tous modèles locaux | 100% offline |

**Fonctionnalités chat** :
- Streaming temps réel (SSE)
- Conversations persistées (SQLite)
- Conversations éphémères (non sauvegardées)
- Historique groupé par date
- Commandes slash (`/fichier`, `/analyse`)

---

### 2. Mémoire Intelligente

Système de mémoire contextuelle avec embeddings vectoriels.

**Entités supportées** :
- **Contacts** : nom, email, entreprise, téléphone, notes, tags
- **Projets** : nom, description, statut, budget, contact lié, tags

**Fonctionnalités** :
- Embeddings Qdrant (`nomic-embed-text-v1.5`, 768 dims)
- Recherche hybride BM25 + sémantique
- Injection contexte automatique dans le LLM
- Scope par entité (global, projet, conversation)
- Extraction automatique d'entités depuis les messages

---

### 3. Gestion de Fichiers

Intégration native avec le système de fichiers via Tauri.

**Fonctionnalités** :
- Drag & Drop avec indexation automatique
- File Browser natif
- Chunking intelligent (1000 chars, 200 overlap)
- Commandes `/fichier [path]` et `/analyse [path]`

**Formats supportés** :
- Texte : `.txt`, `.md`, `.json`
- Code : `.py`, `.js`, `.ts`, `.html`, `.css`
- Documents : `.pdf`, `.docx` (extraction texte)

---

### 4. Skills Office

Génération de documents Office professionnels.

| Skill | Format | Librairie |
|-------|--------|-----------|
| `docx-pro` | Word (.docx) | python-docx |
| `pptx-pro` | PowerPoint (.pptx) | pptxgenjs |
| `xlsx-pro` | Excel (.xlsx) | openpyxl |

**Fonctionnalités** :
- Prompting guidé pour chaque type
- Preview et téléchargement
- Charte visuelle Synoptïa intégrée

---

### 5. Board de Décision

Conseil stratégique multi-LLM avec 5 conseillers IA.

| Conseiller | Personnalité | Provider préféré |
|------------|--------------|------------------|
| L'Analyste | Structuré, factuel | Anthropic |
| Le Stratège | Créatif, visionnaire | OpenAI |
| L'Avocat du Diable | Critique, nuancé | Anthropic |
| Le Pragmatique | Concret, actionnable | Mistral |
| Le Visionnaire | Futuriste, innovant | Gemini |

**Fonctionnalités** :
- Délibération parallèle multi-LLM
- Synthèse automatique (consensus, divergences)
- Niveau de confiance et recommandation
- Historique persisté (SQLite)
- Raccourci clavier `⌘+D`

---

### 6. Calculateurs Financiers

Outils de calcul pour entrepreneurs.

| Calculateur | Description |
|-------------|-------------|
| **ROI** | Return on Investment |
| **ICE** | Impact × Confidence × Ease |
| **RICE** | (Reach × Impact × Confidence) / Effort |
| **NPV** | Net Present Value (Valeur Actuelle Nette) |
| **Break-even** | Seuil de rentabilité |

---

### 7. MCP (Model Context Protocol)

Intégration complète du protocole MCP d'Anthropic.

**Fonctionnalités** :
- Gestion serveurs MCP (start/stop/restart)
- Transport stdio JSON-RPC
- Auto-discovery des tools
- Presets prédéfinis

**Presets inclus** :
- Filesystem - Gestion fichiers
- Fetch - Récupération URLs
- Memory - Mémoire persistante
- Brave Search - Recherche web
- GitHub - Accès repos
- Notion - Workspace
- Slack - Workspace
- Google Drive - Fichiers

**Tool Calling** :
- Function calling pour Claude et OpenAI
- Exécution automatique des tools
- Chaînage de tools (max 5 itérations)
- Affichage status en temps réel

---

### 8. Recherche Web

Les LLMs peuvent chercher sur le web à la demande.

| Provider | Méthode |
|----------|---------|
| **Gemini** | Google Search Grounding (natif) |
| **Autres** | Tool DuckDuckGo (gratuit) |

**Fonctionnalités** :
- Détection automatique du besoin de recherche
- Résultats formatés pour le LLM
- Toggle on/off dans les paramètres
- Pas d'API key requise (DuckDuckGo)

---

### 9. Génération d'Images

Support de deux providers d'images IA.

| Provider | Modèle | Résolutions |
|----------|--------|-------------|
| **GPT Image 1.5** | OpenAI | 1024², 1536×1024, 1024×1536 |
| **Nano Banana Pro** | Gemini | 1K, 2K, 4K |

**Fonctionnalités** :
- Clés API séparées (chat vs images)
- Preview et téléchargement
- Historique des générations

---

### 10. Input Vocal

Dictée vocale via Groq Whisper.

**Fonctionnalités** :
- Modèle `whisper-large-v3-turbo`
- Optimisé français
- Chunking pour fichiers > 25 MB
- Bouton micro dans l'input

---

### 11. Onboarding

Wizard de configuration au premier lancement.

**Étapes** :
1. Bienvenue + présentation
2. Profil utilisateur (import CLAUDE.md possible)
3. Configuration LLM (provider, clé API, modèle)
4. Dossier de travail
5. Récapitulatif + lancement

---

### 12. Interface Utilisateur

**Design** :
- Dark mode premium (charte Synoptïa)
- Glassmorphism + gradients cyan/magenta
- Animations Framer Motion (spring, stagger)

**Navigation** :
- Side toggles latéraux (conversations, mémoire)
- Palette de commandes (`⌘+K`)
- Guided Prompts (6 actions × 4 sous-options)

**Raccourcis clavier** :
| Raccourci | Action |
|-----------|--------|
| `⌘+B` | Conversations |
| `⌘+M` | Mémoire/Espace de travail |
| `⌘+K` | Palette de commandes |
| `⌘+D` | Board de décision |
| `⌘+,` | Paramètres |
| `/` | Commandes slash |

---

## API Backend

### Endpoints principaux

| Route | Description |
|-------|-------------|
| `POST /api/chat/send` | Envoyer un message (SSE) |
| `GET /api/conversations` | Liste des conversations |
| `GET /api/memory/contacts` | Liste des contacts |
| `GET /api/memory/projects` | Liste des projets |
| `POST /api/skills/execute` | Exécuter un skill Office |
| `POST /api/board/deliberate` | Lancer une délibération |
| `POST /api/calc/{type}` | Calculateurs financiers |
| `GET /api/mcp/servers` | Serveurs MCP |
| `GET /api/config/` | Configuration app |
| `POST /api/images/generate` | Générer une image |
| `GET /api/config/web-search` | Status recherche web |

---

## Installation

### Prérequis

- Node.js 20+
- Python 3.12+
- UV (gestionnaire Python)
- Rust (pour Tauri)

### Backend

```bash
cd src/backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd src/frontend
npm install
npm run tauri dev
```

### Production

```bash
cd src/frontend
npm run tauri build
```

---

## Configuration

### Variables d'environnement

```bash
# LLM Providers
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
MISTRAL_API_KEY=...
XAI_API_KEY=xai-...  # Grok
GROQ_API_KEY=gsk_...  # Voice

# Images (optionnel, séparées des clés LLM)
OPENAI_IMAGE_API_KEY=sk-...
GEMINI_IMAGE_API_KEY=AIza...
```

### Fichiers de configuration

- `~/.therese/` - Dossier données utilisateur
- `~/.therese/therese.db` - Base SQLite
- `~/.therese/qdrant/` - Données Qdrant
- `~/.therese/files/` - Fichiers uploadés
- `~/.therese/images/` - Images générées
- `~/.therese/mcp_servers.json` - Config MCP

---

## Licence

MIT - Synoptïa 2026

---

*THÉRÈSE - Ta mémoire, tes données, ton business.*
