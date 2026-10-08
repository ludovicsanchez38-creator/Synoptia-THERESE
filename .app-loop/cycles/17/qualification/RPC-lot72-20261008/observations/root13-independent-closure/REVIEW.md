# MAIN13 : clôture indépendante, rouge conservé

## Résultat réel

Le résultat 6b42e669cce73332c3f8f8801f8f8b95e7489050687e4ddcab56adb16737fe0c, 2 778 octets, conserve le code instrument 86. Sept ACK sur quinze : six `complete`, un `error`. `source_unchanged=true`, transport fermé, erreurs de transport vides, `stage_refs={}`, `passed=false`, `owned_shutdown_proved=false`, `FULL=false`.

Les six retours ordinaires sont all-test 0, logs 0, pytest positif/négatif 1/0 et Vitest positif/négatif 1/0. Leurs vrais reçus concordent à l’identité enfant, au code, à l’absence de timeout/interruption et à `raw_stable=true`. Les quatre XML comportent chacun un testcase : les deux positifs ont une failure et les négatifs zéro ; erreurs/skips zéro. Le log brut est lié par SHA aux deux contrôles logs. Ces réussites locales ne rendent pas la campagne complète.

Le septième ACK 9cd935d0…/1 905 octets, sans identité de feuille, reste `error`, tainted true, termination false, log-stability false. Sa chaîne conserve `RpcPrelaunchRefused` causé par `Chrome absent/changé ou admission CDP hors délai5s`. Le `Session.wait` du parent finit rouge parce que le taint est conservé, non parce qu’un bug produit serait prouvé.

## Différence matérielle avec MAIN12

Chrome MAIN13 PID 46190, naissance 1791496023/756297, PPID 45982, UID 501, PGID 46190 : retour **21**, pas -5. Ni timeout ni interruption ; aucune émission de signal dans sa cleanup. Le stderr 39d063620287e4d7a48c2066c5a5fa2880c02fd088d12034506035ecd915133d, 769 octets, signale `Failed to create socket directory`, puis l’abandon ProcessSingleton. L’erreur de handshake Mach Crashpad 46336 y apparaît séparément.

MAIN12 est rehashé : Chrome retournait -5 et son stderr 3eddb80b…/933 octets contenait le fatal `sandbox_parameters_mac.mm:82`. Les argv Chrome sont identiques modulo les racines QA ; le vrai corps AST `start_auxiliary_for_job` est identique. Le profil différent ne constitue pas, à lui seul, une preuve de causalité. Aucune opération kernel précise causant le nouveau refus, ni un dépassement CDP5 plutôt qu’une absence de Chrome, n’est établi ici. Aucune rallonge de délai proposée.

## Arrêt et attribution

La cleanup physique déclarée pour les cibles exactes est true, sans restant attribué, ambiguïté ni erreur. Durées finish : Chrome 0,745390750 s ; services 0,905276833 s ; Session 0,749405083 s. Toutes leurs bornes cleanup8 sont effectivement marquées respectées. Les durées finish sont distinctes des phases qui incluent les scans et la publication.

Quinze signaux contrôleur uniques sont tous joints aux tuples de naissance, UID/PGID/rôle du backend 46014, Vite 46036 et son enfant 46040. Leur parentage rejoint l’owner enregistré. Aucun signal Chrome ou cible inconnue n’est adopté. Crashpad 46336 est cité dans stderr mais absent des records attribués ; son absence physique ou sa terminaison exhaustive n’est pas certifiée par cette revue.

Les deux reçus finaux ports contiennent douze observations réelles : deux passes sur 17593/5173/17594 pour services-stop, puis Session-stop. Chaque lsof est un enfant avec naissance attribuée au propriétaire, argv exact, rc1, stdout/stderr vides et pids[]. Aucun lsof nouveau n’a été exécuté. Session-close relie son pré-restore distinct et atteste restauration des handlers true, erreur de restauration null, session_closed true. `clean=false`, taint true et log-stability false des reçus restent inchangés malgré l’arrêt physique.

## Contrôles de références

Les 79 sources courantes du catalogue sont rehashées, zéro écart. Dans les JSON locaux ledger/session-rpc et résultat/readiness, 179 références path/SHA/taille/canonicalité ont été contrôlées, sans conflit ni écart. Trente-sept paires .pending/publiées sont de mêmes inode et octets, liens physiques au moins doubles, dont les sept ACK ; ce périmètre inclut aussi les gates, releases, plan et enrollments et n’est donc pas un compteur des seuls ACK.

Le reçu analytique pinne 38 fichiers physiques sélectionnés, dont les deux références MAIN12 utilisées uniquement pour la comparaison. Les observations historiques ne sont pas transposées en preuves courantes. Aucune qualification intégrale de dépendances ou nouveau scan Git 3 579 n’est prétendu dans ce sous-lot.

Lecture seule des sources et bruts. Seuls ce rapport et ce reçu, dans leur nouveau dossier privé, ont été créés. Aucun canari, import G1, service, signal, profil ou source ROOT13 modifié. Avis : archives utilisables pour conserver un rouge instrument correctement clos dans son périmètre fini, **pas de qualification A/B FULL, plateau ou release**.
