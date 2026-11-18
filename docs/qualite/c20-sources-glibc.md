# B-2059 : repli des sources Ubuntu vers Launchpad

Contrôle local du 18/11/2026, dans l'arbre `c20/sources-glibc`.
Périmètre : un correctif de l'assemblage des sources, sans publication.

## Cause

L'orchestrateur signale trois réponses 404 sur les 31 URL du verrou : les
fichiers `glibc_2.35-0ubuntu3.15.dsc`,
`glibc_2.35-0ubuntu3.15.debian.tar.xz` et
`libc6_2.35-0ubuntu3.15_amd64.deb` ont quitté le miroir principal Ubuntu.
Il indique leur disponibilité dans l'archive permanente Launchpad, avec
respectivement 8 888, 962 196 et 3 234 380 octets. Ce constat réseau vient de
l'orchestrateur et n'a pas été revérifié pendant cette intervention hors réseau.

`assemble_sources` ouvrait directement chaque URL source. Le premier 404
interrompait donc le job « Assembler et joindre les sources correspondantes ».
Les octets relus du binaire et les empreintes des sources ne sont pas remis
en cause par un changement d'adresse de téléchargement.

## Choix et comportement

Le [verrou](../../licenses/system-libraries.lock.json) et toutes les preuves
restent inchangés. Cela conserve leur comparaison exacte dans
`validate_catalog` et évite de réécrire une preuve pour résoudre un problème
de disponibilité du miroir.

Le résolveur de `scripts/system_libraries.py` calcule l'adresse permanente
à partir de `package`, `version` et `filename` verrouillés :

- Sources : `https://launchpad.net/ubuntu/+archive/primary/+sourcefiles/<paquet>/<version>/<fichier>`.
- Paquets `.deb` : `https://launchpad.net/ubuntu/+archive/primary/+files/<fichier>`.

Il refuse les champs contenant des séparateurs de chemin et les URL autres
que le chemin Ubuntu canonique du fichier ou son adresse Launchpad exacte.
Seul un **HTTP 404 du miroir** déclenche un essai Launchpad. Il n'y a pas de
boucle de tentatives : un autre code HTTP, une erreur de transport, un délai
dépassé ou une erreur du repli remonte au CLI et entraîne son échec.

L'assembleur conserve le contrôle conjoint du SHA-256 et de la taille du
verrou, avant toute écriture du fichier téléchargé, également pour le cache.
Un miroir qui répond avec de mauvais octets n'entraîne pas de repli : le
contrôle d'intégrité échoue. Les notices, preuves, recettes et verrou copiés
dans l'assemblage suivent le même chemin qu'avant le correctif.

L'assemblage ne télécharge que les 11 sources, soit 23 299 768 octets verrouillés.
Le `.deb` sert au rapprochement des octets natifs ; sa forme Launchpad est
dérivée et testée, mais aucun téléchargement binaire n'a été ajouté. La garde
de `binary_package_url`, qui compare l'URL du miroir à la preuve historique,
reste donc intacte. Le champ `size` d'une bibliothèque décrit son fichier natif,
pas la taille du `.deb` : pour ce dernier, l'orchestrateur doit comparer le
SHA-256 à `binary_package_sha256` et contrôler séparément la taille signalée.

## Tests rouges avant correction

Les tests sont dans `scripts/tests/test_system_libraries.py`, classe
`UbuntuSourceDownloadTests`. Les réponses HTTP et les octets sont simulés avec
`unittest.mock` et `BytesIO`. Seuls les octets des sources et leurs métadonnées
de fixture sont remplacés ; les notices et preuves du véritable assemblage
sont lues localement. Le verrou versionné n'est jamais modifié par les fixtures.

Commande jouée avant toute modification du script :

```bash
python3 -m unittest discover -s scripts/tests -p 'test_system_libraries.py' -k UbuntuSourceDownloadTests -v
```

Rouge conservé dans `.work-t2/round6/b2059-red.log` : **11 méthodes**, dont
**7 rouges**, **4 déjà vertes**, code de sortie 1. Le résumé unittest compte
**10 échecs et 16 erreurs**, sous-cas compris. Les 404 remontent avant tout
repli, les téléchargements isolés ne refusent pas les origines non canoniques
et la dérivation binaire n'existe pas encore.

Les 11 méthodes couvrent : succès après 404 pour chacun des 11 noms source
verrouillés, mauvaise empreinte à taille identique, mauvaise taille avec
empreinte correspondante, origines non canoniques, HTTP 500 et délais sans
repli, échec Launchpad sans nouvelle tentative, assemblage nominal et verrou
copié identique, cache valide sans téléchargement, URL Launchpad exacte,
forme binaire `+files` et champs de chemin invalides.

## Résultats après correction

- Les **11 nouveaux tests passent**.
- `python3 -m unittest discover -s scripts/tests -p 'test_system_libraries.py' -v` :
  **32 tests, 31 réussis, 1 ignoré**, zéro échec ni erreur, code de sortie 0.
  L'ignoré nécessite l'extracteur Debian. Journal :
  `.work-t2/round6/b2059-system-libraries.log`.
- `python3 -m unittest discover -s scripts/tests -p 'test_*.py'` :
  **194 tests, 189 réussis, 2 ignorés, 3 erreurs**, zéro échec d'assertion,
  code de sortie 1. Journal : `.work-t2/round6/b2059-suite.log`.
  `test_expat_embeds_separate_cc0_siphash` et
  `test_real_fixtures_define_components_instead_of_importing_them` échouent
  sur `FileNotFoundError: readelf` ;
  `test_real_deb_cli_refuses_old_notices_then_accepts_completed_notices`
  échoue sur `FileNotFoundError: dpkg-deb`. Ces trois erreurs sont dans
  `test_cpython_components.py`, non modifié. Aucun outil n'a été installé
  et aucun test n'a été masqué pour contourner leur absence.
- `python3 scripts/system_libraries.py check` : code de sortie 0,
  **18 bibliothèques Linux, 4 macOS, 10 Windows, 11 sources** ;
  **58 fichiers CPython Linux, 59 macOS, 21 Windows**.

Aucun accès réseau, démarrage d'application, écoute sur les ports interdits
ou accès au profil `~/.therese`. Aucun `rm`, `git add` ou commit.
Les journaux et assemblages de fixture restent dans `.work-t2/round6/`, ignoré
par Git. La procédure canonique est mise à jour dans
[SIGNATURE-ET-LICENCES.md](../SIGNATURE-ET-LICENCES.md).

## Limites et vérifications de l'orchestrateur

Cette intervention ne prouve pas la disponibilité actuelle de Launchpad ni
l'assemblage des octets distants réels. Avec le réseau, l'orchestrateur doit
contrôler les trois adresses permanentes, leurs empreintes verrouillées et
leurs tailles, puis rejouer l'assemblage sans cache dans un dossier neuf.
Il doit obtenir les **11 sources et 23 299 768 octets**, contrôler le contenu
de `THERESE-sources-systeme-linux.tar.gz` et sa présence dans la release.
La suite complète doit aussi être rejouée avec `readelf` et `dpkg-deb` disponibles.

La prochaine mise à jour de l'image du runner changera les octets livrés et
exigera un **nouveau rapprochement** des natifs, paquets binaires, sources et
notices. Le repli ne met à jour aucune version et n'assouplit aucune garde de
provenance. Aucun build Linux ni contrôle d'installeur réel n'a été exécuté ici.
