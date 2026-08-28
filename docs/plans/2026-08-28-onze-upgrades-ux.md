# Les améliorations d'usage — plan d'exécution

> Dix entrées livrées sur onze. La cinquième est sortie après relecture, son
> diagnostic ne tenait pas : le registre des tâches est en mémoire, brancher
> l'appel au démarrage n'aurait rien ramené.
>
> S'y est ajouté, hors plan, un manque signalé par Ludo en cours de route :
> aucun bouton ne ramenait à l'accueil, et la seule action qui portait ce nom
> menait au second écran d'accueil.

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

### 4. Un seul bouton dans le rail, là où « Rechercher » et « Historique » ouvrent le même tiroir

Vérifié : les deux boutons s'appellent bien « Rechercher » et « Historique »
(`ConversationCanvasPrototype.tsx:1393-1394`), et `surface` ne change que le
focus initial. Et la loupe du rail ne
cherche que dans les titres de conversation, ce que son icône ne dit pas —
elle ne fouille ni les mails, ni les fichiers, ni les contacts. Le mot
« Rechercher » reste à la palette, qui, elle, indexe tout.

### 5. ~~L'historique des actions revient au démarrage~~ — SORTIE DU LOT

**Le diagnostic était faux, et la relecture l'a montré.** `fetchTasks` n'a
effectivement aucun appelant (`services/api/actions.ts:91`), mais
`ActionRunner._tasks` est un dictionnaire **en mémoire**
(`action_agents.py:428`). Au redémarrage du sidecar, la liste est vide :
brancher cet appel au démarrage ne ramènerait rien. Un rapport d'hier n'est pas
« sur le disque et introuvable » par cette voie.

Ce qui survit vraiment, c'est `ProcessingTask` en base, déjà affiché par
l'indicateur de travaux. Réhydrater l'un sans l'autre dupliquerait ce panneau
ou afficherait une tâche éternelle.

C'est la même erreur que les trois idées déjà écartées : un fait local exact,
une cause inventée. L'entrée sort du lot ; un historique durable des actions
est un chantier de persistance, pas un appel d'API oublié. Consigné en dette.

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

### 8. Le brief et les canevas ouvrent l'objet, pas le module — INACHEVÉE

> **Tentée le 28/08, dispatcher retiré.** Les préalables sont posés et vrais :
> le serveur transmet enfin l'identifiant du message d'une relance, et chaque
> item du brief sait quel objet il désigne. C'est le dispatcher qui promettait
> plus qu'il ne tenait.
>
> Sur les cinq types, **un seul ouvrait réellement son objet** : la facture,
> parce que sa lecture va chercher le document par identifiant sans attendre
> son hook. Les autres ouvraient la bonne surface et y affichaient autre chose.
>
> | Type | Ce qui manquait |
> |---|---|
> | Rendez-vous | la cible posée n'alimente pas la ressource que le canevas affiche ; au réveil, le hook reprend le premier événement à venir, pas celui qu'on a cliqué |
> | Relance | la lecture du message court avant que son hook soit allumé, et elle exige un compte que la réponse du serveur n'expose pas |
> | Prospect | la sélection était écrite dans l'état local d'un canevas que la vue CRM n'observe pas ; elle lit son propre magasin, et n'affiche la fiche que sur un onglet précis |
> | Tâche | pas traitée : l'identifiant était calculé puis rejeté sur la liste |
>
> Un brief où la facture s'ouvre et le reste non est exactement ce que ce plan
> interdisait : plus déroutant que l'ancien, uniformément grossier.
>
> Et mon test ne l'a pas vu — il lisait le source au lieu de cliquer. Même
> classe d'erreur que ma première tentative sur l'entrée 9. **La reprise
> commence par un test qui clique un item et vérifie l'objet affiché** : le
> titre du rendez-vous, la fiche du prospect, le formulaire de la tâche, le
> corps du message.

### 8 bis. Le détail de ce qui était prévu

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
depuis un store.

La relecture a exigé cette table avant la première ligne, et elle a raison :
sans elle, le premier item relance force un choix au milieu du travail.

| Ce qu'on clique | Où ça mène | L'identifiant est-il disponible ? |
|---|---|---|
| Événement du jour | canevas Rendez-vous | oui, le canevas sait déjà ouvrir un événement |
| Facture impayée | canevas Facturation | oui, même chose |
| Prospect dormant | vue CRM, fiche ouverte | oui, le CRM lit déjà une sélection depuis son store |
| Tâche | vue Tâches, tâche ouverte | à vérifier, pas de canevas |
| Relance en retard | vue E-mail, message ouvert | **non : le DTO ne le porte pas** |

Le dernier cas impose un préalable backend : `dashboard.py:336` connaît
`follow_up.email_message_id` et ne le met pas dans la réponse, qui n'expose que
l'objet, l'expéditeur et le contact. Une ligne à ajouter, sans quoi « ouvrir
l'objet » sur une relance n'a rien à ouvrir.

La règle qui rend le lot cohérent n'est pas « tout mène à un canevas », c'est
**« un clic mène toujours à l'objet, dans la surface qui sait l'afficher »**.
Un item qui ouvre une fiche pendant qu'un autre ouvre une liste serait
déroutant ; un item qui ouvre son objet, toujours, ne l'est pas.

### 9. Le chat ne ferme plus le canevas qu'il commente — LIVRÉ

> **Livré le 28/08, après une première tentative restaurée.** Ce n'est pas un état à changer, c'est la
> structure du rendu. Le canevas ne vit que dans la branche « accueil » du
> ternaire de la colonne principale ; l'extraire en variable et le rendre dans
> la branche chat compile et passe le typage, mais la variable reste nulle au
> moment où le chat s'ouvre — quelque chose remet `canvasOpen` à faux sur ce
> chemin, et le trouver demande de dérouler la coque, pas d'ajouter une
> condition.
>
> Le contrat d'écran reste acquis sur le papier : sous le seuil, le canevas
> doit céder la place, sinon le chat s'ouvrirait sous un voile.
>
> **Seconde correction, après relecture** : j'avais laissé la moitié du
> changement en place (la fermeture devenue conditionnelle) sous une étiquette
> « reporté ». Un entre-deux n'est pas un report : sur grand écran, ouvrir une
> conversation laissait le canevas collé à elle, sans qu'aucun test ne le
> couvre. La fermeture inconditionnelle est rétablie. Et le diagnostic de cette
> entrée est faux : le canevas n'est PAS prisonnier de la branche accueil, il
> est déjà rendu à part. La reprise devra partir de là.
>
> **Ce qui bloquait vraiment**, trouvé par la relecture : mon test cherchait la
> carte du parcours, qui vit dans la colonne que le ternaire démonte à
> l'ouverture du chat. Le canevas est ailleurs. Et le test « grand écran » ne
> prouvait rien, l'animation de sortie gardant l'élément dans le document — le
> sabotage passait inaperçu.
>
> `openChat` lit désormais la même largeur que le voile, via une fonction
> exportée : un appelant qui aurait interrogé la fenêtre de son côté aurait
> fait deux contrats d'un seul.

`openChat` (`ConversationCanvasPrototype.tsx:888`) appelle `setCanvasOpen(false)`.
Poser une question sur le mail affiché coûte aujourd'hui : perdre le mail,
poser la question, fermer le chat, refaire « Écrire », recliquer le message.

Nuance apportée par la relecture, et elle compte : `chatOpen` est un ternaire
qui **remplace** la colonne principale. Garder le canevas ne pose donc pas le
chat à côté de l'accueil, mais le chat à côté du canevas — l'accueil disparaît
de toute façon. C'est ce qu'on veut ici, mais il fallait le dire.

**Contrat d'écran étroit, tranché** : sous le seuil `xl`, le canevas recouvre
la colonne et l'isole (voile 0.48.1). Poser le chat dessous reviendrait à
ouvrir un chat invisible. Donc **sous le seuil, on continue de fermer le
canevas** ; au-dessus, les deux vivent côte à côte. Deux assertions distinctes
dans les tests, à 1280 et à 1279 pixels.

À traiter aussi : `chooseScenario` appelle encore `fermerLeChat()`, et les
autres `setCanvasOpen(false)` (`:907`, `:1065`, `:1171`, `:1825`) doivent être
passés en revue un par un — seul celui d'`openChat` tombe.

### 10. « Écrire » ouvre un brouillon, comme « Facturer » ouvre un devis

`chooseScenario('email')` n'ouvre même pas le canevas, et la carte s'intitule
« Messages à consulter ». Écrire un message demande : Écrire → « Email
complet » → « Nouveau ». Trois clics pour le verbe le plus simple de l'établi,
quand ses sœurs ont leur bouton de création sur la carte.

Réserve de l'arbitrage : `EmailConversationCard` ne sait générer un brouillon
qu'à partir d'un message **reçu**. Composer depuis zéro vers un destinataire
n'existe pas encore.

**Tranché : brouillon seulement, pas d'envoi.** Réutiliser `EmailCompose` tel
quel ajouterait l'envoi dans une surface qui promet « brouillon confirmé, aucun
envoi » — le canevas perdrait la garantie qu'il affiche. On construit donc le
pendant exact de `selectedInvoiceId === 'new-devis'` : un
`selectedEmailTarget === 'new-message'` qui monte une carte de rédaction sans
envoi, avec sa sortie vers la vue E-mail pour expédier.

### 11. L'accueil fantôme disparaît

`navigationStore.ts:24` porte encore `'home'`, et « Voir les N autres »
(`TodayDashboardCard.tsx:183`) y mène : un **second accueil** derrière celui de
la coque, avec sa checklist, ses actions rapides et ses conversations
récentes.

Ordre imposé : **inventaire de parité d'abord**. La checklist de mise en route
se déplace sur le brief, elle ne s'efface pas. Les actions rapides et les
conversations récentes doublonnent le rail et le tiroir, mais cela se prouve
avant de retirer.

## Ordre d'exécution, corrigé par la relecture

**11 avant 1.** `home.open` figure encore au registre des actions : la palette
l'afficherait juste avant que l'entrée 11 ne retire sa destination.

**Puis 1, 2, 3, 4, 6, 7**, chacun autonome et livrable seul. L'entrée 5 est
sortie du lot.

**Puis 9, puis 8.** Non pas parce que le premier change le sens du second — la
relecture a montré que `openEmbeddedView` ferme le canevas de toute façon —
mais parce que le contrat d'écran tranché en 9 décide de ce qu'un item du brief
peut ouvrir sans se recouvrir lui-même.

**Puis 10**, qui n'a aucune dépendance envers 2 : la fausse dépendance annoncée
dans la première version confondait « Écrire ouvre un brouillon » avec « la
fiche contact propose Facturer ». Si le composeur doit hériter du contact, c'est
le même patron que 2, en parallèle, pas à la suite.

## Les tests à figer avant le premier correctif

Un par entrée, écrits avant le code, sabotés après.

| Entrée | Ce que le test doit tenir |
|---|---|
| 1 | Palette ouverte, requête vide : les actions promises sont là, et l'établi n'est pas affiché deux fois |
| 2 | Contact sélectionné, passage à Facturer : le client est prérempli, et reste modifiable |
| 3 | Sur le parcours du jour seulement : une seule rangée de sources. Les autres parcours gardent la leur |
| 4 | Un seul bouton dans le rail, et le tiroir s'ouvre avec son champ prêt |
| 6 | ⌘O ouvre les Fichiers, et la fiche des raccourcis n'a plus de groupe vide |
| 7 | « imap » trouve encore sa carte, et les puces ne sont plus dans le document |
| 8 | Chaque type d'item du brief ouvre son objet ; celui qui n'a pas d'identifiant est traité, pas oublié |
| 9 | Chat ouvert depuis un e-mail affiché : l'e-mail est encore là à 1280 px, il a cédé la place à 1279 px |
| 10 | « Écrire » mène à une rédaction, et cette surface ne peut pas envoyer |
| 11 | La mise en route est montée sur le brief, et plus aucune navigation ne vise l'accueil fantôme |

## Ce que ce plan ne fait pas

Il ne fusionne aucune carte conversationnelle avec sa vue complète : aucune
paire ne partage la moindre action, et l'avoir tenté a réintroduit BUG-143. Il
ne rend pas la cloison documentaire implicite, il ne retire aucune
confirmation d'envoi, il ne transforme aucune vue métier en panneau latéral, et
il n'ajoute pas un sixième catalogue.
