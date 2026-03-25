# Backlog UltraJury - THERESE v0.8.0
**Date** : 25/03/2026 | **Score** : 69.2/100 | **Cible** : 80+/100
**Stories** : 16 (4 P0, 7 P1, 4 P2, 1 P3)

---

## Recapitulatif

| ID | Titre | Epic | Priorite | Effort | Axes |
|----|-------|------|----------|--------|------|
| US-100 | Chat accessible (aria-live + boutons labellises) | Accessibilite & Inclusion | P0 | M | Accessibilite |
| US-101 | Eliminer les except Exception silencieux | Qualite & Maintenabilite | P0 | L | Qualite Code, Resilience |
| US-102 | Politique de confidentialite et mentions legales in-app | Securite & Conformite | P0 | S | Conformite |
| US-103 | Monitoring et logs structures | Infrastructure & Fiabilite | P0 | L | DevOps |
| US-104 | Compression HTTP (GZipMiddleware) | Performance & Optimisation | P1 | XS | Performance |
| US-105 | Virtualisation des listes de messages | Performance & Optimisation | P1 | M | Performance, Frontend |
| US-106 | Circuit breaker et fallback LLM runtime | Infrastructure & Fiabilite | P1 | L | Resilience |
| US-107 | Harmoniser le tutoiement | Accessibilite & Inclusion | P1 | S | Contenu |
| US-108 | Liste des sous-traitants LLM et consentement granulaire | Securite & Conformite | P1 | M | Conformite, Securite |
| US-109 | Restreindre le scope Tauri FS | Securite & Conformite | P1 | S | Securite |
| US-110 | Corriger la requete N+1 du chat | Performance & Optimisation | P1 | S | Performance, Architecture |
| US-111 | Eclater ChatLayout et ChatInput | Experience Utilisateur | P2 | L | Frontend |
| US-112 | Tests composants frontend (couverture 6% a 25%) | Qualite & Maintenabilite | P2 | XL | Qualite Code, Frontend |
| US-113 | Formulaires accessibles (aria-invalid, focus-visible) | Accessibilite & Inclusion | P2 | M | Accessibilite |
| US-114 | Eclater les routers backend > 1000 lignes | Qualite & Maintenabilite | P2 | L | Architecture |
| US-115 | Documentation utilisateur in-app | Experience Utilisateur | P3 | XL | Produit |

---

## Stories detaillees

---

## Epic 1 : Accessibilite & Inclusion

### US-100 : Chat accessible (aria-live + boutons icones labellises)
**Epic** : Accessibilite & Inclusion | **Priorite** : P0 | **Effort** : M
**Axes** : Accessibilite | **Source** : [C] Accessibilite - Boutons icones sans label, aria-live absent

> En tant qu'entrepreneur utilisant un lecteur d'ecran, je veux que le chat annonce les nouvelles reponses et que chaque bouton soit identifiable, afin de pouvoir utiliser THERESE sans assistance visuelle.

**Criteres d'acceptation** :
- [ ] Le conteneur de messages du chat porte `aria-live="polite"` et `aria-relevant="additions"`
- [ ] Chaque nouvelle reponse IA est annoncee par le lecteur d'ecran (tester avec VoiceOver macOS)
- [ ] Les ~10 boutons icones identifies (copier, regenerer, supprimer, voice, send, etc.) portent un `aria-label` explicite en francais
- [ ] `announceToScreenReader()` est appele a la fin de chaque reponse streamee
- [ ] Aucune regression des tests Vitest existants

**Notes** :
- Fichiers principaux : `src/frontend/src/components/chat/MessageList.tsx`, `ChatInput.tsx`, composants `ui/`
- `announceToScreenReader` existe deja dans `src/frontend/src/lib/accessibility.ts` mais n'est jamais appele dans le chat
- `aria-live` present seulement dans `accessibility.ts` et `GlobalErrorBoundary.tsx` (2 occurrences total)
- Approche : ajouter une `div` aria-live dans `ChatLayout`, alimentee par les chunks SSE termines

---

### US-107 : Harmoniser le tutoiement
**Epic** : Accessibilite & Inclusion | **Priorite** : P1 | **Effort** : S
**Axes** : Contenu | **Source** : [C] Contenu - 34 "vous" vs 50 "tu" incoherents

> En tant qu'entrepreneur, je veux une interface qui me tutoie de facon coherente, afin de ressentir la proximite promise par la marque ("Humain d'abord").

**Criteres d'acceptation** :
- [ ] Toutes les occurrences de "vous/votre/vos" (hors mentions legales et conditions) sont remplacees par "tu/ton/ta/tes"
- [ ] Les badges LLM en anglais ("Flagship", "Coding", "Reasoning") sont traduits en francais
- [ ] La section raccourcis "Core Features" est renommee en francais
- [ ] Les placeholders email en anglais sont traduits
- [ ] Un grep sur le frontend confirme 0 "vous" hors fichiers juridiques

**Notes** :
- Passer sur tous les fichiers `.tsx`, `.ts` du frontend
- Attention aux strings dans les stores Zustand et dans les prompts systeme backend (ceux-ci restent en "tu" deja)
- Ne pas toucher les mentions legales / CGV qui requierent le vouvoiement juridique

---

### US-113 : Formulaires accessibles (aria-invalid, focus-visible)
**Epic** : Accessibilite & Inclusion | **Priorite** : P2 | **Effort** : M
**Axes** : Accessibilite | **Source** : [C] Accessibilite - focus-visible absent, formulaires sans aria-invalid

> En tant qu'entrepreneur naviguant au clavier, je veux voir clairement le champ actif et etre informe des erreurs de saisie, afin de remplir les formulaires sans hesitation.

**Criteres d'acceptation** :
- [ ] `focus-visible` est applique a tous les elements interactifs (inputs, boutons, selects, textareas) via une classe utilitaire globale
- [ ] Les formulaires (onboarding, settings, CRM, email) utilisent `aria-invalid="true"` + `aria-errormessage` quand un champ est en erreur
- [ ] Les champs obligatoires portent `aria-required="true"`
- [ ] `useReducedMotion` est branche sur les composants avec animation (Framer Motion)
- [ ] Les 2 `div` clickables du CRM ont `role="button"` et `tabIndex={0}` + gestion Enter/Space
- [ ] La hierarchie des headings (h1-h6) est corrigee pour etre sequentielle dans les panneaux principaux

**Notes** :
- `useReducedMotion` et `createFocusTrap` existent dans le code mais ne sont jamais importes dans les composants
- `focus-visible` n'est present que dans `Button.tsx` et `AccessibilityTab` - a generaliser via TailwindCSS 4

---

## Epic 2 : Securite & Conformite

### US-102 : Politique de confidentialite et mentions legales in-app
**Epic** : Securite & Conformite | **Priorite** : P0 | **Effort** : S
**Axes** : Conformite | **Source** : [C] Conformite - Absence de politique de confidentialite, mentions legales

> En tant qu'auditeur CNIL, je veux trouver une politique de confidentialite et des mentions legales accessibles dans l'application, afin de verifier la conformite RGPD sans documentation externe.

**Criteres d'acceptation** :
- [ ] Un onglet "Legal" ou "Mentions legales" est accessible dans les parametres (SettingsModal)
- [ ] La politique de confidentialite detaille : donnees collectees, finalites, durees de retention, droits de l'utilisateur (acces, rectification, suppression, portabilite)
- [ ] Les mentions legales identifient l'editeur (Synoptia SARL-U, SIRET 991 606 781 00010)
- [ ] Le contenu est en francais avec accents corrects
- [ ] Un lien "Confidentialite" est visible dans le footer ou la sidebar

**Notes** :
- Le SettingsModal a deja ete splitte en 6 onglets - ajouter un 7e "Legal"
- Contenu juridique a rediger/valider par Ludo (pas de generation automatique du contenu juridique)
- Les donnees sont 100% locales : la politique est plus simple que pour un SaaS cloud

---

### US-108 : Liste des sous-traitants LLM et consentement granulaire
**Epic** : Securite & Conformite | **Priorite** : P1 | **Effort** : M
**Axes** : Conformite, Securite | **Source** : [C] Conformite - Aucune liste sous-traitants LLM, consentement non granulaire

> En tant qu'admin de collectivite, je veux savoir exactement quels fournisseurs LLM traitent mes donnees et pouvoir en desactiver certains, afin de respecter la politique de securite de ma structure.

**Criteres d'acceptation** :
- [ ] Un panneau "Sous-traitants IA" dans les parametres liste tous les providers LLM actifs avec : nom, pays d'hebergement, lien vers leur politique de donnees
- [ ] L'utilisateur peut activer/desactiver individuellement chaque provider (toggle par provider)
- [ ] Un provider desactive n'apparait plus dans le selecteur de modeles du chat
- [ ] Le consentement initial (onboarding) propose un choix granulaire par categorie (modeles cloud US, modeles cloud EU, modeles locaux Ollama)
- [ ] La liste est mise a jour dynamiquement (pas en dur) a partir de la config des providers

**Notes** :
- Les providers sont deja configures dans `src/backend/app/services/providers/` (7 providers)
- L'onboarding existe dans `src/frontend/src/components/onboarding/`
- Stocker les preferences dans la config utilisateur SQLite existante

---

### US-109 : Restreindre le scope Tauri FS
**Epic** : Securite & Conformite | **Priorite** : P1 | **Effort** : S
**Axes** : Securite | **Source** : [I] Securite - Tauri FS scope lecture trop large ($HOME/**)

> En tant que developpeur, je veux que THERESE n'ait acces qu'aux repertoires strictement necessaires, afin de reduire la surface d'attaque en cas de vulnerabilite.

**Criteres d'acceptation** :
- [ ] Le scope FS Tauri est restreint a `~/.therese/**`, `~/Documents/**`, `~/Desktop/**` et `~/Downloads/**`
- [ ] Les repertoires sensibles (`~/.ssh`, `~/.gnupg`, `~/.aws`, `~/Library`) sont explicitement exclus
- [ ] L'endpoint `/api/shutdown` est protege par une confirmation cote frontend (dialog natif Tauri)
- [ ] Le file browser fonctionne toujours dans les repertoires autorises
- [ ] L'execution de code dans le code executor utilise `subprocess.run()` avec timeout et sans acces shell

**Notes** :
- Configuration dans `src/frontend/src-tauri/tauri.conf.json`
- Le code executor est dans `src/backend/app/services/skills/code_executor.py`
- Tester sur macOS (sandboxing Tauri) et verifier que le drag-and-drop fonctionne encore

---

## Epic 3 : Performance & Optimisation

### US-104 : Compression HTTP (GZipMiddleware)
**Epic** : Performance & Optimisation | **Priorite** : P1 | **Effort** : XS
**Axes** : Performance | **Source** : [C] Performance - Aucune compression HTTP

> En tant qu'entrepreneur avec une connexion moyenne, je veux que les reponses API soient compressees, afin de reduire les temps de chargement des longs historiques de chat.

**Criteres d'acceptation** :
- [ ] `GZipMiddleware` est ajoute dans `main.py` avec `minimum_size=500`
- [ ] Les reponses JSON > 500 octets sont compressees (verifiable via `Content-Encoding: gzip` dans les headers)
- [ ] Le streaming SSE du chat continue de fonctionner (pas de buffering)
- [ ] Un test verifie la presence du header `Content-Encoding: gzip` sur `/api/memory/contacts`
- [ ] Aucune regression sur les 850 tests existants

**Notes** :
- Fichier : `src/backend/app/main.py`
- Attention : `GZipMiddleware` peut interferer avec le SSE si mal configure. Tester le streaming du chat apres ajout.
- `starlette.middleware.gzip.GZipMiddleware` est deja disponible (dependance Starlette)

---

### US-105 : Virtualisation des listes de messages
**Epic** : Performance & Optimisation | **Priorite** : P1 | **Effort** : M
**Axes** : Performance, Frontend | **Source** : [I] Performance - Aucune virtualisation des listes messages

> En tant qu'entrepreneur avec des conversations longues (100+ messages), je veux que l'interface reste fluide, afin de ne pas attendre lors du scroll dans l'historique.

**Criteres d'acceptation** :
- [ ] `react-window` (ou `@tanstack/virtual`) est installe et integre dans `MessageList.tsx`
- [ ] Seuls les messages visibles + un buffer de 5 au-dessus/en-dessous sont rendus dans le DOM
- [ ] Le scroll auto vers le dernier message fonctionne toujours
- [ ] La recherche dans les messages fonctionne toujours (scroll-to-result)
- [ ] Le copier/coller de blocs de code dans les messages reste fonctionnel
- [ ] Performance mesuree : <100ms pour afficher une conversation de 200 messages (vs baseline actuelle)

**Notes** :
- Fichier principal : `src/frontend/src/components/chat/MessageList.tsx`
- Les messages ont des hauteurs variables (markdown, code blocks, images) - utiliser `VariableSizeList` de react-window
- Attention aux refs pour le scroll automatique

---

### US-110 : Corriger la requete N+1 du chat
**Epic** : Performance & Optimisation | **Priorite** : P1 | **Effort** : S
**Axes** : Performance, Architecture | **Source** : [C] Performance - N+1 dans chat.py, [I] pas de selectinload

> En tant qu'entrepreneur avec 50+ contacts et projets en memoire, je veux que l'envoi d'un message ne charge pas toutes mes entites, afin d'avoir des reponses en moins de 500ms.

**Criteres d'acceptation** :
- [ ] `_get_existing_entity_names` dans `chat.py` est remplace par une requete paginee ou un cache TTL
- [ ] Les routers utilisant des relations SQLModel emploient `selectinload` pour eviter le lazy loading N+1
- [ ] L'estimation de tokens utilise `tiktoken` (ou un compteur plus precis que `len(text)/4`)
- [ ] Les endpoints `/api/memory/contacts` et `/api/memory/projects` supportent la pagination (`?page=1&limit=20`)
- [ ] Un benchmark montre une amelioration >50% du temps de reponse sur `/api/chat/send` avec 100 contacts

**Notes** :
- Fichiers : `src/backend/app/routers/chat.py` (1408L), `memory.py`
- La pagination n'existe que sur 2/28 routers actuellement
- Pour tiktoken : `tiktoken` est leger et precis pour les modeles OpenAI/Anthropic

---

## Epic 4 : Qualite & Maintenabilite

### US-101 : Eliminer les except Exception silencieux
**Epic** : Qualite & Maintenabilite | **Priorite** : P0 | **Effort** : L
**Axes** : Qualite Code, Resilience | **Source** : [C] Qualite Code - 45+ bare except Exception (20 silencieux), [C] Resilience - 145 except bruts

> En tant que developpeur, je veux que les erreurs soient correctement typees et tracees, afin de diagnostiquer les bugs en production au lieu de les ignorer silencieusement.

**Criteres d'acceptation** :
- [ ] Les 248 `except Exception` identifies sont audites et classes en 3 categories : (a) remplacer par exception specifique, (b) ajouter `logger.exception()`, (c) conserver avec justification
- [ ] Les ~20 `except Exception: pass` silencieux sont tous elimines (remplaces par logging ou exception specifique)
- [ ] Chaque `except` conserve logue au minimum le message d'erreur avec `logger.warning()` ou `logger.exception()`
- [ ] `_validate_document_content` ne retourne plus `True` en cas d'exception (lever l'erreur ou retourner `False`)
- [ ] La regle Ruff `BLE001` (blind exception) est activee dans `pyproject.toml`
- [ ] Les 850 tests existants passent toujours

**Notes** :
- 248 occurrences dans 64 fichiers (grep confirme)
- Commencer par les routers (chat.py 14, crm.py 19, calendar.py 10, email.py 10) et les services critiques (crm_sync.py 14, encryption.py 10)
- Approche iterative : un PR par groupe de fichiers, pas un mega-PR

---

### US-112 : Tests composants frontend (couverture 6% a 25%)
**Epic** : Qualite & Maintenabilite | **Priorite** : P2 | **Effort** : XL
**Axes** : Qualite Code, Frontend | **Source** : [C] Frontend - Tests composants 6% (11/184 fichiers)

> En tant que developpeur, je veux une couverture de tests frontend d'au moins 25%, afin de detecter les regressions avant mise en production.

**Criteres d'acceptation** :
- [ ] La couverture frontend passe de 6% (11/184) a 25% (46+ fichiers testes)
- [ ] Les composants critiques sont couverts : ChatLayout, MessageList, ChatInput, SettingsModal (6 tabs), OnboardingWizard, Sidebar
- [ ] Les stores Zustand principaux sont testes (chatStore, emailStore, calendarStore)
- [ ] Les 35 `console.log` residuels sont remplaces par un logger conditionnel (silencieux en prod)
- [ ] `@typescript-eslint/no-explicit-any` passe de `'off'` a `'warn'`
- [ ] La CI mesure et rapporte la couverture (Vitest `--coverage`)

**Notes** :
- Vitest est deja configure avec jsdom
- Rappel : `navigator.platform` n'est pas "Mac" en jsdom - utiliser `ctrlKey` dans les tests
- Rappel : `vi.advanceTimersByTimeAsync(100)` au lieu de `vi.runAllTimersAsync()` (boucles infinies)
- Prioriser les tests sur les composants modifies frequemment (ChatLayout, CRM, Email)

---

### US-114 : Eclater les routers backend > 1000 lignes
**Epic** : Qualite & Maintenabilite | **Priorite** : P2 | **Effort** : L
**Axes** : Architecture | **Source** : [C] Architecture - Router chat 1408L, crm 1425L, email 1424L, calendar 1342L

> En tant que developpeur, je veux des routers de moins de 500 lignes, afin de naviguer et maintenir le code sans devoir chercher dans des fichiers monolithiques.

**Criteres d'acceptation** :
- [ ] `chat.py` (1408L) est eclate en : `chat_core.py` (CRUD, envoi), `chat_streaming.py` (SSE), `chat_context.py` (entites, memoire)
- [ ] `crm.py` (1425L) est eclate en : `crm_contacts.py`, `crm_pipeline.py`, `crm_activities.py`, `crm_sync.py`
- [ ] `email.py` (1424L) est eclate en : `email_core.py`, `email_send.py`, `email_sync.py`, `email_setup.py`
- [ ] `calendar.py` (1342L) est eclate en : `calendar_events.py`, `calendar_providers.py`, `calendar_sync.py`
- [ ] Les PRAGMA SQLite dupliques sont centralises dans `models/database.py`
- [ ] Aucun router ne depasse 600 lignes
- [ ] L'API REST est inchangee (memes paths, memes schemas)
- [ ] Les 850 tests passent sans modification

**Notes** :
- Le pattern est deja valide : `api.ts` (3030L) a ete eclate en 14 modules, `SettingsModal.tsx` en 6 tabs
- Utiliser des sous-routers FastAPI (`APIRouter(prefix=...)` inclus dans le router principal)

---

## Epic 5 : Infrastructure & Fiabilite

### US-103 : Monitoring et logs structures
**Epic** : Infrastructure & Fiabilite | **Priorite** : P0 | **Effort** : L
**Axes** : DevOps | **Source** : [C] DevOps - 0 monitoring, logs non structures, pas de rotation

> En tant que developpeur deployant THERESE en collectivite, je veux des logs structures et une rotation automatique, afin de diagnostiquer les incidents sans saturer le disque.

**Criteres d'acceptation** :
- [ ] Les logs backend sont au format JSON structure (timestamp, level, module, message, extra)
- [ ] `structlog` ou `python-json-logger` est integre dans `main.py`
- [ ] La rotation des logs est configuree (max 10 Mo par fichier, 5 fichiers conserves)
- [ ] Les logs sont ecrits dans `~/.therese/logs/` (pas stdout seul)
- [ ] Un endpoint `/api/health` retourne : version, uptime, DB size, nombre de conversations, providers actifs
- [ ] Un endpoint `/api/metrics` expose les metriques de base (requetes/min, erreurs, latence P50/P95)
- [ ] Les 35 `console.log` frontend sont remplaces par un logger conditionnel (desactive en build Tauri)
- [ ] La retention des logs est bornee a 30 jours

**Notes** :
- Pas de stack lourde (Prometheus/Grafana) pour l'instant - on reste local-first
- `structlog` est plus idiomatique Python que `python-json-logger`
- L'endpoint `/api/health` servira aussi pour le monitoring des collectivites
- Les 35 console.log sont repartis dans 10 fichiers frontend (grep confirme)

---

### US-106 : Circuit breaker et fallback LLM runtime
**Epic** : Infrastructure & Fiabilite | **Priorite** : P1 | **Effort** : L
**Axes** : Resilience | **Source** : [C] Resilience - Pas de circuit breaker LLM, fallback limite a l'init

> En tant qu'entrepreneur en plein echange avec un client, je veux que THERESE bascule automatiquement sur un autre modele si mon provider principal tombe, afin de ne jamais etre bloque.

**Criteres d'acceptation** :
- [ ] Un circuit breaker est implemente dans `llm.py` : apres 3 erreurs consecutives sur un provider, il est desactive pour 60 secondes
- [ ] Le fallback LLM fonctionne au runtime (pas seulement a l'init) : si le provider selectionne echoue, THERESE tente le provider suivant dans l'ordre de preference de l'utilisateur
- [ ] Le retry est applique aux appels LLM streaming (1 retry avec backoff exponentiel)
- [ ] L'utilisateur est notifie dans le chat quand un fallback est active ("Provider X indisponible, je passe sur Y")
- [ ] Le backup automatique SQLite est configure (copie quotidienne dans `~/.therese/backups/`, retention 7 jours)
- [ ] Un test unitaire simule la defaillance d'un provider et verifie le fallback

**Notes** :
- L'orchestrateur LLM est dans `src/backend/app/services/llm.py` (7 except Exception a nettoyer en meme temps)
- Les providers sont dans `src/backend/app/services/providers/`
- Pattern circuit breaker simple : compteur d'erreurs + timestamp de reouverture, pas besoin de bibliotheque externe
- Le backup SQLite peut utiliser `sqlite3.backup()` (API native Python)

---

## Epic 6 : Experience Utilisateur

### US-111 : Eclater ChatLayout et ChatInput
**Epic** : Experience Utilisateur | **Priorite** : P2 | **Effort** : L
**Axes** : Frontend | **Source** : [C] Frontend - ChatLayout 500L 18 useState, ChatInput 879L monolithe

> En tant que developpeur, je veux des composants chat de moins de 200 lignes, afin de pouvoir modifier l'UX du chat sans risque de regression.

**Criteres d'acceptation** :
- [ ] `ChatLayout` (500L, 18 useState) est decompose en : `ChatHeader`, `ChatMessages`, `ChatFooter`, `ChatSidebar`
- [ ] Les 18 useState sont migres vers le chatStore Zustand existant (max 5 useState locaux dans ChatLayout)
- [ ] `ChatInput` (879L) est decompose en : `ChatInput` (textarea + envoi), `ChatAttachments`, `ChatVoiceButton`, `ChatPromptSuggestions`
- [ ] La transition CSS globale `*` est remplacee par des classes ciblees sur les elements qui transitionnent
- [ ] Aucune regression visuelle (tester manuellement : envoi message, streaming, code blocks, voice, attachments)
- [ ] Les raccourcis clavier fonctionnent toujours

**Notes** :
- Le chatStore Zustand existe deja dans `src/frontend/src/stores/`
- Le pattern de decomposition est deja valide sur SettingsModal (split en 6 tabs)
- La transition `* { transition: ... }` est potentiellement couteuse en repaints

---

### US-115 : Documentation utilisateur in-app
**Epic** : Experience Utilisateur | **Priorite** : P3 | **Effort** : XL
**Axes** : Produit | **Source** : [C] Produit - Pas de documentation in-app, parcours decouverte implicite

> En tant qu'entrepreneur decouvrant THERESE, je veux un guide interactif in-app, afin de comprendre les fonctionnalites sans lire une documentation externe.

**Criteres d'acceptation** :
- [ ] Un systeme de tooltips contextuels s'affiche au premier lancement post-onboarding (5-7 etapes couvrant chat, memoire, skills, settings)
- [ ] Un panneau "Aide" accessible via `?` ou un bouton dans la sidebar liste les raccourcis clavier et les fonctionnalites
- [ ] Le mode demo est rendu decouvrable (bouton visible dans l'onboarding, pas cache)
- [ ] Des metriques d'usage basiques sont collectees localement (nombre de conversations, skills utilisees, providers actifs) - pas de telemetrie externe
- [ ] Un "What's new" s'affiche au premier lancement apres une mise a jour

**Notes** :
- Le mode demo existe deja mais est cache (signale par l'audit)
- Les metriques restent 100% locales (coherent avec la promesse zero cloud)
- Pas de framework de tour guide lourd - un composant maison avec Zustand pour l'etat "deja vu"
- A coupler avec l'onboarding existant dans `src/frontend/src/components/onboarding/`

---

## Sprint 0 - P0 (2 semaines)

**Objectif** : Corriger les 4 points critiques bloquants pour un deploiement en collectivite.
**Score cible** : 69.2 -> ~73/100

| # | Story | Effort | Responsable | Jours estimes |
|---|-------|--------|-------------|---------------|
| 1 | US-100 : Chat accessible (aria-live + boutons) | M | Frontend | 3 |
| 2 | US-101 : Eliminer except Exception silencieux | L | Backend | 5 |
| 3 | US-102 : Politique confidentialite in-app | S | Frontend + Ludo (contenu) | 2 |
| 4 | US-103 : Monitoring et logs structures | L | Backend + DevOps | 5 |

**Total** : ~15 jours-dev
**Validation** : relancer UltraJury apres le sprint pour mesurer la progression.

---

## Roadmap

### Sprint 1 - P1 Quick Wins (2 semaines)

| Story | Effort |
|-------|--------|
| US-104 : GZipMiddleware | XS (0.5j) |
| US-107 : Harmoniser tutoiement | S (2j) |
| US-109 : Restreindre Tauri FS | S (2j) |
| US-110 : Corriger N+1 chat | S (2j) |

**Score cible** : ~75/100

### Sprint 2 - P1 Structurel (2 semaines)

| Story | Effort |
|-------|--------|
| US-105 : Virtualisation messages | M (3j) |
| US-106 : Circuit breaker LLM | L (5j) |
| US-108 : Sous-traitants LLM + consentement | M (3j) |

**Score cible** : ~78/100

### Sprint 3 - P2 Refactoring (3 semaines)

| Story | Effort |
|-------|--------|
| US-111 : Eclater ChatLayout/ChatInput | L (5j) |
| US-112 : Tests frontend 6% -> 25% | XL (8j) |
| US-113 : Formulaires accessibles | M (3j) |
| US-114 : Eclater routers backend | L (5j) |

**Score cible** : ~82/100

### Sprint 4 - P3 Polish (a planifier)

| Story | Effort |
|-------|--------|
| US-115 : Documentation in-app | XL (8j) |

**Score cible** : 85+/100

---

## Matrice effort/impact

```
Impact eleve
     |
     |  US-104(XS)  US-101(L)  US-103(L)
     |  US-100(M)   US-106(L)
     |  US-110(S)   US-102(S)
     |  US-107(S)   US-108(M)  US-109(S)
     |------------------------------------ Effort
     |  US-105(M)   US-111(L)
     |  US-113(M)   US-114(L)
     |               US-112(XL) US-115(XL)
     |
Impact faible
```

---

*Genere le 25/03/2026 a partir de l'audit UltraJury Phase 2 (score 69.2/100)*
*Prochaine revue : fin Sprint 0 (estimation semaine 15)*
