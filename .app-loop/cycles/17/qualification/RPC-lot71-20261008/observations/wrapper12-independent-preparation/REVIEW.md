# WRAPPER12, revue indépendante préparatoire

Auteur : /root/cycle17_gate_review. Avis favorable à la préparation statique uniquement. Aucun constructeur, test, G1, Chrome ou instrument natif exécuté par le relecteur. Aucun ancien gel ni root modifié.

Candidat : /private/tmp/therese-c17-wrapper12-metadata-parent-MtcoJZ/PLAN-INDEX.json
SHA : e7ab1ad86f5ba0dde5dde38bb2feeb3dd31b1d53d18981ac3a9d34aa29f12a15

## Contrôles réellement effectués

Les douze références propres du gel ont été rehashées avec tailles exactes. Les diffs complets avant et inverse reconstruisent byte-exact le builder et le profil depuis leurs préimages ecca6ab6 et bee3c2e7. Le profil courant 980b1236, 2 439 octets, est strictement la préimage MAIN11 de 2 375 octets plus :

`(allow file-read-metadata (literal (param "AUXILIARY_PARENT")))`

Il s'agit d'une seule règle, 64 octets. La chaîne précédente, notamment les trois règles nominatives CARenderServer, IOSurfaceRootUserClient et AGXDeviceUserClient, demeure inchangée. Aucun droit nouveau de lecture data, subpath, écriture, réseau, Mach ou IOKit n'est ajouté. Aucune règle configd ni optimisation/deadline n'est introduite.

La dérivation G1 ajoute le paramètre uniquement dans la branche chrome de sandbox. La valeur est calculée par le contrôleur depuis root/auxiliary, résolue canoniquement et contrôlée sous root, sans valeur héritée ni clé libre du helper. La transformation ajoutée est réversible ; le seul corps G1 changé par cette addition est sandbox. Les clés existantes AUXILIARY_ROOT/HOME_ROOT/TMP_ROOT restent exactes. Les autres modes ne reçoivent pas ce paramètre.

Les trente et une autres définitions du builder sont AST-identiques. Les quatre définitions modifiées sont gather_pins, validate_indexes, checked_chrome_successor et build ; les deux nouvelles sont historical_ips_archive et g1_auxiliary_parent_delta. Les changements de build sont le retour des observations historiques et l'application explicite de la dérivation G1 ; aucun autre hunk inattendu.

## IPS historique et preuves courantes

La résolution est bornée à trois combinaisons origine/pointeur/ref anciennes :

- INDEX RootDomain c0f542c3, /origin_refs/4 ;
- reçu pur V3 c0864b43, /source_refs/267, passed=true/errors=0 ;
- reçu pur V2 1955d363, /source_refs/267, passed=false/errors=3.

Les trois sources physiques ont leurs SHA et tailles exacts. L'ancienne référence IPS est exactement 2e1d81e2/31 835 octets. Son ancien chemin est absent. La copie chrome25577.ips dans root-close6 est canonique, régulière, UID501/GID0/mode100600/nlink1 et rehashée byte-identique. Le code conserve le path réel de l'archive dans les pins, les observations distinctes et les valeurs V2 rouge/V3 vert. Il ne prétend pas que le reçu close6 atteste cette copie ni qu'elle est une preuve runtime actuelle.

Les pointeurs ordinaires continuent leur chemin strict ; une autre origine, un autre pointeur, une ancienne ref différente ou une autre référence absente ne bénéficie pas d'une exemption générique.

## Tests, autorité et limites

Les tests, README et deux comptes rendus purs auteur ont été lus intégralement. Neuf tests sont rapportés verts après un premier rouge sur les seuls timestamps des en-têtes diff. Les hunks et chemins restent comparés en entier. Ces logs sont des comptes rendus condensés auteur ; aucun rejeu indépendant n'a été effectué dans cette revue.

La future racine /private/tmp/therese-c17-wrapper-canary-9818b6b4163e451892dbd3956e1bb492 était absente lors de notre contrôle à 2026-10-08T21:17:38.205032+00:00. Le builder garde --prepare et autorité externe exacte avant allocation. Aucun GO ou root n'a été produit par cette revue.

La préparation utilise le checkout historique WRAPPER HEAD2d69 et ne constitue pas une admission au HEAD courant, une ronde A/B, une preuve UI/CDP ni une release. Le profil n'a pas été compilé ici. L'effet du seul nouveau droit sur le refus Chrome reste inconnu avant un essai natif distinct réellement autorisé.

Les vingt références de cette revue avec SHA/tailles figurent dans receipt.json. Aucun artefact source n'a été changé.
