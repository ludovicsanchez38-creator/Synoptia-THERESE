# MAIN11, Chrome auxiliaire PID 34667 : diagnostic borné

Périmètre : Chrome QA du seul stage `aux-chrome-rpc-all-runtime_ui-visual_capture-network_capture`, PID 34667, fenêtre locale 2026-10-08 22:59:39–22:59:51 (20:59:39–20:59:51 UTC). Aucun navigateur, service ou profil n'a été relancé ou modifié pour cette enquête.

## Établi par les reçus

- `raw/service-start.json` : binaire de la copie Chrome QA, `--user-data-dir` sous MAIN11 et CDP sur 127.0.0.1:17594 ; birth du Chrome 34667 vérifiée avant release, admission à 20:59:40.630 UTC ; readiness non prouvée.
- `raw/receipt.json` : Chrome 34667 attribué, puis nettoyage contrôlé ; SIGTERM à 20:59:46.409 UTC, SIGKILL à 20:59:49.410 UTC, code final -9. Ce code est dû au nettoyage et ne prouve pas un crash. Aucun CDP prêt n'est attesté. Le stage termine avec `instrument_guard_or_cleanup_taint`, pas une recette produit.
- `raw/stderr.log` : avertissement Crashpad, refus SystemConfiguration `SCDynamicStoreCreate` répété chaque seconde de 22:59:45 à 22:59:49. `raw/stdout.log` est vide.
- Le dossier privé `--user-data-dir/.../profile` est vide ; son mtime observé est 18:47:16 locale, avant ce lancement. Cela n'établit pas seul pourquoi Chrome n'a rien écrit.

## Journal système ciblé

`system-authorized/receipt.json` atteste `/usr/bin/log show`, code 0, 133 événements : 132 noyau et 1 sandboxd, filtrés sur ce PID/fenêtre seulement. Le premier essai sans permission système (`receipt.json` à la racine de ce dossier) est rouge, `log: Cannot run while sandboxed`; il reste conservé.

Événement le plus directement lié au chemin de profil : à 22:59:43.742884, `file-read-metadata` est refusé sur le parent exact `MAIN11/auxiliary`. Le profil autorise la lecture du sous-arbre `AUXILIARY_ROOT=MAIN11/auxiliary/aux-chrome-...`, mais pas ce parent intermédiaire. Le processus demande ensuite d'autres services système ; notamment `mach-lookup com.apple.SystemConfiguration.configd` est refusé à 22:59:44.021 et de nouveau pendant les tentatives `SCDynamicStoreCreate`. D'autres refus (dtracehelper, LaunchServices, IOKit, etc.) existent ; leur nécessité pour CDP n'est pas établie.

Conclusion bornée : Chrome a vécu jusqu'au nettoyage mais n'a pas fourni le listener CDP dans la fenêtre de 5 s. Le refus de métadonnées sur le parent du profil, joint au dossier de profil resté vide, est l'hypothèse causale la plus ciblée à tester ensuite, **pas une cause démontrée**. Le refus `configd` est corrélé aux erreurs répétées en stderr, sans preuve qu'il bloque CDP. Le journal borné ne montre pas de SIGSEGV ni de refus ASP pour ce PID, mais il ne prouve pas leur absence hors filtre. Aucune nouvelle règle Seatbelt ou durée n'a été ajoutée par cette enquête.
