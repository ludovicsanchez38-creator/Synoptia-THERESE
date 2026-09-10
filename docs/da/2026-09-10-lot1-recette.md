# DA « Application affinée », lot 1 (socle et coque) : recette du 10/09/2026

Design validé par Grok au troisième passage (`docs/plans/2026-09-10-da-lot1-socle-coque-design.md`).
Pile jetable : backend 17393 (données `/tmp/therese-demo-c6/data`), Vite 1420 (main) ;
« avant » mesuré sur un second Vite (1421) servant l'arbre `grok/da-lot1-primitives`
à `67dcf1df`, dont la coque est celle de la 0.70.0. Captures et mesures brutes dans
`.cartography-work/validation/da-lot1/` (ignoré par git), script `recette-da-lot1.mjs`.

## Mesures au pixel (1280 × 820, clair, police moyenne)

| Mesure | Avant (0.70.0) | Après (lot 1) | DA (`base.css`) |
|---|---|---|---|
| Rail | 64 px, fond `surface-2` | 56 px, fond `surface` | 3,5 rem, `surface` |
| Bouton du rail | 44 × 44, actif jamais marqué | 40 × 40, actif en teinte `#DEF4F9`, `aria-current="page"` | 2,5 rem, `accent-tint` |
| Barre | 56 px | 52 px (`min-h-13`) | 3,25 rem |
| Corps de texte (`body`) | 16 / 24 px | 14 / 21 px | .875rem / 1.5 |
| `h1` d'accueil | 24 px, 700 | 26 px, 800, Plus Jakarta Sans | 1,625 rem, 800 |
| Colonne | 860 px | 896 px | 56 rem |
| Composeur | (pas de carte mesurable) | 896 px, même largeur que la colonne, `shadow-lg` | `min(56rem, …)`, `shadow-lg` |
| Établi dans la carte du composeur | non (bloc au bas de la colonne) | oui, premier enfant | oui |
| Bouton d'envoi | 44 × 44, bordure 1 px | 36 × 36, sans bordure | 2,25 rem, sans bordure |
| Badge « Interface unifiée » | présent | absent | absent |
| Anneau de focus (Tab) | 2 px | 3 px `#0F8FB3`, décalage 2 px | 3 px `ring` |
| Dégagement du fil (B-320) | 290 px | 269 px, mesuré par `ResizeObserver` | (composeur plus bas) |

Mêmes valeurs en sombre et en contraste élevé (le bouton d'envoi y prend la
bordure 1 px de la règle `[data-high-contrast] button`, voulue). À 1024 et
840 px, colonne à 896 et 720 px ; à 800 px, 680 px.

Taille de police : Petite (html 14 px) donne un corps à 12,25 px et un `h1` à
22,75 px ; Grande (18 px) un corps à 15,75 px et un `h1` à 29,25 px. Le
plancher du projet (12 px) est tenu en Petite, de justesse ; à surveiller si
un écran pose du texte sans classe dans une zone dense.

## Ce que la recette a trouvé et corrigé

- **Barre écrasée à 800 px** : la marque « THÉRÈSE » était recouverte par
  l'indicateur de connexion (« THÉRÈSEur actif 10ms »). Marque et son point
  en `shrink-0`, indicateur tronqué plutôt qu'écrasé (Finding 10 conservé),
  latence et mot « Rechercher » repliés sous 840 px comme la DA
  (`max-[840px]:hidden`). Test rouge puis vert (`e5d56ab6`).
- **Parcours e2e B-320 vert par construction** : avec la base presque vide
  des parcours, le dernier contenu tient au-dessus du composeur même sans
  dégagement ; un sabotage (`paddingBottom: 0`) passait. Le spec mesure aussi
  l'invariant mécanique (dégagement ≥ hauteur du fond du composeur) : sabotage
  rouge (0 contre 245), restauration vérifiée par empreinte du diff, rejeu vert.
- **Cache Vite partagé entre deux arbres** : deux serveurs Vite sur le même
  `node_modules` (lien symbolique) ont chargé deux copies de React sur le
  1420 (« Invalid hook call », page vide). Un seul Vite à la fois, relancé
  avec `--force` ; le navigateur intégré gardait de plus un cache de chunks,
  la sonde a été faite en navigateur Playwright propre.

## Captures relues

Accueil à 1280 en clair, sombre et contraste élevé (avec focus clavier),
1024, 840, 800 ; Petite et Grande ; accueil avec « Retrouver » pressé et le
canevas ouvert (colonne 760 px, verbe pressé en teinte) ; Paramètres (modale :
« Fermer », « Voir THERESE.md », « Importer » en `ghost` accent, « Enregistrer »
primaire 36 px) ; vue intégrée Projets (en-tête « Retour » inchangé).

## Portes

- Mes quatre gardes (`jetonsDA`, `Button.da`, `aucuneCouleurEnDur`,
  `ConversationCanvasPrototype.da`) : rouges pour la bonne raison (17 rouges
  sur 18 au premier run), puis vertes ; sabotages rouges sur le rail (`w-14` →
  `w-16`), une couleur en dur dans `Button`, une teinte remise dans `:root`.
- `lot11.test.ts` B-418 aligné sur son invariant (le bouton ne se replie pas),
  l'aspect ayant changé.
- Frontend sur `cf9c74a9` : vitest 2 011 verts, tsc 0, eslint 27 (plafond) ;
  backend inchangé : ruff propre, pytest 3 392 / 0 rouge (XML), mypy 951.
- Primitives de Grok (branche `grok/da-lot1-primitives`, onze commits) :
  aucune assertion supprimée dans un test existant, sabotage de `Segments`
  (`aria-pressed`) rouge, 64 tests de primitives ; portes rejouées sur main
  après fusion (voir le rapport de release).

## Réserves déclarées

- `UpdateBanner.tsx` est en liste blanche nommée de la garde « aucune couleur
  en dur » (seize `rgba` en styles inline, survol piloté en JS) : couche, lot
  des couches.
- Les primitives `Carte`, `Ligne`, `Etiquette`, `Segments`, `EtatVide`,
  `Alerte`, `Squelette` ne sont montées par aucun écran dans ce lot : preuve
  par vitest seulement, recette visuelle à leur premier usage (lot Accueil).
- `Input`, `Select`, `Textarea`, `FormField` alignés sans import de production
  (dette 0.49) : idem.
