# Cycle 20 : lot front-maj

Arbre : `therese-c20-lots/gpt-c20-front-maj`, branche `gpt/c20-front-maj`.
Reprise sur `0fa96143`, base annoncée `v0.83.0-alpha`.

Les sept commits hérités ont été relus. Aucun `git add`, commit ou push n'a
été exécuté pendant cette reprise. Les nouveaux tests et correctifs restent
dans cet arbre, non commités. Aucun appel à un fournisseur LLM ou à un
service en ligne. Les tests remplacent les API par des doubles ; aucun
démarrage de THÉRÈSE, aucun accès au profil réel ni aux ports interdits.

Les identifiants sont présentés dans l'ordre demandé. B-1950 a été terminé
en premier, conformément à la consigne particulière de reprise.

## Verdicts et preuves

Les chemins abrégés `ui/`, `rfc/`, `settings/` et `prototype/` ci-dessous
partent de `src/frontend/src/components/`. Les lignes de rouge sont celles
observées avant le correctif, avec les précisions utiles du diagnostic.

| Id | Verdict | Test (chemin::nom) | Commit du rouge ou ligne d'échec observée | Commit du correctif |
| --- | --- | --- | --- | --- |
| B-1801 | `confirme` | `ui/UpdateBanner.distribution.b1801.test.tsx::Manjaro : propose seulement le téléchargement manuel` | `Error: expect(element).not.toBeInTheDocument()` ; reçu : bouton `Installer maintenant`. 3 échecs, 1 succès au premier lancement. | non commité |
| B-1844 | `confirme` | `settings/AboutTab.versions.b1844.test.tsx::0.9.0-alpha.2 est une mise à jour de 0.9.0-alpha.1` | `193bb30e` (hérité) | `58a61366` (hérité) |
| B-1845 | `confirme` | `settings/AboutTab.versionVide.b1845.test.tsx::n’annonce pas de mise à jour tant que la version installée est inconnue` | `60bbe5fd` (hérité) | `0b8b634a` (hérité) |
| B-1949 | `confirme` | `rfc/RFCChat.arret.b1949.test.tsx::s’annonce « Arrêter la réponse » pendant la génération` | `6552777f` (hérité) | `af2a5fa5` (hérité) |
| B-1950 | `confirme` | `rfc/RFCChat.reflechit.b1950.test.tsx::« THÉRÈSE réfléchit... » est un statut live` | `0fa96143` (hérité), rejoué rouge : `Error: expect(element).toHaveAttribute("role", "status")`, reçu `null`. 1 échec. | non commité |
| B-1951 | `confirme` | `rfc/RFCWizard.fermeture.b1951.test.tsx::permet de trouver la fermeture par son nom puis de fermer` | `TestingLibraryElementError: Unable to find an accessible element with the role "button" and name "Fermer l’assistant de commande"`. 1 échec. | non commité |
| B-1952 | `confirme` | `rfc/RFCWizard.aide.b1952.test.tsx::explique dès le départ qu’une réponse complète est nécessaire` et `::explique encore le blocage après une réponse interrompue et invite à renvoyer` | `Error: expect(element).toHaveAccessibleDescription()` ; attendu `/réponse complète/`, reçu `Envoie d’abord ton brief à THÉRÈSE : « Passer à Faire » s’active dès le premier message.` ; après interruption, description vide. 3 échecs. | non commité |
| B-1953 | `confirme` | `rfc/RFCWizard.capture.b1953.test.tsx::indique qu’il faut attendre la réponse avant de capturer` et `::annonce la préparation de la commande pendant la génération` | `Error: expect(element).toHaveAccessibleDescription()` ; attendu `/Attends la fin de la réponse/` puis `/THÉRÈSE prépare ta commande/`, reçu vide. 2 échecs. | non commité |
| B-1954 | `confirme` | `settings/AboutTab.annonces.b1954.test.tsx::annonce la vérification en cours puis la nouvelle version dans la même région` et `::annonce une mise à jour disponible` | `TestingLibraryElementError: Unable to find an accessible element with the role "status"`. 2 échecs, 1 succès. | non commité |
| B-1955 | `rejete` | `rfc/RFCWizard.aide.b1952.test.tsx::explique encore le blocage après une réponse interrompue et invite à renvoyer` | Doublon déjà traité par B-1952 au moment de son examen ; aucune nouvelle modification. | Sans objet ; couvert par B-1952 non commité |
| B-1956 | `rejete` | `rfc/RFCWizard.fermeture.b1951.test.tsx::permet de trouver la fermeture par son nom puis de fermer` | Doublon déjà traité par B-1951 au moment de son examen ; aucune nouvelle modification. | Sans objet ; couvert par B-1951 non commité |
| B-1957 | `regle_a_trancher` | Aucun test rouge de comportement obtenu | Hauteur fixe constatée, mais défilement prévu dans le parent ; voir la question de présentation et la limite de mesure ci-dessous. | Sans objet ; aucune modification de hauteur |
| B-1958 | `confirme` | `prototype/usePrototypeEmailData.erreurs.b1958.test.tsx::explique l’échec de vérification des comptes avant de lister les messages, puis permet de réessayer` | `AssertionError: expected 'Impossible de charger les messages po…' to be 'Impossible de vérifier la connexion d…' // Object.is equality`. 1 échec, 1 succès. | non commité |

Bilan : 10 candidats confirmés, dont 3 correctifs hérités et 7 terminés
pendant cette reprise ; 2 doublons rejetés après correction du premier
constat ; 1 règle de présentation à trancher. « Rejeté » ne signifie pas que
B-1955 et B-1956 étaient déjà corrigés dans la base initiale.

## Exécution réelle des fichiers corrigés

Ces chemins ont été vérifiés avant les corrections correspondantes :

- `App.tsx:276` monte `UpdateBanner`. Le contrôle de type de paquet est
  appelé à la vérification et au clic d'installation. Le contrôle de
  distribution utilise `get_system_info`, commande déjà enregistrée dans
  `src-tauri/src/lib.rs:596` et implémentée dans `src-tauri/src/commands.rs`.
  Le nouveau module Rust est appelé par cette commande, pas seulement par
  ses tests.
- `App.tsx:287` monte `ConversationCanvasPrototype`, qui monte
  `PrototypeChatSurface` ; celui-ci monte `MessageList`, qui monte
  `HomeCommands` ; `HomeCommands.tsx:206` monte `RFCWizard`. Le wizard monte
  le vrai `RFCChat` aux étapes Réfléchir et Faire.
- `SettingsModal.tsx:858` rend `AboutTab`.
- `ConversationCanvasPrototype.tsx:969` appelle `usePrototypeEmailData`
  lorsque le parcours E-mail est actif.

## Règles conservées et tests existants

Pour B-1801, un paquet `.deb` n'est plus une preuve suffisante : il peut
avoir été extrait ou repaqueté sur une autre distribution. Les distributions
Debian et dérivées sont reconnues par les identifiants natifs ; lecture
impossible ou champ absent signifie installation manuelle. Le contrôle est
refait avant le téléchargement et l'arrêt du moteur. La procédure canonique
est documentée dans [`../UPDATER-SETUP.md`](../UPDATER-SETUP.md).
Les tests existants conservent la couverture Debian, AppImage, RPM, Windows,
macOS, absence de Tauri et choix de vérification automatique.

Un test existant de `UpdateBanner.installation.test.tsx` imposait « aucun
appel IPC » si le type devenait inconnu au clic. La lecture initiale de la
distribution étant désormais nécessaire, il impose maintenant exactement
un appel `get_system_info`. L'interdiction de télécharger ou d'arrêter le
moteur reste vérifiée. Le double natif fournit également `linux_debian:
true` pour les anciens cas Debian. Il s'agit d'une adaptation du contrat
de lecture, pas d'un affaiblissement de la protection d'installation.

Pour B-1952, la règle de provenance est déjà fixée par `goToMake` et les
tests `RFCWizard.confidentialite.t6/t7/t8`. La transition exige une réponse
complète et vérifiée. Seule l'aide a changé : elle reste liée au bouton
après une réponse interrompue. La garde et les tests existants ne changent
pas. Les deux doublons sont prouvés par cette aide, dans
`RFCWizard.tsx:227`, et par le nom du bouton de fermeture, ligne 164.

Pour B-1954, une seule région de statut persistante reçoit l'attente et les
deux résultats. Les liens et boutons de téléchargement restent hors de
cette annonce.

Deux doubles hérités, dans les tests B-1949 et B-1950, violaient `require-yield`.
`yield await new Promise<never>(...)` conserve exactement leur flux en
attente. Aucune assertion n'a été retirée. Le correctif hérité `58a61366`
avait aussi précisé `/à jour/` en `/THÉRÈSE est à jour/` pour ne pas attraper
le libellé du bouton de vérification ; cette précision a été relue et
conservée.

## B-1957 : règle à trancher et limite de preuve

Question : dans une fenêtre basse, l'assistant entier doit-il tenir dans
la zone visible, ou le défilement de son parent est-il le comportement
attendu ? `RFCWizard.tsx:203` fixe l'étape à 450 px ;
`MessageList.tsx:211` fournit déjà `overflow-y-auto`. Le seul dépassement de
450 px ne suffit donc pas à prouver qu'une commande est inaccessible.
Aucun contrat de hauteur minimale ou d'absence de défilement pour cet
assistant n'a été trouvé dans le code et les tests voisins.

Options : conserver le défilement du parent, ou borner le wizard à la place
disponible et faire défiler ses messages en gardant saisie et navigation
visibles. Recommandation : la seconde option, à vérifier sur le parcours
complet avec son en-tête, à 500 et 560 px de hauteur, ainsi qu'après
apparition d'une erreur. Aucune correction de hauteur sans cette preuve.

La reproduction géométrique n'a pas été obtenue : Chromium est arrêté par
le bac à sable (`bootstrap_check_in ... Permission denied (1100)`),
l'écoute d'un serveur local éphémère échoue avec `EPERM`, l'hôte de
navigateur automatisé est indisponible et l'accès natif à Chrome a été
refusé (`Computer Use was not approved to use Google Chrome`). Le fichier
`/tmp/front-maj-apercu.html` a été produit à partir du rendu des composants
et de leurs styles, mais n'a pas pu être inspecté. Il n'est pas présenté
comme une preuve visuelle. Ce blocage de mesure reste distinct de la
question de présentation ; il ne prouve ni le bug ni son absence.

## Portes de sortie

Comptes lus dans le rapport JSON complet, pas déduits de la console :

| Porte | Résultat final | Échecs nommés et preuves |
| --- | --- | --- |
| Frontend, `npm run test -- --run --configLoader runner --reporter=json --outputFile=/tmp/front-maj-vitest.json` | **4 116 tests passés, 0 échoué, 0 ignoré, 0 todo ; 967 fichiers passés, 0 échoué.** Sortie 0. | Aucun échec. Rapport `/tmp/front-maj-vitest.json`, compte relu dans `/tmp/front-maj-counts.json`. |
| TypeScript, `npx --no-install tsc --noEmit` | **0 erreur**, sortie 0. | Journal final vide : `/tmp/front-maj-tsc.log`. |
| Frontend, `npm run lint` | **0 erreur, 27 avertissements**, sortie 0. | Le seuil configuré est 27 ; journal `/tmp/front-maj-lint.log`. |
| Ruff, `.venv/bin/python -m ruff check --no-fix src/backend tests` | **0 diagnostic**, sortie 0. | `All checks passed!` dans `/tmp/front-maj-ruff.log`. |
| Rust, module de distribution compilé directement | **8 tests passés, 0 échoué.** | Aucun échec ; binaire jetable `/tmp/front-maj-distribution-tests`. |
| Tauri, `cargo check --offline --locked` avec cible dans `/tmp` | **Bloqué avant compilation complète** | `error: failed to download tauri-plugin-opener v2.5.0` puis `attempting to make an HTTP request, but --offline was specified` ; `/tmp/front-maj-cargo.log`. |
| Backend, pytest | **Non applicable, non exécuté** | Aucun changement Python ; aucun compte de tests backend revendiqué. |

Les premières passes statiques ont signalé deux erreurs ESLint
`require-yield` dans `RFCChat.arret.b1949.test.tsx:9` et
`RFCChat.reflechit.b1950.test.tsx:9`, ainsi qu'une erreur TypeScript
`TS2345` dans `RFCWizard.aide.b1952.test.tsx:28` : le fragment simulé `done`
n'avait pas de champ `content`. Les doubles ont été corrigés sans retirer
d'assertion, puis TypeScript et ESLint ont été relancés et sont verts.
Les tests concernés ont également été rejoués après cette normalisation.

Le lancement Vitest sans option échoue avant les tests : Vite tente
d'écrire dans `node_modules/.vite-temp`, qui est partagé et non inscriptible.
Tous les tests sont donc exécutés avec `--configLoader runner`, sans
modifier la configuration du dépôt ni les dépendances partagées.

Le contrôle Rust complet a été tenté hors ligne :
`cargo check --offline --locked --manifest-path src/frontend/src-tauri/Cargo.toml --target-dir /tmp/front-maj-cargo`.
Il ne compile pas le projet, car `tauri-plugin-opener v2.5.0` manque au cache.
Aucun téléchargement n'a été tenté. Les tests natifs du module de
distribution ont été compilés et exécutés par `rustc --edition=2021 --test` :
8 passés, 0 échoué (Debian, Ubuntu, Mint, Manjaro, Fedora, inconnu,
identifiants exacts, commentaires et guillemets).

Aucun fichier Python backend ou test Python n'a été modifié : la porte
pytest backend n'est pas applicable à ce lot. Les échecs backend de
référence annoncés dans le mandat ne sont donc ni rejoués ni comptabilisés.

## Limites conservées de l'héritage

Les tests B-1844, B-1845 et B-1949 sont verts lors de la reprise. Comme
demandé, leurs correctifs n'ont pas été refaits. B-1844 couvre les
comparaisons de préversions ; le libellé de phase reste littéralement
« Alpha » dans `AboutTab.tsx:205`. Sa généralisation n'est pas revendiquée.
L'installation réelle N vers N+1 sur Manjaro ou Debian n'a pas été exécutée.

Pour les commits à produire par l'orchestrateur : séparer chaque rouge et
son correctif selon le mandat, expliquer les adaptations de tests
ci-dessus et terminer chaque message par
`Co-Authored-By: Codex <noreply@openai.com>`.
