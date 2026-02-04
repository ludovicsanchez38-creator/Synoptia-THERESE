# CLAUDE.md - THÉRÈSE V2

> Contexte projet pour Claude Code - Ne pas supprimer

## Projet

**THÉRÈSE v2** - Alternative souveraine à Cowork (Anthropic)
- **Créateur** : Ludo Sanchez (Synoptïa)
- **Tagline** : "Ta mémoire, tes données, ton business."
- **Cible** : Solopreneurs et TPE français

### Différenciateurs vs Cowork
1. **Mémoire persistante** (Cowork n'en a pas)
2. **UX/UI premium** dark mode
3. **Souveraineté** des données (100% local)
4. **Marché français**
5. **Guided Prompts adaptés** solopreneurs/TPE (vs générique Cowork)

### Stack technique
- Frontend : Tauri 2.0 + React + TailwindCSS + Framer Motion
- Backend : Python FastAPI + UV
- Database : SQLite + Qdrant (embeddings)
- LLM : Multi-provider (Anthropic, OpenAI, Gemini, Mistral, Grok, Ollama)

### Identité visuelle
```yaml
palette:
  background: "#0B1226"
  surface: "#131B35"
  text_primary: "#E6EDF7"
  text_muted: "#B6C7DA"
  accent_cyan: "#22D3EE"
  accent_magenta: "#E11D8D"
```

---

## TODO / Backlog

- [x] **Bug génération d'images** : RESOLU - Clé Gemini image configurée (26/01/2026)
- [x] **Tests E2E automatisés** : FAIT - 18 tests Playwright (26/01/2026)
- [ ] **Tool `create_contact`** : Permettre à THÉRÈSE d'ajouter directement des contacts en mémoire via un tool
- [ ] **Tool `create_project`** : Idem pour les projets
- [ ] **Tests E2E Skills** : test_skills.py (génération DOCX/PPTX/XLSX)
- [ ] **Tests E2E Images** : test_images.py (génération GPT/Gemini)
- [ ] **Packaging macOS** : Icône + build .app + .dmg

---

## Avancement Développement

### MVP Chat - FAIT (21 janvier 2026)

**Frontend Tauri (src/frontend/)** :
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

**Backend FastAPI (src/backend/)** :
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

### Derniers fixes (session actuelle)
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
  - Testé avec succès: "Qui est Pierre?" → répond avec infos contact

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
  - Bundle principal: 1.2 MB → 303 KB (-75%)

### MVP v1.0 - COMPLET

### Session 21 janvier - UI Guided Prompts (style Cowork)
- [x] **Guided Prompts UI** - Interface guidée pour l'écran vide
  - `src/frontend/src/components/guided/` - Nouveau module complet
  - `actionData.ts` - Configuration 3 actions + 24 sous-options avec prompts
  - `ActionCard.tsx` - Cartes actions avec animations hover/tap Framer Motion
  - `SubOptionsPanel.tsx` - Panel sous-options en pills avec navigation retour
  - `GuidedPrompts.tsx` - Composant orchestrateur avec transitions AnimatePresence
  - `index.ts` - Exports module
- [x] **Intégration MessageList.tsx**
  - Remplacement état vide par `<GuidedPrompts />`
  - Prop `onPromptSelect` pour remonter le prompt sélectionné
- [x] **Intégration ChatInput.tsx**
  - Props `initialPrompt` + `onInitialPromptConsumed`
  - Auto-fill textarea avec resize et focus cursor fin
- [x] **Intégration ChatLayout.tsx**
  - État `guidedPrompt` pour câblage MessageList → ChatInput
  - Handlers `handleGuidedPromptSelect` et `handleGuidedPromptConsumed`

**Les 3 actions Synoptïa** (consolidation 25 janvier 2026) :
| Action | Icône | Sous-options (24 total) |
|--------|-------|------------------------|
| Produire | Sparkles | Email pro, Post LinkedIn, Proposition commerciale, Document Word, Présentation PPT, Tableur Excel, Image IA GPT, Image IA Gemini (8) |
| Comprendre | Brain | Fichier Excel, Document PDF, Site web, Marché, Outil IA, Concept, Best practices (7) |
| Organiser | GitBranch | Réunion, Projet, Semaine, Objectifs, Workflow n8n, Apps Script, Make, Zapier, Processus (9) |

### MVP v1.1 - COMPLET

### Session 21-22 janvier - Identité & Multi-Provider LLM (Phases 1-5)
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

### MVP v1.2 - COMPLET (Multi-Provider)

### Session 22 janvier - Skills Office (Phase 6) COMPLET
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

### MVP v1.3 - COMPLET (Skills Office)

### Session 22 janvier - UI Side Toggles
- [x] **SideToggle.tsx** - Rails latéraux pour ouvrir/fermer panels
  - Composant `src/frontend/src/components/ui/SideToggle.tsx`
  - Rails minces (10px) qui s'élargissent au hover (36px)
  - Indicateur vertical cyan (glow quand panel ouvert)
  - Animation spring Framer Motion
  - Icônes contextuelles (PanelLeftOpen/Close, PanelRightOpen/Close)
- [x] **ChatLayout.tsx** - Intégration des toggles gauche/droite
- [x] **ChatHeader.tsx** - Suppression des icônes Conversations/Mémoire (remplacées par toggles)
- [x] **Fix TS** - Correction erreurs pré-existantes (SkillExecutionPanel, SettingsModal)

**Nouvelles interactions UI** :
- Rail gauche : Ouvre ConversationSidebar (⌘B)
- Rail droit : Ouvre MemoryPanel (⌘M)
- Hover : Rail s'élargit + icône visible
- Click : Toggle le panel correspondant

### MVP v1.4 - COMPLET (Side Toggles)

### Session 22 janvier - Voice Input (Groq Whisper)
- [x] **useVoiceRecorder.ts** - Hook MediaRecorder API
  - Capture audio WebM/Opus via getUserMedia
  - États: idle → recording → processing → idle
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
  - Section "Transcription vocale" dans onglet LLM
  - Validation format clé (doit commencer par "gsk_")
  - Lien vers console.groq.com

**Configuration requise** :
- Clé API Groq (gratuit sur console.groq.com)
- Permissions micro navigateur

### MVP v1.5 - COMPLET (Voice Input)

### Session 22 janvier - Image Generation
- [x] **app/services/image_generator.py** - Service génération images
  - Support GPT Image 1.5 (OpenAI) + Nano Banana Pro (Gemini)
  - Modes: génération simple + avec image de référence
  - Sauvegarde images dans ~/.therese/images/
- [x] **app/routers/images.py** - API endpoints
  - POST /api/images/generate - Génération texte→image
  - POST /api/images/generate-with-reference - Avec image référence
  - GET /api/images/download/{id} - Téléchargement
  - GET /api/images/list - Liste des images générées
  - GET /api/images/status - Status providers disponibles
- [x] **api.ts** - Fonctions frontend
  - generateImage(), downloadGeneratedImage(), getImageStatus()
- [x] **SettingsModal.tsx** - UI sélection provider image

**Providers images supportés** :
| Provider | Modèle | Résolutions |
|----------|--------|-------------|
| GPT Image 1.5 | gpt-image-1.5 | 1024x1024, 1536x1024, 1024x1536 |
| Nano Banana Pro | gemini-3-pro-image-preview | 1K, 2K, 4K |

**Configuration requise** :
- Clé API OpenAI (pour GPT Image 1.5)
- Clé API Gemini (pour Nano Banana Pro)

### MVP v1.6 - COMPLET (Image Generation)

### Session 23 janvier - E3-05 Scope memoire + E3-06 Oubli selectif
- [x] **entities.py** - Champs scope sur Contact, Project, FileMetadata
  - `scope: str` = global | project | conversation
  - `scope_id: str | None` = ID de l'entite parente si scope
- [x] **qdrant.py** - Filtrage par scope dans search()
  - Params: `scope`, `scope_id`, `include_global`
  - Nouvelle methode `delete_by_scope()` pour suppression en cascade
- [x] **memory.py** - API endpoints avec scope
  - `list_contacts(scope, scope_id)` et `list_projects(scope, scope_id)`
  - `delete_contact(cascade=True)` et `delete_project(cascade=True)`
  - Cascade supprime projets/fichiers lies
- [x] **api.ts** - Types et fonctions frontend
  - `MemoryScope`, `ScopeFilter`, `DeleteResponse`
  - `listContactsWithScope()`, `deleteContactWithCascade()`
  - `listProjectsWithScope()`, `deleteProjectWithCascade()`
- [x] **MemoryPanel.tsx** - UI scope et suppression
  - Pills de filtrage (Tout / Global / Projet / Conv.)
  - Boutons suppression sur contacts et projets
  - Modal confirmation avec info cascade
  - Animation Framer Motion sur confirmation

### Session 23 janvier - E4-01 File Browser natif + E4-07 Analyse fichiers chat
- [x] **FileBrowser.tsx** - Navigateur fichiers natif Tauri
  - API Tauri fs (readDir, stat, homeDir)
  - Navigation breadcrumb + boutons (home, up, refresh)
  - Icones par type de fichier (code, doc, image, spreadsheet)
  - Filtrage par recherche
  - Bouton indexation vers Qdrant par fichier
  - Animations Framer Motion (stagger list)
- [x] **chat.py** - Commandes slash fichiers
  - `/fichier [chemin]` - Ajoute le contenu du fichier au contexte
  - `/analyse [chemin]` - Demande une analyse du fichier
  - Extraction texte via file_parser.py (txt, md, pdf, docx, etc.)
  - Message systeme avec contenu fichier avant envoi LLM
- [x] **ChatInput.tsx** - Parsing commandes /fichier et /analyse
  - Detection pattern `/fichier` ou `/analyse` + chemin
  - Envoi du chemin dans metadata message

**Commandes disponibles** :
- `/fichier ~/Documents/rapport.pdf` - Inclut le contenu dans le contexte
- `/analyse ~/Code/script.py` - Demande une analyse detaillee

### Session 23 janvier - E3-08 Extraction automatique d'entites
- [x] **app/services/entity_extractor.py** - Service d'extraction d'entites
  - Utilise le LLM pour extraire contacts et projets des messages
  - Prompt structure retournant du JSON
  - Seuil de confiance configurable (MIN_CONFIDENCE = 0.6)
  - Filtrage des entites deja existantes
- [x] **app/routers/chat.py** - Integration dans le streaming SSE
  - Extraction apres chaque reponse du LLM
  - Nouvel event SSE `entities_detected`
  - Helper `_get_existing_entity_names()` pour eviter les doublons
- [x] **app/models/schemas.py** - Nouveaux schemas
  - `ExtractedContactSchema` et `ExtractedProjectSchema`
  - `EntitiesDetectedResponse`
  - `StreamChunk.entities` pour le transport SSE
- [x] **EntitySuggestion.tsx** - Composant UI de confirmation
  - Affiche les entites detectees sous le message
  - Boutons "Sauvegarder" / "Ignorer" par entite
  - Animation slide-in Framer Motion
  - Appel API pour creer contact/projet
- [x] **chatStore.ts** - Gestion des entites detectees
  - `setMessageEntities()` et `clearMessageEntities()`
  - `detectedEntities` sur les messages
- [x] **MessageList.tsx** - Affichage conditionnel des suggestions
- [x] **ChatInput.tsx** - Parsing de l'event `entities_detected`
- [x] **api.ts** - Types `ExtractedContact`, `ExtractedProject`, `DetectedEntities`

**Flux de fonctionnement** :
1. Utilisateur envoie un message mentionnant une personne/projet
2. LLM repond normalement (streaming)
3. Apres la reponse, extraction d'entites en arriere-plan
4. Si entites detectees, event SSE `entities_detected`
5. UI affiche suggestion sous le message
6. Utilisateur peut sauvegarder ou ignorer chaque entite

### MVP v1.7 - COMPLET (Entity Extraction)

### Session 23 janvier - E5-08 Onboarding Wizard
- [x] **OnboardingWizard.tsx** - Composant principal wizard
  - Modal plein écran avec backdrop blur
  - Stepper 5 étapes avec indicateurs visuels
  - Transitions AnimatePresence entre étapes
  - Barre de progression en bas
- [x] **WelcomeStep.tsx** - Étape 1 : Bienvenue
  - Branding THÉRÈSE avec gradient cyan→magenta
  - 3 features highlights (Mémoire, Local, Multi-LLM)
  - Animation entrée avec stagger
- [x] **ProfileStep.tsx** - Étape 2 : Profil utilisateur
  - Formulaire : nom, surnom, entreprise, rôle, contexte
  - Import CLAUDE.md via Tauri dialog
  - Réutilise api.setProfile() et api.importClaudeMd()
- [x] **LLMStep.tsx** - Étape 3 : Configuration LLM
  - Sélection provider (Anthropic, OpenAI, Gemini, Mistral, Ollama)
  - Input clé API avec validation préfixe
  - Sélection modèle dynamique par provider
  - Badge "Recommandé" sur Anthropic
- [x] **WorkingDirStep.tsx** - Étape 4 : Dossier de travail
  - Sélection répertoire via Tauri dialog
  - Affichage chemin sélectionné
  - Option "Passer" si non nécessaire
- [x] **CompleteStep.tsx** - Étape 5 : Terminé
  - Résumé configuration (profil, LLM, dossier)
  - Animation célébration (confettis CSS)
  - Appel api.completeOnboarding()
- [x] **Backend endpoints**
  - GET `/api/config/onboarding-complete` - Status onboarding
  - POST `/api/config/onboarding-complete` - Marquer terminé
  - Stockage dans table Preferences (SQLite)
- [x] **Schemas Pydantic**
  - `OnboardingStatusResponse` - completed, completed_at
  - `OnboardingCompleteRequest` - completed flag
- [x] **api.ts** - Fonctions frontend
  - `getOnboardingStatus()` - Récupère status
  - `completeOnboarding()` - Marque terminé
- [x] **App.tsx** - Intégration
  - Check onboarding status au démarrage
  - Affiche wizard si non complété
  - Écran de chargement pendant vérification

**Fichiers créés** :
- `src/frontend/src/components/onboarding/index.ts`
- `src/frontend/src/components/onboarding/OnboardingWizard.tsx`
- `src/frontend/src/components/onboarding/WelcomeStep.tsx`
- `src/frontend/src/components/onboarding/ProfileStep.tsx`
- `src/frontend/src/components/onboarding/LLMStep.tsx`
- `src/frontend/src/components/onboarding/WorkingDirStep.tsx`
- `src/frontend/src/components/onboarding/CompleteStep.tsx`

**Fichiers modifiés** :
- `src/backend/app/routers/config.py` - Endpoints onboarding
- `src/backend/app/models/schemas.py` - Schemas onboarding
- `src/frontend/src/services/api.ts` - Fonctions API onboarding
- `src/frontend/src/App.tsx` - Intégration wizard

### MVP v1.8 - COMPLET (Onboarding Wizard)

---

## Lancer le projet

```bash
# Terminal 1 - Backend
cd src/backend
uv run uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend Tauri
cd src/frontend
npm run tauri dev
```

**URLs** :
- Frontend Tauri : http://localhost:1420
- Backend API : http://localhost:8000
- API Docs : http://localhost:8000/docs (si debug=true)

---

## BMAD Method

BMAD (Breakthrough Method for Agile AI-Driven Development) est installé.

### Documentation générée
- [x] `docs/benchmark-cowork.md` - Analyse Cowork (380 lignes)
- [x] `docs/benchmark-memoire.md` - Benchmark mémoire (567 lignes)
- [x] `docs/benchmark-ux.md` - Benchmark UX (640 lignes)
- [x] `docs/prd-therese.md` - PRD complet (639 lignes)
- [x] `docs/architecture.md` - Architecture technique (1276 lignes)
- [x] `docs/stories/` - 35 stories, 5 epics, 4 sprints (143 pts)

---

## Notes importantes

- **Cowork** = produit desktop d'Anthropic lancé 12 janvier 2026
- **Vulnérabilité connue** : prompt injection via fichiers (PromptArmor)
- **Limitation majeure Cowork** : PAS de mémoire persistante entre sessions
- **Cowork dispo** : macOS only, Max ($100-200/mois) puis Pro ($20/mois)

---

---

## Session 23 janvier - Corrections Onboarding (COMPLET)

### Audit complet par 3 agents spécialisés
**23 problèmes identifiés → 12 user stories → Toutes implémentées**

### Corrections UX/Navigation (P0)
- [x] **US-01: WorkingDirStep** - Bouton "Continuer" disabled si pas de dossier
- [x] **US-02: LLMStep** - Warning si pas de clé API + "Continuer" disabled
- [x] **US-03: CompleteStep** - Affichage erreur si finalisation échoue + bouton Réessayer
- [x] **US-04: Accents français** - Tous les accents manquants corrigés

### Accessibilité (P1)
- [x] **US-05: Labels accessibles** - Ajout `id` et `htmlFor` sur tous les inputs
- [x] **US-06: Focus visible** - Remplacement `focus:border-*` par `focus:ring-2 focus:ring-accent-cyan`
- [x] **US-07: Radios sémantiques** - Ajout `role="radiogroup"`, `role="radio"`, `aria-checked`
- [x] **US-08: ARIA modal** - Ajout `role="dialog"`, `aria-modal`, `aria-labelledby`
- [x] **US-09: Contraste placeholders** - Passage de `/50` à `/70` pour meilleure lisibilité

### Intégration Backend/Types (P2)
- [x] **US-10: Types nullable** - `UserProfile` fields en `string | null`
- [x] **US-11: Validation clés API** - Backend valide format (sk-ant-, sk-, AIza, gsk_)
- [x] **US-12: Animations unifiées** - WelcomeStep en animation horizontale (x: 50)

### Fichiers modifiés
| Fichier | Corrections |
|---------|-------------|
| `ProfileStep.tsx` | US-04, US-05, US-06, US-09 |
| `LLMStep.tsx` | US-02, US-04, US-06, US-07, US-09 |
| `WorkingDirStep.tsx` | US-01, US-04 |
| `CompleteStep.tsx` | US-03, US-04 |
| `WelcomeStep.tsx` | US-04, US-12 |
| `OnboardingWizard.tsx` | US-08 |
| `api.ts` | US-10 |
| `config.py` (backend) | US-11 |

### MVP v1.9 - COMPLET (Onboarding Polish)

### Session 26 janvier - SecurityStep Onboarding

Ajout d'une etape de securite obligatoire dans le wizard d'onboarding.

- [x] **SecurityStep.tsx** - Nouvelle etape 4/6
  - Avertissement sur les risques lies aux connexions cloud
  - Liste des 5 risques : LLMs cloud, MCP servers, fichiers, web search, transcription
  - Indicateurs de severite (high/medium/low)
  - Checkbox d'acknowledgement obligatoire
  - Liens vers documentation securite
- [x] **OnboardingWizard.tsx** - Integration SecurityStep
  - Wizard passe de 5 a 6 etapes
  - Ordre: Welcome → Profile → LLM → **Security** → WorkingDir → Complete

**Risques documentes**:
| Connexion | Severite | Description |
|-----------|----------|-------------|
| LLMs Cloud | High | Donnees envoyees aux providers |
| MCP Servers | High | Execution commandes, lecture/ecriture fichiers |
| Acces fichiers | Medium | Lecture fichiers locaux pour contexte |
| Recherche Web | Low | Requetes tracables DuckDuckGo/Google |
| Transcription | Medium | Audio envoye a Groq |

**Sources** : Best practices MCP Security 2026 (Bitdefender, Palo Alto, StackHawk)

### MVP v2.9 - COMPLET (Security Onboarding)

### Session 24 janvier - Board de Décision Stratégique (Epic 1)

Feature complète permettant de convoquer un "board" de 5 conseillers IA pour les décisions stratégiques.

#### US-BOARD-01 : Module Board créé
- [x] **BoardPanel.tsx** - Panel principal modal
  - États: input, deliberating, history, viewing
  - Question stratégique + contexte optionnel
  - Preview des 5 conseillers
  - Raccourci clavier ⌘+D
- [x] **AdvisorCard.tsx** - Carte conseiller
  - Avatar emoji, nom, couleur personnalisée
  - Badge provider LLM (Claude, GPT, Gemini...)
  - Animation streaming Framer Motion
- [x] **DeliberationView.tsx** - Vue délibération
  - Grille responsive des conseillers
  - Streaming simultané des avis
- [x] **SynthesisCard.tsx** - Carte synthèse
  - Recommandation, consensus, divergences
  - Niveau de confiance (high/medium/low)
  - Prochaines étapes suggérées

#### US-BOARD-02 : Délibération Multi-LLM
- [x] **Providers par conseiller**
  | Conseiller | Provider préféré | Raison |
  |------------|------------------|--------|
  | L'Analyste | Anthropic (Claude) | Analyse structurée |
  | Le Stratège | OpenAI (GPT) | Créativité stratégique |
  | L'Avocat du Diable | Anthropic (Claude) | Argumentation nuancée |
  | Le Pragmatique | Mistral | IA française, pragmatisme |
  | Le Visionnaire | Gemini | Vision futuriste |
- [x] **Fallback automatique** - Si provider non configuré, utilise le défaut
- [x] **Badge provider** - UI affiche le provider utilisé par chaque conseiller

#### US-BOARD-03/04 : Synthèse & Historique
- [x] **Synthèse automatique** après tous les avis
  - Points de consensus vs divergences
  - Recommandation finale avec justification
  - Niveau de confiance basé sur le consensus
  - Prochaines étapes concrètes
- [x] **Persistance SQLite** - Table `board_decisions`
  - ID, question, contexte, opinions (JSON), synthesis (JSON)
  - confidence, recommendation (dénormalisés pour queries rapides)
- [x] **API Historique**
  - `GET /api/board/decisions` - Liste des décisions
  - `GET /api/board/decisions/{id}` - Détail complet
  - `DELETE /api/board/decisions/{id}` - Suppression

#### Fichiers créés
```
src/frontend/src/components/board/
├── BoardPanel.tsx
├── AdvisorCard.tsx
├── DeliberationView.tsx
├── SynthesisCard.tsx
└── index.ts

src/backend/app/
├── models/board.py        # AdvisorRole, BoardSynthesis, etc.
├── services/board.py      # BoardService avec SQLite
└── routers/board.py       # API endpoints
```

#### Fichiers modifiés
- `ChatLayout.tsx` - Intégration BoardPanel + raccourci ⌘+D
- `useKeyboardShortcuts.ts` - Handler onToggleBoardPanel
- `ShortcutsModal.tsx` - Affichage raccourci ⌘+D
- `api.ts` - Types et fonctions Board
- `entities.py` - BoardDecisionDB SQLModel
- `llm.py` - `get_llm_service_for_provider()` pour multi-LLM

### MVP v2.0 - COMPLET (Board de Décision)

### Session 24 janvier - Calculateurs Financiers (Epic 2)

Module de calculateurs financiers et décisionnels pour les entrepreneurs.

#### Calculateurs disponibles

| Calculateur | Endpoint | Description |
|-------------|----------|-------------|
| **ROI** | `POST /api/calc/roi` | Return on Investment |
| **ICE** | `POST /api/calc/ice` | Impact × Confidence × Ease |
| **RICE** | `POST /api/calc/rice` | (Reach × Impact × Confidence) / Effort |
| **NPV** | `POST /api/calc/npv` | Net Present Value (VAN) |
| **Break-even** | `POST /api/calc/break-even` | Seuil de rentabilité |

#### Fichiers créés
- `src/backend/app/services/calculators.py` - Service de calculs
- `src/backend/app/routers/calculators.py` - API endpoints

#### Fichiers modifiés
- `routers/__init__.py` - Export calc_router
- `main.py` - Enregistrement /api/calc
- `api.ts` - Types et fonctions frontend

#### Exemples d'utilisation

```typescript
// ROI
const roi = await calculateROI(10000, 15000);
// => { roi_percent: 50, profit: 5000, interpretation: "✅ Très bon ROI..." }

// ICE (priorisation)
const ice = await calculateICE(8, 7, 6);
// => { score: 336, interpretation: "✅ Bon score ICE..." }

// RICE (priorisation produit)
const rice = await calculateRICE(1000, 2, 80, 2);
// => { score: 800, interpretation: "🚀 Score RICE exceptionnel..." }
```

### MVP v2.1 - COMPLET (Calculateurs)

### Session 24 janvier - Soir (Bugs & Features)

#### Bugs corrigés

- [x] **Bug 1: GPT Image 1.5** - Retiré `response_format="b64_json"` (paramètre non supporté)
- [x] **Bug 2: Clé Gemini** - Ajout `_get_api_key_from_db()` pour charger les clés depuis SQLite
- [x] **Bug 3: OpenAI 400** - Corrigé modèle par défaut de "gpt-5.2" vers "gpt-4o"

#### Feature 1: Provider Grok (xAI)

| Modèle | Description |
|--------|-------------|
| grok-3 | Flagship |
| grok-3-fast | Rapide |
| grok-2 | Standard |

**Fichiers modifiés** :
- `llm.py` - Enum GROK + `_stream_grok()` (API compatible OpenAI via api.x.ai)
- `config.py` - Validation clé xai-*, endpoints LLM
- `schemas.py` - `has_grok_key` dans ConfigResponse
- `SettingsModal.tsx` - Provider Grok dans la liste
- `api.ts` - Type `'grok'` dans LLMProvider

#### Feature 2: Conversations éphémères

- `Conversation.ephemeral?: boolean` - Flag pour conversations temporaires
- `createConversation(ephemeral)` - Paramètre optionnel
- `partialize` - Exclut les éphémères de la persistance localStorage

#### Feature 3: Bouton + désactivé si conversation vide

- `isCurrentConversationEmpty()` - Nouvelle fonction computed dans chatStore
- `ChatHeader.tsx` - Bouton + désactivé avec opacité réduite si conversation vide

### MVP v2.2 - COMPLET (Grok + UX)

### Session 24 janvier - Nuit (MCP Integration)

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

**Presets MCP inclus** :
- Filesystem - Gestion fichiers
- Fetch - Récupération URLs
- Memory - Mémoire persistante
- Brave Search - Recherche web
- GitHub - Accès repos
- Notion - Workspace Notion
- Slack - Workspace Slack
- Google Drive - Fichiers Drive

**Frontend** :
- `ToolsPanel.tsx` - Composant complet gestion MCP
- Onglet "Tools" dans SettingsModal
- UI : liste serveurs, presets, status, tools

### MVP v2.3 - COMPLET (MCP)

### Session 24 janvier - Suite (MCP Tool Calling Integration)

#### Feature 5 : Tool Calling LLM intégré

**Objectif** : Permettre au LLM d'utiliser automatiquement les tools MCP pendant la conversation.

**Backend `src/backend/app/services/llm.py`** :
- Nouveaux dataclasses : `ToolCall`, `ToolResult`, `StreamEvent`
- `stream_response_with_tools()` - Streaming avec support tools
- `_stream_anthropic_with_tools()` - Gère les tool_use blocks Claude
- `_stream_openai_with_tools()` - Gère les tool_calls OpenAI
- `continue_with_tool_results()` - Continue après exécution des tools
- Support chaînage de tools (récursif, max 5 itérations)

**Backend `src/backend/app/routers/chat.py`** :
- `_stream_response()` modifié pour tool calling
- `_execute_tools_and_continue()` - Exécute tools MCP et continue
- Intégration automatique des tools disponibles depuis MCPService
- Affichage status et résultats dans le stream SSE

**Frontend** :
- `StreamChunk.type` étendu : 'status' | 'tool_result'
- `ChatInput.tsx` - Gestion des événements status/tool_result
- Affichage du statut d'exécution des tools dans l'activité

**Flux de fonctionnement** :
1. User envoie un message
2. LLM reçoit la liste des tools MCP disponibles
3. LLM peut décider d'utiliser un tool (stop_reason: "tool_calls")
4. Backend exécute le tool via MCPService
5. Résultat envoyé au LLM pour continuation
6. LLM génère la réponse finale (ou utilise d'autres tools)
7. Réponse streamée au frontend

**Fichiers modifiés** :
| Fichier | Modifications |
|---------|--------------|
| `llm.py` | +ToolCall, +ToolResult, +StreamEvent, +stream_response_with_tools, +continue_with_tool_results |
| `chat.py` | +_execute_tools_and_continue, streaming avec tools |
| `schemas.py` | StreamChunk.type += 'status', 'tool_result' |
| `api.ts` | StreamChunk.type mis à jour |
| `ChatInput.tsx` | Gestion status/tool_result |

### MVP v2.4 - COMPLET (MCP Tool Calling)

---

## Récapitulatif des fonctionnalités (MVP v2.4)

### Chat & Conversations
- [x] Chat avec LLM multi-provider (Anthropic, OpenAI, Gemini, Mistral, Grok, Ollama)
- [x] Conversations éphémères (non persistées)
- [x] Streaming SSE des réponses
- [x] Conversations persistées SQLite
- [x] Sidebar conversations avec groupement par date
- [x] Commandes slash (/fichier, /analyse)

### Mémoire
- [x] Contacts et Projets avec CRUD complet
- [x] Embeddings Qdrant (nomic-embed-text)
- [x] Recherche hybride BM25 + sémantique
- [x] Injection contexte auto dans LLM
- [x] Scope (global, project, conversation)

### Fichiers
- [x] Drag & Drop avec indexation Qdrant
- [x] File Browser natif Tauri
- [x] Support: txt, md, json, py, js, ts, html, css

### Skills Office (v2 code-execution)
- [x] Génération DOCX (python-docx) - code-execution + fallback legacy
- [x] Génération PPTX (python-pptx) - code-execution + fallback legacy
- [x] Génération XLSX (openpyxl) - code-execution + fallback legacy
- [x] Sandbox sécurisée (imports restreints, timeout 30s, patterns bloqués)

### Board de Décision (nouveau v2.0)
- [x] 5 conseillers IA avec personnalités distinctes
- [x] Multi-LLM par conseiller (Claude, GPT, Gemini, Mistral)
- [x] Synthèse automatique avec consensus/divergences
- [x] Historique SQLite des décisions
- [x] Raccourci ⌘+D

### Calculateurs (nouveau v2.1)
- [x] ROI (Return on Investment)
- [x] ICE (Impact, Confidence, Ease)
- [x] RICE (Reach, Impact, Confidence, Effort)
- [x] NPV (Net Present Value)
- [x] Break-even (Seuil de rentabilité)

### Onboarding
- [x] Wizard 5 étapes au premier lancement
- [x] Import profil depuis CLAUDE.md
- [x] Configuration LLM guidée

### UI/UX
- [x] Dark mode premium (charte Synoptïa)
- [x] Animations Framer Motion
- [x] Guided Prompts (3 actions × 24 options)
- [x] Side Toggles latéraux
- [x] Input vocal (Groq Whisper)

### MCP & Tool Calling (v2.3/v2.4/v3.5)
- [x] Service MCP avec transport stdio
- [x] Gestion serveurs (start/stop/restart)
- [x] Auto-discovery tools
- [x] 19 presets organises en 8 categories metier
- [x] Onglet Tools dans Settings avec recherche et categories
- [x] API complète /api/mcp/*
- [x] Chiffrement cles API MCP (Fernet + macOS Keychain)
- [x] **Tool Calling LLM intégré** (v2.4)
  - [x] Auto-discovery tools MCP dans le chat
  - [x] Support Claude (Anthropic) et OpenAI pour function calling
  - [x] Exécution automatique des tools via MCP
  - [x] Continuation de conversation avec résultats des tools
  - [x] Chaînage de tools (max 5 itérations)
  - [x] Affichage status tool execution dans l'UI

### MVP v2.4 - COMPLET (MCP Tool Calling)

### Session 24 janvier - Corrections UX (suite)

#### Fixes apportés

| Problème | Fix | Fichier |
|----------|-----|---------|
| Dossier de travail ne persiste pas | FileBrowser charge maintenant le dossier configuré au démarrage | `FileBrowser.tsx` |
| Sidebar "Mémoire" pas adapté | Renommé en "Espace de travail" | `MemoryPanel.tsx` |
| Audio non supporté message peu clair | Messages d'erreur améliorés pour Tauri + bouton désactivé | `useVoiceRecorder.ts`, `ChatInput.tsx` |
| Clés API images non visibles | Indicateurs "Clé OpenAI OK / requise" sur chaque provider image | `SettingsModal.tsx` |

**Détails techniques** :

1. **FileBrowser.tsx** :
   - Appel `getWorkingDirectory()` au mount avant de tomber sur `homeDir()`
   - Si un dossier de travail est configuré et existe, il est utilisé

2. **MemoryPanel.tsx** :
   - Titre "Memoire" → "Espace de travail" (plus neutre pour les 3 tabs)

3. **useVoiceRecorder.ts** / **ChatInput.tsx** :
   - Détection Tauri WebView (`__TAURI__` in window)
   - Messages spécifiques : "La dictée vocale n'est pas disponible dans l'application desktop"
   - `voiceSupported` state pour désactiver le bouton micro proprement
   - Tooltip "Dictée vocale non disponible (prochainement)"

4. **SettingsModal.tsx** :
   - `IMAGE_PROVIDERS` enrichi avec `requiredApiKey` et `keyName`
   - Badges verts "Clé OpenAI OK" ou jaunes "Clé Gemini requise" sur chaque provider
   - Texte explicatif sous la section

### MVP v2.5 - COMPLET (UX Fixes)

### Session 24 janvier - Clés API Images Séparées

#### Feature : Clés API dédiées pour la génération d'images

La clé API Gemini pour le LLM et celle pour Nano Banana Pro (génération d'images) peuvent être différentes. Même chose pour OpenAI (chat vs GPT Image 1.5).

**Modifications backend** :
- `schemas.py` : Ajout `has_openai_image_key` et `has_gemini_image_key` dans ConfigResponse
- `config.py` : Vérification et retour des status des clés image séparées
- `image_generator.py` : Recherche `openai_image_api_key` / `gemini_image_api_key` en priorité

**Modifications frontend** :
- `api.ts` : `getApiKeys()` retourne `openai_image` et `gemini_image`
- `SettingsModal.tsx` :
  - Nouveau format `IMAGE_PROVIDERS` avec `apiKeyId`, `keyPrefix`, `consoleUrl`
  - Champs de saisie dédiés pour chaque clé image
  - Status visuel par provider (vert OK / jaune requis)
  - Liens vers les consoles respectives

**Configuration requise** :
| Provider | Clé API | Préfixe | Console |
|----------|---------|---------|---------|
| GPT Image 1.5 | `openai_image_api_key` | `sk-` | platform.openai.com |
| Nano Banana Pro | `gemini_image_api_key` | `AIza` | aistudio.google.com |

### MVP v2.6 - COMPLET (Clés Images Séparées)

### Session 24 janvier - Mise à jour Modèles LLM

#### Mise à jour des modèles disponibles (janvier 2026)

Tous les modèles LLM ont été mis à jour vers les versions actuelles.

| Provider | Modèles disponibles |
|----------|---------------------|
| **Anthropic** | claude-sonnet-4-5-20250929, claude-haiku-4-5-20251001, claude-opus-4-5-20251101 |
| **OpenAI** | gpt-4o, gpt-4-turbo, o3, o4-mini |
| **Gemini** | gemini-3-pro-preview, gemini-3-flash-preview, gemini-2.5-pro, gemini-2.5-flash |
| **Mistral** | mistral-large-latest, codestral-latest, mistral-small-latest |
| **Grok** | grok-3, grok-3-fast |
| **Ollama** | Dynamique (modèles locaux) |

**Fichiers modifiés** :
- `config.py` - `available_models` pour chaque provider
- `llm.py` - `_default_config()` et `get_llm_service_for_provider()`
- `SettingsModal.tsx` - Array PROVIDERS avec nouveaux modèles
- `LLMStep.tsx` - Onboarding avec modèles à jour

### Session 24 janvier - Recherche Web pour LLMs

#### Feature : Web Search intégré

Les LLMs peuvent maintenant rechercher sur le web à la demande de l'utilisateur.

**Deux méthodes selon le provider** :

| Provider | Méthode | Description |
|----------|---------|-------------|
| **Gemini** | Google Search Grounding | Intégré nativement via `google_search_retrieval` |
| **Claude, GPT, Mistral, Grok** | Tool calling DuckDuckGo | Tool `web_search` ajouté automatiquement |

**Fichiers créés** :
- `src/backend/app/services/web_search.py` - Service DuckDuckGo (gratuit, sans API key)
  - `WebSearchService` - Client async DuckDuckGo HTML
  - `SearchResult`, `SearchResponse` - Dataclasses résultats
  - `WEB_SEARCH_TOOL` - Définition tool pour function calling
  - `execute_web_search()` - Exécution du tool

**Fichiers modifiés** :

| Fichier | Modifications |
|---------|---------------|
| `llm.py` | `_stream_gemini()` avec `google_search_retrieval` grounding (dynamic_threshold: 0.3) |
| `chat.py` | Import `WEB_SEARCH_TOOL`, ajout conditionnel aux tools, exécution dans `_execute_tools_and_continue()` |
| `config.py` | Endpoints `GET/POST /api/config/web-search`, préférence `web_search_enabled` |
| `schemas.py` | `web_search_enabled: bool` dans `ConfigResponse` |
| `api.ts` | `getWebSearchStatus()`, `setWebSearchEnabled()`, types `WebSearchStatus` |
| `SettingsModal.tsx` | Toggle "Recherche Web" avec explications par provider |

**API Endpoints** :
| Endpoint | Description |
|----------|-------------|
| `GET /api/config/web-search` | Status et configuration recherche web |
| `POST /api/config/web-search?enabled=true` | Activer/désactiver la recherche |

**Comportement** :
- Gemini : Grounding automatique si le modèle détecte un besoin de recherche (threshold 0.3)
- Autres : Le LLM peut appeler le tool `web_search` quand l'utilisateur demande des infos actuelles
- Toggle dans Settings → LLM → Recherche Web

### MVP v2.7 - COMPLET (Web Search)

### Session 24 janvier - 30 Nouvelles User Stories (Phases 12-18)

Implémentation de 30 User Stories couvrant 7 nouveaux domaines :

#### US-ERR-01 à US-ERR-05 : Gestion d'erreurs
- [x] `error_handler.py` - Service centralisé avec codes erreurs standardisés
- [x] Messages d'erreur en français (TheresError)
- [x] Retry automatique avec backoff exponentiel
- [x] Mode dégradé si Qdrant indisponible (ServiceStatus singleton)
- [x] Annulation génération en cours (`/api/chat/cancel/{id}`)
- [x] Classification erreurs LLM (contexte trop long, rate limit, auth)

#### US-BAK-01 à US-BAK-05 : Backup & Données
- [x] `data.py` router - Endpoints export/import/backup
- [x] Export conversations JSON/Markdown
- [x] Export complet données (sauf clés API)
- [x] Backup quotidien automatique
- [x] Restauration depuis backup

#### US-SEC-01 à US-SEC-05 : Sécurité & Privacy
- [x] Chiffrement clés API avec Fernet (cryptography)
- [x] Export RGPD (droit de portabilité)
- [x] Sanitization des données exportées (pas de secrets)

#### US-PERF-01 à US-PERF-05 : Performance
- [x] `performance.py` service - StreamingMetrics, PerformanceMonitor
- [x] Tracking first token latency (SLA < 2s)
- [x] Memory management avec cleanup callbacks
- [x] Search index in-memory pour conversations
- [x] PowerSettings (battery saver mode)
- [x] `performance.py` router - `/api/perf/*` endpoints

#### US-PERS-01 à US-PERS-05 : Personnalisation
- [x] `personalisation.py` router - Templates, comportement LLM
- [x] `personalisationStore.ts` - Zustand store frontend
- [x] Prompt templates CRUD
- [x] Comportement LLM configurable (temperature, max_tokens)
- [x] Feature visibility (masquer fonctionnalités)

#### US-ESC-01 à US-ESC-05 : Escalation & Limites
- [x] `token_tracker.py` - Suivi consommation tokens
- [x] Estimation coût par requête (EUR)
- [x] Limites configurables (tokens/jour, budget/mois)
- [x] Historique usage (daily/monthly)
- [x] Détection d'incertitude dans les réponses LLM
- [x] `escalation.py` router - `/api/escalation/*` endpoints

#### UI Onglets Settings
- [x] Onglet Performance (métriques, memory, battery saver)
- [x] Onglet Limites (usage, coûts, configuration limites)

#### Tests Backend
- [x] `test_error_handling.py` - 19 tests
- [x] `test_backup.py` - 11 tests
- [x] `test_services_security.py` - 10 tests
- [x] `test_performance.py` - 17 tests
- [x] `test_personalisation.py` - 15 tests
- [x] `test_escalation.py` - 16 tests
- [x] **Total : 103 tests passent**

### MVP v2.8 - COMPLET (30 User Stories Qualité)

---

## Récapitulatif des fonctionnalités (MVP v2.8)

### Chat & Conversations
- [x] Chat avec LLM multi-provider (Anthropic, OpenAI, Gemini, Mistral, Grok, Ollama)
- [x] Conversations éphémères (non persistées)
- [x] Streaming SSE des réponses
- [x] Conversations persistées SQLite
- [x] Sidebar conversations avec groupement par date
- [x] Commandes slash (/fichier, /analyse)

### Mémoire
- [x] Contacts et Projets avec CRUD complet
- [x] Embeddings Qdrant (nomic-embed-text)
- [x] Recherche hybride BM25 + sémantique
- [x] Injection contexte auto dans LLM
- [x] Scope (global, project, conversation)

### Fichiers
- [x] Drag & Drop avec indexation Qdrant
- [x] File Browser natif Tauri
- [x] Support: txt, md, json, py, js, ts, html, css

### Skills Office (v2 code-execution)
- [x] Génération DOCX (python-docx) - code-execution + fallback legacy
- [x] Génération PPTX (python-pptx) - code-execution + fallback legacy
- [x] Génération XLSX (openpyxl) - code-execution + fallback legacy
- [x] Sandbox sécurisée (imports restreints, timeout 30s, patterns bloqués)

### Board de Décision
- [x] 5 conseillers IA avec personnalités distinctes
- [x] Multi-LLM par conseiller (Claude, GPT, Gemini, Mistral)
- [x] Synthèse automatique avec consensus/divergences
- [x] Historique SQLite des décisions
- [x] Raccourci ⌘+D

### Calculateurs Financiers
- [x] ROI (Return on Investment)
- [x] ICE (Impact, Confidence, Ease)
- [x] RICE (Reach, Impact, Confidence, Effort)
- [x] NPV (Net Present Value)
- [x] Break-even (Seuil de rentabilité)

### Onboarding
- [x] Wizard 5 étapes au premier lancement
- [x] Import profil depuis CLAUDE.md
- [x] Configuration LLM guidée

### UI/UX
- [x] Dark mode premium (charte Synoptïa)
- [x] Animations Framer Motion
- [x] Guided Prompts (3 actions × 24 options)
- [x] Side Toggles latéraux
- [x] Input vocal (Groq Whisper)

### MCP & Tool Calling
- [x] Service MCP avec transport stdio
- [x] Gestion serveurs (start/stop/restart)
- [x] Auto-discovery tools
- [x] Presets prédéfinis (filesystem, fetch, notion, github...)
- [x] Onglet Tools dans Settings
- [x] API complète /api/mcp/*
- [x] Tool Calling LLM intégré
  - [x] Auto-discovery tools MCP dans le chat
  - [x] Support Claude (Anthropic) et OpenAI pour function calling
  - [x] Exécution automatique des tools via MCP
  - [x] Continuation de conversation avec résultats des tools
  - [x] Chaînage de tools (max 5 itérations)
  - [x] Affichage status tool execution dans l'UI

### Génération d'Images
- [x] GPT Image 1.5 (OpenAI)
- [x] Nano Banana Pro (Gemini)
- [x] Clés API séparées pour images
- [x] Téléchargement et prévisualisation

### Recherche Web
- [x] Gemini : Google Search Grounding natif
- [x] Autres LLMs : Tool DuckDuckGo (gratuit, sans API)
- [x] Toggle on/off dans Settings
- [x] Détection automatique du besoin de recherche

### Gestion d'Erreurs (nouveau v2.8)
- [x] Messages d'erreur en français
- [x] Retry automatique avec backoff
- [x] Mode dégradé si services indisponibles
- [x] Annulation génération en cours
- [x] Classification erreurs LLM

### Backup & Données (nouveau v2.8)
- [x] Export conversations JSON/Markdown
- [x] Export complet données RGPD
- [x] Backup automatique quotidien
- [x] Restauration depuis backup

### Performance (nouveau v2.8)
- [x] Tracking first token latency
- [x] Memory management avec cleanup
- [x] Search index conversations
- [x] Battery saver mode

### Limites & Coûts (nouveau v2.8)
- [x] Suivi consommation tokens
- [x] Estimation coût par requête
- [x] Limites configurables
- [x] Historique usage
- [x] Détection d'incertitude LLM
- [x] Affichage coût et tokens par message dans le chat (US-ESC-02)
- [x] Indicateur de confiance sur les réponses IA (US-ESC-01)

---

*Dernière mise à jour : 24 janvier 2026 - MVP v2.8 (103 tests, 30 User Stories Qualité, Intégration Chat complète)*

### Session 26 janvier - Tests E2E automatisés (COMPLET)

**Infrastructure de tests end-to-end avec Playwright** :

- [x] **Structure tests/e2e/** - Configuration complète
  - `conftest.py` - Fixtures (sandbox, backend, browser, page)
  - `test_onboarding.py` - 5 tests wizard
  - `test_chat.py` - 7 tests chat/messages
  - `test_guided_prompts.py` - 6 tests navigation
  - Screenshots automatiques pour debug
  
- [x] **Sandbox isolé** - `~/.therese-test-sandbox`
  - Variable env `THERESE_DATA_DIR` pour isolation
  - Reset DB entre chaque test
  - N'affecte pas `~/.therese` principal

- [x] **Makefile amélioré** - Commandes E2E
  - `make install-e2e` - Install Playwright + dépendances
  - `make test-e2e` - Tests headless (CI)
  - `make test-e2e-headed` - Tests avec navigateur visible
  - `make reset-sandbox` - Reset environnement test
  - `make reset-onboarding` - Reset wizard pour tests

**Tests implémentés (18 total)** :

| Fichier | Tests | Description |
|---------|-------|-------------|
| `test_onboarding.py` | 5 | Wizard 6 étapes, validation champs, navigation |
| `test_chat.py` | 7 | Envoi/réception, streaming, shortcuts, persistence |
| `test_guided_prompts.py` | 6 | Navigation actions, sous-options, animations |

**Commandes rapides** :
```bash
# Installation
make install-e2e

# Lancer les tests (mode visible pour debug)
make test-e2e-headed

# Test spécifique
uv run pytest tests/e2e/test_onboarding.py::test_onboarding_wizard_complete_flow -v
```

**TODO tests** :
- [ ] test_skills.py - Génération documents Office
- [ ] test_images.py - Génération images
- [ ] test_memory.py - CRUD contacts/projets
- [ ] test_board.py - Board de décision

### MVP v2.9+ - COMPLET (Tests E2E Ready)

### Session 27 janvier - MCP Enrichment (Phases 5-8 du plan)

**Implémentation complète de la sécurisation MCP et enrichissement presets**

#### Phase 5 : MCP Security - Chiffrement clés API ✅
- [x] **Backend chiffrement automatique**
  - `mcp.py` - `create_server()` et `update_server()` chiffrent les env vars
  - `mcp_service.py` - `start_server()` déchiffre les env vars au démarrage
  - Utilisation service `encryption.py` existant (Fernet AES-128-CBC + HMAC)
  - Détection auto valeurs chiffrées (préfixe `gAAAAA`)
- [x] **Sécurité renforcée**
  - Clés API MCP stockées chiffrées dans `~/.therese/mcp_servers.json`
  - Déchiffrement transparent au démarrage serveur
  - Gestion erreurs de déchiffrement (fallback valeur chiffrée)

#### Phase 6-8 : MCP Presets - Tier 1/2/3 ✅
- [x] **13 presets MCP disponibles** (vs 3 avant)
  - **Tier 1 (5 presets sans clé)** : filesystem, fetch, git, time, sequential-thinking
  - **Tier 2 (1 preset Google)** : google-workspace
  - **Tier 3 (7 presets externes)** : github, slack, notion, airtable, zapier, make, linear
- [x] **EnvVarModal.tsx** - Modal professionnel saisie clés API
  - Validation préfixe en temps réel (ex: GITHUB_TOKEN → ghp_)
  - Boutons show/hide par champ
  - Indicateurs visuels (✓ vert si valide, ⚠️ rouge si erreur)
  - Liens directs vers consoles providers (9 providers configurés)
  - Bouton "Installer" disabled tant que pas toutes les clés
- [x] **ToolsPanel.tsx** - Intégration modal
  - Remplacement `prompt()` basique par EnvVarModal
  - Flux UX amélioré pour installation presets

**Fichiers créés** :
- `src/frontend/src/components/settings/EnvVarModal.tsx` (258 lignes)
- `IMPLEMENTATION_PHASE5-8.md` - Documentation complète

**Fichiers modifiés** :
- `src/backend/app/routers/mcp.py` - PRESET_SERVERS étendu à 13 presets, chiffrement
- `src/backend/app/services/mcp_service.py` - Déchiffrement au démarrage
- `src/frontend/src/components/settings/ToolsPanel.tsx` - Intégration EnvVarModal

**Tests à effectuer** :
```bash
# Backend
cd src/backend && uv run uvicorn app.main:app --reload --port 8000

# Frontend
cd src/frontend && npm run tauri dev

# Checklist
1. Settings → Tools → Presets (13 presets affichés)
2. Installer preset Tier 1 (fetch) → Sans clé, direct
3. Installer preset Tier 3 (notion) → Modal avec validation
4. Vérifier chiffrement dans ~/.therese/mcp_servers.json (gAAAAA...)
```

**Prochaine étape recommandée** : Tester Phases 5-8 avant d'attaquer Phase 1 (Email Gmail - 5-7 jours)

### MVP v3.0 - COMPLET (MCP Enrichment)

### Session 28 janvier - CRM Sync Google Sheets

**Synchronisation bidirectionnelle CRM depuis Google Sheets** (Google Sheets = source de vérité)

#### Fichiers créés
- `src/backend/app/services/sheets_service.py` - Client Google Sheets API
- `src/backend/app/services/crm_sync.py` - Service de synchronisation CRM
- `src/frontend/src/components/settings/CRMSyncPanel.tsx` - UI de sync

#### Fichiers modifiés
- `src/backend/app/services/oauth.py` - Ajout GSHEETS_SCOPES
- `src/backend/app/routers/crm.py` - Endpoints sync (/api/crm/sync/*)
- `src/backend/app/models/schemas.py` - Schemas CRM sync
- `src/frontend/src/services/api.ts` - Fonctions API CRM sync
- `src/frontend/src/components/settings/SettingsModal.tsx` - Integration CRMSyncPanel

#### Endpoints API
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/crm/sync/config` | GET | Configuration actuelle |
| `/api/crm/sync/config` | POST | Configurer spreadsheet ID |
| `/api/crm/sync/connect` | POST | Lancer OAuth Google Sheets |
| `/api/crm/sync/callback` | GET | Callback OAuth |
| `/api/crm/sync` | POST | Lancer la synchronisation (via API Google) |
| `/api/crm/sync/import` | POST | Import direct des données JSON (bypass OAuth) |

#### Fonctionnalités
- **Sync Clients** : ID, Nom, Entreprise, Email, Tel, Source, Stage, Score, Tags
- **Sync Projects** : ID, ClientID, Name, Description, Status, Budget
- **Sync Deliverables** : ID, ProjectID, Title, Description, Status, DueDate

#### Authentification
1. **OAuth Google Sheets** (prioritaire) - Nécessite credentials Google + redirect_uri autorisé
2. **Clé API Gemini** (fallback) - Uniquement pour spreadsheets publics/partagés
3. **Import direct** (nouveau) - Via MCP Claude Code quand OAuth non disponible

#### Configuration
- Spreadsheet ID par défaut : `1gXhiy43tvaDW0Y9FEGPmfB7BBCbUCOl_Xb6nkWtnnUk` (CRM Synoptia)
- Redirect URI OAuth : `http://localhost:8000/api/crm/sync/callback`
- Accessible dans Settings → Données → Synchronisation CRM

#### Corrections 28/01/2026
- Fix double prefix router (`/api/crm/crm/` → `/api/crm/`)
- Fix AsyncSession (`session.exec()` → `await session.execute()`)
- Fix déchiffrement credentials OAuth depuis MCP Google Workspace
- Fix redirect_uri OAuth (port 8080 → 8000)
- Ajout endpoint `/api/crm/sync/import` pour bypass OAuth

#### Statut synchronisation (28/01/2026)
- 50 contacts en base
- 13 projets en base
- Sync fonctionnel via endpoint import

### MVP v3.1 - COMPLET (CRM Sync)

### Session 29 janvier - Sprint 2 Architecture + Performance (COMPLET)

**Objectif** : Refactoring God Classes + quick wins performance.

#### Wave 1 : Quick Wins (4 tâches S)
- [x] **PERF-2.5** : Embedding async (`asyncio.to_thread`)
- [x] **PERF-2.8** : Reader task stderr MCP
- [x] **PERF-2.9** : COUNT(*) listing conversations (N+1 fix)
- [x] **PERF-2.14** : Cleanup pending requests MCP (timeout 60s)

#### Wave 2 : Refactoring Medium
- [x] **PERF-2.4** : CRM Sync vers AsyncSession
- [x] **PERF-2.7** : Batching updates SSE frontend (debounce)

#### Wave 3 : God Class api.ts
- [x] **PERF-2.2** : Decoupage api.ts en 14 modules (`src/frontend/src/services/api/`)
  - `core.ts`, `chat.ts`, `memory.ts`, `config.ts`, `files.ts`, `skills.ts`
  - `voice.ts`, `images.ts`, `board.ts`, `calculators.ts`, `mcp.ts`
  - `performance.ts`, `personalisation.ts`, `escalation.ts`, `email.ts`
  - `index.ts` (re-exports pour backward compatibility)

#### Wave 4 : God Class llm.py (-73% lignes)
- [x] **PERF-2.1** : Decoupage llm.py (1558 -> 417 lignes) en providers
  - `providers/base.py` - ABC BaseProvider, LLMProvider enum, StreamEvent
  - `providers/anthropic.py` - Claude API streaming + tools
  - `providers/openai.py` - GPT API streaming + tools
  - `providers/gemini.py` - Gemini API + Google Search grounding
  - `providers/mistral.py` - Mistral API streaming
  - `providers/grok.py` - Grok API streaming (OpenAI-compatible)
  - `providers/ollama.py` - Ollama local streaming
  - `context.py` - ContextWindow avec format converters

#### Wave 5 : HTTP Client Pool + Prompt Security
- [x] **PERF-2.6** : Pool global `httpx.AsyncClient` (`http_client.py`)
  - 20 keepalive connections, 100 max, 30s expiry
  - Cleanup automatique au shutdown (`close_http_client()`)
- [x] **PERF-2.11** : Prompt injection mitigation (`prompt_security.py`)
  - Detection patterns OWASP LLM Top 10
  - ThreatLevel: NONE/LOW/MEDIUM/HIGH/CRITICAL
  - Integration dans chat.py (bloque HIGH/CRITICAL)

#### Wave 6 : Keychain Protection
- [x] **PERF-2.10** : macOS Keychain pour cle de chiffrement (`encryption.py`)
  - `keyring` library (service: therese-app, account: encryption-key)
  - Migration automatique fichier -> keychain
  - Fallback fichier si keychain indisponible

#### Tests Sprint 2
- [x] 25 tests LLM (providers, ContextWindow, StreamEvent, ToolCall)
- [x] 31 tests encryption (chiffrement, keychain, rotation cles)
- [x] 10 tests web search (corrigés - format OpenAI function calling)
- [x] 13/14 tests board (corrigés - noms roles)
- [x] **Total : 118 tests services passent**

#### Bugfixes Session 29 janvier
- [x] **Fix CORS OPTIONS** : Auth middleware bloquait les preflight requests
  - Ajout `if request.method == "OPTIONS": return await call_next(request)`
- [x] **Fix auth race condition** : `initializeAuth()` n'etait pas await avant `checkOnboarding()`
  - Refactoring App.tsx : sequentiel `await initializeAuth()` puis `getOnboardingStatus()`
- [x] **Fix image download auth** : Endpoint `/api/images/download` ajouté aux exempt_paths
- [x] **Fix health endpoint** : `/health` ajouté aux exempt_paths (en plus de `/api/health`)
- [x] **Fix web search tests** : WEB_SEARCH_TOOL format OpenAI (nested `function`), SearchResponse `total_results`
- [x] **Fix board tests** : Roles `devil`/`pragmatic` (pas `devils_advocate`/`pragmatist`), accent "Stratège"

### MVP v3.2 - COMPLET (Sprint 2 Architecture + Performance)

### Session 30 janvier - Fenetres independantes pour panels

Les 5 panels (Email, Calendrier, Taches, Factures, CRM) s'ouvrent maintenant dans des fenetres macOS separees au lieu de modals overlay. La fenetre principale (chat) reste intacte.

#### Approche technique
- `WebviewWindow` de Tauri 2.0 cote JS (pas de modif Rust)
- Chaque fenetre charge `index.html?panel=xxx` et affiche le composant en mode standalone
- Gestion singleton : si fenetre deja ouverte, focus au lieu de recreer
- Stores Zustand non partages entre fenetres (chaque fenetre fait ses propres appels API)

#### Fichiers crees
| Fichier | Description |
|---------|-------------|
| `src/frontend/src/services/windowManager.ts` | `openPanelWindow()`, singleton, cleanup via `tauri://destroyed` |
| `src/frontend/src/components/panels/PanelWindow.tsx` | Wrapper standalone - init auth + affiche le bon panel |

#### Fichiers modifies
| Fichier | Modification |
|---------|-------------|
| `App.tsx` | Detecte `?panel=xxx` dans l'URL, affiche `PanelWindow` au lieu de `ChatLayout` |
| `ChatLayout.tsx` | 5 toggle handlers -> `openPanelWindow()`, suppression rendu modal des panels |
| `EmailPanel.tsx` | Prop `standalone`, chargement comptes en mode standalone |
| `CalendarPanel.tsx` | Prop `standalone`, chargement comptes email si pas dispo |
| `TasksPanel.tsx` | Prop `standalone`, `effectiveOpen` pour chargement |
| `InvoicesPanel.tsx` | Prop `standalone`, `effectiveOpen` pour chargement |
| `CRMPanel.tsx` | Prop `standalone`, `effectiveOpen` pour chargement |
| `capabilities/default.json` | `"panel-*"` dans windows, `core:webview:allow-create-webview-window` |
| `tauri.conf.json` | `http://127.0.0.1:8000` ajoute a la CSP |

#### Points techniques importants
- **NE PAS utiliser `onCloseRequested`** sur les WebviewWindow Tauri 2.0 : ca bloque la fermeture native (croix rouge macOS). Utiliser `once('tauri://destroyed')` pour le nettoyage.
- En mode standalone, les panels chargent leurs donnees directement (pas besoin de l'etat `isOpen` du store)
- Les raccourcis clavier ouvrent aussi les fenetres separees

### MVP v3.3 - COMPLET (Fenetres independantes)

### Session 30 janvier - suite - Persistance Email/Calendrier

Corrections pour que les panels Email et Calendrier fonctionnent correctement
en fenetres separees avec donnees persistantes.

#### Problemes identifies et corriges

1. **PanelWindow ne pre-chargeait pas les comptes email** : Pour Email/Calendrier,
   les comptes doivent etre disponibles AVANT que le panel monte. PanelWindow
   appelle maintenant `getEmailAuthStatus()` et peuple le `emailStore` avant
   d'afficher le panel.

2. **CalendarStore ne persistait presque rien** : Seuls `viewMode` et `showCancelled`
   etaient persistes. Maintenant persiste aussi : `calendars`, `currentCalendarId`,
   `events`, `lastSyncAt`.

3. **EmailStore ne persistait pas labels/messages** : Ajout de `labels` et `messages`
   dans le partialize pour un affichage instantane au reopening.

4. **CalendarPanel loadEvents() utilisait new Date()** au lieu de `selectedDate` :
   Les evenements ne se mettaient pas a jour en naviguant entre les mois.

5. **CalendarPanel pas de loading state en standalone** : Ajout `loading=true` initial
   en mode standalone + gestion erreur si pas de compte email configure.

#### Fichiers modifies
| Fichier | Modification |
|---------|-------------|
| `PanelWindow.tsx` | Pre-charge comptes email, gestion erreur avec bouton retry |
| `calendarStore.ts` | Persist calendars, currentCalendarId, events, lastSyncAt |
| `emailStore.ts` | Persist labels, messages |
| `CalendarPanel.tsx` | loadEvents avec selectedDate, loading initial standalone, erreur si pas de compte |

#### Notes techniques
- localStorage est partage entre toutes les fenetres Tauri (meme origine)
- Zustand `persist` hydrate depuis localStorage au mount
- Les donnees cachees s'affichent instantanement, puis se rafraichissent via API
- Si le backend ne repond pas, PanelWindow affiche un ecran d'erreur avec "Reessayer"

### MVP v3.4 - COMPLET (Persistance Email/Calendrier)

### Session 2 fevrier - MCP Connectors Brainstorm (COMPLET)

**Audit des presets MCP + ajout connecteurs solopreneurs/TPE FR**

#### Audit : 5 presets supprimes
| Preset | Raison |
|--------|--------|
| git | Dev-only, aucun solopreneur n'utilise |
| linear | Issue tracking equipes dev |
| github | Dev-only, package deprecie |
| zapier | Package npm inexistant |
| make | Package npm inexistant |

#### Sprint 1 : 5 nouveaux presets Tier S
| Preset | Categorie | Env vars |
|--------|-----------|----------|
| Brave Search | recherche | `BRAVE_API_KEY` |
| Brevo | marketing | `BREVO_API_KEY` |
| Stripe | finance | `STRIPE_API_KEY` |
| HubSpot CRM | crm | `HUBSPOT_ACCESS_TOKEN` |
| Todoist | productivite | `TODOIST_API_KEY` |

#### Sprint 2 : 5 nouveaux presets Tier A
| Preset | Categorie | Env vars |
|--------|-----------|----------|
| Trello | productivite | `TRELLO_API_KEY`, `TRELLO_TOKEN` |
| Perplexity | recherche | `PERPLEXITY_API_KEY` |
| Pipedrive | crm | `PIPEDRIVE_API_TOKEN` |
| WhatsApp Business | communication | `WHATSAPP_API_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_BUSINESS_ACCOUNT_ID` |
| Playwright | avance | Aucune (open source) |

#### Sprint 3 : UI Polish
- [x] Presets organises par categories (8 sections avec icones)
- [x] Composant `PresetCategory` repliable avec headers
- [x] Section "Avance" repliee par defaut (sequential-thinking, slack, playwright)
- [x] Barre de recherche/filtre dans le panel Presets
- [x] Badge "Populaire" (etoile) sur 6 presets cles
- [x] Lien externe vers le service sur chaque preset
- [x] Compteur total presets dans le header

#### Bilan presets MCP (19 total)
| Categorie | Presets |
|-----------|---------|
| Essentiels | Filesystem, Fetch, Time |
| Productivite | Google Workspace, Notion, Airtable, Todoist, Trello |
| Recherche | Brave Search, Perplexity |
| Marketing | Brevo |
| CRM & Ventes | HubSpot CRM, Pipedrive |
| Finance | Stripe |
| Communication | WhatsApp Business |
| Avance | Sequential Thinking, Slack, Playwright |

#### Fichiers modifies
| Fichier | Action |
|---------|--------|
| `src/backend/app/routers/mcp.py` | -5 presets, +10 presets, +category/popular/url |
| `src/frontend/src/services/api.ts` | +category/popular/url sur MCPPreset |
| `src/frontend/src/components/settings/EnvVarModal.tsx` | +12 configs env vars, -4 obsoletes |
| `src/frontend/src/components/settings/ToolsPanel.tsx` | Categories, recherche, badges, PresetCategory |

#### Tier B (a la demande, non implemente)
Mailchimp, Dropbox, Shopify, Discord, X/Twitter, LinkedIn (API restrictive)

#### Watchlist
Pennylane (compta FR) - pas de package npm dedie, a surveiller

### MVP v3.5 - COMPLET (MCP Connectors Brainstorm)

### Session 2 fevrier - Skills Office v2 Code-Execution (COMPLET)

Remplacement du pipeline LLM -> Markdown/JSON -> regex parser -> fichier
par une approche code-execution : LLM -> code Python -> sandbox -> fichier.

#### Architecture
- **code_executor.py** : Module central (extraction, validation, sandbox, CodeGenSkill)
  - `extract_python_code()` : extrait le code des blocs ```python```
  - `validate_code()` : securite via AST + patterns bloques
  - `execute_sandboxed()` : execution async avec timeout 30s
  - `CodeGenSkill(BaseSkill)` : classe abstraite avec fallback automatique
- **Sandbox securisee** :
  - Bloques : os, sys, subprocess, shutil, socket, requests, urllib, eval, exec, compile
  - `__import__` restreint par whitelist selon le format (xlsx/docx/pptx)
  - Builtins limites (pas de getattr, setattr, etc.)
  - Timeout 30 secondes via `asyncio.wait_for`

#### Fichiers modifies
| Fichier | Modification |
|---------|-------------|
| `code_executor.py` | NOUVEAU - Module central sandbox + CodeGenSkill |
| `xlsx_generator.py` | Herite CodeGenSkill, prompt openpyxl (formules, multi-onglets, graphiques) |
| `docx_generator.py` | Herite CodeGenSkill, prompt python-docx (tableaux, styles, mise en page) |
| `pptx_generator.py` | Herite CodeGenSkill, prompt python-pptx (16:9, dark theme, variete slides) |
| `skills.py` router | Prompt enrichi demande du code Python |

#### Points cles
- **Fallback automatique** : si le LLM genere du Markdown au lieu de code, l'ancien parser prend le relais
- **Text/Analysis/Planning skills** : non affectes (restent des BaseSkill classiques)
- **18 skills** enregistres et fonctionnels dans le registry
- **Aucune nouvelle dependance** : openpyxl, python-docx, python-pptx deja installes

#### Verification
```bash
cd src/backend && uv run uvicorn app.main:app --reload --port 8000
# Guided Prompts -> Produire -> Tableur Excel / Document Word / Presentation PPT
# Tester avec modele puissant (Claude, GPT) = code-execution
# Tester avec modele faible (Ollama) = fallback legacy
```

### MVP v3.6 - COMPLET (Skills Office v2 Code-Execution)

### Session 3 février - Skills FILE multi-modèle + fix Opus (COMPLET)

**3 problèmes résolus** : titres génériques, docs vides Gemini Flash, pas d'adaptation au modèle.

#### Étape 1 : Détection capacité modèle
- [x] **`model_capability.py`** (NOUVEAU) - Mapping provider+modèle → "code" ou "markdown"
  - CODE : Anthropic (*), OpenAI (*), Gemini (pro), Mistral (large, codestral), Grok (*)
  - MARKDOWN : Gemini Flash, Mistral Small, Ollama (tous)

#### Étape 2 : Prompt adaptatif dans le router
- [x] **`skills.py`** - Branchement code vs markdown selon capacité modèle
  - Code-capable : instructions Python (python-docx/pptx/openpyxl)
  - Markdown-capable : instructions Markdown structuré via `get_markdown_prompt_addition()`
  - `max_tokens=8192` pour skills FILE (était 4096, causait troncature Opus)

#### Étape 3 : Prompts Markdown par generator
- [x] **`code_executor.py`** - `get_markdown_prompt_addition()` par défaut sur `CodeGenSkill`
- [x] **`docx_generator.py`** - Surcharge avec instructions DOCX Markdown
- [x] **`pptx_generator.py`** - Surcharge avec instructions PPTX (slides séparées par ---)
- [x] **`xlsx_generator.py`** - Surcharge avec instructions XLSX (tableaux Markdown par onglet)

#### Étape 4 : Meilleurs titres
- [x] **`registry.py`** - `_extract_title_from_content()` cherche dans le contenu LLM
- [x] **`registry.py`** - `_extract_title()` amélioré avec 24 préfixes FR/EN
- [x] Priorité prompt quand le contenu est du code Python (évite "Configuration des marges")

#### Fix critique Opus - Réponses tronquées
- [x] **`extract_python_code()`** - Fallback pour blocs ` ```python ` sans ` ``` ` fermant
- [x] **`repair_truncated_code()`** (NOUVEAU) - Retire les lignes incomplètes en fin de code tronqué jusqu'à obtenir un AST valide
- [x] **`CodeGenSkill.execute()`** - Intègre la réparation avant exécution sandbox
- [x] **`generate_content()`** dans `llm.py` - Paramètre `max_tokens` optionnel

#### Imports autorisés élargis
- Ajout `time`, `random`, `copy`, `string`, `textwrap`, `itertools`, `collections` pour les 3 formats

#### Tests manuels
| Modèle | DOCX | PPTX | XLSX |
|--------|------|------|------|
| Opus (Anthropic) | 40 KB OK | 41 KB OK | 5 KB OK (fallback) |
| Ollama/mistral | OK (markdown) | OK (markdown) | OK (markdown) |
| Gemini Flash | OK (markdown) | OK (markdown) | OK (markdown) |
| Grok | OK (code) | OK (code) | OK (fallback) |

#### Fichiers modifiés (8 fichiers)
| Fichier | Action |
|---------|--------|
| `app/services/skills/model_capability.py` | NOUVEAU - Détection capacité modèle |
| `app/services/skills/code_executor.py` | Fix extraction tronquée, réparation, imports élargis |
| `app/routers/skills.py` | Branchement code/markdown, max_tokens=8192 |
| `app/services/llm.py` | Paramètre max_tokens sur generate_content() |
| `app/services/skills/registry.py` | Titres améliorés, priorité prompt pour code |
| `app/services/skills/docx_generator.py` | get_markdown_prompt_addition() |
| `app/services/skills/pptx_generator.py` | get_markdown_prompt_addition() |
| `app/services/skills/xlsx_generator.py` | get_markdown_prompt_addition() |

### MVP v3.7 - COMPLET (Skills Multi-Modèle + Fix Opus)

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
