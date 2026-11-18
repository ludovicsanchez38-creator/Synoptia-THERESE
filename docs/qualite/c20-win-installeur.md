# B-2060 : identité des composants NSIS après signature

Contrôle local du 18 novembre 2026, dans `c20/win-installeur`, sur la base
`4d60c49e06da269a56e3721eaa77a7a929021cb9`. Correctifs uniquement, sans
staging, commit, réseau, lancement de THÉRÈSE ni utilisation de son profil.

## Cause vérifiée

Les scripts, le verrou, leurs tests et le journal fourni ont été lus.
Dans `/tmp/blanc-win-4d60-extrait.log`, les nombres en début de ligne renvoient
au journal complet `/tmp/blanc-win-4d60.log` :

- 3125 : « Signing NSIS plugins » ; 3126, 3198 et 3414 montrent notamment
  `NSISdl.dll`, `StartMenu.dll` et `nsis_tauri_utils.dll` signés par Tauri.
- 4201 : le MSI passe avec 351 fichiers natifs rapprochés.
- 4211 : `nsis_tauri_utils.dll` est refusé, avec le SHA-256 signé
  `6318207bc670201531f8617b60960183921dd4d2a4affdaab17687c5b2e1a743`.
- 4212 : le contrôle de longueur du désinstalleur refuse les données ajoutées.

Le greffon était comparé par SHA-256 intégral à son entrée non signée du
verrou. Authenticode modifie le checksum PE et l'entrée Security, puis ajoute
une table de certificats horodatée. L'empreinte intégrale change donc sans
que le code ait changé. Le MSI n'embarque pas ces composants NSIS ; son
exécutable principal bénéficie déjà d'un rapprochement hors Authenticode.

Le contrôle appelé « en-tête du désinstalleur » ne vérifie pas un certificat.
`firstheader()` recherche la marque NSIS alignée sur 512 octets, lit le
drapeau de désinstallation et la longueur du bloc NSIS. Jusqu'ici,
`offset + longueur == len(uninstall.exe)` devait être vrai. Le certificat,
ajouté après les données déclarées, casse cette égalité. Ensuite, le script
vérifiait les sections et le code du stub épinglé, puis comparait les stubs
de l'installeur et du désinstalleur hors ressources. Les checksum et entrées
Security propres à leurs signatures auraient aussi cassé cette comparaison.

## Correction

Le [comportement canonique](../SIGNATURE-ET-LICENCES.md#identité-des-composants-nsis-signés-b-2060)
décrit les bornes et les champs comparés. Les deux anciens helpers PE sont
déplacés dans `scripts/windows_pe.py` et partagés avec NSIS, sans seconde
implémentation de normalisation. Le contrôle des sections physiques interdit
désormais de déguiser une section en certificat final.

Le verrou ne contient que des hashes intégraux : on ne peut pas en déduire
les hashes neutralisés, ni supposer que le checksum amont vaut zéro. Le
callback conserve donc les greffons avant signature, après vérification de
leur hash exact contre le verrou. La garde revérifie ces octets avant de
neutraliser checksum, Security et table de certificats des deux côtés.
Cette référence locale n'est ni un nouveau catalogue ni un binaire versionné.
Un fichier non signé reste soumis à son empreinte exacte.

Le désinstalleur garde les contrôles de drapeau, d'offset, de longueur,
de code, de sections, de point d'entrée et de stub hors ressources. Sa
longueur est maintenant vérifiée avant la table de certificats, avec le seul
remplissage nul minimal de son alignement. La comparaison des stubs neutralise
checksum et Security si l'un des deux exécutables est signé. Les natifs
extraits des deux conteneurs passent par le même contrôle d'inventaire.

## Tests et rouge préalable

Tous les PE sont construits en mémoire dans le test ; aucun binaire n'est
ajouté au dépôt. Avant modification des scripts de production :

```text
python3 -m unittest discover -s scripts/tests -p 'test_nsis_installer.py' -v
Ran 19 tests
FAILED (failures=1, errors=4)
```

Les quatre erreurs sont les refus des greffons signés dans les deux
conteneurs, du parcours avec désinstalleur signé, et de deux variantes de
signature du désinstalleur. L'échec révèle une table de certificats qui
chevauche `.text` tout en finissant à EOF, acceptée par l'ancien helper PE.
Ces cinq résultats rouges concernent quatre méthodes de test, dont une
exercée avec deux sous-cas. Journal : `/tmp/b2060-rouge.log`.

La suite NSIS contient désormais 24 méthodes, dont 14 ajoutées : greffon
conforme non signé sans référence locale, signé conforme avec un checksum
amont arbitraire non nul, code/données/ressources/en-têtes retouchés, octets
après certificat, table hors fichier, chevauchement de section, entrée
Security incomplète ou non alignée, références absentes ou altérées,
désinstalleurs signés conformes ou altérés, capture et seconde signature.
La capture est exercée en Python ; l'ordre et l'arrêt sur erreur du callback
PowerShell sont vérifiés statiquement.

Vérifications finales sur macOS avec Python 3.14.5 :

| Commande | Résultat |
| --- | --- |
| `python3 -m unittest discover -s scripts/tests -p 'test_*.py'` | 243 tests en 58,007 s : 238 réussis, 3 erreurs, 2 ignorés ; aucun échec d'assertion |
| `python3 scripts/nsis_installer.py check` | Réussi : 6 greffons et le stub `nsis-3.11/Stubs/lzma_solid-x86-unicode` relus, sans réseau |
| `git diff --check` | Réussi |

Les trois erreurs sont exactement celles annoncées, toutes dans
`test_cpython_components.CPythonComponentsTests` :

- `test_expat_embeds_separate_cc0_siphash` : `FileNotFoundError: readelf` ;
- `test_real_fixtures_define_components_instead_of_importing_them` :
  `FileNotFoundError: readelf` ;
- `test_real_deb_cli_refuses_old_notices_then_accepts_completed_notices` :
  `FileNotFoundError: dpkg-deb`.

Les deux tests ignorés demandent des outils Linux absents sur ce Mac.
Les 24 tests NSIS sont verts dans cette exécution finale. Les 15 tests de
`test_packaged_licenses.py` (dont un ignoré) et les deux régressions B-1886
passent également. Sortie complète : `/tmp/b2060-suite-finale.log`.

## Limites et prochaine construction Windows

Les tests locaux ne créent aucune signature cryptographique et ne lancent
ni PowerShell, ni Trusted Signing, ni makensis, ni l'extraction NSIS réelle
de 7-Zip. Ils simulent seulement l'extraction des greffons. Le contrôle du
stub ne compare pas toutes les ressources ou instructions NSIS générées ;
cette limite préexistante est conservée et documentée. La signature et
l'identité de l'éditeur restent vérifiées séparément par
`scripts/verify_windows_signing.ps1`.

L'orchestrateur doit vérifier sur la prochaine construction Windows :

1. Le callback conserve les originaux épinglés sous
   `.work-release/nsis-unsigned/` avant leur signature, y compris sur un
   éventuel second passage ; un cache signé sans original doit être refusé.
2. Le contrôle des licences passe pour MSI **et** NSIS, y compris
   `uninstall.exe` et tous ses greffons réellement reconstitués par 7-Zip 26.
   Relire les preuves JSON et leurs hashes réels, sans imposer un compte
   NSIS déduit des fixtures.
3. Les certificats réels sont en fin de PE et les seules différences de
   corps sont celles autorisées. En particulier, vérifier le padding et
   la longueur NSIS du vrai désinstalleur reconstitué, ainsi que la
   comparaison des deux stubs signés.
4. La vérification Authenticode distincte passe avec le bon éditeur et
   l'horodatage, puis l'installation/désinstallation réelle fonctionne.
   Les limites du moteur onefile et de Smart App Control restent celles
   de la documentation canonique.

Aucune construction Windows réelle ni publication n'a été effectuée ici.

## Réserves de la relecture : tests durcis

Trois méthodes ajoutées dans `scripts/tests/test_nsis_installer.py` couvrent
le remplacement simultané de la référence et du greffon signé dans chacun
des deux conteneurs, le padding nul excessif ou non nul, et les longueurs
27 (refusée) et 28 (acceptée). Le test PowerShell existant vérifie maintenant
que l'appel de capture est immédiatement suivi du contrôle de `$LASTEXITCODE`
avec un `throw` dans son bloc, avant l'import du module et la signature.

Chaque mutation a été appliquée séparément dans une copie sous
`/tmp/b2060-tests-durcis-lszm3cgu/`, puis la méthode concernée a été lancée
contre cette copie. Le témoin sans mutation passe ses 27 tests.

| Garde retirée ou affaiblie dans la copie | Résultat du test ciblé |
| --- | --- |
| SHA-256 de la référence contre le verrou, contrôle de non-signature conservé | Rouge : 2 échecs, installeur et désinstalleur |
| Padding nul de longueur arbitraire autorisé | Rouge : 1 échec, 8 octets nuls au-delà du minimum |
| Contrôle du contenu nul du padding retiré | Rouge : 1 échec, octet non nul à longueur alignée correcte |
| `length < 28` retiré | Rouge : 1 échec à 27 ; 28 reste accepté |
| `throw` du bloc d'échec de capture retiré | Rouge : 1 échec du contrôle de structure |

Les cinq lancements ciblés exécutent chacun une méthode, sans erreur
d'exécution : six échecs d'assertion au total, dont deux sous-cas pour le
SHA-256. Commandes, substitutions exactes et empreintes des scripts sont
dans `resultats.json` ; les journaux et `reproduire.py` sont dans le même
dossier temporaire. Après les mutations, sur l'arbre intact :
`python3 -m unittest discover -s scripts/tests -p 'test_nsis_installer.py'`
donne **27 tests réussis**, sans échec ni erreur (`suite-intacte.log`).
Aucun script de production n'a été modifié ; aucun staging ni commit.

Limite : ni `pwsh` ni `powershell` ne sont disponibles sur ce Mac ; le test
PowerShell reste statique et ne démontre pas une exécution réelle de signature.
Réserve non traitée : `sign_windows.ps1` appelle la capture pour tout fichier
signé ; un Python absent ou un verrou invalide interromprait donc toute
signature. Le workflow `.github/workflows/release.yml` installe Python avec
`actions/setup-python` avant la construction.
