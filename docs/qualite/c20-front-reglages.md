# Cycle 20 : lot front-reglages

Le bilan initial ci-dessous décrit le travail sur `gpt/c20-front-reglages`, base `12a383fb`, issue de l’intégration v0.83.0-alpha, avant les commits de l’orchestrateur. Pendant cette intervention initiale, aucun commit, ajout à l’index, push, dépôt annexe ou bundle n’a été effectué. Le commit historique `41a438a8` a uniquement été lu, puis son correctif de SettingsModal reporté dans cet arbre ; aucune branche main n’a été modifiée. L’état vérifié lors de la reprise figure dans « Remédiation de la relecture, passe 1 ».

Les candidats ont été traités dans l’ordre demandé. Pour chacun des 14 confirmés, le test de comportement a été écrit et exécuté avant la correction, puis vérifié au vert. Les appels API, IPC et mises à jour sont doublés ; aucun fournisseur ni service en ligne n’a été appelé. Aucun backend n’a été démarré et aucun port applicatif réservé ni dossier de données personnel n’a été utilisé.

## Verdicts et preuves rouges

Les chemins de test sont relatifs au dépôt. La colonne rouge remplace le hash de commit, conformément à la particularité du bac à sable. Les fichiers contenant plusieurs candidats se rejouent séparément avec `-t B-xxxx`. Les lignes d’erreur ci-dessous proviennent des sorties réelles, sans reformulation. Pour les assertions de texte, les valeurs reçues étaient respectivement « Connexion refusée. Démarrez Ollama pour utiliser des modèles locaux. » (B-1959), « Aperçu THERESE.md » (B-1961), « Supprimer ce connecteur ? » (B-1964) et « Mise à jour v0.83.1 prêteRedémarrer pour installer » (B-1966).

| Id | Verdict | Test (chemin::nom) | Rouge observé, sans commit | Correctif |
| --- | --- | --- | --- | --- |
| B-1805 | `confirme` | `src/frontend/src/components/settings/SettingsModal.dernierChoix.b1805.test.tsx::B-1805 : une ancienne lecture lente ne remplace pas le dernier modèle choisi` | `AssertionError: expected last "vi.fn()" call to have been called with [ 'mistral', …(2) ]` | non commité |
| B-1846 | `regle_a_trancher` | Repère existant : `src/frontend/src/components/settings/SettingsModal.da.test.tsx::un refus de clé suivi d’un passage sur Ollama sans modèle reste annoncé` | Aucun rouge revendiqué : règle d’activation sans modèle absente | Aucun changement pour ce candidat |
| B-1847 | `confirme` | `src/frontend/src/services/api/core.reprisePort.b1847.test.ts::réessaie après un premier port indisponible` | `AssertionError: expected 'http://127.0.0.1:17293' to be 'http://127.0.0.1:29147' // Object.is equality` | non commité |
| B-1848 | `confirme` | `src/frontend/src/stores/documentStore.ouvertureAnnulee.b1848.test.ts::une fermeture empêche une lecture tardive de rouvrir le document` | `AssertionError: expected { id: 'a', title: 'a', …(10) } to be null` | non commité |
| B-1849 | `confirme` | `src/frontend/src/stores/documentStore.chargementFerme.b1849.test.ts::ne reste pas occupé après la fermeture et une réussite tardive` | `AssertionError: expected true to be false // Object.is equality` | non commité |
| B-1959 | `confirme` | `src/frontend/src/components/settings/LLMTab.textesFrancais.c20.test.tsx::B-1959 : le statut indisponible tutoie et garde le motif` | `Error: expect(element).toHaveTextContent()` | non commité |
| B-1960 | `confirme` | `src/frontend/src/components/settings/LLMTab.textesFrancais.c20.test.tsx::B-1960 : le bouton français ouvre la saisie du modèle personnalisé` | `TestingLibraryElementError: Unable to find an accessible element with the role "button" and name "Modèle personnalisé"` | non commité |
| B-1961 | `confirme` | `src/frontend/src/components/settings/ProfileTab.edition.b1961.test.tsx::B-1961 : le dialogue annonce la modification et sauvegarde le texte saisi` | `Error: expect(element).toHaveAccessibleName()` | non commité |
| B-1962 | `confirme` | `src/frontend/src/components/settings/ToolsPanel.textesFrancais.c20.test.tsx::B-1962 : les décomptes de 0 outils sont en français` | `TestingLibraryElementError: Unable to find an element with the text: /0 outils disponible/. This could be because the text is broken up by multiple elements. In this case, you can provide a function for your text matcher to make your matcher more flexible.` | non commité |
| B-1963 | `confirme` | `src/frontend/src/components/settings/ToolsPanel.textesFrancais.c20.test.tsx::B-1963 : un échec de uvx sans motif ne suppose pas Node.js absent` | `AssertionError: expected "vi.fn()" to be called with arguments: [ Array(1) ]` | non commité |
| B-1964 | `confirme` | `src/frontend/src/components/settings/ToolsPanel.textesFrancais.c20.test.tsx::B-1964 : la confirmation nomme le connecteur choisi parmi plusieurs` | `Error: expect(element).toHaveTextContent()` | non commité |
| B-1965 | `confirme` | `src/frontend/src/components/settings/ToolsPanel.textesFrancais.c20.test.tsx::B-1965 : le connecteur stopped porte un état inactif accessible` | `TestingLibraryElementError: Unable to find an accessible element with the role "img" and name "Installé mais inactif : à démarrer depuis les connecteurs"` | non commité |
| B-1966 | `confirme` | `src/frontend/src/components/ui/UpdateBanner.etatInstalle.b1966.test.tsx::B-1966 : après installation le bandeau annonce installé et propose de l’appliquer` | `Error: expect(element).toHaveTextContent()` | non commité |
| B-1967 | `confirme` | `src/frontend/src/services/api/crm-extended.erreursFrancaises.b1967.test.ts::B-1967 : erreur de connexion > le repli est en français avec le statut HTTP, corps {}` | `AssertionError: expected [Function] to throw error including 'La connexion au CRM n’a pas pu démarr…' but got 'Failed to initiate OAuth: Service Una…'` | non commité |
| B-1968 | `confirme` | `src/frontend/src/services/api/rgpd.erreursFrancaises.b1968.test.ts::B-1968 : erreur RGPD, export > le repli est français avec le statut HTTP, corps {}` | `AssertionError: expected [Function] to throw error including 'L’export des données personnelles a é…' but got 'RGPD export failed: Service Unavailab…'` | non commité |
| B-1969 | `rejete` | `tests/test_f1_coherence_des_couches.py:306` est un docstring ; rendu courant : `src/backend/app/services/invoice_pdf.py:649` | Aucun défaut d’interface démontré : le PDF écrit « TVA à {taux} % » ; la table de libellés à la ligne 48 comporte déjà « TVA réduite 5,5% » | Aucun changement |

## B-1846 : règle à trancher

Question : sélectionner Ollama joignable mais sans modèle doit-il **activer Ollama malgré l’absence de modèle**, ou seulement permettre d’inspecter le service en conservant le fournisseur opérationnel ?

Le test existant `SettingsModal.da.test.tsx:377-406` exige déjà que la carte Ollama soit sélectionnée dans ce cas, mais ne définit pas le fournisseur à enregistrer. `SettingsModal.tsx:613` ne sauvegarde qu’un modèle non vide. `LLMTab.tsx:700-701,756` empêche de régler l’effort sans modèle, et `LLMTab.ollamaCloud.b1160.test.tsx::changer l’effort sans modèle Ollama n’envoie pas un modèle vide` protège ce contrat. Le schéma backend accepte une chaîne de modèle, mais n’exprime aucune règle produit sur l’activation d’un fournisseur vide. Ces éléments ne suffisent pas à choisir entre les deux comportements. Le modèle précédent conservé et le décalage affichage/enregistrement restent donc un risque non résolu, sans être présentés comme une reproduction rouge.

Options :

1. Refuser l’activation sans modèle, garder explicitement le service réellement actif, afficher « Installe un modèle Ollama avant de l’activer » et permettre la consultation du statut local séparément. **Recommandation** : cette option préserve une configuration utilisable et ne présente pas Ollama comme actif à tort.
2. Enregistrer Ollama avec un modèle vide, vider le modèle affiché et bloquer clairement conversation et effort jusqu’au choix d’un modèle installé. Il faut définir le contrat backend et le comportement au redémarrage pour cet état incomplet.

Aucun changement pour B-1846. Le même fichier reçoit uniquement le report de B-1805.

## Chemins de production vérifiés avant correction

- B-1805 : `App` → `PanelContainer.tsx:24-25,148` → `SettingsModal` → `LLMTab`, via `onSelectProvider` et `onSelectModel`. Le correctif ordonne les sauvegardes, ignore les lectures dépassées et restaure la dernière configuration enregistrée après refus. Six scénarios nouveaux, dont trois initialement rouges ; les trois tests B-225 restent verts.
- B-1847 : `SplashScreen.tsx:193` appelle `initApiBase`. Seul le repli sans port résolu libère la promesse ; les appels concurrents partagent toujours une tentative et un port résolu reste mémorisé. Le paramètre URL valide reste prioritaire, conformément au contrat existant.
- B-1848 et B-1849 : `DocumentsList.tsx` ouvre les documents ; `DocumentWorkspace.tsx` appelle la fermeture et suit la génération. La fermeture invalide les lectures et libère `isLoading`, sans annuler la génération détachée ni libérer à tort le chargement de la suivante. La suppression est couverte uniquement au niveau du store : les tests vérifient l’invalidation après confirmation et le maintien du document après refus. Aucun appel de `deleteDocument` depuis un composant n’a été trouvé ; ces tests ne prouvent donc pas un parcours de suppression dans l’interface.
- B-1959 à B-1965 : `SettingsModal` monte `LLMTab`, `ProfileTab` et `ToolsPanel`. Les tests rendent ces vrais composants et utilisent leurs contrôles. Le statut inactif possède un rôle et un nom accessibles. La suppression annonce le nom de la cible et transmet toujours son identifiant exact après confirmation.
- B-1966 : `App.tsx:276` monte `UpdateBanner`. Le plugin local expose `downloadAndInstall` comme une promesse d’installation et ses événements comme `DownloadEvent`. Le bouton de redémarrage attend désormais la résolution de cette promesse, puis dit « Redémarrer pour appliquer » ; l’événement `Finished` seul ne suffit plus. Aucune mise à jour réelle n’a été lancée.
- B-1967 : `CRMSyncPanel.tsx:125,249` utilise le client CRM. Les trois replis sont français, conservent le code HTTP et acceptent une réponse d’erreur non JSON. Les détails fournis par le moteur sont conservés. Le retour OAuth est testé au niveau du client exporté, sans prétendre ouvrir une connexion réelle.
- B-1968 : `MemoryPanel.tsx:294,310,335,350` et `PrivacyTab.tsx:212,231` utilisent le client RGPD. Les neuf opérations de ce client reçoivent des replis français et préservent le détail du moteur ; les tests couvrent JSON vide, erreur non JSON et détail fourni.
- B-1969 : le passage sans accent cité est un commentaire de test, pas une étiquette exécutée. Le rendu de production utilise actuellement « TVA à {taux} % » (`invoice_pdf.py:649`) ; la table historique de libellés est elle aussi accentuée (`invoice_pdf.py:48`). Aucun test de recherche de texte n’a été ajouté pour fabriquer un rouge sur un docstring.

## Tests existants adaptés sans affaiblissement

- `LLMTab.da.test.tsx:414` attendait exactement « Démarrez Ollama ». L’assertion exacte attend désormais « Démarre Ollama », pour B-1959 ; le contrôle du motif et du statut reste en place.
- `MemoryProfileBranch.r5.test.tsx:26` recherchait exactement le dialogue « Aperçu THERESE.md ». Il recherche désormais « Modifier THERESE.md », pour B-1961 ; fermeture et retour au profil restent vérifiés.
- `src/test/c19d/B-1074.test.ts:5` verrouillait aussi le nom exact « Fermer l’aperçu THERESE.md ». La même assertion stricte porte désormais sur « Fermer l’éditeur THERESE.md ». Le nouveau test B-1961 vérifie également le clic de fermeture réel et la disparition du dialogue.

Ces changements de libellé sont à mentionner dans les futurs commits. Leur dernière ligne devra être `Co-Authored-By: Codex <noreply@openai.com>`. Ces trois fichiers sont les seuls tests existants modifiés.

## Contrôles par candidat

| Candidat | Échecs observés avant correction | Nouveaux cas verts après correction |
| --- | ---: | ---: |
| B-1805 | 3 | 6 |
| B-1847 | 2 | 3 |
| B-1848 | 4 | 6 |
| B-1849 | 2 | 3 |
| B-1959 | 1 | 1 |
| B-1960 | 1 | 1 |
| B-1961 | 1 | 1 |
| B-1962 | 3 | 3 |
| B-1963 | 3 | 4 |
| B-1964 | 1 | 1 |
| B-1965 | 2 | 3 |
| B-1966 | 2 | 2 |
| B-1967 | 6 | 9 |
| B-1968 | 18 | 27 |
| Total | 49 | 70 |

Sorties individuelles : `/tmp/front-reglages-bXXXX-rouge.log` et `/tmp/front-reglages-bXXXX-vert.log`. Les vérifications vertes incluent parfois les tests voisins ; les comptes ci-dessus portent uniquement sur les nouveaux cas du candidat. B-1846 et B-1969 n’ont aucun test ajouté.

## Portes finales

**Porte frontend finale : 4 169 passés, 0 échoué, 0 ignoré, 973 fichiers passés sur 973, sortie 0.** Rapport `/tmp/front-reglages-vitest-final.json` lu : tous les résultats individuels sont `passed`, dont les 70 nouveaux cas. Aucun nom d’échec final.

Première passe complète (rapport JSON lu) : **4 166 passés, 3 échoués, 0 ignoré**, dans **973 fichiers** (970 passés, 3 échoués). Les échecs étaient :

1. `src/components/prototype/CapabilityCenter.da.test.tsx::Lot 3 DA : typeCapacite > classe prompts, les 7 parcours et les vues ; un clic onChoose reste inchangé` : délai de 5 000 ms dépassé.
2. `src/components/prototype/ConversationCanvasPrototype.projetMene.p148.test.tsx::P-148 : mener depuis la fenêtre ouverte par la vue Projets > une conversation s’ouvre, la fenêtre se ferme, le focus est dans le champ du message` : délai de 5 000 ms dépassé.
3. `src/test/c19d/B-1074.test.ts::B-1074 : contrat du libellé ou de la structure` : ancien nom de fermeture codifié. Assertion adaptée ci-dessus, sans relâcher le contrôle.

Rejeu des deux fichiers affectés par les délais avec `--maxWorkers=1` : **20 passés, 0 échoué, 0 ignoré**, sans changer les délais ni les assertions (`/tmp/front-reglages-rejeu-delais.json`, lu). Rejeu de B-1074 et B-1961 : **2 passés, 0 échoué**.

La seconde passe complète, verte, utilise `--maxWorkers=2`, les mêmes délais et les mêmes assertions. Les deux fichiers qui avaient dépassé le délai sont verts dans cette passe complète, et pas uniquement dans leur rejeu ciblé.

- Commande frontend standard `cd src/frontend && npm run test -- --run` : sortie 1 avant collecte, 0 test exécuté. Vite tente d’écrire dans `node_modules/.vite-temp`, lien en lecture seule vers le dépôt principal, et reçoit `EPERM`.
- Commande équivalente dans le bac à sable : `npm run test -- --run --no-cache --configLoader runner --maxWorkers=2 --reporter=default --reporter=json --outputFile.json=/tmp/front-reglages-vitest-final.json`. Le chargement direct et l’absence de cache évitent les écritures dans le lien partagé ; même configuration de tests, mêmes assertions, aucun délai maximal augmenté. La première passe utilisait la concurrence par défaut et écrivait `/tmp/front-reglages-vitest.json`.
- TypeScript : `npx --no-install tsc --noEmit`, sortie 0, 0 erreur. La première passe avait identifié deux types de doublures incomplets, corrigés avant ce contrôle final. Dernière passe : `/tmp/front-reglages-tsc-final.log`, vide car aucun diagnostic.
- ESLint : `npm run lint`, sortie 0, 0 erreur, 27 avertissements. Dernière passe : `/tmp/front-reglages-lint-final.log`.
- Ruff : `.venv/bin/python -m ruff check --no-fix src/backend tests`, sortie 0, 0 erreur.
- Pytest backend : non requis et non exécuté, aucun fichier backend ni test Python modifié. Aucun résultat backend, ni aucun XML pytest, n’est revendiqué.
- `git diff --check` : sortie 0. Contrôle du périmètre : 12 fichiers suivis modifiés et 11 nouveaux, tous sous `src/frontend/` ou le présent rapport ; branche et HEAD inchangés, index vide.

## Limites et transmission

L’aperçu graphique via Chromium a été tenté mais son lancement est refusé dans le bac à sable : `bootstrap_check_in … Permission denied (1100)`, puis sortie `SIGTRAP` (journal `/tmp/front-reglages-apercu-erreur.log`). Les textes, rôles et noms accessibles sont vérifiés sur le DOM des vrais composants ; aucune validation visuelle native ni recette réelle de Tauri n’est revendiquée. La palette et les styles ne sont pas modifiés.

L’intégration dans main et les commits appartiennent à l’orchestrateur. Les tests nouveaux sont séparés par candidat ou portent un nom `B-xxxx` utilisable avec `-t`, afin de rejouer les rouges sur la base avant les correctifs. Les anciens tests modifiés pour les seuls libellés doivent accompagner les correctifs correspondants. Aucun changement du registre ni de `.app-loop/`.

Pour les prochains lots, la séquence répétée de lancement ciblé, capture du rouge et lecture des rapports se prête à un petit script commun de contrôle ; sa création sort de ce lot.

## Remédiation de la relecture, passe 1

Reprise du 16 novembre 2026, limitée aux dix constats transmis. **Verdict : NO-GO, uniquement pour le constat 7 encore ouvert.** Les constats 1 à 6, 8 et 9 sont corrigés et testés ; le constat 10 est corrigé dans le bilan. Les résultats de la section « Portes finales » ci-dessus appartiennent à la livraison initiale ; les résultats de cette passe sont ceux donnés ci-dessous.

### État Git et périmètre

L’arbre était propre à l’entrée, mais il n’était pas rebasé : `HEAD=9edd2b88`, `c20/integration=e82f038a`. Le contrôle `git -c core.fsmonitor=false merge-base --is-ancestor c20/integration HEAD` retourne **1**, au début comme à la fin. Le répertoire Git réel indiqué par `git rev-parse --git-dir` est `/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/.git/worktrees/gpt-c20-front-reglages`, hors de cet arbre et hors des racines autorisées en écriture. Le rebase relève donc de l’orchestrateur. Aucun essai d’écriture dans ces métadonnées, aucun rebase, commit, ajout à l’index, push, dépôt annexe ni bundle n’a été effectué.

Les six tests cités dans le constat 7 restent absents de `HEAD` et présents dans l’intégration : `tests/test_b1824_comptage_generation.py`, `tests/test_b1825_mcp_echec_initialisation.py`, `tests/test_b1903_voix_locale_absente.py`, `tests/test_b1904_board_recherche_coupee.py`, `src/frontend/src/components/board/BoardPanel.rechercheCoupee.test.tsx` et `src/frontend/src/components/prototype/BoardRechercheCoupee.test.tsx`. Les écarts Board, voix et MCP n’ont pas été recopiés dans le diff de remédiation. Après rebase, l’orchestrateur devra rejouer les contrôles sur la base intégrée.

Cette passe modifie six fichiers de production frontend, étend cinq fichiers de tests, ajoute deux fichiers de tests et met à jour ce bilan, soit quatorze fichiers. Aucun backend ni test Python n’est modifié. Aucun test existant n’a été supprimé, assoupli ou rendu facultatif. Toutes les modifications de cette passe restent non commitées ; HEAD et index sont inchangés.

### Constats, corrections et preuves rouges

Les chemins frontend sont relatifs à `src/frontend/src`. Les tests nouveaux portent les préfixes `R1-n :` ; pour les isoler, donner le fichier indiqué et `-t 'R1-n :'`. Les lignes d’échec ci-dessous sont copiées des sorties réelles, y compris leurs ellipses de troncature. Les rouges ont été exécutés avant les changements de production correspondants.

| N° | Traitement et preuve actuelle | Test ajouté ou étendu | Rouge observé | Nouveaux cas verts |
| --- | --- | --- | --- | ---: |
| 1 | `SplashScreen.tsx:189` rappelle `initApiBase` avant chaque sonde. Le client mémorise une découverte réussie et libère son repli ; le splash n’a plus de drapeau qui confond les deux. | `components/SplashScreen.reprisePort.r1.test.tsx`, vrai écran et vrai client, sondage et bouton de relance, HTTP et IPC doublés | `AssertionError: expected "vi.fn()" to be called 1 times, but got 0 times` | 2 |
| 2 | `SettingsModal.tsx:621,655` distingue les modèles demandés en cours des modèles confirmés. Un retour au fournisseur retrouve le choix en attente ; une ancienne fin ne supprime pas une demande plus récente. | `components/settings/SettingsModal.dernierChoix.b1805.test.tsx`, aller-retour pendant GET puis pendant POST | `AssertionError: expected [ 'mistral', 'mistral-medium-latest' ] to deeply equal [ 'mistral', 'mistral-small-2603' ]` | 2 |
| 3 | `LLMTab` transmet l’effort et l’adresse Qwen à `SettingsModal.handleSaveLLMOptions` (`:681`), qui utilise la file commune. Une option explicitement demandée est conservée dans cette file. Le choix de modèle tient compte de l’effort confirmé pendant son GET et conserve la normalisation de `xhigh`. | `components/settings/SettingsModal.ecrituresLLM.r1.test.tsx`, options lentes puis modèle, modèle lent puis effort, refus et reprise des deux options | `AssertionError: expected 'mistral-medium-latest' to be 'mistral-medium-3-5' // Object.is equality` ; `AssertionError: expected 'qwen3.8-max' to be 'qwen3.7-plus' // Object.is equality` ; `AssertionError: expected 'auto' to be 'high' // Object.is equality` | 5 |
| 4 | `SettingsModal.tsx:290-348` attend les écritures déjà engagées et contrôle le choix, la configuration confirmée et le numéro de lecture avant d’appliquer le résultat IA. | Même fichier `SettingsModal.ecrituresLLM.r1.test.tsx`, fermeture/réouverture avant et après le POST, restauration après refus suivant, deux relectures successives | `Error: expect(element).toHaveAttribute("aria-pressed", "true") // element.getAttribute("aria-pressed") === "true"` ; reçu : `aria-pressed="false"` | 3 |
| 5 | `documentStore.ts:395-411` vérifie la session d’ouverture et le document actif avant la resynchronisation, puis à nouveau avant l’erreur causale. | `stores/documentStore.ouvertureAnnulee.b1848.test.ts`, fermeture, autre document, même document rouvert, avant le conflit et pendant la resynchronisation | `AssertionError: expected "vi.fn()" to be called 1 times, but got 2 times` ; `AssertionError: expected 'Trame modifiée ailleurs.' to be null` | 6 |
| 6 | `documentStore.ts:222,628` transmet le jeton d’ouverture à la recherche de trame et ignore sa réponse périmée. | `stores/documentStore.trameRetrouvee.b1394.test.ts`, fermeture, autre document, même document rouvert ; vérifie ensuite que la génération de B peut partir | `AssertionError: expected { documentId: 'doc-1', …(2) } to be null` | 3 |
| 7 | Confirmé, non corrigé : intégration non ancêtre et métadonnées Git en lecture seule hors périmètre. Rebase à effectuer par l’orchestrateur, sans prétendre que la base est intégrée. | Contrôle Git d’ascendance, aucun test fonctionnel fabriqué | `git merge-base --is-ancestor c20/integration HEAD` : sortie **1** | Sans objet |
| 8 | Les trois erreurs CRM et les neuf erreurs RGPD acceptent `detail`, puis `message`, puis le repli français, y compris avec un corps JSON nul. Format réel lu dans `src/backend/app/main.py:657-662` ; le 404 « Contact non trouvé » vient notamment de `routers/rgpd.py:70`. | `services/api/crm-extended.erreursFrancaises.b1967.test.ts` et `services/api/rgpd.erreursFrancaises.b1968.test.ts`, `{code, message}` et `null` pour chaque opération | `AssertionError: expected [Function] to throw error including 'Contact non trouvé' but got 'L’export des données personnelles a é…'` ; `AssertionError: expected [Function] to throw error including 'La connexion au CRM n’a pas pu démarr…' but got 'Cannot read properties of null (readi…'` | 24 |
| 9 | `SettingsModal.tsx:644-646` efface statut et reprise d’opération lorsqu’un choix sans modèle ne lance aucune sauvegarde. La règle produit B-1846 reste à trancher ; cette passe ne la décide pas. | `components/settings/SettingsModal.ecrituresLLM.r1.test.tsx`, ancien POST qui réussit puis qui échoue | `AssertionError: expected <p role="status" …(1)></p> to be null` | 2 |
| 10 | Le paragraphe B-1848/B-1849 ne revendique plus de suppression depuis `DocumentsList`. Les garanties de suppression sont limitées au store ; aucun parcours d’interface n’a été ajouté. | Contrôle documentaire ponctuel, reproduit ci-dessous ; aucun test fonctionnel supplémentaire | `AssertionError: Le bilan attribue à DocumentsList une suppression absente de ses appelants.` | 1 contrôle documentaire |

**47 nouveaux cas frontend passent, dont 45 ont fourni un rouge.** Les deux cas supplémentaires du constat 3 protègent les refus et la réutilisation de la file. Les 36 cas CRM/RGPD antérieurs restent intacts, notamment les contrôles de `detail`, JSON vide et corps non JSON.

La vérification du correctif 4 a révélé une régression de sa première version : la première relecture rendait la suivante périmée même sans écriture. Le troisième test R1-4 a échoué avec `Error: expect(element).toHaveValue(mistral-small-2603)`, valeur reçue `mistral-medium-latest`. Le numéro de lecture corrige ce cas ; les trois tests et leurs voisins sont verts. Le premier lancement du test 9 avait seulement une ambiguïté de sélecteur entre la carte Ollama et son bouton de retest ; le sélecteur a été limité au groupe des fournisseurs avant de reproduire le vrai rouge cité au tableau.

Journaux des rouges : `/tmp/front-reglages-r1-N-rouge.log` pour N = 1, 2, 3, 4, 5, 6, 8, 9, 10 ; rouge supplémentaire du constat 4 : `/tmp/front-reglages-r1-4-relecture-rouge.log`. Les journaux verts correspondants portent `-vert.log`. Les deux refus ajoutés au constat 3 sont dans `/tmp/front-reglages-r1-3-refus.log`.

Contrôle documentaire du constat 10, exécuté avant puis après correction depuis la racine de cet arbre (copie d’exécution : `/tmp/front-reglages-r1-10-controle.py`) :

```python
from pathlib import Path

racine = Path.cwd()
source = (racine / 'src/frontend/src/components/documents/DocumentsList.tsx').read_text()
bilan = (racine / 'docs/qualite/c20-front-reglages.md').read_text()
preuve = next(ligne for ligne in bilan.splitlines() if ligne.startswith('- B-1848 et B-1849 :'))
assert 'deleteDocument' not in source, 'Les appelants ont changé : relire le parcours de suppression.'
assert 'ouvre et supprime' not in preuve, 'Le bilan attribue à DocumentsList une suppression absente de ses appelants.'
assert 'uniquement au niveau du store' in preuve, 'La limite de la preuve de suppression doit être explicite.'
```

### Appelants et tests voisins

- Démarrage : `App.tsx:219-223` monte le splash ; `initApiBase` reste partagé et mémorise le port découvert. Tests du splash, reprise des données, erreur fatale et singleton : **45/45**.
- Configuration IA : `PanelContainer.tsx:148` garde `SettingsModal` monté avec `isOpen`. `LLMTab` et `EffortSelector` n’ont pas d’autre parent de production. La voie des options est raccordée au parent ; leurs tests isolés conservent leur API autonome. Après le constat 2 : **40/40** ; après le constat 3 : **58/58**, plus **2/2** pour les refus ; après le dernier ajustement du constat 4 : **57/57** ; après le constat 9 : **51/51**. Ces groupes se recouvrent et ne sont pas additionnés.
- Documents : `DocumentWorkspace.tsx:234` transmet la réorganisation depuis `OutlineTree.tsx:130`. Les fermetures passent par `DocumentWorkspace.tsx:87,96` ; les ouvertures passent notamment par `DocumentsList.tsx:171,222`. Après le constat 5 : **86/86** ; après le constat 6 : **32/32**, avec le suivi normal de trame et la génération détachée conservés.
- Erreurs : `CRMSyncPanel.tsx:125,249`, les actions RGPD de `MemoryPanel` et les réglages de purge de `PrivacyTab` continuent de recevoir des exceptions avec leur motif. Clients et interfaces voisines : **72/72**. Aucun OAuth réel ni appel fournisseur.

### Portes ciblées de cette passe

**Frontend : 365 passés, 0 échoué, 0 ignoré, 50 fichiers passés sur 50, sortie 0.** Rapport `/tmp/front-reglages-r1-frontend.json` lu : tous les fichiers et toutes les assertions sont verts, dont les 47 nouveaux cas. Journal `/tmp/front-reglages-r1-frontend.log` ; sélection résolue `/tmp/front-reglages-r1-frontend-fichiers.txt`. Aucune suite complète n’a été lancée.

Sélection exacte et commande reproductible depuis `src/frontend` (la commande exécutée a passé cette liste résolue comme arguments à `npx`) :

```sh
npx --no-install vitest run \
  src/components/SplashScreen*.test.tsx \
  src/components/settings/SettingsModal*.test.* \
  src/components/settings/LLMTab*.test.tsx \
  src/stores/documentStore*.test.ts \
  src/components/documents/DocumentWorkspace*.test.tsx \
  src/components/documents/OutlineTree*.test.tsx \
  src/services/api/core.reprisePort.b1847.test.ts \
  src/services/api/core.portEtSingleton.test.ts \
  src/services/api/crm-extended.erreursFrancaises.b1967.test.ts \
  src/services/api/rgpd.erreursFrancaises.b1968.test.ts \
  src/components/settings/PrivacyTab.test.tsx \
  src/components/settings/PrivacyTab.purgeIndisponible.b1209.test.tsx \
  src/components/memory/MemoryPanel.rgpd.b1929.test.tsx \
  --maxWorkers=3 --no-cache --configLoader runner \
  --reporter=default --reporter=json \
  --outputFile.json=/tmp/front-reglages-r1-frontend.json
```

`--no-install` évite tout téléchargement ; `--configLoader runner --no-cache` conserve la configuration Vitest en évitant les écritures dans le `node_modules` partagé en lecture seule. Aucun délai de test n’a été augmenté.

**Backend voisin : 66 passés, 0 échec, 0 erreur, 0 ignoré, sortie 0.** XML `/tmp/front-reglages-r1.xml` lu : 66 éléments `testcase`, aucune balise `failure`, `error` ou `skipped`. Aucun rouge connu n’a été soustrait. Données jetables, client HTTP en processus et dépendances externes doublées. Commande depuis la racine :

```sh
THERESE_DATA_DIR="$(mktemp -d /tmp/front-reglages-r1-data.XXXXXX)" \
OLLAMA_BASE_URL=http://127.0.0.1:9 \
.venv/bin/python -m pytest tests/test_routers_rgpd.py tests/test_routers_crm_full.py \
  -q -p no:cacheprovider --timeout=120 --junitxml=/tmp/front-reglages-r1.xml
```

- TypeScript : `npx --no-install tsc --noEmit`, **sortie 0, 0 diagnostic**, `/tmp/front-reglages-r1-tsc.log` lu et vide.
- ESLint : `npm run lint`, **sortie 0, 0 erreur, 27 avertissements**, `/tmp/front-reglages-r1-lint.log` lu. Aucun correctif de lint hors périmètre.
- Ruff : `.venv/bin/python -m ruff check --no-fix src/backend tests`, **sortie 0**, `All checks passed!`, `/tmp/front-reglages-r1-ruff.log` lu.
- Contrôle documentaire 10 : **sortie 0**, `/tmp/front-reglages-r1-10-vert.log` lu.
- `git diff --check` : **sortie 0** ; index vide, HEAD inchangé. Le contrôle d’ascendance reste rouge et maintient le NO-GO.

Aucun serveur applicatif, port réservé, fournisseur LLM ou service réseau n’a été utilisé. Les accès HTTP/IPC frontend sont doublés ; certains tests antérieurs contiennent les ports historiques dans leurs chaînes, sans connexion réelle. Aucun accès au dossier de données personnel ni à `.app-loop/`. Les vérifications d’interface portent sur le DOM des vrais composants ; aucune recette native Tauri ni validation graphique nouvelle n’est revendiquée.

## Remédiation de la relecture, passe 2

Intervention des 16–17 novembre 2026 dans ce seul arbre. HEAD est resté à `4ebf0da70440700dfd5b77f6670883baccb789d0`, l’intégration locale à `75498edd9d40b0aeb14f8c02787a56b4dea27a28`. Aucun commit, ajout à l’index, dépôt annexe, bundle, réseau, fournisseur LLM, serveur applicatif, port réservé ou dossier personnel utilisé. Les liens non suivis `.venv` et `src/frontend/node_modules` étaient présents au départ et sont conservés.

### Constat 1 : contenu restauré, ascendance encore à corriger

Le constat est confirmé : le point commun est `e82f038a`, et les quatre commits `2dd3d2b1`, `9eb74c5d`, `fcf446a5`, `75498edd` manquent à l’ascendance. Le profil du bac à sable accorde seulement la lecture de `.git` et interdit toute élévation : le rebase ne peut pas être exécuté ici. L’orchestrateur doit donc encore corriger l’ascendance ; le NO-GO sur ce point n’est pas déclaré levé.

Le contenu des quatre commits a été reporté **sans index ni commit**, tests d’abord, puis sources après les reproductions rouges des migrations. Les **24 fichiers** concernés ont été comparés octet par octet à `c20/integration` : **0 divergence**. Cela restitue aussi les autres correctifs, tests et bilan de ce lot d’intégration (agents, facture, focus, provenance, refus mémoire et vérification des clés), sans modification supplémentaire de leur contenu. **11 cas backend et 9 cas frontend** sont ainsi récupérés. Les tests Board déjà présents n’ont pas été modifiés.

### Preuves rouges et correctifs

Chaque reproduction ci-dessous a été exécutée seule avant son correctif : fichier dédié ou filtre `-t R2-N` pour un fichier partagé. Les suites voisines ont ensuite été lancées après chaque correction. Les lignes sont recopiées des journaux réels ; celles du constat 1 viennent des XML, le hook `pytest_sessionfinish` existant interrompant le résumé terminal. Les chemins frontend sont relatifs à `src/frontend/src` ; les chemins Python sont relatifs à la racine.

| Constat | Test ajouté ou rétabli | Ligne rouge observée | Correctif |
| --- | --- | --- | --- |
| 1 | `tests/test_c20_b1888_transaction_activites.py::test_reconstruction_preserve_la_transaction_appelante` ; `tests/test_c20_b1889_notes_heritees.py::test_note_rattachee_preservee_si_evenement_sans_projet` | `AssertionError: La transaction de l’appelant a été validée.` ; `AssertionError: assert None == 'projet-existant'` | Report exact de l’intégration : ne valide plus la transaction appelante ; conserve le rattachement d’une note tant que le rendez-vous n’a pas de projet. Ascendance non modifiée, limite ci-dessus. |
| 2 | `components/settings/SettingsModal.ecrituresLLM.r1.test.tsx`, `R2-2` (1 cas) | `AssertionError: expected 'mistral-small-2603' to be 'mistral-large-latest' // Object.is equality` | File d’écriture commune à `SettingsModal` et `ChatInput`, conservée à la fermeture des réglages. Test avec les deux vrais composants, POST différé, dernier modèle enregistré et maximum d’un POST actif. |
| 3 | Même fichier, `R2-3` (effort et adresse, 2 cas) | `TestingLibraryElementError: Unable to find an accessible element with the role "alert"` | Le refus d’une option remonte à son appelant même lorsque la restauration du modèle est devenue périmée. Le modèle plus récent reste enregistré, l’erreur de l’option reste lisible. |
| 4 | Même fichier, `R2-4` (1 cas) | `AssertionError: expected 'xhigh' to be 'auto' // Object.is equality` | Normalisation déplacée dans le chemin commun d’écriture des réglages : une option reprenant `gpt-5.6-luna` pendant la lecture du choix remplace `xhigh` par `auto`. Teste aussi le sélecteur et l’absence de POST supplémentaire. |
| 5 | `components/documents/DocumentsList.creationFermee.r2.test.tsx`, `R2-5` (lecture tardive réussie ou refusée, 2 cas) | `AssertionError: expected "vi.fn()" to not be called at all, but actually been called 1 times` | `openDocument` renvoie un résultat explicite ; la création n’enchaîne la trame que si sa lecture a abouti. Parcours testé avec les vrais liste, modale, atelier et store : fermeture de A, ouverture de B, puis génération de B possible. |
| 6 | `stores/documentStore.trameRetrouvee.b1394.test.ts`, `R2-6` (3 cas) | `AssertionError: expected [ 'doc-1', 'doc-2', 'doc-1' ] to deeply equal [ 'doc-1', 'doc-2' ]` | Le sondage contrôle la session après chaque attente et avant de recharger ; la navigation détache le suivi précédent. Couvre le sondage terminé avant/après la lecture de B et le maintien du suivi pendant une relecture interne de A. Le premier cas était rouge, les deux autres sont des contrôles complémentaires. |
| 7 | `stores/documentStore.ouvertureAnnulee.b1848.test.ts`, `R2-7` (1 cas) | `AssertionError: expected null to be 'Trame modifiée ailleurs.' // Object.is equality` | Session de navigation distincte du numéro de lecture. Un rafraîchissement de A conserve le conflit et sa resynchronisation ; fermeture, suppression ou autre document périment l’ancienne opération. |
| 8 | Même fichier, `R2-8` (1 cas) | `AssertionError: expected [ { id: 'ancienne', …(11) } ] to deeply equal [ { id: 'recente', …(11) } ]` | La réussite d’une réorganisation contrôle elle aussi la session. Test avec une section fraîchement relue et un ancien instantané distinct après fermeture/réouverture de A. |
| 9 | `components/settings/SettingsModal.ecrituresLLM.r1.test.tsx`, `R2-9` (réussite et refus, 2 cas) | `AssertionError: expected <p role="status" …(1)></p> to be null` | L’option qui reprend un choix de modèle termine aussi son statut : reçu de succès ou fin de l’attente avec erreur. Teste une adresse Qwen déjà saisie et une lecture de modèle différée. |
| 10 | `components/settings/ToolsPanel.textesFrancais.c20.test.tsx`, `R2-10` (1 cas) | `TestingLibraryElementError: Unable to find an accessible element with the role "img" and name "Installé : démarrage en cours"` | `starting` possède son annonce et son indicateur d’attente ; les cas `stopped`, `error` et `running` sont conservés. |

**14 nouveaux cas frontend**, dont **12 rouges avant correction** et 2 contrôles complémentaires du constat 6. Journaux individuels : `/tmp/front-reglages-r2-N-rouge.log` et `/tmp/front-reglages-r2-N-vert.log`, N de 2 à 10. Pour le constat 1 : `/tmp/front-reglages-r2-1-rouge.xml` et `/tmp/front-reglages-r2-1-note-rouge.xml`, tous deux lus. Aucune assertion existante retirée ou relâchée. Dans `DocumentsList.test.tsx`, les deux doublures de lecture réussie renvoient maintenant `true`, conformément au nouveau contrat ; les contrôles de génération et d’ordre sont inchangés. Les adaptations de tests d’agents et de facture sont celles, exactes, de l’intégration.

### Appelants relus et tests voisins

- Écritures IA : appels de `SettingsModal` vers `LLMTab`, sauvegardes d’adresse et d’effort, sélecteur et bouton de reprise de `ChatInput`. Après les constats 2, 3, 4 et 9 : respectivement **22**, **21**, **51** et **34** cas voisins verts.
- Documents : création dans `DocumentCreateModal`, enchaînement dans `DocumentsList`, retour/démontage et réorganisation dans `DocumentWorkspace`, relectures après rédaction et suivi de trame dans le store. Le constat 7 a été corrigé avant le 6 pour réutiliser la session de navigation dans le sondage. Après les constats 5, 7, 6 et 8 : respectivement **125**, **107**, **128** et **109** cas voisins verts.
- Connecteurs : `SettingsModal` monte `ToolsPanel`, qui passe les serveurs relus à ses catégories de presets ; `Spinner` masque déjà son icône décorative. Après le constat 10 : **28** cas voisins verts dans 8 fichiers.
- Intégration : appels des migrations dans `database.py`, consommateurs de la provenance, des refus de mémoire et de la vérification des clés, montage d’`AgentSession` et d’`InvoiceForm`, piège de focus. **193** cas frontend voisins verts avant le contrôle final ; contrôles backend inclus ci-dessous.

Ces nombres intermédiaires se recouvrent : ils ne s’ajoutent pas aux comptes finaux.

### Portes ciblées finales

**Backend : 549 passés, 0 échec, 0 erreur, 0 ignoré, sortie 0.** `/tmp/front-reglages-r2.xml` lu : 549 éléments `testcase`, aucune balise `failure`, `error` ou `skipped`. Aucun rouge connu soustrait. Liste exacte exécutée :

```sh
OLLAMA_BASE_URL=http://127.0.0.1:9 PYTHONPATH=/tmp .venv/bin/python -m pytest \
  tests/test_c20_b1888_transaction_activites.py tests/test_c20_b1889_notes_heritees.py \
  tests/test_c20_b1890_activites_sans_contact.py tests/test_c20_b1891_reparation_transaction.py \
  tests/test_c20_b1893_provenance_sans_marque.py tests/test_c20_b2009_motifs_ambigus.py \
  tests/test_c20_b2010_limite_cle.py tests/test_c20_b2011_cle_sans_espace.py \
  tests/test_activity_migration.py tests/test_b1153_migration_colonnes.py \
  tests/test_b1153_rejeu_astra_v2.py tests/test_b1140_migration_sans_verrou.py \
  tests/test_r5_6_journal.py tests/test_b1348_verification_cle.py \
  tests/test_t4_7_provenance.py tests/test_t4_4_historique_documents.py \
  tests/test_c19d_b1088_securite_memoire.py tests/test_r2_2_protection.py \
  -q -p no:cacheprovider -p front_reglages_r2_ipc --timeout=120 \
  --junitxml=/tmp/front-reglages-r2.xml
```

**Adaptation d’exécution, pas un correctif produit :** le lancement natif s’est bloqué après 203 cas, à l’entrée du `TestClient` de `test_confirmation_journalise_issue_avant_traduction[resultat0-echouee]`. Interrompu, il n’a produit aucun XML final et n’est pas compté comme vert. Le diagnostic isolé avec `--timeout-method=thread` a atteint 120 s dans `anyio.from_thread`/le sélecteur asyncio (`/tmp/front-reglages-r2-diagnostic.log`). Une écriture dans une paire de sockets locale est refusée par ce bac à sable : `PermissionError [Errno 1] Operation not permitted`.

Le module temporaire `/tmp/front_reglages_r2_ipc.py`, chargé uniquement par la commande ci-dessus, remplace la paire de sockets de réveil interne d’asyncio par `os.pipe2(O_NONBLOCK | O_CLOEXEC)`. Les lectures, écritures, fermetures et l’enregistrement du lecteur utilisent les pipes ; aucune route, API, donnée, assertion, fixture ou règle de délai n’est remplacée. Le test isolé passe alors (XML `/tmp/front-reglages-r2-ipc.xml` lu), puis les mêmes 18 fichiers passent intégralement. Cette adaptation n’est pas ajoutée au dépôt. Sur une machine permettant le réveil asyncio normal, retirer `PYTHONPATH=/tmp` et `-p front_reglages_r2_ipc`. Journal final : `/tmp/front-reglages-r2-backend-pipe.log`.

**Frontend : 587 passés, 0 échoué, 0 ignoré, 142 fichiers passés sur 142, sortie 0.** Rapport `/tmp/front-reglages-r2-frontend.json` lu, journal `/tmp/front-reglages-r2-frontend.log`. Depuis `src/frontend` :

```sh
npm_config_offline=true npx vitest run \
  src/components/settings/SettingsModal*.test.* \
  src/components/settings/LLMTab*.test.tsx src/components/settings/ToolsPanel*.test.tsx \
  src/components/chat/ChatInput*.test.tsx \
  src/components/documents/DocumentsList*.test.tsx \
  src/components/documents/DocumentWorkspace*.test.tsx \
  src/components/documents/DocumentCreateModal*.test.tsx \
  src/stores/documentStore*.test.ts \
  src/components/atelier/AgentSession.*.test.tsx \
  src/components/invoices/InvoiceForm.*.test.tsx \
  src/hooks/useDialogFocusTrap*.test.tsx src/lib/effortOpenAI*.test.ts \
  --maxWorkers=3 --configLoader runner --no-cache \
  --reporter=json --outputFile=/tmp/front-reglages-r2-frontend.json
```

Le mode npm hors ligne interdit le téléchargement. `runner` et `--no-cache` évitent les écritures dans les dépendances partagées en lecture seule ; la configuration et les délais Vitest du dépôt restent inchangés. Aucune suite complète lancée.

- TypeScript : `npx tsc --noEmit`, **sortie 0, 0 diagnostic** ; `/tmp/front-reglages-r2-tsc.log` lu et vide.
- ESLint : `npm run lint`, **sortie 0, 0 erreur, 27 avertissements** ; `/tmp/front-reglages-r2-lint.log` lu, aucun nettoyage hors périmètre.
- Ruff : `.venv/bin/python -m ruff check --no-fix src/backend tests`, **sortie 0**, `All checks passed!` ; `/tmp/front-reglages-r2-ruff.log` lu.
- `git diff --check` : **sortie 0**. Tous les changements de cette passe restent non indexés et non commités. L’ascendance reste à corriger par l’orchestrateur.
