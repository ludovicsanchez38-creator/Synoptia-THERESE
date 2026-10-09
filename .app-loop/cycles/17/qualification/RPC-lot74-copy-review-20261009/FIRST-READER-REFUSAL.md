# Premier refus du lecteur indépendant

Outil réel `03b9e5`, code 1, après lecture conforme des trente TAR et avant la fin des neuf copies documentaires.

Erreur réelle : `ValueError: Copy changed during read`, sur `INDEPENDENT-PREPARATION-REVIEW.json`.

Le lecteur initial comparait les `stat_result` entiers, ce qui inclut atime et peut donc confondre une lecture normale avec un changement du contenu. L'outil ne conserve pas les deux structures stat : le champ effectivement changé n'est pas démontré par ce premier retour. Sa préimage est conservée byte-exacte sous `verify_copies-before-stat.py`, SHA `fd6487e2a06ac577163991e2e553ecefee37866658a9d234264188b70be0c6f4`, 9 846 octets.

Le successeur compare explicitement dev/inode/type/mode/UID/GID/nlink/taille/mtime_ns/ctime_ns, et conserve les hashes physiques exacts. Il ne compare pas atime. Aucun byte de l'archive ou des sources n'est modifié, aucun runtime n'est lancé et le premier refus n'est pas remplacé par une réussite fabriquée.

Second refus réel `1fba93`, code 1 : `ValueError: Extra file or missing copy`. Les trente TAR, 310 membres et neuf copies documentaires avaient passé les checks. Un README.md de finalisation a été ajouté au dossier canonique depuis la première liste `16703d` ; l'égalité stricte des 41 fichiers a donc refusé un 42e fichier. Le lecteur correspondant est préservé sous `verify_copies-before-readme.py`, SHA `251a7a373f771f0eb94ad0b8bccfb41c328e9e32eae727030918ba07d8ea0472`, 10 108 octets. Cette note ne qualifie pas une annexe non épinglée et n'exempte aucun payload TAR.
