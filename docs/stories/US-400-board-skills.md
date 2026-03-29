Parfait ! Maintenant j'ai une compréhension complète. Je vais générer les user stories de manière structurée. Laisse-moi compiler toutes les informations :

## RECONSTRUCTION DES USER STORIES - THÉRÈSE v2

### MODULE BOARD DE DÉCISION IA (5 CONSEILLERS)

```
### US-400 : Afficher le Board de Décision avec 5 conseillers
**En tant que** solopreneur/TPE
**Je veux** accéder au Board de Décision via Cmd+D (ou bouton dédié)
**Afin de** consulter 5 perspectives d'IA sur une décision stratégique

**Critères d'acceptation :**
- [ ] Raccourci Cmd+D ouvre un modal animé avec le Board
- [ ] Les 5 conseillers sont affichés avec leurs avatars colorés (arc layout MD+, grille mobile)
- [ ] Chaque conseiller affiche : nom, emoji, couleur, personnalité
- [ ] Texte d'intro visible : "Convoque ton Board - 5 conseillers IA..."
- [ ] Champs textarea visibles : "Ta question stratégique" + "Contexte (optionnel)"
- [ ] Bouton "Convoquer le Board" désactivé tant que question < 10 caractères

**Composants :**
- `/src/frontend/src/components/board/BoardPanel.tsx`
- `/src/frontend/src/components/board/AdvisorArcLayout.tsx`
- `/src/backend/app/routers/board.py` (GET /advisors)
- `/src/backend/app/models/board.py`

**data-testid :**
- `board-panel` (conteneur modal)
- `board-submit-btn` (bouton Convoquer)
```

```
### US-401 : Soumettre une question au Board en mode Cloud
**En tant que** solopreneur
**Je veux** poser une question stratégique et recevoir les avis de 5 conseillers IA en parallèle
**Afin de** avoir une vision globale multi-perspectives sur ma décision

**Critères d'acceptation :**
- [ ] Clic sur "Convoquer le Board" lance streamDeliberation via SSE
- [ ] Indicateur de progression : "Analyste en réflexion... 1/5"
- [ ] 5 AdvisorCards se remplissent progressivement (streaming texte)
- [ ] Providers affichés : Claude (cyan), GPT (vert), Grok (bleu), Mistral (orange), Gemini (bleu clair)
- [ ] Web search indicator visible si mode cloud et recherche web activée
- [ ] Synthèse générée automatiquement après tous les avis
- [ ] État "Délibération terminée" + boutons "Nouvelle question" / "Fermer"

**Composants :**
- `/src/frontend/src/components/board/BoardPanel.tsx` (handleStartDeliberation)
- `/src/frontend/src/components/board/DeliberationView.tsx`
- `/src/frontend/src/components/board/AdvisorCard.tsx`
- `/src/backend/app/services/board.py` (deliberate method, streaming)
- `/src/frontend/src/services/api/board.ts` (streamDeliberation)

**data-testid :**
- `board-result` (DeliberationView)
- Patterns: "Délibération", "en cours", providers
```

```
### US-402 : Consulter les 5 avis détaillés des conseillers
**En tant que** solopreneur
**Je veux** lire chaque avis en détail, avec expansion si contenu long
**Afin de** comprendre chaque perspective distincte

**Critères d'acceptation :**
- [ ] AdvisorCard affiche contenu avec couleur spécifique du conseiller
- [ ] Contenu > 300 chars : affichage tronqué + bouton "Voir plus"
- [ ] Clic "Voir plus" : expansio, puis "Réduire"
- [ ] Badge provider (ex "CLAUDE") visible top-right de chaque card
- [ ] Loading spinner pendant la réponse du conseiller
- [ ] Animation fade-in progressive des cards

**Composants :**
- `/src/frontend/src/components/board/AdvisorCard.tsx`
- `/src/backend/app/models/board.py` (AdvisorOpinion, AdvisorRole)

**data-testid :**
- Cards avec role dans className (analyst, strategist, devil, pragmatic, visionary)
```

```
### US-403 : Voir la synthèse finale avec consensus, divergences, recommandation
**En tant que** solopreneur
**Je veux** consulter une synthèse structurée après délibération
**Afin de** obtenir une recommandation claire et actionnable

**Critères d'acceptation :**
- [ ] SynthesisCard affichée en bas avec titre "Synthèse du Board"
- [ ] Badge confiance : "high" (vert), "medium" (jaune), "low" (rouge)
- [ ] Section "Recommandation" avec fond cyan/20
- [ ] Section "Points de consensus" avec checkmark vert
- [ ] Section "Points de divergence" avec warning jaune
- [ ] Section "Prochaines étapes" (liste numérotée) en magenta
- [ ] Layout responsive : grid 2 col sur MD+, 1 col sur mobile

**Composants :**
- `/src/frontend/src/components/board/SynthesisCard.tsx`
- `/src/backend/app/models/board.py` (BoardSynthesis)

**data-testid :**
- Patterns: "Synthèse", "Recommandation", "Consensus", "Divergence", "étapes"
```

```
### US-404 : Basculer entre mode Cloud et mode Souverain (Ollama)
**En tant que** solopreneur avec Ollama local
**Je veux** choisir si les conseillers utilisent des LLMs cloud ou Ollama
**Afin de** maîtriser mes données et coûts

**Critères d'acceptation :**
- [ ] ModeSelector visible au-dessus des conseillers avec 2 boutons : Cloud / Souverain
- [ ] En mode Cloud : providers multi-cloud en parallèle + web search option
- [ ] En mode Souverain : Ollama séquentiel (un conseiller après l'autre)
- [ ] Ollama check : fetch http://localhost:11434/api/tags au mount
- [ ] Mode Souverain désactivé si Ollama indisponible
- [ ] Sur chaque conseiller : mini-select pour choisir le modèle Ollama (7B, 14B, etc)
- [ ] Couleurs RAM recommandées : <4GB vert, 4-8GB jaune, >8GB rouge
- [ ] Banner "Mode souverain - interrogés un par un via Ollama" visible pendant délibération

**Composants :**
- `/src/frontend/src/components/board/ModeSelector.tsx`
- `/src/frontend/src/components/board/BoardPanel.tsx` (Ollama check)
- `/src/frontend/src/components/board/AdvisorArcLayout.tsx` (selects modèle)
- `/src/frontend/src/components/board/DeliberationView.tsx` (banner)

**data-testid :**
- Mode buttons: "Cloud", "Souverain"
```

```
### US-405 : Consulter l'historique des décisions du Board
**En tant que** solopreneur
**Je veux** voir mes décisions passées et les revisiter
**Afin de** suivre mon évolution décisionnelle et comparer

**Critères d'acceptation :**
- [ ] Bouton "Historique" visible dans le header du Board
- [ ] Vue historique : liste des décisions avec question + date + confiance
- [ ] Clic sur décision : affichage en mode "viewing" avec tous les avis + synthèse
- [ ] Bouton supprimer (trash icon) avec confirmation
- [ ] Retour historique <-> détail via "Retour" (ChevronLeft)
- [ ] Limite 50 décisions par défaut (pagination optionnelle)
- [ ] Aucune décision : message "Aucune décision enregistrée"

**Composants :**
- `/src/frontend/src/components/board/BoardPanel.tsx` (viewState='history'|'viewing')
- `/src/backend/app/routers/board.py` (GET /decisions, GET /decisions/{id}, DELETE)
- `/src/backend/app/services/board.py` (list_decisions, get_decision, delete_decision)

**data-testid :**
- Historique button, list items cliquables
```

```
### US-406 : Enrichir la délibération avec contexte utilisateur (THERESE.md + profil)
**En tant que** solopreneur
**Je veux** que les conseillers connaissent mon contexte (THERESE.md, profil)
**Afin de** obtenir des recommandations plus pertinentes et personnalisées

**Critères d'acceptation :**
- [ ] Service board.py injecte _get_user_context() dans system prompt de chaque conseiller
- [ ] Contexte inclut : profil utilisateur + THERESE.md (limité à 8000 chars)
- [ ] Pas d'injection visible côté UI (traitement backend transparent)
- [ ] Web search optionnel en mode cloud (async)
- [ ] Logs backend : "Contexte enrichi : [profil + THERESE.md]"

**Composants :**
- `/src/backend/app/services/board.py` (_get_user_context, deliberate)
- `/src/backend/app/models/board.py` (system_prompt des conseillers)

**data-testid :**
- Pas de testid (transparence backend)
```

---

### MODULE SKILLS OFFICE (DOCX, PPTX, XLSX + CODE EXECUTION)

```
### US-407 : Accéder au menu Guided Prompts et sélectionner une action
**En tant que** solopreneur
**Je veux** voir des actions guidées (Produire, Analyser, Personnaliser...)
**Afin de** créer du contenu structuré rapidement

**Critères d'acceptation :**
- [ ] GuidedPrompts panel accessible depuis sidebar ou homepage
- [ ] 8 actions visibles : Produire (Sparkles), Analyser, Personnaliser, etc.
- [ ] Clic sur action → sous-options affichées (SubOptionsPanel)
- [ ] User commands (P1-C) fusionnés avec actions statiques si show_on_home=true
- [ ] Chaque action a icône, titre, description, question d'intro

**Composants :**
- `/src/frontend/src/components/guided/GuidedPrompts.tsx`
- `/src/frontend/src/components/guided/ActionCard.tsx`
- `/src/frontend/src/components/guided/actionData.ts`

**data-testid :**
- Action cards cliquables
```

```
### US-408 : Générer un Document Word (DOCX) via le skill
**En tant que** solopreneur
**Je veux** générer un document Word complet structuré avec un prompt
**Afin de** créer rapidement rapports, guides, procédures

**Critères d'acceptation :**
- [ ] Sélection "Produire" → "Document Word" ouvre SkillPromptPanel
- [ ] Textarea pour saisir le prompt (placeholder "Décris ce que tu veux créer...")
- [ ] Clic "Générer" → état "generating" avec spinner
- [ ] LLM génère contenu + code Python créant le DOCX
- [ ] Code executor sandboxé exécute le Python via openpyxl/docx
- [ ] Après succès : badge "✅ Document généré" + bouton "Télécharger"
- [ ] Fallback Markdown si code-generation échoue (BUG-043)
- [ ] Fichier sauvegardé en ~/.therese/skills_output/
- [ ] Fichier téléchargeable 24h via /skills/download/{file_id}

**Composants :**
- `/src/frontend/src/components/guided/SkillPromptPanel.tsx`
- `/src/frontend/src/components/guided/SkillExecutionPanel.tsx`
- `/src/frontend/src/services/api/skills.ts` (executeSkill, downloadSkillFile)
- `/src/backend/app/routers/skills.py` (POST /execute/docx-pro, GET /download/{file_id})
- `/src/backend/app/services/skills/code_executor.py`
- `/src/backend/app/services/skills/docx_generator.py`

**data-testid :**
- SkillPromptPanel, spinner, success badge, download button
```

```
### US-409 : Générer une Présentation PowerPoint (PPTX) avec nombre de slides
**En tant que** solopreneur
**Je veux** créer une présentation structurée en 5-10 slides via un prompt
**Afin de** préparer rapidement des pitchs, propositions, formations

**Critères d'acceptation :**
- [ ] Sélection "Produire" → "Présentation PPT"
- [ ] Prompt avec détection du nombre de slides (regex : "\d{1,2}\s*(?:slides?|diapositives?)")
- [ ] Extraction du nb_slides (BUG-pptx-nb-slides, clamp 3-30)
- [ ] LLM génère structure + code Python créant le PPTX
- [ ] Code executor crée fichier PPTX avec styles Synoptia
- [ ] max_tokens = 16384 pour éviter troncature contenus longs
- [ ] Succès : "✅ Présentation générée" + bouton "Télécharger"
- [ ] PPTX téléchargeable via /skills/download/{file_id}

**Composants :**
- `/src/frontend/src/components/guided/SkillPromptPanel.tsx`
- `/src/frontend/src/components/guided/SkillExecutionPanel.tsx`
- `/src/backend/app/routers/skills.py` (POST /execute/pptx-pro)
- `/src/backend/app/services/skills/code_executor.py`
- `/src/backend/app/services/skills/pptx_generator.py`

**data-testid :**
- PPTX generation status, success badge
```

```
### US-410 : Générer un Tableur Excel (XLSX) avec formules et mise en forme
**En tant que** solopreneur
**Je veux** créer un tableur Excel avec données, formules, graphiques
**Afin de** générer rapidement dashboards, budgets, analyses

**Critères d'acceptation :**
- [ ] Sélection "Produire" → "Tableur Excel"
- [ ] Prompt libre pour description du tableur
- [ ] LLM génère contenu + code Python (openpyxl)
- [ ] Code peut inclure : styling (couleurs, fonts), formules, graphiques
- [ ] Couleur palette Synoptia injectée en namespace (SYNOPTIA_COLORS)
- [ ] max_tokens = 16384 pour documents longs
- [ ] Succès : "✅ Tableur généré" + bouton "Télécharger"
- [ ] XLSX téléchargeable via /skills/download/{file_id}
- [ ] Validation contenu : _validate_document_content() si quasi vide

**Composants :**
- `/src/frontend/src/components/guided/SkillPromptPanel.tsx`
- `/src/frontend/src/components/guided/SkillExecutionPanel.tsx`
- `/src/backend/app/routers/skills.py` (POST /execute/xlsx-pro)
- `/src/backend/app/services/skills/code_executor.py`
- `/src/backend/app/services/skills/xlsx_generator.py`

**data-testid :**
- XLSX generation, success status
```

```
### US-411 : Exécuter du code Python sandboxé pour générer les documents
**En tant que** système
**Je veux** exécuter du code Python généré par le LLM de manière sécurisée
**Afin de** créer les fichiers DOCX/PPTX/XLSX sans risque de sécurité

**Critères d'acceptation :**
- [ ] Code executor vérifie les imports autorisés (ALLOWED_IMPORTS par format)
- [ ] Patterns bloqués rejetés : os, sys, subprocess, eval, exec, socket, requests, etc.
- [ ] Timeout exécution = 30 secondes (EXECUTION_TIMEOUT)
- [ ] Namespace autorisé : openpyxl, python-docx, python-pptx, datetime, json, math
- [ ] Palette Synoptia injectée pour styling cohérent
- [ ] AST validation avant exécution (ast.parse)
- [ ] Erreurs capturées et retournées au frontend
- [ ] Logs audit : "Code executed for [skill_id], duration: X.Xs"

**Composants :**
- `/src/backend/app/services/skills/code_executor.py`
- Patterns bloqués (BLOCKED_PATTERNS)
- Imports autorisés (ALLOWED_IMPORTS)

**data-testid :**
- Pas de testid (backend safety)
```

```
### US-412 : Afficher un formulaire dynamique pour les skills enrichis
**En tant que** solopreneur
**Je veux** remplir un formulaire structuré avant de générer un skill
**Afin de** fournir des paramètres précis (destinataire, ton, budget, etc.)

**Critères d'acceptation :**
- [ ] DynamicSkillForm générée dynamiquement selon le schéma du skill
- [ ] Types supportés : text, textarea, select, number, file
- [ ] Champs requis : validation live
- [ ] Valeurs par défaut appliquées au mount
- [ ] Help text visible sous chaque champ
- [ ] Bouton Générer désactivé tant que validation en cours
- [ ] Erreur schéma affichée (P0-B schemaLoadError)
- [ ] Retour (back arrow) pour annuler et revenir aux actions

**Composants :**
- `/src/frontend/src/components/guided/DynamicSkillForm.tsx`
- `/src/frontend/src/services/api/skills.ts` (getSkillInputSchema)
- `/src/backend/app/routers/skills.py` (GET /schema/{skill_id})

**data-testid :**
- Form fields avec labels, help text visible
```

```
### US-413 : Télécharger le fichier généré
**En tant que** solopreneur
**Je veux** télécharger le fichier généré (DOCX/PPTX/XLSX)
**Afin de** l'ouvrir dans mon éditeur Office et l'utiliser/affiner

**Critères d'acceptation :**
- [ ] Bouton "Télécharger" visible après génération réussie
- [ ] Clic : appelle GET /skills/download/{file_id}
- [ ] Réponse FileResponse avec MIME type correct (application/vnd.openxmlformats-*)
- [ ] Nom du fichier : Title_fileId[:8].ext
- [ ] Fichier en cache 24h (registry cache)
- [ ] Fallback : chercher sur disque par glob si absent du cache
- [ ] Erreur 404 si fichier expiré ou non trouvé

**Composants :**
- `/src/frontend/src/components/guided/SkillExecutionPanel.tsx` (onDownload)
- `/src/frontend/src/services/api/skills.ts` (downloadSkillFile)
- `/src/backend/app/routers/skills.py` (GET /download/{file_id})

**data-testid :**
- Download button, file format icons (FileText, Presentation, Table)
```

```
### US-414 : Créer des Custom Commands pour homepage (P1-C)
**En tant que** solopreneur avancé
**Je veux** créer des commandes personnalisées visibles sur la homepage
**Afin de** rapide accès à mes workflows fréquents

**Critères d'acceptation :**
- [ ] Bouton "Créer une commande" visible dans GuidedPrompts
- [ ] CreateCommandForm : nom, icône, description, contenu (prompt/code)
- [ ] Champs : show_on_home (toggle)
- [ ] Commandes sauvegardées en DB et fusionnées avec actions statiques
- [ ] Si show_on_home=true : apparaît sur homepage + dans "Personnaliser"
- [ ] Édition/suppression des commands possibles (future)
- [ ] Icône emoji/unicode supportée (ex: "🎯 Mon workflow")

**Composants :**
- `/src/frontend/src/components/guided/CreateCommandForm.tsx`
- `/src/frontend/src/services/api/commands.ts` (listUserCommands, createUserCommand)
- `/src/backend/app/routers/commands.py` (backend pour user commands)

**data-testid :**
- CreateCommandForm button, form fields
```

```
### US-415 : Enrichir le contexte des skills avec mémoire (contacts, projets)
**En tant que** solopreneur
**Je veux** que les skills connaissent mes contacts et projets
**Afin de** générer du contenu personnalisé (emails avec vrais noms, propositions adaptées)

**Critères d'acceptation :**
- [ ] Router skills.py : enrichissement context via get_enrichment_context()
- [ ] Mémoire injectée : contacts (nom, company, email, notes) + projets (name, status, budget)
- [ ] Récupération DB : SELECT Contact LIMIT 50, SELECT Project LIMIT 50
- [ ] Enrichment affiché dans prompt au LLM
- [ ] Profil utilisateur aussi injecté (name, company, role)
- [ ] Logs : "Enrichment context prepared for [skill_id]"

**Composants :**
- `/src/backend/app/routers/skills.py` (execute_skill, enrichment section)
- `/src/backend/app/services/skills/base.py` (get_enrichment_context)

**data-testid :**
- Pas de testid (backend enrichment transparent)
```

---

## RÉSUMÉ DES FICHIERS PERTINENTS

### Frontend - Board
- `src/frontend/src/components/board/BoardPanel.tsx` (orchestrateur)
- `src/frontend/src/components/board/DeliberationView.tsx` (vue délibération)
- `src/frontend/src/components/board/AdvisorCard.tsx` (affichage avis)
- `src/frontend/src/components/board/SynthesisCard.tsx` (synthèse)
- `src/frontend/src/components/board/ModeSelector.tsx` (Cloud/Souverain)
- `src/frontend/src/components/board/AdvisorArcLayout.tsx` (layout 5 conseillers)
- `src/frontend/src/services/api/board.ts` (API client)

### Backend - Board
- `src/backend/app/routers/board.py` (endpoints)
- `src/backend/app/models/board.py` (datamodels, ADVISOR_CONFIG)
- `src/backend/app/services/board.py` (délibération, streaming)

### Frontend - Skills
- `src/frontend/src/components/guided/GuidedPrompts.tsx` (hub actions)
- `src/frontend/src/components/guided/SkillPromptPanel.tsx` (input prompt)
- `src/frontend/src/components/guided/SkillExecutionPanel.tsx` (état génération)
- `src/frontend/src/components/guided/DynamicSkillForm.tsx` (formulaires)
- `src/frontend/src/components/guided/actionData.ts` (config actions)
- `src/frontend/src/services/api/skills.ts` (API client)

### Backend - Skills
- `src/backend/app/routers/skills.py` (endpoints)
- `src/backend/app/models/schemas_skills.py` (schemas Pydantic)
- `src/backend/app/services/skills/base.py` (BaseSkill, interfaces)
- `src/backend/app/services/skills/code_executor.py` (sécurité Python)
- `src/backend/app/services/skills/docx_generator.py`
- `src/backend/app/services/skills/pptx_generator.py`
- `src/backend/app/services/skills/xlsx_generator.py`
- `src/backend/app/services/skills/registry.py` (SkillsRegistry)

### Tests
- `tests/e2e/test_board.py` (scénarios Board)
- `tests/e2e/test_skills.py` (scénarios Skills)

---

## NUMÉROTATION FINALE

- **US-400** à **US-406** : Board de Décision (7 stories)
- **US-407** à **US-415** : Skills Office (9 stories)

**Total : 16 user stories couvrant les deux modules clés**