# Cycle 20, lot diff-4

**État courant, passe 6 :** B-1883 et B-2008 conservés, types MIME des polices et de WebP explicités ; B-2029 et B-1885 `regle_a_trancher`, **retirés du lot, reportés**. Le test `tests/test_b2029_couverture.py` est conservé par l'intégration et reste collecté ; il lance Node avec un import relatif au répertoire courant. La section « Remédiation de la relecture, passe 6 » fait foi. Les récits, comptes et demandes de réintégration/rebase des passes précédentes ci-dessous sont historiques.

Arbre `gpt-c20-diff-4`, branche `gpt/c20-diff-4`, HEAD de départ et d'arrivée `4dfc79d1`. Trois candidats confirmés et corrigés, deux règles à trancher, cinq candidats rejetés. Vérifications locales sur le code présent dans cet arbre.

La consigne particulière du bac à sable remplace les commits : aucun `git add`, commit, push, dépôt annexe ou bundle. Les trois scripts, leurs trois nouveaux fichiers de tests et ce rapport restent non commités. Aucun test existant n'a été modifié, affaibli ou supprimé.

## Verdicts, dans l'ordre demandé

La colonne « Rouge observé » remplace le commit rouge ; les messages viennent des XML JUnit lus après chaque exécution isolée. « Sans objet » signifie qu'aucune attente nouvelle n'a été imposée au code.

| Id | Verdict | Test (chemin::nom) | Rouge observé | Correctif |
| --- | --- | --- | --- | --- |
| B-1883 | `confirme` | `tests/test_c20_b1883_finaliser_recette.py::test_finalisation_conserve_echec_portes[1-0-1]` | `assert 0 == 1`, avec `SystemExit(0).code` | non commité |
| B-1885 | `regle_a_trancher` | Reproductions des constats 2, 3 et 4, exécutées puis retirées avec le candidat | Faux verts malgré fin étrangère retardée ou alerte consommée ; binaire du PATH appelant introuvable (preuves détaillées en passe 4) | retiré du lot, reporté |
| B-1897 | `regle_a_trancher` | `src/frontend/src/lib/consentSync.profiles.test.ts::reprend la file historique avant de purger les caches de A` | Sans objet : attribution d'une décision nouvelle sans profil non définie | aucun changement |
| B-1898 | `regle_a_trancher` | `tests/test_c19d_b1088_securite_memoire.py::test_faux_positifs_differes_et_contre_exemples_v5` | Sans objet : l'assouplissement est explicitement différé à un arbitrage | aucun changement |
| B-2008 | `confirme` | `tests/test_c20_b2008_mime_recette.py::test_ressources_statiques_ont_un_type_mime[police.woff2-font/woff2]` | `Expected: fulfill(body=b'ressource fictive', content_type='font/woff2')` ; `Actual: fulfill(body=b'ressource fictive', content_type='application/octet-stream')` | non commité |
| B-2023 | `rejete` | `src/frontend/src/test/c19d/B-1067.test.ts::B-1067 : contrat du libellé ou de la structure` | Sans objet : « bientôt » concerne une expiration | aucun changement |
| B-2024 | `rejete` | `tests/test_b1110_agenda_local_recurrent.py::test_dates_ics_creees_par_api_restent_lisibles` ; `test_ancienne_serie_dense_signalee_et_rendez_vous_independant_rendu` | Sans objet : accents déjà présents | aucun changement |
| B-2025 | `rejete` | `tests/test_c22b_pdf_sans_texte.py::test_scan_avertit_le_chat` | Sans objet : JPEG est une solution alternative proposée | aucun changement |
| B-2026 | `rejete` | `tests/test_r1_10_tutoiement.py::test_tutoiement_par_defaut_et_consigne_personnelle_conservee` | Sans objet : les deux registres ont des périmètres distincts | aucun changement |
| B-2027 | `rejete` | `tests/test_c22b_identite_facture.py::test_piece_deja_emise_sans_adresse_ne_propose_pas_de_modifier_le_brouillon` | Sans objet : une pièce émise n'est plus un brouillon modifiable | aucun changement |
| B-2029 | `regle_a_trancher` | Deux reproductions isolées de la passe 5, retirées avec le candidat | `Error: Cannot find package '@playwright/test'` ; `ERR_MODULE_NOT_FOUND` depuis `/tmp` | retiré du lot, reporté |

B-1885 : **retiré du lot, reporté**. Preuve de la relecture : « Une fin de tâche étrangère peut valider l'appel suivi et produire un faux vert » ; « Un tube fourni par `--journal-fd` peut perdre une alerte tout en certifiant un verdict vert » ; « Le lanceur peut ne pas trouver un binaire Ollama pourtant installé et accessible à l'appelant ». Les trois reproductions isolées de la passe 4 confirment ces constats.

B-2029 : **retiré du lot, reporté**. Preuve de la relecture : « Le nouveau test fait échouer la CI backend sur une installation propre ». Le constat complet et les preuves du retrait figurent en passe 5.

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
## Remédiation de la relecture, passe 3

Les douze constats correspondent au code trouvé au début de cette passe. Les correctifs et les tests restent non commités, sans indexation. Les validations ci-dessous remplacent les comptes des passes précédentes. Aucun réseau, fournisseur, serveur de recette ou navigateur réel n'a été lancé. Les ports réservés, le profil réel et `.app-loop/` n'ont pas été utilisés.

### Référence et limite du constat 5

Contrairement au préambule du mandat, le départ est toujours `HEAD=fde4cf36`, avec `c20/integration=a498d9d3` et un ancêtre commun `31e3f98d`. L'index est vide de changements ; les seuls éléments non suivis au départ sont les liens de dépendances `.venv` et `src/frontend/node_modules`.

Les **24 fichiers** apportés par `31e3f98d..a498d9d3` sont rétablis dans les fichiers de travail, d'abord leurs tests puis leurs correctifs. Leur contenu est vérifié octet par octet contre `a498d9d3`, y compris les onze fichiers de tests ou de harnais absents et `docs/qualite/c20-bancs.md`. Les correctifs propres à diff-4 ne sont pas écrasés par l'ancienne version de ses trois scripts présente sur cette intégration. Le test de reconnexion avec ouverture retardée du navigateur reproduit aussi le défaut avant restauration de son scénario parent.

**Le rebase de l'historique n'est pas effectué.** `.git` est en lecture seule dans les permissions de cette session et le mandat interdit les commits et `git add`. Aucun faux état d'ascendance n'est annoncé : `HEAD` reste `fde4cf36`. Le constat 5 est traité pour les contenus de l'intégration de départ, mais reste ouvert pour l'historique.

Pendant les portes, `c20/integration` avance à **`c127023a`** (quatre commits du lot instrument, depuis `428c385b`). Ces commits touchent trois fichiers : les deux fichiers de couverture écran et `docs/qualite/c20-instrument.md`. Ils introduisent l'acquittement simulé du POST de migration, alors que le constat 3 de ce mandat demande son autorisation limitée et que `test_b2029_couverture.py` exige sa transmission à la pile jetable. Le nouveau test d'intégration exige au contraire `requeteAutorisee('POST', MIGRATION_CHAT) === false`. Ces contrats incompatibles n'ont pas été conciliés en affaiblissant un test. Les portes de cette passe portent donc sur **`fde4cf36` + les 24 contenus de `a498d9d3` + ces remédiations**, et non sur `c127023a`. Le rebase final et cette divergence appartiennent à l'orchestrateur.

### Rouges obtenus avant les correctifs

Les neuf reproductions Python ont chacune été exécutées seules : **1 test, 1 échec, 0 erreur, 0 ignoré** dans chaque XML. Les constats 5 et 6 ont aussi une seule assertion de test exécutée en rouge sous Vitest (l'autre test du fichier 6 est hors sélection). Le constat 10 nécessite les deux tests successifs de fin de sauvegarde : son fichier isolé a **1 échec, 2 réussites et 1 rejet non intercepté**, ce dernier visible dans le journal Vitest mais pas comptabilisé comme erreur dans son XML. Les rapports ont été lus.

| Constat | Reproduction principale | Ligne d'échec recopiée | Rapport sous `/tmp/` |
| --- | --- | --- | --- |
| 1 | `test_alerte_reste_rouge_meme_avec_compteur_zero` | `AssertionError: assert 0 == 1` | `diff-4-r3-c1-rouge.xml` |
| 2 | `test_achever_recette_va_jusqu_au_verdict_avec_les_traces_natives` | `ValueError: Preuve serveur requise : fournir le tube via --journal-fd.` | `diff-4-r3-c2-rouge.xml` |
| 3 | `test_garde_autorise_uniquement_la_migration_locale_du_chat` | `At index 0 diff: 'bloquee' != 'continue'` | `diff-4-r3-c3-rouge.xml` |
| 4 | `test_observation_attend_les_deux_traces_apres_le_flux[complete]` | `AssertionError: assert False is ('complete' == 'complete'` | `diff-4-r3-c4-rouge.xml` |
| 5 | `CalendarPanel.reconnexion.chargement.test.tsx` : scénario de reconnexion | `AssertionError: expected 1 to be greater than 1` | `diff-4-r3-c5-rouge.xml` |
| 6 | `b1854-garde-parcours.test.ts` : `refuse les mutations sur les routes bouchonnées` | `expected { status: 200, …(2) } to match object { status: 405 } (2 matching properties omitted from actual)` | `diff-4-r3-c6-rouge.xml` |
| 7 | `test_preuve_refuse_les_evenements_manquants_ou_non_surs[aucun_evenement-openrouter]` | `Failed: DID NOT RAISE <class 'AssertionError'>` | `diff-4-r3-c7-rouge.xml` |
| 8 | `test_preuve_echoue_si_le_chat_annonce_le_fournisseur_choisi` | `Failed: DID NOT RAISE <class 'AssertionError'>` | `diff-4-r3-c8-rouge.xml` |
| 9 | `test_refus_existant_avec_grande_fenetre[True-True]` | `assert not [{'messages': [{'content': "## Langue de tes réponses\nRéponds TOUJOURS en français, quelle que soit la langue du cont...erate_document', 'parameters': {'properties': {...}, 'required': [...], 'type': 'object'}}, 'type': 'function'}, ...]}]` | `diff-4-r3-c9-rouge.xml` |
| 10 | `chatPersistence.fin.test.ts` : `aucune sauvegarde du test précédent ne part après son démontage` | `AssertionError: expected "vi.fn()" to not be called at all, but actually been called 1 times` | `diff-4-r3-c10-rouge.xml` et `.log` |
| 11 | `test_scenario_action_attend_le_commit_durable` | `AssertionError: assert 'running' == 'done'` | `diff-4-r3-c11-rouge.xml` |
| 12 | `test_amorcage_avec_interpreteur_dans_un_chemin_a_espaces` | `AssertionError: assert '' == 'document-factice'` | `diff-4-r3-c12-rouge.xml` |

Le deuxième défaut du constat 10 produit aussi `TypeError: Cannot read properties of undefined (reading 'dispatchEvent')`. Après extension des contre-exemples, le test 2 est paramétré (le témoin nominal est `[aucun]`) et le test 4 distingue le format corrélé et le format natif (`[complete-False]` et `[complete-True]`).

### Corrections et relecture des appelants

1. **Alerte et compteurs indépendants.** Le verdict retire uniquement les diagnostics de compteur nul avant de chercher une troncature. L'alerte corrélée `stop processing: truncating input prompt; truncated = 0`, accompagnée de son reçu GIN, reste rouge. Un autre test couvre deux compteurs sur une même ligne, dont un positif. `--evaluer`, `mesurer_capture` et les verdicts précédents restent exercés.
2. **Chaîne R4 raccordée.** L'appel existant d'`achever_recette_r4.py` fonctionne sans descripteur fourni : `lancer` démarre le binaire Ollama, capture stdout/stderr dans un tube anonyme et transmet sa lecture à l'enfant. Le serveur dédié doit annoncer son écoute sous dix secondes ; une adresse déjà occupée échoue avant la mesure. Il utilise les modèles locaux de `.recette-r4/models`, un seul appel simultané et un seul modèle chargé. Le groupe de processus créé est arrêté à la sortie, avec attente bornée. Dans cette capture détenue par le lanceur, une seule fin native de slot et un seul reçu GIN 200 avec l'identifiant de l'appel sont exigés. Une autre requête, deux fins ou une trace manquante refusent la preuve. Un tube externe conserve l'exigence du préfixe corrélé : l'ancien test de fin anonyme étrangère reste strict. Le test part du véritable script `achever_recette_r4.py`, traverse `lancer`, `mesurer`, le transport Ollama sur `httpx.MockTransport`, puis écrit le verdict et le code de retour de l'appelant. Les portes, le processus serveur et la charge ASGI de recette sont simulés ; aucun Ollama n'est exécuté. Les sept variantes incluent l'alerte avec compteur nul, les traces étrangères ou absentes et le port occupé.
3. **Sauvegarde du chat jetable.** Restauration du POST exact `/api/chat/cache-migration` sur l'origine du backend jetable, sans paramètres. Les variantes d'origine, de méthode et de query restent refusées. Les tests exercent le gestionnaire de route en mémoire, sans connexion aux adresses représentées. L'attestation de pile dans `principal` reste antérieure à l'installation de la garde.
4. **Traces différées.** Après le flux, attente asynchrone des deux traces pendant au plus deux secondes ; absence persistante, erreur de capture ou preuve ambiguë restent rouges. Les hooks HTTP précédents sont restaurés avant l'attente. Huit cas couvrent les deux formats de journal, une preuve complète différée, une seule trace et le silence. Les tests voisins de capture, de rotation, de liens et d'échec du transport restent verts.
5. **Contenus d'intégration.** Voir la limite d'historique et de référence ci-dessus. Le scénario CalendarPanel attend un premier sondage effectivement observé au lieu de supposer que l'ouverture différée du navigateur a terminé. Son contre-test restauré et son voisin passent.
6. **Harnais du parcours 08.** Le contrôle de méthode précède les bouchons de lecture ; les mutations reçoivent 405. Le POST du calcul pur rejoint le moteur, et le scénario vérifie de nouveau les résultats 20 % puis 50 %. La génération d'image fictive reste limitée au seul scénario qui l'exerce. Les deux contre-épreuves de garde sont restaurées ; les 29 tests des routes et du service de calcul sont aussi verts.
7. **Frontière d'erreur.** Restauration de l'exigence d'au moins un événement d'erreur et de la recherche récursive dans tous les champs de tous les événements. Les six contre-épreuves réintroduisent l'absence d'événement et les fuites dans un texte ou un appel d'outil, pour les deux fournisseurs. Le fichier de frontière complet passe.
8. **Attribution effective.** Restauration de `_attribution(service) == ('openai', 'gpt-4.1')` et du double local de `_provider_pour`, qui empêche le scénario de contacter un fournisseur. Les contre-épreuves du mauvais fournisseur annoncé, des réponses HTTP/SSE et du badge sont restaurées. Les fichiers voisins du chat et de MessageBubble passent.
9. **Charge supérieure à la fenêtre.** Restauration des 60 000 répétitions d'identité et des quatre cas avec plafond de 131 072 jetons. Les dix tests R3-4 et les quatre contre-épreuves passent, y compris les quatre rouges connus cités dans le mandat.
10. **Fin des sauvegardes.** Restauration de l'annulation commune des écritures, sans oublier les stores persistants, et du garde `typeof window !== 'undefined'` avant l'événement d'erreur. Les trois tests de fin, les cinq tests R2 de persistance et les quatre tests du stockage différé passent ; aucun rejet non intercepté dans la porte finale.
11. **Clôture durable de l'action.** Restauration de l'attente bornée du producteur, puis du nettoyage de ses seules tâches de clôture, y compris les fermetures protégées. Relecture de `ActionRunner._execute` et `TraitementHandle.terminer` : la clôture durable arrive bien après le statut mémoire et utilise `asyncio.shield`. Les sept contre-épreuves couvrent le commit retardé, le producteur bloqué, le nombre inattendu de producteurs et les différents moments d'annulation ; les huit tests voisins d'actions passent.
12. **Interpréteur avec espaces.** Restauration du lanceur `/bin/sh` et de `shlex.quote` pour Python et le fichier du faux curl. Le contre-test crée un lien vers l'interpréteur dont le nom contient des espaces. Ce test et les trois tests de recette .deb passent.

### Portes sur les fichiers résultants

| Porte | Réussis | Échecs / erreurs | Ignorés | Preuve |
| --- | ---: | ---: | ---: | --- |
| pytest ciblé, 15 fichiers | 168 | 0 / 0 | 0 | `/tmp/diff-4-r3.xml`, XML lu |
| pytest voisin calculateur, 2 fichiers | 29 | 0 / 0 | 0 | `/tmp/diff-4-r3-calculateurs.xml`, XML lu |
| Vitest ciblé, 9 fichiers | 47 | 0 / 0 | 0 | `/tmp/diff-4-r3-vitest.xml`, XML lu |
| Node, garde et voisins sans navigateur | 5 | 0 / 0 | 0 | `/tmp/diff-4-r3-c3-node-vert.log`, TAP lu |
| Ruff `src/backend tests` | sans objet | 0 diagnostic | sans objet | `/tmp/diff-4-r3-ruff.log`, code 0 |
| TypeScript `tsc --noEmit` | sans objet | 0 diagnostic | sans objet | `/tmp/diff-4-r3-tsc.log`, code 0 |
| ESLint `npm run lint` | sans objet | 0 erreur | sans objet | `/tmp/diff-4-r3-eslint.log`, code 0 ; 27 avertissements existants |

**197 tests Python distincts et 47 tests frontend passent. Aucun rouge connu n'a dû être soustrait aux comptes.** Les deux sessions Python finales indiquent chacune `Connexions interdites tentées : 0`. Les fichiers des anciens correctifs B-1883 et B-2008 sont inclus parmi les voisins du banc. Pas de suite complète.

Commande principale, depuis cet arbre :

```sh
PYTHONPATH=/tmp NODE_OPTIONS=--import=file:///tmp/diff-4-r3-node-register.mjs \
OLLAMA_BASE_URL=http://127.0.0.1:9 .venv/bin/python -m pytest \
  tests/test_c20_b1883_finaliser_recette.py tests/test_c20_b1885_banc_ollama.py \
  tests/test_c20_b2008_mime_recette.py tests/test_b1806_banc_ollama.py \
  tests/test_r3_4_ollama.py tests/test_b1807_recette_deb.py \
  tests/test_securite_f2_recette_deb.py tests/test_b1851_preuve_frontiere.py \
  tests/test_frontiere_erreurs.py tests/test_b1852_preuve_attribution.py \
  tests/test_pluriel_fournisseur.py tests/test_r2_3_outil.py \
  tests/test_b2029_couverture.py tests/test_b2033_charges.py tests/test_actions_traitement.py \
  -q -p no:cacheprovider -p diff4_ipc -p tests.bancs_sans_reseau \
  --timeout=120 --junitxml=/tmp/diff-4-r3.xml
```

La commande des calculateurs conserve les mêmes options Python et ajoute seulement leurs deux fichiers, avec un XML distinct. Ruff a été lancé sans correction automatique. La commande frontend sélectionne les neuf fichiers `b1854-garde-parcours.test.ts`, `chatPersistence.fin.test.ts`, `chatPersistence.r2.test.ts`, `debouncedStorage.test.ts`, `MessageBubble.b1970.test.tsx`, `MessageBubble.test.tsx`, `MessageBubble.ollamaCloud.b1156.test.tsx` et les deux scénarios de reconnexion CalendarPanel, avec `--maxWorkers=3 --configLoader=runner --no-cache`. Puis `npx tsc --noEmit` et `npm run lint`, avec `npm_config_offline=true`.

### Adaptations locales et portée des preuves

Le bac à sable empêche le réveil inter-thread d'asyncio par socket interne : les premières tentatives ASGI restent bloquées avant le corps du test, dans `TestClient.__enter__`. Elles ont été interrompues, sans être présentées comme des rouges métier. Le diagnostic borné est conservé dans `/tmp/diff-4-r3-diagnostic-client.log`. Le plugin temporaire `/tmp/diff4_ipc.py` remplace uniquement ce canal de réveil par un tube anonyme non bloquant ; il ne modifie ni les assertions ni le backend. Le plugin restauré `tests.bancs_sans_reseau` interdit toute tentative de connexion.

Playwright était absent des dépendances Node de la racine. Les premières reproductions en mémoire ont utilisé un module inerte sous `/tmp`, qui refuse tout lancement de navigateur, et une configuration Vitest dérivée de celle du dépôt avec cette seule résolution supplémentaire. Les trois archives `@playwright/test`, `playwright` et `playwright-core` en version 1.58.2 ont ensuite été restaurées **hors réseau** dans le `node_modules` ignoré de cet arbre depuis le cache local, après vérification SHA-512 contre `package-lock.json`. Aucun manifeste ni verrou n'a changé. La garde Python (1 test), ses voisins Node (4 tests) et les deux contre-épreuves Vitest ont été rejoués avec ces dépendances réelles et la configuration habituelle ; XML supplémentaires lus : `diff-4-r3-c3-dependances-reelles.xml` et `diff-4-r3-c6-dependances-reelles.xml`. Ces rejeux ne gonflent pas les comptes distincts du tableau. La porte TypeScript finale utilise les vrais types Playwright.

Les tests Node sélectionnés ne lancent ni navigateur ni requête réseau. La suite navigateur et les parcours CLI qui écrivent dans `/private/tmp` ou déplacent vers la corbeille personnelle ne sont pas lancés dans cette passe. Le voisin CLI qui refuse une URL invalide a d'abord échoué parce que les canaux internes de son sous-processus Node ne rendaient pas son diagnostic dans ce bac à sable. Le module temporaire `/tmp/diff4_node_stdio.mjs` redirige seulement stdout/stderr de `spawnSync` vers des fichiers sous `/tmp`, puis les restitue au test. Le vrai enfant Node et toutes les assertions restent exercés. Le rejeu des cinq tests avec `node --import /tmp/diff4_node_stdio.mjs --test-name-pattern='^(la CLI|la base|la garde|les gestes|B-1715)' tests/couverture/couverture-ecran.test.mjs` passe. Aucun test n'a été affaibli pour contourner ces limites.

La chaîne Ollama est vérifiée avec des processus et réponses fictifs. Son usage réel demande le binaire local, la copie du modèle fourni dans `.recette-r4/models`, son nom dans `MODELE.txt` et le port de banc libre ; il n'a pas été exécuté pendant cette passe. Les portes ciblées sont vertes, mais **le constat 5 reste ouvert pour le rebase et la divergence de l'intégration arrivée en cours de travail** : ce rapport ne prononce pas de GO global.

## Remédiation de la relecture, passe 4

Cette passe part de l'arbre rebasé fourni par l'orchestrateur. Seuls les deltas du lot relatifs aux quatre constats et ce bilan sont modifiés. Les anciennes demandes de réintégration ou de rebase, ainsi que les fichiers d'autres lots remis par l'orchestrateur, sont écartés. Aucun fichier n'a été recopié depuis l'intégration ou un autre lot ; aucun rebase, commit, `git add`, dépôt annexe ou bundle.

| Constat | Choix | Verdict du candidat | Traitement |
| --- | --- | --- | --- |
| 1, B-2029 | **(a)** | `confirme` | Simulation de l'URL exacte conservée ; les POST de migration sont exclus de `requeteAutorisee`, y compris la variante `?` vide. Test Python adapté à `fulfill` et étendu ; assertion Node du lot corrigée et étendue. |
| 2, B-1885 | **(b)** | `regle_a_trancher` | Retrait complet du candidat après reproduction de la fin étrangère et des traces retardées. |
| 3, B-1885 | **(b)** | `regle_a_trancher` | Retrait du même candidat après reproduction de l'alerte consommée par le lecteur initial du tube. |
| 4, B-1885 | **(b)** | `regle_a_trancher` | Retrait du même candidat, lanceur compris, après reproduction du binaire accessible au seul PATH appelant. |

Constats 2, 3 et 4 : **retiré du lot, reporté**. Les preuves sont les trois constats du relecteur reproduits ci-dessous. Le constat 2 exige de maîtriser l'accès au serveur ou de corréler réellement les fins natives à leurs requêtes. Ni `OLLAMA_NUM_PARALLEL=1` ni l'attente de la première paire fin/reçu ne prouvent cette propriété. Le constat 3 exige également une maîtrise exclusive du lecteur, que `os.dup` ne procure pas. Aucun correctif simple et prouvé de ces deux courses n'est retenu ; le candidat entier est retiré suivant la règle de cette passe. Le lanceur du constat 4 appartient à ce même candidat et est donc retiré aussi. Ces défauts restent reportés au cycle suivant.

### Tests rouges écrits avant correction ou retrait

Chaque test ci-dessous a été écrit ou étendu avant toute modification du code concerné, puis lancé **seul** avec `--timeout=120`. Chaque XML a été lu : **1 test, 1 échec, 0 erreur, 0 ignoré** par constat. Aucun fournisseur réel ni requête réseau dans ces reproductions.

| Constat | Test isolé | Ligne d'échec recopiée | XML lu |
| --- | --- | --- | --- |
| 1 | `tests/test_b2029_couverture.py::test_garde_simule_la_migration_exacte_et_bloque_les_variantes` | `At index 1 diff: 'continue' != 'bloquee'` | `/tmp/diff-4-r4-c1-rouge.xml` |
| 2 | `tests/test_c20_b1885_banc_ollama.py::test_fin_etrangere_avant_les_traces_retardees_ne_certifie_pas` | `AssertionError: Une fin étrangère et un reçu anticipé ont certifié le verdict` ; `assert 0 == 1` | `/tmp/diff-4-r4-c2-rouge.xml` |
| 3 | `tests/test_c20_b1885_banc_ollama.py::test_tube_externe_avec_autre_lecteur_ne_certifie_pas` | `AssertionError: assert 0 == 1` | `/tmp/diff-4-r4-c3-rouge.xml` |
| 4 | `tests/test_c20_b1885_banc_ollama.py::test_lanceur_resout_ollama_dans_le_path_de_l_appelant` | `AssertionError: Binaire du PATH appelant perdu après isolation` | `/tmp/diff-4-r4-c4-rouge.xml` |

1. Le test B-2029 appelle le vrai gestionnaire enregistré par `installerGardeReseau` avec des routes en mémoire. Il vérifie la réponse `fulfill` exacte (200, JSON `{success: true}`), son comptage unique, puis huit refus, dont `?`, `?autre=1`, `#` et `/`. Avant correction, l'entrée `?` atteint `continue`. Après correction, ce test passe seul : `/tmp/diff-4-r4-c1-vert.xml`, **1 réussite**, XML lu.
2. Le transport HTTP en mémoire émet la fin native étrangère `task 99, truncated = 0`, puis le reçu GIN de la requête suivie. Une tâche suspendue par `asyncio.Event` émet ensuite la vraie fin `task 77, truncated = 9` et le reçu étranger, après l'écriture du verdict. Le test constate la présence finale de `truncated = 9`, mais le verdict a déjà renvoyé **0** et enregistré le vert. L'ordonnancement est déterministe, sans dépendre d'un délai arbitraire.
3. Le détenteur initial lit `truncating input prompt` dans le tube pendant que le collecteur est suspendu par son verrou. Le collecteur ne reçoit ensuite que la fin préfixée par l'identifiant de requête et le reçu GIN correspondant. L'alerte est absente de la capture et `enregistrer_verdict` renvoie pourtant **0**. Le tube et les deux lecteurs restent exclusivement dans le test.
4. Un exécutable inerte est créé sous le répertoire temporaire `opt/homebrew/bin`, seul répertoire du PATH appelant. `shutil.which('ollama')` le trouve avant le lancement. La résolution avec le PATH réellement passé à `Popen` renvoie **None**. Le contrôle précède tout lancement et n'autorise que le faux exécutable du test ; aucun Ollama réel n'est démarré.

Les trois nouveaux tests B-1885 et les anciens tests de ce candidat sont retirés ensemble, conformément au choix **(b)**. Ils ne sont pas présentés comme des tests verts et ne restent pas dans le lot. Aucun test de l'intégration n'est supprimé ou affaibli.

### Changements retenus et appelants relus

Pour le constat 1, le changement fonctionnel se limite à retirer la migration de la liste des POST transmis par `requeteAutorisee`. `requeteASimuler` et l'acquittement installé par `installerGardeReseau` restent ceux de l'intégration. Les deux tests B-2029 existants et leurs assertions sont conservés ; le test Python du lot exige désormais la simulation, et le test Node du lot refuse explicitement la transmission avec ou sans `?`. Relecture de `requeteASimuler` → `installerGardeReseau` → installation dans le parcours, puis des chemins `continue`, `abort`, comptage et attente des acquittements.

Pour les constats 2 à 4, inversion du seul patch B-1885 avec `git diff c20/integration -- scripts/banc_ollama_r4.py tests/test_c20_b1885_banc_ollama.py | git apply --reverse`. Aucun fichier entier n'est récupéré depuis une autre référence. Le contrôle `git diff --exit-code c20/integration -- scripts/banc_ollama_r4.py tests/test_c20_b1885_banc_ollama.py` est vide et retourne **0** : le script est à l'état de l'intégration, et le fichier de tests propre à B-1885 est absent comme dans l'intégration. Relecture de `achever_recette_r4.py:70`, de `lancer` → `mesurer` → `enregistrer_verdict` et de `--evaluer` ; aucun appelant hors lot n'est modifié. Ce retrait ne revendique aucune résolution du défaut initial B-1885.

### Portes ciblées et preuves lues

| Porte | Réussis | Échecs / erreurs / ignorés | Preuve |
| --- | ---: | ---: | --- |
| pytest, cinq fichiers du lot et voisins | **32** | **0 / 0 / 0** | `/tmp/diff-4-r4.xml`, XML lu |
| Node, garde et voisins sans navigateur | **10** | **0 / 0 / 0** | `/tmp/diff-4-r4-node.log`, TAP lu |
| Ruff `src/backend tests` | sans objet | **0 diagnostic** | `/tmp/diff-4-r4-ruff.log`, code 0 |

Répartition Python : B-2029 **1**, B-1806 **4**, R3-4 Ollama **10**, B-1883 **4**, B-2008 **13**. Aucun rouge connu à soustraire. Le premier rejeu Node après correction comptait six réussites ; le rejeu final à dix ajoute la CLI et les trois scénarios d'acquittements concurrents, sans additionner ces rejeux aux comptes distincts.

```sh
THERESE_DATA_DIR="$(mktemp -d /tmp/diff-4-r4-data-XXXXXX)" \
PYTHONPATH=/tmp PYTHONDONTWRITEBYTECODE=1 OLLAMA_BASE_URL=http://127.0.0.1:9 \
.venv/bin/python -m pytest \
  tests/test_b2029_couverture.py tests/test_b1806_banc_ollama.py \
  tests/test_r3_4_ollama.py tests/test_c20_b1883_finaliser_recette.py \
  tests/test_c20_b2008_mime_recette.py \
  -q -p no:cacheprovider -p diff4_ipc -p tests.bancs_sans_reseau \
  --timeout=120 --junitxml=/tmp/diff-4-r4.xml
node --import /tmp/diff4_node_stdio.mjs \
  --test-name-pattern='^(B-2029 : (seule la migration exacte|la garde acquitte)|B-2029 remédiation|B-2029 passe 2|la CLI|la base|la garde|les gestes|B-1715)' \
  tests/couverture/couverture-ecran.test.mjs
.venv/bin/python -m ruff check --no-fix src/backend tests
git diff --check
```

Les deux adaptations temporaires de la passe 3 ont été relues et réutilisées : `/tmp/diff4_ipc.py` remplace seulement le réveil interne asyncio par un tube ; `/tmp/diff4_node_stdio.mjs` restitue stdout/stderr des vrais sous-processus Node depuis des fichiers temporaires. Elles ne modifient aucune assertion. Le plugin `tests.bancs_sans_reseau` indique **0 tentative de connexion** pour chaque session Python. Les cas Node retenus utilisent des doubles en mémoire ; les parcours qui ouvrent un navigateur ou manipulent `/private/tmp` et la corbeille personnelle ne sont pas exécutés.

Aucun fichier sous `src/frontend` modifié : portes Vitest/TypeScript/ESLint non applicables à cette passe. Aucune suite complète, aucun réseau, aucun fournisseur réel, aucun accès aux ports réservés, à `~/.therese` ou à `.app-loop/`. Les liens non suivis `.venv` et `src/frontend/node_modules`, présents à l'arrivée, sont conservés. Les changements de cette passe restent non commités pour le rejeu et le commit de l'orchestrateur.

## Remédiation de la relecture, passe 5

Départ : `HEAD=1f058430`, `c20/integration=1550627b`, ascendance vérifiée. La consigne de dernière passe prime : retrait intégral du candidat P1 ; seul le P2 résolu par une ligne évidente est corrigé. Les anciens constats demandant une réintégration ou un rebase sont écartés. Aucun fichier d'un autre lot n'est modifié, aucun fichier entier n'est recopié depuis une autre référence.

| Constat | Verdict du candidat | Traitement de cette passe |
| --- | --- | --- |
| 1, P1, B-2029 : dépendance Node dans la CI Python | `regle_a_trancher` | Retrait des deltas B-2029 propres au lot : commentaire, assertions Node et candidat Python. Le test Python présent dans l'arbre rebasé est celui de l'intégration. Aucun nouveau correctif P1. |
| 2, P2, B-2008 : polices sans table MIME système | `confirme` | Une seule ligne de production : ajout explicite de `.woff: font/woff` et `.woff2: font/woff2` au dictionnaire existant. Deux cas de test ajoutés. |
| 3, P2, B-2029 : dépendance au répertoire courant | `regle_a_trancher` | Reproduction depuis `/tmp` retirée avec le candidat du lot ; le test Python conservé par l'intégration garde son import relatif au répertoire courant. |

B-2029 : **retiré du lot, reporté**. Constat P1 du relecteur recopié comme preuve :

> Le nouveau test fait échouer la CI backend sur une installation propre - Les jobs Python Linux et Windows sélectionnent ce test sans installer les dépendances Node à la racine. Son import charge `couverture-ecran.mjs`, qui dépend de `@playwright/test`. En simulant l’absence de ce paquet, le test lève `CalledProcessError` ; les validations du lot utilisaient un `node_modules` racine non suivi - Porter ces assertions dans la suite Node dédiée ou rendre le contrôle indépendant de Playwright, puis le vérifier dans les conditions des jobs backend.

### Rouges isolés avant retrait ou correction

Les deux reproductions B-2029 ont été ajoutées dans `tests/test_b2029_couverture.py`, exécutées séparément, puis retirées avec le candidat du lot. Le fichier homonyme conservé par l'intégration est présent dans l'arbre livré. Le nouveau test B-2008 a été ajouté avant de modifier le gestionnaire. Chaque XML a été lu : **1 test, 1 échec, 0 erreur, 0 ignoré**, code 1. Les lignes ci-dessous viennent de leurs messages d'échec.

| Constat | Test isolé | Ligne d'échec recopiée | XML lu |
| --- | --- | --- | --- |
| 1 | `tests/test_b2029_couverture.py::test_garde_sans_dependances_node_des_jobs_backend` | `Error: Cannot find package '@playwright/test'` | `/tmp/diff-4-r5-c1-rouge.xml` |
| 2 | `tests/test_c20_b2008_mime_recette.py::test_polices_sans_table_mime_systeme[police.woff2-font/woff2]` | `Expected: fulfill(body=b'police fictive', content_type='font/woff2')` ; `Actual: fulfill(body=b'police fictive', content_type='application/octet-stream')` | `/tmp/diff-4-r5-c2-rouge.xml` |
| 3 | `tests/test_b2029_couverture.py::test_garde_depuis_tmp` | `Error [ERR_MODULE_NOT_FOUND]: Cannot find module '/tmp/tests/couverture/couverture-ecran.mjs' imported from /tmp/[eval1]` | `/tmp/diff-4-r5-c3-rouge.xml` |

Le constat 1 utilise un chargeur Node qui refuse uniquement `@playwright/test` et appelle le test existant depuis la racine ; il isole donc l'absence de dépendance du problème de répertoire courant. Le constat 3 appelle le même test après `chdir('/tmp')`. Le constat 2 remplace la base MIME par `MimeTypes(filenames=())`, limitée aux types intégrés à Python, puis exerce le véritable gestionnaire `servir` et son appel à `route.fulfill`. Exécution sous Python **3.13.13**.

### Retrait, correctif minimal et appelants relus

Le retrait B-2029 concerne uniquement les deltas propres au lot dans `tests/couverture/couverture-ecran.mjs`, `tests/couverture/couverture-ecran.test.mjs` et le candidat Python. Dans l'arbre rebasé livré, `tests/test_b2029_couverture.py` est conservé par l'intégration : le retrait du candidat ne signifie pas la suppression du test intégré. Le contrôle suivant est **vide, code 0**, ce qui prouve l'identité avec l'intégration, et non l'absence du fichier :

```sh
git diff --exit-code c20/integration -- tests/couverture/couverture-ecran.mjs tests/couverture/couverture-ecran.test.mjs tests/test_b2029_couverture.py
```

La chaîne `requeteASimuler` → `installerGardeReseau` → `principal` et les tests Node déjà intégrés ont été relus. Leurs imports, états de comptage et attentes d'acquittements appartiennent à l'intégration ; aucun ajout du lot n'y reste orphelin. Les dix tests voisins en mémoire passent après retrait. Les assertions retirées sont exclusivement celles du candidat ; aucun test de l'intégration n'est affaibli.

Pour B-2008, le dictionnaire de `scripts/recette_r5_navigateur.py:38` reçoit les deux types explicites sur sa ligne existante. Le branchement `page.route('**/*', servir)` et les chemins de refus, de normalisation d'extension et de repli binaire ont été relus. Les treize cas antérieurs restent inchangés ; les deux nouveaux cas couvrent `.woff2` et `.woff` sans table système. Le fichier passe **15/15**, avec le voisin B-1883 **4/4**. Aucun appelant hors lot n'est modifié.

### Réserves acceptées

Le constat 2 relève de la ligne évidente autorisée et est corrigé. Le candidat B-2029 reste reporté, sans revendication d'une correction de son défaut initial ni de l'import relatif du test conservé par l'intégration. Les passes antérieures restent historiques.

### Portes et limites des preuves

| Porte | Réussis | Échecs / erreurs / ignorés | Preuve |
| --- | ---: | ---: | --- |
| pytest ciblé, B-1883 et B-2008 | **19** | **0 / 0 / 0** | `/tmp/diff-4-r5.xml`, XML lu |
| Même sélection depuis `/tmp`, Playwright indisponible pour Node | **19** | **0 / 0 / 0** | `/tmp/diff-4-r5-isole.xml`, XML lu ; rejeu non additionné aux comptes distincts |
| Node, garde et voisins sans navigateur | **10** | **0 / 0 / 0** | `/tmp/diff-4-r5-node-vert.log`, TAP lu |
| Ruff `src/backend tests` | sans objet | **0 diagnostic** | `/tmp/diff-4-r5-ruff.log`, code 0 |
| TypeScript `tsc --noEmit` | sans objet | **0 diagnostic** | `/tmp/diff-4-r5-tsc.log`, code 0 |
| `git diff --check` et identité des trois fichiers B-2029 avec l'intégration | sans objet | **0** | codes 0 |

Deux cas de test restent ajoutés à cette passe, tous deux pour B-2008 ; les deux reproductions B-2029 sont retirées avec le candidat. Aucun rouge connu n'est soustrait. Le rejeu ciblé des deux scripts restants dans le lot ne sélectionnait pas le test Python B-2029 conservé par l'intégration.

Commandes principales, depuis la racine :

```sh
PYTHONDONTWRITEBYTECODE=1 THERESE_DATA_DIR="$(mktemp -d /tmp/diff-4-r5-data-XXXXXX)" \
OLLAMA_BASE_URL=http://127.0.0.1:9 .venv/bin/python -m pytest \
  tests/test_c20_b1883_finaliser_recette.py tests/test_c20_b2008_mime_recette.py \
  -q -p no:cacheprovider -p tests.bancs_sans_reseau \
  --timeout=120 --junitxml=/tmp/diff-4-r5.xml
.venv/bin/python -m ruff check --no-fix src/backend tests
node --import /tmp/diff4_node_stdio.mjs \
  --test-name-pattern='^(B-2029 : (seule la migration exacte|la garde acquitte)|B-2029 remédiation|B-2029 passe 2|la CLI|la base|seules les lectures|les gestes|B-1715)' \
  tests/couverture/couverture-ecran.test.mjs
git diff --check
```

Le rejeu Python depuis `/tmp` utilise les chemins absolus de l'interpréteur et des deux fichiers de test, `PYTHONPATH` pointant sur cet arbre, une autre base temporaire et `NODE_OPTIONS=--experimental-loader=file:///tmp/diff-4-r5-sans-playwright.mjs`. Ce chargeur reprend le refus de `@playwright/test` de la reproduction rouge. Les deux fichiers Python sélectionnés pour ce rejeu ne dépendent pas de Node ; aucun paquet n'est installé ou déplacé. En revanche, `tests/test_b2029_couverture.py`, conservé par l'intégration, lance toujours Node avec un import relatif au répertoire courant et un chargeur simulant Playwright. Les jobs Linux et Windows sélectionnent `tests/` (`.github/workflows/ci.yml:204`, `.github/workflows/tests-windows.yml:116`) : ce test reste donc collecté. Le rejeu ciblé ne validait pas ce test et ne remplaçait pas une exécution Windows.

Depuis `src/frontend`, `npm_config_offline=true npm_config_cache=/tmp/diff-4-r5-npm npx --no-install tsc --noEmit` passe. Aucun fichier frontend n'a été touché : Vitest et ESLint ne sont pas relancés.

Le premier lancement Node avec `--test` n'a remonté que l'échec de son sous-processus. Le lancement direct a révélé **6 réussites et 4 échecs** liés aux canaux de `spawnSync` (`EPERM`, diagnostics vides). L'adaptation temporaire déjà utilisée en passe 4, `/tmp/diff4_node_stdio.mjs`, a été relue puis réutilisée : elle dirige stdout/stderr des vrais enfants vers des fichiers sous `/tmp`, puis les restitue. Les dix tests passent avec leurs assertions intactes. Ces essais initiaux ne sont pas comptés comme des portes vertes ; aucun correctif n'est apporté aux tests pour contourner le bac à sable.

Le plugin `tests.bancs_sans_reseau` indique **0 tentative de connexion** dans chaque session Python. Les tests Node retenus utilisent des doubles en mémoire ; les parcours avec navigateur, `/private/tmp` ou corbeille personnelle ne sont pas exécutés. Aucune suite complète, aucun réseau, fournisseur LLM, port réservé, `~/.therese` ou `.app-loop/`. Aucun `rm`, rebase, commit, `git add`, dépôt annexe ou bundle. Les liens non suivis `.venv` et `src/frontend/node_modules`, présents à l'arrivée, restent en place. Tous les changements de cette passe restent non commités.

## Remédiation de la relecture, passe 6

Les trois constats sont confirmés et corrigés dans cet arbre. Le périmètre comprend uniquement la fixture et les tests B-2008, une entrée du dictionnaire MIME, les affirmations du bilan sur B-2029 et un nouveau test de cohérence du bilan. Aucun candidat supplémentaire retiré ; B-2029 et B-1885 restent retirés du lot et reportés. Aucun fichier d'un autre lot n'est modifié.

### Tests rouges écrits avant chaque correction

Chaque test a été écrit ou étendu avant son correctif, puis lancé seul. Les trois XML ont été lus : **1 test, 1 échec, 0 erreur, 0 ignoré** par constat, code 1. Le rouge WebP a également été reproduit seul sous Python 3.12.3, avec le même résultat.

| Constat | Test isolé | Ligne d'échec recopiée | XML lu |
| --- | --- | --- | --- |
| 1, P1 Windows | `tests/test_c20_b2008_mime_recette.py::test_fixture_sans_o_directory` | `AttributeError: module 'os' has no attribute 'O_DIRECTORY'. Did you mean: 'O_DIRECT'?` | `/tmp/diff-4-r6-c1-rouge.xml` |
| 2, P2 WebP | `tests/test_c20_b2008_mime_recette.py::test_ressources_sans_table_mime_systeme[photo.webp-image/webp]` | `Expected: fulfill(body=b'police fictive', content_type='image/webp')` ; `Actual: fulfill(body=b'police fictive', content_type='application/octet-stream')` | `/tmp/diff-4-r6-c2-rouge.xml` ; `/tmp/diff-4-r6-c2-py312-rouge.xml` |
| 3, P2 bilan | `tests/test_c20_diff4_bilan.py::test_bilan_distingue_retrait_b2029_et_test_integre` | `AssertionError: Le bilan nie la collecte du test B-2029 pourtant présent.` | `/tmp/diff-4-r6-c3-rouge.xml` |

### Correctifs minimaux et appelants relus

1. **Windows.** Le nouveau test copie le module `os` dans un module simulé, y retire `O_DIRECTORY`, puis demande la véritable fixture et exerce le gestionnaire installé. La fixture ajoute maintenant `monkeypatch.setattr("os.O_DIRECTORY", 0, raising=False)` avant la simulation de `os.open`. Le script de recette reste inchangé pour ce constat. Relecture de l'initialisation simulée, de `page.route` et de la fermeture du navigateur. Après correction : B-2008 **16/16**, voisin B-1883 **4/4** ; `/tmp/diff-4-r6-c1-vert.xml` lu. Ce contrôle sous Linux reproduit l'absence de la constante ; aucune exécution Windows native n'est revendiquée.
2. **WebP.** Une seule entrée de production est ajoutée au dictionnaire existant : `.webp: image/webp`. L'ancien test des deux polices sans table système est étendu aux dix cas déjà promis : WOFF2, WOFF, SVG, PNG, JPG majuscule, WebP, JavaScript, CSS, HTML et extension inconnue. Avant chaque appel au gestionnaire, une nouvelle base `MimeTypes(filenames=())` remplace la base système ; l'initialisation système est désactivée et l'entrée WebP intégrée à Python 3.13 est retirée pour reproduire aussi l'absence constatée sous 3.12.3. Les assertions de corps, type et absence d'abandon sont conservées. Relecture de `page.route` → `servir` → `route.fulfill`, des refus, de la normalisation d'extension et du repli binaire. Après correction : B-2008 **24/24** et B-1883 **4/4** sous Python **3.13.13** et **3.12.3** ; `/tmp/diff-4-r6-c2-vert.xml` et `/tmp/diff-4-r6-py312.xml` lus.
3. **Bilan B-2029.** L'état courant et les affirmations de la passe 5 distinguent désormais le retrait du candidat du lot et le test conservé par l'intégration. Le nouveau test vérifie la présence du fichier, l'abandon de l'affirmation de non-collecte et cette distinction dans l'état courant. Le fichier intégré n'est ni modifié ni supprimé : son import relatif est visible à `tests/test_b2029_couverture.py:22`, son lancement de Node à la ligne 56. Le contrôle `git diff --exit-code c20/integration -- tests/couverture/couverture-ecran.mjs tests/couverture/couverture-ecran.test.mjs tests/test_b2029_couverture.py` reste vide, code **0**. Les sélections `tests/` des deux CI ont été relues, et `pytest --collect-only tests/test_b2029_couverture.py` collecte bien **1 test**, sans l'exécuter. Aucun correctif de ce test hors lot n'est revendiqué.

### Portes ciblées et limites des preuves

| Porte | Réussis | Échecs / erreurs / ignorés | Preuve |
| --- | ---: | ---: | --- |
| pytest final sous Python 3.13.13, lot et voisin B-1883 | **29** | **0 / 0 / 0** | `/tmp/diff-4-r6.xml`, XML lu |
| pytest sous Python 3.12.3, B-2008 et voisin B-1883 | **28** | **0 / 0 / 0** | `/tmp/diff-4-r6-py312.xml`, XML lu ; rejeu non additionné aux comptes distincts |
| Ruff `src/backend tests` | sans objet | **0 diagnostic** | code **0**, `All checks passed!` |
| `git diff --check` | sans objet | **0** | code **0** |

Répartition finale : B-2008 **24**, B-1883 **4**, cohérence du bilan **1**. La passe ajoute dix cas aux dix-neuf précédents : un cas sans `O_DIRECTORY`, huit formats supplémentaires sans table système et un contrôle du bilan. Aucun rouge connu n'est soustrait, aucune assertion existante n'est affaiblie. Le plugin hors réseau indique **0 tentative de connexion** dans chaque session.

Commande de la porte finale depuis la racine :

```sh
PYTHONDONTWRITEBYTECODE=1 THERESE_DATA_DIR="$(mktemp -d /tmp/diff-4-r6-data-XXXXXX)" \
OLLAMA_BASE_URL=http://127.0.0.1:9 .venv/bin/python -m pytest \
  tests/test_c20_b2008_mime_recette.py tests/test_c20_b1883_finaliser_recette.py \
  tests/test_c20_diff4_bilan.py \
  -q -p no:cacheprovider -p tests.bancs_sans_reseau \
  --timeout=120 --junitxml=/tmp/diff-4-r6.xml
.venv/bin/python -m ruff check --no-fix src/backend tests
git diff --check
```

Le Python 3.12.3 disponible n'a pas pytest installé. Le rejeu utilise les modules Python purs de pytest et de son plugin de timeout déjà présents dans `.venv`, sans installation :

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
PYTHONPATH="$PWD/.venv/lib/python3.13/site-packages:$PWD" \
OLLAMA_BASE_URL=http://127.0.0.1:9 python3.12 -m pytest \
  --noconftest -c /dev/null --rootdir="$PWD" \
  tests/test_c20_b2008_mime_recette.py tests/test_c20_b1883_finaliser_recette.py \
  -q -p no:cacheprovider -p pytest_timeout -p tests.bancs_sans_reseau \
  --timeout=120 --junitxml=/tmp/diff-4-r6-py312.xml
```

Ces deux fichiers sont autonomes ; ce rejeu ne charge pas les fixtures backend ni les extensions binaires de Python 3.13. Python 3.11 n'a pas été rejoué localement. Aucun fichier frontend modifié : Vitest, TypeScript et ESLint non applicables. Aucune suite complète, aucun réseau, fournisseur LLM, port réservé, `~/.therese` ou `.app-loop/`. Aucun `rm`, rebase, copie depuis une autre référence, commit, `git add`, dépôt annexe ou bundle. Les changements restent non commités ; les liens préexistants `.venv` et `src/frontend/node_modules` sont conservés.
