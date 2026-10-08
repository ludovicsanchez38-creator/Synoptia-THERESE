# MAIN11, résolution historique bornée du rapport Chrome

Statut : préparation statique seulement. Ce contrôleur n'a pas été exécuté ; MAIN11, G1, Chrome et le dépôt produit restent inchangés.

Préimage : `preimages/verify-prepared-wrapper-v3.mjs`, copie byte-exacte du gel v3. `forward.diff` et `inverse.diff` décrivent le seul delta du collecteur. Toutes les autres assertions MAIN11 restent celles de v3.

Le chemin historique `Google Chrome-2026-10-08-143832.000.ips` dans la Library est absent (`ENOENT`). Le routage n'est admis que si le collecteur lit l'index historique exact `c0f542c3…` à `/private/tmp/therese-c17-chrome-rootdomain-h5whIv/INDEX.json`, au pointeur JSON `/origin_refs/4`, avec le triplet ancien chemin/SHA-256/taille exact. Il vérifie aussi `EVIDENCE.json` exact, `diagnostic_only=true` et PID 25577. La copie `/private/tmp/therese-c17-root-close6-I9BhiHpZ/chrome25577.ips` doit être canonique, régulière, UID 501, GID 0, mode 100600, nlink 1, et conserver le SHA-256 `2e1d81e2…` sur 31 835 octets. Toute autre absence, origine, position ou valeur est refusée.

La référence retenue dans `refs` et `pending` porte le **chemin réel de la copie archivée**. `historical_observations` garde l'ancien chemin absent, le pointeur d'origine, les empreintes, les métadonnées mesurées et l'heure de mesure. Il ne prétend pas que le reçu `close6` épingle la provenance de cette copie : l'égalité d'octets est constatée séparément. Les fichiers INDEX/EVIDENCE restent bruts et inchangés.

Vérification effectuée pour la préparation : préimage, SHA/taille de l'index, d'EVIDENCE et de la copie ; `stat` ciblé de la copie ; diff direct/inverse comparés aux deux sources. Aucune exécution du contrôleur ni test natif. La qualification MAIN11 et tout lancement demandent une décision et une exécution distinctes par root.
