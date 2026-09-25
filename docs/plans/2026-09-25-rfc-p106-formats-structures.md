# RFC P-106 : lire et exporter des formats structurés

Rédigé le 25/09/2026. Proposition S6 de Dr_logic-3D, acceptée par Ludo le 25/09 avec la recommandation du triage : « plus tard, commencer par l'export Mermaid/GraphML des projets (prolonge P-039) ». Aucun code avant la validation de ce document.

Chemins relatifs à `src/backend/app/` et à `src/frontend/src/`, sauf mention contraire.

## 1. Le besoin

Dr_logic-3D, testeur alpha, sur Discord (#discussion et fil du 25/09, 03:35 à 04:29) :

- Il tient ses sujets dans des représentations structurées : cartes mentales Freeplane (`.mm`), graphes yEd (`.graphml`), processus BPMN, plannings Gantt.
- À chaque évolution d'un sujet, il met ces fichiers à jour à la main.
- Il voudrait que THÉRÈSE les lise et les tienne à jour, par MCP ou par import et export, plutôt que par le seul chat.

## 2. Ce qui existe déjà

**Points d'appui :**

- Le moteur PERT/CPM de P-039 est pur et déterministe (`services/planning.py:1-28`). Il gère quatre types de dépendances avec décalage (`models/entities.py:659-680`), des durées à trois points (`:601-626`) et des instantanés relus sans recalcul (`routers/planning.py:297-310`). Aucun écran Gantt ne l'affiche encore.
- `lxml` est déjà dans le verrou, par python-docx : lire et écrire du XML ne demande aucune nouvelle bibliothèque.
- Un fichier indexé est lisible par le modèle via `search_files` et `read_file`, deux lectures qui passent sans carte (`services/contexte_execution.py:48-49`).
- La porte `tests/test_extensions_promises_tenues.py` interdit d'accepter une extension que le parseur ne sait pas extraire.

**Manques :**

- `.mm`, `.graphml`, `.bpmn` et `.gan` ne figurent dans aucune des quatre listes d'extensions (`services/path_security.py:263-283`, `services/file_parser.py:31-72`, `routers/files.py:427`, `lib/formatsIndexables.ts:23`). Un export XML de MS Project passe, mais comme `.xml` brut (`file_parser.py:49`) : le modèle reçoit des balises, pas un plan.
- Les skills Office créent des fichiers neufs à partir de code généré, exécuté en bac à sable (`services/skills/base.py:18-25`, `services/skills/code_executor.py:73`). Aucune ne modifie un fichier existant.
- Aucun des 18 préréglages MCP ne connaît ces formats (`routers/mcp.py:306-521` ; le CLAUDE.md en annonce 19). Surtout, la voie MCP ne sait pas aujourd'hui « lire puis mettre à jour » :
  - tout outil MCP passe par une carte, lecture comprise (`services/tool_confirmations.py:34-50`) ;
  - dès qu'une carte attend, la chaîne d'outils s'arrête (`routers/chat.py:3405-3414`) ;
  - le résultat confirmé revient à l'écran, pas au modèle (`components/chat/ToolConfirmationCard.tsx:117-130`).
- L'interface n'a aucun rendu Mermaid : un diagramme s'y afficherait en bloc de code.

## 3. Quatre options

| | A. Export depuis P-039 | B. Lecture structurée | C. Mise à jour conservatrice | D. Serveur MCP tiers |
|---|---|---|---|---|
| Idée | Le plan d'un projet exporté en Mermaid `gantt` et en GraphML (tâches, dépendances, chemin critique), en fichiers neufs | Un extracteur par format : plan indenté (carte), nœuds et arcs (graphe), couloirs, étapes et flux (BPMN), tableau de tâches (Gantt) | Des opérations bornées (ajouter, renommer, déplacer un nœud, poser une note) appliquées à l'arbre XML d'origine, écrites dans une copie | Ajouter à la main un serveur MCP qui manipule ces formats |
| Pour | Petit, déterministe ; ne touche aucun fichier de l'utilisateur ; recommandé par le triage | Répond au « lire », sans aucune écriture ; le modèle lit sans carte | Répond au « mettre à jour » sans perdre styles, icônes ni extensions yEd | Peu de code chez nous |
| Contre | Ne lit pas ses fichiers. Mermaid ne connaît que la dépendance « après » : SS, FF, SF et décalages deviennent des dates calculées. yEd n'affiche les libellés qu'avec l'extension yFiles | Quatre extracteurs et leurs fichiers témoins ; `.gan` et MSPDI varient selon les outils | BPMN et GraphML portent des coordonnées : un nœud ajouté sans position est invisible ou empilé. Seul Freeplane s'en passe | Chaîne coupée (voir section 2) ; paquets npm non revus ; comportement hors de nos tests |
| Effort | Petit | Moyen | Moyen pour Freeplane, large pour BPMN et GraphML | Petit chez nous, risque élevé |

## 4. Recommandation : A, puis B, puis C pour Freeplane seulement

### Premier lot : exporter le plan d'un projet (A)

- **Exporteurs purs**, voisins du moteur (`services/planning_export.py`). Ils partent d'un instantané `PlanningSnapshot` : on exporte exactement ce qui a été calculé et affiché.
- **Mermaid `gantt`** :
  - dates de début et de fin calculées, tâches critiques marquées `crit`, jalons ;
  - une ligne d'en-tête qui dit que les types de dépendances ne sont pas représentés ;
  - livré en fichier `.mmd` et en bloc de code dans la conversation.
- **GraphML** :
  - une tâche par nœud, une dépendance par arc, avec type et décalage en attributs ;
  - le chemin critique en attribut ;
  - l'extension yFiles (`y:ShapeNode`, `y:NodeLabel`) pour que yEd affiche les libellés, sans coordonnées : la mise en page hiérarchique de yEd les calcule.
- **Plans défectueux** : un plan `invalid` (cycle) est refusé explicitement ; un plan `incomplete` est exporté, avec la mention en tête.
- **Route** `GET /api/projects/{id}/schedule/snapshots/{snapshot_id}/export?format=mermaid|graphml`, téléchargement par le mécanisme existant. Aucun LLM.

### Deuxième lot : lire (B)

- **Formats lus** : `.mm`, `.graphml`, `.bpmn`, `.gan`. MSPDI est reconnu à l'élément racine d'un `.xml` (espace de noms `http://schemas.microsoft.com/project`) ; les autres `.xml` restent lus en texte.
- Les quatre listes d'extensions changent ensemble, sous la porte existante.
- **Parseur durci** (voir la section 8). Les plafonds de nœuds et de profondeur sont annoncés dans le texte extrait, comme pour le PDF et le tableur (`file_parser.py:199-201`, `:283-289`).

### Troisième lot : mettre à jour une carte Freeplane (C, limité)

- **Outil** `proposer_modification_carte` : une mutation locale, donc sous carte. Une carte dédiée montre la liste des opérations et le plan avant et après, pas des arguments bruts (`ToolConfirmationCard.tsx:85-102`).
- **Écriture dans une copie horodatée, jamais par-dessus l'original.** Les attributs et éléments inconnus sont conservés tels quels.
- **BPMN et GraphML en écriture** : hors périmètre tant que la question des coordonnées n'est pas tranchée.

## 5. Décisions attendues de Ludo

1. **L'ordre** : export d'abord (triage) ou lecture d'abord (besoin exprimé) ? Recommandation : export, plus petit, et P-107 en a besoin.
2. **Le Gantt** : quel format compte pour Dr_logic (GanttProject, MS Project XML, ProjectLibre) ? Le `.mpp` binaire est exclu.
3. **L'écriture** : copie seulement, ou écriture en place avec `.bak` ? Recommandation : copie seulement.
4. **Le parseur** : nouvelle dépendance `defusedxml`, ou `lxml` durci à la main ?
5. **Un préréglage MCP dédié** ? Recommandation : non, tant qu'un résultat confirmé ne revient pas au modèle.

## 6. Livraison proposée

1. Design court et revue adverse du design.
2. Exporteurs Mermaid et GraphML, sur les données de démonstration (TDD).
3. Route d'export et bouton dans la vue projet.
4. Lot 2 : extracteurs, listes d'extensions, fichiers témoins.
5. Lot 3 : opérations Freeplane et carte dédiée.

Chaque lot fait l'objet d'un commit, avec sabotage des tests et revue adverse du diff.

## 7. Plan de tests

- **Déterminisme** : un même instantané donne les mêmes octets, hors horodatage d'en-tête.
- **Fidélité au moteur** : un plan avec SS, FF, SF et un décalage négatif produit en Mermaid les dates du moteur, au jour près.
- **Échappement** : un titre avec `:`, `#`, `;`, `<` ou un retour à la ligne ne casse ni la syntaxe Mermaid ni le XML.
- **GraphML** : XML valide, un arc par dépendance, identifiants stables. Relu par l'extracteur du lot 2 dès qu'il existe (aller-retour).
- **Refus** : un plan à cycle est refusé avec un message lisible ; un plan incomplet est marqué.
- **Lot 2** :
  - un fichier avec DTD, entité externe (`file:///etc/passwd`) ou expansion exponentielle est refusé, sans que le fichier visé soit lu ;
  - fichiers témoins issus de Freeplane, yEd, Camunda Modeler et GanttProject.
- **Lot 3** : l'original reste intact (empreinte avant et après) ; un attribut inconnu survit à l'aller-retour.
- **Sabotage** ciblé par fonction de chaque garde (échappement, refus de DTD).

## 8. Risques

- **Sécurité, XML reçu d'un tiers** : un `.mm` ou un `.bpmn` peut porter une entité externe (lecture d'un fichier local, requête réseau) ou une expansion exponentielle. Parade : ni DTD, ni entités, ni réseau, et `huge_tree` refusé. `defusedxml` n'est pas dans le verrou aujourd'hui.
- **Injection de consigne** : le texte d'une carte arrive au modèle comme tout document, sous l'enveloppe des fichiers (`routers/chat.py:420-426`, `services/memory_tools.py:1620-1628`). Aucune voie plus directe.
- **Perte de données** : réécrire un fichier qu'on ne comprend qu'en partie efface le reste (styles, icônes, coordonnées). D'où l'écriture par opérations sur l'arbre d'origine, dans une copie.
- **Fausse fidélité** : un Mermaid ne représente pas les dépendances SS, FF et SF ; l'en-tête du fichier le dit.
- **Souveraineté** : tout se passe en local. Seul le texte extrait peut partir vers le fournisseur de la conversation, sous la finalité `documents` du consentement (`lib/consent.ts:26`).

## Annexe : appuis dans le code

- Origine : `.app-loop/proposals.json`, P-106 (triage du 25/09).
- Moteur : `services/planning.py:20-28` (version, états, types de dépendances), `:433` (`calculate_schedule`). Route `routers/planning.py:171`, sous le préfixe `/api/projects` (`main.py:899`).
- Indexation : `services/indexation.py:186-202` (dossiers choisis) ; `services/path_security.py:280` (`.xml` accepté en texte).
- MCP : `routers/mcp.py:311-319` (Filesystem, risque moyen) ; `routers/chat.py:3042-3150` (portillon), `:3483-3562` (confirmation).
