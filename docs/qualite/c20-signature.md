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
- **B-1858** : une publication Windows réelle exige l'activation de la signature. Sinon : « Signature Windows inactive : secrets Microsoft absents ou incomplets, publication refusée ». Un lancement à blanc peut continuer sans signature et indique « Mode à blanc : signature Windows inactive, publication simulée. »
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
