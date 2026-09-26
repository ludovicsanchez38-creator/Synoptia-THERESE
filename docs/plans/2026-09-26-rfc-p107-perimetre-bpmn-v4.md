# RFC P-107, version 4 : un périmètre d'action visible et gouvernable

Rédigé le 26/09/2026. Remplace la V3 (`docs/plans/2026-09-26-rfc-p107-perimetre-bpmn-v3.md`), refusée (NO-GO sans P1) par la revue adverse du 26/09 (14 constats : deux P2, douze P3 ; rapport de travail `revue-v3-p107-p108.md` de l'orchestrateur, hors dépôt). Les décisions du 25/09/2026 (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md`, points 10 à 13) restent des faits. **C'est la dernière version avant l'implémentation** : il n'y aura pas de nouvelle revue de ce document, chaque lot aura sa revue de conception au moment du code, puis la revue de son diff. Le document se lit donc seul : ce que la V2 et la V3 faisaient bien y est repris en clair, sans renvoi.

**Base de vérification.** Toutes les lignes citées ont été relues à `d0f7ab26` (HEAD du 26/09/2026, 04 h 16), dans un arbre extrait par `git archive`, jamais dans l'arbre de travail. Quarante-sept commits séparent cette base de celle de la V3 (`d80d4406`) ; ceux qui déplacent des lignes citées sont B-1489, B-1494, B-1502 (`routers/chat.py`), B-1528 et B-1531 (`services/llm.py`, sept rangs au-delà de la ligne 500), B-1497, B-1498, B-1504, B-1505, B-1507, B-1522 à B-1524 et B-1536 (`routers/data.py`), P-132 et B-1535 (`routers/skills.py`, `services/skills/text_skills.py`, `services/memory_tools.py`, `services/action_agents.py`, `models/database.py`). Aucun numéro n'est recopié de la V3. Chemins relatifs à `src/backend/app/` (fichiers `.py`) et à `src/frontend/src/` (fichiers `.ts` et `.tsx`) ; `tests/`, `docs/`, `.github/` et `SECURITY.md` partent de la racine du dépôt.

**Prérequis fermés au code, cités et jamais recodés ici :**

- **B-1484** (`ad455ddb`) : le Board cherche avec le moteur choisi (`services/board.py:278`).
- **B-1489** (`d15ef8bd`) : un outil absent de la liste offerte au tour n'est pas exécuté.
- **B-1495** (`d80d4406`) : `include_memory=false` n'injecte aucune mémoire (`routers/chat.py:1740`, `:2398`).
- **B-1496** (`5f492b30`) : `search_memory` du pont appelle `POST /api/memory/search` (`services/mcp_therese_server.py:276`), sous `tests/test_b1496_pont_mcp_routes_existantes.py`.
- **B-1505** (`a3c98b74`) : la purge remet l'interrupteur web en phase avec la base (`routers/data.py:712-716`, `tests/test_b1505_interrupteur_web_apres_purge.py`). La V4 change la valeur que la purge laisse (§4.8.6), pas l'alignement du cache.
- **B-1522** (`eb820c50`) : après une restauration, l'interrupteur web suit la base restaurée (`routers/data.py:1797-1806`, `tests/test_b1522_interrupteur_web_apres_restauration.py`). C'est la moitié « restauration » du constat 12 ; l'autre moitié est au lot 5.

**Prérequis écrits dans une autre RFC**, au design et pas encore au code : P-106 V4 (`docs/plans/2026-09-26-rfc-p106-formats-structures-v4.md`, commitée en `dae1be67`), §6.1 points 1 à 7 et son lot 1, crée `chaine_de_repli()`, `config_du_tour()`, `destination_d_accord()`, le champ `documents_accordes_pour` et `types_de_memoire_permis(documents_permis, domaines_retires=())`. P-107 s'y branche et ne recrée rien.

## 0. Constats de la revue V3 et leur traitement

« Fermé au code » : un commit est sur main et un test nommé le prouve à la base relue. « Design, lot N » : la réponse est écrite ici, et son test est à écrire en premier au lot N.

| # | Gravité | Constat | Traitement | Où | Fermé au code, ou design |
|---|---|---|---|---|---|
| 1 | P2 | Retirer « Factures » laisse les pièces partir chez les agents d'action par la source `crm` | **Accepté.** Relu : la source `crm` joint à chaque contact ses cinq dernières pièces (`services/action_agents.py:296-299`, `:328-342`, `:368-373`) ; trois agents ont `crm` sans `invoices` (`rapport-hebdo`, `prep-rdv`, `onboarding-client`, `agents/action_agents.json`). Le bloc des pièces de la source `crm` dépend désormais du domaine Factures, et sa place dit « pièces retirées dans les réglages » | §4.8.1, §4.8.5 | design, lot 5 (`test_rapport_hebdo_sans_numero_de_piece_quand_factures_retirees`) |
| 2 | P2 | La fonction unique des types de mémoire et l'extraction de la chaîne n'existent que dans P-107 | **Fermé au design par P-106 V4** (`dae1be67`, §6.1 points 1 et 7, lot 1) : `types_de_memoire_permis(documents_permis, domaines_retires=())`, table des quatre types, liste blanche jamais `None` ni vide, sentinelle sur les **six** sites d'écriture (`routers/memory.py:252`, `:281`, `services/indexation.py:167`, `services/memory_tools.py:699`, `:866`, `services/user_profile.py:450`) ; `chaine_de_repli()` extraite. P-107 n'y ajoute que sa condition | §4.3, §4.8.2 | design, lot 1 de P-106 ; branchement au lot 5 |
| 3 | P3 | Lignes à `d80d4406` ; relevé sur l'interrupteur web périmé | **Accepté.** Tout est rebasé à `d0f7ab26` ; le relevé disparaît | tout | fermé au code : B-1505 (`a3c98b74`, `tests/test_b1505_interrupteur_web_apres_purge.py`) |
| 4 | P3 | « Après la purge, les domaines sont vides » est faux : les connecteurs survivent | **Accepté, tranché autrement que la V3.** Relu : la purge ne touche pas `mcp_servers.json` (`routers/data.py:775` ne vide que quatre dossiers). La purge garde désormais les **protections** (domaines retirés, pont coupé, recherche web coupée, mode cabinet) : elle efface tes données, elle ne rouvre rien que tu avais fermé. La note le dit | §4.8.6 | design, lot 5 (`test_purge_garde_les_protections`) |
| 5 | P3 | Trois confirmations d'écran échappent à la sentinelle | **Accepté.** Relu : `components/prototype/VoiceWorkspaceCanvas.tsx:111`, `components/board/BoardPanel.tsx:271`, `components/calendar/EventDetail.tsx:50` et `:59`. Natures ajoutées : `transcription_en_ligne`, `deliberation_cloud` pour le Board classique, `evenement_supprime` (agenda distant). La sentinelle ne cherche plus trois noms de setters : elle part des **portes d'écran**, les fonctions de `services/api` dont la route a un effet hors de la machine, et classe chaque fichier qui en appelle une (seize à la base) | §4.6 | design, lot 6 (`confirmationsEcran.sentinelle.test.ts`) |
| 6 | P3 | Le critère écrit contredit la table | **Accepté.** Un seul critère : une confirmation d'écran est tracée quand elle autorise un **effet hors de la machine**. Les quatre natures de facture (`components/invoices/InvoiceForm.tsx:480`, `:508`, `:536`) sont des écritures locales : elles sortent de la trace, et le crochet les confirme toujours | §4.6 | design, lot 6 |
| 7 | P3 | La réponse proposée joint jusqu'à trois messages du fil | **Accepté.** Relu : `routers/email.py:1893-1910`. Quand E-mails est retiré, le fil n'est pas joint ; la règle des gestes reste littérale (« cet objet, et rien d'autre ») | §4.8.3 | design, lot 5 (`test_email_retire_reponse_proposee_sans_le_fil`) |
| 8 | P3 | Le test vise `POST /api/email/send`, route inexistante | **Accepté.** Relu : l'envoi est `POST /api/email/messages` (`routers/email.py:1284-1285`), même chemin que `list_emails` en GET (`services/mcp_therese_server.py:265`) ; l'entrée `send_email → /api/email/send` (`:267`) est morte, filtrée par `MUTATING_TOOLS` (`:242-250`, `:279-281`) | §4.7 | design, lot 4 (`test_jeton_de_pont_refuse_l_envoi_par_la_meme_route`) |
| 9 | P3 | Un test fige une fuite | **Accepté.** Aucun test n'affirme que `/api/auth/token` rend le jeton ; la limite est consignée dans `SECURITY.md` et la phrase de l'écran est testée | §4.7 | design, lot 4 |
| 10 | P3 | État de la sentinelle 4 inexact | **Accepté.** Relu par analyse du source : `httpx` est importé par 18 modules au premier niveau et par 24 en comptant les imports dans les fonctions ; `sentence_transformers` (`services/embeddings.py:41-48`, `trust_remote_code=True`) et `faster_whisper` (`services/voice_local.py:176-182`, `download_root`) téléchargent. La sentinelle compte les imports dans les fonctions et classe ces deux bibliothèques « réseau » | §4.4 | design, lot 2 |
| 11 | P3 | La chaîne de repli est calculée de façon synchrone | **Accepté.** Relu : `_get_fallback_configs` lit les clés en base (`services/llm.py:784`) et interroge Ollama par un `httpx.get` de deux secondes (`:805` → `:337`). La route calcule la chaîne dans `asyncio.to_thread`. Point d'accroche pour P-106 : `config_du_tour()` ne parcourt les replis que si le principal est indisponible, comme aujourd'hui (`:825-826`) | §4.3 | design, lot 2 (`test_route_ne_bloque_pas_la_boucle_quand_ollama_est_injoignable`) |
| 12 | P3 | Les caches ne sont invalidés qu'à la purge | **Accepté.** Moitié web fermée par B-1522. Le reste : une fonction unique `resynchroniser_les_preferences_en_memoire()`, appelée par la purge, la restauration et le relais de P-108, qui relit dans la base tout ce que le processus garde en mémoire. En relisant, trois caches de plus ont le même défaut à HEAD (défauts ci-dessous) | §4.8.6 | fermé au code pour l'interrupteur web (`eb820c50`, `tests/test_b1522_interrupteur_web_apres_restauration.py`) ; design, lot 5 pour le reste |
| 13 | P3 | Le connecteur `filesystem` échappe à l'accord « documents » | **Accepté, et c'est la décision 8 elle-même** : un outil de lecture de fichier offert à un modèle en ligne exige cet accord. Les outils d'un connecteur qui déclare « Fichiers indexés » suivent la règle de `search_files` et `read_file` (P-106 V4, §6.1 point 6). Lot court, 2b, dès que P-106 lot 1 et P-107 lot 2 sont là | §4.8.4 | design, lot 2b |
| 14 | P3 | Question 3 posée mais lot 5 enchaîné ; directives inline oubliées | **Accepté.** Le lot 5 se livre par domaine sans attendre : le domaine est le seul découpage que les agents et le pont connaissent, et un retrait par outil, si Ludo le veut, s'y ajoute dans la conversation sans rien défaire. La question reste posée parce que la V4 réduit la décision 13 (§11). `[contact: …]` et `[rdv: …]` passent par le même exécuteur que `/contact` et `/rdv` (`routers/chat.py:1544`, `:1550`, `services/slash_commands.py:297`) et sont testés | §4.8.3, §11 | design, lot 5 (`test_agenda_retire_rdv_sans_carte`, paramétré) |

### Défauts du code actuel relevés en relisant, hors de toute RFC

Nouveaux, à reproduire puis à ficher :

- **Après une restauration, le profil, `THERESE.md` et le mode cabinet d'avant restent servis jusqu'au redémarrage.** Jumeaux de B-1522. La restauration remplace la table `preferences` et `THERESE.md` (élément couvert, `routers/data.py:1056`), puis n'oublie que les clés et l'interrupteur web (`:1795`, `:1797-1806`) : ni `set_cached_profile(None)` (`services/user_profile.py:691-694`), ni `reload_therese_md()` (`services/llm.py:285-290`), ni `poser_mode_cabinet` (`services/cloisonnement.py:31-34`, chargé une fois au démarrage, `main.py:121-141`). Effets : le prompt du chat (`services/llm.py:510`), le Board (`services/board.py:243`), la réponse proposée (`services/email_response_generator.py:152`) et **les PDF de facture** (`routers/invoices.py:856`, `:906`) gardent l'émetteur d'avant ; et une base restaurée en mode cabinet laisse remonter les souvenirs généraux dans une conversation de dossier (`services/cloisonnement.py:48`) jusqu'au redémarrage.
- **Après la purge, le mode cabinet reste en mémoire.** Jumeau de B-1505 : la purge efface la préférence (`routers/data.py:699`) sans toucher `poser_mode_cabinet`. Effet borné au redémarrage suivant, et restrictif ; la V4 garde de toute façon ce réglage à la purge (§4.8.6).
- **À reproduire : une image générée depuis les commandes de l'Accueil part sans l'accord « images ».** `components/home/CommandExecutor.tsx:293` appelle `generateImage` sans `hasCloudConsent('images', …)`, là où le canevas Images le demande au premier usage (`components/prototype/ImagesWorkspaceCanvas.tsx:246-251`). B-096 (`21958d1c`, décision de Ludo) a retiré la **confirmation** des deux côtés, pas l'accord, et son message affirmait que le canevas générait déjà sans confirmation, ce qui n'est plus vrai à HEAD. Le chemin est atteint par `components/chat/MessageList.tsx:209-214` (conversation vide), monté par `components/prototype/PrototypeChatSurface.tsx:78` : à confirmer dans l'application lancée avec une commande d'image à l'Accueil.

Déjà connus, cités et non traités ici : **B-1189** (bascule vers un autre service en ligne sans son accord), **B-1240** (la réponse proposée n'interroge pas les accords), et le relevé de la V3 sur `rotate_key`, toujours vrai à HEAD : la rotation change la clé maîtresse (`services/encryption.py:389`, `:415`, `:431`) sans rechiffrer la base, dont la clé en dérive (`:467`), et n'a aucun appelant hors des tests.

## 1. Ce que la V4 change

- **Les pièces sortent de la source `crm` des agents** quand Factures est retiré.
- **La purge garde tes protections**, et une seule fonction remet en phase la mémoire du processus après une purge, une restauration ou un relais.
- **Les confirmations d'écran ont un critère unique**, l'effet hors de la machine, et une sentinelle fondée sur les portes d'écran.
- **La réponse proposée n'emporte plus le fil** quand E-mails est retiré.
- **Le connecteur `filesystem` passe sous l'accord « documents »**, dans un lot court qui suit P-106.
- **La chaîne de repli est calculée hors de la boucle**, et ses règles viennent de P-106 V4.
- **Les tests sont nommés** (fichier et fonction), et le test qui figeait une fuite disparaît.

## 2. Décisions

Les décisions du 25/09 restent des faits : **10** journal des validations (outil, date, oui ou non, empreinte salée, jamais le contenu ; 12 mois ; effacé par « Effacer toutes mes données ») ; **11** ce qui sort, d'après la configuration réelle ; **12** le pont des agents au périmètre, avec un interrupteur ; **13** « retirer » vaut partout, et l'écran le dit.

Tranchées par la V2 et gardées : l'écran parle en mots simples (« Lit », « Prépare », « Enregistre », « Agit à l'extérieur » ; « Te demande avant », « Sans te demander ») et le vocabulaire BPMN ne vit que dans l'export ; trois questions (qui fait, qui valide, où partent les données) à la place d'un RACI ; les confirmations d'écran sont tracées ; l'inventaire ne sait que restreindre ; pas de retrait par projet.

Tranchées par cette V4, sur délégation (choix de conception avec recommandation) : le critère de trace des écrans (§4.6) ; la purge qui garde les protections (§4.8.6) ; le fil de la réponse proposée (§4.8.3) ; l'accord « documents » étendu au connecteur `filesystem` (§4.8.4, application directe de la décision 8) ; la livraison du retrait par domaine sans attendre la question 3, parce qu'un retrait par outil s'y ajouterait sans rien défaire. Seules les questions du §11 restent à Ludo.

## 3. Ce qui existe

**Points d'appui.** Trois classes d'effet par outil du chat (`services/contexte_execution.py:26-28`, table `:30`) ; un nom inconnu, MCP compris, est externe. Un portillon fail-closed : seule la lecture classée passe sans carte (`services/tool_confirmations.py:33`), les cartes vivent en mémoire (`:20`). La liste d'outils du chat est construite à `routers/chat.py:2533-2561` (connecteurs `:2544`, mémoire `:2547`, espace de travail `:2550`, web `:2555`, retrait des outils déjà en attente `:2561`) et le bloc des capacités se dérive d'elle outil par outil (`:2563-2568`). La confirmation d'une carte est `confirm_tool` (`:3558-3573` pour le refus, puis l'exécution `:3600-3623`). L'interrupteur web vit en cache (`services/web_search.py:72-97`), chaque service de recherche le lit avant de partir. Le pont OpenClaw est en lecture seule (`services/mcp_therese_server.py:242-281`) mais reçoit le jeton de session complet (`routers/agents.py:1367-1378`). Le journal d'activité écrit par savepoint (`services/audit.py:136`) et part dans l'export RGPD (`routers/data.py:412`). La ligne d'état de P-118 vit dans `phrasesDeLEtat` (`components/prototype/CapabilityCenter.tsx:500`, affichée `:584`) ; la ligne « Ce qui sort de ta machine » est un texte fixe (`:589`).

**Manques.** Aucune colonne « où partent les données ». Les validations ne laissent aucune trace (`confirm_tool` n'écrit rien, `AuditAction`, `services/audit.py:19`, n'a ni « validé » ni « refusé »). `cleanup_old_logs` (`services/audit.py:218`) n'a aucun appelant planifié et effacerait tout le journal. La purge garde tout le journal (`routers/data.py:700`) et le dit en des termes faux (« raisons légales », `:805`, `:810`). Le crochet des écrans exécute sans rien demander en l'absence de fournisseur (`components/app/useExternalActionConfirmation.ts:19-33`). L'identité d'un préréglage MCP se perd à l'installation : `install_preset` appelle `add_server` avec le seul nom (`routers/mcp.py:682-688`), qui tire un identifiant au hasard (`services/mcp_service.py:414`), et l'écran retrouve un préréglage installé par son nom mis en forme (`routers/mcp.py:529`).

## 4. Conception

### 4.1 Les colonnes de la vue

| Colonne | Source | Valeurs |
|---|---|---|
| Action | inventaire (déclaré) | nom en français |
| Ce qu'elle fait | inventaire, tenu par sentinelle | Lit, Prépare, Enregistre, Agit à l'extérieur |
| Qui valide | **calculé** par `requires_confirmation(nom)` pour un outil du chat ; déclaré pour un chemin | Te demande avant, Sans te demander (démarré par toi), Automatique |
| Où partent les données | **calculé** par un résolveur (§4.3) | Reste sur ta machine, ou le service nommé |
| Ce qui le coupe | inventaire, avec l'état réel du réglage | nom du réglage et son état |

### 4.2 L'inventaire de confiance

Fichier canonique `data/inventaire_confiance.json`, à côté de `data/capacites.json`, lu par `services/inventaire_confiance.py` sur le modèle de `services/capacites.py` (chemin relatif au module, validé à la lecture ; `backend.spec:101` embarque déjà `app/data`). Route `GET /api/confiance/inventaire` dans un nouveau routeur `routers/confiance.py` (le préfixe `/api/confiance` est libre). Le nom évite « périmètre », qui désigne la cloison d'une conversation, et « registre d'actions » (`lib/actionRegistry.ts`).

Quatre types d'entrée : `outil` (une clé de la table des outils natifs), `connecteur` (un préréglage de `PRESET_SERVERS`, `routers/mcp.py:306`, plus une entrée générique pour un serveur ajouté à la main), `chemin` (un chemin de fond, avec ses `points_d_appel` sous la forme `module:fonction`), `service` (un service branché : Gmail, IMAP, Google Agenda, CalDAV, synchro Google Sheets, dictée, images). Champs communs : `id`, `type`, `nom`, `effet`, `sorties` (liste de résolveurs), `interrupteur`, `domaines` (liste, éventuellement vide) et `texte`. Une entrée `connecteur` porte `preset_id` et le motif de ses domaines. Le champ `validation` est interdit pour un outil du chat, puisqu'il est calculé.

**Identité des préréglages** (livrée au lot 2, parce que les lignes `connecteur` en ont besoin) : `install_preset` transmet `preset_id` à `add_server`, qui l'écrit dans `mcp_servers.json` (champ facultatif). Pour un connecteur installé avant ce lot, l'identité se retrouve au chargement par le nom mis en forme, comme le fait déjà `routers/mcp.py:529` ; un préréglage renommé à la main n'est plus reconnu et reste hors domaine. B-1498 relit déjà ce fichier après une restauration (`routers/data.py:1777-1783`).

### 4.3 Les résolveurs de sortie

La route résout chaque résolveur contre la configuration du moment. Aucun ne rend une clé, un jeton, un mot de passe ni une adresse complète de boîte : seuls un nom de service et un nom d'hôte sortent.

| Résolveur | Lit | Rend, par exemple |
|---|---|---|
| `aucune` | rien | « Reste sur ta machine » |
| `fournisseur_ia` | `chaine_de_repli()` (P-106 V4, §6.1 point 1) et `est_modele_ollama_cloud` (`services/ollama_capabilites.py:86`) | « Reste sur ta machine (modèle local mistral-small) », « Ollama Cloud (ollama.com) », « Mistral (en ligne), puis en cas de panne : OpenAI (en ligne), puis ton modèle local », « Aucun service d'IA prêt » |
| `moteur_recherche` | interrupteur (`services/web_search.py:82`) et service choisi (`get_web_search_service`, `:488`) | « Coupée », « Brave Search », « DuckDuckGo », « SearXNG (hôte) » |
| `recherche_conversation` | le fournisseur, puis `moteur_recherche` | « Google, par Gemini » quand le service est Gemini (recherche native, `routers/chat.py:2543`, `:2555`), sinon comme `moteur_recherche` |
| `compte_mail` | `EmailAccount.provider` et la destination de la carte (`get_email_confirmation_destination`, appelée `routers/chat.py:3170`) | « Gmail », « serveur IMAP et SMTP (hôte) », « Aucune boîte branchée » |
| `agenda_actif` | `Calendar.provider` et `get_calendar_confirmation_destination` (appelée `routers/chat.py:3158`), la fonction même de la carte | « Reste sur ta machine », « Google Agenda (en ligne) », « serveur CalDAV (hôte) » |
| `connecteur` | serveurs installés, leur état, leur `preset_id` | « Slack, en marche », « Slack, coupé » |
| `openclaw` | configuration OpenClaw | « Agents OpenClaw, puis le modèle choisi dans OpenClaw, que THÉRÈSE ne connaît pas » |
| `mode_board` | aucun état stable | « Selon le mode choisi à chaque délibération : Souverain (local) ou Cloud » |
| `dictee` | résolu **côté écran** : la préférence de voix locale et l'accord `voice` vivent dans la webview (`lib/consent.ts:26`) | « Reste sur ta machine », « Groq (en ligne) » |
| `images` | clés configurées des générateurs | « Le service choisi à la génération : OpenAI, Gemini ou Fal » |

**La chaîne de repli.** Elle vient de `chaine_de_repli()`, extraite par P-106 V4 de `_resolve_with_circuit_breaker` (`services/llm.py:813-871`) sans en changer les règles : le principal, puis, si la bascule est permise (`:831`) et que le principal n'est pas Ollama (garde B-1071, `:842`), les replis de `_get_fallback_configs` (`:749-811`) dans leur ordre. Qui livre en premier (lot 1 de P-106 ou lot 2 de P-107) crée l'extraction, l'autre la réutilise. La vue ne peut donc pas décrire une autre bascule que celle du moteur ; elle montre le repli tant que B-1189 ne l'a pas supprimé.

**Hors de la boucle d'événements.** `_get_fallback_configs` lit les clés en base (`:784`) et interroge Ollama (`detect_default_ollama_model`, `:805`, qui fait `httpx.get(..., timeout=2.0)` à `:337`), le tout de façon synchrone. Aujourd'hui ce code ne tourne que quand le disjoncteur est ouvert. La route l'appelle dans `asyncio.to_thread`, comme D5 et BUG-155 l'ont imposé ailleurs. **Point d'accroche pour P-106** : `config_du_tour()`, appelée à chaque tour du chat, ne parcourt les replis que si le principal est indisponible (`services/llm.py:825-826`), sinon chaque message paierait deux secondes quand Ollama ne répond pas.

### 4.4 Les sentinelles

Dans `tests/test_sentinelles_structure.py`, qui porte déjà les contrôles AST et JSON du dépôt :

1. **Complétude** (`test_inventaire_couvre_chaque_outil_prereglage_et_outil_du_pont`) : chaque clé de la table des outils natifs (`services/contexte_execution.py:30`), chaque `id` de `PRESET_SERVERS` avec ses `domaines` déclarés et chaque outil du pont filtré (`services/mcp_therese_server.py:250`) a exactement une entrée.
2. **Cohérence de l'effet** (`test_effet_coherent_avec_la_classification`) : `LECTURE_SEULE` impose « Lit », `MUTATION_LOCALE` interdit « Lit », aucune entrée `outil` ne porte `validation`.
3. **Portes de sortie** (`test_chaque_appel_d_une_porte_est_declare`) : liste fermée `LLMService.stream_response` (`services/llm.py:911`), `stream_response_with_tools` (`:968`), `continue_with_tool_results` (`:1063`), `generate_content` (`:1123`), les `search` des services de recherche, `spawn_session` et `send_message` du pont OpenClaw, `send_message` des fournisseurs de mail, `MCPService.call_tool` et `execute_tool_call` (`services/mcp_service.py:843`, `:922`), les générateurs d'images, la transcription. Chaque fonction qui appelle une porte, repérée par l'AST, figure dans les `points_d_appel` d'une entrée.
4. **Imports réseau** (`test_chaque_import_tiers_est_classe`) : chaque module de premier niveau importé par le moteur, **au premier niveau ou dans une fonction**, et absent de `sys.stdlib_module_names`, est classé « réseau » ou « local » dans une table du test, avec un motif. État à la base : 37 modules tiers. Classés réseau : `httpx` (18 modules au premier niveau, 24 avec les imports dans les fonctions), `aiosmtplib`, `imap_tools`, `caldav`, `openai`, `google` (genai), `playwright`, `sentence_transformers` (télécharge le modèle d'indexation au premier usage, `services/embeddings.py:44-48`), `faster_whisper` (télécharge le modèle de dictée, `services/voice_local.py:179-182`). `qdrant_client` est classé local : il ouvre un dossier (`services/qdrant.py:71`, `:112`). Pour la bibliothèque standard, `socket` est importé par trois modules (`services/browser_agent.py`, `services/skills/code_executor.py`, `services/agents/bac_a_sable.py`), `ssl` par un, `urllib` par huit, `smtplib`, `imaplib` et `http.client` par aucun : chacun est classé avec son motif. Tout module qui importe un module « réseau » est une porte, un fournisseur (`services/providers/`) ou une exception motivée. **Ce que la sentinelle ne voit pas** : `asyncio.open_connection` et les sous-processus. Elle rend l'oubli coûteux, pas impossible.

Chacune est vue rouge sur un cas fabriqué au lot 2 (outil ajouté sans entrée ; fonction qui appelle `continue_with_tool_results` sans être déclarée ; module qui importe `imap_tools` dans une fonction sans être classé ; import tiers inconnu).

### 4.5 Le journal des validations

**Ce que le code fait aujourd'hui.** `empreinte_action` (`services/tool_confirmations.py:149`) rend destinataires, copie, objet et corps en clair (alias du corps : `_ALIAS_CORPS`, `:130`). Elle ne sert qu'à dédupliquer les cartes d'un tour, en mémoire. Elle ne doit jamais atteindre un journal.

**Ce que le lot 1 écrit.** Deux nouvelles valeurs d'`AuditAction` (`services/audit.py:19`), `tool_confirmed` et `tool_refused`, écrites par `confirm_tool` :

- à la validation, juste après le refus (`routers/chat.py:3573`) et **avant** l'exécution, pour que la trace existe même si l'exécution échoue ;
- au refus, avant le `return` de `:3572-3573` ;
- rien quand l'action est introuvable (`:3565-3569`).

Colonnes : `action`, `resource_type = "validation"`, `resource_id` = identifiant de conversation (ou vide), `details = {"outil": nom, "origine": "chat", "condensat": hex}`. Ni `ip_address` ni `user_agent`.

**Le condensat.** `HMAC-SHA256(clé, message)`. La clé dérive de la clé maîtresse par HKDF avec `info = b"therese-journal-validations-v1"`, sur le modèle de `derive_db_key_from_master` (`services/encryption.py:470-485`) : aucun secret nouveau à ranger, la clé suit le cycle de vie de la clé maîtresse et n'est jamais écrite. Le message est le JSON canonique (clés triées, séparateurs fixes) de `{"outil": nom, "arguments": arguments}` après `canoniser_arguments` et **sans** les trois clés privées de la carte, `_confirmation_destination`, `_compte_ecran`, `_agenda_ecran` (`routers/chat.py:3159-3173`). La clé HMAC tient le rôle du sel de la décision 10. Le condensat vit dans une fonction à part, `condensat_pour_journal`. Il ne se calcule qu'avec la clé maîtresse, qui déchiffre déjà la base : il n'ouvre aucune porte nouvelle. **Rotation** : `rotate_key` n'est pas prise en charge par l'application (relevé ci-dessus) ; si elle l'est un jour, les condensats d'avant et d'après ne se compareront plus, perte de corrélation sans exposition.

**Conservation.** Douze mois (décision 10). `purger_les_validations(jours=365)` ne supprime que les actions de validation, celles du lot 6 comprises, sur sa propre session comme `cleanup_old_logs` ; elle tourne au démarrage puis toutes les 24 heures dans la boucle quotidienne existante de la purge RGPD (`main.py:384-401`), sans nouvelle tâche. `cleanup_old_logs` n'est pas appelée : elle effacerait tout.

**Purge totale.** `_supprimer_toutes_les_donnees` supprime les lignes de validation avant son commit (`routers/data.py:702`). La ligne `data_deleted_all` (`:638-643`) et le reste du journal suivent la règle actuelle, sur laquelle la question 1 du §11 est posée. Le texte « Les logs d'audit sont conservés pour des raisons légales » (`:805`, `:810`) devient « Le journal d'activité est conservé, sauf les validations, effacées avec le reste. » ; la variante qui compte les sauvegardes garde le mot « sauvegarde » (`tests/test_routers_data.py:513`).

**Export et écran.** Les lignes partent dans l'export RGPD sans changement (`routers/data.py:412`) ; `GET /api/data/logs/actions` (`:891`) gagne la catégorie « validations ». Aucun écran nouveau ne lit le journal (« trop d'interfaces », 27/08) : les critères se vérifient par `GET /api/data/logs` (`:831`) et par l'export.

### 4.6 Les confirmations des écrans

**Le crochet devient fail-closed.** Sans fournisseur, `useExternalActionConfirmation` n'exécute plus l'action (`components/app/useExternalActionConfirmation.ts:32`), l'écrit en console et affiche « Action bloquée : la confirmation est indisponible ». Motif : l'exécution directe servait le mode classique (commentaire `:21`) ; la coque ne monte plus que `ConversationCanvasPrototype`, sous le fournisseur (`App.tsx:248-249`). Trois tests existants exigent l'inverse et sont réécrits au lot 6 : « conserve l'envoi direct en mode classique » (`components/email/EmailCompose.test.tsx:73`), « conserve la suppression directe en mode classique » (`components/email/EmailList.test.tsx:94`), « conserve la mise à la corbeille directe en mode classique » (`components/email/EmailDetail.test.tsx:145`). Le lot commence par passer toute la suite vitest avec le crochet fermé, pour relever les autres rendus sans fournisseur.

**Le critère de trace, unique.** Une confirmation d'écran est tracée quand elle autorise un **effet hors de la machine** : un envoi, une action sur un service distant, un contenu confié à un service en ligne. Une écriture locale ne l'est pas, même confirmée. Le chat suit une autre règle, et c'est voulu : une carte du chat valide une action que l'assistante propose, et toute validation de carte est tracée (§4.5) ; un écran exécute un geste que tu fais toi-même, et seul ce qui quitte la machine mérite une trace.

**Les portes d'écran.** Liste fermée de fonctions de `services/api` dont la route a, au moins dans un cas, un effet hors de la machine : `sendEmail`, `deleteEmailMessage`, `createEvent`, `updateEvent`, `deleteEvent`, `quickAddEvent`, `transcribeAudio`, `generateImage`, `streamDeliberation`, `streamAgentRequest`, `streamAgentSpawn`, `dispatchToOpenClaw`, `sendToOpenClawSession`. À la base, seize fichiers hors tests en appellent une :

| Fichier (appel, confirmation) | Porte | Nature | Tracée |
|---|---|---|---|
| `components/email/EmailCompose.tsx:93` | `sendEmail` | `email_envoye` | oui |
| `components/email/EmailList.tsx:278`, `components/email/EmailDetail.tsx:143` | `deleteEmailMessage` | `email_corbeille` | oui (la corbeille est celle du service) |
| `components/calendar/EventForm.tsx:206` | `createEvent`, `updateEvent` | `evenement_cree`, `evenement_modifie` | oui si l'agenda n'est pas local |
| `components/calendar/EventDetail.tsx:50`, `:59` | `deleteEvent` | `evenement_supprime` | oui si l'agenda n'est pas local |
| `components/prototype/usePrototypeMeetingData.ts:238` (confirmation `components/prototype/MeetingConversationCard.tsx:255`) | `createEvent` | `reunion_creee` | oui si l'agenda n'est pas local (le service envoie les invitations) |
| `components/board/BoardPanel.tsx:303` (confirmation `:271`) | `streamDeliberation` | `deliberation_cloud` | oui en mode Cloud, non en Souverain |
| `components/prototype/usePrototypeBoardData.ts:144` (confirmation `components/prototype/BoardConversationCard.tsx:740`) | `streamDeliberation` | `deliberation_cloud` | oui en mode Cloud, non en Souverain |
| `components/prototype/usePrototypeAtelierData.ts:280` (confirmation `components/prototype/AtelierConversationCard.tsx:185`, `:193`) | `streamAgentRequest` | `mission_atelier` | oui si le modèle choisi est en ligne |
| `components/prototype/ImagesWorkspaceCanvas.tsx:251` (confirmation `:222`) | `generateImage` | `image_generee` | oui |
| `components/prototype/VoiceWorkspaceCanvas.tsx:111` | `transcribeAudio` | `transcription_en_ligne` | oui si le moteur est Groq, non en local |
| `components/home/CommandExecutor.tsx:293` | `generateImage` | aucune | non : aucune confirmation (B-096, décision de Ludo) ; l'accord « images » manque (défaut relevé) |
| `hooks/useVoiceRecorder.ts:192`, `:287` | `transcribeAudio` | aucune | non : dictée gouvernée par l'accord « voice », sans confirmation par usage |
| `components/atelier/AtelierPanel.tsx:110` | `streamAgentRequest` | aucune | non : lancement par ton geste, sans confirmation |
| `components/atelier/AgentSession.tsx:339` | `streamAgentSpawn` | aucune | non : idem |
| `stores/openclawStore.ts:136`, `:197` | `dispatchToOpenClaw`, `sendToOpenClawSession` | aucune | non : lancement par ton geste ; l'accès aux données passe par le pont, gouverné par son interrupteur (§4.7) |

Hors portes, et non tracées parce que locales : les trois changements de statut de `components/invoices/InvoiceForm.tsx:480`, `:508`, `:536` (le crochet les confirme toujours), le devis de conversation (`components/prototype/InvoiceConversationCard.tsx:427`), et les suppressions en ligne de tâches ou de fiches.

**La trace.** Les confirmations locales et le fournisseur du crochet appellent une seule fonction, `tracerValidationEcran(nature, decision)` (`services/api/confiance.ts`, nouveau), dont `nature` est typée par l'union des natures : TypeScript refuse une nature inconnue. Le fournisseur (`components/app/ExternalActionConfirmation.tsx`) l'appelle à la confirmation, avant `action.run()` (`:75`), et à l'abandon (Annuler, Échap, `:55-65`), quand l'aperçu porte une nature. Route `POST /api/confiance/validations-ecran`, corps `{nature, decision}` seulement, modèle Pydantic `extra="forbid"` : titre, description et détails de l'aperçu ne quittent jamais l'écran. Actions `screen_action_confirmed` et `screen_action_refused`, `details = {"nature": …, "origine": "ecran", "declaree": true}`. Même conservation et même purge qu'au §4.5. Un échec de la trace ne bloque jamais l'action. Pour les natures conditionnelles (agenda, Atelier, transcription, Board), c'est le site qui décide, avec l'information qu'il affiche déjà (fournisseur de l'agenda, moteur, mode).

**La sentinelle** (`lib/confirmationsEcran.sentinelle.test.ts`) lit les sources par `import.meta.glob` en texte brut : tout fichier hors tests qui appelle une porte d'écran figure dans la table ci-dessus, tracé avec sa nature ou non tracé avec son motif ; un fichier tracé contient `tracerValidationEcran(`. Un nouvel appelant non classé fait échouer la suite. Vue rouge sur une source fabriquée qui appelle `sendEmail`.

### 4.7 Le pont des agents OpenClaw

**Interrupteur** `pont_agents_actif`, défaut actif, pour ne rien retirer sans geste à ceux qui l'utilisent. Coupé, `dispatch_to_openclaw` lance la session **sans** `therese-bridge` (`routers/agents.py:1367-1378`).

**Le jeton de pont.** Sans lui, aucun réglage ne s'applique au pont, puisque ses appels portent le jeton de l'interface (`routers/agents.py:1373-1375`, envoyé en `X-Therese-Token` par `services/mcp_therese_server.py:331-332`). Un jeton aléatoire par session, créé dans `dispatch_to_openclaw` et passé en `THERESE_MCP_TOKEN` à la place du jeton de session, vit dans un registre en mémoire `{jeton: (session, créé le)}`. Le middleware (`main.py:756-814`) l'accepte uniquement :

- sur les couples (méthode, gabarit) de `TOOL_ROUTES` filtré (`services/mcp_therese_server.py:259-281`), comparés segment par segment, jamais par préfixe ;
- pour un POST, seulement si le gabarit est sur une liste fermée de lectures servies en POST, aujourd'hui `/api/memory/search` (B-1496). `POST /api/email/messages`, qui est l'envoi (`routers/email.py:1284-1285`), partage son chemin avec `list_emails` en GET et doit être refusé ;
- si l'interrupteur est actif et que le domaine de la route n'est pas retiré, relus à chaque requête.

**Révocation** : à l'échec du lancement, avant le 502 (`routers/agents.py:1386-1391`) ; à l'annulation (`:1557-1591`) ; quand THÉRÈSE observe le passage à `done` ou `error` (`:1466-1480`) ; à l'arrêt de l'application ; au plus tard 12 heures après sa création. THÉRÈSE n'observe la fin d'une session que lorsque l'écran relit son détail ; d'ici là le jeton reste valide jusqu'à ses 12 heures, limité aux lectures filtrées.

**Ce que dit l'écran de l'Atelier OpenClaw**, interrupteur coupé : « THÉRÈSE n'ouvre plus tes données à cet agent. Un agent qui peut lancer des commandes sur cette machine peut encore les lire par d'autres voies : ne confie une mission qu'à un agent en qui tu as confiance. » Motif : le jeton de session est écrit dans `.session_token` (`main.py:422`) et rendu à tout appel sans Origin (`main.py:715-726`, route exemptée `:775`). La limite est **consignée dans `SECURITY.md`**, section « Limitations connues (alpha) » (`SECURITY.md:66`), pas figée par un test : le jour où la route est fermée, rien ne doit rougir.

### 4.8 Retirer un domaine

#### 4.8.1 Les domaines et ce qu'ils couvrent

| Domaine | Conversation | Contexte injecté | Gestes et commandes | Agents d'action | Pont OpenClaw | Connecteurs |
|---|---|---|---|---|---|---|
| Mémoire : contacts, projets, et sur chaque fiche les prestations et les traces du carnet | `read_contact`, `create_contact`, `create_project` | types `contact`, `project` | `/contact`, `/projet`, `[contact: …]`, `[projet: …]` ; compétences (contact apparié) ; contexte du carnet de la réponse proposée | `crm` (contacts, étapes, activités) | `list_contacts`, `get_contact`, `search_memory`, `get_project` | aucun préréglage |
| E-mails | `read_emails`, `summarize_emails`, `search_emails`, `send_email` | aucun | fil joint à la réponse proposée | `email` | `list_emails` | `google-workspace` |
| Agenda | `list_calendar_events`, `create_calendar_event` | aucun | `/rdv`, `[rdv: …]` | `calendar` | `list_events` | `google-workspace` |
| Factures et devis : les pièces, leurs lignes et leurs totaux | `search_invoices`, `invoice_totals` | aucun | aucun | `invoices`, et le bloc des pièces de la source `crm` | `list_invoices` | aucun préréglage |
| Tâches | aucun | aucun | aucun | `tasks` | `list_tasks` | aucun préréglage |
| Fichiers indexés | `search_files`, `read_file` | type `file` | aucun | aucun | aucun | `filesystem` |

Les prestations d'une fiche sont des objets du carnet (`services/memory_tools.py:988-1022`, `_etat_courant` `:1141`, `_traces_du_contact` `:1183`) et non des pièces : retirer Factures ne les masque pas, retirer Mémoire les retire avec la fiche. Aucune activité du carnet n'est tirée d'un e-mail. L'écran le dit sous chaque interrupteur.

Restent hors domaine, gouvernés par leurs réglages : `web_search` et `browser_navigate` (interrupteur web, `routers/chat.py:2555`), `generate_document` (sous carte), les pièces jointes (geste explicite), l'extraction d'entités (son interrupteur ; elle n'envoie que le message), le type `owner` (ton profil).

#### 4.8.2 Le crochet mémoire, commun avec P-106

P-106 V4 (§6.1 point 7) ajoute à `_get_memory_context` (`routers/chat.py:745`) le paramètre `types_permis`, calculé à chaque tour par `types_de_memoire_permis(documents_permis, domaines_retires=())` et passé à `async_search(memory_types=…)` (`services/qdrant.py:577-592`), aux deux appels (`routers/chat.py:1740`, `:2398`). La fonction part de la table des quatre types écrits (`contact`, `project`, `file`, `owner`) et rend une **liste blanche**, jamais `None` ni vide : un type absent de la table n'est jamais transmis (aujourd'hui il partirait brut, `routers/chat.py:819-820`), et une liste vide supprime la recherche au lieu de valoir « aucun filtre » (`services/qdrant.py:264`).

P-107 y branche sa condition, au lot 5 : `contact` et `project` sortent si Mémoire est retirée ; `file` sort si Fichiers indexés est retiré (ou, par P-106, sans l'accord « documents »). La phrase D6 (`routers/chat.py:856`) n'est pas émise quand `file` n'est pas permis. `include_memory=false` (B-1495) garde son sens de tout ou rien, appliqué avant. Si le lot 5 de P-107 part avant le lot 1 de P-106, c'est lui qui crée la fonction, avec la table et la sentinelle décrites par P-106 V4, et le paramètre `documents_permis` vaut vrai jusqu'à P-106.

#### 4.8.3 La règle des gestes explicites

**Un geste explicite sur un objet transmet cet objet, et rien d'autre d'un domaine retiré.**

- **Compétences** (`routers/skills.py:63-64`) : le prompt est ton geste. Mémoire retirée, `execute_skill` ne charge ni contacts ni projets (`:109-112`), et l'enrichissement le dit : « contact non joint : la mémoire est retirée dans les réglages ».
- **Réponse proposée à un e-mail** (`routers/email.py:1853-1932`) : le message ouvert part, puisque c'est lui que tu as choisi. Le contexte du carnet sur l'expéditeur (`:1875-1889`) n'est pas joint quand Mémoire est retirée ; **les messages précédents du fil** (`:1893-1910`) ne sont pas joints quand E-mails est retiré. L'accord pour ce chemin reste B-1240.
- **Commandes déterministes et directives** : `execute_slash_command_outcome` (`services/slash_commands.py:297`) est le point unique, appelé pour `/cmd` (`routers/chat.py:1469`) comme pour `[cmd: …]` (`:1544-1550`). Domaine retiré, la commande ne fait rien et répond aussitôt : « L'agenda est retiré de la conversation dans les réglages : crée le rendez-vous depuis l'Agenda. » (et ses variantes pour Mémoire). Aucune carte n'est posée pour `rdv` (`register_pending`, `services/slash_commands.py:279`).

Les écrans (Courrier, Agenda, Contacts, Factures) restent à toi : ce que tu y fais toi-même n'est pas touché.

#### 4.8.4 Les connecteurs

- Domaines déclarés dans `PRESET_SERVERS` : `google-workspace` touche E-mails et Agenda (`routers/mcp.py:342`) ; `filesystem` touche Fichiers indexés (`:311`), puisqu'il lit les mêmes fichiers locaux. Les autres préréglages exposent les données d'un service tiers et n'en déclarent aucun, chacun avec son motif dans l'inventaire.
- **Retrait** (lot 5) : les outils `{identifiant}__{outil}` (`services/mcp_service.py:915`) d'un connecteur qui déclare un domaine retiré quittent la liste du chat au même point que les outils natifs. Le serveur n'est pas arrêté : couper un connecteur reste le geste de l'écran Connecteurs (`routers/mcp.py:94-135`).
- **Accord « documents »** (lot 2b, décision 8) : quand `documents_permis` est faux (P-106 V4, §6.1 point 3), les outils des connecteurs qui déclarent Fichiers indexés sont retirés comme `search_files` et `read_file` (P-106 V4, point 6), et la phrase de remplacement de P-106 les couvre. Un connecteur ajouté à la main n'appartient à aucun domaine : l'écran le dit (« Les connecteurs que tu as ajoutés toi-même se coupent un par un, dans Connecteurs. Ils te demandent toujours avant d'agir. »). **Point d'accroche pour P-106** : la phrase du Centre de confiance de son lot 1 (« Dans le chat, le contenu de tes fichiers ne part vers un service en ligne que si tu l'as autorisé pour ce service ») n'est vraie, pour qui a installé `filesystem`, qu'après le lot 2b ; si le lot 1 de P-106 part avant, elle est bornée « hors connecteurs que tu as installés » jusqu'au lot 2b, qui retire la borne.

#### 4.8.5 Points d'application, tous côté serveur

1. **Liste d'outils du chat** : outils natifs et outils de connecteurs du domaine retirés avant `retirer_outils_deja_en_attente` (`routers/chat.py:2561`) ; le bloc des capacités suit (`:2563-2568`).
2. **Exécution** : B-1489 refuse tout outil absent de la liste du tour ; `confirm_tool` refuse en plus un outil d'un domaine retiré, pour la carte posée avant le retrait, avec la phrase « Accès retiré dans les réglages » (après `:3573`, avant `:3578`).
3. **Contexte mémoire** : §4.8.2.
4. **Gestes et commandes** : §4.8.3.
5. **Agents d'action** : `_gather_local_context` (`services/action_agents.py:253`) retire la source et l'écrit dans le contexte, sur le modèle de la ligne web (`:522-526`) ; dans la source `crm`, la requête des pièces (`:328-334`) et leurs lignes (`:368-373`) sont sautées quand Factures est retiré, et une ligne « pièces retirées dans les réglages : ne rien inventer à ce sujet » les remplace.
6. **Pont** : le middleware (§4.7).

Le réglage `domaines_retires` est mis en cache comme l'interrupteur web ; une préférence illisible au démarrage retire tous les domaines et l'écrit au journal.

#### 4.8.6 Purge, restauration, relais : les protections et la mémoire du processus

**La purge garde les protections.** `_supprimer_toutes_les_donnees` supprime toutes les préférences (`routers/data.py:699`) **sauf** une liste fermée, `PREFERENCES_DE_PROTECTION = ("domaines_retires", "pont_agents_actif", "web_search_enabled", "mode_cabinet")`. Motif : la purge efface tes données ; remettre ces réglages au défaut rouvrirait des accès que tu avais fermés, pour des connecteurs que la purge ne désinstalle pas (`mcp_servers.json` n'est pas touché, `:773` ne vide que quatre dossiers) et pour les données que tu recréeras ensuite. La note le dit : « Tes réglages de protection (domaines retirés, pont des agents, recherche web, cloisonnement par dossier) sont gardés : les connecteurs installés restent sous ces retraits. » C'est un changement de comportement par rapport à B-1505, dont le test change d'attendu (§9).

**La restauration applique ceux de la base restaurée**, sans attendre le redémarrage : la base restaurée fait foi, restrictions comprises.

**Une seule fonction remet la mémoire du processus en phase** : `resynchroniser_les_preferences_en_memoire()` (dans `routers/data.py`, à côté de `_oublier_les_cles_en_memoire`, `:552`). Elle oublie les clés et le service des modèles (B-023, B-1124), recharge le profil (`set_cached_profile`), `THERESE.md` (`reload_therese_md`), l'interrupteur web (`poser_autorisation_recherche(None)` puis `charger_autorisation_depuis_la_base`, `services/web_search.py:72`, `:97`), le mode cabinet (`poser_mode_cabinet`), et au lot 5 les caches de `domaines_retires` et de `pont_agents_actif`. Elle remplace les appels épars de la purge (`routers/data.py:709-721`, `:783-786`) et de la restauration (`:1795-1806`), et le relais de P-108 l'appelle. Si les correctifs des jumeaux de B-1522 (défauts relevés ci-dessus) créent cette fonction avant le lot 5, le lot 5 y ajoute ses deux caches.

**Ce que dit l'écran** : « Retirer un domaine le retire de la conversation, des agents d'action, des agents OpenClaw et des connecteurs qui le touchent. Tes écrans restent à toi. Un geste que tu fais sur un élément précis (répondre à un e-mail, lancer une compétence) transmet cet élément, sans rien d'autre du domaine retiré. » Et pour « Améliorer THÉRÈSE » : « L'Atelier lit le dossier de la mission, pas tes domaines. » (ses agents lisent l'espace de travail de la mission, `services/agents/runtime.py:196-197`).

### 4.9 La vue

- **Le tableau qui fait foi** vit dans Paramètres > Confidentialité, section « Ce que THÉRÈSE peut faire » : un vrai `<table>` avec légende, cinq en-têtes de colonne, une ligne par entrée, groupé par type. Le Centre de confiance fait 360 px (`components/prototype/CapabilityCenter.tsx:564`) : il n'y tiendrait pas.
- **Le Centre de confiance se greffe sur P-118** : la ligne d'état (`:584`) reste ; la ligne fixe « Ce qui sort de ta machine » (`:589`) devient une liste courte dérivée de la route (« Sans te demander : Décision cherche sur le web avec Brave Search », « Agents OpenClaw : accès à tes données actif »), suivie de « Tout voir », qui ouvre Confidentialité (`onOpenPrivacy`, `:595`).
- **Aucun libellé de périmètre écrit en dur** dans les composants : tout vient de la route.

### 4.10 L'export

**P-107 porte seul l'écriture du BPMN**, pour le seul export de l'inventaire : P-106 V4 lit les BPMN et n'en écrit aucun. Deux exports locaux de l'inventaire résolu, enregistrés par la boîte native comme l'export RGPD (`services/api/data.ts:45`) :

- **Mermaid** (`flowchart LR`, un `subgraph` par couloir), lot 7a, sans mise en page.
- **BPMN 2.0 avec diagramme** (`bpmndi`), lot 7b : trois couloirs (Toi, THÉRÈSE, Services extérieurs) ; une colonne par entrée ; pour une validation « avant », une tâche utilisateur « Valider : … », une passerelle « validé ? », puis la tâche de service ; sinon la tâche de service seule. Positions sur une grille fixe, sans algorithme de placement. Écriture par `xml.etree.ElementTree`, sans `DOCTYPE` (le lecteur de P-106 le refuse) ; aucune lecture de fichier extérieur.

Chiffrage : 7a, une à deux heures ; 7b, une demi-journée à une journée, recette dans deux modeleurs comprise. Au-delà, on s'arrête au Mermaid et on le dit à Dr_logic. L'extracteur `.bpmn` de P-106 (son lot 3) sert d'oracle dès qu'il existe ; `ElementTree` avant.

### 4.11 Hors périmètre

- Assouplir le portillon (une demande d'assouplissement aura sa propre RFC).
- Retrait par projet.
- Un bac à sable contre un processus local malveillant, et la fermeture de `/api/auth/token` : le jeton reste lisible dans `.session_token` (§4.7).

## 5. Inventaire des chemins

Contenu initial de l'inventaire, relevé à `d0f7ab26` par les appels aux portes du §4.4.

| Chemin | Points d'appel | Validation | Sorties | Ce qui le coupe |
|---|---|---|---|---|
| Conversation | `routers/chat.py:1857` (sans flux) ; `:2662` (flux avec outils) ; `:3446` (continuation) ; outils `:3240`, `:3268`, `:3303`, `:3337`, `:3368` ; confirmation `:3600`, `:3607`, `:3609`, `:3614`, `:3623` | par outil, calculée | `fournisseur_ia`, puis selon l'outil | par domaine |
| Extraction d'entités | `routers/chat.py:940-969`, `services/entity_extractor.py:135` | automatique | `fournisseur_ia` | Extraction automatique |
| Recherche approfondie | `routers/chat.py:1147`, `services/deep_research.py:92`, `:120`, `:226`, `:298` | démarrée par toi | `fournisseur_ia`, `moteur_recherche` | Recherche web |
| Décision (Board) | `services/board.py:302`, `:520`, `:671`, `:953` | démarrée par toi | `mode_board`, `moteur_recherche` | Recherche web |
| Agents d'action | `services/action_agents.py:532`, `:836` | démarrés par toi | `fournisseur_ia`, `moteur_recherche` | par domaine, Recherche web |
| Améliorer THÉRÈSE (Atelier) | `services/agents/runtime.py:284`, `:321`, `services/agents/tools.py:930` | démarré par toi, fusion après relecture | `fournisseur_ia` (avec le dossier de la mission), `moteur_recherche` | Recherche web |
| Agents OpenClaw et pont | `routers/agents.py:1380`, `:1544` | démarrés par toi | `openclaw` | Pont des agents, par domaine |
| Atelier documentaire | `routers/documents.py:370`, `:501`, `:696` | démarré par toi | `fournisseur_ia` | aucun |
| Réponse proposée à un e-mail | `services/email_response_generator.py:211` | démarrée par toi | `fournisseur_ia` | Mémoire (contexte du carnet), E-mails (fil) |
| Résumé de mails | `services/workspace_tools.py:1405` | lecture, sans carte | `fournisseur_ia` | E-mails |
| Compétences | `routers/skills.py:169`, `:231` | démarrées par toi | `fournisseur_ia` | Mémoire (contact joint seulement) |
| Commandes et directives `contact`, `projet`, `rdv` | `services/slash_commands.py:161`, `:200`, `:251` (carte `:279`) | démarrées par toi ; carte pour `rdv` | `aucune`, `agenda_actif` pour `rdv` | Mémoire, Agenda |
| Génération de commande | `routers/commands_v3.py:159` | démarrée par toi | `fournisseur_ia` | aucun |
| Appel direct d'un connecteur | `routers/mcp.py:250`, `:253`, `:265` | aucune carte ; aucun appelant dans l'interface | `connecteur` | Connecteur coupé |
| Envoi de mail depuis l'écran | `routers/email.py:1284`, `services/workspace_tools.py:1471` | carte d'écran ou du chat | `compte_mail` | aucun (écran) |
| Dictée et transcription | `routers/voice.py:60`, `:100` | démarrée par toi ; confirmation dans le canevas | `dictee` | accord « voice » |
| Images | `routers/images.py:80`, `:110`, `:153`, `:193` | canevas : confirmation ; Accueil : aucune (B-096) | `images` | aucun |
| Synchro CRM Google Sheets | `routers/crm.py` (synchronisation), `services/sheets_service.py` | démarrée par toi | Google Sheets | aucun |

## 6. Lots

Chaîne de chaque lot : revue de conception du lot, tests écrits d'abord et vus rouges, code, sabotage ciblé par fonction (découper le source entre deux `def`, jamais un remplacement de chaîne globale), revue adverse du diff, recette dans l'application lancée. Chaque critère observable se vérifie par une route ou dans l'application, jamais par un écran qui n'existe pas.

### Lot 1 : le journal des validations (moteur)

Livre §4.5. Fichier `tests/test_p107_lot1_journal_validations.py` :

- `test_marqueur_absent_du_journal_apres_validation_et_refus` (paramétré : `send_email` avec le marqueur dans `to`, `cc`, `subject` et les quatre alias de corps ; `slack__post_message` ; `generate_document`) : le marqueur n'apparaît dans aucune colonne d'aucune ligne d'`ActivityLog`, `details` compris ;
- `test_marqueur_absent_de_get_logs_et_de_l_export` et `test_marqueur_absent_des_journaux_techniques` (`caplog`) ;
- `test_validation_refus_et_action_inconnue` : une ligne `tool_confirmed`, une ligne `tool_refused`, aucune pour un identifiant inconnu ;
- `test_condensat_stable`, `test_condensat_change_avec_le_corps`, `test_condensat_ignore_les_cles_privees_de_la_carte`, `test_condensat_differe_du_sha256_non_sale` ;
- `test_conservation_supprime_366_jours_garde_364` et `test_conservation_ne_touche_pas_le_reste_du_journal` (une ligne `contact_created` de 400 jours reste) ;
- `test_purge_efface_les_validations_et_garde_data_deleted_all` ;
- `test_texte_de_purge_sans_raisons_legales` ; `tests/test_routers_data.py:513` reste vert.

Dans `tests/test_sentinelles_structure.py` : `test_empreinte_action_n_atteint_aucun_journal` (ni `logger.*`, ni `log_activity`, ni `AuditService.log`, ni un argument `details=`).

Sabotage : remplacer le condensat par `json.dumps(arguments)` rend `test_marqueur_absent_du_journal_apres_validation_et_refus` rouge.

Critère observable : valider une carte d'envoi, puis `GET /api/data/logs?action=tool_confirmed` rend une ligne avec l'outil et un condensat, sans rien du message ; l'export RGPD contient la même ligne.

### Lot 2 : l'inventaire, les résolveurs, la route, l'identité des préréglages (moteur)

Livre §4.2 à §4.4 et §5. Fichier `tests/test_p107_lot2_inventaire_confiance.py` :

- `test_inventaire_lu_par_chemin_relatif_au_module` ;
- `test_validation_calculee_egale_requires_confirmation` (paramétré sur la table des outils) et `test_outil_mcp_inconnu_te_demande_avant` ;
- `test_resolveur_fournisseur_ia` (paramétré : Ollama local ; Ollama `:cloud` ; Mistral seul ; Mistral avec une clé OpenAI enregistrée, la ligne dit « puis en cas de panne : OpenAI » ; Ollama local avec une clé OpenAI, aucun repli en ligne (B-1071) ; aucun service) ;
- `test_chaine_de_la_vue_egale_la_bascule_du_disjoncteur` : pour chaque cas, principal déclaré en panne, le premier élément disponible de la chaîne rendue est celui que `_resolve_with_circuit_breaker` retient ;
- `test_board_sans_repli` (bascule coupée, `services/board.py:620`) et `test_board_suit_le_moteur_choisi` (Brave sur sa ligne) ;
- `test_resolveur_moteur_recherche` (coupée, Brave, DuckDuckGo, SearXNG avec son hôte, Gemini natif) ;
- `test_resolveur_agenda_actif` (local, Google, CalDAV) et `test_resolveur_compte_mail` (aucune boîte, Gmail, IMAP avec son hôte) ;
- `test_resolveur_connecteur` (en marche, coupé) ;
- `test_aucun_secret_dans_la_reponse` (clé d'API, mot de passe IMAP et jeton OAuth fabriqués absents) ;
- `test_route_ne_bloque_pas_la_boucle_quand_ollama_est_injoignable` : `httpx.get` remplacé par une attente de deux secondes ; pendant la lecture de l'inventaire, `GET /api/health` répond en moins de 300 ms ;
- `test_prereglage_installe_enregistre_son_identite` et `test_identite_retrouvee_par_le_nom_pour_un_fichier_ancien`.

Dans `tests/test_sentinelles_structure.py` : les quatre sentinelles du §4.4, chacune vue rouge sur son cas fabriqué.

Critère observable : `GET /api/confiance/inventaire` sur une installation réelle rend les chemins du §5, les outils et les connecteurs installés, et ses sorties décrivent la configuration du moment.

### Lot 2b : l'accord « documents » couvre le connecteur `filesystem` (moteur)

Livre la troisième puce du §4.8.4. Dépend du lot 1 de P-106 (`documents_permis`) et du lot 2 (identité des préréglages). Fichier `tests/test_p107_lot2b_connecteur_fichiers.py` :

- `test_outils_filesystem_retires_sans_accord_documents` (destination en ligne, accord absent : aucun outil du serveur installé depuis `filesystem` dans la liste ni dans le bloc des capacités) ;
- `test_outils_filesystem_offerts_avec_accord` et `test_outils_filesystem_offerts_en_local` (Ollama local) ;
- `test_connecteur_ajoute_a_la_main_non_concerne` ;
- `test_appel_filesystem_rejoue_refuse` (un appel rejoué hors de la liste n'est pas exécuté, B-1489).

Critère observable : avec Mistral et sans l'accord « documents », demander « lis le fichier devis.pdf de mon dossier » ; l'assistante dit que l'accord manque et où le donner.

### Lot 3 : la vue (écran)

Livre §4.9. Fichier `components/settings/CeQueThereseFait.test.tsx` :

- `getByRole('table', { name: 'Ce que THÉRÈSE peut faire' })`, cinq `columnheader`, une ligne par entrée de la réponse simulée ;
- la même réponse avec la recherche coupée change la ligne du Board, preuve qu'aucun libellé n'est écrit en dur ;
- lecture échouée : « Impossible de lire l'inventaire » au lieu d'une liste vide (doctrine B-051).

Fichier `components/prototype/CapabilityCenter.inventaire.test.tsx` : la ligne d'état de P-118 reste ; le texte fixe de `:589` est remplacé par la liste dérivée ; « Tout voir » ouvre Confidentialité.

Critère observable : recette ligne par ligne, chaque ligne confrontée à un geste réel (une carte pour un outil sous carte, une recherche du Board interrupteur coupé puis rallumé).

### Lot 4 : le pont des agents (moteur, écran, sécurité)

Livre §4.7. Dépend du lot 2. Fichier `tests/test_p107_lot4_pont_agents.py` :

- `test_jeton_de_pont_lit_les_messages` (`GET /api/email/messages` : 200) ;
- `test_jeton_de_pont_refuse_l_envoi_par_la_meme_route` (`POST /api/email/messages` : 403) et `test_jeton_de_pont_refuse_post_tasks` (`POST /api/tasks` : 403) ;
- `test_jeton_de_pont_accepte_la_recherche_en_post` (`POST /api/memory/search` : 200) ;
- `test_jeton_de_pont_refuse_config_et_export` (`GET /api/config/llm`, `GET /api/data/export` : 403) et `test_jeton_de_pont_refuse_un_chemin_encode` (`/api/memory/contacts/..%2F..%2Fconfig%2Fllm/fiche` : 403) ;
- `test_interrupteur_coupe_refuse_tout_et_lance_sans_pont` ;
- `test_revocation_apres_echec_du_lancement`, `test_revocation_au_passage_observe_a_done`, `test_revocation_au_passage_observe_a_error`, `test_revocation_a_l_annulation`, `test_revocation_apres_douze_heures` (horloge simulée) ;
- la suite existante du jeton de session reste verte, sans modification.

Dans `tests/test_sentinelles_structure.py` : `test_chaque_post_du_pont_est_une_lecture_declaree`.

Fichier `components/atelier/NewTaskDialog.pont.test.tsx` : pont coupé, la phrase contient « peut encore les lire par d'autres voies » et ne contient pas « sans accès à tes données ». `SECURITY.md` gagne le paragraphe de la limite dans « Limitations connues (alpha) » (`:66`).

Critère observable : une mission OpenClaw lancée pont coupé répond qu'elle n'a pas accès aux contacts.

### Lot 5 : le retrait par domaine, les protections et la remise en phase (moteur, écran)

Livre §4.8. Dépend du lot 4 (pont). Le lot 1 de P-106 est souhaité avant (sinon ce lot crée `types_de_memoire_permis`, §4.8.2). Fichier `tests/test_p107_lot5_retrait_par_domaine.py` :

- `test_fichiers_retires_aucun_type_file_transmis` (espion sur `async_search`), `test_fichiers_retires_outils_absents_de_la_liste_et_des_capacites`, `test_fichiers_retires_phrase_d6_absente` ;
- `test_memoire_retiree_aucun_contact_ni_projet_transmis`, `test_memoire_retiree_competence_sans_notes_ni_email_du_destinataire`, `test_memoire_retiree_reponse_proposee_sans_contexte_crm`, `test_memoire_retiree_read_contact_absent`, `test_memoire_retiree_get_contact_du_pont_en_403` ;
- `test_memoire_retiree_commande_contact_ne_cree_rien` (paramétré : `/contact Marie` et `[contact: Marie]`) ;
- `test_email_retire_reponse_proposee_sans_le_fil` ;
- `test_email_retire_outils_absents_de_la_liste_et_des_capacites`, `test_email_retire_outils_google_workspace_absents_serveur_manuel_offert`, `test_email_retire_carte_posee_avant_refusee_a_la_confirmation`, `test_email_retire_relance_clients_recoit_acces_retire`, `test_email_retire_jeton_de_pont_403_sur_les_messages` ;
- `test_agenda_retire_rdv_sans_carte` (paramétré : `/rdv` et `[rdv: …]` ; `register_pending` non appelé ; phrase immédiate) ;
- `test_factures_retirees_read_contact_garde_etat_courant` et `test_rapport_hebdo_sans_numero_de_piece_quand_factures_retirees` (aucun numéro de pièce dans le contexte transmis à l'agent) ;
- `test_preference_illisible_retire_tous_les_domaines` ;
- `test_purge_garde_les_protections` (paramétré sur les quatre clés), `test_purge_note_nomme_les_protections_gardees`, `test_purge_garde_les_retraits_et_les_outils_du_connecteur_restent_absents` (serveur installé depuis `google-workspace`, E-mails retiré avant la purge) ;
- `test_restauration_applique_aussitot_les_retraits_restaures` (base restaurée qui retire E-mails : `read_emails` absent sans redémarrage) ;
- `test_resynchronisation_relit_profil_therese_md_et_mode_cabinet` (s'il n'est pas déjà apporté par les correctifs des jumeaux de B-1522).

Dans `tests/test_sentinelles_structure.py` : `test_chaque_outil_commande_source_et_prereglage_a_un_domaine` (outils natifs, outils du pont, `tools` de `agents/action_agents.json`, `DETERMINISTIC_COMMANDS`, préréglages : un domaine ou la liste hors domaine).

Test existant modifié : `tests/test_b1505_interrupteur_web_apres_purge.py::test_la_purge_remet_l_interrupteur_a_son_etat_par_defaut` devient `test_la_purge_garde_l_interrupteur_web`, qui vérifie que la valeur est gardée **et** que le cache suit la base.

Fichier `components/settings/RetraitsParDomaine.test.tsx` : un interrupteur nommé par domaine, avec ce qu'il couvre ; la phrase des gestes explicites ; la phrase des connecteurs ajoutés à la main.

Critère observable : retirer E-mails, puis demander « lis mes mails » ; l'assistante répond que l'accès est retiré dans les réglages, et aucun outil Google Workspace n'est proposé.

### Lot 6 : les confirmations des écrans (écran, moteur)

Livre §4.6. Dépend du lot 1.

- `components/app/useExternalActionConfirmation.test.tsx` : sans fournisseur, l'action n'est pas appelée et « Action bloquée » s'affiche ; toute la suite vitest passe avec le crochet fermé.
- Les trois tests « mode classique » sont inversés : `EmailCompose.test.tsx:73`, `EmailList.test.tsx:94`, `EmailDetail.test.tsx:145` (sans fournisseur, l'action n'est pas appelée).
- `components/app/ExternalActionConfirmation.trace.test.tsx` : le corps envoyé vaut `{nature, decision}` et rien d'autre, à la confirmation et à l'abandon ; une nature absente de l'aperçu n'envoie rien.
- Un test par site conditionnel, dans le fichier de test du composant : `VoiceWorkspaceCanvas` (Groq tracé, local non), `BoardPanel` et `BoardConversationCard` (Cloud tracé, Souverain non), `EventDetail` et `EventForm` (Google tracé, local non), `MeetingConversationCard` (idem), `AtelierConversationCard` (modèle en ligne tracé, local non), `ImagesWorkspaceCanvas` (tracé).
- `lib/confirmationsEcran.sentinelle.test.ts` : la sentinelle du §4.6, vue rouge sur une source fabriquée.
- `tests/test_p107_lot6_validations_ecran.py` : `test_nature_hors_liste_422`, `test_champ_supplementaire_422`, `test_ligne_screen_action_confirmed_sans_contenu`, `test_conservation_et_purge_couvrent_les_validations_ecran`.

Critère observable : envoyer un e-mail depuis le Courrier, puis l'export RGPD contient `screen_action_confirmed`, `email_envoye`, « déclarée par l'interface » ; supprimer un rendez-vous d'un agenda local n'ajoute aucune ligne.

### Lot 7 : l'export (moteur, écran)

Dépend du lot 2, d'aucun lot de P-106. Fichier `tests/test_p107_lot7_export.py`.

- **7a, Mermaid** : `test_mermaid_un_subgraph_par_couloir`, `test_mermaid_validation_avant_en_noeud_de_decision`, `test_mermaid_echappe_guillemets_crochets_retours`, `test_mermaid_deterministe`.
- **7b, BPMN** : `test_bpmn_une_forme_par_noeud_une_arete_par_flux`, `test_bpmn_formes_dans_leur_couloir_sans_chevauchement`, `test_bpmn_identifiants_uniques`, `test_bpmn_deterministe_octet_pour_octet`, `test_bpmn_validation_avant_produit_tache_utilisateur_et_passerelle`, `test_bpmn_sans_doctype`, `test_bpmn_relu_par_l_extracteur_de_p106` (marqué à sauter tant que le lot 3 de P-106 n'existe pas).

Critère observable, en recette : le fichier s'ouvre et s'affiche dans demo.bpmn.io et dans Camunda Modeler.

## 7. Données et migrations

- **Aucune révision Alembic.** La tête reste celle que P-132 vient de poser, `c9d0e1f2a3b4` (`models/database.py:715`) : les validations sont de nouvelles valeurs dans `activity_logs.action` et dans le JSON de `details` ; les réglages sont des lignes de `preferences` (`pont_agents_actif`, `domaines_retires`) ; l'inventaire est un fichier embarqué.
- **`mcp_servers.json`** gagne un champ `preset_id` facultatif ; un fichier ancien se lit tel quel.
- **Purge** : une suppression ciblée des validations, et une exception fermée à la suppression des préférences (`PREFERENCES_DE_PROTECTION`).
- **Sauvegarde et relais** : les préférences voyagent avec la base, ce qui est voulu (un retrait suit l'utilisateur) ; la restauration les applique aussitôt.

## 8. Risques restants

- **Un agent qui a un shell sur la machine** lit le jeton de session ; l'interrupteur et le retrait gouvernent le chemin prévu, pas un agent malveillant. L'écran et `SECURITY.md` le disent.
- **Le repli vers un autre service en ligne** existe tant que B-1189 n'est pas tranché ; la vue le montre au lieu de le taire.
- **Un connecteur ajouté à la main, ou un préréglage renommé**, reste hors des domaines et hors de l'accord « documents » ; l'écran le dit.
- **La sentinelle réseau** ne voit ni `asyncio.open_connection` ni un sous-processus.
- **Fin de session OpenClaw non observée** : le jeton vit jusqu'à 12 heures, limité aux lectures filtrées.
- **Validation déclarée pour les chemins de fond** : aucun portillon hors du chat ; la recette du lot 3 la tient.
- **Trace d'écran déclarée** : le serveur ne voit pas ces confirmations ; la trace est marquée « déclarée par l'interface ».
- **Le condensat est une corrélation, pas un secret** : qui détient la clé maîtresse peut tester une hypothèse ; il déchiffre déjà la base.
- **Cartes jamais tranchées** : une carte perdue au redémarrage ne laisse aucune ligne, ce qui est cohérent avec « rien n'a eu lieu ».
- **Fatigue d'interface** : le tableau vit dans un onglet existant ; le Centre de confiance gagne une liste courte et un bouton.

## 9. Ce que la V4 retire ou reporte, et pourquoi

| Élément de la V3 | Sort | Motif |
|---|---|---|
| Relevé « l'interrupteur web survit à la purge » | retiré | B-1505 l'a fermé |
| « La purge remet les retraits au défaut », avec le motif « les domaines sont vides » | remplacé : la purge garde les protections | le motif était faux (les connecteurs survivent) ; rouvrir un accès fermé n'est pas une remise à zéro |
| Attendu de `test_la_purge_remet_l_interrupteur_a_son_etat_par_defaut` (B-1505) | changé | l'interrupteur web est une protection, gardée comme les autres ; l'alignement du cache, objet de B-1505, reste testé |
| Critère « effet hors de la machine » contredit par sa table | tenu : quatre natures de facture sortent de la trace | une écriture locale confirmée n'est pas une sortie |
| Sentinelle sur `requestExternalAction(`, `setConfirmationSnapshot(`, `setConfirming(true)` | remplacée par les portes d'écran | trois confirmations lui échappaient ; les portes ne dépendent pas du nom d'un setter |
| « transmet cet objet, et rien d'autre » avec le fil joint | tenu : le fil n'est pas joint quand E-mails est retiré | la règle écrite était fausse |
| Test `POST /api/email/send` | remplacé par `POST /api/email/messages` | route inexistante, vert par construction |
| Test « limite connue, figée » | retiré ; limite consignée dans `SECURITY.md` | un test ne doit pas exiger qu'une faille reste ouverte |
| « `httpx` : 18 modules » | corrigé : 18 au premier niveau, 24 en tout | les imports dans les fonctions comptent |
| Chaîne de repli calculée dans la route | calculée dans `asyncio.to_thread` | elle lit la base et Ollama de façon synchrone |
| Fonction des types de mémoire « créée par le premier lot livré » avec son point d'accroche dans P-106 | citée : P-106 V4 la crée | l'amendement est fait dans P-106 V4 |
| Lot 5 conditionné à la question 3 | lot 5 livré par domaine | le domaine est le socle de tout retrait ; un retrait par outil s'y ajouterait sans rien défaire |
| Identité des préréglages au lot 5 | avancée au lot 2 | l'inventaire et le lot 2b en ont besoin |

Ce que la V2 et la V3 faisaient bien est gardé : le condensat HMAC et sa sentinelle, les deux colonnes effet et validation, les résolveurs calculés, la chaîne de repli tirée du code même du disjoncteur, le jeton de pont qui suit `TOOL_ROUTES` couple par couple et la vie de la session, la règle des gestes explicites, le tableau texte comme vue qui fait foi, la greffe sur P-118, l'export Mermaid puis BPMN, l'absence de migration.

## 10. Livraison

Ordre : lot 1, lot 2, lot 3, lot 4, lot 2b (dès que le lot 1 de P-106 est livré), lot 5, lot 6, lot 7a, lot 7b. Dépendances : le 3 dépend du 2 ; le 2b du 2 et du lot 1 de P-106 ; le 4 du 2 ; le 5 du 4 ; le 6 du 1 ; les 7a et 7b du 2. La chaîne de repli est extraite par le premier livré du lot 1 de P-106 ou du lot 2 de P-107 ; la fonction des types de mémoire par le premier livré du lot 1 de P-106 ou du lot 5 de P-107. Revue de conception à chaque lot, revue du diff à chaque lot. Aucune release sans le GO de Ludo.

## 11. Questions réservées à Ludo

1. **Le reste du journal d'activité.** Création, modification et suppression de fiches, clés d'API, exports : ces lignes sont gardées sans limite et survivent à « Effacer toutes mes données » (`routers/data.py:700`). Les effacer, c'est supprimer définitivement des données sur les machines des utilisateurs. **Option A**, 12 mois et effacées par la purge, sauf la ligne qui date la purge (date seule) : « toutes mes données » devient vrai, et l'historique de plus d'un an disparaît. **Option B**, statu quo : le journal grossit sans fin et la note de purge doit continuer de dire qu'il est gardé. **Recommandation** : A.
2. **L'export BPMN dans la communication publique** (page d'accueil, Discord). **Option A**, en parler dès le lot 7a : Dr_logic et d'autres essaieront un Mermaid avant le BPMN. **Option B**, attendre la recette du lot 7b et le retour de Dr_logic. **Recommandation** : B.
3. **La décision 13, par domaine plutôt que par outil.** Tu as validé « retirer un outil… partout » (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md:48-49`), et la V1 prévoyait un réglage par outil de lecture et par serveur MCP. La V4 retire par domaine : on ne peut pas garder la lecture des mails en retirant l'envoi. Motif : les agents d'action ne connaissent que des sources par domaine (`email`, `calendar`, `crm`…), et le pont que des routes ; un retrait par outil ne vaudrait « partout » qu'en inventant une correspondance dans chacun, et l'écran dirait deux choses selon l'endroit. L'envoi reste de toute façon sous carte. **Option A**, domaine seul (ce que livre le lot 5). **Option B**, domaine plus un état « lecture seule » par domaine : les écritures (`send_email`, `create_calendar_event`, `create_contact`, `create_project`) quittent la conversation, les lectures restent, agents et pont inchangés puisqu'ils ne font que lire ; un lot court après le lot 5, un réglage de plus à l'écran. **Option C**, outil par outil : une table de correspondance outil vers source d'agent et route du pont, à tenir à jour, et un écran plus long. **Recommandation** : A maintenant, B seulement sur une demande exprimée.

## Annexe : appuis dans le code (à `d0f7ab26`)

- Mémoire injectée : `routers/chat.py:745-878`, appels `:1740`, `:2398` ; filtre par type `services/qdrant.py:235-270`, `:577-592` ; types écrits `routers/memory.py:252`, `:281`, `services/indexation.py:167`, `services/memory_tools.py:699`, `:866`, `services/user_profile.py:450`.
- Liste d'outils : `routers/chat.py:2533-2568` ; portillon `services/tool_confirmations.py:33-49` ; mise en attente `routers/chat.py:3154-3173` ; confirmation `:3557-3623`.
- Disjoncteur : `services/llm.py:488`, `:749-811`, `:813-871` ; Ollama `:312-345` ; accords `lib/consent.ts:26-42`.
- Pont : `routers/agents.py:1323-1400`, `:1455-1480`, `:1557-1591` ; `services/mcp_therese_server.py:240-281`, `:323-340` ; jeton de session `main.py:418-426`, `:715-726`, `:756-814`.
- Agents d'action : `services/action_agents.py:253-537` ; `agents/action_agents.json`.
- Compétences : `routers/skills.py:63-238` ; `services/skills/text_skills.py:64-75`, `:228-232`.
- Réponse proposée : `routers/email.py:1853-1932` ; `services/email_response_generator.py:124-211`.
- Commandes : `services/slash_commands.py:36`, `:65`, `:161-330` ; `routers/chat.py:1469`, `:1544-1550`.
- Connecteurs : `routers/mcp.py:94-135`, `:224-265`, `:306-529`, `:604-690` ; `services/mcp_service.py:297-330`, `:397-420`, `:843-930`.
- Fiche : `services/memory_tools.py:959-1214`.
- Purge et restauration : `routers/data.py:552-564`, `:634-823`, `:1533-1837`.
- Caches du processus : `services/user_profile.py:683-694` ; `services/llm.py:247-290` ; `services/web_search.py:72-97` ; `services/cloisonnement.py:28-48` ; `main.py:118-160`.
- Confirmations d'écran : `components/app/useExternalActionConfirmation.ts:19-34`, `components/app/ExternalActionConfirmation.tsx:24-138`, et les seize fichiers du §4.6.
- Centre de confiance : `components/prototype/CapabilityCenter.tsx:500-595`.
- Dérivation de clé : `services/encryption.py:470-485`.
