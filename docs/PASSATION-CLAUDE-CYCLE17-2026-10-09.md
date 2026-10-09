# Passation à Claude : THÉRÈSE cycle 17, 9 octobre 2026

Ludo a demandé d'arrêter Codex, de tout documenter et de passer le relais à
Claude. Cette note est un point d'entrée, pas une autorisation de reprendre,
de changer la frontière de sécurité ou de publier. Les faits et preuves du
lot restent dans le suivi canonique ; ne pas recopier une synthèse comme
preuve native.

## Où commencer

Dépôt local :
`/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE-c15-codex`.

Branche autorisée jusque-là : `codex/cycle-17`.
Base du dernier lot : `3dd046bf3cfa582d3c4a86958544ebe72da1df19`.
Le commit portant cette note est le commit de clôture du lot 80 ; lire
`git log -1` et `git status` pour le HEAD réellement repris, sans les deviner.

1. Lire les instructions Claude réellement applicables, le skill
   `/Users/synoptia/.claude/skills/boucle-amelioration-app/SKILL.md` et ses
   références requises. Pour toute préparation/publication de version,
   appliquer intégralement le workflow release-therese canonique.
2. Lire [le suivi canonique](SUIVI-CYCLE17-CODEX-2026-10-04.md), en particulier
   les derniers lots 75 à 80. Les lots précédents et leurs essais rouges
   restent accessibles par ses pointeurs.
3. Lire le dossier de preuves
   `.app-loop/cycles/17/qualification/RPC-lot80-b1684-20261009/`, d'abord
   README, INDEX, ARRET-PASSATION, MAIN-tests-receipt et les revues.
4. Lire l'état, le budget, les calibrations et le registre bugs actuels,
   vérifier les processus et agents réels avant toute reprise autorisée.
   Ne pas lancer une deuxième campagne.
5. Demander à Ludo le mandat de reprise approprié. Son arrêt révoque la
   continuation Codex jusqu'à ce soir ; cette note n'en transfère pas les droits.

## Ce qui est conservé

Le correctif produit B-1684 dans `src/backend/app/services/rgpd_auto.py`,
son test mémoire permanent dans
`tests/test_b1684_purge_reglage_illisible_memoire.py`, la préimage, le mutant
privé inerte, les bruts complets et la relecture indépendante sont enregistrés.
Pour le résultat et ses limites exactes, voir LOT80 du suivi et REVIEW-GATE.
Ne pas confondre le correctif local vérifié et une qualification de pile réelle.

Le registre B-1684 conserve `deferred`, avec sa preuve locale et un sabotage
rouge enregistré. Ne pas le fermer à partir du seul compteur de tests verts.
Le lot n'a pas corrigé B-1612 ou B-1678 ; PISTES-SHARED donne leurs scénarios
proposés et les empreintes du code lu, sans reproduction.

## État de passation

Les reçus d'arrêt sont dans ARRET-PASSATION.json :
boucle et objectif en pause, STOP canonique présent, heartbeat existant en
PAUSED. Aucun processus QA détenu n'est laissé en cours. Aucune publication
n'a été faite par ce lot. Les cinq calibrations expirées, les zéro ronde et
les portes fermées sont détaillés dans le suivi, pas remis à zéro ici.

Les fichiers opérationnels `.app-loop/state.json`, `budget.json`,
`bugs.json`, `STOP` et le TOML de l'automatisation sont locaux et ignorés
par Git ; leurs reçus/pins sont archivés. Sur un autre checkout ou ordinateur,
ne pas supposer que le push a transporté cet état, ni créer un cycle/état neuf
pour faire disparaître le blocage. Demander le raccord de l'état nécessaire.

## Blocage de qualification à reprendre correctement

Lire les preuves ROOT15, LOT76, LOT77 et LOT79, sans les rejouer inchangées.
Chrome QA reste rouge et FULL n'est pas admis. Les sondes synthétiques fermées
ne mesurent pas la pile complète. FULLv4 reste une préparation statique.
Les réserves d'attribution temporelle kernel/birth doivent être conservées.

Une piste précise de provenance a été retrouvée dans les deux Info.plist :
le commit SCM déclaré est enregistré dans CHROME-SCM-READ.json et LOT80.
C'est le bon candidat pour une recherche documentaire primaire ultérieure,
pas une preuve de source/build apparié ni une autorisation de lancer Chrome.
Préparer un delta concret de frontière et ses oracles si nécessaire.
Une exception Chrome hors G1 ou un changement d'instrument demande une
décision de sécurité ciblée ; le GO général antérieur ne suffit pas.

## Limites et fichiers à préserver

Direct Mac uniquement, pas de VM/UTM. Profils, données et ports QA isolés.
Ne jamais lire ou modifier `~/.therese`, ni accéder au port 17293.
Ne pas désactiver la sandbox Chromium, retirer G1 aveuglément, passer en
single-process ou contourner le GPU. Pas de DNS, serveurs, e-mails ou messages
externes sans autorisation précise. Aucun nouveau tag/release/installation
sans les portes et GO spécifiques du workflow.

Neuf documents étaient déjà modifiés et n'appartiennent pas au dernier lot :
les huit fichiers `docs/application-map/` (README, architecture,
constats-visuels, couverture, dependances, fonctionnalites, inconnues, risques)
et `docs/releases/v0.77.1-alpha.md`. Ils ont été conservés byte-exacts.
Les symlinks non suivis `.venv` et `node_modules` sont préexistants.
Le verrou `.agents-sync-paused` zéro octet était déjà présent ; ne pas
l'effacer sous prétexte que le script de sabotage annonce un retrait.

Les décisions de périmètre démo réservées à Ludo dans la passation du
26 septembre restent réservées. Les pistes de backlog ne sont pas des GO.
Conserver les essais rouges et la différence entre lecture, préparation,
mesure locale, qualification runtime et publication.
