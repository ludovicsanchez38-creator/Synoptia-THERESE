# RFC P-104, V2 : le fil de travail

Rédigé le 26/09/2026. Remplace la V1 du 25/09 (`docs/plans/2026-09-25-rfc-p104-fils-de-travail.md`), dont elle garde le besoin et l'option retenue (A : une entité à part, au-dessus du projet). Les cinq décisions que la V1 attendait (§5) ont été prises le 25/09 sur délégation de Ludo (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md:190-193`). Elles sont ici des faits ; ce document en tire les conséquences sur le modèle, l'écran et la livraison.

Aucune question n'est laissée à Ludo. La seule suppression de données prévue est celle qu'une utilisatrice déclenche elle-même sur un fil, après une confirmation qui dit ce qui part.

## 1. Le besoin

Dr_logic-3D, testeur alpha (Discord, 25/09, 03:35 à 04:29) : son unité de travail n'est pas toujours le projet ; un même besoin se découpe en variantes qui ont chacune leurs échanges et leur documentation ; il veut savoir combien de temps il passe sur chaque sujet ; à plat, l'information se noie. La V1 (§1 et §2) détaille ce constat et ce que le code offrait déjà.

## 2. Les décisions du 25/09 et ce qu'elles changent

| Décision | Conséquence dans ce design |
|---|---|
| Le nom est « fil de travail » | Le mot « fil » sert déjà à l'écran pour dire « la conversation » (« modifiables sans quitter le fil », `src/frontend/src/components/prototype/FollowUpsWorkspaceCanvas.tsx:182`) et P-105 parle de fils de courriels. Titres, libellés et registres disent donc toujours « fil de travail » en entier ; « fil » seul n'apparaît qu'à l'intérieur de la fenêtre d'un fil, où il ne peut rien désigner d'autre. La phrase de `FollowUpsWorkspaceCanvas` devient « sans quitter la conversation ». Identifiant interne : `fil`. |
| Un seul niveau de variantes | Une colonne `parent_id`. Un fil qui a un parent ne peut pas en être un ; un fil qui a des variantes ne peut pas devenir variante. |
| Minuteur manuel en phase 1 | Aucune durée n'est déduite des messages, des travaux ou de l'agenda. Règles du minuteur au §4.3. |
| Plusieurs projets par fil, une conversation dans un seul fil | Une table de liens pour les projets ; une **colonne** `fil_id` sur les conversations, qui tient la règle par construction (§4.2). |
| La carte « Reprendre » n'apparaît à l'Accueil que s'il y a un fil en cours, sans bloc permanent | « En cours » est un statut que l'utilisatrice pose, pas une déduction ; la carte tient en quelques lignes et disparaît quand plus aucun fil n'est en cours. Les autres entrées vers les fils sont au §4.5. |

## 3. La revue

**Aucune revue de P-104 n'existe.** Le dossier `docs/plans/revues/` compte douze fichiers : les cinq revues de P-096 (24/09), les passes 2 et 4 à 7 de la revue du diff du cycle 13, et les deux revues des RFC du 25/09 (P-105 à P-108, P-109 à P-125). Une recherche de « P-104 » sur tout le dépôt, dépendances exclues, ne rend que la V1, la RFC P-105 et le fichier des questions. Il n'y a donc aucun constat propre à P-104 auquel répondre.

Les revues voisines du 25/09 ont en revanche relevé des défauts de forme qui se reproduiraient ici. Ils sont traités d'avance :

| Constat voisin | Source | Réponse dans ce design |
|---|---|---|
| Une migration Alembic annoncée sans la constante de tête, la preuve d'estampillage ni la purge | revue P-105 à P-108, P-105 n° 6 | Lot 1 : liste complète des portes (§4.6) |
| Des lignes orphelines après une suppression, faute de cascade et de `PRAGMA foreign_keys` (absent de `src/backend/app/models/database.py`) | P-105 n° 7 | Chaque chemin de suppression nettoie à la main, avec son test (§4.6) |
| Aucune exigence d'accessibilité | P-105 n° 16 | §4.7 |
| Un rafraîchissement périodique qui devient une écriture de fond sans consentement | P-105 n° 4, et le chantier « mise au repos des écritures de fond » | Le minuteur n'écrit qu'au geste ; le plafond est calculé à la lecture (§4.3) |

La revue adverse de ce design est le lot 0.

## 4. Conception

### 4.1 Ce qu'est un fil, et ce qu'il ne fait pas

Un projet est un engagement client : devis, livrables, dossier, cloison documentaire. Un fil de travail suit ce que l'on fait, et peut traverser plusieurs projets. La fenêtre d'un fil le dit en une phrase, sous son titre.

**Le fil ne change jamais ce que l'assistante lit.** La cloison documentaire reste celle du projet de la conversation : `_perimetre_de_conversation` (`src/backend/app/routers/chat.py:652`) et la route de rattachement (`chat.py:3761-3800`) ne lisent pas le fil, et aucune des cloisons `_cloison_projets`, `_cloison_contacts`, `_cloison_fichiers` (`src/backend/app/services/memory_tools.py:369`, `444`, `1354`) non plus. Un fil qui réunit les projets A et B n'ouvre pas les documents de A à une conversation rattachée à B. Motif : un fil est un regroupement posé pour s'organiser ; en faire un périmètre transformerait une commodité en fuite entre clients. Un test le fige (lot 2).

La V1 prévoyait un champ de périmètre (`scope`) sur le fil. Il disparaît : sans effet sur la cloison, il n'aurait rien à dire.

### 4.2 Le modèle

| Table ou colonne | Champs | Pourquoi cette forme |
|---|---|---|
| `fils` | `id`, `nom` (200 caractères au plus), `statut` (`en_cours`, `en_pause`, `clos` ; défaut `en_cours`), `parent_id` (nullable), `created_at`, `updated_at` | Un niveau de variantes, un statut posé à la main |
| `fils_projets` | `fil_id`, `project_id`, `created_at` ; clé primaire sur le couple | Plusieurs projets par fil, un projet dans plusieurs fils |
| `sessions_de_travail` | `id`, `fil_id`, `debut`, `fin` (nullable : minuteur en marche), `source` (`minuteur`, `saisie`), `a_corriger` (booléen), `created_at`, `updated_at` | Le temps réalisé, jamais déduit |
| `conversations.fil_id` | nullable, indexé | Une conversation dans un seul fil : la règle tient par la structure, comme `project_id` (`src/backend/app/models/entities.py:177`) |
| `documents.fil_id` | nullable, indexé | La « documentation propre » d'une variante ; même règle que la conversation, par symétrie |

**La table polymorphe de la V1 (`liens_de_fil`) est abandonnée.** Elle ne pouvait porter aucune clé étrangère (elle visait quatre tables), il lui fallait un index partiel pour tenir « une conversation dans un seul fil », et chaque table visée devenait un chemin de suppression de plus à nettoyer. Deux colonnes et une table de liens disent la même chose, et la règle décidée ne peut plus être violée faute de champ pour l'exprimer : c'est le principe du catalogue documentaire (« la cloison est structurelle », `CLAUDE.md` du dépôt).

**Les tâches n'ont pas de lien direct en phase 1.** Elles appartiennent déjà à un projet (`entities.py:563`, formulaire depuis P-150), et la fenêtre du fil y mène par ses projets, dont la vue d'ensemble (P-148) montre les tâches. Un quatrième rattachement doublerait ce chemin sans besoin exprimé par le testeur.

Invariants, chacun avec son test :

1. un fil variante n'a pas lui-même de variantes ;
2. au plus une session sans `fin` dans toute la base ;
3. `fin` postérieure ou égale à `debut` ;
4. une session ne commence pas dans le futur ;
5. un fil `clos` n'accepte pas de minuteur (on le rouvre d'abord).

### 4.3 Le temps

- **Démarrer et arrêter** : dans la fenêtre du fil, sur la carte « Reprendre », et dans le menu du sélecteur de fil de la conversation (§4.4). Nulle part ailleurs.
- **Un seul minuteur à la fois.** Démarrer sur B arrête A, et une notification le dit : « Minuteur de "Refonte, variante B" arrêté à 14 h 32 (1 h 05) ». Deux minuteurs simultanés compteraient deux fois la même heure.
- **Mettre en pause ou clore un fil arrête son minuteur** à cet instant, et la notification le dit. Un minuteur qui tournerait sur un fil que l'on vient de dire en pause mesurerait un travail qui n'a pas lieu ; et l'invariant 5 interdit un minuteur sur un fil clos.
- **Rappel à 4 h** : la carte et le sélecteur écrivent « le minuteur tourne depuis 4 h 10 ». Aucune action n'est forcée.
- **Plafond à 10 h.** Une session sans fin commencée depuis plus de 10 h est **à corriger** : elle ne compte dans aucun total, et la fenêtre du fil la montre avec « Corriger » (heure de fin à saisir). Cet état est calculé à la lecture, rien ne s'écrit en fond. La seule écriture a lieu au geste : arrêter, corriger, ou démarrer un autre minuteur, qui clôt la session trop longue avec `fin = debut + 10 h` et `a_corriger = vrai`, toujours exclue des totaux tant qu'elle n'est pas corrigée. Une durée inventée ne s'affiche jamais comme mesurée.
- **Saisie à la main** : ajouter une session (début, fin), corriger une session, supprimer une session après confirmation.
- **Le jour civil de Paris** (`date_civile_paris`, `src/backend/app/services/civil_time.py:9`) borne « aujourd'hui » et « cette semaine » ; une session à cheval sur minuit compte à chaque jour sa part.
- **Totaux** : aujourd'hui, cette semaine, depuis le début. Un fil parent affiche son temps propre, celui de ses variantes, puis leur somme.
- **Les travaux ne servent pas de mesure.** `ProcessingTask` porte un projet et une conversation, et son commentaire annonce « le temps par projet » (`src/backend/app/models/processing.py:67-69`), mais les travaux terminés sont purgés à 30 jours (`src/backend/app/services/traitements.py:376`) et mesurent le temps de la machine, pas celui de la personne. Phase 2 au mieux, en suggestion (§5).

### 4.4 L'écran, sans nouvelle vue

Aucune entrée de rail, aucune vue ajoutée à `APP_VIEWS` (`src/frontend/src/stores/navigationStore.ts:24-35`).

1. **Le sélecteur de la conversation.** À côté du sélecteur de projet (`src/frontend/src/components/chat/ConversationProjectPicker.tsx:160-185`), un `<select>` natif « Fil de travail » : « Aucun fil de travail », les fils en cours puis en pause, « Nouveau fil de travail… », « Ouvrir le fil ». Le minuteur y apparaît en texte quand il tourne sur ce fil. **Il ne s'affiche qu'à partir du premier fil créé** : qui n'utilise pas les fils garde l'en-tête d'aujourd'hui. Le premier fil naît de la palette (point 4) ou de la fenêtre d'un projet (§4.5).
2. **La carte « Reprendre » à l'Accueil**, entre le brief du jour (`src/frontend/src/components/prototype/ConversationCanvasPrototype.tsx:2134`) et « Cette semaine » (l.2168). Elle n'existe que si au moins un fil est `en_cours`. Jusqu'à trois lignes, par dernière session décroissante (à défaut, par dernière modification) : nom du fil, temps du jour, bouton du minuteur, « Ouvrir », « Mettre en pause ». Au-delà de trois, « et N autres fils de travail en cours » ouvre la palette (`openCommandPalette`, `src/frontend/src/stores/panelStore.ts:63`, `166`). **Mettre en pause est la seule façon de retirer une ligne** : la carte ne se ferme pas par une croix qui cacherait un fil que l'on dit en cours.
3. **La fenêtre d'un fil** : une modale du même gabarit que la fenêtre du projet, qui réutilise la vue d'ensemble de P-148 (`VueDEnsemble`, `docs/plans/2026-09-26-rfc-p148-vue-d-ensemble-projet.md`, §4.2) nourrie par `GET /api/fils/{id}/ensemble` : variantes (chacune ouvre sa fenêtre), temps (totaux, sessions, minuteur, saisie), conversations, documents, projets (chacun ouvre la fenêtre du projet, où sont tâches, contacts et livrables). Puis les champs du fil : nom, statut, parent pour une variante, et « Supprimer ». Même déroulé de navigation que P-148 (§4.3 de cette RFC-là) : question d'abandon si la saisie est modifiée, événement annulable, fermeture seulement si l'ouverture est acceptée.
4. **La palette** : l'action « Nouveau fil de travail » (registre `src/frontend/src/lib/actionRegistry.ts`, contrôlé par `lexique.test.ts`), qui crée le fil et y rattache la conversation ouverte s'il y en a une ; et la recherche de données, qui gagne le type `fil` (`src/frontend/src/lib/rechercheDeDonnees.ts:14-16`) pour retrouver tout fil, clos compris.
5. **La création d'un document** : le formulaire gagne « Fil de travail (optionnel) » sous « Projet lié (optionnel) » (`src/frontend/src/components/documents/DocumentCreateModal.tsx:186-201`), affiché seulement si un fil existe, et `DocumentCreate` gagne `fil_id` (`src/backend/app/models/schemas_documents.py:12-18`) ; la fenêtre du fil propose aussi « Rédiger un document dans ce fil ». **Le fil d'un document se pose à sa création seulement, en phase 1** : aucune route ne modifie un document lui-même (le routeur ne modifie que les sections et les pistes, `src/backend/app/routers/documents.py:252`, `962`). Rattacher après coup un document existant demanderait une route `PATCH /api/documents/{document_id}` nouvelle ; elle attend la phase 2 (§5).

**Retirés de la V1**, au nom du constat du 27/08 : le filtre par fil dans le tiroir des conversations (qui regroupe par date, `src/frontend/src/components/prototype/PrototypeConversationDrawer.tsx:77-84`) et dans la liste des documents. La fenêtre du fil fait ce travail ; si l'usage montre qu'il manque, il reviendra en phase 2.

### 4.5 Où l'on trouve les fils quand la carte n'est pas là

La décision « sans bloc permanent » ne doit pas rendre un fil en pause introuvable. Quatre entrées, toutes existantes ou déjà prévues :

- le sélecteur de la conversation, dès qu'un fil existe ;
- la palette, par la recherche de données (tous statuts) ;
- la fenêtre d'un projet : une ligne « Fils de travail » dans sa vue d'ensemble (P-148), visible seulement si le projet appartient à au moins un fil, avec « Nouveau fil de travail avec ce projet » dans son état vide ;
- la fenêtre d'un fil, qui liste ses variantes et son parent.

### 4.6 Les données : toutes les portes dès le lot 1

- **Schéma.** `create_all` crée les trois tables sur une base neuve (`database.py:1113`). `apply_adhoc_migrations` (`database.py:255`) ajoute, de façon idempotente, les deux colonnes `fil_id`, leurs index et les trois tables sur une base existante, sur le patron de la table des prestations (`database.py:329-341`). Une révision Alembic fait de même pour `make db-migrate`, chaînée sur la tête du moment (`b8c9d0e1f2a3` aujourd'hui, `database.py:619`, ou la révision de P-132 si elle arrive avant). `ALEMBIC_HEAD_REVISION` suit ; la preuve d'estampillage (`ensure_alembic_stamp`, `database.py:642-785`, dont l'obligation est écrite l.688-692) gagne une fonction `tables_des_fils()` sur le patron de `tables_de_planning()` (l.632-639), qui exige toutes les colonnes des trois tables et les deux colonnes `fil_id`.
- **Export complet** (`_assembler_export_rgpd`, `src/backend/app/routers/data.py:172`) : les trois tables, et `fil_id` dans les lignes de conversations et de documents. `data_format_version` passe au numéro suivant (1.5, ou 1.6 si P-132 a déjà pris 1.5 ; `data.py:262`).
- **« Effacer toutes mes données »** (`_supprimer_toutes_les_donnees`, `data.py:632`) : les trois tables.
- **Import de conversations** (`data.py:1763`) : `fil_id` n'est gardé que si le fil existe localement, sinon il est vidé. Le même défaut existe déjà pour les projets : l'import recopie `project_id` sans vérifier que le projet existe (`data.py:1823`), alors que la route de rattachement le refuse parce qu'une conversation rattachée à un projet absent « cloisonnerait sur du vide » (`chat.py:3786-3790`). C'est un candidat à reproduire, hors de ce chantier.
- **Restauration** : elle ferme la base puis la rouvre par `init_db` (`data.py:1587`, `1665`), donc les migrations ad hoc tournent sur une sauvegarde d'avant les fils. Un test le prouve.
- **Suppressions**, sans cascade possible :
  - supprimer un **projet** (`_nettoyer_et_supprimer_projet`, `src/backend/app/routers/memory.py:361-450`) retire ses lignes de `fils_projets` et le compte dans son rapport ;
  - supprimer une **conversation** (`chat.py:3859`) ou un **document** (`src/backend/app/routers/documents.py:1130`) n'a rien à nettoyer, le lien est sur la ligne supprimée ;
  - supprimer un **fil** vide `fil_id` sur ses conversations et documents, retire ses lignes de `fils_projets`, supprime ses sessions, et supprime ses variantes de la même façon, après une confirmation qui compte chaque famille (même rédaction que la suppression d'un projet dans P-148, §4.4).
- **RGPD.** Un fil ne porte aucune donnée de contact en propre ; son nom peut nommer un client, comme le nom d'un projet. Il est dans l'export complet et dans l'effacement total ; l'anonymisation d'une fiche ne le touche pas, comme elle ne touche pas le nom d'un projet.

### 4.7 Accessibilité

- Le minuteur est un vrai bouton nommé d'après son fil (« Démarrer le minuteur de Refonte »), dont l'état change de nom (« Arrêter le minuteur de Refonte »).
- Le temps affiché se met à jour à la minute, hors de toute région vivante ; seuls le démarrage, l'arrêt et le rappel des 4 h s'annoncent, une fois, par une région `role="status"`.
- Les durées s'écrivent « 1 h 05 », jamais « 01:05 » seul.
- La carte « Reprendre » est une région titrée ; chaque ligne se parcourt au clavier dans l'ordre de lecture.
- Le sélecteur de fil est un `<select>` natif étiqueté, comme celui du projet.

### 4.8 Le lexique

La section 13 de `docs/rules/RULES-DESIGN.md` (l.357-392) reçoit une ligne, sur le modèle de celle des projets (l.382) : « fils : Fil de travail ; un fil de travail, ses variantes ; son absence : « Aucun fil de travail » ; « fil » seul ne s'emploie qu'à l'intérieur de la fenêtre d'un fil ». L'action de palette et les libellés du Centre passent par les registres que `lexique.test.ts` contrôle.

## 5. Ce qui attend la phase 2

- Suggestions de sessions à partir des travaux et de l'agenda, toujours proposées à la validation, jamais posées.
- Comparaison entre l'estimation du planning (P-039) et le temps réel.
- Synthèse d'un fil par l'assistante.
- Le relais avec P-105 : son « en cours » est une définition passée en paramètre au moteur, en attendant les fils (`docs/plans/2026-09-25-rfc-p105-alerte-mail-tache.md:37`, `85`, `232`) ; une fois les fils en usage, « en cours » pourra devenir « les tâches des projets d'un fil en cours ».
- Le filtre par fil dans le tiroir et la liste des documents, si l'usage le réclame.
- Une route de modification d'un document (`PATCH /api/documents/{document_id}`, inexistante aujourd'hui), pour rattacher à un fil un document créé avant lui.
- Hors périmètre : la continuité entre plusieurs machines (P-108).

## 6. Mise en œuvre, lot par lot

Chaque lot : tests écrits d'abord et vus rouges, sabotage ciblé par fonction (règle du 27/08), un commit, revue adverse du diff. P-148 (lots 1 à 3) passe avant le lot 4 de ce chantier, qui réutilise sa vue d'ensemble.

### Lot 0 : revue adverse de ce design

Critère : un verdict GO écrit dans `docs/plans/revues/`, chaque constat corrigé dans une V3 ou réfuté avec sa preuve.

### Lot 1 : modèle, migration et portes de données

Tests à écrire d'abord (pytest) :
- une base neuve a les trois tables et les deux colonnes ; une base d'avant les fils les reçoit au démarrage ; un second démarrage ne change rien ;
- `ensure_alembic_stamp` refuse de ré-estampiller une base ancienne sans les tables ou sans une des colonnes `fil_id` (extension de `tests/test_alembic_stamp.py`) ; `test_constante_epinglee_suit_la_vraie_tete` passe ;
- l'export complet contient les trois tables et `fil_id`, avec la nouvelle version ;
- « Effacer toutes mes données » vide les trois tables ;
- l'import de conversations garde un `fil_id` existant et vide un `fil_id` inconnu ;
- une sauvegarde d'avant les fils se restaure et se lit.

Critère observable : sur une copie de la base de Ludo, l'application démarre, et un export complet porte des tables de fils vides.

### Lot 2 : l'API des fils et du temps

Routes : `/api/fils` (lister, créer, lire, modifier, supprimer), `/api/fils/{id}/sessions` (démarrer, arrêter, ajouter, corriger, supprimer), `/api/fils/{id}/ensemble`, `/api/fils/en-cours` (ce que lit la carte).

Tests à écrire d'abord (pytest) :
- les cinq invariants du §4.2 ;
- démarrer sur B arrête A et le dit dans la réponse ;
- mettre en pause ou clore un fil dont le minuteur tourne l'arrête à cet instant ;
- une session de plus de 10 h est rendue `a_corriger`, exclue des totaux, sans aucune écriture à la lecture ;
- démarrer un minuteur alors qu'une session trop longue traîne la clôt avec `a_corriger` ;
- une session à cheval sur minuit de Paris se répartit sur deux jours ;
- un parent additionne ses variantes, en les montrant séparément ;
- supprimer un fil vide les `fil_id`, retire les liens de projets, supprime sessions et variantes, et le rapport compte chaque famille ;
- **le fil n'élargit pas la cloison** : une conversation rattachée au projet B, dans un fil qui contient A et B, ne reçoit aucun document de A (patron des tests de `_perimetre_de_conversation`).

### Lot 3 : les rattachements

`PATCH /api/chat/conversations/{id}/fil` (ou `null`), `fil_id` à la création d'un document (`POST /api/documents`, `documents.py:188-205`), liens de projets par `/api/fils/{id}`. Suppression d'un projet étendue.

Tests à écrire d'abord (pytest) : un fil inconnu donne 404, pour une conversation comme pour un document créé (même règle que `chat.py:3786-3790` et `documents.py:195-200`) ; une conversation passe d'un fil à un autre sans rester dans le premier ; supprimer un projet retire ses liens de fils et le rapport de suppression les compte.

### Lot 4 : l'écran

Sélecteur de la conversation, fenêtre du fil sur `VueDEnsemble`, action et recherche de palette, champ du formulaire de document, ligne « Fils de travail » dans la vue d'ensemble d'un projet, lexique, phrase de `FollowUpsWorkspaceCanvas`.

Tests à écrire d'abord (vitest) : le sélecteur est absent sans fil et présent dès le premier ; « Nouveau fil de travail » depuis la palette crée le fil et y rattache la conversation ouverte ; la fenêtre du fil mène à une conversation, un document, un projet, avec le déroulé de P-148 ; en démonstration, les noms de fils sont masqués ; `lexique.test.ts` et `lexiqueTitres.test.ts` restent verts avec la nouvelle ligne.

### Lot 5 : le minuteur et la carte « Reprendre »

Tests à écrire d'abord (vitest) : sans fil en cours, aucune carte et aucun titre « Reprendre » dans l'Accueil ; avec un fil en cours, une ligne avec le temps du jour ; « Mettre en pause » retire la ligne et la carte si c'était la dernière ; démarrer, arrêter et le rappel des 4 h s'annoncent une fois ; une session à corriger se signale et ne gonfle pas le total ; au-delà de trois fils, « et N autres » ouvre la palette.

### Lot 6 : recette

Le scénario de Dr_logic dans l'application lancée : un fil « Refonte » avec deux variantes, deux projets, trois conversations et un document par variante, une matinée minutée avec un changement de variante, puis l'Accueil le lendemain matin. En mode démonstration, puis au clavier seul.

## 7. Risques

- **Doublon de concept avec le projet** : la phrase de la fenêtre du fil (§4.1) et la règle « le fil ne change pas ce que l'assistante lit » tracent la frontière ; la recette vérifie qu'un testeur la comprend sans explication.
- **Minuteur oublié** : rappel à 4 h, plafond à 10 h, session « à corriger » exclue des totaux.
- **Surcharge** : aucun changement visible pour qui n'utilise pas les fils ; une carte qui n'existe que si un fil est en cours ; aucun filtre ajouté au tiroir.
- **Le mot « fil »** : lexique et libellés en entier (§2, §4.8).
- **Deux migrations le même jour** (P-132 et P-104) : la seconde se chaîne sur la première et étend la même preuve ; le test de la constante attrape l'oubli.
- **Deux synthèses d'écran** : la fenêtre du fil ne conçoit pas sa propre vue d'ensemble, elle réutilise celle de P-148 ; si P-148 change, les deux suivent.

## Annexe : appuis dans le code (relevés du 26/09)

La V1 citait des lignes qui ont bougé depuis le 25/09 ; toutes celles-ci ont été relevées à nouveau.

- Entités : `src/backend/app/models/entities.py`, `Project` l.81-110 (`contact_id` l.89), `Conversation` l.166-190 (`project_id` l.177, `memory_scope` l.185), `CalendarEvent.project_id` l.515-519, `Task` l.552-580 (`project_id` l.563), `TaskSchedule` l.601-654, `Activity` (le mot « activité » déjà pris par le CRM) l.857-876, `Deliverable` l.879-895, `Document` l.951-962 (`project_id` l.960).
- Travaux : `src/backend/app/models/processing.py:67-69` ; `src/backend/app/services/traitements.py:376`.
- Périmètre et cloisons : `src/backend/app/routers/chat.py:652`, `3761-3800`, `3786-3790`, `3859` ; `src/backend/app/services/memory_tools.py:346`, `369`, `444`, `1354`.
- Documents : `src/backend/app/models/schemas_documents.py:12-18` ; `src/backend/app/routers/documents.py:188-205`, `252`, `962`, `1130`.
- Données : `src/backend/app/routers/data.py:172`, `262`, `632`, `1587`, `1665`, `1763`, `1823` ; `src/backend/app/routers/memory.py:361-450`.
- Migrations : `src/backend/app/models/database.py:255`, `329-341`, `619`, `632-639`, `642-785`, `688-692`, `1113`, `1167`, `1173`.
- Écran : `src/frontend/src/components/chat/ConversationProjectPicker.tsx:160-185` ; `src/frontend/src/components/prototype/PrototypeConversationDrawer.tsx:77-84` ; `src/frontend/src/components/prototype/ConversationCanvasPrototype.tsx:2134`, `2168` ; `src/frontend/src/components/prototype/FollowUpsWorkspaceCanvas.tsx:182` ; `src/frontend/src/components/documents/DocumentCreateModal.tsx:186-201` ; `src/frontend/src/stores/navigationStore.ts:24-35` ; `src/frontend/src/stores/panelStore.ts:63`, `166` ; `src/frontend/src/lib/rechercheDeDonnees.ts:14-16`.
- Temps civil : `src/backend/app/services/civil_time.py:9`.
- Lexique : `docs/rules/RULES-DESIGN.md:357-392`.
- Décisions et voisins : `docs/plans/2026-09-25-questions-rfc-pour-ludo.md:190-193` ; `docs/plans/2026-09-25-rfc-p105-alerte-mail-tache.md:37`, `85`, `172`, `232` ; `docs/plans/revues/2026-09-25-revue-rfc-p105-p108.md` (P-105, constats 4, 6, 7 et 16).
