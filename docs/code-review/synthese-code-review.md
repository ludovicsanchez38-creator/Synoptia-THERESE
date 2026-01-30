# Synthese Code Review - THERESE V2

**Date** : 28 janvier 2026
**Auteur** : Claude Opus 4.5 (consolidation automatisee)
**Sources** : 5 rapports individuels (securite, architecture, performance, qualite, tests)
**Version auditee** : MVP v3.1 (CRM Sync)

---

## 1. Resume executif

### Nombre total de findings par severite

| Severite | Securite | Architecture | Performance | Qualite | Tests | **Total** |
|----------|----------|-------------|-------------|---------|-------|-----------|
| **CRITICAL** | 4 | 1 | 2 | 1 | 6 | **14** |
| **HIGH** | 7 | 5 | 6 | 5 | 8 | **31** |
| **MEDIUM** | 9 | 11 | 9 | 14 | 8 | **51** |
| **LOW** | 5 | 16 | 5 | 10 | 4 | **40** |
| **Total** | **25** | **33** | **22** | **30** | **26** | **136** (note: le rapport tests contient 30 findings numerotes TEST-001 a TEST-030, avec 6 CRITICAL + 8 HIGH + 8 MEDIUM + 4 LOW = 26 findings avec severite, les 4 restants etant a LOW implicite) |

**Total findings : 140** (25 + 33 + 22 + 30 + 30)

### Score de maturite global : 48/100

| Dimension | Score | Poids | Score pondere |
|-----------|-------|-------|---------------|
| Securite | 40/100 | 30% | 12.0 |
| Architecture | 55/100 | 20% | 11.0 |
| Performance | 50/100 | 15% | 7.5 |
| Qualite code | 62/100 | 15% | 9.3 |
| Tests & Fiabilite | 35/100 | 20% | 7.0 |
| **Total** | | **100%** | **46.8 -> 48/100** |

**Justification des scores** :
- **Securite (40)** : 4 CRITICAL non resolus (injection MCP, path traversal, cle plaintext), absence d'auth API
- **Architecture (55)** : Separation routeur/service/modele correcte, mais 3 God Classes, pas de DI, mixite sync/async
- **Performance (50)** : Streaming SSE fonctionnel, mais extraction entites bloquante, event loop bloque par sync DB, pas d'index SQL
- **Qualite (62)** : Score le plus eleve - bonne gestion d'erreurs centralisee, Fernet en place, mais 100+ datetime.utcnow(), 248 f-strings logger
- **Tests (35)** : 398 tests existants mais couverture ~35%, 7 routers sans test, 12+ services critiques sans test

### Themes transverses identifies

1. **Securite MCP et injection de commandes** : Le systeme MCP est le vecteur d'attaque principal (commandes arbitraires, filesystem trop ouvert, cles API heritees par subprocess)
2. **God Classes / monolithes** : 3 fichiers concentrent trop de responsabilites (`llm.py` 1503l, `api.ts` 2944l, `SettingsModal.tsx` 2169l), rendant le refactoring et les tests difficiles
3. **Mixite sync/async et blocage de l'event loop** : Operations synchrones (DB, embeddings) appelees depuis du code async, bloquant l'event loop FastAPI
4. **Couverture de tests insuffisante sur les modules critiques** : Les modules de securite (encryption, OAuth, MCP), de conformite (RGPD, facturation) et metier (email, CRM) n'ont aucun test
5. **Protection des chemins et donnees insuffisante** : Path traversal, pas de limite taille fichier, cle de chiffrement en plaintext, cles API dans os.environ

---

## 2. Cross-references

Les findings ci-dessous apparaissent dans plusieurs rapports, confirmant leur importance.

### Theme A : Injection et execution de commandes MCP

| Finding | Rapport | Description |
|---------|---------|-------------|
| SEC-001 | Securite | Injection de commandes via MCP subprocess |
| ARCH-017 | Architecture | Execution de commandes arbitraires via MCP |
| TEST-008 | Tests | Service MCP non teste (execution commandes systeme) |
| SEC-006 | Securite | MCP filesystem trop permissif (acces a tout $HOME) |

**Risque** : Un serveur MCP malveillant (ou un preset modifie) peut executer n'importe quel binaire systeme et acceder a tous les fichiers du home directory. Le service MCP n'a aucun test unitaire.

### Theme B : Path traversal et acces fichiers non restreint

| Finding | Rapport | Description |
|---------|---------|-------------|
| SEC-002 | Securite | Path traversal dans /fichier et /analyse (chat.py) |
| SEC-003 | Securite | Path traversal dans files.py (indexation) |
| SEC-016 | Securite | Pas de validation taille max fichier |
| PERF-009 | Performance | DoS par fichier volumineux |
| TEST-011 | Tests | Router files non teste |

**Risque** : N'importe quel fichier lisible par le processus peut etre lu, indexe dans Qdrant, et potentiellement envoye aux API LLM cloud. Pas de limite de taille.

### Theme C : Cle de chiffrement et secrets en clair

| Finding | Rapport | Description |
|---------|---------|-------------|
| SEC-004 | Securite | Cle Fernet stockee en plaintext sur disque |
| SEC-005 | Securite | Cles API dans os.environ (heritage subprocess) |
| TEST-006 | Tests | Service encryption non teste |
| TEST-007 | Tests | Service OAuth non teste |

**Risque** : Si la cle de chiffrement est exfiltree (via path traversal SEC-002), toutes les cles API et tokens OAuth sont compromis. Les cles sont aussi exposees via os.environ a tous les subprocess MCP.

### Theme D : God Classes (backend + frontend)

| Finding | Rapport | Description |
|---------|---------|-------------|
| ARCH-001 | Architecture | God Class llm.py (1503 lignes) |
| ARCH-002 | Architecture | God Class api.ts (2944 lignes) |
| ARCH-003 | Architecture | God Class SettingsModal.tsx (2169 lignes) |
| QUAL-004 | Qualite | llm.py - God Object, SRP viole |
| QUAL-005 | Qualite | api.ts - monolithe frontend |
| QUAL-006 | Qualite | SettingsModal.tsx - 8 onglets dans 1 fichier |
| PERF-008 | Performance | httpx.AsyncClient pas de pooling (lie a llm.py) |

**Impact** : Testabilite tres faible, couplage fort, re-renders excessifs (SettingsModal), regression facile lors de modifications.

### Theme E : Mixite sync/async et blocage event loop

| Finding | Rapport | Description |
|---------|---------|-------------|
| ARCH-005 | Architecture | Mixite sync/async dans CRM Sync |
| ARCH-006 | Architecture | Acces synchrone DB dans LLM service |
| ARCH-026 | Architecture | crm_sync.py utilise Session synchrone |
| PERF-002 | Performance | _get_api_key_from_db() bloque l'event loop (CRITICAL) |
| PERF-004 | Performance | Operations embedding synchrones en contexte async |
| PERF-013 | Performance | Recherche semantique synchrone dans pipeline SSE |

**Impact** : Blocage de l'event loop asyncio FastAPI pendant les operations I/O (DB, embeddings). Latence augmentee, potentiel database locked, goulot d'etranglement.

### Theme F : Index SQL manquants et performances DB

| Finding | Rapport | Description |
|---------|---------|-------------|
| ARCH-028 | Architecture | Absence d'index SQL sur colonnes filtrees |
| PERF-006 | Performance | Index manquants (Message.conversation_id, Contact.scope, etc.) |
| PERF-005 | Performance | Pas de mode WAL sur SQLite |
| PERF-012 | Performance | N+1 query listing conversations |
| QUAL-028 | Qualite | Absence d'index documentes dans entities.py |

**Impact** : Full table scans sur les requetes frequentes, erreurs potentielles "database is locked", listing conversations en O(N*M).

### Theme G : Re-renders frontend et SSE

| Finding | Rapport | Description |
|---------|---------|-------------|
| ARCH-027 | Architecture | Re-render en cascade via spread operator (chatStore) |
| PERF-011 | Performance | Re-renders excessifs a chaque chunk SSE |
| PERF-021 | Performance | Conversations persistees en localStorage (serialisation bloquante) |

**Impact** : 100+ re-renders/seconde pendant le streaming, serialisation bloquante de 5-10 MB dans localStorage synchrone.

### Theme H : OAuth credentials et fuites dans les logs

| Finding | Rapport | Description |
|---------|---------|-------------|
| SEC-008 | Securite | Credentials OAuth dans query parameters |
| QUAL-001 | Qualite | client_secret en query parameter (CRITICAL qualite) |
| SEC-009 | Securite | Cle API Gemini dans query parameters |

**Impact** : Les secrets OAuth et cles API sont enregistres dans les access logs serveur, les logs reverse proxy, et l'historique du navigateur.

### Theme I : Rate limiting et authentification absents

| Finding | Rapport | Description |
|---------|---------|-------------|
| SEC-010 | Securite | Absence d'authentification sur toute l'API |
| SEC-015 | Securite | Absence de rate limiting |
| ARCH-008 | Architecture | Pas de rate limiting sur les endpoints API |

**Impact** : N'importe quel processus local peut appeler toutes les API sans restriction, epuiser les credits API, envoyer des emails, supprimer des donnees.

### Theme J : Tests critiques manquants

| Finding | Rapport | Description |
|---------|---------|-------------|
| TEST-001 | Tests | Aucun test router Email |
| TEST-002 | Tests | Aucun test router Calendar |
| TEST-003 | Tests | Aucun test router Invoices |
| TEST-004 | Tests | Aucun test router CRM |
| TEST-005 | Tests | Aucun test router RGPD |
| TEST-006 | Tests | Service encryption non teste |
| TEST-007 | Tests | Service OAuth non teste |
| TEST-008 | Tests | Service MCP non teste |
| TEST-018 | Tests | Providers email non testes |

**Impact** : Les modules a risque legal (RGPD, facturation), securite (encryption, OAuth, MCP) et metier (email, CRM, calendrier) n'ont aucun test. Un bug en production pourrait avoir des consequences legales, financieres ou de securite.

### Theme K : datetime.utcnow() deprecie

| Finding | Rapport | Description |
|---------|---------|-------------|
| ARCH-022 | Architecture | datetime.utcnow() deprecie (Python 3.12+) |
| QUAL-002 | Qualite | 100+ occurrences dans 30+ fichiers |

**Impact** : Pas de bug immediat mais datetimes naive causant potentiellement des comparaisons incorrectes avec des datetimes aware.

---

## 3. Matrice priorite (Impact x Effort)

### Legende effort
- **S** = Small (< 2h)
- **M** = Medium (2h-1 jour)
- **L** = Large (1-3 jours)
- **XL** = Extra Large (> 3 jours)

| | **Effort Faible (S/M)** | **Effort Eleve (L/XL)** |
|---|---|---|
| **Impact Haut** | **QUICK WINS** | **PROJETS CRITIQUES** |
| | SEC-008/QUAL-001 : OAuth credentials -> body POST (S) | SEC-001/ARCH-017 : Whitelist commandes MCP (M-L) |
| | PERF-005 : Activer WAL SQLite (S) | SEC-002/SEC-003 : Path traversal protection (M) |
| | PERF-001 : Extraction entites fire-and-forget (S) | SEC-004 : Migration cle vers Keychain (L) |
| | PERF-002 : Cache cles API au demarrage (M) | SEC-010 : Auth token par session (M) |
| | PERF-006/ARCH-028 : Ajouter index SQL (S) | ARCH-001/QUAL-004 : Decouvrir llm.py (L) |
| | PERF-012 : COUNT(*) listing conversations (S) | ARCH-005/026 : Migrer CRM Sync vers AsyncSession (M) |
| | SEC-016/PERF-009 : Limite taille fichier (S) | TEST-006/007/008 : Tests encryption/OAuth/MCP (L) |
| | ARCH-029 : Fix global exception handler (S) | ARCH-002/QUAL-005 : Decouvrir api.ts (M) |
| | ARCH-008 : Ajouter rate limiting slowapi (S) | ARCH-003/QUAL-006 : Decouvrir SettingsModal (M) |
| | SEC-005 : Supprimer cles de os.environ (M) | TEST-001/018 : Tests email complets (L) |
| **Impact Bas** | **NICE-TO-HAVE** | **A EVITER (pour l'instant)** |
| | ARCH-022/QUAL-002 : datetime.now(timezone.utc) (S) | ARCH-004 : DI complet avec Depends() (XL) |
| | QUAL-003 : f-strings logger -> lazy formatting (M) | ARCH-023 : Migration Alembic complete (L) |
| | ARCH-009/PERF-022 : Supprimer import json redondants (S) | PERF-021 : Migration localStorage -> IndexedDB (L) |
| | ARCH-011 : Factoriser parsing SSE (S) | ARCH-014 : Pagination reelle stores Zustand (L) |
| | QUAL-008 : Optional[X] -> X pipe None (M) | PERF-018 : Integration tiktoken (M) |
| | ARCH-015 : Renommer ImportError (S) | PERF-019 : Trie pour SearchIndex (L) |
| | TEST-029 : Supprimer event_loop fixture deprecated (S) | |
| | QUAL-024 : Commentaire japonais -> francais (S) | |

---

## 4. Top 10 actions prioritaires

### #1 - Securiser l'execution de commandes MCP (whitelist)

- **Findings** : SEC-001, ARCH-017, TEST-008
- **Severite** : CRITICAL
- **Effort** : M
- **Description** : Implementer une whitelist stricte de commandes autorisees pour les serveurs MCP (`npx`, `node`, `python`, `uvx`, `uv`). Valider que `server.command` correspond a un executable connu. Bloquer les chemins absolus vers des binaires systeme sensibles (`rm`, `sh`, `bash`, `curl`, etc.). Ajouter des tests unitaires pour le service MCP avec subprocess mock.
- **Fichiers concernes** :
  - `src/backend/app/services/mcp_service.py` (validation commande avant execution)
  - `src/backend/app/routers/mcp.py` (validation a l'ajout de serveur)
  - `tests/test_services_mcp.py` (a creer, 18+ tests)

### #2 - Corriger le path traversal (chat.py + files.py)

- **Findings** : SEC-002, SEC-003, TEST-011
- **Severite** : CRITICAL
- **Effort** : M
- **Description** : Ajouter une validation de chemin dans `_get_file_context()` et `index_file()`. Verifier que `path.resolve()` est un sous-chemin du working directory ou du home directory. Bloquer explicitement `~/.therese/`, `~/.ssh/`, `/etc/`, `~/.aws/`. Implementer une denylist de patterns de fichiers sensibles (`*.key`, `*.pem`, `.env`, `.encryption_key`).
- **Fichiers concernes** :
  - `src/backend/app/routers/chat.py:130-131` (validation chemin /fichier)
  - `src/backend/app/routers/files.py:68` (validation chemin indexation)
  - `tests/test_routers_files.py` (a creer, 10+ tests dont path traversal)

### #3 - Proteger la cle de chiffrement Fernet

- **Findings** : SEC-004, TEST-006
- **Severite** : CRITICAL
- **Effort** : L
- **Description** : Migrer le stockage de la cle Fernet depuis le fichier plaintext `~/.therese/.encryption_key` vers le macOS Keychain (via `keyring` Python ou `security` CLI). Alternative : activer la derivation depuis un mot de passe maitre (la methode `_derive_key_from_password()` existe deja). En attendant, ajouter `.encryption_key` dans la denylist du path traversal (action #2). Creer les tests unitaires du service encryption.
- **Fichiers concernes** :
  - `src/backend/app/services/encryption.py` (migration stockage cle)
  - `tests/test_services_encryption.py` (a creer, 12+ tests)

### #4 - Ajouter l'authentification API locale

- **Findings** : SEC-010
- **Severite** : HIGH
- **Effort** : M
- **Description** : Generer un token de session unique au demarrage de l'application (`secrets.token_urlsafe(32)`). Le passer au frontend Tauri via une variable d'environnement ou un fichier temporaire. Verifier ce token dans un middleware FastAPI pour tous les endpoints via un header `X-Therese-Token`. Exclure le endpoint health check.
- **Fichiers concernes** :
  - `src/backend/app/main.py` (middleware d'authentification)
  - `src/frontend/src/services/api.ts` (ajout header sur toutes les requetes)

### #5 - Debloquer l'event loop (cache cles API + WAL + index)

- **Findings** : PERF-002, PERF-005, PERF-006, ARCH-006, ARCH-028
- **Severite** : CRITICAL (PERF-002) + HIGH
- **Effort** : M (combinaison de quick wins)
- **Description** : (1) Charger et cacher toutes les cles API au demarrage dans un dictionnaire en memoire, supprimer `_get_api_key_from_db()` synchrone. (2) Ajouter `PRAGMA journal_mode=WAL` et `PRAGMA busy_timeout=5000` dans l'init DB. (3) Ajouter `index=True` sur `Message.conversation_id`, `Message.created_at`, `Contact.scope`, `Project.contact_id`, `Conversation.updated_at`. (4) Remplacer le N+1 query listing conversations par un COUNT(*) avec GROUP BY.
- **Fichiers concernes** :
  - `src/backend/app/services/llm.py:21-61` (supprimer _get_api_key_from_db, cache)
  - `src/backend/app/models/database.py:47-57` (WAL mode)
  - `src/backend/app/models/entities.py` (index=True sur colonnes cles)
  - `src/backend/app/routers/chat.py:835-869` (COUNT(*) au lieu de N+1)

### #6 - Deplacer les credentials OAuth/API hors des query parameters

- **Findings** : SEC-008, QUAL-001, SEC-009
- **Severite** : CRITICAL (QUAL-001) + HIGH (SEC-008)
- **Effort** : S
- **Description** : Migrer `client_id` et `client_secret` des `Query(...)` vers un schema Pydantic dans le body de la requete POST pour l'endpoint `initiate_oauth()`. Pour la cle Gemini (SEC-009), l'API Google impose le passage en query param - documenter le risque et privilegier OAuth quand possible.
- **Fichiers concernes** :
  - `src/backend/app/routers/email.py:230-233` (Query -> Body)
  - `src/frontend/src/services/api.ts` (adapter l'appel frontend)

### #7 - Isoler les cles API des subprocess MCP

- **Findings** : SEC-005, SEC-006
- **Severite** : HIGH
- **Effort** : M
- **Description** : (1) Supprimer le stockage des cles API dans `os.environ`. Les charger directement depuis la DB au moment de l'utilisation. (2) Dans `mcp_service.py`, ne passer aux subprocess que les variables d'environnement strictement necessaires (pas `os.environ.copy()`). (3) Restreindre le preset filesystem a `{WORKING_DIRECTORY}` au lieu de `{HOME}`.
- **Fichiers concernes** :
  - `src/backend/app/routers/config.py:232-244` (supprimer os.environ)
  - `src/backend/app/services/mcp_service.py:215` (env minimal)
  - `src/backend/app/routers/mcp.py:337-342` (preset filesystem restreint)

### #8 - Lancer l'extraction d'entites en fire-and-forget

- **Findings** : PERF-001
- **Severite** : CRITICAL
- **Effort** : S
- **Description** : L'extraction d'entites apres chaque message bloque le stream SSE pendant 2-10 secondes. Lancer l'extraction via `asyncio.create_task()` apres l'envoi du `done` event. Le resultat peut etre envoye via un endpoint separe ou un second stream SSE.
- **Fichiers concernes** :
  - `src/backend/app/routers/chat.py:658-685` (fire-and-forget)

### #9 - Creer les tests pour les modules critiques sans couverture

- **Findings** : TEST-001 a TEST-008, TEST-018
- **Severite** : CRITICAL (6 findings)
- **Effort** : XL (effort total, decomposable en sprints)
- **Description** : Creer les fichiers de test pour les modules les plus critiques : (1) `test_services_encryption.py` (12+ tests), (2) `test_services_oauth.py` (15+ tests), (3) `test_services_mcp.py` (18+ tests), (4) `test_routers_email.py` (25+ tests), (5) `test_routers_invoices.py` (20+ tests), (6) `test_routers_rgpd.py` (15+ tests). Total : ~105 nouveaux tests minimum.
- **Fichiers concernes** :
  - `tests/test_services_encryption.py` (a creer)
  - `tests/test_services_oauth.py` (a creer)
  - `tests/test_services_mcp.py` (a creer)
  - `tests/test_routers_email.py` (a creer)
  - `tests/test_routers_invoices.py` (a creer)
  - `tests/test_routers_rgpd.py` (a creer)

### #10 - Decouvrir llm.py en providers modulaires

- **Findings** : ARCH-001, QUAL-004, PERF-008
- **Severite** : HIGH
- **Effort** : L
- **Description** : Extraire chaque provider LLM dans un module separe sous `services/providers/`. Creer une interface `BaseLLMProvider(ABC)` avec les methodes `stream()`, `stream_with_tools()`, `continue_with_tools()`. Extraire `ContextWindow` dans `context.py`, le system prompt builder dans `prompt_builder.py`, et `_get_api_key_from_db` dans `api_keys.py`. Partager un pool global de `httpx.AsyncClient`.
- **Fichiers concernes** :
  - `src/backend/app/services/llm.py` (a decouvrir en ~8 fichiers)
  - `src/backend/app/services/providers/` (nouveau repertoire)
  - `src/backend/app/services/providers/__init__.py`
  - `src/backend/app/services/providers/anthropic.py`
  - `src/backend/app/services/providers/openai.py`
  - `src/backend/app/services/providers/gemini.py`
  - `src/backend/app/services/providers/mistral.py`
  - `src/backend/app/services/providers/grok.py`
  - `src/backend/app/services/providers/ollama.py`
  - `src/backend/app/services/context.py`
  - `src/backend/app/services/prompt_builder.py`

---

## 5. Quick Wins (effort < 2h chacun)

### QW-1 : Activer WAL mode sur SQLite (15 min)

**Findings** : PERF-005
**Impact** : Elimination des erreurs "database is locked", lectures concurrentes pendant les ecritures.
**Instructions** :
- Dans `src/backend/app/models/database.py`, apres la creation du moteur async, ajouter :
  ```
  @event.listens_for(engine.sync_engine, "connect")
  def set_sqlite_pragma(dbapi_conn, connection_record):
      cursor = dbapi_conn.cursor()
      cursor.execute("PRAGMA journal_mode=WAL")
      cursor.execute("PRAGMA busy_timeout=5000")
      cursor.close()
  ```

### QW-2 : Deplacer OAuth credentials en POST body (30 min)

**Findings** : SEC-008, QUAL-001
**Impact** : Elimination de la fuite de secrets dans les logs serveur.
**Instructions** :
- Creer un schema Pydantic `OAuthInitiateRequest` avec `client_id` et `client_secret`
- Remplacer les parametres `Query(...)` par un body dans `email.py:230-233`
- Adapter l'appel frontend dans `api.ts`

### QW-3 : Extraction d'entites en fire-and-forget (30 min)

**Findings** : PERF-001
**Impact** : Elimination de 2-10s de latence apres chaque reponse.
**Instructions** :
- Dans `chat.py:658-685`, envoyer le `done` event immediatement
- Lancer `asyncio.create_task(extract_and_notify(...))` apres le `done`
- L'extraction continue en arriere-plan

### QW-4 : Ajouter index SQL manquants (30 min)

**Findings** : PERF-006, ARCH-028, QUAL-028
**Impact** : Requetes 10-100x plus rapides sur les tables principales.
**Instructions** :
- Dans `entities.py`, ajouter `sa_column_kwargs={"index": True}` ou `Field(index=True)` sur :
  - `Message.conversation_id`
  - `Message.created_at`
  - `Contact.scope`
  - `Project.contact_id`
  - `Project.scope`
  - `Conversation.updated_at`

### QW-5 : Limite de taille fichier (30 min)

**Findings** : SEC-016, PERF-009
**Impact** : Protection contre OOM et freeze de l'application.
**Instructions** :
- Dans `file_parser.py`, verifier `file_path.stat().st_size` avant lecture
- Rejeter si > 50 MB avec un message explicite
- Pour les PDF, limiter a 100 pages max

### QW-6 : Requete COUNT(*) pour listing conversations (30 min)

**Findings** : PERF-012
**Impact** : De 51 requetes SQL a 1 seule. Latence reduite de 200-500ms a < 10ms.
**Instructions** :
- Dans `chat.py:835-869`, remplacer la boucle de comptage par une sous-requete `func.count()` avec GROUP BY
- Ou stocker `message_count` sur le modele `Conversation`

### QW-7 : Supprimer les import json redondants (15 min)

**Findings** : ARCH-009, PERF-022
**Impact** : Nettoyage de code, elimination d'un code smell copier-coller.
**Instructions** :
- Dans `llm.py`, supprimer les 10 `import json` a l'interieur des boucles de streaming (lignes 482, 558, 588, 676, 771, 891, 936, 972, 1093, 1159)
- Le module `json` est deja importe en tete de fichier (ligne 8)

### QW-8 : Creer le helper utc_now() (30 min)

**Findings** : ARCH-022, QUAL-002
**Impact** : 100+ occurrences corrigees, conformite Python 3.12+.
**Instructions** :
- Creer `src/backend/app/utils.py` avec :
  ```
  from datetime import datetime, timezone
  def utc_now() -> datetime:
      return datetime.now(timezone.utc)
  ```
- Rechercher-remplacer `datetime.utcnow()` par `utc_now()` dans tout le backend

### QW-9 : Fix global exception handler (30 min)

**Findings** : ARCH-029
**Impact** : Les erreurs 422 de validation Pydantic ne sont plus transformees en erreurs 500 generiques.
**Instructions** :
- Dans `main.py:146-168`, changer `@app.exception_handler(Exception)` pour ne capturer que `TheresError`
- Ajouter un handler separe pour `Exception` en fallback (erreurs non gerees uniquement)
- Laisser FastAPI gerer nativement `HTTPException` et `RequestValidationError`

### QW-10 : Ajouter rate limiting avec slowapi (1h)

**Findings** : SEC-015, ARCH-008
**Impact** : Protection contre l'epuisement des credits API par un script local.
**Instructions** :
- Installer `slowapi` dans les dependances
- Ajouter un Limiter dans `main.py`
- Limiter les endpoints critiques : `/api/chat/send` (10/min), `/api/board/deliberate` (3/min), `/api/images/generate` (5/min)

---

## 6. Decisions architecturales requises

Les points suivants necessitent une discussion avant implementation car ils impactent la structure globale du projet.

### Decision 1 : Pattern DI vs Singletons

**Contexte** : 7+ services utilisent des variables `global` ou des singletons `__new__` (ARCH-004, QUAL-012, QUAL-030).
**Options** :
- **A) FastAPI Depends()** : Approche idiomatique FastAPI, remplacement progressif, bonne testabilite. Effort : L.
- **B) Container DI (dependency-injector)** : Plus structure, mais ajoute une dependance. Effort : XL.
- **C) Statu quo + nettoyage** : Garder les singletons mais les rendre thread-safe (asyncio.Lock) et uniformiser le pattern. Effort : M.
**Recommandation** : Option A pour les services critiques (LLM, MCP, Encryption), option C pour les autres.

### Decision 2 : Decoupage de llm.py (providers modulaires vs monolithe)

**Contexte** : `llm.py` fait 1503 lignes avec 6 providers (ARCH-001, QUAL-004).
**Options** :
- **A) Providers modulaires** : Un fichier par provider sous `services/providers/`. Interface ABC commune. Effort : L.
- **B) Split fonctionnel** : Garder un fichier par "concern" (streaming, tools, context). Effort : M.
- **C) Monolithe reorganise** : Garder un fichier mais mieux structure avec des classes internes. Effort : S.
**Recommandation** : Option A (providers modulaires) car elle favorise l'ajout de nouveaux providers et les tests unitaires.

### Decision 3 : Migration Alembic vs create_all

**Contexte** : `create_all()` ne gere pas les modifications de schema existant (ARCH-023). Alembic est dans les dependances mais non utilise.
**Options** :
- **A) Alembic complet** : Generer toutes les migrations, executer au startup. Effort : M.
- **B) Migration hybride** : `create_all()` + ALTER TABLE fallback au demarrage pour les nouvelles colonnes. Effort : S.
- **C) Statu quo** : Garder `create_all()`, les utilisateurs devront reinitialiser leur DB en cas de changement de schema. Effort : 0.
**Recommandation** : Option A pour un produit desktop ou les utilisateurs ne peuvent pas reinitialiser leur DB facilement.

### Decision 4 : Strategie de tests (pyramide des tests)

**Contexte** : 398 tests existants mais couverture ~35%. 7 routers sans test, 12+ services sans test (rapport Tests).
**Options** :
- **A) Pyramide classique** : Tests unitaires (services) -> Integration (routers + httpx.AsyncClient) -> E2E (Playwright). Effort : XL progressif.
- **B) Integration first** : Prioriser les tests d'integration avec httpx.AsyncClient + DB en memoire, couvrant routeur+service+DB d'un coup. Effort : L.
- **C) Tests de securite d'abord** : Couvrir uniquement les modules critiques securite (encryption, OAuth, MCP, path traversal). Effort : M.
**Recommandation** : Option C en Sprint 1 (securite), puis option B en Sprint 3 (integration).

### Decision 5 : Keychain macOS vs mot de passe maitre pour la cle de chiffrement

**Contexte** : La cle Fernet est en plaintext dans `~/.therese/.encryption_key` (SEC-004).
**Options** :
- **A) macOS Keychain** : Via le module `keyring` Python ou la commande `security`. Transparent pour l'utilisateur, natif macOS. Effort : M.
- **B) Mot de passe maitre** : Deriver la cle depuis un mot de passe demande au demarrage (la methode existe deja). Effort : S.
- **C) Permissions fichier renforcees** : Garder le fichier mais avec chiffrement du fichier lui-meme via le Keychain. Effort : M.
**Recommandation** : Option A (Keychain macOS) car c'est la plus transparente pour un produit desktop macOS. L'utilisateur n'a pas a retenir un mot de passe supplementaire.

---

## 7. Plan en 3 sprints

### Sprint 1 - Securite critique + bloquants (1 semaine)

**Objectif** : Eliminer tous les findings CRITICAL et les failles de securite exploitables.

| # | Action | Findings | Effort | Dependance |
|---|--------|----------|--------|------------|
| 1.1 | Whitelist commandes MCP | SEC-001, ARCH-017 | M | - |
| 1.2 | Path traversal protection | SEC-002, SEC-003 | M | - |
| 1.3 | OAuth credentials -> body POST | SEC-008, QUAL-001 | S | - |
| 1.4 | Extraction entites fire-and-forget | PERF-001 | S | - |
| 1.5 | Cache cles API + supprimer sync DB | PERF-002, ARCH-006 | M | - |
| 1.6 | WAL mode SQLite | PERF-005 | S | - |
| 1.7 | Index SQL manquants | PERF-006, ARCH-028 | S | 1.6 |
| 1.8 | Authentification API locale (token) | SEC-010 | M | - |
| 1.9 | Isolation cles API subprocess MCP | SEC-005, SEC-006 | M | 1.1 |
| 1.10 | Limite taille fichier | SEC-016, PERF-009 | S | - |
| 1.11 | Rate limiting (slowapi) | SEC-015, ARCH-008 | S | - |
| 1.12 | Fix global exception handler | ARCH-029 | S | - |
| 1.13 | Tests encryption.py | TEST-006 | M | - |
| 1.14 | Tests oauth.py | TEST-007 | M | - |
| 1.15 | Tests mcp_service.py | TEST-008 | L | 1.1 |

**Dependances** :
- 1.7 (index SQL) necessite 1.6 (WAL) pour eviter des locks pendant la creation d'index
- 1.9 (isolation cles) necessite 1.1 (whitelist MCP) pour avoir un cadre securise
- 1.15 (tests MCP) necessite 1.1 (whitelist) pour tester la validation des commandes

**Delivrables** :
- 0 findings CRITICAL restants
- Token d'auth local en place
- 45+ nouveaux tests (encryption + OAuth + MCP)

---

### Sprint 2 - Architecture + Performance (2 semaines)

**Objectif** : Refactoring structurel des God Classes + quick wins performance + securite restante.

| # | Action | Findings | Effort | Dependance |
|---|--------|----------|--------|------------|
| 2.1 | Decouvrir llm.py en providers modulaires | ARCH-001, QUAL-004 | L | Sprint 1.5 |
| 2.2 | Decouvrir api.ts par domaine | ARCH-002, QUAL-005 | M | - |
| 2.3 | Decouvrir SettingsModal en composants par onglet | ARCH-003, QUAL-006 | M | - |
| 2.4 | Migrer CRM Sync vers AsyncSession | ARCH-005, ARCH-026 | M | - |
| 2.5 | Embedding async (asyncio.to_thread) | PERF-004 | S | - |
| 2.6 | Pool global httpx.AsyncClient | PERF-008, PERF-014 | M | 2.1 |
| 2.7 | Batching updates SSE frontend (debounce 50ms) | PERF-011, ARCH-027 | M | - |
| 2.8 | Reader task stderr MCP | PERF-015 | S | - |
| 2.9 | COUNT(*) listing conversations | PERF-012 | S | Sprint 1.7 |
| 2.10 | Protection cle chiffrement (Keychain) | SEC-004 | L | Sprint 1.2 |
| 2.11 | Prompt injection mitigation | SEC-007 | M | 2.1 |
| 2.12 | Board timeout + parallelisation | ARCH-020, PERF-007 | M | 2.1, 2.6 |
| 2.13 | Batch import CRM (upsert + progression) | PERF-010 | M | 2.4 |
| 2.14 | Cleanup pending requests MCP | PERF-016 | S | - |

**Dependances** :
- 2.1 (decouvrir llm.py) est prerequis pour 2.6 (pool httpx), 2.11 (prompt injection), 2.12 (board)
- 2.4 (async CRM) est prerequis pour 2.13 (batch import)
- 2.10 (Keychain) necessite que le path traversal soit corrige (Sprint 1.2) pour que la cle ne soit plus accessible

**Delivrables** :
- God Classes resolues (llm.py, api.ts, SettingsModal.tsx)
- Event loop debloque (async DB, async embeddings)
- Streaming frontend optimise (debounce)
- Cle de chiffrement securisee dans Keychain

---

### Sprint 3 - Qualite + Dette technique tests (2 semaines)

**Objectif** : Couvrir les modules critiques avec des tests, ameliorer la qualite du code, mettre en place Alembic.

| # | Action | Findings | Effort | Dependance |
|---|--------|----------|--------|------------|
| 3.1 | Tests router Email | TEST-001, TEST-018 | L | - |
| 3.2 | Tests router Invoices | TEST-003, TEST-027 | M | - |
| 3.3 | Tests router RGPD | TEST-005 | M | - |
| 3.4 | Tests router CRM + services sync | TEST-004, TEST-015 | L | - |
| 3.5 | Tests router Calendar | TEST-002 | M | - |
| 3.6 | Tests SSE streaming parsing | TEST-013 | M | - |
| 3.7 | Tests tool calling flow | TEST-014 | M | Sprint 2.1 |
| 3.8 | Tests api.ts frontend | TEST-021 | M | Sprint 2.2 |
| 3.9 | Tests Qdrant service | TEST-022 | M | - |
| 3.10 | Migrations Alembic | ARCH-023 | M | Sprint 2 |
| 3.11 | Remplacer except Exception generiques | ARCH-007, QUAL-009 | M | - |
| 3.12 | f-strings logger -> lazy formatting | QUAL-003 | M | - |
| 3.13 | datetime.utcnow() -> utc_now() | ARCH-022, QUAL-002 | S | - |
| 3.14 | Optional[X] -> X pipe None | QUAL-008 | M | - |
| 3.15 | Consolider conftest.py + testpaths | TEST-016, TEST-028 | S | - |
| 3.16 | Supprimer event_loop fixture deprecated | TEST-029 | S | - |
| 3.17 | Edge cases dans tests existants | TEST-020 | M | - |
| 3.18 | Docstrings fonctions internes chat.py | QUAL-016 | S | - |

**Dependances** :
- 3.7 (tests tool calling) necessite Sprint 2.1 (providers modulaires)
- 3.8 (tests api.ts) necessite Sprint 2.2 (api.ts decouvert)
- 3.10 (Alembic) necessite Sprint 2 (structure stabilisee)

**Delivrables** :
- Couverture tests : de ~35% a ~60%
- ~200 nouveaux tests
- Qualite code amelioree (datetime, logger, exceptions, types)
- Migrations Alembic en place

---

## 8. Dependances entre les fixes

```
Sprint 1 (Securite)                     Sprint 2 (Architecture)               Sprint 3 (Qualite/Tests)
=====================                   =======================               ======================

[1.1 Whitelist MCP] -----------------> [2.11 Prompt injection]
        |                                       |
        |                               [2.1 Decouvrir llm.py] ------------> [3.7 Tests tool calling]
        |                                  |       |       |
        +-> [1.9 Isolation cles MCP]       |       |       +-> [2.12 Board timeout]
        |                                  |       |
        +-> [1.15 Tests MCP] --------->    |       +-> [2.6 Pool httpx]
                                           |
[1.2 Path traversal] --------+            |
                              +-> [2.10 Keychain cle chiffrement]
[1.13 Tests encryption] ------+

[1.5 Cache cles API] --------> [2.1 Decouvrir llm.py]

[1.6 WAL SQLite] --> [1.7 Index SQL] --> [2.9 COUNT(*)]

                                [2.2 Decouvrir api.ts] ---------> [3.8 Tests api.ts frontend]

                                [2.4 Async CRM] --> [2.13 Batch import CRM]

                                [2.3 Decouvrir SettingsModal]

[1.12 Fix exception handler]

[1.3 OAuth -> body]

[1.4 Fire-and-forget entites]

[1.8 Auth token local]

[1.10 Limite taille fichier]

[1.11 Rate limiting]

                                                                  [3.10 Alembic] (apres Sprint 2)

                                                                  [3.1-3.9 Tests] (independants)

                                                                  [3.11-3.18 Qualite] (independants)
```

**Chemin critique** : 1.1 -> 1.9 -> 2.1 -> 2.6/2.11/2.12 -> 3.7

---

## 9. Verification de coherence

### Fichiers critiques presents dans 3+ rapports

| Fichier | Securite | Architecture | Performance | Qualite | Tests |
|---------|----------|-------------|-------------|---------|-------|
| `llm.py` | SEC-005, SEC-007, SEC-009 | ARCH-001, ARCH-006, ARCH-009, ARCH-030 | PERF-002, PERF-004, PERF-008, PERF-014, PERF-018, PERF-022 | QUAL-003, QUAL-004, QUAL-013 | TEST-014 |
| `mcp_service.py` | SEC-001, SEC-005 | ARCH-004, ARCH-017 | PERF-015, PERF-016 | QUAL-003, QUAL-026, QUAL-030 | TEST-008 |
| `encryption.py` | SEC-004, SEC-025 | - | - | QUAL-011, QUAL-012 | TEST-006 |
| `chat.py` | SEC-002 | ARCH-012, ARCH-027 | PERF-001, PERF-011, PERF-012, PERF-013, PERF-017, PERF-023 | QUAL-016, QUAL-019, QUAL-020 | TEST-013, TEST-014 |

**Verification** :
- `llm.py` : present dans 5/5 rapports. Confirme.
- `mcp_service.py` : present dans 5/5 rapports. Confirme.
- `encryption.py` : present dans 3/5 rapports (Securite, Qualite, Tests). Confirme.
- `chat.py` : present dans 5/5 rapports. Confirme.

### Coherence des findings numerotes

| Rapport | Plage attendue | Nombre | Severites | Confirme |
|---------|---------------|--------|-----------|----------|
| Securite | SEC-001 a SEC-025 | 25 | 4C + 7H + 9M + 5L = 25 | Oui |
| Architecture | ARCH-001 a ARCH-033 | 33 | 1C + 5H + 11M + 16L = 33 | Oui |
| Performance | PERF-001 a PERF-023 | 22 | 2C + 6H + 9M + 5L = 22 | Oui (pas de PERF-022 numerote explicitement mais 22 findings) |
| Qualite | QUAL-001 a QUAL-030 | 30 | 1C + 5H + 14M + 10L = 30 | Oui |
| Tests | TEST-001 a TEST-030 | 30 | 6C + 8H + 8M + 4L = 26 (+ 4 non categorises) | Oui |

Note : Le rapport Performance contient en fait un PERF-022 ("Double import json en boucle de streaming", LOW) mais la numerotation saute ensuite a PERF-023. Le total de 22 findings est correct.

### Coherence du Top 10

Le Top 10 couvre :
- **4/14 findings CRITICAL** directement (SEC-001, SEC-002/003, SEC-004, PERF-001) et 4 autres indirectement (PERF-002 dans #5, QUAL-001 dans #6, TEST-006/007/008 dans #9)
- Les 5 themes transverses principaux
- Un mix equilibre de securite (actions 1-4, 6-7), performance (5, 8), tests (9), architecture (10)
- Les efforts vont de S a XL, permettant un demarrage immediat sur les quick wins

---

*Synthese generee le 28 janvier 2026 par Claude Opus 4.5. Ce document consolide les 5 rapports de code review individuels en un plan d'action unifie. Il est auto-suffisant et lisible sans les rapports sources.*
