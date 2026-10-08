# Revue SQL MAIN14, avant le canari natif

ROOT a lu intégralement le contrat physique MAIN `da3e15` :
`/private/tmp/therese-c17-wrapper-canary-187602c63a0b498a95d25c19843000a8/complements/contrats-normalises-proposes.json`,
SHA `f83732d5193fe7b3b20a07812508ccb2582236742a1a5c64c2ccab8b59c17f3d`,
7 702 octets. Construction réelle `09078e` / `632ca5`, code0 ; source
canari historique HEAD2d69 distincte du dépôt documentaire HEADd148.

Les 36 sources/modes restent explicites. B1753 conserve les registres et
tâches vides entre les deux tests, sans changer les assertions produit.
B1760 conserve dix nouveaux exports joints à nodeid, UUID, HTTP, persistance
et PDF réel ; date d'échéance actuelle dans l'en-tête et première ligne
automatique, absence de l'ancienne date, suffixe et mentions préservés,
contenu émis immuable. SQLCipher réel est requis par le harnais ; il n'est
pas attribué au runtime plaintext v3. Les relations historiques ne sont
pas réécrites et aucun ancien résultat n'est transféré comme résultat actuel.

La note matérialise la lecture MAIN, sans modifier le contrat préparatoire
`root_reviewed:false` ou fabriquer une exécution SQL. Les trois parents SQL
restent soumis aux contrôles tardifs du runtime. Cette revue seule ne
constitue ni PASS natif, ni ronde A/B, ni FULL, ni autorisation de release.

ROOT GO physique également lu `da3e15` : SHA
`782264545625a883593469de24eef30d3b526e61e6b67ba118edb7b50f6e4dee`,
3 398 octets. Il reste limité à WRAPPER_CANARY ; l'appel outil exact MAIN
et le coupe-circuit gouvernent le lancement réel. Aucune publication.
