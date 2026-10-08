# MAIN11, exception de lecture bornée pour trois profils Apple

La préimage est le contrôleur v2 `/private/tmp/therese-c17-root11-static-controls-v2-loPvxR/verify-prepared-wrapper.mjs` SHA-256 `e8ea3ec950f8defce2e28fddfbfe1697b90425207b6dbcee045c88ffb5284a72` / 19 296 octets. Le v2 et son refus réel avant toute exécution native (outil MAIN `fa326c`, code 1, observation `e6e3d3`) restent intacts. Le refus provenait du contrôle UID 501 appliqué aux profils système UID 0. Ce nouveau gel n'a pas été exécuté.

Le seul delta touche `ref()` et sa garde UID. Le processus lecteur doit être UID 501 ; toutes les références autres que les trois chemins exacts continuent d'exiger un fichier canonique régulier possédé par UID 501. Pour les trois fichiers Apple seulement, la lecture est acceptée si le chemin est canonique, le fichier régulier non-symlink a UID 0, GID 0, mode `0100644`, nlink 1, et ses SHA-256/taille sont exactement ceux épinglés :

- `/System/Library/Sandbox/Profiles/com.apple.GameOverlayUI.sb` : `6320ed0b…` / 10 845 octets ;
- `/System/Library/Sandbox/Profiles/com.apple.gputoolsserviced.sb` : `fb138176…` / 7 234 octets ;
- `/System/Library/Sandbox/Profiles/appsandbox-common.sb` : `b9ffebd2…` / 32 355 octets.

Les métadonnées ont été lues séparément : UID/GID 0/0, mode `100644`, nlink 1 pour chacun. La préimage et les diffs avant/inverse sont conservés. Aucun autre chemin, propriétaire système, wildcard, droit de profil, réseau ou règle Chrome n'est admis. Les oracles MAIN11 ROOT, builder, PLAN, HEAD documentaire `5f89164c…`, profil `bee3c2e7…`, 79 sources et sous-comptes restent inchangés.

Contrôles effectués ici : lecture des métadonnées, diff exact et empreintes. Aucun Node, contrôleur, profil, G1, navigateur, QA runtime ni native n'a été lancé ; aucune admission, FULL ou release n'est revendiquée.
