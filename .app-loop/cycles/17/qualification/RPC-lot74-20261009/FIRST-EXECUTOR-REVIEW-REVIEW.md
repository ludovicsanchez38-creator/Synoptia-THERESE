# LOT74 : revue préparatoire indépendante

Acteur `/root/cycle17_gate_review`. Contrôleur, plan, INDEX, README et exécuteur MAIN lus intégralement. Aucun contrôleur, archiveur, G1, processus QA, collecteur système ou runtime exécuté par le relecteur. Lecture de fichiers, SHA, JSON et membres TAR existants uniquement.

Avis favorable à cette préparation documentaire exacte, pas à une qualification native ou à une release. Le contrôleur reste fermé : `--execute` refuse avant émission. L'exécuteur séparé exige un appel MAIN explicite et cette revue physique épinglée. Cette revue n'est ni un GO humain ni une nouvelle admission runtime.

## Mesures physiques

Les trois pins centraux sont exacts : INDEX `9ead71cd…` / 3 911 octets, PLAN `2b43270e…` / 12 619, contrôleur `4938b04f…` / 22 710. Les douze refs locales sont rehashées, et les deux paires de diffs direct/inverse reconstruisent exactement les préimages.

Lecture indépendante `2055e1` : 28 lignes plus dix documents externes, 297 entrées, 14 568 266 octets, digest exact `bcf84da4132f8d65202a911bfe9156441eb2f0cd97ce2ae9509fd063549ce5c4`. Aucun parcours récursif de checkout ou de dépendances. Sélection déterminée par ancres et tables pinned, non par découverte libre. Quinze publications sélectionnées avec nlink 2 ont leur pending du même inode/dev, propriétaire et octets ; les autres entrées sont régulières nlink 1.

Seule exception de taille au-delà de 3 MB : `source-qa-evidence.tar.gz`, SHA `bab6b66a868bb7d361e32f3d8a389bbaf588ae0edee1f153ffb7cd5d3a174a68`, 6 963 011 octets, bornée à 8 MB. Lecture existante `107bd0` : 95 membres réguliers exacts, modes TAR 0600, uid/gid/mtime 0, aucun lien, SHA/tailles égaux au manifeste ; 32 592 096 octets de contenu et 32 665 600 octets de flux TAR. Ce sont des snapshots documentaires, pas des objets physiques d'identité vivante. Les liens de publication sont archivés comme octets réguliers, jamais recréés ni suivis.

Le brut système privé complet `stdout.json` de 237 034 octets est absent des 297 chemins. Seuls son reçu et une sélection de sept événements correspondent au plan. Chaque événement minimal retrouve une occurrence physique exacte dans le brut privé. Les refs vers ce brut dans les métadonnées ne font pas entrer son contenu dans l'archive.

## Conservation des statuts

La compilation Mach dépréciée rouge, l'ancien archivage rouge, le préflight checker rouge puis son successeur vert, le post-birth structurel seul, ROOT15 natif rouge exit 86 et la première contradiction analytique de chronologie restent distincts. Le microcanari Mach vert garde sa portée unique. Aucun snapshot WRAPPER ou pur n'est promu en A/B, FULL ou release.

La revue indépendante ROOT15 et ses neuf fichiers sont sélectionnés byte-exacts. Elle conserve sept ACK sur quinze, taint/clean/owned-shutdown rouges et les quatre écarts entre horodatages kernel et births libproc, sans tolérance inventée. FULLv4 n'est pas sélectionné partiellement et demeure un chantier séparé.

## Exécuteur MAIN

Source `archive-lot74-reviewed.py` exact : `b4aa19d2c95d3f9563559e0ed6ed8cd2cffb6095a04963e50f588e2283da3eb0`, 9 869 octets, régulière canonique UID 501/nlink 1 (`91a0cb`). Import du seul contrôleur préparé pinned, sans son `main()`. Aucune importation produit/G1 ou invocation OS enfant dans les deux sources lues.

Il rétablit l'égalité complète du digest et du cardinal des 297 entrées, puis ajoute les treize contrôles préparatoires. Émission prévue : trente TAR, deux copies de métadonnées, manifeste et reçu. Destination littérale `RPC-lot74-20261009`, branche `codex/cycle-17` contrôlée, absence de destination exigée, parents canoniques, écritures O_EXCL sans overwrite/suppression. TAR USTAR réguliers, mode 0600, uid/gid/mtime 0, noms relatifs, contenu rehashé, gzip CRC relu, bornes 3 MB sauf ligne source 8 MB et total compressé 24 MB. Les sources/inodes/timestamps/nlink sont recontrôlés avant/après.

Les bytes source de publication et les classifications sont conservés. L'archivage ne garantit pas une capture hostile sans race ; pins, lstat/fstat et comparaisons réduisent le risque mais ne remplacent pas une autorité runtime. Aucune archive nouvelle n'existait comme résultat de cette revue.

Le prochain contrôle du relecteur portera uniquement sur les copies et membres effectivement émis par MAIN, leurs hashes, modes et manifeste. Il ne réinterprétera pas un reçu documentaire comme une qualification native.
