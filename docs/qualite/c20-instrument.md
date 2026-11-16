# Cycle 20 : lot instrument

## Verdict et preuves

Les lignes « rouge » ont été relevées avant toute modification de l'instrument. Le cinquième test complète la vérification après le correctif et n'a pas été rejoué sur la base. Aucun commit n'a été créé : l'orchestrateur rejouera les tests sur la base sans correctif et effectuera les commits.

| ID | Verdict | Test (chemin::nom) | Rouge observé | Correctif |
| --- | --- | --- | --- | --- |
| B-2029 | confirme | `tests/couverture/couverture-ecran.test.mjs::B-2029 : seule la migration exacte du chat est simulable` | `not ok 1 - B-2029 : seule la migration exacte du chat est simulable` | non commité |
| B-2029 | confirme | `tests/couverture/couverture-ecran.test.mjs::B-2029 : la garde acquitte et compte la migration sans accès réseau` | `not ok 2 - B-2029 : la garde acquitte et compte la migration sans accès réseau` | non commité |
| B-2029 | confirme | `tests/couverture/couverture-ecran.test.mjs::B-2029 : le parcours avec la seule migration du chat écrit son rapport` | `not ok 3 - B-2029 : le parcours avec la seule migration du chat écrit son rapport` | non commité |
| B-2029 | confirme | `tests/couverture/couverture-ecran.test.mjs::B-2029 : une interruption conserve les simulations et bloque la migration avec paramètre` | `not ok 4 - B-2029 : une interruption conserve les simulations et bloque la migration avec paramètre` | non commité |
| B-2029 | confirme | `tests/couverture/couverture-ecran.test.mjs::B-2029 : les autres écritures bloquées interrompent aussi le parcours` | Test complémentaire ajouté après le correctif ; rouge non observé. | non commité |

Le rouge de la garde montre `action: 'abort'` et `raison: 'blockedbyclient'` au lieu de `action: 'fulfill'`. Dans le parcours factice, les deux POST de migration apparaissaient dans les requêtes bloquées et provoquaient l'interruption. Le premier test constatait l'absence de fonction exportée pour décider de la simulation ; le quatrième constatait deux blocages là où seule la requête avec paramètre devait être bloquée.

Le stockage utilisé par `chatStore` émet le POST depuis `chatPersistence.ts`. L'instrument exécuté en CLI installe effectivement `installerGardeReseau` dans `principal`, puis contrôle les blocages avant d'écrire son rapport. Le test de parcours exerce cette CLI avec une page, un contexte et les réponses de vérification factices : il a reproduit l'interruption avant le correctif, puis vérifié l'écriture de `rapport.json` après celui-ci.

La garde acquitte maintenant uniquement le POST exact de migration du moteur jetable avec un HTTP 200 et `{"success":true}`, sans le transmettre au réseau. `requeteAutorisee` conserve sa signification et refuse toujours ce POST. La prévisualisation déjà autorisée conserve son comportement. Les autres POST testés, notamment avec paramètre ou sur les ports du frontend et du moteur réel, restent bloqués et interrompent le parcours.

Les deux rapports portent sous `garde.ecritures_simulees` un `nombre` et une liste `requetes` contenant la méthode et l'adresse sans paramètres ni identifiants. Les simulations sont distinguées des requêtes bloquées et des écritures effectivement transmises.

## Portes

- Reproduction isolée avant correction, tests B-2029 : **0 réussi, 4 échoués**, aucun ignoré. Les quatre noms figurent dans le tableau ; les échecs étaient attendus.
- Vérification ciblée après correction, avant ajout du test complémentaire : **4 réussis, 0 échoué**, aucun ignoré.
- `node --test tests/couverture/couverture-ecran.test.mjs` : **25 tests, 13 réussis, 0 échoué, 12 ignorés**, aucun annulé. Noms des échecs : **aucun**. Les 12 tests ignorés nécessitent un navigateur ; ils ont été volontairement désactivés. Un répertoire personnel temporaire sous `/private/tmp` a isolé les fichiers créés par les tests existants.
- Portes backend, frontend et suites complètes : non lancées conformément à la consigne propre à ce lot, qui limite l'exécution au fichier de tests Node ci-dessus.

## Limite de la preuve

Aucun navigateur, parcours réel, fournisseur LLM ou service en ligne n'a été lancé. La recalibration et la vérification sur la pile jetable restent à effectuer par l'orchestrateur. Aucun fichier produit sous `src/` n'a été modifié.

## Remédiation de la relecture, passe 1

Le constat P2 est confirmé : une interruption pouvait être enregistrée avant la fin d'un acquittement concurrent. Le nouveau test `tests/couverture/couverture-ecran.test.mjs::B-2029 remédiation : une interruption conserve les acquittements concurrents` exerce la CLI avec une page, des requêtes et un système de fichiers factices. Il déclenche deux acquittements concurrents et un POST bloqué, puis termine le premier acquittement et rejette le second après le retour de la fermeture factice. Il vérifie la cause, le POST bloqué et la présence du seul acquittement réussi dans le rapport.

Rouge observé sur le test seul avant correction :

```text
not ok 1 - B-2029 remédiation : une interruption conserve les acquittements concurrents
```

L'assertion relevait `nombre: 0` et `requetes: []` au lieu d'une écriture acquittée. Après correction, le même test isolé passe : **1 réussi, 0 échec**. La garde suit les acquittements en cours ; après fermeture du navigateur, leurs promesses sont réglées avant la rédaction du rapport. Un acquittement rejeté n'est pas comptabilisé et ne remplace pas la cause initiale de l'interruption. Le suivi reste hors de l'objet sérialisé.

Portes de cette passe :

- `couverture-ecran.test.mjs` : **14 réussis, 0 échec, 12 ignorés** sur 26. Les tests navigateur sont restés désactivés. Les répertoires temporaires et leur corbeille factice ont été redirigés dans cet arbre. Deux premiers essais ont échoué dans les hooks de déplacement vers la corbeille factice absente ; après correction de cette isolation, le rejeu est vert.
- `tests/couverture/test_backend_offline.py` : **19 réussis, 0 échec, 0 erreur, 0 ignoré**. Résultat vérifié dans `/tmp/instrument-r1.xml`.
- `ruff check --no-fix src/backend tests` : **aucune erreur**. Un premier lancement avait refusé la valeur `1` de `RUFF_NO_CACHE` ; le rejeu avec `true` passe.
- `b1102-snapshot-chromium.test.mjs` : **0 réussi, 2 échecs** au lancement de Chromium, avant les assertions. Les deux échecs se reproduisent avec les fichiers commités avant cette remédiation. La variante headless révèle un refus `bootstrap_check_in ... Permission denied` par l'environnement ; ces deux contrôles restent à rejouer sur une machine où Chromium démarre.

La surcouche `sandbox-exec` a elle-même été refusée par l'environnement. Les tests de la garde et de la CLI utilisent des accès factices ; les tentatives Chromium ont été faites sans serveur ni navigation et n'ont pas atteint les assertions. Aucun parcours réel, fournisseur LLM ou service en ligne n'a été lancé. La suite complète n'a pas été lancée et les changements de cette passe restent non commités.
