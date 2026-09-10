# DA « Application affinée », lot 1 : socle et coque (design à challenger avant le code)

Date : 10/09/2026. Cadrage validé par Ludo (« Go DA! ») :
`docs/plans/2026-09-10-cadrage-da-application-affinee.md`. Proposition P-066
acceptée, cycle 7 en `IMPLEMENT`. Source : `docs/da/2026-09-05-propositions/`
(`maquettes/da/base.css` = la direction 2 entière, `tokens.css` = les jetons
réels de `globals.css`, `d2.css` vide). Ce document est soumis à Grok
(contradicteur) AVANT toute ligne de code.

## Ce que le lot change, en une phrase

La coque (barre, rail, colonne, composeur avec l'établi) et les primitives
`components/ui` prennent la forme de `base.css` en consommant les jetons
existants ; aucun écran n'est retouché, aucun comportement ne change.

## Décisions tranchées par défaut (Ludo peut corriger)

1. Ordre : socle d'abord, puis les huit écrans maquettés, puis les écrans sans
   maquette (maquettes produites par Syn sur DQ SYN, validées page par page).
2. Une release par lot : ce lot donne la 0.71.0-alpha.

## 1. Mécanisme de cascade (le point qui décide de la forme du chantier)

Tailwind 4 : toute règle écrite hors `@layer` bat toute utilitaire (leçon
`.btn-da`, `globals.css`). Recopier les sélecteurs d'élément de `base.css`
hors couche (`h1{font-size}`, `body{font}`, `:focus-visible{outline}`)
écraserait `text-2xl`, `text-sm` et `focus-visible:ring-*` sur toute
l'application en un commit. Donc :

| Contenu de `base.css` | Où il va | Pourquoi |
|---|---|---|
| `--font-family-editorial` (= display en direction 2) | `@theme` | génère `font-editorial` ; Instrument Serif (direction 1) n'est pas importé |
| `--colonne: 56rem` | `@theme` `--container-colonne` | génère `max-w-colonne` ; B-109 : `:root` ne génère aucune utilitaire |
| `--rail: 3.5rem`, barre 3,25 rem, `--espace-1..5` | rien | déjà dans la grille Tailwind : `w-14`, `h-13`, `p-2/3/4/6/8` |
| `--shadow-card: var(--shadow-sm)` (clair) | `:root` | la DA retire l'ombre large des cartes en clair ; le sombre garde la sienne (`[data-theme="dark"]`, plus spécifique) |
| `h1, h2, h3` (1,625 rem 800 / 1,1875 rem 700 / 1 rem 700, `letter-spacing -0.01em`, `line-height 1.2`, `margin 0`) | `@layer base` | un titre sans classe prend la DA ; un titre avec `text-2xl` garde sa taille jusqu'au lot de son écran |
| `body { font: 400 .875rem/1.5 }` | `@layer base` | le texte sans classe passe de 16 à 14 px : c'est le socle ; mesuré en recette |
| `:focus-visible { outline: 3px solid var(--color-ring); outline-offset: 2px }` | `@layer base` | les composants qui posent `focus-visible:outline-none` + anneau gardent le leur |
| `.btn*`, `.carte`, `.ligne`, `.etiquette`, `.segments`, `.vide`, `.alerte`, `.chargement`, `.champ`, `.tableau` | composants React dans `components/ui` | aucune classe globale copiée ; aucune collision de nom mesurée (`grep className="btn\|carte\|ligne…"` vide) |
| `[data-reduced-motion] *{transition:none}` | déjà dans l'app (`MotionConfig`, `globals.css`) | rien |

Exception documentée : les seules classes globales conservées sont celles
qui portent une transition sur `transform` et doivent rester hors couche
(`.card-brutal` tant qu'un écran l'utilise, puis retrait).

## 2. Ce que la DA validée retire : l'ombre et le soulèvement

`base.css` : `.btn` sans ombre ni `translateY` (hover = `background`
`surface-2`, primaire = `brightness(.96)`) ; `.carte` avec `--shadow-card =
--shadow-sm` en clair ; `.ligne:hover` = `surface-2`. La DA « Équilibre » du
30/08 (`btn-da` : ombre de carte + `translateY(-1px)` + `--shadow-pop`,
`card-brutal` : soulèvement des cartes) est donc remplacée. Portée : les 254
`<Button>` (primary, secondary, danger portent `btn-da`) et les cartes
`card-brutal`. `btn-da` quitte `Button.tsx` ; la classe reste dans
`globals.css` marquée dépréciée jusqu'au dernier usage hors primitive
(comptés au moment du lot), puis est retirée.

## 3. Table des tailles (chiffrée)

| Élément | Actuel | DA (`base.css`) | Décision |
|---|---|---|---|
| Barre | `min-h-14` (56 px) | 3,25 rem (52 px) | `h-13` |
| Rail | `w-16` (64 px), fond `surface-2` | 3,5 rem (56 px), fond `surface` | `w-14 bg-surface` |
| Bouton du rail (`IconButton`) | 44 px `rounded-md`, actif = remplissage cyan | 40 px `radius-sm`, actif = `accent-tint` + `text-accent`, hover `surface-2` | 40 px `rounded-sm`, actif teinte (le cyan plein est réservé au geste principal) |
| Avatar | 44 px | 40 px, `accent-fill` / `accent-ink`, display 700 | 40 px |
| `Button` md | 44 px `px-4 rounded-md` | `.btn` 2,25 rem (36 px) `padding 0 1rem` `radius-md` | `h-9 px-4 rounded-md` |
| `Button` sm | 32 px `rounded-sm` | (pas de variante DA) | inchangé `h-8 px-3 rounded-sm` |
| `Button` lg | 48 px | (pas de variante DA) | `h-11 px-6 rounded-md` (44 px, le geste principal d'un écran peut le garder) |
| `Button` icon | 44 px | `.btn-icone` 36 px | `h-9 w-9 rounded-md` |
| Envoyer (composeur) | 44 px, `border-text`, ombre, soulèvement | 36 px `radius-sm`, sans bordure, `accent-fill` ; désactivé = `surface-2` + `text-muted`, opacité 1 | DA |
| Colonne | `max-w-[860px]` (760 avec canevas) | 56 rem (896 px) | `max-w-colonne` ; avec canevas ouvert : inchangé 760 px |
| Étiquette | (aucune primitive) | 14 px 600, `padding .15rem .5rem`, pilule | primitive `Etiquette` |
| Ligne | (aucune primitive) | `grid 2rem 1fr auto`, `padding .7rem 1rem` | primitive `Ligne` |

Cibles tactiles : 44 → 36 px sur les boutons courants. L'application est un
logiciel de bureau ; WCAG 2.5.8 (AA) exige 24 px, 2.5.5 (AAA) 44 px. La DA
validée choisit 36 px ; le geste principal d'un écran peut rester en `lg`
(44 px). Aucun test ne fige `h-11`, `w-16`, `min-h-14` ni `max-w-[860px]`
(mesuré).

## 4. Typographie : la DA contredit deux fois le plancher du projet

`typographie.test.ts` : rien sous 12 px, ce qui se clique à 14 px au moins.

- `.recherche kbd` à `.7rem` (11,2 px) : interdit. Le raccourci reste en
  `text-xs` (plafonné à 12 px par `--text-xs`).
- `.ligne .detail` à `.8125rem` (13 px) dans une ligne cliquable : la règle
  du projet prime, `text-sm` (14 px). Même choix pour `.barre .etat` (13 px)
  et `.composeur .etabli button` : 14 px partout, `text-xs` réservé aux
  métadonnées non cliquables (`.meta`, `.aide`, en-têtes de tableau).
- `.meta`, `.aide` : classes Tailwind explicites (`text-xs font-medium
  text-text-muted`), pas d'utilitaire nommée : le test cherche `text-xs`
  dans la balise et une classe `meta` lui échapperait.
- `.editorial` = `font-editorial` (alias de display), pas une police de plus.

## 5. L'établi change de place

DA : les cinq verbes vivent en tête du composeur (`.composeur .etabli`,
pilules bordées, hover `border-accent`), précédés d'un libellé. Actuel : bloc
« Par où commencer » en bas de la colonne, sous un trait, à 224 px du composeur.

Décision : le groupe garde son libellé visible « Par où commencer » (c'est le
`span` de tête de l'établi DA) et son nom accessible, et se déplace dans le
composeur, au-dessus du champ. `Etabli.test.tsx` (deux `findByText('Par où
commencer')`) et les cinq tests qui citent le libellé restent verts sans
modification ; le test qui change est celui de l'emplacement, écrit rouge
d'abord (« le groupe est un descendant de `prototype-composer-backdrop` »).
Le composeur plus haut est absorbé par la mesure réelle de `composerClearance`
(`ResizeObserver` sur le fond du composeur, garde B-320) : rien n'est
recouvert.

## 6. Ce que la maquette n'a pas et que la coque garde

`WindowControls` gauche et droite, `onMouseDown={startWindowDrag}`,
`data-dialog-allow`, `ConnectionStatus` dans la barre (Finding 10),
`TraitementsIndicator`, et les onze sélecteurs testés (`shell-profile-button`,
« Navigation principale », `shell-background-activities`,
`coque-colonne-principale`, « Contrôle des données », `workspace-label`,
`prototype-conversation-scroll`, `prototype-composer-backdrop`,
`etat-connexion-coque`, « Plus d’outils », « Par où commencer »).

Retiré : le badge « Interface unifiée » (persona 08 : « je ne sais pas ce que
c'est » ; la DA ne l'a pas ; aucun test ne l'assert, un commentaire le cite).
L'espace de travail devient la pilule `.etat` de la DA (`<b>` sur le nom),
même `data-testid`. « Contrôle des données » devient un bouton discret
(`text-accent`, hover `accent-tint`), « Rechercher » la pilule bordée avec
`kbd`. Le pied du composeur porte une seule phrase, celle de la DA
(« Thérèse te demande confirmation avant tout envoi ou modification
externe. ») à la place de « Données réelles · sources affichées » et de la
ligne sous le composeur ; aucun test ne cite ces deux phrases (mesuré).

Les vues intégrées (`PrototypeUnifiedViewCanvas`, en-tête « Retour ») ne
changent pas dans ce lot ; le composeur reste propre à l'accueil
conversationnel.

## 7. Primitives livrées dans `components/ui` (exportées par `index.ts`)

| Primitive | Contenu DA | Note |
|---|---|---|
| `Button` (alignée) | variants `primary` (accent-fill / accent-ink, hover brightness), `secondary` (border-border, bg-surface, hover surface-2), `ghost` → aspect « discret » (text-accent, hover accent-tint), `danger` (error 12 %, text-error) ; tailles du § 3 ; `disabled` opacité .5 ; plus de `btn-da` | l'API (`variant`, `size`) ne change pas : 254 usages compilent tels quels |
| `Input`, `Select`, `Textarea` (alignées) | `border-border`, `rounded-sm`, `bg-surface` (au lieu de `surface-2`), `min-h-9`, focus = `border-accent` + anneau `ring/30 %` ; erreur = `border-error` | API inchangée |
| `FormField` (alignée) | libellé 13 px 600 → `text-sm font-semibold` (plancher), aide `text-xs` | API inchangée |
| `Carte`, `CarteTete` (nouvelles) | `bg-surface border rounded-md shadow-[var(--shadow-card)]` ; tête : icône ronde `accent-tint`, titre `h2`, `actions` à droite | remplace les cartes à la main écran par écran, pas dans ce lot |
| `Ligne` (nouvelle) | `grid-cols-[2rem_1fr_auto]`, puce de domaine, titre 600, détail `text-sm` muted, droite ; `role="button"` + clavier quand cliquable ; `dense` | idem |
| `Etiquette` (nouvelle) | `ton` = erreur / attention / succès / info / neutre, `domaine` = agenda / tâches / factures / prospects ; en contraste élevé : fond transparent + `border currentColor` | consomme `--color-domaine-*` et sémantiques ; teintes à 12-14 % en `color-mix` |
| `Segments` (nouvelle) | `role="tablist"`, pilule `surface-2`, sélectionné `surface` + `shadow-sm` | |
| `EtatVide`, `Alerte`, `Squelette` (nouvelles) | `.vide` (h3 + p + action), `.alerte` (`role="alert"`, error 8 % / bordure 30 %), `.chargement` (barre animée, `aria-hidden`, respecte `reduced-motion`) | `Spinner` reste l'attente ponctuelle |

Les 488 `<button>` bruts et les cartes à la main des écrans ne sont pas
migrés ici : c'est le travail de chaque lot d'écran.

## 8. Gardes mécaniques (validées par sabotage)

1. `typographie.test.ts` et `contrasteDesTeintes.test.ts` existants (plancher
   12/14 px, teintes AA).
2. Nouveau `components/ui/aucuneCouleurEnDur.test.ts` : aucun `#rrggbb` ni
   `rgb(` dans `components/ui/**` et dans la coque
   (`ConversationCanvasPrototype.tsx`), liste blanche nommée et vide au
   départ. Borné : les couleurs de marque des fournisseurs (`AdvisorCard`)
   et le SVG de `ChatHeader` sont légitimes, un rouge dessus serait du bruit.
3. Nouveau `components/ui/Button.da.test.tsx` : tailles et absence de
   `btn-da` par variant.
4. Nouveau `ConversationCanvasPrototype.da.test.tsx` : rail `w-14`, boutons
   du rail 40 px, établi descendant du composeur, envoyer sans `border-text`,
   badge « Interface unifiée » absent, colonne `max-w-colonne`.
5. `Etiquette.test.tsx` : contraste élevé retire la teinte (bordure
   `currentColor`).

## 9. Plan de preuve

1. Tests rouges d'abord pour ce qui change (§ 8.3 à 8.5), vérifiés rouges
   pour la bonne raison, sabotage par retour arrière.
2. Six portes : ruff, pytest (XML), vitest json, tsc, eslint (27), mypy 951.
3. Recette visuelle sur la pile jetable relancée (`pile-jetable-c6.sh`,
   17393 et 1420, jamais 17293) : accueil et une vue intégrée, à 1280, 1024
   et 800 px, en clair, sombre et contraste élevé, taille de police petite,
   moyenne, grande ; captures avant/après dans `.cartography-work/validation/
   da-lot1/` (ignoré par git), rapport `docs/da/2026-09-10-lot1-recette.md`.
   Vérifier : rien sous le composeur (B-320), anneau de focus visible sur
   rail et composeur, étiquettes en contraste élevé, `body` 14 px sans
   régression de lecture sur les vues intégrées.
4. Revue Grok du diff avant le tag, `/release-therese 0.71.0-alpha` avec le
   GO de Ludo.

## 10. Ce que ce lot ne fait pas

- Aucun écran, aucun canevas, aucune couche (palette, modales) n'est
  retouché : ils gardent leurs classes ; ils héritent seulement de `body`,
  des titres sans classe, du focus et des primitives.
- Aucun comportement ne change : les 3 392 pytest, 1 994 vitest et 99
  parcours e2e restent la vérité.
- Pas de nouvelle police, pas de nouveau jeton de couleur.
