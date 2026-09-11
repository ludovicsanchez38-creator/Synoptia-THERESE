# DA « Application affinée », lot 5 : recette de Devis et factures (11/09/2026)

Design : `docs/plans/2026-09-11-da-lot5-devis-design.md` (rédigé par Grok,
NO-GO, NO-GO puis GO du contradicteur en v3). Code par Grok en worktree
(15 gardes rouges puis vertes), fusionné sur `main` en `618fd7fb` sans revue
ni recette : le solde Grok s'est épuisé pendant qu'il corrigeait la recette.
Revue adverse du diff par un relecteur Claude Opus le 11/09 au matin :
**NO-GO, 5 P2 et 7 P3, aucun P1** ; trois points contre-vérifiés par
l'orchestrateur (garde `h-9` qui exemptait tout bouton sans classe de hauteur,
bouton Client rendu vide sans client, `RangeError` d'`Intl.DateTimeFormat` sur
une date invalide). Douze reprises par un implémenteur Claude Opus en worktree,
en TDD (7 tests rouges d'abord, deux gardes vérifiées par sabotage), fusionnées
en `1baaaaa2`.

## Portes (main, après fusion)

vitest 2 139 / 2 139 (93 sur `components/invoices`) ; tsc 0 ; eslint 27
(plafond). Le test intermittent B-749 n'a pas rougi.

## Recette (pile jetable c6)

Script `src/frontend/scripts-recette/recette-da-lot5.mjs`, écrit par Grok,
réparé par l'orchestrateur (`057aa8ab`) : le glob `**/api/invoices**`
attrapait aussi le module Vite `/src/services/api/invoices.ts` et la coque ne
démarrait jamais ; les interceptions sont des prédicats sur `url.pathname`.
Seize cas, captures et `apres-mesures.json` dans
`.cartography-work/validation/da-lot5/` : liste de quatre pièces à 1280 px
(clair, sombre, contraste élevé, polices 14, 16, 18 px), 1024, 840, 800 px ;
focus sur la commande Client ; vide, vide filtré (échues, payées) ;
chargement ; erreur 500 avec Réessayer ; formulaire avec ligne 2 vide ;
profil émetteur incomplet.

| Mesure | Avant reprises | Après reprises |
|---|---|---|
| Textes sous 12 px | 0 | 0 |
| Interactifs sous 14 px (police 16) | 0 | 0 |
| Grand geste « Nouvelle facture » | 44 px | 44 px |
| Boutons PDF et Supprimer | 36 px | 36 px, séparés par un `gap-2` |
| Commande Client (bouton texte) | 20 px | 40 px (`min-h-9`) |
| Carte du tableau à 1280 | 1 176 px, `overflow-x-auto` | inchangé |
| Compteur | « 4 pièces, dont 1 pièce échue » | inchangé |

À police 14 px, `h-9` vaut 32 px et `text-sm` passe sous 14 px : effet du
`rem`, identique aux lots précédents, pas un défaut du lot.

## Écarts relevés

- Le cas « pièce sans client » n'est pas capturé (les quatre fixtures ont un
  client) ; il est couvert par les tests alignés (`getByRole('button',
  { name: 'FACT-2026-001' })`).
- Les champs date du formulaire s'affichent en `MM/DD/YYYY` en headless
  (locale du navigateur), hors lot.
