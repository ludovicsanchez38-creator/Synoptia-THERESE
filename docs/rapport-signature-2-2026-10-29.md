# Lot T2 — Signature et licences, deuxième tour — 29 octobre 2026

Branche : `coco/therese-signature-20261029`. Base commune : `08d0a8a0`.
Départ de ce tour : `12885802`, arbre propre. Aucun push, aucune CI déclenchée.

**Les trois défauts de contrôle sont corrigés ; la diffusion reste refusée.**
Douze des treize attributions visées sont retrouvées dans les archives
verrouillées. Celle de `rustls-platform-verifier-android 0.1.1` n'y figure pas.
`THIRD_PARTY_LICENSES` commence donc par **PROVISOIRE — DIFFUSION REFUSÉE**.
Le contrôle de release retourne **1**, sans possibilité de confondre fraîcheur
et complétude. Le contrôle renforcé révèle également des lacunes préexistantes
hors des treize entrées : **25 entrées bloquent actuellement la release**.
Ce rapport ne conclut pas à la validation juridique de la redistribution.

## P1 : attributions propres aux versions

Le cache `.work-t2/cache/licenses` a suffi aux recherches de ce tour. Aucun
accès réseau pour les licences, aucune extraction sur disque, aucun code de
paquet exécuté. Les empreintes SHA-256/SRI des archives sont vérifiées avant
lecture. Une seconde passe vérifie **28 archives distinctes et 38 fichiers
internes** utilisés comme preuves, sans modifier le cache.

Les sources, chemins internes, empreintes et modes d'extraction sont conservés
dans `licenses/attribution-sources.json`. Les textes complémentaires sont dans
`licenses/supplements/`, avec leur SHA-256 dans `licenses/overrides.json`.
Ces fichiers font partie de l'empreinte globale et sont forcés en LF.

| Entrée initialement générique | Attribution retrouvée dans l'archive verrouillée |
| --- | --- |
| `convert_case 0.4.0` | David Purdum, `Cargo.toml: package.authors` |
| `dispatch 0.2.0` | Steven Sheldon, `Cargo.toml: package.authors` |
| `fxhash 0.2.1` | cbreeden dans les auteurs ; copyright 2015 The Rust Project Developers dans `lib.rs` |
| `mac 0.1.1` | Jonathan Reem, `Cargo.toml: package.authors` |
| `r-efi 5.3.0` | AUTHORS intégral : Red Hat 2017–2023, Microsoft 2019–2023, David Rheinsberg 2022–2023, liste des contributeurs et conditions MIT |
| `rustls-platform-verifier-android 0.1.1` | **Introuvable** : Cargo, sources, POM et contenu de l'AAR examinés ; `attribution_missing: true` |
| `sigchld 0.2.4` | Jack O'Connor, `Cargo.toml: package.authors` |
| `tao-macros 0.1.3` | Tauri Programme within The Commons Conservancy, `Cargo.toml: package.authors` |
| `winapi-i686-pc-windows-gnu 0.4.0` | Peter Atashian dans les auteurs ; copyrights 2016 et 2016–2018 winapi-rs developers dans les sources |
| `winapi-x86_64-pc-windows-gnu 0.4.0` | Mêmes attributions, vérifiées séparément dans cette archive |
| `imurmurhash 0.1.4` | Copyright 2013 Gary Court, Jens Taylor ; licence MIT complète dans README |
| `keyv 4.5.4` | Jared Wray, `package.json: author` |
| `stackback 0.0.2` | Roman Shtylman dans les métadonnées ; copyright 2012 the V8 project authors et bloc BSD de `formatstack.js`, conservé |

Une métadonnée auteur est présentée comme telle : elle n'est pas transformée
en une déclaration de titularité, et aucune année de copyright n'est inventée.
La ligne générique du modèle MIT est retirée du texte partagé ; les attributions
retrouvées sont explicitement référencées par chaque entrée avec ce texte.

Les **25 blocages** sont :

- Dix attributions non établies : `rustls-platform-verifier-android 0.1.1` et
  les neuf crates `objc2-app-kit`, `objc2-core-foundation`, `objc2-core-graphics`,
  `objc2-foundation`, `objc2-io-surface`, `objc2-osa-kit`, `objc2-quartz-core`,
  `objc2-ui-kit`, `objc2-web-kit`, toutes en `0.3.2`.
- Deux suppléments natifs encore génériques : `libXau-libxcb-libdrm` et
  `svt-av1`, rattachés à `python:av@17.1.0`.
- Quatre notices BSD amont contenant encore un champ générique dans la clause
  de responsabilité : `eslint-scope 8.4.0`, `esrecurse 4.3.0`, `estraverse 5.3.0`,
  `esutils 2.0.3`. Leurs copyrights nommés ne sont pas effacés.
- Neuf entrées Python avec des champs génériques amont, y compris dans des
  sous-composants : `caldav 2.2.3`, `jaraco-context 6.1.0`,
  `jaraco-functools 4.4.0`, `keyring 25.7.0`, `setuptools 84.2.1`, `zipp 3.23.0`,
  `torch 2.9.1` et ses deux roues CPU Linux et Windows.

Les exemples pédagogiques des annexes normatives Apache, GNU et FreeType sont
reconnus séparément ; leurs textes ne sont pas modifiés. Un test interdit qu'une
annexe fasse ignorer une autre attribution générique placée après la licence.
Les réserves de rapprochement des **22 suppléments natifs** avec les binaires
et recettes exacts subsistent ; leur présence n'est pas une validation de redistribution.

## P2 : conditions complètes et refus des simples renvois

Les notices de `siphasher 0.3.11` et `1.0.1` référencent maintenant les textes
complets MIT et Apache-2.0. Les attributions Rust Project Developers et Frank
Denis, avec leurs années respectives, sont conservées. `rsa 4.9.1` référence le
texte Apache-2.0 complet et conserve l'attribution Sybren A. Stüvel. Ces trois
notices originales ont été comparées aux archives verrouillées : identiques
après la normalisation LF et des extrémités déjà pratiquée par le collecteur.

Le contrôle examine des clauses de licence, indépendamment du nom du fichier.
Il refuse un COPYING fait d'un renvoi, un LICENSE contenant TODO, même accolé
à des conditions complètes, et un copyright limité à une attribution.
À l'inverse, un AUTHORS contenant une MIT complète est accepté.
Les reconnaissances de clauses restent des garde-fous de contenu, pas un audit
juridique exhaustif de chaque notice composite.

Ce contrôle révèle **27 entrées** autrefois acceptées sans conditions reconnues,
dont les trois citées par la relecture. Toutes reçoivent des conditions
complémentaires : famille objc2/block2/dispatch2, six plugins Tauri, format,
natural-compare, certifi et exception GCC. Les notices et attributions
existantes sont conservées. Les textes GPL-3 auxquels renvoient quatre notices
LGPL-3 sont aussi joints explicitement. Les textes communs restent dédupliqués
par SHA-256 dans le document livré.

`refresh` applique désormais les suppléments même si la collecte trouve déjà
une notice. Une collecte sans conditions complètes échoue avant de remplacer
l'inventaire. `generate` produit le document provisoire ; `check` le refuse.
Il vérifie aussi les empreintes des suppléments locaux et leur présence exacte
dans l'inventaire. Cinq textes contenant des espaces ou séparateurs amont sont stockés en
chaînes JSON afin de préserver leur contenu sans étendre l'exception Git.

## P2 : huit appels d'actions épinglés

Les deux appels du job `licences-signature` de `ci.yml`, puis les six appels
signalés de `release.yml`, sont épinglés. Chaque ligne porte la version en
commentaire. Les autres jobs historiques de `ci.yml` restent hors de cette
harmonisation demandée ; toutes les actions externes de `release.yml` ont une
empreinte complète, y compris celles déjà épinglées au premier tour.

| Action | Version | Commit vérifié dans le dépôt officiel |
| --- | --- | --- |
| [actions/checkout](https://github.com/actions/checkout/releases/tag/v5.1.0) | v5.1.0 | `fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09` |
| [actions/setup-python](https://github.com/actions/setup-python/releases/tag/v6.3.0) | v6.3.0 | `ece7cb06caefa5fff74198d8649806c4678c61a1` |
| [actions/setup-node](https://github.com/actions/setup-node/releases/tag/v6.5.0) | v6.5.0 | `249970729cb0ef3589644e2896645e5dc5ba9c38` |
| [actions/upload-artifact](https://github.com/actions/upload-artifact/releases/tag/v4.6.2) | v4.6.2 | `ea165f8d65b6e75b540449e92b4886f43607fa02` |

Vérification en lecture seule par `git ls-remote --tags` contre chacun des quatre
dépôts officiels : correspondance exacte du tag et de l'empreinte retenue.
Preuve : `.work-t2/evidence/t2-round2-action-pins.json`. Aucun appel de publication
ou de déclenchement de workflow. Les tests contrôlent les SHA complets et les
commentaires de version dans le périmètre demandé.

## Contrôles locaux et suites complètes

Les tests rouges ont précédé les corrections : le premier passage affiche
exactement **16 échecs, 17 réussites et 7 sous-tests réussis** dans pytest
(`t2-round2-red.xml`). Ce total inclut les contre-épreuves sur les trois paquets
et les huit appels d'actions. Deux autres contre-épreuves ont d'abord échoué :
attribution générique après une annexe et conservation des espaces d'un texte
sérialisé. Elles passent après correction.

| Contrôle final | Résultat |
| --- | --- |
| Scripts du lot + contrats updater/empaquetage ciblés | **55 tests réussis, 18 sous-tests réussis**, zéro échec ; 38 des 55 tests sont dans `scripts/tests`, dont 22 pour le générateur de licences |
| Licences | `generate` : code **0** ; `check` : code **1**, refus attendu des 25 entrées provisoires |
| Cohérence indépendante de l'inventaire et du fichier généré | **1 326 entrées**, **5 682 256 octets** ; couverture et empreintes cohérentes, octets identiques au rendu déterministe |
| Workflows YAML | **4 parsés**, aucune erreur |
| actionlint 1.7.7 sans ShellCheck/Pyflakes | Code **0**, **0 diagnostic** sur les deux workflows modifiés |
| actionlint avec ShellCheck | Code **1**, **16 diagnostics**, les mêmes 16 que sur `08d0a8a0` après normalisation des positions ; aucun nouveau |
| Ruff, script et tests modifiés | Code **0**, aucun diagnostic |
| TypeScript `tsc --noEmit` | Code **0** |

**Pytest complet : 6 378 cas, dont 6 357 réussis, 2 échecs, 15 ignorés et
4 xfail**, en **2 777,206 s** selon le JUnit ; processus terminé avec le code 1.
Les deux échecs sont :

- `tests/test_c19_recherche_contenu.py::test_recherche_absente_16384_fragments_en_moins_d_une_seconde`
  : seuil de performance d'une seconde non tenu dans la suite ;
- `tests/test_routers_rgpd.py::TestRGPDAnonymize::test_anonymize_supprime_le_dossier_par_le_chemin_canonique`
  : assertion de purge RGPD, déjà signalée dans le premier rapport.

**Reprise isolée des deux cas : 2 réussis, zéro échec**, en **1,971 s**,
avec données et répertoire temporaire neufs dans l'arbre, sans changement du
code métier ou des tests. Ce résultat ne transforme pas la suite complète
en une suite verte et ne prouve pas que les interactions de suite sont résolues.
Preuves : `t2-round2-pytest-full.xml`, `t2-round2-pytest-summary.json` et
`t2-round2-pytest-recheck.xml`.

**Vitest complet : 3 943 tests dans 904 fichiers, dont 3 936 réussis et
7 échecs, aucun ignoré**, en **2 388,65 s**. Les sept échecs sont des assertions
ou recherches d'éléments d'interface, sans dépassement du délai de test.
Ils touchent les fichiers suivants :

- `ConfirmationSuppressionProjet.p148.test.tsx` ;
- `OnboardingWizard.retourGardeLeService.p111.test.tsx` ;
- `CapabilityCenter.da.test.tsx` ;
- `ConversationCanvasPrototype.paletteDonnees.p016.test.tsx` ;
- `ConversationCanvasPrototype.retirerCapacite.b1378.test.tsx` ;
- `EmailConversationCard.sansBoite.b1435.test.tsx` ;
- `EmailSetupWizard.retourMcp.test.tsx`.

**Reprise des sept fichiers entiers : 33 tests réussis, aucun échec ni ignoré**,
en **39,31 s**, avec `--maxWorkers=1 --testTimeout=20000`, sans changement du code ou des tests.
La suite complète n'est donc pas présentée comme verte : ses sept échecs ne se
reproduisent pas dans cette reprise. Les noms complets des cas et la nature des
échecs figurent dans `t2-round2-vitest-summary.json` ; le résultat de reprise est
conservé dans `t2-round2-vitest-recheck.json`.

Les commandes de suites sont lancées avec fichiers temporaires, données,
caches npm/uv/XDG et rapports dans `.work-t2/` sous l'arbre, en réutilisant les
dépendances installées au premier tour. Le frontend est lancé depuis
`src/frontend`, pour respecter les lectures relatives des tests.

```bash
TMPDIR="$PWD/.work-t2/round2/tmp" .venv/bin/python -m pytest --noconftest \
  scripts/tests tests/test_b1111_manifeste_updater.py \
  tests/test_sentinelles_structure.py::TestEmpaquetage::test_le_paquet_linux_embarque_les_bibliotheques_du_backend \
  -q --basetemp="$PWD/.work-t2/round2/tmp/targeted-commit" \
  --junitxml=.work-t2/evidence/t2-round2-targeted-commit.xml
# Suite Python complète, avec THERESE_DATA_DIR et caches redirigés dans l'arbre :
.venv/bin/python -m pytest -q \
  --basetemp="$PWD/.work-t2/round2/tmp/pytest-full" \
  --junitxml=.work-t2/evidence/t2-round2-pytest-full.xml
# Depuis src/frontend, avec TMPDIR et npm_config_cache dans l'arbre :
node node_modules/vitest/vitest.mjs run --maxWorkers=2 \
  --reporter=default --reporter=json \
  --outputFile.json="$PWD/../../.work-t2/evidence/t2-round2-vitest-full.json"
```

Preuves conservées dans `.work-t2/evidence/t2-round2-*` : journaux et JUnit,
JSON Vitest, vérification des archives, résolution des tags, comparaison
ShellCheck, résultats du générateur et contrôles Git. Elles restent ignorées
par Git ; les textes et preuves d'attribution nécessaires au contrôle sont,
eux, versionnés.

## Rectificatif de git diff --check

L'affirmation du premier rapport « diff --check réussi » était trop large.
Elle est rectifiée dans sa copie versionnée. Le fichier historique du dossier
parent reste en lecture seule ; le présent rapport en constitue aussi l'erratum.

Sur le diff final depuis `08d0a8a0`, `git diff --check 08d0a8a0` retourne **2**
et signale exactement :

- **1 323** lignes avec espaces finaux (`trailing whitespace.`) ;
- **12** séparateurs interprétés comme marqueurs de conflit (`leftover conflict marker`) ;
- **1** espace avant tabulation dans l'indentation (`space before tab in indent.`) ;
- **1** ligne blanche finale (`new blank line at EOF.`).

Tous ces diagnostics sont dans **`THIRD_PARTY_LICENSES`**. Les espaces et
séparateurs viennent des textes amont conservés, dont des titres soulignés par
des signes `=` ; les 12 diagnostics de marqueur ne démontrent pas des conflits
Git non résolus. Le séparateur de fin du rendu produit la ligne blanche finale.
Les licences n'ont pas été nettoyées globalement pour faire taire Git.

Le seul contrôle avec exception est :

```bash
git diff --check 08d0a8a0 -- . ':!THIRD_PARTY_LICENSES'
```

Il retourne **0**, aucun diagnostic, y compris pour tous les nouveaux fichiers
versionnés. Aucune modification globale de `core.whitespace`, aucune exclusion
du répertoire `licenses/` ou du reste du dépôt. Les cinq copies de textes
amont à espaces ou séparateurs ambigus sont sérialisées en JSON sans altération
des textes restitués.

## Fichiers modifiés et limites

- `scripts/third_party_licenses.py` : contrôle des clauses, des attributions,
  des suppléments et du statut provisoire ; application systématique des suppléments.
- `scripts/tests/test_release_licenses.py`, `scripts/tests/test_release_pipeline.py` :
  contre-épreuves et contrats de release.
- `licenses/overrides.json`, `licenses/inventory.json`, `licenses/attribution-sources.json`,
  `licenses/supplements/`, `THIRD_PARTY_LICENSES` : textes, preuves et génération.
- `.gitattributes` : LF des nouveaux fichiers de preuves et textes.
- `.github/workflows/ci.yml`, `.github/workflows/release.yml` : les huit références.
- `docs/SIGNATURE-ET-LICENCES.md`, le rapport du premier tour corrigé et ce rapport.

La signature native, la notarisation/agrafage Apple, les extractions NSIS/MSI
et Authenticode restent à éprouver sur leurs plateformes après résolution des
blocages de notices. La limitation Windows onefile du premier tour subsiste.
Aucune prétention de CI verte ou d'installeur signé vérifié sur ce poste Linux.
Les obligations et réserves GPL/LGPL du premier rapport restent à traiter avec
les sources exactes des binaires ; l'inventaire conservateur n'établit pas à lui
seul quels composants sont embarqués. Aucune valeur de secret ni configuration locale
n'a été affichée. Les écritures de travail et de tests sont dirigées dans l'arbre ;
seul le rapport final demandé est copié dans le dossier parent.

Commit de correction : `72aed20e` — « Compléter les notices, bloquer les
attributions provisoires et épingler les actions ». Le rapport final est livré
dans un commit documentaire séparé sur la même branche. Aucun push.
