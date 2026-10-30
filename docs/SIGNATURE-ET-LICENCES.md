# Signature et licences

État au 29 octobre 2026. La release fonctionne sans compte Apple ou Microsoft :
macOS utilise une signature ad hoc vérifiée, Windows reste sans Authenticode.
L'absence d'un secret de plateforme ne fait pas échouer le build. Une configuration
complète mais invalide, une signature incorrecte ou une notarisation refusée fait
en revanche échouer la release avant l'envoi des fichiers au brouillon GitHub.
La signature cryptographique de l'updater Tauri reste obligatoire et indépendante.

## Chaîne macOS

1. `scripts/sign_macos.py prepare` importe le certificat dans un trousseau du
   runner **avant PyInstaller**, seulement lorsque les six secrets Apple sont
   présents. Il prépare le profil `notarytool`. Sinon, l'identité devient `-`.
2. `backend.spec` transmet cette identité et `Entitlements.plist` à PyInstaller.
   Chaque bibliothèque native est signée après réécriture de ses chemins et
   avant compression dans le moteur onefile. Le runtime renforcé est activé,
   y compris en ad hoc. Signer uniquement l'exécutable extérieur ne suffit pas.
3. `verify_embedded_macos.py` réextrait tous les Mach-O internes, vérifie leurs
   signatures avec `codesign --verify --deep --strict`, leurs entitlements,
   le runtime renforcé et, en mode Developer ID, la Team ID attendue. Le nombre
   réel est journalisé ; zéro binaire vérifié est une erreur.
4. Après Tauri, signature des Mach-O et bundles imbriqués par profondeur
   décroissante, puis du bundle principal. `--deep` sert à **vérifier**, jamais
   à déléguer la signature. Aucun lien symbolique n'est re-signé.
5. Avec Apple : soumission du bundle dans un ZIP, attente de `Accepted`,
   agrafage du bundle et `spctl --assess --type execute`.
6. Reconstruction du DMG à partir de ce bundle, avec le lien Applications,
   signature du DMG, puis soumission **du DMG lui-même**, agrafage et validation.
   Sans Apple : signature ad hoc et vérification stricte du DMG, sans appel
   réseau à la notarisation ni attente d'une acceptation Gatekeeper.
7. Recréation de l'archive updater depuis le bundle final ; les signatures
   updater sont recalculées sur ces octets avant publication. Les recettes
   et les contrôles des licences précèdent également la publication.

Le plafond du job est de 150 minutes ; chaque soumission Apple attend au plus
45 minutes. Le DMG reconstruit a une présentation simple, avec l'app et le lien
Applications. Le runner hébergé est éphémère ; le trousseau et le P12 sont dans
son répertoire temporaire, jamais archivés. Ne pas réutiliser cette procédure
sur un runner persistant sans définir la gestion de ces fichiers sensibles.

`Entitlements.plist` conserve `com.apple.security.cs.disable-library-validation`
pour le moteur Python, notamment nécessaire avec les bibliothèques ad hoc, et
ajoute `com.apple.security.device.audio-input` pour le micro. L'exception de
validation reste aussi appliquée à l'interface par Tauri ; son retrait pour le
mode Developer ID demande une recette réelle. Aucune exemption JIT ou mémoire
exécutable non signée supplémentaire n'est ajoutée sans preuve de nécessité.

## Créer les secrets Apple

Dans GitHub, enregistrer les secrets du dépôt, sans modifier les fichiers du
projet ni y copier de certificat ou de mot de passe :

| Nom | Contenu attendu |
| --- | --- |
| `APPLE_CERTIFICATE` | Export P12 du certificat **Developer ID Application** et de sa clé privée, encodé en base64 |
| `APPLE_CERTIFICATE_PASSWORD` | Mot de passe non vide de cet export |
| `APPLE_SIGNING_IDENTITY` | Nom exact de l'identité Developer ID Application |
| `APPLE_ID` | Compte Apple autorisé à notariser pour l'organisation |
| `APPLE_PASSWORD` | Mot de passe **spécifique à l'application**, créé pour la notarisation |
| `APPLE_TEAM_ID` | Identifiant de l'équipe Apple Developer |

Ludo inscrit l'organisation à l'[Apple Developer Program](https://developer.apple.com/programs/enroll/)
avec les justificatifs demandés, dont le D-U-N-S pour une organisation. Depuis
un Mac, le titulaire du compte crée le certificat Developer ID Application,
avec une CSR et sa clé privée dans le trousseau, puis exporte l'identité en P12
protégé. Suivre la [procédure Apple du certificat](https://developer.apple.com/help/account/certificates/create-developer-id-certificates/).
Le compte Apple doit avoir l'authentification à deux facteurs ; créer ensuite
le mot de passe spécifique à l'application dans la gestion de ce compte.
Cette implémentation choisit l'authentification Apple ID de `notarytool` ; les
secrets API App Store Connect ne sont pas consommés.

Une saisie partielle revient explicitement à l'ad hoc. Lorsque les six secrets
existent, l'activation est automatique au prochain build autorisé. L'ad hoc ne
prouve ni l'identité de l'éditeur ni l'acceptation par Gatekeeper. Référence :
[notarisation et agrafage Apple](https://developer.apple.com/documentation/security/customizing-the-notarization-workflow).

## Signature Windows et limite du onefile

L'action officielle [Azure/artifact-signing-action](https://github.com/Azure/artifact-signing-action)
est épinglée à `b443cf8ea4124818d2ea9f043cba29fc3ec47b16` (référence `v1`
résolue pendant ce lot). Elle signe récursivement les `.exe`, `.dll`, `.pyd`
accessibles avant empaquetage, puis les installeurs finaux, dont les `.msi`.
Le callback `signCommand` de Tauri utilise le même module Microsoft
`TrustedSigning` **0.5.8**, installé par cette action : l'exécutable principal,
le sidecar, le désinstalleur NSIS et les installeurs passent ainsi par la
signature avant leur inclusion dans les conteneurs. Toute évolution de
l'action doit aussi faire réviser cette version du module et ses paramètres.

SHA-256 et un horodatage RFC 3161 sont demandés. `Get-AuthenticodeSignature`
contrôle la validité et la présence de l'horodatage ; le callback vérifie aussi
chaque fichier reçu de Tauri. Sans les six secrets Microsoft, l'action et le
callback sont désactivés, et la limite est annoncée dans le journal.

**Limite non corrigée :** le backend Windows reste un fichier unique
PyInstaller. Les DLL et `.pyd` compressés dedans, extraits au lancement, ne sont
pas atteignables par cette action. Une signature valide de `backend.exe` ou de
l'installeur ne signe pas ces bibliothèques. La chaîne Windows n'est donc pas
une garantie de compatibilité avec Smart App Control. Le prochain lot doit
passer Windows en **onedir**, adapter les chemins de lancement et les ressources
Tauri, puis signer chaque PE avant empaquetage et vérifier les fichiers installés
sur un vrai Windows. Cette migration n'est pas réalisée ici. Vérifier également
les DLL auxiliaires de l'installeur et son désinstalleur sur une installation réelle.
Une signature nouvelle ne promet pas la disparition immédiate de SmartScreen.

## Créer les secrets Microsoft

Créer un abonnement Azure et un compte Artifact Signing, faire valider l'identité
de Synoptïa, puis créer un profil **Public Trust**. Choisir la région du service
et garder son endpoint associé. La procédure officielle couvre ces opérations :
[configuration d'Artifact Signing](https://learn.microsoft.com/en-us/azure/artifact-signing/quickstart).
Créer une application Entra ID et son principal de service, puis attribuer à ce
principal le rôle **Artifact Signing Certificate Profile Signer**, au périmètre
du profil utilisé. Le rôle Owner seul ne donne pas le droit de signer : voir
[les rôles Microsoft](https://learn.microsoft.com/en-us/azure/artifact-signing/tutorial-assign-roles).
Créer un secret client avec une échéance et organiser son renouvellement.

| Nom GitHub | Contenu attendu |
| --- | --- |
| `AZURE_TENANT_ID` | Identifiant du tenant Entra |
| `AZURE_CLIENT_ID` | Identifiant de l'application Entra |
| `AZURE_CLIENT_SECRET` | Secret client du principal de service |
| `AZURE_SIGNING_ENDPOINT` | Endpoint régional Artifact Signing |
| `AZURE_SIGNING_ACCOUNT` | Nom du compte Artifact Signing |
| `AZURE_CERTIFICATE_PROFILE` | Nom du profil Public Trust |

La présence des six secrets active la chaîne. Les autres méthodes de connexion
Azure sont désactivées pour éviter l'emploi involontaire d'une identité du runner.
Aucun secret ni jeton n'est requis pour les tests Linux du lot. Les installations
npm de release utilisent `--ignore-scripts`, mais les builds Rust et les outils
de packaging restent dans le job de signature : l'isolation dans un job dédié
reste une amélioration à faire, pas une propriété de cette version.

## Générer et contrôler les licences

`THIRD_PARTY_LICENSES` est une ressource Tauri nommée ainsi dans les quatre
formats distribués : app/DMG macOS, NSIS et MSI Windows, paquet Debian Linux.
La surcharge Linux conserve explicitement cette ressource. La CI vérifie le
fichier versionné ; la release compare aussi les notices extraites des deux
installeurs Windows, du `.deb`, du DMG et de l’archive updater macOS, octet pour octet.
Toute AppImage produite est aussi inspectée ; la release actuelle ne demande que `deb`.

```bash
# Après un changement de verrou : réseau requis, aucun paquet exécuté.
python scripts/third_party_licenses.py refresh
# Régénération déterministe depuis l'instantané versionné, hors réseau.
python scripts/third_party_licenses.py generate
# Contrôle de release : couverture, textes, attributions et fraîcheur, hors réseau.
python scripts/third_party_licenses.py check
python -m unittest discover -s scripts/tests -p 'test_*.py'
```

Les entrées d’empreinte et le fichier livré sont forcés en LF par `.gitattributes`,
pour garder les mêmes empreintes lors d’un checkout Windows.
Le générateur lit explicitement en UTF-8 et écrit en UTF-8/LF sur chaque OS.
Le contrôle compare les octets : une notice réécrite en CRLF est refusée.

Python 3.11 ou ultérieur suffit au générateur. Ses tests de pipeline demandent
PyYAML. Les verrous npm racine et frontend, Cargo et uv sont couverts de façon
conservatrice : développement, variantes d'OS et dépendances GPU non embarquées
figurent aussi dans l'inventaire. Ce document n'est donc pas un inventaire des
seuls fichiers effectivement installés.

`licenses/inventory.json` conserve textes, chemins d'origine et empreintes des
archives. Le téléchargement vérifie les SHA-256/SRI des verrous ; aucune archive
n'est extraite sur le système et aucun code de dépendance n'est exécuté. Les
textes identiques sont dédupliqués dans le document final. Les archives sans
conditions complètes demandent une entrée explicite dans `licenses/overrides.json`.
Un simple lien, une attribution seule ou un texte contenant TODO ne satisfait
pas le contrôle. Les textes supplémentaires de `licenses/supplements/` sont
vérifiés par SHA-256 et inclus dans l'empreinte des verrous. Les attributions
propres aux versions et leurs preuves figurent dans `licenses/attribution-sources.json`.
Une métadonnée auteur est identifiée comme telle ; aucune année ni titularité
de copyright n'est inventée. Les nouveaux textes sont au besoin sérialisés en chaînes JSON pour conserver
leurs espaces et séparateurs amont à l’identique.

`refresh` applique les suppléments même lorsqu'une archive a déjà une notice.
Le contrôle exige le texte intégral de **chaque licence nommée** dans une
expression, y compris avec `OR` ou `/` : une MIT complète ne couvre pas un
simple renvoi Apache. Un identifiant inconnu reste refusé.
`generate` peut produire un document de travail **PROVISOIRE**, qualifié dès sa
première ligne avec la liste des entrées à compléter. `check`, appelé par la
CI et la release, le **refuse** tant qu'une attribution manque ou contient un
champ générique sans preuve admise. L'exemple Apache est exempté uniquement
après son paragraphe normatif complet, y compris dans sa présentation RTF ;
une occurrence identique dans un autre composant reste refusée. Les exemples
GNU et FreeType sont également circonscrits à leurs passages pédagogiques et
restent intacts dans les textes livrés.

Le statut **« texte amont reproduit tel quel »** est accordé fichier par fichier
et entrée par entrée dans `licenses/attribution-sources.json` (`upstream-verbatim`).
Il conserve les champs génériques écrits par l'amont ainsi que les copyrights
nommés. Chaque preuve porte l'URL et l'empreinte de l'archive verrouillée,
le chemin interne, le SHA-256 du fichier, les numéros et textes exacts des lignes
concernées et le SHA-256 du texte livré. `check` lie la preuve à l'entrée et
reconstitue les octets du fichier interne (LF/CRLF, blancs aux extrémités)
pour vérifier aussi son empreinte. Une modification du texte, d'une ligne ou
de l'empreinte invalide l'exception. Aucun supplément local ou texte partagé
n'obtient ce statut. Les archives ont été vérifiées lors de l'établissement
des preuves ; `generate` et `check` restent hors réseau.

Au quatrième tour du 29 octobre 2026, les neuf crates objc2 0.3.2 reçoivent
le statut explicite **« aucun titulaire nommé en amont »**
(`no-holder-named-upstream`), accordé séparément à chaque entrée. Ce statut
requiert la preuve de `licenses/attribution-sources.json` : archive verrouillée
vérifiée, commit lu dans `.cargo_vcs_info.json`, recherche dans tous les fichiers
de la crate et de l'arbre amont, empreintes des textes livrés. Les archives
intégrales conservées dans `licenses/evidence/` permettent de répéter le contrôle
hors réseau. Les 1 606 fichiers ordinaires et les 191 liens symboliques de l'arbre
sont lus ; la portée d'une crate inclut les sources générées visées par ses liens.
Les occurrences d'API, de prose et les auteurs d'autres crates restent consignés,
avec zéro occurrence attribuant la crate. Une nouvelle ligne nominative dans la
crate ou ses sources générées invalide la preuve, même avec des hashes recalculés.

Depuis le cinquième tour, `attribution_evidence.py` autorise seulement les neuf
triplets nom/version/commit listés dans son code, avec le SHA-256 de référence
de l'arbre objc2 vérifié (`a6685e9b30da4c2b9ed807e8344d7248447daf1d5ab5b7af4fa3755545f96a4d`).
Le nom et la version des deux manifestes Cargo doivent correspondre à l'identité
de l'entrée ; une version héritée est résolue dans le workspace de cet arbre.
`AUTHORS`, `CONTRIBUTORS`, `MAINTAINERS`, les titres d'auteurs seuls et les
commentaires `///`, `//!`, `#`, `*` sont également pris en compte.

Les textes intégraux de toutes les licences déclarées et de `LICENSE.md` sont
conservés, puis une phrase distincte du copyright indique l'absence de titulaire
et l'auteur déclaré du workspace, Mads Marquart. Cette métadonnée n'est jamais
transformée en titulaire. Sans ce statut et sa preuve exacte, toute attribution
manquante reste bloquante. Les neuf réserves sont levées pour ce motif précis.

Le contrôle de couverture a aussi fait compléter **45 entrées**, dont
`android_system_properties 0.1.5`, `shlex 1.3.0` et `tqdm 4.67.1`, sans supprimer
leurs notices ni leurs attributions originales. Voir le rapport du troisième
tour pour la liste exhaustive et les résultats des suites.

Une réserve de rapprochement des binaires (`review_required`) reste distincte
d'une attribution manquante (`attribution_missing`) ; elle n'est pas une
validation de redistribution. L'ajout d'un supplément conserve ces deux
réserves ; leur levée doit être explicite. Pour PyAV 17.1.0, les versions SVT-AV1 4.1.0,
libXau 1.0.9, libxcb 1.13.1 et libdrm 2.4.115 sont reliées aux binaires des roues,
aux recettes et aux licences amont par des preuves versionnées. SVT-AV1 est
déclaré `BSD-3-Clause-Clear`, conformément à cette version.

Des roues natives des trois plateformes complètent les archives source. Les
roues Torch CPU CPython 3.13 sont verrouillées dans
`licenses/runtime-wheels.lock.json` et installées par leur URL **avec empreinte**.
Le script refuse un décalage de version avec uv. Les dépendances natives
repérées dans PyAV et Piper, que les métadonnées Python ne décrivent pas toutes,
sont consignées dans `licenses/native-components.lock.json`. Leurs textes sont
épinglés ; le manifeste des sources correspondant au quatrième tour complète
le rapprochement des composants copyleft avec leurs recettes de construction.

## Bibliothèques du système de build (tour 6)

Les verrous npm/Cargo/uv ne décrivent pas les bibliothèques que PyInstaller copie
depuis Ubuntu. `licenses/system-libraries.lock.json` complète ces verrous :
**18 bibliothèques**, dont **17 fichiers de 16 paquets binaires Ubuntu 22.04**,
et libpython CPython 3.13.17 de setup-python. Les 13 notices originales et le
rapprochement du complément v0.82.0 sont conservés dans `licenses/system-linux/`.
Le générateur les ajoute à `THIRD_PARTY_LICENSES`, avec les textes GNU complets.

Le spec enregistre la provenance de tous les fichiers natifs trouvés par Analysis,
y compris ceux classés comme données. Après PyInstaller et la signature du moteur,
`system_libraries.py inventory --platform <Linux|macOS|Windows>` parcourt les
binaires réels (onedir ou contenu onefile). Il reconnaît ELF, Mach-O et PE par leurs
octets, rapproche les roues de leur RECORD et des versions de l'inventaire, les
extensions CPython de leur origine lib-dynload et version, et les bibliothèques
Ubuntu par **SHA-256 et identité dpkg** (paquet et source, versions exactes).
Le nom/SONAME seul n'autorise jamais une bibliothèque système.

Le résultat `.work-release/system-libraries.json` est une ressource Tauri.
`verify_packaged_licenses.py` lit chaque installeur final et exige les mêmes
notices, le même inventaire et les mêmes octets natifs. Un ajout par l'empaqueteur
Linux est également rapproché du catalogue et des paquets du runner. Une
bibliothèque inconnue ou modifiée arrête la release. Chaque artefact reçoit une
preuve JSON avec son SHA-256 et son inventaire ; le publieur vérifie cette preuve
avant de joindre les fichiers au brouillon. Les preuves sont jointes à la release.

Le catalogue est fermé sur les versions relues : un changement du runner peut
faire échouer la garde. Le relevé `system-libraries-unreviewed.json` conserve alors
les fichiers et candidats dpkg à examiner. Pour mettre à jour le catalogue,
rapprocher les **octets** du nouveau build des membres des paquets binaires,
contrôler leurs notices et leurs paquets source exacts (index de distribution
signés), puis réviser catalogue, preuve et empreintes ensemble. Ne pas contourner
le contrôle en conservant un nom sous une autre version. Les entrées CPython et
les règles de licence relues dans le script doivent également être actualisées.

Le complément exige les sources de **readline 8.1.2-1**, **gdbm 1.23-1** et
**glibc 2.35-0ubuntu3.15** : 11 fichiers, 23 299 768 octets (dsc, orig, correctifs
Debian/Ubuntu et signatures amont). Le job de sources les assemble et joint
`THERESE-sources-systeme-linux.tar.gz` avant les installeurs. Le catalogue couvre
également les licences permissives et l'exception GCC des autres fichiers.

```bash
python scripts/system_libraries.py check
python scripts/system_libraries.py assemble-sources .work-t2/sources-systeme-linux
```

macOS et Windows : la garde sait ouvrir le contenu natif du moteur onefile et
comparer les DMG/archive updater ou MSI/NSIS. **Le catalogue de bibliothèques
hors roues actuellement relu est Linux seulement.** La première CI macOS/Windows
peut donc refuser des composants comme OpenSSL, ncurses, Python.framework,
python313.dll ou les runtimes Microsoft : il faut alors établir leurs versions,
notices et preuves, pas les assimiler globalement à Python. Le complément relu
indique que libedit reste liée au système macOS et n'est pas embarquée ; ce constat
v0.82.0 ne dispense pas de scanner le prochain build. Les binaires auxiliaires
introduits par NSIS/AppImage ne bénéficient d'aucune exemption implicite.
Ces extracteurs et la reliaison ne sont pas validés par un build de plateforme ici.

La méthode de reconstruction et de remplacement LGPL est dans
[`licenses/LISEZMOI-SOURCES.txt`](../licenses/LISEZMOI-SOURCES.txt), incluse dans
les deux archives. Elle couvre les paquets source Ubuntu, libmvec et la copie
privée du moteur Linux, ainsi que la reconstruction nécessaire des onefile.
La reliaison fonctionnelle reste à démontrer sur une vraie construction.

## Copyleft et travail avant diffusion publique

Piper et recurring-ical-events déclarent **GPL-3.0-or-later** ; x-wr-timezone
**LGPL-3.0-or-later**. Les roues PyAV 17.1.0 contiennent notamment FFmpeg, x264 et
x265, repérés dans les trois plateformes. Le BSD déclaré par le paquet Python
ne décrit donc pas à lui seul les obligations de ces roues. FFmpeg explique
l'effet de l'activation de composants GPL dans sa [page de licences](https://ffmpeg.org/legal.html).
Les suppléments incluent les textes GPL/LGPL de ces composants et d'espeak-ng,
LAME, GnuTLS, Nettle, GMP, libunistring et libiconv. Le runtime GCC conserve son
exception ; PyInstaller a aussi une exception de distribution à examiner avec
sa licence. Une mention GPL dans la longue notice d'un paquet permissif n'en
fait pas automatiquement un paquet entièrement GPL.

Le script signale séparément GPL, LGPL et AGPL ; la licence propre de THÉRÈSE
reste AGPL-3.0-only dans `LICENSE`. Les détections de textes sont des alertes à
qualifier, pas une décision juridique automatique. Les modèles de voix et leurs
jeux de données, téléchargés en dehors des verrous, ne sont pas couverts ici.

**Les sources correspondantes sont décrites dans `licenses/copyleft-sources.json`.**
Le manifeste rattache 27 composants aux entrées de l'inventaire, avec version,
licence, URL et SHA-256 de l'archive téléchargée. Les recettes de roues sont
épinglées au commit et leur copie locale est contrôlée. Les archives de dépôt
PyAV, pyav-ffmpeg et Piper conservent les scripts et les correctifs de construction.
La source MSYS2 libiconv 1.19-1 inclut ses trois correctifs ; ses onze sections PE
concordent avec celles de la DLL de la roue Windows. Les preuves complémentaires
figurent dans `licenses/copyleft-version-evidence.json`.

Chaque composant déclare `required_supporting_sources`, avec une liste vide
explicite si son archive source suffit. Les rattachements indispensables des
versions livrées sont aussi imposés par le code : arbres PyAV/FFmpeg pour les
dix bibliothèques d'AV, correctifs MSYS2 pour libiconv, arbre Piper pour Piper
et espeak-ng, source vendue de setuptools pour autocommand. Retirer une archive
ou sa référence bloque le contrôle. Les archives FFmpeg incluent notamment
`patches/ffmpeg.patch`, `patches/gmp.patch` et `patches/lame.patch`.

Les douze sources directement présentes dans Cargo.lock ou uv.lock sont
comparées au verrou lui-même (URL, SHA-256 et version), indépendamment de
l'inventaire. La source de soutien setuptools est aussi comparée à uv.lock. Les cinq objets
complets de soutien (URL, SHA-256, commit et autres champs) sont désormais liés
à `supporting_source_bindings` dans la preuve empreintée : une archive valide
substituée sous le nom FFmpeg ou MSYS2 libiconv est refusée avant téléchargement.
Les autres sources exigent `evidence_refs` et `recipe_refs` non vides et
résolubles. Les références peuvent désigner une recette copiée localement ou
un membre de l'archive complète (axe-core, lightningcss, setuptools).
Les `source_bindings` de la preuve empreintée fixent version, source,
rattachements, recettes et archives de soutien requises pour les 27 composants.
Ce rapprochement conserve les résultats de la revue des versions ; il ne
constitue pas une reconstruction comparative des binaires.

Le correctif amont `ffmpeg.patch` déplace x264/x265 du groupe GPL au groupe
VERSION3 de configure, et les bibliothèques annoncent LGPL-3.0. Cette étiquette
ne supprime pas les obligations GPL de ces codecs : le manifeste retient
prudemment GPL-3.0-or-later pour la combinaison et conserve le correctif exact.

```bash
# Hors réseau : couverture complète, inventaire, preuves et recettes.
python scripts/copyleft_sources.py verifier
# Téléchargements vérifiés ; réutilise uniquement les fichiers dont le hash est exact.
python scripts/copyleft_sources.py assembler .work-t2/sources-copyleft
```

Le garde refuse toute entrée copyleft sans source ou exclusion justifiée, un
inventaire périmé, une preuve modifiée, une recette absente ou une source signalée
manquante. Le manifeste couvre aussi les portions MPL détectées, `adodbapi` de
pywin32 et `autocommand` de setuptools, par prudence. Les choix Apache-2.0 pour
caldav/DOMPurify et MIT pour r-efi sont explicites. Les exceptions PyInstaller et
GCC, les hooks de construction et les notices concernant seulement des tests
sont motivés séparément ; aucune exemption ne s'applique à tout paquet permissif.

La CI et chaque build de release exécutent `verifier`. Le job `sources-copyleft`
assemble les archives, leurs recettes, le manifeste, les preuves et un
`LISEZMOI-SOURCES.txt`, puis joint `THERESE-sources-copyleft.tar.gz` au brouillon de
la même version. Les builds des installeurs dépendent de la réussite de ce job.
Un téléchargement absent ou d'empreinte différente empêche donc leur publication.
`assembler`, y compris appelé directement, valide l'ensemble avant toute
écriture ou tout téléchargement. Il refuse un manifeste incomplet. Un échec
de téléchargement ou de SHA-256 interrompt la commande avant l'écriture des
documents finaux ; les archives déjà téléchargées restent réutilisables.

La tête de `THIRD_PARTY_LICENSES` indique cette pièce jointe et l'engagement de
conservation : pendant toute la distribution des binaires, au moins trois ans
après leur dernière distribution, et aussi longtemps qu'un support ou des pièces
de rechange sont proposés pour cette version. Ce choix conservateur reprend la
borne la plus stricte de GPL-3.0 §6b ; la fourniture simultanée sur le même site
suit §6d, qui ne prescrit pas à lui seul un délai fixe de trois ans. L'exploitation
des releases doit effectivement respecter cette durée ; la CI ne peut garantir
la conservation future d'une pièce jointe.

La disponibilité des sources ne valide pas les modalités de remplacement ou de
reliaison LGPL dans le moteur onefile, ni toute la redistribution du produit.
Ces modalités et les signatures réelles restent à vérifier sur les plateformes.
Voir la [GPL-3.0, section 6](https://www.gnu.org/licenses/gpl-3.0.html#section6) et
la [FAQ GNU sur les binaires](https://www.gnu.org/licenses/gpl-faq.html#UnchangedJustBinary).

## Première CI à examiner

Sans secrets : même build macOS que pour la future signature réelle, nombre de
Mach-O internes non nul, contrôles stricts réussis, recette `/health` du sidecar
signé ; sur Windows, avertissement d'absence de signature, NSIS/MSI construits et
notices identiques ; sur Linux, notice dans le `.deb` et recette existante.
Les vérifications doivent précéder l'envoi des artefacts au brouillon.

Avec Apple : signatures Developer ID avec Team ID sur les objets internes,
deux soumissions acceptées, bundle et DMG agrafés, `stapler validate` et `spctl`
réussis. Tester ensuite sur Mac téléchargé sous quarantaine : installation,
premier lancement, micro, accès au trousseau et mise à jour depuis l'alpha.

Avec Microsoft : signatures et horodatages valides sur les fichiers accessibles,
installeurs et désinstalleur ; installation réelle et relevé des fichiers
extraits. Les DLL internes du moteur resteront une limite attendue tant que le
passage en dossier n'est pas fait. Sur les deux OS, vérifier une vraie mise à
jour avec les signatures générées **après** la dernière modification des octets.
Aucun de ces résultats de plateforme n'est revendiqué à partir des tests Linux.
