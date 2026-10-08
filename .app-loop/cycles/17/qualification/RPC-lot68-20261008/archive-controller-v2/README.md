# Contrôleur lot68 v2, préparation statique

Successeur distinct de `/private/tmp/therese-c17-lot68-archive-controller-vVzFqI`, qui reste figé avec son premier refus réel `8cd0c2`. `PLAN.json` est sa copie byte-exacte : mêmes 22 racines, mêmes ancres, même limite de 64 MiB par TAR gzip, même sélection INDEX + 24 références de la source fraîche et ROOT10 natif toujours différé dans ce plan. Aucune archive n'est produite ici.

Le seul delta de sélection est l'exclusion de `fixtures/` à la racine d'une sortie de tests, une fois son reçu `row.result` validé avec le SHA de l'ancre et la valeur attendue. Les classes autorisées sont exactement `pure_green` et `raw_red`; définitions, autorité, diagnostic, préflight, signature Chrome et source QA ne bénéficient d'aucune exclusion. Les métadonnées d'exclusion sont conservées dans le reçu. La correction ne contourne donc pas un `.git` étranger ou une dépendance hors fixture.

Préimage, diff reconstruit et retour rouge sont conservés dans ce dossier. `node --check` contrôle seulement la syntaxe ; ni ce contrôleur ni son supplément n'ont été exécutés par l'auteur. Après revue externe, l'invocation future exige `--execute`, le SHA exact du plan et une destination neuve sous `/private/tmp/therese-c17-lot68-archive-<id>` ; aucun chemin canonique n'est visé.
