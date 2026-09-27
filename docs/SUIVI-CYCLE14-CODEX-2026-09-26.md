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

## Couverture écran et retour en réparation, 27/09/2026

La première passe passive sur la pile jetable ouvrait seulement l'onboarding :
ses 21 identifiants ne prouvaient aucun écran métier. L'onboarding a été
terminé dans la seule base `/private/tmp/therese-c14-couverture.Hd7bEl/data`.
Une passe active a alors ouvert 21 écrans dans quatre combinaisons (1440 et
800 px, clair et sombre) et consigné 141 gestes en 1440 clair. Elle a révélé
un focus perdu, un indice visuel recouvrant du texte et des lacunes dans son
propre instrument. La phase est revenue de `ZERO_CHECK` à `REPAIR` ; aucune
ronde de plateau n'a été acquise.

| Bug | Correction et contrôle |
| --- | --- |
| B-1712 | Le bouton « Ouvrir les réglages IA » reste monté, mais masqué et retiré de la navigation tant que la modale est ouverte. Après Échap, Chromium rend le focus au même bouton. Ancien code réintroduit : 1 test rouge ; restauration : 1 vert. |
| B-1713 | L'indice « Voir la suite » ne recouvre plus les textes de l'Accueil. Mesure Chromium sur la page servie : rouge avec deux collisions à 1440 et une à 800, puis vert sans collision aux deux tailles ; 1024 et 1280 sans collision également. Captures inspectées. |
| B-1714 | L'instrument refuse toute autre base que 1420/17393, contrôle par lectures authentifiées `data_dir` et `db_path` sous `/private/tmp` avant Chromium, bloque les requêtes hors pile et les écritures, puis retrouve les contrôles par rôle, rang et signature ARIA. Garde réseau neutralisée : test rouge ; restaurée : test vert. |
| B-1715 | Le filtre de statut « Envoyée », le rafraîchissement GET des tâches et les cinq cartes Actions qui ouvrent seulement leur fiche sont exercés dans leur contexte précis ; l'envoi et le lancement restent exclus. Exceptions neutralisées : test rouge ; restaurées : test vert. |
| B-1716 | La translation de l'indice introduisait 40 px de contenu rogné à 800 px sur neuf écrans. Un espacement interne garde la même position du bouton sans déborder. Chromium : neuf écrans rouges à 40 px sous sabotage, puis zéro après restauration ; Accueil sans collision à 800, 1024, 1280 et 1440 px. |
| B-1717 | Les filtres Factures persistent après réouverture. L'instrument restaure uniquement leur clé locale initiale avant de tester le bouton de création : il passe d'« introuvable » à une ouverture réelle de fenêtre. Rouge/vert en Chromium, puis sabotage rouge/vert, sans toucher aux données métier. |
| B-1718 | Une réponse asynchrone retire « Connecter ton agenda » de la checklist et décale de un le rang de sept boutons encore visibles. L'instrument les relocalise maintenant par signature accessible et occurrence visible. Test Chromium rouge avant et sous sabotage, vert restauré ; neuf tests d'instrument passent. |

Les preuves ciblées et les captures sont sous
`.app-loop/cycles/14/couverture-ecran/`. L'instrument est versionné dans
`tests/couverture/couverture-ecran.mjs` avec ses tests
`tests/couverture/couverture-ecran.test.mjs`. La passe du premier correctif a
couvert 21 écrans aux quatre combinaisons et 139 gestes. Elle n'a relevé que
quatre anomalies : le sélecteur de fichiers natif, « Aujourd'hui » déjà actif
et le défilement voulu de la grille CRM aux deux largeurs. Un lecteur neutre
a d'abord classé les deux gestes comme insuffisamment prouvés ; il a ensuite
reçu l'événement `filechooser` sans sélection de fichier, puis mesuré le retour
de l'agenda d'octobre à septembre 2026. Ces deux gestes sont des faux
positifs. Les deux débordements CRM sont dans un conteneur défilant ; les
captures aux deux largeurs ont été inspectées. Le rapport est
`.app-loop/cycles/14/couverture-ecran/actif-stable-a/rapport.json`, avec
preuve de tri dans `tri-neutre-a/preuves.json`. Cette passe précède un nouveau
durcissement de l'instrument et ne compte pas encore comme ronde de plateau.
L'instrument ne remplace pas la recette des résultats métier de P-146.

Une tentative de reprise a été interrompue quand les deux services temporaires
ont cessé d'écouter ; elle n'est pas comptée comme une ronde. L'ancienne base
jetable chiffrée a été laissée intacte après un refus de démarrage faute de
sa clé. La nouvelle pile utilise
`/private/tmp/therese-c14-reprise-9ukq24jp/data`, un `HOME` temporaire, les
ports locaux 1420/17393 et `THERESE_DB_PLAINTEXT=1` sur cette base neuve.
Son dossier et sa base ont été vérifiés par `/api/config/stats` avant de
terminer l'onboarding jetable. Au premier démarrage, le préchargement du
modèle d'embeddings a contacté Hugging Face et téléchargé des métadonnées ;
le téléchargement des poids a été interrompu à 0 %. Le moteur a ensuite été
relancé avec `HF_HUB_OFFLINE=1` et `TRANSFORMERS_OFFLINE=1` ; il a continué
sans ce modèle. Aucun fournisseur LLM payant n'a été appelé.

## Durcissement de la couverture hors ligne

La revue contradictoire de l'instrument a ouvert trois défauts confirmés :

| Bug | Défaut et correction vérifiée |
| --- | --- |
| B-1719 | Si une requête est bloquée, la passe s'interrompait avant `rapport.json` et perdait la liste des URL. Elle écrit désormais `interruption.json`, avec écran, cause et garde ; les paramètres d'URL ne sont pas conservés. Test rouge avant, vert après. |
| B-1720 | Une requête GET locale pouvait déclencher un appel fournisseur depuis le backend (OpenRouter, Gmail, Calendar ou Drive selon les comptes et clés). L'instrument exige maintenant l'attestation d'un wrapper ASGI de test avant jeton et navigateur. Ce wrapper interdit DNS et sockets Python hors loopback, retire les proxies de l'environnement et laisse l'application produit inchangée. Le précontrôle refuse l'ancien backend, puis accepte le nouveau sur la base jetable exacte. Certaines routes GET de rappel OAuth et de découverte fournisseur sont également bloquées côté navigateur. |
| B-1721 | Après le retrait asynchrone d'un bouton, son rang parmi des boutons homonymes pouvait viser le mauvais. Si le nombre de signatures identiques a changé, l'instrument signale l'ambiguïté sans cliquer. Cas à trois boutons rouge avant, vert après dans Chromium. |

Le wrapper est limité au processus Python Uvicorn unique. Un sous-processus,
une bibliothèque native contournant `socket`, une socket héritée ou un relais
local explicite ne sont pas couverts par cette seule garde. Pour cette pile,
le lancement ajoute un environnement vierge (`env -i`), aucun identifiant
fournisseur, les services externes désactivés, un `HOME` jetable et les
variables Hugging Face hors ligne. Un auto-test Python de la garde passe ;
le démarrage réel répond sur 17393 et l'attestation précède les lectures
authentifiées. Le code de ce wrapper est
`tests/couverture/backend_offline.py` et son test
`tests/couverture/test_backend_offline.py`.

## Relecture de l'instrument avant le plateau

La passe destinée à devenir la première ronde a été interrompue après les
premiers écrans : la relecture de son code a montré que sa déduplication
globale par rôle et nom pouvait ignorer un contrôle métier homonyme sur un
autre écran. Cette tentative reste sous
`.app-loop/cycles/14/couverture-ecran/zero-check-a-interrompue/` et n'est
comptée ni comme couverture complète ni comme ronde de plateau.

| Bug | Défaut et correction |
| --- | --- |
| B-1722 | L'instrument déduplique uniquement les contrôles de l'en-tête direct et du rail principal de la coque. Il exerce les contrôles métier sur chaque écran, même quand leur nom est identique. Un contrôle commun ne rejoint l'ensemble des gestes exercés qu'après un clic réussi. Le rail est identifié par sa place dans la coque ; une navigation métier homonyme reste distincte. |
| B-1723 | La relocalisation refuse un groupe de boutons homonymes sans identité explicite. Elle vérifie aussi les identifiants des boutons uniques et tous les attributs d'identité présents lors du relevé : un `data-testid` constant ne masque pas un `data-id` métier changé. Les ambiguïtés sont décrites comme telles dans le rapport. |
| B-1724 | Le nom d'un contrôle inclus dans un `<label>` englobant est relevé, même sans `id` ni `aria-label`. Une case à cocher ainsi nommée n'est plus éliminée avant l'exercice. |

Les témoins rouges avant correction, les sabotages rouges et les 20 tests
Chromium verts de l'instrument sont dans
`.app-loop/cycles/14/couverture-ecran/`. Ils ne remplacent pas la mesure
complète de l'application servie. La cartographie et les contrôles de
calibration ont ensuite été actualisés sur les empreintes finales avant les
deux rondes indépendantes.

La double lecture des deux fichiers de l'instrument sur les SHA finaux
`cf455966…1e3bd` et `811f6e03…bf48` est complète. La cartographie régénérée
valide 2 077/2 077 fichiers, sans rapport invalide, double lecture manquante
ni empreinte périmée. La calibration `screen_coverage` sur la pile servie
1420/17393 a détecté un contrôle sans nom et un contenu rogné ; la capture
avec témoin magenta a été inspectée. Une requête témoin externe a été bloquée
et consignée sans son paramètre secret. L'Accueil sain ne présente aucune
anomalie avant et après ces contrôles, et `index.html` a retrouvé son SHA
`2ef2d3c1…b3ca30`. Les preuves et leurs empreintes figurent dans
`.app-loop/cycles/14/calibration/screen-controls-cf45.json`. La calibration
est `PASS` ; aucune ronde de plateau n'est encore comptée à ce stade.

## Première ronde exploratoire servie après durcissement

La première passe complète du nouvel instrument a ouvert 21 écrans dans les
quatre combinaisons 1440/800 px et clair/sombre. Elle a exercé 208 gestes
en 1440 clair. La garde n'a relevé aucune requête bloquée, fenêtre,
téléchargement ni accès au port réel. Le rapport brut
`.app-loop/cycles/14/couverture-ecran/zero-check-a/rapport.json` porte 18
anomalies dédupliquées. Cette passe a découvert des défauts : elle ne compte
donc pas comme ronde de plateau.

| Bug | Observation sur l'application servie |
| --- | --- |
| B-1725 | Les actions « Copier le prompt » et « Utiliser » sont homonymes sur les cartes de la bibliothèque ; aucun nom accessible n'indique le titre du prompt. |
| B-1726 | L'overlay de la bibliothèque ne porte pas `role="dialog"` et `aria-modal="true"`. Le parcours tente neuf boutons de l'Accueil derrière lui et obtient neuf clics impossibles. |
| B-1727 | Dans Projets et Documents, le bouton d'en-tête et celui de l'état vide ont le même nom sans identité DOM distincte. Quatre gestes sont refusés par la relocalisation sûre. |
| B-1728 | À 1440 px, le panneau Actions fixé à droite couvre notamment « Ouvrir Agenda » et « Message vocal » ; ces boutons restent dans la zone que le moteur croit côte à côte et les deux clics échouent. |

Les deux signalements de défilement horizontal du CRM et le clic sur
« Aujourd'hui » déjà actif dans l'Agenda reproduisent des faux positifs
préalablement prouvés dans `tri-neutre-a/preuves.json`. Les corrections
applicatives B-1725 à B-1728 doivent être vérifiées sur la page servie avant
de recommencer la ronde A.

## Vérification des corrections B-1725 à B-1728

La vérification ciblée sur la pile locale jetable a parcouru les quatre écrans
concernés dans les quatre combinaisons 1440/800 px et clair/sombre. Le rapport
`retest-b1725-b1728/rapport.json` contient zéro anomalie, 60 gestes sûrs en
1440 clair, aucune sortie bloquée par la garde et l'attestation du répertoire
de données jetables. Les captures à 1440 et 800 px ont été inspectées : la
bibliothèque reste dans un dialogue centré, les créations Projets/Documents
sont accessibles par leurs deux boutons, et Actions occupe sa propre colonne
à 1440 px tout en devenant un panneau couvrant à 800 px. Les quatre bugs sont
marqués `fixed`, avec sabotage rouge et contrôle vert associés dans
`.app-loop/bugs.json`.

La calibration du parcours écran a été rejouée après ces corrections. Le
contrôle négatif et la restauration sont propres ; les témoins visuels
produisent `contenu-rogne` et `nom-accessible-vide`, et la requête réseau
témoin est bloquée avec son paramètre masqué. Le manifeste
`screen-controls-cf45.json` atteste aussi le retour de `index.html` à son
SHA-256 initial et l'absence du verrou temporaire. La cartographie actualisée
valide 2080 fichiers sur 2080 ; les dix fichiers du dernier lot ont deux
lectures indépendantes. Une divergence de formulation sur
`DocumentsList.test.tsx` a été arbitrée `concordant` après lecture des deux
gestes du test. La couverture complète A2 puis la contre-épreuve indépendante
B restent nécessaires avant de compter une ronde de plateau.

## Ronde complète A2 sur la pile jetable

Le rapport `zero-check-a2/rapport.json` couvre 21 écrans dans quatre
combinaisons de largeur et de thème, avec 197 gestes sûrs réellement exercés
en 1440 clair. La garde réseau est vide et atteste le répertoire de données
jetables. Il contient trois signalements uniques, tous arbitrés dans
`tri-anomalies-a2-final.json` : les deux largeurs de la grille CRM et le
bouton « Aujourd'hui » sur le mois déjà courant. Une sonde Chromium
indépendante prouve que la colonne « Archive » devient visible au clavier
après des flèches espacées, à 1440 comme à 800 px ; le premier essai,
envoyé pendant le défilement animé, est conservé comme non concluant.
Le témoin de l'Agenda prouve le retour depuis le mois suivant. Entrée et
Espace déplient et replient aussi un prompt à ces deux largeurs.

L'audit `visuel-a2.json` inspecte les captures des panneaux, dialogues et du
CRM au début puis à la fin du défilement. `journaux-a2.json` relève zéro
erreur console ou réseau sur les 84 vues et zéro ligne d'erreur du backend
jetable dans l'intervalle de la ronde. Le frontend complet passe 3343 tests
sur 3343 ; la compilation passe et le lint termine avec zéro erreur
(26 avertissements). Le premier JUnit à 3343 tests avait révélé
un sélecteur trop large dans l'ancien test clavier B-823 après le nouveau
nommage accessible B-1725 : le test a été précisé puis toute la suite a été
relancée. La cartographie finale valide à nouveau 2080 fichiers sur 2080.
La ronde B indépendante et le calcul du plateau restent à effectuer.

## Plateau calculé

La ronde B, menée séparément par `/root/plateau_prep`, a retrouvé les mêmes
trois identifiants de signalement, sans nouvelle anomalie, sur 21 écrans dans
quatre combinaisons. Elle a exercé 197 gestes sûrs en 1440 clair ; sa garde
est vide. Le tri B comprend un témoin Agenda distinct, et les pièces
`visuel-b.json` et `journaux-b.json` documentent les captures et l'absence
d'erreurs inexpliquées. Le manifeste `transitions-final-87.json` vérifie
87 transitions critiques sur 87, en s'appuyant sur les preuves de tests et de
navigateur associées.

`app_loop.py plateau-evaluate` a accepté successivement
`plateau-round-a2.json` et `plateau-round-b.json` : deux rondes indépendantes
propres sur deux. Le cycle 14 est passé de `ZERO_CHECK` à `GAP_SCAN` pour
examiner les améliorations éventuelles. Le verdict porte sur le périmètre
couvert et les instruments calibrés ; il ne prouve ni la recette fonctionnelle
P-146 dans l'application Tauri packagée, ni une release.

## Retour du scan et remise à zéro du plateau

Le scan a révélé sept défauts confirmés après les deux rondes propres. Le
compteur du plateau a donc été remis à zéro et la phase est revenue à
`REPRODUCE`, puis `REPAIR`. Chaque correction ci-dessous possède un témoin
rouge, un contrôle vert et un sabotage rouge dans
`.app-loop/cycles/14/gap-scan/` ou
`.app-loop/cycles/14/repair-activity-timeline/`.

| Bug | Défaut corrigé |
| --- | --- |
| B-1729 | Une panne de lecture du fil d'activités CRM affichait « Aucune activité ». L'écran distingue maintenant l'échec, annonce une alerte et permet de réessayer. |
| B-1730 | La copie réussie d'un prompt ne changeait que la coche visuelle. Un statut accessible annonce maintenant le succès et nomme le prompt. |
| B-1731 | Dans le tiroir de conversations réellement monté, une alerte d'export restait visible après un nouvel export réussi. Le succès l'efface. Le composant `ConversationSidebar` contenant un autre problème d'export n'est pas monté dans l'application actuelle ; son test exploratoire a été placé dans la Corbeille. |
| B-1732 | Le nom accessible des cartes Actions fusionnait titre, description et badges. Il annonce maintenant l'ouverture de la fiche ; la description reste disponible séparément. |
| B-1733 | Le contrôle écran sautait la fiche sûre « Rapport hebdomadaire », car sa description contient « Génère ». Les six fiches connues sont identifiées strictement avant le filtre des gestes sortants. |
| B-1734 | Une première correction de ce filtre excluait aussi toute fiche homonyme du CRM. L'exception et son refus de sécurité sont maintenant bornés à l'écran Actions. |
| B-1735 | En navigateur, Fichiers affichait simultanément l'indisponibilité de l'accès natif, « Dossier vide », « 0 élément » et un filtre actif. La vue web ne prétend plus avoir lu un dossier ; le mode natif conserve sa liste et son compteur. |

Les tests frontend complets passent **3347/3347** après B-1735. Le build passe ;
le lint finit avec zéro erreur et 26 avertissements. Le code backend n'a pas
changé depuis sa suite complète à 4176 tests réussis et cinq ignorés. Le
contrôle ciblé de l'application servie ouvre Conversations, Prompts, CRM et
Actions dans quatre combinaisons : 72 gestes sûrs à 1440 clair, six fiches
Actions effectivement ouvertes, aucune sortie réseau. Ses deux signalements
uniques concernent les largeurs de la grille CRM déjà arbitrées. La vue
Fichiers corrigée est vérifiée séparément à 1440/800 px en clair/sombre :
16 gestes sûrs, zéro anomalie, garde réseau vide ; la capture à 800 sombre a
été inspectée.

La cartographie après ces changements valide **2080/2080** fichiers, avec
deux lectures indépendantes des 13 fichiers applicatifs et de test modifiés
au scan. Les témoins Chromium de l'interface, des captures et du réseau
repassent sur la pile jetable. La recalibration `screen_coverage` détecte
les témoins visuels et la requête sortante bloquée. Son premier passage sain
après restauration signale « Conversations » introuvable pendant la
réouverture ; un second passage sans modification ne reproduit pas l'anomalie.
Les deux rapports sont conservés dans
`.app-loop/cycles/14/calibration/screen-controls-b1735.json`. `index.html`
est restauré à son SHA exact et le verrou temporaire est absent. Deux
nouvelles rondes indépendantes restent à calculer avant de déclarer un
nouveau plateau.

## Nouveau plateau et portail de décision

Les rondes indépendantes A3 (`/root`) et B2 (`/root/plateau_prep`) ont chacune
parcouru 21 écrans dans quatre combinaisons de largeur et de thème, avec
197 gestes sûrs exercés, dont les six fiches Actions. Leurs rapports ne
remontent que les trois mêmes signalements : deux largeurs du Pipeline et
« Aujourd'hui » déjà sur le mois courant. La navigation clavier du Pipeline
et le retour au mois courant ont été vérifiés à nouveau dans B2. Les gardes
réseau et les journaux des deux périodes sont vides ; des captures ont été
inspectées dans chaque ronde. Les gestes destructifs ou sortants ne font pas
partie de ces essais.

Le manifeste `transitions-final-94.json` couvre 94 transitions critiques sur
94 : 70 références historiques contrôlées, 17 transitions déjà qualifiées et
sept issues des corrections B-1729 à B-1735. Les 301 références de preuve
internes sont présentes avec leur empreinte attendue. La suite frontend
actuelle passe 3347 tests sur 3347, les témoins Chromium de l'instrument
20 sur 20, et la cartographie de référence couvre 2080 fichiers sur 2080.
Le backend n'a pas été modifié depuis ses 4176 tests réussis, cinq ignorés,
et les 15 contrôles de confinement complémentaires.

Le premier calcul A3 a été refusé car son manifeste reprenait le SHA Git de
l'ancien inventaire A2. La référence a été corrigée et le calcul relancé
avec un nouvel identifiant ; `plateau-evaluate` a alors accepté A3 puis B2,
soit **deux rondes propres indépendantes sur deux**. L'état est passé de
`ZERO_CHECK` à `GAP_SCAN`, puis à `HUMAN_GATE` après déduplication des
propositions. Ce verdict signifie « aucun bug détectable dans le périmètre
couvert avec les instruments calibrés ». Il ne vaut ni recette de
l'application Tauri packagée, ni publication.

Trois propositions restent à décider, sans implémentation à ce stade :

| ID | Proposition | Constat et périmètre |
| --- | --- | --- |
| P-157 | Signaler visuellement le défilement horizontal du Pipeline | À 800 px, les colonnes suivantes restent hors champ sans indice visuel. Le défilement au clavier et au pointeur fonctionne ; P-071 a accepté la fusion Contacts/Pipeline, sans cette indication. |
| P-158 | Rendre réglable la largeur du tiroir Conversations | Le tiroir a une largeur fixe de 22rem et tronque les titres. P-068 et P-092 portent sur d'autres changements de structure. |
| P-159 | Afficher le contexte réellement transmis au modèle | Le chat lit au plus 50 messages passés, en exclut certains, ajoute le message courant et peut ensuite réduire le contexte selon le budget du modèle. `max_history_messages` est stocké mais n'agit pas sur ce parcours ; un réglage éventuel reste une décision distincte. |

`next-action` répond `portail` en phase `HUMAN_GATE` : attendre `oui`, `non`
ou `plus tard` pour chaque proposition. Aucun build Tauri ni release n'a été
effectué dans cette reprise ; l'instance réelle et le port 17293 n'ont pas
été sollicités.
