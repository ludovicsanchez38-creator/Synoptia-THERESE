# Chantier E — Nommage et accessibilité

Design soumis à relecture AVANT code. **Rien n'est codé.**

Le plus petit des chantiers, et celui qui touche le plus de personas : huit sur
dix ont buté sur un mot.

## E1 — Le focus se pose sur un bouton invisible (U1)

Trouvé par la passe navigateur, mesuré :

```json
{"focusEstSurLeBouton": true, "labelFocalise": "Supprimer",
 "focusVisible": true, "opaciteDuConteneur": "0"}
```

Les actions de ligne de *Devis et factures* vivent dans
`opacity-0 group-hover:opacity-100`. Les boutons restent dans le flux de
tabulation. Il manque `group-focus-within:opacity-100`.

Nuance conservée : le clic ouvre une confirmation visible, donc c'est un
manquement de visibilité du focus (WCAG 2.4.7), pas une perte de données.

## E2 — « Écrire » affiche trois libellés de lecture (U3)

Après un clic sur **Écrire** :

| Où | Texte |
|---|---|
| sous-titre de l'accueil | « Je **consulte** la boîte connectée » |
| carte du parcours | « **Messages à consulter** » |
| titre du canevas | « **Lecture** et brouillon » |

Le verbe cliqué est *Écrire*. `scenarioLabels.email` est le titre accessible du
canevas : un utilisateur au lecteur d'écran clique **Écrire** et s'entend
annoncer **« Consulter mes emails »**.

## E3 — Le gate de lexique ne voit rien de tout ça

`lexiqueTitres.test.ts` existe et ne couvre ni `scenarioLabels`, ni
`scenarioPrompts`, ni les sous-titres de carte. C'est pour ça que la dérive est
passée — et qu'elle repassera.

## E4 — Le jargon relevé par l'artisan

Dix-neuf mots, avec fichier et ligne : *canevas*, *profil émetteur*,
*référentiel contacts*, *facturation locale*, *THERESE.md*, *contexte
additionnel*, *capacités*, *parcours*, *scopes*, *indexation*, *pipeline*…

« Un mot que je ne comprends pas, je ne le demande pas, je ferme. »

## Questions au relecteur

1. **E1** : `group-focus-within` suffit-il, ou faut-il aussi rendre les actions
   visibles en permanence sur écran tactile (pas de survol) ?
2. **E2** : renommer `scenarioLabels.email` casse-t-il un test, un deep link,
   une commande de palette ?
3. **E3** : quelle forme de gate ? Une table `verbe → libellés attendus` serait
   rigide ; un test qui interdit « consulter » dans le parcours *Écrire* est
   plus souple mais plus faible.
4. **E4** : lesquels valent le coût ? Certains sont des termes de l'interface
   (canevas, parcours) qui ont un sens pour l'équipe. En renommer un touche
   beaucoup de fichiers.
5. Y a-t-il un **cinquième défaut d'accessibilité** que la passe navigateur n'a
   pas vu et que le code révèle ?
