# Aude Perrin — j'ai rattaché mon dossier, l'application m'a dit qu'elle l'avait indexé, et elle n'a jamais retrouvé le fichier dont je lui donnais le nom exact

## Ce que j'ai fait

Dimanche soir, les filles couchées. Jeudi j'anime le cadrage chez Vermeer.
Le dossier est déjà sur mon disque (ma note de visite, le planning de
l'atelier, le budget prévisionnel). Je ne viens pas explorer, je viens
repartir avec une page à envoyer à Paul Vermeer.

**Minutes 0 à 4, rattacher le dossier.** J'ai créé le dossier « Vermeer
Industries », puis j'ai suivi les trois libellés de la section « Dossier
synchronisé » : **« Attacher »**, **« Préparer la synchronisation »**,
**« Appliquer »**. Les trois ont répondu comme promis. La préparation
m'annonce trois fichiers à indexer, zéro conflit. L'exécution passe à
`progression 1.0`, et le journal affiche mes trois fichiers en
`etat: "fait"`, `erreur: null`, avec une heure d'indexation. De mon côté
de l'écran, c'est un succès franc, et je n'ai aucune raison d'aller
vérifier.

**Minutes 4 à 7, je vérifie quand même.** Réflexe de consultante : je
regarde ce que l'application dit avoir rangé. Les trois fichiers sont bien
listés dans le dossier. Mais chacun affiche `chunk_count: 0` et
`content_hash: null`, et l'index sémantique contient **un seul point**, la
fiche du dossier, aucun de mes fichiers. Une recherche sur le nom exact de
ma note ne renvoie rien. Sur son contenu non plus.

**Minutes 7 à 11, je demande quand même.** J'ai rattaché la conversation au
dossier (le rattachement tient, je l'ai relu : `project_id` et
`memory_scope: "project"` sont enregistrés), et j'ai demandé : « Retrouve
la note de cadrage. Le fichier s'appelle `note-cadrage-vermeer.md` […]
cite-moi les trois questions à trancher jeudi. » Trois minutes de réponse,
le modèle est local et lent, je m'y attendais et je ne le lui reproche pas.
L'outil `search_files` est bien parti et a répondu en 27 millisecondes :
`{"found": false, "total": 0}`. Thérèse me l'a dit honnêtement, sans rien
inventer, et m'a conseillé de vérifier l'orthographe du nom puis
« d'activer le rattachement au projet Vermeer », qui était déjà actif.
J'ai quand même essayé son conseil à l'envers, en basculant la
conversation sur « tous les dossiers » pour être sûre que rien ne filtrait
mes fichiers : même réponse, `found: false`. Ce n'est donc pas une
histoire de périmètre.

**Minutes 11 à 14, produire la page.** « Nouveau document », rattaché au
dossier Vermeer, brief d'une page. « Générer la trame » a rendu la main en
une minute avec **treize sections**, toutes en `status: "vide"`,
`content: ""`. J'ai demandé « Exporter .md » pour voir : refus net et
honnête, `Document vide : rien à exporter.` Pour remplir ces treize
sections il n'existe qu'un bouton « Rédiger », section par section, et au
rythme que je viens de mesurer ce soir ma page d'une page me coûte une
demi-heure de clics. Je n'ai pas une demi-heure.

**Minutes 14 à 22, le point que mon dossier ne tranche pas.** La recherche
approfondie a très bien tourné : trois axes, vingt-trois sources
consultées, un rapport structuré qui se termine par une liste de neuf
sources cliquables. De ce côté, rien à redire, je peux aller vérifier.
Sauf que le rapport m'affirme qu'« une entreprise avec jusqu'à 8 salariés
peut être exemptée de l'obligation de facturation électronique », un seuil
qui reprend le chiffre de ma question et que je n'ai trouvé nulle part.
L'invention vient du modèle, je le sais. Ce qui me gêne, c'est qu'elle
m'arrive sans le petit indicateur de confiance que la même application
affiche sur une réponse de chat ordinaire.

**Ce que je retiens.** Mon dossier est intact, mes fichiers sont lisibles,
rien n'a été perdu. Mais entre « Appliquer » qui affiche « fait » et une
recherche par nom qui ne trouve rien, il y a un trou dans lequel je suis
tombée sans le voir. J'ai passé mon budget entier à vérifier une opération
que l'application m'avait déjà présentée comme réussie, et jeudi je vais
chez Vermeer avec ma note ouverte dans un éditeur de texte, comme avant.

## Dette connue rencontrée

| Dette | Je l'ai vue | Une ligne de preuve |
|---|---|---|
| 501 à l'envoi de facture | non | hors de mon geste, je n'ai touché aucune facture |
| TVA à 20 % par défaut | non | hors de mon geste |
| Notification après l'échéance | non | hors de mon geste |
| Pas de chemin pour un 2e calendrier | non | hors de mon geste |
| Cloison absente | non | hors mandat, je n'ai pas testé l'étanchéité |
| Pas d'écran « cabinet » | non | hors mandat |

## Correctifs tenus (0.54 / 0.55)

- **Le rattachement de conversation tient et se relit.** API : `PATCH
  /api/chat/conversations/{id}/project` puis `GET` sur la même
  conversation rendent `project_id` et `memory_scope: "project"`. Le cas
  fragile documenté dans `components/chat/ConversationProjectPicker.tsx:86`
  (conversation neuve non encore persistée) ne s'est pas produit.
- **La recherche approfondie ne plante pas à l'import.** API : le flux
  `POST /api/chat/deep-research` décompose en trois axes, exécute les trois
  recherches (5, 9 et 9 sources) et rend un rapport complet. Aucune erreur
  d'import, aucune interruption.
- **L'export refuse au lieu de livrer une coquille.** API : `GET
  /api/documents/{id}/export?format=md` sur un document à treize sections
  vides répond `400 {"message": "Document vide : rien à exporter."}`. Il ne
  me tend pas un fichier d'apparence finie que j'aurais envoyé sans le
  relire. C'est exactement le comportement qui m'évite le pire.
- **`Ouvrir <X>` nomme vraiment sa destination.** Code : le libellé dérive
  de `viewLabels`, la table que la vue utilise pour son propre titre
  (`components/prototype/BoutonOuvrirLaVue.tsx:31` et
  `components/prototype/PrototypeUnifiedViewCanvas.tsx:17-27,56`). Un
  bouton « Ouvrir Documents » ouvre un panneau intitulé « Documents », et
  un test rend le bouton pour chaque vue au lieu de comparer deux
  littéraux (`components/prototype/nomDeLaDestination.test.tsx:18`).
- **L'écran ne promet pas la confirmation que j'allais lui reprocher, il
  annonce franchement le contraire.** Code,
  `components/settings/PrivacyTab.tsx:281-287` : « ta requête part chez le
  moteur (DuckDuckGo par défaut) dès que l'assistante décide de chercher, y
  compris en modèle local, et sans te demander confirmation ». Le contrat
  est tenu parce qu'il est honnête. Pas de finding.

## Findings

### 1. L'indexation d'un dossier se déclare « fait » sans produire un seul chunk, et la recherche par nom de fichier retourne alors `found: false` — GRAVITÉ MAJEURE

**Ce qui s'est passé.** La chaîne « Attacher / Préparer la synchronisation
/ Appliquer » signale un succès complet à chacune de ses étapes visibles :
plan à trois fichiers sans conflit, exécution `etat: "done"` /
`progression: 1.0`, journal des opérations à `etat: "fait"`,
`erreur: null`, `attempt_count: 1` sur les trois. Chaque fichier reçoit
même un `indexed_at` horodaté. Mais aucun contenu n'entre dans l'index :
les trois ressortent avec `chunk_count: 0` et `content_hash: null`, et
`GET /api/config/stats/qdrant` rend `{"status": "GREEN",
"points_count": 1}` (le seul point est la fiche du dossier). Trois minutes
plus tard, toujours zéro.

Deuxième moitié, et je me garde d'affirmer qu'elle découle de la première :
l'outil `search_files` répond `{"found": false, "total": 0,
"documents": []}` en 27 ms sur le nom exact `note-cadrage-vermeer.md`,
alors que la même application liste ce fichier dans
`GET /api/memory/projects/{id}/files` et me sert son texte intégral sur
`GET /api/files/{id}/content`. **J'ai testé l'hypothèse du périmètre et je
l'écarte** : rebasculée en transversal (`project_id: null`,
`memory_scope: "all"`, le réglage qui n'exclut rien), la même demande rend
le même `{"found": false, "total": 0}` en 50 ms. L'échec ne dépend donc pas
de la cloison. Le fichier est là, lisible, nommé, et introuvable dans les
deux périmètres.

**Source.** API. `POST /api/projects/{id}/sync/plan` et `/sync/apply`,
`GET /api/projects/{id}/sync/journal`, `GET /api/memory/projects/{id}/files`,
`GET /api/config/stats/qdrant`, `POST /api/memory/search` (0 résultat sur
le nom comme sur le contenu), et l'événement `tool_result` de deux flux
`POST /api/chat/send` successifs, l'un en `memory_scope: "project"`,
l'autre en `memory_scope: "all"`.

**Ce que je n'ai pas déterminé.** Je constate deux ruptures et je ne dis
pas laquelle cause l'autre. Elles peuvent être indépendantes : l'index
sémantique vide gêne la recherche par le contenu, et la recherche par le
NOM est un tout autre chemin. Je laisse le diagnostic à qui connaît le
code, mais les deux symptômes sont reproductibles en trois appels.

**Libellés exacts lus.** « Dossier synchronisé », « Attacher », « Préparer
la synchronisation », « Appliquer »
(`components/memory/ProjectSyncSection.tsx:186,209,238,248`), et dans le
journal `"etat": "fait"`.

**Pourquoi ça compte pour moi.** C'est ma ligne rouge, prise du seul côté
par lequel elle pouvait m'atteindre. Le chat, lui, a été honnête : il m'a
dit qu'il ne trouvait pas. C'est la couche du dessous qui m'a affirmé un
travail qu'elle n'avait pas fait, avec une heure d'indexation à l'appui. Je
suis consultante : si je ne peux pas croire un « fait », je dois tout
revérifier à la main, et alors l'outil ne me fait rien gagner. Pire, un
« fait » mensonger est plus coûteux qu'une erreur franche, parce qu'il
m'enlève l'idée même d'aller regarder.

### 2. Aucun chemin ne mène à une page envoyable dans le temps d'une soirée : la trame produit treize sections vides, rédigeables une par une seulement — GRAVITÉ MAJEURE

**Ce qui s'est passé.** Mon brief demandait une page de synthèse d'une
page. « Générer la trame » a rendu treize sections (`Contexte du projet`,
`Projet`, `Stakeholders`, `Observations du 12 août`, `Synthèse des
constats`, `Points critiques`, `Hypothèses de travail`…), toutes en
`status: "vide"` et `content: ""`, sur trois niveaux de profondeur. Pour
obtenir la moindre ligne exportable, il faut ensuite cliquer « Rédiger »
sur chaque section : `SectionEditor.tsx:321` porte ce bouton, et le seul
appel de rédaction côté store est `draftSection`, branché section par
section depuis `DocumentWorkspace.tsx:202`. Il n'existe aucun « tout
rédiger ». **Je n'ai pas cliqué « Rédiger » : mon budget était déjà
épuisé.** Mon estimation vient des deux seules générations que j'ai
réellement mesurées ce soir, environ trois minutes pour la réponse de chat
et une minute pour la trame. À ce rythme, treize sections en série
représentent une demi-heure au bas mot, sans compter les retouches. Le
chiffre exact reste à mesurer ; le fait qu'il n'existe qu'un chemin
séquentiel, non.

**Source.** API pour la trame (`POST /api/documents/{id}/outline`, treize
sections à `status: "vide"`) et l'export
(`GET /api/documents/{id}/export?format=md` → `400 Document vide : rien à
exporter.`). Code pour l'absence de rédaction groupée :
`components/documents/SectionEditor.tsx:301,321` et
`components/documents/DocumentWorkspace.tsx:68,202`.

**Libellés exacts lus.** « Nouveau document », « Proposition, dossier ou
rapport structuré », « Générer la trame », « Pas encore de contenu - clique
sur « Rédiger » pour démarrer. », « Rédiger », « Exporter .md »,
« Exporter .docx ».

**Pourquoi ça compte pour moi.** Le sous-titre annonce « Proposition,
dossier ou rapport structuré » : la promesse porte sur le livrable, pas sur
un plan. Or ce que j'obtiens en une minute, c'est un sommaire que j'aurais
écrit moi-même en trois, et le vrai travail commence après, à un rythme que
je ne peux pas tenir un dimanche soir. Une trame de treize sections pour un
brief d'une page se trompe aussi d'échelle : je demandais une page, on me
propose un dossier. Le geste « produire un document » n'a pas de format
court, et c'est le seul dont j'aie besoin avant un atelier.

### 3. Le garde-fou d'incertitude ne tourne pas sur la recherche approfondie, alors qu'il tourne sur le chat — GRAVITÉ MODÉRÉE

**Correction que je dois à ma propre vérification.** J'ai d'abord cru que
les sources étaient perdues, parce que le serveur émet un événement
`{"type": "sources", "content": "[…23 entrées titre + url…]"}` que
l'interface n'exploite nulle part. C'est exact mais sans conséquence : en
relisant la fin du flux, le rapport se termine par une section `## Sources`
en Markdown avec les neuf liens numérotés, et mes appels de note `[1]` à
`[9]` y renvoient bien. Je peux vérifier. L'événement structuré est
redondant, pas manquant. Ce qui reste tient sur un seul point, et il est
vérifié des deux côtés.

**Ce qui s'est passé.** Le chemin de chat normal appelle
`setMessageMetadata(assistantMessageId, chunk.usage, chunk.uncertainty)`
(`ChatInput.tsx:719-721`), ce qui alimente le bandeau de confiance rendu
par `MessageBubble.tsx:606-625` (« confiance faible / moyenne », avec les
formulations douteuses en infobulle). Sur ma question de facturation
électronique, `handleDeepResearch` ne l'appelle jamais : sa boucle de
consommation (`ChatInput.tsx:848-871`) traite `text`, `decomposition`,
`searching`, `search_done`, `synthesizing` et `error`, et rien d'autre.
Côté serveur, l'événement `done` de `deep-research` est nu
(`{"type": "done", "content": ""}`), là où celui de `/api/chat/send` m'a
renvoyé un bloc complet `{"is_uncertain": false, "confidence_score": 100,
"confidence_level": "high", "should_verify": false}`. Le calcul
d'incertitude n'est donc ni fait ni transmis ni affiché sur cette surface.

**Source.** API pour les deux flux comparés (`POST /api/chat/deep-research`
et `POST /api/chat/send`, événements `done` de chacun). Code pour le
traitement : `src/frontend/src/components/chat/ChatInput.tsx:719-721` et
`848-871`, `src/frontend/src/components/chat/MessageBubble.tsx:606-625`.

**Libellés exacts lus.** « Recherche approfondie (multi-sources) » et
« Lancer une recherche approfondie » (`ChatInput.tsx:1367-1368`),
« Lancement de la recherche approfondie... », « Rédaction du rapport... ».

**Pourquoi ça compte pour moi.** J'appuie sur ce bouton précisément quand
la réponse n'est pas dans mon dossier, donc quand je suis le moins capable
de juger ce qu'on me répond. Le rapport m'a affirmé une exemption « jusqu'à
8 salariés » que le modèle a inventée : ça, c'est sa limite, je la lui
accorde et je ne la lui reproche pas. Mais l'application sait fabriquer un
signal de confiance, elle me le montre sur une simple question de chat, et
elle le retire exactement là où j'en ai le plus besoin. Un rapport titré,
sourcé, numéroté et sans la moindre réserve affichée, c'est le format qui
donne le plus envie de faire un copier-coller. Si je recopie cette phrase
dans une page à en-tête Vermeer, c'est mon nom dessus, pas le sien.

## Ai-je abandonné ?

Oui. Pas sur ma ligne rouge (le chat ne m'a jamais affirmé avoir trouvé ce
qu'il n'avait pas trouvé, il a été honnête), mais sur le temps : à vingt
minutes je n'avais toujours pas de page, et le seul chemin restant était
treize rédactions en série. Je prépare Vermeer dans mon éditeur de texte,
et je réessaierai quand « fait » voudra dire fait.
