# WRAPPER14 : MAC_CHROMIUM_TMPDIR QA, préparation fermée

Auteur : `/root/shared4_execution`. Aucun constructeur, root WRAPPER14, G1,
Chrome, profil Apple, service, socket, signal ou campagne n'a été exécuté.
Les seuls appels exécutés sont les tests stdlib purs décrits ci-dessous.
Aucune décision, autorité ou admission réelle n'est produite par ce lot.

## Delta exact

Préimage builder13 :
`/private/tmp/therese-c17-wrapper13-dirhelper-P5WQpQ/build_fresh_wrapper.py`,
SHA `f76830c89475c58ea63599d7633d9a5031777a0655b2c0c3a838bdea96fe5719`,
90 352 octets, copie byte-exacte sous `preimages/`.

La seule racine future acceptée devient
`/private/tmp/therese-c17-wrapper-canary-187602c63a0b498a95d25c19843000a8`.
Elle reste absente. Les cinq descriptors Chrome exacts reçoivent
`MAC_CHROMIUM_TMPDIR = TMPDIR = <root>/auxiliary/<aux-chrome-job>/tmp`.
Les autres clés/valeurs, argv, cwd, options headful/sandbox, scénarios, ports,
CDP 5 s, startup 50 s et cleanup 8 s restent identiques à la préimage.

G1 refusait cette clé hors de son ensemble autorisé. La dérivation
`g1_chromium_tmpdir_delta` ajoute donc le seul prédicat nécessaire dans le
corps réel `validate_environment`, avant FD/Popen : racine ROOT14 exacte,
mode `chrome`, stage dans les cinq noms auxiliaires fermés, clé obligatoire,
valeur égale au TMPDIR et au chemin attendu canonique existant et directory.
Aucun ajout aux ensembles globaux ENV_CONSTANTS/ENV_PATHS/ENV_CONTEXT ni aux
environnements des services, parents, feuilles RPC ou helpers ordinaires.
Toute autre racine, mode, stage, valeur, lien ou clé reste refusée. Le retour
conserve l'environnement complet : aucune filtration ni fallback.

Tous les autres corps AST G1 sont inchangés, ainsi que les flags/caps et
tables d'admission fermés. La préimage/preview G1 montre cette différence
uniquement ; ce n'est pas une copie G1 qualifiée. La dérivation est jointe au
diff existant `root-wrapper-admission.diff` lors d'une construction future,
et au SHA de la copie G1 déjà comptée : la table de sources reste 79, sans
nouveau helper. La composition exacte des 26 commandes reprend les cinq
environnements sans héritage ni nouvelle clé dans les 21 autres commandes.
Le gate conservé transmet `os.environ` par execve après admission/release.

Le profil Chrome reste SHA
`2ecae3a24ec871a44827b3f712ced1ef5e84d8f778906c37b3a5b51bb374dcdf`,
2 499 octets, copie locale byte-identique. La référence CLI stricte conserve
le chemin d'origine builder13 `profile/chrome.sb`. Aucun droit nouveau,
profil modifié/compilé, compteur, FULL ou release activé.

## Origines et hypothèse

[La source primaire Chromium](https://raw.githubusercontent.com/chromium/chromium/main/base/files/file_util_apple.mm)
consultée confirme que GetTempDir privilégie cette variable pour les runs
macOS hermétiques avant le mécanisme natif. Ce code `main` n'est pas une
preuve du comportement du binaire Chrome installé ni de causalité du refus
ROOT13. Le rouge ROOT13 transmis par MAIN reste historique : ce lot ne le
requalifie pas et ne lit/mute aucun dossier temporaire personnel Darwin.

QA source et HEAD canari historiques restent `kGvU1hdx/source` et
`2d69e30c9c6dd18823ee6102271876003a6a67cc`. Le HEAD documentaire transmis
`d1486c2ad1d1879b1c10196fe269e16b35b85e6e` reste distinct et n'est pas
consommé comme preuve source actuelle. Les trois seules routes IPS archivales,
leur pointeur exact, l'absence historique et les anciens rouges sont
préservés dans des corps inchangés. Les 11 originaux, core18, overlay28/19 et
79 sources restent des contrats futurs de construction, pas des sorties
physiquement émises ici.

## Pures réellement observés

Commande :

```text
/Users/synoptia/.local/share/uv/python/cpython-3.13.5-macos-aarch64-none/bin/python3.13 -I -B run_pure.py
```

Dernier outil `0b7d6e`, exit 0 : 23 tests PASS, zéro erreur/échec/skip,
18 pins avant/après identiques, aucune tentative OS interdite. Reçu
`proofs/pure-bc7q7o5k/receipt.json`, sinks stdout/stderr directs et exclusifs.
Les vrais corps chrome_prepare, validate_environment/child_path sélectionnés
par AST et compose_26_commands sont exécutés sur des doubles explicitement
synthétiques. Le constructeur n'est jamais appelé ; G1 entier n'est pas
importé. Les faux Path/VM/emitter ne sont pas des observations OS.

Deux rouges préalables sont conservés :

- Outil `4f00d9`, 23 tests/22 PASS/1 FAIL : regroupement de lignes blanches
  différent entre BSD diff et difflib. Les quatre premiers diffs sont gardés,
  puis régénérés avec le difflib exact exigé par le test. Source/assertions
  inchangées ; seulement un extrait réellement retourné est disponible,
  explicitement marqué incomplet, aucun stdout complet fabriqué.
- Outil `bd1fbc`, 1 erreur de chargement : unittest.mock importait SSL après
  substitution de socket.socket. Reçu/sinks directs conservés sous
  `proofs/pure-lb53c5ys`. La préimage du runner est gardée ; unittest.mock est
  désormais préchargé avant la garde. Aucun test métier n'est assoupli.

Le passage `358a50` précède l'ajout au même cas21 du vrai corps compose26 ;
son ancien test byte-exact est conservé sous `preimages/test-before-compose-body.py`.
Le passage final est distinct, sans mise à jour rétroactive des reçus.

## Usage futur fermé

CLI originale préservée : `--root`, `--web-profile-ref`, `--chrome-profile-ref`,
`--authority-ref`, `--prepare`. Elle exige une autorité MAIN neuve externe
exacte sur ce builder et cette racine, et les contrôles physiques originaux.
Elle n'a pas été appelée. Le futur checker doit relire ce delta G1 et les
cinq environnements. Aucun simple code 0 pur ne fournit un GO natif.
FULL/A+B restent fermés ; aucune intégration de ce delta dans FULLv2.
