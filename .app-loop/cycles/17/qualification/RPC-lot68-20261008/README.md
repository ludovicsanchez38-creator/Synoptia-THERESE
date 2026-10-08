# Lot 68, preuves conservées sans qualification de release

Voir le lot68 dans `docs/SUIVI-CYCLE17-CODEX-2026-10-04.md` pour l'état canonique.
Ce dossier contient les37 archives vérifiées, leurs trois reçus bruts byte-exacts,
les contrôleurs de stockage et les propositions/tests statiques supplémentaires.
`COPY-MANIFEST-pre-split.json` conserve les110 fichiers de la copie initiale.
Le manifeste courant épingle112 fichiers après fragmentation mécanique.
L'archive35 de6 032 202 octets dépasse la limite Git3Mo : elle est conservée
en trois fragments de2 097 152 /2 097 152 /1 837 898 octets, dans l'ordre
part-001, part-002, part-003. Leur concaténation reconstruite a le SHA
`2074bb9ffdb178f23d97a38f680e40bfe340fd09a4a46d3d3dbc303b47baa892`.
Le reçu natif brut et le compte37 archives sont inchangés. Aucun contournement
du hook ni suppression : le fichier complet est aussi conservé en TMP.

ROOT10 reste rouge, CALIBRATE0/2, A/B et FULL non qualifiés. Le nettoyage
physique réussi ne rend pas le résultat natif vert. Les archives ne sont pas
des racines exécutables ni des preuves d'inodes/hardlinks/ownership actifs.
Les quatre liens Singleton et deux sockets privés sont seulement consignés.

`profile-three-static/` est une proposition non compilée/non exécutée.
`composition-main-pure/` conserve les dix tests isolés réellement passés,
pas un lancement Chrome ou une qualification de Session. Le Chrome normal
ouvert par Ludo a été observé séparément ; aucune donnée de son profil n'a
été copiée, importée ou adoptée comme autorité QA.

Aucune version, release, publication ou installation n'est préparée par
ces reçus de stockage. Les preuves de sortie et les limites de la boucle
restent les critères de décision.
