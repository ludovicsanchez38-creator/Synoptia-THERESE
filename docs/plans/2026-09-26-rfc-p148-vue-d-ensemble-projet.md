# RFC P-148 : ouvrir un projet montre ce qu'il rassemble, et y mène

Rédigé le 26/09/2026. Proposition acceptée le 25/09 (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md:199`). Aucune question n'est laissée à Ludo : ce chantier ne crée ni n'efface aucune donnée, il montre des liens qui existent déjà.

## 1. Le constat

L'état vide de la vue Projets fait une promesse : « Crée ton premier projet pour rassembler les contacts, documents et tâches d'une même affaire » (`src/frontend/src/components/memory/ProjectsPanel.tsx:233`). Une fois le projet créé, cliquer sa carte ouvre `ProjectModal` en mode édition (`ProjectsPanel.tsx:120-123`, rendu l.271-279). Cette fenêtre s'intitule « Modifier le projet » (`src/frontend/src/components/memory/ProjectModal.tsx:371-376`) et empile :

- le formulaire : nom, description, statut, contact associé, budget, notes (l.393-465), puis les étiquettes (l.544-553) ;
- le dossier synchronisé (l.467-470) ;
- les livrables, depuis P-153 (l.472-475, `ProjectDeliverablesSection.tsx`) ;
- les fichiers joints au projet, avec ajout et suppression (l.477-542).

Ce qui manque pour tenir la promesse : les **conversations** du projet, ses **documents** rédigés dans l'atelier, ses **tâches** (une tâche se rattache à un projet depuis P-150, mais la fenêtre du projet ne les montre pas), et un chemin vers la **fiche** du contact, qui n'est qu'un sélecteur (l.425-441). Rien, dans cette fenêtre, ne mène ailleurs.

Deux défauts voisins tiennent à la même absence :

- dans la palette, un projet trouvé ouvre la liste des projets, pas le projet (`src/frontend/src/components/prototype/ConversationCanvasPrototype.tsx:1402-1403`) ;
- la confirmation de suppression dit seulement « Cette action est irréversible » (`ProjectModal.tsx:592-617`), alors que supprimer un projet supprime ses tâches et ses livrables, et détache ses conversations, ses documents et ses rendez-vous (`src/backend/app/routers/memory.py:361-450`).

## 2. Ce que le moteur relie déjà à un projet

Le relevé le plus sûr est la fonction qui défait ces liens à la suppression, `_nettoyer_et_supprimer_projet` (`memory.py:361-450`) : elle énumère fichiers, conversations, documents, rendez-vous, tâches et livrables, et son rapport les compte (l.444-451).

| Famille | Lien en base | Route qui lit par projet | Écran qui y mène aujourd'hui |
|---|---|---|---|
| Conversations | `Conversation.project_id` (`src/backend/app/models/entities.py:177`) | **aucune** : `GET /api/chat/conversations` n'a que `limit` et `offset` (`src/backend/app/routers/chat.py:3610-3618`) | le sélecteur de projet de chaque conversation, un par un |
| Documents de l'atelier | `Document.project_id` (`entities.py:960`), vérifié à la création (`src/backend/app/routers/documents.py:195-200`) | **aucune** : `GET /api/documents` rend tout (`documents.py:214-240`) | aucun |
| Fichiers joints | `FileMetadata.scope = "project"`, `scope_id` (`entities.py:233-234`) | `GET /api/memory/projects/{id}/files`, borné et tronqué (`memory.py:1298-1323`) | la fenêtre du projet |
| Tâches | `Task.project_id` (`entities.py:563`) | `GET /api/tasks?project_id=` (`src/backend/app/routers/tasks.py:63-92`) | le filtre « Filtrer par projet » de la vue Tâches (`src/frontend/src/components/tasks/TasksPanel.tsx:288-299`), porté par `filterProjectId` (`src/frontend/src/stores/taskStore.ts:45`, `126`) |
| Livrables | `Deliverable.project_id` (`entities.py:885`) | `GET /api/crm/deliverables?project_id=` (`src/backend/app/routers/crm.py:258-281`) | la fenêtre du projet (P-153) |
| Contact associé | `Project.contact_id` (`entities.py:89`) | `GET /api/memory/contacts/{id}` (`memory.py:854`) | le sélecteur de la fenêtre, sans lien vers la fiche |
| Contacts créés dans le projet | `Contact.scope = "project"`, `scope_id` (`entities.py:53-54`) | `GET /api/memory/contacts?scope=project&scope_id=…&include_global=false` (`memory.py:668-702`) | aucun |
| Rendez-vous | `CalendarEvent.project_id` (`entities.py:515-519`) | aucune | aucun |
| Planning | tables de P-039 | `GET /api/projects/{id}/schedule` (`src/backend/app/routers/planning.py:171`, préfixe `src/backend/app/main.py:899`) | aucun (lots B à D de P-039) |

Les gestes pour **mener** à chaque famille existent aussi, dans la coque :

- ouvrir une conversation : `loadConversation` puis `openChat` (`ConversationCanvasPrototype.tsx:1417-1420`) ;
- ouvrir un document : `demanderLOuverture` (`src/frontend/src/stores/documentStore.ts:269`), que la liste des documents consomme (`src/frontend/src/components/documents/DocumentsList.tsx:179-182`) ;
- ouvrir une fiche : `chooseScenario('memory')` puis `setSelectedContactId` (`ConversationCanvasPrototype.tsx:2169-2171`) ;
- montrer les tâches d'un projet : `setFilterProjectId` (`taskStore.ts:126`) puis la vue Tâches, qui recharge au changement de filtre (`TasksPanel.tsx:117`, `168`).

Et un canal existe pour qu'un composant hors de la coque demande une ouverture : l'événement `therese:ouvrir-travail` de P-140 (`src/frontend/src/lib/destinationDuTravail.ts:12-20`, `46-67`), écouté par la coque (`ConversationCanvasPrototype.tsx:1430-1437`) et émis par le panneau Travaux (`src/frontend/src/components/traitements/TraitementsPanel.tsx:100`).

## 3. Décision : pas de nouvel écran

Le constat de Ludo du 27/08 (« je trouve qu'il y a trop d'interfaces ») a été instruit dans le code : la cause n'était pas le nombre d'écrans mais leur imprévisibilité, et deux surfaces qui se ressemblent sans rien partager font douter (`CLAUDE.md` du dépôt, rapport 0.49.0 ; `docs/rules/RULES-DESIGN.md:364-370`). D'où trois refus :

- **pas de vue « Projet » de plus** dans le rail ni dans `APP_VIEWS` (`src/frontend/src/stores/navigationStore.ts:24-35`) ;
- **pas de nouveaux gestes de création** dans le projet (« nouvelle conversation ici », « nouvelle tâche ici ») : la promesse dit « y mène », et chaque famille a déjà son geste de rattachement, que l'état vide de chaque ligne nomme ;
- **pas de seconde mécanique de navigation** : on étend `DestinationDuTravail`, on n'invente pas un deuxième bus.

**La fenêtre du projet devient une vue d'ensemble d'abord, un formulaire ensuite.** En mode édition, dans cet ordre :

1. **Ce que rassemble ce projet** : quatre lignes nouvelles (Conversations, Documents, Tâches, Contacts) ;
2. les sections existantes, remontées sous le même intitulé : Livrables (P-153), Fichiers du projet, Dossier synchronisé ;
3. **Informations du projet** : le formulaire actuel, inchangé.

Le mode création (« Nouveau projet ») ne change pas.

## 4. Conception

### 4.1 Le moteur : une lecture, une définition

Une route en lecture seule, `GET /api/memory/projects/{project_id}/ensemble?limite=5`, servie par un service neuf, `src/backend/app/services/projet_ensemble.py`. Pourquoi une route agrégée plutôt que deux filtres de plus et six appels depuis l'écran :

- **une seule définition** de ce qu'un projet rassemble, partagée avec la suppression (lot 4). C'est la leçon des relances : deux surfaces qui réécrivent le même filtre finissent par répondre deux chiffres (`tests/test_relance_une_seule_definition.py:1-9`) ;
- **un seul état de chargement** dans la fenêtre, au lieu de quatre sections qui chargent et échouent chacune à leur rythme ;
- **pas de plafond client** : le tiroir charge au plus 500 conversations (`src/frontend/src/hooks/useConversationSync.ts:85-103`), un filtre côté écran mentirait au-delà.

Réponse (clés françaises, comme `/api/dashboard/semaine`) :

```json
{
  "conversations": { "total": 7, "elements": [{ "id": "…", "titre": "…", "mise_a_jour": "…" }] },
  "documents":     { "total": 2, "elements": [{ "id": "…", "titre": "…", "statut": "en_cours", "mise_a_jour": "…" }] },
  "taches":        { "total": 9, "ouvertes": 4, "en_retard": 1,
                     "elements": [{ "id": "…", "titre": "…", "statut": "todo", "echeance": "…" }] },
  "contacts":      { "associe": { "id": "…", "nom": "…" },
                     "du_projet": { "total": 1, "elements": [{ "id": "…", "nom": "…", "entreprise": "…" }] } },
  "livrables":     { "total": 3 },
  "fichiers":      { "total": 12 },
  "rendez_vous":   { "total": 2 },
  "indisponibles": []
}
```

Règles :

- **404** si le projet n'existe pas. `limite` entre 1 et 200, comme la liste des conversations (`chat.py:3616`) ; défaut 5.
- **Tri** : conversations et documents du plus récent au plus ancien ; tâches ouvertes (`todo`, `in_progress`) d'abord, puis par échéance, sans échéance en dernier. Le service ne réutilise pas les rangs privés du routeur des tâches : un service n'importe pas un routeur (règle écrite dans `src/backend/app/routers/prestations.py:28-30`).
- **En retard** : échéance antérieure au jour civil de Paris (`date_civile_paris`, `src/backend/app/services/civil_time.py:9`), tâche ouverte.
- **Chaque famille se dégrade seule** et se nomme dans `indisponibles`, comme `/semaine` (`src/backend/app/routers/dashboard.py:555-556`). Une panne n'est pas un vide.
- **Les conversations sont listées quel que soit leur `memory_scope`**. Aucun modèle ne lit cette route : elle montre à l'utilisatrice ses propres liens, la cloison documentaire n'est pas en jeu.
- Livrables, fichiers et rendez-vous ne rendent qu'un total : les deux premiers ont déjà leur section, le troisième ne sert qu'à la confirmation de suppression (§4.4).

### 4.2 L'écran : quatre lignes

Un composant générique, `VueDEnsemble` (liste de familles : libellé, total, éléments, texte du vide, action « tout afficher »), et un composant qui le nourrit, `ProjectEnsembleSection`, sur le patron de `ProjectDeliverablesSection` (chargement, panne, vide distincts). Le générique servira tel quel à la fenêtre du fil de travail (P-104 V2).

| Ligne | Éléments (5 au plus) | « Tout afficher » | Vide |
|---|---|---|---|
| Conversations | titre, date relative | recharge avec `limite=200` sur place, « liste incomplète » au-delà | « Aucune conversation rattachée. Une conversation se rattache depuis son sélecteur de projet. » |
| Documents | titre, « En cours » ou « Terminé » | idem | « Aucun document. Un document se rattache à un projet à sa création. » |
| Tâches | titre, échéance ; en tête « 4 ouvertes, dont 1 en retard » | « Voir les 9 tâches dans Tâches » (vue Tâches filtrée sur le projet) | « Aucune tâche. Une tâche se rattache à un projet depuis son formulaire. » |
| Contacts | contact associé, puis contacts créés dans le projet | recharge sur place | « Aucun contact associé : choisis-le plus bas, dans Informations du projet. » |

Détails qui comptent :

- **Titre et focus.** En édition, la fenêtre porte le nom du projet (masqué en démonstration) et le sous-titre « Ce qu'il rassemble, puis ses informations » ; son nom accessible devient « Projet {nom} ». Le focus initial va sur ce titre (`tabIndex={-1}` et `data-dialog-autofocus`, comme `src/frontend/src/components/prototype/FollowUpsWorkspaceCanvas.tsx:182`), plus sur le champ « Nom » (`ProjectModal.tsx:394`) : sinon l'ouverture ferait défiler la fenêtre jusqu'au formulaire et cacherait la vue d'ensemble. En création, le champ « Nom » garde le focus.
- **Démonstration** : chaque texte passe par le `maskText` de la fenêtre (`ProjectModal.tsx:98-104`), qui refuse de révéler un texte tant que les contacts ne sont pas chargés. Les liens restent actifs : ils mènent en lecture, comme partout en démonstration.
- **Accessibilité** : chaque ligne est une liste nommée par son libellé et son total ; chaque élément est un vrai bouton dont le nom dit la destination (« Ouvrir la conversation Devis cuisine ») ; le total est dans le texte, jamais seulement dans une pastille.
- **La promesse de l'état vide** devient exacte et complète : « Crée ton premier projet pour rassembler les conversations, documents, tâches et contacts d'une même affaire. »

### 4.3 Y mener

`DestinationDuTravail` (`destinationDuTravail.ts:12-17`) gagne deux cas, et `ActionsDOuverture` (l.46-52) deux actions :

- `{ kind: 'contact'; id }` et `ouvrirContact(id)`, que la coque implémente comme `CetteSemaine` (`ConversationCanvasPrototype.tsx:2169-2171`) ;
- `{ kind: 'taches-du-projet'; projetId }` et `ouvrirLesTachesDuProjet(projetId)` : `setFilterProjectId(projetId)` puis `openEmbeddedView('tasks')`. Le filtre n'est pas persisté (`taskStore.ts:131-137`) et il se voit dans son sélecteur : on le retire d'un geste.

Conversations et documents réutilisent les cas existants (`conversation`, `document`).

Le déroulé d'un clic dans la fenêtre :

1. **Saisie modifiée** (B-1392, `ProjectModal.tsx:115-122`) : la destination est retenue et la question « Abandonner les modifications ? » s'affiche ; « Abandonner » poursuit, « Continuer la saisie » annule la navigation.
2. **Émission** de `therese:ouvrir-travail` en événement **annulable**. La coque appelle `preventDefault()` quand elle refuse, c'est-à-dire quand `blockStreamingNavigation` dit non (réponse en cours, `ConversationCanvasPrototype.tsx:1076-1088`). `dispatchEvent` rend alors `false`.
3. **Fermeture** de la fenêtre seulement si l'ouverture a été acceptée. Une navigation refusée laisse la fenêtre ouverte, avec l'avertissement « Réponse en cours » que la coque affiche déjà.

La fenêtre est rendue à deux endroits, la vue Projets et le conteneur global des panneaux (`src/frontend/src/components/chat/PanelContainer.tsx:124-129`) : le bus fonctionne pour les deux, puisque `onClose` est fourni par chacun.

### 4.4 La suppression dit ce qu'elle emporte

La confirmation lit les totaux de la même route et les écrit : « 9 tâches et 3 livrables seront supprimés, ainsi que 12 fichiers joints. 7 conversations, 2 documents et 2 rendez-vous resteront, détachés du projet. » Une famille à zéro est omise. Les conversations détachées perdent leur cloison de projet et reviennent aux documents généraux (`memory.py:400-408`) : la phrase le dit.

Pour que le compte annoncé soit le compte exécuté, `_nettoyer_et_supprimer_projet` et le service lisent **les mêmes prédicats**, exposés par `projet_ensemble.py` (une fonction par famille qui rend sa clause `where`). Ce partage est posé dès le lot 1, avec le test qui fige l'égalité entre les totaux annoncés et le rapport de suppression : sans lui, la route naîtrait avec une seconde définition de ce qu'un projet rassemble, ce que le §4.1 veut précisément éviter.

### 4.5 La palette ouvre le projet

`usePanelStore` gagne `openEditProject(project)`, jumeau de `openEditContact` (`src/frontend/src/stores/panelStore.ts:78`) : il pose `editingProject` et `showProjectModal` (l.53, `187-188`). `ouvrirUneDonnee` (`ConversationCanvasPrototype.tsx:1397-1408`) lit le projet par `getProject` (`src/frontend/src/services/api/memory.ts:160`) et ouvre sa fenêtre. Un projet supprimé entre-temps donne une notification « Ce projet n'existe plus », jamais une fenêtre vide.

## 5. Mise en œuvre, lot par lot

Chaque lot : tests écrits d'abord et vus rouges, sabotage ciblé par fonction, un commit, revue adverse du diff.

### Lot 1 : la route d'ensemble, sur une définition partagée

Le service expose une fonction par famille qui rend sa clause `where` ; la route et `_nettoyer_et_supprimer_projet` (`memory.py:361-450`) les lisent toutes deux, dans ce même lot.

Tests à écrire d'abord (pytest, nouveau `tests/test_p148_ensemble_du_projet.py`) :
- 404 pour un projet inconnu ; 422 pour `limite=0` et `limite=201` ;
- une base avec du bruit (autre projet, conversation sans projet, contact rangé dans un autre projet, fichier global) : chaque total ne compte que ce projet ;
- ordre des conversations et documents par `updated_at` décroissant ; tâches ouvertes d'abord, échéance croissante, sans échéance en dernier ;
- `en_retard` bascule à minuit de Paris, pas à minuit UTC ;
- une conversation en `memory_scope = "all"` rattachée au projet est listée ;
- une famille dont la lecture échoue est nommée dans `indisponibles`, les autres sont rendues ;
- sur une même base, les totaux de la route égalent le rapport de `DELETE /api/memory/projects/{id}` (`memory.py:1389`) pour les six familles, et les tests existants de la suppression d'un projet restent verts sans retouche.

Critère observable : sur la base de démonstration, `curl` de la route rend les mêmes totaux que les écrans Tâches (filtré), Livrables et Fichiers.

### Lot 2 : la vue d'ensemble dans la fenêtre

Tests à écrire d'abord (vitest) :
- en édition, les quatre lignes précèdent Livrables, Fichiers et Dossier synchronisé, qui précèdent « Informations du projet » ;
- le focus initial est sur le titre du projet en édition, sur « Nom » en création ;
- chargement, panne (bandeau `role="alert"` avec « Réessayer ») et vide sont trois rendus distincts, par ligne ;
- « Tout afficher » recharge avec `limite=200` et dit « liste incomplète » si le total dépasse ;
- en démonstration, aucun titre ni nom n'apparaît en clair avant le chargement des contacts ;
- `ModalesHorsChamp.c12.test.tsx` et `ProjectModal.livrables.p153.test.tsx` restent verts sans retouche de leurs attentes ;
- l'état vide de `ProjectsPanel` porte la nouvelle phrase.

Critère observable : dans l'application lancée, ouvrir un projet montre d'un coup d'œil ses conversations, documents, tâches et contacts, sans défiler.

### Lot 3 : y mener

Tests à écrire d'abord (vitest) :
- `destinationDuTravail.p140.test.ts` : les deux nouveaux cas appellent la bonne action, les anciens sont intacts ;
- un clic sur une conversation émet `{ kind: 'conversation', id }`, ferme la fenêtre, et le focus arrive dans le composeur (pas sur `BODY`) ;
- un clic sur « Voir les 9 tâches » pose le filtre projet puis ouvre Tâches ;
- un clic sur le contact associé ouvre sa fiche ;
- avec une saisie modifiée, la question d'abandon passe avant la navigation ; « Continuer la saisie » annule ;
- pendant une réponse en cours, la navigation est refusée et la fenêtre reste ouverte ;
- les mêmes gestes fonctionnent depuis la fenêtre ouverte par le conteneur global.

Critère observable : depuis un projet, chaque famille s'ouvre en un clic, sans passer par sa liste générale, et la fenêtre du projet ne reste jamais ouverte par-dessus la destination.

### Lot 4 : la suppression qui dit ce qu'elle emporte

Le moteur est prêt depuis le lot 1 ; ce lot n'écrit que la confirmation.

Tests à écrire d'abord (vitest) : la confirmation écrit les familles non nulles, omet les nulles, et dit que les conversations reviennent aux documents généraux ; une lecture des totaux en panne laisse la confirmation d'aujourd'hui (« Cette action est irréversible »), jamais un « 0 tâche » inventé.

### Lot 5 : la palette ouvre le projet

Tests à écrire d'abord (vitest) : mise à jour de `ConversationCanvasPrototype.paletteDonnees.p016.test.tsx` (un projet trouvé ouvre sa fenêtre) ; `openEditProject` pose le projet et ouvre la fenêtre ; un projet disparu donne la notification.

### Lot 6 : recette

Dans l'application lancée, sur les données de démonstration puis en mode démonstration : un projet avec trois conversations, un document, quatre tâches dont une en retard, un contact associé et un contact créé dans le projet. Parcours au clavier seul, à 125 % de taille de texte (grille de recette), et suppression d'un projet de test avec lecture de la confirmation.

## 6. Risques

- **La fenêtre s'allonge.** Elle est bornée à 85 % de la hauteur et défile (`ProjectModal.tsx:362`) ; la vue d'ensemble tient en quatre lignes de cinq éléments au plus, et le formulaire passe dessous. Si la recette montre une fenêtre trop haute, la réponse est de réduire à trois éléments par ligne, pas d'ajouter des onglets.
- **Deux fenêtres de projet** (vue Projets et conteneur global) doivent se comporter pareil : chaque test du lot 3 tourne sur les deux montages.
- **Le focus rendu à la fermeture** (`useDialogFocusTrap`) peut viser une carte du Kanban démontée par la navigation ; le test « focus dans le composeur » du lot 3 le couvre.
- **Une remédiation cache souvent sa régression** : la réorganisation de la fenêtre touche un composant chargé d'historique (B-1392, B-1030, B-1060, B-1061, B-1443). Les tests existants de `ProjectModal` doivent passer sans que leurs attentes soient réécrites.

## 7. Lien avec P-104

La fenêtre d'un fil de travail (P-104 V2) réutilise `VueDEnsemble` et le même déroulé de navigation, nourris par sa propre route. Ce chantier passe donc avant le lot d'interface de P-104. P-104 ajoutera aussi une cinquième ligne, « Fils de travail », à la vue d'ensemble d'un projet, visible seulement quand le projet appartient à un fil (`docs/plans/2026-09-26-rfc-p104-fils-de-travail-v2.md`, §4.5) : `VueDEnsemble` doit donc accepter une famille de plus sans retouche de sa structure.

## Annexe : appuis dans le code (relevés du 26/09)

- Fenêtre et vue : `src/frontend/src/components/memory/ProjectModal.tsx:98-104`, `115-122`, `362`, `371-376`, `393-475`, `477-553`, `592-617` ; `src/frontend/src/components/memory/ProjectsPanel.tsx:120-123`, `221-234`, `271-279` ; `src/frontend/src/components/memory/ProjectDeliverablesSection.tsx:1-97` ; `src/frontend/src/components/chat/PanelContainer.tsx:124-129`.
- Liens en base : `src/backend/app/models/entities.py:53-54`, `89`, `177`, `233-234`, `515-519`, `563`, `885`, `960`.
- Routes : `src/backend/app/routers/chat.py:3610-3618`, `3761-3800` ; `src/backend/app/routers/documents.py:195-200`, `214-240` ; `src/backend/app/routers/memory.py:361-450`, `668-702`, `854`, `1270`, `1298-1323`, `1389` ; `src/backend/app/routers/tasks.py:63-92` ; `src/backend/app/routers/crm.py:258-281` ; `src/backend/app/routers/planning.py:171` ; `src/backend/app/main.py:899`.
- Navigation : `src/frontend/src/lib/destinationDuTravail.ts:12-67` ; `src/frontend/src/components/prototype/ConversationCanvasPrototype.tsx:1076-1088`, `1397-1408`, `1412-1428`, `1430-1437`, `2169-2171` ; `src/frontend/src/stores/documentStore.ts:269` ; `src/frontend/src/stores/taskStore.ts:45`, `126`, `131-137` ; `src/frontend/src/stores/panelStore.ts:53`, `78`, `187-188` ; `src/frontend/src/components/tasks/TasksPanel.tsx:117`, `168`, `288-299` ; `src/frontend/src/hooks/useConversationSync.ts:85-103`.
