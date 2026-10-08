# MAIN12 Chrome 40332 : diagnostic ciblé, lecture seule

Périmètre : Chrome QA du WRAPPER canary `/private/tmp/therese-c17-wrapper-canary-9818b6b4163e451892dbd3956e1bb492`. Aucune relance, modification de profil, permission ou produit. Le canari reste rouge.

## Attribution physique

- Reçu de stage : `raw/receipt.json`, copie exacte du reçu MAIN12 (SHA-256 `ba833212843935773eb3a4d5fe7afc2b190b40a52d66505f44ed0d286440696e`).
- Service-start : `raw/service-start.json` (SHA-256 `7c65bccc6fa5676e6394d5cc42631c34b76825d73accf8105b672050a20adddf`). PID 40332, PPID 40206, UID 501, birth `(1791494499, 845497)`, démarrage 23:21:39.845373 locale, admission 23:21:40.664600, commande Chrome QA et profil sous la racine WRAPPER.
- Fin du stage 23:21:43.130599 locale, `exit_code=-5`, sans timeout ni interruption. Le reçu indique `cleanup.signals=[]`, aucun processus attribué restant, fermeture locale sous 8 s ; `log_stability_proved=false`, donc aucune qualification positive.
- Stderr exact `raw/stderr.log` (SHA-256 `3eddb80bd30892fb794c12f268c8610b07e836632d794b427955d98a4c4b6443`) : FATAL `content/browser/sandbox_parameters_mac.mm:82`, `Input/output error (5)` horodaté 23:21:41.546709. Le stdout est vide.

## Journal ciblé

La première tentative de `/usr/bin/log show` dans le sandbox outil a échoué avec `Cannot run while sandboxed` (reçu local `receipt.json`, SHA-256 `469453a73e4d3ffb846a5e4aa7425e1656605ed30bec33533288f1d9df609e4e`). Elle n'est pas un diagnostic Chrome.

La collecte autorisée séparée `/private/tmp/therese-c17-root12-chrome40332-log-authorized-uWc2pv/receipt.json` (SHA-256 `edac040f0d22a4d698884b27ce93be4a7bf8043f417ac54df20ce7cc58bc52ba`) a retourné 0 et 100 événements pour le seul PID 40332 et les messages système le nommant, entre 23:21:39 et 23:21:44 locale. Raw `stdout.json` SHA-256 `b7118cc01c33afae91b1b89cac8c466e5463a3bcb16cb38096aec7ffa1d5c57d`, 121996 octets ; stderr vide. Le collecteur exact est pinné par le reçu.

Tous les 100 `eventMessage` ont été lus. Refus de `com.apple.bsd.dirhelper` et `opendirectoryd` répétés dès 23:21:41.367 et encore à 41.531382, puis `configd` 41.480305, `com.apple.networkd.plist` 41.494207, `DNSConfiguration` 41.529501, `/private/etc/resolv.conf` 41.531007. Aucun chemin `User-Darwin-dir` n'est nommé dans ce journal. Le journal signale AMFI corpse du même PID/thread 5179490 à 41.532932. Aucun refus sur le nouveau chemin parent `<QA_ROOT>/auxiliary` n'apparaît dans cette fenêtre. Aucune ligne de refus n'est horodatée exactement 41.546709. La proximité ne permet pas d'attribuer le FATAL à un droit précis ; aucune nouvelle règle n'est proposée.

## IPS exact

Seul `Google Chrome-2026-10-08-232144.ips` a été lu dans DiagnosticReports, après sélection par heure. Son en-tête et son corps confirment PID 40332, PPID 40206, lancement 23:21:39.8454, version Chrome 154.0.8037.99, incident `205B9576-D257-411B-9BE2-B398CE0E9057`, thread fautif 5179490, `EXC_BREAKPOINT` / `SIGTRAP`. Sa pile ChromeMain n'est pas symbolisée. Copie byte-exacte `raw/Google Chrome-2026-10-08-232144.ips`, SHA-256 `771438ec2d829ee7911c39f949afaa8d76701aa5120f8a85603ed03fb651036e`, 57483 octets, identique à la source actuelle. Le fichier source n'a pas été modifié.

Limite : le source Chromium `main` consulté ne correspond pas nécessairement au build 154.0.8037.99 ; sa ligne 82 ne permet pas d'identifier l'assertion exacte de ce binaire. Aucune cause unique ni remédiation de permission n'est établie par ce lot.
