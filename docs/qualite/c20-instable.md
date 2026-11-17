# Cycle 20 : instabilité de la vérification de clé, B-2057

Audit local du 18 novembre 2026, branche `c20/instable`, point de départ
`f0ea4e69`. Aucun défaut du composant établi pour cet échec : le test lit
avant la fin de la sauvegarde. Le correctif porte sur le test et sa recette.

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
aucun test sauté dans le fichier livré. Le composant reste inchangé.

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

Depuis la racine :

```sh
node scripts/verifier_instabilite_b2057.mjs
```

Le script lit l'original depuis Git sans modifier l'index, conserve l'état
corrigé présent, injecte **la même** promesse de sauvegarde retardée de
250 ms réelles avec `node:timers/promises` dans les deux versions, puis
restaure le fichier dans un `finally`. Ce délai représente la réponse lente
du serveur ; il n'augmente aucun délai d'attente du test. L'horloge Node de
l'injection reste réelle même quand les minuteries du test sont simulées.
Les exécutions filtrées ciblent uniquement le cas indisponible pour comparer
la même assertion. La campagne sous charge exécute le fichier entier sans filtre.

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
arrêtés et attendus par le script ; le lanceur a terminé en code 0.

Sources testées, rapports JSON, journaux, comptes par passage et temps CPU
sont conservés dans le répertoire local ignoré :
`scratchpad/b2057/2026-11-17T23-26-55.166Z/`.
La campagne complète dure quelques dizaines de secondes sur cette machine ;
ce résultat ne prouve pas toutes les charges possibles.

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

## Portes finales

Toutes les commandes utilisent les dépendances installées, avec
`npm_config_offline=true npm_config_update_notifier=false`, depuis `src/frontend`.

| Commande | Résultat |
| --- | --- |
| `npx --no-install vitest run src/components/onboarding src/test/fetchHorsReseau.r4c.test.ts --reporter=default --reporter=json --outputFile=../../scratchpad/b2057-portes/vitest.json` | 50 fichiers, 122/122 tests réussis, 0 erreur non interceptée rapportée, sortie 0 |
| `npx --no-install tsc --noEmit` | 0 erreur, sortie 0 |
| `npx --no-install eslint . --max-warnings 27` | 0 erreur, 27 avertissements, sortie 0 |
| `node --check scripts/verifier_instabilite_b2057.mjs` depuis la racine | sortie 0 |

Journaux sous `scratchpad/b2057-portes/`. La suite complète de 4 313 tests
mentionnée dans le mandat n'a pas été relancée : la preuve livrée couvre le
fichier répété et ses voisins. Aucun réseau, serveur, port interdit ou profil
utilisateur utilisé. Aucun `git add`, commit ou suppression par `rm`.
