# LOT80 : deux pistes issues de la lecture ciblée

Auteur : `/root/shared4_execution`. Statut : analyse de code en lecture seule, sans reproduction, test exécuté ou correctif. Ce rapport est une piste à revalider au prochain HEAD, pas une admission.

Dépôt observé : `/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE-c15-codex`. HEAD observé : `3dd046bf3cfa582d3c4a86958544ebe72da1df19`. Les empreintes ci-dessous ont été recontrôlées physiquement. Les deux entrées du registre restent `deferred` lors de leur relecture ciblée ; le registre entier n'est pas déclaré inchangé entre lectures.

## B-1612 : décoration incomplète du catalogue dynamique

Constat source : `src/frontend/src/lib/catalogueModeles.ts:26–51` ne décore que GLM, Kimi, Qwen et MiniMax. `decorer`, lignes 55–56, retourne donc le seul identifiant comme nom pour les autres modèles. `chargerCatalogue`, lignes 64–76, utilise ce résultat même quand la réponse réussit. Le repli statique de la ligne 140 contient pourtant `claude-opus-5-5` avec le nom `Claude Opus 5.5` et le badge `Recommandé`.

Raccord visible vérifié : `src/frontend/src/components/settings/LLMTab.tsx:146–155` installe le catalogue dynamique ; lignes 187–189, celui-ci remplace le repli ; lignes 538–540, le sélecteur affiche son nom/badge. Une réponse synthétique contenant cet identifiant ferait donc perdre ces décorations dans Réglages. Le titre historique B-1612 vise l'Atelier ; sa surface actuelle exacte n'est pas qualifiée par ce rapport. Entrée connue : `.app-loop/bugs.json:35494`.

Régression proposée, NON EXÉCUTÉE : tester les vrais `chargerCatalogue`/`decorer` avec un fetcher injecté retournant `['claude-opus-5-5', 'modele-fictif-inconnu']`, sans réseau et avec cache isolé. Exiger identifiants inchangés, nom/badge du premier conformes au repli existant, second identifiant conservé tel quel. Les tests lus `catalogueModeles.test.ts:19–28,53–58` couvrent GLM/MiniMax ; `catalogueModeles.p122.test.ts` vérifie les listes statiques, pas cette jonction dynamique. Une correction future pourrait partager les décorations existantes, sans changer disponibilités, recommandations ou fournisseurs. Rien n'a été corrigé ici.

## B-1678 : filtre des projets distinct du texte masqué affiché

Constat source : `src/frontend/src/components/memory/ProjectsPanel.tsx:58–64` filtre les noms, descriptions et tags bruts. Le panneau possède déjà `maskText` à la ligne 48 et transmet la sélection au kanban, lignes 254–255. `ProjectsKanban.tsx:331–332,360,368,374` affiche en revanche ces trois champs masqués. Entrée connue : `.app-loop/bugs.json:36789`.

Scénario synthétique proposé, NON EXÉCUTÉ : projet brut `OriginalUnique`, remplacement démo `OriginalUnique → Projet Azur`. La carte afficherait `Projet Azur`, mais chercher `Azur` serait exclu par le filtre brut ; chercher `OriginalUnique` resterait inclus. Ce n'est pas une fuite de données reproduite ni une observation de l'UI réelle.

Régression isolée envisagée : mocker uniquement la liste des projets, employer le hook/store démo réel sur un stockage jsdom jetable, vérifier recherche du texte affiché, témoin mode démo désactivé, puis changement de mode/map sans changement de projets ni de filtre. `useDemoMask.ts:67–73` fait varier `maskText` avec mode/map ; une éventuelle correction du mémo devrait donc inclure cette dépendance, tout en préservant le repli accents/casse. `ProjectsPanel.tagsEtFiltre.p123.test.tsx:44–58` couvre la recherche normale ; `ProjectsPanel.demo.c10.test.tsx` couvre surtout la garde de suppression, pas ce filtrage. Aucun test ajouté ni exécuté.

## Empreintes des sources lues

Les chemins de cette table sont relatifs au dépôt absolu déclaré plus haut.

| Fichier | SHA256 |
| --- | --- |
| `src/frontend/src/lib/catalogueModeles.ts` | `524dc034bd93a44a38d9bda3f84f387f6e31d83123285f9193ac5cdc92bc040f` |
| `src/frontend/src/components/settings/LLMTab.tsx` | `a7a3b99c848f1610f4b40276594a6780846b3cc72741a574dc1d06d4db286405` |
| `src/frontend/src/components/memory/ProjectsPanel.tsx` | `752feff13b5ab35499943fd0260ca8e9bf1480bb8112819ddcfec464ea641e09` |
| `src/frontend/src/components/memory/ProjectsKanban.tsx` | `4e59ebdd9a8a1c04013a7f6cc5bc46123c34b3a9825d637d2f7d80b83b69e073` |
| `src/frontend/src/hooks/useDemoMask.ts` | `8b9b956242a95f3caf6bee323b73f58cf74b25bb486062b7d0f080ff2b53dc4c` |
| `src/frontend/src/lib/catalogueModeles.test.ts` | `526034c5fe234540bb4a8fedd58322b7c5f9816b65d7f96ef386a370a4b2c025` |
| `src/frontend/src/lib/catalogueModeles.p122.test.ts` | `bbb6980ca3063ea497e7df8195a98eab120bc8f3de87266fb8b0923289480a7a` |
| `src/frontend/src/components/memory/ProjectsPanel.tagsEtFiltre.p123.test.tsx` | `8a8a357c3c01b394af7cc5a287dfbaaa231e0e3b73676df60aede50d8c667ff7` |
| `src/frontend/src/components/memory/ProjectsPanel.demo.c10.test.tsx` | `666296a23fa66fed94ab8e36130c8e06cf81281aba4d027473a309ffedf74aa0` |
| `.app-loop/bugs.json` | `5b8abd82dd271d084cf7115faa8035fa60f7c02d408d2df11b5553e1312b6c3b` |

## Limites et reprise

Aucun import produit/G1, test, API fournisseur, DB, serveur, navigateur ou calibration n'a été exécuté. Aucune disponibilité actuelle des modèles n'est attestée. Aucun fichier du dépôt, état ou document utilisateur préexistant n'a été modifié par cette lecture. Les choix démo réservés B-1694/B-1698/B-1701/B-1702/B-1708 ne sont pas arbitrés ici.

Ce document ne porte pas sur le correctif B-1684 piloté par MAIN. Le lot courant n'est pas étendu à ces deux pistes. Toutes les portes A/B/FULL restent fermées ; ce rapport ne compte aucune ronde ni qualification native. Avant une reprise : recontrôler HEAD, sources et statuts, puis faire approuver l'isolation de chaque régression proposée.
