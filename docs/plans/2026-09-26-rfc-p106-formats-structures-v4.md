# RFC P-106 (V4) : lire des cartes mentales, des graphes, des processus et des plannings, puis tenir une carte à jour

Rédigé le 26/09/2026. Remplace la V3 (`docs/plans/2026-09-26-rfc-p106-formats-structures-v3.md`), refusée (NO-GO) par la revue adverse du 26/09 (constats 14 à 21, dont un P1 ; rapport de travail « revue-v3-p105-p106.md » de l'orchestrateur, hors dépôt). Les décisions du 25/09/2026 (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md`, points 7 à 9) restent des faits. Les réponses aux revues de la V1 (V2, section 7) et de la V2 (V3, section 0) restent valables ; la section 0 bis dit où en est chacune au code. La V4 s'aligne sur la V3 de P-107 (`docs/plans/2026-09-26-rfc-p107-perimetre-bpmn-v3.md`, §4.3 et §4.8.2) : une seule fonction dit quels types de mémoire partent, une seule extraction dit la chaîne de repli.

**Base de vérification.** Toutes les lignes citées ont été relues à `2d49d8d5` (HEAD du 26/09/2026 au début de la rédaction), avec `git show 2d49d8d5:<fichier>`, jamais dans l'arbre de travail. Cinq commits sont arrivés pendant la rédaction (`62639261` à `06607577` : B-1506, B-1522, B-1523, B-1524 et un réglage de CI) ; ils ne déplacent aucune ligne citée ici (`routers/data.py` ne change qu'après sa ligne 1257). Depuis la base de la V3 (`6f927313`), B-1489, B-1502, B-1513, B-1514 et B-1521 ont déplacé des lignes de `routers/chat.py`, `services/llm.py` et `components/chat/ChatInput.tsx` : toutes les citations ont été rebasées. Chemins relatifs à `src/backend/app/` (fichiers `.py`) et à `src/frontend/src/` (fichiers `.ts` et `.tsx`) ; les tests, `docs/`, `.github/`, `uv.lock` et `pyproject.toml` partent de la racine du dépôt. Vérification mécanique : chaque citation a été imprimée à la base par un script et relue ; les seuls fichiers cités absents sont les fixtures et tests à créer.

Aucun code avant la validation de ce document.

## 0. Constats de la revue V3 et leur traitement

« Fermé au code » veut dire : un commit est sur main et un test nommé le prouve à la base relue. « Design, lot N » veut dire : la réponse est écrite ici, et son test est à écrire en premier au lot N.

| # | Grav. | Constat de la revue V3 | Traitement | État | Où |
|---|---|---|---|---|---|
| 14 | P1 | `/fichier` et `/analyse`, quatrième voie : un fichier local entier part sous le seul accord `llm` | **Accepté.** Relu : motif `routers/chat.py:213-216`, lecture `:219-234`, appel sans flux `:1761-1772` (sous la garde `produce_prompt`) et en flux `:2421-2434` (sous `allow_file_commands`), vers `_get_file_context`, qui rend jusqu'à 15 000 caractères (`:413`). Ces chemins ne sont pas consignés comme pièces jointes (`:1317` ne consigne que `request.file_paths`) : ni rejeu, ni marque « documents » sur la conversation. **Moitié composeur fermée au code** par B-1521 (`2d49d8d5`, `components/chat/ChatInput.tsx:568-575`). **Moitié serveur** : les points 4 et 7 de 6.1 s'appliquent aux chemins que rend `_parse_file_commands` sur le texte que le moteur lit réellement. Relevé en relisant : ce texte est celui d'**après** la substitution des variables (`routers/chat.py:1637-1646`, transmis à `:1692`), alors que le composeur teste le texte brut ; candidat D-1 (section 2), que la garde serveur couvre sans l'attendre | composeur : fermé au code (`2d49d8d5`, `components/chat/ChatInput.commandeFichier.b1521.test.tsx`) ; serveur : design, lot 1 | 2 ; 6.1 ; lot 1 |
| 15 | P2 | L'image jointe part chez le secours sans accord « documents » pour lui | **Accepté.** Relu : `separer_images_et_documents` (`routers/chat.py:501-517`) écarte l'image de l'extraction, `_attacher_images` la pose sur le dernier message (`:520-535`, `:534`), aux deux chemins (`:1777-1781`, `:2438-2440`). Seule l'image **du tour courant** part : une image d'un tour précédent est rejouée par `_pieces_jointes_recentes` puis passée à l'extraction (`:1795-1805`, `:2458-2469`), jamais reposée sur le message. Les points 4 et 7 couvrent l'image du tour | design, lot 1 | 6.1 ; lot 1 |
| 16 | P2 | Liste de types en dur et `config_du_tour()` seule, contre la fonction unique et l'extraction unique de P-107 | **Accepté.** Le lot 1 crée `types_de_memoire_permis(documents_permis, domaines_retires=())`, avec sa table et la sentinelle que P-107 nomme ; la liste en dur disparaît. Précision au code : **six** sites écrivent un type dans l'index, pas quatre (`routers/memory.py:252`, `:281`, `services/indexation.py:167`, `services/memory_tools.py:698`, `:865`, `services/user_profile.py:450`) ; la sentinelle les lit tous. Le lot 1 extrait aussi `chaine_de_repli()` de `_resolve_with_circuit_breaker` (`services/llm.py:806-864`), d'où sortent `config_du_tour()` et, pour P-107, la vue. Le premier des deux lots livrés (lot 1 de P-106, lots 2 ou 5 de P-107) crée ; l'autre réutilise | design, lot 1 | 6.1 ; lot 1 |
| 17 | P3 | La synchronisation d'un dossier est un sixième appelant, dont le scanner ne filtre que l'extension | **Accepté.** Relu : `services/project_sync.py:101` (extension), `:112` (taille) ; échec d'une opération consigné avec `str(e)` (`services/project_sync_service.py:459-463`), seul le 404 étant traité à part (`:574-584`) ; `services/path_security.py:257-260` exige déjà que le scanner applique la même règle que l'indexation. Le scanner applique le contrôle d'en-tête et range le fichier parmi les refusés, comme il range les instables (`services/project_sync.py:60`, `:68`, `:128`) ; à l'application, un refus de format devient « obsolète » avec la phrase, comme un fichier disparu | design, lot 2 | 6.2 ; lot 2 |
| 18 | P3 | `documents_accordes_pour` calculé par `hasCloudConsent` seul, alors que la garde accepte aussi l'accord de session | **Accepté.** Même prédicat que la garde (`components/chat/ChatInput.tsx:579-583`), accord de session lu d'abord, lecture du stockage protégée | design, lot 1 | 6.1 ; lot 1 |
| 19 | P3 | La consigne au modèle renvoie à un bouton qui n'apparaît qu'une fois | **Accepté.** La ligne reste visible tant que l'accord manque (annoncée une seule fois aux lecteurs d'écran), et la consigne nomme aussi l'autre chemin réel : joindre le fichier au message, qui demande l'accord | design, lot 1 | 6.1 ; lot 1 |
| 20 | P3 | Périmé : B-1489 et B-1502 sont livrés | **Accepté.** Sections 2, 5, 6.1 et 9 mises à jour. Le test « outil non offert appelé quand même » devient une garde de non-régression. `config=` alimente `context.config_effective` (`services/llm.py:973-975`), que la continuation reprend (`:1066-1067`) : imposer la configuration au premier appel la fait tenir tout le tour | B-1489 : fermé au code (`d15ef8bd`, `tests/test_b1489_outil_non_offert.py`) ; B-1502 : fermé au code (`f085e226`, `tests/test_b1502_suite_des_outils_meme_fournisseur.py`) | 2 ; 5 ; 6.1 |
| 21 | P3 | La table ne distingue pas le code du design | **Accepté.** Colonne « État » ci-dessus et en 0 bis | fermé au document | 0 ; 0 bis |

## 0 bis. Constats de la revue V2 : où en est chacun au code

| # | Constat de la revue V2 | État à `2d49d8d5` |
|---|---|---|
| 18 (P1) | Le contenu des fichiers part sous le seul accord `llm` | Design, lot 1, étendu à cinq voies (constats 14 et 15 ci-dessus). Fermé au code pour la seule moitié composeur de `/fichier` (B-1521) |
| 19 | Un outil retiré reste exécutable | **Fermé au code** (B-1489, `d15ef8bd`, `routers/chat.py:3106-3140`, `tests/test_b1489_outil_non_offert.py`) |
| 20 | Le disjoncteur bascule après l'offre des outils | **Fermé au code** pour la continuation (B-1502, `f085e226`, `services/llm.py:1063-1072`, `tests/test_b1502_suite_des_outils_meme_fournisseur.py`). Résolution unique, destination consentie et bascule refusée : design, lot 1 |
| 21 | Refus après l'écriture de la métadonnée | Design, lots 2 et 4 |
| 22 | Cloison de l'outil de carte | Design, lot 5 |
| 23 | Modifications successives | Design, lot 5 |
| 24 | Formules Freeplane | Design, lot 5 |
| 25 | « Octet pour octet » | Design, lot 5 |
| 26 | `noter` | Design, lot 5 |
| 27 | Identifiants de nœuds dans l'index | Design, lot 2 |
| 28 | Exception dérivée de `ValueError` | Design, lot 2 (sept appelants, constat 17) |
| 29 | Création réelle sur le job Windows | Design, lot 5 |
| 30 | Plannings déjà indexés | Design, lot 4 |

## 1. Ce que la V4 change

- **Le P1 est fermé en design sur cinq voies**, pas trois : outils, contexte mémoire, pièces jointes (nouvelles et rejouées), commandes `/fichier` et `/analyse`, image du tour. Aucun contenu de fichier ne part vers un service en ligne sans l'accord « documents » donné pour ce service, même quand le disjoncteur change de fournisseur, et même quand une variable apporte la commande.
- Une seule fonction dit quels types de mémoire partent, une seule extraction dit la chaîne de repli, partagées avec P-107.
- Le refus d'un fichier dangereux a lieu avant toute écriture, et dit sa raison sur sept chemins, synchronisation comprise.
- L'accord manquant reste visible tant qu'il manque, et le serveur lit l'accord comme l'écran le lit.
- Le reste de la V3 est gardé : ordre des lots (décision 7), parseur durci, formats lus, copie dans un dossier de THÉRÈSE (décision 9), export différé.

## 2. Prérequis

| Nom | Nature | État à la base relue | Bloque |
|---|---|---|---|
| **B-1489** | Un outil non offert au tour s'exécutait | **Fermé au code** (`d15ef8bd`, `tests/test_b1489_outil_non_offert.py`) : `routers/chat.py:3106-3140` | rien : le lot 1 garde un test de non-régression |
| **B-1502** | La suite d'un tour d'outils repartait chez le principal | **Fermé au code** (`f085e226`, `tests/test_b1502_suite_des_outils_meme_fournisseur.py`) : `services/llm.py:1063-1072`, `services/context.py:21-24` | rien |
| **B-1521** | `/fichier` et `/analyse` ne demandaient que l'accord `llm` au composeur | **Fermé au code côté composeur** (`2d49d8d5`, `components/chat/ChatInput.commandeFichier.b1521.test.tsx`) ; le moteur ne vérifie toujours rien | rien : la garde serveur est le lot 1 |
| **D-1** (candidat à reproduire, hors RFC) | Une variable dont la valeur commence une ligne par `/fichier <chemin>` fait lire ce fichier après substitution, sans que le composeur demande l'accord « documents » | Preuves ci-dessous | rien : le lot 1 lit le même texte que le moteur |
| **D-2** (candidat à reproduire, hors RFC) | Sur le chemin sans flux, la panne du fournisseur de repli est comptée au fournisseur principal | Preuves ci-dessous | rien ; le lot 1 ne l'aggrave pas (point 8) |

**D-1, preuves.** La substitution a lieu « sur le SEUL texte destiné au LLM, APRÈS tous les parseurs déterministes » (`routers/chat.py:1631-1646`) et promet que les valeurs ne sont jamais re-scannées (`services/variables_service.py:297-299`) ; or la lecture des commandes de fichier vient après, sur ce texte substitué : `_parse_file_commands(llm_user_message)` sans flux (`routers/chat.py:1761-1763`), et `_stream_response` reçoit le texte substitué (`:1691-1692`) qu'il lit à `:2421`. Le composeur, lui, teste le texte tapé (`components/chat/ChatInput.tsx:571`) : un message `{mon_dossier}` dont la valeur est `/fichier /Users/moi/devis.pdf` lit le fichier et l'envoie sans que la question « documents » soit posée. Correction recommandée pour le ticket : lire les commandes de fichier sur le texte d'avant la substitution (`detection_message`, `routers/chat.py:1636`), comme la détection de compétence. P-106 ne l'attend pas : la garde du lot 1 s'appuie sur le résultat même de `_parse_file_commands` que le moteur utilise.

**D-2, preuves.** `stream_response` n'a pas de configuration propre (`services/llm.py:904-911`, `:928`) ; avec `raise_on_error`, il compte une panne sur `self.config.provider` (`:939-942`), c'est-à-dire le principal, même quand le disjoncteur a basculé ; la comptabilité de `stream_response_with_tools`, qui viserait le bon fournisseur (`:1035-1036`), est court-circuitée par la levée (`:931-950`). Le secours en panne ne voit jamais son circuit s'ouvrir depuis le chat sans flux (`routers/chat.py:1857`).

## 3. Le besoin

Dr_logic-3D, testeur alpha, sur Discord (#discussion et fil du 25/09, 03:35 à 04:29) :

- Il tient ses sujets dans des représentations structurées : cartes mentales Freeplane (`.mm`), graphes yEd (`.graphml`), processus BPMN, plannings Gantt.
- À chaque évolution d'un sujet, il met ces fichiers à jour à la main.
- Il voudrait que THÉRÈSE les lise et les tienne à jour, plutôt que de tout recopier dans le chat.

## 4. Décisions du 25/09/2026 (tranchées)

7. **Lecture d'abord.** On commence par lire les fichiers de Dr_logic ; l'export Mermaid et GraphML du planning attend la saisie des durées et des dépendances (suite de P-039).
8. **Accord « documents » exigé dès qu'un outil de lecture de fichier est offert à un modèle en ligne.**
9. **La copie d'une carte modifiée est rangée dans un dossier de THÉRÈSE**, jamais à côté de l'originale.

La V4 lit la décision 8 dans son esprit : l'outil n'est qu'une des cinq voies par lesquelles le contenu d'un fichier atteint le modèle. Les quatre autres sont soumises au même accord. Ce n'est pas une décision nouvelle : c'est la seule lecture qui rende vraie la phrase promise à l'utilisateur.

## 5. État du code à la base relue

Les points d'appui de la V2 (section 4) et de la V3 (section 5) restent justes, lignes rebasées ; seuls ceux qui changent ou s'ajoutent sont repris ici.

- **Cinq voies du contenu d'un fichier vers le modèle, dans le chat.**
  1. **Outils** : `MEMORY_TOOLS` (`services/memory_tools.py:228-234`) est ajouté à chaque tour outillé (`routers/chat.py:2547`) ; `read_file` enveloppe son contenu (`services/memory_tools.py:1620-1628`). Le chemin sans flux n'offre aucun outil (`routers/chat.py:1857`).
  2. **Contexte mémoire** : `_get_memory_context` (`routers/chat.py:745`) cherche sans filtre de type (`:769-784`), injecte chaque fragment `file` avec le nom du fichier (`:804-818`) et tout type inconnu tel quel (`:819-820`). Il est appelé par les deux chemins (`:1740-1742` sans flux, `:2398-2400` en flux) dès que `include_memory` est vrai, sa valeur par défaut (`models/schemas.py:110`), que `ChatInput` pose explicitement (`components/chat/ChatInput.tsx:718`). La phrase D6 sur les documents hors périmètre y est ajoutée sans condition d'accord (`routers/chat.py:856-878`).
  3. **Pièces jointes** : extraites (`routers/chat.py:333`), enveloppées (`:423-427`), rejouées d'un tour à l'autre (`:570-625`), ajoutées au contexte (`:1808-1824` et `:2487-2500`), avec la consigne `BLOC_PIECES_JOINTES` (`:2621-2622`).
  4. **Commandes `/fichier` et `/analyse`** : motif `routers/chat.py:213-216`, lecture `:219-234`, appels `:1761-1772` et `:2421-2434`, sur le texte d'après substitution (D-1). Non consignées (`:1317`), donc jamais rejouées.
  5. **Image du tour** : `routers/chat.py:1777-1781` et `:2438-2440`, posée sur le dernier message (`:534`).
- **Filtre par type.** `async_search` accepte `memory_types` (`services/qdrant.py:577-592`), appliqué en filtre de la requête (`services/qdrant.py:264-272`) **seulement s'il n'est pas vide** : une liste vide vaut « aucun filtre ». Types écrits à la base : `contact`, `project`, `file`, `owner`, sur six sites (`routers/memory.py:252`, `:281`, `services/indexation.py:167`, `services/memory_tools.py:698`, `:865`, `services/user_profile.py:450`).
- **Consentement.** Un accord par finalité et par destination (`lib/consent.ts:40-42`), rangé dans le stockage du navigateur, lu sans protection (`lib/consent.ts:44-47`, `:82-88`) ; le composeur garde aussi l'accord donné dans la session (`components/chat/ChatInput.tsx:234-240`, `:1038-1039`) et le lit **avant** le stockage (`:579-583`). La destination est le fournisseur, ou « ollama-cloud », ou rien pour un modèle local (`lib/ollamaCloud.ts:19-23`). Le serveur sait reconnaître un modèle Ollama en ligne (`services/ollama_capabilites.py:86-90`) mais ne connaît aucun accord. Les accords « documents » ne se donnent qu'au composeur (`components/chat/ChatInput.tsx:1033`) ; Paramètres les liste et les retire (`components/settings/PrivacyTab.tsx:106`).
- **Disjoncteur.** Le chat utilise le service partagé, qui bascule par défaut (`services/llm.py:488`, `:500`) vers le premier fournisseur disponible d'une liste ordonnée (`services/llm.py:742-804`, ordre `:755-758`, Ollama local en dernier recours `:795-802`), sauf si la bascule est refusée (`:824-830`) ou depuis un fournisseur local (B-1071, `:835-841`) ; sans repli disponible, le principal est tenté (`:858-864`). La résolution a lieu dans l'appel de flux (`:973`), qui accepte une configuration imposée (`:962`) et la range dans `context.config_effective` (`:975`) ; la continuation après outils la reprend (B-1502, `:1066-1067`). `stream_response` n'accepte pas de configuration (`:904-911`) et compte ses pannes sur le principal (D-2).
- **Ordre d'écriture de l'indexation.** Validation (`services/indexation.py:249-256`, seuls `PermissionError`, `FileNotFoundError` et `ValueError` attrapés), métadonnée commitée (`:554`), puis extraction (`:583`). En synchronisation, l'extraction lit une copie dont l'empreinte a été vérifiée contre le plan (`:357-387`, `:399-421`). `read_file` ne lit que les fichiers à fragments (`services/memory_tools.py:1536-1543`) et rend une phrase générique sur toute exception d'extraction (`:1581-1600`).
- **Sept points d'entrée de l'extraction ou de la validation** : `services/indexation.py:250` (validation), `:583` (indexation), `routers/chat.py:333` (pièce jointe et commande de fichier, par `_get_file_context`), `routers/files.py:406` (contenu d'un fichier : `ValueError` devient 413, `:410-412`, toute autre exception 500, `:413-415`), `services/memory_tools.py:1584` (`read_file`), le scanner de synchronisation (`services/project_sync.py:79`, filtre `:101`) et l'application d'un plan (`services/project_sync_service.py:554-584`).
- **Sorties.** Dossier `outputs` (`services/skills/registry.py:32`), téléchargement par identifiant qui cherche `*_<8 caractères>.*` à la racine (`routers/skills.py:266-267`).
- **L'Atelier a son propre `read_file`** (`services/agents/runtime.py:196-197`) : hors du chat, dans le périmètre de P-107.

## 6. Conception V4

### 6.1 Aucun contenu de fichier en ligne sans l'accord « documents » (décision 8)

**Principe.** Dans le chat, le contenu d'un fichier, par l'une des cinq voies, ne part vers un service en ligne que si l'accord « documents » a été donné **pour ce service-là**, celui qui recevra réellement le tour.

**Ce que l'écran transmet** (constat 18). `ChatRequest` (`models/schemas.py:105-119`) gagne `documents_accordes_pour: str | None = None`. `ChatInput` le calcule par une fonction `accordDocumentsPour(destination)`, **avec le même prédicat que sa garde** (`components/chat/ChatInput.tsx:579-583`) : la destination (`fournisseurDAccord`, `lib/ollamaCloud.ts:19-23`) si `cloudConsentGrantedRef.current === 'documents:' + destination`, lu d'abord, ou si `hasCloudConsent('documents', destination)` ; sinon rien. Si la lecture du stockage lève, le champ vaut rien et l'envoi continue. La valeur par défaut ferme : un appelant qui ne transmet rien n'ouvre rien.

**Ce que le serveur décide, une fois par tour, avant de construire quoi que ce soit.**

1. **Chaîne de repli, extraction unique** (constat 16). `LLMService` gagne `chaine_de_repli()`, extraite de `_resolve_with_circuit_breaker` (`services/llm.py:806-864`) sans en changer les règles : le principal, puis, si la bascule est permise (`:824`) et que le principal n'est pas Ollama (`:835`), les replis de `_get_fallback_configs` dans leur ordre (`:742-804`). `config_du_tour()` rend le premier élément disponible au disjoncteur, sinon le principal (`:858-864`). `_resolve_with_circuit_breaker` devient `return self.config_du_tour()` ; P-107 tire de `chaine_de_repli()` la vue qui décrit la bascule. Qui livre en premier crée, l'autre réutilise.
2. **Destination d'accord.** Une fonction serveur `destination_d_accord(config)`, miroir de `lib/ollamaCloud.ts:19-23` : rien pour Ollama local, « ollama-cloud » pour un modèle Ollama en ligne (`est_modele_ollama_cloud`), le nom du fournisseur sinon. Un test confronte les deux implémentations sur la même table de cas.
3. `documents_permis = destination is None or destination == request.documents_accordes_pour`.
4. **Le tour porte-t-il du contenu de fichier, hors mémoire ?** Calculé une fois, avant le contexte, et réutilisé ensuite pour lire les fichiers (les deux ne peuvent pas diverger) : un chemin dans `request.file_paths` (document **ou image**, constat 15), une pièce jointe rejouée qui est un document (la liste de `_pieces_jointes_recentes` passée par `separer_images_et_documents` : une image rejouée part à l'extraction et n'atteint jamais le modèle, compter son chemin refuserait une bascule pour rien), ou une commande reconnue par `_parse_file_commands` sur le texte que le moteur lit (constat 14), sous les mêmes gardes `produce_prompt` et `allow_file_commands`.
5. **Bascule.** Si `documents_permis` est faux **et** que le principal (`llm_service.config`) aurait été permis, c'est la bascule qui a changé la destination. Alors :
   - si le tour porte du contenu de fichier (point 4) : **la bascule est refusée pour ce tour**, le principal est imposé, et une panne réelle remonte comme quand la bascule est interdite. Répondre sur un document sans le document serait faux ; l'envoyer au secours serait une fuite ;
   - sinon, le tour part chez le secours, sans aucun contenu de fichier (points 6 et 7).
6. **Outils** : si `documents_permis` est faux, `search_files` et `read_file` sont retirés de `tools` après leur ajout (`routers/chat.py:2547`). Le bloc des capacités, construit sur `tool_names` (`:2568`, `:2598-2601`), cesse de les promettre, et une phrase les remplace : « Les fichiers indexés ne sont pas consultables ici : l'accord pour envoyer des documents à ce service n'est pas donné. Si on te les demande, dis-le, dis où se trouve le lien « Autoriser » sous le composeur, et qu'on peut aussi joindre le fichier au message. »
7. **Contexte mémoire** (constat 16) : `_get_memory_context` gagne `types_permis: list[str]`, calculé **à chaque tour** par `types_de_memoire_permis(documents_permis)` et passé à `async_search(memory_types=...)`. La fonction part de sa table (`contact` : mémoire ; `project` : mémoire ; `file` : document ; `owner` : profil), retire `file` si `documents_permis` est faux (et, pour P-107, les types des domaines retirés), et rend une **liste blanche** : un type absent de la table n'est jamais transmis. Le filtre est posé en amont, dans la requête : filtrer après coup laisserait des fragments de fichiers consommer les huit résultats (`limit=8`). Une liste vide n'est jamais passée (elle vaudrait « aucun filtre », `services/qdrant.py:264`) : la recherche n'a alors pas lieu. Quand `file` n'est pas permis, la phrase D6 (`routers/chat.py:856-878`) n'est pas émise, comme le prévoit P-107 : elle parlerait de documents que la conversation ne consulte pas. `include_memory=false` (B-1495) garde sa priorité : aucune mémoire du tout.
8. **Tour refusé** : si `documents_permis` est faux, que la bascule n'est pas en cause, et que le tour porte du contenu de fichier (point 4), le tour est refusé avec la phrase « L'accord pour envoyer des documents à ce service n'est pas donné. » Rien n'est envoyé. Cas atteints : requête forgée, composeur contourné par une variable (D-1), mini-chat RFC qui porte une ligne `/fichier` (`components/rfc/RFCChat.tsx:97-101` ne transmet pas le champ).
9. **Configuration imposée** : `stream_response_with_tools(context, tools, config=config_du_tour)` (paramètre existant, `services/llm.py:962`), et `stream_response` gagne le même paramètre, transmis tel quel ; sa comptabilité de panne (`:939-942`) vise alors le fournisseur de la configuration imposée, pour ne pas étendre D-2. La configuration imposée alimente `context.config_effective` (`:973-975`), que la continuation reprend (`:1066-1067`) : le disjoncteur ne résout qu'une fois pour tout le tour, outils compris.

**Exécution.** B-1489 refuse tout outil absent de la liste du tour (`routers/chat.py:3132-3140`) : un modèle qui rappelle `read_file` vu plus tôt ne le fait pas exécuter.

**Côté écran** (constat 19).

- `ChatInput` transmet `documents_accordes_pour` à chaque envoi.
- Les pièces jointes et les commandes de fichier gardent leur règle actuelle (accord « documents » demandé, `components/chat/ChatInput.tsx:572-603`).
- Tant que la destination est en ligne et que l'accord « documents » pour elle manque, une ligne discrète **reste** sous le composeur : « Tes fichiers ne sont pas lus par ce service. Autoriser ». Elle n'est annoncée aux lecteurs d'écran qu'à sa première apparition dans la conversation. Le lien ouvre la boîte d'accord existante avec la finalité `documents`. Motif de la persistance : la consigne au modèle y renvoie, et c'est, avec la pièce jointe, le seul endroit où cet accord se donne (Paramètres ne fait que le retirer).

**La phrase du Centre de confiance.** Dans `phrasesDeLEtat` (`components/prototype/CapabilityCenter.tsx:500`) : « Dans le chat, le contenu de tes fichiers ne part vers un service en ligne que si tu l'as autorisé pour ce service. » Elle n'est vraie qu'avec quatre conditions, chacune testée au lot 1 : outils non offerts (point 6), outils non exécutés (B-1489), aucun fragment de fichier, aucune pièce jointe, aucune commande de fichier ni image (points 7 et 8), fournisseur effectif égal à la destination consentie (points 3, 5 et 9). Elle est bornée au chat : l'Atelier appartient à P-107. Elle est écrite dans le dernier commit du lot 1, après les tests.

**Pourquoi cette forme plutôt qu'exiger l'accord « documents » à chaque message.** Inchangé : bloquer toute conversation en ligne de qui refuse l'envoi de ses documents serait disproportionné, et ne pas offrir les documents sans accord respecte la décision.

### 6.2 Un parseur XML durci, et un refus qui précède toute écriture

- `lxml` devient une dépendance directe (`pyproject.toml`), à la version déjà verrouillée (`uv.lock:1406`). Réglage unique : `XMLParser(resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False)`.
- **Tout fichier structuré qui déclare un `DOCTYPE` est refusé** (`.mm`, `.graphml`, `.bpmn`, `.gan`, et un `.xml` reconnu comme MS Project), sans que rien de ce qu'il désigne soit lu. Si un fichier témoin réel en portait un, le lot s'arrête et le design est rouvert.
- Plafonds : 5 000 éléments utiles, 64 niveaux ; au-delà, l'extraction s'arrête et le dit dans le texte.

**Une exception à part.** `FormatStructureRefuse(Exception)`, **non dérivée de `ValueError`** : la route de contenu traduit toute `ValueError` en « trop volumineux » (`routers/files.py:410-412`), et l'indexation en 400 générique (`services/indexation.py:255-256`). Elle porte la phrase de refus (« ce fichier déclare un type de document, refusé par sécurité »).

**Le contrôle avant l'écriture.** `controler_en_tete(chemin)`, appelé par `validate_indexable_file` (`services/path_security.py:286`), lit l'en-tête du fichier (4 kilo-octets, en texte) : pour une extension structurée, ou un `.xml` dont l'élément racine porte l'espace de noms MS Project, la présence d'un `DOCTYPE` lève `FormatStructureRefuse`. Ce contrôle a lieu avant la métadonnée commitée (`services/indexation.py:554`) : un fichier refusé ne laisse **aucune ligne** à zéro fragment. Le scanner de synchronisation appelle la même fonction, comme `services/path_security.py:257-260` l'exige déjà pour la taille.

**Les sept points d'entrée, un par un** (constat 17).

| Point d'entrée | Ce que voit l'utilisateur |
|---|---|
| `services/indexation.py:250` (validation) | nouvelle branche `except FormatStructureRefuse` : 422 avec la phrase, levée `from` l'exception d'origine ; l'écran d'indexation l'affiche telle quelle |
| `services/indexation.py:583` (extraction) | le fichier a changé entre validation et extraction : la ligne neuve est supprimée ; en réindexation, l'index existant reste intact ; 422 avec la phrase |
| `routers/chat.py:333` (pièce jointe, commande de fichier) | la phrase rendue comme erreur de pièce jointe, par l'`except Exception` existant qui rend déjà un couple contexte, erreur (`routers/chat.py:441-443`) |
| `routers/files.py:406` (contenu d'un fichier) | branche placée **avant** `except ValueError` et `except Exception` : 422, avec la phrase |
| `services/memory_tools.py:1584` (`read_file`) | branche placée avant l'`except Exception` générique (`services/memory_tools.py:1585`) : la phrase rendue telle quelle au modèle |
| Scanner de synchronisation (`services/project_sync.py:101-116`) | après les filtres d'extension et de taille, `controler_en_tete` ; un fichier refusé n'entre pas au plan et rejoint `refuses`, un ensemble de `ResultatScan` à côté de `instables` (`services/project_sync.py:68`), compté dans le diff comme eux (`:60`) ; le plan dit « 1 fichier refusé par sécurité : carte.mm » |
| Application d'un plan (`services/project_sync_service.py:554-584`) | un 422 dont la cause est `FormatStructureRefuse` (le fichier a changé depuis le scan) est consigné `OBSOLETE` avec la phrase, comme un fichier disparu (`:578-583`), jamais en échec « 422: … » ; au plan suivant, le scanner le range parmi les refusés |

Le `.xml` ordinaire ne change pas : sans l'espace de noms MS Project dans ses 4 premiers kilo-octets, il reste lu en texte brut, `DOCTYPE` compris.

### 6.3 Ce que le modèle lit (lecture seule)

Inchangé. Chaque format donne un texte rangé pour tenir dans les 10 000 caractères de `read_file` (`services/memory_tools.py:1516`) : un résumé d'abord, puis le détail.

| Format | Reconnu par | Texte produit |
|---|---|---|
| Carte Freeplane (et FreeMind) | extension `.mm` | plan indenté ; notes en ligne, texte enrichi aplati ; **pour `read_file` seulement**, identifiant de chaque nœud entre crochets |
| Graphe yEd | extension `.graphml` | nœuds (libellé yFiles, sinon clés `label` ou `name`, sinon identifiant), puis arcs « A → B (libellé) » ; groupes rendus comme parents |
| Processus BPMN | extension `.bpmn` | par processus et participant : couloirs, étapes typées, flux avec condition |
| Planning MS Project (et exports ProjectLibre) | `.xml` dont l'élément racine porte l'espace de noms `http://schemas.microsoft.com/project` | tableau : tâche, début, fin, durée, avancement, prédécesseurs avec type et décalage |
| Planning GanttProject | extension `.gan` | même tableau |

**Identifiants de nœuds.** `extract_text` (`services/file_parser.py:75`) gagne `avec_identifiants: bool = False`, transmis par `extract_text_async`. Seul `read_file` passe `True` (`services/memory_tools.py:1584`). L'indexation (`services/indexation.py:583`), les pièces jointes (`routers/chat.py:333`) et la route de contenu (`routers/files.py:406`) reçoivent le texte sans crochets.

**Plannings déjà indexés.** Un `.xml` MS Project indexé avant le lot 4 garde ses fragments bruts jusqu'à sa prochaine indexation. `read_file` relit le disque (`services/memory_tools.py:1584`) : il donne la structure dès le lot 4. Réindexer d'office serait une écriture de fond, cliente de la mise au repos que P-105 attend aussi. Le lot 4 le dit dans les notes de version.

Choix tranchés de la V2 inchangés : les deux formats de planning sont lus, le `.mpp` binaire ne l'est pas ; le texte d'une carte arrive au modèle sous l'enveloppe des fichiers.

### 6.4 Tenir une carte Freeplane à jour, dans une copie

Inchangé par rapport à la V3, repris en entier.

**L'outil.** `proposer_modification_carte(fichier_id, operations, base)`, classé `MUTATION_LOCALE` dans `CLASSIFICATION_DES_OUTILS` (`services/contexte_execution.py:30`), donc sous carte (`services/tool_confirmations.py:33-49`). Il fait partie des outils de fichiers : retiré avec `search_files` et `read_file` quand `documents_permis` est faux (6.1, point 6).

**Cloison.** `fichier_id` est résolu par `_cloison_fichiers`, exactement comme `read_file` (`services/memory_tools.py:1536-1543`), à la proposition **et** à la confirmation : un identifiant inconnu, un fichier hors du périmètre et un fichier qui n'est pas un `.mm` reçoivent le même refus (`_REFUS_LECTURE`, `services/memory_tools.py:1510`).

**Liste fermée d'opérations** : `ajouter`, `renommer`, `deplacer`, `noter` ; aucune suppression, aucun attribut, icône, lien, style ni script ; un argument inattendu refuse toute la proposition ; 500 caractères par texte ; 50 opérations au plus ; avec trois précisions :

- **Formules** : tout texte d'opération dont le premier caractère non blanc est « = » est refusé, et toute la proposition avec lui. La vérification sur un témoin Freeplane 1.11 (lot 5) dira si d'autres formes existent.
- **`noter`** : ajoute un paragraphe `<p>` à la fin de la note `richcontent TYPE="NOTE"` existante, texte posé par l'arbre XML, donc échappé une fois ; sans note, elle est créée sous cette forme ; une note sous une autre forme : opération refusée.
- **Texte enrichi** : un nœud dont le texte est en `richcontent TYPE="NODE"` ne se renomme pas.

**La base : original ou dernière copie.**

- Chaque copie est nommée `<nom assaini>_modifiee_<AAAA-MM-JJ>_<HHhMM>_o<8 premiers caractères de l'identifiant de l'original>_<8 caractères>.mm`, à la racine d'`outputs`, pour rester téléchargeable par la route existante (`routers/skills.py:266-267`).
- Juste après la déclaration XML, la copie porte `<!-- therese-origine sha256=<empreinte> -->`, l'empreinte de l'original d'où part la chaîne.
- `base` vaut `"derniere_copie"` par défaut, ou `"original"`. Avec `"derniere_copie"`, l'outil prend la copie la plus récente qui porte `o<8 caractères>` de cet original **et** dont l'empreinte d'origine égale l'empreinte actuelle de l'original ; sinon il repart de l'original et le dit.
- La carte de confirmation dit toujours sa base : « À partir de ta copie du 26/09 à 14 h 05 (tes modifications précédentes comprises) », « À partir de ton original », ou « Ton original a changé depuis ta dernière copie : on repart de l'original, sans les modifications de la copie du 26/09 à 14 h 05 ».

**À la confirmation.**

1. La base est relue et son empreinte comparée à celle de la proposition ; si elle a changé, rien n'est écrit (« la carte a changé depuis la proposition, redemande-la »).
2. Les opérations sont appliquées à l'arbre de la base, relu par le parseur durci qui garde commentaires et espaces.
3. La copie est écrite dans `outputs`, d'un seul geste (fichier temporaire puis renommage), jamais à côté de l'originale (décision 9).
4. **Nom valide sous Windows**, vérifié par une fonction pure testée dans la CI principale : aucun caractère `<>:"/\|?*` ni caractère de contrôle, aucun nom réservé (`CON`, `PRN`, `AUX`, `NUL`, `COM1` à `COM9`, `LPT1` à `LPT9`, avec ou sans extension, quelle que soit la casse), pas de point ni d'espace final, 255 caractères au plus. Le job Windows (`.github/workflows/tests-windows.yml:3-4`) reste un complément.
5. La carte affiche « Copie enregistrée dans THÉRÈSE. Télécharger. Ton original n'a pas été modifié. » ; `.mm` entre dans la table de types du téléchargement (`routers/skills.py:273-281`).

**Ce que la copie devient.** Archivée par la sauvegarde (`routers/data.py:1114`), effacée par « Effacer toutes mes données » (`routers/data.py:773-777`), jamais indexée d'office. Le résultat revient à l'écran, pas au modèle (`components/chat/ToolConfirmationCard.tsx:181-186`).

**BPMN et GraphML en écriture : hors périmètre.**

### 6.5 Export du planning, différé (décision 7)

Inchangé : ne se code pas avant la saisie des durées et des dépendances ; fidélité à l'instantané par l'empreinte des entrées (`services/planning.py:120`), Mermaid `gantt` et GraphML à coordonnées simples, plan à cycle refusé, téléchargement seulement. P-107 ne peut pas compter sur un écrivain BPMN de P-106.

### 6.6 Pas de préréglage MCP dédié

Inchangé.

## 7. Mise en œuvre, lot par lot

Chaque lot fait l'objet d'un commit, tests rouges d'abord, sabotage ciblé par fonction et revue adverse du diff. Les fichiers témoins sont produits par les outils eux-mêmes (Freeplane, yEd, Camunda Modeler, GanttProject, ProjectLibre) et rangés dans `tests/fixtures/formats_structures/`.

**Dépendances.** Lot 1 d'abord (B-1489 et B-1502 sont fermés). Lots 2 à 5 après le lot 1 (décision 8 : aucun format nouveau avant l'accord). Lot 5 après le lot 2. Lot 6 après la saisie du planning (suite de P-039). Si le lot 2 ou le lot 5 de P-107 est livré avant, le lot 1 réutilise `chaine_de_repli()` et `types_de_memoire_permis` au lieu de les créer.

### Lot 1 : aucun contenu de fichier en ligne sans l'accord « documents »

- **Moteur.** `chaine_de_repli()` et `config_du_tour()` extraites ; `destination_d_accord` ; `types_de_memoire_permis` et sa table ; `documents_accordes_pour` ; calcul unique du contenu de fichier porté par le tour (cinq voies) ; retrait des outils de fichiers et phrase de remplacement ; `types_permis` aux deux appels ; D6 conditionnée ; refus du tour ou refus de la bascule ; configuration imposée à `stream_response_with_tools` et à `stream_response`.
- **Écran.** `accordDocumentsPour` et transmission du champ par `ChatInput` ; ligne « Autoriser » persistante ; puis, dans le dernier commit du lot, la phrase du Centre de confiance.
- **Données.** Rien.
- **Tests à écrire en premier** (pytest, avec un fournisseur doublé qui enregistre le `ContextWindow`, les outils et les images reçus) :
  - **le test du P1** : service en ligne, accord `llm` seul, fichier indexé pertinent : aucun fragment de fichier dans le contexte envoyé, un fragment de contact pertinent y est toujours ; avec l'accord « documents » pour ce service : le fragment de fichier est présent ;
  - Ollama local sans le champ : fragments et outils présents ; modèle Ollama `:cloud` : traité comme en ligne ;
  - **`types_de_memoire_permis`** (constat 16) : table des quatre types ; sans accord, `["contact", "project", "owner"]` ; avec accord, les quatre ; la recherche vectorielle reçoit toujours une liste blanche, jamais `None`, jamais `[]` ; **sentinelle** : une analyse du source relève chaque type écrit (argument `memory_type=` et clé `"memory_type"` à valeur littérale), les six sites à la base, et rougit si l'un manque à la table ; vue rouge sur un type fabriqué ;
  - **D6** : conversation sans projet, documents de projet indexés, accord `llm` seul : aucune phrase « Périmètre documentaire » ; avec accord : la phrase est là ;
  - outils : sans accord, `read_file` et `search_files` absents des outils **et** du bloc des capacités, phrase de remplacement présente ; avec accord, présents ; `disable_tools` inchangé ;
  - **outil non offert appelé quand même** (garde de non-régression de B-1489, `tests/test_b1489_outil_non_offert.py` reste vert) : le modèle doublé appelle `read_file` retiré par le lot 1 ; il n'est pas exécuté ;
  - **chaîne de repli** : `config_du_tour()` et l'ancienne résolution rendent la même configuration sur une table d'états (principal ouvert ou fermé, bascule permise ou non, principal Ollama, replis disponibles ou non) ;
  - **bascule sans contenu de fichier** : accord pour le principal, disjoncteur ouvert, secours en ligne : le tour part chez le secours sans outils de fichiers ni fragments ; la suite après outils part chez le même secours (B-1502) ;
  - **bascule avec pièce jointe rejouée** : refusée, principal imposé, rien au secours ;
  - **image d'un tour précédent, disjoncteur ouvert**, accord pour le seul principal : bascule permise, et rien de l'image n'est envoyé au secours ;
  - **`/fichier` avec disjoncteur ouvert**, accord pour le seul principal : bascule refusée, principal imposé, rien au secours (constat 14) ;
  - **image jointe, disjoncteur ouvert**, accord pour le seul principal : bascule refusée, aucune image envoyée au secours (constat 15) ;
  - **`/fichier devis.pdf` sous accord `llm` seul** : tour refusé avec la phrase, aucun appel au fournisseur, avec et sans flux (constat 14) ;
  - **commande apportée par une variable** (valeur `/fichier <chemin témoin>`, message `{mon_dossier}`), accord `llm` seul : tour refusé, aucun appel au fournisseur (D-1 couvert sans l'attendre) ;
  - **image jointe sans accord pour ce service** (requête forgée) : tour refusé ;
  - pièce jointe sans accord pour ce service : tour refusé, aucun appel ;
  - **résolution unique** : le disjoncteur change d'état entre la construction du contexte et l'envoi ; l'appel part vers la configuration résolue au début ;
  - **chemin sans flux** : mêmes garanties ; `stream_response(config=...)` transmet la configuration, et une panne y est comptée au fournisseur de cette configuration ;
  - mini-chat RFC en ligne (aucun champ) : aucun fragment de fichier ; message qui porte une ligne `/fichier` : tour refusé ;
  - `destination_d_accord` et `fournisseurDAccord` donnent la même réponse sur la même table de cas.
  - vitest : accord `llm` seul, la requête porte `documents_accordes_pour: null` ; accord « documents » en stockage, la requête porte la destination ; **stockage indisponible, accord donné dans la session : la requête porte la destination** (constat 18) ; **lecture du stockage qui lève, sans accord de session : champ nul, envoi non bloqué** ; **troisième message sans accord : la ligne « Autoriser » est toujours là, annoncée une seule fois** (constat 19) ; « Autoriser » ouvre la boîte avec la finalité `documents` ; une pièce jointe et une commande de fichier exigent toujours l'accord (`components/chat/ChatInput.commandeFichier.b1521.test.tsx` inchangé) ; la phrase du Centre de confiance est présente et commence par « Dans le chat ».
- **Critères observables.** Service en ligne, accord `llm` seul, `devis.pdf` indexé : « que contient mon fichier devis.pdf ? » obtient une réponse qui dit l'accord manquant et montre le chemin, et le journal de la requête envoyée au fournisseur doublé ne contient aucune ligne du devis ; `/fichier devis.pdf` tapé ou apporté par une variable n'envoie rien ; après « Autoriser », la même question lit le fichier.

### Lot 2 : parseur durci, cartes Freeplane et graphes yEd

- **Moteur.** Module des formats structurés : parseur durci, `controler_en_tete` dans `validate_indexable_file` et dans le scanner de synchronisation, `FormatStructureRefuse`, extracteurs `.mm` et `.graphml`, plafonds, paramètre `avec_identifiants`. Ensemble nommé du parseur (`STRUCTURED_XML_EXTENSIONS`) branché dans `extract_text` (`services/file_parser.py:75`). `lxml` déclaré.
- **Écran.** Les deux extensions dans `lib/formatsIndexables.ts`, avec un groupe « Cartes et schémas » dans les filtres du sélecteur ; la phrase de refus affichée à l'indexation ; les fichiers refusés nommés dans le plan de synchronisation.
- **Données.** Rien.
- **Listes.** `.mm` et `.graphml` ajoutées ensemble à `INDEXABLE_EXTENSIONS` (`services/path_security.py:263-283`), à l'ensemble du parseur, à la liste de l'écran et à `ALLOWED_UPLOAD_EXTENSIONS` (`routers/files.py:427`) ; la porte des promesses (`tests/test_extensions_promises_tenues.py:20-31`) inclut le nouvel ensemble.
- **Tests à écrire en premier.**
  - sécurité : `DOCTYPE` avec entité externe vers un fichier témoin : refusé, le marqueur n'apparaît nulle part ; entité vers `http://127.0.0.1:9/` : aucune connexion ; expansion exponentielle refusée en moins d'une seconde ; `huge_tree` jamais activé ;
  - refus avant écriture : indexer un `.mm` à `DOCTYPE` : 422 avec la phrase, aucune ligne dans `file_metadata` ;
  - refus à l'extraction : un `.mm` sain validé, puis remplacé par un `.mm` à `DOCTYPE` avant l'extraction : la ligne neuve est supprimée ; en réindexation, l'index existant est intact ;
  - `read_file` atteint la phrase de refus : un `.mm` indexé sain, puis modifié sur le disque pour déclarer un `DOCTYPE` : `read_file` rend la phrase de refus, pas la phrase générique ;
  - pièce jointe et commande `/fichier` à `DOCTYPE` : phrase de refus à l'écran ; route de contenu : 422, jamais 413 ni 500 ; `FormatStructureRefuse` n'est pas une `ValueError` ;
  - **synchronisation** (constat 17) : dossier synchronisé avec un `.mm` à `DOCTYPE` : absent du plan, compté parmi les refusés et nommé, aucune opération créée, aucun échec au plan suivant ; `.mm` sain au plan, remplacé par un `.mm` à `DOCTYPE` avant l'application : opération `OBSOLETE` avec la phrase, jamais « 422: … » ; au plan suivant, le fichier est parmi les refusés ;
  - identifiants : `read_file` rend les identifiants entre crochets ; les fragments de l'index, la pièce jointe et la route de contenu n'en contiennent aucun ;
  - Freeplane : plan fidèle au témoin, notes, texte enrichi aplati, accents ; FreeMind accepté ; plafond annoncé ; résumé en tête ;
  - yEd : libellés yFiles, arcs orientés, groupes ; GraphML sans yFiles lu par ses clés ;
  - porte des promesses verte ; `lib/formatsIndexables.test.ts` vert ; un `.xml` ordinaire à `DOCTYPE` reste lu en texte.
- **Critères observables.** Une carte Freeplane réelle indexée répond à « quelles sont les branches de ma carte Projet X ? », et `read_file` rend le résumé puis le plan ; la même carte, dans un dossier synchronisé, entre au plan ; une carte à `DOCTYPE` y est nommée comme refusée.

### Lot 3 : processus BPMN

Inchangé : extracteur `.bpmn` (processus, participants, couloirs, étapes typées, flux et conditions, sous-processus), extension à l'écran, témoins Camunda Modeler et bpmn.io, fichier sans BPMNDI lu quand même, porte des promesses verte, un `.bpmn` à `DOCTYPE` refusé avant écriture et au scanner. Critère : « Qui valide la commande dans mon processus achats ? » trouve le couloir et l'étape.

### Lot 4 : plannings MS Project et GanttProject

- **Moteur.** Reconnaissance du XML MS Project sur les 4 premiers kilo-octets, extracteurs MS Project et `.gan`.
- **Écran.** `.gan` à la liste de l'écran (`.xml` y est déjà).
- **Données.** Rien. Aucune réindexation d'office (section 6.3).
- **Tests à écrire en premier.** Témoin ProjectLibre en XML MS Project et témoin GanttProject : tâches, dates, durées, avancement, prédécesseurs avec type et décalage négatif, jalon ; `.xml` MS Project à `DOCTYPE` refusé avant écriture et au scanner ; `.xml` ordinaire à `DOCTYPE` toujours lu en texte ; un `.xml` MS Project à `DOCTYPE` déjà indexé en texte avant le lot 4 : `read_file` rend désormais la phrase de refus ; un `.xml` MS Project sain déjà indexé en texte : `read_file` rend le tableau, alors que l'index garde ses anciens fragments ; porte des promesses verte.
- **Critères observables.** « Quelles tâches dépendent de la livraison du serveur ? » répond d'après les prédécesseurs du fichier ; les notes de version disent que les plannings déjà indexés se relisent en structure et que leur recherche se met à jour à leur prochaine indexation.

### Lot 5 : tenir une carte Freeplane à jour, dans une copie

- **Moteur.** Outil `proposer_modification_carte`, classé ; cloison ; base et empreinte d'origine ; opérations ; refus des formules ; `noter` en ajout ; validité du nom ; écriture de la copie ; `.mm` dans la table de types du téléchargement ; outil retiré avec les autres outils de fichiers sans accord.
- **Écran.** Carte de confirmation dédiée (opérations en phrases, plan avant et après, base), « Télécharger », « Ton original n'a pas été modifié ».
- **Données.** Un fichier dans `outputs`, rien en base.
- **Tests à écrire en premier.**
  - original intact (SHA-256 avant et après) ; base modifiée après la proposition : rien n'est écrit ;
  - cloison : fichier d'un autre projet : refus identique à un identifiant inconnu, à la proposition et à la confirmation ; fichier qui n'est pas un `.mm` : même refus ;
  - **sans accord « documents » pour le service en ligne : l'outil n'est pas offert, et appelé quand même, il n'est pas exécuté** ;
  - deux modifications successives : la seconde copie contient les deux ; la carte de la seconde dit « À partir de ta copie du … » ;
  - original changé entre deux modifications : la seconde repart de l'original, la carte le dit ;
  - `base="original"` explicite : seule la nouvelle opération ;
  - préservation : un attribut inconnu, un commentaire et un attribut `script1` survivent à l'aller-retour, comparés par forme canonique (C14N) élément par élément ;
  - formule : `ajouter`, `renommer` et `noter` avec « =1+1 » ou «   =x » : proposition refusée, rien n'est écrit ; vérification sur un témoin Freeplane 1.11 que « = » est le seul préfixe évalué ;
  - `noter` : note existante conservée, paragraphe ajouté ; « <b> » apparaît littéralement à la réouverture ; note sous une autre forme : opération refusée ;
  - attribut sous n'importe quel nom : proposition refusée entière ; suppression impossible ; déplacement sous son propre descendant refusé ; nœud en texte enrichi non renommable ; échappement de `<`, `&` et des guillemets ;
  - nom de la copie, fonction pure : chaque caractère interdit, chaque nom réservé (avec et sans extension, en minuscules), point final, espace final, longueur ; le nom produit depuis `CON.mm` ou `a:b.mm` est valide ;
  - copie dans `outputs`, jamais dans le dossier de l'original ; téléchargeable par la route existante ;
  - outil classé `MUTATION_LOCALE` ; test de complétude des classes vert ;
  - vitest : la carte montre les opérations en phrases et sa base, et ne crée rien avant « Confirmer ».
- **Critères observables.** « Ajoute une branche Relance fournisseur sous Achats dans ma carte Projet X », puis « ajoute aussi Relance transporteur » : la seconde copie téléchargée s'ouvre dans Freeplane avec les deux branches, et l'original n'a pas bougé.

### Lot 6 : export du planning (différé)

Inchangé par rapport à la V2.

## 8. Ce que la V4 retire ou reporte, et pourquoi

Aucune décision de Ludo n'est réduite : les décisions 7, 8 et 9 sont tenues, et la décision 8 est appliquée plus largement que sa lettre (section 4). Ce que la V3 faisait bien est gardé : champ de destination plutôt que booléen, résolution unique, refus de la bascule quand le tour porte un document, refus avant écriture, cloison et base de l'outil de carte, formules refusées, forme canonique, garde Windows en test pur.

| Retiré ou reporté | Pourquoi |
|---|---|
| « Trois voies » du contenu d'un fichier (V3, sections 1, 4 et 5) | Il y en a cinq : les commandes de fichier et l'image du tour en sont deux (constats 14 et 15) |
| Liste de types écrite en dur, `["contact", "project", "owner"]` (V3, 6.1 et lot 1) | Remplacée par `types_de_memoire_permis`, partagée avec P-107 ; une seule table dit quels types partent (constat 16) |
| Filtre de type posé seulement sans accord (V3, 6.1) | Remplacé par une liste blanche à chaque tour, pour qu'un type nouveau ne parte jamais sans être classé ; une liste vide n'est jamais passée |
| `config_du_tour()` décrite comme corps recopié de `_resolve_with_circuit_breaker` (V3, 6.1) | Remplacée par une extraction unique d'où sortent la résolution du moteur, `config_du_tour()` et la vue de P-107 |
| Calcul du champ par `hasCloudConsent` seul (V3, 6.1) | Refusait des tours que la garde de l'écran laissait partir (constat 18) |
| Ligne « Autoriser » une fois par conversation (V3, 6.1) | La consigne au modèle y renvoie ; elle reste visible tant que l'accord manque (constat 19) |
| Prérequis B-1489 « à corriger » et continuation « chez le principal » (V3, sections 2, 6.1, 9) | Livrés (B-1489, B-1502) ; le test correspondant devient une garde de non-régression |
| « Cinq appelants » de l'extraction (V3, 6.2) | Sept : le scanner et l'application d'un plan de synchronisation en sont deux (constat 17) |
| Champ `lecture_fichiers`, phrase sans borne, test `read_file` inatteignable, « octet pour octet », job Windows comme garde, réindexation des plannings (retraits de la V3) | Motifs de la V3, section 8, toujours valables |

## 9. Risques restants

- **Confiance dans l'écran.** Le serveur croit `documents_accordes_pour`, comme il croit aujourd'hui l'accord tenu par l'interface. La valeur par défaut ferme ; un appelant local malveillant pourrait l'ouvrir, comme il le peut déjà pour le reste de l'API locale.
- **Friction de l'accord.** Qui n'a donné que l'accord `llm` perd, en ligne, les fragments de fichiers qu'il recevait jusqu'ici, et voit une ligne permanente sous le composeur tant qu'il n'a pas choisi. La ligne est le prix d'une consigne vraie ; si elle pèse en usage réel, un « Ne plus proposer » par service serait la suite, pas une réponse du lot 1.
- **Points d'index sans type.** Le filtre en liste blanche écarte désormais un point qui ne porterait aucun type. Tous les écrivains de la base en posent un (six sites, section 5) ; un point écrit par une version très ancienne, s'il en existe, cesserait de nourrir le contexte. Non observé ; dit dans les notes de version du lot 1.
- **Bascule refusée.** Un tour qui porte un document, une commande de fichier ou une image échoue quand le principal est en panne, au lieu de partir chez le secours. C'est voulu ; l'utilisateur voit l'erreur de panne habituelle.
- **D-1 et D-2** restent des défauts du code actuel tant que l'orchestrateur ne les a pas corrigés ; le lot 1 couvre D-1 côté serveur et n'étend pas D-2.
- **L'Atelier** envoie à ses agents des fichiers d'espace de travail sous ses propres règles : c'est P-107 qui doit le rendre visible et le gouverner.
- **Variété des fichiers réels, grandes cartes, copies qui s'accumulent, export suspendu à P-039, P-107 sans écrivain BPMN** : inchangés.
- **Formules Freeplane.** Si le témoin montre d'autres préfixes évalués que « = », le lot 5 s'arrête pour étendre la liste.
- **Collision de préfixe d'identifiant.** Deux originaux dont l'identifiant partage ses 8 premiers caractères seraient confondus dans la recherche de la dernière copie ; l'empreinte d'origine écarte toute copie d'un autre original.

## 10. Questions réservées à Ludo

Aucune. La copie d'une carte ne remplace jamais le fichier de l'utilisateur ; les fragments de fichiers retirés des réponses en ligne sans accord ne sont pas effacés (ils restent dans l'index local) ; rien n'est annoncé publiquement hors des notes de version habituelles, rien ne touche à la marque. D-1 et D-2 sont des défauts ordinaires, corrigés hors RFC.

## Amendements de la revue unique V4 (26/09/2026)

Verdict GO. Pas de V5 : les constats P2 de `docs/plans/revues/2026-09-26-revue-rfc-v4-p105-p106.md` s'imposent aux lots concernés, avec leurs tests, et seront vérifiés à la revue de conception de chaque lot.
