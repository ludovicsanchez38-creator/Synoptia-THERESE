# Cycle 20 : serveur de développement Vite

## B-2054

**Cause confirmée dans l’arbre reçu.** Les entrées explicites
`['index.html', 'src/**/*.{ts,tsx}']` sélectionnent aussi les tests.
`src/frontend/src/App.lienEvitement.b1915.test.tsx` importe
`@tailwindcss/oxide` et `lightningcss`, outils natifs Node inadaptés à
l’optimisation navigateur. Ce test et sa preuve restent inchangés.

**Rouge constaté avant le correctif.** Le nouveau test
`src/frontend/src/test/viteOptimizeDeps.b2054.test.ts` charge l’export réel
de `vite.config.ts` pour `command: 'serve'`, dans un processus Node séparé
de jsdom. Il résout les motifs avec le moteur `tinyglobby` installé pour
Vite, contre les fichiers réels de l’arbre. Résultat : 1 échec, 1 succès.
Ligne copiée de Vitest :

```text
AssertionError: B-2054 : 1007 fichier(s) de test dans optimizeDeps.entries (ex. src/App.demarrageAccords.test.tsx, src/App.lienEvitement.b1915.test.tsx, src/OnboardingRafraichitLeProfil.test.tsx): expected 1007 to be +0 // Object.is equality
```

**Correctif.** Ajout des exclusions `!src/**/*.{test,spec}.{ts,tsx}`,
`!src/**/__tests__/**` et `!src/test/**` dans `optimizeDeps.entries`.
La règle du test couvre ces catégories pour tout fichier présent ou ajouté
ultérieurement. Son second cas conserve `index.html` et toutes les sources
applicatives TypeScript, y compris celles chargées en lazy. Aucune option
du build n’est modifiée.

**Vérification des imports hors tests.** Analyse syntaxique TypeScript des
imports, réexports, `import()` et `require()` dans les 399 fichiers
`src/**/*.{ts,tsx,js,jsx}` hors tests. Aucun import calculé, module natif
Node, module intégré Node, Oxide ou Lightning CSS relevé. Les imports externes
restants sont des bibliothèques frontend et les ponts JavaScript Tauri.
Aucun défaut supplémentaire identifié dans ce périmètre.

**Portes après correctif**, depuis `src/frontend`, avec
`npm_config_offline=true npm_config_update_notifier=false` et `--no-install` :

| Commande | Résultat |
| --- | --- |
| `npx --no-install vitest run src/test/viteOptimizeDeps.b2054.test.ts src/test/viteSecrets.c19.test.ts src/test/envExample.test.ts` | 3 fichiers, 15 tests réussis, 0 échec, sortie 0 |
| `npx --no-install tsc --noEmit` | 0 erreur, sortie 0 |
| `npx --no-install eslint . --max-warnings 27` | 0 erreur, 27 avertissements, sortie 0 |

**Limite.** Le test prouve la sélection des entrées, pas l’exécution de
l’optimiseur ni la stabilité du serveur. Il ne parcourt pas les dépendances
transitives des paquets et ne prouve pas les parcours Playwright ou le build.
La tenue réelle du serveur sera vérifiée par l’orchestrateur. Aucun serveur,
port, réseau, fournisseur de modèles ou profil `~/.therese` utilisé ici.
Changements laissés non indexés et non commités sur `c20/vite-dev`.
