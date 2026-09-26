# Suivi du cycle 14 par Codex, 26/09/2026

Cette note complète `PASSATION-CODEX-2026-09-26.md`. Elle décrit uniquement le
travail fait dans une copie isolée, créée depuis `main` à `375b9df8` : le dépôt
source et la version publiée n'ont pas été modifiés dans cette session.

## État vérifié

- Boucle locale : cycle 14 ouvert, phase `CALIBRATE`. La garde de sortie de MAP
  a été forcée avec une justification enregistrée : les lecteurs étaient des
  sous-agents Codex, sans appel ni consommation Claude à inventer.
- Carte différentielle : à l'ouverture, 10 fichiers à relire, aucun nouveau
  ni disparu ; le cumul de la branche en compte 13 après les deux correctifs.
  Le dernier rafraîchissement a repéré les trois fichiers touchés ; chacun a
  été relu par deux lecteurs indépendants, puis la carte a été régénérée.
  Couverture validée 2 071/2 071 sur
  `src tests scripts .github`, dont une double lecture de `rgpd_auto.py`.
  Les 113 divergences d'invariants encore listées dans le rapport ont déjà un
  arbitrage ; la garde n'en signale aucune de non résolue.
- Le registre local compte pour le cycle 13 366 bugs corrigés, 180 différés et
  9 rejetés, légèrement plus que le cliché de la passation (365/178/9).
- `B-1605` corrigé dans la branche locale `codex/cycle-14` : le formulaire
  accepte `0,5` pour devis et factures, mais refuse toujours zéro. Le schéma
  API acceptait déjà les quantités strictement positives.
- `B-1709` découvert par revue indépendante puis corrigé séparément : une
  quantité ou un prix de 400 chiffres devenait `Infinity` et partait à l'API.
  Les valeurs non finies sont maintenant refusées avant la requête.
- TDD `B-1605` : 2/7 tests rouges avant correctif ; 26/26 tests ciblés verts,
  170/170 tests factures verts, 8/8 tests backend verts, TypeScript, ESLint et
  Ruff verts. Sabotage de l'ancienne borne : 2/7 rouges ; après restauration :
  7/7 verts. Les JUnit et le détail sont dans la copie locale sous
  `.app-loop/cycles/14/repair-b1605/`.
- TDD `B-1709` : 2/9 tests rouges avant correctif, 9/9 verts, sabotage
  2/9 rouges puis restauration 9/9 verts. La suite factures élargie est à
  172/172, et la suite frontend complète à 3 335/3 335. TypeScript et
  ESLint ciblé sont verts.
- Calibrations `test_runner` et `logs` valides dans la copie. `runtime_ui`,
  `visual_capture` et `network_capture` sont invalides : la sandbox refuse
  l'écoute de `127.0.0.1:17393` (`Errno 1`) et le démarrage de Chromium
  (`MachPortRendezvousServer`, permission refusée). Aucun service n'écoute
  sur 17393/1420 après ces essais. Preuves et script rejouable dans
  `.app-loop/cycles/14/calibration/` de la copie locale.
- Aucun parcours réel de THÉRÈSE, aucune installation ni release n'a été
  vérifié ou effectué pendant ce cycle. Le plateau est donc non évalué.

## Reprise sur un hôte autorisé

1. Intégrer les commits de `codex/cycle-14` dans le dépôt source après revue.
   Vérifier d'abord que sa base est encore `375b9df8` ou rebaser proprement.
2. Reprendre le cycle 14 de la boucle dans le dépôt source avec son état local,
   puis rafraîchir et valider sa carte différentielle. Ne pas copier les JSON
   d'état de cette copie sans réconciliation des chemins et des événements.
3. Rejouer les calibrations navigateur avec le script C14 et une pile jetable
   17393/1420, puis vérifier le correctif `B-1605` dans l'application servie.
4. Poursuivre les différés moyens selon la passation. Les décisions métier et
   de marque listées dans cette dernière restent réservées à Ludo. Aucune
   release sans son GO explicite.

L'envoi GitHub de cette branche n'a pas pu être fait depuis cette session :
la résolution DNS de `github.com` est refusée par la sandbox. Une archive Git
vérifiée des commits est disponible à côté de la copie du dépôt, sous
`../THERESE-cycle14-Codex-2026-09-26.bundle`. Elle transporte la branche et
requiert le commit de base `375b9df8`, déjà présent dans le dépôt source.

## Reprise dans le dépôt source par Codex, 26/09/2026

Les sections précédentes décrivent la copie de préparation. Cette reprise a
été effectuée dans le worktree isolé
`/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE-c14-codex`, sur la
branche `codex/cycle-14`. `main` est restée sur `375b9df8` et propre. Le
bundle a passé `git bundle verify` ; son SHA-256 est
`daf9ee7c3e795185415ad32e87e1f085b1b703d2545ccb21d1bfea35e93eb2be`.
Les six commits importés se terminent à `637d81ba` avant la présente note.

### État local réconcilié

- Le dernier événement de la boucle source (cycle 13, `POST_RELEASE`) apparaît
  dans l'historique de la copie, suivi de 17 événements du cycle 14. La copie
  ajoute `B-1709` et passe `B-1605` de `deferred` à `fixed` ; aucun autre bug ne
  diffère. Les 106 calibrations source sont le préfixe exact des 111 entrées de
  la copie, et les budgets des cycles 1 à 13 sont identiques.
- Les dossiers ignorés `.app-loop` et `.cartography-work` ont été transférés
  dans le worktree après ce contrôle. Seuls les chemins opérationnels
  `state.json:repo` et `inventory.json:repo` ont été reliés au worktree ; la
  copie a été ajoutée à `repo_precedents`. Le `STOP` posé dans l'ancienne
  sandbox a été levé par `app_loop.py resume`, avec événement tracé.
- `cartography.py refresh` a rendu 0 modifié, 0 nouveau, 0 disparu. La
  validation a rendu `PASS`, 2 071/2 071 fichiers couverts dans
  `src tests scripts .github`, sans erreur de preuve ni lecteur manquant.

### Calibration et recette sur données jetables

Le dépôt, localhost et Chromium Playwright ont été vérifiés avant la reprise.
Les contrôles de navigateur ont utilisé 127.0.0.1:1420 et :17393. Le backend
avait un `HOME` et un `THERESE_DATA_DIR` sous
`/private/tmp/therese-c14-reprise-jd_nb5om/`, `THERESE_SKIP_SERVICES=1`, le
mode hors ligne des modèles et les clés API usuelles retirées de son
environnement. Le port 17293 et `~/.therese` n'ont pas été utilisés. Les deux
services ont été arrêtés après la recette.

Les cinq instruments ont été rejoués avec contrôles positif et négatif puis
enregistrés `PASS` pour 24 heures : `test_runner`, `logs`, `runtime_ui`,
`visual_capture` et `network_capture`. Les preuves brutes sont locales, sous
`.app-loop/cycles/14/calibration/reprise/` et dans
`browser-controls-c14-app.json` au niveau `calibration/`. Deux captures saines
étaient identiques ; le défaut visuel injecté donnait une capture différente.
Playwright a vu les réponses témoin 200 et 503, sans erreur de page ni requête
refusée. Les captures ont été inspectées.

Le premier contrôle `standalone` a révélé une erreur dans le témoin réseau du
script local : le chemin testé finissait par `/fault`, alors que la requête
visait `/api/calibration/c14-fault`. Sa sortie en échec a été conservée, la
condition a été corrigée en égalité exacte, puis le contrôle a passé. Ce
script vit dans `.app-loop`, hors Git ; cette ligne explique la correction à
rejouer si le script est transporté séparément.

Sur l'application servie, un contact fictif `Cycle14 Jetable` a permis de
créer un devis et une facture en brouillon avec `0,5` jour chacun. Pour les
deux, l'UI a envoyé `0.5`, l'API a répondu 200 avec `0.5`, puis une lecture
indépendante de chaque pièce a retrouvé `0.5`. La quantité `0` et une saisie
de 400 chiffres ont été refusées avant tout POST. Rapport et captures :
`.app-loop/cycles/14/calibration/reprise/verifier-b1605-browser.json` et
`b1605-{devis,facture}-demi-jour.png` dans le même dossier.

### Position actuelle et limites

`app_loop.py status` rend `active`, cycle 14, phase `DISCOVER`, cinq
calibrations valides, zéro ronde de plateau. Les 301 différés attendent la
suite de la découverte et de la reproduction. La copie locale des dépendances
frontend a servi Vite 5.4.21 alors que `package.json` demande `^7.3.6` :
resynchroniser les dépendances verrouillées et recalibrer avant un plateau ou
une release. L'indexation du contact fictif a échoué hors ligne faute de modèle
local ; la recette de facturation a réussi. Aucune suite complète, aucun
binaire installé, aucune fusion et aucune release n'ont été vérifiés ou
effectués pendant cette reprise. L'état et les preuves de la boucle restent
ignorés par Git : la branche seule ne les transporte pas.
