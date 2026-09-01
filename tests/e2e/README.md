# Tests de bout en bout

**La suite vivante est `stories/`**, en TypeScript, lancee par Playwright.

```bash
npm run test:e2e          # les 96 parcours (desktop + mobile)
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

## Etat des parcours TypeScript

Les trente tests d API passent et tournent en CI (`tests-e2e.yml`). Les
soixante-cinq parcours d interface sont en cours de reecriture pour la coque
conversationnelle : ils attendaient des surfaces que l ecran par defaut ne
monte plus.
