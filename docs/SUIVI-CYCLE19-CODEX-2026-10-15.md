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

## État de clôture de cette relance

**Boucle en pause, STOP présent, automatisation PAUSED.** La reprise du
15 octobre s'est arrêtée sur le plafond de consommation estimée, avant la
correction. Aucun processus QA n'est conservé. Un heartbeat ne doit pas
lever cette pause. Le cycle 19 reste en MAP, sans transition forcée nouvelle,
sans ronde ni release.

Les lecteurs ont dépassé l'enveloppe indicative de 18 000 jetons chacun.
Le backend rapporte environ 68 000 jetons de sorties d'outils avant
troncature ; le frontend signale un dépassement sans mesure exacte, compté
prudemment à 30 000 ; l'orchestration de reprise est estimée à 25 000.
Avec les 90 000 initiaux, le registre atteint **213 000 estimés**, dépassant
les plafonds GPT de 180 000 et global de 200 000. Ce sont des estimations de
travail et de sorties, pas une mesure de jetons facturés ni du quota du
compte. Le coupe-circuit a refusé la suite lors de leur enregistrement.
Les plafonds n'ont pas été relevés.

### Résultats conservés

- Cartographie validée à **100 % : 2 139 / 2 139**, sans fichier manquant,
  rapport invalide, écart de hash, erreur d'ancre ou seconde lecture absente.
- Les 110 divergences textuelles correspondent toutes à des décisions
  `concordant` préexistantes, aucune décision nouvelle inventée.
- Treize rapports C19 : neuf lectures intégrales et sept lectures
  différentielles au total, la deuxième lecture du test de modèle comprise.
  Les rapports différentiels indiquent les anciennes lectures et les bases
  Git appariées par SHA ; ils ne prétendent pas une relecture intégrale.
- Cinq instruments calibrés avec contrôles positifs et négatifs réels.
- Ruff vert. Suite backend : 4 467 tests recensés, 0 échec, 0 erreur,
  4 ignorés. Suite autonome : 186 recensés, 0 échec, 0 erreur, 4 ignorés.
- Vitest interrompu à l'arrêt budgétaire : aucun verdict global retenu.
  tsc, ESLint et mypy n'ont pas été exécutés par cette reprise.
- Aucun changement du code produit, aucun tag, aucune release.

### Défauts et reprise possible

**B-1793, confirmé** : après un refus de budget de continuation, les jetons
déjà consommés par le premier appel ne sont pas comptabilisés. Le test API
simule un premier appel à 20 jetons d'entrée et 5 de sortie, puis un résultat
d'outil qui fait refuser la suite. L'appel fournisseur suivant est bien
interdit, mais `record_usage` n'a pas été appelé quand l'erreur terminale est
émise. Le test rouge échoue exactement sur `[False] != [True]`.
Il est distinct de B-1775 et B-1776, qui concernent les contrôles avant appel.
Correction non entamée ; le scénario est conservé sous
`.app-loop/cycles/19/reproduction-usage/`, hors de la suite de production.

**B-1794, candidat uniquement** : deux sélections rapides de modèle pourraient
se terminer dans l'ordre inverse. Observation statique dans
`SettingsModal.tsx:559-569` et `LLMTab.tsx:570-575` ; une reproduction par
promesses différées reste nécessaire. Ne pas présenter ce point comme
confirmé. La persistance du texte après refus de continuation est également
une piste de lecture, pas un défaut reproduit dans ce lot.

État et empreintes de clôture :
`.app-loop/cycles/19/reprise/cloture-budget.json`,
`manifest-cloture.json` et `arret-portes-budget.json`.
La reprise exige un nouvel ordre de Ludo et une enveloppe explicite ; elle
devra repartir du test rouge B-1793 et éviter une nouvelle lecture générale.

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

## Constat de départ avant la reprise

Au lancement, `cartography.py refresh` puis `validate` sur le périmètre
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

L'automatisation `th-r-se-cycle-19-reprise-born-e` avait été créée ACTIVE dans
ce chat. Les reprises étaient prévues toutes les quinze minutes, jusqu'à
l'échéance ci-dessus, à un budget atteint ou à un portail humain. Elle doit
vérifier l'absence de campagne concurrente, reprendre ce suivi et rester
silencieuse si l'état n'a pas changé. À l'arrêt, documenter les preuves et
mettre l'automatisation en pause avec l'outil de l'application. Cette pause
est désormais appliquée et vérifiée.
