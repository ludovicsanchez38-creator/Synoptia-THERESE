# DA « Application affinée », lot 3 : recette du tiroir et du catalogue (11/09/2026)

Design : `docs/plans/2026-09-11-da-lot3-tiroir-design.md` (rédigé par Grok,
GO du contradicteur en v1, 14 reprises P2/P3 appliquées avant le code). Code
par Grok en worktree (`grok/da-lot3-tiroir`, trois commits : reprises du
design, 17 gardes rouges, implémentation), fusionné sur `main` en `5b03e707`.

## Portes (main, après fusion)

- vitest 2 094 / 2 095 : le seul rouge, `PromptLibrary.cycle6` « sophie-02 »,
  est hors du lot et passe seul deux fois de suite (intermittent sous la suite
  complète, candidat B-749) ; tsc 0 ; eslint 27 (plafond) ; e2e parcours-08
  (capacités) 14 / 14 sur la pile Playwright.

## Recette visuelle (pile jetable c6, 17393 et 1420)

Script `.cartography-work/validation/da-lot3/recette-da-lot3.mjs`, 21 captures
`apres-*` (tiroir vide, tiroir, catalogue ; 1280 px en clair, sombre et
contraste élevé ; 1024, 840 et 800 px en clair ; focus clavier à 1280),
mesures `apres-mesures.json`.

| Surface | Largeur | Fond | Titre | Textes < 12 px | Interactifs < 14 px | Premier focus |
|---|---|---|---|---|---|---|
| Tiroir (1280) | 352 px (22 rem) | surface | Conversations | 0 | aucun | champ de recherche |
| Tiroir (800) | 352 px | surface | Conversations | 0 | aucun | champ de recherche |
| Catalogue (1280) | 1 120 px | surface | Capacités | 0 | aucun | champ de recherche |
| Catalogue (800) | 760 px | surface | Capacités | 0 | aucun | champ de recherche |

Lecture des captures : tiroir à 22 rem en surface bordée, titre `h2`, champ de
recherche du socle, état vide en `EtatVide`, « Nouvelle conversation » en
bouton principal plein ; catalogue titré « Capacités » avec le compte
(« 30 capacités » calculé), six groupes à gauche avec le nom long et le compte,
cartes pleine largeur en grille de deux, étiquette de type (Parcours, Vue,
Action) en 12 px non cliquable, pied de légende.

## Réserves

- Le tiroir AVEC conversations n'a pas été capturé : la liste vient du store
  de conversations, pas d'une route interceptable, et la pile jetable n'a
  aucune conversation. À capturer sur des données de démonstration lors de la
  recette globale avant la release.
- Les portraits du catalogue (Board, agents) sont retirés au profit des
  pastilles de domaine : plancher `PrototypeThemeContract` abaissé de 12 à 10
  (choix du design § 3, cohérent avec la maquette).
- P-068 (un seul tiroir à onglets), P-069 (six intentions), P-070 (genre et
  aperçu) au portail humain.
