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
