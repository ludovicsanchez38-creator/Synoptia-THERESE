# Audit DA/UI des écrans harmonisés en 0.73.0 (P-090) : cycle 9, 15/09/2026

Vérification du travail d'Astra (session Codex du 12/09) : les quinze écrans harmonisés sans maquette, plus le Centre de confiance, mesurés dans l'application réelle sur pile jetable (uvicorn 17393 + Vite 1420, données vierges, mise en route terminée). Script `.cartography-work/validation/da-audit-c9/audit-da-c9.mjs` (Playwright, captures après stabilisation à deux empreintes identiques), instruments calibrés le 15/09.

## Matrice

- Largeurs : 1280 × 900, 1024 × 820, 800 × 760 ; thèmes : clair, sombre, contraste élevé ; plus grande police à 1280 clair.
- Mesures par cas : interactifs sous 14 px, textes sous 12 px, dégradés décoratifs, débordement horizontal, erreurs console, erreurs de page, réponses réseau ≥ 400, cibles sous 24 px.

## Résultat

- Cas joués : 160 ; réussis : 156 ; en échec d'ouverture : ['palette-clair-800', 'palette-sombre-800', 'palette-contraste-800', 'apropos-clair-1280-grande'].
- Aucun interactif sous 14 px, aucun texte sous 12 px, aucun débordement horizontal, aucune erreur console ou réseau sur les 156 cas ouverts.
- Unique dégradé mesuré partout : le voile de lisibilité derrière le composeur (livré au lot 1 du socle), pas un décor.
- Palette à 800 px : les trois cas ont échoué à l'ouverture parce que le bouton « Rechercher » n'avait plus de nom accessible sous 840 px (« ⌘K ») : **B-761, corrigé** (preuve `scripts-recette/recette-rechercher-800.mjs`).
- « À propos » en grande police à 1280 : un délai d'ouverture isolé (15 s), non reproduit.

## Ce que l'audit a trouvé hors mesure

- Le centre de notifications, harmonisé au lot 10D, n'était monté nulle part (ChatHeader, son seul parent, n'est rendu par personne), pas plus que la palette historique de `chat/` ni `EmailConnect` : **B-760, retirés**.
- Astra avait capturé 7 écrans sur 15 ; les 16 sont désormais couverts aux neuf combinaisons.

## Écrans et cas

| Écran | Cas | Ouverts | Stabilisation médiane |
|---|---|---|---|
| palette | 10 | 7 | 1400 ms |
| raccourcis | 10 | 10 | 2288 ms |
| travaux | 10 | 10 | 1153 ms |
| apropos | 10 | 9 | 1232 ms |
| memoire | 10 | 10 | 570 ms |
| livrables | 10 | 10 | 625 ms |
| relances | 10 | 10 | 624 ms |
| images | 10 | 10 | 633 ms |
| voix | 10 | 10 | 636 ms |
| capacites | 10 | 10 | 1287 ms |
| calculateurs | 10 | 10 | 1303 ms |
| prompts | 10 | 10 | 664 ms |
| confiance | 10 | 10 | 1165 ms |
| email | 10 | 10 | 1272 ms |
| documents | 10 | 10 | 568 ms |
| atelier | 10 | 10 | 603 ms |

Captures : `.cartography-work/validation/da-audit-c9/<écran>-<thème>-<largeur>.png` (ignoré par git).
