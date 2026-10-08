# Probe getconf / dirhelper, préparation uniquement

Statut : `prepared_not_executed`. Aucun Chrome, `getconf`, `sandbox-exec` ou profil n'a été exécuté par l'auteur de ce lot. Le résultat MAIN12 reste rouge et le candidat ne vaut ni permission admise, ni preuve de causalité, ni qualification CDP.

## Hypothèse bornée

Le profil `profiles/main12.sb` est la copie byte-exacte de `/private/tmp/therese-c17-wrapper-canary-9818b6b4163e451892dbd3956e1bb492/g1/chrome.sb`, SHA-256 `980b12368975718d33dba1572ce94da04ca378ca827df1be10a1ed15a7104cdb`. `profiles/dirhelper.sb` est identique avec une seule règle ajoutée : `(allow mach-lookup (global-name "com.apple.bsd.dirhelper"))`. Le diff et son inverse sont fournis. Aucun autre droit de fichier, réseau, IOKit, Mach ou délai n'a changé.

Le [source Chromium 143](https://chromium.googlesource.com/chromium/src/+/refs/tags/143.0.7499.91/content/browser/sandbox_parameters_mac.mm) montre `AddDarwinDirs` appelant successivement `confstr` pour cache, user et temp, et une vérification fatale sur retour nul. [Le changement Chromium de base](https://chromium.googlesource.com/chromium/src/base/+/a5773509b4f6e61d6093a66f3572a9d0a4fc29ce%5E!/) relie les répertoires Darwin à `confstr`. Le binaire MAIN12 est Chrome 154.0.8037.99 : ces sources ne prouvent pas la correspondance exacte de `sandbox_parameters_mac.mm:82` dans ce build. Les 18 mentions `bsd.dirhelper` du journal MAIN12 justifient seulement un test différentiel restreint.

## Pilote préparé

`run_getconf.mjs` lance séquentiellement, pour chaque profil, exactement `/usr/bin/getconf DARWIN_USER_DIR`, `DARWIN_USER_CACHE_DIR`, `DARWIN_USER_TEMP_DIR` via `/usr/bin/sandbox-exec -f <profil>`. Les deux profils reçoivent les mêmes cinq paramètres QA `QA_ROOT`, `AUXILIARY_PARENT`, `AUXILIARY_ROOT`, `HOME_ROOT`, `TMP_ROOT`, le même UID 501, le même `HOME`, `CFFIXED_USER_HOME`, `TMPDIR` et le même environnement fermé. La racine QA est neuve et privée sous la racine de sortie.

Chaque processus a un timeout de 10 s et une limite de sortie de 64 KiB. Une erreur de lancement, un timeout ou un débordement arrête la suite ; la sortie est rouge/incomplète. Le pilote borne le processus direct, mais ne prétend pas attribuer ou nettoyer un descendant qui existerait malgré la commande fermée `getconf`. Les six stdout/stderr bruts et les reçus par cas sont créés exclusivement dans des fichiers 0600, sous des répertoires 0700. Le script ne décode, n'affiche, n'ouvre ni ne parcourt les chemins que `getconf` pourrait retourner. Les reçus n'exposent que taille et empreinte du stdout, les codes de sortie, signal et durée. Les stdout bruts peuvent néanmoins contenir un chemin personnel : ils doivent rester privés et hors archive/rapport public.

Invocation future envisagée, uniquement par root après revue et hors sandbox outil :

```text
node /private/tmp/therese-c17-getconf-dirhelper-XeZCB9/run_getconf.mjs --execute --out /private/tmp/therese-c17-getconf-dirhelper-run-<nonce-32-hex-neuf>
```

Le pilote refuse toute sortie préexistante ou hors du préfixe exact, tout UID différent de 501 et toute modification des deux profils. La sortie principale contient uniquement une référence au reçu de suite. Il ne teste pas les services, Chrome, CDP ou l'absence d'autre contrainte du sandbox hôte. Une différence entre les profils établira au mieux la contribution de ce droit à ces trois appels `getconf` dans ce contexte QA, pas la cause complète du crash MAIN12.

`tests/plan.test.mjs` contient trois contrôles purs (delta de profil, six commandes fermées, environnement/paramètres identiques). Ils ont été exécutés par l'auteur via `node --test` : 3/3 PASS, exit 0, sans `getconf`, `sandbox-exec` ni Chrome. Cette vérification lexicale ne qualifie pas l'exécution future.
