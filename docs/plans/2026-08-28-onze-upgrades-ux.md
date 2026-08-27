# Les onze améliorations d'usage — plan d'exécution

Issu de l'audit à trois voix du 27/08 (Grok, Codex, trois agents internes sur
des angles séparés, puis arbitrage). Objectif posé par Ludo, mot pour mot :
« améliorer la fluidité, le moins de complexité possible pour une puissance
maximale de l'outil ».

## Ce que les trois auditeurs ont trouvé, séparément

Une cause unique, vue de trois côtés : **l'application perd le contexte à
chaque passage de relais**. Le chat ferme l'objet qu'il commente, la
navigation transporte un nom de vue et jamais l'objet, le brief du jour
affiche « Tu peux agir ici, sans chercher le bon module » trois lignes
au-dessus d'un appel qui ouvre le module.

C'est la suite de 0.49 : on avait réglé « rien ne se comporte comme annoncé »,
il reste « tout se fait oublier ».

## Règles de ce lot

1. **Aucune interface en plus.** Chaque ligne ci-dessous supprime ou fusionne
   un geste, ou rend atteignable une capacité déjà payée.
2. **Aucune perte de puissance.** Une idée qui allège en retirant une
   capacité est refusée, même si elle simplifie.
3. **Preuve avant travail.** Chaque entrée cite le fichier et la ligne qui
   montrent le défaut. Une preuve qui ne tient pas fait tomber l'entrée : trois
   idées de l'audit ont déjà été écartées ainsi.
4. **TDD et sabotage ciblé par fonction**, jamais par chaîne globale — la
   leçon du 27/08, où un remplacement inverse a rouvert la cloison des projets.

## Premier train — effort petit, sept entrées

### 1. La palette montre ce qu'elle sait faire avant qu'on tape

`visibleActions` rend une liste vide tant que la requête est vide
(`ConversationCanvasPrototype.tsx:434-443`), alors que « Ouvrir les Projets »,
« Ouvrir les Fichiers », « Nouveau document », « Bibliothèque de prompts » et
« Exporter les données » sont câblées et attendent. Les commandes créées par
l'utilisateur n'y entrent pas non plus.

Deux sources à brancher au même endroit. La déduplication parcours/capacités
reste en place.

### 2. Le devis hérite du client déjà à l'écran

`InvoiceConversationCard.tsx:274` : `useState('')`. Le formulaire naît
toujours vide alors que `selectedContactId` **survit déjà** au passage de
« Retrouver » à « Facturer » (`ConversationCanvasPrototype.tsx:742`), et que
le canevas voisin le reçoit.

Condition non négociable : la valeur reste modifiable, et sa provenance se
voit. Un préremplissage silencieux qui verrouille serait pire que le champ
vide.

### 3. Une seule rangée de sources sur l'accueil

La carte du jour affiche « Sources réelles » avec des pastilles conditionnées
aux données chargées ; la coque colle en dessous une rangée « Sources » écrite
en dur. **Uniquement sur le parcours `today`** : les pastilles des autres
parcours (« Brouillon confirmé, aucun envoi », « Écriture confirmée »,
« Worktree isolé ») sont distinctes et disent chacune ce que ce parcours peut
faire. Elles restent.

### 4. Un seul bouton « Conversations » dans le rail

Deux boutons (`ConversationCanvasPrototype.tsx:1393-1394`) ouvrent le même
tiroir : `surface` ne change que le focus initial. Et la loupe du rail ne
cherche que dans les titres de conversation, ce que son icône ne dit pas —
elle ne fouille ni les mails, ni les fichiers, ni les contacts. Le mot
« Rechercher » reste à la palette, qui, elle, indexe tout.

### 5. L'historique des actions revient au démarrage

`services/api/actions.ts:91` : `fetchTasks` existe et n'a **aucun appelant**.
Un rapport lancé hier est sur le disque et introuvable.

Piège à ne pas rater : ne pas relancer le sondage sur des tâches terminées, et
traiter le statut `running` orphelin d'une session morte — sinon on réhydrate
une tâche qui tournera pour l'éternité.

### 6. ⌘O cesse d'être une touche morte

Le gestionnaire a sa branche (`useKeyboardShortcuts.ts:175`), la coque ne
fournit jamais `onOpenFile`, et la fiche des raccourcis affiche un groupe
« Fichiers » vide. `files.open` est dans le registre.

### 7. Le tiroir arrête d'afficher quatre-vingt-dix puces d'infrastructure

Trente cartes fois trois puces en 12 px, quatre cents pixels sous une phrase
qui promet de garder les détails techniques en retrait. On retire l'affichage,
**on garde le champ** : il alimente la recherche du tiroir, et taper « imap »
doit continuer de trouver.

## Second train — effort moyen, quatre entrées

### 8. Le brief et les canevas ouvrent l'objet, pas le module

Le plus fort du lot, et la contradiction la plus audible :
`TodayDashboardCard.tsx:159` appelle `onOpenView(item.targetView)` trois lignes
sous « Tu peux agir ici, sans chercher le bon module »
(`ConversationCanvasPrototype.tsx:1481`). L'identité existe déjà dans le modèle
de lecture (`prototypeReadModels.ts:14-22`) : elle est calculée puis jetée.

Même défaut en sortie : les boutons « Gérer mes X » des canevas ramènent à la
racine du module sans transmettre l'objet en cours
(`EmailConversationCard.tsx:485`, `InvoiceConversationCard.tsx:630`,
`MeetingConversationCard.tsx:461`, `ContactsMemoryCard.tsx:286`).

**C'est un chantier par vue, pas une destination à préciser.** Les panneaux
gardent leur sélection en état interne ; seul le CRM lit déjà une sélection
depuis un store. Avertissement de l'arbitrage : **ne pas livrer la seule
tranche CRM** — un brief où un item ouvre la fiche pendant qu'un autre ouvre la
boîte entière serait plus déroutant qu'un brief uniformément grossier.

### 9. Le chat ne ferme plus le canevas qu'il commente

`openChat` (`ConversationCanvasPrototype.tsx:888`) appelle `setCanvasOpen(false)`.
Poser une question sur le mail affiché coûte aujourd'hui : perdre le mail,
poser la question, fermer le chat, refaire « Écrire », recliquer le message.

Les deux surfaces coexistent déjà dans le JSX. Le voile de la 0.48.1
(`usePanneauCouvrant`) traite le cas de l'écran étroit.

### 10. « Écrire » ouvre un brouillon, comme « Facturer » ouvre un devis

`chooseScenario('email')` n'ouvre même pas le canevas, et la carte s'intitule
« Messages à consulter ». Écrire un message demande : Écrire → « Email
complet » → « Nouveau ». Trois clics pour le verbe le plus simple de l'établi,
quand ses sœurs ont leur bouton de création sur la carte.

Réserve de l'arbitrage : `EmailConversationCard` ne sait générer un brouillon
qu'à partir d'un message **reçu**. Composer depuis zéro vers un destinataire
n'existe pas encore — c'est ce qu'il faut construire, et c'est ce qui fait
passer cette entrée de « petite » à « moyenne ».

### 11. L'accueil fantôme disparaît

`navigationStore.ts:24` porte encore `'home'`, et « Voir les N autres »
(`TodayDashboardCard.tsx:183`) y mène : un **second accueil** derrière celui de
la coque, avec sa checklist, ses actions rapides et ses conversations
récentes.

Ordre imposé : **inventaire de parité d'abord**. La checklist de mise en route
se déplace sur le brief, elle ne s'efface pas. Les actions rapides et les
conversations récentes doublonnent le rail et le tiroir, mais cela se prouve
avant de retirer.

## Ordre d'exécution

Le premier train dans l'ordre 1 à 7, chacun autonome et livrable seul. Puis 2
avant 10 (le devis hérite avant que la fiche contact ne propose « Facturer »),
et 9 avant 8 (garder le canevas ouvert change ce que « ouvrir l'objet »
signifie).

## Ce que ce plan ne fait pas

Il ne fusionne aucune carte conversationnelle avec sa vue complète : aucune
paire ne partage la moindre action, et l'avoir tenté a réintroduit BUG-143. Il
ne rend pas la cloison documentaire implicite, il ne retire aucune
confirmation d'envoi, il ne transforme aucune vue métier en panneau latéral, et
il n'ajoute pas un sixième catalogue.
