# THÉRÈSE, cycle 19 : reprise du 15 octobre 2026

Ludo demande de relancer une boucle depuis la dernière boucle réalisée par
Claude, en évitant les tentatives répétées qui ont consommé les quotas lors
du cycle 17. Le présent cycle reprend le dépôt principal après le cycle 18,
pas le checkout `Synoptia-THERESE-c15-codex` resté en CALIBRATE.

## Base et périmètre

- Dépôt : `/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE`.
- Branche de travail : `codex/cycle-19`, créée depuis `f61f28a3` ; main préservée.
- État hérité : cycle 18, POST_RELEASE, deux rondes enregistrées, en pause.
- Référence de livraison : [rapport v0.78.0-alpha](releases/v0.78.0-alpha.md).
- Démarrage du cycle 19 : 15/10/2026 à 09:24:23 Europe/Paris.
- Échéance de cette relance : **15/10/2026 à 10:54:23 Europe/Paris**.
- Profil et données de test jetables ; aucune lecture du profil personnel
  `~/.therese`, aucun accès au port 17293, aucune publication.

L'état courant fait foi dans `.app-loop/state.json`. Les états, budgets,
calibrations et STOP antérieurs sont conservés dans
`.app-loop/cycles/19/reprise/avant-*`. Le champ descriptif `repo`, hérité du
checkout du cycle 17, a été réaligné sur le dépôt effectivement utilisé.
L'historique et les 24 transitions forcées antérieures sont conservés.
Le nouveau cycle a été ouvert par `new-cycle`, puis `resume`, sans forçage.

## Contrôles effectivement réalisés

Le harnais navigateur du cycle 18 a été repris avec seulement le numéro de
cycle et les noms de sortie actualisés. Les deux passages, autonome puis sur
THÉRÈSE, sont verts dès leur première tentative.

- Backend `/health` : healthy, version 0.78.0.
- Attestation du backend de test : offline, loopback-only.
- Base vérifiée vide : zéro contact, projet, conversation, message ou fichier.
- Ports QA : Vite 1420 et API 17393, liés à 127.0.0.1.
- HOME et données : sous `/private/tmp/therese-c19-1ir4t0s8/`.
- Contrôles positifs et négatifs verts pour `runtime_ui`, `visual_capture`
  et `network_capture`, enregistrés avec une validité de 24 heures.
- Capture saine inspectée : accueil THÉRÈSE visible, moteur actif,
  messagerie non branchée, aucune configuration de compte réel.
- Processus backend et Vite détenus par le smoke arrêtés et récoltés.

Preuves locales : `.app-loop/cycles/19/calibration/` et
`.app-loop/cycles/19/reprise/demarrage-receipt.json`.
Commande de reproduction bornée, depuis le dépôt :
`python3 .app-loop/cycles/19/reprise/demarrage.py`.
Elle crée une nouvelle base jetable, lance la pile hors ligne et ferme ses
deux processus dans un `finally`. Elle ne sert pas de preuve de plateau.
Ces scripts et preuves sont locaux, ignorés par Git ; un push du suivi ne
les transporte pas vers une autre machine.

## Travail suivant

La phase reste MAP. `cartography.py refresh` puis `validate` sur le périmètre
existant `src tests scripts .github` donnent 2 124 fichiers couverts sur
2 139, soit 99,30 %. Quinze fichiers ont changé depuis leurs lectures,
notamment les derniers correctifs et le bump du cycle 18. Aucun nouveau
fichier, rapport invalide, écart de hash ou erreur de preuve.

Lire `.cartography-work/inventory/refresh.json` pour les quinze chemins et
leurs lots. Ne pas recommencer l'inventaire. Rapprocher les 110 divergences
textuelles héritées des arbitrages déjà enregistrés ; ne pas les déclarer
bugs produit ni inventer de nouvelle décision humaine. Un fichier attend
également sa deuxième lecture indépendante. Les calibrations `test_runner`
et `logs` restent à renouveler. Aucune ronde du cycle 19 n'est validée.

## Limites de consommation et reprise

Cette relance est bornée à 90 minutes, 200 000 jetons déclarés au total,
dont 180 000 GPT, et huit appels GPT. Le compteur initial de 90 000 jetons
est une **estimation prudente**, explicitement étiquetée ; le compte exact
de cette conversation n'est pas fourni par le runtime. Ce registre ne
mesure pas le quota hebdomadaire du compte et ne constitue pas un plafond
matériel sur celui-ci. Aucun moteur externe CLI n'a été lancé.

Appliquer la règle anti-mur du skill actuel : au deuxième échec pour une
même cause, arrêter cette voie ; trois lots sans progrès mesurable imposent
une pause. Aucune relance automatique ne lève cette pause. Ne pas réactiver
l'ancienne automatisation du cycle 17. Ne pas relever les plafonds.

L'automatisation `th-r-se-cycle-19-reprise-born-e` a été créée ACTIVE dans
ce chat. Une reprise est prévue toutes les quinze minutes, jusqu'à
l'échéance ci-dessus, à un budget atteint ou à un portail humain. Elle doit
vérifier l'absence de campagne concurrente, reprendre ce suivi et rester
silencieuse si l'état n'a pas changé. À l'arrêt, documenter les preuves et
mettre l'automatisation en pause avec l'outil de l'application.
