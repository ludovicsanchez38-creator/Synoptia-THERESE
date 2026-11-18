# Cycle 20 : vérification de clé, B-2057 et B-2058

Audit local du 18 novembre 2026, branche `c20/instable`, point de départ
`f0ea4e69`. Pour l'échec B-2057, le test lit avant la fin de la sauvegarde.
Sa correction est déjà intégrée dans `28261aba`. La relecture a aussi
reproduit le défaut produit préexistant B-2058, traité séparément ci-dessous.

## Cause confirmée

Dans `LLMStep.tsx`, `handleSaveApiKey` attend `api.setApiKey`, puis pose
`saved=true`, mémorise l'origine de la clé, arme l'effacement de `saved` à
3 000 ms et lance `void verifierLaCle(...)`. Cette dernière fonction pose
`verification.en_cours`, attend le fournisseur, puis remet `verification`
à `null` si la vérification est indisponible. Elle intercepte ce rejet.
Le texte « Clé API enregistrée » exige **`saved && !verification`**.

Dans le test original, `enregistrer()` attend seulement un `act` au chargement,
puis clique avec `fireEvent.click` sans attendre la promesse de sauvegarde
ni son rendu. Le cas indisponible enchaîne :

```tsx
await waitFor(() => expect(screen.queryByTestId('verification-cle')).toBeNull());
expect(screen.getByText('Clé API enregistrée')).toBeInTheDocument();
```

L'absence du verdict est vraie **avant** la sauvegarde, puis de nouveau après
le rejet de la vérification. `waitFor` peut donc réussir sur l'état initial.
L'assertion `getByText` suivante est synchrone : elle ne bénéficie d'aucun délai
pour attendre la sauvegarde. Il n'y a pas de `findByText` qui aurait expiré.
Testing Library installé utilise par défaut 1 000 ms pour `waitFor`/`findBy`,
un intervalle de 50 ms et un premier contrôle immédiat. Augmenter ce plafond
ne corrigerait pas l'absence déjà satisfaite.

Le rapport `/tmp/instable-b1348-echec.json` contient neuf cas, dont ce seul
échec sur `getByText`, et une entrée Framer Motion encore en cours
(`opacity: 0.23099`, `translateX(38.4505px)`). La transition du composant dure
300 ms et modifie son style ; elle ne diffère pas le montage de ses enfants.
`getByText` cherche dans le DOM indépendamment de cette opacité. Ce style ne
prouve donc pas un défaut d'animation : il accompagne ici une lecture trop tôt.
Autre dépendance au temps réel supprimée : le message transitoire peut expirer
à 3 s si le processus du test est retardé. Cette expiration n'explique pas à
elle seule la capture d'entrée fournie.

## Correction

Dans `LLMStep.verificationCle.b1348.test.tsx` :

- Le rendu initial et le clic de sauvegarde sont encadrés par `act` asynchrone.
  Le clic attend explicitement la promesse effectivement renvoyée par
  `setApiKey`, puis React termine le rendu et les réponses immédiatement
  résolues/rejetées des doublures du fournisseur.
- Les assertions lisent alors directement le verdict final ou le texte
  « Clé API enregistrée », puis contrôlent l'absence de verdict. Les états,
  rôles, message de refus et appel à `verifierCle('anthropic')` restent vérifiés.
- `vi.useFakeTimers()` remplace l'horloge réelle pour tout ce fichier.
  Le précédent existe dans le voisin `LLMStep.test.tsx`, notamment pour les
  délais et les réponses asynchrones. `cleanup` démonte avant le retour aux
  minuteries réelles. Aucun changement global de configuration ou d'animation.
- Un dixième test retient séparément sauvegarde et vérification : après
  **30 000 ms simulées**, le bouton reste désactivé et aucun succès/verdict
  n'est inventé ; après libération de la sauvegarde, le verdict est `en_cours` ;
  après **2 999 ms simulées**, le rejet produit le texte de succès et aucun
  verdict ; après **1 ms supplémentaire**, le retour transitoire s'efface et
  la mention permanente de la clé chiffrée reste affichée.

Aucun délai d'attente augmenté, aucun retry, aucune assertion de succès retirée,
aucun test sauté dans le fichier livré. Ce premier lot B-2057 ne modifiait
pas le composant ; la remédiation B-2058 le corrige ensuite.

## Tests voisins

Les huit autres cas du fichier original attendaient positivement le verdict
avec `findByTestId`, puis son `data-etat` avec `waitFor`. Ils ne confondaient
pas les deux absences, mais utilisaient toujours le plafond réel par défaut.
Ils sont maintenant synchronisés par le même `act` et la même horloge simulée.

La recherche a couvert les tests de `src/components/onboarding/` :

- `LLMStep.cleCollee.test.tsx` attend l'appel de sauvegarde, puis l'absence
  d'erreur de préfixe. Cela prouve la validation locale et l'argument transmis,
  pas la fin d'une sauvegarde. Il ne contrôle pas le retour transitoire de 3 s.
- `LLMStep.erreurCle.test.tsx` attend une alerte positive ;
  `LLMStep.origineCle.test.tsx` attend la sortie du chargement avant ses
  assertions d'absence, ou attend positivement l'origine. Ils n'ont pas cette
  même course sur une absence vraie avant et après sauvegarde.
- `LLMStep.plusTard.test.tsx:40` contient aussi un `waitFor` sur un appel
  **non** effectué. Cette attente peut réussir immédiatement et ne prouve
  jamais qu'un appel ne surviendra pas plus tard. Le composant actuel délègue
  ce geste à `onNext(null)` et n'appelle pas `clearLLMConfig` directement.
  Ce constat est documenté sans étendre le lot à ce contrat différent.
- `WorkingDirStep.c9.test.tsx` attend une disparition après avoir constaté
  positivement l'avertissement et l'appel de sauvegarde. L'absence n'est donc
  pas satisfaite sur l'écran initial, contrairement au cas B-2057.
- Plusieurs voisins (`localDabord`, `ramCompatible`, `cloudSeulCapable`,
  `ollamaCloud`, `sondeLente`, `cloudPromesse`, `erreurCle`, `cleCollee`)
  vidangent les promesses immédiatement résolues avec `act(Promise.resolve)`.
  Cela correspond à leurs doublures actuelles ; ce n'est pas une attente
  valable si ces doublures deviennent des réponses réellement différées.
  Le cas `catalogueLent.r6` contrôle déjà explicitement sa promesse différée.
- `ProfileStep.test.tsx` pilote aussi le temps ;
  `ProfileStep.nomVideVisible.test.tsx` attend encore 20 ms réelles pour
  écouter les rejets. Ce contrôle a une limite d'observation temporelle,
  mais ne constitue pas une reproduction de B-2057.

## Preuves reproductibles

Les comptes ci-dessous sont ceux de la campagne historique, vérifiés dans
`scratchpad/b2057/2026-11-17T23-26-55.166Z/comptes.json`. Ils ne proviennent
pas d'une nouvelle exécution de la recette après le commit `28261aba`.
Depuis ce commit, `HEAD` contient le test corrigé : il ne peut plus servir
de source « originale ». Les deux sources sont donc épinglées explicitement.

| Condition | Processus Vitest | Résultat |
| --- | ---: | --- |
| Original, sauvegarde retardée de 250 ms | 3 | 3 échecs du même `getByText`, 3 codes 1 |
| Corrigé, même sauvegarde retardée de 250 ms | 3 | 3 réussites, 3 codes 0 |
| Corrigé, fichier entier, sous charge CPU | 20 consécutifs | 200/200 tests réussis, 0 échec, 20 codes 0 |

Une première manipulation exploratoire identique avait déjà donné trois
échecs supplémentaires de l'original. Le tableau compte la campagne automatisée,
sans mélanger les deux séries : **6/6 échecs observés avant au total**.

La charge comporte huit processus Node indépendants qui calculent en boucle
pendant les vingt commandes `npx --no-install vitest run <fichier>`.
Leurs PID étaient 44958 à 44965. Leurs relevés `process.cpuUsage()` à l'arrêt
donnent environ 32,1 à 32,6 secondes CPU par processus. Les huit ont été
arrêtés et attendus à la fin de la campagne ; le lanceur a terminé en code 0.

Sources testées, rapports JSON, journaux, comptes par passage et temps CPU
sont conservés dans le répertoire local ignoré :
`scratchpad/b2057/2026-11-17T23-26-55.166Z/`.
La campagne complète dure quelques dizaines de secondes sur cette machine ;
ce résultat ne prouve pas toutes les charges possibles.

### Reproduction manuelle dans une copie temporaire

Aucune commande ci-dessous ne réécrit le test suivi. Depuis la racine du
dépôt, préparer une copie temporaire du frontend et réutiliser les dépendances
déjà installées, sans installation ni réseau :

```sh
repro_b2057=$(mktemp -d /tmp/therese-b2057.XXXXXX)
depot_b2057=$PWD
git archive 28261aba src/frontend | tar -x -C "$repro_b2057"
ln -s "$PWD/src/frontend/node_modules" "$repro_b2057/src/frontend/node_modules"
test_b2057=src/frontend/src/components/onboarding/LLMStep.verificationCle.b1348.test.tsx
git show "f0ea4e69:$test_b2057" > "$repro_b2057/$test_b2057"
```

Dans **cette copie temporaire**, ouvrir le test et ajouter l'import suivant :

```tsx
import { setTimeout as ralentirB2057 } from 'node:timers/promises';
```

Remplacer son unique `apiMocks.setApiKey.mockResolvedValue(undefined);` par :

```tsx
apiMocks.setApiKey.mockImplementation(() => ralentirB2057(250));
```

Depuis le frontend temporaire, exécuter manuellement trois fois la commande :

```sh
cd "$repro_b2057/src/frontend"
npm_config_offline=true npm_config_update_notifier=false npx --no-install vitest run src/components/onboarding/LLMStep.verificationCle.b1348.test.tsx -t 'indisponible'
```

Attendu : un échec `getByText('Clé API enregistrée')` et un code 1 à chaque
passage. Dans le même terminal, exporter le test corrigé dans le **même
fichier temporaire** en utilisant le chemin conservé vers le dépôt d'origine :

```sh
git -C "$depot_b2057" show "28261aba:$test_b2057" > "$repro_b2057/$test_b2057"
```

Réappliquer à la main les deux modifications de lenteur ci-dessus dans la
copie corrigée, puis relancer trois fois la même commande filtrée. Attendu :
un test réussi, aucun échec, code 0. Le délai injecté reste de **250 ms réelles**
dans les deux versions, y compris sous l'horloge simulée du test corrigé.
Il simule le serveur sans augmenter le délai d'attente des assertions.

Pour les vingt passages du fichier entier, réexporter la version `28261aba`
sans injection et retirer `-t 'indisponible'` de la commande. Relancer cette
commande vingt fois à la main et conserver chaque sortie avec son code.
La charge historique était constituée de huit processus de calcul : pour
refaire expressément cette condition, ouvrir huit terminaux séparés, lancer
dans chacun `node -e 'let n=1; for (;;) n=Math.sqrt(n+1)'`, puis arrêter
**chacun** avec Ctrl+C après les vingt passages. Ce choix reste manuel ;
aucune charge n'a été lancée pendant la remédiation de la relecture.
Sans cette charge, la répétition vérifie seulement les vingt passages normaux.

Les deux fichiers `original.tsx` et `corrige.tsx` de la campagne historique
restent également disponibles dans son dossier de preuves. La recette
`scripts/verifier_instabilite_b2057.mjs` est retirée du dépôt : elle réécrivait
un fichier suivi et lançait une charge CPU. Le déplacement vers `~/.Trash`+a été refusé par le bac à sable (`Operation not permitted`). Le fichier est
conservé hors du dépôt dans
`/tmp/therese-c20-b2057-retrait.9BDpVS/verifier_instabilite_b2057.mjs`.
Aucune suppression ni modification de l'index n'a été exécutée.

## Code 1 avec tous les tests verts

Vérifiés : `vitest.config.ts`, `vite.config.ts`, `src/test/setup.ts`, les
contrôles de transport dans `src/test/`, le journal fourni et l'implémentation
Vitest 4.0.17 installée localement. La configuration Vitest distincte est
utilisée ; aucun serveur de développement Vite n'est lancé.

- Pas de seuil de couverture dans le dépôt ; la couverture est désactivée
  par défaut et la commande `vitest run` ne l'active pas. Les trois reporters
  déclarés **dans `coverage`** ne l'activent pas non plus.
- Pas de hook global de fermeture dans cette configuration, ni surcharge de
  `teardownTimeout`, ni option ignorant les erreurs non interceptées.
  Le délai de fermeture installé vaut 10 s. Le code de fermeture peut signaler
  un dépassement ; aucune trace correspondante n'existe dans le journal fourni.
  Aucun défaut de fermeture n'a été reproduit dans les campagnes ici.
- Le setup bloque `fetch` par une promesse rejetée hors réseau, réinitialise
  le stockage de session et annule les écritures différées. Son contrôle
  `fetchHorsReseau.r4c.test.ts` passe avec les voisins. Le rejet de
  `verifierCle` dans le composant est intercepté. Aucun rejet applicatif
  responsable du code 1 nocturne n'a été identifié dans ce périmètre.
- Le reporter JSON installé calcule `success` et les compteurs depuis les
  suites/tests uniquement (`index.M8mOzt4Y.js`, `JsonReporter.onTestRunEnd`).
  Il ne reçoit pas les erreurs non interceptées dans son calcul.
  Par ailleurs, `_checkUnhandledErrors` dans `cli-api.Cx2DW4Bc.js` pose bien
  `process.exitCode=1` quand une telle erreur existe. Les deux états sont
  donc compatibles.

Diagnostic jetable, avec la configuration réelle et le reporter JSON :

| Injection diagnostique | Tests JSON | `success` JSON | Code |
| --- | --- | --- | ---: |
| `window.scrollTo` et `canvas.getContext`, non implémentés par jsdom | 1/1 réussi | true | 0 |
| `Promise.reject(...)` non intercepté dans `afterAll`, après le test | 1/1 réussi | true | 1 |
| Même rejet, reporters `default` et `json` ensemble | 1/1 réussi | true | 1 |

Le deuxième cas ne journalise que l'écriture du JSON avec `--reporter=json`.
Le troisième expose explicitement **1 Unhandled Rejection** dans le journal.
Fixtures et sorties conservées sous `scratchpad/b2057-diagnostic/`, hors de
la découverte des tests après diagnostic. Pour une prochaine occurrence :

```sh
npx --no-install vitest run --reporter=default --reporter=json --outputFile=<rapport.json>
```

**Limite : le mécanisme est vérifié, l'attribution de l'incident reste
inexpliquée.** Le journal `/tmp/instable-b1348-journal.log` contient des
messages jsdom et la confirmation d'écriture du JSON, sans trace de rejet
ni de dépassement de fermeture. Ce journal accompagne la reproduction avec
échec de test, pas une preuve complète de la première exécution tout verte.
Il ne permet pas de retrouver une pile absente. Aucune erreur n'est masquée,
aucun seuil n'est relâché et aucun correctif spéculatif de configuration
n'est livré.

## Portes du premier lot B-2057

Toutes les commandes utilisent les dépendances installées, avec
`npm_config_offline=true npm_config_update_notifier=false`, depuis `src/frontend`.

| Commande | Résultat |
| --- | --- |
| `npx --no-install vitest run src/components/onboarding src/test/fetchHorsReseau.r4c.test.ts --reporter=default --reporter=json --outputFile=../../scratchpad/b2057-portes/vitest.json` | 50 fichiers, 122/122 tests réussis, 0 erreur non interceptée rapportée, sortie 0 |
| `npx --no-install tsc --noEmit` | 0 erreur, sortie 0 |
| `npx --no-install eslint . --max-warnings 27` | 0 erreur, 27 avertissements, sortie 0 |

Journaux sous `scratchpad/b2057-portes/`. La suite complète de 4 313 tests
mentionnée dans le mandat n'a pas été relancée : la preuve livrée couvre le
fichier répété et ses voisins. Aucun réseau, serveur, port interdit ou profil
utilisateur utilisé. Aucun `git add`, commit ou suppression par `rm`.

## Remédiation de la relecture : B-2058

### Cause et correction produit

`handleSaveApiKey` capture bien le fournisseur A dans sa fermeture : la clé
était donc enregistrée sous A dans `apiKeys`. Mais `saving`, `saved`, le champ
de saisie, les erreurs et `verification` étaient des états uniques partagés.
Après sélection de B, la réponse de A posait encore `saved=true`, effaçait
la saisie de B et y affichait son verdict. Le calcul `hasApiKey || saved`
autorisait alors « Continuer » sous B sans clé B. Réinitialiser ces états
au changement de fournisseur ne protégeait pas contre une réponse ultérieure.

Ces états sont désormais rangés par fournisseur. Chaque sauvegarde crée une
demande numérotée, utilisée aussi par sa vérification, ses erreurs, son
`finally` et son minuteur. Une mise à jour n'est appliquée que si cette
demande est encore courante pour ce fournisseur. Le retour sur A retrouve
sa clé, son origine et son résultat, sans réutiliser ceux de B. Le bouton
« Continuer » exige la présence de la clé du fournisseur sélectionné ; le
message transitoire de sauvegarde n'accorde plus cette permission.

Un verrou synchrone par fournisseur empêche également Entrée de lancer une
seconde écriture pendant la première, ce que le bouton désactivé seul
n'empêchait pas. Les minuteurs sont indépendants entre fournisseurs et
annulés au démontage ; les demandes y sont invalidées avant toute réponse tardive.

### Rouge puis vert en horloge pilotée

Le nouveau fichier `LLMStep.changementFournisseur.b2058.test.tsx` utilise
`vi.useFakeTimers()`, des promesses différées libérées explicitement et
`act`, sans attente réelle. Exécuté avant toute modification du composant :
**11/11 tests rouges, sortie 1**. Après correction, les onze cas et les dix
tests B-1348 donnent **21/21 réussites, sortie 0**.

Un douzième cas a ensuite reproduit en rouge la sélection automatique
d'Ollama déclenchée par une nouvelle sonde pendant la configuration de A
(`rouge-sonde.json`, un échec, sortie 1). Le complément interdit cette sonde
pendant la configuration et protège aussi l'effet de sélection automatique.
Les **12/12 cas B-2058 sont verts** dans la porte finale, sans cas sauté.

Les douze cas couvrent :

- Sauvegarde A en attente pendant **30 000 ms simulées**, passage à B,
  résolution sous B : ni succès ni « Continuer » actif sous B, saisie B
  conservée ; retour A configuré, puis expiration du message à 3 000 ms.
- Vérification A acceptée, refusée ou rejetée après le passage à B : aucun
  verdict A sous B ; retour A avec sa propre origine et le résultat attendu.
- Échec de sauvegarde A et attente d'une sauvegarde B indépendante : aucune
  erreur A sous B et aucune fin de A qui désactive l'attente de B.
- Entrée pendant la sauvegarde : une seule écriture.
- Nouvelle clé A après rechargement du coffre, puis ancienne vérification
  acceptée ou rejetée : le nouveau verdict reste inchangé dans les deux cas.
- Configuration finale A réussie ou échouée : le fournisseur reste verrouillé
  jusqu'à la réponse ; en cas d'échec, l'édition redevient possible.
- Sonde Ollama pendant la configuration de A : aucune nouvelle sonde n'est
  lancée et le choix A reste conservé jusqu'à sa réponse.

Rapports et journaux du rouge, du vert ciblé et des portes :
`scratchpad/b2058-relecture/`.

### Autres opérations asynchrones du composant

- **Configuration finale (`setLLMConfig`) : concernée.** La sélection de B
  restait possible pendant l'enregistrement de A ; la réponse pouvait alors
  appeler `onNext(A)` ou afficher l'erreur A sous B. Le choix de fournisseur
  est désormais désactivé pendant `configuring` et le gestionnaire respecte
  aussi le verrou synchrone `configuringRef`. Les deux issues sont testées.
  Les boutons de sonde sont aussi désactivés pendant cette attente ;
  `loadState` et l'effet de sélection automatique respectent ce verrou.
- **Chargement global (`loadState`) : pas ce défaut d'attribution.** Les clés
  et origines sont déjà des tables par fournisseur, les sondes Ollama et RAM
  sont globales. `loadRequestRef` protège les rechargements concurrents et le
  démontage. Il ne transforme aucune réponse A en verdict du fournisseur B.
- **Catalogue : déjà protégé.** L'effet dépend du fournisseur et sa fermeture
  `annule` interdit à un ancien chargement de modifier le catalogue, le modèle
  ou l'indicateur d'attente après changement de fournisseur ou démontage.
- **Configurer plus tard : pas de résultat propre à A.** Le choix transmis
  est toujours `null` ; `configuringRef` sérialise déjà les clics pendant
  l'attente de `onNext(null)`. Le verrou du fournisseur couvre aussi ce délai.

### Portes après remédiation

Depuis `src/frontend`, dépendances installées uniquement, avec
`npm_config_offline=true npm_config_update_notifier=false` :

| Commande | Résultat final |
| --- | --- |
| `npx --no-install vitest run src/components/onboarding/ --reporter=default --reporter=json --outputFile=../../scratchpad/b2058-relecture/onboarding-final.json` | 50 fichiers, **132/132 tests réussis**, 0 échec, 0 test sauté, aucune erreur non interceptée rapportée, sortie 0 |
| `npx --no-install tsc --noEmit` | **0 erreur**, sortie 0 |
| `npx --no-install eslint . --max-warnings 27` | **0 erreur, 27 avertissements**, sortie 0 |

Journaux : `onboarding-final.log`, `tsc-final.log`, `eslint-final.log` dans
`scratchpad/b2058-relecture/`. Les deux sources B-2057 épinglées ont également
été comparées aux fichiers conservés de la campagne : contenu identique.
`git diff --check` passe ; l'index est inchangé. Aucun `git add`, commit,
serveur, profil utilisateur, accès réseau ou processus de charge CPU pendant
cette remédiation. La seule réserve d'exécution est la destination du fichier
retiré : `/tmp` a remplacé la Corbeille, inaccessible dans le bac à sable.
