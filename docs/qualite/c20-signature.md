# Cycle 20 : garde-fous de la chaîne de publication

Périmètre : correctifs locaux, sans réseau, sans publication et sans signature réelle. Les échecs ci-dessous ont été relevés avant les correctifs sur les reproductions du dépôt. Le test B-1858 a été ajouté puis exécuté rouge avant son implémentation.

| ID | Verdict | Test | Ligne d'échec observée avant correctif | Fichiers corrigés |
|---|---|---|---|---|
| B-1855 | Corrigé | `scripts/tests/test_c20_b1855_tag_checkout.py::test_le_tag_manuel_designe_le_commit_valide_par_la_ci` | `E   AssertionError: aucune comparaison du commit du tag manuel à celui de la CI ; refs checkout : {'sources-copyleft': None, 'build': None}` | `.github/workflows/release.yml` |
| B-1856 | Corrigé | `scripts/tests/test_c20_b1856_sources_brouillon.py::test_les_sources_verifient_le_statut_brouillon_avant_upload` | `E   AssertionError: la release existante est seulement recherchée, sans contrôle du statut brouillon` | `.github/workflows/release.yml` |
| B-1858 | Corrigé | `scripts/tests/test_c20_b1858_signature_windows_obligatoire.py::test_la_publication_windows_exige_une_signature_sauf_a_blanc` | `E   AssertionError: La publication Windows ne refuse pas une signature inactive` | `.github/workflows/release.yml`, nouveau test B-1858 |
| B-1881 | Corrigé | `scripts/tests/test_c20_b1881_publication_brouillon.py::test_une_release_publique_ne_recoit_aucun_upload` | `E   AssertionError: release publique : upload effectué malgré isDraft=false : [['gh', 'release', 'upload', 'v0.83.0-alpha', '--clobber', 'preuve-factice.json', 'factice.dmg']]` | `scripts/publish_release_artifacts.py` |
| B-1882 | Corrigé | `scripts/tests/test_c20_b1882_architecture_macos.py::test_archive_x64_refusee_avant_renommage_et_publication` | `E   AssertionError: archive x86_64 publiée sous aarch64 : [['gh', 'release', 'upload', 'v0.83.0-alpha', '--clobber', 'THERESE.app.tar.gz.json', 'THERESE_aarch64.app.tar.gz.sig', 'THERESE_aarch64.app.tar.gz']]` | `scripts/publish_release_artifacts.py` |
| B-1886 | Corrigé | `scripts/tests/test_c20_b1886_executable_etranger.py::test_un_executable_etranger_ne_passe_pas_par_sa_seule_table_pe` | `E   Failed: DID NOT RAISE <class 'ValueError'>` | `scripts/verify_packaged_licenses.py`, `scripts/tests/test_packaged_licenses.py` |
| B-1887 | Déjà vert, inchangé | `scripts/tests/test_c20_b1887_identite_signataire.py::test_la_garde_authenticode_controle_le_certificat_signataire` | Aucun échec : test vert avant les correctifs. | Aucun. |

Les cas supplémentaires sont dans `scripts/tests/test_c20_signature_gardes.py` : tag identique, divergent ou absent ; lecture du brouillon réussie ou en échec ; course de création perdue ; archive universelle et vérification des octets et de la preuve de l'alias. Les commandes de publication et de signature y sont fictives. Le test Windows existant qui acceptait auparavant un exécutable signé étranger exige désormais la provenance du build ; il vérifie aussi le refus de modifications signées ou non signées.

## Ce qui change pour lancer une release

- **B-1855** : hors mode à blanc, le tag est résolu jusqu'au commit et comparé au commit du déclenchement, celui des contrôles CI. Un tag introuvable est refusé avec « Tag demandé introuvable ou sans commit » ; un commit différent avec « Le commit du tag demandé diffère du commit validé par la CI : publication refusée ».
- **B-1856** : juste avant de joindre les sources, la lecture du statut doit réussir et indiquer un brouillon. Sinon : « Impossible de vérifier le statut brouillon de la release : envoi des sources refusé » ou « La release doit être un brouillon : envoi des sources refusé ».
- **B-1858** : une publication réelle exige l'activation de la signature Windows dès `preflight`, avant le dépôt des sources ou des installeurs. Sinon : « Signature Windows inactive : secrets Microsoft absents ou incomplets, publication refusée ». Le contrôle du job Windows reste en place. Un lancement à blanc peut continuer sans signature et indique « Mode à blanc : signature Windows inactive, publication simulée. »
- **B-1881** : juste avant l'envoi des artefacts, y compris après une création de brouillon perdue dans une course, le statut est relu. Une release publiée est refusée avec « La release doit être un brouillon : publication refusée ». Une lecture échouée ou illisible est également bloquante.
- **B-1882** : l'exécutable Mach-O de l'archive doit contenir une tranche ARM64, y compris pour une archive universelle. Sinon : « Archive macOS incompatible : architecture aarch64 absente » ou un message d'archive illisible. L'alias reprend les octets originaux sans re-signer le bundle ; sa preuve porte le nom et l'empreinte du fichier envoyé.
- **B-1886** : un exécutable Windows étranger ou modifié est refusé avec « Exécutable principal différent de ce build ». Pour comparer un fichier signé à celui du build, seuls les champs PE et le bloc de certificat modifiés par Authenticode sont neutralisés ; la signature reste contrôlée séparément.
- **B-1887** : la vérification exige une signature Authenticode valide et horodatée ; elle compare le champ `O` du certificat à l'éditeur attendu lorsque celui-ci est renseigné.

Le mode à blanc et ses libellés `a-blanc-*` restent utilisables. Il ne publie pas les sources ni les artefacts ; les contrôles qui interviennent uniquement juste avant ces envois ne sont donc pas exercés par le lancement à blanc lui-même.

## Limites et portes locales

Ces tests utilisent des commandes et certificats fictifs. Ils ne prouvent ni la configuration effective des services Apple et Microsoft, ni la création, l'identité, la validité ou l'horodatage d'une signature réelle. La comparaison PE et les archives universelles doivent encore être confrontées aux octets d'un vrai build signé. Les lectures du statut et l'envoi restent deux opérations distinctes, sans transaction atomique côté service.

La porte Ruff demandée a d'abord signalé 23 écarts déjà présents à `HEAD`, vérifiés fichier par fichier. Les corrections concernent les imports, les contextes et deux captures de variables ; elles conservent les assertions existantes. L'orthographe usuelle du nom Windows reste volontairement conservée avec une exception Ruff ciblée.

- Tests ciblés signature et licences : **32 réussis, 1 ignoré, 9 sous-tests réussis**.
- `test_release_pipeline.py` et `test_macos_signing.py` : **41 réussis et 519 sous-tests réussis**.
- Porte complète `scripts/tests` : **212 réussis, 5 échecs, 2 ignorés et 798 sous-tests réussis**. Deux échecs CPython indiquent `FileNotFoundError: ... 'readelf'`. Trois autres rencontrent `TypeError: expected string or bytes-like object, got 'NoneType'` dans `distribution_files`, car des métadonnées de distributions Python locales n'ont pas de nom ; cette fonction est inchangée depuis `HEAD`. Ces cinq cas sont hors des reproductions de signature. `dpkg-deb` est également absent : les deux tests qui le demandent explicitement sont ignorés, et le test CPython du paquet Debian n'a pas encore atteint son appel à cet outil. Aucun substitut ni téléchargement n'a été utilisé pour masquer ces limites.
- Ruff sur `scripts tests` : **vert, zéro erreur**. Chargement YAML de `release.yml` : **vert**. `git diff --check` : **vert**.
- Les tests CPython ont conservé leurs copies temporaires dans le dossier ignoré `.work-t2/round7`, qui occupe environ 983 Mo au contrôle final. Le périmètre d'écriture ne permet pas de les déplacer vers la Corbeille située hors de l'arbre de travail.

## Remédiation de la relecture

- **B-1858** : la garde ajoutée à `preflight` utilise `WINDOWS_SIGNE`, calculé à partir des six secrets Microsoft déjà requis. Elle est ignorée à blanc. `sources-copyleft` et `build` dépendent tous deux de la réussite de `preflight` ; la garde du job Windows reste présente. Avant correction, le test de structure a échoué avec la ligne suivante :

  `E   AssertionError: La signature Windows n'est pas exigée dans preflight avant tout dépôt`

- **B-1886** : le nouveau test construit une table de certificats fictive en suffixe, alignée sur huit octets, avec somme de contrôle et répertoire de sécurité réécrits. Il vérifie que le même build est accepté et qu'un binaire différent atteint bien la comparaison normalisée avant d'être refusé. Le cas passe sans modification du code de comparaison : la relecture a révélé une preuve manquante, sans défaut de ce code démontré.

- **Portes de remédiation** : 214 tests et 802 sous-tests réussis, 2 tests ignorés. La commande complète retourne un échec à cause des 5 tests `CPythonComponentsTests` préexistants : 2 faute de `readelf`, 3 à cause de métadonnées Python sans nom. Le XML `/tmp/signature-r1.xml` ne contient aucun autre échec. Chargement YAML et `git diff --check` réussis.

Les tests ont conservé leurs copies temporaires dans `.work-t2/round7`, qui totalise 3,1 Go au contrôle de cette remédiation. Aucun nettoyage n'a été effectué.

## Réconciliation avec l'intégration (18/11)

Contrôle dans cet arbre, sur `c20/signature-c20`, après rebase des huit commits du lot sur `c20/integration`. Aucun code de publication, workflow ou dépendance CI n'a été modifié. Aucun réseau, serveur, accès à `~/.therese`, `git add` ou commit n'a été utilisé.

- **B-1085** : le test existant de `scripts/tests/test_release_pipeline.py` appelle toujours `release_notes.body` pour les notes signées et non signées. Son attente de commande macOS lit désormais `productName` dans `tauri.conf.json` et il vérifie que tous les chemins `/Applications/….app` produits correspondent à ce nom. Le contrôle existant de l'absence de `xattr` après signature est conservé. La garde `tests/test_b1085_commande_xattr_nom_du_paquet.py` interdit désormais tout chemin d'application dans le workflow, sans dupliquer les tests du générateur.
- **Découverte unittest** : les deux modules qui importaient `pytest` utilisent désormais `unittest.TestCase`, `unittest.mock` et des dossiers temporaires. Chaque cas paramétré devient un `subTest`, avec restauration des substitutions et un dossier neuf pour chaque course de création.

| Module converti | Cas avant | Cas après | Méthodes unittest | Sous-tests paramétrés | Assertions conservées | Attentes d'exception conservées |
|---|---:|---:|---:|---:|---:|---:|
| `test_c20_b1886_executable_etranger.py` | 2 | 2 | 2 | 0 | 10 | 2 |
| `test_c20_signature_gardes.py` | 11 | 11 | 5 | 9 | 12 | 2 |
| Total | 13 | 13 | 7 | 9 | 22 | 4 |

Les neuf sous-tests remplacent trois méthodes paramétrées comptant chacune trois cas. Les quatre autres méthodes représentent chacune un cas : le total reste donc treize, et non seize. La comparaison des arbres syntaxiques avec `HEAD` confirme la conservation, test par test, des expressions des 22 assertions, des quatre attentes d'exception, de leurs messages recherchés et des neuf jeux de paramètres.

Commandes exécutées avant puis après modification :

```sh
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
OLLAMA_BASE_URL=http://127.0.0.1:9 PYTHONPATH=src/backend /Users/synoptia/.claude/travail/therese-c20-pile/venv/bin/python -m pytest tests/test_b1085_commande_xattr_nom_du_paquet.py scripts/tests -q -p no:cacheprovider
```

- **Unittest avant** : 203 tests, dont 196 réussis, 5 erreurs et 2 ignorés. Deux erreurs sont les imports `pytest` ; les trois autres sont les outils Linux absents indiqués ci-dessous.
- **Unittest après** : 208 tests, dont 203 réussis, 3 erreurs et 2 ignorés. Les sept méthodes converties remplacent les deux erreurs de chargement. Aucun import `pytest` ne reste dans ces modules.
- **Pytest après** : 216 tests, dont 211 réussis, 3 échecs et 2 ignorés, ainsi que **821 sous-tests réussis**. B-1085, le test des notes et les sept méthodes converties sont verts. Le rapport XML compte 1 037 tests en incluant les sous-tests. Pour cette exécution, `PYTEST_ADDOPTS` ne contient que `--junitxml=.work-t2/reconciliation-18-11/pytest-apres.xml` : le hook existant de `tests/conftest.py` appelle `os._exit` avant l'affichage du résumé terminal, d'où ce relevé XML.

Les trois erreurs restantes de `CPythonComponentsTests` sont identiques avant et après modification, avec le même `FileNotFoundError`, et constituent aussi les trois échecs pytest :

| Test | Outil absent sur ce Mac |
|---|---|
| `test_expat_embeds_separate_cc0_siphash` | `readelf` |
| `test_real_fixtures_define_components_instead_of_importing_them` | `readelf` |
| `test_real_deb_cli_refuses_old_notices_then_accepts_completed_notices` | `dpkg-deb` |

Ces limites n'ont pas été masquées et aucun outil n'a été installé. Les deux tests déjà ignorés nécessitent également `dpkg-deb`. Les journaux avant/après, le relevé des erreurs, le rapport XML et le contrôle de conservation des assertions sont dans le dossier local ignoré `.work-t2/reconciliation-18-11/`. Les copies CPython de `.work-t2/round7` sont conservées, sans nettoyage.

Ruff sur les quatre fichiers Python touchés : **vert** (`venv/bin/python -m ruff check --no-cache` avec leurs chemins). `git diff --check` : **vert**. Toutes les modifications restent hors index.

## À vérifier sur un vrai build

- B-1886 avec les secrets Microsoft présents : extraire `therese.exe` de l'installeur NSIS et de l'image MSI et vérifier qu'il est accepté par la comparaison normalisée ; un horodatage ou une seconde signature compris dans la taille déclarée passent ; un octet après la taille déclarée ou un alignement autre que 8 bloquerait la release.
- `verify_windows_signing.ps1` ne relit pas la validité Authenticode de l'exécutable extrait de l'installeur.
- Désinstalleur NSIS signé : vérifier que `nsis_installer.py` ne le refuse pas pour « octets ajoutés ».
- B-1855 : `git rev-parse refs/tags/$TAG^{commit}` égale `GITHUB_SHA` sur une poussée de tag annoté et sur un lancement manuel (le checkout est en `fetch-depth: 0` sans `fetch-tags`).
- B-1856 et B-1881 : première release absente, création en brouillon puis lecture `isDraft` à `true`.
- B-1882 : l'archive réécrite par `sign_macos.py finish` contient bien `THERESE.app/Contents/MacOS/therese` sans préfixe `./`.
- À blanc sur les trois systèmes, avec et sans secrets Microsoft.
