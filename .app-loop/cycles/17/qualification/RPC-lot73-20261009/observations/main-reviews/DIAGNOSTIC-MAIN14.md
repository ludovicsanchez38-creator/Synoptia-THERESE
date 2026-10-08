# MAIN14 : échec natif et diagnostic IPC ciblé

Natif MAIN `192832`, session52812, terminal `86e6fa` code86.
Résultat réel SHA `93e325cba60c1a0acc4c56a5381b246a7f096f096168aa3b92ab997419359422`,
2 778 octets : sept ACK sur quinze, aucun des quatre parents complet,
sources inchangées et transport RPC fermé, propreté globale/fermeture
qualifiée fausses. C'est une erreur d'instrumentation, pas un bug produit
causal établi. Aucune ronde A/B, calibration complète ou release.

Chrome QA PID52371, birth `1791497547/819649`, parent52214 birth
`1791497515/555159`, UID501, PGID52371. Reçu original SHA575e97ee…,
172 900 octets ; début UTC22:12:27.819508, fin22:12:31.098811.
Il sort en -5, sans timeout/interruption ni signal de nettoyage. Cleanup
0,732452958997 s, deadline tenue, mais taint/stabilité restent rouges.
Les ports17593/5173/17594 sont vides MAIN `681202`.

Stderr lu intégralement MAIN `3ec81b`, SHA
`637af0aa91e5274970a1f3668f78e09532088181b0555c0450ffae9be1e03221`,
1 250 octets. FATAL `mach_port_rendezvous_mac.cc:159` :
bootstrap_check_in de `com.google.Chrome.MachPortRendezvousServer.52371`
refusé1100. Le précédent message ProcessSingleton n'y apparaît plus ;
cette évolution ne prouve pas que Chrome, CDP ou le confinement sont qualifiés.
Crashpad52395 n'est nommé que dans stderr, sans attribution nouvelle.

Collecte MAIN `9cc619` / `dd5368`, code0 : 87 événements macOS, limitée
au PID52371 et aux messages système nommant ce seul PID, fenêtre Paris
09/10 00:12:27–00:12:34. Reçu direct
`/private/tmp/therese-c17-root14-chrome52371-log-sLdxZLOA/receipt.json`, SHA
`9e9879ff4f52ecfe39dd6e6748e93a01233b14846125cffc1adebb11535baf0f`,
1 475 octets. MAIN `65e4a6` isole deux refus mach-register : canal apps
à00:12:29.498006 et rendezvous52371 à00:12:29.499381, ce dernier joint
au FATAL stderr. Les autres refus ne justifient aucune permission globale.
Aucun chemin personnel Darwin n'a été ouvert ou ajouté au profil.

La [source primaire Chromium](https://raw.githubusercontent.com/chromium/chromium/main/base/apple/mach_port_rendezvous_mac.cc)
consultée décrit le nom BundleID.PID du serveur, son bootstrap_check_in
et le lookup des enfants vers le PID parent. Le
[profil commun Chromium](https://raw.githubusercontent.com/chromium/chromium/main/sandbox/policy/mac/common.sb)
paramètre le lookup avec browser-pid. Il s'agit de `main`, pas du code
exact du binaire154 installé. Ces sources orientent une future permission
bornée au canal propre du navigateur ; elles ne prouvent pas son résultat.
Aucun profil, garde G1, cap, délai ou permission n'a été modifié ici.
