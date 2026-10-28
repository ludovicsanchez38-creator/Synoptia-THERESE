# Lot 11 : régressions de l’intégration c22

Rapport du 28 octobre 2026. État du code validé : `b5165422`. Branche `boucle/c22-integration`, départ `3f3404c4`, référence `45be2f16`.
Travail effectué dans l’arbre courant uniquement, sans changement de branche ni action distante.
Aucun chemin `-o` n’était indiqué dans la demande. Le chemin de repli annoncé est celui de ce rapport.

## Correctifs

| Point | État | Commit et vérification |
| --- | --- | --- |
| Notifications accentuées | Fait | `8eef460c` fix(notifications): expliciter les rappels avec et sans horaire (B-1047). Le test AST reconnaît de nouveau « RDV demain à ». Les branches avec horaire et journée entière sont explicites ; leur texte affiché est conservé. |
| Recherche web confirmée | Fait | `70c85f29` test(chat): simuler la réponse après recherche confirmée (B-1319). Le test simule le modèle, vérifie la synthèse renvoyée, la transmission des résultats bruts au modèle, le repli sur la requête, la comptabilisation et l’absence de nouveaux outils. Aucun besoin d’Ollama. |
| Connexions SQLite et lecture portable | Fait | `febdf392` fix(tests): fermer les bases et lire les témoins en UTF-8. Six connexions des tests de reprise et de Reply-To sont enveloppées dans `closing`. Les écritures conservent aussi la transaction pour valider leurs insertions. Lecture du témoin avec `encoding="utf-8"`. Les deux portes restent inchangées. |
| Profil de facturation déjà configuré | Fait ; question produit ci-dessous | `010bfab9` fix(facturation): préserver le statut des profils déjà configurés. Le statut reprend les critères historiques nom ou société, SIRET et adresse. Les deux régressions passent sans enrichir leurs profils de test. Le contrôle supplémentaire d’identité lors de la génération du PDF reste exercé par les tests c22b. |
| Périmètre des pièces jointes | Fait | `18556a69` test(documents): respecter le contrat de retour de l’indexeur (B-1213). Les quatre doublures renvoyaient `None`, hors contrat de l’indexeur réel. Elles renvoient désormais un vrai `FileResponse` avec un fragment. Toutes les assertions de périmètre et de provenance sont conservées. Le PDF sans texte reste refusé avec 422. |
| Génération de réponse et Reply-To | Fait | `c45251c8` test(messagerie): vérifier les brouillons tardifs avec Reply-To (B-1296). Les messages fictifs portent leurs en-têtes vérifiés. Le test garde le refus du brouillon tardif A, puis vérifie que B compose son propre texte à son adresse Reply-To. |
| Aide et Plus d’outils | Fait | `0ec7e113` test(accueil): vérifier les accès distincts à l’aide et aux outils. L’ancienne assertion interdisait toute entrée Aide. Le test ouvre désormais l’aide et son guide, vérifie qu’elle n’ouvre pas Capacités, puis ouvre le tiroir avec Plus d’outils. |
| Rayons et contrastes | Fait | `b37f6484` fix(interface): respecter les jetons de contraste et de rayon. Les trois nouveaux composants utilisent `rounded-sm` ou `rounded-md` et les liens utilisent `text-accent-cyan-ink`. Les trois tests de garde ne sont pas modifiés. |
| Erreurs mypy nouvelles | Fait | `97041172` fix(typage): corriger les huit diagnostics ajoutés par c22. Les huit diagnostics ont disparu ; le cliquet CI est abaissé à 935. |
| Dépendance Opener | Fait, aucune modification requise | `src/frontend/package.json` déclare `@tauri-apps/plugin-opener` en `2.5.0`. Le manifeste racine et l’entrée résolue de `src/frontend/package-lock.json` portent également `2.5.0`, tout comme le module installé. Le package racine du dépôt délègue le développement et la construction au frontend. |
| Isolation des dossiers temporaires Git | Fait | `b5165422` test(agents): isoler les dépôts temporaires du dépôt parent (B-099). Les deux fixtures, dans `tests/test_agents_depot_autorise.py` et `src/backend/tests/test_agents.py`, bornent la recherche des dépôts ancêtres avec `GIT_CEILING_DIRECTORIES`. Le vrai Git et les assertions de périmètre ou d’absence de dépôt restent utilisés. |
| E2E complet | Pas fait, conformément à la demande | À rejouer par Syn. Aucun serveur de recette démarré. |

## Tests ciblés

Reproduction avant correction, dans l’environnement des portes : **10 échecs et 17 réussites** sur la sélection pytest, **5 échecs et 45 réussites** sur les quatre fichiers Vitest. Les échecs correspondent à ceux signalés.

Après correction : **104 tests Python réussis**, **63 tests Vitest réussis** sur neuf fichiers, aucun échec.

Python : `test_c19d_b1047.py`, `test_c22b_recurrences.py`, `test_c20f_notifications_paris.py`, `test_confirm_tool_endpoint.py`, `test_c22b_recherche_confirmee.py`, `test_connexions_sqlite_fermees.py`, `test_lecture_de_fichier_portable.py`, `test_reprise_copies_auto.py`, `test_c22b_reply_to.py`, `test_lot7_mecaniques.py::TestB387B411LeStatutDeFacturationLitLaBaseQuandLeCacheEstVide`, `test_regression.py::TestP0PROD2_BillingProfile`, `test_billing_profile_cache.py`, `test_c22b_identite_facture.py`, `test_scope_piece_jointe_chat.py` et `test_c22b_pdf_sans_texte.py`.

Vitest, sous `src/frontend/src/` : `components/email/EmailDetail.sessionGeneration.test.tsx`, `components/email/EmailDetail.replyTo.test.tsx`, `components/prototype/Etabli.test.tsx`, `styles/rayons.test.ts`, `test/a11y.test.tsx`, `components/Aide.test.tsx`, `components/llm/GuidePremierServiceIA.test.tsx`, `components/RepriseDonnees.test.tsx` et `lib/pdfLocaux.test.ts`.

TypeScript : `tsc --noEmit --incremental false -p src/frontend/tsconfig.json` réussi. Ruff sur les fichiers Python modifiés et `git diff --check` réussis.

## Référence mypy et méthode

La référence est extraite par `git archive 45be2f16` sous `scratchpad/lot11/base/`, dans cet arbre, sans créer ni modifier un autre worktree. L’extraction conserve `src/backend/__init__.py`, `src/backend/app/` et `pyproject.toml`. Le marqueur de paquet est nécessaire pour conserver les mêmes noms de modules ; un premier essai qui l’omettait a été écarté, car non comparable.

La commande demandée, avec le même exécutable `.venv/bin/mypy`, les mêmes dépendances et un environnement vidé, donne **936 erreurs sur la référence**, contre **943 dans le journal c22 initial**. La comparaison des diagnostics donne **huit erreurs nouvelles et une ancienne disparue** : il ne suffit donc pas de retirer sept erreurs quelconques.

Erreurs nouvelles : deux annotations du middleware de reprise, trois retours des routes de reprise, un retour de la route d’ouverture de PDF, le retour textuel de l’identifiant de calendrier et la signature de la clé de tri des occurrences CalDAV. L’erreur disparue concernait l’ancien appel de `_caldav_event_to_dto` avec un `CalendarObjectResource`.

Le passage final donne **935 erreurs**, aucune nouvelle et la même erreur CalDAV disparue. La comparaison tient compte des lignes déplacées avec un rapprochement des sources et conserve la multiplicité des diagnostics ; les 935 diagnostics restants sont rattachés à des lignes de la référence. Aucun `type: ignore` ni assouplissement de configuration mypy n’a été ajouté.

Le contrôle CI exige une égalité stricte et aurait rejeté ce progrès avec son ancien seuil 936. Son script réel a été rejoué avec une sortie mypy simulant les 935 erreurs mesurées : code 1 avant recalage, code 0 après abaissement du seuil à 935. L’exécution sur un runner GitHub n’est pas vérifiée.

## Portes complètes

Un passage complet terminé de chaque suite demandée, avec `nice -n 10` et un HOME neuf sous `scratchpad/lot11/final/home` (Vitest et mypy) ou `scratchpad/lot11/final/pytest-home` (pytest). Pour Python : environnement vidé, `OLLAMA_BASE_URL=http://127.0.0.1:1`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `LANG=C.UTF-8` et PATH de la porte. Vitest reprend l’environnement vidé de sa porte et `--maxWorkers=2`.

```text
nice -n 10 .venv/bin/python -m pytest tests/ --ignore=tests/e2e -q -p no:cacheprovider --junitxml=<sortie>/pytest.xml
cd src/frontend
nice -n 10 node_modules/.bin/vitest run --maxWorkers=2
# depuis la racine :
nice -n 10 .venv/bin/mypy src/backend/app --ignore-missing-imports --no-error-summary --cache-dir=/dev/null
```

| Suite | Base c21 `45be2f16` | Intégration initiale | Résultat final |
| --- | --- | --- | --- |
| pytest `tests/` hors e2e | 6 152 réussis, 0 échec (chiffre fourni par Syn) | 6 167 réussis, 10 échecs, 15 ignorés | Passage complet : **6 175 réussis, 2 échecs de tests corrigés ensuite, 15 ignorés**, code 1, 1 131,92 s. Rejeu ciblé : **8/8 réussis**. Consolidation : **6 177 réussis, 0 échec, 15 ignorés**. |
| Vitest complet | 3 922 réussis, 0 échec (chiffre fourni par Syn) | 3 938 réussis, 5 échecs | **3 943 réussis, 0 échec**, 904 fichiers, code 0, 1 081,32 s |
| mypy | **936 erreurs mesurées** | 943 erreurs | **935 erreurs**, **0 nouvelle**, 1 ancienne disparue, code 1 attendu pour la dette restante |

Les dix échecs pytest initiaux ont disparu du passage complet. Ses deux échecs résiduels sont documentés ci-dessous et passent après correction en sélection ciblée. La consolidation par identifiant de test remplace ces deux résultats par leur rejeu : **6 177 réussites et 15 ignorés**, soit 25 réussites de plus que la base. Ce total consolidé ne représente pas un deuxième passage complet vert. La suite complète n’a pas été répétée après ces deux dernières corrections de tests, conformément à la demande d’un seul passage complet.

Vitest gagne 21 réussites par rapport à la base. Le typage conserve une dette de 935 erreurs préexistantes ; la disparition des huit erreurs nouvelles ne signifie pas que le dépôt est entièrement typé.

Le premier lancement pytest a été interrompu après 1 785 cas (1 772 réussites, 12 ignorés et un échec), car son TMPDIR sous cet arbre révélait une hypothèse de fixture : le dossier « sans dépôt » héritait du Git parent et la route répondait 409 au lieu de 404. Le problème a été reproduit isolément (4 réussites, 1 échec), corrigé dans la fixture, puis vérifié (5 réussites). Le passage complet final a été relancé avec un HOME neuf. Ce lancement partiel n’est pas compté comme une suite complète et ses preuves restent dans `pytest-partiel.{log,xml}` et `diagnostic/`.

Le passage complet a ensuite révélé deux erreurs de tests :

1. `test_cliquet_mypy_ci.py::TestCliquetMypy::test_la_baseline_est_celle_mesuree_sur_le_runner` figeait encore `936`. Il est recalé à `935` avec le workflow, sur la mesure comparative ; l’égalité reste stricte.
2. `test_harnais_backend_autonome.py::test_le_dossier_src_backend_tests_tient_seul` échouait parce que son sous-processus exécutait `src/backend/tests/test_agents.py::TestGitService::test_is_repo_false`, qui découvrait à son tour le dépôt parent. Ce second test de dossier vierge reçoit la même isolation Git.

Sélection de ces deux fichiers ou cas : **6 réussites et 2 échecs avant**, puis **8 réussites et aucun échec après** (`diagnostic/pytest-portes-{avant,apres}.xml`). Le sous-processus backend autonome est bien exercé par le second cas, sans supprimer ni ignorer de test. Les dernières corrections ont été regroupées dans les commits de typage et d’isolation concernés.

Les preuves locales, non versionnées, sont sous `scratchpad/lot11/` : `pytest-avant.xml`, `vitest-avant.log`, `pytest-correctifs.xml`, `vitest-correctifs.log`, `mypy-base.log`, `mypy-ecart-initial.json`, `comparer_mypy.py`, `tsc.log`, `cliquet-{avant,apres}/resultat.log` et `final/{pytest.xml,pytest.log,pytest-consolide.json,vitest.log,mypy.log,mypy-ecart.json}`. Les comptes pytest proviennent des XML, car le hook de sortie du dépôt peut interrompre l’affichage du résumé console.

## Question et limites

**Question produit :** faut-il à l’avenir inclure la forme juridique et, selon celle-ci, le capital dans le statut global « profil complet » ? Si oui, quel parcours proposer aux utilisateurs déjà configurés pour compléter ces informations ? En attendant une décision, le critère historique est conservé, comme demandé. Ce statut ne vaut pas validation des mentions d’un PDF.

Pas de recette native Windows ou macOS, de lecteur PDF réel, de fournisseur IA réel ni de compte CalDAV réel. Les tests utilisent des données et services simulés. La suite autonome `src/backend/tests/` n’a pas de lancement supplémentaire séparé : elle est exécutée par son test de harnais dans `tests/`, y compris dans le rejeu ciblé. L’E2E complet reste à Syn.
