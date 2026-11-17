# Cycle 20 : lot front-maj

Arbre : `therese-c20-lots/gpt-c20-front-maj`, branche `gpt/c20-front-maj`.
État reçu pour la passe 3 : HEAD `d3e815e7`, tests de passe 2 `fefd0e1d`
et correctifs `d3e815e7` déjà commités par l'orchestrateur.
La base d'intégration `75498edd` est un ancêtre du lot reçu.
La référence locale `c20/integration` a depuis avancé à `a498d9d3`,
incluant `31e3f98d` ; cette nouvelle ascendance manque encore au lot.
Le constat 1 de la passe 3 décrit ce retard distinct.

État remis à la relecture après la passe 1 (historique avant rebase) :
`7c94e52a`, avec les tests `6ab9f8cf`.

La reprise historique partait du rouge B-1950, maintenant `90e29bad` après
rebase. Aucun commit n'avait été créé pendant cette reprise ;
l'orchestrateur a ensuite commité les tests (`b53869ce`) et correctifs
(`f1087358`). Les comptes ci-dessous sont historiques. Seule la section
« Remédiation de la relecture, passe 3 » décrit le travail actuel, laissé
non commité. Aucun service réel n'est utilisé pour ses tests.

Les identifiants sont présentés dans l'ordre demandé. B-1950 a été terminé
en premier, conformément à la consigne particulière de reprise.

## Verdicts et preuves

Les chemins abrégés `ui/`, `rfc/`, `settings/` et `prototype/` ci-dessous
partent de `src/frontend/src/components/`. Les lignes de rouge sont celles
observées avant le correctif, avec les précisions utiles du diagnostic.

| Id | Verdict | Test (chemin::nom) | Commit du rouge ou ligne d'échec observée | Commit du correctif |
| --- | --- | --- | --- | --- |
| B-1801 | `confirme` | `ui/UpdateBanner.distribution.b1801.test.tsx::Manjaro : propose seulement le téléchargement manuel` | `Error: expect(element).not.toBeInTheDocument()` ; reçu : bouton `Installer maintenant`. 3 échecs, 1 succès au premier lancement. | `f1087358` |
| B-1844 | `confirme` | `settings/AboutTab.versions.b1844.test.tsx::0.9.0-alpha.2 est une mise à jour de 0.9.0-alpha.1` | `d805a3a4` (hérité) | `5ed7a868` (hérité) |
| B-1845 | `confirme` | `settings/AboutTab.versionVide.b1845.test.tsx::n’annonce pas de mise à jour tant que la version installée est inconnue` | `0198b00d` (hérité) | `d5568587` (hérité) |
| B-1949 | `amelioration` | `rfc/RFCChat.arret.b1949.test.tsx::s’annonce « Arrêter la réponse » pendant la génération` | `97e8ff6f` (hérité), rouge portant sur l'attribut ; requalification en R1-9 ci-dessous | `61f1a8f9` (hérité) |
| B-1950 | `confirme` | `rfc/RFCChat.reflechit.b1950.test.tsx::« THÉRÈSE réfléchit... » est un statut live` | `90e29bad` (hérité), rejoué rouge : `Error: expect(element).toHaveAttribute("role", "status")`, reçu `null`. 1 échec. | `f1087358` |
| B-1951 | `confirme` | `rfc/RFCWizard.fermeture.b1951.test.tsx::permet de trouver la fermeture par son nom puis de fermer` | `TestingLibraryElementError: Unable to find an accessible element with the role "button" and name "Fermer l’assistant de commande"`. 1 échec. | `f1087358` |
| B-1952 | `confirme` | `rfc/RFCWizard.aide.b1952.test.tsx::explique dès le départ qu’une réponse complète est nécessaire` et `::explique encore le blocage après une réponse interrompue et invite à renvoyer` | `Error: expect(element).toHaveAccessibleDescription()` ; attendu `/réponse complète/`, reçu `Envoie d’abord ton brief à THÉRÈSE : « Passer à Faire » s’active dès le premier message.` ; après interruption, description vide. 3 échecs. | `f1087358` |
| B-1953 | `confirme` | `rfc/RFCWizard.capture.b1953.test.tsx::indique qu’il faut attendre la réponse avant de capturer` et `::annonce la préparation de la commande pendant la génération` | `Error: expect(element).toHaveAccessibleDescription()` ; attendu `/Attends la fin de la réponse/` puis `/THÉRÈSE prépare ta commande/`, reçu vide. 2 échecs. | `f1087358` |
| B-1954 | `confirme` | `settings/AboutTab.annonces.b1954.test.tsx::annonce la vérification en cours puis la nouvelle version dans la même région` et `::annonce une mise à jour disponible` | `TestingLibraryElementError: Unable to find an accessible element with the role "status"`. 2 échecs, 1 succès. | `f1087358` |
| B-1955 | `rejete` | `rfc/RFCWizard.aide.b1952.test.tsx::explique encore le blocage après une réponse interrompue et invite à renvoyer` | Doublon déjà traité par B-1952 au moment de son examen ; aucune nouvelle modification. | Sans objet ; couvert par B-1952 `f1087358` |
| B-1956 | `rejete` | `rfc/RFCWizard.fermeture.b1951.test.tsx::permet de trouver la fermeture par son nom puis de fermer` | Doublon déjà traité par B-1951 au moment de son examen ; aucune nouvelle modification. | Sans objet ; couvert par B-1951 `f1087358` |
| B-1957 | `regle_a_trancher` | Aucun test rouge de comportement obtenu | Hauteur fixe constatée, mais défilement prévu dans le parent ; voir la question de présentation et la limite de mesure ci-dessous. | Sans objet ; aucune modification de hauteur |
| B-1958 | `confirme` | `prototype/usePrototypeEmailData.erreurs.b1958.test.tsx::explique l’échec de vérification des comptes avant de lister les messages, puis permet de réessayer` | `AssertionError: expected 'Impossible de charger les messages po…' to be 'Impossible de vérifier la connexion d…' // Object.is equality`. 1 échec, 1 succès. | `f1087358` |

Bilan après requalification R1-9 : 9 candidats confirmés, dont 2 correctifs
hérités et 7 terminés pendant cette reprise ; 1 amélioration héritée ;
2 doublons rejetés après correction du premier
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
attente. Aucune assertion n'a été retirée. Le correctif hérité `5ed7a868`
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

## Portes de sortie historiques, avant relecture

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

Consigne historique pour les commits de l'orchestrateur : séparer chaque rouge et
son correctif selon le mandat, expliquer les adaptations de tests
ci-dessus et terminer chaque message par
`Co-Authored-By: Codex <noreply@openai.com>`.

## Remédiation de la relecture, passe 1

Départ historique : `f1087358`. Cette passe a ensuite été commitée par
l'orchestrateur : `6ab9f8cf` pour les tests et `7c94e52a` pour les correctifs.
C'est cet état qui a été remis à la relecture contradictoire suivante.
La mention d'ascendance de `c20/integration` dans le précédent bilan ne
décrivait pas l'intégration locale lors de la passe 2. Le rebase effectué
ensuite a intégré `75498edd` ; le nouveau retard est décrit en passe 3.
Pendant la passe 1, aucun ajout à l'index, commit, push, dépôt annexe ou
bundle n'avait été effectué par l'agent. Aucun réseau, fournisseur LLM,
serveur ou application THÉRÈSE lancé. Aucun accès au profil réel,
à `.app-loop/` ou aux ports interdits. API frontend doublées et données
pytest jetables sous `/tmp`, sondes désactivées.

### Décisions et correctifs

1. **Identité installée, confirmé.** `AboutTab` refuse de conclure quand le
   moteur fournit seulement `X.Y.Z` et que la publication distingue une
   préversion du même numéro, par exemple `X.Y.Z-alpha.2`. Il affiche une
   erreur et le lien manuel. L'alias historique avec le tag simple
   `X.Y.Z-alpha`, documenté et déjà testé, reste accepté. Aucun suffixe
   numéroté n'est inventé ; aucun changement du moteur ou de la procédure
   de publication. Le test passe par la lecture simulée de `/health`,
   avec `0.83.0`, au lieu d'injecter une préversion complète dans le store.
2. **SemVer, confirmé.** La comparaison valide les deux versions en entier,
   ignore les métadonnées de build et compare les identifiants numériques
   sans arrondi. `null` signifie illisible et `0` égalité. Seize cas couvrent
   les builds, l'ordre numérique et lexical, les grands identifiants,
   les champs absents, les zéros initiaux et les versions mal formées.
3. **OS natif, confirmé.** `get_system_info.os` décide de la compatibilité :
   Linux exige `deb` et `linux_debian === true`, macOS `app`, Windows `nsis`
   ou `msi`. L'absence d'OS interdit l'installation. Onze cas couvrent une
   plateforme webview vide ou trompeuse, le système inconnu et sa perte
   au clic. Les contrôles précèdent toujours le téléchargement et l'arrêt
   du moteur. La procédure est dans [UPDATER-SETUP](../UPDATER-SETUP.md).
4. **Capture pendant le flux, confirmé.** Le vrai `RFCChat` remonte son état
   au wizard. Le bouton et sa garde attendent chaque réponse. Deux cas
   exercent une deuxième réponse complète ou interrompue : la capture
   reprend respectivement les deux sources vérifiées ou seulement la
   première. Les parcours existants de refus, interruption, capture
   manuelle et retrait des sources restent verts.
5. **Nouvelle lecture au clic, confirmé.** Une version manquante est relue,
   puis comparée dans le même clic. Le montage et le clic partagent une
   lecture en cours ; le bouton évite les doubles clics. Trois cas
   vérifient la reprise, la lecture partagée et un nouvel échec suivi
   d'une troisième lecture réussie. Aucun appel aux publications tant
   que le moteur n'a pas fourni la version.
6. **Repli manuel, confirmé.** Le texte dit que la vérification automatique
   est impossible et indique la méthode manuelle. Il ne prétend plus
   qu'une nouvelle version existe. Le test vérifie aussi l'absence
   d'appel au plugin updater et la présence du lien.
7. **Régions live, confirmé sur le DOM.** Les régions de `RFCChat` et
   `AboutTab` existent vides avant l'action, restent accessibles et
   reçoivent ensuite le texte dans le même nœud. `sr-only` remplace le
   masquage du statut vide ; le test applique aussi la règle CSS
   `empty:hidden` qui causait l'exclusion. **L'annonce vocale avec un
   lecteur d'écran natif n'a pas été exercée** : les deux tests DOM
   ne sont pas présentés comme une preuve VoiceOver.
8. **Aide Réfléchir, confirmé.** Avant l'envoi, elle demande le brief ;
   pendant le flux elle indique que THÉRÈSE répond ; après interruption
   elle invite à renvoyer. Deux nouveaux cas couvrent le premier envoi
   et le renvoi, sans affaiblir les trois tests existants.
9. **B-1949, requalifié en amélioration.** Le `title` donnait déjà le nom
   accessible « Arrêter la réponse ». L'assertion historique sur
   `aria-label` reste conservée. Un test retire cet attribut uniquement
   dans son DOM et retrouve le même bouton par son nom. Aucun défaut
   d'usage antérieur n'est revendiqué. Le rouge de remédiation est le
   test documentaire de qualification, pas ce test de caractérisation.
10. **Bilan après rebase, historique.** Le bilan de passe 1 distinguait
    l'état `f1087358` de la remédiation alors en cours. Celle-ci a depuis
    été commitée dans `6ab9f8cf` et `7c94e52a`. Le test de cette passe ne
    contrôlait que le tableau historique ; R2-5 vérifie aussi l'état de
    la passe 1 et le rattachement du travail actuel à la passe 2.

### Rouges isolés, observés avant correction

Les fichiers sont relatifs à `src/frontend/src/`. Chaque commande utilise
`vitest run <fichier> --configLoader runner --maxWorkers=3 --reporter=verbose`.
Seuls les nouveaux cas R1-6, R1-8, R1-9 et R1-10 ont été sélectionnés avec
`-t R1-N` dans leur fichier existant. Les cas non sélectionnés de ces
lancements ne sont pas des tests ignorés de la porte finale.

| Constat | Fichier et sélection | Résultat rouge | Journal |
| --- | --- | --- | --- |
| 1 | `components/settings/AboutTab.identite.r1.test.tsx` | 1 échec | `/tmp/front-maj-r1-1-rouge.log` |
| 2 | `components/settings/AboutTab.semver.r1.test.tsx` | 12 échecs, 4 succès | `/tmp/front-maj-r1-2-rouge.log` |
| 3 | `components/ui/UpdateBanner.systeme.r1.test.tsx` | 11 échecs | `/tmp/front-maj-r1-3-rouge.log` |
| 4 | `components/rfc/RFCWizard.flux.r1.test.tsx` | 2 échecs de comportement au rejeu | `/tmp/front-maj-r1-4-rouge-confirme.log` |
| 5 | `components/settings/AboutTab.reessai.r1.test.tsx` | 3 échecs | `/tmp/front-maj-r1-5-rouge.log` |
| 6 | `components/ui/UpdateBanner.distribution.b1801.test.tsx`, `R1-6` | 1 échec | `/tmp/front-maj-r1-6-rouge.log` |
| 7 | `test/frontMaj.annonces.r1.test.tsx` | 2 échecs | `/tmp/front-maj-r1-7-rouge.log` |
| 8 | `components/rfc/RFCWizard.aide.b1952.test.tsx`, `R1-8` | 2 échecs | `/tmp/front-maj-r1-8-rouge.log` |
| 9 | `test/frontMaj.bilan.r1.test.ts`, `R1-9` | 1 échec | `/tmp/front-maj-r1-9-rouge-confirme.log` |
| 10 | `test/frontMaj.bilan.r1.test.ts`, `R1-10` | 1 échec | `/tmp/front-maj-r1-10-rouge.log` |

Lignes d'échec recopiées des journaux ci-dessus :

```text
1. TestingLibraryElementError: Unable to find role="alert"
2. TestingLibraryElementError: Unable to find an element with the text: /Nouvelle version disponible/. This could be because the text is broken up by multiple elements. In this case, you can provide a function for your text matcher to make your matcher more flexible.
3. Error: expect(element).not.toBeInTheDocument()
4. Error: expect(element).toBeDisabled()
5. AssertionError: expected "vi.fn()" to be called 2 times, but got 1 times
6. Error: expect(element).not.toHaveTextContent()
7. TestingLibraryElementError: Unable to find an accessible element with the role "status"
7. AssertionError: expected true to be false // Object.is equality
8. Error: expect(element).toHaveAccessibleDescription()
9. AssertionError: expected '| B-1949 | `confirme` | `rfc/RFCChat.…' to contain '`amelioration`'
10. AssertionError: expected '# Cycle 20 : lot front-maj\n\nArbre :…' to contain 'f1087358'
```

Deux erreurs de montage des nouveaux tests ont été corrigées avant de
retenir leur preuve : `resetAllMocks` effaçait le double `matchMedia` du
test R1-4 ; `import.meta.url` donnait une URL HTTP dans le test documentaire
R1-9. Le premier lancement R1-4 avait déjà un rouge de comportement sur
l'interruption ; le rejeu des deux cas, liaison d'état du flux retirée,
a confirmé les deux rouges avant de rétablir cette liaison. Pour R1-9,
la ligne du bilan a été remise à son état initial, puis le test a échoué
sur `confirme` avant sa requalification. Ces erreurs de montage ne sont
pas comptées comme preuves de défaut produit. Le nouveau test R1-8 attend
la propagation de l'effet React après interruption, sans changer son
assertion ni les tests antérieurs.

### Appelants et tests voisins

Après chaque correctif, les appelants ont été relus et les tests voisins
rejoués : `SettingsModal → AboutTab → useBackendStore`,
`App → UpdateBanner → installationAutomatiqueAutorisee`,
`HomeCommands → RFCWizard → RFCChat`, puis les chemins de capture et de
reprise des sources. Les rapports intermédiaires `/tmp/front-maj-r1-N-vert.json`
portent ces sélections ; la porte finale ci-dessous est le compte de
référence, sans additionner plusieurs passages du même test.

Les doubles natifs existants ont été complétés avec `os`. Le cas MSI sous
Linux impose désormais exactement une lecture `get_system_info`, à la place
de l'ancien « aucun IPC ». Il interdit toujours tout téléchargement,
appel updater et arrêt du moteur ; aucune assertion de protection n'a été
retirée. Les tests B-1949 et B-1952 existants conservent leurs assertions.

### Portes de cette passe

| Porte | Résultat lu | Preuve |
| --- | --- | --- |
| Vitest ciblé, 3 workers au maximum | **108 passés, 0 échoué, 0 ignoré, 0 todo ; 28 fichiers passés** | `/tmp/front-maj-r1-vitest.json` |
| TypeScript | **0 erreur**, sortie 0 | `/tmp/front-maj-r1-tsc.log` vide |
| ESLint | **0 erreur, 27 avertissements**, sortie 0 | `/tmp/front-maj-r1-lint.log` |
| Pytest voisin updater | **16 passés, 0 échec, 0 erreur, 0 ignoré**, sortie 0 | `/tmp/front-maj-r1.xml`, XML relu |
| Ruff backend et tests | **0 diagnostic**, sortie 0 | `/tmp/front-maj-r1-ruff.log` : `All checks passed!` |

Commandes reproductibles, à partir de la racine sauf pour le frontend :

```sh
# Depuis src/frontend ; outils déjà installés, aucun téléchargement.
npx --offline --no-install vitest run src/components/settings/AboutTab src/components/ui/UpdateBanner src/components/rfc src/components/home/HomeCommands.assistantCommande.test.tsx src/components/home/HomeCommands.panneauGuide.test.tsx src/components/home/HomeCommands.cycle6.test.tsx src/hooks/useBackend.c9.test.ts src/test/frontMaj.annonces.r1.test.tsx src/test/frontMaj.bilan.r1.test.ts --configLoader runner --maxWorkers=3 --reporter=json --outputFile=/tmp/front-maj-r1-vitest.json
npx --offline --no-install tsc --noEmit
npm run lint

# Depuis la racine ; données jetables, cache et bytecode désactivés.
THERESE_DATA_DIR="$(mktemp -d /tmp/front-maj-r1-data.XXXXXX)" PYTHONDONTWRITEBYTECODE=1 OLLAMA_BASE_URL=http://127.0.0.1:9 .venv/bin/python -m pytest tests/test_b1111_manifeste_updater.py -q -p no:cacheprovider --timeout=120 --junitxml=/tmp/front-maj-r1.xml
.venv/bin/python -m ruff check --no-fix src/backend tests
```

`--configLoader runner` évite l'écriture de configuration dans les
dépendances partagées. Aucune suite complète, aucun test Python sans
rapport et aucun lint corrigé ailleurs. Les rouges connus cités dans le
mandat ne font pas partie de la sélection et ne sont pas comptés.

**VERDICT : GO AVEC RÉSERVES.** Les défauts reproduits sont corrigés et les
portes ciblées sont vertes. La réserve concerne l'annonce effective par
un lecteur d'écran natif, non mesurée. Aucune installation réelle ni
publication n'est revendiquée. La hauteur B-1957 reste hors de cette passe.

## Remédiation de la relecture, passe 2

Départ historique : HEAD `7c94e52a`, branche `gpt/c20-front-maj`.
Cette passe a depuis été commitée par l'orchestrateur : tests `fefd0e1d`,
correctifs `d3e815e7`, après rebase sur `75498edd`.
Cette base, qui contient `e82f038a`, est bien un ancêtre du lot reçu en
passe 3. Les paragraphes suivants décrivent les observations de la passe 2,
avant ces opérations ; ils ne décrivent pas la branche actuelle.
Les liens `.venv` et `src/frontend/node_modules`, seuls éléments non suivis
au départ, avaient été conservés. Aucun réseau, fournisseur LLM, serveur
ni application réelle n'avait été utilisé.

### Constats et corrections

1. **Identité installée : corrigé.** La garde de `AboutTab` refuse aussi
   de conclure face à la version finale du même numéro quand le moteur
   n'a fourni aucun suffixe. Les métadonnées de build ne lèvent pas cette
   ambiguïté. `AboutTab.identite.r1.test.tsx` couvre la préversion numérotée,
   la finale et la finale avec métadonnées. L'alias historique `X.Y.Z-alpha`
   reste couvert par le test existant. Les tests des régions accessibles
   utilisent maintenant une identité explicite ; leurs assertions sont
   conservées. Le cas SemVer d'égalité des builds utilise une préversion
   explicite, et l'ancien couple de finales avec builds reste testé dans
   le fichier d'identité, avec le refus de conclure désormais requis.
2. **Passage à Faire pendant un deuxième flux : corrigé.** Le bouton et
   `goToMake` gardent la transition tant que `reflectStreaming` est vrai.
   L'aide reste reliée au bouton pendant ce deuxième échange. Deux tests
   avec le vrai mini-chat vérifient l'absence d'interruption au clic, puis
   la reprise de deux sources après la fin normale ou de la première
   seulement après un arrêt volontaire. Les tests voisins de provenance
   attendent désormais le bouton actif avant le clic ; leurs assertions
   sur les sources, les refus et les suppressions sont conservées.
3. **Fausse erreur pendant la lecture : corrigé.** Un état de lecture
   distinct annonce l'attente dès le montage et pendant la lecture partagée
   avec le clic. L'erreur et le lien manuel apparaissent après rejet ou
   réponse sans version. Les assertions incorrectes de `reessai.r1` et
   `versionVide.b1845` sont remplacées par l'attente sans alerte ni lien,
   sans retirer l'interdiction d'appeler les publications avant la version.
   Deux nouveaux cas couvrent l'échec différé et la réponse vide au montage.
4. **Intégration absente : constat historique, résolu jusqu'à `75498edd`.**
   Le contrôle d'ascendance échouait pendant cette passe. Les correctifs
   MCP et Board ainsi que les six fichiers de tests jusqu'à `e82f038a`
   manquaient alors. Le mandat ne permettait pas de réécrire les commits
   et les métadonnées Git hors de l'arbre. L'orchestrateur a depuis
   effectué ce rebase : `75498edd` est un ancêtre de `d3e815e7`.
   Le retard sur les commits ultérieurs relève du constat 1 de la passe 3.
5. **Bilan périmé : corrigé.** L'introduction et l'état de la passe 1 citent
   les commits `6ab9f8cf` et `7c94e52a`. Le bilan de l'époque annonçait
   seulement la passe 2 non commitée. Cet état a été remplacé ci-dessus
   par les commits effectivement reçus ; le test documentaire de passe 3
   contrôle aussi leur ascendance réelle.

### Rouges isolés avant les correctifs

Chaque sélection ci-dessous a été lancée seule avant sa correction.
Les cas hors sélection ne sont pas des tests ignorés de la porte finale.

| Constat | Test sélectionné | Ligne d'échec observée |
| --- | --- | --- |
| 1 | `AboutTab.identite.r1.test.tsx`, cas final `v0.83.0` | `TestingLibraryElementError: Unable to find role="alert"` |
| 2 | `RFCWizard.flux.r1.test.tsx`, `R2-2.*complète` | `Error: expect(element).toBeDisabled()` |
| 3 | `AboutTab.reessai.r1.test.tsx`, `partage la lecture` | `Error: expect(element).not.toBeInTheDocument()` |
| 4 | `/tmp/test_front_maj_r2_integration.py::test_l_integration_courante_est_un_ancetre_du_lot` | `AssertionError: c20/integration n'est pas un ancêtre de HEAD` |
| 5 | `frontMaj.bilan.r1.test.ts`, `R2-5` | ``AssertionError: expected '\n\nDépart vérifié : `f1087358`, arbr…' to contain '6ab9f8cf'`` |

Le rouge 1 est relevé dans la sortie du lancement isolé. Les journaux des
rouges 2 à 5 sont `/tmp/front-maj-r2-N-rouge.log`. Le contrôle local de Git
est jetable, hors suite produit : `/tmp/front-maj-r2-integration.xml`, lu,
**1 échec, 0 erreur, 0 ignoré** à cette date, avant le rebase sur `75498edd`.
Commande historique : `git merge-base --is-ancestor c20/integration HEAD`
(sortie alors observée : 1). Le contrôle de la nouvelle référence locale
est consigné séparément en passe 3.

### Appelants et tests voisins

Relus après chaque correction : `SettingsModal → AboutTab → useBackendStore`
et `checkHealth`, puis `HomeCommands → RFCWizard → RFCChat` et
`sourcesVerifiees`, jusqu'aux transitions vers Faire et Capturer.
Après R2-1 : **35 tests passés, 10 fichiers**. Après R2-2 : **37 tests passés,
15 fichiers** ; après R2-3 : **37 tests passés, 10 fichiers**. Rapports
`/tmp/front-maj-r2-{1,2,3}-vert.json`, lus.
Le premier lancement voisin RFC avait signalé deux attentes manquantes
dans les tests d'aide et de provenance ; les attentes portent maintenant
sur les mêmes assertions finales ou ajoutent la vérification du bouton
actif. Aucun test n'est désactivé.

### Portes de cette passe

| Porte | Résultat lu | Preuve |
| --- | --- | --- |
| Vitest ciblé, 3 workers au maximum | **115 passés, 0 échoué, 0 ignoré, 0 todo ; 28 fichiers passés**, sortie 0 | `/tmp/front-maj-r2-vitest.json` |
| TypeScript | **0 erreur**, sortie 0 | `/tmp/front-maj-r2-tsc.log`, vide |
| ESLint | **0 erreur, 27 avertissements**, sortie 0 | `/tmp/front-maj-r2-lint.log` |
| Pytest voisin updater | **16 passés, 0 échec, 0 erreur, 0 ignoré**, sortie 0 | `/tmp/front-maj-r2.xml`, XML lu |
| Ruff backend et tests | **0 diagnostic**, sortie 0 | `/tmp/front-maj-r2-ruff.log` : `All checks passed!` |
| Précondition de rebase, contrôle local distinct | **1 échec**, sortie 1 | `/tmp/front-maj-r2-integration.xml`, XML lu ; constat 4 ouvert |

Sept cas frontend ajoutés et plusieurs assertions existantes renforcées ou
adaptées au contrat corrigé. Le premier contrôle documentaire a signalé
l'absence du nom littéral `c20/integration` dans l'introduction ; le texte
a été précisé sans changer l'assertion, puis la sélection finale est passée.
Les comptes ne cumulent pas les rejeux. Aucune suite complète n'a été lancée,
aucun rouge connu n'a été sélectionné ou retranché, aucun lint ailleurs corrigé.

Commandes reproductibles :

```sh
# Depuis src/frontend ; outils installés, mode hors ligne, pas de cache partagé.
npx --offline --no-install vitest run src/components/settings/AboutTab src/components/ui/UpdateBanner src/components/rfc src/components/home/HomeCommands.assistantCommande.test.tsx src/components/home/HomeCommands.panneauGuide.test.tsx src/components/home/HomeCommands.cycle6.test.tsx src/hooks/useBackend.c9.test.ts src/test/frontMaj.annonces.r1.test.tsx src/test/frontMaj.bilan.r1.test.ts --configLoader runner --maxWorkers=3 --no-cache --reporter=json --outputFile=/tmp/front-maj-r2-vitest.json
npx --offline --no-install tsc --noEmit
npm run lint

# Depuis la racine ; données et cache jetables, sans bytecode partagé.
THERESE_DATA_DIR="$(mktemp -d /tmp/front-maj-r2-data.XXXXXX)" PYTHONDONTWRITEBYTECODE=1 OLLAMA_BASE_URL=http://127.0.0.1:9 .venv/bin/python -m pytest tests/test_b1111_manifeste_updater.py -q -p no:cacheprovider --timeout=120 --junitxml=/tmp/front-maj-r2.xml
RUFF_CACHE_DIR=/tmp/front-maj-r2-ruff-cache .venv/bin/python -m ruff check --no-fix src/backend tests
git merge-base --is-ancestor c20/integration HEAD
```

**VERDICT HISTORIQUE : NO-GO tant que le constat 4 restait ouvert.** Les
constats 1, 2, 3 et 5 étaient corrigés et leurs portes ciblées étaient vertes.
L'orchestrateur a ensuite intégré `75498edd` et commité cette passe.
Aucun commit ni ajout à l'index n'avait été fait par l'agent.

## Remédiation de la relecture, passe 3

État reçu le 17 novembre 2026 : HEAD `d3e815e7`, base commune avec
`c20/integration` : `75498edd`. La référence d'intégration locale vaut
`a498d9d3`. Les fichiers suivis étaient propres ; les deux liens de
dépendances non suivis étaient déjà présents. Les changements de cette
remise restent non commités, sans ajout à l'index.

### Constats et corrections

1. **Retard d'intégration confirmé, rebase restant à l'orchestrateur.**
   Le contrôle local d'ascendance échoue. Une simulation de la seule
   fonction `_kill_zombie_backends` extraite des sources Git confirme
   également le défaut : sans WMIC, le code de HEAD arrête le PID fictif
   `414` d'un `backend.exe` tiers ; le code de `c20/integration` l'épargne.
   Aucun processus Windows réel n'est interrogé ou arrêté. Le rebase
   réécrirait des commits et les métadonnées situées dans
   `Synoptia-THERESE/.git/worktrees/gpt-c20-front-maj`, hors de cet arbre,
   en lecture seule. Il n'a pas été exécuté, conformément au mandat.
   Aucun correctif Windows n'est recopié partiellement ; ce constat
   demeure ouvert et les deux rouges locaux ne sont pas masqués.
2. **Lecture de version bloquée corrigée.** `checkHealth` borne désormais
   toute la lecture à 30 secondes, corps JSON compris. L'expiration rejette
   la promesse partagée et annule la requête. Une réponse ou un rejet tardif
   ne peut plus changer le résultat expiré ni celui du nouvel essai.
   Trois cas traversent le vrai service API avec un `fetch` simulé : lecture
   au montage, lecture partagée avec le clic, résolution ou rejet tardif
   pendant le nouvel essai. Ils vérifient alerte, lien manuel, bouton actif,
   annulation, nouvelle requête et comparaison finale. Le délai des autres
   requêtes API, notamment des flux, conserve son contrat.
3. **Dérivées Ubuntu corrigées.** Le détecteur accepte les identifiants
   exacts `debian` et `ubuntu` dans `ID` ou `ID_LIKE`. Deux tests ajoutés
   couvrent `ID=pop / ID_LIKE=ubuntu` et Ubuntu sans `ID_LIKE`. Le test
   d'exclusion des sous-chaînes est renforcé avec `nonubuntu`. Le paquet
   `deb` et le système Linux restent exigés par l'appelant.
4. **Région live de capture corrigée.** Le même paragraphe `status` reste
   présent et accessible, vide lorsque Capturer devient actif, puis reçoit
   le message de préparation. Le test existant vérifie maintenant l'identité
   du nœud avant et après le clic, en conservant ses assertions sur le bouton,
   son aide et le formulaire final. La vérification porte sur le DOM ;
   aucune annonce avec un lecteur d'écran natif n'est revendiquée.
5. **Bilan actualisé.** L'introduction et la passe 2 distinguent les états
   historiques des commits livrés `fefd0e1d` et `d3e815e7`. Le test conserve
   les vérifications historiques de passe 1 et remplace l'exigence périmée
   « non commités » de passe 2 par les commits reçus, leur ascendance Git
   effective avec `75498edd` et le rattachement du travail actuel à la passe 3.

### Rouges isolés avant les correctifs

Les lignes ci-dessous sont recopiées des sorties observées. Les cas exclus
par `-t` ou `--exact` ne sont pas des tests ignorés de la porte finale.

| Constat | Test ou sélection isolée | Ligne d'échec observée |
| --- | --- | --- |
| 1 | `/tmp/test_front_maj_r3_integration.py` | `AssertionError: c20/integration n'est pas un ancêtre de HEAD` |
| 1, comportement Windows | `/tmp/test_front_maj_r3_windows.py`, cas `HEAD` | `AssertionError: Un backend.exe tiers a été arrêté` ; `assert ['414'] == []` |
| 2 | `AboutTab.delai.r3.test.tsx`, trois cas | `TestingLibraryElementError: Unable to find an accessible element with the role "alert"` |
| 3 | `linux_distribution.rs`, `tests::derivee_ubuntu_sans_identifiant_debian` | `assertion failed: est_debian_dans("ID=pop\nID_LIKE=ubuntu\n")` |
| 4 | `RFCWizard.capture.b1953.test.tsx`, `annonce la préparation` | `TestingLibraryElementError: Unable to find an accessible element with the role "status"` |
| 5 | `frontMaj.bilan.r1.test.ts`, `R3-5` | ``AssertionError: expected '# Cycle 20 : lot front-maj\n\nArbre :…' to contain 'État reçu pour la passe 3 : HEAD `d3e…'`` |

Journaux : `/tmp/front-maj-r3-{1,2,3,4,5}-rouge.log`, plus
`/tmp/front-maj-r3-1-windows-rouge.log`. Les XML des contrôles locaux Git et
Windows ont été lus : chacun a **1 échec, 0 erreur, 0 ignoré** sur HEAD.
Le même test Windows avec les sources de `c20/integration` a **1 succès**
(`/tmp/front-maj-r3-windows-integration.xml`, lu). Ces contrôles locaux
restent distincts de la suite produit et ne sont pas comptés comme verts.

### Appelants et tests voisins

Après chaque correctif, relecture de `SettingsModal → AboutTab → checkHealth`,
de `useBackend` et `useHealthCheck`, de `get_system_info → UpdateBanner`, puis
de `HomeCommands → RFCWizard → RFCChat / RFCCapture`. Les essais voisins ont
donné **76 succès dans 18 fichiers** pour la lecture de version, **10 succès
Rust et 39 succès dans 3 fichiers Vitest** pour les distributions, et
**37 succès dans 15 fichiers** pour la capture. Rapports JSON
`/tmp/front-maj-r3-{2,3,4}-vert.json` lus ; sortie Rust
`/tmp/front-maj-r3-3-vert.log` lue. Aucun test existant désactivé ou affaibli.

### Portes de cette passe

| Porte | Résultat lu | Preuve |
| --- | --- | --- |
| Vitest ciblé, au plus 3 workers | **156 passés, 0 échoué, 0 ignoré, 0 todo ; 37 fichiers passés**, sortie 0 | `/tmp/front-maj-r3-vitest.json` ; rejeu des 4 contrôles documentaires dans `/tmp/front-maj-r3-5-vert.json` |
| Rust, module de distribution seul | **10 passés, 0 échoué, 0 ignoré**, sortie 0 | `/tmp/front-maj-r3-3-vert.log` |
| Pytest voisin updater | **16 passés, 0 échec, 0 erreur, 0 ignoré**, sortie 0 | `/tmp/front-maj-r3.xml`, XML lu |
| Ruff backend et tests | **0 diagnostic**, sortie 0 | `/tmp/front-maj-r3-ruff.log` : `All checks passed!` |
| TypeScript | **0 erreur**, sortie 0 | `/tmp/front-maj-r3-tsc.log`, vide |
| ESLint | **0 erreur, 27 avertissements**, sortie 0 | `/tmp/front-maj-r3-lint.log` |
| Contrôles locaux du constat 1, distincts de la suite produit | **2 échecs sur HEAD**, 0 erreur ; **1 succès sur les sources d'intégration** | `/tmp/front-maj-r3-integration.xml`, `/tmp/front-maj-r3-windows-head.xml`, `/tmp/front-maj-r3-windows-integration.xml`, tous lus |

Les comptes ne cumulent pas les rejeux. Six nouveaux cas produit : trois
pour la lecture de version, deux pour les distributions, un pour le bilan.
Les assertions existantes de capture et d'exclusion des identifiants sont
renforcées. Le contrôle documentaire compare les ascendants de l'état reçu
`d3e815e7`, afin de rester valable après le rebase de l'orchestrateur.
Les rouges connus du mandat ne font pas partie de la sélection ; aucun
échec n'a été retranché des comptes.

Commandes reproductibles :

```sh
# Depuis src/frontend ; outils installés, aucun téléchargement ni cache partagé.
npx --offline --no-install vitest run src/components/settings/AboutTab src/components/ui/UpdateBanner src/components/rfc src/components/home/HomeCommands.assistantCommande.test.tsx src/components/home/HomeCommands.panneauGuide.test.tsx src/components/home/HomeCommands.cycle6.test.tsx src/hooks/useBackend.c9.test.ts src/hooks/useHealthCheck.test.ts src/services/api/core. src/services/api/authPrive.f2.test.ts src/services/api/config.timeouts.test.ts src/test/frontMaj.annonces.r1.test.tsx src/test/frontMaj.bilan.r1.test.ts --configLoader runner --maxWorkers=3 --no-cache --reporter=json --outputFile=/tmp/front-maj-r3-vitest.json
npx --offline --no-install tsc --noEmit
npm run lint

# Depuis la racine ; profils et caches jetables, aucun bytecode partagé.
THERESE_DATA_DIR="$(mktemp -d /tmp/front-maj-r3-data.XXXXXX)" PYTHONDONTWRITEBYTECODE=1 OLLAMA_BASE_URL=http://127.0.0.1:9 .venv/bin/python -m pytest tests/test_b1111_manifeste_updater.py -q -p no:cacheprovider --timeout=120 --junitxml=/tmp/front-maj-r3.xml
RUFF_CACHE_DIR=/tmp/front-maj-r3-ruff-cache .venv/bin/python -m ruff check --no-fix src/backend tests
/home/synoptia/.rustup/toolchains/stable-x86_64-unknown-linux-gnu/bin/rustc --edition=2021 --test src/frontend/src-tauri/src/linux_distribution.rs -o /tmp/front-maj-r3-distribution-tests
/tmp/front-maj-r3-distribution-tests
git merge-base --is-ancestor c20/integration HEAD
```

Le compilateur Rust installé a été appelé par son chemin absolu : `rustc`
n'était pas dans le PATH. La première erreur de commande n'est pas comptée
comme un rouge produit ; le test de dérivée Ubuntu a ensuite échoué avant
le changement du prédicat, puis les dix cas ont réussi.

Le constat 1 reste ouvert : les correctifs de cette passe ne valent pas
validation de l'intégration courante. Aucun réseau, fournisseur LLM, service
réel, accès au profil personnel ou aux ports interdits. Les données pytest
sont jetables, les appels frontend sont simulés. Aucune suite complète,
aucune correction de lint ailleurs, aucun commit ni ajout à l'index.

**VERDICT : NO-GO tant que le constat 1 reste ouvert.** Les constats 2 à 5
sont corrigés et leurs portes ciblées sont vertes. Le rebase sur
l'intégration courante et le rejeu de ses tests restent à l'orchestrateur.
