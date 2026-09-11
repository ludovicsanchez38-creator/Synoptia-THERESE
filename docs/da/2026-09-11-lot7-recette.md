# DA « Application affinée », lot 7 : recette de Décision (11/09/2026)

Design : `docs/plans/2026-09-11-da-lot7-decision-design.md` (rédigé par Grok,
trois revues Grok puis trois revues Claude Opus jusqu'au GO en v6 ; v7 et v8
par l'implémenteur). Code par un implémenteur Claude Opus en worktree
(38 gardes, 33 rouges d'abord), extension de la primitive `Ligne`
(`coupe?: boolean`, défaut faux). Revue adverse du diff par un relecteur
Claude Opus : **NO-GO, un P1 sur le script de recette (un glob qui n'attrapait
pas l'URL de détail), trois P2, huit P3** ; huit points repris
(conteneur teinté de la progression rétabli, `aria-hidden` sur six glyphes,
`mt-2` orphelin retiré, garde du plancher étendue à six montages), fusionné
sur `main` en `11b956ca` après un rebase (conflit résolu sur la garde des
couleurs, qui balaie désormais les lots 6 et 7).

## Portes (main, après fusion)

vitest 2 182 / 2 182 dans le worktree ; 244 sur le périmètre (prototype,
ui, tasks, memory) rejoués sur `main` ; tsc 0 ; eslint 27 (plafond).

## Recette (pile jetable c6)

Script `src/frontend/scripts-recette/recette-da-lot7.mjs` (interceptions par
prédicat sur le chemin, ouverture par le scénario `board` de la coque, route
`onboarding-complete` servie). Vingt-deux cas, captures et `mesures.json`
dans `.cartography-work/validation/da-lot7/` : historique de cinq décisions
et détail à 1280 (clair, sombre, contraste élevé, polices 14, 16, 18 px),
1024, 840, 800 ; en cours, en cours avec recherche web ; partiel, partiel avec
texte ; annulation ; formulaire ; détail pendant un run ; historique vide ;
panne ; chargement ; clic sur la puce ; focus d'une rangée.

| Mesure | Résultat |
|---|---|
| Textes sous 12 px (carte et détail) | 0 sur tous les cas |
| Interactifs sous 14 px (police 16) | 0 |
| Boutons (Nouvelle question, Ouvrir Décision, Annuler la délibération, Confirmer, Réessayer, Convoquer) | 36 px |
| Cartes de mode du formulaire | 108 px |
| Rangées de l'historique (`Ligne coupe`) | bouton texte 21 px, cible étirée à la rangée par le pseudo-élément (motif du lot 2) |
| Carte d'historique | 634 px canevas ouvert à 1280, 896 px fermé ; `overflow: hidden` |
| Panneau de décision | 526 px à 1280, 620 px en dessous |
| Clic sur la puce d'une rangée | ouvre le détail |

À police 14 px, `h-9` vaut 32 px : effet du `rem`, identique aux lots
précédents.

## Écarts relevés

- Canevas ouvert à 1280, le titre d'une rangée d'historique est coupé après
  une vingtaine de caractères : la colonne `auto` (date, mode, étiquette,
  chevron) prend la place. Lisible, mais à reconsidérer (masquer le mode sous
  une largeur, ou passer l'étiquette sous le titre). P3, point 7 de la revue.
- L'étiquette « Consensus moyen / faible » est en ton neutre `bg-surface-2`,
  la même teinte que le survol de la rangée : au survol la pilule se fond.
  P3, point 8 de la revue, à trancher au design.
- Sous un run en erreur à cinq avis rendus, la meta lit « Délibération
  partielle · 5 avis rendus · … · 5 conseillers » : assumé par le design
  (§ 3.1), à rouvrir si la phrase gêne.
- `CLASSE_BOUTON_VUE` est recopiée de l'Accueil : dette inscrite au § Reste.
