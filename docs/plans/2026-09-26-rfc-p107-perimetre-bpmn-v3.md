# RFC P-107, version 3 : un périmètre d'action visible et gouvernable

Rédigé le 26/09/2026. Remplace la V2 (`docs/plans/2026-09-26-rfc-p107-perimetre-bpmn-v2.md`), refusée (NO-GO) par la revue adverse du 26/09 (19 constats : quatre P2, quinze P3 ; rapport de travail `revue-v2-p107-p108.md` de l'orchestrateur). Les décisions du 25/09/2026 (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md`, points 10 à 13) restent des faits ; l'écart de la V2 à la décision 13 est désormais signalé et posé à Ludo (§11). Aucun code avant la validation de ce document.

**Base de vérification.** Toutes les lignes citées ont été relues au commit `d80d4406` (26/09/2026, 02 h 37), par `git show d80d4406:<fichier>`, jamais dans l'arbre de travail, où l'orchestrateur corrige des défauts en parallèle. Les numéros de ligne de la V2 valaient pour `ca9f44d1` ; ceux de `routers/chat.py` ont glissé d'un à six rangs après la ligne 1697 (B-1495), et de six après la ligne 2380. Chemins relatifs à `src/backend/app/` (fichiers `.py`) et à `src/frontend/src/` (fichiers `.ts` et `.tsx`) ; les tests et `docs/` partent de la racine du dépôt.

**Prérequis corrigés à part par l'orchestrateur**, cités par leur numéro et jamais recodés ici :

- **B-1484** (corrigé, `ad455ddb`) : le Board cherche avec le moteur choisi (`services/board.py:278`, `get_web_search_service()`).
- **B-1495** (corrigé, `d80d4406`) : `include_memory=false` n'injecte plus la mémoire (`routers/chat.py:1739-1741`, `:2376-2378`).
- **B-1496** (corrigé, `5f492b30`) : l'outil `search_memory` du pont appelle `POST /api/memory/search` (`services/mcp_therese_server.py:274-276`), et `tests/test_b1496_pont_mcp_routes_existantes.py` vérifie que chaque outil du pont vise une route servie avec sa méthode.
- **B-1489** (corrigé en `d15ef8bd`, après la base de relecture) : un outil absent de la liste offerte au tour n'est plus exécuté. Prérequis du lot 5 : retirer un outil de la liste ne vaudrait rien sans lui. Ce commit et B-1494 (`6f927313`) ont déplacé les lignes de `routers/chat.py` au-delà de la ligne 2159 : les numéros cités ici valent à `d80d4406`.
- **B-1189** (différé, point c) et **B-1240** (différé) : deux défauts existants que cette RFC rend visibles sans les trancher (§4.3 et §4.8.3).

## 0. Constats de la revue V2 et leur traitement

| # | Gravité | Constat | Traitement | Où |
|---|---|---|---|---|
| 1 | P2 | Retirer « Fichiers indexés » laisse partir leur contenu par l'injection de mémoire, que le tableau déclarait « aucune » | **Accepté.** Relu : `_get_memory_context` (`routers/chat.py:745`) injecte les fragments `file` avec le nom du fichier (`:804-818`), aux deux appels (`:1739`, `:2376`). Même trou que le P1 de P-106 (constat 18 de sa revue). Crochet commun : le paramètre `types_permis` que la V3 de P-106 ajoute à `_get_memory_context` ; P-107 n'en ajoute pas un second, il restreint la même liste blanche selon les domaines retirés. Tableau corrigé, test « domaine retiré, aucun fragment `file` transmis » | §4.8.2, lot 5 |
| 2 | P2 | Les compétences versent contacts et notes au modèle, hors des points d'application | **Accepté, précisé.** `routers/skills.py:93-117` charge 50 contacts (nom, entreprise, e-mail, notes) et 50 projets (statut, budget). Seul le contact apparié au destinataire ou au client part au prompt (`services/skills/text_skills.py:64-72`, `:226-236`) ; aucun code ne relit les projets. Mémoire retirée : ni contacts ni projets chargés, et le prompt le dit. Test | §4.8.3, lot 5 |
| 3 | P2 | Le résolveur `fournisseur_ia` lit la configuration, pas la destination : la bascule du disjoncteur part chez un autre service en ligne | **Accepté.** Relu : bascule par défaut (`services/llm.py:488`), replis pris parmi toutes les clés enregistrées (`:772-790`, `:849-856`), Ollama seul exempté (`:833-841`). Le service de repli n'a reçu aucun accord, puisque l'accord se donne par finalité et par fournisseur (`lib/consent.ts:40-42`) : c'est **B-1189** (c), déjà reproduit et différé. P-107 possède la vérité de la vue, B-1189 la coupure : le résolveur rend la chaîne réelle, calculée par le même code que le disjoncteur. Test paramétré avec une clé de repli | §4.3, lot 2 |
| 4 | P2 | `/api/auth/token` rend le jeton complet à un appel sans Origin ; la phrase « l'agent travaillera sans accès à tes données » est fausse | **Accepté pour la phrase ; fermer la route est réfuté comme remède.** Le jeton est aussi écrit en clair dans `.session_token` (`main.py:404-407`), lisible par tout processus de l'utilisateur, ce que dit déjà le commentaire de la route (`main.py:692-695`) : fermer la route n'ôterait rien à un agent qui a un shell. La phrase est réécrite ; un test fige la limite connue pour qu'elle reste dite | §4.7, lot 4 |
| 5 | P3 | Le jeton de pont n'est révoqué ni à la fin d'une session ni à l'échec du lancement | **Accepté.** Un jeton par session, révoqué à l'échec du lancement (`routers/agents.py:1386-1391`), à l'annulation (`:1557`), au passage observé à `done` ou `error` (`:1474`), à l'arrêt et au plus tard après 12 heures. Trois tests | §4.7, lot 4 |
| 6 | P3 | `search_memory` du pont appelle en GET une route POST | **Corrigé à part (B-1496).** Conséquence pour la V3 : la règle « jeton de pont en GET seulement » tombe. Le jeton accepte exactement les couples (méthode, gabarit) de `TOOL_ROUTES` filtrés, et un POST n'y est admis que sur une liste fermée de lectures (`/api/memory/search`) | §4.7, lot 4 |
| 7 | P3 | La fiche d'un contact (prestations, traces) reste lisible quand « Factures » ou « E-mails » est retiré | **Accepté, tranché par le tableau.** Prestations et traces sont des objets du carnet (`services/memory_tools.py:1133-1152`, `:1155-1183`), et aucune `Activity(` du moteur n'est tirée d'un e-mail (`routers/crm.py:141`, `:534`, `routers/rgpd.py:284`, `:365`, `services/rgpd_auto.py:211`, `services/scoring.py:113`). La fiche entière relève de « Mémoire », ce que le tableau et l'écran disent. Test | §4.8.1, lot 5 |
| 8 | P3 | La réponse proposée à un e-mail est rangée sous « E-mails » sans point d'application, et l'écran dit « tes écrans restent à toi » | **Tranché par une règle écrite** : un geste explicite sur un objet transmet cet objet, et rien d'autre d'un domaine retiré. La réponse proposée transmet le message ouvert ; le contexte du carnet qu'elle joint (`routers/email.py:1875-1886`) relève de « Mémoire » et n'est plus joint quand Mémoire est retirée. L'accord jamais consulté sur ce chemin est **B-1240**, hors RFC | §4.8.3, lot 5 |
| 9 | P3 | Les connecteurs MCP échappent au retrait ; Google Workspace reste offert quand « E-mails » est retiré | **Accepté.** Chaque préréglage déclare les domaines de THÉRÈSE qu'il touche ; ses outils quittent la liste du chat quand l'un d'eux est retiré. L'identité du préréglage est gardée à l'installation (aujourd'hui perdue : identifiant tiré au hasard, `services/mcp_service.py:414`). Un connecteur ajouté à la main n'appartient à aucun domaine, et l'écran le dit | §4.8.4, lot 5 |
| 10 | P3 | `/rdv` pose une carte que la confirmation refusera | **Accepté et étendu** aux trois commandes déterministes (`services/slash_commands.py:36`) : `/contact` et `/projet` écrivent en Mémoire sans passer par la liste d'outils (`:183`, `:233`). Refus à la préparation, avec une phrase immédiate | §4.8.3, lot 5 |
| 11 | P3 | Sentinelle réseau incomplète, porte `continue_with_tool_results` oubliée, inventaire incomplet | **Accepté, avec une correction de la revue** : le code n'importe ni `imaplib` ni `smtplib`, mais `imap_tools` et `aiosmtplib` (`services/email/imap_smtp_provider.py:21`, `:30`), plus `caldav`, `openai`, `google.genai`, `playwright` et `socket`. La promesse « exhaustive par construction » est retirée ; la sentinelle devient une classification de tout import tiers. `continue_with_tool_results` entre dans les portes ; l'inventaire gagne `routers/chat.py:2640` et `services/agents/runtime.py:284` | §4.4, §5, lot 2 |
| 12 | P3 | Les critères « ouvrir le journal » visent un écran qui n'existe pas | **Accepté.** Aucun écran ne lit `/api/data/logs`. Pas d'écran nouveau (« trop d'interfaces », 27/08) : les critères se vérifient dans l'export RGPD et par `GET /api/data/logs` | lots 1 et 6 |
| 13 | P3 | La purge continue de dire « Les logs d'audit sont conservés pour des raisons légales » | **Accepté.** Texte réécrit au lot 1 (`routers/data.py:796-803`) ; `tests/test_routers_data.py:512` lit ce texte et garde son assertion | §4.5, lot 1 |
| 14 | P3 | Le crochet fail-closed fait échouer un test existant | **Accepté, et élargi** : trois tests exigent l'exécution directe sans fournisseur (`components/email/EmailCompose.test.tsx:73`, `components/email/EmailList.test.tsx:94`, `components/email/EmailDetail.test.tsx:145`). Le lot 6 les inverse | lot 6 |
| 15 | P3 | Trois confirmations d'écran échappent à la trace | **Accepté, et porté à cinq sites locaux** (Board, Atelier, devis de conversation, génération d'images, réunion), avec un critère écrit et une sentinelle sur les motifs d'appel | §4.6, lot 6 |
| 16 | P3 | « Registre d'actions » est déjà pris (`lib/actionRegistry.ts`) | **Accepté.** Nouveau nom : **inventaire de confiance** (`data/inventaire_confiance.json`, `services/inventaire_confiance.py`, `GET /api/confiance/inventaire`) | §4.2 |
| 17 | P3 | Après la purge, le cache des retraits reste en mémoire puis les domaines se rouvrent au redémarrage | **Accepté.** La purge remet les retraits au défaut, comme toutes les préférences (`routers/data.py:697`), invalide le cache aussitôt, et l'écran de purge le dit. Le même défaut existe pour l'interrupteur web : relevé à reproduire (ci-dessous) | §4.8.5, lot 5 |
| 18 | P3 | `rotate_key` change `_fernet` sans changer `_master_key` | **Vérifié, fondé.** `services/encryption.py:415`, `:431` ; la clé de base dérive de `_master_key` (`:467`) ; aucun appelant hors des tests. La V3 écrit que la rotation n'est pas prise en charge ; défaut latent relevé à reproduire | §4.5 |
| 19 | P3 | La décision 13 est réduite (retrait par domaine au lieu de par outil) sans le dire | **Accepté.** L'écart est signalé et posé à Ludo avec une recommandation | §11, question 3 |

### Défauts du code actuel relevés en relisant, hors de toute RFC

- **B-1189** (différé) : bascule vers un autre service en ligne sans l'accord de ce service. **B-1240** (différé) : la réponse proposée à un e-mail appelle le service sans consulter les accords. Cités, non traités ici.
- **À reproduire : l'interrupteur de recherche web survit à la purge jusqu'au redémarrage.** La purge supprime la préférence (`routers/data.py:697`) mais n'invalide que le profil et les clés (`:707-714`) ; le cache de `services/web_search.py:72-94` garde l'ancienne valeur. Entre-temps, la liste d'outils du chat relit la base (`routers/chat.py:2514-2518`) et offre `web_search`, que le service refuse encore. Effet borné au redémarrage suivant, où le défaut « autorisé » s'applique.
- **À reproduire : `rotate_key` casserait l'ouverture de la base.** Défaut latent, sans appelant dans le moteur : la rotation écrit une nouvelle clé maîtresse (`services/encryption.py:411`, `:427-428`) sans rechiffrer la base SQLCipher, dont la clé dérive de la clé maîtresse (`:467`).

## 1. Ce que la V3 change

- **Un crochet mémoire commun avec P-106** : une seule liste blanche de types injectables, restreinte par l'accord « documents » (P-106) et par les domaines retirés (P-107).
- **Une règle pour les gestes explicites**, qui dit ce que le retrait couvre hors de la conversation : compétences, réponse proposée, commandes déterministes.
- **Les connecteurs entrent dans le retrait** par les domaines que chaque préréglage déclare.
- **Le fournisseur d'IA se lit comme une chaîne** (« Mistral, puis en cas de panne : OpenAI »), calculée par le code même du disjoncteur.
- **Le jeton de pont suit la vie de la session**, et sa règle d'accès suit exactement `TOOL_ROUTES`.
- **L'écran ne promet plus ce que le poste ne peut garantir** au sujet d'OpenClaw.
- **Le registre s'appelle inventaire de confiance.**
- **Les confirmations d'écran tracées** obéissent à un critère écrit, sur cinq sites de plus.
- **La sentinelle réseau** classe tout import tiers et ne se dit plus exhaustive.
- **Le Board n'a plus de résolveur à part** (B-1484).

## 2. Décisions

Les décisions 10 à 12 et les cinq questions tranchées par la V2 (V2, §2) sont inchangées. La décision 13 est tenue sur sa portée (le retrait vaut dans la conversation, pour les agents d'action, pour le pont, et pour les gestes du §4.8.3), mais pas sur sa granularité : le retrait se fait par domaine et non par outil. C'est un écart, posé à Ludo (§11, question 3).

## 3. Ce qui existe

Les points d'appui et les manques relevés par la V2 (V2, §3) restent vrais, à trois changements près :

- **Le Board suit le moteur choisi** depuis B-1484 (`services/board.py:38`, `:278`). La ligne « écart » de la V2 sur DuckDuckGo et le résolveur `moteur_board` n'ont plus d'objet.
- **`include_memory` est honoré** depuis B-1495, en tout ou rien (`routers/chat.py:1739-1741`, `:2376-2378`). Il ne distingue pas les types de mémoire : le crochet du §4.8.2 le complète.
- **Le pont appelle `POST /api/memory/search`** depuis B-1496 (`services/mcp_therese_server.py:274-276`). Cette route ne rend que des fiches et des dossiers : les fragments de fichiers n'y reçoivent pas de titre et sont écartés (`routers/memory.py:515-546`).

Deux faits relevés pour la V3 :

- **L'identité d'un préréglage MCP se perd à l'installation.** `install_preset` appelle `add_server` avec le seul nom (`routers/mcp.py:682-688`), qui tire un identifiant au hasard (`services/mcp_service.py:414`). L'écran retrouve un préréglage installé par son nom mis en forme (`routers/mcp.py:529`). Les outils portent `{identifiant}__{outil}` (`services/mcp_service.py:915`).
- **Les confirmations d'écran passent par deux mécanismes** : le crochet `useExternalActionConfirmation` (sept appels, V2 §4.6) et des confirmations locales propres à cinq composants (`components/prototype/BoardConversationCard.tsx:726`, `components/prototype/AtelierConversationCard.tsx:174`, `components/prototype/InvoiceConversationCard.tsx:417`, `components/prototype/ImagesWorkspaceCanvas.tsx:201` et `:228`, `components/prototype/MeetingConversationCard.tsx:257`).

## 4. Conception

### 4.1 Les colonnes de la vue

Inchangées (V2, §4.1) : action, ce qu'elle fait (déclaré), qui valide (calculé pour un outil du chat), où partent les données (calculé), ce qui le coupe (état réel).

### 4.2 L'inventaire de confiance

Fichier canonique `data/inventaire_confiance.json`, lu par `services/inventaire_confiance.py` sur le modèle de `services/capacites.py` (chemin relatif au module, validé à la lecture). Route `GET /api/confiance/inventaire` dans un nouveau routeur `routers/confiance.py` ; le préfixe `/api/confiance` n'existe nulle part aujourd'hui. Le nom évite les deux collisions : « périmètre » (cloison d'une conversation) et « registre d'actions » (`lib/actionRegistry.ts`, cité par `services/chat_actions.py:4-10`).

Quatre types d'entrée, inchangés : `outil`, `connecteur`, `chemin`, `service`. Champs communs : `id`, `type`, `nom`, `effet`, `sorties`, `interrupteur`, `domaines` (liste, éventuellement vide) et `texte`. Une entrée `connecteur` porte en plus `preset_id` et le motif de ses domaines (« Gmail et Agenda de ton compte Google : les mêmes données que tes domaines E-mails et Agenda »). Le champ `validation` reste interdit pour un outil du chat.

### 4.3 Les résolveurs de sortie

| Résolveur | Lit | Rend, par exemple |
|---|---|---|
| `aucune` | rien | « Reste sur ta machine » |
| `fournisseur_ia` | la chaîne de repli réelle (ci-dessous) et `est_modele_ollama_cloud` | « Reste sur ta machine (modèle local mistral-small) », « Mistral (en ligne), puis en cas de panne : OpenAI (en ligne), puis ton modèle local », « Aucun service d'IA prêt » |
| `moteur_recherche` | interrupteur (`services/web_search.py:82-94`) et service choisi (`get_web_search_service`, `:488`) | « Coupée », « Brave Search », « DuckDuckGo », « SearXNG (hôte) » |
| `recherche_conversation` | le fournisseur, puis `moteur_recherche` | « Google, par Gemini » quand le service est Gemini (recherche native, `routers/chat.py:2533`), sinon comme `moteur_recherche` |
| `compte_mail`, `agenda_actif`, `connecteur`, `openclaw`, `mode_board`, `dictee`, `images` | inchangés (V2, §4.3) | |

**La chaîne de repli.** Une seule fonction décrit la bascule, extraite de `_resolve_with_circuit_breaker` (`services/llm.py:806-864`) sans en changer les règles : le fournisseur principal, puis, si `bascule_circuit` est vrai et que le principal n'est pas Ollama (garde B-1071, `:832-841`), les replis de `_get_fallback_configs` dans leur ordre (`:772-800`). P-106 (V3, lot 1) en tire `config_du_tour()`, la configuration qu'un tour retiendra ; P-107 (lot 2) en tire `chaine_de_repli()`, la liste complète pour la vue. Le premier des deux lots livrés fait l'extraction ; le second la réutilise. Ainsi la vue ne peut pas décrire une autre bascule que celle du moteur. Elle dit le repli tant que B-1189 ne l'a pas supprimé ; le jour où il l'est, la chaîne se réduit d'elle-même.

Aucun résolveur ne rend une clé, un jeton, un mot de passe ou une adresse complète de boîte.

### 4.4 Les sentinelles

Dans `tests/test_sentinelles_structure.py` :

1. **Complétude des outils** : inchangée (V2, §4.4), plus chaque préréglage de `PRESET_SERVERS` (`routers/mcp.py:306`) avec ses `domaines` déclarés.
2. **Cohérence de l'effet** : inchangée.
3. **Portes de sortie** : liste fermée `LLMService.stream_response`, `generate_content`, `stream_response_with_tools`, **`continue_with_tool_results`** (`services/llm.py:1051`), les `search` des services de recherche, `spawn_session` et `send_message` du pont OpenClaw, `send_message` des fournisseurs de mail, `MCPService.call_tool` et `execute_tool_call`, les générateurs d'images, la transcription. Chaque fonction qui appelle une porte, repérée par l'AST, figure dans les `points_d_appel` d'une entrée.
4. **Imports réseau** : chaque module de premier niveau importé par le moteur et qui n'appartient pas à la bibliothèque standard (`sys.stdlib_module_names`) est classé « réseau » ou « local » dans une table du test. Sont classés réseau aujourd'hui : `httpx` (18 modules l'importent), `aiosmtplib`, `imap_tools`, `caldav`, `openai`, `google.genai`, `playwright`. Pour la bibliothèque standard, `socket`, `ssl`, `smtplib`, `imaplib`, `http.client`, `urllib.request` sont listés ; `socket` est importé par trois modules (`services/browser_agent.py:100`, `services/skills/code_executor.py:1016`, `services/agents/bac_a_sable.py:36`), classés chacun avec leur motif. Tout module qui importe un module « réseau » est une porte, un fournisseur ou une exception motivée. **Ce que la sentinelle ne voit pas** : un accès réseau par `asyncio.open_connection` ou par un sous-processus. Elle rend l'oubli coûteux, pas impossible.

### 4.5 Le journal des validations

Inchangé (V2, §4.5) : `tool_confirmed` et `tool_refused` écrits par `confirm_tool` (`routers/chat.py:3520-3604`), à la validation avant l'exécution et au refus avant le `return` de `:3535-3536` ; condensat HMAC par une clé dérivée de la clé maîtresse ; `empreinte_action` tenue hors des journaux par sentinelle ; conservation 12 mois dans la boucle quotidienne existante ; effacement par la purge totale.

Deux ajouts :

- **Rotation.** La clé du condensat suit la clé maîtresse chargée au démarrage. La rotation de clé n'est pas prise en charge par l'application : `rotate_key` n'a aucun appelant hors des tests, et elle romprait l'ouverture de la base (relevé ci-dessus). Si une rotation est un jour livrée, les condensats d'avant et d'après ne se compareront plus entre eux ; c'est une perte de corrélation, sans exposition.
- **Le texte de la purge.** « Les logs d'audit sont conservés pour des raisons légales » (`routers/data.py:798`, `:803`) devient, tant que la question 1 du §11 n'est pas tranchée : « Le journal d'activité est conservé, sauf les validations, effacées avec le reste. » Le mot « sauvegarde » reste dans la variante qui en parle, pour `tests/test_routers_data.py:512`.

### 4.6 Les confirmations des écrans

**Le crochet devient fail-closed** (inchangé, V2 §4.6). Trois tests existants exigent l'inverse et sont réécrits au lot 6 : « conserve l'envoi direct en mode classique » (`components/email/EmailCompose.test.tsx:73`), « conserve la suppression directe en mode classique » (`components/email/EmailList.test.tsx:94`), « conserve la mise à la corbeille directe en mode classique » (`components/email/EmailDetail.test.tsx:145`). Le lot commence par passer toute la suite vitest avec le crochet fermé, pour relever les autres rendus sans fournisseur.

**Le critère de trace.** Une confirmation d'écran est tracée quand elle autorise un effet hors de la machine : un envoi, une action sur un service distant, ou un contenu confié à un service en ligne. Une écriture purement locale (brouillon, suppression locale) ne l'est pas, comme les écritures locales des écrans ne le sont pas aujourd'hui.

| Site | Nature | Tracée |
|---|---|---|
| les sept appels du crochet (V2, §4.6) | `email_envoye`, `email_corbeille`, `evenement_cree`, `evenement_modifie`, `piece_changement_statut`, `facture_payee`, `devis_accepte`, `devis_refuse` | oui |
| `components/prototype/BoardConversationCard.tsx:726` | `deliberation_cloud` | oui en mode Cloud ; non en mode Souverain, où rien ne part |
| `components/prototype/AtelierConversationCard.tsx:174` | `mission_atelier` | oui : des agents travaillent avec un modèle choisi |
| `components/prototype/ImagesWorkspaceCanvas.tsx:201`, `:228` | `image_generee` | oui : le prompt part chez le générateur |
| `components/prototype/MeetingConversationCard.tsx:257` | `reunion_creee` | oui : un agenda distant envoie les invitations |
| `components/prototype/InvoiceConversationCard.tsx:417` | aucune | non : brouillon local |

Les confirmations locales appellent la même fonction que le fournisseur, `tracerValidationEcran(nature, decision)` (`services/api/confiance.ts`, nouveau), dont le paramètre `nature` est typé par l'union : TypeScript refuse une nature inconnue. La route `POST /api/confiance/validations-ecran` et son modèle `extra="forbid"` sont inchangés.

**Sentinelle** (vitest) : chaque fichier de `src/` qui contient `requestExternalAction(`, `setConfirmationSnapshot(` ou `setConfirming(true)` figure dans la table ci-dessus, tracé ou non avec son motif. Un nouveau site non classé fait échouer la suite. Les confirmations de suppression en ligne (tâches, agenda, Board) utilisent d'autres états et restent hors de ce contrôle, parce qu'elles sont locales.

### 4.7 Le pont des agents OpenClaw

**Interrupteur** (`pont_agents_actif`, défaut actif) : inchangé.

**Le jeton de pont.** Un jeton aléatoire par session d'agent, créé dans `dispatch_to_openclaw` et passé en `THERESE_MCP_TOKEN` à la place du jeton de session (`routers/agents.py:1367-1378`). Il vit dans un registre en mémoire `{jeton: (session, créé le)}`. Le middleware (`main.py:738-796`) l'accepte uniquement :

- sur les couples (méthode, gabarit) de `TOOL_ROUTES` après retrait des outils d'écriture (`services/mcp_therese_server.py:259-281`), comparés segment par segment, jamais par préfixe ;
- pour un POST, seulement si le gabarit figure sur une liste fermée de lectures servies en POST, aujourd'hui `/api/memory/search` (B-1496) ; une sentinelle vérifie que chaque POST de `TOOL_ROUTES` filtré y figure ;
- si l'interrupteur est actif et que le domaine de la route n'est pas retiré, relus à chaque requête.

**Révocation** : à l'échec du lancement, avant le 502 (`routers/agents.py:1386-1391`) ; à l'annulation (`:1557`) ; quand THÉRÈSE observe le passage à `done` ou `error` (`:1474`) ; à l'arrêt de l'application ; au plus tard 12 heures après sa création. THÉRÈSE n'observe la fin d'une session que lorsque l'écran relit son détail (`:1466-1474`). Tant que ce n'est pas fait, le jeton reste valide jusqu'à ses 12 heures, mais il n'ouvre que les lectures du pont, filtrées à chaque requête.

**Ce que dit l'écran de l'Atelier**, interrupteur coupé : « THÉRÈSE n'ouvre plus tes données à cet agent. Un agent qui peut lancer des commandes sur cette machine peut encore les lire par d'autres voies : ne confie une mission qu'à un agent en qui tu as confiance. » La V2 promettait « sans accès à tes données », ce que le poste ne garantit pas : le jeton de session est lisible dans `.session_token` (`main.py:404-407`) et rendu à tout appel sans Origin (`main.py:697-708`, route exemptée à `:757`).

### 4.8 Retirer un domaine

#### 4.8.1 Les domaines et ce qu'ils couvrent

| Domaine | Conversation | Contexte injecté | Gestes et commandes | Agents d'action | Pont OpenClaw | Connecteurs |
|---|---|---|---|---|---|---|
| Mémoire : contacts, projets, et sur chaque fiche les prestations et les traces du carnet | `read_contact`, `create_contact`, `create_project` | types `contact` et `project` | `/contact`, `/projet` ; compétences (contact apparié) ; contexte du carnet de la réponse proposée | `crm` | `list_contacts`, `get_contact`, `search_memory`, `get_project` | aucun préréglage |
| E-mails | `read_emails`, `summarize_emails`, `search_emails`, `send_email` | aucun | aucun (la réponse proposée transmet le message ouvert, par ton geste) | `email` | `list_emails` | `google-workspace` |
| Agenda | `list_calendar_events`, `create_calendar_event` | aucun | `/rdv` | `calendar` | `list_events` | `google-workspace` |
| Factures et devis : les pièces, leurs lignes et leurs totaux | `search_invoices`, `invoice_totals` | aucun | aucun | `invoices` | `list_invoices` | aucun préréglage |
| Tâches | aucun | aucun | aucun | `tasks` | `list_tasks` | aucun préréglage |
| Fichiers indexés | `search_files`, `read_file` | type `file` | aucun | aucun | aucun | `filesystem` |

Les prestations d'une fiche sont des objets du carnet (intitulé, montant, financeur, `services/memory_tools.py:1141-1151`) et non des pièces : retirer « Factures » ne les masque pas, retirer « Mémoire » les retire avec la fiche. L'écran le dit sous chaque interrupteur.

Restent hors domaine, gouvernés par leurs réglages : `web_search` et `browser_navigate` (interrupteur web, `routers/chat.py:2533`), `generate_document` (sous carte), les pièces jointes (geste explicite), l'extraction d'entités (son interrupteur ; elle n'envoie que le message, les noms connus servant à un tri local après la réponse, `services/entity_extractor.py:135-143`), le type `owner` (ton profil).

#### 4.8.2 Le crochet mémoire commun avec P-106

La V3 de P-106 ajoute à `_get_memory_context` le paramètre `types_permis: list[str] | None`, une liste blanche passée à `async_search(memory_types=...)` (`services/qdrant.py:577-592`), aux deux appels (`routers/chat.py:1739`, `:2376`). P-107 n'ajoute pas de second paramètre. Une fonction unique, `types_de_memoire_permis(documents_permis, domaines_retires)`, part des quatre types écrits dans l'index (`contact`, `project`, `file`, `owner` : `routers/memory.py:252`, `:281`, `services/indexation.py:167`, `services/user_profile.py:450`) et retire :

- `file` si `documents_permis` est faux (P-106) ou si « Fichiers indexés » est retiré (P-107) ;
- `contact` et `project` si « Mémoire » est retirée (P-107).

**Qui porte quoi.** Le paramètre `types_permis` est nommé par la V3 de P-106, qui calcule la liste en ligne (`["contact", "project", "owner"]` quand l'accord manque). Le premier des deux lots livrés (lot 1 de P-106 ou lot 5 de P-107) crée le paramètre et la fonction `types_de_memoire_permis`, avec sa sentinelle : tout type écrit dans l'index figure dans la table de la fonction, faute de quoi il n'est jamais transmis. L'autre lot y branche sa condition au lieu de recalculer la liste. **Point d'accroche à reporter dans P-106** : que son lot 1 passe par cette fonction plutôt que par une liste écrite en dur, pour qu'une seule table dise quels types partent. `include_memory=false` (B-1495) garde son sens de tout ou rien, appliqué avant.

La phrase D6 sur les documents hors périmètre (`routers/chat.py:856-878`) n'est pas émise quand `file` n'est pas permis : elle parlerait de fichiers que la conversation ne consulte de toute façon pas.

#### 4.8.3 La règle des gestes explicites

**Un geste explicite sur un objet transmet cet objet, et rien d'autre d'un domaine retiré.** Elle tranche trois chemins que la V2 laissait flous :

- **Compétences** (`routers/skills.py:47`) : le prompt est ton geste. Mémoire retirée, `execute_skill` ne charge ni contacts ni projets (`:93-117`) ; l'enrichissement le dit (« contact non joint : la mémoire est retirée dans les réglages »).
- **Réponse proposée à un e-mail** (`routers/email.py:1853`) : le message ouvert part, puisque c'est lui que tu as choisi. Le contexte du carnet sur l'expéditeur (`:1875-1886`) n'est plus joint quand Mémoire est retirée. L'accord pour ce chemin reste **B-1240**.
- **Commandes déterministes** (`services/slash_commands.py:36`) : elles agissent dans la conversation, que le retrait couvre. Domaine retiré, `/contact`, `/projet` ou `/rdv` ne font rien et répondent aussitôt : « L'agenda est retiré de la conversation dans les réglages : crée le rendez-vous depuis l'Agenda. » Aucune carte n'est posée pour `/rdv` (`:279`).

Les écrans (Courrier, Agenda, Contacts, Factures) restent à toi : ce que tu y fais toi-même n'est pas touché.

#### 4.8.4 Les connecteurs

- `install_preset` transmet `preset_id` à `add_server`, qui l'enregistre dans `mcp_servers.json`. Pour un connecteur déjà installé, l'identité se retrouve au chargement par le nom, comme le fait déjà l'écran (`routers/mcp.py:529`) ; un préréglage renommé à la main ne se retrouve pas, et reste hors domaine.
- Domaines déclarés : `google-workspace` touche E-mails et Agenda (`routers/mcp.py:342`) ; `filesystem` touche Fichiers indexés (`:311`), puisqu'il lit les mêmes fichiers locaux. Les autres préréglages exposent les données d'un service tiers, pas celles d'un domaine de THÉRÈSE, et n'en déclarent aucun, chacun avec son motif dans l'inventaire.
- Quand un domaine est retiré, les outils des connecteurs qui le déclarent quittent la liste du chat au même point que les outils natifs. Le serveur n'est pas arrêté : couper un connecteur reste le geste de l'écran Connecteurs (`routers/mcp.py:94-135`).
- Un connecteur ajouté à la main n'appartient à aucun domaine. L'écran le dit : « Les connecteurs que tu as ajoutés toi-même se coupent un par un, dans Connecteurs. Ils te demandent toujours avant d'agir. »

#### 4.8.5 Points d'application, tous côté serveur

1. **Liste d'outils du chat** : outils natifs et outils de connecteurs du domaine retirés avant `retirer_outils_deja_en_attente` (`routers/chat.py:2539`) ; le bloc des capacités suit (`:2546`).
2. **Exécution** : B-1489 refuse tout outil absent de la liste du tour ; `confirm_tool` refuse en plus un outil d'un domaine retiré, pour la carte posée avant le retrait, avec la phrase « Accès retiré dans les réglages ».
3. **Contexte mémoire** : `types_de_memoire_permis` (§4.8.2).
4. **Gestes et commandes** : §4.8.3.
5. **Agents d'action** : `_gather_local_context` (`services/action_agents.py:253`) retire la source et l'écrit dans le contexte, sur le modèle de la ligne web (`:505-524`).
6. **Pont** : le middleware (§4.7).

**Le réglage** (`domaines_retires`) est mis en cache comme l'interrupteur web ; une préférence illisible au démarrage retire tous les domaines et l'écrit au journal. **La purge** remet les retraits au défaut, comme toutes les préférences (`routers/data.py:695-697`), et invalide le cache aussitôt, ainsi que celui de `pont_agents_actif`. La réponse de la purge le dit : « Tes réglages, retraits compris, reviennent aux valeurs de départ. » Garder les retraits après « Effacer toutes mes données » ferait mentir la promesse d'une remise à zéro ; après la purge, les domaines sont d'ailleurs vides.

**Ce que dit l'écran** : « Retirer un domaine le retire de la conversation, des agents d'action, des agents OpenClaw et des connecteurs qui le touchent. Tes écrans restent à toi. Un geste que tu fais sur un élément précis (répondre à un e-mail, lancer une compétence) transmet cet élément, sans rien d'autre du domaine retiré. » Et pour l'Atelier « Améliorer THÉRÈSE » : « L'Atelier lit le dossier de la mission, pas tes domaines. » Ses agents lisent l'espace de travail de la mission (`services/agents/runtime.py:196-197`), ce que la vue montre à sa ligne (§5), comme le demande P-106.

### 4.9 La vue

Inchangée (V2, §4.9). La ligne du Board suit `moteur_recherche`.

### 4.10 L'export

Inchangé (V2, §4.10) : Mermaid d'abord (lot 7a), BPMN avec `bpmndi` sur une grille fixe ensuite (lot 7b), le lecteur `.bpmn` de P-106 comme oracle. La V3 de P-106 confirme qu'elle ne fournit aucun écrivain BPMN.

### 4.11 Hors périmètre

Inchangé (V2, §4.11), avec une précision : ce document ne ferme pas `/api/auth/token` (§0, constat 4).

## 5. Inventaire des chemins

Contenu initial de l'inventaire, relevé à `d80d4406` par les appels aux portes du §4.4. Changements par rapport à la V2 : Board sous `moteur_recherche`, continuation et Atelier complétés, compétences, réponse proposée et commandes gouvernées.

| Chemin | Points d'appel | Validation | Sorties | Ce qui le coupe |
|---|---|---|---|---|
| Conversation | `routers/chat.py:1856` (sans flux) ; `:2640` (flux avec outils) ; `:3409` (continuation) ; outils `:3203`, `:3266`, `:3300`, `:3331` ; confirmation `:3563`, `:3570`, `:3577`, `:3586` | par outil, calculée | `fournisseur_ia`, puis selon l'outil | par domaine |
| Extraction d'entités | `routers/chat.py:975`, `services/entity_extractor.py:135` | automatique | `fournisseur_ia` | Extraction automatique |
| Recherche approfondie | `routers/chat.py:1147`, `services/deep_research.py:92`, `:120`, `:226`, `:298` | démarrée par toi | `fournisseur_ia`, `moteur_recherche` | Recherche web |
| Décision (Board) | `services/board.py:302`, `:520`, `:671`, `:953` | démarrée par toi | `mode_board`, `moteur_recherche` | Recherche web |
| Agents d'action | `services/action_agents.py:530`, `:834` | démarrés par toi | `fournisseur_ia`, `moteur_recherche` | par domaine, Recherche web |
| Améliorer THÉRÈSE (Atelier) | `services/agents/runtime.py:284`, `:321`, `services/agents/tools.py:930` | démarré par toi, fusion après relecture | `fournisseur_ia` (avec le dossier de la mission), `moteur_recherche` | Recherche web |
| Agents OpenClaw et pont | `routers/agents.py:1380`, `:1544` | démarrés par toi | `openclaw` | Pont des agents, par domaine |
| Atelier documentaire | `routers/documents.py:370`, `:501`, `:696` | démarré par toi | `fournisseur_ia` | aucun |
| Réponse proposée à un e-mail | `services/email_response_generator.py:211` | démarrée par toi | `fournisseur_ia` | Mémoire (contexte du carnet seulement) |
| Résumé de mails | `services/workspace_tools.py:1405` | lecture, sans carte | `fournisseur_ia` | E-mails |
| Compétences | `routers/skills.py:161`, `:223` | démarrées par toi | `fournisseur_ia` | Mémoire (contact joint seulement) |
| Commandes `/contact`, `/projet`, `/rdv` | `services/slash_commands.py:183`, `:233`, `:279` | démarrées par toi ; carte pour `/rdv` | `aucune`, `agenda_actif` pour `/rdv` | Mémoire, Agenda |
| Génération de commande | `routers/commands_v3.py:159` | démarrée par toi | `fournisseur_ia` | aucun |
| Appel direct d'un connecteur | `routers/mcp.py:250`, `:253`, `:265` | aucune carte ; aucun appelant dans l'interface | `connecteur` | Connecteur coupé |
| Envoi de mail depuis l'écran | `routers/email.py:1336`, `:1348`, `services/workspace_tools.py:1471` | carte d'écran ou du chat | `compte_mail` | aucun (écran) |
| Dictée | `routers/voice.py:55`, `:215` | démarrée par toi | `dictee` | accord « voice » |
| Images | `routers/images.py:80`, `:153` | démarrées par toi, carte d'écran | `images` | aucun |
| Synchro CRM Google Sheets | `routers/crm.py:918-1156`, `services/sheets_service.py` | démarrée par toi | Google Sheets | aucun |

## 6. Lots

Chaîne de chaque lot : tests écrits d'abord et vus rouges, code, sabotage ciblé par fonction, revue adverse du diff, recette dans l'application lancée.

### Lot 1 : le journal des validations (moteur)

Livre §4.5. Tests de la V2 (lot 1), plus :

- le texte de purge ne contient plus « raisons légales » et dit que les validations sont effacées ; `tests/test_routers_data.py:512` reste vert ;
- **critère observable** (au lieu de « ouvrir le journal ») : valider une carte d'envoi, puis `GET /api/data/logs?action=tool_confirmed` rend une ligne avec l'outil et un condensat, sans rien du message ; l'export RGPD contient la même ligne.

### Lot 2 : l'inventaire, les résolveurs et la route (moteur)

Livre §4.2 à §4.4 et le §5. Tests de la V2 (lot 2), plus :

- **chaîne de repli**, tableau paramétré : Mistral seul ; Mistral avec une clé OpenAI enregistrée (la ligne dit « puis en cas de panne : OpenAI ») ; Ollama local avec une clé OpenAI (aucun repli en ligne, garde B-1071) ; Board, dont la bascule est coupée (`services/board.py:620`) ; chaque cas confronté à ce que `_resolve_with_circuit_breaker` retient quand le principal est déclaré en panne ;
- **Board** : le moteur choisi (Brave) apparaît sur sa ligne, preuve que `moteur_board` a disparu ;
- **sentinelle 4** vue rouge sur un module fabriqué qui importe `imap_tools` sans être classé, puis sur un import tiers inconnu ;
- **sentinelle 3** vue rouge sur une fonction fabriquée qui appelle `continue_with_tool_results` sans être déclarée.

### Lot 3 : la vue (écran)

Inchangé (V2, lot 3).

### Lot 4 : le pont des agents (moteur, écran)

Livre §4.7. Tests de la V2 (lot 4), plus :

- `POST /api/memory/search` passe avec le jeton de pont ; `POST /api/email/send` et `POST /api/tasks` renvoient 403 ;
- sentinelle : chaque POST de `TOOL_ROUTES` filtré figure dans la liste fermée des lectures ;
- révocation : lancement en échec (le 502 est rendu et le jeton refusé ensuite), passage observé à `done`, passage observé à `error`, annulation, 12 heures sur horloge simulée ;
- **limite connue, figée** : pont coupé et jeton de pont révoqué, `GET /api/auth/token` sans Origin rend toujours le jeton de session. Le test porte le nom de la limite, pour qu'un changement futur la fasse relire ;
- vitest : la phrase de l'Atelier contient « peut encore les lire par d'autres voies » et ne contient pas « sans accès à tes données ».

### Lot 5 : le retrait par domaine (moteur, écran)

Livre §4.8. Dépend du lot 4 pour le pont et de **B-1489** (corrigé).

- **sentinelle** : chaque outil natif, chaque outil du pont, chaque `tools` de `agents/action_agents.json`, chaque préréglage et chaque commande de `DETERMINISTIC_COMMANDS` appartient à un domaine ou à la liste hors domaine ;
- **Fichiers indexés retirés** : un fichier indexé pertinent n'apparaît pas dans le contexte transmis (espion sur `async_search` : `memory_types` sans `file`) ; `search_files` et `read_file` absents de la liste et du bloc des capacités ; la phrase D6 absente ;
- **Mémoire retirée** : aucun `contact` ni `project` dans `memory_types` ; `execute_skill` avec un destinataire connu produit un prompt sans ses notes ni son e-mail ; `generate-response` sur un message d'un contact connu produit un prompt sans « Contexte CRM » ; `/contact Marie` ne crée rien et répond la phrase ; `read_contact` absent ; `get_contact` du pont en 403 ;
- **Factures retirées** : `read_contact` reste offert et rend `etat_courant` (les prestations relèvent de Mémoire, test de contrat) ;
- **E-mails retirés** : les quatre outils absents de la liste et du bloc des capacités ; aucun outil `…__` d'un serveur installé depuis `google-workspace` ; un serveur ajouté à la main reste offert ; une carte `send_email` posée avant le retrait est refusée à la confirmation ; l'agent « relance-clients » reçoit la ligne « accès retiré » ; le jeton de pont reçoit 403 sur `/api/email/messages` ;
- **Agenda retiré** : `/rdv` ne pose aucune carte (`register_pending` non appelé) et répond la phrase ;
- **identité de préréglage** : un préréglage installé enregistre `preset_id` ; un fichier `mcp_servers.json` d'avant ce lot retrouve l'identité par le nom ;
- **purge** : après `DELETE /api/data/all?confirm=true`, `domaines_retires` et `pont_agents_actif` reviennent au défaut sans redémarrage, et la note le dit ;
- **préférence illisible** : tous les domaines retirés, avertissement au journal ;
- vitest : un interrupteur nommé par domaine, avec ce qu'il couvre ; la phrase des gestes explicites ; la phrase des connecteurs ajoutés à la main.

Critère observable : retirer E-mails, puis demander « lis mes mails » ; l'assistante répond que l'accès est retiré dans les réglages, et Google Workspace n'est pas proposé.

### Lot 6 : les confirmations des écrans (écran, moteur)

Livre §4.6. Dépend du lot 1.

- vitest : les trois tests « mode classique » sont inversés (sans fournisseur, l'action n'est pas appelée et le message « Action bloquée » s'affiche) ; toute la suite passe avec le crochet fermé ;
- vitest : chacun des cinq sites locaux appelle `tracerValidationEcran` avec sa nature à la confirmation et à l'abandon, sauf le devis de conversation ; le Board en mode Souverain n'appelle rien ;
- vitest : la sentinelle des motifs d'appel, vue rouge sur un composant fabriqué ;
- pytest : inchangé (V2, lot 6).

Critère observable : envoyer un e-mail depuis le Courrier, puis l'export RGPD contient « screen_action_confirmed, email_envoye, déclarée par l'interface ».

### Lot 7 : l'export

Inchangé (V2, lot 7a et 7b).

## 7. Données et migrations

- **Aucune révision Alembic.** La tête reste `b8c9d0e1f2a3` (`models/database.py:619`).
- **`mcp_servers.json`** gagne un champ `preset_id` facultatif. Un fichier d'avant le lot 5 se lit tel quel, et B-1498 (corrigé) relit déjà ce fichier après une restauration (`routers/data.py:1693-1699`).
- **Préférences** : `pont_agents_actif`, `domaines_retires`, effacées par la purge avec les autres (`routers/data.py:697`).
- Le reste est inchangé (V2, §7).

## 8. Risques restants

- **Un agent qui a un shell sur la machine** lit le jeton de session. L'interrupteur et le retrait gouvernent le chemin prévu, pas un agent malveillant ; l'écran le dit désormais.
- **Le repli vers un autre service en ligne** existe tant que B-1189 n'est pas tranché ; la vue le montre au lieu de le taire.
- **Un connecteur ajouté à la main, ou un préréglage renommé**, reste hors des domaines ; l'écran le dit.
- **La sentinelle réseau** ne voit ni `asyncio.open_connection` ni un sous-processus.
- **Fin de session OpenClaw non observée** : le jeton reste valide jusqu'à 12 heures, limité aux lectures filtrées.
- **Validation déclarée pour les chemins de fond**, ce qu'OpenClaw fait des données, le condensat comme corrélation, les cartes jamais tranchées, la fatigue d'interface : inchangés (V2, §8).

## 9. Ce que la V3 retire ou reporte, et pourquoi

| Élément de la V2 | Sort | Motif |
|---|---|---|
| Résolveur `moteur_board` et ligne « écart » DuckDuckGo | retirés | B-1484 : le Board suit le moteur choisi |
| « Registre d'actions », `data/registre_actions.json` | renommé | collision avec `lib/actionRegistry.ts` |
| Règle « jeton de pont en GET seulement » | remplacée | B-1496 : une lecture est servie en POST ; la règle suit désormais `TOOL_ROUTES` couple par couple |
| « Exhaustive par construction » (sentinelle 4) | retiré | faux : `asyncio` et les sous-processus lui échappent |
| « L'agent travaillera sans accès à tes données » | retiré | le poste ne le garantit pas |
| Critères « ouvrir le journal » | remplacés | aucun écran ne lit le journal ; pas d'écran nouveau |
| Retrait par outil isolé | reporté à la décision de Ludo | §11, question 3 |
| Fermeture de `/api/auth/token` | écartée | le même jeton est lisible dans `.session_token` ; hors périmètre (V2, §4.11) |

Ce que la V2 faisait bien est gardé tel quel : le condensat HMAC et sa sentinelle, les deux colonnes effet et validation, les résolveurs calculés, le tableau texte comme vue qui fait foi, la greffe sur P-118, l'export Mermaid puis BPMN, l'absence de migration.

## 10. Livraison

Ordre : lot 1, lot 2, lot 3, lot 4, lot 5 (B-1489 est corrigé), lot 6, lot 7a, lot 7b. Le crochet mémoire (§4.8.2) est créé par le premier livré du lot 1 de P-106 ou du lot 5 de P-107. La chaîne de repli (§4.3) est extraite par le premier livré du lot 1 de P-106 ou du lot 2 de P-107. Revue adverse du design de ce document avant le lot 1, puis revue du diff à chaque lot. Aucune release sans le GO de Ludo.

## 11. Questions réservées à Ludo

1. **Le reste du journal d'activité** : inchangée (V2, §11, question 1). Suppression définitive de données sur les machines des utilisateurs. **Recommandation** : 12 mois et effacé par la purge, sauf la ligne qui date la purge.
2. **L'export BPMN dans la communication publique** : inchangée (V2, §11, question 2). **Recommandation** : attendre la recette du lot 7 et le retour de Dr_logic.
3. **La décision 13, retrait par domaine plutôt que par outil.** Tu as validé « Retirer un outil… partout » (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md:48-49`), et la V1 prévoyait un réglage « par outil de lecture et par serveur MCP » (`docs/plans/2026-09-25-rfc-p107-perimetre-bpmn.md:68`). La V2 et la V3 retirent par domaine : on ne peut plus garder la lecture des mails tout en retirant l'envoi. **Motif** : les agents d'action ne connaissent que des sources par domaine (`email`, `calendar`, `crm`…), et le pont ne connaît que des routes ; un retrait par outil ne pourrait valoir « partout » qu'en inventant une correspondance outil par outil dans chacun, et l'écran dirait deux choses différentes selon l'endroit. L'envoi reste de toute façon sous carte, donc jamais fait sans toi. **Recommandation** : garder le retrait par domaine pour ce chantier, et n'ajouter un état « lecture seule » par domaine (écritures retirées, lectures gardées) que sur une demande exprimée.

## Annexe : appuis dans le code

- Mémoire injectée : `routers/chat.py:745-882`, appels `:1739`, `:2376` ; filtre par type `services/qdrant.py:235-270`, `:577-592`.
- Liste d'outils : `routers/chat.py:2512-2546` ; portillon `services/tool_confirmations.py:33-49` ; confirmation `routers/chat.py:3520-3604`.
- Disjoncteur : `services/llm.py:485-500`, `:769-800`, `:806-864` ; accords `lib/consent.ts:26-80`.
- Pont : `routers/agents.py:1367-1400`, `:1455-1480`, `:1557` ; `services/mcp_therese_server.py:240-281` ; jeton de session `main.py:400-409`, `:686-708`, `:738-796`.
- Compétences : `routers/skills.py:47-161` ; `services/skills/text_skills.py:58-75`, `:220-239`.
- Réponse proposée : `routers/email.py:1853-1886` ; `services/email_response_generator.py:124-215`.
- Commandes : `services/slash_commands.py:36`, `:161-294`.
- Connecteurs : `routers/mcp.py:306-513`, `:525-536`, `:603-690` ; `services/mcp_service.py:397-420`, `:904-930`.
- Fiche : `services/memory_tools.py:958-1019`, `:1133-1183`.
- Purge : `routers/data.py:632-806`.
- Confirmations d'écran : `components/app/useExternalActionConfirmation.ts`, `components/app/ExternalActionConfirmation.tsx`, et les cinq sites du §3.
