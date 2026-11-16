# Cycle 20 : reproduction, signature et publication des paquets

Base examinée : `cd287fb34b54c8ce78e322a71bdce3d323f0fa0c`, branche de travail `gpt/c20-repro-signature`. Aucun correctif de production n'a été appliqué.

## Verdicts et preuves

Les lignes d'échec ci-dessous sont recopiées des exécutions isolées. `confirme` qualifie le défaut précisément décrit dans la colonne de preuve ; les limites des simulations figurent après le tableau.

| ID | Verdict | Test `chemin::nom` | Ligne d'échec ou preuve |
|---|---|---|---|
| B-1833 | `regle_a_trancher` | — | `src/frontend/src-tauri/capabilities/default.json:73` autorise `$HOME/**`, avec la liste de refus `:47-67` ; `src/frontend/src-tauri/tauri.conf.json:74` règle `requireLiteralLeadingDot` à `true`. Décider si la webview peut parcourir tout le domicile hors exclusions, ou seulement les dossiers explicitement choisis. Les exemples de dotfiles lisibles ne sont pas établis par cette lecture. |
| B-1834 | `rejete` | — | `src/frontend/src-tauri/capabilities/default.json:22` donne effectivement `shell:allow-open`, mais `src/frontend/node_modules/@tauri-apps/plugin-shell/dist-js/index.d.ts:267-269` documente le filtre regex par défaut sur `plugins.shell.open` ; `src/frontend/src-tauri/tauri.conf.json:69-72` ne le remplace pas par une regex plus large. Le paquet JS installé et le crate verrouillé sont tous deux en version 2.3.4. L'absence d'une liste `allow` dans la capability ne prouve donc pas une ouverture sans filtre. |
| B-1835 | `confirme` | `scripts/tests/test_c20_b1835_fallback_windows.py::test_le_repli_verifie_la_commande_avant_de_retenir_un_pid` | `E       AssertionError: tasklist retient les PID backend.exe sans vérifier la ligne de commande` |
| B-1836 | `confirme` | `scripts/tests/test_c20_b1836_port_windows.py::test_le_motif_du_port_ne_vise_pas_un_port_plus_long` | `E       AssertionError: le filtre '%--port%17293%' vise aussi --port 172930` |
| B-1855 | `confirme` | `scripts/tests/test_c20_b1855_tag_checkout.py::test_le_tag_manuel_designe_le_commit_valide_par_la_ci` | `E       AssertionError: aucune comparaison du commit du tag manuel à celui de la CI ; refs checkout : {'sources-copyleft': None, 'build': None}` |
| B-1856 | `confirme` | `scripts/tests/test_c20_b1856_sources_brouillon.py::test_les_sources_verifient_le_statut_brouillon_avant_upload` | `E       AssertionError: la release existante est seulement recherchée, sans contrôle du statut brouillon` |
| B-1857 | `regle_a_trancher` | Test conditionnel : `scripts/tests/test_c20_b1857_matrice_publication.py::test_les_installeurs_attendent_tous_les_builds` | `E       AssertionError: une jambe publie avant les autres : ['Publier les artefacts vérifiés']`. La présence possible d'installeurs dans un **brouillon** incomplet est établie par la structure ; décider si ce brouillon partiel est acceptable pendant un échec de matrice, ou si les trois builds doivent réussir avant tout dépôt d'installeur. Le test rouge encode uniquement la seconde option. |
| B-1858 | `regle_a_trancher` | — | `scripts/prepare_windows_signing.py:10-13,22` prévoit explicitement le build non signé lorsque des secrets manquent ; `.github/workflows/release.yml:475-478,523-524` saute la vérification Authenticode mais ne bloque pas la publication. Décider si les alphas non signées restent temporairement autorisées, avec indication claire, ou si toute publication non `dry_run` exige la signature Microsoft. La signature updater n'est pas une signature Authenticode. |
| B-1881 | `confirme` | `scripts/tests/test_c20_b1881_publication_brouillon.py::test_une_release_publique_ne_recoit_aucun_upload` | `E       AssertionError: release publique : upload effectué malgré isDraft=false : [['gh', 'release', 'upload', 'v0.83.0-alpha', '--clobber', 'preuve-factice.json', 'factice.dmg']]` |
| B-1882 | `confirme` | `scripts/tests/test_c20_b1882_architecture_macos.py::test_archive_x64_refusee_avant_renommage_et_publication` | `E       AssertionError: archive x86_64 publiée sous aarch64 : [['gh', 'release', 'upload', 'v0.83.0-alpha', '--clobber', 'THERESE.app.tar.gz.json', 'THERESE_aarch64.app.tar.gz.sig', 'THERESE_aarch64.app.tar.gz']]` |
| B-1884 | `rejete` | — | `docs/UPDATER-SETUP.md:45-50,60-62` précise que seul l'alias Linux **générique** d'un `.deb` doit être retiré, et que `linux-x86_64-deb` doit rester. `tests/test_b1111_manifeste_updater.py:98-103` attend explicitement le MSI sous `windows-x86_64`. Le workflow ne construit que le `.deb` sur Linux (`.github/workflows/release.yml:429`) : l'absence d'AppImage est réelle, mais sa production n'est pas une obligation démontrée ici. |
| B-1886 | `confirme` | `scripts/tests/test_c20_b1886_executable_etranger.py::test_un_executable_etranger_ne_passe_pas_par_sa_seule_table_pe` | `E       Failed: DID NOT RAISE <class 'ValueError'>` |
| B-1887 | `confirme` | `scripts/tests/test_c20_b1887_identite_signataire.py::test_la_garde_authenticode_controle_le_certificat_signataire` | `E       AssertionError: aucun contrôle de l'identité du signataire, seulement statut et horodatage` |

## Portée des reproductions

- Les neuf fichiers de test ont été exécutés individuellement, avec `OLLAMA_BASE_URL=http://127.0.0.1:9 .venv/bin/python -m pytest <fichier> -q -p no:cacheprovider`. La variable `PYTHONDONTWRITEBYTECODE=1` a été ajoutée pour éviter les écritures de bytecode dans l'environnement lié. Chaque fichier donne un seul échec attendu avec le chargement normal des greffons pytest. `ruff check --no-cache` passe sur les neuf fichiers.
- B-1835 est un contrôle structurel du repli Rust ; B-1836 rejoue le joker `%` du filtre WQL lu dans le code avec SQLite en mémoire. Aucun processus Windows n'a été interrogé ni arrêté. Ces tests ne remplacent pas un essai Windows ultérieur avec des processus jetables.
- B-1855, B-1856, B-1857 et B-1887 sont des contrôles structurels ciblés. Pour B-1855, l'expression actuelle ne lie pas les checkouts au tag demandé ; le test propose une vérification explicite du commit dans le preflight. Pour B-1857, seul le fait d'un dépôt possible dans un brouillon est démontré ; aucune publication publique automatique n'est déduite.
- B-1881 exécute `main()` avec les commandes externes interceptées en mémoire. La release renvoyée par le double est publique ; aucune commande `gh` ni signature réelle n'est lancée. B-1882 utilise une archive virtuelle contenant un en-tête Mach-O x86_64 factice ; copies, signature updater et publication sont simulées. La preuve initiale porte l'ancien nom, comme le montrent `scripts/publish_release_artifacts.py:31-45,54-63,71-72`.
- B-1886 utilise un PE fictif dont le répertoire de certificats annonce une taille non nulle, sans vraie signature. La garde des licences l'accepte malgré l'empreinte différente. Cela ne prouve pas à lui seul qu'un tiers authentiquement signé et horodaté a passé toute la chaîne : la seconde garde est examinée séparément par B-1887. Le workflow pointe `verify_windows_signing.ps1` vers les dossiers `binaries` et `bundle`, pas directement vers le dossier d'extraction temporaire de l'installeur (`.github/workflows/release.yml:475-478`). Le contrôle d'identité du binaire extrait reste à qualifier.
- B-1833 et B-1834 n'ont pas été exercés dans une webview Tauri. Pour B-1833, la configuration des fichiers cachés limite les conclusions sur les exemples nommés. Pour B-1834, la documentation locale du plugin établit le filtre par défaut, mais un essai Tauri serait nécessaire pour constater les destinations réellement acceptées dans l'application empaquetée.

## Corrections minimales à proposer, sans application

### B-1835 : repli Windows sur le nom d'image

Supprimer le repli `tasklist` tant qu'il ne sait pas vérifier la ligne de commande du PID, ou le remplacer par une énumération suivie d'une vérification précise avant `taskkill`. Risque : sur une machine sans `wmic`, un ancien moteur ne sera plus arrêté ; il faudra qualifier le démarrage et la libération du port dans l'application Windows signée. Aucune clé de signature n'est concernée directement.

### B-1836 : port Windows trop largement reconnu

Récupérer la ligne de commande puis vérifier les arguments `--host` et `--port` comme des valeurs entières, par un analyseur partagé ou équivalent. Risque : une variante légitime d'arguments peut cesser d'être reconnue et laisser un ancien moteur actif ; vérifier les formes réellement utilisées par le sidecar Windows avant release.

### B-1855 : tag manuel et sources construites

Avant tout dépôt, refuser hors mode à blanc si le commit résolu du tag demandé diffère du commit du déclenchement évalué par la CI et l'E2E ; rendre le tag disponible au preflight. Aligner seulement les checkouts du build sur le tag ne suffirait pas si la CI a testé une autre référence. Risque : un lancement manuel actuellement accepté sera bloqué, en particulier si le tag n'est pas accessible localement ; le libellé `a-blanc-*` doit rester exempté. Le correctif change l'entrée de la chaîne de signature, pas les certificats.

### B-1856 : archives de sources sur une release existante

Avant l'upload, lire l'état de la release et refuser si elle n'est pas un brouillon. Faire le contrôle après une éventuelle création. Risque : une reprise volontaire sur une release publique sera bloquée ; l'échec ou les permissions de lecture doivent eux aussi bloquer. Un contrôle suivi d'un upload séparé laisse une fenêtre de concurrence si le brouillon est publié entre les deux opérations.

### B-1881 : publication directe sur une release existante

Dans le script autonome, lire et exiger l'état brouillon juste avant l'upload, y compris après une course de création perdue. Traiter les erreurs de lecture comme bloquantes. Risque : les appels directs destinés à compléter une release publique ne fonctionneront plus ; coordonner avec le contrôle des sources B-1856. La fenêtre de concurrence entre contrôle et upload reste à traiter dans la procédure de publication.

### B-1882 : renommage d'archive macOS

Avant de créer l'alias `aarch64`, vérifier l'architecture effective du binaire contenu dans l'archive, refuser toute incompatibilité, puis produire une preuve dont le nom et le champ `artifact` correspondent au fichier effectivement chargé. Risque : une archive universelle ou un changement de disposition du bundle peut être refusé ; les consommateurs de preuves et le manifeste updater doivent suivre le nouveau nom. Le renommage seul ne re-signe pas le bundle Apple ; conserver les octets du bundle et régénérer la signature updater sur l'archive finale.

### B-1886 : exception PE qui contourne l'empreinte du build

Pour fermer immédiatement le contournement, ne plus accepter un binaire principal différent de ceux du build sur la seule présence d'une table de certificats. Risque direct : la signature Authenticode modifie les octets et peut donc bloquer les builds Windows légitimes déjà signés. Avant d'activer la garde en release, définir une preuve reliant effectivement l'exécutable signé et empaqueté à ce build, par exemple une comparaison correctement normalisée de l'Authenticode et du jeton Tauri, puis la qualifier sur MSI et NSIS.

### B-1887 : identité du signataire Windows

Comparer le certificat signataire valide à une identité attendue configurée pour la release, en plus du statut et de l'horodatage ; traiter explicitement la rotation des certificats Microsoft et les éventuels binaires tiers autorisés. Risque : une empreinte figée ou une identité incorrecte peut bloquer tous les fichiers signés du prochain build. Le choix exact de l'identité et des exceptions dépend du profil Microsoft en cours de mise en place ; il ne faut pas confondre le certificat de signature avec celui d'horodatage.

## Git et isolement

Le fichier `.git` de ce worktree pointe vers les métadonnées du dépôt principal, et le répertoire Git commun se trouve lui aussi dans ce dépôt. Ils sont hors des racines inscriptibles et Ludo a interdit de toucher au dépôt principal. Les commits demandés ne peuvent donc pas être créés dans ce contexte sans franchir ces deux limites ; aucun commit n'a été tenté. Les tests et ce rapport restent dans le seul arbre de travail pour reprise. Aucun push ni appel réseau n'a été effectué.
