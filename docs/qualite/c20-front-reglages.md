# Cycle 20 : lot front-reglages

Travail limité à `gpt/c20-front-reglages`, base de cet arbre `12a383fb`, issue de l’intégration v0.83.0-alpha. Aucun commit, ajout à l’index, push, dépôt annexe ou bundle. Les modifications restent non commitées pour le rejeu et les commits de l’orchestrateur. Le commit historique `41a438a8` a uniquement été lu, puis son correctif de SettingsModal reporté dans cet arbre ; aucune branche main n’a été modifiée.

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
- B-1848 et B-1849 : `DocumentsList.tsx` ouvre et supprime les documents ; `DocumentWorkspace.tsx` appelle la fermeture et suit la génération. La fermeture invalide les lectures. Une suppression confirmée invalide uniquement la lecture du document supprimé ; un refus laisse le document consultable. Fermer libère `isLoading`, sans annuler la génération détachée ni libérer à tort le chargement de la suivante.
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
