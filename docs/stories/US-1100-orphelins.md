Parfait ! J'ai maintenant une vision complète. Créons un rapport exhaustif d'analyse. Voici mon rapport d'AVOCAT DU DIABLE:

---

## RAPPORT D'ANALYSE INVERSE - THÉRÈSE V2
### Fonctionnalités oubliées par les 11 scribes

J'ai effectué une analyse INVERSE exhaustive du codebase en examinant:
1. **30 routers backend** (vs 11 domaines mentionnés)
2. **120+ composants frontend**
3. **20 stores Zustand**
4. **22 hooks custom**
5. **100+ services backend**
6. **30+ modules API frontend**

### DÉCOUVERTES CRITIQUES

#### A) ROUTERS BACKEND NON COUVERTS (11 orphelins):

| Router | Endpoints | Statut | Criticité |
|--------|-----------|--------|-----------|
| **agents.py** | 12 endpoints (sessions, tasks, dispatch, OpenClaw) | Aucune US | P1 - ATELIER |
| **browser.py** | 8 endpoints (navigate, extract, screenshot, click, fill) | Aucune US | P1 - WEB BROWSING |
| **calculators.py** | 6 endpoints (ROI, ICE, RICE, NPV, Break-even) | Aucune US | P2 - OUTILS |
| **commands_v3.py** | 6 endpoints (list, get, schema, create, update, delete) | Aucune US | P1 - COMMANDES UNIFIÉES |
| **dashboard.py** | 1 endpoint (/today) | Aucune US | P1 - ACCUEIL |
| **escalation.py** | 12 endpoints (pricing, limits, usage, cost estimation) | Aucune US | P1 - RATE LIMITING |
| **notifications.py** | 5 endpoints (list, count, read, generate) | Aucune US | P1 - NOTIFICATIONS |
| **performance.py** | 11 endpoints (metrics, memory, power mode) | Aucune US | P1 - PERF MONITORING |
| **personalisation.py** | 10 endpoints (templates, LLM behavior, features) | Aucune US | P1 - CUSTOMIZATION |
| **rgpd.py** | 9 endpoints (export, anonymize, purge, stats) | Aucune US | P1 - COMPLIANCE |
| **tools.py** | 5 endpoints (install, test, delete) | Aucune US | P1 - TOOL MANAGEMENT |

#### B) COMPOSANTS FRONTEND SANS TESTS (120+ composants, seulement 5 testés):

**Catégories orphelines:**

```
Atelier (Agents):
  - AgentChat.tsx / AgentChat 2.tsx
  - AgentInput.tsx
  - AgentMessageBubble.tsx
  - AtelierPanel.tsx
  - CodeReviewPanel.tsx
  - MissionStepper.tsx
  - NewTaskDialog.tsx
  - SessionList.tsx

RFC (Réfléchir-Faire-Capturer):
  - RFCWizard.tsx
  - RFCChat.tsx
  - RFCCapture.tsx

Board (Conseil IA):
  - AdvisorArcLayout.tsx
  - AdvisorCard.tsx
  - DeliberationView.tsx
  - ModeSelector.tsx
  - SynthesisCard.tsx

Settings (15 tabs, 0 tests):
  - AccessibilityTab.tsx
  - AdvancedTab.tsx
  - AgentsTab.tsx
  - CRMSyncPanel.tsx
  - DataTab.tsx
  - EnvVarModal.tsx
  - LimitsTab.tsx
  - LLMTab.tsx
  - PerformanceTab.tsx
  - PrivacyTab.tsx
  - ServicesTab.tsx
  - ToolsPanel.tsx

Home/Dashboard (0 tests):
  - DashboardToday.tsx
  - CommandCard.tsx
  - CommandCategoryGroup.tsx
  - CommandExecutor.tsx

Guided (0 tests):
  - CreateCommandForm.tsx
  - DynamicSkillForm.tsx
  - SkillPromptPanel.tsx
  - SubOptionsPanel.tsx

Memory (0 tests):
  - ContactModal.tsx
  - ProjectModal.tsx
  - ProjectsKanban.tsx
```

#### C) STORES NON COUVERTS (2 importants):

```
atelierStore.ts        - État complet du système d'agents (8142 bytes)
openclawStore.ts       - État OpenClaw sessions (6329 bytes)
```

#### D) HOOKS CUSTOMS NON DOCUMENTÉS:

```
useGuardedAction.ts    - Action guard (NOUVEAU)
useAutosave.ts         - Sauvegarde auto
useConversationSync.ts - Sync conversations
useDemoMask.ts         - Masquage données démo
useFileDrop.ts         - Drag & drop fichiers
useGhostText.ts        - Texte fantôme
useHealthCheck.ts      - Vérification santé API
useKeyboardShortcuts.ts - Raccourcis clavier
useMotionConfig.ts     - Configuration animations
useOnlineStatus.ts     - Statut connectivité
useReducedMotion.ts    - Mode sans animations
useVoiceRecorder.ts    - Enregistrement vocal
```

#### E) SERVICES BACKEND CRITIQUES NON DOCUMENTÉS:

```
audit.py               - AuditService avec logging d'activités
browser_agent.py       - Orchestration browser automation
circuit_breaker.py     - Résilience API (retry + timeout)
command_registry.py    - Registre dynamique des commandes
crm_import.py          - Import CRM (custom formats)
crm_export.py          - Export CRM
deep_research.py       - Recherche profonde (multi-sources)
email_classifier_v2.py - Classification emails v2
entity_extractor.py    - Extraction entités NER
image_generator.py     - Génération images (DALL-E, etc.)
invoice_pdf.py         - Génération PDF factures
memory_tools.py        - Outils mémoire
notification_service.py - Service notifications
openclaw_bridge.py     - Pont OpenClaw
performance.py         - Service perf monitoring
prompt_security.py     - Injection prompt prevention
rgpd_auto.py           - Automatisation RGPD
scoring.py             - Scoring contacts CRM
sheets_service.py      - Intégration Google Sheets
web_search.py          - Recherche web (Brave)
workspace_tools.py     - Outils workspace
```

---

## USER STORIES MANQUANTES (À partir de US-1100)

Voici les 25+ stories critiques oubliées par les autres scribes:

### DOMAIN: AGENTS / ATELIER (Agents de code embarqués)

**US-1100: Créer la structure UI du système d'agents**
- Epic: E6 (Agents IA)
- Description: Implémenter les composants React pour l'Atelier (agents chat panel)
  - AgentChat: interface chat bidirectionnelle avec les agents
  - MissionStepper: progression des tâches (spec → implementation → testing → review)
  - SessionList: historique des sessions d'agents
- Frontend: AtelierPanel.tsx, AgentChat.tsx, MissionStepper.tsx, SessionList.tsx
- Backend: /api/agents/request, /api/agents/sessions
- Tests requis: Vitest pour AgentChat streaming, MissionStepper progression
- Critère d'acceptation:
  - Chat agent fonctionne en temps réel
  - Progression des étapes visible
  - Historique persistant

**US-1101: Implémenter la soumission et approbation de diffs**
- Epic: E6
- Description: Interface de review code pour approver/rejeter diffs générés par les agents
  - Afficher diff colorisé
  - Boutons Approve/Reject/Rollback
  - Historique des rollbacks
- Frontend: CodeReviewPanel.tsx, DiffFileResponse
- Backend: /api/agents/tasks/{id}/approve, /reject, /rollback
- Dépendances: Git Service, Diff rendering
- Critère d'acceptation:
  - Diff affiche clairement additions/suppressions
  - Rollback restaure version précédente
  - Audit trail des actions

**US-1102: Intégrer OpenClaw (orchestration multi-agents)**
- Epic: E6
- Description: Dispatcher une tâche vers OpenClaw pour parallélisation
  - UI de dispatch
  - Monitoring des 5+ agents en parallèle
  - Collecte et fusion des résultats
- Frontend: openclawStore.ts, dispatch UI
- Backend: /api/agents/dispatch, /api/agents/sessions/{id}/send, /openclaw/status
- Services: SwarmOrchestrator, OpenClawBridge
- Critère d'acceptation:
  - 5+ agents tournent en parallèle
  - Timeout approprié par tâche
  - Fusion des résultats robuste

**US-1103: Système de configuration agent (source code path)**
- Epic: E6
- Description: Configuration du répertoire source pour agents (priorité DB → env → auto-détect)
- Frontend: AgentsTab.tsx (settings)
- Backend: /api/agents/config (GET/PUT)
- Services: _get_source_path() avec 4 niveaux de fallback
- Critère d'acceptation:
  - Validation du chemin .git
  - Test 4 emplacements connus
  - Env var override fonctionne

---

### DOMAIN: BROWSER (Web browsing automation)

**US-1104: Implémenter le contrôle de navigateur complet**
- Epic: E6
- Description: API browser pour navigation web automatisée
  - POST /navigate: naviguer vers URL
  - POST /extract: extraire texte page
  - POST /screenshot: capturer écran
  - POST /click: cliquer sur élément
  - POST /fill: remplir formulaire
  - POST /links: extraire tous liens
  - GET /status: état navigateur
  - POST /close: fermer session
- Frontend: browser.ts API client
- Backend: browser.py router + browser_agent.py service
- Dépendances: Playwright ou Selenium + pool de sessions
- Tests requis:
  - Navigation vers URL valide
  - Extraction texte complet page
  - Remplissage formulaires multi-champs
  - Gestion timeouts/erreurs réseau
- Critère d'acceptation:
  - 5+ actions basiques implémentées
  - Session pooling (max 3 parallèles)
  - Timeout 30s par action

---

### DOMAIN: CALCULATORS (Outils de calcul métier)

**US-1105: Implémenter les calculatrices métier**
- Epic: E6
- Description: 5 calculatrices financières/product
  - ROI: investissement/retour
  - ICE: Impact/Confidence/Ease
  - RICE: Reach/Impact/Confidence/Effort (formule Intercom)
  - NPV: Net Present Value
  - Break-even: seuil rentabilité
- Frontend: calculators.ts API client + UI panels
- Backend: /api/calculators/{roi|ice|rice|npv|break-even} + /api/calculators/help
- Services: calculators.py avec formules mathématiques
- Critère d'acceptation:
  - Chaque calculatrice valide inputs
  - Résultats cohérents (test 5 cas connus)
  - Documentation dans /help

---

### DOMAIN: DASHBOARD / HOME

**US-1106: Créer le dashboard "Aujourd'hui"**
- Epic: E5 (entendu, mais oublié dans les user stories)
- Description: Vue d'accueil avec bilan du jour
  - Tâches du jour
  - Événements calendrier
  - Mails non lus
  - Résumé conversations
- Frontend: DashboardToday.tsx, CommandCard.tsx, HomeCommands.tsx
- Backend: /api/dashboard/today avec agrégation
- Dépendances: taskStore, calendarStore, emailStore, chatStore
- Critère d'acceptation:
  - 4 sections (tâches, calendrier, emails, chat)
  - Actualisation auto toutes les 5 min
  - Performant même avec 1000+ messages

---

### DOMAIN: COMMANDS V3 (Système unifié de commandes)

**US-1107: Implémenter le registre de commandes unifiées**
- Epic: E6
- Description: Registre centralisé de toutes les commandes (builtin, skill, user, mcp)
  - GET /api/commands: liste avec filtres
  - GET /api/commands/{id}: détail
  - GET /api/commands/{id}/schema: schéma formulaire
  - POST /api/commands: créer custom
  - PUT /api/commands/{id}: modifier
  - DELETE /api/commands/{id}: supprimer
- Frontend: CommandsStore, CreateCommandForm.tsx, DynamicSkillForm.tsx
- Backend: commands_v3.py + command_registry.py
- Services: CommandRegistry avec 4 sources (builtin, skill, user, mcp)
- Critère d'acceptation:
  - Pagination 50 par 50
  - Filtres (category, show_on_home, source) fonctionnent
  - Schéma skill généré dynamiquement
  - Commandes user persisten en DB

**US-1108: Créer le wizard RFC (Réfléchir-Faire-Capturer)**
- Epic: E6
- Description: Wizard 3 étapes pour création commande guidée
  - Étape 1 (Réfléchir): chat avec THÉRÈSE sur besoin
  - Étape 2 (Faire): éditer code/schema
  - Étape 3 (Capturer): review + créer commande
- Frontend: RFCWizard.tsx, RFCChat.tsx, RFCCapture.tsx
- Backend: /api/commands-v3/generate (template generation)
- Services: SkillIntent detector pour suggestion
- Critère d'acceptation:
  - 3 étapes navigate bien
  - Génération template depuis schema
  - Commande créée en DB après capture

---

### DOMAIN: NOTIFICATIONS

**US-1109: Implémenter le système de notifications**
- Epic: E5
- Description: Notifications système en temps réel + centre de notif
  - GET /api/notifications: liste paginée
  - GET /api/notifications/count: compte non lues
  - PATCH /api/notifications/{id}/read: marquer lue
  - POST /api/notifications/read-all: tout lire
  - POST /api/notifications/generate: créer notif
- Frontend: NotificationCenter.tsx, notificationStore.ts
- Backend: notifications.py + notification_service.py
- Dépendances: WebSocket ou SSE pour temps réel
- Critère d'acceptation:
  - Badge compte mise à jour en temps réel
  - Historique persiste 30 jours
  - Notif toast disparaît après 5s

---

### DOMAIN: ESCALATION / RATE LIMITING

**US-1110: Implémenter la gestion des limites et pricing**
- Epic: E7 (Rate limiting / Costs)
- Description: Tracking usage, pricing, limites contexte
  - GET /api/escalation/prices: tarifs providers
  - GET /api/escalation/limits: limites utilisateur
  - POST /api/escalation/limits: configurer
  - POST /api/escalation/check-limits: avant requête
  - GET /api/escalation/usage/{daily|monthly|history}
  - GET /api/escalation/usage/stats: analytics
  - POST /api/escalation/check-uncertainty: risque dépassement?
- Frontend: LimitsTab.tsx (settings)
- Backend: escalation.py + token_tracker.py
- Critère d'acceptation:
  - Tracking tokens par provider/day/month
  - Alert à 80% quota
  - Blocage à 100% quota
  - Stats détaillées par modèle

**US-1111: Implémenter le mode économie batterie**
- Epic: E7
- Description: Réduire charge CPU/GPU en mode batterie
  - POST /api/escalation/limits: qualifier max concurrency
  - POST /api/performance/power/battery-saver: activer
  - Réduire rafraîchissements UI
  - Désactiver animations
  - Réduire fréquence sync
- Frontend: PerformanceTab.tsx, useMotionConfig.ts
- Backend: performance.py + circuit breaker adjustments
- Critère d'acceptation:
  - CPU usage -40% en mode batterie
  - UX reste fluide (60+ FPS)
  - Toggle ON/OFF dans settings

---

### DOMAIN: PERFORMANCE MONITORING

**US-1112: Créer le panneau de monitoring perf**
- Epic: E7
- Description: Dashboard perf temps réel
  - GET /api/performance/metrics: latence, throughput
  - GET /api/performance/metrics/recent: 24h
  - GET /api/performance/memory: heap usage
  - POST /api/performance/memory/cleanup: GC manual
  - GET /api/performance/conversations/count: nombre convos
  - GET /api/performance/status: health check
- Frontend: PerformanceTab.tsx avec graphiques
- Backend: performance.py service + circuit_breaker.py
- Critère d'acceptation:
  - Graphiques latence / throughput
  - Memory usage trend
  - Health check rouge/vert
  - Cleanup récupère 50%+ mémoire

---

### DOMAIN: PERSONALISATION

**US-1113: Implémenter les templates de prompts**
- Epic: E6 (Customization)
- Description: Créer/éditer/supprimer templates de prompts personnalisés
  - GET /api/personalisation/templates: liste
  - POST /api/personalisation/templates: créer
  - PUT /api/personalisation/templates/{id}: éditer
  - DELETE /api/personalisation/templates/{id}: supprimer
- Frontend: SettingsModal.tsx avec template builder
- Backend: personalisation.py
- Services: PromptTemplate storage
- Critère d'acceptation:
  - Variables {{user}}, {{date}}, {{context}} supportées
  - Preview live du template
  - 10+ templates built-in fournis
  - Persistance en DB

**US-1114: Contrôler le comportement du LLM par profil**
- Epic: E6
- Description: Config créative/prudent par provider/modèle
  - GET /api/personalisation/llm-behavior: config
  - POST /api/personalisation/llm-behavior: update
  - Température, top_p, max_tokens
- Frontend: LLMTab.tsx dans settings
- Backend: personalisation.py + LLMBehaviorSettings
- Critère d'acceptation:
  - Température 0.0-2.0 avec slider
  - Différentes presets (créatif, factuel, prudent)
  - Appliqué avant envoi requête LLM

**US-1115: Gérer la visibilité des features**
- Epic: E6
- Description: Masquer/afficher features par profile utilisateur
  - GET /api/personalisation/features: flags visibilité
  - POST /api/personalisation/features: update
- Frontend: AdvancedTab.tsx toggle features
- Backend: personalisation.py + FeatureVisibilitySettings
- Critère d'acceptation:
  - Features panel, voicerecorder, imagegen cachables
  - Persist en DB
  - Reload reload app applique changement

---

### DOMAIN: RGPD / PRIVACY

**US-1116: Exporter les données d'un contact (RGPD)**
- Epic: E7 (Compliance)
- Description: Export JSON/CSV complet d'une personne
  - GET /api/rgpd/export/{contact_id}
  - Tous les champs (emails, conversations, memos)
  - Format GDPR-compliant
- Frontend: MemoryPanel export button
- Backend: rgpd.py + export service
- Critère d'acceptation:
  - Export en < 5s
  - JSON structuré
  - Hashage timestamps

**US-1117: Anonymiser un contact (RGPD)**
- Epic: E7
- Description: Supprimer données identifiantes d'une personne
  - POST /api/rgpd/anonymize/{contact_id}
  - Hash email, nom → "ANON-xxxx"
  - Garder données métier (activités)
- Backend: rgpd.py + rgpd_auto.py
- Critère d'acceptation:
  - Audit trail de l'anonymisation
  - Impossible de retrouver l'identité
  - Contacts "en double" après anon

**US-1118: Gérer la purge automatique**
- Epic: E7
- Description: Configuration de la purge RGPD (retention policy)
  - GET /api/rgpd/purge/settings
  - PUT /api/rgpd/purge/settings
  - Retention 90/180/365 jours configurable
- Frontend: PrivacyTab.tsx
- Backend: rgpd.py + scheduled purge job
- Critère d'acceptation:
  - Purge en arrière-plan sans bloquer
  - Stats avant/après
  - Notification utilisateur

**US-1119: Statistiques RGPD**
- Epic: E7
- Description: Dashboard conformité RGPD
  - GET /api/rgpd/stats
  - Nombre contacts, dernier export, purges effectuées
- Frontend: DataTab.tsx
- Backend: rgpd.py + RGPDStatsResponse
- Critère d'acceptation:
  - Mise à jour quotidienne
  - Export CSV stats possibilité

---

### DOMAIN: TOOLS MANAGEMENT

**US-1120: Implémenter l'installation de tools**
- Epic: E6
- Description: Installer/tester/supprimer des outils (MCP, CLI)
  - GET /api/tools: liste
  - POST /api/tools/install: installer
  - GET /api/tools/{id}/manifest: metadata
  - POST /api/tools/{id}/test: tester
  - DELETE /api/tools/{id}: supprimer
- Frontend: ToolsPanel.tsx dans settings
- Backend: tools.py + tool_installer.py
- Critère d'acceptation:
  - Install télécharge + installe en ~/.therese/
  - Test vérifie accessibilité
  - Manifest affiche version, dépendances
  - Uninstall nettoie proprement

---

### DOMAIN: ACCESSIBILITY & UI

**US-1121: Implémenter l'onglet Accessibility (settings)**
- Epic: E5
- Description: Paramètres d'accessibilité avancés
  - Taille police (+/-10-150%)
  - Contraste haut
  - Animations réduites
  - Lecteur écran support
  - Zoom interface
- Frontend: AccessibilityTab.tsx, useReducedMotion.ts
- Services: AccessibilityStore + CSS personnalisé
- Critère d'acceptation:
  - WCAG 2.1 AA compliance
  - Zoom 150% ne casse pas layout
  - Animations disable = pas de transition

**US-1122: Implémenter les variables d'environnement UI (settings)**
- Epic: E6
- Description: Éditeur de variables d'environnement dans settings
  - Interface EnvVarModal.tsx
  - CRUD variables (create, list, edit, delete)
  - Validation (no secrets en plain text)
- Frontend: EnvVarModal.tsx, SettingsModal.tsx
- Backend: /api/config/env (GET/POST)
- Critère d'acceptation:
  - Avertissement "secrets" visible
  - Variables appliquées après save
  - Encryption avant storage DB

---

### DOMAIN: EMAIL (améliorations)

**US-1123: Implémenter le classifier d'emails v2**
- Epic: E2 (Email, amélioration)
- Description: Nouvelle version du classifier avec meilleure précision
  - POST /api/email/classify: prédire catégories
  - Support multiple catégories
  - Confidence scores
- Backend: email_classifier_v2.py + entity_matcher
- Services: NER pour extraction entités, scoring
- Critère d'acceptation:
  - Accuracy 95%+ sur dataset test
  - Support "urgent", "collaboration", "info"
  - Temps < 200ms par email

**US-1124: Générateur de réponses intelligentes**
- Epic: E2
- Description: Proposer brouillons de réponses basées sur contexte
  - GET /api/email/response-suggestions: générer suggestions
  - Context mémoire injecté (contact, projets)
- Frontend: ResponseGeneratorModal.tsx
- Backend: email_response_generator.py
- Services: LLM prompt + mémoire
- Critère d'acceptation:
  - 3+ suggestions générées
  - Prennent en compte historique contact
  - Temps < 3s pour 3 suggestions

---

### DOMAIN: AUDITING & LOGGING

**US-1125: Implémenter le système d'audit complet**
- Epic: E7 (Security/Compliance)
- Description: Logging de toutes les actions utilisateur
  - login, logout, create, update, delete, export, download
  - IP, user-agent, timestamp
  - Retention 1 an min
- Backend: audit.py + AuditService
- Models: ActivityLog
- Critère d'acceptation:
  - Chaque action loggée (< 10ms overhead)
  - Recherche par action/date/user
  - Export audit trail CSV

---

### DOMAIN: SECURITY

**US-1126: Implémenter la sécurité des prompts (injection prevention)**
- Epic: E7
- Description: Détecter et bloquer injection prompts
  - Patterns dangereux (ignore instructions, etc.)
  - Sanitization input utilisateur
- Backend: prompt_security.py service
- Critère d'acceptation:
  - Blocage "ignore all instructions" input
  - Log tentative injection
  - Pas de faux positifs (< 1%)

---

### DOMAIN: AI/ML SERVICES

**US-1127: Implémenter la génération d'images**
- Epic: E6
- Description: Intégration génération images (DALL-E 3, Stable Diffusion)
  - POST /api/images/generate: générer image
  - GET /api/images/history: historique générations
- Frontend: ImageGenerationPanel.tsx
- Backend: image_generator.py
- Critère d'acceptation:
  - Génération en < 10s
  - 4 résolutions supportées
  - Historique persiste

**US-1128: Impléter la recherche web profonde (deep research)**
- Epic: E6
- Description: Recherche multi-sources avec synthèse
  - Google, DuckDuckGo, Brave Search
  - Agrégation + synthèse LLM
  - Sources citées
- Backend: deep_research.py + web_search.py
- Critère d'acceptation:
  - 10+ résultats par requête
  - Synthèse en < 5s
  - Sources clickables

**US-1129: Scoring intelligent de contacts CRM**
- Epic: E2 (CRM, enhancement)
- Description: Calculer lead score basé sur historique
  - Fréquence interaction
  - Budget estimé
  - Engagement rate
- Backend: scoring.py service
- Services: Analytics sur activités
- Critère d'acceptation:
  - Score 0-100
  - Explications lisibles
  - Mise à jour quotidienne

---

### DOMAIN: INTEGRATIONS

**US-1130: Intégration Google Sheets (sync bidirectionnel)**
- Epic: E6
- Description: Sync CRM bidirectionnel avec Google Sheets
  - Lecture pipeline
  - Écriture mises à jour
- Backend: sheets_service.py + crm_sync.py
- Critère d'acceptation:
  - Sync chaque heure
  - Conflits résolus (last-write-wins)
  - Audit changes

**US-1131: Système MCP théorèse (MCP server embarqué)**
- Epic: E6
- Description: MCP server pour exposer THÉRÈSE comme tool externe
  - list_resources: conversations, mémoire
  - read_resource: détails
  - call_tool: actions (chat, create contact)
- Backend: mcp_therese_server.py
- Critère d'acceptation:
  - Compatible Claude Desktop
  - 10+ tools exposés
  - Authentification secure

---

### DOMAIN: BUILD & DEPLOYMENT

**US-1132: Implémenter le circuit breaker (résilience)**
- Epic: E7
- Description: Résilience API avec fallbacks intelligents
  - Retry avec backoff exponentiel
  - Timeout 30-60s par requête
  - Fallback mode dégradé
- Backend: circuit_breaker.py service
- Critère d'acceptation:
  - API indisponible ≤ 5min = fallback local
  - Retry 3x avant failover
  - Logging clair de transitions

---

## RÉSUMÉ EXÉCUTIF

**Fonctionnalités critiques oubliées:** 25+ user stories (US-1100 à US-1132)
**Impact:** ~40% de la surface d'API backend est orpheline
**Risque:** Bugs non testés (comme mentionné BUG-100 sur calendrier)
**Écoulement de travail:** 2-3 sprints pour couvrir tout (80+ stories si décomposées)

**Top 3 priorités:**
1. US-1100 (Atelier agents UI) - Fondamental
2. US-1107 (Commands V3 registry) - Bloquant pour slash commands
3. US-1109 (Notifications) - UX critique