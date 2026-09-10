# DA « Application affinée », lot 4 : recette de Contacts et pipeline (11/09/2026)

Design : `docs/plans/2026-09-11-da-lot4-contacts-design.md` (rédigé par Grok,
NO-GO puis GO du contradicteur en v2, 10 reprises appliquées avant le code).
Code par Grok en worktree (19 gardes rouges puis vertes), fusionné sur `main`
en `9626cd61`. Recette écrite et lancée par Grok
(`.cartography-work/validation/da-lot4/recette-da-lot4.mjs`, 23 captures,
`apres-mesures.json`), relue par l'orchestrateur sur la capture du pipeline.

## Portes (main, après fusion)

vitest 2 114 / 2 114 ; tsc 0 ; eslint 27 (plafond) ; e2e parcours-04 (CRM)
7 / 7 sur la pile Playwright.

## Recette (pile jetable c6)

La vue s'ouvre par `window.__therese.runAction('crm.open' | 'memory.open')`
(le paramètre `?view=` est avalé au remontage en Strict Mode : à noter pour les
recettes suivantes). États : pipeline avec quatre contacts, pipeline vide,
fiche contact, erreur 500 ; 1280 px en clair, sombre, contraste élevé ; 1024,
840, 800 px ; focus clavier.

| Mesure | Résultat |
|---|---|
| Textes sous 12 px | 0 |
| Boutons d'action (Importer, Nouveau contact, Ajouter une activité, Exporter) | 36 px |
| Onglets et périmètre (segments, `classeSegment`) | 28 px (exemption du socle) |
| Colonnes du pipeline | 240 px (15 rem), sept colonnes, défilement horizontal 1 752 / 1 176 px à 1280 |
| Fiche contact | 1 176 px |
| Chevauchements | 0 |

## Écarts relevés

- Le repli des actions de tête (`max-[840px]:basis-full`) ne joue qu'en
  dessous de 840 px : à 840 exactement les actions restent à droite. Conforme
  à la règle du socle (même seuil que la barre du lot 1).
- Les icônes des boutons « Importer (.vcf) » et « Nouveau contact » sont
  collées au texte (pas d'espace entre l'icône et le libellé) : P3 à reprendre
  avec la revue du diff.
- Sur la fiche, le bouton « Ajouter » des prestations fait 32 px et le champ
  Intitulé est tronqué : composants hors du lot (`ListeDesPrestations`), à
  traiter au lot des couches.
- La cinquième colonne (Livraison) est coupée par le bord du cadre à toutes
  les largeurs : c'est le défilement horizontal du design, pas un débordement.
