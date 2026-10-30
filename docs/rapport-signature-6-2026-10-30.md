# THÉRÈSE — Signature et licences, sixième tour

30 octobre 2026. Arbre : `/home/synoptia/staging/therese-lot4-20261029/wt-therese`.
Branche : `coco/therese-signature-20261029`. Départ propre sur **b6512dbd**.
Commit de réalisation : **3f97353d**, « Inventorier les bibliothèques système et fermer la garde de release ».

**Le trou Linux est couvert par un catalogue empreinté, un inventaire automatique du build et une comparaison du contenu final des installeurs. La réserve sur l’identité des archives de soutien est corrigée. 104 tests distincts passent. Aucun build complet, aucune CI déclenchée, aucun push ni téléversement.**

Le catalogue relu est celui des octets Ubuntu 22.04/CPython du complément v0.82.0. Une bibliothèque nouvelle ou une mise à jour du runner provoque un refus jusqu’à rapprochement et revue. Les extracteurs macOS/Windows sont raccordés à la garde, mais leurs bibliothèques système hors roues ne disposent pas encore de preuves dans ce catalogue : ces plateformes peuvent être bloquées à leur première CI. Ce rapport ne présente donc pas les trois plateformes comme déjà validées.

## 1. Preuves examinées et contre-épreuve sur la release publiée

Ont été relus `prompt-coco-signature.md`, `relecture-signature-5.md`, ainsi que `RAPPORT.md`, `OPERATION.md`, les inventaires, notices, sources et outils du complément situé dans `/home/synoptia/staging/therese-copyleft-v0820-2026-10-30/`.

L’archive préparée `a-televerser-v0820/THERESE-sources-systeme-linux.tar.gz` a été contrôlée : **23 338 564 octets**, SHA-256 `d76da0ed53057ab491c3bef874e31435ac8f882f67aa32b2efc559ccf06b246d`. Ses **11 fichiers source**, totalisant **23 299 768 octets**, correspondent tous aux tailles et SHA-256 intégrés au nouveau catalogue. Aucun original du complément n’a été modifié.

Le nouveau scanner a également lu le véritable `.deb` v0.82.0 conservé dans le cache de cette opération, sans installation ni exécution :

- SHA-256 de l’installeur : `211423b73bd5d5ba19b2520cce936a8322f0fee95626cb7ed3b48c17ce39fd3b` ;
- **593 chemins de fichiers natifs**, liens internes résolus ;
- **18 bibliothèques du complément** retrouvées avec leurs SHA-256 exacts ;
- **17 bibliothèques Ubuntu**, issues de **16 paquets binaires**, rapprochées une seconde fois des membres de leurs paquets `.deb` : empreinte de chaque paquet puis empreinte du fichier extrait ;
- **0 notice et 0 inventaire** embarqués dans cette ancienne release : la nouvelle garde la refuse, avec « Notice de l’installeur absente ou périmée ».

Cette relecture reprend les preuves de provenance du complément, qui décrit la vérification des sources jusqu’aux index Ubuntu signés. Elle ne prétend pas avoir refait ici la vérification cryptographique InRelease. La réserve historique sur l’index universe de libobjc reste documentée dans ce complément ; le fichier et son paquet binaire ont, eux, été revérifiés par SHA-256.

## 2. Inventaire automatique et garde de release

### Au build

`backend.spec` appelle `record_analysis` après Analysis : chaque objet natif est lié à son fichier d’origine et son SHA-256 avant strip, signature ou compression. Les fichiers natifs classés parmi les données sont également relevés.

Après construction et signature du moteur, avant nettoyage et avant Tauri, `scripts/system_libraries.py inventory` inspecte les octets effectivement livrables : dossier Linux onedir ou membres natifs du onefile macOS/Windows. La reconnaissance utilise les signatures ELF, Mach-O et PE, sans dépendre de l’extension du nom.

Le rapprochement distingue :

1. Les fichiers des distributions Python : leur SHA-256 doit correspondre au RECORD installé, leur version à une entrée de l’inventaire des verrous, et leur licence être connue. Les roues Torch CPU sont rattachées aux entrées dédiées déjà verrouillées.
2. Les extensions de CPython : origine directe `lib-dynload`, véritable nom de module standard, suffixe d’extension Python et version CPython exacte. Une bibliothèque arbitraire placée dans ce répertoire n’obtient pas automatiquement la licence PSF.
3. Les bibliothèques système : correspondance exacte de SHA-256 avec le catalogue relu ; sur Linux, rapprochement supplémentaire avec dpkg pour le nom et la version du paquet binaire **et** du paquet source. Le SONAME ne sert jamais à déduire la version source ou la licence.

Un objet sans provenance, licence ou version établie fait échouer le build. Le relevé `system-libraries-unreviewed.json` conserve alors les objets à revoir et les candidats dpkg disponibles. Aucun inventaire accepté n’est produit pour ce cas.

L’inventaire accepté `.work-release/system-libraries.json` devient une ressource Tauri dans les deux déclarations de ressources existantes. Il fixe notamment les SHA-256 du catalogue et des notices.

### Dans chaque installeur

`verify_packaged_licenses.py` compare les notices et l’inventaire embarqués octet pour octet, puis vérifie les noms et SHA-256 des fichiers natifs du moteur. Les ajouts, retraits et modifications sont refusés. Les liens sortant du paquet, les cycles et les liens natifs non résolus sont refusés.

- **Debian** : lecture en flux par `dpkg-deb --fsys-tarfile`, sans extraction sur disque. Tous les fichiers natifs du paquet sont examinés ; les éventuelles bibliothèques ajoutées hors du moteur doivent aussi correspondre au catalogue et au paquet du runner. L’exécutable principal doit correspondre au résultat de compilation Tauri de ce build.
- **AppImage** : la release actuelle demande explicitement `--bundles deb` et n’en produit donc pas. Si une AppImage apparaît dans le dossier de sortie, elle est inspectée avec `unsquashfs`, vérifiée puis incluse dans la liste de publication. Une bibliothèque ou un auxiliaire natif AppImage inconnu bloque ; aucune exemption globale n’est accordée à AppRun. Le runtime AppImage n’est appelé que pour obtenir son offset SquashFS.
- **macOS** : comparaison du onefile dans l’archive updater et dans le DMG monté en lecture seule ; les autres binaires natifs, hormis l’exécutable Tauri contrôlé par la garde de signature, sont refusés s’ils n’ont pas d’inventaire.
- **Windows** : extraction administrative MSI et extraction NSIS avec 7z ; comparaison des membres natifs du onefile et refus des binaires auxiliaires non inventoriés. La limite antérieure de signature des DLL enfermées dans le onefile n’est pas supprimée par ce travail de licences.

Chaque installeur vérifié reçoit un fichier de preuve JSON contenant son SHA-256, celui de l’inventaire de build et ses fichiers natifs. `publish_release_artifacts.py` exige ces preuves et revérifie les empreintes avant publication ; les preuves sont jointes aux artefacts. Il prend aussi en compte une AppImage éventuelle.

La CI exécute le contrôle du catalogue. Le job de sources, requis avant les builds, assemble et joint également `THERESE-sources-systeme-linux.tar.gz`. La garde ne comporte aucun `continue-on-error`. Le nettoyage Linux conserve maintenant l’interpréteur installé par setup-python : il est nécessaire aux contrôles après Tauri. L’inventaire est produit avant suppression de l’environnement de construction.

## 3. Catalogue, notices et sources exactes

Les **1 326 entrées** historiques de `licenses/inventory.json` sont identiques à celles de b6512dbd ; seule l’empreinte de fraîcheur est actualisée. Le catalogue système est un document séparé comportant **18 bibliothèques**, **13 notices d’origine** et **11 ressources source**.

| Bibliothèque | Paquet et version exacts | Licence relue |
| --- | --- | --- |
| libbz2.so.1.0 | libbz2-1.0 1.0.8-5ubuntu0.1 | bzip2-1.0.6 |
| libcrypto.so.3 | libssl3 3.0.2-0ubuntu1.30 | Apache-2.0 |
| libffi.so.8 | libffi8 3.4.2-4 | MIT |
| libgcc_s.so.1 | libgcc-s1 12.3.0-1ubuntu1~22.04.3 | GPL-3.0-or-later WITH GCC-exception-3.1 |
| libgdbm.so.6 | libgdbm6 1.23-1 | GPL-3.0-or-later |
| libgdbm_compat.so.4 | libgdbm-compat4 1.23-1 | GPL-3.0-or-later |
| liblzma.so.5 | liblzma5 5.2.5-2ubuntu1.2 | LicenseRef-Public-Domain |
| libmvec.so.1 | libc6 2.35-0ubuntu3.15 | LGPL-2.1-or-later |
| libncursesw.so.6 | libncursesw6 6.3-2ubuntu0.3 | X11 |
| libobjc.so.4 | libobjc4 12.3.0-1ubuntu1~22.04.3 | GPL-3.0-or-later WITH GCC-exception-3.1 |
| libreadline.so.8 | libreadline8 8.1.2-1 | GPL-3.0-or-later |
| libsqlite3.so.0 | libsqlite3-0 3.37.2-2ubuntu0.8 | LicenseRef-Public-Domain |
| libssl.so.3 | libssl3 3.0.2-0ubuntu1.30 | Apache-2.0 |
| libstdc++.so.6 | libstdc++6 12.3.0-1ubuntu1~22.04.3 | GPL-3.0-or-later WITH GCC-exception-3.1 |
| libtinfo.so.6 | libtinfo6 6.3-2ubuntu0.3 | X11 |
| libuuid.so.1 | libuuid1 2.37.2-4ubuntu3.6 | BSD-3-Clause |
| libz.so.1 | zlib1g 1:1.2.11.dfsg-2ubuntu9.2 | Zlib |
| libpython3.13.so.1.0 | CPython 3.13.17 | PSF-2.0 |

Les quatre fichiers `libreadline.so.8`, `libgdbm.so.6`, `libgdbm_compat.so.4` et `libmvec.so.1` imposent ici les sources de **trois composants supplémentaires** :

| Composant source | Version | Ressources | Octets |
| --- | --- | ---: | ---: |
| readline | 8.1.2-1 | 3 | 3 024 797 |
| gdbm | 1.23-1 | 4 | 1 137 102 |
| glibc | 2.35-0ubuntu3.15 | 4 | 19 137 869 |
| Total | | **11** | **23 299 768** |

Le catalogue exige tous les fichiers du complément, y compris `.dsc`, archives amont, correctifs Debian/Ubuntu et signatures amont. Le passage d’une licence GPL à une licence permissive ou le retrait de l’obligation de sources est également refusé par les règles relues du catalogue.

`THIRD_PARTY_LICENSES` contient les notices système originales et les textes GNU complets auxquels elles renvoient. Taille finale : **6 009 037 octets** ; SHA-256 **`1a3b4b00637a184daca7a2f2bb0a96ccfee237892cf15a3ec9826beb8888c23a`**. Les notices et preuves système participent à l’empreinte de fraîcheur. Les fichiers sont forcés en LF ; les espaces de fin de ligne présents dans les textes amont sont préservés, avec une règle `.gitattributes` limitée à ces notices pour le contrôle whitespace.

`licenses/LISEZMOI-SOURCES.txt` est incorporé au LISEZMOI de l’archive historique et au complément système. Il décrit : extraction du paquet source par `dpkg-source -x`, installation des dépendances de construction, reconstruction par `dpkg-buildpackage`, remplacement de libmvec dans une copie privée du moteur Linux, usage de `THERESE_BACKEND_LIBS`, contrôle du chargement et précautions de compatibilité entre composants glibc. Il explique aussi la reconstruction du moteur PyInstaller et de l’application, nécessaire pour les plateformes onefile. Il distingue ces instructions d’une validation fonctionnelle de reliaison, qui reste à réaliser.

### Assemblages réellement vérifiés ici

Les téléchargements ont été remplacés par les octets des caches existants, puis les vrais contrôles SHA-256, de preuve et de recettes ont été exécutés. Aucun code source téléchargé n’a été exécuté.

- Archive historique : **27 composants**, **39 ressources**, **104 493 917 octets** de ressources ; dossier final **42 fichiers, 104 681 071 octets**. Les ressources source et recettes restent celles du tour 5 ; preuve et LISEZMOI sont actualisés.
- Complément système : **3 composants source**, **11 ressources**, **23 299 768 octets** de sources ; dossier final **28 fichiers, 23 790 502 octets** avec notices, catalogue, preuve et LISEZMOI.
- Total des ressources : **50**, **127 793 685 octets**, couvrant **30 composants source**.
- Archive locale déterministe du complément réassemblé : **23 413 943 octets**, SHA-256 **`5c81bdcd8b3acf9effb43cac0eccfbef01c2d60ff2550ee07f58bdb3a93784dc`**. Elle diffère de l’archive préparée pour la v0.82.0, car elle inclut le nouveau catalogue, les textes de licence complets et la méthode de reconstruction. La CI utilise son assemblage propre ; son enveloppe tar/gzip n’est pas annoncée comme identique à cette archive locale.

## 4. Réserve du tour 5 : identité des archives de soutien

Les **cinq objets complets** de `supporting_sources` sont maintenant portés par `supporting_source_bindings` dans `licenses/copyleft-version-evidence.json`, dont l’empreinte est contrôlée par le manifeste. La comparaison porte sur l’objet complet : URL, SHA-256, commit lorsqu’il existe et autres champs, pas seulement sur le nom de fichier. Les doublons sont refusés.

Le test rouge initial a repris exactement la substitution de l’objet PyAV sous le nom `pyav-ffmpeg-8.1.1-2-build-tree.tar.gz`, puis sous celui de la source MSYS2 libiconv. Le validateur précédent acceptait les deux substitutions. Les nouveaux tests exigent le refus par le validateur, par la véritable CLI `verifier` et par `assemble`, avant le premier téléchargement ou la première écriture d’assemblage.

Empreintes finales :

- preuve `copyleft-version-evidence.json` : `82ae13794f507450c0c9ea3a408b5007e08478c7c73bc260dc5574ca358fd46b` ;
- manifeste `copyleft-sources.json` : `0a520eefa3471a710c678852fa164af3ae8a9268554f88d28951f3738a3d3d99` ;
- catalogue système : `6b7f03491f0a2b3050c7c8cfaa7d7f57fd8683290b307ad0ef877fed783e952b`.

## 5. Vérifications et nombres exacts

**Rouge avant correction :** deux méthodes exécutées initialement ; deux sous-tests de substitution échouent et le test de garde constate son absence. Le nouveau module système était également absent. Une seconde contre-épreuve rouge a ensuite montré qu’un fichier quelconque dans `lib-dynload` recevait trop largement l’attribution PSF ; elle a été corrigée et rejouée avec succès.

**Vert : 104 méthodes de test distinctes, aucun test ignoré.** Une exécution complète a validé 100 méthodes en 97,943 s ; les quatre méthodes ajoutées pendant la revue finale ont été couvertes, avec les tests touchés, par le dernier rejeu de 29 méthodes en 1,185 s. Les 104 méthodes n’ont donc pas été comptées comme une unique invocation de 104 tests.

| Fichier de tests | Méthodes distinctes validées |
| --- | ---: |
| attribution_evidence | 12 |
| copyleft_sources | 20 |
| cpu_torch | 1 |
| embedded_macos | 2 |
| macos_signing | 5 |
| packaged_licenses | 1 |
| release_licenses | 35 |
| release_pipeline | 10 |
| system_libraries | 18 |
| **Total** | **104** |

Les nouvelles contre-épreuves couvrent notamment ajout/retrait/modification de bibliothèque, licence inconnue ou déclassée, changement de version, octets différents sous le même SONAME, source omise ou cache corrompu, lien extérieur, contenu natif sans extension, membre onefile classé comme donnée, inventaire embarqué absent/périmé, preuve de publication périmée et traitement de l’AppImage. Un véritable petit paquet `.deb` de test est construit et lu par `dpkg-deb` : la garde l’accepte, puis refuse le même paquet augmenté d’un fichier ELF non inventorié. Ce test ne construit pas THÉRÈSE.

Autres vérifications :

- `third_party_licenses.py generate`, puis **`check` : code 0**, 1 326 archives verrouillées et 6 009 037 octets de notices ;
- `copyleft_sources.py verifier` : **code 0**, 27 composants, aucune source manquante ;
- `system_libraries.py check` : **code 0**, 18 bibliothèques et 11 ressources source ;
- assemblages réels et rapprochements du `.deb` décrits plus haut ;
- syntaxe Python vérifiée par `py_compile` ; YAML des deux workflows valide ;
- actionlint sans ShellCheck/Pyflakes : **0 diagnostic** ; avec ShellCheck et sans Pyflakes : **16 diagnostics**, mêmes messages qu’à b6512dbd après abstraction des positions, aucun nouveau ;
- `git diff --check` et contrôle du diff indexé : **code 0**.

Les journaux, relevés, fixtures et assemblages sont conservés dans `.work-t2/round6/`, notamment `red-initial.txt`, `red-stdlib.txt`, `all-tests.txt`, `final-changed-tests.txt`, `check-final.txt`, `sources-final.txt`, `published-deb-scan.json`, `published-deb-scan.txt`, `complement-archive-check.txt`, `copyleft-assembly.txt`, `system-archive.json` et `final-metrics.json`.

## 6. Fichiers changés et vérifications restant à faire

**36 fichiers de réalisation**, regroupés ainsi :

- nouvel outillage `scripts/system_libraries.py`, garde des installeurs et contrôle des preuves par le publieur ;
- `backend.spec`, les deux déclarations de ressources Tauri et les workflows CI/release ;
- générateur des notices, assembleur historique, preuve des archives de soutien ;
- catalogue système, preuve du complément, 13 notices originales, texte LGPL-2.0, LISEZMOI ;
- `THIRD_PARTY_LICENSES`, empreinte de l’inventaire historique et `.gitattributes` ;
- tests de sources, pipeline et bibliothèques système ; documentation `SIGNATURE-ET-LICENCES.md`.

Sur une **vraie CI Linux**, vérifier que l’inventaire automatique de toutes les bibliothèques du build courant passe avec le runner réellement utilisé, que les versions dpkg/source et les octets concordent, que le `.deb` contient les deux ressources et que sa preuve est jointe avant publication. Les 593 fichiers du `.deb` historique ne sont pas un nombre attendu imposé au prochain build : seul l’inventaire de ce build donne son nombre exact. Un runner mis à jour peut légitimement nécessiter une nouvelle revue de catalogue.

Si **AppImage** est activée, vérifier l’extraction réelle, le contenu d’AppDir et l’identité/licence de ses auxiliaires. L’AppImage n’existe pas dans les sorties actuellement demandées ; aucune AppImage réelle n’a été construite ou exécutée ici.

Sur **macOS et Windows**, éprouver les vrais extracteurs, onefiles, signatures et formats d’installation. Compléter les preuves des bibliothèques système non couvertes avant que la garde ne permette la release. Le constat fourni sur libedit macOS est « liée au système, non embarquée » pour la v0.82.0 ; OpenSSL, ncurses et Python.framework restent à rapprocher sur le nouveau build. Windows n’avait pas été inspecté dans le complément ; les DLL du runtime Python/Microsoft et les auxiliaires NSIS ne sont pas présumés couverts. Le catalogue actuel ne fournit pas leurs nouvelles notices par invention.

Enfin, exécuter une **véritable reconstruction et reliaison LGPL**, avec chargement de la bibliothèque modifiée et essais des fonctions concernées. Les sources et la méthode sont livrées ; ni une reliaison réussie, ni une notarisation, ni une signature Windows réelle n’ont été établies dans cet environnement. Les suites applicatives backend/frontend n’ont pas été relancées : ce tour touche l’outillage de licences et le packaging, contrôlés par les tests ci-dessus.

Aucune commande de suppression `rm`, aucun push et aucun déclenchement de CI n’ont été exécutés. Aucune valeur de configuration, clé ou secret n’a été affichée. Le dépôt et les fichiers du complément restent locaux ; les artefacts de test ne sont pas publiés.
