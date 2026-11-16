# Cycle 20, lot diff-4

Arbre `gpt-c20-diff-4`, branche `gpt/c20-diff-4`, HEAD de départ et d'arrivée `4dfc79d1`. Trois candidats confirmés et corrigés, deux règles à trancher, cinq candidats rejetés. Vérifications locales sur le code présent dans cet arbre.

La consigne particulière du bac à sable remplace les commits : aucun `git add`, commit, push, dépôt annexe ou bundle. Les trois scripts, leurs trois nouveaux fichiers de tests et ce rapport restent non commités. Aucun test existant n'a été modifié, affaibli ou supprimé.

## Verdicts, dans l'ordre demandé

La colonne « Rouge observé » remplace le commit rouge ; les messages viennent des XML JUnit lus après chaque exécution isolée. « Sans objet » signifie qu'aucune attente nouvelle n'a été imposée au code.

| Id | Verdict | Test (chemin::nom) | Rouge observé | Correctif |
| --- | --- | --- | --- | --- |
| B-1883 | `confirme` | `tests/test_c20_b1883_finaliser_recette.py::test_finalisation_conserve_echec_portes[1-0-1]` | `assert 0 == 1`, avec `SystemExit(0).code` | non commité |
| B-1885 | `confirme` | `tests/test_c20_b1885_banc_ollama.py::test_verdict_exige_un_journal_lu[False-troncatures0-1]` | `AssertionError: assert 0 == 1` malgré `journal_serveur_lu: False` | non commité |
| B-1897 | `regle_a_trancher` | `src/frontend/src/lib/consentSync.profiles.test.ts::reprend la file historique avant de purger les caches de A` | Sans objet : attribution d'une décision nouvelle sans profil non définie | aucun changement |
| B-1898 | `regle_a_trancher` | `tests/test_c19d_b1088_securite_memoire.py::test_faux_positifs_differes_et_contre_exemples_v5` | Sans objet : l'assouplissement est explicitement différé à un arbitrage | aucun changement |
| B-2008 | `confirme` | `tests/test_c20_b2008_mime_recette.py::test_ressources_statiques_ont_un_type_mime[police.woff2-font/woff2]` | `Expected: fulfill(body=b'ressource fictive', content_type='font/woff2')` ; `Actual: fulfill(body=b'ressource fictive', content_type='application/octet-stream')` | non commité |
| B-2023 | `rejete` | `src/frontend/src/test/c19d/B-1067.test.ts::B-1067 : contrat du libellé ou de la structure` | Sans objet : « bientôt » concerne une expiration | aucun changement |
| B-2024 | `rejete` | `tests/test_b1110_agenda_local_recurrent.py::test_dates_ics_creees_par_api_restent_lisibles` ; `test_ancienne_serie_dense_signalee_et_rendez_vous_independant_rendu` | Sans objet : accents déjà présents | aucun changement |
| B-2025 | `rejete` | `tests/test_c22b_pdf_sans_texte.py::test_scan_avertit_le_chat` | Sans objet : JPEG est une solution alternative proposée | aucun changement |
| B-2026 | `rejete` | `tests/test_r1_10_tutoiement.py::test_tutoiement_par_defaut_et_consigne_personnelle_conservee` | Sans objet : les deux registres ont des périmètres distincts | aucun changement |
| B-2027 | `rejete` | `tests/test_c22b_identite_facture.py::test_piece_deja_emise_sans_adresse_ne_propose_pas_de_modifier_le_brouillon` | Sans objet : une pièce émise n'est plus un brouillon modifiable | aucun changement |

## Corrections et chemin d'exécution vérifié avant modification

### B-1883

`scripts/finaliser_recette_r6.py` exécute directement les deux sous-processus à son lancement. Son rôle de clôture est documenté dans `docs/recette/2026-10-21-r6.md:36`. `portes_r6.py:43` refuse toute porte en échec sauf mypy, traité par comparaison de diagnostics. Le comparateur ne remplace donc pas ce code de sortie.

Le test exécute le véritable lanceur par `runpy`, depuis une copie temporaire, avec les sous-processus simulés. Rouge : **1 échec, 3 réussites**, précisément `test_finalisation_conserve_echec_portes[1-0-1]`. Le lanceur retournait zéro pour des portes rouges et une comparaison verte.

Correction : conserver le code des portes et renvoyer `code_portes or code`. Le comparateur reste exécuté pour produire son bilan. Vert : **4 réussites**. XML : `/tmp/diff-4-b1883-rouge.xml` et `/tmp/diff-4-b1883-vert.xml`.

### B-1885

`scripts/achever_recette_r4.py:70` lance le banc ; son entrée principale appelle `lancer`, puis `mesurer` dans le processus enfant. `mesurer` appelle `enregistrer_verdict`, également utilisé par `--evaluer`. C'est ce véritable calcul du verdict que le test exerce, sans démarrer le banc ni un fournisseur.

Rouge : **2 échecs, 3 réussites**. Les deux échecs sont `test_verdict_exige_un_journal_lu[False-troncatures0-1]` et `test_verdict_exige_un_journal_lu[None-troncatures1-1]`, chacun avec `AssertionError: assert 0 == 1`. Une preuve explicitement absente, ou un ancien résultat sans indication de lecture, passait au vert.

Correction : relever la position du journal avant la passe et analyser seulement les lignes nouvelles à la fin. Le contrat d'emplacement du journal est documenté dans l'en-tête de `scripts/banc_ollama_r4.py`. Une absence, une erreur de lecture, une rotation, un raccourcissement ou un chemin extérieur empêchent de déclarer la lecture complète. Le verdict exige cette lecture en plus de l'absence de troncatures effectives ; `truncated = 0` conserve son sens précédent.

Vert : **10 réussites**, comprenant la lecture après un ancien avertissement, les nouvelles troncatures et les journaux inexploitables. XML : `/tmp/diff-4-b1885-rouge.xml` et `/tmp/diff-4-b1885-vert.xml`. Un résultat historique sans preuve de lecture devient volontairement rouge lors de `--evaluer` ; aucun ancien test ne codifiait le succès de ce cas.

### B-2008

Le script installe `servir` par `page.route('**/*', servir)` avant la navigation. Le test exécute le véritable script avec Playwright simulé, récupère le gestionnaire enregistré et lui fait servir des fichiers temporaires. Il vérifie le corps et le type MIME réellement transmis à `route.fulfill`, ainsi que les refus de destinations extérieures ou de fichiers absents.

Rouge : **6 échecs, 7 réussites**, dans `test_ressources_statiques_ont_un_type_mime`, avec les paramètres suivants :

| Paramètre échoué | Type attendu | Type observé |
| --- | --- | --- |
| `police.woff2-font/woff2` | `font/woff2` | `application/octet-stream` |
| `police.woff-font/woff` | `font/woff` | `application/octet-stream` |
| `icone.svg-image/svg+xml` | `image/svg+xml` | `application/octet-stream` |
| `photo.png-image/png` | `image/png` | `application/octet-stream` |
| `photo.JPG-image/jpeg` | `image/jpeg` | `application/octet-stream` |
| `photo.webp-image/webp` | `image/webp` | `application/octet-stream` |

Correction : utiliser la table standard `mimetypes` pour les autres extensions, conserver les types historiques JS/CSS/HTML et le repli binaire pour une extension inconnue. Vert : **13 réussites**. XML : `/tmp/diff-4-b2008-rouge.xml` et `/tmp/diff-4-b2008-vert.xml`.

## Règles à trancher

### B-1897 : propriétaire d'une décision prise sans profil

La migration existante est appelée par `profileStorageIsolation.ts:28-35` avant le montage normal des écrans (`App.tsx:143-165`). Elle rattache l'ancienne file au profil précédent connu, ou au profil historique par défaut. Le test de migration cité dans le tableau passe. Cela ne définit pas le propriétaire d'une décision **nouvelle** prise alors que l'identité du profil est absente. `consentSync.ts:34-39` et `:53-67` montrent la différence entre les clés et le refus signalés dans le candidat ; ce parcours sans profil n'a pas été confirmé par un nouveau test rouge.

Question : faut-il refuser une nouvelle décision tant que le profil est inconnu, la conserver jusqu'à une attribution explicite, ou l'affecter automatiquement au prochain profil identifié ?

Recommandation : attendre l'identification du profil avant de recueillir la décision, avec un message de reprise explicite. Pour une file déjà orpheline, demander son attribution plutôt que deviner son propriétaire. Le rattachement automatique au prochain profil pourrait transférer un accord entre deux dossiers. Aucun changement de code ou de test en attendant cette règle.

### B-1898 : traitement des faux positifs sensibles

Les lignes `253-270` de `tests/test_c19d_b1088_securite_memoire.py` documentent expressément le report : cinq assouplissements lexicaux auraient rouvert les catégories protégées, et une confirmation humaine reste une proposition. Les **9 cas existants** de ce groupe passent ; ils comprennent les formulations professionnelles et les contre-exemples médicaux ou religieux. Leur réussite prouve le comportement actuel, pas sa qualité d'usage.

Question : conserver le refus conservateur, autoriser des exceptions lexicales, ou ajouter une confirmation spécifique pour une formulation professionnelle reconnue comme faux positif ?

Recommandation : définir une confirmation ciblée pour les formulations professionnelles, avec un corpus de contre-exemples conservé et des protections séparées pour les secrets. Ne pas ajouter une exception lexicale générale à « traitement », « diagnostic » ou « prie ». L'éligibilité exacte à cette confirmation et son effet sur le journal et les fiches doivent être décidés. Aucun changement en attendant cette règle.

## Preuves des rejets

- **B-2023** : `MemoryPanel.tsx:517-522` affiche le nombre de contacts dont le consentement expire bientôt, sous condition `expires_ou_bientot > 0`. Le mot ne promet aucune fonctionnalité future. Le contrat source existant est fragile comme technique de test, mais le défaut de libellé allégué n'est pas présent. Le test existant passe ; il n'est pas remplacé.
- **B-2024** : `workspace_tools.py:1684` contient déjà « événement(s) » et `:1689` « (journée) ». Les assertions actuelles de `test_b1110_agenda_local_recurrent.py:193` et `:337` exigent ces accents. Les **36 tests** du fichier passent, ainsi que le voisin `test_b1431_messages_agenda_accentues.py` (**1 test**). Le candidat cite un état antérieur au code de cet arbre.
- **B-2025** : `file_parser.py:95-101` constate l'absence de texte, présente le scan comme une possibilité et propose soit une version avec reconnaissance de texte, soit les pages converties en JPEG/PNG pour un modèle compatible. Le PDF n'est pas désigné comme un JPEG. Les **3 tests** du fichier cité passent.
- **B-2026** : `llm.py:557-559` précise « sauf demande explicite [...] ou consigne personnelle contraire », puis donne au courrier destiné à un tiers le registre demandé pour son destinataire. La coexistence avec la préférence de vouvoiement est donc voulue et cohérente. Les **2 cas** du test cité passent sans appel à un modèle.
- **B-2027** : `invoices.py:1296-1303` distingue la pièce émise immuable du brouillon. Pour la première, le message dit « Consulte le PDF d’origine si tu l’as conservé » ; pour la seconde, il demande de renseigner l'adresse dans le brouillon. Les **4 tests** du fichier cité passent, dont le refus de modifier les champs après émission. Un conseil de modification du brouillon serait incorrect pour le cas signalé.

## Portes finales

Les comptes pytest viennent de `/tmp/diff-4-pytest.xml`, relu intégralement par le parseur XML. Les comptes Vitest viennent de `/tmp/diff-4-vitest.json`, avec vérification de chaque fichier et de ses assertions.

| Porte | Réussis | Échoués / erreurs | Ignorés | Résultat |
| --- | ---: | ---: | ---: | --- |
| pytest ciblé | 82 | 0 / 0 | 0 | code 0 |
| Vitest ciblé, 5 fichiers | 20 | 0 / 0 | 0 | code 0 |
| Ruff, `src/backend tests` | sans objet | 0 diagnostic | sans objet | code 0 |
| TypeScript, `tsc --noEmit` | sans objet | 0 diagnostic | sans objet | code 0 |
| ESLint, `npm run lint` | sans objet | 0 erreur | sans objet | code 0 ; 27 avertissements dans des fichiers non modifiés |
| Syntaxe des trois scripts, `ast.parse` | 3 | 0 | 0 | code 0 |
| `git diff --check` | sans objet | 0 | sans objet | code 0 |

**Noms des échecs finaux : aucun.** Les neuf échecs rouges initiaux sont détaillés ci-dessus. Répartition pytest : B-1883 **4**, B-1885 **10**, B-2008 **13**, arbitrage B-1898 **9**, agenda récurrent **36**, accents agenda **1**, PDF sans texte **3**, tutoiement **2**, identité facture **4**. Les **27 nouveaux tests** sont tous verts.

Commande backend exécutée :

```sh
OLLAMA_BASE_URL=http://127.0.0.1:9 .venv/bin/python -m pytest tests/test_c20_b1883_finaliser_recette.py tests/test_c20_b1885_banc_ollama.py tests/test_c20_b2008_mime_recette.py tests/test_c19d_b1088_securite_memoire.py::test_faux_positifs_differes_et_contre_exemples_v5 tests/test_b1110_agenda_local_recurrent.py tests/test_b1431_messages_agenda_accentues.py tests/test_c22b_pdf_sans_texte.py tests/test_r1_10_tutoiement.py tests/test_c22b_identite_facture.py -q -p no:cacheprovider --timeout=120 --junitxml=/tmp/diff-4-pytest.xml
.venv/bin/python -m ruff check --no-fix src/backend tests
```

Commandes frontend exécutées depuis `src/frontend` :

```sh
npx vitest run src/lib/consentSync.test.ts src/lib/consentSync.profiles.test.ts src/lib/consentSync.demarrage.test.ts src/lib/profileStorageIsolation.test.ts src/test/c19d/B-1067.test.ts --maxWorkers=3 --configLoader=runner --no-cache --reporter=default --reporter=json --outputFile=/tmp/diff-4-vitest.json
npx tsc --noEmit
npm run lint
```

Le premier lancement Vitest standard s'est arrêté **avant toute collecte** : `EPERM` lors de l'écriture de son fichier temporaire dans le `node_modules` partagé. La reprise conserve la configuration du dépôt, avec `--configLoader=runner --no-cache` pour ne pas écrire dans ce lien. Aucun fichier du dépôt principal n'a été modifié. Cette erreur d'infrastructure initiale n'est pas comptée comme un test rouge de candidat.

Journaux des portes : `/tmp/diff-4-pytest.log`, `/tmp/diff-4-vitest.log`, `/tmp/diff-4-ruff.log`, `/tmp/diff-4-tsc.log` et `/tmp/diff-4-eslint.log`.

## Limites et remise à l'orchestrateur

Les modifications concernent uniquement des scripts de recette et leurs tests. Les simulations vérifient les codes de sortie, l'exploitation des journaux fictifs et les types MIME ; elles ne constituent ni un banc Ollama réel ni une inspection de captures navigateur. Aucun fournisseur, service en ligne, port réservé ou profil réel n'a été utilisé. `.app-loop/` n'a pas été consulté ni modifié. La suite complète n'a pas été lancée.

Restent à décider : B-1897 et B-1898. Restent à effectuer par l'orchestrateur : rejeu de chaque nouveau test sur la base sans correctif, commits distincts en français et portes complètes sur les deux machines. Le bandeau de co-auteur demandé devra terminer chaque message de commit : `Co-Authored-By: Codex <noreply@openai.com>`.

## Remédiation de la relecture, passe 1

Les trois P1 de la relecture sont confirmés. Cette passe ne modifie que `scripts/banc_ollama_r4.py`, `tests/test_c20_b1885_banc_ollama.py` et la présente section. Les autres candidats et scripts du lot restent hors périmètre. Changements laissés non commités, sans `git add`, dépôt annexe ou bundle.

### Rouges constatés avant chaque correctif

Chaque test ci-dessous a été ajouté puis lancé **seul**, avant son correctif. Chaque XML contient exactement **1 test, 1 échec, 0 erreur, 0 ignoré**, code de sortie 1. Les lignes reproduites sont celles des messages d'échec lus dans ces XML.

| Constat | Test dans `tests/test_c20_b1885_banc_ollama.py` | Ligne d'échec recopiée | XML |
| --- | --- | --- | --- |
| 1 : journal ancien sans nouvel octet | `test_journal_inchange_ne_valide_pas_la_passe` | `AssertionError: assert 0 == 1` | `/tmp/diff-4-r1-c1-rouge.xml` |
| 2 : copie, troncature puis repousse sur le même inode | `test_journal_tronque_puis_regrossi_ne_prouve_pas_la_continuite` | `assert True is False` | `/tmp/diff-4-r1-c2-rouge.xml` |
| 3 : substitution du fichier par un lien à l'ouverture | `test_journal_refuse_le_lien_substitue_a_l_ouverture[feuille]` | `AssertionError: assert ['Path.open'] == []` | `/tmp/diff-4-r1-c3-rouge.xml` |

Le troisième test a ensuite été étendu au relevé initial et aux répertoires parents : son cas rouge initial se nomme désormais `[lecture-feuille]`. Ses fichiers « hors périmètre » sont exclusivement des fichiers fictifs dans les temporaires de cet arbre ; aucune donnée extérieure réelle n'est utilisée. Le helper de test `position_journal` permet de rejouer les trois reproductions sur l'ancien lecteur qui recevait un simple `stat()`.

### Corrections et vérifications des appelants

1. **Preuve propre à chaque appel.** Un fichier inchangé ne valide plus sa lecture. Le véritable transport reçoit un identifiant unique `banc_r4` dans l'URL, sans changement du corps JSON ; son hook précédent est conservé puis restauré, y compris après erreur. Entre les bornes de chaque appel, le lecteur exige un reçu GIN 200 portant cet identifiant et une fin de génération. Le verdict exige aussi la preuve de **chaque** appel : une croissance sans rapport, une trace d'un autre appel ou un ancien résultat sans cette preuve restent rouges. Le contrat de journal reconnu est décrit dans l'en-tête du script. Un serveur qui ne produit pas ces traces laisse le banc rouge ; sa configuration n'a pas été modifiée et aucune compatibilité réelle de journal n'est revendiquée ici.
2. **Vérification du préfixe conservé.** Le relevé initial et les relevés par appel capturent l'empreinte SHA-256 de tout le contenu déjà présent, par blocs. Elle est comparée avant d'exploiter les nouveaux octets. Une copie suivie d'une troncature puis d'une repousse qui remplace ce préfixe est refusée même si l'inode reste identique et si la taille finale augmente. Les contrôles de taille, d'inode et de stabilité pendant la lecture restent actifs ; les dates de modification sont comparées à la nanoseconde, sans dépendre de la date d'accès. Les tests couvrent également une altération au milieu d'un préfixe de plusieurs blocs, ainsi qu'un journal initialement vide avec et sans ajout.
3. **Ouverture ancrée dans le worktree.** Le relevé et la lecture ouvrent chaque composant depuis un descripteur de répertoire avec `O_NOFOLLOW`, puis vérifient avec `fstat` l'identité et la nature du fichier effectivement ouvert. Les entrées sont revérifiées après lecture. Les liens, y compris dans un parent remplacé pendant l'ouverture, sont refusés. Les fichiers non ordinaires sont refusés sans blocage ; les descripteurs sont fermés même en cas d'erreur de lecture. Le test de course vérifie l'absence d'ouverture du fichier fictif extérieur, pas seulement l'absence de ses lignes dans le résultat.

Après chaque correctif, relecture des raccords `mesurer` → `observer` → `observer_flux_journal` → `lire_troncatures` → `enregistrer_verdict`, du véritable `_stream_request` et de ses consommateurs. `--evaluer` applique le même verdict conservateur aux résultats sauvegardés. `achever_recette_r4.py` propage toujours le code du banc. Aucun de ces appelants hors du script R4 n'a été modifié.

Les assertions existantes sont conservées. Le résultat fictif du test de verdict inclut désormais une preuve par appel afin de continuer à isoler le drapeau global et les troncatures. Les tests de lecture prennent leur position via le nouveau relevé, sans relâcher leurs résultats attendus. **23 cas supplémentaires**, tous verts, couvrent les trois constats et les régressions de leurs correctifs.

### Portes exécutées et XML lus

Les contrôles intermédiaires ont lancé les trois fichiers de tests du lot et le voisin `test_ollama_erreur_http.py` après chaque correction : **45/45**, **49/49**, puis **51/51** réussites, sans erreur ni test ignoré. XML lus : `/tmp/diff-4-r1-c1-vert.xml`, `/tmp/diff-4-r1-c2-vert.xml`, `/tmp/diff-4-r1-c3-vert.xml`.

Le rejeu final ajoute les tests de fermeture des ressources et le fichier voisin `test_r3_4_ollama.py`. Résultats nominatifs relus dans `/tmp/diff-4-r1.xml` :

| Fichier | Réussis | Échoués | Erreurs / ignorés |
| --- | ---: | ---: | ---: |
| `test_c20_b1885_banc_ollama.py` | 33 | 0 | 0 / 0 |
| `test_c20_b1883_finaliser_recette.py` | 4 | 0 | 0 / 0 |
| `test_c20_b2008_mime_recette.py` | 13 | 0 | 0 / 0 |
| `test_r3_4_ollama.py` | 6 | 4 connus | 0 / 0 |
| `test_ollama_erreur_http.py` | 8 | 0 | 0 / 0 |
| **Total** | **64** | **4 connus** | **0 / 0** |

Code pytest final : **1**, exclusivement pour `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[True-True]`, `[True-False]`, `[False-True]` et `[False-False]`, les quatre cas explicitement exclus par le mandat. **Aucun autre rouge** ; aucun de ces quatre cas n'a été modifié, ignoré ou marqué xfail.

Pour les lancements répétés, un lanceur de validation local a été créé sous `.pytest_cache/diff-4-r1/`, dossier ignoré par Git. Il exécute le module pytest, interdit les connexions et les binds par un audit Python, désactive le bytecode et place les données ainsi que les temporaires de tests dans cet arbre. Commande finale réellement exécutée :

```sh
OLLAMA_BASE_URL=http://127.0.0.1:9 .venv/bin/python -B .pytest_cache/diff-4-r1/pytest_hors_reseau.py tests/test_c20_b1885_banc_ollama.py tests/test_c20_b1883_finaliser_recette.py tests/test_c20_b2008_mime_recette.py tests/test_r3_4_ollama.py tests/test_ollama_erreur_http.py -q -p no:cacheprovider --timeout=120 --junitxml=/tmp/diff-4-r1.xml
.venv/bin/python -B -m ruff check --no-fix --no-cache src/backend tests
git diff --check
```

Ruff : **code 0, aucun diagnostic**. `git diff --check` : **code 0**. Aucun frontend modifié, donc aucune porte frontend lancée. Aucune suite complète, aucun réseau, aucun moteur réel, aucun port réservé ni profil utilisateur ; `.app-loop/` n'a pas été consulté ou modifié. Les échanges HTTP des nouveaux tests passent exclusivement par `httpx.MockTransport`.

**Verdict de remédiation ciblée : GO**, avec les quatre rouges connus ci-dessus. Les tests prouvent les refus et le parcours simulé ; ils ne constituent pas un banc Ollama réel. Le rejeu sans correctifs, les commits et les portes complètes restent à l'orchestrateur.

## Remédiation de la relecture, passe 2

Cette section remplace les conclusions de la passe 1 sur la continuité et la corrélation du journal. Les huit constats sont confirmés dans l'arbre effectivement livré. Aucun commit, `git add`, rebase, dépôt annexe ou bundle n'a été effectué. Les changements restent dans cet arbre ; les rapports de validation sont sous `/tmp`.

### Base réellement présente et récupération de l'intégration

Au début de cette passe, `HEAD=34d3566c`, `c20/integration=75498edd` et leur ancêtre commun est `e82f038a`. `git merge-base --is-ancestor c20/integration HEAD` retourne **1** : l'état local n'est donc pas celui annoncé comme rebasé. Quatre commits d'intégration manquent : `2dd3d2b1`, `9eb74c5d`, `fcf446a5`, `75498edd`. Le diff à trois points ne contient que les sept fichiers propres au lot ; les absences du diff entre les deux arbres ne prouvent pas des suppressions commises par diff-4.

Les permissions de cette session placent `.git` en lecture seule, et le mandat interdit les commits et l'indexation. Les contenus d'intégration ont donc été récupérés par lecture des objets Git, d'abord les tests, puis leurs correctifs, sans modifier l'historique. **24 fichiers sont identiques octet par octet à l'intégration initiale `75498edd`** : huit fichiers de production, treize fichiers de tests absents, deux fichiers de tests divergents et `docs/qualite/c20-migrations.md`. Cela rétablit également les protections associées aux tests manquants de provenance, de motifs sensibles et de sessions d'agent, sans inventer de nouvelle correction pour ces modules.

Pendant les validations, la référence partagée `c20/integration` a avancé à `31e3f98d` avec six commits du lot rust-windows. Leurs fichiers sont distincts des 24 restaurations ; ils restent hors des constats confiés à diff-4. La comparaison de cette passe est donc épinglée à `75498edd`, et le rebase final devra prendre en compte l'intégration courante.

Les treize fichiers restaurés restent non suivis dans l'index actuel, conformément au mandat. Un simple `git diff c20/integration` les affiche donc encore comme absents ; leur présence et leur contenu ont été vérifiés directement contre les objets de la référence. **L'ascendance Git reste divergente** : le rebase et les commits appartiennent encore à l'orchestrateur. Les liens `.venv` et `src/frontend/node_modules`, déjà non suivis à l'arrivée, sont conservés tels quels.

### Rouges obtenus avant correction

Chaque reproduction principale ci-dessous a été rétablie ou ajoutée puis exécutée seule avant son correctif. Les XML ont été lus : **un test exécuté, un échec, aucune erreur** pour chacun. Les lignes d'échec sont recopiées depuis ces rapports.

| Constat | Test | Ligne d'échec | Rapport `/tmp/` |
| --- | --- | --- | --- |
| 1 | `test_fin_d_une_autre_tache_ne_valide_pas_le_recu` | `assert True is False` | `diff-4-r2-c1-rouge.xml` |
| 2 | `test_rotation_copie_troncature_depuis_journal_vide` | `assert True is False` | `diff-4-r2-c2-rouge.xml` |
| 3 | `test_lien_physique_refuse_avant_toute_lecture[releve]` | `assert [29] == []` | `diff-4-r2-c3-rouge.xml` |
| 4 | `test_note_rattachee_preservee_si_evenement_sans_projet` | `AssertionError: assert None == 'projet-existant'` | `diff-4-r2-c4-rouge.xml` |
| 5, colonne absente | `test_migration_ajoute_contact_absent_sans_perte[standard]` | `KeyError: 'contact_id'` | `diff-4-r2-c5-contact-rouge.xml` |
| 5, reconstruction | `test_reconstruction_preserve_la_transaction_appelante` | `AssertionError: La transaction de l’appelant a été validée.` | `diff-4-r2-c5-transaction-rouge.xml` |
| 5, réparation | `test_reparation_preserve_la_transaction_appelante` | `AssertionError: La réparation a validé la transaction de l’appelant.` | `diff-4-r2-c5-reparation-rouge.xml` |
| 6 | `écarte le paiement pendant la question d’abandon et le rétablit ensuite` | `Error: expect(element).not.toBeInTheDocument()` | `diff-4-r2-c6-rouge.xml` |
| 7 | `test_limite_ne_presente_pas_la_cle_comme_acceptee` | `AssertionError: assert 'acceptée' not in 'Clé accepté...de requêtes.'` | `diff-4-r2-c7-rouge.xml` |
| 8 | `affiche le refus du moteur pendant la vérification de destination` | `Error: expect(element).toHaveTextContent()` | `diff-4-r2-c8-agent-rouge.xml` |

Pour le constat 6, le bouton trouvé à tort est « Marquer comme payée ». Pour le constat 8, le message attendu est « Le profil a changé. Reviens au profil concerné avant de réessayer. » ; le message reçu demande de vérifier la connexion au moteur.

Les dépendances récupérées pour le constat 8 ont aussi été reproduites avant restauration du code :

| Test exécuté seul | Ligne d'échec | Rapport `/tmp/` |
| --- | --- | --- |
| `test_reponse_sans_information_documentaire_reste_prudente[attribut-absent]` | `AssertionError: assert 'sans_document' == 'documents'` | `diff-4-r2-c8-provenance-rouge.xml` |
| `test_refus_ambigu_sans_attribution_inexacte`, cas politique de confidentialité | `AssertionError: assert 'opinion politique' not in 'Cette donné...n politique.'` | `diff-4-r2-c8-motifs-rouge.xml` |
| `test_cle_sans_espace_ne_cite_pas_un_autre_fournisseur` | `assert 'OpenAI' in "Ta clé Claude n'est rattachée à aucun espace de travail. Dans la Console Claude, crée une clé rattachée à un espace (par exemple « Default Workspace »)."` | `diff-4-r2-c8-espace-rouge.xml` |

Le rejeu complémentaire des trois autres fichiers AgentSession restaurés donne **4 échecs et 6 réussites** avant correction (`diff-4-r2-c8-autres-agents-rouge.xml`), dont l'attente remise dans le sens de l'intégration dans `AgentSession.accordMoteur.test.tsx`.

La relecture de l'appelant `--evaluer` a également révélé qu'un ancien résultat pouvait conserver ses booléens de preuve. Avant correction, `test_reevaluation_refuse_les_anciennes_preuves_non_capturees` échoue seul avec `AssertionError: assert 0 == 1` (`diff-4-r2-c2-reevaluation-rouge.xml`).

### Corrections, limites et appelants relus

1. **Fin corrélée.** La ligne de fin doit contenir `request="/api/chat?banc_r4=<identifiant>"` et le diagnostic `stop processing: … truncated = N`. Le reçu GIN 200 et la fin doivent chacun apparaître exactement une fois pour cet identifiant. Une fin anonyme, ou celle d'une autre requête avec le bon reçu, est refusée. Le nouveau test couvre ces deux variantes, y compris avec la capture par tube.
2. **Flux conservé.** `CaptureJournal` garde un descripteur du tube anonyme de sortie du serveur et accumule les octets en mémoire. Un thread draine le tube pendant le transport HTTP ; les relevés le drainent aussi pour éviter une dépendance à l'ordonnancement. Une rotation de copie ne peut effacer ces octets. Le lecteur de fichiers conserve ses usages diagnostiques, mais ne peut plus certifier un appel. Le test reproduit la copie-troncature depuis un fichier vide, avec changement de date ; un autre vérifie que l'alerte reste dans la capture quand sa copie sur disque est effacée. Les lignes incomplètes ne prouvent rien. `preuve_journal_v=2` empêche `--evaluer` de valider les anciens résultats non capturés.
3. **Aucun chemin de fichier pour la preuve.** Le tube anonyme n'a pas de chemin réouvrable dans l'arbre et son descripteur reste détenu jusqu'à la fin de la mesure. Les fichiers ordinaires et FIFO nommés sont refusés comme source de capture. Le lecteur diagnostique existant contrôle `st_nlink == 1` avant toute empreinte et après lecture ; le test espion vérifie qu'aucun contenu du lien physique fictif n'est lu. Les tests antérieurs de liens symboliques, substitutions, rotations et fermeture des descripteurs restent présents.
4. **Notes héritées.** Restauration exacte de `e.project_id IS NOT NULL`. La note conserve son dossier et n'est pas marquée migrée tant que le rendez-vous n'a pas de projet ; un rattachement ultérieur reste possible. Appelants relus : `apply_adhoc_migrations` et la migration Alembic `f2a3b4c5d6e7`.
5. **Activités.** Restauration exacte des accès protégés à `contact_id` et du refus de reconstruction/réparation pendant une transaction appelante. Le `commit()` prématuré est retiré. Relecture du chemin de démarrage et des branches de schéma enrichi, de réparation et de restauration des clés étrangères.
6. **Facture.** Restauration du masquage des actions, de la garde de soumission et du focus sur la question d'abandon. Récupération du filtrage des éléments masqués dans le piège de focus. Les deux assertions structurelles du pied sont conservées et vérifiées après « Continuer la saisie », conformément au test d'intégration. Relecture des gestionnaires de fermeture, soumission, paiement et conversion.
7. **HTTP 429.** Le message dit que la clé ne peut pas être vérifiée pour l'instant et propose de réessayer. Il ne prétend plus qu'elle est acceptée. Relecture de l'appel `verifier_cle` puis `message_verification` dans la route de configuration.
8. **Comparaison et tests d'intégration.** Les treize fichiers manquants et les deux tests divergents sont rétablis ; les corrections correspondantes sont identiques à l'intégration. Relecture des deux parcours d'accord d'AgentSession, de la persistance de provenance dans le chat et des appels à `message_refus` dans les fiches et le journal d'actions. Le présent bilan distingue la divergence de base des modifications propres au lot.

La chaîne `lancer` → `mesurer` → `observer_flux_journal` → `lire_troncatures` → `enregistrer_verdict`, le transport Ollama et `achever_recette_r4.py` ont été relus. Le lanceur transmet le descripteur hérité avec `--journal-fd` et `pass_fds`. **Un banc réel exige désormais un lanceur fournissant directement le tube de sortie du serveur et une instrumentation serveur corrélant ses fins.** Un journal Ollama natif dépourvu de cet identifiant n'est pas une preuve suffisante. `achever_recette_r4.py`, qui ne fournit pas ce descripteur, échoue explicitement avant le fournisseur ; il ne peut pas produire un faux vert. Aucun serveur ni fournisseur n'a été lancé ou modifié pendant cette passe, et aucune compatibilité réelle de ces traces n'est revendiquée.

**12 cas ajoutés** dans le test du banc, **20 cas restaurés** dans les treize fichiers d'intégration. Aucune assertion existante n'est supprimée. Les fixtures positives du banc portent maintenant la corrélation explicite et la version de preuve afin de continuer à tester le succès autorisé et les autres gardes indépendamment.

### Portes ciblées et environnement de validation

Les vérifications intermédiaires ont été relancées après les correctifs : banc et voisins **60/60**, puis **62 réussites et le nouveau rouge du constat 2**, puis **69/69** ; migrations d'activités et voisins **196/196** ; facture et focus **38/38** ; AgentSession **32/32**. Le premier rejeu des voisins de la facture a aussi signalé les deux tests de focus et les deux tests de pied à restaurer ensemble ; les quatre sont verts après récupération de l'intégration.

Le bac à sable bloque le réveil inter-thread d'un simple portail AnyIO, même sans l'application ni le garde réseau. Plusieurs essais HTTP ont été interrompus ; un diagnostic a aussi produit une erreur de préparation `no such table: invoice_lines`. Une reprise sur une base neuve avec une attente système bornée a fait passer le test HTTP de migration des notes. Le lanceur **local et ignoré par Git** `.pytest_cache/diff-4-r2/sitecustomize.py` interdit `socket.connect` et `socket.bind`, et borne `selectors.DefaultSelector.select()` à 1 ms. Aucun transport ASGI, accès SQLCipher ou test n'est remplacé par ce lanceur. Les essais interrompus et le diagnostic en erreur ne sont pas comptés comme portes réussies.

La porte finale utilise une nouvelle base dans `.pytest_cache/diff-4-r2/data-final`, le bytecode désactivé, `TMPDIR` dans cet arbre et `PYTHONPATH` pointant sur ce lanceur. Commande pytest :

```sh
OLLAMA_BASE_URL=http://127.0.0.1:9 .venv/bin/python -m pytest tests/test_c20_b1885_banc_ollama.py tests/test_c20_b1883_finaliser_recette.py tests/test_c20_b2008_mime_recette.py tests/test_r3_4_ollama.py tests/test_ollama_erreur_http.py tests/test_c20_b1888_transaction_activites.py tests/test_c20_b1889_notes_heritees.py tests/test_c20_b1890_activites_sans_contact.py tests/test_c20_b1891_reparation_transaction.py tests/test_activity_migration.py tests/test_b1153_migration_colonnes.py tests/test_b1140_migration_sans_verrou.py tests/test_b1153_rejeu_astra_v2.py tests/test_r5_9_notes.py tests/test_r5_6_journal.py tests/test_c20_b2010_limite_cle.py tests/test_b1348_verification_cle.py tests/test_c20_b1893_provenance_sans_marque.py tests/test_c20_b2009_motifs_ambigus.py tests/test_c20_b2011_cle_sans_espace.py tests/test_c19d_b1088_securite_memoire.py tests/test_t4_7_provenance.py -q -p no:cacheprovider --timeout=120 --junitxml=/tmp/diff-4-r2.xml
.venv/bin/python -B -m ruff check --no-fix --no-cache src/backend tests
```

Depuis `src/frontend`, npm est forcé hors ligne et son cache reste dans cet arbre. `--configLoader=runner --no-cache` évite les écritures dans le `node_modules` partagé :

```sh
npx --no-install vitest run src/components/atelier/AgentSession src/components/invoices/InvoiceForm src/hooks/useDialogFocusTrap --maxWorkers=3 --configLoader=runner --no-cache --reporter=default --reporter=junit --outputFile=/tmp/diff-4-r2-vitest.xml
npx --no-install tsc --noEmit
npm run lint
```

Les deux XML finaux ont été lus, cas par cas, et leurs totaux vérifiés :

| Porte | Réussis | Échecs / erreurs | Ignorés | Résultat |
| --- | ---: | ---: | ---: | --- |
| pytest ciblé, 22 fichiers | 606 | 4 connus / 0 | 0 | code 1 |
| Vitest ciblé, 60 fichiers | 207 | 0 / 0 | 0 | code 0 |
| Ruff, `src/backend tests` | sans objet | 0 diagnostic | sans objet | code 0 |
| TypeScript, `tsc --noEmit` | sans objet | 0 diagnostic | sans objet | code 0 |
| ESLint, `npm run lint` | sans objet | 0 erreur | sans objet | code 0 ; 27 avertissements existants |
| Syntaxe du banc et `git diff --check` | sans objet | 0 | sans objet | code 0 |

Les **610 cas pytest** se répartissent ainsi : trois fichiers du lot **62 réussites**, voisins Ollama **14 réussites et 4 échecs connus**, activités **196 réussites**, notes **12**, journal d'actions **22**, vérification des clés **22**, provenance **8**, sécurité des fiches **270**. Le fichier du banc compte **45 tests**, dont les **12 cas ajoutés** de cette passe.

Les seuls échecs finaux sont `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[True-True]`, `[True-False]`, `[False-True]` et `[False-False]`, explicitement exclus par le mandat. **Aucun autre rouge final** ; aucun de ces quatre cas n'a été modifié, ignoré ou marqué xfail. Les **20 cas des treize fichiers restaurés** passent également. Rapports : `/tmp/diff-4-r2.xml` et `/tmp/diff-4-r2-vitest.xml` ; journaux : `/tmp/diff-4-r2-pytest.log`, `/tmp/diff-4-r2-vitest.log`, `/tmp/diff-4-r2-ruff.log`, `/tmp/diff-4-r2-tsc.log`, `/tmp/diff-4-r2-eslint.log`.

Aucune suite complète, aucun réseau, aucun fournisseur réel, aucun port réservé, aucun accès à `~/.therese` ou `.app-loop/`. Les simulations HTTP utilisent exclusivement les transports en mémoire. L'historique et l'index restent inchangés ; l'orchestrateur conserve le rejeu sans correctifs, le rebase effectif et les commits.
