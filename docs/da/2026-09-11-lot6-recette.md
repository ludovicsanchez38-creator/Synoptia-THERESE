# DA « Application affinée », lot 6 : recette de Projets et tâches (11/09/2026)

Design : `docs/plans/2026-09-11-da-lot6-projets-design.md` (rédigé par Grok,
quatre revues jusqu'au GO ; cinq points restants repris en v5 par
l'implémenteur). Code par un implémenteur Claude Opus en worktree (48 gardes,
28 rouges d'abord), revue adverse du diff par un relecteur Claude Opus :
**GO, cinq P2 et sept P3**, dix repris (`b81843ce`), deux fichés comme bugs
préexistants hors DA : B-750 (dnd-kit : Entrée sur une commande révélée au
focus démarre un glisser) et B-751 (masque du mode démo absent des
`aria-label` de la liste, corrigé dans les reprises). B-752 fiché en passant
(kanban projets sans masque de démo).

## Portes (main, après fusion)

vitest 2 179 / 2 179 (192 sur le périmètre tasks, memory, ui, lot6DA) ;
tsc 0 ; eslint 27 (plafond).

## Recette (pile jetable c6)

Script `src/frontend/scripts-recette/recette-da-lot6.mjs`, écrit par
l'implémenteur, réparé par l'orchestrateur (`6a9e924b`) : interceptions
ancrées sur le chemin `/api` (le glob attrapait un module Vite, comme au
lot 5), segments ciblés dans leur groupe nommé, actions `projects.open` et
`tasks.open`, sonde B-750 en vue Colonnes. Vingt-quatre cas, captures et
`apres-mesures.json` dans `.cartography-work/validation/da-lot6/` : kanban
cinq tâches à 1280 (clair, sombre, contraste élevé, polices 14, 16, 18 px),
1024, 840, 800 ; liste à 1280 clair et sombre, 800 ; focus segment et carte ;
vide ; titre manquant ; panne ; projets trois, zéro, deux cents, 800, panne,
chargement lent ; glisser ; Entrée sur une commande.

| Mesure | Résultat |
|---|---|
| Textes sous 12 px | 0 sur tous les cas |
| Interactifs sous 14 px (police 16) | 0 |
| Boutons (Filtrer, Rafraîchir, Nouvelle tâche, Marquer, Supprimer, Nouveau projet, Réessayer) | 36 px |
| Boutons texte « Ouvrir la tâche » et nom du projet | 21 et 20 px, puis 36 px après `1ffded8a` |
| Segments (primitive `Segments`) | 28 px, exemption du socle |
| Colonnes du kanban | 3 à 1280 et 1024, 2 à 840 et 800 (deux rangées) |
| Listes défilantes de colonne | 3 |
| Anneau de focus (segment, carte) | 3 px solid |
| Titre manquant | « Ajoute un titre : c'est la seule chose obligatoire. », champ `aria-invalid`, aucun bandeau |
| Glisser | seuil 8 px tenu |

À police 14 px, `h-9` vaut 32 px et `text-sm` passe sous 14 px : effet du
`rem`, identique aux lots précédents.

## Écarts relevés

- **B-750 confirmé par la recette** : Entrée sur « Marquer terminé » révélé
  au focus ne produit aucune requête, le titre apparaît deux fois (calque de
  glisser) et le focus tombe sur `body`. Préexistant, hors DA, à réparer en
  REPAIR (`setActivatorNodeRef` sur les deux enveloppes sortables).
- Le bouton « Revenir à la conversation » de la coque mesure 32 px : il
  appartient au lot 1, pas à celui-ci ; à reprendre avec la coque.
- L'annonce du chargement lent des projets est lue vide par la sonde
  (`[role="status"]` premier trouvé) : limite de l'instrument, à préciser
  avant d'en faire un constat.
- Deux phrases du design restent fausses et ne seront pas réécrites (document
  validé) : § 3 « le `p-2` de la colonne suffit » et § 6 « la colonne de la
  coque, 56 rem, suffit ».
