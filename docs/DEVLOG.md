# DEVLOG - THÉRÈSE V2

> Ce fichier est le journal de développement complet. Pour un résumé par version, voir [CHANGELOG.md](./CHANGELOG.md).
> Pour les règles de travail Claude Code, voir [CLAUDE.md](../CLAUDE.md) à la racine.

---

## Session 21 janvier 2026 - MVP Chat (v1.0)

### Frontend Tauri (src/frontend/)
- [x] Structure Tauri 2.0 + React + TailwindCSS
- [x] `ChatLayout.tsx` - Layout principal avec raccourcis clavier
- [x] `ChatHeader.tsx` - Header avec branding, drag region macOS
- [x] `MessageList.tsx` - Liste messages + état vide premium
- [x] `MessageBubble.tsx` - Rendu Markdown + coloration syntaxique
- [x] `ChatInput.tsx` - Saisie + commandes slash + streaming
- [x] `CommandPalette.tsx` - Palette Cmd+K
- [x] `ShortcutsModal.tsx` - Affichage raccourcis
- [x] `TypingIndicator.tsx` - Animation "réflexion"
- [x] `SlashCommandsMenu.tsx` - Menu commandes /
- [x] `chatStore.ts` - Zustand store avec persistance
- [x] `statusStore.ts` - État connexion
- [x] `api.ts` - Service API avec streaming SSE
- [x] `useHealthCheck.ts` - Health check backend
- [x] `useKeyboardShortcuts.ts` - Raccourcis globaux
- [x] `useConversationSync.ts` - Sync conversations

### Backend FastAPI (src/backend/)
- [x] `app/main.py` - App FastAPI avec lifespan
- [x] `app/routers/chat.py` - Endpoints chat + streaming SSE
- [x] `app/routers/memory.py` - Contacts/Projets CRUD
- [x] `app/routers/files.py` - Upload fichiers
- [x] `app/routers/config.py` - Préférences/API keys
- [x] `app/services/llm.py` - Service LLM (Claude API)
- [x] `app/services/qdrant.py` - Vector store
- [x] `app/services/embeddings.py` - Embeddings
- [x] `app/models/entities.py` - SQLModel entities
- [x] `app/models/schemas.py` - Pydantic schemas
- [x] Alembic migrations configurées

### Derniers fixes
- [x] Fix erreur 404 "Conversation not found" (sync conversation_id)
- [x] Fix drag fenêtre Tauri (data-tauri-drag-region + z-index)
- [x] Padding pour boutons macOS (pl-20)

### Session 21 janvier - après-midi
- [x] Streaming API testé et fonctionnel
- [x] Panel Mémoire (`src/frontend/src/components/memory/MemoryPanel.tsx`)
  - Sidebar slide-in avec tabs Contacts/Projets
  - Recherche intégrée, liste avec avatars/badges
  - Toggle via Cmd+M ou bouton header
- [x] Page Paramètres (`src/frontend/src/components/settings/SettingsModal.tsx`)
  - Modal config clé API Anthropic
  - Validation format sk-ant-*, show/hide password
  - Status visuel (configuré/non configuré)

### Session 21 janvier - soirée (BMAD P0 complété)
- [x] `ContactModal.tsx` - CRUD contacts (nom, email, entreprise, téléphone, notes, tags)
- [x] `ProjectModal.tsx` - CRUD projets (nom, description, statut, budget, contact lié, tags)
- [x] `ConversationSidebar.tsx` - Sidebar gauche avec liste groupée par date, recherche, Cmd+B
- [x] `SettingsModal.tsx` refondu - 3 onglets (API, Modèle, Données), sélection LLM Claude
- [x] `ChatLayout.tsx` - Intégration de tous les nouveaux composants
- [x] `useKeyboardShortcuts.ts` - Ajout Cmd+B, Cmd+Shift+C, Cmd+Shift+P

### Session 21 janvier - nuit (BMAD P1 Mémoire complété)
- [x] **E3-02: Embeddings nomic-embed-text**
  - Modèle: `nomic-ai/nomic-embed-text-v1.5` (768 dims)
  - Auto-embedding contacts/projets à la création/màj/suppression
  - Dépendance `einops` ajoutée, `trust_remote_code=True`
- [x] **E3-03: Recherche hybride BM25 + semantic**
  - Semantic search via Qdrant `query_points()`
  - Fallback keyword search pour compléter
  - Score sémantique prioritaire sur keyword
- [x] **E3-04: Injection contexte auto dans LLM**
  - `_get_memory_context()` dans chat.py
  - Recherche mémoire sur chaque message user
  - Injection dans system prompt via `memory_context`
  - Testé avec succès: "Qui est Pierre?" -> répond avec infos contact

### Session 21 janvier - suite (BMAD P2 File Management + Polish)
- [x] **E4-05: Drag & Drop Fichiers**
  - `useFileDrop.ts` - Hook Tauri pour événements drag/drop
  - `DropZone.tsx` - Composant overlay full-screen + inline variant
  - `FileChip.tsx` - Badge fichier avec taille/type/suppression
  - Intégré dans `ChatInput.tsx` avec bouton pièce jointe + picker
  - Support Tauri dialog plugin pour sélection fichiers
- [x] **E4-06: Indexation fichiers en mémoire**
  - `file_parser.py` - Service extraction texte + chunking (1000 chars, 200 overlap)
  - Support: .txt, .md, .json, .py, .js, .ts, .html, .css
  - Chunks indexés dans Qdrant avec `entity_id` référence
  - `chat.py` mis à jour pour inclure fichiers dans contexte mémoire
- [x] **E5-04: Animations Framer Motion**
  - `animations.ts` - Bibliothèque variants (fade, scale, slide, modal, message)
  - `useReducedMotion.ts` - Hook accessibilité (prefers-reduced-motion)
  - `MessageBubble.tsx` - Animation spring sur messages
  - Transitions: spring 500/30, ease [0.4,0,0.2,1]

### Session 21 janvier - fin (BMAD E5 Polish complété)
- [x] **E5-05: Animation stagger liste conversations**
  - `ConversationSidebar.tsx` - staggerContainer + staggerItem sur liste
  - Groupement par date avec animations entrée décalées
- [x] **E5-06: Animation ouverture/fermeture modals**
  - `ContactModal.tsx`, `ProjectModal.tsx`, `SettingsModal.tsx`
  - modalVariants + overlayVariants (scale + fade)
- [x] **E5-07: Animation sidebar et panels**
  - `MemoryPanel.tsx` - sidebarVariants (slide-in droite)
  - `ConversationSidebar.tsx` - sidebarLeftVariants (slide-in gauche)
- [x] **Fix bug double drop fichiers**
  - Pattern refs pour éviter recréation listeners
  - `isSetupRef` pour React StrictMode
  - Déduplication par path dans ChatInput

### Session 21 janvier - finale (Tests + Optimisation)
- [x] **Tests Vitest**
  - Config `vitest.config.ts` + setup mocks Tauri
  - 32 tests : chatStore (15) + utils (17)
  - Scripts: `npm test`, `npm run test:watch`
- [x] **Code splitting bundle**
  - Chunks séparés: react, ui, markdown, state, tauri
  - Bundle principal: 1.2 MB -> 303 KB (-75%)

---

## Session 21 janvier - UI Guided Prompts (v1.1)

- [x] **Guided Prompts UI** - Interface guidée pour l'écran vide
  - `src/frontend/src/components/guided/` - Nouveau module complet
  - `actionData.ts` - Configuration 3 actions + 24 sous-options avec prompts
  - `ActionCard.tsx` - Cartes actions avec animations hover/tap Framer Motion
  - `SubOptionsPanel.tsx` - Panel sous-options en pills avec navigation retour
  - `GuidedPrompts.tsx` - Composant orchestrateur avec transitions AnimatePresence
  - `index.ts` - Exports module
- [x] **Intégration MessageList.tsx** - Remplacement état vide par `<GuidedPrompts />`
- [x] **Intégration ChatInput.tsx** - Props `initialPrompt` + `onInitialPromptConsumed`
- [x] **Intégration ChatLayout.tsx** - État `guidedPrompt` pour câblage MessageList -> ChatInput

**Les 3 actions Synoptïa** (consolidation 25 janvier 2026) :
| Action | Icône | Sous-options (24 total) |
|--------|-------|------------------------|
| Produire | Sparkles | Email pro, Post LinkedIn, Proposition commerciale, Document Word, Présentation PPT, Tableur Excel, Image IA GPT, Image IA Gemini (8) |
| Comprendre | Brain | Fichier Excel, Document PDF, Site web, Marché, Outil IA, Concept, Best practices (7) |
| Organiser | GitBranch | Réunion, Projet, Semaine, Objectifs, Workflow n8n, Apps Script, Make, Zapier, Processus (9) |

---

## Session 21-22 janvier - Identité & Multi-Provider LLM (v1.2)

- [x] **Phase 1 : Identité utilisateur** (fix bug "Pierre" au lieu de "Ludo")
  - `app/services/user_profile.py` - Service profil utilisateur avec cache
  - Endpoints `/api/config/profile` (GET/POST/DELETE)
  - Injection identité dans system prompt LLM
  - Onglet Profil dans SettingsModal (nom, surnom, entreprise, rôle, contexte)
- [x] **Phase 2 : Import CLAUDE.md**
  - Endpoint `/api/config/profile/import-claude-md`
  - Parse sections Identité/Infos perso automatique
  - Bouton import dans UI avec Tauri dialog
- [x] **Phase 3 : UI Conversations améliorée**
  - Bouton conversations dans ChatHeader
  - Hint raccourci Cmd+B dans GuidedPrompts
- [x] **Phase 4 : Sélecteur dossier de travail**
  - Endpoints `/api/config/working-directory` (GET/POST)
  - UI dans SettingsModal onglet Données
  - Validation chemin existant
- [x] **Phase 5 : Multi-Provider LLM**
  - Support 5 providers : Anthropic, OpenAI, Gemini, Mistral, Ollama
  - `llm.py` - Streaming pour tous les providers
  - Endpoints `/api/config/llm` et `/api/config/ollama/status`
  - UI unifiée dans SettingsModal (sélection provider, clé API, modèle)
  - Ollama : détection auto des modèles locaux

**Providers supportés (janvier 2026)** :
| Provider | Modèle ID API | Notes |
|----------|---------------|-------|
| Anthropic | `claude-opus-4-5-20251101` | Opus 4.5 - Recommandé |
| OpenAI | `gpt-5.2` | GPT-5.2 |
| Gemini | `gemini-3-pro-preview` | Gemini 3 Pro - 1M context |
| Mistral | `mistral-large-latest` | Mistral Large 3 - IA française |
| Grok | `grok-4` | Grok 4 - xAI |
| Ollama | Dynamique (local) | 100% local |

---

## Session 22 janvier - Skills Office (v1.3)

- [x] `actionData.ts` avec `generatesFile` sur sous-options
- [x] Backend `app/services/skills/` - DOCX/PPTX/XLSX generators
- [x] `app/routers/skills.py` - Endpoints execute/download/list
- [x] UI `SkillExecutionPanel.tsx` - Spinner, preview, téléchargement
- [x] Intégration `GuidedPrompts.tsx` avec détection skill
- [x] **Fix** : Bug cache fichiers (`registry.py` - name mangling Python)
- [x] **Fix** : Bug XLSX merged cells (`xlsx_generator.py` - `column_letter`)

**Skills disponibles** :
| Skill | Format | Description |
|-------|--------|-------------|
| docx-pro | .docx | Document Word avec style Synoptïa |
| pptx-pro | .pptx | Présentation PowerPoint |
| xlsx-pro | .xlsx | Tableur Excel avec formules |

---

## Session 22 janvier - UI Side Toggles (v1.4)

- [x] **SideToggle.tsx** - Rails latéraux pour ouvrir/fermer panels
  - Composant `src/frontend/src/components/ui/SideToggle.tsx`
  - Rails minces (10px) qui s'élargissent au hover (36px)
  - Indicateur vertical cyan (glow quand panel ouvert)
  - Animation spring Framer Motion
  - Icônes contextuelles (PanelLeftOpen/Close, PanelRightOpen/Close)
- [x] **ChatLayout.tsx** - Intégration des toggles gauche/droite
- [x] **ChatHeader.tsx** - Suppression des icônes Conversations/Mémoire (remplacées par toggles)

**Nouvelles interactions UI** :
- Rail gauche : Ouvre ConversationSidebar (Cmd+B)
- Rail droit : Ouvre MemoryPanel (Cmd+M)

---

## Session 22 janvier - Voice Input (v1.5)

- [x] **useVoiceRecorder.ts** - Hook MediaRecorder API
  - Capture audio WebM/Opus via getUserMedia
  - États: idle -> recording -> processing -> idle
  - Gestion permissions micro navigateur
- [x] **transcribeAudio** dans api.ts - Envoi audio au backend
- [x] **Backend /api/voice/transcribe** - Endpoint transcription
  - Groq API avec modèle whisper-large-v3-turbo
  - Chunking si fichier > 25 MB
  - Prompt optimisé pour français
- [x] **ChatInput.tsx** - Bouton micro intégré
  - Icône Mic/MicOff selon état
  - Animation pulse rouge pendant enregistrement
  - Spinner pendant transcription
  - Transcription insérée dans textarea
- [x] **SettingsModal.tsx** - Configuration clé API Groq

---

## Session 22 janvier - Image Generation (v1.6)

- [x] **app/services/image_generator.py** - Service génération images
  - Support GPT Image 1.5 (OpenAI) + Nano Banana Pro (Gemini)
  - Modes: génération simple + avec image de référence
  - Sauvegarde images dans ~/.therese/images/
- [x] **app/routers/images.py** - API endpoints
  - POST /api/images/generate - Génération texte->image
  - POST /api/images/generate-with-reference - Avec image référence
  - GET /api/images/download/{id} - Téléchargement
  - GET /api/images/list - Liste des images générées
  - GET /api/images/status - Status providers disponibles
- [x] **api.ts** - Fonctions frontend
- [x] **SettingsModal.tsx** - UI sélection provider image

**Providers images supportés** :
| Provider | Modèle | Résolutions |
|----------|--------|-------------|
| GPT Image 1.5 | gpt-image-1.5 | 1024x1024, 1536x1024, 1024x1536 |
| Nano Banana Pro | gemini-3-pro-image-preview | 1K, 2K, 4K |

---

## Session 23 janvier - Scope Mémoire + Oubli Sélectif

- [x] **entities.py** - Champs scope sur Contact, Project, FileMetadata
  - `scope: str` = global | project | conversation
  - `scope_id: str | None` = ID de l'entité parente si scope
- [x] **qdrant.py** - Filtrage par scope dans search()
- [x] **memory.py** - API endpoints avec scope
- [x] **api.ts** - Types et fonctions frontend
- [x] **MemoryPanel.tsx** - UI scope et suppression avec modal confirmation

---

## Session 23 janvier - File Browser + Analyse Fichiers Chat

- [x] **FileBrowser.tsx** - Navigateur fichiers natif Tauri
  - API Tauri fs (readDir, stat, homeDir)
  - Navigation breadcrumb + boutons (home, up, refresh)
  - Icônes par type de fichier
  - Filtrage par recherche
  - Bouton indexation vers Qdrant par fichier
- [x] **chat.py** - Commandes slash fichiers
  - `/fichier [chemin]` - Ajoute le contenu du fichier au contexte
  - `/analyse [chemin]` - Demande une analyse du fichier

---

## Session 23 janvier - Extraction Automatique d'Entités (v1.7)

- [x] **app/services/entity_extractor.py** - Service d'extraction d'entités
  - Utilise le LLM pour extraire contacts et projets des messages
  - Prompt structuré retournant du JSON
  - Seuil de confiance configurable (MIN_CONFIDENCE = 0.6)
- [x] **app/routers/chat.py** - Intégration dans le streaming SSE
  - Extraction après chaque réponse du LLM
  - Nouvel event SSE `entities_detected`
- [x] **EntitySuggestion.tsx** - Composant UI de confirmation
  - Boutons "Sauvegarder" / "Ignorer" par entité
  - Animation slide-in Framer Motion

**Flux** : User envoie message -> LLM répond -> extraction en arrière-plan -> event SSE -> UI suggestion -> user confirme/ignore

---

## Session 23 janvier - Onboarding Wizard (v1.8)

- [x] **OnboardingWizard.tsx** - Composant principal wizard
  - Modal plein écran avec backdrop blur
  - Stepper 5 étapes avec indicateurs visuels
  - Transitions AnimatePresence entre étapes
- [x] **WelcomeStep.tsx** - Étape 1 : Bienvenue
- [x] **ProfileStep.tsx** - Étape 2 : Profil utilisateur
- [x] **LLMStep.tsx** - Étape 3 : Configuration LLM
- [x] **WorkingDirStep.tsx** - Étape 4 : Dossier de travail
- [x] **CompleteStep.tsx** - Étape 5 : Terminé
- [x] **Backend endpoints** - GET/POST `/api/config/onboarding-complete`
- [x] **App.tsx** - Check onboarding status au démarrage

---

## Session 23 janvier - Corrections Onboarding (v1.9)

### Audit complet par 3 agents spécialisés
**23 problèmes identifiés -> 12 user stories -> Toutes implémentées**

### Corrections UX/Navigation (P0)
- [x] **US-01: WorkingDirStep** - Bouton "Continuer" disabled si pas de dossier
- [x] **US-02: LLMStep** - Warning si pas de clé API + "Continuer" disabled
- [x] **US-03: CompleteStep** - Affichage erreur si finalisation échoue + bouton Réessayer
- [x] **US-04: Accents français** - Tous les accents manquants corrigés

### Accessibilité (P1)
- [x] **US-05 à US-09** - Labels accessibles, focus visible, radios sémantiques, ARIA modal, contraste placeholders

### Intégration Backend/Types (P2)
- [x] **US-10 à US-12** - Types nullable, validation clés API, animations unifiées

---

## Session 26 janvier - SecurityStep Onboarding (v2.9)

- [x] **SecurityStep.tsx** - Nouvelle étape 4/6
  - Avertissement sur les risques liés aux connexions cloud
  - Liste des 5 risques (LLMs cloud, MCP servers, fichiers, web search, transcription)
  - Checkbox d'acknowledgement obligatoire
- [x] **OnboardingWizard.tsx** - Wizard passe de 5 à 6 étapes

---

## Session 24 janvier - Board de Décision Stratégique (v2.0)

Feature complète permettant de convoquer un "board" de 5 conseillers IA pour les décisions stratégiques.

#### US-BOARD-01 : Module Board créé
- [x] **BoardPanel.tsx** - Panel principal modal (états: input, deliberating, history, viewing)
- [x] **AdvisorCard.tsx** - Carte conseiller (avatar emoji, nom, couleur, badge provider)
- [x] **DeliberationView.tsx** - Vue délibération (grille responsive, streaming simultané)
- [x] **SynthesisCard.tsx** - Carte synthèse (recommandation, consensus, divergences, confiance)

#### US-BOARD-02 : Délibération Multi-LLM
| Conseiller | Provider préféré | Raison |
|------------|------------------|--------|
| L'Analyste | Anthropic (Claude) | Analyse structurée |
| Le Stratège | OpenAI (GPT) | Créativité stratégique |
| L'Avocat du Diable | Anthropic (Claude) | Argumentation nuancée |
| Le Pragmatique | Mistral | IA française, pragmatisme |
| Le Visionnaire | Gemini | Vision futuriste |

#### US-BOARD-03/04 : Synthèse & Historique
- [x] Synthèse automatique après tous les avis
- [x] Persistance SQLite - Table `board_decisions`
- [x] API Historique (GET/DELETE /api/board/decisions)

---

## Session 24 janvier - Calculateurs Financiers (v2.1)

| Calculateur | Endpoint | Description |
|-------------|----------|-------------|
| **ROI** | `POST /api/calc/roi` | Return on Investment |
| **ICE** | `POST /api/calc/ice` | Impact x Confidence x Ease |
| **RICE** | `POST /api/calc/rice` | (Reach x Impact x Confidence) / Effort |
| **NPV** | `POST /api/calc/npv` | Net Present Value (VAN) |
| **Break-even** | `POST /api/calc/break-even` | Seuil de rentabilité |

---

## Session 24 janvier - Soir (v2.2 - Grok + UX)

#### Bugs corrigés
- [x] **Bug 1: GPT Image 1.5** - Retiré `response_format="b64_json"` (non supporté)
- [x] **Bug 2: Clé Gemini** - Ajout `_get_api_key_from_db()` pour charger les clés depuis SQLite
- [x] **Bug 3: OpenAI 400** - Corrigé modèle par défaut "gpt-5.2" -> "gpt-4o"

#### Feature 1: Provider Grok (xAI)
- Modèles : grok-3, grok-3-fast, grok-2
- API compatible OpenAI via api.x.ai

#### Feature 2: Conversations éphémères
- `Conversation.ephemeral?: boolean` - Flag pour conversations temporaires

#### Feature 3: Bouton + désactivé si conversation vide

---

## Session 24 janvier - Nuit (v2.3 - MCP)

#### Feature 4 : MCP (Model Context Protocol)

**Backend `src/backend/app/services/mcp_service.py`** :
- `MCPService` - Gestion des serveurs MCP (start/stop/restart)
- Transport stdio pour communication JSON-RPC
- Auto-discovery des tools via `tools/list`
- Exécution des tools via `tools/call`
- Persistance config dans `~/.therese/mcp_servers.json`

**API `src/backend/app/routers/mcp.py`** :
| Endpoint | Description |
|----------|-------------|
| `GET /api/mcp/servers` | Liste des serveurs |
| `POST /api/mcp/servers` | Ajouter un serveur |
| `POST /api/mcp/servers/{id}/start` | Démarrer |
| `POST /api/mcp/servers/{id}/stop` | Arrêter |
| `DELETE /api/mcp/servers/{id}` | Supprimer |
| `GET /api/mcp/tools` | Liste des tools disponibles |
| `POST /api/mcp/tools/call` | Exécuter un tool |
| `GET /api/mcp/presets` | Presets disponibles |
| `POST /api/mcp/presets/{id}/install` | Installer preset |

**Presets MCP inclus** : Filesystem, Fetch, Memory, Brave Search, GitHub, Notion, Slack, Google Drive

**Frontend** :
- `ToolsPanel.tsx` - Composant complet gestion MCP
- Onglet "Tools" dans SettingsModal

---

## Session 24 janvier - Suite (v2.4 - MCP Tool Calling)

#### Feature 5 : Tool Calling LLM intégré
- Nouveaux dataclasses : `ToolCall`, `ToolResult`, `StreamEvent`
- `stream_response_with_tools()` - Streaming avec support tools
- Support Claude (Anthropic) et OpenAI pour function calling
- Chaînage de tools (récursif, max 5 itérations)
- Exécution automatique des tools via MCP dans le chat

**Flux** : User envoie message -> LLM reçoit tools MCP -> LLM décide d'utiliser un tool -> backend exécute via MCP -> résultat renvoyé au LLM -> réponse finale streamée

---

## Session 24 janvier - Corrections UX (v2.5)

| Problème | Fix | Fichier |
|----------|-----|---------|
| Dossier de travail ne persiste pas | FileBrowser charge le dossier configuré au démarrage | `FileBrowser.tsx` |
| Sidebar "Mémoire" pas adapté | Renommé en "Espace de travail" | `MemoryPanel.tsx` |
| Audio non supporté message peu clair | Messages d'erreur améliorés pour Tauri + bouton désactivé | `useVoiceRecorder.ts`, `ChatInput.tsx` |
| Clés API images non visibles | Indicateurs "Clé OpenAI OK / requise" sur chaque provider image | `SettingsModal.tsx` |

---

## Session 24 janvier - Clés API Images Séparées (v2.6)

La clé API Gemini pour le LLM et celle pour Nano Banana Pro (génération d'images) peuvent être différentes. Même chose pour OpenAI.

| Provider | Clé API | Préfixe | Console |
|----------|---------|---------|---------|
| GPT Image 1.5 | `openai_image_api_key` | `sk-` | platform.openai.com |
| Nano Banana Pro | `gemini_image_api_key` | `AIza` | aistudio.google.com |

---

## Session 24 janvier - Mise à jour Modèles LLM

| Provider | Modèles disponibles |
|----------|---------------------|
| **Anthropic** | claude-sonnet-4-5-20250929, claude-haiku-4-5-20251001, claude-opus-4-5-20251101 |
| **OpenAI** | gpt-4o, gpt-4-turbo, o3, o4-mini |
| **Gemini** | gemini-3-pro-preview, gemini-3-flash-preview, gemini-2.5-pro, gemini-2.5-flash |
| **Mistral** | mistral-large-latest, codestral-latest, mistral-small-latest |
| **Grok** | grok-3, grok-3-fast |
| **Ollama** | Dynamique (modèles locaux) |

---

## Session 24 janvier - Recherche Web (v2.7)

**Deux méthodes selon le provider** :
| Provider | Méthode | Description |
|----------|---------|-------------|
| **Gemini** | Google Search Grounding | Intégré nativement via `google_search_retrieval` |
| **Claude, GPT, Mistral, Grok** | Tool calling DuckDuckGo | Tool `web_search` ajouté automatiquement |

- `src/backend/app/services/web_search.py` - Service DuckDuckGo (gratuit, sans API key)
- Toggle on/off dans Settings -> LLM -> Recherche Web

---

## Session 24 janvier - 30 User Stories Qualité (v2.8)

Implémentation de 30 User Stories couvrant 7 domaines :

#### US-ERR-01 à US-ERR-05 : Gestion d'erreurs
- `error_handler.py` - Service centralisé avec codes erreurs standardisés
- Messages d'erreur en français (TheresError)
- Retry automatique avec backoff exponentiel
- Mode dégradé si Qdrant indisponible
- Annulation génération en cours (`/api/chat/cancel/{id}`)

#### US-BAK-01 à US-BAK-05 : Backup & Données
- `data.py` router - Endpoints export/import/backup
- Export conversations JSON/Markdown
- Export complet données (sauf clés API)
- Backup quotidien automatique + restauration

#### US-SEC-01 à US-SEC-05 : Sécurité & Privacy
- Chiffrement clés API avec Fernet (cryptography)
- Export RGPD (droit de portabilité)
- Sanitization des données exportées

#### US-PERF-01 à US-PERF-05 : Performance
- `performance.py` service - StreamingMetrics, PerformanceMonitor
- Tracking first token latency (SLA < 2s)
- Memory management + search index conversations
- PowerSettings (battery saver mode)

#### US-PERS-01 à US-PERS-05 : Personnalisation
- Prompt templates CRUD
- Comportement LLM configurable (temperature, max_tokens)
- Feature visibility (masquer fonctionnalités)

#### US-ESC-01 à US-ESC-05 : Escalation & Limites
- `token_tracker.py` - Suivi consommation tokens
- Estimation coût par requête (EUR)
- Limites configurables (tokens/jour, budget/mois)
- Détection d'incertitude dans les réponses LLM

#### Tests Backend
- 103 tests passent (19 erreurs + 11 backup + 10 sécurité + 17 performance + 15 personnalisation + 16 escalation)

---

## Session 26 janvier - Tests E2E (v2.9+)

**Infrastructure de tests end-to-end avec Playwright** :

- [x] **Structure tests/e2e/** - Configuration complète
  - `conftest.py` - Fixtures (sandbox, backend, browser, page)
  - `test_onboarding.py` - 5 tests wizard
  - `test_chat.py` - 7 tests chat/messages
  - `test_guided_prompts.py` - 6 tests navigation
- [x] **Sandbox isolé** - `~/.therese-test-sandbox`
- [x] **Makefile** - `make install-e2e`, `make test-e2e`, `make test-e2e-headed`

---

## Session 27 janvier - MCP Enrichment (v3.0)

#### Phase 5 : MCP Security - Chiffrement clés API
- Backend chiffrement automatique (Fernet AES-128-CBC + HMAC)
- Clés API MCP stockées chiffrées dans `~/.therese/mcp_servers.json`
- Déchiffrement transparent au démarrage serveur

#### Phase 6-8 : MCP Presets - Tier 1/2/3
- 13 presets MCP disponibles (vs 3 avant)
  - **Tier 1** : filesystem, fetch, git, time, sequential-thinking
  - **Tier 2** : google-workspace
  - **Tier 3** : github, slack, notion, airtable, zapier, make, linear
- **EnvVarModal.tsx** - Modal professionnel saisie clés API avec validation

---

## Session 28 janvier - CRM Sync Google Sheets (v3.1)

**Synchronisation bidirectionnelle CRM depuis Google Sheets**

#### Fichiers créés
- `src/backend/app/services/sheets_service.py` - Client Google Sheets API
- `src/backend/app/services/crm_sync.py` - Service de synchronisation CRM
- `src/frontend/src/components/settings/CRMSyncPanel.tsx` - UI de sync

#### Endpoints API
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/crm/sync/config` | GET/POST | Configuration spreadsheet ID |
| `/api/crm/sync/connect` | POST | Lancer OAuth Google Sheets |
| `/api/crm/sync/callback` | GET | Callback OAuth |
| `/api/crm/sync` | POST | Lancer la synchronisation |
| `/api/crm/sync/import` | POST | Import direct JSON (bypass OAuth) |

#### Fonctionnalités
- Sync Clients, Projects, Deliverables
- 3 modes d'authentification : OAuth Google Sheets, clé API Gemini (fallback), import direct

#### Corrections 28/01/2026
- Fix double prefix router (`/api/crm/crm/` -> `/api/crm/`)
- Fix AsyncSession (`session.exec()` -> `await session.execute()`)
- Fix déchiffrement credentials OAuth depuis MCP Google Workspace
- Fix redirect_uri OAuth (port 8080 -> 8000)
- 50 contacts + 13 projets synchronisés

---

## Session 29 janvier - Sprint 2 Architecture + Performance (v3.2)

**Objectif** : Refactoring God Classes + quick wins performance.

#### Wave 1 : Quick Wins
- Embedding async (`asyncio.to_thread`)
- Reader task stderr MCP
- COUNT(*) listing conversations (N+1 fix)
- Cleanup pending requests MCP (timeout 60s)

#### Wave 2 : Refactoring Medium
- CRM Sync vers AsyncSession
- Batching updates SSE frontend (debounce)

#### Wave 3 : God Class api.ts
- Découpage api.ts en 14 modules (`src/frontend/src/services/api/`)
  - `core.ts`, `chat.ts`, `memory.ts`, `config.ts`, `files.ts`, `skills.ts`
  - `voice.ts`, `images.ts`, `board.ts`, `calculators.ts`, `mcp.ts`
  - `performance.ts`, `personalisation.ts`, `escalation.ts`, `email.ts`
  - `index.ts` (re-exports pour backward compatibility)

#### Wave 4 : God Class llm.py (-73% lignes)
- Découpage llm.py (1558 -> 417 lignes) en providers
  - `providers/base.py` - ABC BaseProvider, LLMProvider enum, StreamEvent
  - `providers/anthropic.py`, `openai.py`, `gemini.py`, `mistral.py`, `grok.py`, `ollama.py`
  - `context.py` - ContextWindow avec format converters

#### Wave 5 : HTTP Client Pool + Prompt Security
- Pool global `httpx.AsyncClient` (`http_client.py`) - 20 keepalive, 100 max
- Prompt injection mitigation (`prompt_security.py`) - Détection patterns OWASP LLM Top 10

#### Wave 6 : Keychain Protection
- macOS Keychain pour clé de chiffrement (`encryption.py`) via `keyring`
- Migration automatique fichier -> keychain

#### Tests Sprint 2
- 25 tests LLM + 31 tests encryption + 10 tests web search + 13 tests board
- **Total : 118 tests services passent**

#### Bugfixes
- Fix CORS OPTIONS (auth middleware bloquait preflight requests)
- Fix auth race condition (initializeAuth pas await avant checkOnboarding)
- Fix image download auth (endpoint ajouté aux exempt_paths)
- Fix health endpoint (/health ajouté aux exempt_paths)

---

## Session 30 janvier - Fenêtres indépendantes (v3.3)

Les 5 panels (Email, Calendrier, Tâches, Factures, CRM) s'ouvrent dans des fenêtres macOS séparées.

#### Approche technique
- `WebviewWindow` de Tauri 2.0 côté JS (pas de modif Rust)
- Chaque fenêtre charge `index.html?panel=xxx`
- Gestion singleton : si fenêtre déjà ouverte, focus au lieu de recréer
- Stores Zustand non partagés entre fenêtres

#### Points techniques importants
- **NE PAS utiliser `onCloseRequested`** sur les WebviewWindow Tauri 2.0 : ça bloque la fermeture native (croix rouge macOS). Utiliser `once('tauri://destroyed')` pour le nettoyage.
- En mode standalone, les panels chargent leurs données directement

---

## Session 30 janvier - Persistance Email/Calendrier (v3.4)

Corrections pour que les panels Email et Calendrier fonctionnent en fenêtres séparées.

1. PanelWindow pré-charge maintenant les comptes email
2. CalendarStore persiste calendars, currentCalendarId, events, lastSyncAt
3. EmailStore persiste labels, messages
4. CalendarPanel utilise selectedDate au lieu de new Date()
5. Loading state en mode standalone

**Note** : localStorage est partagé entre toutes les fenêtres Tauri (même origine)

---

## Session 2 février - MCP Connectors Brainstorm (v3.5)

**Audit des presets MCP + ajout connecteurs solopreneurs/TPE FR**

#### Audit : 5 presets supprimés
| Preset | Raison |
|--------|--------|
| git | Dev-only |
| linear | Issue tracking équipes dev |
| github | Dev-only, package déprécié |
| zapier | Package npm inexistant |
| make | Package npm inexistant |

#### Sprint 1 : 5 nouveaux presets Tier S
Brave Search, Brevo, Stripe, HubSpot CRM, Todoist

#### Sprint 2 : 5 nouveaux presets Tier A
Trello, Perplexity, Pipedrive, WhatsApp Business, Playwright

#### Sprint 3 : UI Polish
- Presets organisés par catégories (8 sections avec icônes)
- Barre de recherche/filtre
- Badge "Populaire" sur 6 presets clés
- Compteur total presets

#### Bilan presets MCP (19 total)
| Catégorie | Presets |
|-----------|---------|
| Essentiels | Filesystem, Fetch, Time |
| Productivité | Google Workspace, Notion, Airtable, Todoist, Trello |
| Recherche | Brave Search, Perplexity |
| Marketing | Brevo |
| CRM & Ventes | HubSpot CRM, Pipedrive |
| Finance | Stripe |
| Communication | WhatsApp Business |
| Avancé | Sequential Thinking, Slack, Playwright |

---

## Session 2 février - Skills Office v2 Code-Execution (v3.6)

Remplacement du pipeline LLM -> Markdown/JSON -> regex parser -> fichier par une approche code-execution : LLM -> code Python -> sandbox -> fichier.

#### Architecture
- **code_executor.py** : Module central (extraction, validation, sandbox, CodeGenSkill)
  - `extract_python_code()` : extrait le code des blocs ```python```
  - `validate_code()` : sécurité via AST + patterns bloqués
  - `execute_sandboxed()` : exécution async avec timeout 30s
  - `CodeGenSkill(BaseSkill)` : classe abstraite avec fallback automatique
- **Sandbox sécurisée** :
  - Bloqués : os, sys, subprocess, shutil, socket, requests, urllib, eval, exec, compile
  - `__import__` restreint par whitelist selon le format
  - Timeout 30 secondes via `asyncio.wait_for`

#### Points clés
- Fallback automatique : si le LLM génère du Markdown au lieu de code, l'ancien parser prend le relais
- 18 skills enregistrés et fonctionnels dans le registry

---

## Session 3 février - Skills FILE multi-modèle + fix Opus (v3.7)

**3 problèmes résolus** : titres génériques, docs vides Gemini Flash, pas d'adaptation au modèle.

#### Étape 1 : Détection capacité modèle
- `model_capability.py` - Mapping provider+modèle -> "code" ou "markdown"
  - CODE : Anthropic (*), OpenAI (*), Gemini (pro), Mistral (large, codestral), Grok (*)
  - MARKDOWN : Gemini Flash, Mistral Small, Ollama (tous)

#### Étape 2 : Prompt adaptatif
- `skills.py` - Branchement code vs markdown selon capacité modèle
- `max_tokens=8192` pour skills FILE (était 4096, causait troncature Opus)

#### Étape 3 : Prompts Markdown par generator
- Surcharges `get_markdown_prompt_addition()` par format (DOCX, PPTX, XLSX)

#### Étape 4 : Meilleurs titres
- `registry.py` - `_extract_title_from_content()` avec 24 préfixes FR/EN

#### Fix critique Opus - Réponses tronquées
- Fallback pour blocs ```python``` sans ``` fermant
- `repair_truncated_code()` - Retire les lignes incomplètes jusqu'à obtenir un AST valide
- Imports autorisés élargis (time, random, copy, string, textwrap, itertools, collections)

---

## TODO / Backlog (mis à jour 4 février 2026)

- [x] **Tool `create_contact`** : FAIT - memory_tools.py + intégration chat.py tool calling
- [x] **Tool `create_project`** : FAIT - memory_tools.py + intégration chat.py tool calling
- [x] **Tests E2E Skills** : FAIT - test_skills.py (6 tests DOCX/PPTX/XLSX)
- [x] **Tests E2E Images** : FAIT - test_images.py (6 tests GPT/Gemini)
- [x] **Packaging macOS** : PRÊT - icônes + config Tauri, `make build` fonctionne
- [x] **Cleanup MCP config** : FAIT - 3 test-servers supprimés (4 février 2026)
- [ ] **Fix test board streaming** : `test_deliberate_returns_sse_stream` (infra test)
- [ ] **Email Gmail** : Infra OAuth/Gmail faite, reste intégration router API
- [ ] **Code signing macOS** : Apple Developer + notarization pour distribution
