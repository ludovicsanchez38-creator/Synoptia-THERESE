# Archive des preuves ROOT10 closes

Ce contrôleur dérive du contrôleur lot68 v1 conservé en préimage. Il ne lance aucun enfant, service, navigateur, socket ni Git. Il exige le reçu réel de fermeture main `315c9c8d…`, le rouge natif inchangé et trois racines exactes. Les limites USTAR/gzip de 64 MiB, types réguliers, SHA, taille, identité physique et contrôle après écriture sont conservés.

Le seul ajout de types est leur observation et exclusion, jamais leur suivi : quatre symlinks Singleton aux cibles exactes et deux sockets privés, inventoriés réellement par `728313`. Le contrôleur refuse tout autre symlink/socket et revérifie identité/cible après archivage. Ces objets sont consignés dans le reçu. Aucun fichier d’origine n’est changé ou supprimé.

Le résultat natif reste rouge. La fermeture physique, la signature et le diagnostic ne donnent ni FULL, ni ronde, ni permission de publication. L’extraction TAR conserve les octets et propriétés déclarées, pas les inodes et hardlinks actifs de la Session originale ; elle ne peut donc jamais servir d’autorité live.
