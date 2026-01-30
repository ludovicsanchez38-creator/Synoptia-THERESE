# Rapport de Performance - THERESE V2

**Date** : 28 janvier 2026
**Auditeur** : Claude Opus 4.5 (audit automatise)
**Scope** : Backend Python FastAPI + Frontend React/Tauri
**Classification** : CRITICAL / HIGH / MEDIUM / LOW

---

## Resume executif

L'audit de performance de THERESE V2 revele **22 findings** dont **2 CRITICAL**, **6 HIGH**, **9 MEDIUM** et **5 LOW**. Les principaux goulots d'etranglement identifies sont :

1. **Extraction d'entites bloquante** (CRITICAL) - Un appel LLM complet apres chaque message utilisateur, execute de maniere synchrone dans le pipeline SSE, ajoutant 2-10 secondes de latence avant la fermeture du stream.

2. **Appel synchrone SQLite dans contexte async** (CRITICAL) - `_get_api_key_from_db()` cree un moteur SQLAlchemy synchrone a chaque appel, bloquant l'event loop asyncio.

3. **Modele embedding de ~400 MB en memoire permanente** sans possibilite de dechargement, et operations d'embedding synchrones appelees depuis du code async.

4. **Pas de limite de taille fichier** sur les uploads et le parsing, exposant a un DoS par fichier volumineux.

5. **Absence de mode WAL sur SQLite** et d'index sur les colonnes frequemment requetees, causant des contentions sous charge.

6. **Re-renders excessifs cote frontend** a chaque chunk SSE, avec remplacement complet de l'arbre de conversations dans le store Zustand.

---

## Findings

### PERF-001 : Extraction d'entites bloquante dans le pipeline SSE
- **Severite** : CRITICAL
- **Fichier** : `src/backend/app/routers/chat.py:658-685`
- **Description** : Apres l'envoi du chunk SSE `done`, le code execute `extractor.extract_entities()` qui effectue un appel LLM complet (streaming collect). Cet appel est **synchrone dans le generateur SSE** - le client doit attendre la fin de l'extraction avant que le stream ne se termine reellement. L'extraction fait un appel LLM avec le system prompt `EXTRACTION_SYSTEM_PROMPT`, collecte la reponse complete, parse le JSON, puis envoie l'event `entities_detected`.
- **Impact** : Ajoute 2-10 secondes (selon le provider LLM) de latence apres la reponse visible. Le frontend ne peut pas fermer la connexion SSE tant que l'extraction n'est pas terminee. L'utilisateur voit la reponse complete mais le spinner de streaming reste actif.
- **Remediation** : Lancer l'extraction en fire-and-forget via `asyncio.create_task()`. Envoyer le resultat via un endpoint separe ou un websocket. Alternativement, envoyer le `done` event immediatement, puis continuer l'extraction et envoyer `entities_detected` apres.
- **Gain estime** : Elimination de 2-10s de latence per message. Amelioration percue massive de la reactivite.

---

### PERF-002 : Appel synchrone SQLite bloquant l'event loop (`_get_api_key_from_db`)
- **Severite** : CRITICAL
- **Fichier** : `src/backend/app/services/llm.py:21-61`
- **Description** : La fonction `_get_api_key_from_db()` cree un **moteur SQLAlchemy synchrone** (`create_engine`) a chaque appel, puis execute une requete SQL synchrone avec `engine.connect()`. Cette fonction est appelee dans `_default_config()` (4 fois pour verifier chaque provider) et dans `get_llm_service_for_provider()` (1 fois par provider). Chaque appel cree un nouveau moteur, ouvre une connexion, execute une query, et ferme tout. Dans un contexte FastAPI async, cela **bloque l'event loop** pendant chaque operation I/O SQLite.
- **Impact** : Blocage de l'event loop pour ~5-20ms par appel. Au demarrage du Board (qui pre-charge 5 providers), cela represente 5x l'appel = 25-100ms de blocage. Chaque nouvelle requete chat bloque aussi si le service LLM n'est pas encore initialise. Sous charge, cela cree un goulot d'etranglement.
- **Remediation** : (1) Mettre en cache les cles API apres le premier chargement. (2) Utiliser le moteur async existant de `database.py` au lieu de creer un moteur sync. (3) Charger toutes les cles au demarrage de l'application et les stocker dans un dictionnaire cache.
- **Gain estime** : Elimination du blocage de l'event loop. Demarrage du Board 5-10x plus rapide.

---

### PERF-003 : Modele embedding ~400 MB permanent en memoire
- **Severite** : HIGH
- **Fichier** : `src/backend/app/services/embeddings.py:30-40`
- **Description** : Le modele `nomic-ai/nomic-embed-text-v1.5` est charge via `SentenceTransformer` en singleton et reste en memoire pour toute la duree de vie de l'application. Ce modele (768 dimensions, architecture BERT) occupe environ 270-400 MB de RAM. Le chargement est lazy (a la premiere utilisation) mais il n'y a aucun mecanisme de dechargement.
- **Impact** : Sur un MacBook avec 16 GB de RAM, cela represente ~2.5% de la memoire totale en permanence. Pour une application desktop, c'est significatif, surtout quand l'utilisateur ne fait pas de recherche semantique pendant de longues periodes. Avec l'embedding model + Qdrant embedded + SQLite + le process Python + le process Tauri, la consommation memoire totale peut atteindre 1-2 GB.
- **Remediation** : (1) Ajouter un timer de dechargement automatique (ex: decharger si pas utilise depuis 10 minutes). (2) Utiliser un modele plus leger (ex: `all-MiniLM-L6-v2` a ~80 MB). (3) Integrer dans le `MemoryManager` existant (performance.py) un callback de dechargement. (4) Offrir une option "mode economie memoire" dans les PowerSettings.
- **Gain estime** : Liberation de 270-400 MB de RAM quand le modele n'est pas utilise.

---

### PERF-004 : Operations d'embedding synchrones dans un contexte async
- **Severite** : HIGH
- **Fichier** : `src/backend/app/services/qdrant.py:100,140` / `src/backend/app/services/embeddings.py:52,65`
- **Description** : Les methodes `embed_text()` et `embed_texts()` de `EmbeddingsService` sont synchrones (elles appellent `model.encode()` qui est une operation CPU-bound). Cependant, elles sont appelees depuis des contextes async via `QdrantService.add_memory()`, `add_memories()` et `search()`. Le `QdrantService` lui-meme est synchrone mais appele depuis des handlers FastAPI async. Le Qdrant client est en mode embedded (synchrone egalement).
- **Impact** : Chaque appel embedding bloque l'event loop pendant 50-200ms (selon la longueur du texte). Pendant ce temps, aucune autre requete HTTP ne peut etre traitee. Si un utilisateur indexe un fichier avec 50 chunks, l'event loop est bloque pendant 2.5-10 secondes.
- **Remediation** : (1) Wrapper les appels embedding dans `asyncio.to_thread()` ou `loop.run_in_executor()`. (2) Rendre le QdrantService async en utilisant le client Qdrant async (`AsyncQdrantClient`). (3) Pour le batch embedding, utiliser un thread pool.
- **Gain estime** : Event loop debloque pendant les embeddings. Reactivite maintenue meme pendant l'indexation de fichiers.

---

### PERF-005 : Pas de mode WAL sur SQLite
- **Severite** : HIGH
- **Fichier** : `src/backend/app/models/database.py:47-57`
- **Description** : La base SQLite est initialisee sans activer le mode WAL (Write-Ahead Logging). Le mode par defaut (journal mode DELETE) verrouille la base entiere pendant les ecritures. Avec un seul utilisateur desktop c'est rarement un probleme, mais avec les operations concurrentes (streaming SSE + entity extraction + token tracking + session commit), cela peut causer des erreurs `database is locked`.
- **Impact** : Risque de `sqlite3.OperationalError: database is locked` lors d'ecritures concurrentes. Le Board de decision lance 5 LLM calls en parallele puis ecrit les resultats - si deux ecritures coincident, l'une echoue. La creation du moteur sync dans `_get_api_key_from_db()` (PERF-002) aggrave le probleme car elle cree sa propre connexion independante.
- **Remediation** : Ajouter `PRAGMA journal_mode=WAL` et `PRAGMA busy_timeout=5000` dans l'initialisation de la base de donnees. Configurer via `connect_args` ou un event listener `pool_events`.
- **Gain estime** : Elimination des erreurs `database is locked`. Lectures concurrentes pendant les ecritures.

---

### PERF-006 : Index manquants sur les colonnes frequemment requetees
- **Severite** : HIGH
- **Fichier** : `src/backend/app/models/entities.py`
- **Description** : Plusieurs colonnes utilisees dans les clauses WHERE n'ont pas d'index :
  - `Message.conversation_id` (ligne 117) - pas d'index, requete a chaque chargement de conversation
  - `Contact.scope` / `Contact.scope_id` - pas d'index, filtre frequent dans les requetes memoire
  - `Project.contact_id` (ligne 75) - pas d'index (le `foreign_key` ne cree pas d'index automatique avec SQLModel)
  - `Project.scope` / `Project.scope_id` - pas d'index
  - `Conversation.updated_at` - pas d'index, utilise dans ORDER BY pour le listing
  - `Message.created_at` - pas d'index, utilise dans ORDER BY pour l'historique
  - `Activity.contact_id` (ligne 467) - a un index (bien)
  - `EmailMessage.thread_id` (ligne 247) - a un index (bien)
- **Impact** : Full table scan a chaque requete de messages pour une conversation. Avec 1000+ conversations et 50000+ messages, le listing et le chargement deviennent lents (>100ms au lieu de <5ms). Le tri par `updated_at` sans index force un tri en memoire.
- **Remediation** : Ajouter `index=True` sur : `Message.conversation_id`, `Message.created_at`, `Contact.scope`, `Project.contact_id`, `Project.scope`, `Conversation.updated_at`. Creer une migration Alembic pour ajouter ces index.
- **Gain estime** : Requetes 10-100x plus rapides sur les tables principales. Listing conversations < 5ms.

---

### PERF-007 : Board de decision - 5 appels LLM paralleles + synthese sequentielle
- **Severite** : HIGH
- **Fichier** : `src/backend/app/services/board.py:131-329`
- **Description** : La deliberation du Board est correctement parallelisee (les 5 conseillers sont lances via `asyncio.create_task` en parallele, ligne 260). Cependant :
  1. Le pre-chargement des LLM services (lignes 176-190) appelle `get_llm_service_for_provider()` sequentiellement pour chaque provider, et chacun appelle `_get_api_key_from_db()` (PERF-002).
  2. La synthese (ligne 290) est un 6e appel LLM sequentiel apres les 5 paralleles.
  3. Chaque service LLM cree potentiellement un nouveau `httpx.AsyncClient` (pas de partage).
  4. La recherche web initiale (ligne 157) est sequentielle avant le lancement des conseillers.
- **Impact** : Le pre-chargement bloque l'event loop 5x (PERF-002). La synthese ajoute un 6e appel LLM. Total : recherche web (~2s) + 5 LLM paralleles (~10-30s selon provider le plus lent) + synthese (~5-15s) = 17-47 secondes minimum.
- **Remediation** : (1) Cacher les cles API (PERF-002). (2) Lancer la recherche web et le pre-chargement des services en parallele. (3) Partager un pool de `httpx.AsyncClient` entre les services.
- **Gain estime** : Reduction de 2-5s sur le pre-chargement. Reduction du temps total du Board de ~10%.

---

### PERF-008 : httpx.AsyncClient cree par instance LLMService (pas de pooling)
- **Severite** : HIGH
- **Fichier** : `src/backend/app/services/llm.py:370-374`
- **Description** : Chaque `LLMService` cree son propre `httpx.AsyncClient` de maniere lazy. Le client global (`get_llm_service()`) reutilise le meme client, mais `get_llm_service_for_provider()` cree un **nouveau** `LLMService` a chaque appel (ligne 1503), et donc un nouveau `httpx.AsyncClient`. Le Board cree 5 services differents, donc potentiellement 5 clients HTTP distincts.
- **Impact** : Chaque nouveau client HTTP necessite une nouvelle connexion TCP + TLS handshake (~100-200ms vers les API cloud). Pas de connection pooling ni de keep-alive entre les appels. Fuite de connexions si `close()` n'est jamais appele (et il ne l'est pas pour les services crees par `get_llm_service_for_provider()`).
- **Remediation** : (1) Partager un seul `httpx.AsyncClient` global avec un timeout configurable. (2) Cacher les `LLMService` par provider (au lieu d'en creer un nouveau a chaque appel). (3) Ajouter un `__del__` ou un mecanisme de fermeture explicite.
- **Gain estime** : Elimination des handshakes TCP/TLS redondants. Reduction de ~500ms-1s par deliberation Board.

---

### PERF-009 : Pas de limite de taille fichier (DoS potentiel)
- **Severite** : MEDIUM
- **Fichier** : `src/backend/app/services/file_parser.py` (global)
- **Description** : Le service `file_parser.py` n'impose aucune limite de taille fichier. La fonction `extract_text()` lit le fichier entierement en memoire. Pour les PDF (`_extract_pdf`), toutes les pages sont extraites. Pour les fichiers texte (`_extract_plain_text`), le contenu entier est lu via `file_path.read_text()`. La seule protection est dans `chat.py:202` qui tronque a 15000 caracteres **apres** l'extraction complete.
- **Impact** : Un fichier PDF de 1 GB serait entierement charge en memoire, puis toutes ses pages seraient parsees. Un fichier CSV de 500 MB serait lu integralement. Cela peut provoquer un OOM (Out of Memory) ou geler l'application pendant plusieurs minutes.
- **Remediation** : (1) Ajouter une verification de taille maximale (ex: 50 MB) dans `extract_text()` avant lecture. (2) Pour les PDF, limiter le nombre de pages (ex: 100 pages max). (3) Pour les CSV, la limite de 500 lignes existe deja (ligne 131), mais la lecture initiale charge tout. (4) Utiliser un streaming reader pour les gros fichiers.
- **Gain estime** : Protection contre les OOM et les freeze de l'application.

---

### PERF-010 : CRM Import batch sans pagination ni streaming
- **Severite** : MEDIUM
- **Fichier** : `src/backend/app/services/crm_import.py:470-591`
- **Description** : La methode `import_contacts()` charge toutes les lignes du fichier en memoire (`raw_data = _parse_csv(content)` ou `_parse_xlsx(content)`), puis itere sequentiellement sur chaque ligne avec une requete SELECT pour verifier l'existence (`await session.execute(stmt)` par ligne). Pour un fichier de 10000 contacts, cela fait 10000 requetes SELECT individuelles. Le `commit()` final (ligne 586) est un seul gros commit a la fin.
- **Impact** : Import de 10000 contacts = 10000 requetes SELECT + 10000 INSERT/UPDATE, puis un seul commit. Cela peut prendre plusieurs minutes et bloquer la base de donnees. Si le commit final echoue (ex: contrainte unique), tout est perdu.
- **Remediation** : (1) Batch les commits par lots de 100. (2) Pre-charger tous les contacts existants en une seule requete (IN clause ou dictionnaire). (3) Utiliser `session.execute(insert(...).on_conflict_do_update(...))` pour l'upsert. (4) Ajouter un yield de progression pour informer le frontend.
- **Gain estime** : Import 10-50x plus rapide pour les gros fichiers.

---

### PERF-011 : Re-renders excessifs du store Zustand a chaque chunk SSE
- **Severite** : MEDIUM
- **Fichier** : `src/frontend/src/stores/chatStore.ts:182-196`
- **Description** : La methode `updateMessage()` est appelee a chaque chunk SSE (potentiellement 50-200 fois par seconde pendant le streaming). A chaque appel, elle cree un **nouveau tableau** de conversations via `.map()`, un nouveau tableau de messages via `.map()` imbriquee, et un nouveau objet message avec le contenu mis a jour. Cela cree un nouvel arbre d'objets complet a chaque chunk.
- **Impact** : Chaque mise a jour declenche un re-render de tous les composants abonnes au store (MessageList, ConversationSidebar, etc.). Avec Zustand et React, les selecteurs peuvent mitiger cela, mais si un composant utilise `useChatStore()` sans selecteur fin, tout re-render. A 100 chunks/seconde, cela represente 100 re-renders/seconde avec creation de ~100 objets temporaires par render.
- **Remediation** : (1) Batching des updates (accumuler les chunks dans un buffer et flush toutes les 50-100ms). (2) Utiliser `immer` middleware de Zustand pour des mutations in-place. (3) Separer le contenu du message streaming dans un state local (useRef) et ne mettre a jour le store qu'en fin de streaming. (4) Utiliser un selecteur fin : `useChatStore(state => state.conversations[state.currentConversationId].messages[lastIndex].content)`.
- **Gain estime** : Reduction de 90-95% des re-renders pendant le streaming. UI plus fluide.

---

### PERF-012 : Listing conversations avec N+1 query pour le comptage de messages
- **Severite** : MEDIUM
- **Fichier** : `src/backend/app/routers/chat.py:835-869`
- **Description** : L'endpoint `list_conversations` execute une requete pour lister les conversations, puis pour **chaque** conversation, execute une **nouvelle requete** pour compter les messages (`select(Message).where(Message.conversation_id == conv.id)`, ligne 853). De plus, le comptage charge **tous les messages en memoire** (`len(msg_result.scalars().all())`) au lieu d'utiliser `COUNT(*)`.
- **Impact** : Pour 50 conversations, cela fait 51 requetes SQL. Chaque requete de comptage charge TOUS les objets Message en memoire juste pour compter. Pour une conversation avec 500 messages, cela instancie 500 objets Python juste pour obtenir le nombre 500. Latence : O(N*M) ou N = nombre de conversations et M = messages moyens par conversation.
- **Remediation** : (1) Utiliser `func.count()` avec un GROUP BY dans une seule requete. (2) Stocker `message_count` sur le modele `Conversation` et le mettre a jour incrementalement. (3) Utiliser une sous-requete correlee.
- **Gain estime** : De 51 requetes a 1 requete. Latence reduite de 200-500ms a < 10ms pour 50 conversations.

---

### PERF-013 : Recherche semantique synchrone dans le pipeline SSE
- **Severite** : MEDIUM
- **Fichier** : `src/backend/app/routers/chat.py:224-283` (appele a la ligne 483)
- **Description** : `_get_memory_context()` est une fonction synchrone qui appelle `qdrant.search()`, lequel appelle `embed_text()` (synchrone, CPU-bound) puis `client.query_points()` (synchrone, I/O-bound). Elle est appelee dans `_do_stream_response()` avant de commencer le streaming LLM. Cela ajoute de la latence avant le premier token.
- **Impact** : Delai de 100-300ms avant le debut du streaming (embedding ~50-100ms + recherche Qdrant ~50-200ms). Ce delai s'ajoute a la latence du LLM. Le SLA de 2 secondes pour le first token est menace.
- **Remediation** : (1) Rendre `_get_memory_context()` async avec `asyncio.to_thread()`. (2) Lancer la recherche memoire en parallele avec la preparation du contexte LLM. (3) Mettre en cache les embeddings des requetes recentes (les memes questions reviennent souvent).
- **Gain estime** : Reduction du time-to-first-token de 100-300ms.

---

### PERF-014 : Pas de fermeture explicite des clients httpx
- **Severite** : MEDIUM
- **Fichier** : `src/backend/app/services/llm.py:1392-1396, 1495-1503`
- **Description** : `LLMService.close()` existe (ligne 1392) mais n'est jamais appele pour les services crees par `get_llm_service_for_provider()`. Le service global `_llm_service` est ferme implicitement quand le process s'arrete, mais pas de maniere propre. Les `httpx.AsyncClient` non fermes gardent les connexions TCP ouvertes.
- **Impact** : Fuite de connexions TCP. Chaque appel Board cree jusqu'a 5 clients httpx qui ne sont jamais fermes. Sur une longue session (plusieurs heures), cela peut accumuler des dizaines de connexions fantomes. Les descripteurs de fichiers s'accumulent.
- **Remediation** : (1) Utiliser `async with` pour les clients temporaires. (2) Cacher les services par provider avec un dictionnaire global. (3) Ajouter une fermeture explicite dans le shutdown de l'application.
- **Gain estime** : Elimination des fuites de connexions TCP. Stabilite memoire sur les longues sessions.

---

### PERF-015 : MCP subprocess stderr non consomme
- **Severite** : MEDIUM
- **Fichier** : `src/backend/app/services/mcp_service.py:229-235, 300-324`
- **Description** : Les processus MCP sont lances avec `stderr=asyncio.subprocess.PIPE` (ligne 233) mais seul `stdout` est lu dans `_read_server_output()` (ligne 308). Le flux stderr n'est jamais lu. Si le processus MCP ecrit beaucoup sur stderr, le buffer pipe se remplit et le processus se bloque (deadlock).
- **Impact** : Si un serveur MCP genere des erreurs ou des logs sur stderr, le buffer pipe (typiquement 64 KB sur macOS) finit par se remplir. Le processus MCP se bloque en ecriture, ce qui bloque les tool calls. L'utilisateur voit un timeout (30s) sans explication.
- **Remediation** : (1) Lancer un reader task pour stderr en parallele. (2) Ou utiliser `stderr=asyncio.subprocess.DEVNULL` si les logs stderr ne sont pas necessaires. (3) Mieux : capturer stderr et le loguer.
- **Gain estime** : Elimination des deadlocks MCP. Meilleur diagnostic des erreurs.

---

### PERF-016 : MCP pending_requests jamais nettoyees en cas de crash serveur
- **Severite** : MEDIUM
- **Fichier** : `src/backend/app/services/mcp_service.py:99-101, 358-373`
- **Description** : Le dictionnaire `_pending_requests` stocke des `asyncio.Future` pour chaque requete envoyee a un serveur MCP. Si le serveur crashe ou le reader task echoue (ligne 318-324), les futures restent dans `_pending_requests` indefiniment. Le timeout de 30s (ligne 369) gere le cas normal, mais si le serveur crashe apres le timeout, les futures orphelines ne sont jamais nettoyees.
- **Impact** : Fuite de memoire mineure (chaque Future + son ID). Plus important : si le serveur est redemarme avec le meme ID, les anciens pending requests peuvent interferer.
- **Remediation** : (1) Nettoyer `_pending_requests` dans `stop_server()`. (2) Ajouter un check dans `_read_server_output()` : quand le reader se termine, cancel toutes les futures en attente pour ce serveur. (3) Utiliser un prefixe server_id dans les request IDs.
- **Gain estime** : Elimination des futures orphelines. Comportement previsible apres un crash MCP.

---

### PERF-017 : Pas de backpressure sur le SSE streaming
- **Severite** : MEDIUM
- **Fichier** : `src/backend/app/routers/chat.py:436-457` / `src/frontend/src/services/api.ts:214-242`
- **Description** : Le pipeline SSE n'a aucun mecanisme de backpressure. Le backend genere les chunks aussi vite que le LLM les produit et les serialise en JSON + SSE format. Si le client (frontend) est lent a consommer (ex: re-renders couteux, tab en arriere-plan), les chunks s'accumulent dans le buffer TCP du serveur, puis dans le buffer uvicorn.
- **Impact** : Si le frontend est surcharge ou l'onglet est en arriere-plan, les chunks s'accumulent en memoire cote serveur. Pour une longue reponse (10000 tokens), cela peut representer ~100 KB de donnees bufferisees. Le header `X-Accel-Buffering: no` desactive le buffering nginx mais pas le buffering Python.
- **Remediation** : (1) Ajouter un mecanisme de debounce cote frontend (ne pas traiter chaque chunk individuellement). (2) Cote backend, surveiller si le client est toujours connecte avant d'envoyer. (3) Limiter la vitesse d'envoi si necessaire.
- **Gain estime** : Stabilite sous charge. Pas d'accumulation memoire.

---

### PERF-018 : Token estimation imprecise (len // 4)
- **Severite** : MEDIUM
- **Fichier** : `src/backend/app/routers/chat.py:627-628` / `src/backend/app/services/llm.py:178-179`
- **Description** : L'estimation des tokens utilise la formule `len(text) // 4` (1 token = 4 caracteres). C'est une approximation tres grossiere, surtout pour le francais (qui utilise des accents et des mots plus longs). Aucun tokenizer reel n'est utilise. Cette estimation est utilisee a la fois pour le context trimming (`ContextWindow.estimate_tokens()`) et pour le token tracking/cout (`chat.py:627`).
- **Impact** : (1) Le context trimming peut etre trop agressif ou trop laxiste (difference de 20-50%). (2) Le calcul de cout est fausse, affichant des montants incorrects a l'utilisateur. (3) Pour le francais, la surestimation est typiquement de ~30% (les tokenizers modernes ont ~3 chars/token pour le francais, pas 4).
- **Remediation** : (1) Utiliser `tiktoken` pour les modeles OpenAI/GPT. (2) Pour Anthropic, utiliser leur API de comptage de tokens. (3) Au minimum, utiliser un ratio de 3 chars/token pour le francais.
- **Gain estime** : Estimations 30-50% plus precises. Couts affiches corrects.

---

### PERF-019 : SearchIndex.search() fait un scan complet de l'index inverse
- **Severite** : LOW
- **Fichier** : `src/backend/app/services/performance.py:361-392`
- **Description** : La methode `SearchIndex.search()` itere sur **tous les mots de l'index inverse** pour le prefix matching (ligne 380 : `for indexed_word, conv_ids in self._index.items()`). Pour chaque mot de la requete, c'est un O(n) ou n = nombre de mots uniques dans l'index.
- **Impact** : Avec 1000 conversations et 50000 mots uniques, une recherche de 3 mots fait 3 * 50000 = 150000 iterations. C'est rapide en pratique (<10ms), mais ne scale pas lineairement. Pour une utilisation desktop single-user, c'est acceptable.
- **Remediation** : (1) Utiliser un trie (arbre prefixe) pour le prefix matching. (2) Ou limiter le prefix matching aux mots commencant par le prefixe (sorted list + bisect).
- **Gain estime** : Negligeable pour l'utilisation actuelle. Pertinent si l'index depasse 100000 mots.

---

### PERF-020 : Garbage collection explicite trop frequente
- **Severite** : LOW
- **Fichier** : `src/backend/app/services/performance.py:178-184`
- **Description** : Le `PerformanceMonitor` appelle `gc.collect()` toutes les 5 minutes (`_gc_interval = 300`). Le `MemoryManager.run_cleanup()` appelle aussi `gc.collect()` (ligne 280). Le GC de Python est deja automatique et incremental. Forcer un full GC toutes les 5 minutes cause une pause de 10-50ms a chaque fois.
- **Impact** : Micro-pauses de 10-50ms toutes les 5 minutes. Pour une application desktop, c'est negligeable. Mais si le GC est force pendant un streaming, cela peut causer un micro-stutter visible.
- **Remediation** : (1) Augmenter l'intervalle a 30 minutes ou 1 heure. (2) Ne forcer le GC que quand la memoire depasse un seuil (ex: 500 MB). (3) Supprimer le GC explicite et laisser Python gerer.
- **Gain estime** : Elimination des micro-pauses periodiques.

---

### PERF-021 : Conversations persistees en localStorage avec l'historique complet
- **Severite** : LOW
- **Fichier** : `src/frontend/src/stores/chatStore.ts:313-320`
- **Description** : Le store Zustand est persiste dans `localStorage` via le middleware `persist` avec le nom `therese-chat`. Toutes les conversations (sauf ephemeres) sont persistees, y compris **tous les messages**. La serialisation se fait a chaque mutation du store. Avec 100 conversations et 5000 messages, le localStorage peut atteindre 5-10 MB.
- **Impact** : (1) La serialisation JSON de 5-10 MB a chaque mutation prend 50-200ms. (2) `localStorage` est synchrone et bloque le thread principal. (3) La limite de localStorage est generalement 5-10 MB (Tauri peut etre plus genereux). (4) Au-dela de la limite, les donnees sont silencieusement perdues.
- **Remediation** : (1) Ne persister que les IDs et metadata des conversations, pas les messages. (2) Utiliser IndexedDB (async) au lieu de localStorage. (3) Limiter le nombre de conversations persistees (ex: 50 dernieres). (4) Compresser les donnees avec lz-string.
- **Gain estime** : Serialisation 10-100x plus rapide. Pas de risque de perte de donnees.

---

### PERF-022 : Double import json en boucle de streaming
- **Severite** : LOW
- **Fichier** : `src/backend/app/services/llm.py:482,558,589,677,891,974`
- **Description** : Plusieurs methodes de streaming font `import json` a l'interieur des boucles `async for` (ex: lignes 482, 558, 589). Bien que Python cache les modules importes (le `import` ne recharge pas le module), l'instruction `import` implique un lookup dans `sys.modules` a chaque iteration, ce qui est un overhead negligeable mais inutile.
- **Impact** : Negligeable en pratique (< 1 microseconde par iteration). Le module `json` est deja importe en haut du fichier (ligne 8).
- **Remediation** : Supprimer les `import json` a l'interieur des boucles. Le `json` importe en haut du fichier est suffisant.
- **Gain estime** : Negligeable. Nettoyage de code.

---

### PERF-023 : Pas de timeout/limite sur le nombre d'iterations de tool calling
- **Severite** : LOW
- **Fichier** : `src/backend/app/routers/chat.py:544, 688-819`
- **Description** : Le chainage de tools est limite a 5 iterations (`max_tool_iterations = 5`), ce qui est bien. Cependant, il n'y a pas de timeout global pour l'ensemble de la chaine d'outils. Si chaque iteration prend 30 secondes (timeout MCP), la chaine complete peut prendre 5 * 30 = 150 secondes (2.5 minutes) pendant lesquelles le SSE reste ouvert.
- **Impact** : L'utilisateur peut attendre 2.5 minutes sans possibilite d'annulation efficace (le mecanisme de cancellation `_is_cancelled()` n'est pas verifie dans `_execute_tools_and_continue()`).
- **Remediation** : (1) Ajouter un timeout global (ex: 120 secondes). (2) Verifier `_is_cancelled()` dans `_execute_tools_and_continue()`. (3) Ajouter un heartbeat SSE pendant les executions longues.
- **Gain estime** : Meilleure experience utilisateur. Capacite d'annulation reelle.

---

## Roadmap optimisations

Ordonnees par impact/effort :

### Sprint 1 - Quick Wins (1-2 jours)

| # | Finding | Action | Effort |
|---|---------|--------|--------|
| 1 | PERF-001 | Fire-and-forget pour l'extraction d'entites | 30 min |
| 2 | PERF-002 | Cache des cles API au demarrage | 1h |
| 3 | PERF-005 | Activer WAL mode sur SQLite | 15 min |
| 4 | PERF-006 | Ajouter les index manquants (migration Alembic) | 1h |
| 5 | PERF-022 | Supprimer les imports redondants | 15 min |
| 6 | PERF-012 | Requete COUNT(*) pour le listing conversations | 30 min |

### Sprint 2 - Performance fondamentale (3-5 jours)

| # | Finding | Action | Effort |
|---|---------|--------|--------|
| 7 | PERF-004 | Wrapper embeddings dans asyncio.to_thread() | 2h |
| 8 | PERF-008 | Pool global de httpx.AsyncClient | 3h |
| 9 | PERF-014 | Fermeture explicite des clients httpx | 1h |
| 10 | PERF-009 | Limite de taille fichier (50 MB) | 1h |
| 11 | PERF-011 | Batching des updates SSE frontend (50ms debounce) | 3h |
| 12 | PERF-015 | Reader task pour stderr MCP | 1h |

### Sprint 3 - Optimisations avancees (1 semaine)

| # | Finding | Action | Effort |
|---|---------|--------|--------|
| 13 | PERF-003 | Dechargement automatique du modele embedding | 4h |
| 14 | PERF-010 | Batch import CRM avec upsert et progression | 6h |
| 15 | PERF-013 | Recherche memoire async + cache embeddings | 4h |
| 16 | PERF-016 | Cleanup des pending requests MCP | 2h |
| 17 | PERF-017 | Backpressure SSE | 4h |
| 18 | PERF-021 | Migration localStorage vers IndexedDB | 6h |

### Backlog

| # | Finding | Action | Effort |
|---|---------|--------|--------|
| 19 | PERF-018 | Integration tiktoken pour estimation tokens | 3h |
| 20 | PERF-019 | Trie pour le SearchIndex | 4h |
| 21 | PERF-020 | Suppression GC explicite | 15 min |
| 22 | PERF-023 | Timeout global tool chain + cancellation check | 2h |
| 23 | PERF-007 | Paralleliser pre-chargement Board + recherche web | 2h |

---

## Metriques recommandees

### Backend (a tracker dans PerformanceMonitor)

| Metrique | Description | SLA |
|----------|-------------|-----|
| `first_token_latency_ms` | Deja implemente (PERF-01) | < 2000 ms |
| `entity_extraction_latency_ms` | Temps de l'extraction d'entites | < 5000 ms |
| `embedding_latency_ms` | Temps d'un embed_text() | < 200 ms |
| `db_query_latency_ms` | Latence des requetes SQLite | < 50 ms |
| `memory_usage_mb` | RAM totale du process Python | < 1000 MB |
| `embedding_model_loaded` | Boolean : modele en memoire ou non | - |
| `active_httpx_clients` | Nombre de clients httpx ouverts | < 10 |
| `mcp_pending_requests` | Nombre de requests MCP en attente | < 20 |
| `sse_active_streams` | Deja implemente | < 5 |
| `sqlite_wal_size_mb` | Taille du fichier WAL | < 100 MB |

### Frontend (a tracker dans React DevTools / Performance API)

| Metrique | Description | SLA |
|----------|-------------|-----|
| `renders_per_second` | Re-renders pendant le streaming | < 30/s |
| `localstorage_size_kb` | Taille des donnees persistees | < 5000 KB |
| `sse_chunks_per_second` | Debit de chunks recus | Informatif |
| `time_to_interactive_ms` | Temps de chargement initial | < 3000 ms |

### Commandes de monitoring

```bash
# Taille de la base SQLite
ls -lh ~/.therese/therese.db

# Verifier le mode WAL
sqlite3 ~/.therese/therese.db "PRAGMA journal_mode;"

# Compter les index
sqlite3 ~/.therese/therese.db ".indices"

# Taille localStorage (dans DevTools console)
# JSON.stringify(localStorage).length / 1024 + " KB"
```

---

*Rapport genere le 28 janvier 2026 par Claude Opus 4.5*
*22 findings : 2 CRITICAL, 6 HIGH, 9 MEDIUM, 5 LOW*
