# DA « Application affinée », lot 9 : recette des Paramètres (11/09/2026)

Design : `docs/plans/2026-09-11-da-lot9-parametres-design.md` (rédigé par
Grok, deux revues Grok puis trois revues Claude Opus jusqu'au GO en v5 ; v6 et
v7 par l'implémenteur). Code par un implémenteur Claude Opus en worktree
(66 gardes, 51 rouges d'abord), trois extensions de primitives partagées
(`Alerte.ton`, `CarteTete.niveau`, `FormField` en `text-sm`) sans changer
leur rendu par défaut. Revue adverse du diff par un relecteur Claude Opus :
**NO-GO, un P1 (après un refus de clé puis un clic sur un Ollama joignable et
vide, l'erreur n'était plus rendue nulle part), quatre P2, trois P3** ; sept
points repris (`setCleInvalide(false)` en tête du changement de fournisseur,
garde B-201 élargie au garde optionnel, `gap-y-4` sur les grilles du profil,
« Réessayer l'effort » seulement si un effort a échoué, masquage de l'erreur
pendant le chargement prouvé au rendu, mode démo dans une carte comme ses
voisines), fusionné sur `main` en `bd535f91`. Le fichier vide « { » qui
traînait à la racine du dépôt depuis un ancien commit part avec ce lot.

## Portes (main, après fusion)

vitest 2 388 / 2 388 dans le worktree ; 554 sur le périmètre (settings, ui,
lib) rejoués sur `main` ; tsc 0 ; eslint 27 (plafond).

## Recette (pile jetable c6)

Script `src/frontend/scripts-recette/recette-da-lot9.mjs` (interceptions par
prédicat sur le chemin ; attente de 300 ms après un changement d'onglet, le
temps que `transition-colors` suive la classe). Trente-cinq cas, captures et
`apres-mesures.json` dans `.cartography-work/validation/da-lot9/` : Service
d'IA avec Ollama actif à 1280 (clair, sombre, contraste élevé, polices 14,
16, 18 px), 1024, 1023, 840, 800 ; OpenAI avec clé, sans clé, clé corrompue,
refus de préfixe, modèle hors catalogue, fournisseur inconnu, Ollama
indisponible, lecture en échec ; focus d'un onglet et d'une carte ; clavier
dans la grille ; Profil à 1280 (trois thèmes), 1024, 1023, 840, 800, nom long
à deux polices, profil absent ; chargement ; reprise du chargement ; overlay.

| Mesure | Résultat |
|---|---|
| Textes sous 12 px | 0 sur les 35 cas |
| Interactifs sous 14 px (police 16) | 0 |
| Onglets, Fermer, Enregistrer, cartes d'action | 36 px (38 en contraste élevé, bordure) |
| Nav au-dessus du panneau | à partir de 1023 px, colonne à 1024 et au-dessus |
| Modale | 1152 px à 1280, 784 à 800 ; overlay `fixed` sur tout l'écran |
| Tabulation dans la grille des fournisseurs | 14 arrêts, aucune flèche (doctrine `Segments`) |
| Chargement | six squelettes, « Lecture des réglages… » |
| Reprise du chargement | focus rendu au panneau Profil, bandeau parti |
| Modèle hors catalogue | option « (personnalisé) » présente, mention rendue |

À police 14 px, `h-9` vaut 32 px : effet du `rem`, identique aux lots
précédents.

## Écarts relevés

- Les sondes de focus lisent un `outline` de 0 px après un `focus()`
  programmatique (même limite qu'au lot 8) ; la carte courante montre son
  halo `box-shadow`. À confirmer au clavier dans l'application.
- B-753 fiché : React avertit « two children with the same key » sur
  `claude-fable-5` et `claude-sonnet-5` dans le sélecteur de modèle
  (doublons du catalogue, préexistant).
- Services et connecteurs rend encore l'erreur de coque une seconde fois :
  dette écrite au design, onglet non maquetté.
