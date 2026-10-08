# Revue indépendante de clôture ROOT14

Portée : lecture des bruts terminaux, sans lancement, import G1, sondes OS, signal ou mutation de ROOT14. Acteur : /root/cycle17_gate_review.

Racine : /private/tmp/therese-c17-wrapper-canary-187602c63a0b498a95d25c19843000a8

Conclusion : rouge instrument archivable. La fermeture physique des identités attribuées est cohérente avec les reçus. La campagne reste non qualifiée : runner86, sept ACK sur quinze, aucun des quatre reçus parents finalisés, owned_shutdown_proved=false, clean=false, taint=true et log_stability_proved=false. Pas de FULL, A/B ou release.

Contrôles physiques : 79 sources exactes du catalogue, 214 références courantes du graphe ledger/RPC initialement rehashées, puis 220 références courantes avec les oracles plus deux références historiques ROOT13, soit 223 références SHA/taille contrôlées. Aucun écart dans deux lectures bornées. Les 37 couples pending/publiés sont des fichiers réguliers canoniques du même inode/dev, nlink≥2 et mêmes octets. Aucun historique n'est substitué à une source courante.

Les six ACK ordinaires joignent réellement request, receipt, cleanup et childbirth : all-test_runner0, all-logs0, pytest positif1/négatif0 et Vitest positif1/négatif0. Les quatre XML ont chacun une suite et un testcase, zéro erreur/skip; un failure exact pour chaque positif, aucun pour les négatifs. Le log JSON contient le témoin sain corrélé et l'erreur injectée corrélée. Le septième ACK est error, sans leafbirth ni exit métier, avec la chaîne RpcPrelaunchRefused → InstrumentError admission CDP.

Chrome52371, birth1791497547/819649, parent52214 birth1791497515/555159, UID501/PGID52371, a bien été lancé/libéré. Gate, release et service-start sont joints aux mêmes identité, argv, env et cwd. MAC_CHROMIUM_TMPDIR=TMPDIR est réellement le tmp QA du service. Chrome sort en -5, timed_out=false, interruption=null, aucun signal de cleanup Chrome. Le fils52408 birth1791497549/359166 a été attribué pendant parent exact vivant. Crashpad52395, présent dans stderr, n'est pas admis au ledger : sa terminaison n'est pas prétendue.

Différence matérielle ROOT13 relue : exit21 ProcessSingleton/Failed to create socket directory précédemment; ROOT14 stderr1250B 637af0aa91e5274970a1f3668f78e09532088181b0555c0450ffae9be1e03221 porte maintenant FATAL mach_port_rendezvous_mac.cc159, bootstrap_check_in com.google.Chrome.MachPortRendezvousServer.52371 denied1100. Aucun refus configd, Mach global ou causalité kernel unique n'est inféré depuis ces lignes.

Cleanup Chrome0.732453s, services0.883034s et Session0.749016s, avec bornes8 vraies dans les bruts, physiques clean=true et remaining_attributed/ambiguities/errors vides. Ces valeurs ne réparent pas le taint. Les 15 événements uniques SIGSTOP/SIGTERM/SIGCONT concernent backend52244, Vite52257 et fils52262; 45 occurrences recopiées dans trois reçus se joignent aux mêmes births/UID/PGID/rôle/filiation. Aucun signal Chrome ou PID inconnu. Deux passages×trois ports17593/5173/17594 par arrêt services et Session, soit12 scans finaux, rc1/flux/PIDs vides et diagnostics Python-gate à birth propre. Handlers restaurés, Session close vrai.

Les bornes50 de démarrage,5 d'observation CDP et8 de cleanup restent distinctes. Chrome commence à22:12:27.819508UTC et cleanup débute environ2.547s après son start; le texte d'exception regroupe mort/changement/expiration et ne prouve pas une expiration5s. L'arrêt finish ne comprend pas les sondes ports ni la publication; les reçus séparent explicitement ces phases. Pas de modification de délai, profil ou attribution.

Limites : aucun nouveau syscall libproc/lsof ni mesure de liveness courante par le relecteur; assurance bornée aux preuves enregistrées et identités capturées, pas à tous les descendants ou au confinement total. Aucun résultat incomplet rempli par défaut. Le kernel ciblé est le lot séparé du parent.

