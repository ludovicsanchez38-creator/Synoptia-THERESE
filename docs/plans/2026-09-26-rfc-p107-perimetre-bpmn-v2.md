# RFC P-107, version 2 : un périmètre d'action visible et gouvernable

Rédigé le 26/09/2026. Remplace la V1 (`docs/plans/2026-09-25-rfc-p107-perimetre-bpmn.md`), jugée NO-GO par la revue adverse (`docs/plans/revues/2026-09-25-revue-rfc-p105-p108.md`, section P-107 : un P1, deux P2, sept P3). Intègre les décisions du 25/09/2026 (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md`, points 10 à 13). Aucun code avant la validation de ce document.

Toutes les lignes citées ont été relues au commit `ca9f44d1` (26/09/2026, 01 h 30). Chemins relatifs à `src/backend/app/` et à `src/frontend/src/`, sauf mention contraire.

## 0. Ce qui change par rapport à la V1

- **Le journal des validations n'écrit jamais `empreinte_action`.** Il écrit un condensat HMAC dérivé de la clé maîtresse, calculé sur des arguments dont les clés privées sont retirées. La fonction de déduplication reste en mémoire, et une sentinelle l'empêche d'atteindre un journal.
- **Deux colonnes au lieu de quatre régimes mêlés** : l'effet est déclaré, la validation est calculée par le portillon.
- **Les données qui sortent sont calculées** d'après la configuration réelle (fournisseur d'IA, agenda, compte mail, moteur de recherche, connecteurs), par des résolveurs testés un par un.
- **Le registre change de nom** : `data/registre_actions.json` et `/api/confiance/...`, parce que « périmètre » désigne déjà la cloison d'une conversation dans 12 fichiers du moteur (117 lignes contiennent `perimetre`, par exemple `services/perimetre_backfill.py` et `_perimetre_de_conversation` dans `routers/chat.py:3568`).
- **L'inventaire des chemins est relevé dans le code** (§5) et tenu à jour par deux sentinelles.
- **Le pont des agents OpenClaw entre au registre**, avec un interrupteur et un jeton qui lui est propre, faute de quoi ni l'interrupteur ni le retrait ne peuvent s'appliquer côté serveur.
- **Le retrait se fait par domaine de données, partout** : conversation, agents d'action, pont OpenClaw, contexte mémoire injecté.
- **La vue qui fait foi est un tableau texte** dans Confidentialité ; le Centre de confiance se greffe sur la ligne d'état livrée par P-118.
- **L'export BPMN appartient à P-107**, avec sa mise en page et son chiffrage : la V2 de P-106 n'écrit aucun BPMN. Un export Mermaid sort d'abord ; le lecteur BPMN de P-106 servira d'oracle de test.
- **Les confirmations des écrans sont tracées** par une route dédiée, marquées « déclarées par l'interface », et le crochet cesse d'exécuter une action faute de fournisseur.
- **Aucune migration Alembic.**

## 1. Le besoin

Dr_logic-3D, sur Discord (fil du 25/09, 03:35 à 04:29), demande un modèle BPMN du périmètre d'action de THÉRÈSE (étapes, RACI, validations requises), pour rendre **visible** et **gouvernable** ce que THÉRÈSE observe, prépare, propose ou exécute, et dire où une validation est exigée.

## 2. Décisions tranchées

### Décisions du 25/09/2026 (faits acquis)

| N° | Décision | Où elle vit dans cette V2 |
|---|---|---|
| 10 | Journal des validations : outil, date, oui ou non, empreinte salée, jamais le contenu ; conservé 12 mois ; effacé par « Effacer toutes mes données ». | §4.5, lot 1 |
| 11 | Le Centre de confiance dit ce qui sort d'après la configuration réelle, comme la ligne d'état de P-118. | §4.3, lots 2 et 3 |
| 12 | Le pont qui ouvre contacts, e-mails, factures, tâches et agenda aux agents OpenClaw apparaît au périmètre, avec un interrupteur. | §4.7, lot 4 |
| 13 | « Retirer » vaut partout (conversation, agents, Atelier), et l'écran le dit. | §4.8, lot 5 |

### Questions de la V1 tranchées par cette V2

1. **Vocabulaire à l'écran.** L'écran parle en mots simples : pour l'effet, « Lit », « Prépare », « Enregistre », « Agit à l'extérieur » ; pour la validation, « Te demande avant » ou « Sans te demander ». Le vocabulaire BPMN (observe, prépare, propose, exécute) n'apparaît que dans l'export, où il a un sens pour le lecteur. Motif : « propose » n'est pas un effet mais une étape de validation (constat 6 de la revue) ; le mettre à côté de « lit » à l'écran reproduirait la confusion.
2. **RACI.** Remplacé par trois questions : qui fait, qui valide, où partent les données. Avec un seul humain, le RACI se réduit à une formule creuse ; les trois questions sont celles que pose un utilisateur. L'export BPMN rend la même information par ses couloirs.
3. **Tracer les confirmations des écrans.** Oui, par une route dédiée, au lot 6 (§4.6).
4. **Assouplir (lecture MCP sans carte).** Non. Le registre ne sait que restreindre ; aucune entrée ne peut retirer un outil du portillon. Une demande d'assouplissement fera l'objet de sa propre RFC.
5. **Retrait par projet.** Non : le retrait vaut pour toute l'application. Le cloisonnement par dossier existe déjà pour le carnet (`mode_cabinet`, `routers/config.py:710-798`) ; un second axe par projet doublerait la surface de réglage sans demande exprimée.

## 3. Ce qui existe, relu dans le code

### Points d'appui

- **Trois classes d'effet par outil du chat** : `LECTURE_SEULE`, `MUTATION_LOCALE`, `MUTATION_EXTERNE` (`services/contexte_execution.py:26-28`), attribuées aux 16 outils natifs (`:30-53`). Un nom inconnu, MCP compris, est externe (`:56-59`).
- **Un portillon fail-closed** : seule la lecture classée passe sans carte (`services/tool_confirmations.py:33-49`). Le modèle apprend quels outils sont sous carte par un bloc dérivé de la liste réellement transmise (`:52-86`, appelé à `routers/chat.py:2586`). Les cartes en attente vivent en mémoire (`services/tool_confirmations.py:19-20`).
- **Une seule carte par action** dans un tour (`routers/chat.py:3140-3159`) et aucune relance tant qu'une carte attend (`:3444`) ; un outil déjà en attente est retiré de la liste (`:2213`, appelé à `:2533`).
- **Le bloc des capacités annoncées est dérivé outil par outil** de la liste transmise (`routers/chat.py:2540-2580`) : retirer un outil de la liste suffit à ne plus le promettre.
- **Couper un connecteur MCP sans le désinstaller existe déjà** : `PUT /api/mcp/servers/{id}` avec `enabled=false` arrête le serveur et l'enregistre (`routers/mcp.py:123-135`), et seuls les serveurs en marche exposent leurs outils (`services/mcp_service.py:882-888`). La V1 affirmait le contraire.
- **L'interrupteur de recherche web est gardé à la porte** : chaque service de recherche le vérifie avant de partir (`services/web_search.py:213`, `:303`, `:436`, `:705`). Il couvre donc déjà le Board (`services/board.py:278`, `:302`), l'Atelier (`services/agents/tools.py:928`), la recherche approfondie (`services/deep_research.py:117`, `:212`) et les agents d'action, qui le lisent aussi explicitement (`services/action_agents.py:520-524`).
- **L'extraction d'entités a son interrupteur**, lu depuis B-1154 (`routers/chat.py:960-968`).
- **Le pont OpenClaw est en lecture seule** : les six outils d'écriture sont retirés de la liste et refusés à l'exécution (`services/mcp_therese_server.py:242-250`, `:277-279`, `:372-375`).
- **L'Atelier « Améliorer THÉRÈSE »** retire `write_file` et `run_command` à `/spawn` (`routers/agents.py:74`, `:618`) et ne fusionne qu'une tâche en statut `review` (`:863-875`).
- **La ligne d'état de P-118** lit le service d'IA et la recherche web à l'ouverture du Centre de confiance (`components/prototype/CapabilityCenter.tsx:491-516`, `:533-540`).
- **Le journal d'activité** (`services/audit.py:63-75`) écrit par savepoint sans décider de la transaction de l'appelant (`:136-138`) ; il part dans l'export RGPD (`routers/data.py:410-420`).

### Manques

- **Aucune colonne « données qui sortent »** nulle part, et aucune correspondance entre un outil et ce qu'il fait sortir.
- **La ligne « Ce qui sort de ta machine » est un texte écrit à la main** (`components/prototype/CapabilityCenter.tsx:589`). Elle nomme trois chemins qui cherchent sans carte ; rien ne la tient à jour.
- **Les validations ne laissent aucune trace** : `confirm_tool` (`routers/chat.py:3514-3598`) n'écrit rien au journal, et `AuditAction` n'a ni « validé » ni « refusé » (`services/audit.py:19-60`).
- **Le nettoyage du journal ne tourne jamais** : `DELETE /api/data/logs` (`routers/data.py:906-925`) n'a aucun appelant dans l'interface, et le démarrage ne planifie que l'OAuth, les notifications et la purge RGPD des contacts (`main.py:341-383`). De plus, `cleanup_old_logs` efface **toutes** les actions plus anciennes que N jours (`services/audit.py:218-247`).
- **La purge garde tout le journal** : « On garde les logs d'audit (trace legale) » (`routers/data.py:698`).
- **Le pont reçoit le jeton de session complet** (`routers/agents.py:1373-1375`, envoyé en `X-Therese-Token` par `services/mcp_therese_server.py:328-330`), et le middleware ne distingue pas ses appels de ceux de l'interface (`main.py:770-790`). Aucun réglage ne peut donc s'appliquer au pont côté serveur.
- **Le crochet des écrans exécute sans rien demander** en l'absence de fournisseur (`components/app/useExternalActionConfirmation.ts:26-33`). Le fournisseur n'entoure que `ConversationCanvasPrototype` (`App.tsx:248-250`).

### Écarts de la V1 relevés par cette V2

| V1 | Réalité |
|---|---|
| « on ne peut ni retirer un outil de lecture ni couper un outil MCP sans désinstaller son serveur » | Couper un serveur MCP existe (`routers/mcp.py:123-135`). Reste vrai pour les outils natifs. |
| Chemins de fond : Board, recherche approfondie, agents d'action, Atelier, extraction | Manquaient : le pont OpenClaw (`routers/agents.py:1367-1378`), la rédaction de l'atelier documentaire (`routers/documents.py:370`, `:501`, `:696`), la réponse proposée à un e-mail (`services/email_response_generator.py:211`), les compétences (`routers/skills.py:161`, `:223`), la génération de commande (`routers/commands_v3.py:159`), le résumé de mails (`services/workspace_tools.py:1405`). |
| Registre `data/perimetre.json`, route `/api/perimetre` | Collision avec le périmètre de conversation. Renommé. |
| `components/chat/ToolConfirmationCard.tsx:85-102` « arguments bruts » | Ces lignes portent aujourd'hui les titres français des cartes (B-1480). Citation retirée. |
| (non relevé) | Le Board cherche toujours chez DuckDuckGo, même quand l'utilisateur a choisi Brave ou SearXNG (`services/board.py:278`). Candidat défaut à reproduire hors de cette RFC ; la vue le dira tel quel en attendant. |

## 4. Conception

### 4.1 Les colonnes de la vue

| Colonne | Source | Valeurs |
|---|---|---|
| Action | registre (déclaré) | nom en français |
| Ce qu'elle fait | registre (déclaré, tenu par sentinelle) | Lit, Prépare, Enregistre, Agit à l'extérieur |
| Qui valide | **calculé** : `requires_confirmation(nom)` pour un outil du chat ; pour un chemin de fond, déclaré (§8) | Te demande avant, Sans te demander (démarré par toi), Automatique |
| Où partent les données | **calculé** par un résolveur (§4.3) | Reste sur ta machine, ou le service nommé |
| Ce qui le coupe | registre, avec l'état réel de l'interrupteur | nom du réglage et son état |

« Prépare » désigne ce qui produit une proposition que l'utilisateur relit sans que rien ne soit appliqué : l'Atelier (diff en attente de relecture), les agents d'action, la recherche approfondie. « Enregistre » désigne une écriture sur la machine (contact, projet, document, rendez-vous local). Un rendez-vous posé dans un agenda Google reste « Enregistre » dans la colonne déclarée, et la colonne calculée dit « Google Agenda (en ligne) » : l'utilisateur lit les deux.

### 4.2 Le registre `data/registre_actions.json`

Fichier canonique à côté de `data/capacites.json`, lu par un module `services/registre_actions.py` sur le modèle de `services/capacites.py` (chemin résolu relativement au module, validé à la lecture). Quatre types d'entrée :

- `outil` : un outil natif du chat (clé de `CLASSIFICATION_DES_OUTILS`) ;
- `connecteur` : un préréglage MCP (`PRESET_SERVERS`, `routers/mcp.py:306`), plus une entrée générique pour tout serveur ajouté à la main ;
- `chemin` : un chemin de fond, avec la liste de ses points d'appel sous la forme `module:Classe.fonction` ;
- `service` : un service branché par l'utilisateur (Gmail, IMAP, Google Agenda, CalDAV, synchro Google Sheets du CRM, dictée Groq, génération d'images).

Champs communs : `id`, `type`, `nom`, `effet`, `sorties` (liste de résolveurs), `interrupteur`, `domaine` (§4.8) et `texte` (une phrase). Le champ `validation` n'existe que pour les chemins et les services ; pour un outil du chat, il est interdit, puisque calculé.

### 4.3 Les résolveurs de sortie

La route résout chaque nom de résolveur contre la configuration réelle, au moment de la lecture :

| Résolveur | Lit | Rend, par exemple |
|---|---|---|
| `aucune` | rien | « Reste sur ta machine » |
| `fournisseur_ia` | configuration du service d'IA, `est_modele_ollama_cloud` (`services/ollama_capabilites.py:86`) | « Reste sur ta machine (modèle local mistral-small) », « Ollama Cloud (ollama.com) », « Mistral (en ligne) », « Aucun service d'IA prêt » |
| `moteur_recherche` | interrupteur (`services/web_search.py:82-94`), service choisi (`get_web_search_service`, `:488`), fournisseur Gemini | « Coupée », « Brave Search », « DuckDuckGo », « SearXNG (adresse) », « Google, par Gemini » |
| `moteur_board` | interrupteur seulement : le Board instancie toujours `WebSearchService`, c'est-à-dire DuckDuckGo (`services/board.py:38`, `:278` ; classe `services/web_search.py:263-270`), quel que soit le moteur choisi | « Coupée », « DuckDuckGo » |
| `compte_mail` | `EmailAccount.provider` (`models/entities.py:347`) et la destination que la carte utilise déjà (`services/workspace_tools.py:1053`) | « Gmail », « serveur IMAP et SMTP (hôte) », « Aucune boîte branchée » |
| `agenda_actif` | `Calendar.provider` (`models/entities.py:487`) et `get_calendar_confirmation_destination` (`services/workspace_tools.py:1240`), la fonction même qu'utilise la carte (`routers/chat.py:3110-3118`) | « Reste sur ta machine », « Google Agenda (en ligne) », « serveur CalDAV (hôte) » |
| `connecteur` | serveurs MCP installés et leur état | « Slack, en marche », « Slack, coupé » |
| `openclaw` | configuration OpenClaw | « Agents OpenClaw, puis le modèle choisi dans OpenClaw, que THÉRÈSE ne connaît pas » |
| `mode_board` | aucun état stable | « Selon le mode choisi à chaque délibération : Souverain (local) ou Cloud » |
| `dictee` | résolu **côté écran** : la préférence de voix locale et l'accord `voice` vivent dans la webview (`lib/consent.ts:26`) | « Reste sur ta machine », « Groq (en ligne) » |
| `images` | clés configurées des générateurs (`services/image_generator.py:147`, `:226`, `:308`) | « Le service choisi à la génération : OpenAI, Gemini ou Fal » |

Aucun résolveur ne rend une clé, un jeton, un mot de passe ou une adresse complète de boîte ; seuls un nom de service et un nom d'hôte sortent.

### 4.4 Les sentinelles

Quatre sentinelles, dans `tests/test_sentinelles_structure.py` (qui porte déjà les contrôles AST et JSON du dépôt) :

1. **Complétude des outils** : chaque clé de `CLASSIFICATION_DES_OUTILS` (`services/contexte_execution.py:30-53`), chaque `id` de `PRESET_SERVERS` et chaque outil du pont (`services/mcp_therese_server.py:250`) a exactement une entrée.
2. **Cohérence de l'effet** : `LECTURE_SEULE` impose « Lit » ; `MUTATION_LOCALE` interdit « Lit » ; aucune entrée `outil` ne porte de champ `validation`.
3. **Portes de sortie** : une liste fermée de portes (`LLMService.stream_response`, `LLMService.generate_content`, `LLMService.stream_response_with_tools`, les `search` des services de recherche, `spawn_session`, `send_message` des fournisseurs de mail, `MCPService.call_tool`, les générateurs d'images, la transcription Groq) ; chaque fonction qui appelle une porte, repérée par l'AST, figure dans les `points_d_appel` d'une entrée. Une nouvelle fonction qui appelle le modèle sans être déclarée fait échouer la suite.
4. **Modules réseau** : 33 modules mentionnent aujourd'hui `httpx` ou `http_client` (relevé du 26/09), dont les 10 fichiers de `services/providers/`. Chaque module qui importe `httpx` ou `services/http_client` est soit une porte, soit un fournisseur (`services/providers/`), soit listé comme technique avec son motif (`core/logging_config.py`, `services/error_handler.py`). Cette sentinelle rend la liste des portes exhaustive par construction.

### 4.5 Le journal des validations (constat P1)

**Ce que dit le code aujourd'hui.** `empreinte_action` n'est appelée qu'à un endroit (`routers/chat.py:3140`). Son résultat ne sert qu'au `set` local `empreintes_en_attente` (`:3078`, `:3141`, `:3159`), qui disparaît avec le tour. Les deux journaux voisins n'écrivent que les clés triées des arguments (`:3133-3138`) ou le nom de l'outil (`:3142-3145`). Le code actuel n'écrit donc jamais l'empreinte.

**Ce que la V1 proposait, et pourquoi c'était faux.** La V1 voulait écrire « l'empreinte de l'action (`empreinte_action`) » au journal. Or cette fonction rend destinataires, copie, objet et corps en clair (`services/tool_confirmations.py:181-189`). Le constat de la revue est fondé : la V2 l'accepte sans réserve.

**Ce que la V2 écrit.** Deux nouvelles valeurs d'`AuditAction` (`tool_confirmed`, `tool_refused`), écrites par `confirm_tool` :

- à la validation, **avant** l'exécution (la trace existe même si l'exécution échoue) ;
- au refus, avant le `return` de `routers/chat.py:3529-3530` ;
- rien quand l'action est introuvable (`:3523-3526`).

Colonnes : `action`, `resource_type = "validation"`, `resource_id` = identifiant de conversation (ou vide), `details` = `{"outil": nom, "origine": "chat", "condensat": hex}`. Ni `ip_address` ni `user_agent`.

**Le condensat.** `HMAC-SHA256(clé, message)` :

- la clé est dérivée de la clé maîtresse par HKDF avec `info = b"therese-journal-validations-v1"`, sur le modèle exact de `derive_db_key_from_master` (`services/encryption.py:470-485`). Aucun nouveau secret à ranger : la clé suit le cycle de vie de la clé maîtresse et n'est jamais écrite en base ;
- le message est le JSON canonique (clés triées, séparateurs fixes) de `{"outil": nom, "arguments": arguments}`, **après** `canoniser_arguments` et **sans** les clés privées ajoutées pour la carte, `_confirmation_destination`, `_compte_ecran` et `_agenda_ecran` (`routers/chat.py:3116-3130`).

La clé HMAC tient le rôle du sel de la décision 10 (« empreinte salée ») : sans elle, le condensat ne se recalcule pas, et le test « différent du SHA-256 non salé » en apporte la preuve. Le condensat permet de dire « cette même action a été validée deux fois » sans rien garder de son contenu. Il ne se calcule qu'avec la clé maîtresse, qui déchiffre déjà la base : il n'ouvre aucune porte nouvelle.

**Une fonction nouvelle, jamais `empreinte_action`.** Le condensat vit dans une fonction à part, `condensat_pour_journal`. `empreinte_action` garde son rôle de déduplication en mémoire ; une sentinelle AST vérifie que son résultat n'atteint jamais un appel `logger.*`, `log_activity`, `AuditService.log` ni un argument `details=`.

**Conservation.** 12 mois (décision 10). Une méthode nouvelle, `purger_les_validations(jours=365)`, ne supprime que les actions de validation (y compris celles du lot 6) ; elle travaille sur sa propre session comme `cleanup_old_logs` (`services/audit.py:237-242`). Elle tourne au démarrage puis toutes les 24 heures, dans la boucle quotidienne existante de la purge RGPD (`main.py:369-383`), sans nouvelle tâche de fond. **`cleanup_old_logs` n'est pas appelée** : elle effacerait tout le journal.

**Purge totale.** `_supprimer_toutes_les_donnees` supprime les lignes de validation (`delete(ActivityLog).where(ActivityLog.action.in_(...))`) avant son commit (`routers/data.py:700`). La ligne `data_deleted_all` écrite juste avant (`:636-641`) et le reste du journal suivent la règle actuelle, sur laquelle une question est posée (§11).

**Export et écran.** Les lignes partent dans l'export RGPD sans changement (`routers/data.py:410-420`). La liste des catégories de `GET /api/data/logs/actions` gagne « validations » (`routers/data.py:884-903`).

### 4.6 Les confirmations des écrans

Le serveur ne voit pas ces confirmations : l'écran demande, puis appelle lui-même la route métier. Deux changements :

1. **Le crochet devient fail-closed.** Sans fournisseur, `useExternalActionConfirmation` n'exécute plus l'action (`components/app/useExternalActionConfirmation.ts:32`), la signale en console et affiche « Action bloquée : la confirmation est indisponible ». Motif : l'exécution directe servait le mode classique (commentaire `:21`) ; `App.tsx` ne monte plus que `ConversationCanvasPrototype`, sous le fournisseur (`App.tsx:248-250`). Un écran rendu un jour hors du fournisseur doit échouer visiblement plutôt qu'agir sans demander.
2. **Une trace déclarée.** Le fournisseur (`components/app/ExternalActionConfirmation.tsx:24-84`) envoie `POST /api/confiance/validations-ecran` avec `{nature, decision}` seulement, à la confirmation (avant `action.run()`) et à l'abandon (Annuler ou Échap). `nature` appartient à une liste fermée, tirée des sept appels existants :

| Appel | Nature |
|---|---|
| `components/email/EmailCompose.tsx:93` | `email_envoye` |
| `components/email/EmailList.tsx:278`, `components/email/EmailDetail.tsx:143` | `email_corbeille` |
| `components/calendar/EventForm.tsx:206` | `evenement_cree`, `evenement_modifie` |
| `components/invoices/InvoiceForm.tsx:464` | `piece_changement_statut` |
| `components/invoices/InvoiceForm.tsx:492` | `facture_payee` |
| `components/invoices/InvoiceForm.tsx:520` | `devis_accepte`, `devis_refuse` |

`ExternalActionPreview` gagne un champ `nature` typé par cette union : TypeScript refuse un appel qui l'oublie. Le modèle Pydantic de la route interdit tout champ supplémentaire (`extra="forbid"`) : le titre, la description et les détails de l'aperçu, qui portent le contenu, ne quittent jamais l'écran. Actions écrites : `screen_action_confirmed` et `screen_action_refused`, avec `details = {"nature": ..., "origine": "ecran", "declaree": true}`. Même conservation et même purge qu'au §4.5. Un échec de la trace ne bloque jamais l'action.

### 4.7 Le pont des agents OpenClaw

- **Au registre** : une entrée `chemin.pont_openclaw`, domaines multiples (mémoire, e-mails, factures, tâches, agenda), sortie `openclaw`, interrupteur `pont_agents`.
- **L'interrupteur** (préférence `pont_agents_actif`, défaut : actif, pour ne rien retirer sans geste à ceux qui l'utilisent) : coupé, `dispatch_to_openclaw` lance la session **sans** `therese-bridge` (`routers/agents.py:1367-1378`), et l'écran de l'Atelier le dit (« l'agent travaillera sans accès à tes données »).
- **Un jeton de pont.** Sans lui, aucun réglage ne s'applique au pont, puisque ses appels portent le jeton de l'interface. À chaque envoi vers OpenClaw, un jeton aléatoire est créé en mémoire et passé en `THERESE_MCP_TOKEN` à la place du jeton de session. Le middleware d'authentification (`main.py:738-796`) l'accepte uniquement :
  - en `GET` ;
  - sur les gabarits de `TOOL_ROUTES` filtrés (`services/mcp_therese_server.py:259-279`), comparés segment par segment (`[^/]+` par paramètre), jamais par préfixe ;
  - si l'interrupteur du pont est actif et si le domaine de la route n'est pas retiré, relus **à chaque requête**.

  Le jeton est révoqué à l'annulation de la session (`routers/agents.py:1557`), à l'arrêt de l'application, et au plus tard 12 heures après sa création.

C'est un changement d'authentification. Il a son propre lot, ses tests de refus et sa revue adverse.

### 4.8 Retirer un domaine, partout

Les agents d'action nomment déjà leurs sources par domaine (`email`, `calendar`, `crm`, `tasks`, `invoices`, `web_search` dans `agents/action_agents.json`, lus par `_gather_local_context`, `services/action_agents.py:253-505`). La V2 reprend ce découpage :

| Domaine | Conversation | Contexte injecté | Agents d'action | Pont OpenClaw |
|---|---|---|---|---|
| Mémoire (contacts, projets) | `read_contact`, `create_contact`, `create_project` | mémoire injectée (`routers/chat.py:1737`, `:2370`) | `crm` | `list_contacts`, `get_contact`, `search_memory`, `get_project` |
| E-mails | `read_emails`, `summarize_emails`, `search_emails`, `send_email` | aucun | `email` | `list_emails` |
| Agenda | `list_calendar_events`, `create_calendar_event` | aucun | `calendar` | `list_events` |
| Factures et devis | `search_invoices`, `invoice_totals` | aucun | `invoices` | `list_invoices` |
| Tâches | aucun | aucun | `tasks` | `list_tasks` |
| Fichiers indexés | `search_files`, `read_file` | aucun | aucun | aucun |

**Alignement avec P-106.** La V2 de P-106 retire aussi `search_files` et `read_file` de la liste quand le service est en ligne et que l'accord « documents » manque (sa §5.1). Les deux filtres ne font que restreindre et se composent : un outil n'est offert que s'il passe les deux. La ligne du registre pour ces deux outils porte les deux conditions, l'accord étant résolu côté écran comme la dictée.

Restent hors domaine, gouvernés par leurs réglages actuels : `web_search` et `browser_navigate` (interrupteur de recherche web, `routers/chat.py:2527`), `generate_document` (sous carte), les pièces jointes (geste explicite de l'utilisateur).

**Points d'application**, tous côté serveur :

1. la liste d'outils du chat, filtrée avant `routers/chat.py:2533` (le bloc des capacités suit, `:2540-2580`) ;
2. l'injection de mémoire, sautée quand « Mémoire » est retirée ;
3. `confirm_tool` et la boucle d'outils refusent un outil d'un domaine retiré, pour couvrir la carte posée avant le retrait ;
4. `_gather_local_context` retire le domaine et l'écrit dans le contexte (« accès retiré dans les réglages : ne rien inventer à ce sujet »), sur le modèle de la ligne web (`services/action_agents.py:520-524`) ;
5. le middleware, pour le jeton de pont (§4.7).

Le réglage (préférence `domaines_retires`) est mis en cache comme l'interrupteur web (`services/web_search.py:72-122`). Une préférence illisible au démarrage retire tous les domaines et l'écrit au journal : même doctrine que la recherche web (`:117-122`).

**Ce que dit l'écran** : « Retirer un domaine le retire de la conversation, des agents d'action et des agents OpenClaw. Tes écrans (Courrier, Agenda, Factures) restent à toi. » L'Atelier « Améliorer THÉRÈSE » ne lit aucun de ces domaines (ses outils portent sur le code, `services/agents/tools.py:589`, `:631`, et le web, `:920`) : l'écran le dit aussi.

### 4.9 La vue

- **Le tableau qui fait foi** vit dans Paramètres > Confidentialité, section « Ce que THÉRÈSE peut faire » : un vrai `<table>` avec légende, cinq en-têtes de colonne et une ligne par entrée, groupé par type. Le Centre de confiance fait 360 px de large (`components/prototype/CapabilityCenter.tsx:564`) : il n'y tiendrait pas.
- **Le Centre de confiance se greffe sur P-118** : la ligne d'état (`:579-585`) reste, avec la phrase que P-106 y ajoute sur les fichiers indexés (V2 de P-106, §5.1) ; la ligne « Ce qui sort de ta machine » (`:589`) devient une liste dérivée de la route (« Sans te demander : Décision cherche sur le web avec DuckDuckGo », « Agents OpenClaw : accès à tes données actif »), suivie d'un bouton « Tout voir » qui ouvre Confidentialité (`onOpenPrivacy`, `:595`).
- **Aucun libellé de périmètre écrit en dur** dans les composants : tout vient de la route.

### 4.10 L'export

**P-107 porte seul la production du BPMN.** La V2 de P-106 (`docs/plans/2026-09-26-rfc-p106-formats-structures-v2.md`) lit les fichiers BPMN mais n'en écrit aucun, « ni dans cette RFC ni plus tard sans une RFC dédiée » (§5.4, l.142), et renvoie explicitement à P-107 (§5.5, l.154). Cette RFC est la RFC dédiée, pour un seul usage : l'export du registre. Elle ne fournit pas d'écrivain BPMN général.

Deux exports locaux du registre résolu, enregistrés par la boîte d'enregistrement native comme l'export RGPD (`services/api/data.ts:64-73`) :

- **Mermaid** (`flowchart LR`, un `subgraph` par couloir), lisible en texte et affichable dans beaucoup d'outils. Il sort en premier (lot 7a), parce qu'il ne demande aucune mise en page.
- **BPMN 2.0 avec diagramme** (`bpmndi`, lot 7b). La structure est régulière, la mise en page aussi : trois couloirs (Toi, THÉRÈSE, Services extérieurs) ; une colonne par entrée ; pour une validation « avant », une tâche utilisateur « Valider : … », une passerelle « validé ? », puis la tâche de service ; sinon la tâche de service seule. Positions calculées sur une grille fixe (hauteur de couloir, largeur de colonne), sans algorithme de placement. Écriture par `xml.etree.ElementTree` de la bibliothèque standard, sans `DOCTYPE` (le lecteur de P-106 refuse tout fichier qui en déclare un, §5.2, l.86) ; aucune lecture de fichier extérieur, donc aucune surface d'entités XML.

**Chiffrage** : lot 7a, une à deux heures ; lot 7b, une demi-journée à une journée en TDD, recette dans deux modeleurs comprise. Si le 7b dépasse ce budget, on s'arrête au Mermaid et on le dit à Dr_logic.

**Oracle de test** : quand le lot 3 de P-106 (extracteur `.bpmn`) est livré, il relit l'export de P-107 et doit retrouver chaque couloir, chaque étape et chaque flux. Avant cela, la relecture se fait par `ElementTree`.

L'écran ne dessine pas le BPMN : le tableau texte reste la vue accessible, le BPMN une vue dérivée pour le discours et l'audit.

### 4.11 Hors périmètre

- Assouplir le portillon (question 4, tranchée non).
- Retrait par projet (question 5, tranchée non).
- Un bac à sable contre un processus local malveillant : le jeton de session reste lisible dans `~/.therese/.session_token` par tout processus de l'utilisateur (`main.py:694-695`). Le jeton de pont rend les réglages applicables au chemin prévu ; il ne transforme pas OpenClaw en processus confiné (§8).

## 5. Inventaire des chemins, relevé dans le code

Relevé par l'AST (appels aux portes de §4.4, fonction englobante) puis complété à la main pour `generate_content` et les services branchés. Cet inventaire devient le contenu initial du registre ; la sentinelle 3 le tient exhaustif.

| Chemin | Points d'appel | Validation | Sorties | Interrupteur |
|---|---|---|---|---|
| Conversation | `routers/chat.py:1854` (`send_message`) ; outils `:3197`, `:3325` ; confirmation `:3557`, `:3564` | par outil, calculée | `fournisseur_ia`, puis selon l'outil | par domaine |
| Extraction d'entités | `routers/chat.py:975`, `services/entity_extractor.py:135` | automatique | `fournisseur_ia` | Extraction automatique (`routers/chat.py:964-968`) |
| Recherche approfondie | `routers/chat.py:1147`, `services/deep_research.py:92`, `:117`, `:212`, `:298` | démarrée par toi | `fournisseur_ia`, `moteur_recherche` | Recherche web |
| Décision (Board) | `services/board.py:302`, `:520`, `:671`, `:953` | démarrée par toi | `mode_board`, `moteur_board` | Recherche web |
| Agents d'action | `services/action_agents.py:530`, `:834` | démarrés par toi | `fournisseur_ia`, `moteur_recherche` | par domaine, Recherche web |
| Améliorer THÉRÈSE (Atelier) | `services/agents/runtime.py:321`, `services/agents/tools.py:928` | démarré par toi, fusion après relecture | `fournisseur_ia`, `moteur_recherche` | Recherche web |
| Agents OpenClaw et pont | `routers/agents.py:1380`, `:1544`, `services/mcp_therese_server.py:401`, `:403` | démarrés par toi | `openclaw` | Pont des agents, par domaine |
| Atelier documentaire | `routers/documents.py:370`, `:501`, `:696` | démarré par toi | `fournisseur_ia` | aucun |
| Réponse proposée à un e-mail | `services/email_response_generator.py:211` | démarrée par toi | `fournisseur_ia` | E-mails |
| Résumé de mails | `services/workspace_tools.py:1405` | lecture, sans carte | `fournisseur_ia` | E-mails |
| Compétences | `routers/skills.py:161`, `:223` | démarrées par toi | `fournisseur_ia` | aucun |
| Génération de commande | `routers/commands_v3.py:159` | démarrée par toi | `fournisseur_ia` | aucun |
| Appel direct d'un connecteur | `routers/mcp.py:250`, `:253`, `:265` | aucune carte ; aucun appelant dans l'interface (`callMCPTool`, `services/api/mcp.ts:139`, n'est importé par aucun composant) | `connecteur` | Connecteur coupé |
| Envoi de mail depuis l'écran | `routers/email.py:1336`, `:1348` | carte d'écran (§4.6) | `compte_mail` | aucun |
| Dictée | `routers/voice.py:55`, `:96` | démarrée par toi | `dictee` | accord « voice » |
| Images | `routers/images.py:80`, `:153` | démarrées par toi | `images` | aucun |
| Synchro CRM Google Sheets | `routers/crm.py:918-1156`, `services/sheets_service.py` | démarrée par toi | Google Sheets | aucun |

## 6. Lots, livrables un par un

Chaque lot suit la même chaîne : tests écrits d'abord et vus rouges, code, sabotage ciblé par fonction (règle du 27/08 : découper le source entre deux `def`, jamais un remplacement de chaîne globale), revue adverse du diff, recette dans l'application lancée.

### Lot 1 : le journal des validations (moteur, données)

Livre §4.5. Aucune migration.

Tests à écrire en premier :

- **marqueur** : un marqueur unique glissé dans `to`, `cc`, `subject` et les quatre alias de corps (`_ALIAS_CORPS`, `services/tool_confirmations.py:130`) d'un `send_email`, dans les arguments d'un outil MCP (`slack__post_message`) et dans le contenu d'un `generate_document`. Chaque action est validée puis, dans un second passage, refusée. Le marqueur n'apparaît dans aucune colonne d'aucune ligne d'`ActivityLog` (`services/audit.py:68-75`, `details` compris), ni dans la réponse de `GET /api/data/logs` (`routers/data.py:824`), ni dans l'export assemblé (`routers/data.py:410-420`), ni dans `caplog` ;
- une validation écrit une ligne `tool_confirmed`, un refus une ligne `tool_refused`, un identifiant inconnu aucune ;
- **condensat** : stable pour une même action ; différent si le corps change ; insensible aux trois clés privées ; différent du SHA-256 non salé des mêmes arguments ;
- **conservation** : une validation de 366 jours est supprimée par la tâche quotidienne, une de 364 jours reste, et une ligne `contact_created` de 400 jours **reste** (le reste du journal n'est pas touché) ;
- **purge** : après `DELETE /api/data/all?confirm=true`, plus aucune ligne de validation, et la ligne `data_deleted_all` est présente ;
- **sentinelle** : le résultat d'`empreinte_action` n'atteint ni `logger.*` ni un journal.

Critères observables : valider une carte d'envoi puis ouvrir le journal montre « Validé : send_email » et un condensat, sans rien du message.

Sabotage : remplacer le condensat par `json.dumps(arguments)` doit rendre le test du marqueur rouge.

### Lot 2 : le registre, les résolveurs et la route (moteur)

Livre §4.2 à §4.4 et l'inventaire du §5. Route `GET /api/confiance/registre` (nouveau routeur `routers/confiance.py` ; le préfixe est libre aujourd'hui).

Tests à écrire en premier :

- les quatre sentinelles du §4.4, chacune vue rouge sur un cas fabriqué (outil ajouté sans entrée, fonction qui appelle `generate_content` sans être déclarée, module qui importe `httpx` sans être classé) ;
- **validation calculée** : pour chaque outil, la valeur rendue par la route égale `requires_confirmation(nom)` ; un outil MCP inconnu apparaît « Te demande avant » ;
- **un test par résolveur et par configuration** (tableau paramétré) : Ollama local, Ollama `:cloud`, Mistral, aucun service ; recherche coupée, Brave, DuckDuckGo, Gemini ; agenda local, Google, CalDAV ; aucune boîte, Gmail, IMAP ; connecteur en marche, coupé ;
- **aucun secret** : une clé d'API configurée, un mot de passe IMAP et un jeton OAuth fabriqués n'apparaissent pas dans la réponse ;
- **interrupteur** : couper la recherche web change la ligne du Board dans la réponse.

Critères observables : `GET /api/confiance/registre` sur une installation réelle rend autant de lignes que le §5 plus les outils et les connecteurs installés, et les sorties décrivent la configuration du moment.

### Lot 3 : la vue (écran)

Livre §4.9.

Tests vitest à écrire en premier :

- `getByRole('table', { name: 'Ce que THÉRÈSE peut faire' })`, cinq `columnheader`, une ligne par entrée de la réponse simulée ;
- la même réponse simulée avec la recherche coupée fait changer la ligne du Board : preuve qu'aucun libellé n'est écrit en dur ;
- le Centre de confiance garde la ligne d'état P-118 et remplace le texte fixe de `:589` par la liste dérivée ; « Tout voir » ouvre Confidentialité ;
- lecture échouée : le tableau dit « Impossible de lire le registre » au lieu d'une liste vide (doctrine B-051).

Critères observables : recette par ligne, chaque ligne confrontée à un geste réel dans l'application (une carte pour les outils sous carte, une recherche du Board avec l'interrupteur coupé puis rallumé).

### Lot 4 : le pont des agents (moteur, écran)

Livre §4.7. Dépend du lot 2 pour l'entrée du registre.

Tests à écrire en premier :

- avec le jeton de pont : `GET /api/email/messages` passe ; `POST /api/email/send`, `GET /api/config/llm` et `GET /api/data/export` renvoient 403 ; `GET /api/memory/contacts/..%2F..%2Fconfig%2Fllm/fiche` renvoie 403 ;
- interrupteur coupé : toute route renvoie 403 au jeton de pont, et `dispatch_to_openclaw` construit une configuration sans `therese-bridge` ;
- jeton révoqué après annulation, puis après 12 heures (horloge simulée) ;
- le jeton de session garde exactement son comportement (suite existante verte).

Critères observables : une mission OpenClaw lancée pont coupé répond qu'elle n'a pas accès aux contacts.

### Lot 5 : le retrait par domaine (moteur, écran)

Livre §4.8. Dépend du lot 4 pour le pont.

Tests à écrire en premier :

- **sentinelle** : chaque outil de `CLASSIFICATION_DES_OUTILS`, chaque outil du pont et chaque `tools` d'`agents/action_agents.json` appartient à un domaine ou à la liste « hors domaine » ;
- domaine E-mails retiré : les quatre outils disparaissent de la liste transmise **et** du bloc des capacités (sur le modèle de `tests/test_chat_capacites_annoncees.py`) ; une carte `send_email` posée avant le retrait est refusée à la confirmation ; l'agent « relance-clients » reçoit la ligne « accès retiré » ; le jeton de pont reçoit 403 sur `/api/email/messages` ;
- domaine Mémoire retiré : aucune mémoire injectée dans le prompt système ;
- préférence illisible : tous les domaines retirés et un avertissement au journal.

Tests vitest : un interrupteur par domaine, nommé ; la phrase « Tes écrans restent à toi » est présente.

Critères observables : retirer E-mails puis demander « lis mes mails » ; l'assistante répond que l'accès est retiré dans les réglages.

### Lot 6 : les confirmations des écrans (écran, moteur)

Livre §4.6. Dépend du lot 1.

Tests à écrire en premier :

- vitest : le crochet monté sans fournisseur n'appelle pas l'action ; le fournisseur envoie `{nature, decision}` et rien d'autre (corps de requête inspecté) à la confirmation et à l'abandon ;
- pytest : `POST /api/confiance/validations-ecran` refuse une nature hors liste (422) et un champ supplémentaire (422) ; écrit une ligne `screen_action_confirmed` sans contenu ; la purge et la conservation du lot 1 la couvrent.

Critères observables : envoyer un e-mail depuis le Courrier puis ouvrir le journal montre « Confirmé à l'écran : email_envoye (déclaré par l'interface) ».

### Lot 7 : l'export (moteur, écran)

Livre §4.10. Dépend du lot 2. Ne dépend pas de P-106, qui ne fournit aucun écrivain BPMN.

**Lot 7a, Mermaid.** Tests à écrire en premier :

- un couloir par `subgraph`, une entrée par nœud, les validations « avant » représentées par un nœud de décision ;
- les noms contenant `"`, `[`, `]` ou un retour à la ligne sont échappés ;
- un même registre produit un texte identique.

**Lot 7b, BPMN.** Tests à écrire en premier :

- chaque nœud de flux a exactement un `BPMNShape`, chaque flux de séquence un `BPMNEdge` ; chaque forme tient dans son couloir ; aucune forme n'en chevauche une autre ; les identifiants sont uniques ;
- un même registre produit un fichier identique octet pour octet ;
- une entrée « Te demande avant » produit une tâche utilisateur et une passerelle ; une entrée « Sans te demander » n'en produit aucune ;
- aucun `DOCTYPE` dans la sortie ;
- relecture par l'extracteur `.bpmn` du lot 3 de P-106 dès qu'il existe (couloirs, étapes et flux retrouvés), par `ElementTree` avant.

Critère observable, à vérifier en recette : le fichier s'ouvre et s'affiche dans demo.bpmn.io et dans Camunda Modeler.

## 7. Données et migrations

- **Aucune révision Alembic.** La tête reste `b8c9d0e1f2a3` (`models/database.py:619`) et la preuve d'estampillage (`:688-761`) n'est pas touchée : les validations sont de nouvelles valeurs dans `activity_logs.action` et dans le JSON de `details` ; les réglages sont des lignes de `preferences` (`pont_agents_actif`, `domaines_retires`) ; le registre est un fichier embarqué.
- **Embarquement** : rien à ajouter, `backend.spec` embarque déjà tout le dossier `app/data` (`src/backend/backend.spec:100-101`). Un test lit le registre par le même chemin relatif au module que `services/capacites.py`.
- **Purge** : une ligne `delete()` ciblée dans `_supprimer_toutes_les_donnees` ; les préférences nouvelles partent déjà avec `delete(Preference)` (`routers/data.py:697`).
- **Export** : inchangé, les lignes nouvelles y figurent d'office.
- **Sauvegarde** : les préférences nouvelles voyagent avec la base, ce qui est voulu (un retrait suit l'utilisateur d'une restauration).

## 8. Risques restants

- **Validation déclarée pour les chemins de fond.** Aucun portillon n'existe hors du chat ; « démarré par toi » ou « automatique » y reste une déclaration, tenue par la recette du lot 3 et non par un calcul.
- **Ce qu'OpenClaw fait des données** échappe à THÉRÈSE : le modèle choisi dans OpenClaw n'est pas connu, la vue le dit.
- **Le jeton de pont n'est pas un bac à sable.** Un processus local qui lit `~/.therese/.session_token` a tout l'accès de l'interface ; le retrait gouverne le chemin prévu, pas un agent malveillant qui aurait un shell.
- **Le condensat est une corrélation, pas un secret.** Qui détient la clé maîtresse peut tester une hypothèse (« a-t-il envoyé tel texte à telle adresse ? ») ; il déchiffre déjà la base, donc rien de nouveau n'est exposé.
- **Cartes jamais tranchées** : une carte perdue au redémarrage (`services/tool_confirmations.py:10-12`) ne laisse aucune ligne. C'est cohérent avec « rien n'a eu lieu ».
- **Tâche quotidienne et purge** : la suppression des validations anciennes est idempotente ; si elle croise une purge ou une restauration, elle échoue proprement et recommence le lendemain. Elle entrera dans la « mise au repos » validée le 25/09 quand celle-ci existera.
- **Fatigue d'interface** (« trop d'interfaces », 27/08) : le tableau vit dans un onglet existant, et le Centre de confiance ne gagne qu'une liste courte et un bouton.

## 9. Réponse à la revue

| Gravité | Constat de la revue | Réponse | Où dans la V2 |
|---|---|---|---|
| P1 | `empreinte_action` contient le texte de l'e-mail ; la trace « sans contenu » l'écrirait en clair dans un journal gardé après la purge. | **Accepté.** Fondé sur `services/tool_confirmations.py:181-189`. Le code actuel n'écrit jamais l'empreinte (`routers/chat.py:3078`, `:3140-3159`), mais la V1 proposait de l'écrire : c'était faux. Le journal écrit un condensat HMAC dérivé par HKDF, sur des arguments sans clés privées ; une sentinelle interdit à `empreinte_action` d'atteindre un journal ; le test du marqueur commence par `send_email`, ses quatre alias de corps, `cc` et `subject`. | §4.5, lot 1 |
| P2 | La rétention « alignée sur le nettoyage des journaux » est inopérante : ce nettoyage ne tourne jamais. | **Accepté.** Tâche quotidienne dans la boucle RGPD existante (`main.py:369-383`), ciblée sur les seules validations, 12 mois ; effacement par la purge totale (décision 10). `cleanup_old_logs` n'est pas utilisée, car elle efface tout (`services/audit.py:218-247`). Le sort du reste du journal est posé à Ludo (§11). | §4.5, lot 1, §11 |
| P2 | La colonne « données qui sortent » est déclarée à la main alors qu'elle dépend de la configuration. | **Accepté.** Résolveurs calculés à la lecture (fournisseur et modèle, type d'agenda, compte mail, moteur, connecteurs), un test par combinaison ; décision 11. | §4.3, lot 2 |
| P3 | L'inventaire oublie le pont MCP ; aucune sentinelle ne couvre les chemins de fond. | **Accepté.** Le pont entre au registre avec interrupteur (décision 12) et jeton propre ; deux sentinelles (portes de sortie, modules réseau) rendent l'inventaire exhaustif ; l'inventaire du §5 ajoute dix chemins que ni la V1 ni la revue n'avaient relevés (atelier documentaire, réponse proposée à un e-mail, résumé de mails, compétences, génération de commande, appel direct d'un connecteur, envoi depuis l'écran, dictée, images, synchro Google Sheets). | §4.4, §4.7, §5, lots 2 et 4 |
| P3 | P-118 est livré : la ligne s'appelle « Ce qui sort de ta machine » et lit déjà le service et la recherche. | **Accepté.** Greffe sur `phrasesDeLEtat` et la ligne d'état (`components/prototype/CapabilityCenter.tsx:491-516`, `:579-585`) ; seule la ligne fixe de `:589` est remplacée. | §4.9, lot 3 |
| P3 | Les quatre régimes mélangent l'effet et la validation. | **Accepté.** Deux colonnes : effet déclaré, validation calculée ; le vocabulaire BPMN reste dans l'export. | §2 (question 1), §4.1 |
| P3 | Le lot 2 compte sur un écrivain BPMN que P-106 ne prévoit pas ; un BPMN sans diagramme ne s'affiche pas. | **Accepté.** P-107 porte seul l'écrivain, pour le seul export du registre (la V2 de P-106 exclut toute écriture BPMN, §5.4) : Mermaid d'abord (lot 7a), puis BPMN avec `bpmndi` sur une grille fixe (lot 7b), chiffré à une demi-journée ou une journée ; le lecteur BPMN de P-106 sert d'oracle de test. L'affichage dans les modeleurs reste à vérifier en recette. | §4.10, lots 7a et 7b |
| P3 | Tracer les confirmations des écrans suppose une route ; sans fournisseur, le crochet exécute sans demander. | **Accepté.** Route `POST /api/confiance/validations-ecran`, liste fermée de natures, trace marquée « déclarée » ; crochet fail-closed. | §4.6, lot 6 |
| P3 | « Retirer un outil » ne touche que la liste du chat. | **Accepté.** Retrait par domaine appliqué à la conversation, au contexte mémoire, aux confirmations, aux agents d'action et au pont ; l'écran dit ce qui reste à l'utilisateur (décision 13). | §4.8, lot 5 |
| P3 | Le BPMN est purement visuel ; la vue qui fait foi doit être un tableau texte. | **Accepté.** Tableau `<table>` avec légende et en-têtes dans Confidentialité, test vitest par rôle. | §4.9, lot 3 |

## 10. Livraison

Ordre : lot 1, lot 2, lot 3, lot 4, lot 5, lot 6, lot 7a, lot 7b. Les lots 1 et 2 ne dépendent de rien ; le lot 3 dépend du 2 ; le 5 du 4 ; le 6 du 1 ; les 7a et 7b du 2, et d'aucun lot de P-106. Revue adverse du design de ce document avant le lot 1, puis revue du diff à chaque lot. Aucune release sans le GO de Ludo.

## 11. Questions réservées à Ludo

1. **Le reste du journal d'activité** (création, modification et suppression de fiches, clés d'API, exports) est aujourd'hui gardé sans limite et survit à « Effacer toutes mes données » (`routers/data.py:698`). Faut-il lui appliquer la même règle que les validations, c'est-à-dire l'effacer après 12 mois et à la purge totale ? C'est une suppression définitive de données sur la machine des utilisateurs. **Recommandation** : oui, 12 mois et effacé par la purge, sauf la ligne qui date la purge elle-même (date seule, sans détail). Rien dans une application locale mono-utilisateur n'impose de garder ce journal, et « toutes mes données » doit être vrai.
2. **Montrer l'export BPMN dans la communication publique** (page d'accueil, Discord) relève de la marque. **Recommandation** : attendre la recette du lot 7 et le retour de Dr_logic avant d'en parler publiquement.

## Annexe : appuis dans le code

- Origine : `.app-loop/proposals.json`, P-107.
- Portillon : `services/tool_confirmations.py:33-49` ; mise en attente `routers/chat.py:3106-3183` ; confirmation `:3514-3598`.
- Classement : `services/contexte_execution.py:30-59`.
- Journal : `services/audit.py:19-75`, `:136-138`, `:218-247` ; routes `routers/data.py:824-925` ; purge `:632-700`.
- Planificateurs : `main.py:341-383`. Middleware d'authentification : `main.py:738-796`.
- Pont : `routers/agents.py:1322-1400` ; `services/mcp_therese_server.py:242-279`, `:321-403`.
- Agents d'action : `services/action_agents.py:253-535` ; `agents/action_agents.json`.
- Centre de confiance : `components/prototype/CapabilityCenter.tsx:491-601`.
- Confirmations des écrans : `components/app/useExternalActionConfirmation.ts:19-34`, `components/app/ExternalActionConfirmation.tsx:24-84`, `App.tsx:248-259`.
- Dérivation de clé : `services/encryption.py:470-485`.
- Manifeste de capacités, modèle du registre : `services/capacites.py`, `data/capacites.json` (17 capacités).
