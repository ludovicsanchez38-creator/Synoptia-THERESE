# ROOT11, revue indépendante de clôture et fenêtre CDP

Auteur : /root/cycle17_gate_review. Lecture seule des preuves existantes. Aucun instrument G1 importé, aucun processus QA lancé, aucun signal émis, aucun ancien fichier modifié. Ce reçu n'est ni une admission, ni un positif natif, ni une qualification FULL.

## Résultat conservé

ROOT : /private/tmp/therese-c17-wrapper-canary-eff7b4e4f24649dd8628503bc7bfc8b3

Le résultat natif reste rouge, exit 86, sept ACK sur quinze et stage_refs vide. Six RPC terminés ont leurs vraies naissances, reçus et codes : all-test-runner 0, all-logs 0, pytest positif/négatif 1/0, Vitest positif/négatif 1/0. Les quatre XML contiennent chacun un cas ; les positifs contiennent une failure, sans error/skip. Le témoin logs contient la marque saine et l'erreur injectée corrélée.

Le septième ACK est une erreur prélaunch de la feuille Node, sans leafbirth ni code inventé. La chaîne préservée est RpcPrelaunchRefused, causée par InstrumentError « Chrome absent/changé ou admission CDP hors délai5s ». Chrome a réellement été lancé séparément. Sa sortie -9 correspond au SIGKILL attribué du contrôleur, pas à un crash autonome démontré.

## Clôture physique bornée

79 sources courantes rehashées, aucun écart. 218 références physiques locales de la sélection de reçus contrôlées, aucun écart. 34 couples publication/pending ont même device/inode, nlink 2, UID 501 et bytes : gates, releases, sept demandes et sept ACK.

21 événements de signal uniques sont reliés aux births, UID, PGID et rôles canoniques, sans additionner les copies du même batch présentes dans plusieurs reçus :

- backend 34553, birth 1791493151/922768 ;
- Vite 34560, birth 1791493153/543258 ;
- enfant Vite 34564, birth 1791493154/698177, parent 34560 ;
- Chrome 34667, birth 1791493179/848255.

La filiation Chrome réellement capturée inclut 34816 puis son enfant 34817, ainsi que 34829. Contrairement à une observation historique d'un autre canari, 34817 est ici une birth attribuée par parent vivant ; son nom dans stderr ne crée pas cette attribution.

Les nettoyages physiques des cibles attribuées sont déclarés et joints aux bruts : Chrome 3,769728958 s, services 0,939757250 s, Session 0,739907917 s, tous sous huit secondes, zéro résidu/ambiguïté/erreur. Le scan de ports et la publication du reçu sont hors de cette borne finish et portent leur portée séparée.

Les deux reçus finaux de ports comportent chacun deux passes sur 17593, 5173 et 17594. Les douze diagnostics lsof sont réellement admis avec birth/parent/UID/PGID, rc1, stdout/stderr vides, pids vide. La clôture Session et la restauration des handlers sont vraies ; le reçu pre-restore conserve les flags antérieurs faux.

Les flags originaux restent inchangés : clean=false, taint=true, raw_stable/log_stability_proved=false, owned_shutdown_proved=false. Une fermeture physique des cibles connues ne transforme pas le canari en succès.

## Fenêtre CDP 5 s et coût du contrôleur

Le code actuel calcule expires après Session.start Chrome. Le 50 s est une borne de démarrage/admission, pas une lifetime promise du service. Avant chaque observation, attribute rescane tous les PID listés et les PID connus ; observe_auxiliary_port appelle de nouveau attribute avant chacun de ses deux diagnostics. Chaque listener_pids vérifie encore l'absence de tous les anciens diagnostics lsof attribués.

Ce coût synchrone est inclus dans les cinq secondes et peut consommer une partie ou la totalité d'une itération. Aucun syscall global ni double scan n'est préempté à la deadline. Cela crée une capacité de dépassement/refus instrument, pas une raison de rallonger la borne.

Dans ce brut précis, 106 births diagnostic-lsof ont été capturées entre 20:59:40.634624 et 20:59:45.581649 UTC. Le chemin de code donne 53 doubles observations, mais leurs retours CDP absents ne sont pas sauvegardés individuellement. Ces naissances contredisent une famine avant le premier scan ; elles ne prouvent pas que le port a été disponible, ni un coût nul du contrôleur.

Les compteurs finaux, 1 099 snapshots dans le reçu Chrome, concernent toute la campagne et le cleanup, pas uniquement cette fenêtre. Le tail conservé commence à 20:59:47, après le refus. Aucune durée attribute/info ni valeur expires n'est persistée. On ne peut donc attribuer une proportion chiffrée des cinq secondes aux scans, ni prouver un instant d'ouverture CDP manqué. Aucune optimisation ni changement de délai proposé/appliqué ici.

## Manquant et limites

Huit RPC non terminés, les quatre parents complets, admission CDP, UI/écrans, calibrations complètes et rondes A/B restent manquants. Le périmètre est celui des familles observées et attribuées, pas une preuve d'exhaustivité hostile, de confinement total ou d'absence universelle de descendants. Aucun effet de qualification native/release n'est déduit du présent reçu.

Les 40 références sélectionnées avec SHA et tailles sont dans receipt.json. Les raw sources restent à leur emplacement et inchangés.
