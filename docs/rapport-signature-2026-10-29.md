# Lot T2 — Signature et licences — 29 octobre 2026

> Rapport du premier tour. La relecture a invalidé la complétude annoncée des
> notices. Le deuxième tour ajoute les textes manquants et un refus explicite
> des attributions génériques ou introuvables : le livrable courant est
> PROVISOIRE et ne passe pas le contrôle de release. Les résultats ci-dessous
> restent historiques ; voir `rapport-signature-2-2026-10-29.md`.

Travail sur `coco/therese-signature-20261029`, à partir de
`08d0a8a0a17425482b7a33b33c5ae7b269a0260f`, identique à la référence locale
`origin/main` (0.82.0). Aucun push, aucune CI déclenchée, aucun compte de
signature consulté ou créé, aucune valeur secrète affichée.

Les rapports A1 et A8 du 27 octobre ont été consultés en lecture seule.
Le travail commencé avant l'interruption a été repris depuis le commit
`3fbd5cea` et ses modifications non commitées, sans repartir de zéro.
Une copie de ce rapport est livrée à l'emplacement expressément demandé :
`/home/synoptia/staging/therese-lot4-20261029/rapport-signature.md`.
Cette livraison est la seule écriture autorisée dans le répertoire parent.

## Résultat et limites

La chaîne macOS est préparée avec un repli ad hoc actif, y compris pour les
bibliothèques compressées dans le moteur. La signature Microsoft est raccordée
aux fichiers accessibles et aux installeurs ; **les DLL et `.pyd` internes au
onefile Windows restent hors couverture**. Leur prise en charge demande le
passage en dossier, proposé mais non réalisé conformément au lot.

`THIRD_PARTY_LICENSES` contient les textes, pas seulement des identifiants de
licences, et est déclaré comme ressource des trois plateformes, y compris NSIS
et MSI. La CI refuse son absence ou son obsolescence. Les contrôles de release
comparent aussi la ressource réellement embarquée au fichier versionné.

**La conformité de redistribution n'est pas soldée par ces notices.** Les
sources correspondantes des bibliothèques copyleft natives restent à constituer
et à rendre disponibles ; 38 entrées portent une réserve de revue explicite
sur les attributions ou les versions des sources natives. Ces points doivent
être traités avant de qualifier la distribution publique de conforme.

## Fichiers modifiés ou ajoutés

| Fichiers | Changement |
| --- | --- |
| `.github/workflows/release.yml` | Préparation Apple avant PyInstaller ; repli ad hoc ; action Microsoft épinglée avant/après empaquetage ; vérifications ; finalisation avant publication ; délai porté à 150 min ; installations gelées et npm sans scripts |
| `.github/workflows/ci.yml` | Job de contrats de signature et contrôle des notices hors réseau |
| `src/backend/backend.spec` | Identité Apple/ad hoc et entitlements transmis à PyInstaller avant la compression des bibliothèques |
| `src/frontend/src-tauri/Entitlements.plist` | Entitlements explicites, ajout de l'accès au microphone |
| `src/frontend/src-tauri/tauri.conf.json` | Retrait de l'identité ad hoc figée ; ressource des licences avec destination stable |
| `src/frontend/src-tauri/tauri.linux.conf.json` | Conservation explicite de la notice dans la surcharge Linux et des ressources existantes |
| `scripts/sign_macos.py` | Import confidentiel du P12, signature par profondeur, notarisation app/DMG, agrafage, recréation de l'archive updater |
| `scripts/verify_embedded_macos.py` | Réextraction et contrôle de tous les Mach-O, y compris un Mach-O classé comme donnée, sans exécuter le moteur |
| `scripts/prepare_windows_signing.py`, `scripts/sign_windows.ps1`, `scripts/verify_windows_signing.ps1` | Activation conditionnelle, callback Tauri, vérification Authenticode et horodatage |
| `scripts/install_cpu_torch.py` | Installation par URL et empreinte de la roue Torch CPU CPython 3.13 couverte par les notices |
| `scripts/publish_release_artifacts.py` | Contrôle des formats attendus, signatures updater recalculées après toutes les modifications, envoi au brouillon ensuite |
| `scripts/verify_packaged_licenses.py` | Comparaison des ressources du bundle, du `.deb` et des extractions NSIS/MSI |
| `scripts/third_party_licenses.py`, `licenses/inventory.json`, `licenses/overrides.json`, `licenses/native-components.lock.json`, `licenses/runtime-wheels.lock.json`, `THIRD_PARTY_LICENSES` | Collecte vérifiée, notices complètes, provenance, suppléments natifs/CPU et contrôle de fraîcheur |
| `scripts/tests/test_*.py` | Tests Linux des signatures, de l'ordre du pipeline, des licences et de l'empaquetage |
| `src/frontend/src/lib/pdfLocaux.test.ts`, `tests/test_sentinelles_structure.py` | Contrôle des destinations du guide et de la récursion du dossier moteur compatible avec la table de ressources Tauri |
| `docs/SIGNATURE-ET-LICENCES.md` | Procédure opérationnelle, noms des secrets, création des comptes, limites et recette CI |
| `.gitattributes` | Fins de ligne LF imposées pour les fichiers entrant dans les empreintes et les notices, y compris sur Windows |
| `.gitignore` | Exclusion des preuves et caches de travail et des extractions d'inspection |
| `docs/rapport-signature-2026-10-29.md` | Ce rapport |

## Ce que fait la signature

### macOS

Les six secrets Apple sont nécessaires à l'activation complète. Un jeu absent
ou incomplet active `-`, sans importer de certificat ni lancer de notarisation.
Un jeu complet mais invalide ne revient pas silencieusement à l'ad hoc : il fait
échouer la chaîne. La clé updater existante reste un prérequis indépendant.

PyInstaller signe les bibliothèques après leurs réécritures Mach-O, avant le
onefile, avec le runtime renforcé. Le contrôle réextrait le contenu réellement
compressé, vérifie chaque Mach-O avec `codesign --verify --deep --strict`, son
runtime, ses entitlements et, si disponible, sa Team ID. Le nombre vérifié est
obligatoirement non nul : le nombre ancien d'environ 417 n'est pas codé en dur.

Les objets imbriqués, puis le bundle principal sont signés. En mode Apple,
le bundle est notarisé et agrafé, puis un DMG est reconstruit, signé, notarisé
**lui aussi** et agrafé. Le DMG a une présentation simple avec un lien
Applications. L'archive updater est refaite depuis le bundle final et sa
signature est recalculée ensuite. Rien n'est envoyé au brouillon avant les
recettes et contrôles du runner concerné.

L'exception de validation des bibliothèques est conservée ; elle reste aussi
appliquée à l'interface par Tauri. Son retrait nécessite une recette signée
réelle. L'accès micro est explicite. Le runtime n'est pas attesté sur Linux.

### Windows

L'action officielle `Azure/artifact-signing-action` est épinglée au commit
`b443cf8ea4124818d2ea9f043cba29fc3ec47b16`. Son module Microsoft
`TrustedSigning` 0.5.8 sert aussi au callback Tauri. SHA-256, horodatage RFC 3161,
validité Authenticode et présence du certificat d'horodatage sont demandés.

La couverture prévue inclut les fichiers accessibles `.exe`, `.dll`, `.pyd`,
le binaire principal, le sidecar, le désinstalleur NSIS et les installeurs finaux.
La vérification de chaque fichier passé au callback précède son empaquetage.
**Cette couverture ne traverse pas le onefile.** La suite proposée est :
passer Windows en onedir, adapter les ressources et le lancement, signer tout
le dossier avant Tauri, puis contrôler les fichiers réellement installés.
Aucune migration ni promesse de disparition immédiate de SmartScreen dans ce lot.

## Licences trouvées et conséquences

L'inventaire conservateur comprend **1 326 entrées** : 578 crates Cargo,
515 entrées npm, 211 entrées Python/roues et 22 suppléments natifs. Il comprend
les outils de développement, variantes d'OS et paquets GPU présents dans les
verrous, même quand ils ne sont pas livrés. Les 800 textes distincts sont
dédupliqués ; le fichier final fait **5 659 471 octets**. Les archives SRI/SHA-256
sont vérifiées sans exécuter de paquet ni extraire de chemin sur le système.

| Composant | Licence et effet à prendre en compte |
| --- | --- |
| `piper-tts 1.4.2`, `recurring-ical-events 3.8.0` | GPL-3.0-or-later : conserver licences/attributions et fournir les sources correspondantes des binaires distribués |
| FFmpeg des roues `av 17.1.0` | La déclaration BSD de PyAV ne couvre pas tous les binaires. Les roues contiennent notamment x264 et x265 ; le chemin GPL de FFmpeg s'applique lorsqu'il est construit avec ces composants |
| x264 et x265 des trois roues PyAV inspectées | GPL-2.0-or-later ; clauses « any later version » vérifiées dans les en-têtes source amont ; sources exactes et recette de construction des roues à conserver |
| espeak-ng dans Piper | GPL-3.0-or-later ; texte et provenance du supplément présents, correspondance exacte des sources natives à compléter |
| `x-wr-timezone 2.0.1` | LGPL-3.0-or-later : sources de la bibliothèque et modalités de remplacement/reliaison à vérifier pour le mode onefile |
| LAME, GnuTLS, Nettle, GMP, libunistring, libiconv, ALSA | Textes LGPL et alternatives GPL lorsqu'elles existent ; versions natives et attributions signalées pour revue |
| `caldav 2.2.3` | GPL-3.0-or-later **OU Apache-2.0** : la présence d'une alternative GPL ne rend pas la GPL obligatoire si l'autre option est valablement retenue |
| `r-efi 5.3.0` | MIT **OU** Apache-2.0 **OU** LGPL-2.1-or-later ; même distinction entre choix et obligation |
| PyInstaller et runtime GCC | Textes GPL accompagnés d'exceptions de redistribution ; ne pas les traiter comme une GPL sans exception |
| THÉRÈSE | AGPL-3.0-only, licence propre du projet conservée. Aucune dépendance distincte AGPL déclarée n'a été identifiée ; le détecteur AGPL est testé |

Le contrôle remonte également des textes GPL/LGPL dans les notices de lxml,
NumPy, SciPy, Pillow Windows, Torch, pywin32, setuptools et des hooks PyInstaller.
Ces alertes portent sur les textes collectés, notamment ceux des sous-composants
et des outils de construction ; elles ne changent pas automatiquement la
licence du paquet principal. Les exceptions et alternatives doivent être lues
au niveau du composant concerné.

Le simple envoi du code THÉRÈSE ne remplace pas les sources des bibliothèques
GPL/LGPL. Les liens amont des notices ne constituent pas une offre complète de
sources. La voie à préparer pour la bêta est un corpus des sources exactes,
patches et recettes des composants redistribués, disponible avec la version,
et une vérification des conditions de remplacement LGPL. Les modèles de voix
et données téléchargés séparément sont hors verrous et hors inventaire.

Sources primaires consultées : [PyInstaller et la signature onefile](https://pyinstaller.org/en/stable/feature-notes.html#macos-binary-code-signing),
[Apple et la notarisation](https://developer.apple.com/documentation/security/customizing-the-notarization-workflow),
[Microsoft Artifact Signing](https://learn.microsoft.com/en-us/azure/artifact-signing/quickstart),
[licences FFmpeg](https://ffmpeg.org/legal.html),
[redistribution des binaires selon GNU](https://www.gnu.org/licenses/gpl-faq.html#UnchangedJustBinary),
[ressources Tauri et récursion des répertoires mappés](https://v2.tauri.app/develop/resources/).

## Validation Linux

Des tests rouges ont précédé les implémentations : générateur absent, chaîne
absente, ordre de publication, ressource Linux oubliée, publication incomplète,
roue CPU absente, inspection des notices et bibliothèque Mach-O rangée comme
donnée. Un cas AUTHORS seul a également été refusé avant ajout des textes.

- **Pytest ciblé final de la reprise : 41 réussis**, scripts du lot, 16 tests existants du manifeste
  updater et la sentinelle du dossier moteur Linux, avec `--noconftest` pour ne pas charger le backend inutilement.
  Les 40 contrôles hérités ont d'abord été rejoués avec succès ; un nouveau test
  rouge a révélé qu'une notice en CRLF était acceptée par le contrôle de fraîcheur.
  La comparaison porte maintenant sur les octets, et le générateur impose
  UTF-8/LF indépendamment de l'OS. Ce test passe après correction.
- **Vitest ciblé : 24 réussis**, 3 fichiers (ressources du guide, ouverture du
  guide dans le navigateur de fichiers et comportement d'installation updater).
- **Licences :** `refresh`, `generate`, puis `check` réussis. Contre-épreuves
  réelles : fichier déplacé → code 1 ; contenu périmé → code 1 ; restauration →
  code 0. Aucune suppression utilisée pour ces contre-épreuves.
  À la reprise, `generate` puis `check` passent et restituent exactement les
  mêmes octets que le fichier versionné (empreinte SHA-256 inchangée).
  `check` passe aussi avec une locale ASCII et le mode UTF-8 implicite de Python
  désactivé, ce qui contrôle l'encodage explicite des lectures.
- **Workflows :** quatre YAML parsés ; `actionlint 1.7.7` installé dans le seul
  arbre de travail, archive vérifiée par les sommes officielles. Zéro diagnostic
  de syntaxe/expression sur les deux workflows modifiés. Avec ShellCheck activé,
  16 diagnostics existants, également reproduits sur les fichiers de départ.
  Comparaison refaite à la reprise avec `origin/main` : mêmes 16 diagnostics,
  aucun nouveau. Les contenus des configurations n'ont pas été affichés.
- **Updater :** signature réelle d’un petit fichier avec une clé jetable et
  la CLI Tauri installée ; variables d’authentification du signer vérifiées,
  aucune publication ni utilisation de la clé de release.
- **Ruff :** scripts et tests du lot sans diagnostic. **TypeScript :**
  `tsc --noEmit` réussi. **Git — rectificatif :** l'affirmation initiale
  « diff --check réussi » ne caractérisait pas le diff soumis. Sur le premier
  tour, `git diff --check 08d0a8a0` retourne 2 : 1 322 espaces finaux,
  12 signalements `leftover conflict marker`, un espace avant tabulation et
  une ligne blanche finale, tous dans `THIRD_PARTY_LICENSES`. Les espaces et
  séparateurs proviennent des textes amont ; ces séparateurs ne sont pas des
  conflits Git non résolus. Le contrôle du reste du dépôt est explicitement
  `git diff --check 08d0a8a0 -- . ':!THIRD_PARTY_LICENSES'`. Aucune règle globale
  Git n'est assouplie. Le rapport du deuxième tour donne le nouveau décompte.
- **Pytest complet : 6 378 cas**, dont **6 354 réussis, 5 échecs, 15 ignorés et
  4 xfail**, en 2 496,165 s. Commande : `.venv/bin/python -m pytest -q`
  avec données, fichiers temporaires et JUnit dans l'arbre. Deux échecs étaient
  les contrats du pipeline (`includeUpdaterJson`) et du répertoire récursif de
  ressources : corrigés et inclus dans les 41 contrôles verts. Un échec était
  dû à Torch absent, un autre au `--basetemp` placé à côté de `TMPDIR` et donc
  non reconnu comme profil temporaire par le test B-748. Le test RGPD de purge
  Qdrant échouait dans la suite mais réussit en isolation ; l'interaction de
  suite n'est pas corrigée ici. Reprise ciblée des trois cas avant l'interruption, avec Torch CPU installé et les dossiers sous
  `TMPDIR` : **3 réussis**, sans modification du code métier. La suite complète
  backend n’a pas été relancée et n’est pas présentée comme entièrement verte.
- **Vitest complet, première exécution : 3 943 tests dans 904 fichiers**, dont
  **3 942 réussis et 1 échec** : le test du guide supposait une liste de ressources.
  Il contrôle maintenant les destinations de la table. Les 24 tests ciblés
  passent après correction. La seconde suite complète a été coupée par le
  redémarrage de la machine, sans bilan final.
  À la reprise, une tentative depuis la racine avec `--root src/frontend` a été
  interrompue : cette option ne change pas le répertoire de travail des tests.
  Un contrôle ciblé a donné 1 réussite et 1 échec `ENOENT` sur une lecture
  relative du test du guide. Cette tentative n'a pas de bilan complet et n'est
  pas comptée comme une validation. La relance finale part de `src/frontend`.
- **Vitest complet à la reprise : 3 943 tests dans 904 fichiers**, dont
  **3 911 réussis et 32 échecs**, en 2 566,51 s. Les échecs concernent 28 fichiers :
  26 dépassements du délai de 5 secondes et 6 attentes ou assertions d'interface.
  Le poste était fortement chargé ; ce résultat n'est pas
  présenté comme une suite verte. Les tests du guide modifiés dans ce lot passent.
  **Reprise des seuls 32 cas échoués : 31 réussis, 1 échec restant et 75 autres
  cas ignorés par le filtre**, avec un worker et `--testTimeout=20000`, sans
  modification du code ni des tests, en 200,706 s. L'échec restant est
  `src/components/prototype/ConversationCanvasPrototype.paletteDonnees.p016.test.tsx`,
  cas « P-148 : le projet choisi ouvre sa fenêtre, plus la liste des projets » :
  la boîte de dialogue du projet attendu n'est pas trouvée. Ce fichier et le
  composant concerné ne sont pas modifiés par le lot. La suite frontend complète
  n'est donc pas présentée comme entièrement verte, même après cette reprise.
  Preuves : `vitest-resume-frontend.json`, `vitest-resume-failures-summary.json`
  et `vitest-resume-failed-recheck.json` dans `.work-t2/evidence/`.
- **Cargo, packaging réel Tauri, E2E natifs : non lancés**. Cargo et PowerShell
  ne sont pas disponibles sur ce poste ; aucune machine macOS/Windows n'est
  disponible. Cela ne vaut pas validation des binaires de release.
- **Inspection Debian synthétique : 3 cas réussis**, notice présente acceptée,
  notice périmée et notice manquante rejetées par le vrai parcours `dpkg-deb`
  du script. Ce petit paquet de test n'est pas l'installeur THÉRÈSE.

Les preuves locales restent dans `.work-t2/evidence/`, ignoré par Git ; elles
contiennent notamment les JUnit pytest, JSON Vitest et journaux de contrôles.
Les dépendances et caches d'installation restent dans l'arbre de travail.
L'environnement Python initial était sans Torch/CUDA ; Torch CPU 2.9.1 a
ensuite été installé pour reprendre le contrôle d'import qui avait échoué.
Aucun modèle d'embedding réel n'est chargé par ce test, qui remplace son constructeur.

Commandes principales de la reprise, depuis la racine (les sorties sont
conservées sous `.work-t2/evidence/`) :

```bash
TMPDIR="$PWD/.work-t2/tmp" .venv/bin/python -m pytest --noconftest \
  scripts/tests tests/test_b1111_manifeste_updater.py \
  tests/test_sentinelles_structure.py::TestEmpaquetage::test_le_paquet_linux_embarque_les_bibliotheques_du_backend \
  -q --basetemp="$PWD/.work-t2/tmp/pytest-resume-final" \
  --junitxml=.work-t2/evidence/pytest-resume-final.xml
(
  cd src/frontend
  TMPDIR="$PWD/../../.work-t2/tmp" npm_config_cache="$PWD/../../.work-t2/cache/npm" \
    node node_modules/vitest/vitest.mjs run --reporter=default --reporter=json \
    --outputFile.json="$PWD/../../.work-t2/evidence/vitest-resume-frontend.json"
)
python3 scripts/third_party_licenses.py generate
python3 scripts/third_party_licenses.py check
.work-t2/actionlint -shellcheck= -pyflakes= .github/workflows/ci.yml .github/workflows/release.yml
```

Écart à la règle de lecture seule hors de l'arbre : au moins quatre commandes
`npm test` ont écrit leurs journaux usuels dans `~/.npm/_logs` faute de redéfinir
le cache pour ces commandes. Leurs contenus n'ont pas été affichés et ils n'ont
pas été déplacés ou supprimés. Les caches **d'installation** avaient bien été
redirigés dans l'arbre. À la reprise, les outils Node sont appelés directement,
avec répertoires temporaires et cache npm explicitement placés dans l'arbre.

## Ce que le premier passage CI doit montrer

1. Sans Apple, tous les objets du moteur, le sidecar, le bundle et le DMG doivent
   passer la vérification ad hoc stricte. Le journal donne le nombre réel de
   Mach-O réextraits. La recette existante du sidecar doit atteindre `/health`.
2. Avec Apple, le trousseau doit être disponible dès PyInstaller ; les signatures
   internes portent la bonne Team ID et le runtime renforcé. Les deux
   soumissions doivent être acceptées, le bundle et le DMG agrafés,
   `stapler validate` et `spctl` réussis. Une erreur doit empêcher l'envoi des
   artefacts de ce runner au brouillon.
3. Sans Microsoft, les étapes de signature sont sautées explicitement, NSIS et
   MSI sont construits et leurs notices extraites sont identiques. Avec les
   secrets, signatures et horodatages des fichiers accessibles sont valides.
   L'installation réelle doit contrôler le désinstalleur, les fichiers déposés
   et les DLL auxiliaires. Les DLL/.pyd du onefile restent la limite connue.
4. La notice du `.deb`, du bundle macOS et des deux conteneurs Windows doit être
   identique au fichier versionné. La première CI doit confirmer les chemins
   effectivement produits par Tauri et la capacité de 7-Zip à lire NSIS.
5. Les signatures updater doivent correspondre aux **octets finaux** : tester
   une mise à jour macOS et Windows et le manifeste construit après la matrice.
   Les artefacts conservent les noms attendus, dont l'archive macOS aarch64.
6. Sur machines réelles : Mac sous quarantaine, micro, trousseau, passage de
   l'alpha à la version signée ; Windows avec Smart App Control/SmartScreen.
   Aucun de ces essais n'est prétendu validé ici.

## Points douteux et travaux restants

- 16 paquets sans texte amont exploitable à leur commit utilisent les textes
  normatifs SPDX des licences déclarées ; leurs attributions doivent être
  revues. Les 22 suppléments natifs portent aussi une réserve sur leur
  rapprochement avec les versions et recettes exactes. Les réserves figurent
  **dans le fichier livré**, pas seulement dans ce rapport.
- La collecte des dépendances verrouillées et de ces roues n'est pas un audit
  exhaustif de chaque fichier d'un bundle réel (runtime Python, bibliothèques
  système, ressources téléchargées séparément).
- La signature réelle, l'acceptation Apple, PowerShell/Authenticode et
  l'inspection des installeurs ne peuvent être éprouvés sur ce poste Linux.
- Le moteur Windows onefile n'est pas complètement signé. Il ne faut pas
  annoncer que l'application est compatible Smart App Control sur cette base.
- Le test frontend d'ouverture d'une fiche projet par la palette reste en échec
  après reprise isolée ; l'interaction de suite du test backend RGPD n'a pas été
  résolue. Aucun de ces parcours métier n'a été modifié dans ce lot.
- Les étapes de compilation et de signature partagent encore un job ; les
  scripts npm d'installation sont désactivés, mais l'isolation des secrets dans
  un job séparé reste à réaliser. Les fichiers sensibles temporaires supposent
  un runner GitHub hébergé éphémère, pas un runner persistant.
- Aucun compte Apple/Azure, tarif, quota, délai réel de notarisation ou droit de
  signature n'a été testé. Un jeu de secrets complet mais incorrect échoue.

## Commits et publication

Premier commit : `3fbd5cea` — « Préparer les signatures Apple et Microsoft et
embarquer les licences tierces ». Deuxième commit : `2b319960` — « Fiabiliser
les contrôles de signature et les notices multiplateformes ». Le rapport
fait l'objet d'un commit documentaire séparé. Les hooks sont désactivés pour ces
seuls commits (`git -c core.hooksPath=/dev/null commit`), afin de ne pas exécuter
le hook `post-commit` local et de respecter l'interdiction d'effet externe.
Aucun push et aucun lancement de workflow.
