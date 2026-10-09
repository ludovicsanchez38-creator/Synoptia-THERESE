# LOT78 : matrice documentaire de la frontière Chrome/G1

Lot clos sur les sources et les fichiers seulement, le 9 octobre 2026. Aucun nouvel essai natif, aucune activation d'instrument, aucune admission FULL ou release. Auteur principal `/root`, identité de protocole ; propriétaire Unix QA UID501, pas UID0.

## Résultat

La [matrice](matrix/MATRIX.md) couvre textuellement toutes les 21 expressions du profil ROOT15, dont 19 `allow`, et 24 groupes de gardes G1 **sélectionnées**. Ce n'est ni une compilation SBPL, ni une preuve noyau, ni une lecture exhaustive des 193433 octets G1. L'[inventaire MAIN](MAIN-profile-inventory.json) et l'[inventaire Shared](matrix/PROFILE-INVENTORY.json) concordent littéralement avec le profil pinné.

La frontière initiale G1 ferme les argv/env/birth et la remise des reçus, sans intercepter atomiquement tous les fork/exec internes. Le profil accorde déjà process-fork/process-exec/sysctl-read sans filtre, des lectures système et des écritures dans les arbres QA définis. Ces droits existants ne sont pas des permissions nouvellement proposées ni des bugs produit confirmés.

Trois lacunes empêchent de conclure à un remplacement équivalent :

1. Protéger le browser lui-même, pas seulement les helpers.
2. Éviter qu'une politique appliquée au browser soit héritée puis suivie d'une seconde application interne par les helpers. LOT77 n'éprouve que son fork synthétique sans exec.
3. Fermer les capacités des FD et canaux préouverts/transmis ; `close_fds=True` au seul lancement initial n'en donne pas une couverture générale.

Le [rapport Chromium final](chromium/REPORT.md) recroise les chemins helper, launcher et transmission de politique. Ses sources `main` mouvantes et la table datée M128 ne sont pas appariées au build QA dont la metadata relue est `154.0.8037.99`. La [tentative d'appariement](MAIN-version-source-attempt.json) a rencontré une page tag inaccessible et une recherche officielle vide. Cela ne prouve pas qu'un tag ou son code n'existent pas.

La préimage [v1](chromium-v1/REPORT.md) est conservée : v2 précise UID501, l'ancre posix_spawnp sur le même fichier `main` et les pins des entrées locales. Elle ne modifie aucun source runtime ou résultat rouge. Le forum Apple App Sandbox est une comparaison documentaire, pas une preuve de la cause privée exacte de Chrome154.

## Revue et vérifications réelles

La [revue indépendante](review/REVIEW.json) ne trouve pas de défaut documentaire bloquant sur ses sources examinées. Ses 26 fichiers littéraux uniques ont été rehashés avant/après, sans adoption récursive du graphe de références. Elle ne crée aucun GO ni verdict runtime. Ses lectures G1 et logs sont explicitement bornées.

MAIN a relu entièrement les trois livrables et leurs INDEX, puis vérifié les 13 premières copies canoniques et les 26 entrées de la revue : reçu [MAIN-final-text-copy-check.json](MAIN-final-text-copy-check.json), outil `07f2e4`, exit0. Le [script de lecture/comparaison](verify-lot78.mjs) conserve l'inventaire textuel et les neuf SHA des documents préexistants. Il n'importe ni G1, ni produit, ni API sandbox/libproc. Son succès sur ces entrées n'est pas un étalonnage par mutants ou une garantie d'exhaustivité.

Une tentative inline `549cb2` a échoué en SyntaxError sur des retours à la ligne littéraux avant évaluation. Le reçu garde cet échec de préparation ; aucun essai natif ou source existant n'a été modifié. Les lectures incomplètes/erreurs préparatoires antérieures sont nommées dans [MAIN-source-checks.json](MAIN-source-checks.json), sans résultats reconstruits.

Les oracles du tableau restent envisagés et **non exécutés**. Pour Mach, une ressource publiée et un contrôle positif joignable sont nécessaires avant de qualifier un refus causal. Les trois oracles IOKit restent non définis/non exécutables dans ce périmètre ; changer le pin textuel n'éprouve aucun driver.

## Décisions et prochaine question

| Voie | Statut actuel | Ce qui manque avant activation |
| --- | --- | --- |
| Conserver G1 et étudier des contrôles synthétiques nouveaux | Analyse/préparation QA autorisée ; pas de série inchangée à rejouer | Question nouvelle, sources figées, isolation, contrôle positif/négatif, attribution réelle, bornes et revue préalable |
| Politique initiale unique par type avec browser protégé | Piste documentaire ; aucun hook équivalent établi sur Chrome154 inchangé | Source/version appariées, frontière browser/helpers et FD démontrée, delta d'instrument précis, décision de sécurité ciblée et revue indépendante |
| Chrome hors G1 via CDP/broker même UID | Exception non autorisée ; pas solution équivalente validée | Décision explicite sur les droits perdus et nouveau périmètre ; aucun GO général ne la crée |

Aucun profil alternatif n'est fourni ou activé par cette table. Ne pas désactiver Chromium, supprimer aveuglément G1, employer single-process ou contourner le GPU. Ajouter des droits de chemin/lookup n'est pas une solution démontrée à forbidden-sandbox-reinit.

La prochaine préparation utile doit choisir une lacune nouvelle, par exemple héritage à travers exec ou capacité d'un FD déjà ouvert sur un témoin synthétique, sans la promouvoir en comportement de Chrome. Il faut distinguer mesure possible, oracle causal et décision de frontière ; ne pas refaire LOT76/77 ou cette matrice sans delta.

ROOT15 reste rouge, 7/15 ACK, Chrome exit−5, GPU fatal ; quatre timestamps kernel légèrement antérieurs aux births libproc gardent leur réserve, sans tolérance inventée. LOT76/77 s'arrêtent au premier rouge. Mach micro vert et FULLv4 statique ne deviennent pas une admission. CDP5/startup50/cleanup8 restent séparés et inchangés.

## Boucle et persistance

Usage enregistré une seule fois `866be5` : 78 lots GPT, plancher30259333 tokens et durée472s conservés. Ajouts tokens/durée non mesurés, pas une consommation nulle. Budget réel `71d10f` PASS. État `7292a4` : CALIBRATE, cinq calibrations expirées, zéro ronde FULL, diversité dégradée, 23 transitions forcées historiques. Le goal déjà bloqué n'est ni réinitialisé ni déclaré achevé.

Snapshot QA ciblé final `0b178d`, exit1/vide, sans signal ; pas une absence exhaustive des processus ni une clôture adoptée des anciens PID ROOT15 incertains. Aucune campagne native lancée dans LOT78.

Heartbeat existant actualisé avec le repère LOT78 par l'outil du produit, puis persistance vérifiée byte-exacte `c9c295` : ACTIVE, même chat/cadence/échéance, pas un nouveau réveil prouvé. Voir [AUTOMATION-UPDATE.json](AUTOMATION-UPDATE.json). Aucun changement de modèle ou d'autorité QA.

Suivi humain canonique : [SUIVI-CYCLE17-CODEX-2026-10-04.md](../../../../../docs/SUIVI-CYCLE17-CODEX-2026-10-04.md). Les portes `release-therese` restent fermées : aucune nouvelle calibration, ronde indépendante A/B, bump, tag, build de release, landing, updater, publication Discord, installation ou production.
