# DA « Application affinée », lot 7 : l'écran Décision (Board) (design à challenger avant le code)

Version 7, 11/09/2026 10:52, après la revue de la v6 (8 points repris, 0 non
repris, plus quatre changements non écrits trouvés au passage) ; journal
`.cartography-work/reviews/opus-da-lot7-decision-design-v6.log`. Précédent : lot 3 (Tiroir), livré sur `main` ;
cadence : une seule release pour toute la DA (décision Ludo 11/09, 0.72.0-alpha
porte l'ensemble). Maquette :
`docs/da/2026-09-05-propositions/maquettes/decision.html` (états `normal`,
`encours`, `partiel`), critères de `ecrans.json` : « Cinq avis lisibles,
synthèse mise en avant, Markdown rendu. Synthèse présentée tôt ; cinq avis
et leurs divergences accessibles ; réponse partielle, interruption et échec
d'un conseiller prévus. » Déjà décidé côté UX, pas à rejuger : titre
« Décision » (lexique 0.48, `BoutonOuvrirLaVue` → « Ouvrir Décision ») ;
Markdown rendu dans le panneau (0.66.1, `CompactMarkdown`) ; consensus
qualifié, pas une fiabilité factuelle (revue 30/08) ; plafond de 30
décisions, total non mesuré ; confirmation avant lancement et consentement
`llm:board` ; annulation d'un Board engagé à confirmation dédiée.

## Ce que le lot change, en une phrase

La carte d'historique (`BoardHistoryCard`) et le canevas
(`BoardWorkspaceCanvas`, montés par la coque `ConversationCanvasPrototype.tsx`
aux lignes 1823 et 384) prennent la forme de la maquette en consommant les
primitives du lot 1 (`Carte`, `CarteTete`, `Ligne`, `Etiquette`, `Alerte`,
`EtatVide`, `Squelette`, `Button`, `Textarea`, `FormField`) ; les mêmes
données, les mêmes états, les mêmes destinations. Aucun appel réseau, aucun
store, aucun parcours ne change.

## Décisions tranchées par défaut (Ludo peut corriger)

1. **L'écran affiché n'est pas `BoardPanel.tsx`** (leçon B-613). `showBoardPanel`
   ouvre le dialogue classique via `PanelContainer` / `onOpenClassic`. On
   habille `BoardHistoryCard` et `BoardWorkspaceCanvas` dans
   `BoardConversationCard.tsx`. `BoardPanel`, `AdvisorCard`, `DeliberationView`,
   `AdvisorArcLayout`, `ModeSelector` hors lot.
2. Le canevas reste le panneau côte à côte (`max-w-[620px]`, `role="region"`,
   hotfix 0.48.1). La maquette est une page à 66 rem : page pleine = P-080.
3. Les cinq noms officiels restent (L'Analyste, Le Stratège, L'Avocat du
   Diable, Le Pragmatique, Le Visionnaire). Les noms maquette (Financier,
   Opérationnel, Voix du client, Contradicteur) sont P-088.
4. Les portraits (`CharacterPortrait` index 1 à 5) restent l'avatar de
   chaque conseiller (le glyphe lettre de la maquette est un bouche-trou).
5. La formulation de la maquette remplace les mentions techniques là où
   l'état est le même (tête du canevas, statut enregistré / en cours /
   partielle, « Réfléchit… », « Avis non rendu », « Synthèse en préparation,
   elle arrive après le dernier avis. »). Les états sans équivalent maquetté
   (erreur de flux sans avis, sauvegarde non vérifiée, annulée, formulaire,
   historique vide / erreur) gardent leur prose.
6. Toute taille de bouton est `md` (36 px, le `.btn` du socle
   `min-height: 2.25rem`, `base.css:60`) ou `icon` (36 px) ; `sm` n'y
   est pas employé. « Préparer la délibération » aussi, en `md` (lot 1
   garde `lg` pour un écran qui l'a maquetté ; `decision.html` n'a que des
   `.btn` à 2,25 rem).
7. Le radiogroup Cloud / Souverain (roving, descriptions) reste un
   `radiogroup` ; `Segments` n'est pas monté ici.
8. **Toute icône lucide de l'écran est en 18 px** (`className="h-[18px] w-[18px]"`,
   comme le lot 2, `TodayDashboardCard.tsx:191`, `:303`, `:314`), sauf les deux
   tailles nommées de `Spinner` (`ligne` 14 px, `bouton` 16 px,
   `Spinner.tsx:17-24`, qui n'a pas de 18 px). Les icônes décoratives portent
   `aria-hidden="true"`, sauf celles qui vivent déjà dans un `Button` ou une
   prop `icone` (le texte du bouton et le titre de l'`Alerte` les nomment ;
   `Alerte.tsx:32` pose lui-même l'attribut). La table complète — reprise ou
   abandon, icône par icône — est au § 4bis.
9. **Tout `Button` qui porte une icône reçoit `className="gap-1.5"`** :
   `Button` est `inline-flex items-center justify-center` sans `gap`
   (`Button.tsx:22`), là où les boutons maison d'aujourd'hui écrivent
   `gap-1.5` à la main (`BoardConversationCard.tsx:104`, `:185`, `:253`,
   `:255`). Sans cette classe, l'icône colle au texte.

## 1. La carte d'historique : `BoardHistoryCard`

Maquette : pas de liste (elle ouvre déjà une décision). On habille la carte
du scénario `board` (entrée), comme le brief du lot 2.

Constante locale `CLASSE_BOUTON_VUE` (même chaîne que
`TodayDashboardCard.tsx:84-85`, extraire dans un module partagé si Accueil
et Décision bougent dans le même commit, sinon recopier **cette** chaîne,
pas une variante) :

`inline-flex h-9 items-center rounded-md border border-border bg-surface px-4 text-sm font-semibold text-text transition-colors hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg`

| Élément | Aujourd'hui | Cible |
|---|---|---|
| Cadre | `section` ombre `rgba`, `data-testid="board-history-card"` | `Carte as="section" className="overflow-hidden"` `aria-labelledby="board-history-title"` même testid ; `shadow-sm` (celle de `Carte`, l'ombre `rgba` d'aujourd'hui disparaît). **`overflow-hidden` est conservé** (`BoardConversationCard.tsx:94`) et il ne l'est pas par habitude : `Carte` ne pose que `bg-surface border border-border rounded-md shadow-sm` (`Carte.tsx:20`) et la dernière `Ligne` est le dernier élément de la carte, sans pied pour la couvrir (au contraire de l'Accueil, `TodayDashboardCard.tsx:376`) ; son `hover:bg-surface-2` n'a pas de rayon (`Ligne.tsx:63`) et déborderait les deux coins arrondis du bas. Le pseudo-élément étiré du titre (`before:inset-0` de la rangée) et l'anneau de focus vivent à 16 px des bords (`px-4`) : rien à rogner |
| Tête | portrait index 1 + `h2` « Décision » + meta | `CarteTete idTitre="board-history-title"` icône `Gavel` 18 px, titre « Décision » ; meta inchangée : chargement « Lecture de l'historique local » ; `ready` → `libelleDecisionsChargees(n)` (`n >= 30` : « n décisions chargées (total non mesuré) » ; sinon « n décision(s) enregistrée(s) », pluriel `n > 1`) |
| Actions | boutons maison « Nouvelle question » + `BoutonOuvrirLaVue` | `Button variant="primary" size="md"` « Nouvelle question », `Plus` 18 px, même `onNewBoard` ; `BoutonOuvrirLaVue vue="board"` `className={CLASSE_BOUTON_VUE}`, libellé « Ouvrir Décision » inchangé |
| Run en cours | bouton `data-testid="board-current-run"`, rangée entière teintée `bg-domaine-prospects-tint border-b border-domaine-prospects/30`, titre `text-xs` | `<div data-testid="board-current-run">` enveloppe `Ligne` (pas une prop de `Ligne` : `Ligne.tsx:26-35` n'a ni rest props ni `data-testid`) ; `Ligne domaine="prospects"` `onClick={onOpenCurrent}` puce = `Spinner taille="bouton"` (16 px, dans la puce `h-8`, comme lot 2 ; `Spinner` n'a pas 18 px : `ligne` 14, `bouton` 16, `zone` 24, `Spinner.tsx:17-24`) / `CheckCircle2` 18 px / `AlertCircle` 18 px selon `running` / `complete` / autre ; titre = `run.question` en `text-sm`, `coupe` (même question longue) ; detail = `run.phase \|\| run.status` ; `ChevronRight` 18 px muted. **La teinte de fond de la rangée est volontairement abandonnée** (aucune classe de fond, ni sur la `Ligne`, ni sur le `div` enveloppe) : dans la DA, un domaine colore sa **puce**, pas sa rangée (`Ligne.tsx:69-77`, `FOND_DOMAINE` n'est posé que sur le `span` de la puce), et l'Accueil n'a aucune rangée teintée (`TodayDashboardCard.tsx:300-319`). Une seule rangée peinte au-dessus de cinq rangées nues serait la seule de l'application. Ce que la rangée dit reste dit : la puce porte le `Spinner` tant que le run tourne, et `detail` porte la phase en clair. Le `border-b` d'aujourd'hui part aussi : `Ligne` porte son propre `border-t` (`Ligne.tsx:63`), et les deux feraient un double filet |
| Lignes | bouton flex, reco + date `text-xs`, `truncate` | `Ligne domaine="prospects"` puce `History` 18 px, `onClick={() => onOpenDecision(id)}` ; titre = `decision.question`, **coupé à une ligne** par la prop `coupe` (ci-dessous, `Ligne` du lot 1) ; `Ligne.detail` = `decision.recommendation` **seul** (le `p` de `Ligne.tsx:80` a ce textContent exact : le test `getByText(synthesis.recommendation)` de `BoardConversationCard.test.tsx:51-52` reste vert ; une concaténation `reco · date · mode` le casserait, matcher exact par défaut) ; `droite` = `<span className="text-sm text-text-muted">{formatDate(decision.created_at)}{decision.mode ? ' · ' + (decision.mode === 'sovereign' ? 'Souverain' : 'Cloud') : ''}</span>` (sans « Mode », scan d'une liste de 5 ; le canevas § 3.1 porte « Mode souverain » / « Mode cloud »). **Segment de mode seulement si `decision.mode` est renseigné** : `BoardDecisionResponse.mode` est optionnel (`board.ts:54`) et aujourd'hui `BoardConversationCard.tsx:130` écrit « Cloud » sur un enregistrement sans mode, donc affirme un fait non mesuré ; aucune assertion ne porte sur cette chaîne (`BoardConversationCard.test.tsx` ne cherche « Souverain » que dans le radiogroup du formulaire, `:74`). Même règle qu'en meta du canevas § 3.1 : la liste et le détail ne donnent pas deux réponses au même enregistrement + `Etiquette ton={high → succes, medium → neutre, low → neutre, sinon neutre}>{confidenceLabel(decision.confidence)}</Etiquette>` (jamais `erreur` : un consensus faible est un accord entre avis, revue 30/08, `BoardConversationCard.tsx:64-70` « Consensus faible ») + `ChevronRight` 18 px. Date et mode restent dans la ligne (`droite`) **et** dans la meta du canevas § 3.1 |

**La seule primitive du lot 1 qui bouge dans ce lot : `Ligne` gagne une prop
`coupe?: boolean` (défaut `false`), dans le même commit que l'écran.** Sans
elle, la liste perd la coupe d'aujourd'hui (`BoardConversationCard.tsx:130`,
`truncate` sur la question **et** sur la reco) : `Ligne.tsx:80` rend le
détail dans un `p` sans `truncate` et sans classe transmissible.
**Les deux chiffres de la v5 étaient faux** (revue v5, point 6) : la carte
n'affiche pas trente rangées mais **cinq** (`BoardConversationCard.tsx:90`,
`resource.data.decisions.slice(0, 5)`, le plafond de 30 portant sur la
ressource chargée, pas sur la liste rendue), et elle ne vit pas dans le
panneau de 620 px mais dans la colonne principale
(`ConversationCanvasPrototype.tsx:1823` la monte dans le bloc `:1688`,
`max-w-[760px]` canevas ouvert, `max-w-colonne` sinon ; les 620 px sont le
canevas, `:333`). La prop ne tient donc ni sur un volume de liste ni sur
une largeur de panneau : **elle tient sur ce qu'elle préserve**. Sans
elle, une question réelle de 90 caractères et sa recommandation prennent
deux à trois lignes chacune dans une rangée de 760 px au plus (canevas
ouvert ; `max-w-colonne` sinon), les cinq rangées
cessent d'être de même hauteur, les dates de `droite` ne s'alignent plus,
et la coupe qui existe aujourd'hui (`:130`) est perdue au passage à
`Ligne`. `coupe` ajoute
`block w-full truncate` au libellé (le `button` étiré quand la rangée est
cliquable, le `span` sinon) et `truncate` au `p` du détail. **Jamais
`relative` sur ce bouton** : son `before:absolute before:inset-0` se cale
sur la rangée `relative` (`Ligne.tsx:65`) ; le positionner rabattrait le
pseudo-élément sur le texte et tuerait le clic étiré (P1 de la revue du lot
1, `Ligne.test.tsx:109-131`). `block w-full` est nécessaire : un `button`
inline-block à largeur automatique déborde la cellule `1fr` au lieu d'être
coupé. Défaut `false` : le seul autre composant qui monte `Ligne`
(`TodayDashboardCard.tsx`, lot 2) ne la passe pas, son rendu et
`Ligne.test.tsx` sont inchangés. La ligne d'historique Décision la passe,
le run en cours aussi (même question longue).

## 2. Le canevas : `BoardWorkspaceCanvas`

Panneau inchangé (largeur, fermer, `role="region"`). Pied : `BoutonOuvrirLaVue`
comme en tête de carte (`className={CLASSE_BOUTON_VUE}`). Bandeau : conserver
`className="border-b border-border px-5 py-4 pr-16"` (`BoardConversationCard.tsx:315`)
; `BoutonFermerLePanneau` est `absolute right-4 top-3.5` et porte le mot
« Fermer » (`BoutonFermerLePanneau.tsx:21`) : sans `pr-16` le `h2` « Décision »
passe sous le bouton.

| Élément | Aujourd'hui | Cible |
|---|---|---|
| Bandeau | `div` `border-b border-border px-5 py-4 pr-16` (`:315`) | **mêmes classes** `px-5 py-4 pr-16` (`pr-16` inclus) |
| Sur-titre | « Board réel » uppercase 12 px | retiré (mention technique) |
| `h2` | « Délibération stratégique » / « Décision enregistrée » | « Décision » toujours (pas d'`id` aujourd'hui, on n'en invente pas) ; **classes inchangées, `text-xl` compris** (`BoardConversationCard.tsx:315` `mt-2 text-xl font-bold tracking-[-0.02em] text-text`) : les sept autres bandeaux de canevas de la coque portent la même chaîne sur leur `h2` (`AtelierConversationCard.tsx:355`, `CalculatorWorkspaceCanvas.tsx:287`, `DeliverablesWorkspaceCanvas.tsx:288`, `EmailConversationCard.tsx:361`, `MeetingConversationCard.tsx:448`, `ContactsMemoryCard.tsx:171`, `InvoiceConversationCard.tsx:699` ; chez Atelier et Board, le `h2` est sur la même ligne que le `div` du bandeau) et les réduire est hors lot ; c'est donc la **question** qui descend d'un cran (§ 3.1, `text-lg`) |
| Sous-titre | « Cinq regards… » | inchangé |

Ordre du corps, identique à `BoardWorkspaceCanvas.tsx:317-323` : 1) resource
loading ; 2) resource error ; 3) `showRun` ; 4) formulaire si `new-board` /
`current` ; 5) decision loading ; 6) decision error ; 7) `DecisionDetail`.

## 3. Question, statut, synthèse, avis

Ordre dans `BoardRunView` et `DecisionDetail`, de haut en bas : question
(§ 3.1), **progression et phase** (§ 5, `BoardRunView` et `run.status ===
'running'` seulement), synthèse (§ 3.2 : carte pleine si elle existe,
**placeholder** si `run.status === 'running'` sans `run.synthesis`), avis
(§ 3.3), divergences (§ 3.4, seulement si une synthèse existe), extraits
web, ligne d'usage de la synthèse, bandeaux d'état (§ 5), pied d'actions.
La barre et la phase restent **au-dessus** des avis : juste après la
`Carte` question et **hors** de cette carte (c'est un état, pas la
question), avant la carte synthèse, comme aujourd'hui
(`BoardConversationCard.tsx:173`, immédiatement avant la grille `:175`).
Pendant un `running`, le seul indicateur vivant ne doit pas tomber sous
cinq cartes qui coulent, dans un panneau de 620 px à défilement
(`ConversationCanvasPrototype.tsx:333`). Ce qui reste en bas de § 5, ce
sont les fins de course (`error`, `persistence_error`, `cancelled`), la
confirmation d'annulation et le pied. Extraits et usage n'existent
aujourd'hui que dans `DecisionDetail` (`BoardConversationCard.tsx:281-283`,
après `SynthesisView`) : ils restent là, mais **après** les divergences et
**avant** les bandeaux (absents du détail) et le pied. `BoardRunView` n'a
ni extraits ni usage : question → progression (`running`) → synthèse →
avis → divergences → bandeaux § 5 → pied. La synthèse passe **au-dessus**
des avis (critère « présentée tôt ») ; les gestionnaires ne changent pas.

Les deux conteneurs **gardent leur `data-testid`** alors que § 3.1 et § 3.3
réécrivent tout leur intérieur : `data-testid="board-run-view"` sur le `div`
de `BoardRunView` (`BoardConversationCard.tsx:170`) et
`data-testid="board-decision-detail"` sur celui de `DecisionDetail` (`:262`).
Quatre assertions de `BoardConversationCard.test.tsx` passent par
`board-decision-detail` (`:114`, `:115`, `:140`, `:141`) : les perdre
casserait la suite pour une raison qui n'a rien à voir avec le lot.
`board-run-view` n'en porte aucune aujourd'hui et reste quand même (recette
§ 8 et garde § 6.2).

### 3.1 Question

`Carte as="section" className="p-4"`. **Marge intérieure explicite** :
`Carte` n'en pose aucune (`Carte.tsx:20`, `bg-surface border border-border
rounded-md shadow-sm` et rien d'autre), donc sans classe la carte colle son
texte au bord. `p-4` = les 16 px d'aujourd'hui
(`BoardConversationCard.tsx:171` et `:263`) et les 16 px horizontaux de
`CarteTete` (`px-4`, `Carte.tsx:42`), la seule tête montée dans ce lot
(§ 1). La maquette met 16 px en haut et 24 px sur les côtés
(`decision.html:5`, `.question{padding:var(--espace-3) var(--espace-4)}`,
`base.css:13` `--espace-3: 1rem`, `--espace-4: 1.5rem`) : c'est la
respiration d'une page de 66 rem, elle revient avec P-080, le panneau de
620 px garde 16 px sur les quatre côtés.
`h3 className="text-lg font-bold leading-6"` = la
question (le label uppercase 12 px « Question soumise » / « Décision du … »
sort : la date va dans la meta). **`text-lg` (1,125 rem), pas `text-xl`** :
le `h2` « Décision » du bandeau garde `text-xl` (§ 2, chaîne commune aux sept
autres canevas de la coque), et un `h3` aussi gros que le `h2` qui le domine
contredirait le socle (`maquettes/da/base.css:50-51`, `h2` 1,1875 rem,
`h3` 1 rem). La maquette met la question à 1,25 rem parce qu'elle y est le
`h1` d'une page de 66 rem (`decision.html:6`, `.question h1`) : la page
pleine P-080 le rétablira, le panneau de 620 px reste un cran en dessous.
Meta `text-sm font-medium text-text-muted`,
segments séparés par « · » :

- **une seule** `Etiquette` de statut (jamais recopiée en bandeau § 5).
  Les branches `run.status` s'appliquent **uniquement** dans `BoardRunView`
  (le composant qui reçoit `run`). `DecisionDetail` ne reçoit pas `run`
  (`BoardConversationCard.tsx:260`) : il ne le lit pas. `showRun`
  (`:312`) = `run.status !== 'idle' && (target === 'current' || target ===
  'new-board')` : l'intersection `run.status === 'complete'` et
  `DecisionDetail` est presque vide (`showRun` garde `BoardRunView` tant
  que le run n'est pas `idle` et que la cible est `current` / `new-board`)
  ; un détail ouvert pendant un run vivant (cible = id, `showRun` faux, le
  flux continue) ne doit **pas** recevoir l'étiquette du run (`en cours` /
  `partielle`) sur une décision déjà sauvegardée. Un `DecisionDetail` avec
  `run` idle n'a plus le bandeau vert actuel (§ 5 retiré) : c'est l'état
  `normal` de la maquette, porté par l'étiquette ci-dessous.
  - **`DecisionDetail`** : toujours `Etiquette ton="succes"` « Décision
    enregistrée » (maquette `#statut-normal`, `decision.html:63`,
    `ecrans.json` « normal: Décision enregistrée »), **sans** lire `run` ;
  - **`BoardRunView`**, `run.status === 'running'` : `Etiquette ton="info"`
    « Délibération en cours · N/5 avis » (N = `completed`, même compteur
    que `aria-valuenow` de la barre) ;
  - **`BoardRunView`**, `run.status === 'complete'` : `Etiquette
    ton="succes"` « Décision enregistrée » ;
  - **`BoardRunView`**, `run.status === 'error'` et au moins un avis rendu
    (contenu non vide **ou** `isComplete`) : `Etiquette ton="attention"`
    « **Délibération partielle · N avis rendu** » (`s` à `rendu` seulement si
    `N > 1` : « avis » est invariable), N = nombre d'avis avec contenu non vide **ou** `isComplete`,
    **le même prédicat** que « au moins un avis rendu » et que l'affichage de
    l'étiquette ; pas `completed` seul : un avis interrompu avec du texte
    compte dans N, un avis vide coincé `isRunning: true` ne compte pas.
    **Le dénominateur de la maquette n'est pas repris** (revue v6, point 2).
    `#statut-partiel` écrit « Délibération partielle · 4/5 avis »
    (`decision.html:63`) parce que la maquette est un état figé où quatre
    conseillers sur cinq ont répondu ; dans l'application, `run.status ===
    'error'` et cinq avis rendus coexistent sans difficulté — un
    `chunk.type === 'error'` posé à la synthèse ou à la sauvegarde ne touche
    pas `advisors` (`usePrototypeBoardData.ts:244-246`) —, et « Délibération
    partielle · 5/5 avis » dirait partiel et complet dans la même phrase.
    **La branche « N = `completed` » que proposait la revue ne ferme pas ce
    cas non plus** : cinq `isComplete` suivis d'une erreur donnent
    `completed === 5` tout autant. Seul le retrait du dénominateur le ferme,
    et il ne coûte rien : le total vit déjà dans le segment suivant de la
    même meta (« 5 conseillers », ci-dessous) ;
  - **`BoardRunView`**, sinon : pas d'étiquette de statut dans la meta
    (échec sans avis, `persistence_error`, `cancelled` : bandeaux § 5
    seulement) ;
- mode : en `BoardRunView`, **toujours**
  `run.mode === 'sovereign' ? 'Mode souverain' : 'Mode cloud'`
  (`BoardRunState.mode` n'est pas optionnel, `usePrototypeBoardData.ts:39` ; le
  formulaire en pose toujours un, `BoardConversationCard.tsx:193`). En
  `DecisionDetail`, **le segment n'existe que si `decision.mode` est
  renseigné** (`BoardDecisionDetail.mode?: string`, `board.ts:74`) : une
  décision enregistrée avant le suivi du mode sortirait « Mode cloud » par
  défaut, c'est-à-dire un fait non mesuré affiché comme mesuré. Le préfixe
  « Mode » reste **uniquement** dans la meta du canevas (maquette
  `decision.html:63` « Mode souverain ») ; la ligne d'historique § 1 garde
  « Souverain » / « Cloud » sans « Mode » (scan) **et la même condition
  d'existence** ;
- nombre de conseillers : en `BoardRunView`, « 5 conseillers » (les cinq
  cartes existent par construction, `advisorOrder.map`, § 3.3) ; en
  `DecisionDetail`, `{decision.opinions.length} conseiller` suivi de `s` si
  `decision.opinions.length > 1` — `opinions` est la liste réellement
  sauvegardée (`board.ts:62-72` ; la fixture n'en a qu'une,
  `BoardConversationCard.test.tsx:22`), et le détail ne doit pas annoncer
  cinq avis quand il en affiche un (§ 3.3, « on n'invente pas un avis
  manquant »). `DecisionDetail` n'a aujourd'hui ni l'un ni l'autre segment
  (`BoardConversationCard.tsx:262-267`) : les deux constantes « 5
  conseillers » et « Mode cloud » y seraient des inventions du lot ;
- en `DecisionDetail` seulement : `formatDate(created_at)` (helper actuel,
  « Date inconnue » inchangé) ;
- en run `complete` seulement, si `run.decisionId` : `Identifiant : {run.decisionId}`
  (même chaîne qu'aujourd'hui, `BoardConversationCard.tsx:183`) ;
- `decision.context` / `run.context` inchangé, sous la meta, `text-sm`.

Pas de durée, pas de « Contexte lu : contact, 2 devis » (P-080).

### 3.2 Synthèse (`data-testid="board-synthesis"` conservé)

**Ne pas monter `CarteTete`** dans le canevas (`CarteTete` impose un `h2`,
`Carte.tsx:52` ; le canevas a déjà le `h2` « Décision », la question un
`h3` : ordre h2 → h3 → h2 interdit). Tête à la main, mêmes classes que
`CarteTete` : conteneur `flex flex-wrap items-center gap-3 px-4 pt-4 pb-2` ;
**pastille reprise de la maquette** (`decision.html:68`,
`div.carte-tete > .icone`), recopiée à la main puisque `CarteTete` n'est pas
monté ici : `<span aria-hidden="true" className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-accent-tint text-accent">`
(chaîne exacte de `Carte.tsx:43-50`) contenant
`<Gavel className="h-[18px] w-[18px]" />` (lucide, **déjà importé**,
`BoardConversationCard.tsx:9`). Le glyphe de la maquette (axe vertical et
deux chevrons opposés) n'est pas repris tel quel : son équivalent lucide,
`ChevronsUpDown`, signifie « trier » ou « déplier » dans une interface, ce
qu'une pastille décorative ne doit pas laisser croire. **La v5 mettait
`Scale` ici ; le motif qui écarte `ChevronsUpDown` l'écarte aussi** (revue
v5, point 5) : `Scale` porte déjà un sens dans l'application, et dans le
**même groupe** `decide` (`CapabilityCenter.tsx:262`, `id: 'legal', group:
'decide', title: 'Références juridiques', icon: Scale`). Une balance en tête
de la synthèse d'une Décision renverrait au juridique. Le glyphe de
Décision est `Gavel` partout ailleurs (`CapabilityCenter.tsx:250`
`id: 'decision-board'`, `components/chat/CommandPalette.tsx:67`
`'board.open'`, `lib/etabli.ts:16`), et ce design l'emploie déjà en tête de
la carte d'historique (§ 1) et sur « Préparer la délibération » (§ 4). Le
répéter sur la pastille ne crée pas d'ambiguïté : la pastille est le glyphe
de **domaine**, pas un bouton (`Carte.tsx:5-6`, « c'est le glyphe de
domaine, pas un bouton ») ; elle dit « cette carte appartient à Décision ».
Titre en `h3` « Synthèse » (sans
classe : `@layer base` 1 rem) ; meta `p className="text-xs font-medium text-text-muted"`
« **Ce que les avis ont en commun, et ce qui les sépare** » : chaîne
maquette `normal` (`decision.html:68`) **privée de son nombre** (revue v5,
point 1). La v5 écrivait « les cinq avis » dans les trois montages, y
compris sous un `DecisionDetail` à une seule opinion (fixture
`BoardConversationCard.test.tsx:22`, montée en détail par le test `:106`)
et sous un run partiel à quatre avis, et `decision.synthesis` n'est pas
optionnel (`board.ts:73`), donc cette carte s'affiche **toujours** en
détail. C'est exactement ce que § 3.1 interdit trente lignes plus haut
(« le détail ne doit pas annoncer cinq avis quand il en affiche un ») et ce
que la recette § 8 vérifie (« un détail à une seule opinion qui annonce
« 1 conseiller » »). Le N de § 3.1 n'est pas réemployé ici non plus : le
compte est déjà dans l'étiquette de statut **et** dans le segment
« N conseiller(s) » de la meta de question ; une troisième occurrence du
même chiffre sur le même écran n'ajoute rien et fait un troisième endroit
à tenir juste. La formule sans nombre est vraie des trois états. L'état
maquette `partiel` récrit la phrase entière (`decision.html` script l.97 :
« Ce que les quatre avis rendus ont en commun ; le Contradicteur n'a pas
répondu ») : **on ne suit pas** ; en `error` avec avis manquant, même meta
(pas de synthèse provisoire sans API).

**Marge intérieure du corps, écrite une fois pour les deux montages qui
rendent quelque chose** : `px-4 pb-4` sur le conteneur du corps, soit 16 px
sur les côtés et en bas et **rien en haut**, la tête recopiée ci-dessus
finissant déjà par `pb-2`. C'est la maquette telle quelle
(`decision.html:10`, `.synthese .texte-synthese{padding:0 var(--espace-3)
var(--espace-3)}`, `--espace-3: 1rem`, `base.css:13`), et le placeholder
prend la même valeur (la maquette lui donne `padding:var(--espace-3)` en
attribut `style`, `decision.html:75` : mêmes 16 px). Sans cette classe, les
deux corps collent au bord : `Carte` ne pose aucune marge (`Carte.tsx:20`).

Trois montages, un seul `data-testid="board-synthesis"` :

1. **`run.status === 'running'` et pas de `run.synthesis`** (état maquette
   `encours`, `decision.html:75` `#attente`, script `:95`) : `Carte as="article"
   className="border-l-[3px] border-l-accent-fill"`, tête ci-dessus, corps
   `<div className="px-4 pb-4">` contenant
   `<p className="text-sm text-text-muted">Synthèse en préparation, elle arrive après le dernier avis.</p>`
   + deux `Squelette` `largeur="w-[80%]"` et `largeur="w-[60%]"` (comme
   `.attente .chargement`, `decision.html:31-32`). Pas un trou.
2. **`run.synthesis` ou `decision.synthesis` existe** : même `Carte as="article"
   className="border-l-[3px] border-l-accent-fill"`, même tête, corps
   `<div className="px-4 pb-4">`. Bloc recommandation, **icône et intitulé
   repris de la maquette** (revue v5, point 7) : conteneur
   `flex items-start gap-3 rounded-sm bg-accent-tint p-3`, puis
   `<Check aria-hidden="true" className="h-[18px] w-[18px] shrink-0 text-accent" />`
   (lucide `Check`, le tracé `M20 6L9 17l-5-5` de la maquette,
   `decision.html:70` ; **import à ajouter**, le bloc `lucide-react` de
   `BoardConversationCard.tsx:4-18` a `CheckCircle2` mais pas `Check`), puis
   `<p className="text-sm"><span className="font-semibold text-accent">Recommandation : </span><b className="text-accent">{synthesis.recommendation}</b></p>`.
   **L'intitulé est un élément frère du `<b>`, jamais concaténé à la
   donnée** : le `textContent` du `<b>` reste exactement
   `synthesis.recommendation`. C'est la condition qui garde les assertions
   vertes : `getByText(synthesis.recommendation)`
   (`BoardConversationCard.test.tsx:51-52`, carte d'historique, matcher
   exact) et les deux `toHaveTextContent` du détail (`:114-115`,
   sous-chaîne, indifférents au préfixe). La v5 retirait les deux sans le
   dire, alors que l'écran d'aujourd'hui affiche bien le mot
   (`BoardConversationCard.tsx:143`, `<div className="text-xs font-semibold
   uppercase tracking-[0.12em] text-success">Recommandation</div>`) et que
   la maquette l'écrit dans le gras (« Recommandation : accepter, à deux
   conditions. »). Ce qui **est** abandonné ici, volontairement : le
   sur-titre uppercase 12 px (forme, remplacée par l'intitulé en ligne, et
   `text-xs` de toute façon proscrit § 6.7 s'il tombait dans un sous-arbre
   interactif) et la teinte `success` du bloc actuel, la maquette posant
   `accent-tint`. Sous la reco :
   `Etiquette ton={high → succes, medium → neutre, low → neutre, sinon neutre}>{confidenceLabel(synthesis.confidence)}</Etiquette>`
   (le badge actuel de `SynthesisView`, `BoardConversationCard.tsx:143` ;
   il reste aussi sur la ligne d'historique). Consensus : `h4 className="text-sm font-bold text-text"`
   « Consensus » (aujourd'hui `BoardConversationCard.tsx:145` `h4 className="text-xs font-bold text-text"`),
   puis liste `ul` `text-sm`, `CheckCircle2` 18 px `text-success`, rôle
   visuel seulement. Prochaines étapes : `h4 className="text-sm font-bold text-text"`
   « Prochaines étapes » (aujourd'hui `:148`), puis `ol` numérotée `text-sm`,
   mêmes `next_steps`. Pas de bouton Copier ni « Créer les tâches » (P-081).
   `CompactMarkdown` n'est pas monté sur la synthèse (aujourd'hui du texte
   brut) : inchangé.
3. **Sinon** (pas de synthèse et pas `running`) : pas de carte synthèse.

### 3.3 Avis

Grille **`grid grid-cols-[repeat(auto-fill,minmax(16rem,1fr))] gap-3`**, le
modèle de la maquette (`decision.html:15`,
`.avis{grid-template-columns:repeat(auto-fill,minmax(16rem,1fr))}`) repris
tel quel (revue v6, point 1). Ni `sm:grid-cols-2`, ni le `xl:grid-cols-2`
d'aujourd'hui (`BoardConversationCard.tsx:175` et `:268`). La v6 écrivait
`grid-cols-1 sm:grid-cols-2` « le panneau fait 620 px » : **les deux moitiés
étaient fausses**. Le panneau ne fait pas 620 px, il fait
`w-full max-w-[620px] sm:w-[calc(100%-48px)] xl:relative xl:w-[43%] xl:min-w-[440px]`
(`ConversationCanvasPrototype.tsx:333`), soit 440 px au plancher sous `xl`,
où deux colonnes fixes tomberaient à ~205 px, sous le plancher de 16 rem que
le design invoquait lui-même comme modèle. Et un point de rupture `sm`
aurait changé le rendu à trois des quatre largeurs de la recette sans qu'une
ligne l'annonce.

Le nombre de colonnes est alors **dérivé de la largeur réelle du panneau**,
pas d'un point de rupture de fenêtre : corps du canevas = panneau moins
`p-5` (40 px, `BoardConversationCard.tsx:316`), deux colonnes tiennent dès
`2 × 256 + 12 = 524 px`, trois en demanderaient 792.

| Largeur de fenêtre | Panneau | Corps | Colonnes |
|---|---|---|---|
| 1280 px (`xl`, côte à côte) | `43 %` = 550 px | 510 px | **1** |
| 1024 px (calque) | `min(100 % − 48, 620)` = 620 px | 580 px | **2** |
| 840 px (calque) | 620 px (plafond `max-w`) | 580 px | **2** |
| 800 px (calque) | 620 px (plafond `max-w`) | 580 px | **2** |

L'inversion est réelle et voulue : à 1280 px le panneau **partage** la
fenêtre avec la colonne principale et n'en prend que 43 %, alors qu'en
dessous il est un calque plafonné à 620 px. Une carte d'avis y reste au
moins à 256 px, jamais à 205. À 440 px (le plancher `xl:min-w`), une seule
colonne. La page pleine de 66 rem (P-080) en donnera trois sans changer
cette chaîne : c'est l'intérêt d'`auto-fill`.

Cinq cartes dans `advisorOrder` pour le run ; pour le
détail, `decision.opinions` tel quel (on n'invente pas un avis manquant).
Chaque avis : `Carte as="section" className="p-3"` (le test Markdown fait
`closest('section')`). **Marge intérieure** : `p-3`, les 12 px
d'aujourd'hui (`BoardConversationCard.tsx:155` pour le run, `:270` pour le
détail), `Carte` n'en posant aucune (`Carte.tsx:20`). La maquette met 16 px
(`decision.html:16`, `.avis .carte{padding:var(--espace-3)}`) dans une page
de 66 rem ; la grille est désormais la même, c'est le contenant qui diffère
— deux colonnes de ~284 px dans un panneau de 620 px, où 16 px de chaque
côté prennent sur un texte déjà étroit. Les 16 px reviennent avec la page
pleine (P-080).
Tête : portrait `h-8 w-8 rounded-full` sans bordure ni ombre ; **pas de
`h4` pour le nom**. La raison écrite en v5 était fausse (revue v5,
point 2) : le `h3` « Où les avis divergent » de § 3.4 ne vient pas « après
des non-titres », et remonter d'un `h4` à un `h3` entre deux blocs frères
ne casse aucun plan. La vraie rupture est **à l'intérieur** de la carte :
`CompactMarkdown` rend `h1`, `h2` **et** `h3` Markdown en `<h3>`
(`CompactMarkdown.tsx:11-13`, `mb-2 mt-3 text-sm font-bold first:mt-0`), et
un avis en contient, voir la fixture `BoardConversationCard.test.tsx:124`
(`'### Points de vigilance…'`), assertion `getByRole('heading', { name:
'Points de vigilance' })` `:134`. Un nom en `h4` serait donc le titre d'une
carte **dominé** par les titres de son propre contenu. Conséquence assumée
par écrit : les cinq `h4` du run (`BoardConversationCard.tsx:156`) sortent
du plan du document. Le plan de l'écran reste h2 (« Décision », bandeau
§ 2) → h3 (question § 3.1, « Synthèse » § 3.2, titres Markdown des avis,
« Où les avis divergent » § 3.4) ; les noms se repèrent au portrait et à la
graisse, comme dans le détail d'aujourd'hui (`:273`, déjà un `strong`) et
dans la maquette (`decision.html:78`, `<b>La Stratège</b>`).
Nom = `strong className="block text-sm font-semibold"` =
`info.name` / `opinion.name` (détail actuel `BoardConversationCard.tsx:273`
déjà en `strong` ; maquette `decision.html:78` `<b>La Stratège</b>`, pas un
titre) ; meta **`p className="truncate text-sm text-text-muted"`**
= `advisor.provider \|\| info.personality` (run) ou
`provider · modèle · coût` (détail, `formaterCout`, « provider inconnu » /
« modèle non mesuré » inchangés). **`truncate` est conservé** (revue v6,
point 5) : il existe aux deux montages aujourd'hui
(`BoardConversationCard.tsx:156` et `:273`), et la carte passe dans une
colonne d'environ 284 px alors que la meta du détail concatène trois
segments (`provider · modèle · coût`) et que celle du run peut porter une
personnalité entière (« Vision et positionnement », `decision.html:78`).
Sans lui, une carte d'avis serait la seule surface de l'écran dont la
deuxième ligne pousse la grille. Le `min-w-0 flex-1` du conteneur reste
(`BoardConversationCard.tsx:156`) : sans lui, `truncate` ne coupe rien dans
une piste flex. **En détail, la meta n'est rendue que si
`opinion.provider \|\| opinion.model`** : garde actuelle de
`BoardConversationCard.tsx:273`, conservée telle quelle. Sans elle, une
décision enregistrée avant le suivi des fournisseurs afficherait
« provider inconnu · modèle non mesuré » sur chaque carte là où rien n'est
affiché aujourd'hui, ce qui prend à revers le test « rend le détail
sauvegardé sans inventer les providers historiques »
(`BoardConversationCard.test.tsx:106`, fixture sans `provider` ni `model`,
`:22`). Pastille lettre S/F/O/C hors lot.
Position Accepte / Refuse : P-088. Icônes de tête (run
`AdvisorOpinionCard` seulement, à droite du nom) : **dérivées de la table
du corps ci-dessous**, pas de `isRunning` / `isComplete` seuls.
Aujourd'hui `:156` : `isRunning` → `Spinner taille="ligne"`, `isComplete`
→ `CheckCircle2`, sinon pastille `h-2 w-2 rounded-full bg-border` ; après
`error`, un conseiller coincé `isRunning: true` garde le Spinner à côté de
« Avis non rendu » ou du `CompactMarkdown`. `DecisionDetail` n'a pas ces
icônes (`:271-274`) : on n'en invente pas.

`PrototypeAdvisorState` n'a que `isRunning` / `isComplete`
(`usePrototypeBoardData.ts:19-26`) ; `chunk.type === 'error'` pose
`run.status = 'error'` et ne touche pas `advisors` (`:244-246`) : un
conseiller interrompu reste `isRunning: true` **avec son contenu déjà
reçu** (l'avis partiel, aujourd'hui affiché : `BoardConversationCard.tsx:157-161`
montre le contenu dès qu'il existe) ; un conseiller jamais parti n'est
pas dans `run.advisors`. L'`Alerte` § 5 promet « Les avis partiels
restent visibles ». D'où la table, **dérivable**, premier match :

| État de l'avis | Cible |
|---|---|
| contenu non vide et `run.status === 'running'` et `isRunning` | texte `whitespace-pre-wrap text-sm` + curseur pulse (streaming, pas de Markdown) |
| contenu non vide, tout autre cas (y compris `isComplete`, `DecisionDetail`, **et** `isRunning: true` coincé après `error` / `persistence_error` / `cancelled`) | `CompactMarkdown className="mt-3 text-sm leading-6"` |
| `run.status === 'running'` et `isRunning` sans contenu | `Etiquette ton="neutre"` « Réfléchit… » + deux `Squelette` `largeur="w-[80%]"` et `w-[60%]` |
| `run.status === 'running'` et attente (pas encore dans `run.advisors`) | même squelette, sans étiquette « Réfléchit… » |
| `run.status !== 'running'` et contenu vide (avis absent, `isRunning` coincé sans texte, ou `isComplete` sans texte) | `Etiquette ton="erreur"` « Avis non rendu » ; **jamais** le squelette ; **pas** de bouton « Redemander cet avis » (P-088) |

Icônes de tête, **même table**, premier match (run seulement) :

| État de l'avis | Icône |
|---|---|
| contenu non vide et `run.status === 'running'` et `isRunning` | `Spinner taille="ligne"` (14 px, `Spinner.tsx:17-24`) |
| contenu non vide, tout autre cas | `CheckCircle2` 18 px `text-success` si `isComplete` ; pastille `span className="h-2 w-2 rounded-full bg-border"` si `isRunning: true` coincé (pas `isComplete`) |
| `run.status === 'running'` et `isRunning` sans contenu | `Spinner taille="ligne"` |
| `run.status === 'running'` et attente (pas encore dans `run.advisors`) | pastille |
| `run.status !== 'running'` et contenu vide | pastille |

Règle icône : **pas de Spinner si `run.status !== 'running'`** (y compris
`isRunning: true` coincé). Règle corps : contenu non vide → **toujours**
rendu (`pre-wrap` seulement si `running` et `isRunning`, `CompactMarkdown`
sinon). « Avis non rendu » uniquement si contenu vide et `status !==
'running'`. Un avis interrompu avec du texte ne disparaît pas.

En `DecisionDetail`, un `opinion.content` vide : même « Avis non rendu »
(pas un `CompactMarkdown` vide). Recette SSE alignée : un run `error` avec
un conseiller encore `isRunning: true` et contenu vide affiche « Avis non
rendu », pas « Réfléchit… » ; le même run avec contenu non vide affiche
`CompactMarkdown` (avis partiel), pas « Avis non rendu », pas le `pre-wrap`.

### 3.4 Divergences

Après la grille, **seulement si** `run.synthesis` ou `decision.synthesis`
existe (donc **masqué** tant que `run.status === 'running'` sans synthèse ;
maquette `encours` masque `#divergences`, `decision.html:95`) :

- si `divergence_points.length > 0` : `h3 text-base` « Où les avis
  divergent », liste `text-sm` des points (plus dans la carte synthèse) ;
- si vide : le même `h3`, puis « Aucune divergence enregistrée. » inchangé.

L'`AlertCircle` que porte aujourd'hui chaque point de divergence
(`BoardConversationCard.tsx:146`, `h-3.5` dans le bloc `warning` de
`SynthesisView`) **est abandonné avec ce bloc** : la maquette liste les
divergences en `<li>` nus, sans glyphe (`decision.html:86`), et un
pictogramme d'alerte par point ferait d'un désaccord entre conseillers une
anomalie — ce que la revue du 30/08 interdit déjà pour le consensus.

Ce `h3` est **au même rang que les autres `h3` de l'écran** : celui de la
question (§ 3.1), celui de la tête de synthèse (§ 3.2), et ceux que
`CompactMarkdown` produit à l'intérieur des cartes d'avis
(`CompactMarkdown.tsx:11-13`, `h1`/`h2`/`h3` Markdown rendus en `<h3>`).
La v5 écrivait qu'il venait « après des non-titres, pas après des `h4`
d'avis » : c'est faux (revue v5, point 2), il vient après des `h3`, et ce
n'est pas un défaut, deux `h3` successifs sont des frères. La maquette met
le même titre au même rang (`decision.html:86` `<h3>Où les avis
divergent</h3>`, après les cartes `:78` dont le nom est un `<b>`). Les
`h4` « Consensus » / « Prochaines étapes » restent **à l'intérieur** de
l'article synthèse (sous le `h3` « Synthèse »). Pas de `h3` divergences
tant qu'il n'y a pas de synthèse (le message « Aucune divergence
enregistrée. » pendant `running` serait faux).

Extraits web et ligne d'usage de la synthèse : cartes `text-sm`, libellés
exacts conservés (« Extraits du moteur de recherche »). Place dans l'ordre
du corps (§ 3) : **après** les divergences, **avant** les bandeaux § 5 et
le pied (aujourd'hui ils suivent `SynthesisView`, `BoardConversationCard.tsx:281-283`).
Snippet d'un extrait : `text-sm leading-5 text-text-muted`, **hors** classe
`text-xs`, dans le même `<a>` (aujourd'hui `BoardConversationCard.tsx:282`
`text-xs` **dans** le lien ; la garde § 6.7, interactif + sous-arbre, copie
lot 3, serait rouge). Même commit que la garde 7.

**Les deux tailles que la v6 laissait au hasard** (revue v6, point 6) :
le titre des extraits est `h4 className="text-sm font-bold text-text"`
« Extraits du moteur de recherche » (aujourd'hui
`BoardConversationCard.tsx:282` `text-xs font-bold`), **la même chaîne** que
les `h4` « Consensus » et « Prochaines étapes » du § 3.2 — c'est un titre
de même rang, à la même distance de l'œil ; et la ligne d'usage de la
synthèse est `div className="… px-3 py-2 text-sm text-accent"`
(aujourd'hui `:283` `text-xs text-accent`). Ni l'un ni l'autre n'est un
interactif ni le sous-arbre d'un interactif : la garde § 6.7 ne les couvre
pas, un `text-xs` y survivrait au vert. Reste de la carte des extraits
inchangé : `Carte as="section" className="p-4"` (mêmes 16 px
qu'aujourd'hui), lien `ExternalLink` 18 px, titre de l'extrait en `strong`.

## 4. Le formulaire (`data-testid="board-new-form"`)

`fieldset` `data-testid="board-form-fields"` et le gel `disabled` inchangés.
`FormField htmlFor="board-question"` label « Question stratégique » +
`Textarea id="board-question"` mêmes `aria-label`, `aria-invalid`,
`aria-describedby`, placeholder, `h-28`. Contexte : `FormField
htmlFor="board-context"` label « Contexte utile, facultatif » +
`Textarea id="board-context"` `aria-label="Contexte du Board"` (conservé),
placeholder inchangé « Contraintes, hypothèses, chiffres ou échéance… »
(`BoardConversationCard.tsx:247`), `className` inchangé sur la hauteur :
`h-24` (pas `h-28`) ; sans `htmlFor` / `id` le libellé visible ne cible
plus le champ (`FormField.tsx:53-61` ; aujourd'hui le `label` l'enveloppe,
`BoardConversationCard.tsx:247`).
Erreur : `p#board-form-error` `role="alert"` `text-sm` inchangé (pas le
`text-xs` de `FormField.error`). Mode : même `radiogroup`
`aria-labelledby="board-mode-label"`, roving, deux radios ; cartes
`rounded-md border p-3 text-left text-sm`, actif
**`border-domaine-prospects bg-domaine-prospects-tint`**, inactif
`border-border`, icônes `Globe` (Cloud) et `ShieldCheck` (Souverain) 18 px
`text-domaine-prospects`. **La v6 écrivait `border-accent bg-accent-tint` ;
ce changement est refusé** (revue v6, point 3) : `prospects` est la couleur
de domaine de Décision sur tout l'écran (la puce de chaque `Ligne` § 1,
le remplissage de la barre de progression § 5), tandis qu'`accent-tint`
sert deux fois dans le même panneau à dire « la synthèse » (pastille et
bloc recommandation, § 3.2). Deux surfaces `accent-tint` voisines avec
deux sens différents coûtent plus que l'uniformité qu'elles promettent, et
le choix d'un mode n'est pas une action, c'est l'état d'un réglage.
Rangée des cinq portraits : grille
`grid-cols-5`, portraits index 1 à 5, `truncate` inchangés ; **ligne
« Conseillers réellement configurés » en `text-sm font-bold`** (aujourd'hui
`text-xs font-bold`, `BoardConversationCard.tsx:249`) ; **noms
`truncate text-sm text-text-muted`** (aujourd'hui `truncate text-xs`,
même ligne ; sans ces deux phrases le code recopie `text-xs` deux fois) ;
l'icône `Users` de cette ligne est **reprise en 18 px**,
`text-domaine-prospects`, `aria-hidden="true"` : c'est la seule marque de
tête d'un bloc qui n'a pas de titre.
Confirmation
`data-testid="board-confirmation"` : conteneur et textes exactement ceux
d'aujourd'hui (`rounded-md border border-accent-cyan/30 bg-accent-tint p-3`,
six appels, Ollama sans repli), `ShieldCheck` de tête **repris en 18 px**
`shrink-0` ; **`Button variant="secondary" size="md"` Annuler** — la v6
écrivait `ghost` sans le dire, or le bouton d'aujourd'hui est une surface
bordée (`BoardConversationCard.tsx:253`, `border border-border bg-surface`),
c'est-à-dire un `secondary`, et un `ghost` perdrait son survol sur ce
conteneur (`Button.tsx:30`, `hover:bg-accent-tint` = le fond du parent) ;
`Button variant="primary" size="md" className="gap-1.5"` « Confirmer et
lancer », **icône `Play` reprise en 18 px `fill-current`**,
`disabled={run.status === 'running'}` **inchangé**
(`BoardConversationCard.tsx:253`) : c'est le filet contre un second POST, le
motif exact des deux P1 du Board souverain. `Button` transmet `disabled` et
pose `disabled:opacity-50 disabled:cursor-not-allowed` (`Button.tsx:16-24`),
qui remplace le `disabled:opacity-60` écrit à la main aujourd'hui. Geste :
`Button variant="primary" size="md" className="gap-1.5"` « Préparer la
délibération », `Gavel` 18 px, même `requestConfirmation`.

## 4bis. Les icônes, une par une

Le lot ne laisse aucune icône au hasard (revue v6, point 4 : quatre
glyphes d'aujourd'hui n'étaient ni repris ni abandonnés par écrit). Table
exhaustive du bloc `lucide-react` de `BoardConversationCard.tsx:4-18`,
premier match ; 18 px partout (décision 8), `Spinner` mis à part.

| Icône | Aujourd'hui | Cible |
|---|---|---|
| `Gavel` | sur-titre « Board réel » du bandeau (`:315`), état vide (`:124`), « Préparer la délibération » (`:255`) | sur-titre **retiré** (§ 2) et `Gavel` de l'état vide **abandonnée** (§ 5) ; reprise en tête de la carte d'historique (§ 1), sur la pastille de la carte synthèse (§ 3.2) et sur « Préparer la délibération » (§ 4) |
| `Plus` | « Nouvelle question » (`:104`) | reprise, § 1 |
| `History` | puce de chaque rangée (`:129`) | reprise, § 1 |
| `ChevronRight` | rangées et run en cours (`:113`, `:131`) | reprise en `droite`, § 1 |
| `CheckCircle2` | puce du run `complete` (`:111`), tête d'avis (`:156`), liste consensus (`:145`), bandeau vert (`:183`) | reprise aux trois premiers endroits (§ 1, § 3.3, § 3.2) ; **abandonnée** avec le bandeau vert, que la meta § 3.1 remplace |
| `AlertCircle` | puce du run en erreur (`:111`), historique erreur (`:121`), canevas erreurs (`:318`, `:322`), points de divergence (`:146`) | reprise à la puce (§ 1) et en `icone` des trois `Alerte` (§ 5) ; **abandonnée** sur les points de divergence (§ 3.4, la maquette les liste nus, `decision.html:86`) |
| `Globe` | phase de recherche web (`:173`), radio « Cloud » (`:248`) | reprise aux deux endroits (§ 5, § 4) |
| `ShieldCheck` | radio « Souverain » (`:248`), tête du bandeau de confirmation (`:253`) | **reprise aux deux endroits** (§ 4) : c'est la marque du geste sous garde, elle ne se perd pas au moment où l'on confirme |
| `Square` | « Annuler la délibération » (`:185`), 14 px | reprise en 18 px `fill-current` (§ 5) |
| `Play` | « Confirmer et lancer » (`:253`), 14 px | **reprise** en 18 px `fill-current` (§ 4) : les trois gestes de lancement du lot portent un glyphe (`Plus`, `Gavel`, `Play`), en retirer un seul ferait du bouton le plus engageant le plus nu |
| `ExternalLink` | extrait web (`:282`) | reprise, § 3.4 |
| `Users` | ligne « Conseillers réellement configurés » (`:249`) | **reprise** (§ 4) |
| `RefreshCw` | « Réessayer » de l'historique (`:121`) | **abandonnée** : depuis le lot 2, un « Réessayer » est un `Button` nu (`TodayDashboardCard.tsx:287` et `:257`), et c'est le seul des trois « Réessayer » de l'écran qui porte une icône aujourd'hui — les deux du canevas n'en ont pas (`:318`, `:322`). La reprendre ferait diverger trois boutons identiques |
| `Check` | absente | **ajoutée** au bloc recommandation (§ 3.2), 18 px |
| `Spinner` | puce du run (`:111`), phase (`:173`), tête d'avis (`:156`), deux chargements du canevas (`:317`, `:321`) | `taille="bouton"` à la puce et à la phase, `taille="ligne"` à la tête d'avis (§ 1, § 5, § 3.3) ; **les deux du canevas cèdent la place aux `Squelette`** (§ 5) |

## 5. Les états

L'`Etiquette` de statut vit **uniquement** dans la meta § 3.1. Cette section
ne porte plus que progressbar, phase, bandeaux, boutons.

| État | Aujourd'hui | Cible |
|---|---|---|
| historique, chargement | spinner + « Je consulte les décisions… » | même `div` grille que `SqueletteDeLigne` (`TodayDashboardCard.tsx:71-81`) : `div className="grid grid-cols-[2rem_1fr_auto] items-center gap-3 border-t border-border px-4 py-3"` + `Squelette largeur="w-8" classeBarre="h-8 rounded-sm"` + deux barres `largeur="w-[60%]"` / `largeur="w-[40%]"` ; trois rangées dans un `div aria-hidden="true"` (pas `Ligne` : `Ligne.tsx:26-35` n'a pas de rest props, `aria-hidden` ignoré / refusé par TS) ; puis le texte actuel en `role="status"` `px-4 py-3 text-sm text-text-muted` |
| historique, erreur | icône + « Historique indisponible » + message + Réessayer + Ouvrir | `Alerte data-testid="board-history-error"` `icone={AlertCircle 18 px}` titre « Historique indisponible », `children` = `resource.error`, `action` = `Button variant="secondary" size="md"` Réessayer ; « Ouvrir Décision » reste en tête (un seul Réessayer). **L'`Alerte` est enveloppée d'un `div className="px-4 pt-3 pb-4"`**, comme à l'Accueil (`TodayDashboardCard.tsx:281`) : `Alerte` ne pose que sa propre marge intérieure (`Alerte.tsx:27`), la `Carte` n'en pose aucune (`Carte.tsx:20`), et sans enveloppe le bandeau colle aux trois bords d'une carte désormais `overflow-hidden`. Dans le **canevas**, aucune enveloppe : le corps est déjà en `p-5` (`BoardConversationCard.tsx:316`) |
| historique, vide | « Aucune décision enregistrée » + « Convoquer le Board » | `EtatVide data-testid="board-history-empty"` titre et texte actuels, `action` = `Button variant="primary" size="md"` « Convoquer le Board » ; la `Gavel` d'aujourd'hui (`BoardConversationCard.tsx:124`) est **volontairement abandonnée** : `EtatVide` n'a pas de prop `icone` (`EtatVide.tsx:11-16`) et la glisser dans `children` la mettrait à l'intérieur du `p` du texte (`EtatVide.tsx:22`), au milieu d'une phrase ; le titre porte l'état. Le `data-testid` passe par les rest props (`EtatVide` étend `HTMLAttributes<HTMLDivElement>`) |
| canevas, chargement resource / décision | spinner + « Chargement du Board… » / « Chargement de la décision… » | mêmes textes en `role="status"` `text-sm text-text-muted`, plus deux `Squelette`. **`StateShell` reste, et ce sont ses deux derniers appelants** (revue v6, point 8) : la fonction locale `BoardConversationCard.tsx:42-44` perd ses quatre autres appels (historique chargement, historique erreur, canevas erreur ×2), et sans appelant du tout elle rougirait `tsc` (`tsconfig.json:16` `noUnusedLocals`) et `eslint` (`eslint.config.js:19` `no-unused-vars` en `error`), soit deux des quatre portes du § 8.2. Sa chaîne passe de `flex min-h-48 items-center justify-center px-5 py-8` à **`flex min-h-48 flex-col items-center justify-center gap-3 px-5 py-8`** : en ligne, le texte et les barres se mettraient côte à côte. Et chaque `Squelette` reçoit `className="w-full max-w-sm"` — sa racine est un `flex flex-col` sans largeur propre (`Squelette.tsx:36`), donc dans un parent `items-center` un `largeur="w-[80%]"` vaudrait 80 % de zéro. jsdom ne mesure pas cela : la preuve est à la recette |
| canevas, erreur resource / décision | message + Réessayer | `Alerte icone={<AlertCircle className="h-[18px] w-[18px]" />}` (les deux, comme l'`Alerte` de l'historique : `Alerte` a la prop et ne rend rien sans elle, `Alerte.tsx:31-35` ; aujourd'hui l'icône existe aux deux endroits, `BoardConversationCard.tsx:318` et `:322`), titre = le message actuel, `action` = `Button secondary md` Réessayer (`onRetry` / `onRetryDecision`) |
| run `running` | barre + phase + N/5 | pas d'`Etiquette` ici (meta § 3.1) ; **place : juste après la `Carte` question et avant la carte synthèse** (§ 3), pas en bas du corps ; le bouton « Annuler la délibération » ci-dessous reste, lui, au pied d'actions en bas (aujourd'hui `BoardConversationCard.tsx:185`) ; barre visible `div.mt-2.h-1.5.overflow-hidden.rounded-full.bg-surface` `role="progressbar"` `aria-label="Progression de la délibération"` `aria-valuemin={0}` `aria-valuemax={5}` `aria-valuenow={completed}` `aria-valuetext={`${completed} conseiller${completed > 1 ? 's' : ''} sur 5 terminé${completed > 1 ? 's' : ''}`}` (mêmes `aria-*` qu'aujourd'hui, `BoardConversationCard.tsx:173` ; la maquette n'a pas de barre, l'écran actuel si) ; remplissage `h-full bg-domaine-prospects` `width: ${Math.max(4, completed / 5 * 100)}%` ; **le compteur visible « N/5 conseillers terminés » d'aujourd'hui (`BoardConversationCard.tsx:173`, `<div className="mt-1 text-right text-xs text-text-muted">`) n'est pas repris** (revue v5, point 4) : le même N est déjà dans l'étiquette « Délibération en cours · N/5 avis » (§ 3.1), à quelques pixels au-dessus, et dans l'`aria-valuetext` de la barre pour qui ne voit pas l'image ; trois affichages d'un seul compte font trois endroits à tenir juste ; phase actuelle en `role="status"` `text-sm`, **avec son icône reprise** (revue v5, point 4) : `<Globe aria-hidden="true" className="h-[18px] w-[18px] animate-pulse" />` si `run.isSearchingWeb`, sinon `<Spinner taille="bouton" />`, sachant que `Spinner` n'a pas de 18 px (`ligne` 14, `bouton` 16, `zone` 24, `Spinner.tsx:17-24`), `bouton` est la plus proche et déjà celle du § 1 ; **sans `annonce`** dans les deux cas : `Spinner` rend alors un `Loader2 aria-hidden="true"` (`Spinner.tsx:54-58`) et la phase du `role="status"` dit déjà « Recherche web en cours » (`usePrototypeBoardData.ts:155`), une seconde annonce ferait doublon ; bouton `Button variant="danger" size="md"` « Annuler la délibération », **icône reprise en 18 px** : `<Square className="h-[18px] w-[18px] fill-current" />` (aujourd'hui 14 px, `BoardConversationCard.tsx:185` ; 18 px est la taille d'icône de bouton de tout le lot, `Plus` § 1, `Gavel` § 4) |
| run `running`, confirmation | `data-testid="board-cancel-confirmation"`, `div` `rounded-md border border-error/40 bg-[var(--color-error-tint)] p-3 text-sm text-error` | le même `div` (pas `Alerte` : ce n'est pas une erreur), textes conservés, mais **fond repeint en `bg-surface`** : `rounded-md border border-error/40 bg-surface p-3 text-sm text-text`, la question en `strong className="text-error"`. Raison : `Button variant="danger"` rend une **teinte**, `bg-[var(--color-error-tint)] text-error` (`Button.tsx:31`), exactement le fond du conteneur d'aujourd'hui — « Confirmer l'annulation » deviendrait du texte rouge sur rouge, sans bordure, à côté d'un « Continuer en arrière-plan » bordé qui, lui, se verrait. Le geste destructeur serait le moins visible des deux. Sur `bg-surface`, le rapport revient dans le bon sens : `Button danger md` « Confirmer l'annulation » est le seul rempli, `Button secondary md` « Continuer en arrière-plan » reste bordé. La bordure `border-error/40` garde au bloc sa couleur d'avertissement |
| run `complete` | bandeau vert + identifiant | pas d'`Etiquette` ici (meta § 3.1 « Décision enregistrée ») ; identifiant déjà dans la meta § 3.1 (`Identifiant : {run.decisionId}`) ; `Button variant="primary" size="md"` « Nouvelle question » `onReset` (pied commun, ci-dessous) |
| run `error` / `persistence_error` | bandeau `role="alert"` à deux `<p>` | `Alerte` titre = le gras actuel (« Sauvegarde non vérifiée. » / « Délibération incomplète. ») ; `children` = **un seul texte** (les deux phrases concaténées, espace au milieu) : `{run.error}` + « Les avis partiels restent visibles mais aucune conclusion ne doit être considérée comme sauvegardée. » (si `run.error` est vide, la seconde phrase seule). `Alerte` enveloppe `children` dans un seul `<p>` (`Alerte.tsx:38`) : deux `<p>` dans `children` = HTML invalide. Pas de Réessayer (aucun aujourd'hui). Cette `Alerte` n'est **pas** le statut : si `run.status === 'error'` et au moins un avis rendu, le statut est l'`Etiquette ton="attention"` § 3.1, l'`Alerte` se colle **sous** ; si zéro avis, pas d'étiquette, l'`Alerte` « Délibération incomplète. » reste seule. `persistence_error` : pas l'étiquette partielle (ce n'est pas un avis manquant), `Alerte` « Sauvegarde non vérifiée. » seule. Pied : `Button variant="primary" size="md"` « Nouvelle question » `onReset` (aujourd'hui `BoardConversationCard.tsx:185` : `running` ? Annuler : Nouvelle question, donc aussi sur erreur). Le canevas affiche `BoardRunView` tant que `status !== 'idle'` (`:312`) ; sous `xl`, le canevas est un calque `absolute` `max-w-[620px]` (`ConversationCanvasPrototype.tsx:333`, `xl:relative`) qui recouvre la carte (où le même geste existe encore) : sans ce bouton, plus aucun geste dans le panneau. |
| run `cancelled` | bandeau warning sans `role="alert"` | `div` (pas `Alerte`) `className="rounded-md border border-warning/40 bg-[var(--color-warning-tint)] p-3 text-sm text-warning"` (aujourd'hui `text-xs`, `BoardConversationCard.tsx:182`) ; texte inchangé : « Délibération annulée. Aucun résultat complet n'est présenté comme une décision. » ; `Button variant="primary" size="md"` « Nouvelle question » `onReset` (pied commun, ci-dessous) |

Un seul « Réessayer » par état : historique erreur, canevas resource
erreur, canevas décision erreur. Zéro ailleurs.

`Button variant="primary" size="md"` « Nouvelle question » `onReset` sur
tout run dont `status !== 'running'` (`complete`, `cancelled`, `error` et
`persistence_error` compris), pas seulement `complete` et `cancelled`.

## 6. Gardes mécaniques et tests à aligner

Nouveaux (`BoardConversationCard.da.test.tsx`, rouges d'abord ; la garde 9
vit dans `Ligne.test.tsx` : le contrat d'une primitive se teste chez elle) :

1. une ligne d'historique = un seul `button`, grille `2rem 1fr auto`, le
   badge porte `data-etiquette` ; `detail` est exactement
   `decision.recommendation` (pas une concaténation) ; `droite` contient
   `formatDate(decision.created_at)` · « Souverain » ou « Cloud » (sans
   « Mode ») puis l'`Etiquette` ; sur une décision **sans** `mode`, `droite`
   ne contient ni « Souverain » ni « Cloud », et le « · » qui les précède
   disparaît avec le segment ; titre et détail portent `truncate` (prop
   `coupe`), le titre porte en plus `block w-full` et **jamais** `relative` ;
   `ton` du consensus `low` / `medium` n'est pas `erreur` ; le run en cours porte `data-testid="board-current-run"`
   sur le `div` enveloppe, pas sur `Ligne` ; **ni ce `div` ni la rangée du
   run en cours ne portent de classe de fond** (`bg-`), la teinte de
   domaine ne vivant que sur la puce ; la `Carte` de l'historique porte
   `overflow-hidden` ;
2. la synthèse (`board-synthesis`) précède la première carte d'avis dans
   le DOM, en run `complete` avec synthèse, en `DecisionDetail`, **et** en
   run `running` sans synthèse (placeholder « Synthèse en préparation, elle
   arrive après le dernier avis. ») ; pas de `h2` « Synthèse » dans le
   canevas (tête en `h3`) ; en run `running`, le `role="progressbar"` précède
   `board-synthesis` dans le DOM, qui précède la première carte d'avis ;
   extraits et usage, s'ils existent, viennent après les divergences et
   avant les bandeaux § 5 ; les deux conteneurs portent toujours
   `data-testid="board-run-view"` (`BoardRunView`) et
   `data-testid="board-decision-detail"` (`DecisionDetail`) ; **la grille
   des avis porte `grid-cols-[repeat(auto-fill,minmax(16rem,1fr))]`** aux
   deux montages, ni `sm:grid-cols-2` ni `xl:grid-cols-2` ;
3. « Réfléchit… » seulement sur un avis `isRunning` sans contenu **et**
   `run.status === 'running'` ; « Avis non rendu » sans bouton « Redemander »
   dès que `run.status !== 'running'` et contenu vide (y compris `isRunning`
   coincé) ; contenu non vide + `run.status !== 'running'` (y compris
   `isRunning: true` coincé) → `CompactMarkdown`, jamais « Avis non rendu »,
   jamais le `pre-wrap` ; `CompactMarkdown` sur un avis complet (pas de `###`)
   ; **pas de `Spinner` de tête** si `run.status !== 'running'` (y compris
   `isRunning: true` coincé : pastille si « Avis non rendu », `CheckCircle2`
   seulement si `isComplete`) ;
4. statut : une seule `Etiquette` de statut, dans la meta de la question ;
   branches `run.status` seulement dans `BoardRunView` ; « Décision
   enregistrée » dans `BoardRunView` si `run.status === 'complete'`, **et**
   toujours dans `DecisionDetail` (même si `run.status` est `running` /
   `error` / `idle` en arrière-plan, cible = id, `showRun` faux) ;
   `DecisionDetail` ne lit pas `run` ; « Délibération en
   cours · 2/5 avis » pour `completed === 2` (run `running`) ; « **Délibération
   partielle · 4 avis rendus** » pour `run.status === 'error'` et 4 avis avec
   contenu non vide ou `isComplete` (N = ce prédicat, pas `completed` seul :
   un 5e avis interrompu avec du texte porte l'étiquette à « 5 avis rendus »)
   ; **aucune étiquette de statut de l'écran ne contient « /5 » sous
   `run.status === 'error'`**, ni « 4/5 », ni « 5/5 » — la garde le vérifie
   sur les deux jeux (quatre avis rendus, puis cinq) ; « Délibération
   partielle · 1 avis rendu » au singulier pour un seul ; titres
   d'erreur de run inchangés ; meta de `DecisionDetail` sur la fixture
   actuelle (une opinion, `mode: 'sovereign'`) = « 1 conseiller » et
   « Mode souverain », **jamais** « 5 conseillers » ; la même fixture privée
   de `mode` n'affiche aucun segment de mode (ni « Mode cloud », ni le « · »
   correspondant) ; deux opinions donnent « 2 conseillers » ; en
   `BoardRunView`, « 5 conseillers » et « Mode cloud » / « Mode souverain »
   restent inconditionnels ; **meta de synthèse = « Ce que les avis ont en
   commun, et ce qui les sépare », la même chaîne dans les trois montages**
   (run `running` sans synthèse, run `complete`, `DecisionDetail` à une
   opinion) : elle ne contient **aucun nombre** : ni « cinq », ni
   « quatre », ni la variante `partiel` de la maquette ; pendant un run
   `running`, la zone de progression **ne répète pas le compte** (aucun
   texte « conseillers terminés » dans le DOM, le N ne vit que dans
   l'étiquette et dans `aria-valuetext`) et porte l'icône de phase
   (`Globe` si `run.isSearchingWeb`, sinon le `Loader2` du `Spinner`), sans
   `role="status"` ni `aria-label` propre à l'icône ;
5. un seul « Réessayer » sur historique erreur, canevas resource erreur,
   canevas décision erreur ; zéro sur vide, chargement, run `complete`,
   run `error` ; « Nouvelle question » présent sur run `complete`,
   `cancelled`, `error` et `persistence_error`, absent pendant `running` ;
6. tête du canevas : plus de « Board réel », `h2` « Décision » ; bandeau
   `className="border-b border-border px-5 py-4 pr-16"` (`pr-16` conservé) ;
7. aucune classe `text-xs` sur un interactif **ni dans son sous-arbre**
   (carte + canevas), y compris le snippet d'un extrait web ; aucune couleur
   en dur dans `BoardConversationCard.tsx` ;
8. primitives : `CarteTete` pose `idTitre` sur l'historique ; `Alerte` /
   `EtatVide` transmettent les testid et rendent `action` ; `FormField`
   contexte a `htmlFor="board-context"` et le `Textarea` `id="board-context"`
   `placeholder="Contraintes, hypothèses, chiffres ou échéance…"` et `h-24` ;
   `h4 className="text-sm font-bold text-text"` « Consensus » et
   « Prochaines étapes » ; noms d'avis en
   `strong className="block text-sm font-semibold"` (pas `h4`) ; ligne
   « Conseillers réellement configurés » `text-sm font-bold`, noms des
   portraits `truncate text-sm text-text-muted` ; la tête de la carte
   synthèse porte la pastille
   `grid h-8 w-8 shrink-0 place-items-center rounded-full bg-accent-tint text-accent`
   avec **`Gavel`** 18 px et `aria-hidden="true"` (jamais `Scale`, pris par
   « Références juridiques », `CapabilityCenter.tsx:262`) ; **les trois
   marges intérieures sont posées** : `p-4` sur la `Carte` question,
   `px-4 pb-4` sur le corps de la carte synthèse (les **deux** montages,
   placeholder compris), `p-3` sur chaque `Carte` d'avis ; aucune de ces
   trois surfaces ne doit sortir avec la seule chaîne de `Carte`
   (`bg-surface border border-border rounded-md shadow-sm`, `Carte.tsx:20`) ;
   le bloc recommandation porte
   `flex items-start gap-3 rounded-sm bg-accent-tint p-3`, une icône
   `Check` 18 px `aria-hidden="true"` et l'intitulé « Recommandation : »
   dans un élément **distinct** du `<b>`, dont le `textContent` reste
   exactement `synthesis.recommendation` ; les deux `Alerte` du canevas
   rendent leur `icone` ; « Confirmer et lancer » est `disabled` quand
   `run.status === 'running'` ; en `DecisionDetail`, une opinion sans
   `provider` **ni** `model` n'affiche aucune meta (ni « provider inconnu »,
   ni « modèle non mesuré », ni le « · » qui les sépare) ; **la meta d'un
   avis porte `truncate` aux deux montages** ; `h4 className="text-sm
   font-bold text-text"` aussi sur « Extraits du moteur de recherche », et
   la ligne d'usage de la synthèse en `text-sm` ; le conteneur de l'`Alerte`
   de l'historique porte `px-4 pt-3 pb-4` ; la carte du mode active porte
   `border-domaine-prospects bg-domaine-prospects-tint` (jamais
   `bg-accent-tint`) ; « Annuler » de `board-confirmation` est un
   `secondary` ; `board-cancel-confirmation` porte `bg-surface` et **jamais**
   `bg-[var(--color-error-tint)]`, qui est le fond du `Button danger` qu'il
   contient ; **tout `<svg>` rendu porte `h-[18px] w-[18px]`**, à la seule
   exception du `Loader2` de `Spinner` (repéré par `animate-spin`, sa taille
   étant nommée, `Spinner.tsx:17-24`) — la garde balaie le DOM des deux
   montages, pas le texte du fichier, et `CharacterPortrait` n'est pas un
   `svg` (`DecisionMissionPrototype.tsx:25`, un `span` à image de fond) ;
   tout `Button` porteur d'une icône a `gap-1.5` ; les deux chargements du canevas rendent leur texte en
   `role="status"` et deux `Squelette`, dans un conteneur `flex-col`.
9. `Ligne.test.tsx` (primitive, même commit) : `coupe` pose `truncate` sur
   le `p` du détail et `block w-full truncate` sur le libellé, sans
   `relative` (le `before:absolute before:inset-0` reste calé sur la rangée,
   `Ligne.tsx:65`) ; **sans** `coupe`, aucune de ces classes n'apparaît, et
   les cinq tests existants de `Ligne.test.tsx` (`:19`, `:59`, `:69`, `:102`,
   `:118`) passent sans modification (le rendu du lot 2 est inchangé).

À aligner dans le même commit, forme seulement :
`aucuneCouleurEnDur.test.ts` (ajouter `BoardConversationCard.tsx` aux
sources, l'ombre `rgba` disparaît). `BoardConversationCard.test.tsx` ne
change pas de chaînes (reco, consensus, extraits, confirmation, plafond 30,
Markdown `closest('section')` : `Carte as="section"`) et ses quatre
assertions qui passent par `board-decision-detail` (`:114`, `:115`, `:140`,
`:141`) tiennent parce que le testid est conservé (§ 3). `Ligne.test.tsx`
gagne la garde 9 et ne perd rien. Aucune assertion de comportement n'est
retirée.

## 7. Ce que ce lot ne fait pas

- Page pleine 66 rem, fil d'Ariane « Décisions › Décision du … », durée,
  « Contexte lu : contact, 2 devis, agenda » : le canevas reste le panneau
  620 px. Fonctionnalité : **P-080**.
- « Copier », « Créer les tâches », « Exporter en Markdown », « Poser une
  autre question » (on garde « Nouvelle question »), « modifiable tant
  qu'aucune tâche n'est créée » : **P-081**.
- « Redemander cet avis », positions Accepte / Refuse / sous condition,
  renommage des cinq conseillers : **P-088**.
- `BoardPanel` et ses sous-composants, scénario `board` de l'en-tête de
  coque (ligne « THÉRÈSE · heure », lot 2), Atelier, autres lots.
- Aucun changement de données, d'API, de store ni de navigation.

## 8. Plan de preuve

1. Tests rouges d'abord (§ 6), vérifiés rouges pour la bonne raison,
   sabotage par remplacement inverse, `.agents-sync-paused` posé.
2. Six portes : ruff, pytest (XML), vitest json, tsc, eslint (27), mypy 951.
3. Recette visuelle sur la pile jetable (17393 et 1420, jamais 17293) :
   états forcés par interception Playwright `page.route` de
   `**/api/board/decisions*` , `**/api/board/advisors` et
   `**/api/board/deliberate` (SSE) : cinq avis + synthèse (normal) ;
   délibération 2/5 avec squelettes **et** placeholder « Synthèse en
   préparation, elle arrive après le dernier avis. », `#divergences`
   absent (encours) ; quatre avis + un vide (partiel / erreur de run) :
   étiquette « Délibération partielle · 4 avis rendus », le 5e « Avis non
   rendu » même si le SSE `error` a laissé `isRunning: true` **et contenu
   vide**, `Alerte` « Délibération incomplète. » sous l'étiquette, pas à
   sa place, pied « Nouvelle question » (le calque sous `xl` recouvre la
   carte) ; un 5e avis interrompu **avec** du texte : `CompactMarkdown`,
   pas « Avis non rendu » ; extraits après les divergences s'il y en a ;
   historique vide ; historique en panne ; chargement lent ; ouvrir un
   détail (cible = id) pendant un run `running` : étiquette « Décision
   enregistrée », pas « Délibération en cours ». Largeurs 1280,
   1024, 840, 800 px ; clair, sombre, contraste élevé ; trois tailles de
   police. Captures `.cartography-work/validation/da-lot7/`, rapport
   `docs/da/2026-09-11-lot7-recette.md`. Vérifier : synthèse au-dessus des
   avis, Markdown rendu, étiquette de statut (une seule), un seul Réessayer,
   anneau 3 px sur une ligne, établi visible, composeur non recouvert, barre
   de progression visible **sans défiler** pendant un `running` (elle est
   au-dessus des cinq cartes), rangées d'historique coupées à une ligne
   (titre et reco) sur une question de 90 caractères, dont **un clic hors du
   texte du titre** (sur la puce, sur la reco) qui ouvre bien la décision :
   `coupe` pose `overflow:hidden` sur le libellé, et seule la recette prouve
   que le `before:absolute before:inset-0` n'en est pas rogné (son bloc
   conteneur est la rangée `relative`, pas le bouton ; jsdom ne mesure pas
   ce clip, garde 9 comprise), et un détail à une
   seule opinion qui annonce « 1 conseiller », pas « 5 conseillers ».
   Vérifier aussi, sur les trois états : la meta de synthèse **sans
   nombre** (cinq avis rendus, délibération 2/5, partiel à quatre : la même
   phrase) ; l'icône de phase à gauche de la phase, `Globe` pulsé pendant
   « Recherche web en cours » et roue sinon, **sans** « N/5 conseillers
   terminés » sous la barre ; la coche et l'intitulé
   « Recommandation : » devant la recommandation, sur un fond
   `accent-tint` ; et les trois marges (question, corps de synthèse, cartes
   d'avis), dont aucune ne doit laisser le texte toucher le bord.
   Six points ajoutés par la revue de la v6, tous invisibles en jsdom :
   **le nombre de colonnes de la grille des avis** aux quatre largeurs — une
   à 1280 px (panneau à 43 %), deux à 1024, 840 et 800 px (calque plafonné
   à 620 px), jamais une carte sous 16 rem ; **le survol de la dernière
   rangée d'historique**, qui doit rester dans les coins arrondis de la
   carte (`overflow-hidden`) et l'`Alerte` d'erreur qui ne doit toucher
   aucun bord ; **« Confirmer l'annulation »**, qui doit se lire comme un
   bouton rempli sur le fond `surface` de son bloc, plus visible que
   « Continuer en arrière-plan » ; **les deux chargements du canevas**, dont
   les barres de `Squelette` doivent occuper la largeur et non s'effondrer ;
   **la meta d'un avis**, coupée à une ligne dans la colonne la plus
   étroite (440 px) ; et **la rangée du run en cours**, désormais sans fond
   teinté, qui doit rester repérable par sa puce et sa phase.
4. Revue Grok du diff avant le tag, `/release-therese 0.72.0-alpha` avec le
   GO de Ludo (toute la DA, pas ce lot seul).

## Points non repris

Aucun de la v6. Les 8 points de
`.cartography-work/reviews/opus-da-lot7-decision-design-v6.log` (1 P2, 7 P3)
sont repris ci-dessus : grille des avis reprise de la maquette avec le
nombre de colonnes écrit aux quatre largeurs (§ 3.3 et garde 6.2, point 1),
dénominateur de la délibération partielle retiré et garde 6.4 retournée
(§ 3.1, garde 6.4 et § 8.3, point 2), trois teintes tranchées (§ 4 : carte
de mode **refusée** en `accent`, « Confirmer et lancer » passé en `primary`
avec sa raison, « Confirmer l'annulation » en `danger` sur un fond repeint,
point 3), table exhaustive des icônes (§ 4bis, point 4), `truncate` de la
meta d'avis conservé et mis sous garde (§ 3.3 et garde 6.8, point 5),
classes du `h4` des extraits et de la ligne d'usage écrites (§ 3.4 et
garde 6.8, point 6), `overflow-hidden` posé sur la `Carte` d'historique et
porté en recette (§ 1, garde 6.1 et § 8.3, point 7), `StateShell` conservé
comme conteneur des deux chargements du canevas, avec sa chaîne (§ 5,
point 8).

**Quatre changements que la revue n'avait pas demandés y sont écrits**,
trouvés en vérifiant les huit points : le fond du bloc
`board-cancel-confirmation`, qui était **le même** que celui du
`Button danger` qu'il contient (`Button.tsx:31`) et aurait fait disparaître
le geste destructeur ; le survol du `ghost` « Annuler » de
`board-confirmation`, égal au fond de son conteneur, d'où le retour au
`secondary` qui existe aujourd'hui ; la teinte de fond de la rangée du run
en cours, perdue au passage à `Ligne` ; et l'absence de `gap` sur `Button`,
qui collait chaque icône à son libellé (décision 9). S'ajoutent deux
précisions à la revue, sans effet sur le fond : le réglage `noUnusedLocals`
est en `tsconfig.json:16`, non `tsconfig.app.json`, qui n'existe pas dans
ce dépôt ; et `@typescript-eslint/no-unused-vars` est en `eslint.config.js:19`,
non `:18`.

Aucun de la v5. Les 8 points de
`.cartography-work/reviews/opus-da-lot7-decision-design-v5.log` (1 P1,
1 P2, 6 P3) sont repris ci-dessus : meta de synthèse sans nombre et
garde 6.4 retournée (§ 3.2 et § 6.4, point 1), prémisse des titres
récrite et sortie assumée des cinq `h4` du run (§ 3.3 et § 3.4, point 2),
marges intérieures des trois surfaces tranchées et mises sous garde
(§ 3.1 `p-4`, § 3.2 `px-4 pb-4`, § 3.3 `p-3`, garde 6.8, point 3),
compteur de progression repris par l'étiquette et icônes de phase et
d'annulation reprises (§ 5 et garde 6.4, point 4), pastille de synthèse
passée de `Scale` à `Gavel` (§ 3.2 et garde 6.8, point 5), justification
de `coupe` récrite sur pièces (§ 1, point 6), icône `Check` et intitulé
« Recommandation : » repris (§ 3.2 et garde 6.8, point 7), parenthèse du
numéro de portail retirée (§ 7, point 8). S'y ajoutent trois précisions de
détail, qui ne changent rien au fond. **Deux corrigent le design** sans que
la revue les ait demandées : la citation de `decision.synthesis`, absente
de la v5, que la revue donne en `board.ts:73` ; et les trois renvois au
script de la maquette, décalés d'une ligne (la revue en avait relevé un,
les deux autres se sont vus au passage), corrigés en `decision.html:95`
pour `encours`, `:97` pour `partiel`, `:95` pour le masquage de
`#divergences`. **La troisième précise la revue** : les trois numéros du
lot **sont** enregistrés, au registre du portail de la boucle
(`.app-loop/proposals.json`), qui vit **hors dépôt git**, d'où leur
absence du `grep` sur `docs/` que cite la revue. Seul point de la v5 sur lequel le
design tranche autrement que la correction proposée : au point 1, la revue
offrait « retirer le nombre **ou** réemployer le N de § 3.1 » ; c'est la
première branche qui est prise, et le § 3.2 dit pourquoi (le compte vit
déjà dans l'étiquette de statut et dans le segment « N conseiller(s) »).

Aucun de la v4. Les 10 points de
`.cartography-work/reviews/opus-da-lot7-decision-design-v4.log` (1 P1, 3 P2,
6 P3) sont repris ci-dessus : meta du détail mesurée (§ 3.1), barre et phase
au-dessus des avis (§ 3 et § 5), testid des deux conteneurs (§ 3 et
garde 6.2), meta d'avis conditionnelle (§ 3.3), taille de la question
tranchée à `text-lg` (§ 2 et § 3.1), pastille de synthèse reprise avec
`Scale` (§ 3.2 ; **remplacée par `Gavel` en v6**, point 5 de la revue de la
v5 : `Scale` est déjà « Références juridiques » dans le même groupe
`decide`), icônes des `Alerte` et abandon assumé de la `Gavel` de
l'état vide (§ 5), `disabled` du bouton de confirmation (§ 4), coupe des
rangées tranchée par la prop `coupe` de `Ligne` (§ 1 et garde 6.9),
`P-088` attribué (§ 3.3 et § 7). Seule correction apportée à la revue
elle-même : `mode?: string` de `BoardDecisionDetail` est en `board.ts:74`,
pas dans l'intervalle `:60-73` qu'elle cite, ce qui ne change rien au fond.

Aucun de la v3. Les 6 points de `.cartography-work/reviews/grok-da-lot7-decision-design-v3.log` (1 P1, 1 P2, 4 P3) sont repris ci-dessus. Les 9 points de `.cartography-work/reviews/grok-da-lot7-decision-design-v2.log` (2 P1, 2 P2, 5 P3) et les 20 points de `.cartography-work/reviews/grok-da-lot7-decision-design-v1.log` (4 P1, 10 P2, 6 P3) restent repris.
