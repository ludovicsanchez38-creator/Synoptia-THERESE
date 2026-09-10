# DA « Application affinée », lot 2 : recette de l'écran Accueil (11/09/2026)

Design : `docs/plans/2026-09-10-da-lot2-accueil-design.md` (GO Grok en v6 après six
revues). Pile jetable c6 (uvicorn 17393, Vite 1420, jamais 17293), six états du
brief forcés par interception Playwright de `/api/dashboard/today` et
`/api/dashboard/setup-status` (`.cartography-work/validation/da-lot2/recette-da-lot2.mjs`),
22 captures avant et 22 après, mesures `avant-mesures.json` / `apres-mesures.json`
(dossier ignoré par git).

## Avant / après (1280 px, clair, 16 px, état normal)

| Mesure | Avant | Après |
|---|---|---|
| h1 | "Plus Jakarta Sans", Int 800 | "Plus Jakarta Sans", Int 800 (`font-editorial`) |
| Titre de la carte | Ton attention aujourd’hui | Ton attention aujourd’hui |
| Ligne « THÉRÈSE · heure » | oui | non (ligne du jour : date, sources, « Rafraîchi à ») |
| Ombre de la carte | rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) | rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) (`shadow-sm`) |
| Boutons de tête | [('Ouvrir Agenda', 34), ('Relancer Clair', 67)] | [('Ouvrir Agenda', 36), ('Commencer : Re', 36)] (36 px) |
| Textes sous 12 px dans la carte | 0 | 0 |

## Les états, après

| Cas | Titre de tête | Réessayer | < 12 px | ligne THÉRÈSE | largeur carte |
|---|---|---|---|---|---|
| normal-1280-light-16px | Ton attention aujourd’hui | 0 | 0 | non | 896 |
| normal-1280-dark-16px | Ton attention aujourd’hui | 0 | 0 | non | 896 |
| normal-1280-hc-16px | Ton attention aujourd’hui | 0 | 0 | non | 896 |
| normal-1024-light-16px | Ton attention aujourd’hui | 0 | 0 | non | 896 |
| normal-840-light-16px | Ton attention aujourd’hui | 0 | 0 | non | 720 |
| normal-800-light-16px | Ton attention aujourd’hui | 0 | 0 | non | 680 |
| normal-1280-light-14px | Ton attention aujourd’hui | 0 | 0 | non | 784 |
| normal-1280-light-18px | Ton attention aujourd’hui | 0 | 0 | non | 1008 |
| vide-1280-light-16px | Rien ne presse aujourd’hui | 0 | 0 | non | 896 |
| vide-1280-dark-16px | Rien ne presse aujourd’hui | 0 | 0 | non | 896 |
| agenda-indisponible-1280-light-16px | Ton attention aujourd’hui | 1 | 0 | non | 896 |
| agenda-indisponible-1280-dark-16px | Ton attention aujourd’hui | 1 | 0 | non | 896 |
| agenda-indisponible-vide-1280-light-16px | Ta journée | 1 | 0 | non | 896 |
| agenda-indisponible-vide-1280-dark-16px | Ta journée | 1 | 0 | non | 896 |
| panne-1280-light-16px | Ta journée | 1 | 0 | non | 896 |
| panne-1280-dark-16px | Ta journée | 1 | 0 | non | 896 |
| sans-messagerie-1280-light-16px | Ta journée | 0 | 0 | non | 896 |
| sans-messagerie-1280-dark-16px | Ta journée | 0 | 0 | non | 896 |
| chargement-1280-light-16px | Ta journée | 0 | 0 | non | 896 |
| chargement-1280-dark-16px | Ta journée | 0 | 0 | non | 896 |
| agenda-indisponible-800-light-16px | Ton attention aujourd’hui | 1 | 0 | non | 680 |

Lecture : un seul « Réessayer » sur agenda indisponible (avec liste et sans
liste) et sur la panne totale, zéro ailleurs ; « Rien ne presse aujourd'hui »
réservé au vide constaté ; « Ta journée » en chargement, panne, sans messagerie ;
aucun texte sous 12 px ; la ligne « THÉRÈSE · heure » a disparu du brief.

## Défaut trouvé et corrigé

À 800 px, état agenda indisponible : l'étiquette « À traiter » de la dernière
ligne, repliée sous le composeur, se dessinait PAR-DESSUS lui. Cause : la
`Ligne` du lot 1 pose `relative z-10` sur sa zone droite (pour laisser les vrais
interactifs au-dessus du bouton étiré) et le fond du composeur n'avait aucun
plan. Correctif : `z-20` sur `prototype-composer-backdrop`, garde rouge puis
verte dans `ConversationCanvasPrototype.da.test.tsx`, sonde
`sonde-chevauchement.mjs` (`elementFromPoint` sur chaque étiquette sous le
composeur) : zéro faute, capture `apres2-agenda-indisponible-800-light-16px.png`.

Second point : `rounded-none` sur le bouton de repli hors du jeu de rayons
(garde `rayons.test.ts`) : retiré.

## Portes

- vitest 2 077 verts (json), tsc 0, eslint 27 avertissements (plafond), e2e
  B-320 (le composeur ne recouvre rien) vert sur la pile Playwright.
- pytest, ruff, mypy : backend non touché par le lot ; la CI de `main` les
  rejoue.

## Réserves

- Le geste principal écrit le titre entier de la première ligne (« Commencer :
  Relancer Claire Roux pour la facture de juillet ») : long à 1280 px, sur une
  ligne entière à 800 px. C'est le choix du design (§ 2.2, pas de troncature) ;
  à revoir si Ludo le trouve lourd.
- L'indicateur « Voir la suite » (B-562) chevauche le pied « Lu dans » quand la
  carte dépasse la fenêtre : comportement antérieur au lot, hors périmètre.
- Les états `relance` et `validee` de la maquette : P-067 au portail humain.
