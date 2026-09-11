# DA « Application affinée », lot 8 : recette de l'Agenda (11/09/2026)

Design : `docs/plans/2026-09-11-da-lot8-agenda-design.md` (rédigé par Grok,
deux revues Grok puis trois revues Claude Opus jusqu'au GO en v5 ; v6 et v7
par l'implémenteur). Branche « le formulaire remplace la grille » (le
comportement actuel) : le panneau latéral de la maquette reste une décision
de Ludo, à porter par-dessus. Code par un implémenteur Claude Opus en
worktree (67 gardes, 55 rouges d'abord). Revue adverse du diff par un
relecteur Claude Opus : **NO-GO, deux P1 (cases du Mois qui débordent sur la
semaine suivante à 640 px de haut ; recette non jouée), un P2, huit P3** ;
neuf points repris (`grid-rows-[max-content_repeat(6,auto)]` et
`min-h-[5.5rem]` sur la case, comme la maquette ; « Toute la journée » du
Jour en `text-sm` ; repli à `max-[840px]` ; garde des 12 px sur les quatre
vues ; `min-h-[32px]` rétabli ; `resize-none` ; `VUES` typé sur le store,
vérifié par sabotage `TS2820` ; trait unique sous l'en-tête du Mois),
fusionné sur `main` en `7fff767a`.

## Portes (main, après fusion)

vitest 2 270 / 2 270 dans le worktree ; 258 sur le périmètre (calendar, ui,
BoardConversationCard) rejoués après rebase ; tsc 0 ; eslint 27 (plafond).

## Recette (pile jetable c6)

Script `src/frontend/scripts-recette/recette-da-lot8.mjs` (interceptions par
prédicat sur le chemin dès l'écriture, horloge figée au 2 septembre 2026
11:48 par `context.clock`). Vingt-huit cas, captures et `apres-mesures.json`
dans `.cartography-work/validation/da-lot8/` : Semaine à 1280 (clair, sombre,
contraste élevé, polices 14, 16, 18 px), 1024, 840, 800 et 1280 × 640 ; Mois
à 1280 clair et sombre, 800, 1280 × 640 ; Jour à 900 et 640 de haut ; Liste
pleine et vide ; semaine à cheval sur deux mois ; cache périmé ; 403 Google ;
bandeau fusionné (403 + cache) ; reconnexion ; chargement ; aucun agenda ;
CalDAV ; nouveau rendez-vous ; focus ; empilement des lignes d'heure.

| Mesure | Résultat |
|---|---|
| Textes sous 12 px | 0 sur les 28 cas (« Journée » à 12 px est un renversement écrit, hors interactif) |
| Interactifs sous 14 px (police 16) | 0 |
| Boutons (Période, Aujourd'hui, Synchroniser, Importer, Exporter, Nouveau rendez-vous) et segments Jour / Semaine / Mois / Liste | 36 px |
| Trois gabarits de la Semaine (en-tête, Journée, piste) | traits alignés aux mêmes x, gouttière 129 px |
| Piste horaire | défile encore, `scrollTop` 120 au montage, repère « Il est 11:48 » posé |
| Mois à 1280 × 640 | 7 rangées, case chargée grandit (« +2 autres » visible), la carte défile (grille 855 px dans une carte de 600) |
| Formulaire « Nouveau rendez-vous » | champ Agenda en lecture seule, cinq champs `required`, grille remplacée, pied absent |
| Pied de grille | « Agenda local « … » · aucun agenda en ligne branché » ; absent quand aucun agenda |
| Bandeau fusionné 403 + cache | une seule Alerte, un seul Réessayer |

À police 14 px, `h-9` vaut 32 px : effet du `rem`, identique aux lots
précédents.

## Écarts relevés

- La sonde de focus lit un `outline` de 0 px sur le bloc et sur le segment
  après un `focus()` programmatique, alors que les gardes de rendu
  vérifient la classe `focus-visible:outline-[3px]` : limite de
  l'instrument (Chromium n'applique pas `:focus-visible` à ce focus-là dans
  ce cas), à confirmer au clavier dans l'application.
- L'annonce du chargement est lue vide par la sonde (`[role="status"]`
  premier trouvé) : même limite qu'au lot 6.
- Le panneau latéral de la maquette (formulaire par-dessus la grille) n'est
  pas codé : décision de Ludo, version de design dédiée si elle est prise.
- L'anneau rentrant est recopié dans trois fichiers : module partagé à
  faire au prochain lot qui y touche (§ Reste du design).
