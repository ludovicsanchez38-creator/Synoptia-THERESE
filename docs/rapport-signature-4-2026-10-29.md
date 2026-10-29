# Lot T2 — Signature et licences tierces, quatrième tour

29 octobre 2026. Travail repris à `b90ddbed6a9db54450d6178fcf28851a9e352765`, sur
`coco/therese-signature-20261029`, dans l'arbre demandé. Les règles initiales et
la relecture du troisième tour ont été relues. Commit technique local :
**`b82ae680` — « Prouver les attributions absentes et fournir les sources copyleft »**,
puis **`12ce178f` — « Placer les mentions factuelles après les textes de licences »**.

Les neuf entrées objc2 sont désormais acceptées sur preuve d'absence de titulaire
nommé. Le corpus des sources contient **27 composants**, couvrant **41 entrées**
de l'inventaire ; **18 autres entrées** sont écartées individuellement avec leur
raison et les empreintes de leurs notices. **Aucune source exacte recherchée dans
ce périmètre ne reste manquante.** Les gardes des licences et des sources passent.
Cela ne constitue pas une vérification des signatures réelles ni des modalités de
reliaison LGPL dans le moteur onefile.

## Preuves des neuf entrées objc2

Le statut `no-holder-named-upstream` est attribué entrée par entrée dans
`licenses/attribution-sources.json` et `licenses/overrides.json`. Le marqueur
`attribution_missing: true` conserve le fait historique ; il n'est accepté que si
le nouveau statut est accompagné de sa preuve exacte. Toute autre attribution
marquée manquante ou générique reste refusée.

Toutes les archives verrouillées ont été vérifiées par leur SHA-256 Cargo.
Leur `.cargo_vcs_info.json`, lui-même empreinté, désigne le commit
**`7b1abfd750a2cacaea71d6a56ecfb83cb7de560b`**. L'archive de l'arbre complet,
[téléchargée à ce commit](https://codeload.github.com/madsmtm/objc2/tar.gz/7b1abfd750a2cacaea71d6a56ecfb83cb7de560b),
a pour SHA-256 `a6685e9b30da4c2b9ed807e8344d7248447daf1d5ab5b7af4fa3755545f96a4d`.

Le contrôle relit **tous les fichiers**, sans filtre d'extension : 1 433 fichiers
dans les neuf archives et **1 606 fichiers ordinaires + 191 liens symboliques**
dans l'arbre amont, soit 1 797 contenus Git examinés. Les cibles des liens vers
`generated/` font partie de la portée de chaque crate. Les archives complètes,
3 206 472 octets, sont versionnées dans `licenses/evidence/` : le contrôle peut
répéter la recherche hors réseau, sans se fier au seul résultat d'un scan déclaré.

Les motifs consignés comprennent `Copyright`, `©`, `(c)` et `(C)` suivis d'une
année ou d'un nom, `SPDX-FileCopyrightText`, `Authors`, `authors =` et
`authors.workspace =`. Les deux manifestes Cargo de chaque archive sont lus et
contrôlés. Chaque fichier lu porte son SHA-256, et chaque occurrence son chemin,
sa ligne et son texte. Le relevé conserve 11 occurrences brutes dans l'arbre ;
ce ne sont pas onze attributions des crates : elles concernent notamment les
métadonnées du workspace/d'autres crates, le traducteur d'en-têtes, ou de la prose.
Les archives app-kit et foundation contiennent chacune trois occurrences de
`Copyright` dans des identifiants/documentations d'API ; quartz-core contient une
mention en prose des auteurs. **Zéro occurrence attribuant chacune des neuf
crates**, dans l'archive comme dans l'arbre et ses sources générées : les deux
listes `attributing_occurrences` sont vides pour chaque preuve.

| Crate 0.3.2 | Fichiers de l'archive lus | SHA-256 de l'archive verrouillée |
| --- | ---: | --- |
| `objc2-app-kit` | 309 | `d49e936b501e5c5bf01fda3a9452ff86dc3ea98ad5f283e1455153142d97518c` |
| `objc2-core-foundation` | 76 | `2a180dd8642fa45cdb7dd721cd4c11b1cadd4929ce112ebd8b9f5803cc79d536` |
| `objc2-core-graphics` | 61 | `e022c9d066895efa1345f8e33e584b9f958da2fd4cd116792e15e07e4720a807` |
| `objc2-foundation` | 239 | `e3e0adef53c21f888deb4fa59fc59f7eb17404926ee8a6f59f5df0fd7f9f3272` |
| `objc2-io-surface` | 16 | `180788110936d59bab6bd83b6060ffdfffb3b922ba1396b312ae795e1de9d81d` |
| `objc2-osa-kit` | 13 | `f112d1746737b0da274ef79a23aac283376f335f4095a083a267a082f21db0c0` |
| `objc2-quartz-core` | 38 | `96c1358452b371bf9f104e21ec536d37a650eb10f7ee379fff67d2e08d537f1f` |
| `objc2-ui-kit` | 459 | `d87d638e33c06f577498cbcc50491496a3ed4246998a7fbba7ccb98b1e7eab22` |
| `objc2-web-kit` | 222 | `b2e5aaab980c433cf470df9d7af96a7b46a9d892d521a2cbbb2f8a4c16751e7f` |

Chaque fichier de licence livré est empreinté dans `notices` de sa preuve.
Les huit expressions `Zlib OR Apache-2.0 OR MIT` ont leurs trois textes intégraux ;
`objc2-foundation` déclare seulement MIT dans son archive, dont le texte intégral
est livré. Les notices précédentes sont conservées. Le `LICENSE.md` amont intégral
est joint aux neuf entrées ; empreinte de ses octets amont :
`7f976f7e9cb2d87df7230606feb932c3f21ac0e664045a775b600046ff850c54`.
Les empreintes des textes rendus et des fichiers amont sont distinguées.

Après les textes intégraux dédupliqués, une section finale rattache à chaque
entrée cette mention factuelle, distincte d'une ligne de copyright :

> Aucun titulaire n'est nommé par le projet amont au commit 7b1abfd750a2cacaea71d6a56ecfb83cb7de560b. Projet objc2, auteur déclaré du workspace : Mads Marquart.

L'auteur du workspace n'est pas transformé en titulaire d'une crate.

## Sources retenues et rapprochements

`licenses/copyleft-sources.json` consigne pour chaque composant la version source,
la licence, les entrées d'inventaire couvertes, l'URL de l'archive source,
son SHA-256 effectivement téléchargé, ainsi que les URL au commit et empreintes
des recettes des roues. Il lie aussi une preuve de versions à son empreinte.
Les 59 entrées signalées par GPL/LGPL/AGPL ou MPL sont toutes couvertes par une
source ou une exclusion. Aucun composant tiers AGPL supplémentaire n'a été trouvé.

| Composant retenu | Version source | Licence / portée |
| --- | --- | --- |
| alsa-lib | `1.2.14` | LGPL-2.1-or-later |
| ffmpeg | `8.1.1` | GPL-3.0-or-later |
| gmp | `6.3.0` | LGPL-3.0-or-later OR GPL-2.0-or-later |
| libunistring | `1.4.2` | LGPL-3.0-or-later OR GPL-2.0-or-later |
| nettle-hogweed | `3.10.2` | LGPL-3.0-or-later OR GPL-2.0-or-later |
| gnutls | `3.8.13` | LGPL-2.1-or-later |
| lame | `3.100` | LGPL-2.0-or-later |
| x264 | `b35605ace3ddf7c1a5d67a2eb553f034aef41d55 (core 165)` | GPL-2.0-or-later |
| x265 | `4.2+1-e444744 (archive 4.2)` | GPL-2.0-or-later |
| libiconv | `1.19 (MSYS2 1.19-1)` | LGPL-2.1-or-later |
| espeak-ng | `1.52.0.1 / 212928b394a96e8fd2096616bfd54e17845c48f6` | GPL-3.0-or-later |
| piper-tts | `1.4.2` | GPL-3.0-or-later |
| recurring-ical-events | `3.8.0` | GPL-3.0-or-later |
| x-wr-timezone | `2.0.1` | LGPL-3.0-or-later |
| certifi | `2026.10.19` | MPL-2.0 |
| pathspec | `1.0.3` | License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0) |
| tqdm | `4.67.1` | MPL-2.0 AND MIT |
| grpcio | `1.76.0` | Apache License 2.0 ; notice agrégée MPL conservée avec les sources |
| cssparser-macros@0.6.1 | `0.6.1` | MPL-2.0 |
| cssparser@0.29.6 | `0.29.6` | MPL-2.0 |
| dtoa-short@0.3.5 | `0.3.5` | MPL-2.0 |
| option-ext@0.2.0 | `0.2.0` | MPL-2.0 |
| selectors@0.24.0 | `0.24.0` | MPL-2.0 |
| axe-core | `4.12.1 / 5d002cca1f862a0699d9f1bb7b5a1ec334fa1b22` | MPL-2.0 |
| lightningcss | `1.30.2 / 400f705e63e139c326f480aed11e1416f5a3a61f` | MPL-2.0 |
| adodbapi (pywin32) | `pywin32 311 / adodbapi 2.6.2.0` | LGPL-2.1-or-later |
| autocommand (setuptools) | `2.2.2` | LGPL-3.0-only |

Les cinq crates MPL et les paquets MPL Python/npm sont conservés par prudence,
y compris les variantes de plateformes et outils de l'inventaire conservateur.
`lightningcss` couvre ses douze entrées npm. Le choix n'est pas d'exempter un
composant dès que son paquet principal annonce une licence permissive : ainsi,
`adodbapi` et `autocommand` ont bien leurs sources fournies. La source intégrale de
setuptools est également jointe pour conserver les adaptations vendues avec lui.

Rapprochements principaux :

- **PyAV 17.1.0** : commit `97241598792f4c980c32458187154c7c999d68b3`,
  [sélection de FFmpeg](https://github.com/PyAV-Org/PyAV/blob/97241598792f4c980c32458187154c7c999d68b3/scripts/ffmpeg-8.1.json).
  La recette **pyav-ffmpeg 8.1.1-2**, commit
  `b84838a003b1626152ef530750d5c3e0022c3db9`, fixe les URL et SHA-256 des
  [archives sources](https://github.com/PyAV-Org/pyav-ffmpeg/blob/b84838a003b1626152ef530750d5c3e0022c3db9/scripts/pkg.py).
  Les archives des deux dépôts sont jointes intégralement, avec scripts et patches.
- **FFmpeg** : version 8.1.1 confirmée dans les binaires inspectés. La recette
  applique un patch qui retire x264/x265 du groupe GPL de configure et les met
  dans VERSION3. Les bibliothèques Linux affichent donc **LGPL version 3 or later**.
  Ce changement de déclaration ne supprime pas les obligations GPL des codecs :
  le manifeste retient prudemment **GPL-3.0-or-later pour la combinaison** et livre
  le correctif exact. La [page officielle FFmpeg](https://ffmpeg.org/legal.html)
  décrit l'effet des composants GPL sur la combinaison.
- **x265** : `x265_4.2.tar.gz` contient `x265Version.txt` avec `e444744`, distance 1
  du tag 4.2. Cela concorde avec **4.2+1-e444744** dans les trois roues ; aucune
  substitution par une autre archive « 4.2 » n'a été faite.
- **Piper 1.4.2** : commit `d6975e21a440c0d8b6e5fb7c41027409af13d44d`, dont
  [CMakeLists.txt](https://github.com/OHF-Voice/piper1-gpl/blob/d6975e21a440c0d8b6e5fb7c41027409af13d44d/CMakeLists.txt)
  fixe espeak-ng au commit `212928b394a96e8fd2096616bfd54e17845c48f6`.
  Les trois espeakbridge portent 1.52.0.1. L'archive source de ce commit et le
  dépôt de recettes Piper sont joints, sans remplacer le commit par un tag voisin.
- **libiconv Windows** : l'export `_libiconv_version` vaut `0x0113`, soit 1.19.
  Le paquet officiel MSYS2 **1.19-1** a été téléchargé : les onze sections PE de
  sa DLL sont identiques à celles de la roue, avec un SHA-256 par section ; le
  fichier entier diffère par ses métadonnées/surplus. Sa
  [recette au commit](https://github.com/msys2/MINGW-packages/blob/045d46aedb9fdbd93b0900b1e20c1a6c73f23072/mingw-w64-libiconv/PKGBUILD)
  et l'archive source MSYS2 sont incluses. Cette dernière contient l'archive
  libiconv amont au même SHA-256, un PKGBUILD identique au commit et trois patches.
- **Sources npm** : `gitHead` des versions exactes axe-core/lightningcss et
  intégrités de chaque distribution confrontées au verrou. Le code source
  du dépôt à ces commits est livré, y compris les recettes de compilation.
- **adodbapi** : version interne 2.6.2.0 lue dans la roue pywin32 311 ; source
  complète au commit du tag `b311`, `8b328dffac71b7afaf2d72f47c4048f27a32f6c8`.
  Le manifeste ne prétend pas que tout pywin32 soit LGPL.

Les empreintes et marqueurs des binaires, la correspondance libiconv, ainsi que
la portée de la GPL du lanceur de tests lxml figurent dans
`licenses/copyleft-version-evidence.json`. Ce fichier est contrôlé hors réseau
et livré dans l'ensemble assemblé.

## Entrées écartées et raisons

Les exclusions sont individuelles et liées aux empreintes des notices concernées.

| Entrées | Raison retenue |
| --- | --- |
| `python:caldav@2.2.3` | Choix explicite Apache-2.0, alternative autorisée par GPL-3.0-or-later OR Apache-2.0. Notices Apache et attributions conservées. |
| `cargo:r-efi@5.3.0` | Choix explicite MIT parmi MIT OR Apache-2.0 OR LGPL-2.1-or-later ; notice MIT conservée. |
| `npm:dompurify@3.4.17` | Choix explicite Apache-2.0 dans MPL-2.0 OR Apache-2.0 ; notices conservées. |
| `python:pyinstaller@6.18.0` | Exception PyInstaller : le bootloader et son incorporation dans le programme distribué bénéficient de l’exception explicite. Aucun changement apporté à PyInstaller lui-même. |
| `python:pyinstaller-hooks-contrib@2026.0` | Les hooks de construction GPL sont exécutés lors du build ; les runtime hooks intégrés à l’exécutable sont expressément Apache-2.0 selon LICENSE. Le paquet de hooks de construction n’est pas une bibliothèque du moteur. |
| `native:gcc-runtime@python:av@17.1.0`, `python:numpy@2.4.1/wheel-linux`, `python:numpy@2.4.1/wheel-macos`, `python:numpy@2.4.1/wheel-windows`, `python:scipy@1.17.0`, `python:scipy@1.17.0/wheel-linux`, `python:scipy@1.17.0/wheel-macos`, `python:scipy@1.17.0/wheel-windows` | GCC Runtime Library Exception 3.1 : libgcc/libgfortran/libquadmath issus d’une compilation éligible, liés à des modules indépendants. Les bibliothèques runtime ne sont pas modifiées ; notices et exception conservées. Pas d’exemption générale des programmes GCC. |
| `python:pillow@13.0.0/wheel-windows` | Le texte GPL de cette roue concerne l’alternative FreeType ; la FreeType License (FTL), présente intégralement dans la même notice, est retenue avec son attribution. Pas de libimagequant GPL livré dans la roue inventoriée. |
| `python:lxml@6.1.1` | GPL.txt concerne le lanceur de tests test.py, copyright Shuttleworth Foundation, exclu du code lxml installé. LICENSES.txt de la source 6.1.1 explicite cette portée ; le cœur lxml est BSD, libxml2/libxslt MIT. |
| `python:torch@2.9.1`, `python:torch@2.9.1/wheel-cpu-linux`, `python:torch@2.9.1/wheel-cpu-windows` | Les sections GPL du relevé agrégé visent les tests cpr/test et les outils vcpkg/ports/ffnvcodec, sans code lié dans les roues ; la section finale du runtime GCC/libgomp bénéficie de GCC Runtime Library Exception 3.1. Cette exclusion n’étend pas l’exception aux autres composants. |

## Script, CI et conservation

`scripts/copyleft_sources.py verifier` est hors réseau. Il contrôle la cohérence
avec les verrous et l'inventaire, la couverture des entrées détectées, les
exclusions documentées, les recettes locales épinglées et les preuves de version.
Une source absente, une version non renseignée, une recette manquante, une
empreinte de preuve modifiée ou une nouvelle entrée copyleft non couverte
produit un code non nul.

`assembler <dossier>` télécharge les archives et recettes, vérifie leur SHA-256,
refuse les noms sortant du dossier, et conserve leurs octets. Il ajoute le
manifeste, les preuves de versions et le `LISEZMOI-SOURCES.txt` français. Un
fichier déjà présent n'est réutilisé qu'après vérification de son empreinte.
Aucun code amont n'est exécuté. Un manifeste incomplet peut donner un corpus
partiel à examiner, mais la commande reste en échec : pas de substitution de version.

Le garde est branché sans tolérance d'échec dans `ci.yml` et dans les contrôles
préalables du build de `release.yml`. Le nouveau job `sources-copyleft`, après
les précontrôles/CI/E2E, vérifie et assemble le corpus puis joint
`THERESE-sources-copyleft.tar.gz` au brouillon de la même release. Les builds des
installeurs en dépendent : ni ceux-ci ni la publication du manifeste updater ne
peuvent passer si les sources n'ont pas été vérifiées et jointes. Les deux
nouvelles actions externes reprennent les SHA déjà vérifiés de checkout/setup-python.
**Ce workflow a seulement été préparé ; il n'a pas été déclenché.**

La tête de `THIRD_PARTY_LICENSES` indique la pièce jointe de la même version et
la durée de disponibilité. Le texte le plus strict retenu est **GPL-3.0, §6b** :
au moins trois ans et aussi longtemps que support/pièces de rechange sont proposés
pour le modèle concerné. Notre engagement est plus conservateur : conservation
pendant la distribution des binaires et au moins trois ans après leur dernière
distribution, prolongée tant que le support/pièces sont proposés. La diffusion
par pièce jointe simultanée relève de **§6d** ; cette voie n'impose pas à elle seule
un délai fixe de trois ans. Voir le [texte GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.html#section6).
La conservation future des releases est un engagement d'exploitation, pas une
propriété que les tests locaux peuvent garantir.

## Assemblage local

Dossier ignoré par Git : `.work-t2/round4/sources-copyleft/`.
Le premier assemblage a téléchargé les fichiers avec leurs empreintes ; un
second passage a revérifié les fichiers présents et actualisé le manifeste et
les preuves après la revue finale.

- **32 archives sources** et **7 fichiers de recettes**  soit
  **104 493 917 octets** téléchargés et vérifiés.
- **42 fichiers** au total avec manifeste  preuve et LISEZMOI :
  **104 618 802 octets**  soit **99.77 Mio**.
- Pièce locale préparée avec la même commande `tar` que la release :
  `.work-t2/round4/THERESE-sources-copyleft.tar.gz`  **103 298 088 octets**
  (**98.51 Mio**)  SHA-256
  `68a57986f042dfa31f95370b772ac293af62cf51d3ad24636c06e059eafd41e3`.

## Tests rouges et résultats

Les tests ont été ajoutés avant l'évolution de chaque garde, avec journaux dans
`.work-t2/round4/evidence/` :

- Absence de titulaire : preuve exacte initialement non prise en charge ;
  statut seul refusé ; copyright/©/(c)/(C)/SPDX/Authors dans archive ou arbre
  refusé, même après recalcul des hashes ; auteurs dans chacun des deux
  manifestes refusés ; archive, arbre, commit, décompte ou notice modifiés refusés.
  Un test supplémentaire a d'abord échoué pour les sources générées liées par
  lien symbolique, puis passe après prise en compte de leur portée.
- Sources : script initialement absent ; manque de composant, inventaire périmé,
  recette non épinglée, version absente, faux hash, exclusion sans preuve et
  chemin sortant refusés. Preuve de version modifiée et inclusion de cette preuve
  dans le corpus ont chacune leur test rouge puis vert.
- Ordre des mentions : le test exigeant la mention factuelle après le texte MIT
  échoue d'abord, puis passe après son déplacement dans la section finale.
- Pipeline et en-tête : tests d'abord en échec sur l'absence du garde, de la
  dépendance à l'assemblage et de l'indication des sources/durée ; verts ensuite.

| Contrôle final | Résultat |
| --- | --- |
| Tests des scripts du lot | **67 réussis, 91 sous-tests réussis**, zéro échec/erreur/ignoré |
| Dont tests des notices / preuves d'absence / sources | **35 / 6 / 9** tests |
| `third_party_licenses.py generate` | **0** |
| `third_party_licenses.py check` | **0**, **0 entrée refusée**, 1 326 entrées |
| Première ligne de `THIRD_PARTY_LICENSES` | `THÉRÈSE — Licences des composants tiers` |
| Taille de `THIRD_PARTY_LICENSES` | **5 724 461 octets** |
| `copyleft_sources.py verifier` | **0**, 27 composants ; aucune source manquante |
| `copyleft_sources.py assembler` | **0**, tous les SHA-256 concordent |
| Ruff sur les scripts/tests modifiés | **0** |
| actionlint 1.7.7, sans ShellCheck/Pyflakes | **0**, zéro diagnostic sur HEAD et `08d0a8a0` |
| actionlint avec ShellCheck, Pyflakes désactivé | **1**, mêmes **16 diagnostics** que `08d0a8a0` après retrait des positions |

Aucune suite complète pytest ou Vitest n'a été lancée, conformément à la consigne.
Les tests exécutés sont ceux de `scripts/tests/`, comprenant les contrats du
pipeline. Les résultats des signatures macOS/Windows et de la notarisation ne
sont pas déduits de ces tests Linux.

`git diff --check` pour ce tour relève **un espace final dans la recette amont
`licenses/recipes/ffmpeg-8.1.1-2-pkg.py.txt`**. Ses octets ont été conservés pour
respecter son empreinte. Depuis `08d0a8a0`, il retrouve les 1 343 diagnostics déjà
présents dans `THIRD_PARTY_LICENSES`, plus cet espace. Aucune règle générale
masquant les espaces n'a été ajoutée.

## Ce qui manque encore

Aucune archive source exacte du périmètre inventorié ne manque après les
recherches PyPI, Cargo, npm, dépôts aux commits, recettes PyAV/FFmpeg/Piper et
archive source MSYS2. Le statut « source manquante » reste prévu et bloquant
pour les prochaines mises à jour.

Restent les limites déjà séparées des deux réserves de ce tour : vérification
réelle des installations/signatures/notarisations et des mises à jour sur les
plateformes ; remplacement/reliaison des bibliothèques LGPL dans le onefile ;
respect effectif de la conservation des pièces jointes. Aucun rebuild comparatif
reproduisant octet pour octet les roues n'a été réalisé. Les modèles de voix
récupérés hors des verrous restent hors de cet inventaire.

## Fichiers changés

Les scripts du contrôle, leurs tests, les deux workflows et la documentation
évoluent ; les notices, inventaire et preuves sont régénérés. Les 10 archives de
preuve objc2 et les 7 copies exactes de recettes sont versionnées. Le corpus de
sources de 100 Mio reste dans le dossier de travail ignoré.

```text
.gitattributes
.github/workflows/ci.yml
.github/workflows/release.yml
THIRD_PARTY_LICENSES
docs/SIGNATURE-ET-LICENCES.md
licenses/attribution-sources.json
licenses/copyleft-sources.json
licenses/copyleft-version-evidence.json
licenses/evidence/objc2-7b1abfd.tar.gz
licenses/evidence/objc2-app-kit-0.3.2.crate
licenses/evidence/objc2-core-foundation-0.3.2.crate
licenses/evidence/objc2-core-graphics-0.3.2.crate
licenses/evidence/objc2-foundation-0.3.2.crate
licenses/evidence/objc2-io-surface-0.3.2.crate
licenses/evidence/objc2-osa-kit-0.3.2.crate
licenses/evidence/objc2-quartz-core-0.3.2.crate
licenses/evidence/objc2-ui-kit-0.3.2.crate
licenses/evidence/objc2-web-kit-0.3.2.crate
licenses/inventory.json
licenses/overrides.json
licenses/recipes/ffmpeg-8.1.1-2-build.py.txt
licenses/recipes/ffmpeg-8.1.1-2-pkg.py.txt
licenses/recipes/libiconv-1.19-1-PKGBUILD.txt
licenses/recipes/piper-1.4.2-CMakeLists.txt
licenses/recipes/piper-1.4.2-pyproject.toml.txt
licenses/recipes/pyav-17.1.0-ffmpeg-8.1.json.txt
licenses/recipes/pywin32-311-setup.py.txt
scripts/attribution_evidence.py
scripts/copyleft_sources.py
scripts/tests/test_attribution_evidence.py
scripts/tests/test_copyleft_sources.py
scripts/tests/test_release_licenses.py
scripts/tests/test_release_pipeline.py
scripts/third_party_licenses.py
docs/rapport-signature-4-2026-10-29.md
```

Le présent rapport est versionné dans `docs/rapport-signature-4-2026-10-29.md`
et copié à l'emplacement demandé, hors de l'arbre, comme exception explicite.
Les autres écritures de travail sont sous l'arbre. Aucun `rm`, aucun push,
aucun déclenchement de CI, aucune publication ni affichage de secret ou jeton.
