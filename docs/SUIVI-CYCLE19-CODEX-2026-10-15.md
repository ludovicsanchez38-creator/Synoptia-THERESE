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
- Échéance initiale de cette relance : 15/10/2026 à 10:54:23 Europe/Paris,
  annulée par le GO vocal ci-dessous.
- Profil et données de test jetables ; aucune lecture du profil personnel
  `~/.therese`, aucun accès au port 17293, aucune publication.

L'état courant fait foi dans `.app-loop/state.json`. Les états, budgets,
calibrations et STOP antérieurs sont conservés dans
`.app-loop/cycles/19/reprise/avant-*`. Le champ descriptif `repo`, hérité du
checkout du cycle 17, a été réaligné sur le dépôt effectivement utilisé.
L'historique et les 24 transitions forcées antérieures sont conservés.
Le nouveau cycle a été ouvert par `new-cycle`, puis `resume`, sans forçage.

## GO de reprise après échange vocal

Ludo a explicitement demandé de retirer tous les plafonds ajoutés par Codex
et de continuer le travail utile, sans rester bloqué sur des étapes sans
valeur ajoutée. Ce GO annule l'échéance de 10 h 54 et les plafonds d'appels,
de jetons et de durée de cette relance. Ils sont désormais désactivés dans
le budget local, selon la valeur zéro prévue par le script. Les compteurs
historiques approximatifs sont conservés et ne deviennent pas des mesures
de quota réel. Aucun reset d'abonnement n'a été demandé ou consommé.

La boucle et l'automatisation sont de nouveau ACTIVE ; l'automatisation
s'appelle maintenant « THÉRÈSE cycle 19, travail utile ». La règle d'arrêt
sur blocage répété sans progrès reste applicable. La reprise part du test
rouge B-1793, sans refaire les lectures. Le suivi de l'ancienne pause
ci-dessous est conservé comme historique et ne commande plus l'arrêt.

Passage MAP → CALIBRATE documenté avec une exception comptable : le script
historique exige des jetons Claude, alors que les lecteurs étaient Codex et
que leurs usages GPT sont enregistrés. La carte était déjà à 100 %, les
preuves et doubles lectures complètes, les divergences arbitrées ; aucune
preuve manquante n'a été contournée. Puis CALIBRATE → DISCOVER → REPRODUCE
avec les cinq instruments valides. B-1794 a été différé uniquement pendant
le lot de correction prioritaire B-1793 et devra revenir en reproduction.

## Lot B-1793 : comptabilisation après refus de continuation

Le défaut est corrigé dans `chat.py` : le registre reçoit les jetons des
appels déjà effectués avant l'émission de l'erreur de budget de continuation.
Le flux s'arrête ensuite, sans second appel au modèle, double compte ni
événement `done` de succès. La même fonction de comptabilisation sert au
chemin nominal et conserve les coûts calculés appel par appel.

Le test de régression fait désormais partie de la suite versionnée :
`tests/test_c19_usage_refus_budget.py`. Le test échouait avant correction.
Le retrait ciblé de la correction le fait de nouveau échouer ; sa
restauration exacte rend les deux tests de continuation verts. Les
65 tests voisins passent aussi. La relecture indépendante du diff n'a
relevé aucun point bloquant.

Vérification complète après correction, dans un HOME et des données QA
jetables : Ruff vert ; 4 468 tests backend recensés, aucun échec ou erreur,
4 ignorés ; 186 tests autonomes recensés, aucun échec ou erreur, 4 ignorés.
Mypy compte 936 erreurs, exactement la dette de référence existante : ce
contrôle confirme l'absence d'augmentation, pas un typage globalement vert.
Les preuves se trouvent sous `.app-loop/cycles/19/reproduction-usage/`
et `.app-loop/cycles/19/portes-b1793/`. `reprise/portes.py` accepte désormais
un nom de lot et une sélection de contrôles pour préserver les anciennes
preuves et ne relancer que les suites nécessaires.

Le second candidat B-1794 a été réactivé et reproduit par réponses différées.
Sa correction et sa revue sont en cours. Aucune ronde de plateau du cycle
19 ni release ne sont encore validées.

## Pause budgétaire antérieure, remplacée par le GO ci-dessus

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

## Historique des limites initiales, annulées par le GO vocal

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
