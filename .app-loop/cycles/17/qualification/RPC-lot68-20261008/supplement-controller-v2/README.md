# Supplément d'archives du lot 68, v2 préparée

Ce contrôleur reprend byte pour byte le contrôleur22 v2 comme préimage, puis change uniquement l'identité du plan, sa cardinalité fermée à 12, les schémas du reçu et le préfixe de destination privée. Son exclusion très étroite des fixtures synthétiques reste identique à la v2 du contrôleur22. Le supplément initial sous `...archive-supplement-qFaQPh` demeure intact et non exécuté.

`PLAN.json` épingle les racines physiques de deux contrôles de préallocation, du gel Git et des sorties Python46, Python47 et Node, du gel listener et de son contrôle/sortie Node, des deux rechecks de signature Chrome et du contrôleur22 original. Python46 est une observation historique non additive. Les rechecks Chrome sont séparés rouge/vert et ne sont jamais des résultats purs ni natifs. Aucun résultat ROOT10 natif, même désormais clos rouge, n'est inclus dans ce plan ; il exige une révision explicite ultérieure.

Le contrôleur vérifie les ancres SHA et statuts avant création d'une destination, écrit au plus 64 MiB par TAR USTAR gzip, vérifie types/chemins/membres/SHA/bytes et recontrôle les sources après. Il refuse symlinks, `.git` non sélectionné, dépendances, types inconnus et sorties existantes. `fixtures/` top-level ne peut être exclu qu'après résultat épinglé validé sur une ligne de sortie de test de classe exacte `pure_green` ou `raw_red`; aucune ligne du supplément n'emploie cette exception. La copie du contrôleur22 original est archivée comme code/provenance, pas comme preuve d'exécution verte.

Préparation uniquement : `node --check archive_lot68_supplement_v2.mjs` a rendu 0. Aucune archive ni copie canonique n'a été faite. Future invocation root, après revue des pins :

```
node /private/tmp/therese-c17-lot68-archive-supplement-v2-qvX6gv/archive_lot68_supplement_v2.mjs --execute --expected-plan-sha256 <SHA256_PLAN_JSON> --out-dir /private/tmp/therese-c17-lot68-supplement-archive-<id-neuf>
```
