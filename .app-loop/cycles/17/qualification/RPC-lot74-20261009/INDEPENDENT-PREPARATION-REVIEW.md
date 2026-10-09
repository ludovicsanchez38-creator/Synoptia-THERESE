# LOT74 : revue corrective worktree

Acteur `/root/cycle17_gate_review`. Avis favorable à la préparation documentaire exacte de l'exécuteur `f20c1a846a6435344b50e1b4dd421484f11d60320a7410d068d3fea2adef5673`, 11 634 octets. Aucun exécuteur, contrôleur, Git CLI, G1, archive ou runtime lancé par le relecteur.

La première revue demeure immuable et préparatoire. Le premier appel MAIN `825584` est rouge avant création de destination. Le récit `ARCHIVE-LOT74-PREMIER-REFUS.md` est explicitement un compte rendu MAIN, pas un stdout/stderr brut ni un reçu de ce relecteur. La préimage `b4aa19d2…` / 9 869 octets et les trois pièces de l'ancienne revue sont vérifiées physiquement.

Delta relu intégralement : seule adaptation de branche au vrai worktree, plus les copies documentaires annoncées. `.git` est un fichier canonique régulier de 104 octets, SHA `c16434f6…`, qui pointe exactement vers le gitdir physique déclaré. Son HEAD canonique régulier de 31 octets, SHA `f2018152…`, porte `ref: refs/heads/codex/cycle-17`. Aucun parcours d'autres worktrees ni child CLI. Destination LOT74 absente lors de cette lecture (`44f520`).

Le candidat initial correctif `070ff826…` avait une seule réserve : récit du premier refus non soumis à `exact()`. L'exécuteur final ajoute exclusivement le contrôle SHA `eb860e2311ba1ae94be6485d90b225bce977ef6dd41fce24e4984d8d439536fd` / 1 159 octets. Retirer cette unique ligne restitue byte-exact le candidat relu, sans autre changement.

Les 297 entrées, 14 568 266 octets, digest `bcf84da4…`, contrôleur `4938b04f…`, PLAN `2b43270e…` et INDEX `9ead71cd…` restent identiques. Cette revue corrective ne retraverse pas leur sélection : elle s'appuie sur les mesures FS-only antérieures et rehashes les pins centraux. Les contraintes TAR, bornes 3/8/24 MB, exception source unique de 95 membres, publications nlink 2 et exclusion du journal système brut sont inchangées.

Copies futures : exécuteur, INDEX et les deux pièces locales de la présente revue, préimage du premier exécuteur, récit interprété du refus, trois pièces de l'ancienne revue, soit neuf copies documentaires en plus des trente TAR, manifeste et reçu. Les deux pièces locales sont limitées à REVIEW.md et observations.json ; aucun autre fichier local de revue n'est demandé. O_EXCL, destination canonique fermée, absence d'overwrite/suppression et recontrôle sources avant/après sont conservés.

Les rouges, statuts structurels/purs et limites de provenance restent préservés. Avis de préparation seulement : aucun GO humain, admission A/B, FULL ou release. Le futur résultat MAIN doit encore être lu comme résultat d'archivage effectif.
