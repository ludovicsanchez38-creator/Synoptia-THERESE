# Premier refus de l'exécuteur MAIN LOT74

Compte rendu MAIN du retour réel de l'outil `825584`, pas une copie brute
stdout/stderr ni un reçu attribué au relecteur.

L'exécuteur SHA b4aa19d2c95d3f9563559e0ed6ed8cd2cffb6095a04963e50f588e2283da3eb0
a terminé en code1 avant la création de la destination : il traitait
`.git` comme un répertoire, alors que le checkout est un worktree Git.
Exception réelle : NotADirectoryError à la lecture de `.git/HEAD`.

MAIN a vérifié le fichier `.git` (`058d0c`) et git-dir/common-dir (`6f2ec5`) :
le répertoire de ce worktree est physiquement
`/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/.git/worktrees/Synoptia-THERESE-c15-codex`.
L'absence du dossier canonique LOT74 est vérifiée après cet échec (`ca5cd3`).
La préimage byte-exacte est conservée sous
`archive-lot74-reviewed-before-worktree.py`, SHA b4aa19d2c95d3f9563559e0ed6ed8cd2cffb6095a04963e50f588e2283da3eb0.

La correction doit contrôler ce gitdir exact et sa branche, sans parcourir
ou modifier les autres worktrees. Elle ne change ni sélection297, ni
bornes d'archive, statut natif, permissions, produits ou gels préparatoires.
