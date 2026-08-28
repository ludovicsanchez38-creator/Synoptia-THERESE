# U2 - L'entrée 9 et son correctif tiennent en navigateur réel

**Ce n'est pas un défaut : c'est la validation que les tests unitaires ne
pouvaient pas produire.**

Le plan UX du 27/08 réclamait « un gate clavier en navigateur réel à 1279 et
1280 px — les tests unitaires ne valident ni `inert`, ni Tab, ni les couches
superposées ». Il n'existait pas. Voici la mesure.

## Le contexte

L'entrée 9 (v0.53.0) fait survivre le canevas à l'ouverture du chat au-dessus du
seuil `xl`. La relecture Grok avait trouvé que `estCoteACote()` est un
**instantané** lu à l'ouverture, alors que l'isolation suit la largeur en
continu : ouvrir large puis rétrécir posait `inert` sur la conversation restée à
côté. Correctif livré le matin même.

**Le mock des tests ne pouvait pas le voir** : ses auditeurs `matchMedia` sont
des `vi.fn()`, personne ne reçoit jamais l'événement `change`.

## Mesuré dans le navigateur

À **1280 px**, parcours « Préparer » ouvert (canevas monté), puis clic sur
*Nouvelle conversation* :

```json
{"largeur": 1280, "canevasPresent": true, "chatPresent": true, "chatInerte": false}
```

Les deux surfaces coexistent, le chat est vivant. **C'est le contrat de
l'entrée 9.**

Puis redimensionnement à **1279 px**, sans rien d'autre :

```json
{"largeur": 1279, "canevas": false, "chatPresent": true,
 "chatInerte": false, "composeurUtilisable": true}
```

Le canevas a cédé la place, le chat reste vivant et le composeur prend le focus.
**Le correctif tient.**

Note d'observation : le canevas met un cycle de rendu de plus que prévu à
quitter le DOM (`AnimatePresence` + la bascule d'état). Une mesure prise à
l'instant du redimensionnement le voit encore présent. Ce n'est pas un défaut —
le chat n'est à aucun moment inerte — mais c'est exactement le genre de délai
qui rendrait un futur test E2E instable s'il n'attendait pas la disparition.

## Ce que ça vaut

Le seul chemin par lequel ce correctif pouvait être vérifié était un navigateur.
Il est maintenant vérifié.
