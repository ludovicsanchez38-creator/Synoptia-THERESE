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
