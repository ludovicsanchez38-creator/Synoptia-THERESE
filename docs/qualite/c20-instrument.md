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
