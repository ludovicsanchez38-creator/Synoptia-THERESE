# Tests de bout en bout

**La suite vivante est `stories/`**, en TypeScript, lancee par Playwright.

```bash
npm run test:e2e          # les 196 tests (desktop + mobile)
npx playwright test --project=desktop   # les 98 tests reellement mesurables ici
make test-e2e-api         # les 30 contrats d API seulement, ~15 s
```

`playwright.config.ts` lance lui-meme ses DEUX serveurs : un backend jetable
sur un port dedie avec un `THERESE_DATA_DIR` temporaire detruit a la fin, et
un Vite qui vise ce backend. `reuseExistingServer` est a `false` pour ne jamais
retomber sur l instance reelle (17293).

## La suite Python a ete retiree le 01/09/2026

Vingt modules, cent vingt-cinq tests, dernier changement fonctionnel en fevrier.
Deux raisons, pas une :

1. **Elle etait dangereuse.** Elle lancait un backend jetable sur le port 8000
   puis naviguait vers un frontend sur 1420 qu elle ne lancait PAS — or un
   frontend ouvert a la main vise 17293 par defaut. Ses tests creent et
   suppriment contacts, factures et taches : `make test-e2e` avec un `make dev`
   ouvert ecrivait dans les vraies donnees. La suite TypeScript s etait donne
   cette garde des la revue 0.40 ; celle-ci ne l a jamais eue.

2. **Elle faisait double emploi.** Meme perimetre que `stories/`, meme
   dependance a une interface qui a change. Les reparer, c etait faire deux
   fois le meme travail.

Elles restent dans l historique git (`git log -- tests/e2e/test_*.py`) si un
scenario particulier devait etre repris.

## État des parcours TypeScript (mesuré le 02/09/2026)

`npx playwright test --project=desktop` : **97 passés, 0 échec, 1 `fixme`**
sur 98. Les trente tests d'API passent et tournent en CI (`tests-e2e.yml`,
qui ne lance encore qu'eux) ; les soixante-huit parcours
d'interface ont été réécrits pour la coque conversationnelle les 01 et
02/09/2026. Le projet `desktop` est donc prêt à être branché en CI, où
chromium est déjà installé.

Le seul test rouge est déclaré : `parcours-04`, « Échap ferme le formulaire de
contact sans éjecter le panneau CRM », marqué `fixme` parce qu'il constate un
défaut de l'application (`CreateContactModal` n'utilise pas
`lib/escapeStack.ts`) et non du test.

Une instabilité reste, qui n'appartient ni aux tests ni à l'application :
**le serveur Vite de développement recharge parfois la page en pleine
exécution**, et le parcours qui avait une surface ouverte à cet instant tombe.
Mesuré à environ 3 % (un échec sur trente-six à `--repeat-each=6`), trace
sans ambiguïté dans le journal Playwright (« navigated to
http://localhost:1420/ … element was detached from the DOM »), et aucun
`window.location.reload()` de l'application ne se déclenche sans clic. La
cause tient aux neuf surfaces chargées en `lazy()`
(`PrototypeUnifiedViewCanvas.tsx`) : leurs dépendances, @dnd-kit en tête, sont
découvertes au vol par l'optimiseur de Vite, qui recharge alors tous les
clients connectés. `src/frontend/vite.config.ts` ne déclare aucun
`optimizeDeps` ; les y déclarer fermerait la porte. En attendant, la CI
l'absorbe (`retries: process.env.CI ? 2 : 0`) et une relance locale du seul
parcours concerné suffit.

`--project=mobile` n'est PAS mesurable sur un poste sans WebKit : `devices
['iPhone 13']` est un profil WebKit, et les soixante-huit parcours y échouent
sur « Executable doesn't exist … /webkit-2248/pw_run.sh ». Seuls les trente
tests d'API y tournent, puisqu'ils n'ouvrent aucun navigateur. La CI n'installe
que chromium (`npx playwright install --with-deps chromium`) : y étendre
`npx playwright test` sans projet nommé ferait donc échouer tout le volet
mobile.
