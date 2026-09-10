# DA « Application affinée », lot 1 : socle et coque (design à challenger avant le code)

Date : 10/09/2026. Cadrage validé par Ludo (« Go DA! ») :
`docs/plans/2026-09-10-cadrage-da-application-affinee.md`. Proposition P-066
acceptée, cycle 7 en `IMPLEMENT`. Source : `docs/da/2026-09-05-propositions/`
(`maquettes/da/base.css` = la direction 2 entière, `tokens.css` = les jetons
réels de `globals.css`, `d2.css` vide). Ce document est soumis à Grok
(contradicteur) AVANT toute ligne de code. Version 3 (10/09, 18:55) : la
version 1 a reçu un NO-GO de Grok (22 points, tous confirmés à la lecture du
code, `.cartography-work/reviews/c7-grok-da-lot1-design.log`), la version 2
un second NO-GO (21 points traités, un partiel, 9 nouveaux,
`c7-grok-da-lot1-design-v2.log`) ; chaque point est intégré ci-dessous.

## Ce que le lot change, en une phrase

La coque (barre, rail, colonne, composeur avec l'établi) et les primitives
`components/ui` prennent la forme de `base.css` en consommant les jetons
existants. Aucun fichier d'écran n'est édité, mais tous les écrans héritent
de `Button` (254 usages : 44 → 36 px, `ghost` en accent), de `body` à 14 px
et du focus ; aucun comportement ne change.

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

Ordre impératif (Grok 1) : les jumeaux déjà écrits HORS couche dans
`globals.css` (`h1, h2, h3 { font-family; letter-spacing }` l.266-271 et
`:focus-visible { outline: 2px }` l.312-315) sont retirés d'abord, sinon les
règles DA posées en `@layer base` restent mortes derrière eux.

| Contenu de `base.css` | Où il va | Pourquoi |
|---|---|---|
| `html{font-size:16px}` | **ne pas copier** | `useFontSize()` pose 14, 16 ou 18 px sur `<html>` (préférence Petite / Grande) ; le copier figerait la préférence |
| `--font-family-editorial` | `@theme --font-editorial` (même pile que display) | Tailwind 4 génère `font-*` depuis `--font-*`, pas depuis `--font-family-*` (`--font-family-display` du projet ne produit pas `font-display`, 0 usage) ; Instrument Serif (direction 1) n'est pas importé |
| `--colonne: 56rem` | `@theme --container-colonne: 56rem` | génère `max-w-colonne` (namespace `--container-*`, comme `--container-4xl`) ; B-109 : `:root` ne génère aucune utilitaire ; la garde asserte la déclaration ET le style calculé |
| (jetons du projet) `--color-error-tint`, `--color-success-tint`, `--color-warning-tint`, `--color-info-tint` | **promus de `:root` (l.160-165) dans `@theme`**, mêmes pigments ; les redéfinitions sombre et contraste élevé restent | B-109 : en `:root` ils ne génèrent pas `bg-error-tint`, et les primitives (`Etiquette`, `Alerte`, `Button danger`) partiraient sans fond ; le motif de `contrasteDesTeintes.test.ts` (`--color-error:`) ne les attrape pas |
| `--rail: 3.5rem`, barre 3,25 rem, `--espace-1..5` | rien | déjà dans la grille Tailwind : `w-14`, `min-h-13`, `p-2/3/4/6/8` |
| `--shadow-card: var(--shadow-sm)` (clair) | **jeton global inchangé** | cinq usages hors lot (`FollowUpsWorkspaceCanvas`, `ImagesWorkspaceCanvas`, `VoiceWorkspaceCanvas`, `CapabilityCenter`, `PrototypeConversationDrawer`) ; seule la primitive `Carte` prend `shadow-sm` ; les canevas suivront à leur lot |
| `h1, h2, h3` (1,625 rem 800 / 1,1875 rem 700 / 1 rem 700, display, `letter-spacing -0.01em`, `line-height 1.2`, `margin 0`) | `@layer base`, après retrait du jumeau hors couche | un titre sans classe prend la DA ; un titre avec `text-2xl` garde sa taille jusqu'au lot de son écran |
| `body{font:400 .875rem/1.5 var(--font-family-sans)}` (ligne DA entière : le raccourci `font` sans famille est invalide et serait ignoré) | `@layer base`, en PLUS du bloc `body` hors couche existant (`background-color`, `color`, `overflow: hidden`, `border-radius`), qui reste | le texte sans classe passe de 16 à 14 px ; mesuré en recette, y compris en Petite (12,25 px : `--text-xs` plafonne les `text-xs`, pas le texte sans classe, à vérifier au pixel) |
| `:focus-visible { outline: 3px solid var(--color-ring); outline-offset: 2px }` | `@layer base`, après retrait du jumeau hors couche (le bloc contraste élevé l.630 reste) | les composants qui posent `focus-visible:outline-none` + anneau gardent le leur |
| `.btn*`, `.carte`, `.ligne`, `.etiquette`, `.segments`, `.vide`, `.alerte`, `.chargement`, `.champ`, `.tableau` | composants React dans `components/ui` | aucune classe globale copiée ; aucune collision de nom mesurée |
| `[data-reduced-motion="true"] *{transition:none}` | rien : l'app pose `data-reduce-motion` (sans « d », `globals.css` l.491) et `prefers-reduced-motion` l.479 | le `Squelette` s'appuie sur ces deux filets, pas sur l'attribut DA |

Plus aucune classe globale de bouton ou de carte : `btn-da` n'a d'usage que
dans `Button.tsx`, `card-brutal` que dans `QuickActions.tsx`, jamais monté
par la coque (aucun import hors son test). Les deux classes sont retirées
dans ce lot, de `globals.css`, de `Button.tsx` et de `QuickActions.tsx`.

## 2. Ce que la DA validée retire : l'ombre et le soulèvement

`base.css` : `.btn` sans ombre ni `translateY` (hover = `background`
`surface-2`, primaire = `brightness(.96)`) ; `.carte` avec `--shadow-card =
--shadow-sm` en clair ; `.ligne:hover` = `surface-2`. La DA « Équilibre » du
30/08 (`btn-da` : ombre de carte + `translateY(-1px)` + `--shadow-pop`,
`card-brutal` : soulèvement des cartes) est donc remplacée. Portée : les 254
`<Button>` (primary, secondary, danger portent `btn-da`). `btn-da` et
`card-brutal` sont retirés (voir § 1). Le jeton global `--shadow-card`
ne bouge pas.

## 3. Table des tailles (chiffrée)

| Élément | Actuel | DA (`base.css`) | Décision |
|---|---|---|---|
| Barre | `min-h-14` (56 px) | 3,25 rem (52 px) | `min-h-13` (plancher DA, croissance permise : `ConnectionStatus`, `TraitementsIndicator` et les pastilles Windows `h-8` ne doivent pas être clippés) |
| Rail | `w-16` (64 px), fond `surface-2` | 3,5 rem (56 px), fond `surface` | `w-14 bg-surface` |
| Bouton du rail (`IconButton`) | 44 px `rounded-md`, actif = remplissage cyan | 40 px `radius-sm`, actif = `accent-tint` + `text-accent`, hover `surface-2` | 40 px `rounded-sm`, actif teinte (le cyan plein est réservé au geste principal) |
| Avatar | 44 px, `text-sm` | 40 px, `accent-fill` / `accent-ink`, display 700, `.8rem` | 40 px, `text-sm` (12,8 px sur un bouton : sous le plancher) |
| `Button` md | 44 px `px-4 rounded-md` | `.btn` 2,25 rem (36 px) `padding 0 1rem` `radius-md` | `h-9 px-4 rounded-md` |
| `Button` sm | 32 px `rounded-sm` | (pas de variante DA) | inchangé `h-8 px-3 rounded-sm` |
| `Button` lg | 48 px | (pas de variante DA) | `h-11 px-6 rounded-md` (44 px, le geste principal d'un écran peut le garder) |
| `Button` icon | 44 px | `.btn-icone` 36 px | `h-9 w-9 rounded-md` |
| Envoyer (composeur) | 44 px, `border-text`, ombre, soulèvement | 36 px `radius-sm`, sans bordure, `accent-fill` ; désactivé = `surface-2` + `text-muted`, opacité 1 | DA |
| Champ du composeur | `text-sm` | `.9375rem` (15 px) | `text-sm` : une seule échelle (14 px), la DA n'est pas suivie ici |
| Conteneur du composeur | `rounded-md border` + `shadow-[0_18px_45px_-24px_rgba(…)]` + anneau `rgba(34,211,238,.12)` | `radius-md`, `shadow-lg` | `shadow-lg` et anneau `ring-ring/30` (jetons) : c'est ce qui rend la garde « aucune couleur en dur » possible |
| Colonne ET composeur | `max-w-[860px]` (760 avec canevas), même ternaire aux deux endroits | 56 rem (896 px) | `max-w-colonne` sur les deux ; avec canevas ouvert : inchangé 760 px sur les deux |
| Étiquette | (aucune primitive) | 14 px 600, `padding .15rem .5rem`, pilule | primitive `Etiquette` |
| Ligne | (aucune primitive) | `grid 2rem 1fr auto`, `padding .7rem 1rem` | primitive `Ligne` |

Cibles tactiles : 44 → 36 px sur les boutons courants. L'application est un
logiciel de bureau ; WCAG 2.5.8 (AA) exige 24 px, 2.5.5 (AAA) 44 px. La DA
validée choisit 36 px ; le geste principal d'un écran peut rester en `lg`
(44 px). Aucun test ne fige `h-11`, `w-16`, `min-h-14` ni `max-w-[860px]`
(mesuré).

## 4. Typographie : la DA contredit deux fois le plancher du projet

`typographie.test.ts` : rien sous 12 px, ce qui se clique à 14 px au moins.
Trois contradictions avec la maquette, toutes tranchées en faveur du
projet ; une quatrième (le champ du composeur à 15 px) tranchée pour une
échelle unique.

- `.avatar` à `.8rem` (12,8 px) sur le bouton profil cliquable : `text-sm`.
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
composeur, au-dessus du champ, **premier enfant de la carte du composeur** (le bloc `rounded-md border
bg-surface` de la l.1950, lui-même dans le wrapper `pointer-events-auto` ;
le fond `prototype-composer-backdrop` est `pointer-events-none` et le wrapper
contient aussi la phrase sous la carte : « dans le wrapper » ne suffit pas). Il reçoit `data-testid="etabli-composeur"` pour être ciblé sans
remonter au parent. `actionsVisibles` (masquage de « Facturer » sur une
installation neuve, `etabliSansFacturer.test.tsx`) et `aria-pressed` (lu par
`Etabli.test.tsx`) sont conservés tels quels. Le verbe pressé abandonne le
cyan plein (réservé au geste principal) : pilule `border-accent bg-accent-tint
text-accent`, les autres `border-border bg-surface text-text` avec hover
`border-accent text-accent` (DA `.etabli button:hover`). `Etabli.test.tsx` et les tests
qui citent le libellé restent verts sans modification ; le test qui change
est celui de l'emplacement, écrit rouge d'abord (« `etabli-composeur` est un
descendant du wrapper `pointer-events-auto` du composeur »).

Le parcours e2e `parcours-08-capacites-prototype.spec.ts` (B-320) mesure
aujourd'hui « le parent de « Par où commencer » finit au-dessus du champ » :
une fois l'établi dans le composeur, ce parent serait le composeur entier
(rouge) ou le groupe seul (tautologie). Il est réécrit sur ce qu'il protège
vraiment : après défilement au bout, le DERNIER ENFANT de la colonne
intérieure du fil (pas la boîte de `prototype-conversation-scroll`, qui est
la colonne entière sous le composeur posé en `absolute`) finit au-dessus du
bord haut de la carte du composeur, aux deux largeurs. Ce spec est
lancé à part, hors des six portes, avec le rapport JSON. Le composeur plus
haut est absorbé par la mesure réelle de `composerClearance`
(`ResizeObserver` sur le fond du composeur).

## 6. Ce que la maquette n'a pas et que la coque garde

`WindowControls` gauche et droite, `onMouseDown={startWindowDrag}`,
`data-dialog-allow`, `ConnectionStatus` dans la barre (Finding 10),
`TraitementsIndicator`, le bouton « Accueil » du rail (Ludo, 28/08), la
dictée (`VoiceDictationButton`) et son erreur, le bandeau de capacité
choisie et le message de destination, `IndiceDeDefilement` (B-562), la
cascade Échap (`pushEscapeHandler`), `actionsVisibles` et `aria-pressed` de
l'établi, et les onze sélecteurs testés (`shell-profile-button`,
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

Branché dans ce lot : `IconButton` déclare `active` sans qu'aucun appel ne
le passe et n'accepte aucune autre prop ; il dérive lui-même
`aria-current={active ? 'page' : undefined}` (pas de rest props à ouvrir) ;
le rail reçoit ainsi `aria-current="page"` (DA
`.rail button[aria-current="page"]`) sur « Accueil » quand l'accueil
conversationnel est affiché sans vue ni chat, et sur « Projets » quand la vue
Projets est ouverte. C'est un attribut en plus, aucun geste ne change.

Le `h1` d'accueil (l.1697, `text-2xl font-bold tracking-[-0.035em]`) vit
dans le fichier déjà édité : il perd sa taille et son tracking pour laisser
`@layer base` poser 1,625 rem / 800 / -0,01 em, sinon la recette de
l'accueil ne montre pas le titre DA.

Les vues intégrées (`PrototypeUnifiedViewCanvas`, en-tête « Retour ») ne
changent pas dans ce lot ; le composeur reste propre à l'accueil
conversationnel.

## 7. Primitives livrées dans `components/ui` (exportées par `index.ts`)

| Primitive | Contenu DA | Note |
|---|---|---|
| `Button` (alignée) | variants `primary` (accent-fill / accent-ink, hover brightness), `secondary` (border-border, bg-surface, hover surface-2), `ghost` → aspect « discret » (text-accent, hover accent-tint), `danger` (fond `--color-error-tint`, text-error) ; tailles du § 3 ; `disabled` opacité .5 ; plus de `btn-da` | l'API (`variant`, `size`) ne change pas : 254 usages compilent tels quels. Effet visible partout : les « Annuler », « Retour », « Fermer » en `ghost` passent du gris à l'accent ; la recette regarde Paramètres, la mise en route et une modale pour juger si c'est trop |
| `Input`, `Select`, `Textarea` (alignées) | `border-border`, `rounded-sm`, `bg-surface` (au lieu de `surface-2`), `min-h-9`, focus = `border-accent` + anneau `ring/30 %` ; erreur = `border-error` | API inchangée. Zéro import de production (dette 0.49, mesurée) : alignées pour les écrans à venir, elles ne comptent pas comme preuve visuelle |
| `FormField` (alignée) | libellé 13 px 600 → `text-sm font-semibold` (plancher), aide `text-xs` | API inchangée |
| `Carte`, `CarteTete` (nouvelles) | `bg-surface border rounded-md shadow-sm` (jamais le jeton global `--shadow-card`, voir § 1) ; tête : icône ronde `accent-tint`, titre `h2`, `actions` à droite | remplace les cartes à la main écran par écran, pas dans ce lot |
| `Ligne` (nouvelle) | `grid-cols-[2rem_1fr_auto]`, puce de domaine, titre 600, détail `text-sm` muted, droite ; `dense` | quand elle est cliquable, la rangée n'est PAS un bouton : le titre est un `<button>` « étiré » (`before:absolute before:inset-0` sur une rangée `relative`) et les actions de droite sont `relative` au-dessus : un seul interactif pour la rangée, Entrée et Espace natifs, aucun interactif emboîté ; non cliquable = aucun rôle |
| `Etiquette` (nouvelle) | `ton` = erreur / attention / succès / info / neutre, `domaine` = agenda / tâches / factures / prospects ; en contraste élevé : fond transparent + `border currentColor` | fonds = les jetons de teinte OPAQUES du projet (`--color-*-tint`, `--color-domaine-*-tint`, déjà AA sur la surface), encre = jeton sémantique ; pas de `color-mix` translucide (c'est le défaut que les teintes opaques ont corrigé) |
| `Segments` (nouvelle) | pilule `surface-2`, sélectionné `surface` + `shadow-sm` | pas de `tablist` orphelin (sans onglets, roving ni flèches) : un `role="group"` nommé et des boutons `aria-pressed`, motif déjà lu par les tests de l'établi |
| `EtatVide`, `Alerte`, `Squelette` (nouvelles) | `.vide` (h3 + p + action), `.alerte` (`role="alert"`, fond `--color-error-tint`, bordure `error/30`), `.chargement` (barre animée, `aria-hidden`) | `Squelette` s'arrête sous `html[data-reduce-motion="true"]` et `prefers-reduced-motion` (les deux filets de l'app) ; `Spinner` reste l'attente ponctuelle |

Les 488 `<button>` bruts et les cartes à la main des écrans ne sont pas
migrés ici : c'est le travail de chaque lot d'écran.

## 8. Gardes mécaniques (validées par sabotage)

1. `typographie.test.ts` et `contrasteDesTeintes.test.ts` existants (plancher
   12/14 px, teintes AA).
2. Nouveau `components/ui/aucuneCouleurEnDur.test.ts` : aucun `#rrggbb` ni
   `rgb(` dans `components/ui/**` et dans la coque
   (`ConversationCanvasPrototype.tsx`), liste blanche nommée et vide.
   Prérequis : les deux `rgba(…)` du composeur (ombre l.1950, anneau) sont
   remplacés par `shadow-lg` et `ring-ring/30` dans ce lot, sinon la garde
   est rouge avant tout refactor. Borné : les couleurs de marque des
   fournisseurs (`AdvisorCard`) et le SVG de `ChatHeader` sont légitimes.
3. Nouveau `components/ui/Button.da.test.tsx` : tailles et absence de
   `btn-da` par variant.
4. Nouveau `ConversationCanvasPrototype.da.test.tsx` : rail `w-14`, boutons
   du rail 40 px, `etabli-composeur` descendant du wrapper cliquable du
   composeur, envoyer sans `border-text`, badge « Interface unifiée » absent,
   `aria-current="page"` sur Accueil, colonne ET composeur `max-w-colonne`.
   Contre B-109 : une classe présente dans un `className` ne prouve pas
   qu'une règle existe ; `styles/jetonsDA.test.ts` asserte la déclaration
   `--container-colonne: 56rem`, `--font-editorial` et les quatre teintes
   sémantiques DANS le bloc `@theme` de `globals.css` (jsdom ne calcule pas
   une largeur issue de `@theme` : la largeur réelle se mesure en recette et
   dans le parcours e2e B-320, pas en jsdom).
5. `Etiquette.test.tsx` : contraste élevé retire la teinte (bordure
   `currentColor`).

## 9. Plan de preuve

1. Tests rouges d'abord pour ce qui change (§ 8.3 à 8.5), vérifiés rouges
   pour la bonne raison, sabotage par retour arrière.
2. Six portes : ruff, pytest (XML), vitest json, tsc, eslint (27), mypy 951.
3. Recette visuelle sur la pile jetable relancée (`pile-jetable-c6.sh`,
   17393 et 1420, jamais 17293) : accueil, accueil avec un verbe de l'établi
   cliqué et le canevas ouvert (760 px), Paramètres (boutons `ghost`), la
   mise en route (idem), une modale, une vue intégrée ; à 1280, 1024, 840 et
   800 px ; en clair, sombre et contraste élevé ; tailles de police petite,
   moyenne et grande mesurées au pixel sur un texte sans classe ; captures
   avant/après dans `.cartography-work/validation/da-lot1/` (ignoré par git),
   rapport `docs/da/2026-09-10-lot1-recette.md`. Vérifier : rien sous le
   composeur (e2e B-320 réécrit, lancé à part), anneau de focus visible sur
   rail et composeur, étiquettes en contraste élevé, barre non clippée.
4. Revue Grok du diff avant le tag, `/release-therese 0.71.0-alpha` avec le
   GO de Ludo.

## 10. Ce que ce lot ne fait pas

- Aucun fichier d'écran, de canevas ou de couche (palette, modales) n'est
  édité, sauf `QuickActions.tsx` (retrait de `card-brutal`) : ils gardent
  leurs classes et héritent de `body`, des titres sans classe, du focus et
  des primitives (`Button` surtout : 254 usages changent de taille, `ghost`
  de couleur).
- Aucun comportement ne change : les 3 392 pytest, 1 994 vitest et 99
  parcours e2e restent la vérité.
- Pas de nouvelle police, pas de nouveau jeton de couleur.
