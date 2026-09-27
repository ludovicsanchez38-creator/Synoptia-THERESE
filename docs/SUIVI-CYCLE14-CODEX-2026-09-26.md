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

## Deuxième passage de réparation, 27/09/2026

La boucle a continué de `DISCOVER` à `REPRODUCE`, puis à `REPAIR`, sans PR ni
release. Les six fiches ci-dessous ont été reproduites sur des données
jetables, corrigées et fermées dans `.app-loop/bugs.json` après un sabotage
rouge sous `.agents-sync-paused` et un retour au vert. Le verrou a été retiré
après chaque restauration vérifiée.

| Bug | Constat et correctif | Preuve ciblée |
| --- | --- | --- |
| B-1553 | `/today` et `/semaine` rendaient l'heure murale de Paris sans décalage. Ils réutilisent maintenant le sérialiseur de l'Agenda, déplacé dans `civil_time.py`. | 2 tests rouges avant, 71 voisins verts, 2 rouges au sabotage, 2 verts restaurés. |
| B-1563 | `POST` et `PUT /preferences` permettaient de changer `working_directory` sans passer par sa route gardée. La porte générique refuse cette clé. | 2 rouges avant et au sabotage, 2 verts restaurés. |
| B-1564 | `GET /preferences` rendait les jetons et secrets CRM chiffrés. Il partage désormais avec l'export RGPD un prédicat qui filtre les clés sensibles. | 1 rouge avant et au sabotage, 1 vert restauré ; 93 tests voisins sécurité/configuration/export verts. |
| B-1703 | Six tests du routeur chat pouvaient appeler un fournisseur cloud hérité de l'environnement. Un fixture limité à ce fichier remplace le transport LLM par un flux fictif. | Clé Anthropic factice, réseau interdit : 1 rouge avant et au sabotage ; 101 tests chat et voisins verts. |
| B-1710 | `DELETE /preferences/working_directory` effaçait le dossier choisi et réactivait le repli MCP vers un dossier plus large. La route générique refuse maintenant cette suppression. | 1 rouge avant, 1 rouge au sabotage, 1 vert restauré. |
| B-1711 | `DELETE /preferences/anthropic_api_key` effaçait la base mais laissait la clé dans le cache LLM. La route générique refuse les clés API et renvoie vers la suppression dédiée, qui invalide les caches. | Clé factice et données jetables : 1 rouge avant, 1 rouge au sabotage, 1 vert restauré ; 35 tests voisins verts. |

Les JUnit rouges, verts, de sabotage et de restauration sont conservés dans
`.app-loop/cycles/14/repair-b1553/`, `repair-b1563-b1564/`,
`repair-b1703/` et `repair-b1710-b1711/`. Le filtre des secrets conserve
explicitement `token_limits`, qui règle un budget de jetons sans contenir
d'identifiant : ce cas a d'abord échoué, puis passé après la correction.
Ruff sur les neuf fichiers de code et de tests touchés et `git diff --check`
passent. Après les deux dernières gardes, un dernier passage des cinq modules
de tests concernés a réussi 112/112, avec HOME, base et clés factices isolés
(`verification-current/final-focused.xml`).

Les dépendances frontend du worktree ont été réinstallées depuis
`package-lock.json` en mode hors ligne : Vite est à `7.3.6`. `npm run build`
réussit (TypeScript et build Vite). Sur la pile jetable 1420/17393, avec
Chromium en fuseau `America/Martinique`, un rendez-vous local fictif créé à
16 h à Paris apparaît à 10 h dans le brief. Les réponses réelles de `/today`
et `/semaine` portent `+02:00`. Aucune requête extérieure ni erreur de page ;
capture inspectée et rapport `repair-b1553/recette-martinique.json`.

La suite backend complète a exécuté 4 188 tests : 4 173 réussis, 5 ignorés,
10 échoués dans les seuls tests de confinement des commandes d'agents, que la
sandbox de cette session empêchait de démarrer. Le lot de confinement entier,
relancé avec les permissions locales requises, passe 15/15 sur HOME et données
temporaires. Il ne s'agit donc pas d'un passage intégral vert sous la sandbox
initiale ; les deux résultats et leurs JUnit restent distincts sous
`.app-loop/cycles/14/verification-current/`.

Le changement de Vite a déclenché une nouvelle calibration sur l'application
servie : `runtime_ui`, `visual_capture` et `network_capture` sont `PASS` avec
contrôles positif et négatif, jusqu'au 28/09/2026 à 07:46 UTC. Deux captures
saines sont identiques, le défaut témoin est visiblement différent, les
réponses réseau 200 et 503 ont été relevées. Les captures ont été inspectées.
Les instruments `test_runner` et `logs` restent `PASS` ; `calibration-status`
rend `PASS` pour les cinq. Le rapport neuf est
`.app-loop/cycles/14/calibration/browser-controls-c14-app-vite7.json`.
Playwright 1.58.2 a été copié sous `.app-loop/tools/` pour garder l'outil de
calibration disponible après `npm ci`, sans changer les dépendances verrouillées.

Le différé B-1240 demeure une question d'architecture : l'accord cloud pour
générer une réponse à un e-mail reste dans le stockage du navigateur, alors
qu'une garde fiable dans le moteur aurait besoin d'un état côté serveur.
B-1499 demande une règle de migration pour des dates anciennes ambiguës ;
B-1609 et B-1672 restent dans la file des heures hors de Paris. Aucun de ces
quatre sujets n'a été déclaré corrigé. La pile jetable a été arrêtée après
recette ; aucun service n'écoute sur 1420 ou 17393. Le port 17293,
`~/.therese`, `main` et la version installée n'ont pas été modifiés.

La double lecture différentielle des neuf fichiers modifiés ou nouveaux a
validé les empreintes et les ancres des deux lecteurs. La cartographie couvre
2 074/2 074 fichiers dans `src`, `tests`, `scripts` et `.github` (`PASS`) ; la
carte fonctionnelle sous `docs/application-map/` a été régénérée. Aucun bug
candidat ou confirmé ne reste dans le registre. La phase a avancé de `REPAIR`
à `ZERO_CHECK`, avec zéro ronde de plateau acquise : la couverture de tous les
écrans et les deux rondes indépendantes restent à mesurer. Aucune release
n'est engagée.
