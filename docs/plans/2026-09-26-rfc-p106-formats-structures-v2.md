# RFC P-106 (V2) : lire des cartes mentales, des graphes, des processus et des plannings, puis tenir une carte à jour

Rédigé le 26/09/2026. Remplace la V1 (`docs/plans/2026-09-25-rfc-p106-formats-structures.md`), jugée NO-GO par la revue adverse (`docs/plans/revues/2026-09-25-revue-rfc-p105-p108.md`, section P-106). Intègre les décisions du 25/09/2026 (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md`, section « Décisions du 25/09/2026 », points 7 à 9), qui sont traitées ici comme des faits.

**Base de vérification.** Toutes les lignes citées ont été relues au commit `900765fb` (26/09/2026). Un autre agent commite pendant la rédaction : une ligne peut avoir glissé de quelques rangs, jamais changé de sens. Chemins relatifs à `src/backend/app/` (fichiers `.py`) et à `src/frontend/src/` (fichiers `.ts` et `.tsx`) ; les tests, le verrou et la documentation partent de la racine du dépôt.

Aucun code avant la validation de ce document.

## 1. Ce que la V2 change

- **L'ordre s'inverse** (décision 7) : on commence par lire les fichiers de Dr_logic ; l'export du planning attend que le planning puisse se saisir.
- **Un préalable de confidentialité passe en premier** (décision 8) : aucun outil de lecture de fichier n'est offert à un modèle en ligne sans l'accord « documents ».
- **La copie d'une carte modifiée va dans un dossier de THÉRÈSE** (décision 9), sous un nom valable sur les trois systèmes.
- Le parseur XML est tranché en interne (constat 9), la mise à jour Freeplane se limite à une liste fermée d'opérations sans écriture d'attribut (constat 8), et les promesses sans chemin de la V1 sont retirées (constats 5 et 6).
- Le format de planning à lire est tranché : XML MS Project (qui couvre aussi ProjectLibre) et GanttProject.

## 2. Le besoin

Dr_logic-3D, testeur alpha, sur Discord (#discussion et fil du 25/09, 03:35 à 04:29) :

- Il tient ses sujets dans des représentations structurées : cartes mentales Freeplane (`.mm`), graphes yEd (`.graphml`), processus BPMN, plannings Gantt.
- À chaque évolution d'un sujet, il met ces fichiers à jour à la main.
- Il voudrait que THÉRÈSE les lise et les tienne à jour, plutôt que de tout recopier dans le chat.

## 3. Décisions du 25/09/2026 (tranchées)

7. **Lecture d'abord.** On commence par lire les fichiers de Dr_logic (cartes mentales, graphes, BPMN, plannings). L'export Mermaid et GraphML du planning attend la saisie des durées et des dépendances (suite de P-039).
8. **Accord « documents » exigé dès qu'un outil de lecture de fichier est offert à un modèle en ligne.**
9. **La copie d'une carte modifiée est rangée dans un dossier de THÉRÈSE**, jamais à côté de l'originale.

Les questions de la V1 qui n'ont pas été reposées le 25/09 sont tranchées ici (sections 5 et 6), chacune avec son motif.

## 4. État du code à HEAD

### 4.1 Points d'appui

- **Extraction de texte.** `extract_text` aiguille par extension (`services/file_parser.py:75-133`) : texte et code, CSV, PDF, DOCX, XLSX, PPTX. Limite de 50 Mo avant tout traitement (`:14`, `:89-92`). Les troncatures sont annoncées dans le texte extrait (PDF `:199-201`, tableur `:283-289`).
- **Quatre listes de formats**, qui doivent bouger ensemble :
  - `INDEXABLE_EXTENSIONS`, qui fait autorité à l'entrée (`services/path_security.py:263-283`), `.xml` compris (l.280) ;
  - les ensembles du parseur (`services/file_parser.py:31-72`), où `.xml` est lu en texte brut avec le code (l.49) ;
  - la liste de l'écran (`lib/formatsIndexables.ts:21-46`, `EXTENSIONS_INDEXABLES` l.41, filtres du sélecteur l.63), confrontée au fichier Python par `lib/formatsIndexables.test.ts` ;
  - `ALLOWED_UPLOAD_EXTENSIONS`, plus étroite, pour le dépôt dans un projet (`routers/files.py:427`).
- **La porte des promesses.** `tests/test_extensions_promises_tenues.py:20-31` interdit d'accepter une extension que les ensembles nommés du parseur ne couvrent pas.
- **Lecture par le modèle.** `search_files` et `read_file` sont des lectures sans carte (`services/contexte_execution.py:48-49`, portillon `services/tool_confirmations.py:33-49`). `read_file` enveloppe son JSON par `sanitize_for_context` (`services/memory_tools.py:1620-1628`) et borne le contenu à 10 000 caractères (`_PLAFOND_LECTURE`, `services/memory_tools.py:1516`). Une pièce jointe du chat passe par `extract_text` (`routers/chat.py:333`) puis par la même enveloppe (`routers/chat.py:424`).
- **`lxml` 6.1.1 est dans le verrou** (`uv.lock:1406`), tiré par python-docx (`pyproject.toml:28`), mais n'est pas une dépendance directe. `defusedxml` n'est pas dans le verrou.
- **Moteur PERT de P-039.** Pur et déterministe (`services/planning.py:1-28`, `ENGINE_VERSION` l.20), empreinte des entrées `fingerprint_inputs` (`:120`), comparée à `PlanningSnapshot.input_hash` (`models/entities.py:777`). Routes : lecture du planning, calcul, suppression d'une dépendance, lecture d'un instantané (`routers/planning.py:171`, `:192`, `:271`, `:297`), sous le préfixe `/api/projects` (`main.py:899`).
- **Sorties de THÉRÈSE.** Les fichiers produits vont dans `outputs` du dossier de données (`services/skills/registry.py:32`). Ce dossier est archivé par la sauvegarde (`routers/data.py:1081`) et vidé par « Effacer toutes mes données » (`routers/data.py:768-771`). Il se télécharge par identifiant (`routers/skills.py:242-287`, motif `*_<8 premiers caractères>.*` l.266-267, identifiant borné l.30, table de types l.273-281).

### 4.2 Manques

- `.mm`, `.graphml`, `.bpmn` et `.gan` ne figurent dans aucune des quatre listes. Un XML MS Project passe, mais comme `.xml` brut : le modèle reçoit des balises, pas un plan.
- **Personne ne peut saisir de durée ni de dépendance.** `TaskSchedule` et `TaskDependency` ne sont construits par aucun routeur ni service (recherche de `TaskDependency(` et `TaskSchedule(` sans résultat dans `routers/` et `services/`), et l'écran n'appelle jamais `/schedule`. Tout projet réel sortirait « incomplet » et sans dates (constat 1).
- **L'accord « documents » ne couvre pas la lecture par outil** (constat 3). `finaliteCloud` ne vaut `'documents'` que si le message porte une pièce jointe ou si la conversation en a porté une (`components/chat/ChatInput.tsx:558-562`). Or `MEMORY_TOOLS`, qui contient `search_files` et `read_file` (`services/memory_tools.py:228-234`), est offert à chaque message dès que les outils sont actifs (`routers/chat.py:2519`) : un document indexé lu par `read_file` part aujourd'hui sous l'accord `llm`.
- **La voie MCP ne sait pas « lire puis mettre à jour ».** Tout outil de connecteur passe par une carte (`services/tool_confirmations.py:33-49`), la chaîne d'outils s'arrête tant qu'une carte attend (`routers/chat.py:3437-3445`), et le résultat confirmé revient à l'écran, pas au modèle (`components/chat/ToolConfirmationCard.tsx:181-186`). Le dépôt compte 18 préréglages de connecteurs (`routers/mcp.py:311-513`, le `CLAUDE.md` en annonce 19) ; aucun ne connaît ces formats.
- Aucune compétence ne modifie un fichier existant : elles créent des fichiers neufs (`services/skills/base.py:18-25`, imports autorisés `services/skills/code_executor.py:72`).
- L'interface n'a aucun rendu Mermaid.

## 5. Conception V2

### 5.1 L'accord « documents » pour la lecture de fichiers (décision 8)

Principe : **un modèle en ligne ne reçoit `search_files` et `read_file` que si l'accord « documents » est donné pour ce service.** Sans cet accord, les deux outils ne lui sont pas offerts, et rien ne lui est promis à leur sujet.

**Côté serveur.**

- `ChatRequest` (`models/schemas.py:105`) gagne `lecture_fichiers: bool = False`.
- Après l'ajout de `MEMORY_TOOLS` (`routers/chat.py:2519`), si la destination est en ligne et que `lecture_fichiers` n'est pas vrai, les deux outils sont retirés de `tools`.
- Est en ligne tout service autre qu'Ollama, et un modèle Ollama « cloud » (`services/ollama_capabilites.py:86-90`). Ollama local garde les deux outils, puisque rien ne quitte la machine.
- Le bloc des capacités se construit ensuite sur `tool_names` (`routers/chat.py:2540`, `:2570-2573`) : les lignes `search_files` et `read_file` disparaissent d'elles-mêmes. Aucun outil retiré ne reste promis, leçon de D1.
- Une phrase remplace ces lignes : « Les fichiers indexés ne sont pas consultables ici : l'accord pour envoyer des documents à ce service n'est pas donné. Si on te les demande, dis-le, et indique le bouton Autoriser sous le composeur. »
- La valeur par défaut est `False` : un appelant qui ne transmet rien n'ouvre rien (fermeture par défaut). Le seul appelant du chat avec outils est `ChatInput` ; le mini-chat RFC coupe tous les outils (`components/rfc/RFCChat.tsx:100`) et ne change pas.

**Côté écran.**

- Au moment d'envoyer vers un service en ligne, `ChatInput` transmet `lecture_fichiers = hasCloudConsent('documents', destination)`.
- Les pièces jointes gardent leur règle actuelle (accord « documents » exigé, `ChatInput.tsx:558-562`).
- Si seul l'accord `llm` est donné, le message part sans les outils de fichiers, et une ligne discrète apparaît une fois par conversation sous le composeur : « Tes fichiers indexés ne sont pas lus par ce service. Autoriser ». Le bouton ouvre la boîte d'accord existante avec la finalité `documents`.
- Le Centre de confiance le dit dans ses phrases d'état (`components/prototype/CapabilityCenter.tsx:500`, `phrasesDeLEtat`) : « Tes fichiers indexés ne partent vers un service en ligne que si tu l'as autorisé. »

**Pourquoi cette forme plutôt que l'accord « documents » à chaque message.** La décision 8 se lit de deux façons : exiger l'accord « documents » avant tout message en ligne (puisque les outils sont toujours offerts), ou ne pas offrir les outils sans cet accord. La première bloquerait toute conversation en ligne pour qui refuse l'envoi de ses documents, alors qu'il accepte celui de ses messages. La seconde respecte la décision (aucun outil de lecture offert sans l'accord) et garde la conversation possible. C'est elle qui est retenue.

### 5.2 Un parseur XML durci (constat 9, tranché ici)

- `lxml` devient une dépendance directe dans `pyproject.toml`, à la version déjà verrouillée. Pas de `defusedxml` : une dépendance de plus pour un réglage que `lxml` offre déjà.
- Réglage unique, dans une fonction du nouveau module : `XMLParser(resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False)`.
- **Tout fichier qui déclare un `DOCTYPE` est refusé**, avec une phrase claire (« ce fichier déclare un type de document, refusé par sécurité »), sans que rien de ce qu'il désigne soit lu. Freeplane, yEd, les modeleurs BPMN, GanttProject et MS Project n'en écrivent pas ; si un fichier témoin réel en portait un, le lot s'arrête et le design est rouvert.
- Plafonds : 5 000 éléments utiles et 64 niveaux de profondeur. Au-delà, l'extraction s'arrête et le dit dans le texte (« carte tronquée à 5 000 nœuds »), comme le PDF et le tableur.
- Un refus doit empêcher toute indexation à vide et dire sa raison. Il lève une exception dédiée, levée hors du `try` qui avale tout dans `extract_text` (`services/file_parser.py:96-133`), comme la limite de 50 Mo (`:89-92`).
  - `read_file` attrape aujourd'hui toute exception et rend une phrase générique (« format non pris en charge, fichier vide ou trop volumineux », `services/memory_tools.py:1580-1600`), que le modèle relaierait à tort. Cette exception est donc attrapée avant la branche générique, et sa phrase de refus est rendue telle quelle.
  - Côté indexation, l'exception remonte de `services/indexation.py:583` ; ce qui l'attrape plus haut n'a pas été lu pour cette RFC. Le lot 2 le lit, puis fait dire le refus à l'écran, jamais un document indexé sans contenu.

### 5.3 Ce que le modèle lit (lecture seule)

Chaque format donne un texte, rangé pour tenir dans les 10 000 caractères de `read_file` : **un résumé d'abord** (titre, nombre d'éléments, premier niveau), **puis le détail**. Une grande carte tronquée garde ainsi sa structure d'ensemble.

| Format | Reconnu par | Texte produit |
|---|---|---|
| Carte Freeplane (et FreeMind) | extension `.mm` | plan indenté ; notes en ligne (« Note : … »), texte enrichi aplati ; identifiant de chaque nœud entre crochets, pour qu'une modification puisse le viser (section 5.4) |
| Graphe yEd | extension `.graphml` | nœuds (libellé yFiles `y:NodeLabel`, sinon clés `label` ou `name`, sinon identifiant) puis arcs « A → B (libellé) » ; groupes rendus comme parents |
| Processus BPMN | extension `.bpmn` | par processus et par participant : couloirs, étapes typées (tâche, passerelle, événement, sous-processus), flux « A → B » avec leur condition |
| Planning MS Project (et exports ProjectLibre) | `.xml` dont l'élément racine porte l'espace de noms `http://schemas.microsoft.com/project` | tableau : tâche, début, fin, durée, avancement, prédécesseurs avec type (FS, SS, FF, SF) et décalage |
| Planning GanttProject | extension `.gan` | même tableau |

**Choix tranché ici (question 2 de la V1).** Les deux formats de planning sont lus. Le XML MS Project couvre MS Project et ProjectLibre, qui l'exporte ; GanttProject a son propre format ouvert. Le `.mpp` binaire et le format natif de ProjectLibre ne sont pas lus. Motif : Dr_logic n'a pas nommé son outil, et deux lecteurs couvrent les trois outils libres ou courants.

**Le `.xml` ordinaire ne change pas.** La reconnaissance du XML MS Project se fait sur les 4 premiers kilo-octets lus comme du texte : sans l'espace de noms attendu, le fichier reste lu en texte brut comme aujourd'hui, `DOCTYPE` compris. Seul un XML MS Project passe par le parseur durci. Motif : refuser les `.xml` à `DOCTYPE` (XHTML, configurations) serait une régression pour un format déjà accepté.

**Injection de consigne.** Le texte d'une carte arrive au modèle comme tout document, sous l'enveloppe des fichiers (`services/memory_tools.py:1620-1628`, `routers/chat.py:424`). Aucune voie plus directe n'est ouverte, et la lecture n'a aucun effet.

### 5.4 Tenir une carte Freeplane à jour, dans une copie

**L'outil.** `proposer_modification_carte(fichier_id, operations)`, classé `MUTATION_LOCALE` dans `CLASSIFICATION_DES_OUTILS` (`services/contexte_execution.py:30`), donc sous carte. Un outil non classé serait traité comme externe (`classe_de`, `:56-59`) et ferait rougir le test de complétude.

**Liste fermée d'opérations** (constat 8) :

| Opération | Arguments | Refusée si |
|---|---|---|
| `ajouter` | parent, texte, position facultative | parent absent |
| `renommer` | nœud, texte | nœud absent, ou nœud en texte enrichi (à renommer dans Freeplane) |
| `deplacer` | nœud, nouveau parent, position facultative | nœud ou parent absent, ou déplacement sous son propre descendant |
| `noter` | nœud, texte brut | nœud absent |

- Aucune opération ne supprime un nœud, n'écrit un attribut, une icône, un lien, un style ni un script. Le schéma de l'outil n'a aucun champ pour le dire : un argument inattendu refuse toute la proposition. Motif : Freeplane sait exécuter des scripts Groovy rangés dans les attributs d'un nœud (`script1`, `script2`…), selon ses réglages ; une consigne glissée dans un document ne doit pas pouvoir en faire poser un.
- Les attributs, éléments et commentaires existants, scripts compris, sont recopiés tels quels, jamais interprétés.
- Texte borné à 500 caractères et échappé ; une note est écrite en HTML échappé, dans la forme que Freeplane attend pour ses notes.
- Cinquante opérations au plus par proposition.

**La carte de confirmation.** Une carte dédiée remplace l'affichage générique des arguments (`components/chat/ToolConfirmationCard.tsx:119-147`) : la liste des opérations en phrases (« Ajouter "Relance fournisseur" sous "Achats" ») et le plan avant et après des seules branches touchées.

**À la confirmation.**

1. L'original est relu et son empreinte SHA-256 comparée à celle prise lors de la proposition. Si elle a changé (la carte a été modifiée entre-temps), rien n'est écrit : « la carte a changé depuis la proposition, redemande-la ».
2. Les opérations sont appliquées à l'arbre XML d'origine, relu par un parseur durci qui garde commentaires et espaces.
3. **La copie est écrite dans `outputs`** (décision 9), d'un seul geste (fichier temporaire puis renommage), jamais à côté de l'originale : un dossier de travail ou synchronisé la réindexerait et doublerait les résultats de recherche.
4. Nom : `<nom d'origine>_modifiee_2026-09-26_14h05_<8 caractères>.mm`. Aucun deux-points, qui rend un nom invalide sous Windows ; le nom d'origine est assaini et borné. Le suffixe reprend le motif de la route de téléchargement (`routers/skills.py:266-267`), qui gagne `.mm` dans sa table de types (l.273-281).
5. La carte affiche « Copie enregistrée dans THÉRÈSE. Télécharger. Ton original n'a pas été modifié. »

**Ce que la copie devient.** Elle est archivée par la sauvegarde et effacée par « Effacer toutes mes données », comme tout le dossier `outputs` (`routers/data.py:768-771`, `:1081`). Elle n'est jamais indexée d'office : `dossiers_choisis()` ajoute bien le dossier de données aux dossiers autorisés (`services/indexation.py:200-201`), mais l'indexation reste un geste, et seules les racines synchronisées sont parcourues.

**Le résultat revient à l'écran, pas au modèle** (`ToolConfirmationCard.tsx:181-186`). C'est acceptable ici : la confirmation clôt l'échange, et le modèle n'a rien à faire de la copie.

**BPMN et GraphML en écriture : hors périmètre.** Ces formats portent des coordonnées ; un élément ajouté sans position est invisible ou empilé dans les modeleurs. Aucune écriture n'est prévue pour eux, ni dans cette RFC ni plus tard sans une RFC dédiée.

### 5.5 Export du planning, différé (décision 7)

L'export ne se code pas tant que la saisie des durées et des dépendances (suite de P-039) n'existe pas. Ses conditions sont fixées dès maintenant, pour qu'il ne reparte pas avec les défauts de la V1 :

- **Fidélité à l'instantané** (constat 2). `PlanningTaskResult` n'a ni dépendances ni jalon (`services/planning.py:54-68`, jalon en entrée seulement, l.41). L'export relit donc les entrées courantes (`_project_inputs`, `routers/planning.py:45`), recalcule `fingerprint_inputs` (`services/planning.py:120`) et refuse si l'empreinte diffère de `input_hash` de l'instantané : « le plan a changé depuis le calcul, recalcule-le ».
- **Mermaid `gantt`** : dates du moteur, tâches critiques marquées, jalons, et une ligne d'en-tête qui dit que les dépendances SS, FF et SF ne sont pas représentées.
- **GraphML** (constat 4) : extension yFiles, et des coordonnées simples posées par l'export (colonne selon le rang topologique, ligne selon l'ordre dans le rang). Le fichier s'ouvre lisible sans compter sur une mise en page automatique.
- **Plans défectueux** : un plan à cycle est refusé ; un plan incomplet est exporté avec la mention en tête.
- **Téléchargement seulement** (constat 6) : aucune promesse de « bloc de code dans la conversation », faute d'outil du chat pour le produire.

**P-107 ne peut pas compter sur un écrivain BPMN de P-106** (constat 5). P-106 ne produit que Mermaid et GraphML, et seulement après la saisie du planning. Si P-107 veut exporter son registre en BPMN, il devra chiffrer son propre écrivain et sa mise en page, ou exporter en Mermaid. Le lecteur BPMN du lot 3 pourra en revanche lui servir d'oracle de test.

### 5.6 Pas de préréglage MCP dédié

*Choix tranché ici (question 5 de la V1).* Aucun préréglage de connecteur pour ces formats. Motif : un outil de connecteur passe par une carte même en lecture, arrête la chaîne d'outils et ne rend pas son résultat au modèle (section 4.2). La voie interne (`read_file`, puis la proposition sous carte) répond au besoin sans ces trois défauts.

## 6. Mise en œuvre, lot par lot

Chaque lot fait l'objet d'un commit, tests rouges d'abord, sabotage ciblé par fonction (jamais par chaîne globale) et revue adverse du diff. Le design de ce document passe par sa propre revue adverse avant le lot 1. **Les fichiers témoins sont produits par les outils eux-mêmes** (Freeplane, yEd, Camunda Modeler, GanttProject, ProjectLibre), jamais écrits à la main, et rangés dans un nouveau dossier `tests/fixtures/formats_structures/`.

### Lot 1 : l'accord « documents » pour la lecture de fichiers

- **Moteur.** Champ `lecture_fichiers` de `ChatRequest` ; retrait des deux outils pour une destination en ligne sans accord ; phrase de remplacement dans le bloc des capacités.
- **Écran.** Transmission du champ par `ChatInput` ; ligne « Tes fichiers indexés ne sont pas lus par ce service. Autoriser » ; phrase du Centre de confiance.
- **Données.** Rien.
- **Tests à écrire en premier.**
  - pytest : service en ligne sans le champ, `read_file` et `search_files` absents des outils **et** du bloc des capacités ; avec `lecture_fichiers=true`, présents ; Ollama local, présents sans le champ ; modèle Ollama `:cloud`, traité comme en ligne ; `disable_tools`, aucun outil comme aujourd'hui.
  - vitest : seul l'accord `llm` donné, la requête porte `lecture_fichiers: false` et la ligne s'affiche une fois ; accord « documents » donné, `true` et aucune ligne ; « Autoriser » ouvre la boîte d'accord avec la finalité `documents` ; une pièce jointe exige toujours l'accord « documents » (test existant inchangé).
- **Critères observables.** Avec un service en ligne et le seul accord `llm`, « que contient mon fichier devis.pdf ? » obtient une réponse qui dit l'accord manquant, sans lecture ; après « Autoriser », la même question lit le fichier.

### Lot 2 : parseur durci, cartes Freeplane et graphes yEd

- **Moteur.** Nouveau module des formats structurés : parseur durci, extracteurs `.mm` et `.graphml`, plafonds. Nouvel ensemble nommé du parseur (`STRUCTURED_XML_EXTENSIONS`) branché dans `extract_text`. `lxml` déclaré dans `pyproject.toml`.
- **Écran.** Les deux extensions dans `lib/formatsIndexables.ts`, avec un groupe « Cartes et schémas » dans les filtres du sélecteur.
- **Données.** Rien.
- **Listes.** `.mm` et `.graphml` ajoutées ensemble à `INDEXABLE_EXTENSIONS`, au nouvel ensemble du parseur, à la liste de l'écran et à `ALLOWED_UPLOAD_EXTENSIONS`. *Choix tranché ici* : la liste de dépôt dans un projet s'ouvre aussi, pour qu'une carte se range dans son projet comme un PDF. `_extensions_extractibles()` (`tests/test_extensions_promises_tenues.py:20-31`) inclut le nouvel ensemble.
- **Tests à écrire en premier.**
  - sécurité : un fichier avec `DOCTYPE` et entité externe vers un fichier témoin temporaire est refusé, et le marqueur de ce fichier n'apparaît nulle part ; une entité vers `http://127.0.0.1:9/` n'ouvre aucune connexion ; une expansion exponentielle (« milliard de rires ») est refusée en moins d'une seconde ; `huge_tree` jamais activé ;
  - refus : ni indexation à vide, ni document « lu » sans contenu ; l'écran dit pourquoi ; `read_file` sur un fichier à `DOCTYPE` rend la phrase de refus, pas la phrase générique ;
  - Freeplane : plan indenté fidèle au témoin, notes, texte enrichi aplati, identifiants de nœuds, accents ; FreeMind accepté ; plafond de 5 000 nœuds annoncé ; résumé en tête ;
  - yEd : libellés yFiles lus, arcs orientés, groupes ; GraphML sans yFiles lu par ses clés ;
  - porte des promesses verte ; `lib/formatsIndexables.test.ts` vert ; un `.xml` ordinaire reste lu en texte.
- **Critères observables.** Une carte Freeplane réelle indexée depuis le dossier de travail répond à « quelles sont les branches de ma carte Projet X ? », et `read_file` rend le résumé puis le plan.

### Lot 3 : processus BPMN

- **Moteur.** Extracteur `.bpmn` : processus, participants, couloirs, étapes typées, flux et conditions, sous-processus.
- **Écran.** Extension ajoutée à la liste de l'écran.
- **Données.** Rien.
- **Tests à écrire en premier.** Témoins Camunda Modeler et bpmn.io : couloirs et étapes rattachés ; passerelle exclusive avec deux conditions ; collaboration à deux participants ; sous-processus replié ; fichier sans diagramme (sans BPMNDI) lu quand même ; porte des promesses verte.
- **Critères observables.** « Qui valide la commande dans mon processus achats ? » trouve le couloir et l'étape.

### Lot 4 : plannings MS Project et GanttProject

- **Moteur.** Reconnaissance du XML MS Project sur les 4 premiers kilo-octets, extracteur MS Project, extracteur `.gan`.
- **Écran.** `.gan` ajoutée à la liste de l'écran (`.xml` y est déjà).
- **Données.** Rien.
- **Tests à écrire en premier.** Témoin ProjectLibre exporté en XML MS Project et témoin GanttProject : tâches, dates, durées, avancement ; prédécesseurs avec type et décalage négatif ; jalon ; `.xml` MS Project à `DOCTYPE` refusé ; `.xml` ordinaire à `DOCTYPE` toujours lu en texte ; porte des promesses verte.
- **Critères observables.** « Quelles tâches dépendent de la livraison du serveur ? » répond d'après les prédécesseurs du fichier.

### Lot 5 : tenir une carte Freeplane à jour, dans une copie

- **Moteur.** Outil `proposer_modification_carte`, classé ; exécution confirmée (empreinte, opérations, écriture de la copie) ; `.mm` dans la table de types du téléchargement.
- **Écran.** Carte de confirmation dédiée (opérations en phrases, plan avant et après), bouton « Télécharger », phrase « Ton original n'a pas été modifié ».
- **Données.** Un fichier dans `outputs`, rien en base.
- **Tests à écrire en premier.**
  - l'original est intact (SHA-256 avant et après) ; original modifié après la proposition : rien n'est écrit ;
  - un attribut inconnu, un commentaire et un attribut `script1` survivent à l'aller-retour, octet pour octet dans leur élément ;
  - **attribut `script` refusé** : une proposition qui tente d'écrire un attribut, sous n'importe quel nom, est refusée entière et rien n'est écrit ;
  - suppression impossible (aucune opération ne le permet) ; déplacement sous son propre descendant refusé ; nœud en texte enrichi non renommable ; texte échappé (`<`, `&`, guillemets) ;
  - copie dans `outputs`, jamais dans le dossier de l'originale ; nom sans deux-points, valide sous Windows (test du nom, et création réelle sur le job Windows de la CI) ; téléchargeable par la route existante ;
  - outil classé `MUTATION_LOCALE`, donc sous carte ; test de complétude des classes vert ;
  - vitest : la carte montre les opérations en phrases et ne crée rien avant « Confirmer ».
- **Critères observables.** Dans une conversation, « ajoute une branche Relance fournisseur sous Achats dans ma carte Projet X » produit une carte de confirmation ; après confirmation, la copie téléchargée s'ouvre dans Freeplane avec la branche, et l'original n'a pas bougé.

### Lot 6 : export du planning (différé)

Conditionné à la livraison de la saisie des durées et des dépendances (suite de P-039). Conditions fixées en section 5.5. Tests prévus : déterminisme (mêmes octets hors horodatage), dates Mermaid égales à celles du moteur avec SS, FF, SF et décalage négatif, échappement (`:`, `#`, `;`, `<`, retour à la ligne), GraphML valide relu par l'extracteur du lot 2, refus d'un plan à cycle, refus d'un instantané périmé (empreinte différente).

## 7. Réponse à la revue

### Constats

| # | Gravité | Constat | Réponse | Où, dans la V2 |
|---|---|---|---|---|
| 1 | P2 | L'export porte sur des plans que personne ne peut construire | Accepté, confirmé à HEAD (aucun constructeur de `TaskSchedule` ni de `TaskDependency` hors modèles, lecture et export RGPD). Décision 7 : lecture d'abord, export après la saisie du planning | 3, 4.2, 5.5 ; lot 6 différé |
| 2 | P2 | L'instantané n'a ni arcs ni jalons | Accepté. Condition fixée pour l'export : empreinte recalculée et comparée à `input_hash`, refus si elle diffère | 5.5 ; lot 6 |
| 3 | P2 | La finalité « documents » ne couvre pas `read_file` | Accepté, confirmé (`ChatInput.tsx:558-562`, `routers/chat.py:2519`). Décision 8 : les outils de fichiers ne sont offerts à un modèle en ligne qu'avec l'accord « documents » | 5.1 ; lot 1, placé avant tout nouveau format |
| 4 | P3 | Contradiction sur la mise en page yEd | Accepté. L'export pose lui-même des coordonnées simples ; l'écriture GraphML d'un fichier de l'utilisateur reste hors périmètre | 5.4, 5.5 |
| 5 | P3 | « P-107 en a besoin » est faux | Accepté. Argument retiré ; P-106 ne fournit aucun écrivain BPMN, et le dit à P-107 | 5.5 |
| 6 | P3 | « Bloc de code dans la conversation » sans chemin | Accepté. Promesse retirée : téléchargement seulement | 5.5 |
| 7 | P3 | Copie sans emplacement, deux-points sous Windows | Décision 9 : dossier `outputs` de THÉRÈSE ; nom sans deux-points, test Windows | 5.4 ; lot 5 |
| 8 | P3 | Freeplane peut exécuter des attributs `script` | Accepté. Liste fermée de quatre opérations, aucune écriture d'attribut, test « attribut `script` refusé » | 5.4 ; lot 5 |
| 9 | P3 | Question technique remontée à tort ; `lxml` transitif | Accepté et tranché en interne : `lxml` déclaré en dépendance directe, parseur `resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False`, refus de tout `DOCTYPE` | 5.2 ; lot 2 |

### Questions de la revue

| Question | Réponse | Où |
|---|---|---|
| Saisie du planning d'abord, ou lecture des fichiers de Dr_logic ? | Décision 7 : lecture d'abord, export après la saisie | 3, 5.5 |
| Un accord « documents » dédié pour la lecture en cours de conversation ? | Décision 8 : oui, exigé dès qu'un outil de lecture est offert à un modèle en ligne | 5.1 ; lot 1 |
| Où ranger la copie d'une carte modifiée ? | Décision 9 : dans un dossier de THÉRÈSE | 5.4 ; lot 5 |

### Questions de la V1 non reposées le 25/09

| Question V1 | Tranchée ici | Où |
|---|---|---|
| 1. L'ordre | Par la décision 7 | 3 |
| 2. Le format Gantt | XML MS Project (MS Project, ProjectLibre) et GanttProject | 5.3 ; lot 4 |
| 3. Copie ou écriture en place | Copie, par la décision 9 | 5.4 |
| 4. `defusedxml` ou `lxml` durci | `lxml` durci (constat 9) | 5.2 |
| 5. Préréglage MCP dédié | Non | 5.6 |

## 8. Corrections de la V1 trouvées en relisant le code

- **Lignes décalées.** L'arrêt de la chaîne d'outils sur une carte est à `routers/chat.py:3437-3445` (la V1 citait 3405-3414) ; le calcul de `finaliteCloud` à `ChatInput.tsx:558-562` (la revue citait 547-551).
- **Le texte de la V1 sur la souveraineté était faux** : il affirmait que le texte extrait partait « sous la finalité documents » (constat 3). Corrigé par la décision 8.
- **Sniffer tous les `.xml` aurait régressé.** La V1 prévoyait de reconnaître MS Project « à l'élément racine d'un `.xml` », ce qui supposait de parser tous les `.xml` ; avec le refus des `DOCTYPE`, des fichiers aujourd'hui lus en texte auraient été refusés. La V2 lit d'abord 4 kilo-octets en texte.
- **La lecture est bornée à 10 000 caractères** (`services/memory_tools.py:1516`) : d'où le résumé en tête de chaque extraction.
- **18 préréglages de connecteurs** à HEAD (`routers/mcp.py:311-513`), et non 19 comme l'annonce le `CLAUDE.md`.

## 9. Risques restants

- **Variété des fichiers réels.** Versions de Freeplane, graphes yEd avec ou sans yFiles, BPMN produits par d'autres modeleurs que Camunda, exports MS Project incomplets. Parade : fichiers témoins produits par les outils, et un format mal lu dit ce qu'il n'a pas compris plutôt que de deviner.
- **Grandes cartes.** Au-delà de 10 000 caractères, `read_file` tronque ; le résumé en tête garde la vue d'ensemble, mais une branche profonde peut manquer. La recherche dans l'index, elle, couvre tout le fichier.
- **Friction de l'accord.** Les utilisateurs qui n'ont donné que l'accord `llm` verront la ligne « Autoriser », et le modèle refusera de lire leurs fichiers tant qu'ils n'auront pas accepté. C'est voulu, mais cela peut surprendre ceux qui s'en servaient déjà.
- **Confiance dans l'écran.** Le serveur croit le champ `lecture_fichiers` que l'écran lui transmet, comme il croit aujourd'hui le consentement tenu par l'interface (`lib/consent.ts:44-67`). La valeur par défaut ferme.
- **Copies qui s'accumulent.** Chaque modification confirmée produit une copie dans `outputs` ; l'utilisateur remplace lui-même son original. Aucune purge automatique n'est prévue.
- **Export suspendu à P-039.** Tant que la saisie du planning n'est pas planifiée, le lot 6 n'a pas de date.
- **P-107.** Sa RFC doit être reprise sur ce point : elle comptait sur un écrivain BPMN qui n'existera pas ici.

## 10. Questions réservées à Ludo

Aucune. La copie d'une carte ne remplace jamais le fichier de l'utilisateur ; elle suit le sort déjà connu du dossier `outputs` (effacée avec « Effacer toutes mes données »). Rien n'est annoncé publiquement, rien ne touche à la marque.
