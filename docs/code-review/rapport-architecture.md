# Rapport d'Architecture - THERESE V2

**Date** : 28 janvier 2026
**Auditeur** : Claude Opus 4.5 (architecte logiciel senior)
**Version auditee** : MVP v3.1

---

## Resume executif

THERESE V2 est un assistant IA desktop (FastAPI + React/Tauri) pour solopreneurs francais. L'architecture suit un pattern classique backend/frontend decouples communicant via REST/SSE. Le projet a grandi rapidement d'un MVP chat vers un produit riche (CRM, email, calendrier, MCP, board strategique, skills Office, etc.) en une semaine de developpement intensif.

### Forces

- **Separation routeur/service/modele** globalement respectee cote backend
- **Pattern Provider** bien implemente pour Email, Calendar, LLM (ABC + Factory)
- **Gestion des erreurs** centralisee avec `TheresError` et messages en francais
- **Securite des cles API** : chiffrement Fernet en base
- **Lifespan propre** : startup/shutdown bien geree dans `main.py`
- **Zustand stores** bien scopees avec persistance selective
- **CORS restreint** aux origines Tauri/Vite (pas de wildcard)

### Faiblesses principales

- **3 God Classes** : `llm.py` (1503l), `api.ts` (2944l), `SettingsModal.tsx` (2169l)
- **Singletons globaux** partout (`global _xxx_service`) sans injection de dependances
- **Mixite sync/async** dans CRM sync (Session sync dans service async)
- **`except Exception` generique** (106 occurrences dans 34 fichiers)
- **Imports `json` redondants** dans `llm.py` (11 fois dans des boucles internes)
- **Pas de validation CORS dynamique** : origines hardcodees
- **Pas de rate limiting** sur les endpoints API
- **Pas de tests d'integration** backend (seulement 103 unit tests + 18 E2E)

---

## Findings

### ARCH-001 : God Class - `llm.py` (1503 lignes)

- **Severite** : HIGH
- **Fichier(s)** : `src/backend/app/services/llm.py`
- **Description** : Ce fichier contient TOUT le service LLM : configuration, contexte, 6 providers de streaming (Anthropic, OpenAI, Gemini, Mistral, Grok, Ollama), tool calling pour 2 providers, formatage des contextes, et gestion des cles API. C'est la classe la plus critique du projet et elle accumule trop de responsabilites.
- **Impact** : Risque eleve de regression lors de l'ajout d'un nouveau provider ou d'une modification du tool calling. Testabilite tres faible. Couplage fort avec la DB via `_get_api_key_from_db()` qui cree un moteur SQLAlchemy synchrone a chaque appel.
- **Remediation** :
  1. Extraire chaque provider dans un module separe : `providers/anthropic.py`, `providers/openai.py`, etc.
  2. Creer une interface `BaseLLMProvider(ABC)` avec `stream()`, `stream_with_tools()`, `continue_with_tools()`
  3. Extraire `ContextWindow` dans `context.py`
  4. Extraire `_get_api_key_from_db` dans `services/api_keys.py`
  5. Extraire le system prompt builder dans `prompt_builder.py`
- **Effort estime** : L

---

### ARCH-002 : God Class - `api.ts` (2944 lignes)

- **Severite** : HIGH
- **Fichier(s)** : `src/frontend/src/services/api.ts`
- **Description** : Ce fichier unique contient TOUS les types TypeScript et TOUTES les fonctions d'appel API du frontend. Il definit 80+ interfaces/types et 60+ fonctions couvrant chat, contacts, projets, skills, images, board, MCP, email, calendar, tasks, invoices, CRM, performance, escalation, RGPD, etc.
- **Impact** : Import massif depuis tous les composants. Temps de compilation impacte. Impossible de tree-shaker par domaine. Difficulte a retrouver une fonction specifique.
- **Remediation** :
  1. Decouvrir par domaine : `api/chat.ts`, `api/contacts.ts`, `api/llm.ts`, `api/skills.ts`, `api/email.ts`, `api/calendar.ts`, `api/crm.ts`, etc.
  2. Fichier `api/types.ts` pour les types partages (ApiError, request helper)
  3. Barrel export depuis `api/index.ts`
- **Effort estime** : M

---

### ARCH-003 : God Class - `SettingsModal.tsx` (2169 lignes)

- **Severite** : HIGH
- **Fichier(s)** : `src/frontend/src/components/settings/SettingsModal.tsx`
- **Description** : Ce composant unique gere 8 onglets (profile, api, tools, data, accessibility, performance, personalisation, escalation) avec 20+ useState hooks, 15+ handlers async. Il contient la configuration de tous les providers LLM, les providers images, la gestion Ollama, le profil utilisateur, le dossier de travail, les stats, la recherche web, etc.
- **Impact** : Re-render excessif a chaque changement d'etat. Bundle size impacte (tout est charge meme si un seul onglet est ouvert). Maintenabilite tres faible.
- **Remediation** :
  1. Extraire chaque onglet dans un composant dedie : `ProfileTab.tsx`, `LLMTab.tsx`, `DataTab.tsx`, `PerformanceTab.tsx`, etc.
  2. Utiliser un pattern de lazy loading pour chaque onglet
  3. Le composant `SettingsModal` ne garde que le layout (tabs + routing)
  4. Deplacer les constantes `PROVIDERS`, `IMAGE_PROVIDERS` dans des fichiers de config
- **Effort estime** : M

---

### ARCH-004 : Singletons globaux sans injection de dependances

- **Severite** : MEDIUM
- **Fichier(s)** : `src/backend/app/services/llm.py:1404`, `services/qdrant.py:31-39`, `services/error_handler.py:206-216`, `services/embeddings.py:21-28`, `services/token_tracker.py:141-145`, `services/skills/registry.py:189-202`, `services/mcp_service.py`
- **Description** : Pratiquement tous les services utilisent des variables `global` ou des singletons `__new__` pour maintenir une instance unique. Aucune injection de dependances n'est utilisee. Les services se recuperent mutuellement via des imports et des fonctions `get_xxx_service()`.
- **Impact** : Testabilite tres difficile (impossible de mocker sans monkey-patching). Couplage fort entre services. Risque de race conditions dans les singletons avec `_statuses` et `_last_check` de `ServiceStatus` (dict mutable partage).
- **Remediation** :
  1. Introduire un container DI leger (ex: `dependency-injector` ou simplement FastAPI `Depends()`)
  2. Passer les services en dependances des routers via `Depends()`
  3. Les singletons thread-safe avec `asyncio.Lock` si necessaire
- **Effort estime** : L

---

### ARCH-005 : Mixite sync/async dans CRM Sync

- **Severite** : HIGH
- **Fichier(s)** : `src/backend/app/services/crm_sync.py:78,131,159,245`
- **Description** : `CRMSyncService.__init__` attend un `Session` synchrone (from `sqlmodel`), mais les methodes internes (`_sync_contacts`, `_sync_projects`, `_sync_deliverables`) sont declarees `async`. Le code utilise `self.session.get()`, `self.session.add()`, `self.session.commit()` qui sont des operations synchrones sur un objet `Session` synchrone. Les fonctions helper (`get_crm_config`, `set_crm_spreadsheet_id`, etc.) utilisent aussi `session.exec()` synchrone.
- **Impact** : Blocage potentiel de la boucle asyncio pendant les operations DB. En production avec SQLite, cela peut provoquer des timeouts car les operations DB bloquent le thread principal.
- **Remediation** :
  1. Migrer `CRMSyncService` vers `AsyncSession`
  2. Remplacer `session.get()` par `await session.get()`
  3. Remplacer `session.exec()` par `await session.execute()`
  4. Remplacer `session.commit()` par `await session.commit()`
  5. Utiliser `run_in_executor` en attendant si la migration est trop lourde
- **Effort estime** : M

---

### ARCH-006 : Acces synchrone a la DB dans le service LLM

- **Severite** : HIGH
- **Fichier(s)** : `src/backend/app/services/llm.py:32-61`
- **Description** : La fonction `_get_api_key_from_db()` cree un moteur SQLAlchemy **synchrone** (`create_engine`) a chaque appel pour recuperer les cles API. Cette fonction est appelee depuis `_default_config()` qui est elle-meme appelee dans le constructeur `LLMService.__init__()`. Chaque creation d'une instance LLM ouvre une connexion synchrone a la DB.
- **Impact** : Chaque requete chat cree potentiellement 4 connexions synchrones a la DB (une par provider verifie dans `_default_config`). Blocage de la boucle asyncio. Fuites potentielles de connexions.
- **Remediation** :
  1. Charger les cles API au startup et les cacher (comme fait pour le profil utilisateur)
  2. Utiliser l'`AsyncSession` existante du framework FastAPI
  3. Passer les cles API en parametre au lieu de les charger depuis la DB dans le constructeur
- **Effort estime** : M

---

### ARCH-007 : `except Exception` generique massif

- **Severite** : MEDIUM
- **Fichier(s)** : 34 fichiers, 106+ occurrences (voir grep ci-dessus)
- **Description** : L'utilisation de `except Exception` sans distinction du type d'erreur est omnipresente. Dans `llm.py`, les erreurs JSON parse sont melangees avec les erreurs reseau. Dans `crm_sync.py`, les erreurs de mapping de donnees sont melangees avec les erreurs DB. Certains `except Exception:` (sans `as e`) avalent silencieusement les erreurs.
- **Impact** : Diagnostic difficile en production. Des bugs peuvent etre masques. Le `TheresError` centralise existe mais n'est pas utilise systematiquement.
- **Remediation** :
  1. Remplacer les `except Exception` par des exceptions specifiques (HTTPError, JSONDecodeError, SQLAlchemyError, etc.)
  2. Utiliser `classify_llm_error()` et `classify_http_error()` du `error_handler.py` existant
  3. Logger avec `logger.exception()` au lieu de `logger.error()` pour preserver la stacktrace
  4. Auditer les 25 `except Exception:` (sans `as e`) qui avalent les erreurs
- **Effort estime** : M

---

### ARCH-008 : Pas de rate limiting sur les endpoints API

- **Severite** : MEDIUM
- **Fichier(s)** : `src/backend/app/main.py:130-142`
- **Description** : Aucun middleware de rate limiting n'est configure. Les endpoints LLM, voice, images, et board sont tous accessibles sans limitation. Meme si l'application est locale (Tauri), les endpoints ecoutent sur `127.0.0.1:8000` et sont accessibles par tout processus local.
- **Impact** : Un script malveillant local pourrait consommer les credits API (Anthropic, OpenAI, etc.) en bombardant les endpoints. Le board strategique fait 5 appels LLM par requete, multipliant le cout.
- **Remediation** :
  1. Ajouter `slowapi` ou un middleware custom avec limite par endpoint
  2. Limiter specifiquement `/api/chat/send`, `/api/board/deliberate`, `/api/images/generate`
  3. Le `token_tracker.py` existant pourrait etre utilise pour limiter automatiquement
- **Effort estime** : S

---

### ARCH-009 : Imports `json` redondants dans les boucles de streaming

- **Severite** : LOW
- **Fichier(s)** : `src/backend/app/services/llm.py:482,558,588,676,771,891,936,972,1093,1159`
- **Description** : Le module `json` est importe au niveau du fichier (ligne 8) mais est re-importe 10 fois a l'interieur de boucles `for`/`while` dans les methodes de streaming. L'instruction `import json` dans une boucle n'a pas de cout significatif en Python (le module est cache dans `sys.modules`), mais c'est un code smell qui revele un copier-coller.
- **Impact** : Lisibilite reduite. Indice de code duplique entre les providers.
- **Remediation** : Supprimer les 10 `import json` internes, le module est deja importe en tete de fichier.
- **Effort estime** : S

---

### ARCH-010 : ServiceStatus singleton avec etat mutable non thread-safe

- **Severite** : MEDIUM
- **Fichier(s)** : `src/backend/app/services/error_handler.py:203-243`
- **Description** : `ServiceStatus` utilise un pattern singleton avec `__new__` et stocke l'etat dans des attributs de classe (`_statuses`, `_last_check`). Ces dicts sont mutes depuis plusieurs coroutines asyncio sans verrou. L'import `import time` est fait a l'interieur des methodes au lieu du module.
- **Impact** : Race condition theorique si deux coroutines mettent a jour le meme service simultanement. L'import inline de `time` est un code smell.
- **Remediation** :
  1. Ajouter un `asyncio.Lock` pour les mutations
  2. Deplacer `import time` en tete de fichier
  3. Considerer `dataclasses` ou un `dict` protege par lock
- **Effort estime** : S

---

### ARCH-011 : Duplication du parsing SSE entre `streamMessage` et `streamDeliberation`

- **Severite** : LOW
- **Fichier(s)** : `src/frontend/src/services/api.ts:193-243` et `api.ts:981-1040`
- **Description** : Le code de parsing SSE (lecture du reader, decodage, split par lignes, extraction `data:`, JSON parse) est duplique quasi identiquement entre `streamMessage()` et `streamDeliberation()`. Un troisieme usage similaire existe probablement dans les fonctions email/CRM.
- **Impact** : Tout bug dans le parsing SSE doit etre corrige a N endroits.
- **Remediation** : Extraire une fonction generique `streamSSE<T>(url, body): AsyncGenerator<T>` reutilisable.
- **Effort estime** : S

---

### ARCH-012 : Pas de validation du `conversation_id` cote frontend

- **Severite** : MEDIUM
- **Fichier(s)** : `src/frontend/src/stores/chatStore.ts:126-177`
- **Description** : Dans `addMessage`, si aucune conversation n'existe, un ID est genere localement (`generateId()`). Ce ID est ensuite envoye au backend qui cree une conversation avec. Il n'y a pas de validation que l'ID n'entre pas en collision. Si la conversation est deja creee cote backend, un conflit peut survenir.
- **Impact** : La synchronisation frontend-backend des conversations peut se desynchroniser, causant des erreurs 404 (bug deja rencontre et documente dans CLAUDE.md).
- **Remediation** :
  1. Toujours creer la conversation cote backend d'abord (`POST /api/chat/conversations`)
  2. Utiliser l'ID retourne par le backend
  3. Ou utiliser UUIDv4 des deux cotes (collision quasi impossible)
- **Effort estime** : S

---

### ARCH-013 : Hardcoded API base URL dans `api.ts`

- **Severite** : MEDIUM
- **Fichier(s)** : `src/frontend/src/services/api.ts:7`
- **Description** : `API_BASE = 'http://127.0.0.1:8000'` est hardcode. En mode Tauri production, le port pourrait etre different. Il n'y a pas de configuration d'environnement pour le frontend.
- **Impact** : Impossible de deployer sur un port different sans modifier le code source.
- **Remediation** :
  1. Utiliser une variable d'environnement Vite (`import.meta.env.VITE_API_BASE`)
  2. Ou detecter dynamiquement via Tauri config
  3. Valeur par defaut : `http://127.0.0.1:8000`
- **Effort estime** : S

---

### ARCH-014 : Pas de pagination reelle dans les stores Zustand

- **Severite** : LOW
- **Fichier(s)** : `src/frontend/src/stores/chatStore.ts`, `stores/emailStore.ts`
- **Description** : Le `chatStore` charge TOUTES les conversations et tous leurs messages en memoire. Il n'y a pas de pagination locale ni de chargement a la demande. Le `emailStore` a un `pageToken` et `hasMore` mais ceux-ci ne sont pas utilises pour la pagination dans le store lui-meme.
- **Impact** : Avec beaucoup de conversations/messages, la consommation memoire augmente lineairement. Le persist Zustand serialise tout dans localStorage.
- **Remediation** :
  1. Implementer un chargement a la demande (load messages only when conversation is opened)
  2. Limiter le nombre de conversations en memoire (LRU)
  3. Ne persister que les IDs dans localStorage, charger le contenu depuis le backend
- **Effort estime** : M

---

### ARCH-015 : `CRMImportService` - Classe `ImportError` masque le builtin Python

- **Severite** : LOW
- **Fichier(s)** : `src/backend/app/services/crm_import.py:29`
- **Description** : La dataclass `ImportError` a le meme nom que le builtin Python `ImportError` (erreur d'import de module). Cela masque le builtin dans tout le scope du fichier.
- **Impact** : Si un `import` echoue dans ce fichier, l'exception levee sera le builtin `ImportError`, pas la dataclass, mais cela peut creer de la confusion lors du debug.
- **Remediation** : Renommer en `CRMImportError` ou `ImportRowError`.
- **Effort estime** : S

---

### ARCH-016 : Configuration `Settings` desynchronisee avec la realite

- **Severite** : MEDIUM
- **Fichier(s)** : `src/backend/app/config.py:38`
- **Description** : Le champ `llm_provider` dans `Settings` est de type `Literal["claude", "mistral", "ollama"]` alors que le `LLMProvider` enum dans `llm.py` supporte 6 providers (anthropic, openai, gemini, mistral, grok, ollama). Les noms sont aussi differents ("claude" vs "anthropic"). Les modeles par defaut dans config (`claude_model = "claude-sonnet-4-20250514"`) ne correspondent plus aux modeles actuels (`claude-opus-4-5-20251101`).
- **Impact** : La configuration via `.env` utilise des valeurs obsoletes. Les `Settings` ne refletent plus l'etat reel du systeme.
- **Remediation** :
  1. Mettre a jour `Settings.llm_provider` avec les 6 providers
  2. Harmoniser les noms (anthropic partout, pas claude)
  3. Mettre a jour les modeles par defaut
  4. Ou mieux : supprimer les champs LLM de `Settings` et s'appuyer entierement sur la DB
- **Effort estime** : S

---

### ARCH-017 : MCP - Execution de commandes arbitraires

- **Severite** : CRITICAL
- **Fichier(s)** : `src/backend/app/services/mcp_service.py:95-99`
- **Description** : Le service MCP lance des sous-processus avec les commandes configurees par l'utilisateur (via `subprocess` ou `asyncio.create_subprocess_exec`). Les commandes et arguments viennent du fichier `~/.therese/mcp_servers.json` qui peut etre modifie par n'importe quel processus local. Il n'y a pas de whitelist de commandes autorisees.
- **Impact** : Un processus malveillant local pourrait modifier `mcp_servers.json` pour injecter des commandes arbitraires qui seraient executees avec les privileges de l'utilisateur.
- **Remediation** :
  1. Verifier que les commandes MCP sont dans un chemin connu (node_modules, npx, uvx)
  2. Ajouter une validation des commandes autorisees
  3. Logger toutes les executions de commandes MCP
  4. Signer ou hasher le fichier de config (mesure avancee)
  5. L'onboarding SecurityStep documente deja le risque - bien
- **Effort estime** : M

---

### ARCH-018 : Pattern de duplication du code d'export CRM

- **Severite** : LOW
- **Fichier(s)** : `src/backend/app/services/crm_export.py:130-230` vs `crm_export.py:572-613`
- **Description** : Le code de styling Excel (header_font, header_fill, border, etc.) est duplique entre `export_to_xlsx()` et `_populate_xlsx_sheet()`. Les deux fonctions appliquent les memes styles de la meme maniere.
- **Impact** : Toute modification de style doit etre faite en double.
- **Remediation** : Extraire les styles dans une constante ou une fonction `_get_xlsx_styles()`.
- **Effort estime** : S

---

### ARCH-019 : Pas de validation des inputs dans les calculateurs

- **Severite** : LOW
- **Fichier(s)** : `src/backend/app/routers/calculators.py` (via `api.ts`)
- **Description** : Les calculateurs financiers (ROI, ICE, RICE, NPV, Break-even) recoivent des nombres depuis le frontend sans validation de plage. Une division par zero est possible dans le calcul de break-even si `unit_cost` est egal a `unit_price`.
- **Impact** : Crash 500 potentiel sur des inputs invalides.
- **Remediation** :
  1. Ajouter des validateurs Pydantic avec `Field(ge=0)` ou `Field(gt=0)`
  2. Gerer la division par zero explicitement
- **Effort estime** : S

---

### ARCH-020 : Board deliberation - Pas de timeout par conseiller

- **Severite** : MEDIUM
- **Fichier(s)** : `src/backend/app/services/board.py`
- **Description** : La deliberation du board fait 5 appels LLM sequentiels (un par conseiller) + 1 pour la synthese. Si un provider est lent ou ne repond pas, toute la deliberation est bloquee. Le timeout httpx est de 120s, donc une deliberation pourrait prendre jusqu'a 12 minutes (6 x 120s) en pire cas.
- **Impact** : L'utilisateur attend sans feedback si un provider est down. L'UI montre un spinner indefini.
- **Remediation** :
  1. Ajouter un timeout par conseiller (30s max)
  2. Paralleliser les appels conseillers avec `asyncio.gather(..., return_exceptions=True)`
  3. Si un conseiller timeout, afficher "indisponible" et continuer
  4. La synthese se fait avec les avis disponibles
- **Effort estime** : M

---

### ARCH-021 : `emailStore` persiste les comptes email dans localStorage

- **Severite** : MEDIUM
- **Fichier(s)** : `src/frontend/src/stores/emailStore.ts:157-165`
- **Description** : Le store email persiste les objets `accounts` via Zustand persist dans localStorage. Ces objets pourraient contenir des tokens OAuth ou d'autres donnees sensibles selon l'implementation de `EmailAccount`.
- **Impact** : Les tokens OAuth seraient accessibles a tout script s'executant dans le contexte de la WebView Tauri.
- **Remediation** :
  1. Ne pas persister les comptes avec tokens dans localStorage
  2. Persister uniquement les IDs des comptes, recharger les donnees depuis le backend
  3. Les tokens doivent rester cote backend (deja chiffres en DB)
- **Effort estime** : S

---

### ARCH-022 : Utilisation de `datetime.utcnow()` deprece

- **Severite** : LOW
- **Fichier(s)** : Multiple (entities.py, crm_sync.py, crm_export.py, board.py, etc.)
- **Description** : `datetime.utcnow()` est deprece depuis Python 3.12 au profit de `datetime.now(timezone.utc)`. L'ancien appel ne retourne pas un datetime timezone-aware, ce qui peut causer des comparaisons incorrectes.
- **Impact** : Pas de bug immediat mais non-conformite avec les recommandations Python modernes.
- **Remediation** : Remplacer par `datetime.now(timezone.utc)` partout.
- **Effort estime** : S

---

### ARCH-023 : Pas de migration Alembic pour les nouvelles entites

- **Severite** : MEDIUM
- **Fichier(s)** : `src/backend/app/models/database.py:71`, `entities.py`
- **Description** : La creation des tables utilise `SQLModel.metadata.create_all()` qui ne gere pas les migrations (ajout de colonnes, renommage, etc.). Alembic est dans les dependances mais l'entite `BoardDecisionDB`, `Deliverable`, et les champs RGPD sur `Contact` ont ete ajoutes sans migration.
- **Impact** : Si un utilisateur met a jour l'application, les nouvelles colonnes ne seront pas ajoutees a sa DB existante. `create_all` ne fait que creer les tables manquantes, pas modifier les existantes.
- **Remediation** :
  1. Generer des migrations Alembic pour chaque changement de schema
  2. Executer `alembic upgrade head` au startup
  3. Ou au minimum, ajouter un check de schema au demarrage avec `ALTER TABLE` fallback
- **Effort estime** : M

---

### ARCH-024 : Skills Registry - Cache en memoire sans eviction

- **Severite** : LOW
- **Fichier(s)** : `src/backend/app/services/skills/registry.py:176-180`
- **Description** : Le `_file_cache` du SkillsRegistry est un dict en memoire sans limite de taille ni TTL. Chaque fichier genere (DOCX, PPTX, XLSX) est stocke indefiniment en memoire via son `SkillResult` (qui contient le `file_path`).
- **Impact** : Fuite memoire progressive si beaucoup de fichiers sont generes. Les `Path` eux-memes sont legers, mais sans eviction, le dict grandit indefiniment.
- **Remediation** :
  1. Ajouter un `maxsize` au cache (ex: 100 derniers fichiers)
  2. Ou utiliser `functools.lru_cache` ou `cachetools.TTLCache`
  3. Nettoyer les fichiers physiques aussi (cron job ou au startup)
- **Effort estime** : S

---

### ARCH-025 : CORS origins hardcodes sans support production

- **Severite** : LOW
- **Fichier(s)** : `src/backend/app/main.py:132-137`
- **Description** : Les origines CORS sont hardcodees : `localhost:1420`, `localhost:5173`, `tauri://localhost`, `https://tauri.localhost`. C'est correct pour le dev et le build Tauri, mais pas configurable.
- **Impact** : Faible en pratique car l'app est locale. Mais si le port change ou si un mode "reseau local" est ajoute, il faudra modifier le code.
- **Remediation** : Charger depuis `Settings` ou une variable d'environnement.
- **Effort estime** : S

---

### ARCH-026 : `crm_sync.py` utilise `Session` synchrone mais l'entete dit `async`

- **Severite** : HIGH
- **Fichier(s)** : `src/backend/app/services/crm_sync.py:78`
- **Description** : Le constructeur `CRMSyncService.__init__` prend un `Session` (from `sqlmodel`) qui est synchrone. Les methodes `_sync_contacts`, `_sync_projects`, `_sync_deliverables` sont declarees `async def` mais utilisent uniquement des operations synchrones sur `self.session`. Les fonctions helper en bas du fichier (`get_crm_config`, `set_crm_spreadsheet_id`, etc.) utilisent aussi `session.exec()` synchrone.
- **Impact** : Meme impact que ARCH-005 (doublon identifie). Les operations synchrones bloquent la boucle asyncio.
- **Remediation** : Voir ARCH-005.
- **Effort estime** : (inclus dans ARCH-005)

---

### ARCH-027 : `chatStore` - Re-render en cascade via spread operator

- **Severite** : LOW
- **Fichier(s)** : `src/frontend/src/stores/chatStore.ts:182-196`
- **Description** : Les fonctions `updateMessage`, `setMessageEntities`, `setMessageMetadata` creent une nouvelle copie de tout l'arbre `conversations` (spread de l'array, spread de la conversation, spread des messages) a chaque mise a jour d'un seul message. Cela provoque un re-render de tous les composants abonnes au store.
- **Impact** : Performance degradee avec beaucoup de conversations/messages. Chaque caractere recu en streaming provoque un full tree copy.
- **Remediation** :
  1. Utiliser `immer` middleware de Zustand pour des mutations immutables efficaces
  2. Ou stocker les messages dans un Map par ID au lieu d'un array imbrique
  3. Utiliser des selectors granulaires dans les composants
- **Effort estime** : M

---

### ARCH-028 : Absence d'index SQL sur les colonnes filtrees

- **Severite** : MEDIUM
- **Fichier(s)** : `src/backend/app/models/entities.py`
- **Description** : Les entites `Contact`, `Project`, `Conversation` sont requetees avec des filtres sur `scope`, `scope_id`, `stage`, `status`, `contact_id`, mais aucun index SQL n'est defini en dehors des cles primaires. L'export CRM filtre aussi sur `stage` et `source`.
- **Impact** : Avec 50 contacts, l'impact est negligeable. Mais si le CRM croit a 500+ contacts avec beaucoup de conversations, les full table scans seront sensibles.
- **Remediation** :
  1. Ajouter `sa_column_kwargs={"index": True}` sur les champs frequemment filtres
  2. Minimalement : `Contact.stage`, `Contact.scope`, `Project.status`, `Project.contact_id`, `Conversation.updated_at`
- **Effort estime** : S

---

### ARCH-029 : Le global exception handler masque les erreurs FastAPI natives

- **Severite** : MEDIUM
- **Fichier(s)** : `src/backend/app/main.py:146-168`
- **Description** : Le `@app.exception_handler(Exception)` capture TOUTES les exceptions, y compris les `RequestValidationError` de Pydantic et les `HTTPException` de FastAPI. Cela masque les messages de validation natifs de FastAPI et retourne toujours un format `TheresError`.
- **Impact** : Les erreurs 422 de validation Pydantic sont transformees en erreurs 500 generiques. Le frontend ne recoit pas les details de validation.
- **Remediation** :
  1. N'intercepter que `TheresError` avec `@app.exception_handler(TheresError)`
  2. Laisser FastAPI gerer `HTTPException` et `RequestValidationError` nativement
  3. Garder un fallback pour `Exception` mais seulement pour les erreurs non-gerees
- **Effort estime** : S

---

### ARCH-030 : Pas de type hints sur les retours de `_get_api_key_from_db`

- **Severite** : LOW
- **Fichier(s)** : `src/backend/app/services/llm.py:21-61`
- **Description** : La fonction `_get_api_key_from_db` a un type hint retour `str | None` correct. Cependant, elle importe `create_engine` et `text` a chaque appel au lieu du niveau module. Elle cree aussi un moteur SQLAlchemy synchrone a chaque invocation.
- **Impact** : Voir ARCH-006. Doublon d'impact, code smell.
- **Remediation** : Voir ARCH-006.
- **Effort estime** : (inclus dans ARCH-006)

---

### ARCH-031 : Absence de tests d'integration backend

- **Severite** : MEDIUM
- **Fichier(s)** : `tests/`
- **Description** : Le projet a 103 unit tests backend et 18 tests E2E Playwright, mais pas de tests d'integration pour les endpoints API. Aucun test ne verifie le flux complet requete HTTP -> routeur -> service -> DB -> reponse.
- **Impact** : Les regressions sur les endpoints ne sont detectees qu'en E2E (lent) ou manuellement. Les tests unitaires mockent souvent les dependances et ne testent pas les interactions reelles.
- **Remediation** :
  1. Utiliser `httpx.AsyncClient` avec `app` pour des tests d'integration rapides
  2. Tester au minimum : chat send, contact CRUD, config API keys, skills execute
  3. Utiliser une DB SQLite en memoire pour les tests
- **Effort estime** : M

---

### ARCH-032 : `pyproject.toml` - Dependances sous-specifiees

- **Severite** : LOW
- **Fichier(s)** : `pyproject.toml:13-55`
- **Description** : Les dependances utilisent `>=` sans borne superieure (ex: `fastapi>=0.109.0`). Cela signifie qu'un `uv sync` futur pourrait installer des versions majeures incompatibles.
- **Impact** : Build non-reproductible. Une mise a jour de dependance pourrait casser le projet.
- **Remediation** :
  1. Ajouter des bornes superieures : `fastapi>=0.109.0,<1.0`
  2. Ou utiliser un lockfile (`uv.lock`) pour figer les versions exactes
  3. Le lockfile est la meilleure approche pour un projet de production
- **Effort estime** : S

---

### ARCH-033 : `accessibilityStore.ts` importe mais contenu non audite

- **Severite** : LOW
- **Fichier(s)** : `src/frontend/src/stores/accessibilityStore.ts`
- **Description** : Le store d'accessibilite est importe dans `SettingsModal.tsx` mais son contenu et son utilisation n'ont pas pu etre pleinement audites dans ce rapport. Il gere probablement les preferences d'accessibilite (reduced motion, contraste, etc.).
- **Impact** : Potentiellement des preferences qui ne sont pas correctement appliquees partout.
- **Remediation** : Auditer separement le module d'accessibilite.
- **Effort estime** : S

---

## Roadmap de refactoring

### Phase 1 - Corrections critiques (Sprint 1, 1 semaine)

| Priorite | Finding | Effort | Description |
|----------|---------|--------|-------------|
| 1 | ARCH-017 | M | Securiser MCP - whitelist commandes |
| 2 | ARCH-005/026 | M | Migrer CRM Sync vers AsyncSession |
| 3 | ARCH-006 | M | Cacher les cles API au startup, supprimer _get_api_key_from_db synchrone |
| 4 | ARCH-029 | S | Fix global exception handler (ne pas masquer FastAPI errors) |
| 5 | ARCH-008 | S | Ajouter rate limiting (slowapi) |

### Phase 2 - God Classes (Sprint 2, 2 semaines)

| Priorite | Finding | Effort | Description |
|----------|---------|--------|-------------|
| 6 | ARCH-001 | L | Decouvrir llm.py en providers modulaires |
| 7 | ARCH-002 | M | Decouvrir api.ts par domaine |
| 8 | ARCH-003 | M | Decouvrir SettingsModal en composants par onglet |

### Phase 3 - Architecture (Sprint 3, 2 semaines)

| Priorite | Finding | Effort | Description |
|----------|---------|--------|-------------|
| 9 | ARCH-004 | L | Introduire DI avec FastAPI Depends |
| 10 | ARCH-023 | M | Mettre en place les migrations Alembic |
| 11 | ARCH-020 | M | Paralleliser + timeout le board |
| 12 | ARCH-031 | M | Ajouter tests d'integration backend |

### Phase 4 - Qualite (Sprint 4, 1 semaine)

| Priorite | Finding | Effort | Description |
|----------|---------|--------|-------------|
| 13 | ARCH-007 | M | Remplacer except Exception generiques |
| 14 | ARCH-028 | S | Ajouter index SQL |
| 15 | ARCH-027 | M | Optimiser chatStore (immer ou Map) |
| 16 | ARCH-014 | M | Pagination reelle dans les stores |

### Phase 5 - Polish (Backlog)

| Priorite | Finding | Effort | Description |
|----------|---------|--------|-------------|
| 17 | ARCH-016 | S | Synchroniser Settings avec les providers reels |
| 18 | ARCH-013 | S | Externaliser API_BASE |
| 19 | ARCH-009 | S | Cleanup imports json redondants |
| 20 | ARCH-011 | S | Factoriser parsing SSE |
| 21 | ARCH-015 | S | Renommer ImportError |
| 22 | ARCH-018 | S | Factoriser styles Excel |
| 23 | ARCH-022 | S | Migrer vers datetime.now(timezone.utc) |
| 24 | ARCH-032 | S | Borner les dependances pyproject.toml |
| 25 | ARCH-010 | S | Thread-safe ServiceStatus |
| 26 | ARCH-021 | S | Ne pas persister tokens email dans localStorage |
| 27 | ARCH-024 | S | Ajouter eviction au cache skills |
| 28 | ARCH-012 | S | Valider conversation_id |
| 29 | ARCH-019 | S | Valider inputs calculateurs |
| 30 | ARCH-025 | S | Configurer CORS depuis Settings |

---

## Diagramme d'architecture actuel

```
+---------------------------------------------------------------+
|                        TAURI SHELL (macOS)                      |
|  +---------------------------+  +---------------------------+   |
|  |     Frontend (React)       |  |    Backend (FastAPI)       |  |
|  |                            |  |                            |  |
|  |  Zustand Stores:           |  |  Routers (22):             |  |
|  |   - chatStore              |  |   chat, memory, files,     |  |
|  |   - statusStore            |  |   config, skills, voice,   |  |
|  |   - personalisationStore   |  |   images, board, calc,     |  |
|  |   - emailStore             |  |   mcp, data, perf,         |  |
|  |   - calendarStore          |  |   personalisation,         |  |
|  |   - taskStore              |  |   escalation, email,       |  |
|  |   - invoiceStore           |  |   calendar, tasks,         |  |
|  |   - accessibilityStore     |  |   invoices, crm, rgpd,     |  |
|  |                            |  |   email_setup              |  |
|  |  Components:               |  |                            |  |
|  |   - ChatLayout             |  |  Services:                 |  |
|  |   - SettingsModal (2169l!) |  |   - llm.py (1503l!)        |  |
|  |   - BoardPanel             |  |   - mcp_service.py         |  |
|  |   - MemoryPanel            |  |   - board.py               |  |
|  |   - OnboardingWizard       |  |   - crm_import/export/sync |  |
|  |   - GuidedPrompts          |  |   - error_handler.py       |  |
|  |                            |  |   - skills/registry.py     |  |
|  |  API Service:              |  |   - email/providers        |  |
|  |   api.ts (2944l!)          |  |   - calendar/providers     |  |
|  |                            |  |   - encryption.py          |  |
|  |       HTTP/SSE             |  |   - performance.py         |  |
|  |   localhost:1420           |  |   - token_tracker.py       |  |
|  +------------|---------------+  +------------|---------------+  |
|               |    REST/SSE (port 8000)       |                  |
|               +-------------------------------+                  |
+---------------------------------------------------------------+
                              |
              +---------------+----------------+
              |               |                |
        +-----+-----+  +-----+-----+   +------+------+
        |  SQLite    |  |  Qdrant   |   |  MCP Servers |
        |  ~/.therese|  |  (vector) |   |  (stdio)     |
        |  /therese  |  |  768 dims |   |  filesystem  |
        |  .db       |  |  nomic-   |   |  fetch, git  |
        |            |  |  embed    |   |  notion, etc |
        +------------+  +-----------+   +------+-------+
                                               |
                     +-------------------------+----------+
                     |              |           |          |
               +-----+----+  +----+---+  +----+---+  +---+----+
               | Anthropic |  | OpenAI |  | Gemini |  | Mistral|
               | Claude    |  | GPT    |  | Google |  |  +Grok |
               | Opus 4.5  |  | 5.2    |  | 3 Pro  |  |  +Ollama
               +-----------+  +--------+  +--------+  +--------+
```

### Flux de donnees principal (Chat)

```
1. User tape un message dans ChatInput.tsx
2. chatStore.addMessage() stocke localement
3. api.streamMessage() POST /api/chat/send (SSE)
4. chat.py router recoit la requete
5. Recherche memoire dans Qdrant (contacts/projets pertinents)
6. LLMService.prepare_context() construit le prompt avec :
   - System prompt + user identity + THERESE.md
   - Memory context (contacts/projets)
   - Historique conversation
7. LLMService.stream_response_with_tools() appelle le provider LLM
8. Si tool_call (MCP ou web_search) :
   8a. Execute le tool via MCPService ou WebSearchService
   8b. Envoie le resultat au LLM pour continuation
9. SSE chunks streames vers le frontend
10. chatStore.updateMessage() met a jour le contenu
11. Apres la reponse : entity extraction en arriere-plan
12. Si entites detectees : SSE event "entities_detected"
13. EntitySuggestion.tsx affiche les suggestions
```

---

*Rapport genere le 28 janvier 2026 par Claude Opus 4.5*
*33 findings identifies (1 CRITICAL, 5 HIGH, 11 MEDIUM, 16 LOW)*
