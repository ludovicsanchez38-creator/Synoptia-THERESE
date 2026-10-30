# Lot T2 — Signature et licences, troisième tour — 29 octobre 2026

Branche `coco/therese-signature-20261029`. Départ propre à `bd95a87b687726f6db1a66b185261b47cde37957`, base de comparaison `08d0a8a0`. Travail poursuivi dans l’arbre demandé ; aucun push, aucune CI déclenchée.

**Les deux constats de contrôle sont corrigés. 16 des 25 blocages sont levés ; 9 restent bloquants.** `THIRD_PARTY_LICENSES` reste **PROVISOIRE — DIFFUSION REFUSÉE**. Sur **1 326 entrées**, `generate` retourne **0**, `check` retourne **1** et refuse exactement les neuf crates objc2 listées plus bas. Aucune licence déclarée ne manque désormais de conditions reconnues. Le fichier généré fait **5 721 633 octets** et correspond octet pour octet au rendu déterministe.

## Contrôles corrigés, avec tests rouges préalables

1. L’exemption Apache porte uniquement sur le champ immédiatement précédé du paragraphe normatif entier et suivi du début de son exemple. Les blocs supplémentaires « AUTRE COMPOSANT » avec `Copyright [yyyy] [name of copyright owner]` et `Copyright 2026 [name of copyright owner]` sont refusés. Le format RTF de l’annexe Meson dans NumPy est reconnu sans modifier le texte livré et sans élargir la portée. Les exemptions pédagogiques GNU et FreeType ont été circonscrites de la même façon : leurs contre-épreuves avaient également révélé des remplacements globaux.

2. Toutes les licences nommées dans une déclaration sont contrôlées séparément, y compris `OR`, `AND`, `/` et les classificateurs Python. Une MIT complète accompagnée d’un simple renvoi Apache est refusée. Un identifiant ou classificateur inconnu ne disparaît pas derrière un identifiant reconnu. `android_system_properties 0.1.5` et `shlex 1.3.0` ont leur texte Apache intégral, en plus de leurs notices originales. La passe de l’inventaire a conduit à compléter **45 entrées**, toutes listées ci-dessous.

3. Le statut **« texte amont reproduit tel quel »** (`upstream-verbatim`) est accordé seulement aux fichiers précisément prouvés. Le contrôle rapproche paquet, archive verrouillée, intégrité, chemin interne, SHA-256 de la notice entière, lignes exactes et empreinte du fichier source reconstitué. Cette reconstitution conserve LF/CRLF et les blancs retirés aux seules extrémités par le collecteur historique. Une preuve absente, une empreinte discordante, une ligne différente ou un autre texte livré entraîne le refus. Les suppléments locaux et textes partagés ne peuvent pas recevoir cette exception. Les copyrights nommés sont intacts.

Les premières contre-épreuves ont donné **32 échecs, 33 réussites et 20 sous-tests réussis** (`red.xml`, dont les références mobiles de CI). Des tests rouges supplémentaires ont couvert les empreintes du membre et de l’archive (2 échecs), les licences nommées inconnues/Clear BSD (2), le format RTF (1), GNU/FreeType hors exemple (2), un classificateur inconnu (1) et la version précise de rust-cache dans les deux workflows (2). Trois échecs supplémentaires ont ensuite prouvé qu’un supplément pouvait effacer une réserve existante ; ce comportement est corrigé, les réserves de libunistring et mingw-winpthread sont rétablies. Une levée exige maintenant une valeur explicite. Tous ces tests passent après correction. Le contrat historique qui recherchait encore `upload-artifact@v4` a ensuite échoué dans la suite complète ; il attend désormais l’empreinte complète vérifiée, en conservant ses assertions sur les délais et le rapport.

## Les 16 blocages levés et leurs preuves

Toutes les preuves nécessaires au contrôle sont versionnées dans `licenses/attribution-sources.json` ; chaque fichier complémentaire est lié à son SHA-256 par `licenses/overrides.json`. Les URL, commits, chemins et empreintes complètes des fichiers amont y figurent. Les archives verrouillées ont été vérifiées avant lecture, sans exécuter leur code.

### Les 13 entrées qui reproduisent le champ générique amont

Les 16 fichiers ci-dessous sont identiques à leur contenu d’archive après la normalisation historique documentée. La ligne générique, elle, est identique octet pour octet. Les empreintes d’archives sont abrégées ici à 16 caractères ; les SHA-256 complets des archives, fichiers internes et textes livrés, ainsi que le texte exact des lignes, figurent dans le JSON versionné.

| Entrée | Chemin interne et ligne | SHA-256 archive (préfixe) |
| --- | --- | --- |
| `npm:eslint-scope@8.4.0` | `package/LICENSE:16` | `c3a28a402da98e9d` |
| `npm:esrecurse@4.3.0` | `package/esrecurse.js:16` | `3ecf9370d7296b47` |
| `npm:estraverse@5.3.0` | `package/LICENSE.BSD:13` | `3e8d45da5b8085a4` |
| `npm:esutils@2.0.3` | `package/LICENSE.BSD:13` | `c5adbd730a495a3c` |
| `python:caldav@2.2.3` | `caldav-2.2.3/venv/lib/python3.13/site-packages/jaraco_functools-4.3.0.dist-info/licenses/LICENSE:3` | `d53e2de4e4aee9e3` |
| `python:caldav@2.2.3` | `caldav-2.2.3/venv/lib/python3.13/site-packages/keyring-25.7.0.dist-info/licenses/LICENSE:3` | `d53e2de4e4aee9e3` |
| `python:jaraco-context@6.1.0` | `jaraco_context-6.1.0/LICENSE:3` | `129a341b0a85a7db` |
| `python:jaraco-functools@4.4.0` | `jaraco_functools-4.4.0/LICENSE:3` | `da21933b0417b895` |
| `python:keyring@25.7.0` | `keyring-25.7.0/LICENSE:3` | `fe01bd85eb3f8fb3` |
| `python:setuptools@84.2.1` | `setuptools-84.2.1/setuptools/_vendor/jaraco_context-6.1.0.dist-info/licenses/LICENSE:3` | `3ff8b3b5492a0aa6` |
| `python:setuptools@84.2.1` | `setuptools-84.2.1/setuptools/_vendor/jaraco_functools-4.4.0.dist-info/licenses/LICENSE:3` | `3ff8b3b5492a0aa6` |
| `python:setuptools@84.2.1` | `setuptools-84.2.1/setuptools/_vendor/zipp-3.23.0.dist-info/licenses/LICENSE:3` | `3ff8b3b5492a0aa6` |
| `python:torch@2.9.1` | `torch-2.9.1.dist-info/licenses/LICENSE:8369` | `1edee27a7c9897f4` |
| `python:torch@2.9.1/wheel-cpu-linux` | `torch-2.9.1+cpu.dist-info/licenses/LICENSE:8327` | `39b3dff6d8fba240` |
| `python:torch@2.9.1/wheel-cpu-windows` | `torch-2.9.1+cpu.dist-info/LICENSE:7335` | `404a7ab2fffaf2ca` |
| `python:zipp@3.23.0` | `zipp-3.23.0/LICENSE:3` | `a07157588a12518c` |

Pour `esrecurse`, le texte déjà livré était le fichier JavaScript complet : sa copie amont a été comparée à `package/esrecurse.js` dans le paquet npm verrouillé et son chemin interne est maintenant explicite. Les clauses BSD avec `<COPYRIGHT HOLDER>`, les MIT avec `<copyright holders>` et les exemples internes Torch sont conservés tels que publiés ; aucun nom n’a été substitué.

### Rustls Android 0.1.1

Le paquet ne contient pas de `.cargo_vcs_info.json`. Le tag `v/0.1.1` du dépôt principal a été écarté : il contient Android **0.1.0**. Le tag de release `v/0.3.3`, résolu au commit **`669ace0a801ef4be8e0e23d9c534849497ee5782`**, contient Android **0.1.1**. Son `android-release-support/Cargo.toml` et son `src/lib.rs` sont identiques octet pour octet à `Cargo.toml.orig` et `src/lib.rs` de l’archive verrouillée. Le commit de passage d’Android à 0.1.1, `da3d9c36f48fb9f8f97e94f132fdab67ab0fc75b`, est également consigné.

Le fichier MIT de ce tag donne **Copyright (c) 2022 1Password**. Les fichiers MIT et Apache sont ajoutés intégralement :

| Fichier amont | SHA-256 |
| --- | --- |
| [LICENSE-MIT](https://raw.githubusercontent.com/rustls/rustls-platform-verifier/669ace0a801ef4be8e0e23d9c534849497ee5782/LICENSE-MIT) | `1c7cf76689c837a68ed8d704994e52a0f2940c087958f860d17f3186afbdcc0c` |
| [LICENSE-APACHE](https://raw.githubusercontent.com/rustls/rustls-platform-verifier/669ace0a801ef4be8e0e23d9c534849497ee5782/LICENSE-APACHE) | `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4` |

### Les deux suppléments natifs PyAV

Les trois roues verrouillées de `av 17.1.0` ont été ouvertes après vérification d’intégrité. Les binaires SVT contiennent `v4.1.0` sur Linux, macOS et Windows. Les bibliothèques Linux contiennent dans leurs noms de fichiers de débogage les versions **libXau 1.0.9-3.el8**, **libxcb 1.13.1-1.el8** et **libdrm 2.4.115-2.el8**. Les SONAME 6.0.0, 1.1.0 et 2.4.0 n’ont pas été pris pour les versions source. Les noms et SHA-256 des neuf bibliothèques examinées sont consignés.

La recette [PyAV 17.1.0, `scripts/ffmpeg-8.1.json`](https://github.com/PyAV-Org/PyAV/blob/97241598792f4c980c32458187154c7c999d68b3/scripts/ffmpeg-8.1.json) désigne FFmpeg **8.1.1-2**. La recette correspondante, commit `b84838a003b1626152ef530750d5c3e0022c3db9`, fixe SVT-AV1 **4.1.0** et son archive SHA-256 `184162d3db3a4448882b17230413b4938ca252eef6b3c5e2f1236b2fcf497881`. Les bibliothèques FFmpeg des roues portent aussi la version 8.1.1.

| Composant et version | Commit du tag amont | Licence / fichier de preuve principal | SHA-256 du fichier |
| --- | --- | --- | --- |
| SVT-AV1 4.1.0 | `c04f951541ad600e0d9c10836f2ab7b9bc69816d` | [LICENSE.md](https://gitlab.com/AOMediaCodec/SVT-AV1/-/raw/c04f951541ad600e0d9c10836f2ab7b9bc69816d/LICENSE.md) | `0acc2fcb27472bdc9aaf8b71f37055bbdac4f54671b7d922f241bd7fcd0dd3e6` |
| libXau 1.0.9 | `d9443b2c57b512cfb250b35707378654d86c7dea` | [COPYING](https://gitlab.freedesktop.org/xorg/lib/libxau/-/raw/d9443b2c57b512cfb250b35707378654d86c7dea/COPYING) | `56abe29bb1d9806a9e04fa9f80fed2c0f18027594df3f098148d814aef6bddfa` |
| libxcb 1.13.1 | `8287ebd7b752c33b0cabc4982606fe4831106f7e` | [COPYING](https://gitlab.freedesktop.org/xorg/lib/libxcb/-/raw/8287ebd7b752c33b0cabc4982606fe4831106f7e/COPYING) | `c5ffbfeaa501071ceeb97b7de2c0d703fdaa35de01c0fb6cbac1c28453a3e9fd` |
| libdrm 2.4.115 | `ee558cea20d1f9d822fe1a28e97beaf365bf9d38` | [xf86drm.c](https://gitlab.freedesktop.org/mesa/drm/-/raw/ee558cea20d1f9d822fe1a28e97beaf365bf9d38/xf86drm.c) | `406f82058a4c6aedc815826dc8e896e03cde9be26e6ab5c37263037d5417fc77` |

Le groupe `libXau-libxcb-libdrm` contient désormais les deux COPYING et les 13 en-têtes de licence intacts des sources et en-têtes libdrm correspondants, avec leurs attributions. Libdrm n’a pas de COPYING central à ce tag. SVT-AV1 fournit **BSD-3-Clause-Clear**, copyright Alliance for Open Media 2021 : la déclaration et le verrou natif ont été corrigés, le modèle BSD générique a été remplacé. Les deux références d’artefacts natives pointent maintenant sur les fichiers amont épinglés.

## Les neuf blocages maintenus

Toutes les archives suivantes désignent **`7b1abfd750a2cacaea71d6a56ecfb83cb7de560b`** dans `.cargo_vcs_info.json` :

- `cargo:objc2-app-kit@0.3.2`.
- `cargo:objc2-core-foundation@0.3.2`.
- `cargo:objc2-core-graphics@0.3.2`.
- `cargo:objc2-foundation@0.3.2`.
- `cargo:objc2-io-surface@0.3.2`.
- `cargo:objc2-osa-kit@0.3.2`.
- `cargo:objc2-quartz-core@0.3.2`.
- `cargo:objc2-ui-kit@0.3.2`.
- `cargo:objc2-web-kit@0.3.2`.

Le [LICENSE.md à ce commit](https://github.com/madsmtm/objc2/blob/7b1abfd750a2cacaea71d6a56ecfb83cb7de560b/LICENSE.md), SHA-256 **`7f976f7e9cb2d87df7230606feb932c3f21ac0e664045a775b600046ff850c54`**, expose les licences et la réserve relative aux SDK Apple, mais ne nomme aucun auteur ou titulaire. Ce fichier est désormais livré intégralement avec ces entrées. Les chemins usuels `LICENSE.txt`, `LICENSE-MIT.txt`, `LICENSE-APACHE.txt` et `LICENSE-ZLIB.txt` n’existent pas à ce commit ; l’arbre Git ne contient que LICENSE.md comme notice centrale.

Une recherche complémentaire dans **517 fichiers source/documentation** de ce commit n’a trouvé aucune ligne Copyright ou Authors attribuant ces crates. `workspace.package.authors` nomme Mads Marquart, mais les **neuf Cargo.toml.orig n’héritent pas de ce champ** et ne déclarent aucun auteur. Cette piste est conservée avec URL, commit, empreinte du manifeste racine et empreinte de chaque manifeste verrouillé ; elle n’est pas transformée en attribution propre à une crate. `attribution_missing: true` demeure pour les neuf entrées. Aucun remplacement générique ni attribution inventée ne les fait passer.

## Les 45 entrées révélées par le contrôle de couverture

Les variantes typographiques déjà complètes (commentaires de code, formulations ISC/BSD, MIT-CMU) ont d’abord été distinguées des manques. Le contrôle final a demandé les compléments suivants. Les déclarations de paquet sont conservées, même lorsqu’elles divergent du texte présent dans l’archive (par exemple sqlcipher3 déclare MIT mais livre Zlib) ; les deux informations restent visibles. Les conditions partagées n’empruntent pas le copyright d’un autre paquet.

| Entrée | Conditions intégrales ajoutées |
| --- | --- |
| `cargo:aho-corasick@1.1.4` | Unlicense |
| `cargo:android_system_properties@0.1.5` | Apache-2.0 |
| `cargo:brotli-decompressor@5.0.0` | MIT |
| `cargo:brotli@8.0.2` | BSD-3-Clause |
| `cargo:byteorder@1.5.0` | Unlicense |
| `cargo:cargo_toml@0.22.3` | Apache-2.0 |
| `cargo:cesu8@1.1.0` | Apache-2.0 |
| `cargo:dasp_sample@0.11.0` | Apache-2.0 |
| `cargo:dirs-sys@0.4.1` | Apache-2.0 |
| `cargo:dirs-sys@0.5.0` | Apache-2.0 |
| `cargo:dirs@5.0.1` | Apache-2.0 |
| `cargo:dirs@6.0.0` | Apache-2.0 |
| `cargo:dispatch2@0.3.0` | Zlib |
| `cargo:dunce@1.0.5` | Apache-2.0, MIT-0 |
| `cargo:ident_case@1.0.1` | Apache-2.0 |
| `cargo:memchr@2.7.6` | Unlicense |
| `cargo:objc2-app-kit@0.3.2` | Zlib |
| `cargo:objc2-core-foundation@0.3.2` | Zlib |
| `cargo:objc2-core-graphics@0.3.2` | Zlib |
| `cargo:objc2-exception-helper@0.1.1` | Zlib |
| `cargo:objc2-io-surface@0.3.2` | Zlib |
| `cargo:objc2-osa-kit@0.3.2` | Zlib |
| `cargo:objc2-quartz-core@0.3.2` | Zlib |
| `cargo:objc2-ui-kit@0.3.2` | Zlib |
| `cargo:objc2-web-kit@0.3.2` | Zlib |
| `cargo:same-file@1.0.6` | Unlicense |
| `cargo:shlex@1.3.0` | Apache-2.0 |
| `cargo:walkdir@2.5.0` | Unlicense |
| `cargo:wasip2@1.0.2+wasi-0.2.9` | LLVM-exception |
| `cargo:winapi-util@0.1.11` | Unlicense |
| `native:gmp@python:av@17.1.0` | GPL-2.0-or-later |
| `native:libunistring@python:av@17.1.0` | GPL-2.0-or-later |
| `native:mingw-winpthread@python:av@17.1.0` | MIT |
| `native:nettle-hogweed@python:av@17.1.0` | GPL-2.0-or-later |
| `python:altgraph@0.17.5` | MIT |
| `python:cffi@2.0.0` | MIT |
| `python:niquests@3.17.0` | Apache-2.0 |
| `python:pywin32@311` | PSF-2.0 |
| `python:regex@2026.1.15` | CNRI-Python |
| `python:requests@2.34.2` | Apache-2.0 |
| `python:sqlcipher3@0.6.2` | MIT |
| `python:sqlcipher3@0.6.2/wheel-linux` | MIT |
| `python:sqlcipher3@0.6.2/wheel-macos` | MIT |
| `python:sqlcipher3@0.6.2/wheel-windows` | MIT |
| `python:tqdm@4.67.1` | MPL-2.0 |

L’audit final ne trouve **aucune licence déclarée non couverte**. Tous les textes d’origine et leurs attributions restent rattachés : **2 249 notices antérieures conservées**, hors les deux modèles natifs génériques explicitement remplacés. Cette reconnaissance de clauses est un garde-fou de contenu ; elle ne tranche pas les droits des composants composites ni les obligations de fourniture des sources.

## Actions de CI

Les **20 appels restants** de `.github/workflows/ci.yml` sont épinglés, avec version en commentaire. Cela complète les deux appels déjà corrigés au tour précédent, et les deux actions Rust déjà épinglées, soit **24 appels externes** dans ce workflow. Les six références ont été vérifiées sur les dépôts officiels, en lecture seule : résolution des tags avec `git ls-remote --tags`, et commit officiel de rust-toolchain. Les commentaires des deux actions Rust, déjà épinglées, sont précisés aussi dans release.yml.

| Action | Version | Commit |
| --- | --- | --- |
| [actions/checkout](https://github.com/actions/checkout/releases/tag/v5.1.0) | v5.1.0 | `fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09` |
| [actions/setup-python](https://github.com/actions/setup-python/releases/tag/v6.3.0) | v6.3.0 | `ece7cb06caefa5fff74198d8649806c4678c61a1` |
| [actions/setup-node](https://github.com/actions/setup-node/releases/tag/v6.5.0) | v6.5.0 | `249970729cb0ef3589644e2896645e5dc5ba9c38` |
| [actions/upload-artifact](https://github.com/actions/upload-artifact/releases/tag/v4.6.2) | v4.6.2 | `ea165f8d65b6e75b540449e92b4886f43607fa02` |
| [Swatinem/rust-cache](https://github.com/Swatinem/rust-cache/releases/tag/v2.9.2) | v2.9.2 | `6323deb102c322ba6fcbdcafc7e3dddab59af2b6` |
| [dtolnay/rust-toolchain](https://github.com/dtolnay/rust-toolchain/commit/6bed0761d98439e5a578e2877258200ad565ba87) | stable, révision du 2026-09-03 | `6bed0761d98439e5a578e2877258200ad565ba87` |

## Vérifications locales et suites

Les preuves de ce tour se trouvent dans `.work-t2/round3/evidence/`. Les données de test, répertoires temporaires, caches uv/npm/XDG et rapports sont placés sous `.work-t2/round3/`. La base est un worktree détaché à `08d0a8a0` sous ce même arbre ; elle réutilise les mêmes dépendances installées. Aucun fichier métier n’a été modifié.

| Contrôle | Résultat |
| --- | --- |
| Scripts du lot et contrats updater/empaquetage | **70 tests réussis, 60 sous-tests réussis**, zéro échec ; dont **50 tests dans scripts/tests**, **34 pour les licences** |
| Contrats de CI existants relus après épinglage | **37 réussis, 9 ignorés**, zéro échec |
| Backend autonome `src/backend/tests/` | **182 réussis, 4 xfail**, 186 cas, zéro échec ; 35,142 s |
| Inventaire et rendu | `generate` **0**, `check` **1**, **9 entrées refusées**, **1 326 entrées**, **5 721 633 octets**, rendu déterministe |
| Audit des preuves | **54 archives**, **83 fichiers internes**, **23 URL amont** revérifiés, zéro divergence |
| Workflows YAML | **4** analysés sans erreur, sans affichage de leur contenu |
| actionlint 1.7.7 sans ShellCheck/Pyflakes | **0 diagnostic**, code **0**, sur HEAD et base |
| actionlint avec ShellCheck, Pyflakes désactivé | **16 diagnostics**, code **1**, identiques sur HEAD et base après retrait des positions ; aucun nouveau |
| Ruff, scripts et tests modifiés | Code **0** |
| TypeScript `tsc --noEmit` | Code **0** |
| Fins de lignes des nouveaux textes et preuves | **27 fichiers** explicitement en LF |

### Pytest complet, premier passage du tour

**6378 cas : 6355 réussis, 4 échecs, 0 erreurs, 15 ignorés et 4 xfail**, en **1499.409 s** (JUnit), code processus **1**.

- `tests.test_c19_recherche_contenu::test_recherche_absente_16384_fragments_en_moins_d_une_seconde`.
- `tests.test_regression_socle.TestB748ProfilTemporaireSansTrousseau::test_un_data_dir_temporaire_necrit_jamais_dans_le_trousseau`.
- `tests.test_routers_rgpd.TestRGPDAnonymize::test_anonymize_supprime_le_dossier_par_le_chemin_canonique`.
- `tests.test_workflow_linux_harnais::test_le_backend_autonome_linux_garde_ses_bornes_et_son_rapport`.

### Pytest complet, base 08d0a8a0

**6378 cas : 6349 réussis, 10 échecs, 0 erreurs, 15 ignorés et 4 xfail**, en **3834.048 s** (JUnit), code processus **1**.

- `tests.test_c20f_docx_professionnels::test_b1324_dix_budgets_apres_correctif[8-400-6]`.
- `tests.test_c20f_docx_professionnels::test_b1324_dix_budgets_apres_correctif[12-250-8]`.
- `tests.test_c20f_docx_professionnels::test_b1324_dix_budgets_apres_correctif[1-3125-8]`.
- `tests.test_c20f_docx_professionnels::test_b1324_dix_budgets_apres_correctif[5-1000-5]`.
- `tests.test_c20f_docx_professionnels::test_b1324_dix_budgets_apres_correctif[1-24999-1]`.
- `tests.test_c20f_docx_professionnels::test_b1324_dix_budgets_apres_correctif[1-25001-1]`.
- `tests.test_c20f_docx_professionnels::test_b1324_dix_budgets_apres_correctif[2-12500-1]`.
- `tests.test_c20f_docx_professionnels::test_b1324_dix_budgets_apres_correctif[2-12501-1]`.
- `tests.test_regression_socle.TestB748ProfilTemporaireSansTrousseau::test_un_data_dir_temporaire_necrit_jamais_dans_le_trousseau`.
- `tests.test_routers_rgpd.TestRGPDAnonymize::test_anonymize_supprime_le_dossier_par_le_chemin_canonique`.

### Pytest complet final après adaptation du contrat de workflow

**6378 cas : 6357 réussis, 2 échecs, 0 erreurs, 15 ignorés et 4 xfail**, en **2049.073 s** (JUnit), code processus **1**.

- `tests.test_regression_socle.TestB748ProfilTemporaireSansTrousseau::test_un_data_dir_temporaire_necrit_jamais_dans_le_trousseau`.
- `tests.test_routers_rgpd.TestRGPDAnonymize::test_anonymize_supprime_le_dossier_par_le_chemin_canonique`.

### Vitest complet du tour

**3943 tests dans 904 fichiers : 3943 réussis, 0 échecs, 0 ignorés**, code processus **0**, durée du processus **1158.458 s**.


### Vitest complet de la base 08d0a8a0

**3943 tests dans 904 fichiers : 3943 réussis, 0 échecs, 0 ignorés**, code processus **0**, durée du processus **2412.162 s**.


### Interprétation des reprises et comparaison demandée

La suite finale reste en échec sur les cas RGPD et trousseau, également en échec sur la base. Le cas C19 et le contrat de workflow passent dans ce dernier lancement.

Les huit échecs DOCX de la base sont des dépassements du délai de 8 secondes sous un plafond de mémoire de 1 Go. Ils sont listés avec leurs paramètres et n’ont pas été rejoués isolément. Aucun échec de contenu DOCX n’est déduit de ces dépassements de budget.

Le premier passage Python a révélé un contrat qui cherchait encore le tag mobile `actions/upload-artifact@v4`. Sa correction attend le SHA vérifié et ne change ni les assertions de délais ni celle du rapport. Les trois cas de ce fichier passent ensuite. Dans la reprise groupée de six cas, le cas RGPD et le cas du trousseau passent ; le test C19 de performance échoue encore sous la charge des suites de la base (**5 réussites, 1 échec**). Ces reprises ne sont pas présentées comme une suite complète verte.

La comparaison HEAD/base utilise les mêmes commandes, la même concurrence (pytest et Vitest à deux workers exécutés ensemble), les mêmes dépendances et des données neuves propres à chaque arbre. Elle est exécutée successivement sur les deux arbres. La dernière suite Python se déroule ensuite seule, après la correction du contrat de workflow. Les neuf fichiers des cas signalés au deuxième tour sont identiques entre la base et `797ec24e` (empreintes de blobs Git enregistrées). Les versions communes sont Python 3.12.3, pytest 9.0.2, Node 22.23.4 et Vitest 4.0.17. Les durées ne sont donc pas des mesures comparatives de performance. La charge de l’hôte partagé n’est pas contrôlée ; les conclusions portent sur les résultats effectivement observés, avec des conditions de lancement identiques.

Le cas supplémentaire du trousseau, qui passe en reprise isolée, échoue aussi dans la suite complète de la base.

| Échec du deuxième tour | Résultat en suite complète sur la base | Conclusion |
| --- | --- | --- |
| `tests.test_c19_recherche_contenu::test_recherche_absente_16384_fragments_en_moins_d_une_seconde` | passed | Non établi sur la base dans cette comparaison. |
| `tests.test_routers_rgpd.TestRGPDAnonymize::test_anonymize_supprime_le_dossier_par_le_chemin_canonique` | failed | Échec aussi établi sur la base, mêmes options et concurrence. |
| `src/frontend/src/components/memory/ConfirmationSuppressionProjet.p148.test.tsx` — P-148 : la confirmation de suppression, depuis la fenêtre du projet écrit les familles non nulles, omet les autres, et l’annonce dans une région de statut | passed | Non établi sur la base dans cette comparaison. |
| `src/frontend/src/components/onboarding/OnboardingWizard.retourGardeLeService.p111.test.tsx` — P-111 : un retour sur l’étape IA garde le service retenu Claude retenu, puis Retour : Claude reste choisi malgré Ollama | passed | Non établi sur la base dans cette comparaison. |
| `src/frontend/src/components/prototype/CapabilityCenter.da.test.tsx` — Lot 3 DA : typeCapacite classe prompts, les 7 parcours et les vues ; un clic onChoose reste inchangé | passed | Non établi sur la base dans cette comparaison. |
| `src/frontend/src/components/prototype/ConversationCanvasPrototype.paletteDonnees.p016.test.tsx` — P-016 : la palette retrouve un client par son nom P-148 : le projet choisi ouvre sa fenêtre, plus la liste des projets | passed | Non établi sur la base dans cette comparaison. |
| `src/frontend/src/components/prototype/ConversationCanvasPrototype.retirerCapacite.b1378.test.tsx` — B-1378 : retirer une capacité retire sa demande la phrase posée par la capacité part avec elle, le focus revient au champ | passed | Non établi sur la base dans cette comparaison. |
| `src/frontend/src/components/prototype/EmailConversationCard.sansBoite.b1435.test.tsx` — B-1435 : rédaction sans boîte branchée depuis l’établi, « Écrire » sans boîte le dit | passed | Non établi sur la base dans cette comparaison. |
| `src/frontend/src/components/email/wizard/EmailSetupWizard.retourMcp.test.tsx` — EmailSetupWizard : retour arrière avec identifiants détectés (B-329) deux retours depuis la vérification ramènent au choix du mode, jamais à un écran vide | passed | Non établi sur la base dans cette comparaison. |

Commandes reproductibles (les variables de données/cache ci-dessus sont fixées par les lanceurs de preuve) :

```bash
.venv/bin/python -m pytest -q --basetemp="$PWD/.work-t2/round3/head-pytest/pytest-temp" \
  --junitxml=.work-t2/round3/evidence/head-pytest-full.xml
# Depuis src/frontend :
node node_modules/vitest/vitest.mjs run --maxWorkers=2 \
  --reporter=default --reporter=json \
  --outputFile.json="$PWD/../../.work-t2/round3/evidence/head-vitest-full.json"
```

Cargo et PowerShell ne sont pas disponibles ; les signatures, la notarisation/agrafage, les installeurs et mises à jour réels macOS/Windows ne sont pas vérifiés ici. Les limites de signature du moteur Windows onefile et les réserves sur les sources exactes des autres composants GPL/LGPL restent celles des tours précédents. La release reste volontairement bloquée par les neuf attributions non établies.

## Diff, fichiers changés et livraison

`git diff --check 08d0a8a0` retourne **2** : **1 329 espaces finaux**, **12 séparateurs assimilés à des marqueurs de conflit**, **1 espace avant tabulation** et **1 ligne blanche finale**, tous dans `THIRD_PARTY_LICENSES`. Depuis `bd95a87b`, il signale **7 espaces finaux** dans ce même fichier. Les textes amont n’ont pas été nettoyés pour faire taire Git. `git diff --check 08d0a8a0 -- . ':!THIRD_PARTY_LICENSES'` retourne **0** ; aucune exception globale n’a été ajoutée.

- `scripts/third_party_licenses.py` : portée exacte des exemples normatifs, contrôle de chaque licence déclarée, statut amont avec preuves vérifiées, chemin d’archive explicite pour esrecurse.
- `scripts/tests/test_release_licenses.py`, `scripts/tests/test_release_pipeline.py`, `tests/test_workflow_linux_harnais.py` : contre-épreuves et contrats d’actions épinglées.
- `.github/workflows/ci.yml` : les 20 appels encore mobiles ; commentaires de version des deux actions Rust précisés dans ci.yml et release.yml.
- `licenses/attribution-sources.json`, `licenses/overrides.json`, `licenses/native-components.lock.json`, `licenses/inventory.json` et `THIRD_PARTY_LICENSES` : preuves, textes, déclarations natives corrigées et rendu.
- **26 nouveaux fichiers** dans `licenses/supplements/` : 7 conditions partagées, 16 fichiers natifs, LICENSE.md objc2 et 2 licences Rustls Android.
- `docs/SIGNATURE-ET-LICENCES.md` et `docs/rapport-signature-3-2026-10-29.md` : fonctionnement et bilan final.

Commit de correction : `797ec24e` — « Rattacher chaque licence déclarée et prouver les attributions amont ». Commit complémentaire : `dfacebbf` — « Conserver explicitement les réserves lors des compléments de licences ». Le rapport final fait l’objet d’un commit documentaire distinct.

Le présent rapport est également livré à `/home/synoptia/staging/therese-lot4-20261029/rapport-signature-3.md`. Les écritures de travail et tests restent sous l’arbre ; cette copie finale est l’exception expressément demandée. Aucun secret de CI ni jeton n’a été affiché, aucun `rm`, aucune publication ni déclenchement de workflow.

### Liste exhaustive des fichiers de ce tour

```text
.github/workflows/ci.yml
.github/workflows/release.yml
THIRD_PARTY_LICENSES
docs/SIGNATURE-ET-LICENCES.md
docs/rapport-signature-3-2026-10-29.md
licenses/attribution-sources.json
licenses/inventory.json
licenses/native-components.lock.json
licenses/overrides.json
licenses/supplements/Apache-2.0-LLVM.json
licenses/supplements/BSD-3-Clause.json
licenses/supplements/GPL-2.0.json
licenses/supplements/MIT-0.json
licenses/supplements/Python-2.0.json
licenses/supplements/SVT-AV1-4.1.0-LICENSE.md.json
licenses/supplements/Unlicense.json
licenses/supplements/Zlib.json
licenses/supplements/libXau-1.0.9-COPYING.json
licenses/supplements/libdrm-2.4.115-include-drm-drm.h.json
licenses/supplements/libdrm-2.4.115-include-drm-drm_fourcc.h.json
licenses/supplements/libdrm-2.4.115-include-drm-drm_mode.h.json
licenses/supplements/libdrm-2.4.115-libdrm_macros.h.json
licenses/supplements/libdrm-2.4.115-libsync.h.json
licenses/supplements/libdrm-2.4.115-util_math.h.json
licenses/supplements/libdrm-2.4.115-xf86drm.c.json
licenses/supplements/libdrm-2.4.115-xf86drm.h.json
licenses/supplements/libdrm-2.4.115-xf86drmHash.c.json
licenses/supplements/libdrm-2.4.115-xf86drmMode.c.json
licenses/supplements/libdrm-2.4.115-xf86drmMode.h.json
licenses/supplements/libdrm-2.4.115-xf86drmRandom.c.json
licenses/supplements/libdrm-2.4.115-xf86drmSL.c.json
licenses/supplements/libxcb-1.13.1-COPYING.json
licenses/supplements/objc2-7b1abfd-LICENSE.json
licenses/supplements/rustls-platform-verifier-android-0.1.1-LICENSE-APACHE.json
licenses/supplements/rustls-platform-verifier-android-0.1.1-LICENSE-MIT.json
scripts/tests/test_release_licenses.py
scripts/tests/test_release_pipeline.py
scripts/third_party_licenses.py
tests/test_workflow_linux_harnais.py
```
