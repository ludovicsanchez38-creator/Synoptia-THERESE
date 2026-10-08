# Refus réel du contrôleur22 v1

Retour main identifié par le fragment d'exécution `8cd0c2` : code 1 avant création de la destination et de toute archive. Le parcours v1 a rencontré `.git` sous `/private/tmp/therese-c17-worker-context-tests-root-uWFp3P0s/fixtures/test_binding_boolean_bytes/therese-c17-synthetic-source/source/.git` et a refusé conformément à sa règle. Aucun reçu d'archive vert n'a été produit. Ce document consigne le retour transmis par main, sans prétendre être une copie du flux brut de l'outil.

Inventaire borné des seules sorties de tests prévues dans le plan22 : `fixtures/` top-level est présent pour worker-context, préallocation v1/v2 et replay V10 v3. Les fixtures de préallocation contiennent elles aussi `.git` et `node_modules` synthétiques. Les autres sorties inspectées ne présentent pas de `.git` dans les cinq premiers niveaux ; `synthetic-fixtures/` de RPC n'est pas exclu par la correction. Aucun checkout QA réel n'a été parcouru pendant cet inventaire.

La v2 exclut seulement `fixtures/` top-level après validation de `row.result` épinglé et seulement si `class` est `pure_green` ou `raw_red`. Elle inscrit `fixtures/` dans `excluded` du reçu de la future archive. Tous les autres `.git`, dépendances, symlinks, sockets et types non réguliers restent soumis aux refus de v1 ; les 24 références choisies de la source fraîche ne changent pas.
