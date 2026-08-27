# Simplifier THÉRÈSE sans rien lui retirer — le plan

> 27/08/2026. Fondé sur cinq lectures parallèles du code (43 constats
> ancrés fichier:ligne), dont les cinq structurants ont été contre-vérifiés
> à la main. Contrainte absolue : **aucune perte de fonctionnalité**.

> Les 43 constats avec leurs preuves fichier:ligne :
> `2026-08-27-constats-ux-detail.md`. Cinq y sont marqués VÉRIFIÉ (relus à la
> main) ; les autres restent des pistes à confirmer avant exécution.

## Le vrai diagnostic

Ludo : « je trouve qu'il y a trop d'interfaces ».

Deux hypothèses ont été écartées **par le code**, pas par opinion :

1. « Six capacités existent en double, fusionnons » — faux. Aucune paire ne
   partage la moindre action. Côté conversation on AGIT dans un contexte (et
   on croise les domaines) ; côté vue complète on ADMINISTRE un domaine.
   Fusionner aurait supprimé du métier et réintroduit BUG-143.
2. « Il y a trop d'écrans » — le nombre n'est pas la cause. Une capacité
   centrale mérite d'être joignable de partout.

**La cause est ailleurs, et elle est simple : on ne sait pas où l'on est, on
ne peut pas revenir, et cliquer ne produit souvent rien.**

Trois défauts vérifiés à la main expliquent l'essentiel du ressenti :

| Vérifié | Ce que vit l'utilisateur |
|---|---|
| 5 fermetures de vue, **2 seulement dépilent** l'historique (`ConversationCanvasPrototype.tsx` : `goBack()` n'apparaît que 2 fois pour 5 `setEmbeddedView(null)`) | « Retour » ne ramène pas d'où l'on vient : il traverse des écrans non demandés, et rouvre parfois une vue fermée depuis longtemps |
| `resolveEscape` — l'« autorité unique d'Échap » — n'a **aucun appelant** : 14 composants lui délèguent par commentaire, la fonction est morte | Échap ne marche que par accident d'ordre dans une cascade de 10 branches recopiée à la main |
| Une carte du tiroir ne fait qu'écrire une phrase dans le composeur : la destination n'est ouverte qu'**après validation** (`chooseCapability:1105` pose `setComposerValue`, seul `submitComposer` lit `destination`) | On clique sur « Tâches », rien ne s'ouvre. Il faut deviner qu'il faut appuyer sur Entrée |

Ce n'est pas un problème de quantité. C'est un problème de **prévisibilité**.

## P0 — Rendre le retour déterministe

Le chantier qui, seul, change le plus le ressenti.

- **Un seul chemin de fermeture.** Les cinq sites (`:836`, `:973`, `:1016`,
  `:1071`, `:1095`) passent par une fonction unique qui ferme la surface ET
  dépile. Aujourd'hui deux le font, trois l'oublient.
- **Une pile qui ne peut plus mentir.** Le store refuse une `setView`
  identique à la vue courante (`navigationStore.ts:57`) : tant qu'il reste
  bloqué sur une vue qui n'est plus affichée, plusieurs liens de
  l'application ne font **rien** (pastille contacts d'une conversation,
  carte du brief, renvois depuis les Réglages). Fermer la surface doit
  toujours remettre le store d'accord avec l'écran.
- **Une autorité d'Échap réellement branchée.** Soit `resolveEscape` reprend
  du service, soit on la supprime et la cascade devient la source déclarée.
  Ce qu'on ne peut pas garder : 14 composants qui délèguent à du code mort.
  La copie active a d'ailleurs perdu deux branches (`showCommandPalette`,
  `showConversationSidebar`).
- **Un test de véracité bidirectionnel** : tout raccourci annoncé existe, et
  tout raccourci qui existe est annoncé. Le test actuel ne vérifie qu'un
  sens.

*Rien n'est retiré* : mêmes surfaces, mêmes destinations, mêmes raccourcis.
Seul le comportement du retour devient prévisible.

## P0 bis — Un fichier joint disparaît au premier clic

Hors sujet UX, trouvé en chemin, et à corriger tout de suite :
`ProjectModal.tsx:104` appelle `api.deleteFile` **sans aucune
confirmation**, alors que l'application a déjà un mécanisme commun
(`requestExternalAction`) et cinq autres formes de confirmation ailleurs.
Un clic sur la corbeille, le fichier est perdu.

## P1 — Que cliquer produise quelque chose

- **Les cartes du tiroir ouvrent leur destination.** Elle est déjà déclarée
  dans le code (`destination: { kind: 'view' | 'deliverables' | 'images' | …
  }`) et déjà lue — mais seulement après validation du composeur. Le clic
  doit l'ouvrir directement. La phrase pré-remplie garde son sens pour les
  cartes qui n'ont pas de destination : elle devient l'exception, pas la
  règle.
- **La mise en route redevient joignable** sur une installation neuve.
- **« Écrire » mène à un composeur** — c'est le seul verbe de l'établi qui
  n'en propose aucun, alors que ses trois sœurs ont leur bouton de création.
- **Une commande de la palette qui ne produit rien** est rebranchée sur le
  geste réel (`actionRegistry.ts:50`).

*Rien n'est retiré* : on ajoute l'effet attendu là où il manquait.

## P2 — Que l'œil sache où se poser

- **29 éléments interactifs** sur l'écran par défaut, dont 13 de navigation
  ou de configuration. Objectif : hiérarchiser, pas supprimer — un rail dont
  les registres sont séparés, un composeur dont les 13 blocs ont une règle
  de priorité, des réassurances regroupées dans le Centre de confiance qui
  est déjà leur maison.
- **L'échelle typographique est écrasée** : 73 % du texte des surfaces
  chargées est en 12 px, la taille que la charte réserve aux métadonnées.
  Rétablir les niveaux intermédiaires suffit à créer une hiérarchie.
- **Trois informations affichées en permanence sont vides ou inexploitables**
  — les renseigner ou les retirer.
- **90 puces de vocabulaire technique** dans un catalogue destiné à des
  solopreneurs : les passer en révélation progressive plutôt que de les
  effacer.

## P3 — Que les mêmes choses se ressemblent

Chiffres relevés dans le code : **141 indicateurs de chargement** en 14
tailles, **5 formes d'état vide**, **2 systèmes de boutons**, **102
occurrences de `text-red-400`** qui ignorent le thème (le projet a déjà
corrigé ce motif ailleurs), **4 primitives de formulaire livrées et jamais
branchées** face à 257 champs stylés à la main.

Ordre : d'abord un composant unique pour le chargement et pour l'état vide
(gain immédiat, risque faible), ensuite les couleurs sémantiques, enfin la
convergence des boutons et des champs, qui est le plus gros morceau et peut
attendre.

## P4 — Les noms

Déjà cadré : quatre titres violent le lexique 0.48 (`Calendrier`,
`Facturation`, `Board de décision`, `Atelier de code`), deux canevas portent
le nom de leur domaine au lieu de leur travail, et les boutons « Ouvrir X »
promettent un agrandissement alors qu'ils mènent ailleurs. Le test qui
ferme la porte est **déjà écrit et rouge** :
`src/frontend/src/lib/lexiqueTitres.test.ts`.

Détail : `docs/plans/2026-08-27-noms-des-surfaces.md`.

## Ce que ce plan ne fait pas

- **Il ne retire aucune capacité.** Chaque chantier ajoute un comportement
  attendu ou unifie une implémentation ; aucun ne supprime une fonction.
- **Il ne tranche pas le cap produit** (application conversationnelle ou
  application à vues). Ce choix reste ouvert et n'est pas nécessaire pour
  exécuter ce plan.
- **Il ne fusionne pas les surfaces.** L'idée d'« une capacité, une surface »
  reste valable comme direction, mais elle devient une conception nouvelle,
  pas une suppression de doublon — à reprendre quand le cap sera fixé.

## Ordre recommandé

P0 et P0 bis d'abord : ils corrigent des défauts, pas des préférences. Puis
P1, qui rend l'application obéissante. P2 et P4 ensuite, qui la rendent
lisible. P3 en dernier, par lots, parce que c'est le plus long et le moins
visible.

Chaque étape : TDD, gates complets (pytest hors e2e, vitest, tsc, eslint 27,
mypy fresh), revue Soso sur le diff, et recette visuelle dans l'app packagée
pour les changements d'écran.

## Vérification propre à ce plan

Deux garanties mécaniques à poser, parce qu'elles empêchent la dérive de
revenir :

1. **Un test de retour** : depuis chaque vue embarquée, fermer ramène à
   l'écran précédent, en un seul geste, et la pile reflète l'écran affiché.
2. **Un test de véracité bidirectionnel** sur les raccourcis et les actions
   annoncées.
