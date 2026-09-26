# RFC P-106 (V3) : lire des cartes mentales, des graphes, des processus et des plannings, puis tenir une carte à jour

Rédigé le 26/09/2026. Remplace la V2 (`docs/plans/2026-09-26-rfc-p106-formats-structures-v2.md`), refusée (NO-GO) par la revue adverse du 26/09 (constats 18 à 30, dont un P1 ; rapport de travail `revue-v2-p105-p106.md` de l'orchestrateur). Les décisions du 25/09/2026 (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md`, points 7 à 9) restent des faits. La réponse à la revue de la V1 (V2, section 7) reste valable et n'est pas recopiée ici.

**Base de vérification.** Toutes les lignes citées ont été relues à `6f927313` (HEAD du 26/09/2026), avec `git show HEAD:<fichier>`, jamais dans l'arbre de travail, où l'orchestrateur corrige des défauts en parallèle. B-1495 (`d80d4406`, `include_memory` enfin respecté) et B-1494 (`6f927313`), livrés pendant la rédaction, ont décalé `routers/chat.py` : la revue citait 803-817, 1737, 2370 et 3247 ; ce document cite 804-818, 1739-1741, 2397-2399 et 3273 pour les mêmes instructions. Chemins relatifs à `src/backend/app/` (fichiers `.py`) et à `src/frontend/src/` (fichiers `.ts` et `.tsx`) ; les tests, `docs/`, `.github/`, `uv.lock` et `pyproject.toml` partent de la racine du dépôt.

Aucun code avant la validation de ce document.

## 0. Constats de la revue V2 et leur traitement

| # | Gravité | Constat de la revue V2 | Traitement | Où |
|---|---|---|---|---|
| 18 | P1 | Retirer `search_files` et `read_file` laisse partir le contenu des fichiers indexés par le contexte mémoire, sous le seul accord `llm` ; la phrase du Centre de confiance serait fausse | **Accepté.** Relu : `_get_memory_context` (`routers/chat.py:745`) injecte les fragments `file` (`routers/chat.py:804-818`), aux deux appels (`routers/chat.py:1739-1741`, `:2397-2399`), puis `prepare_context` (`routers/chat.py:1847`, `:2510`) ; les fichiers indexés portent `"memory_type": "file"` (`services/indexation.py:167`). Le drapeau d'accord descend jusqu'à la recherche vectorielle, filtrée en amont par `memory_types` (`services/qdrant.py:576-592`). Les pièces jointes (nouvelles et rejouées) sont couvertes aussi. La phrase du Centre de confiance est bornée au chat et n'est écrite qu'au dernier commit du lot 1, quand ses quatre conditions sont testées | 6.1 ; lot 1 |
| 19 | P2 | Retirer un outil de la liste offerte n'empêche pas son exécution | **Accepté.** Défaut du code actuel (`routers/chat.py:3273`, cité 3247 par la revue avant deux décalages, n'interroge jamais `tools`, reçue `routers/chat.py:3045`) : prérequis B-1489, corrigé hors RFC. Le lot 1 ajoute son propre test de bout en bout, qui rougit si B-1489 régresse | 2 ; lot 1 |
| 20 | P2 | Le disjoncteur peut basculer vers un autre fournisseur après que les outils ont été offerts | **Accepté.** Le fournisseur effectif est résolu une fois par tour, avant de construire le contexte, puis imposé à l'appel (`config`, `services/llm.py:962`, `:973`) ; l'écran transmet la destination couverte par l'accord, et non plus un booléen. Si la bascule change de destination, le tour part sans aucun contenu de fichier, ou la bascule est refusée s'il porte une pièce jointe | 6.1 ; lot 1 |
| 21 | P2 | « Un refus empêche toute indexation à vide » est contredit par l'ordre d'écriture ; le test `read_file` du lot 2 ne peut pas passer | **Accepté.** La métadonnée est commitée avant l'extraction (`services/indexation.py:550-554`, extraction `:583`) et `read_file` écarte les fichiers à zéro fragment (`services/memory_tools.py:1536-1539`). Contrôle déplacé dans `validate_indexable_file` (`services/path_security.py:286`), avant toute écriture ; un refus à l'extraction (fichier modifié entre-temps) retire la ligne neuve. Test `read_file` réécrit sur les deux seuls cas atteignables | 6.2 ; lots 2 et 4 |
| 22 | P2 | Le nouvel outil ne dit pas sa cloison | **Accepté.** Même cloison que `read_file` (`_cloison_fichiers`, `services/memory_tools.py:1536-1543`), à la proposition et à la confirmation, même refus pour un identifiant inconnu et un fichier hors périmètre | 6.4 ; lot 5 |
| 23 | P2 | Deux modifications successives divergent | **Accepté.** La proposition part de la dernière copie de cet original quand elle existe (base dite sur la carte), retrouvée par son nom dans `outputs` ; l'empreinte de l'original d'origine est gardée dans la copie, pour repartir de l'original s'il a changé | 6.4 ; lot 5 |
| 24 | P3 | Freeplane évalue un texte qui commence par « = » | **Accepté** sans attendre la vérification : tout texte d'opération qui commence par « = » est refusé. La vérification sur un témoin Freeplane 1.11 reste au lot 5, pour savoir si d'autres préfixes existent | 6.4 ; lot 5 |
| 25 | P3 | « Octet pour octet » hors de portée de lxml | **Accepté.** Comparaison par forme canonique (C14N) élément par élément | lot 5 |
| 26 | P3 | `noter` : remplacer ou compléter, et échappement | **Accepté.** Ajout à la fin de la note HTML existante, texte posé par l'arbre (échappé une fois, jamais interprété) ; note d'une autre forme : opération refusée | 6.4 ; lot 5 |
| 27 | P3 | Les identifiants de nœuds entreraient dans l'index | **Accepté.** Identifiants produits seulement pour `read_file` (paramètre de l'extracteur) ; l'indexation, les pièces jointes et la route de contenu n'en reçoivent pas | 6.3 ; lot 2 |
| 28 | P3 | Une exception de refus dérivée de `ValueError` sera lue « trop volumineux » | **Accepté.** Exception distincte, non dérivée de `ValueError`, rendue 422 ; cinq appelants traités un par un (la revue en comptait quatre) | 6.2 ; lot 2 |
| 29 | P3 | La création réelle sur le job Windows ne bloque rien | **Accepté** (`.github/workflows/tests-windows.yml:3-4`). La garde est un test pur de validité du nom, dans la CI principale | 6.4 ; lot 5 |
| 30 | P3 | Les plannings MS Project déjà indexés en texte gardent leurs balises | **Accepté, par annonce.** `read_file` relit le disque et donne la structure dès le lot 4 ; l'index garde les anciens fragments jusqu'à la prochaine indexation du fichier. Une réindexation automatique serait une écriture de fond, cliente de la mise au repos : elle n'est pas faite ici | 6.3 ; lot 4 |

## 1. Ce que la V3 change

- **Le P1 est fermé** : aucun contenu de fichier ne part vers un service en ligne sans l'accord « documents » donné pour ce service, par aucune des trois voies du chat (outils, contexte mémoire, pièces jointes), et même quand le disjoncteur change de fournisseur.
- Le refus d'un fichier dangereux a lieu avant toute écriture en base, et dit sa raison sur chaque chemin.
- L'outil de mise à jour d'une carte a sa cloison, suit la dernière copie, et refuse les formules.
- Le reste de la V2 est gardé : ordre des lots (décision 7), parseur durci, formats lus, copie dans un dossier de THÉRÈSE (décision 9), export différé.

## 2. Prérequis

| Nom | Nature | État à la base relue | Bloque |
|---|---|---|---|
| **B-1489** | Un outil non offert au tour est exécuté si le modèle l'appelle : la branche des outils de mémoire (`routers/chat.py:3273`) ne vérifie pas que l'outil figurait dans `tools` (`routers/chat.py:3045`) | À corriger par l'orchestrateur, hors RFC | lot 1 : sans lui, retirer `read_file` de la liste ne prouve rien |

Aucun autre prérequis. Le lot 1 ne dépend d'aucun nouveau format ; les lots 2 à 5 dépendent du lot 1 (décision 8 : aucun format nouveau avant l'accord).

## 3. Le besoin

Dr_logic-3D, testeur alpha, sur Discord (#discussion et fil du 25/09, 03:35 à 04:29) :

- Il tient ses sujets dans des représentations structurées : cartes mentales Freeplane (`.mm`), graphes yEd (`.graphml`), processus BPMN, plannings Gantt.
- À chaque évolution d'un sujet, il met ces fichiers à jour à la main.
- Il voudrait que THÉRÈSE les lise et les tienne à jour, plutôt que de tout recopier dans le chat.

## 4. Décisions du 25/09/2026 (tranchées)

7. **Lecture d'abord.** On commence par lire les fichiers de Dr_logic ; l'export Mermaid et GraphML du planning attend la saisie des durées et des dépendances (suite de P-039).
8. **Accord « documents » exigé dès qu'un outil de lecture de fichier est offert à un modèle en ligne.**
9. **La copie d'une carte modifiée est rangée dans un dossier de THÉRÈSE**, jamais à côté de l'originale.

La V3 lit la décision 8 dans son esprit, pas seulement dans sa lettre : l'outil n'est qu'une des trois voies par lesquelles le contenu d'un fichier atteint le modèle. Les deux autres (contexte mémoire, pièces jointes) sont soumises au même accord. Ce n'est pas une décision nouvelle : c'est la seule lecture qui rende vraie la phrase promise à l'utilisateur.

## 5. État du code à HEAD

Les points d'appui de la V2 (section 4) restent justes, lignes relues ; seuls ceux qui changent ou s'ajoutent sont repris ici.

- **Trois voies du contenu d'un fichier vers le modèle, dans le chat.**
  1. Les outils : `MEMORY_TOOLS` (`services/memory_tools.py:228-234`) est ajouté à chaque tour outillé (`routers/chat.py:2546`) ; `read_file` enveloppe son contenu (`services/memory_tools.py:1620-1628`).
  2. Le contexte mémoire : `_get_memory_context` (`routers/chat.py:745`) cherche dans l'index sans filtre de type (`routers/chat.py:769`) et injecte chaque fragment `file` avec le nom du fichier (`routers/chat.py:804-818`). Il est appelé par les deux chemins de `/api/chat/send` (`routers/chat.py:1739-1741` sans flux, `:2397-2399` en flux) dès que `include_memory` est vrai, sa valeur par défaut (`models/schemas.py:110`), que `ChatInput` pose explicitement (`components/chat/ChatInput.tsx:700`). B-1495 vient de faire respecter ce champ ; il ne dit rien de la destination.
  3. Les pièces jointes : extraites (`routers/chat.py:333`), enveloppées (`routers/chat.py:422-428`), rejouées d'un tour à l'autre (`routers/chat.py:570`), puis ajoutées au contexte mémoire (`routers/chat.py:1819-1821` et `:2498-2500`).
- **Filtre par type déjà disponible.** `async_search` accepte `memory_types` (`services/qdrant.py:576-592`), appliqué en filtre de la requête (`services/qdrant.py:264-269`). Les types écrits dans l'index à HEAD sont `contact`, `project`, `file` et `owner` (`routers/memory.py:252`, `:281`, `services/indexation.py:167`, `services/user_profile.py:450`).
- **Consentement.** Un accord par finalité et par destination (`lib/consent.ts:41-43`), rangé dans le stockage du navigateur (`lib/consent.ts:44-67`) ; la destination d'un envoi est le fournisseur, ou « ollama-cloud » pour un modèle Ollama en ligne, ou rien pour un modèle local (`lib/ollamaCloud.ts:19-23`). Le serveur sait reconnaître un modèle Ollama en ligne (`services/ollama_capabilites.py:86-90`) mais ne connaît aucun accord.
- **Disjoncteur.** Le chat utilise le service partagé, qui bascule par défaut (`services/llm.py:1200-1205`, `bascule_circuit` vrai par défaut) vers le premier fournisseur disponible dans un ordre fixe (`services/llm.py:756-758`, `:849-856`), sauf depuis un fournisseur local (B-1071, `services/llm.py:832-840`). La résolution a lieu dans l'appel de flux (`services/llm.py:973`), qui accepte une configuration imposée (`services/llm.py:962`) ; `stream_response` n'en accepte pas (`services/llm.py:904-911`). La continuation après outils utilise toujours la configuration principale (`services/llm.py:1069-1079`).
- **Ordre d'écriture de l'indexation.** Validation (`services/indexation.py:250-257`, seuls `PermissionError`, `FileNotFoundError` et `ValueError` y sont attrapés), métadonnée commitée (`services/indexation.py:550-554`), puis extraction (`services/indexation.py:583`). `read_file` ne lit que les fichiers à fragments (`services/memory_tools.py:1536-1539`) et rend une phrase générique sur toute exception d'extraction (`services/memory_tools.py:1581-1600`).
- **Cinq appelants de l'extraction ou de la validation** : `services/indexation.py:250` (validation), `services/indexation.py:583` (indexation), `routers/chat.py:333` (pièce jointe), `routers/files.py:406` (contenu d'un fichier, dont `ValueError` devient 413, `routers/files.py:410-411`), `services/memory_tools.py:1584` (`read_file`).
- **Sorties.** Dossier `outputs` (`services/skills/registry.py:32`), téléchargement par identifiant qui cherche `*_<8 caractères>.*` à la racine, sans descendre (`routers/skills.py:266-267`).
- **L'Atelier a son propre `read_file`**, qui lit les fichiers d'un espace de travail pour ses agents (`services/agents/runtime.py:196-197`) : hors du chat, hors de cette RFC, dans le périmètre de P-107.

## 6. Conception V3

### 6.1 Aucun contenu de fichier en ligne sans l'accord « documents » (décision 8, constats 18 à 20)

**Principe.** Dans le chat, le contenu d'un fichier (outil de lecture, fragment d'index, pièce jointe) ne part vers un service en ligne que si l'accord « documents » a été donné **pour ce service-là**, celui qui recevra réellement le tour.

**Ce que l'écran transmet.** `ChatRequest` (`models/schemas.py:105`) gagne `documents_accordes_pour: str | None = None` : la destination d'accord (même calcul que `fournisseurDAccord`, `lib/ollamaCloud.ts:19-23`) si `hasCloudConsent('documents', destination)` est vrai, sinon rien. La V2 transmettait un booléen ; un booléen ne dit pas pour quel fournisseur l'accord vaut, et c'est ce qui laissait passer la bascule (constat 20). La valeur par défaut ferme : un appelant qui ne transmet rien n'ouvre rien.

**Ce que le serveur décide, une fois par tour, avant de construire quoi que ce soit.**

1. `LLMService` gagne une méthode publique `config_du_tour()` qui rend la configuration que le disjoncteur retiendrait (le corps de `_resolve_with_circuit_breaker`, sans rien changer à ses règles).
2. Une fonction serveur `destination_d_accord(config)`, miroir de `lib/ollamaCloud.ts:19-23` : rien pour Ollama local, « ollama-cloud » pour un modèle Ollama en ligne (`est_modele_ollama_cloud`), le nom du fournisseur sinon. Un test confronte les deux implémentations sur la même table de cas.
3. `documents_permis = destination is None or destination == request.documents_accordes_pour`.
4. Si `documents_permis` est faux **et** que la destination principale (`llm_service.config`) aurait été permise, c'est la bascule qui a changé la destination. Alors :
   - si le tour porte une pièce jointe, nouvelle ou rejouée : **la bascule est refusée pour ce tour**, la configuration principale est imposée, et une panne réelle remonte comme aujourd'hui quand la bascule est interdite. Motif : répondre sur un document sans le document serait une réponse fausse, et l'envoyer au fournisseur de secours serait une fuite ;
   - sinon, le tour part chez le fournisseur de secours, sans aucun contenu de fichier (points 5 à 7).
5. **Outils** : si `documents_permis` est faux, `search_files` et `read_file` sont retirés de `tools` après leur ajout (`routers/chat.py:2546`). Le bloc des capacités, construit sur `tool_names` (`routers/chat.py:2567`, `:2597-2600`), cesse de les promettre, et une phrase les remplace : « Les fichiers indexés ne sont pas consultables ici : l'accord pour envoyer des documents à ce service n'est pas donné. Si on te les demande, dis-le, et indique le bouton Autoriser sous le composeur. »
6. **Contexte mémoire** : `_get_memory_context` gagne `types_permis: list[str] | None`. Si `documents_permis` est faux, il reçoit la liste des types qui ne sont pas des documents, `["contact", "project", "owner"]`, passée à `async_search(memory_types=...)`. Le filtre est posé **en amont**, dans la requête : filtrer après coup laisserait des fragments de fichiers consommer les huit résultats de la recherche (`limit=8`) et appauvrirait le contexte pour rien. La liste est une **liste blanche** : un type ajouté demain à l'index n'est pas envoyé tant qu'il n'est pas classé. Les deux appels (`routers/chat.py:1739-1741`, `:2397-2399`) passent le paramètre ; `include_memory=false` garde sa priorité (aucune mémoire du tout).
7. **Pièces jointes** : si `documents_permis` est faux et que la bascule n'est pas en cause (l'écran a envoyé une pièce jointe sans accord pour ce service, ce qu'il empêche aujourd'hui, `components/chat/ChatInput.tsx:558-575`), le tour est refusé avec une phrase : « L'accord pour envoyer des documents à ce service n'est pas donné. » Rien n'est envoyé.
8. **La configuration résolue est imposée à l'appel** : `stream_response_with_tools(context, tools, config=config_du_tour)` (paramètre existant, `services/llm.py:962`), et `stream_response` gagne le même paramètre, transmis tel quel. Le disjoncteur ne résout donc qu'une fois : il ne peut pas changer d'avis entre la construction du contexte et l'envoi.

**Exécution.** B-1489 refuse à l'exécution tout outil absent de la liste du tour. Sans lui, un modèle qui rappelle `read_file` vu plus tôt dans la conversation le ferait exécuter (constat 19).

**Continuation après outils.** Elle part toujours vers la configuration principale (`services/llm.py:1069-1079`), pas vers celle du tour. Pour P-106, c'est sans risque : un tour basculé n'a pas reçu `read_file`, et un tour non basculé a pour configuration la principale. L'incohérence elle-même (un tour commencé chez le fournisseur de secours finit chez le principal) est un défaut du code actuel, hors RFC, signalé à l'orchestrateur.

**Les autres appelants du chat.** Le mini-chat RFC (`components/rfc/RFCChat.tsx:97-101`) ne transmet pas le champ : en ligne, il ne reçoit plus de fragments de fichiers. C'est un changement de comportement voulu (il en recevait jusqu'ici sous le seul accord `llm`).

**Côté écran.**

- `ChatInput` transmet `documents_accordes_pour` à chaque envoi.
- Les pièces jointes gardent leur règle actuelle (accord « documents » demandé, `components/chat/ChatInput.tsx:558-575`).
- Si seul l'accord `llm` est donné, une ligne discrète apparaît une fois par conversation sous le composeur : « Tes fichiers ne sont pas lus par ce service. Autoriser ». Le bouton ouvre la boîte d'accord existante avec la finalité `documents`.

**La phrase du Centre de confiance.** Dans `phrasesDeLEtat` (`components/prototype/CapabilityCenter.tsx:500`) : « Dans le chat, le contenu de tes fichiers ne part vers un service en ligne que si tu l'as autorisé pour ce service. » Elle n'est vraie qu'avec quatre conditions, chacune testée au lot 1 : outils non offerts (point 5), outils non exécutés (B-1489), aucun fragment de fichier dans le contexte ni pièce jointe (points 6 et 7), fournisseur effectif égal à la destination consentie (points 3, 4 et 8). Elle est **bornée au chat** : l'Atelier lit des fichiers d'espace de travail pour ses agents (`services/agents/runtime.py:196-197`), et ce périmètre appartient à P-107. Elle est écrite dans le dernier commit du lot 1, après les quatre tests.

**Pourquoi cette forme plutôt qu'exiger l'accord « documents » à chaque message.** Inchangé par rapport à la V2 : bloquer toute conversation en ligne de qui refuse l'envoi de ses documents serait disproportionné, et ne pas offrir les documents sans accord respecte la décision.

### 6.2 Un parseur XML durci, et un refus qui précède toute écriture (constats 21 et 28)

- `lxml` devient une dépendance directe (`pyproject.toml`), à la version déjà verrouillée (`uv.lock:1406`). Réglage unique : `XMLParser(resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False)`.
- **Tout fichier structuré qui déclare un `DOCTYPE` est refusé** (`.mm`, `.graphml`, `.bpmn`, `.gan`, et un `.xml` reconnu comme MS Project), sans que rien de ce qu'il désigne soit lu. Si un fichier témoin réel en portait un, le lot s'arrête et le design est rouvert.
- Plafonds : 5 000 éléments utiles, 64 niveaux ; au-delà, l'extraction s'arrête et le dit dans le texte.

**Une exception à part.** `FormatStructureRefuse(Exception)`, **non dérivée de `ValueError`** : la route de contenu traduit toute `ValueError` en « trop volumineux » (`routers/files.py:410-411`), et l'indexation en 400 générique (`services/indexation.py:255-256`). Elle porte la phrase de refus (« ce fichier déclare un type de document, refusé par sécurité »).

**Le contrôle avant l'écriture.** `validate_indexable_file` (`services/path_security.py:286`) appelle un contrôle léger qui lit l'en-tête du fichier (4 kilo-octets, en texte) : pour une extension structurée, ou un `.xml` dont l'élément racine porte l'espace de noms MS Project, la présence d'un `DOCTYPE` lève `FormatStructureRefuse`. Ce contrôle a lieu avant la métadonnée commitée (`services/indexation.py:550-554`) : un fichier refusé ne laisse **aucune ligne** à zéro fragment.

**Les cinq appelants, un par un.**

| Appelant | Ce que voit l'utilisateur |
|---|---|
| `services/indexation.py:250` (validation) | nouvelle branche `except FormatStructureRefuse` : 422, avec la phrase ; l'écran d'indexation l'affiche telle quelle |
| `services/indexation.py:583` (extraction) | le fichier a changé entre validation et extraction : la ligne neuve est supprimée ; en réindexation, l'index existant reste intact, comme pour un abandon ; 422 avec la phrase |
| `routers/chat.py:333` (pièce jointe) | la phrase de refus rendue comme erreur de pièce jointe (la fonction rend déjà un couple contexte, erreur) |
| `routers/files.py:406` (contenu d'un fichier) | branche `except FormatStructureRefuse` placée **avant** `except ValueError` : 422, avec la phrase |
| `services/memory_tools.py:1584` (`read_file`) | branche placée avant l'`except Exception` générique (`services/memory_tools.py:1585`) : la phrase de refus est rendue telle quelle au modèle |

Le `.xml` ordinaire ne change pas : sans l'espace de noms MS Project dans ses 4 premiers kilo-octets, il reste lu en texte brut, `DOCTYPE` compris.

### 6.3 Ce que le modèle lit (lecture seule)

Inchangé, sauf les identifiants et l'annonce du lot 4. Chaque format donne un texte rangé pour tenir dans les 10 000 caractères de `read_file` (`services/memory_tools.py:1516`) : un résumé d'abord, puis le détail.

| Format | Reconnu par | Texte produit |
|---|---|---|
| Carte Freeplane (et FreeMind) | extension `.mm` | plan indenté ; notes en ligne, texte enrichi aplati ; **pour `read_file` seulement**, identifiant de chaque nœud entre crochets |
| Graphe yEd | extension `.graphml` | nœuds (libellé yFiles, sinon clés `label` ou `name`, sinon identifiant), puis arcs « A → B (libellé) » ; groupes rendus comme parents |
| Processus BPMN | extension `.bpmn` | par processus et participant : couloirs, étapes typées, flux avec condition |
| Planning MS Project (et exports ProjectLibre) | `.xml` dont l'élément racine porte l'espace de noms `http://schemas.microsoft.com/project` | tableau : tâche, début, fin, durée, avancement, prédécesseurs avec type et décalage |
| Planning GanttProject | extension `.gan` | même tableau |

**Identifiants de nœuds** (constat 27). `extract_text` gagne un paramètre `avec_identifiants: bool = False`, transmis par `extract_text_async`. Seul `read_file` passe `True` (`services/memory_tools.py:1584`) : les identifiants servent à viser un nœud dans une proposition de modification, pas à la recherche. L'indexation (`services/indexation.py:583`), les pièces jointes (`routers/chat.py:333`) et la route de contenu (`routers/files.py:406`) reçoivent le texte sans crochets.

**Plannings déjà indexés** (constat 30). Un `.xml` MS Project indexé avant le lot 4 garde ses fragments bruts dans l'index jusqu'à sa prochaine indexation (fichier modifié, redéposé, ou dossier synchronisé qui le voit changer). `read_file`, lui, relit le disque (`services/memory_tools.py:1584`) : il donne la structure dès le lot 4. Réindexer d'office ces fichiers serait une écriture de fond, cliente de la mise au repos que P-105 attend aussi ; ce n'est pas justifié pour un défaut de qualité de recherche. Le lot 4 le dit dans les notes de version, par le flux de release habituel.

Choix tranchés de la V2 inchangés : les deux formats de planning sont lus, le `.mpp` binaire ne l'est pas ; le texte d'une carte arrive au modèle sous l'enveloppe des fichiers, sans voie plus directe.

### 6.4 Tenir une carte Freeplane à jour, dans une copie

**L'outil.** `proposer_modification_carte(fichier_id, operations, base)`, classé `MUTATION_LOCALE` dans `CLASSIFICATION_DES_OUTILS` (`services/contexte_execution.py:30`), donc sous carte (`services/tool_confirmations.py:33-49`).

**Cloison** (constat 22). `fichier_id` est résolu par `_cloison_fichiers`, exactement comme `read_file` (`services/memory_tools.py:1536-1543`), à la proposition **et** à la confirmation : un identifiant inconnu, un fichier hors du périmètre de la conversation et un fichier qui n'est pas un `.mm` reçoivent le même refus (`_REFUS_LECTURE`, `services/memory_tools.py:1510`), pour que la réponse ne devienne pas un oracle.

**Liste fermée d'opérations** (inchangée : `ajouter`, `renommer`, `deplacer`, `noter` ; aucune suppression, aucun attribut, icône, lien, style ni script ; un argument inattendu refuse toute la proposition ; 500 caractères par texte ; 50 opérations au plus), avec trois précisions :

- **Formules** (constat 24) : tout texte d'opération dont le premier caractère non blanc est « = » est refusé, et toute la proposition avec lui. Freeplane évalue un tel texte comme une formule quand les formules sont actives. La vérification sur un témoin Freeplane 1.11 (lot 5) dira si d'autres formes existent ; le refus ne l'attend pas.
- **`noter`** (constat 26) : ajoute un paragraphe à la fin de la note existante, qui est conservée. La note est un `richcontent TYPE="NOTE"` contenant du HTML ; le paragraphe est un élément `<p>` dont le texte est posé par l'arbre XML, donc échappé une fois et jamais interprété (« <b> » apparaît tel quel dans Freeplane). Sans note, elle est créée sous cette forme. Une note sous une autre forme que Thérèse ne sait pas compléter : l'opération est refusée (« note dans un format que Thérèse ne sait pas compléter : complète-la dans Freeplane »).
- **Texte enrichi** : un nœud dont le texte est en `richcontent TYPE="NODE"` ne se renomme pas (inchangé).

**La base : original ou dernière copie** (constat 23).

- Chaque copie est nommée `<nom assaini>_modifiee_<AAAA-MM-JJ>_<HHhMM>_o<8 premiers caractères de l'identifiant de l'original>_<8 caractères>.mm`, à la racine d'`outputs`, pour rester téléchargeable par la route existante (`routers/skills.py:266-267`).
- Juste après la déclaration XML, la copie porte un commentaire `<!-- therese-origine sha256=<empreinte> -->` : l'empreinte de l'original d'où part la chaîne de copies. Ce commentaire n'est lu que dans les copies de THÉRÈSE.
- `base` vaut `"derniere_copie"` par défaut, ou `"original"`. Avec `"derniere_copie"`, l'outil prend la copie la plus récente dont le nom porte `o<8 caractères>` de cet original **et** dont l'empreinte d'origine égale l'empreinte actuelle de l'original. Si l'original a changé depuis (l'utilisateur l'a modifié dans Freeplane), la chaîne est périmée : l'outil repart de l'original et le dit.
- La carte de confirmation dit toujours sa base : « À partir de ta copie du 26/09 à 14 h 05 (tes modifications précédentes comprises) », « À partir de ton original », ou « Ton original a changé depuis ta dernière copie : on repart de l'original, sans les modifications de la copie du 26/09 à 14 h 05 ».

**La carte de confirmation.** Inchangée : opérations en phrases, plan avant et après des seules branches touchées, et la base.

**À la confirmation.**

1. La base (original ou copie) est relue et son empreinte comparée à celle prise lors de la proposition ; si elle a changé, rien n'est écrit (« la carte a changé depuis la proposition, redemande-la »).
2. Les opérations sont appliquées à l'arbre de la base, relu par le parseur durci qui garde commentaires et espaces.
3. La copie est écrite dans `outputs`, d'un seul geste (fichier temporaire puis renommage), jamais à côté de l'originale (décision 9).
4. **Nom valide sous Windows** (constat 29), vérifié par une fonction pure testée dans la CI principale : aucun caractère `<>:"/\|?*` ni caractère de contrôle, aucun nom réservé (`CON`, `PRN`, `AUX`, `NUL`, `COM1` à `COM9`, `LPT1` à `LPT9`, avec ou sans extension, quelle que soit la casse), pas de point ni d'espace final, 255 caractères au plus pour le nom. Le job Windows (`.github/workflows/tests-windows.yml`) reste un complément, qui ne conditionne pas la release.
5. La carte affiche « Copie enregistrée dans THÉRÈSE. Télécharger. Ton original n'a pas été modifié. » ; `.mm` entre dans la table de types du téléchargement (`routers/skills.py:273-281`).

**Ce que la copie devient.** Inchangé : archivée par la sauvegarde, effacée par « Effacer toutes mes données » (`routers/data.py:768-771`, archive `routers/data.py:1091`), jamais indexée d'office. **Le résultat revient à l'écran, pas au modèle** (`components/chat/ToolConfirmationCard.tsx:181-186`) : le modèle n'a pas besoin de l'identifiant de la copie, puisque la base suivante est retrouvée par le serveur.

**BPMN et GraphML en écriture : hors périmètre** (inchangé).

### 6.5 Export du planning, différé (décision 7)

Inchangé : ne se code pas avant la saisie des durées et des dépendances ; fidélité à l'instantané par l'empreinte des entrées (`services/planning.py:120`), Mermaid `gantt` et GraphML à coordonnées simples, plan à cycle refusé, téléchargement seulement. P-107 ne peut pas compter sur un écrivain BPMN de P-106.

### 6.6 Pas de préréglage MCP dédié

Inchangé.

## 7. Mise en œuvre, lot par lot

Chaque lot fait l'objet d'un commit, tests rouges d'abord, sabotage ciblé par fonction et revue adverse du diff. Les fichiers témoins sont produits par les outils eux-mêmes (Freeplane, yEd, Camunda Modeler, GanttProject, ProjectLibre) et rangés dans `tests/fixtures/formats_structures/`.

**Dépendances.** Lot 1 après B-1489. Lots 2 à 5 après le lot 1. Lot 5 après le lot 2 (parseur, `.mm`). Lot 6 après la saisie du planning (suite de P-039).

### Lot 1 : aucun contenu de fichier en ligne sans l'accord « documents »

- **Moteur.** Champ `documents_accordes_pour` ; `config_du_tour()` ; `destination_d_accord` ; retrait des deux outils et phrase de remplacement ; `types_permis` jusqu'à `async_search` aux deux appels ; refus du tour ou refus de la bascule selon le cas ; configuration imposée à `stream_response_with_tools` et à `stream_response`.
- **Écran.** Transmission du champ par `ChatInput` ; ligne « Autoriser » ; puis, dans le dernier commit du lot, la phrase du Centre de confiance.
- **Données.** Rien.
- **Tests à écrire en premier** (pytest, avec un fournisseur doublé qui enregistre le `ContextWindow` et les outils reçus) :
  - **le test du P1** : service en ligne, accord `llm` seul, fichier indexé pertinent pour la question : **aucun fragment de fichier dans le contexte envoyé**, et un fragment de contact pertinent y est toujours ;
  - même situation avec l'accord « documents » pour ce service : le fragment de fichier est présent ;
  - Ollama local sans le champ : fragments et outils présents ; modèle Ollama `:cloud` : traité comme en ligne ;
  - la recherche vectorielle reçoit `memory_types=["contact", "project", "owner"]` (filtre en amont) ;
  - **classement des types** : tout type de mémoire écrit dans le code (relevé par une analyse du source, sur le patron du test de complétude des outils) est soit dans la liste blanche, soit déclaré document ; un type inconnu fait rougir le test ;
  - outils : sans accord, `read_file` et `search_files` absents des outils **et** du bloc des capacités ; avec accord, présents ; `disable_tools` inchangé ;
  - **outil non offert appelé quand même** (exige B-1489) : le modèle doublé appelle `read_file` alors que l'outil a été retiré ; il n'est pas exécuté, aucun contenu n'est renvoyé ;
  - **bascule sans pièce jointe** : accord pour le fournisseur principal, disjoncteur ouvert, secours en ligne : le tour part chez le secours sans outils de fichiers ni fragments de fichiers ;
  - **bascule avec pièce jointe rejouée** : la bascule est refusée, la configuration principale est imposée, rien n'est envoyé au secours ;
  - **résolution unique** : le disjoncteur change d'état entre la construction du contexte et l'envoi ; l'appel part vers la configuration résolue au début ;
  - **pièce jointe sans accord pour ce service** : tour refusé avec la phrase, aucun appel au fournisseur ;
  - chemin sans flux (`stream=false`) : mêmes garanties que le chemin en flux ;
  - mini-chat RFC en ligne (aucun champ) : aucun fragment de fichier ;
  - `destination_d_accord` et `fournisseurDAccord` donnent la même réponse sur la même table de cas.
  - vitest : accord `llm` seul, la requête porte `documents_accordes_pour: null` et la ligne s'affiche une fois ; accord « documents », la requête porte la destination et aucune ligne ; « Autoriser » ouvre la boîte avec la finalité `documents` ; une pièce jointe exige toujours l'accord (test existant inchangé) ; la phrase du Centre de confiance est présente et commence par « Dans le chat ».
- **Critères observables.** Service en ligne, accord `llm` seul, `devis.pdf` indexé : « que contient mon fichier devis.pdf ? » obtient une réponse qui dit l'accord manquant, et le journal de la requête envoyée au fournisseur (fournisseur doublé en recette) ne contient aucune ligne du devis ; après « Autoriser », la même question lit le fichier.

### Lot 2 : parseur durci, cartes Freeplane et graphes yEd

- **Moteur.** Module des formats structurés : parseur durci, contrôle d'en-tête dans `validate_indexable_file`, `FormatStructureRefuse`, extracteurs `.mm` et `.graphml`, plafonds, paramètre `avec_identifiants`. Ensemble nommé du parseur (`STRUCTURED_XML_EXTENSIONS`) branché dans `extract_text` (`services/file_parser.py:75`). `lxml` déclaré.
- **Écran.** Les deux extensions dans `lib/formatsIndexables.ts`, avec un groupe « Cartes et schémas » dans les filtres du sélecteur ; la phrase de refus affichée à l'indexation.
- **Données.** Rien.
- **Listes.** `.mm` et `.graphml` ajoutées ensemble à `INDEXABLE_EXTENSIONS` (`services/path_security.py:263-283`), à l'ensemble du parseur, à la liste de l'écran et à `ALLOWED_UPLOAD_EXTENSIONS` (`routers/files.py:427`) ; la porte des promesses (`tests/test_extensions_promises_tenues.py:20-31`) inclut le nouvel ensemble.
- **Tests à écrire en premier.**
  - sécurité : `DOCTYPE` avec entité externe vers un fichier témoin : refusé, le marqueur n'apparaît nulle part ; entité vers `http://127.0.0.1:9/` : aucune connexion ; expansion exponentielle refusée en moins d'une seconde ; `huge_tree` jamais activé ;
  - **refus avant écriture** (constat 21) : indexer un `.mm` à `DOCTYPE` : 422 avec la phrase, **aucune ligne dans `file_metadata`** ;
  - **refus à l'extraction** : un `.mm` sain validé, puis remplacé par un `.mm` à `DOCTYPE` avant l'extraction : la ligne neuve est supprimée ; en réindexation, l'index existant est intact ;
  - **`read_file` atteint la phrase de refus** : un `.mm` indexé sain, puis modifié sur le disque pour déclarer un `DOCTYPE` : `read_file` rend la phrase de refus, pas la phrase générique ;
  - **les cinq appelants** : pièce jointe à `DOCTYPE` : phrase de refus à l'écran ; route de contenu : 422, jamais 413 ; `FormatStructureRefuse` n'est pas une `ValueError` ;
  - **identifiants** (constat 27) : `read_file` rend les identifiants entre crochets ; les fragments écrits dans l'index n'en contiennent aucun ; la pièce jointe et la route de contenu non plus ;
  - Freeplane : plan fidèle au témoin, notes, texte enrichi aplati, accents ; FreeMind accepté ; plafond annoncé ; résumé en tête ;
  - yEd : libellés yFiles, arcs orientés, groupes ; GraphML sans yFiles lu par ses clés ;
  - porte des promesses verte ; `lib/formatsIndexables.test.ts` vert ; un `.xml` ordinaire à `DOCTYPE` reste lu en texte.
- **Critères observables.** Une carte Freeplane réelle indexée répond à « quelles sont les branches de ma carte Projet X ? », et `read_file` rend le résumé puis le plan.

### Lot 3 : processus BPMN

Inchangé par rapport à la V2 : extracteur `.bpmn` (processus, participants, couloirs, étapes typées, flux et conditions, sous-processus), extension à l'écran, témoins Camunda Modeler et bpmn.io, fichier sans BPMNDI lu quand même, porte des promesses verte, et un `.bpmn` à `DOCTYPE` refusé avant écriture. Critère : « Qui valide la commande dans mon processus achats ? » trouve le couloir et l'étape.

### Lot 4 : plannings MS Project et GanttProject

- **Moteur.** Reconnaissance du XML MS Project sur les 4 premiers kilo-octets, extracteurs MS Project et `.gan`.
- **Écran.** `.gan` à la liste de l'écran (`.xml` y est déjà).
- **Données.** Rien. Aucune réindexation d'office (section 6.3).
- **Tests à écrire en premier.** Témoin ProjectLibre en XML MS Project et témoin GanttProject : tâches, dates, durées, avancement, prédécesseurs avec type et décalage négatif, jalon ; `.xml` MS Project à `DOCTYPE` refusé avant écriture ; `.xml` ordinaire à `DOCTYPE` toujours lu en texte ; **un `.xml` MS Project à `DOCTYPE` déjà indexé en texte avant le lot 4 : `read_file` rend désormais la phrase de refus** ; **un `.xml` MS Project sain déjà indexé en texte : `read_file` rend le tableau**, alors que l'index garde ses anciens fragments ; porte des promesses verte.
- **Critères observables.** « Quelles tâches dépendent de la livraison du serveur ? » répond d'après les prédécesseurs du fichier ; les notes de version disent que les plannings déjà indexés se relisent en structure et que leur recherche se met à jour à leur prochaine indexation.

### Lot 5 : tenir une carte Freeplane à jour, dans une copie

- **Moteur.** Outil `proposer_modification_carte`, classé ; cloison ; base et empreinte d'origine ; opérations ; refus des formules ; `noter` en ajout ; validité du nom ; écriture de la copie ; `.mm` dans la table de types du téléchargement.
- **Écran.** Carte de confirmation dédiée (opérations en phrases, plan avant et après, base), « Télécharger », « Ton original n'a pas été modifié ».
- **Données.** Un fichier dans `outputs`, rien en base.
- **Tests à écrire en premier.**
  - original intact (SHA-256 avant et après) ; base modifiée après la proposition : rien n'est écrit ;
  - **cloison** (constat 22) : fichier d'un autre projet : refus identique à un identifiant inconnu, à la proposition et à la confirmation ; fichier qui n'est pas un `.mm` : même refus ;
  - **deux modifications successives** (constat 23) : la seconde copie contient les deux ; la carte de la seconde dit « À partir de ta copie du … » ;
  - **original changé entre deux modifications** : la seconde repart de l'original, la carte le dit, la copie ne contient que la seconde ;
  - `base="original"` explicite : seule la nouvelle opération ;
  - **préservation** (constat 25) : un attribut inconnu, un commentaire et un attribut `script1` survivent à l'aller-retour, comparés par forme canonique (C14N) élément par élément ;
  - **formule** (constat 24) : `ajouter`, `renommer` et `noter` avec un texte « =1+1 » ou «   =x » : proposition refusée, rien n'est écrit ; vérification sur un témoin Freeplane 1.11 que « = » est bien le seul préfixe évalué (sinon, liste étendue et design rouvert) ;
  - **`noter`** (constat 26) : note existante conservée, paragraphe ajouté à la fin ; « <b> » dans le texte apparaît littéralement à la réouverture ; note sous une autre forme : opération refusée ;
  - attribut sous n'importe quel nom : proposition refusée entière ; suppression impossible ; déplacement sous son propre descendant refusé ; nœud en texte enrichi non renommable ; échappement de `<`, `&` et des guillemets ;
  - **nom de la copie** (constat 29), fonction pure : chaque caractère interdit, chaque nom réservé (avec et sans extension, en minuscules), point final, espace final, longueur ; le nom produit depuis un original nommé `CON.mm` ou `a:b.mm` est valide ;
  - copie dans `outputs`, jamais dans le dossier de l'original ; téléchargeable par la route existante ;
  - outil classé `MUTATION_LOCALE`, donc sous carte ; test de complétude des classes vert ;
  - vitest : la carte montre les opérations en phrases et sa base, et ne crée rien avant « Confirmer ».
- **Critères observables.** « Ajoute une branche Relance fournisseur sous Achats dans ma carte Projet X », puis « ajoute aussi Relance transporteur » : la seconde copie téléchargée s'ouvre dans Freeplane avec les deux branches, et l'original n'a pas bougé.

### Lot 6 : export du planning (différé)

Inchangé par rapport à la V2.

## 8. Ce que la V3 retire ou reporte, et pourquoi

Aucune décision de Ludo n'est réduite : les décisions 7, 8 et 9 sont tenues, et la décision 8 est appliquée plus largement que sa lettre (section 4).

| Retiré ou reporté | Pourquoi |
|---|---|
| Champ `lecture_fichiers: bool` (V2, 5.1) | Remplacé par `documents_accordes_pour` : un booléen ne dit pas pour quel fournisseur l'accord vaut (constat 20) |
| Phrase du Centre de confiance sans borne (« Tes fichiers indexés ne partent vers un service en ligne que si tu l'as autorisé ») | Fausse à HEAD (constat 18), et fausse pour l'Atelier même après le lot 1. Remplacée par une phrase bornée au chat et au service, écrite après ses quatre tests |
| Test « `read_file` sur un fichier à `DOCTYPE` rend la phrase de refus » tel qu'écrit (V2, lot 2) | Inatteignable : un fichier refusé n'a pas de fragments. Remplacé par les deux cas atteignables (fichier modifié après indexation, `.xml` MS Project indexé avant le lot 4) |
| « Survivent octet pour octet » (V2, lot 5) | Hors de portée de lxml ; remplacé par la forme canonique |
| « Création réelle sur le job Windows » comme garde | Le job ne conditionne pas la release ; remplacé par un test pur, le job restant un complément |
| Réindexation des plannings déjà indexés | Reportée : ce serait une écriture de fond, cliente de la mise au repos ; annonce à la place |
| Liste de « quatre appelants » de l'extraction | Il y en a cinq : la validation de l'indexation en est un |

## 9. Risques restants

- **Confiance dans l'écran.** Le serveur croit `documents_accordes_pour`, comme il croit aujourd'hui l'accord tenu par l'interface (`lib/consent.ts:44-67`). La valeur par défaut ferme ; un appelant local malveillant pourrait l'ouvrir, comme il le peut déjà pour tout le reste de l'API locale.
- **Friction de l'accord.** Qui n'a donné que l'accord `llm` perd, en ligne, les fragments de fichiers qu'il recevait jusqu'ici dans ses réponses, sans l'avoir choisi. La ligne « Autoriser » le dit, une fois par conversation. Les réponses peuvent paraître moins informées ; c'est le prix de la promesse.
- **Bascule refusée.** Un tour qui porte une pièce jointe échoue quand le fournisseur principal est en panne, au lieu de partir chez le secours. C'est voulu ; l'utilisateur voit l'erreur de panne habituelle.
- **Continuation après outils** (`services/llm.py:1069-1079`) : incohérence préexistante, hors RFC, signalée à l'orchestrateur.
- **L'Atelier** envoie à ses agents des fichiers d'espace de travail sous ses propres règles : c'est P-107 qui doit le rendre visible et le gouverner.
- **Variété des fichiers réels, grandes cartes, copies qui s'accumulent, export suspendu à P-039, P-107 sans écrivain BPMN** : inchangés par rapport à la V2 (section 9).
- **Formules Freeplane.** Si le témoin montre d'autres préfixes évalués que « = », le lot 5 s'arrête pour étendre la liste.
- **Collision de préfixe d'identifiant.** Deux originaux dont l'identifiant partage ses 8 premiers caractères seraient confondus dans la recherche de la dernière copie ; l'empreinte d'origine écarte toute copie d'un autre original, et l'outil repart alors de l'original.

## 10. Questions réservées à Ludo

Aucune. La copie d'une carte ne remplace jamais le fichier de l'utilisateur et suit le sort connu du dossier `outputs` ; les fragments de fichiers retirés des réponses en ligne sans accord ne sont pas effacés (ils restent dans l'index local) ; rien n'est annoncé publiquement hors des notes de version habituelles, rien ne touche à la marque.
