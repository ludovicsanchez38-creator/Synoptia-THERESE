# MAIN12, revue indépendante de clôture

Auteur : /root/cycle17_gate_review. Revue en lecture seule des bruts natifs clos. Aucun canari relancé, aucun processus QA, import G1/libproc, signal ou cleanup effectué par le relecteur. ROOT12 n'a pas été modifié. Cette note prépare l'archive LOT71 et ne crée aucune admission.

ROOT : /private/tmp/therese-c17-wrapper-canary-9818b6b4163e451892dbd3956e1bb492
Résultat : 6ec067febe9e1daa1160023cbdb829f3a8dcec38058d6d443f8104fbab7d2503, 2 778 octets.

## Verdict réel

Le canari est rouge, exit 86, sept ACK sur quinze, stage_refs vide et les quatre parents complets absents. Les sources restent inchangées et le transport est clos, mais passed=false, clean=false, owned_shutdown_proved=false, log_stability_tainted=true et log_stability_proved=false restent conservés dans les reçus originaux. Aucun statut FULL, A/B, UI, density/78 ou release n'est déduit de la clôture physique.

Six ACK ordinaires sont liés à leurs véritables child_identity, rc et reçus terminaux. Les codes sont all-test-runner 0, all-logs 0, pytest positif/négatif 1/0, Vitest positif/négatif 1/0. Chaque XML pytest/Vitest a un seul testcase, aucune error/skip ; chacun des deux positifs détecteurs contient une failure. Les rc non nuls attendus ne sont pas reclassés timeout.

Le septième ACK, rpc-all-runtime_ui-visual_capture-network_capture, est une erreur prélaunch de la feuille Node sans leafbirth, receipt de feuille ou code inventés. La chaîne RpcPrelaunchRefused causée par InstrumentError « Chrome absent/changé ou admission CDP hors délai5s » est conservée dans l'ACK et calibrate.stderr.

## Fait nouveau Chrome

Chrome PID 40332, birth 1791494499/845497, UID 501, PPID 40206, PGID 40332, a réellement été lancé et libéré. Il sort en -5, sans timeout ni interruption ; cleanup.signals est vide. Ce n'est pas le SIGKILL contrôlé observé dans MAIN11.

Le stderr physique SHA3eddb80bd30892fb794c12f268c8610b07e836632d794b427955d98a4c4b6443, 933 octets, contient à 1008/232141.546709 la ligne FATAL de PID40332, content/browser/sandbox_parameters_mac.mm:82, « Check failed: . : Input/output error (5) ». Cette observation ne détermine pas le syscall ou le droit causal sous-jacent.

Le descendant 40371 est attribué par filiation au parent 40332 vivant. Le PID Crashpad 40358 est seulement nommé dans stderr ; aucune naissance de ce PID n'est admise au ledger inspecté. Son nom ne permet ni adoption ni promesse de terminaison exhaustive.

## Contrôles physiques réellement effectués

79 sources physiques courantes rehashées, zéro écart. 216 références locales des reçus sélectionnés ont été contrôlées, zéro écart. 34 couples publication/pending gate, release, demande et ACK ont même device/inode, nlink2, UID501 et bytes identiques.

15 événements de signal uniques du contrôleur, sans additionner leurs copies dans plusieurs reçus, correspondent aux trois identités canoniques :

- backend 40227, birth 1791494471/80744, PGID 40227 ;
- Vite 40231, birth 1791494472/705013, PGID 40231 ;
- enfant Vite 40234, birth 1791494473/823501, parent 40231, PGID 40231.

Chaque événement porte les birth, UID, PGID et rôle joints au record canonique. Les seuls signaux sont les STOP répétés, TERM et CONT définis par cleanup. Aucun de ces événements ne vise Chrome.

Les cibles exactement attribuées sont déclarées terminées et les flux archivés, avec résidus, ambiguïtés et erreurs vides. Les durées finish sont Chrome 0,738672916 s, services 0,901575917 s et Session 0,766882750 s, toutes inférieures à 8 s. La borne finish ne promet pas une durée identique pour scan de ports et publication de reçus.

Les reçus finaux services-stop et session-stop contiennent chacun deux passes réelles sur 17593, 5173, 17594. Les douze diagnostics lsof sont admis avec identité/birth/UID/PPID/PGID, rc 1, stdout/stderr vides et pids vide. Leurs références physiques sont intactes :

- ports-absence-2.json : a2125738e24e09e213cb3ea1db6c37ea700955922785127699f63e373400615d ;
- ports-absence-3.json : e11e3876b1054204f9d122f9918572ad573ec141bbdbfa6593dd3813107590d1.

Le reçu Sessionclose3158e48d… prouve session_closed=true et interrupt_handlers_restored=true. Le pré-reçu31952d51… garde session_closed=false et handlersrestored=false à son étape antérieure ; aucune réécriture d'un brut antérieur n'a eu lieu.

## Limites de la revue

La fermeture concerne la famille effectivement observée et attribuée. Elle ne prouve pas une exhaustivité hostile, le confinement total ni la disparition universelle de petits-enfants inconnus. Crashpad 40358 demeure explicitement hors attribution. L'arrêt physique des cibles et les ports vides ne transforment pas le canari tainté en PASS.

Les 36 références sélectionnées avec SHA et tailles sont conservées dans receipt.json. Les totaux de contrôles sont ceux de notre inspection readonly précédente, pas un nouveau test natif. Les bruts ROOT12 restent à leur emplacement original.
