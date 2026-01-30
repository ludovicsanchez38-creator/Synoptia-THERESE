# Rapport Qualite Code - THERESE V2

**Date** : 28 janvier 2026
**Auditeur** : Claude Opus 4.5
**Scope** : `src/backend/` (Python) + `src/frontend/src/` (TypeScript/React)

---

## Resume executif

**Score global : 62/100 - Correct avec des axes d'amelioration significatifs**

Le projet THERESE V2 est fonctionnel avec une architecture globalement coherente (FastAPI + React/Tauri). Les principales faiblesses identifiees sont :

1. **CRITICAL** : Secret OAuth (`client_secret`) passe en query parameter (visible dans les logs serveur, l'historique navigateur et les proxies)
2. **HIGH** : Utilisation massive de `datetime.utcnow()` (deprecie depuis Python 3.12, 100+ occurrences)
3. **HIGH** : Fichiers excessivement longs - 15 fichiers Python depassent 500 lignes, le plus gros atteint 1503 lignes
4. **HIGH** : 248 f-strings dans les appels `logger.*()` (evaluation systematique meme si le log level est desactive)
5. **MEDIUM** : Duplication de code significative (construction du provider IMAP repetee 4 fois, pattern singleton inconsistant)
6. **MEDIUM** : 318 usages de `Optional[X]` au lieu de `X | None` (style pre-3.10 melange avec le style moderne)

**Points positifs** :
- Chiffrement des cles API avec Fernet (AES-128-CBC + HMAC)
- Gestion d'erreurs centralisee avec messages en francais
- Bonne couverture des schemas Pydantic
- Architecture modulaire (routers, services, models)

---

## Metriques globales

| Metrique | Valeur |
|----------|--------|
| Nombre total de fichiers Python | **100** |
| Nombre total de fichiers TS/TSX | **110** |
| Fichiers >500 lignes (Python) | **15** (voir liste) |
| Fichiers >500 lignes (TS/TSX) | **6** (voir liste) |
| Fonctions >50 lignes | **~25** (voir liste) |
| Usages de `Any` (Python) | **~80** imports/usages |
| Usages de `any` (TypeScript) | **7** |
| `Optional[X]` (style ancien) | **318** occurrences |
| TODO trouves | **16** |
| `datetime.utcnow()` (deprecie) | **100+** occurrences |
| f-strings dans logger | **248** occurrences |
| `except Exception: pass` (silencieux) | **14** blocs |

### Fichiers >500 lignes (Python)

| Fichier | Lignes |
|---------|--------|
| `app/services/llm.py` | 1503 |
| `app/routers/crm.py` | 1387 |
| `app/routers/calendar.py` | 1238 |
| `app/routers/email.py` | 1180 |
| `app/routers/config.py` | 1053 |
| `app/routers/chat.py` | 976 |
| `app/models/schemas.py` | 864 |
| `app/services/crm_import.py` | 863 |
| `app/routers/data.py` | 782 |
| `app/routers/memory.py` | 767 |
| `app/services/crm_export.py` | 613 |
| `app/services/mcp_service.py` | 561 |
| `app/services/crm_sync.py` | 551 |
| `app/services/calendar/caldav_provider.py` | 552 |
| `app/services/skills/planning_skills.py` | 518 |

### Fichiers >500 lignes (TS/TSX)

| Fichier | Lignes |
|---------|--------|
| `services/api.ts` | 2944 |
| `components/settings/SettingsModal.tsx` | 2169 |
| `components/memory/MemoryPanel.tsx` | 827 |
| `components/settings/ToolsPanel.tsx` | 677 |
| `components/board/BoardPanel.tsx` | 527 |
| `components/chat/ChatInput.tsx` | 520 |

---

## Findings

### QUAL-001 : Secret OAuth passe en Query Parameter
- **Severite** : CRITICAL
- **Fichier** : `src/backend/app/routers/email.py:231-232`
- **Description** : Le `client_secret` Google OAuth est passe comme parametre de query string dans l'endpoint `POST /auth/initiate`. Les query parameters sont visibles dans les logs serveur HTTP, l'historique du navigateur, les outils de monitoring et les proxies intermediaires. C'est une fuite de secret.
- **Code** :
  ```python
  async def initiate_oauth(
      client_id: str = Query(..., description="Google OAuth client ID"),
      client_secret: str = Query(..., description="Google OAuth client secret"),
  ) -> OAuthInitiateResponse:
  ```
- **Remediation** : Passer `client_id` et `client_secret` dans le body de la requete POST (via un schema Pydantic) plutot qu'en query parameter.

---

### QUAL-002 : datetime.utcnow() deprecie (100+ occurrences)
- **Severite** : HIGH
- **Fichier** : 30+ fichiers dans `src/backend/`
- **Description** : `datetime.utcnow()` est deprecie depuis Python 3.12 (PEP 587). Il retourne un objet `datetime` naive (sans timezone), ce qui cause des bugs subtils lors de comparaisons avec des datetimes aware. Plus de 100 occurrences ont ete trouvees dans le projet.
- **Exemples** :
  - `app/models/entities.py:49` : `created_at: datetime = Field(default_factory=datetime.utcnow)`
  - `app/services/token_tracker.py:161,167,183,192,234`
  - `app/routers/config.py:40`
  - `app/routers/email.py:159,206,207,290,303,411`
  - `app/services/mcp_service.py:52,129`
  - `app/services/crm_sync.py:191,277,360,458,483,502,538,542`
  - Et 70+ autres occurrences
- **Remediation** : Remplacer par `datetime.now(datetime.UTC)` (Python 3.11+) ou `datetime.now(timezone.utc)`. Creer un helper `utc_now()` pour centraliser.

---

### QUAL-003 : f-strings dans les appels logger (248 occurrences)
- **Severite** : HIGH
- **Fichier** : 43 fichiers dans `src/backend/`
- **Description** : L'utilisation de f-strings dans les appels `logger.info(f"...")`, `logger.error(f"...")`, etc. force l'evaluation de l'interpolation de string **meme si le log level est desactive**. Cela degrade les performances, surtout pour `logger.debug()`.
- **Exemples** :
  - `app/services/llm.py` : 28 occurrences
  - `app/routers/crm.py` : 28 occurrences
  - `app/services/mcp_service.py` : 18 occurrences
  - `app/services/crm_sync.py` : 12 occurrences
- **Remediation** : Utiliser le lazy formatting : `logger.info("Started MCP server: %s (PID %d)", server.name, process.pid)`.

---

### QUAL-004 : Fichier llm.py de 1503 lignes (God Object)
- **Severite** : HIGH
- **Fichier** : `src/backend/app/services/llm.py` (1503 lignes)
- **Description** : Ce fichier concentre les implementations de streaming pour 6 providers LLM differents (Anthropic, OpenAI, Gemini, Mistral, Grok, Ollama), plus le tool calling, dans un seul module. C'est un "God Object" qui viole le principe de responsabilite unique.
- **Remediation** : Extraire chaque provider dans un module separe (`providers/anthropic.py`, `providers/openai.py`, etc.) avec une interface commune (Protocol/ABC). Garder `llm.py` comme facade/factory.

---

### QUAL-005 : api.ts de 2944 lignes (monolithe frontend)
- **Severite** : HIGH
- **Fichier** : `src/frontend/src/services/api.ts` (2944 lignes)
- **Description** : Toute la couche API du frontend est dans un seul fichier. Cela rend la navigation, la maintenance et les revues de code difficiles.
- **Remediation** : Decouper par domaine fonctionnel : `api/chat.ts`, `api/memory.ts`, `api/config.ts`, `api/email.ts`, `api/crm.ts`, etc. Garder un barrel export dans `api/index.ts`.

---

### QUAL-006 : SettingsModal.tsx de 2169 lignes
- **Severite** : HIGH
- **Fichier** : `src/frontend/src/components/settings/SettingsModal.tsx` (2169 lignes)
- **Description** : Le composant Settings regroupe 8+ onglets dans un seul fichier. Cela cree un composant geant difficile a maintenir.
- **Remediation** : Extraire chaque onglet en composant independant (`APISettings.tsx`, `LLMSettings.tsx`, `DataSettings.tsx`, etc.) et garder `SettingsModal.tsx` comme orchestrateur.

---

### QUAL-007 : Duplication du pattern IMAP Provider (4 repetitions)
- **Severite** : MEDIUM
- **Fichier** : `src/backend/app/routers/email.py:455,573,669,813`
- **Description** : Le bloc de construction du provider IMAP est repete 4 fois dans email.py avec les memes parametres :
  ```python
  provider = get_email_provider(
      provider_type="imap",
      email_address=account.email,
      password=decrypt_value(account.imap_password),
      imap_host=account.imap_host,
      imap_port=account.imap_port,
      smtp_host=account.smtp_host,
      smtp_port=account.smtp_port,
      smtp_use_tls=account.smtp_use_tls,
  )
  ```
- **Remediation** : Extraire une fonction helper `_get_imap_provider(account: EmailAccount) -> EmailProvider`.

---

### QUAL-008 : Melange Optional[X] et X | None
- **Severite** : MEDIUM
- **Fichier** : 41 fichiers Python
- **Description** : Le projet utilise a la fois le style ancien `Optional[str]` (318 occurrences) et le style moderne `str | None`. Ce melange cree une inconsistance. Le style `X | None` est prefere depuis Python 3.10 et est deja utilise dans entities.py.
- **Exemples** :
  - `app/services/calendar/base_provider.py` : 35 usages de `Optional`
  - `app/services/audit.py` : 23 usages
  - `app/services/email/base_provider.py` : 24 usages
  - `app/routers/email.py` : 17 usages
- **Remediation** : Migrer progressivement vers `X | None` pour uniformiser. Ajouter une regle ruff/flake8 pour bloquer `Optional`.

---

### QUAL-009 : except Exception: pass (14 blocs silencieux)
- **Severite** : MEDIUM
- **Fichier** : Multiples fichiers
- **Description** : 14 blocs `except Exception: pass` avalent silencieusement toutes les exceptions sans logging ni re-raise. Cela masque des bugs potentiels.
- **Emplacements** :
  - `app/services/calendar/caldav_provider.py:251,439,550`
  - `app/services/skills/xlsx_generator.py:305`
  - `app/services/board.py:314`
  - `app/routers/config.py:54`
  - `app/routers/crm.py:803,808,836,934`
  - `app/routers/voice.py:149`
  - `app/services/user_profile.py:255`
- **Remediation** : Au minimum, ajouter un `logger.debug()` dans chaque bloc catch. Idealement, restreindre le type d'exception catchee (`except ValueError`, `except KeyError`, etc.).

---

### QUAL-010 : API_BASE hardcode dans api.ts
- **Severite** : MEDIUM
- **Fichier** : `src/frontend/src/services/api.ts:7`
- **Description** : L'URL du backend est hardcodee `http://127.0.0.1:8000`. Cela empeche de configurer un port different ou un backend distant.
- **Code** :
  ```typescript
  export const API_BASE = 'http://127.0.0.1:8000';
  ```
- **Remediation** : Utiliser une variable d'environnement Vite (`import.meta.env.VITE_API_BASE`) avec fallback.

---

### QUAL-011 : Return type inconsistant sur rotate_key()
- **Severite** : MEDIUM
- **Fichier** : `src/backend/app/services/encryption.py:158-182`
- **Description** : La methode `rotate_key()` est annotee `-> None` mais retourne `old_key` (de type `bytes | None`). L'annotation de type est incorrecte.
- **Code** :
  ```python
  def rotate_key(self) -> None:
      ...
      return old_key  # Pour permettre le re-chiffrement
  ```
- **Remediation** : Corriger l'annotation : `def rotate_key(self) -> bytes | None:`.

---

### QUAL-012 : Double pattern singleton (classe + global)
- **Severite** : MEDIUM
- **Fichier** : `encryption.py`, `token_tracker.py`, `mcp_service.py`, `performance.py`, `qdrant.py`, `embeddings.py`
- **Description** : Plusieurs services implementent un singleton via `__new__` ET un accesseur global (`_instance` + `get_xxx_service()`). Ce double mecanisme est redondant et confus.
- **Exemples** :
  - `EncryptionService._instance` + `_encryption_service` + `get_encryption_service()`
  - `TokenTracker._instance` + `_token_tracker` + `get_token_tracker()`
  - `MCPService` : pas de singleton `__new__` mais `_mcp_service` + `get_mcp_service()`
- **Remediation** : Choisir UN pattern : soit `__new__` singleton, soit module-level global avec getter. L'approche FastAPI idiomatique est d'utiliser `Depends()` avec un factory.

---

### QUAL-013 : Usages de `Any` dans le backend Python (~80)
- **Severite** : MEDIUM
- **Fichier** : Multiples fichiers services
- **Description** : ~80 usages de `Any` en type hint, principalement pour des dictionnaires de donnees non structures. Cela reduit la valeur du type checking.
- **Principaux fichiers concernes** :
  - `app/services/crm_export.py` : `list[Any]` pour les entities
  - `app/services/skills/base.py` : `dict[str, Any]` pour context/metadata
  - `app/services/llm.py` : `dict[str, Any]` pour les request bodies
  - `app/services/mcp_service.py` : `result: Any` dans ToolCallResult
- **Remediation** : Introduire des TypedDict ou des dataclasses pour les structures de donnees recurrentes. Accepter `Any` pour les payloads JSON externes (API responses).

---

### QUAL-014 : Usages de `any` dans le frontend TypeScript (7)
- **Severite** : MEDIUM
- **Fichier** : 4 fichiers TS/TSX
- **Description** : 7 usages de `any` en TypeScript, dont certains facilement evitables.
- **Emplacements** :
  - `CRMSyncPanel.tsx:84,113` : `catch (err: any)` - Utiliser `catch (err: unknown)`
  - `TasksPanel.tsx:56` : `const params: any = {}` - Utiliser `Record<string, string>`
  - `InvoiceForm.tsx:79` : `value: any` - Utiliser le type correct du champ
  - `taskStore.ts:99,103` : `as any` cast - Creer un type union pour les statuts/priorites
  - `useVoiceRecorder.test.ts:40` : `as any` pour mock - Acceptable dans les tests
- **Remediation** : Remplacer chaque `any` par le type correct ou `unknown`.

---

### QUAL-015 : TODO non trackes (16)
- **Severite** : MEDIUM
- **Fichier** : Multiples fichiers
- **Description** : 16 TODO trouves dans le code, dont plusieurs semblent etre des fonctionnalites manquantes significatives.
- **TODO critiques** :
  - `invoices.py:422-424` : 3 TODO pour ajouter adresse/SIREN/TVA au profil (impactent la conformite legale des factures)
  - `invoices.py:462,469` : TODO pour integration email avec factures
  - `files.py:236` : TODO pour parser des fichiers correctement
  - `EmailDetail.tsx:91` : TODO pour ouvrir le compose de reponse
  - `VerifyStep.tsx:43` : TODO hardcode email `ludo@gmail.com` au lieu de l'email OAuth reel
- **Remediation** : Migrer chaque TODO vers un ticket dans le backlog (CLAUDE.md ou systeme de suivi) avec priorite et sprint cible.

---

### QUAL-016 : Absence de docstrings sur fonctions internes du chat
- **Severite** : MEDIUM
- **Fichier** : `src/backend/app/routers/chat.py`
- **Description** : Plusieurs fonctions "privees" complexes manquent de docstrings :
  - `_register_generation()` (ligne 62)
  - `_cancel_generation()` (ligne 67)
  - `_is_cancelled()` (ligne 75)
  - `_parse_file_commands()` (ligne 96)
  - `_get_memory_context()` (ligne 224) - 67 lignes, complexe
  - `_get_existing_entity_names()` (ligne 291)
  - `_execute_tools_and_continue()` (ligne 688) - tres complexe
- **Remediation** : Ajouter des docstrings expliquant le but, les parametres et les effets de bord.

---

### QUAL-017 : Melange francais/anglais dans le code
- **Severite** : LOW
- **Fichier** : Ensemble du projet
- **Description** : Le code melange francais et anglais de maniere inconsistante :
  - **Variables/fonctions** : majoritairement en anglais (OK)
  - **Commentaires** : melange FR/EN (ex: `# Mots-cles urgents (rouge)` vs `# Start process with stdio transport`)
  - **Messages d'erreur API** : melange FR/EN (ex: `"Account not found"` vs `"Echec de connexion: ..."`)
  - **Docstrings** : melange FR/EN dans le meme fichier
  - **TODOs** : certains en francais, d'autres en anglais, un en japonais (`EmailConnect.tsx:40` - `需要実装`)
- **Remediation** : Choisir une convention : code et identifiants en anglais, messages utilisateur en francais. Documenter la convention.

---

### QUAL-018 : Inconsistance des codes HTTP et format reponse
- **Severite** : LOW
- **Fichier** : Routers divers
- **Description** : Les endpoints ne suivent pas un format de reponse uniforme :
  - Certains retournent `{"deleted": True, "id": ...}` (memory.py)
  - D'autres retournent directement l'objet modifie
  - Les erreurs utilisent parfois `HTTPException(400)`, parfois `HTTPException(404)`
  - Pas de schema de reponse d'erreur uniforme (ex: `{"code": "...", "message": "..."}`)
- **Remediation** : Definir un schema d'erreur standard et un middleware FastAPI pour formater toutes les erreurs.

---

### QUAL-019 : Nombres magiques
- **Severite** : LOW
- **Fichier** : Multiples fichiers
- **Description** : Plusieurs nombres magiques sans constantes nommees :
  - `chat.py` : `limit: int = 8` pour la recherche memoire
  - `mcp_service.py:369` : `timeout=30.0` pour les requetes MCP
  - `token_tracker.py` : `maxlen=1000` pour l'historique
  - `error_handler.py:209` : `_check_interval: float = 60.0` (OK, documente)
  - `email_classifier.py` : seuils 50, 20 pour la classification
  - `entity_extractor.py` : `MIN_CONFIDENCE = 0.6` (OK, constante nommee)
  - `chat.py` : max 5 iterations de tool calling
- **Remediation** : Extraire les seuils et limites en constantes nommees en haut de chaque module.

---

### QUAL-020 : Fonctions >50 lignes
- **Severite** : LOW
- **Fichier** : Multiples
- **Description** : Liste des fonctions depassant 50 lignes :
  - `llm.py:_stream_anthropic_with_tools()` - ~120 lignes
  - `llm.py:_stream_openai_with_tools()` - ~100 lignes
  - `llm.py:_stream_gemini()` - ~80 lignes
  - `llm.py:_stream_anthropic()` - ~70 lignes
  - `llm.py:_stream_ollama()` - ~60 lignes
  - `chat.py:_do_stream_response()` - ~230 lignes (la plus longue)
  - `chat.py:_execute_tools_and_continue()` - ~150 lignes
  - `chat.py:send_message()` - ~110 lignes
  - `email.py:get_gmail_service_for_account()` - ~80 lignes
  - `email.py:_list_messages_gmail()` - ~50 lignes
  - `email.py:handle_oauth_callback()` - ~60 lignes
  - `email.py:classify_email()` - ~85 lignes
  - `email.py:generate_email_response()` - ~70 lignes
  - `crm.py:import_crm_from_json()` - ~100+ lignes
  - `config.py:get_config()` - ~80 lignes
  - `data.py:create_backup()` - ~70 lignes
  - `data.py:restore_backup()` - ~60 lignes
  - `mcp_service.py:start_server()` - ~65 lignes
  - `crm_import.py:import_contacts_from_csv()` - ~80 lignes
  - `crm_export.py:_populate_xlsx_sheet()` - ~60 lignes
  - `email_classifier_v2.py:classify()` - ~80 lignes
  - `calendar.py:sync_google_calendars()` - ~70 lignes
- **Remediation** : Decomposer les fonctions les plus longues en sous-fonctions. Priorite sur `_do_stream_response()` (230 lignes) et `_execute_tools_and_continue()` (150 lignes).

---

### QUAL-021 : Melange List/Dict (typing) et list/dict (builtin)
- **Severite** : LOW
- **Fichier** : `app/services/calendar_service.py`, `app/services/invoice_pdf.py`
- **Description** : Certains fichiers utilisent encore `List`, `Dict` de `typing` au lieu de `list`, `dict` builtin (disponible depuis Python 3.9).
- **Code** :
  ```python
  from typing import List, Dict, Any, Optional
  async def list_calendars(self) -> List[Dict[str, Any]]:
  ```
- **Remediation** : Remplacer `List` par `list`, `Dict` par `dict`, `Tuple` par `tuple`.

---

### QUAL-022 : ServiceStatus avec attributs de classe mutables
- **Severite** : MEDIUM
- **Fichier** : `src/backend/app/services/error_handler.py:203-210`
- **Description** : La classe `ServiceStatus` definit des attributs de classe mutables (`_statuses: dict`, `_last_check: dict`). En Python, les attributs de classe mutables sont partages entre toutes les instances. Le pattern `__new__` singleton compense ce probleme, mais le code dans `__new__` reinitialise aussi ces attributs a chaque creation, ce qui cree un comportement confus.
- **Code** :
  ```python
  class ServiceStatus:
      _instance = None
      _statuses: dict[str, bool] = {}       # Mutable class attribute
      _last_check: dict[str, float] = {}    # Mutable class attribute
  ```
- **Remediation** : Deplacer `_statuses` et `_last_check` dans `__init__` (appele une seule fois grace au singleton).

---

### QUAL-023 : TODO hardcode email dans VerifyStep
- **Severite** : MEDIUM
- **Fichier** : `src/frontend/src/components/email/wizard/VerifyStep.tsx:43`
- **Description** : L'email `ludo@gmail.com` est hardcode dans le composant de verification OAuth au lieu d'utiliser la reponse OAuth reelle. Cela signifie que le wizard d'email montrera toujours le mauvais email aux autres utilisateurs.
- **Code** :
  ```typescript
  setAccountEmail('ludo@gmail.com'); // TODO: Get from actual OAuth response
  ```
- **Remediation** : Recuperer l'email depuis la reponse OAuth callback.

---

### QUAL-024 : Commentaire en japonais dans le code
- **Severite** : LOW
- **Fichier** : `src/frontend/src/components/email/EmailConnect.tsx:40`
- **Description** : Un commentaire en japonais a ete laisse dans le code :
  ```typescript
  // TODO: Handle callback (需要実装 OAuth callback handler)
  ```
  `需要実装` signifie "implementation necessaire". Cela suggere du code copie depuis une source externe sans nettoyage.
- **Remediation** : Remplacer par un commentaire en anglais ou francais.

---

### QUAL-025 : Absence de tests pour les routers principaux
- **Severite** : MEDIUM
- **Fichier** : `src/backend/tests/`
- **Description** : Les tests existants (103) couvrent principalement les user stories qualite (error_handling, backup, security, performance, personalisation, escalation). Les routers principaux (chat, memory, config, email, crm, calendar, invoices) n'ont pas de tests unitaires backend. Seuls des tests E2E Playwright existent pour quelques flux.
- **Remediation** : Ajouter des tests unitaires pour chaque router avec mocking des services.

---

### QUAL-026 : Pattern async inconsistant dans MCP
- **Severite** : LOW
- **Fichier** : `src/backend/app/services/mcp_service.py:178`
- **Description** : La methode `add_server()` est synchrone mais lance un `asyncio.create_task(self._save_config())`. Le `create_task` est fire-and-forget sans gestion d'erreur. Si `_save_config()` echoue, l'erreur est perdue.
- **Code** :
  ```python
  def add_server(self, ...) -> MCPServer:
      ...
      asyncio.create_task(self._save_config())  # fire-and-forget
  ```
- **Remediation** : Rendre `add_server()` async et awaiter `_save_config()`, ou ajouter un callback d'erreur au task.

---

### QUAL-027 : Imports locaux dans des fonctions (anti-pattern)
- **Severite** : LOW
- **Fichier** : Multiples fichiers
- **Description** : De nombreuses fonctions importent des modules localement pour eviter des imports circulaires :
  - `mcp_service.py:213` : `from app.services.encryption import decrypt_value, is_value_encrypted`
  - `email.py:922` : `from app.services.email_classifier_v2 import EmailClassifierV2`
  - `email.py:1013` : `from app.services.email_response_generator import EmailResponseGenerator`
  - `chat.py` : imports locaux dans `_get_memory_context()`
  - `email.py:1135` : `from sqlalchemy import func`
- **Remediation** : Refactorer l'architecture pour eliminer les imports circulaires. Utiliser le pattern d'injection de dependances de FastAPI.

---

### QUAL-028 : Absence d'index SQLite documentes
- **Severite** : LOW
- **Fichier** : `src/backend/app/models/entities.py`
- **Description** : Les entites SQLModel ne definissent pas d'index explicites sur les colonnes frequemment utilisees dans les `WHERE` clauses :
  - `EmailMessage.account_id` (filtre systematique)
  - `EmailMessage.priority` (filtre dans les stats)
  - `Contact.email` (lookup par email)
  - `Contact.scope` et `Contact.scope_id` (filtre par scope)
  - `Preference.key` (lookup par cle)
- **Remediation** : Ajouter `index=True` sur les champs frequemment requetes : `Field(index=True)`.

---

### QUAL-029 : Accents manquants dans les messages d'erreur backend
- **Severite** : LOW
- **Fichier** : `src/backend/app/services/error_handler.py`
- **Description** : Les messages d'erreur en francais dans `ERROR_MESSAGES` n'ont pas d'accents (ex: "Verifiez" au lieu de "Verifiez", "repondre" au lieu de "repondre"). Cela degrade la qualite percue pour un produit cible sur le marche francais.
- **Remediation** : Ajouter les accents dans toutes les chaines de caracteres destinees aux utilisateurs.

---

### QUAL-030 : Singleton MCPService avec etat global
- **Severite** : LOW
- **Fichier** : `src/backend/app/services/mcp_service.py:545-561`
- **Description** : Le `MCPService` utilise un pattern de singleton global qui rend le testing difficile et couple l'etat au module.
- **Remediation** : Utiliser un systeme de dependency injection (ex: FastAPI `Depends`) pour injecter le service. Cela permet de substituer un mock dans les tests.

---

## Quick wins

### 1. Creer un helper `utc_now()` (Impact: HIGH, Effort: LOW)
```python
# app/utils.py
from datetime import datetime, timezone

def utc_now() -> datetime:
    return datetime.now(timezone.utc)
```
Puis rechercher-remplacer `datetime.utcnow()` par `utc_now()` dans tout le backend.

### 2. Extraire le provider IMAP en helper (Impact: MEDIUM, Effort: LOW)
```python
# Dans email.py
def _build_imap_provider(account: EmailAccount):
    return get_email_provider(
        provider_type="imap",
        email_address=account.email,
        password=decrypt_value(account.imap_password),
        imap_host=account.imap_host,
        imap_port=account.imap_port,
        smtp_host=account.smtp_host,
        smtp_port=account.smtp_port,
        smtp_use_tls=account.smtp_use_tls,
    )
```
Remplacer les 4 duplications.

### 3. Deplacer client_secret en POST body (Impact: CRITICAL, Effort: LOW)
Changer les parametres `Query(...)` en schema Pydantic dans le body pour `initiate_oauth()`.

### 4. Ajouter logging dans les except-pass (Impact: MEDIUM, Effort: LOW)
Remplacer les 14 blocs `except Exception: pass` par `except Exception: logger.debug(...)`.

### 5. Configurer ruff pour bloquer les f-strings dans logger (Impact: MEDIUM, Effort: LOW)
Ajouter la regle `G004` (logging-f-string) dans la configuration ruff/flake8.

### 6. Remplacer Optional par X | None (Impact: LOW, Effort: MEDIUM)
Faire un rechercher-remplacer progressif. Commencer par les nouveaux fichiers.

### 7. Migrer les TODO en backlog (Impact: MEDIUM, Effort: LOW)
Ajouter les 16 TODO identifies dans le CLAUDE.md ou un systeme de tracking.

---

*Rapport genere le 28 janvier 2026 par Claude Opus 4.5*
