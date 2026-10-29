# THÉRÈSE — Signature et licences tierces, cinquième tour

29 octobre 2026. Branche `coco/therese-signature-20261029`, départ exact
`da37a7683a1db178093a0bbaa35e8ff462fee65c`, arbre de travail demandé conservé.
Consignes et `relecture-signature-4.md` relues. Les quatre constats sont corrigés,
avec tests rouges avant correction. Aucun changement des workflows à ce tour.

Le corpus validé au quatrième tour est conservé : 1 326 entrées d'inventaire,
27 composants, 39 ressources de sources/recettes. Aucune version ni archive
amont n'a été remplacée. Les sources ont été reprises du cache local validé,
sans téléchargement supplémentaire. Aucun push, déclenchement de CI ou
publication. Aucune suite complète du dépôt n'a été lancée.

## Archives indispensables

Chaque composant déclare désormais `required_supporting_sources`. Le code
impose également les rattachements nécessaires aux identités des paquets
livrés : vider la liste, supprimer une référence ou la remplacer par une
référence inconnue ne permet pas de contourner le contrôle. Les **24 références
obligatoires** relient 13 composants aux cinq archives de soutien.

Le retrait isolé de `pyav-ffmpeg-8.1.1-2-build-tree.tar.gz`, sans changement des
27 composants, recettes, preuves ou inventaire, est refusé par
`verify_manifest()` et la véritable `main()` en mode `verifier`. Le test ne
substitue que la lecture du manifeste, en mémoire. La même contre-épreuve est
reprise pour `mingw-w64-libiconv-1.19-1.src.tar.zst`.

`assemble()` relit et contrôle l'inventaire, les verrous et le manifeste avant
le premier téléchargement ou la première écriture, même pour un appel direct.
La CLI refuse également le manifeste avant d'appeler l'assembleur. En cas
d'échec d'une ressource, elle ne produit pas les documents finaux d'un corpus
annoncé comme complet. Les fichiers déjà téléchargés peuvent servir de cache.

Revue des 27 composants, avec les recettes et correctifs conservés :

| Composant | Sources, correctifs et recettes indispensables |
| --- | --- |
| alsa-lib | Source amont ; arbres PyAV et pyav-ffmpeg obligatoires ; sélection PyAV, `pkg.py`, `build-ffmpeg.py` et infrastructure de construction inclus. |
| ffmpeg | Mêmes deux arbres ; notamment `patches/ffmpeg.patch`. |
| gmp | Mêmes deux arbres ; notamment `patches/gmp.patch`. |
| libunistring | Mêmes deux arbres et recettes de construction. |
| nettle-hogweed | Mêmes deux arbres et recettes de construction. |
| gnutls | Mêmes deux arbres et recettes de construction. |
| lame | Mêmes deux arbres ; notamment `patches/lame.patch`. |
| x264 | Mêmes deux arbres ; paramètres et recette de compilation conservés. |
| x265 | Mêmes deux arbres ; paramètres, recette et traitement des archives statiques conservés. |
| libiconv | Mêmes deux arbres, plus source MSYS2 obligatoire : `PKGBUILD`, `iconv.pc`, `0003-add-cp65001-as-utf8-alias.patch`, `0002-fix-cr-for-awk-in-configure.all.patch`, `fix-pointer-buf.patch`. |
| espeak-ng | Source au commit fixé ; arbre Piper obligatoire, avec CMake et recette Python. |
| piper-tts | Sdist verrouillé 1.4.2 ; arbre Piper obligatoire, avec CMake, recette Python et scripts. |
| recurring-ical-events | Sdist intégral de uv.lock ; aucun correctif externe identifié. |
| x-wr-timezone | Sdist intégral de uv.lock ; aucun correctif externe identifié. |
| certifi | Sdist intégral de uv.lock ; aucun correctif externe identifié. |
| pathspec | Sdist intégral de uv.lock ; aucun correctif externe identifié. |
| tqdm | Sdist intégral de uv.lock ; aucun correctif externe identifié. |
| grpcio | Sdist intégral de uv.lock ; sources et construction incluses. |
| cssparser-macros 0.6.1 | Archive Cargo intégrale, manifestes et sources inclus. |
| cssparser 0.29.6 | Archive Cargo intégrale, manifestes et sources inclus. |
| dtoa-short 0.3.5 | Archive Cargo intégrale, manifestes et sources inclus. |
| option-ext 0.2.0 | Archive Cargo intégrale, manifestes et sources inclus. |
| selectors 0.24.0 | Archive Cargo intégrale, manifestes et sources inclus. |
| axe-core | Dépôt complet au commit établi : `Gruntfile.js`, infrastructure de construction et `patches/colorjs.io+0.4.3.patch` inclus. Référence obligatoire à la recette embarquée. |
| lightningcss | Dépôt complet au commit établi : `scripts/build-npm.js`, manifestes Cargo, scripts et correctifs npm inclus. Références obligatoires aux recettes embarquées. |
| adodbapi (pywin32) | Dépôt pywin32 complet au commit b311 ; copie épinglée de `setup.py`, référencée obligatoirement. |
| autocommand (setuptools) | Source autocommand ; source intégrale setuptools obligatoire pour conserver le code vendu et ses adaptations, avec références à `pyproject.toml` et `setup.py`. |

Les listes de soutien explicitement vides concernent les composants dont les
recettes/correctifs sont déjà dans l'archive source. Elles ne suppriment pas
l'obligation de fournir cette archive. Les trois correctifs FFmpeg/GMP/LAME,
`scripts/cibuildpkg.py`, et les cinq membres MSYS2 ci-dessus ont été relus et
empreintés depuis les archives locales : neuf membres consignés dans
`.work-t2/round5/evidence/required-members-audit.json`.

## Exception d'absence de titulaire et listes d'auteurs

`attribution_evidence.py` contient une liste fermée des neuf triplets autorisés :
`objc2-app-kit`, `objc2-core-foundation`, `objc2-core-graphics`,
`objc2-foundation`, `objc2-io-surface`, `objc2-osa-kit`, `objc2-quartz-core`,
`objc2-ui-kit`, `objc2-web-kit`, tous en **0.3.2**, au commit
`7b1abfd750a2cacaea71d6a56ecfb83cb7de560b`.

Pour chacun, l'empreinte de référence de l'arbre est imposée par le code :
`a6685e9b30da4c2b9ed807e8344d7248447daf1d5ab5b7af4fa3755545f96a4d`.
Recalculer une preuve sur un autre arbre ne peut pas modifier cette référence.
L'identité Cargo est comparée aux noms et versions de `Cargo.toml` et
`Cargo.toml.orig`. Dans les vraies crates, `version.workspace = true` est résolu
avec la version du workspace de l'arbre vérifié. Le champ d'auteurs du workspace
n'est toujours pas transformé en titulaire des crates.

La contre-épreuve `cargo:example@1` avec une preuve bien formée est maintenant
refusée. Les tests du scan autorisent explicitement leur fixture synthétique
dans une politique remplacée uniquement pendant ces tests ; le test du refus
d'`example` et celui des neuf vraies preuves utilisent la politique réelle.
Cela évite que le nouveau filtre rende les tests d'auteurs artificiellement verts.

Le scan reconnaît les fichiers `AUTHORS`, `CONTRIBUTORS`, `MAINTAINERS` (avec
extensions), les titres seuls suivis de noms et les commentaires `///`, `//!`,
`#`, `*`. Les fixtures exactes `AUTHORS` contenant `Authors\nAlice\n` et
`/// Authors: Alice` sont reprises dans l'archive et dans la portée de la crate
dans l'arbre. Les cas ne contenant que les noms dans les fichiers dédiés sont
également couverts. Les mentions de contributeurs/mainteneurs dans la prose
restent distinguées des présentations nominatives.

Les neuf preuves ont été régénérées à partir des mêmes octets et vérifiées :
**1 433 fichiers de crates, 1 797 contenus de l'arbre dont 191 liens**.
Le relevé de l'arbre comporte maintenant **13 occurrences brutes**, contre 11
avec les anciens motifs ; les deux occurrences supplémentaires sont de la
prose. Toujours **zéro occurrence attribuant l'une des neuf crates**.
L'inventaire ne change que d'empreinte des verrous ; les notices régénérées ne
changent que leur empreinte globale, sans modification des textes de licence.

## Version et source

Le contrôle lit directement les sdists de `uv.lock` et les sources de
`Cargo.lock`. Pour les **12 composants directement rattachables** (sept Python,
cinq Cargo), URL, SHA-256 et version doivent correspondre au verrou lui-même.
Le test qui modifie simultanément l'inventaire et la source confirme que le
comparateur ne se contente pas des déclarations de l'inventaire. La source de
soutien setuptools est elle aussi comparée directement à uv.lock.

La mutation exacte de la relecture — Piper déclaré en `1.4.1`, avec l'objet
source de recurring-ical-events — est refusée. Les substitutions isolées d'URL,
de SHA-256 et de version sont testées séparément pour Piper et une crate Cargo.

Pour les **15 autres composants**, `evidence_refs` et `recipe_refs` sont
obligatoires, non vides, et doivent se résoudre. `evidence_files` vide est refusé.
Les `source_bindings` de la preuve empreintée fixent, pour les 27 composants,
version, paquets couverts, source, recettes et références de soutien. Une recette
externe reste contrôlée contre sa copie locale et son commit ; une recette dans
une archive source est identifiée par ressource, chemin de membre et SHA-256.
L'assembleur vérifie réellement les cinq membres de recettes embarquées
d'axe-core, lightningcss et setuptools, sans extraction ni exécution.

Ces gardes conservent les rapprochements de versions déjà revus. Ils ne sont
pas présentés comme une reconstruction automatique des binaires ou une
authentification indépendante de toute déclaration dans une nouvelle preuve.
Une future mise à jour exige une nouvelle revue des preuves et dépendances.

## Tests rouges et vérifications finales

Les journaux sont dans `.work-t2/round5/evidence/`.

| Garde | Rouge avant correction |
| --- | --- |
| Archives obligatoires | Retraits FFmpeg/libiconv acceptés ; références absentes ou remplacées acceptées. Premier passage : 3 tests, 5 échecs et 2 erreurs après atteinte du dossier simulé par l'ancien assembleur. Le test final refuse explicitement la première écriture. |
| Listes d'auteurs | 1 test, 16 sous-cas en échec sur les présentations ordinaires ignorées. |
| Exception bornée et identité | 10 tests, 6 échecs : paquet non autorisé, quatre discordances nom/version, arbre remplacé avec preuve recalculée. |
| Version/source/preuves | 4 tests, 14 échecs : substitution Piper, preuve vide, six mutations isolées et six références absentes/vides/inconnues. |
| Recettes embarquées | 1 test, 2 sous-cas en échec : membre absent ou empreinte différente acceptés. |

Un rejeu des trois tests finaux d'archives sur le code et le manifeste de
`da37a768`, chargés en mémoire, confirme également les refus absents dans la
base. Il conserve la preuve de version de cette base en mémoire ; il ne modifie
pas l'arbre courant et ne télécharge rien (`red-support-base-replay.txt`).
Ce rejeu donne **3 tests, 7 échecs, zéro erreur**, comme attendu sur l'ancien garde.

Résultat final des seuls tests des scripts : **83 tests, 175 sous-tests réussis,
zéro échec, erreur ou test ignoré**. Le résultat détaillé est dans
`scripts-tests.json` et `scripts-tests-final.txt`.

| Module | Tests |
| --- | ---: |
| `test_attribution_evidence` | 12 |
| `test_copyleft_sources` | 19 |
| `test_release_licenses` | 35 |
| `test_release_pipeline` | 8 |
| `test_macos_signing` | 5 |
| `test_embedded_macos` | 2 |
| `test_cpu_torch` | 1 |
| `test_packaged_licenses` | 1 |

Les tests couvrent aussi le retrait individuel de chacune des **24 références
obligatoires** et de chacune des **cinq archives de soutien**, ainsi que le
refus d'assemblage avant écriture/téléchargement pour FFmpeg et libiconv.

| Commande / contrôle | Résultat |
| --- | --- |
| `third_party_licenses.py generate`, puis `check` | Codes 0 ; 1 326 entrées, **5 724 461 octets** ; titre non provisoire. |
| `copyleft_sources.py verifier` | Code 0 ; 27 composants, aucune source manquante. |
| `copyleft_sources.py assembler .work-t2/round5/sources-copyleft` | Une seule exécution réelle finale ; code 0 ; 39 ressources vérifiées. |
| Ruff sur les deux scripts et leurs tests | Code 0. |
| `git diff --check` du tour | Code 0 ; aucun diagnostic nouveau. |
| actionlint 1.7.7, sans ShellCheck ni Pyflakes, sur ci.yml et release.yml | Code 0, zéro diagnostic pour l'arbre courant comme pour `08d0a8a0`. |
| actionlint avec ShellCheck, Pyflakes désactivé, mêmes deux workflows | Code 1, **16 diagnostics** pour l'arbre courant comme pour `08d0a8a0` ; messages identiques après retrait des positions des workflows. |

Aucune suite complète pytest/Vitest ni exécution de CI. Les tests n'ont pas
exécuté les recettes amont ni reconstruit les roues.

## Assemblage final

Dossier confirmé ignoré par Git : `.work-t2/round5/sources-copyleft/`.
Les 39 ressources ont été préchargées depuis le corpus local du quatrième tour,
empreintes vérifiées, puis toutes revérifiées par la vraie commande `assembler`.
Le manifeste assemblé est identique octet pour octet au manifeste versionné ;
la preuve est également identique et toutes les ressources concordent avec
leur SHA-256.

- **32 archives et 7 recettes**, soit **39 ressources**, **104 493 917 octets**.
- Avec manifeste, preuve et LISEZMOI : **42 fichiers**, **104 674 242 octets**.
- SHA-256 du manifeste assemblé :
  `37865d575dd21c63d86cf1f0ab3ae2a731b786648f91457b1b5d536c4e3047f6`.
- Mesures : `.work-t2/round5/evidence/assembly-summary.json`.

## Fichiers et limites

Fichiers modifiés : `scripts/copyleft_sources.py`,
`scripts/attribution_evidence.py`, leurs deux modules de tests,
`licenses/copyleft-sources.json`, `licenses/copyleft-version-evidence.json`,
`licenses/attribution-sources.json`, l'empreinte dans `licenses/inventory.json`,
`THIRD_PARTY_LICENSES`, `docs/SIGNATURE-ET-LICENCES.md`, et le présent rapport.
Les archives objc2 et les sept copies de recettes amont sont inchangées.

Les conclusions du quatrième tour sur les licences et exclusions restent
inchangées. Les limites déjà déclarées subsistent : signatures et notarisation
à exercer sur macOS/Windows, reliaison/remplacement LGPL dans le moteur
onefile, conservation effective des pièces jointes, absence de reconstruction
comparative des roues, modèles de voix hors des verrous.

Le rapport est versionné ici et copié à
`/home/synoptia/staging/therese-lot4-20261029/rapport-signature-5.md`, seule
écriture hors de l'arbre expressément demandée. Les journaux et le corpus sont
sous `.work-t2/round5/` ; `TMPDIR` y dirige les temporaires des tests. Aucun `rm`,
push, déclenchement de CI ou publication n'a été effectué.
