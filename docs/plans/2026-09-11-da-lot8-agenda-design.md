# DA « Application affinée », lot 8 : l'écran Agenda (design à challenger avant le code)

Version 5, 11/09/2026 10:25, après la revue de la v4 (12 points repris, 0 non
repris) ; journal `.cartography-work/reviews/opus-da-lot8-agenda-design-v4.log`. Précédent : lot 3 (Tiroir), sur `main` ; cadence : une
seule release pour toute la DA (décision Ludo 11/09, 0.72.0-alpha porte
l'ensemble). Maquette :
`docs/da/2026-09-05-propositions/maquettes/agenda.html` (états `normal`,
`mois`, `nouveau`, `erreur`), critères de `ecrans.json` : « Mois et semaine,
ligne de l'heure, création sans modale imbriquée. Jour, semaine, mois et
liste préservés ; chevauchements lisibles ; titre complet accessible ; aucune
création de calendrier avant geste explicite. » Déjà décidé côté UX, pas à
rejuger : titre « Agenda » (lexique, B-241 : la coque pose le `h2`, le
panneau garde un `<p>` visible) ; aucune création de calendrier avant geste
explicite (BUG-143) ; P-029/P-030 trace d'un rafraîchissement raté (`staleWarning`,
`data-testid="calendar-stale-warning"`) ; semaine française lundi-dimanche
(B-247) ; dates civiles (BUG-144, B-475) ; `choisirVue` range la fiche
sans fermer le formulaire (B-238).

## Ce que le lot change, en une phrase

Le panneau Agenda (`CalendarPanel.tsx`, monté `standalone` par la vue
`calendar` de `PrototypeUnifiedViewCanvas.tsx`) et ses trois enfants
(`CalendarView`, `EventForm`, `EventDetail`) prennent la forme de la maquette
**sur les états `normal`, `mois` et `erreur`** en consommant les primitives du
lot 1 (`Carte`, `Segments`, `Alerte`, `EtatVide`, `Squelette`,
`Etiquette`, `Button`, `Input`, `Select`, `Textarea`, `FormField`) ; les
mêmes données, les mêmes états, les mêmes destinations. **Deux éléments
nouveaux apparaissent à l'écran, et ce sont les deux seuls** : le champ
« Agenda » en lecture seule du formulaire (maquette `agenda.html:101`, § 6)
et le pied sous la grille qui nomme l'agenda courant (§ 8). Tous deux
affichent une donnée déjà connue du composant, tous deux sont assumés au
§ 10, et tout le reste est déjà rendu aujourd'hui. Le `h3` de période ne
gagne **pas** de suffixe « (aujourd'hui) » : la vue Jour en porte déjà un
(`CalendarView.tsx:646-648`, § 5), et deux fois le même mot sur le même
écran, ce n'est pas un repère, c'est un bruit (§ 1). L'état maquetté
`nouveau` (`.panneau` 26 rem, grille encore visible, `agenda.html:36-38` et
`ecrans.json:123` « création sans modale imbriquée ») **n'est pas l'écran
livré** : le formulaire remplace encore la grille (décision 5). Aucun appel
réseau, aucun store, aucune navigation ne change.

**Cette version décrit intégralement une seule des deux issues de la
décision 5 : la branche « remplacement conservé »**, celle du code actuel.
La branche « panneau 26 rem » n'est pas décrite ici et exigerait une version
dédiée du design avant toute ligne de code ; ce qu'elle devrait fixer est
listé en décision 5. L'arbitrage appartient à Ludo, ce document ne le rend
pas à sa place.

## Décisions tranchées par défaut (Ludo peut corriger)

1. L'écran vivant est `CalendarPanel` en `standalone`. Le mode overlay
   (`isOpen`, `role="dialog"`) reçoit le même chrome intérieur ; hors lot de
   changer son ouverture.
2. La maquette montre cinq colonnes (mardi-samedi d'une semaine d'exemple).
   La grille reste à **sept jours**, lundi-dimanche (B-247, critères).
3. Fenêtres horaires inchangées (semaine 8-20, jour 6-22, élargies par
   `getVisibleHourRange`). La maquette 8-17 est un canevas, pas une borne.
4. `viewMode` par défaut reste `month` (persisté). L'état `normal` de la
   maquette est un canevas Semaine, pas un changement de défaut.
5. Création : le formulaire **remplace** encore la grille (cascade actuelle
   `CalendarPanel.tsx:569-580`). L'état maquetté `nouveau` n'est pas livré
   dans ce lot : implémenter `.panneau` (26 rem, `position:absolute; top:0;
   right:0; bottom:0; width:26rem`, grille encore visible) changerait les
   cibles de clic. Ce n'est pas un numéro de portail qui escamote un état
   déjà dessiné : l'écart entre la maquette et l'écran livré est nommé ici,
   et **l'arbitrage revient à Ludo, avant le code**.
   - **Branche décrite ici, « remplacement conservé »** (le code actuel) :
     tout ce document la décrit (§ 6, § 8, § 9, § 11) et se code en l'état.
   - **Branche « panneau 26 rem »** : elle n'est pas décrite, et une version
     dédiée du design devra la fixer **avant toute ligne de code**, au moins
     sur ces cinq points, aucun n'étant tranché aujourd'hui :
     1. **l'ancêtre positionné** : la zone de contenu est `flex-1
        overflow-hidden` (`CalendarPanel.tsx:569`), sans `relative` ; un
        `position:absolute` y remonterait jusqu'au premier ancêtre positionné,
        qui n'est pas la zone de grille. Dire quel élément porte `relative`,
        et ce que devient `overflow-hidden` sur un panneau qui scrolle seul ;
     2. **la cascade du § 8** : le panneau sort du ternaire `loading` /
        `EventForm` / `EventDetail` / `CalendarView` ; dire ce que devient
        `isEventFormOpen` comme branche de cette cascade, et où passent les
        bandeaux stale / erreur pendant la saisie ;
     3. **le piège de focus** : panneau non modal (focus libre, grille
        atteignable au clavier, `Échap` ferme) ou modal (`role="dialog"`
        `aria-modal="true"`, focus capturé), et où le focus repart à la
        fermeture (le geste « Nouveau rendez-vous », § 2) ;
     4. **la grille derrière** : cliquable pendant la saisie (un clic sur un
        créneau change-t-il le brouillon, l'écrase-t-il, ouvre-t-il une
        fiche ?) ou neutralisée, et ce qu'il advient des données saisies dans
        chacun des cas ;
     5. **la recette** : l'état `nouveau` à 1280, 1024, 840 et 800 px (26 rem
        de panneau sur 800 px de large ne laissent pas une grille lisible),
        plus la garde mécanique correspondante, que le § 11 ne prévoit pas
        aujourd'hui (il ne liste qu'« ouverture Nouveau rendez-vous »).
6. Toute taille de `Button` est `md` (36 px) ou `icon` (36 px) ; `size="sm"`
   n'y est pas employé. « Nouveau rendez-vous » est le grand geste, en `lg`.
   Les blocs de la grille et les jetons « Journée » sont des `<button>`
   bruts en `text-sm` (typographie, pas `Button size="sm"`).
7. Les libellés de la maquette remplacent la prose là où l'état est le même
   (geste de création, alerte de cache, lieu). Un état sans équivalent
   maquetté garde ses mots (reauth, 403, validation, suppression).

## 1. L'en-tête (`.vue-tete`)

Maquette : `flex` wrap, gap `--espace-3`, marge basse `--espace-3`. Fusionner
les deux barres actuelles (`calendarHeader` + `calendarNav`) en une rangée.

| Élément | Aujourd'hui | Cible |
|---|---|---|
| Conteneur | deux `px-6 py-4` / `py-3` `border-b` | `flex flex-wrap items-center gap-3 px-4 pt-4 pb-3 border-b border-border` ; sous 840 px les actions (`basis-full`) passent sous le titre |
| Pastille | 2,5 rem, `border-[var(--btn-ink)]` | 2 rem `rounded-full bg-accent-tint text-accent`, icône `Calendar` 18 px, `aria-hidden` |
| Titre | `<p className="text-lg font-semibold">Agenda</p>` | inchangé (B-241) ; meta email `text-sm text-text-muted` conservée. `staleWarning` **sort de l'en-tête** (il n'est plus le `<p role="status">` sous le titre, `CalendarPanel.tsx:428-432`) : bandeau au-dessus de la cascade, § 8 |
| Nav | `Button ghost sm`, `aria-label` « Période précédente/suivante » | `Button variant="secondary" size="icon"` (mêmes `aria-label` et `title`) ; « Aujourd'hui » `Button variant="secondary" size="md"` |
| Période | `<h3 className="capitalize">` + `getNavLabel()` | `<h3 id="agenda-periode" className="text-base font-semibold">` ; jour : `toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })` puis première lettre seule en capitale (lot 2, jamais `capitalize`) ; **aucun suffixe ` (aujourd'hui)`** : `getNavLabel()` n'en a pas aujourd'hui (`CalendarPanel.tsx:333-341`) et la vue Jour en rend déjà un juste en dessous (`CalendarView.tsx:646-648`, § 5) ; semaine : libellé ci-dessous (bornes lundi-dimanche inchangées, `getDay()` + offset actuel) ; mois/liste : mois long + année, première lettre seule en capitale. L'`id` n'est pas décoratif : il **nomme les quatre sections de vue** par `aria-labelledby="agenda-periode"` (§ 3, châssis) |
| Sélecteur | `<select aria-label="Calendrier affiché">` maison, `Z_LAYER.ONBOARDING` | `Select aria-label="Agenda affiché"` (**le mot change**, lexique : voir la note ci-dessous), `options={calendars.map(c => ({ value: c.id, label: c.summary }))}`, `value={currentCalendarId \|\| ''}`, même `onChange` ; wrapper `relative` + z-index conservé (BUG-049) ; liste vide : aucune option, pas de bouton « créer » (BUG-143) |
| Sync / ICS | `Button ghost sm` | `Button variant="ghost" size="icon"` ; `aria-label` / `title` conservés (« Synchroniser l'agenda », « Importer un fichier .ics », « Exporter en .ics ») ; `input.hidden` inchangé |
| Segments + geste | modes + « Nouvel événement » dans `calendarHeader` (droite) | dans la rangée fusionnée, groupe `className="ml-auto flex flex-wrap gap-2"` (`basis-full` sous 840 px, déjà annoncé sur le conteneur) = `Segments` puis le `Button variant="primary" size="lg"` « Nouveau rendez-vous » ; maquette `.vue-tete .actions{margin-left:auto}` (règle `agenda.html:7`, élément `agenda.html:69`). Sans `ml-auto` le groupe reste collé au sélecteur / sync, pas à droite |
| Fermer (overlay) | `<button>` sans nom | `Button variant="ghost" size="icon"` `aria-label="Fermer l'agenda"` (absent en `standalone`) |
| Dialogue (overlay) | `role="dialog"` `aria-modal="true"` `aria-label="Calendrier"` (`CalendarPanel.tsx:617`) | `aria-label="Agenda"` (lexique, note ci-dessous) ; `role`, `aria-modal` et l'ouverture inchangés |

**Le lexique vaut aussi pour ce qui ne se voit pas.** L'écran s'appelle
« Agenda » à l'œil (B-241) et disait encore « Calendrier » au lecteur d'écran,
à deux endroits : le dialogue (`CalendarPanel.tsx:617`) et le sélecteur
(`CalendarPanel.tsx:516`). Aucune garde ne tranchait : l'extracteur de
`src/frontend/src/lib/lexiqueTitres.test.ts:44-59` ne lit que les `<h1-3>` et
le `<p>` de titre démoté, jamais un `aria-label` ; la règle
`{ titre: 'Calendrier', lexique: 'Agenda' }` (`:27`) ne pouvait donc pas voir
ces deux chaînes. **Ce document tranche : le lexique porte aussi sur les noms
accessibles**, donc `aria-label="Agenda"` sur le dialogue et « Agenda
affiché » sur le `Select`. Aucun test existant ne lit « Calendrier affiché »
(`grep -rn "Calendrier affiché" src/frontend/src` ne rend que
`CalendarPanel.tsx:516`), donc rien ne casse. **Ce point est montré à l'humain
à la recette** (§ 11.3) : étendre le lexique au-delà du texte visible est une
règle de langue, pas un détail d'implémentation, et elle revient à Ludo.

**Ce que cette extension ne couvre pas**, et ce n'est pas un oubli : elle
porte sur les **noms** — titres et noms accessibles — pas sur les messages
d'état, qui gardent leurs mots par la décision 7. Restent donc « Aucun
calendrier sélectionné. Choisis un calendrier dans le menu déroulant. »
(`EventForm.tsx:48`), le libellé `Calendrier` de la confirmation externe
(`EventForm.tsx:162`), « Impossible de charger les calendriers »
(`CalendarPanel.tsx:164`), « Calendrier exporté avec succès » (`:286`) et la
phrase de reconnexion (`:535`). Les harmoniser, c'est réécrire des messages
qu'aucun état maquetté ne couvre, et ce serait un autre lot : à trancher avec
le reste du point, à la recette.

Libellé de semaine (`getNavLabel`, vue `week`). Aujourd'hui `fmtStart` et
`fmtEnd` portent chacun `month: 'short'` (`CalendarPanel.tsx:351-353`, ex.
« 31 août - 6 sept. 2026 »). Cible, à partir du lundi et du dimanche déjà
calculés :

- jour du mois : `1` → « 1er », sinon le nombre décimal (`getDate()`) ;
  « 1er » **seulement** quand ce jour vaut 1 (lundi ou dimanche) ;
- même mois, même année : `Semaine du {jourLundi} au {jourDimanche} {mois long} {année}`
  (ex. « Semaine du 1er au 7 septembre 2026 ») ;
- mois différents, même année : `Semaine du {jourLundi} {moisLundi} au {jourDimanche} {moisDimanche} {année}`
  (ex. « Semaine du 31 août au 6 septembre 2026 ») ;
- années différentes : les deux années,
  `Semaine du {jourLundi} {moisLundi} {annéeLundi} au {jourDimanche} {moisDimanche} {annéeDimanche}`
  (ex. « Semaine du 29 décembre 2025 au 4 janvier 2026 ») ;
- mois long = `toLocaleDateString('fr-FR', { month: 'long' })`, pas `month: 'short'`.

`data-testid="calendar-panel"` conservé sur les deux racines.

## 2. Segments et geste principal

Vivent dans le groupe `ml-auto flex flex-wrap gap-2` de § 1 (pas une
seconde barre ; maquette `.vue-tete .actions`, règle `agenda.html:7`,
élément `agenda.html:69`). Ordre
visuel de la maquette, ids du store : Jour `day`, Semaine `week`,
Mois `month`, Liste `list`. `Segments label="Vue de l'agenda" valeur={viewMode}
onChange={(id) => choisirVue(id as …)}` (groupe + `aria-pressed`, pas un
`tablist`). Pas `sm` : `classeSegment` est déjà `text-sm`. Geste :
`Button variant="primary" size="lg"` icône `Plus` 18 px, libellé « Nouveau
rendez-vous », `onClick={handleNewEvent}`.

## 3. Le châssis des quatre vues, puis la grille semaine (`CalendarView` `WeekView`)

### 3.0 Le châssis, écrit une fois pour les quatre vues

Les quatre vues partagent une hauteur, un conteneur et un nom. Rien de tout
cela n'est laissé au codeur, et **`min-h-0` seul ne suffit pas** : il ne vaut
que pour un élément flex, et les quatre racines d'aujourd'hui tiennent leur
hauteur d'un `h-full` (`CalendarView.tsx:390` Semaine, `:225` Mois, `:637`
Jour, `:105` Liste). Remplacer ce `h-full` par un `min-h-0` inerte ferait
retomber la carte à sa hauteur automatique, le `flex-1 overflow-y-auto` de la
piste horaire (`CalendarView.tsx:453`) n'aurait plus de hauteur à remplir, le
bas de la grille serait clippé sans moyen d'y accéder, et l'effet qui amène
l'heure courante à l'écran au montage (`CalendarView.tsx:359-365`) deviendrait
sans objet.

- **La zone de contenu ne change pas** : `CalendarPanel.tsx:569` reste
  `flex-1 overflow-hidden`. Sa hauteur est déjà définie (elle est l'enfant
  `flex-1` d'un `flex flex-col` : `CalendarPanel.tsx:590` en `standalone`,
  `:621` en overlay), et son `overflow` non visible ramène son
  `min-height:auto` à zéro, ce qui est exactement ce qui fait marcher le
  `h-full` des vues aujourd'hui. Rien à corriger là, et rien à y ajouter.
- **La branche « grille » de la cascade** (§ 8 : ni chargement, ni
  formulaire, ni fiche) rend un conteneur à elle :
  `<div className="h-full flex flex-col gap-2 p-4">`, qui contient la vue
  puis le pied. Ce conteneur est **propre à cette branche** : `EventForm`,
  `EventDetail` et le chargement gardent leur `h-full` et leurs paddings
  actuels, sans en hériter un second.
- **Chaque vue** est une `Carte as="section" aria-labelledby="agenda-periode"`
  en `flex-1 min-h-0` — `flex-1` pour occuper la place, `min-h-0` parce
  qu'elle est cette fois bien un élément flex. S'y ajoute, par vue : `flex
  flex-col` pour Semaine (§ 3) et Jour (§ 5), `overflow-y-auto` pour Mois
  (§ 4) et Liste (§ 5).
- **Le pied** (§ 8) est le second enfant de ce conteneur, `shrink-0` : il ne
  se laisse pas comprimer par la carte et ne défile pas avec elle. Le `mt-2`
  annoncé au § 8 devient le `gap-2` du conteneur.
- **Le nom des quatre sections** vient du `h3#agenda-periode` de l'en-tête
  (§ 1), par `aria-labelledby`, jamais par un `aria-label` recopié : une
  seule source de vérité, et le nom suit le libellé affiché. La maquette
  nomme ses deux sections de la même façon (`agenda.html:73`
  `aria-label="Semaine du 1er au 5 septembre 2026"`, `:84`
  `aria-label="Septembre 2026"`). En application, `CalendarView` n'est monté
  que par `CalendarPanel` (`CalendarPanel.tsx:579`, seul site), donc l'id
  existe toujours ; monté seul dans un test unitaire, la section reste sans
  nom, ce qu'aucune assertion ne regarde.
- **Partout où un conteneur défile, l'anneau de focus est rentrant.** Le
  socle pose `:focus-visible{outline:3px solid;outline-offset:2px}`
  (`docs/da/2026-09-05-propositions/maquettes/da/base.css:23`), soit 5 px hors
  boîte, qu'un `overflow` non visible coupe. Les interactifs des quatre vues
  portent donc `focus-visible:outline focus-visible:outline-[3px]
  focus-visible:outline-offset-[-3px] focus-visible:outline-ring` : blocs de
  la Semaine et du Jour (§ 3, § 5), jetons de journée entière (§ 3, § 5),
  puces du Mois (§ 4), lignes de la Liste (§ 5). Les jetons de journée entière
  vivent au-dessus du conteneur défilant (`shrink-0`) et rien ne les clippe :
  ils prennent quand même l'anneau rentrant, pour que le focus se dessine de
  la même façon sur toute la surface de l'écran plutôt que d'un pixel
  différent selon la rangée. L'anneau reste visible dans
  les trois thèmes, y compris en contraste élevé (`--color-ring: #FFFFFF`,
  `src/frontend/src/styles/globals.css:547`, contre `#0F8FB3` en clair `:57`
  et `#22D3EE` en sombre `:201`).

### 3.1 La grille semaine

`Carte as="section" aria-labelledby="agenda-periode" className="flex-1
min-h-0 flex flex-col"` (**sans** `overflow-hidden`). La maquette pose
`.semaine{overflow:hidden}` (`agenda.html:8`) ; collée sur la carte, elle
tuerait le scroll interne actuel `flex-1 overflow-y-auto`
(`CalendarView.tsx:453`). Le scroll reste sur la grille horaire, et l'anneau
des blocs est rentrant pour cette raison même (§ 3.0).

Grille `grid-cols-[3.5rem_repeat(7,1fr)]` (gutter `3.5rem` de la maquette,
**7** colonnes). **Même gabarit** pour l'en-tête, la rangée « Journée » et
la piste horaire : aujourd'hui les trois sont du `flex` + gutter `w-16`
(4 rem, `CalendarView.tsx:396-398`, `423-450`, `456`) ; coller `3.5rem` sur
l'en-tête / les heures et garder `w-16` sur « Journée » décale les jetons
sous le mauvais jour. En-tête : **deux nœuds distincts** par jour (comme
aujourd'hui, pas collés « mar.1 » comme `agenda.html:75`) : un `div` dont
le texte entier est `lun.` … `dim.` (`text-sm text-text-muted`) + un nœud
numéro `text-base font-semibold tabular-nums`. Heures : `text-xs tabular-nums
text-text-muted` (non interactif, plancher 12 px). Pas de `bg-accent-cyan/5`.

**Les sept colonnes de jour sont séparées par un trait, la gouttière des
heures non.** Dans les trois gabarits (en-tête, rangée « Journée », piste
horaire), chaque colonne de jour porte `border-l border-border`, y compris la
première : elle sépare alors la gouttière du lundi, elle ne double pas la
bordure de la `Carte`, qui est à gauche de la gouttière. La colonne 1
(gouttière) n'en porte aucune. C'est le gabarit d'aujourd'hui
(`CalendarView.tsx:406`, `:435`, `:508`, en `border-border/20`) et celui de la
maquette (`agenda.html:10` `.semaine .jour-tete{…border-left:1px solid
var(--color-border)…}`, `:15` `.semaine .jour{…border-left:1px solid
var(--color-border)…}`), à l'opacité près : la DA pose le jeton plein,
`border-border`, plus `/20`. Les lignes d'heure passent de
`border-t border-border/15` à `border-t border-border` pour la même raison
(la maquette les peint en `var(--color-border)` plein, `agenda.html:15`).

**Le jour courant.** Cellule d'en-tête : numéro `text-accent`, fond
`bg-accent-tint`. Cellule « Journée » et colonne de la piste horaire :
`bg-surface-2`, **pas** `bg-accent-tint`. La raison est mesurable :
`--color-accent-tint` et `--color-domaine-agenda-tint` valent la même chose en
clair (`#DEF4F9`, `src/frontend/src/styles/globals.css:47` et `:86`), se
touchent en sombre (`#15314B` contre `#15334D`, `:200` et `:215`) et sont
identiques en contraste élevé (`#000000`, `:546` et `:521`) — un bloc de
rendez-vous posé sur la colonne du jour disparaîtrait dans le fond, il ne
resterait que ses 3 px de bord gauche. La maquette évite la même collision en
ne posant que 40 % de la teinte
(`.semaine .jour.aujourdhui{background-color:color-mix(in srgb,var(--color-accent-tint) 40%,transparent)}`,
`agenda.html:16`), degré qu'on ne veut pas recopier ici : la DA proscrit les
couleurs en dur, `color-mix(` compris
(`components/ui/aucuneCouleurEnDur.test.ts:38`, dont le balayage porte sur les
primitives et la coque, `:27-32`, et non sur ces quatre fichiers — raison de
plus pour ne pas y ouvrir la brèche), et un jeton existant fait le travail.
`bg-surface-2` est le jeton prévu pour cette bande légèrement contrastée, et
il se distingue de `--color-surface` dans les deux thèmes courants (`#F0F4FB`
contre `#FFFFFF` en clair, `:14` et `:13` ; `#0E1630` contre `#131B35` en
sombre, `:186` et `:185`). En contraste élevé les deux valent `#0A0A0A`
(`:531` et `:530`) : la colonne ne se distingue alors que par son numéro
`text-accent` en tête, ce qui est la limite du thème, pas un choix de ce lot.

**Un fond opaque impose de dire qui peint par-dessus.** Aujourd'hui les
lignes d'heure (`CalendarView.tsx:472-478`) sont rendues avant les colonnes
(`:506-510`) sans z-index ni l'une ni l'autre : les colonnes peignent
par-dessus, et cela ne se voit pas parce que `bg-accent-cyan/5` est à 5 %.
Avec `bg-surface-2`, opaque, la colonne du jour effacerait son quadrillage.
Les lignes d'heure portent donc `z-[1]` : au-dessus des fonds de colonne (qui
n'ont pas de z-index et ne créent aucun contexte d'empilement), sous les blocs
(`z-10`) et sous le repère de l'heure (`z-20`). Le contrôle est à la recette
(§ 11.3).

**Où vit le conteneur positionné de la piste horaire.** La ligne de l'heure est
un critère de l'écran (`ecrans.json:123`), et passer la piste à une grille de
huit colonnes déplace la question. Aujourd'hui le repère est `absolute left-0
right-0` **dans la zone jours** `flex-1 flex relative` (`CalendarView.tsx:471`
et `486-496`) : il ne traverse donc pas la gouttière des heures, et c'est ce
comportement qu'il faut garder. Structure cible :

- piste = `div className="grid grid-cols-[3.5rem_repeat(7,1fr)]"` portant le
  `style={{ height: weekHours.length * HOUR_HEIGHT_PX }}` actuel ;
- colonne 1 = la gouttière des heures (`relative`, libellés `absolute` comme
  aujourd'hui) ;
- colonnes 2 à 8 = **un seul** `div className="col-start-2 col-span-7 relative
  grid grid-cols-7"`. C'est **lui** qui porte `relative`. Il contient les
  lignes d'heure `absolute left-0 right-0`, le repère de l'heure `absolute
  left-0 right-0` (donc sur les sept colonnes de jour, **jamais** sur la
  gouttière) et les sept colonnes jour, chacune `relative` pour ses propres
  blocs.

Les sept `1fr` internes coïncident avec les sept `1fr` de l'en-tête et de la
rangée « Journée » tant qu'aucun `gap` n'est posé, et aucun des trois n'en
porte.

Rangée « Journée » **conservée** au-dessus de la grille horaire
(`CalendarView.tsx:423-450`) : `grid grid-cols-[3.5rem_repeat(7,1fr)]`,
première cellule = libellé gutter `text-sm text-text-muted` « Journée »
(plus `text-xs`), **pas** `w-16` + `flex-1`. `getTimedEventLayout` exige
`start_datetime` / `end_datetime` et retourne `null` sans eux
(`calendarEventLayout.ts:90-92`) : un `all_day` n'a pas de `top` dans la
grille horaire. Filtre `allDayByDate` inchangé. Jetons : `<button>`
`text-sm truncate border-l-[3px] border-domaine-agenda bg-domaine-agenda-tint
text-domaine-agenda px-2 py-0.5 rounded-sm hover:brightness-95` + anneau
rentrant (§ 3.0) (plus de magenta `bg-accent-magenta/20`).

**Le survol se garde, et il est le même partout dans les grilles.** Chaque
bloc, chaque jeton et chaque puce des vues Semaine, Mois et Jour porte
`hover:brightness-95` : c'est le motif déjà posé par la DA sur une surface
teintée (`Button variant="danger"`, `src/frontend/src/components/ui/Button.tsx:31`),
et il n'invente aucune couleur. Sans lui, les grilles perdraient l'affordance
que la Liste conserve (`hover:bg-surface-2`, § 5, motif de
`components/ui/Ligne.tsx:63`) : deux gestes identiques, deux réponses
différentes sur le même écran. En contraste élevé, les teintes de domaine sont
ramenées au noir (`globals.css:519-521`) et ce retour ne se voit pas — tout
comme le `hover:bg-surface-2` de `Ligne` sur `--color-surface-2: #0A0A0A`
(`:531`) : la limite est celle du thème, et le repère garanti dans les trois
thèmes reste l'anneau de focus.

Blocs horaires : `absolute`, `getTimedEventLayout` inchangé (côte à côte =
chevauchement lisible), **`HOUR_HEIGHT_PX = 60` conservé**
(`CalendarView.tsx:284`), **pas** 48. La maquette tient ses 3 rem parce
qu'elle écrit en 12/13 px (`agenda.html:18-19`), taille refusée ici sur un
interactif : en `text-sm` sur deux lignes, le contenu d'un bloc mesure
2 x 20 px + `py-0.5` (2 px + 2 px) = **44 px**, quand 48 px par heure ne
donnent que 36 px à un rendez-vous de 45 minutes. La décision est chiffrée,
rien n'est laissé à deviner : à 60 px par heure, les deux lignes tiennent
**dès 44 minutes** ; en dessous, `overflow-hidden` rogne la ligne d'horaire,
qui **reste entière dans le nom accessible du bouton** (le DOM garde titre et
horaire). C'est, à trois minutes près, le seuil d'aujourd'hui (40 minutes en
`text-xs`), et non une ligne sacrifiée. **Pas** `left-1
right-1` : ces classes contredisent le placement en pourcents. Le rendu
garde le `style` inline actuel (`CalendarView.tsx:523-528`) :

```
style={{
  top: layout.top,
  height: Math.max(layout.height, 20),
  left: `${layout.leftPercent}%`,
  width: `${layout.widthPercent}%`,
}}
```

Classe `absolute z-10 rounded-sm border-l-[3px] border-domaine-agenda
bg-domaine-agenda-tint text-domaine-agenda px-2 py-0.5 text-left overflow-hidden
hover:brightness-95
focus-visible:outline focus-visible:outline-[3px] focus-visible:outline-offset-[-3px]
focus-visible:outline-ring` (`z-10` conservé de `CalendarView.tsx:522`, au-dessus
des lignes d'heure passées en `z-[1]`) ; titre `text-sm font-semibold truncate` (le DOM
garde le résumé entier) ; horaire `text-sm truncate` (**le `truncate` est
porteur** : sans lui, « 09:00 à 10:30 · sur place » replie sur deux ou trois
lignes dans une colonne de 105 px, ce qu'une semaine à 840 px donne, et les
44 px calculés ci-dessous deviennent faux ; le DOM et le nom accessible gardent
la chaîne entière, comme pour le titre), **début et fin conservés**,
forme `HH:MM à HH:MM` (`formatTime(start_datetime)` + ` à ` +
`formatTime(end_datetime)`, plus le ` - ` actuel) ; si `location`, même
ligne, séparateur ` · ` (ex. « 09:00 à 10:30 · sur place » ; sans lieu,
« 10:00 à 12:00 »). Ligne de l'heure : `bg-instant` conservé (repère, pas
une erreur), rendue seulement si `nowLineTop !== null` (garde actuelle
`CalendarView.tsx:379-382` : aujourd'hui dans la semaine **et** heure dans
la fenêtre) ; le repère porte `role="img"` `aria-label={`Il est ${HH}:${MM}`}`
`pointer-events-none` (un `aria-label` sur un `div` sans rôle n'est pas
exposé ; `HH`/`MM` = `padStart(2, '0')` de `getHours()` / `getMinutes()`).
Le jour affiche déjà l'heure en texte (`CalendarView.tsx:732-734`), pas
d'`aria-label` sur son repère. `whileHover` / `scale` retirés.

## 4. Grille mois (`MonthView`)

`Carte as="section" aria-labelledby="agenda-periode" className="flex-1 min-h-0
overflow-y-auto"` (§ 3.0), et **à l'intérieur** un `div` qui porte la grille :
`<div className="grid grid-cols-7 min-h-full grid-rows-[auto_repeat(6,minmax(5.5rem,1fr))]">`,
**7 en-têtes** puis **42 cases** (49 enfants), lundi d'abord, sans `gap`. La
grille est un `div` **enfant** de la `Carte`, jamais la `Carte` elle-même :
`semaineFrancaise.test.tsx:53` sélectionne
`container.querySelectorAll('div.grid-cols-7')`, et une `section` ne répond
pas à ce sélecteur. Ce `div` ne reprend **ni** `rounded-md` **ni**
`border border-border` : `Carte.tsx:20` les pose déjà, les redoubler dessine
deux traits.

**Qui défile, et qui remplit.** Les six rangées de 5,5 rem valent 33 rem, plus
les en-têtes, dans une zone que `CalendarPanel.tsx:569` clippe en
`overflow-hidden` : sur une fenêtre courte, sans rien dire, la dernière
semaine du mois devient invisible **et** inatteignable (aujourd'hui les
cellules n'ont aucune hauteur minimale et se compriment,
`CalendarView.tsx:236`). C'est donc la `Carte` qui défile (`overflow-y-auto`),
et la grille qui la remplit : `min-h-full` lui donne au moins la hauteur
visible, et `grid-rows-[auto_repeat(6,minmax(5.5rem,1fr))]` fait le reste —
5,5 rem plancher, `1fr` quand il y a de la place, donc ni vide sous la grille
sur une fenêtre haute, ni rangée écrasée sur une fenêtre basse. La hauteur
minimale vit **sur les rangées, pas sur les cases** : `min-h-[5.5rem]` sort de
la classe des cellules, une seule source pour une seule mesure. Les sept
en-têtes portent `sticky top-0 z-10 bg-surface` : ils restent lisibles pendant
le défilement sans sortir de la grille, donc sans casser le décompte de 49
enfants (`bg-surface` opaque est obligatoire, sinon les cases défilent
au travers). La maquette pose `.mois{overflow:hidden}` (`agenda.html:26`) sur
une grille qui tient toujours dans sa page ; ici c'est `overflow-y-auto`, et
cet `overflow` non visible coupe l'anneau du socle
(`:focus-visible{outline:3px solid;outline-offset:2px}`,
`docs/da/2026-09-05-propositions/maquettes/da/base.css:23`, 5 px hors boîte),
d'où l'anneau **rentrant** sur les puces (§ 3.0). La recette vérifie une
fenêtre basse (§ 11.3). En-têtes :
nœuds séparés `text-sm text-text-muted`, texte
entier `lun.` … `dim.` (maquette `.jt`, `agenda.html:85` ; la regex
d'`etiquettesJours` lit le texte entier) ; ces en-têtes portent `border-b
border-border` et **aucun** `border-l`. Cellules `p-1.5
border-t border-l border-border text-sm` plus `[&:nth-child(7n+1)]:border-l-0` :
les sept en-têtes occupent les enfants 1 à 7 et les 42 cases les enfants 8 à
49, donc `7n+1` retombe exactement sur la première case de chaque rangée (8,
15, 22, 29, 36, 43), comme la maquette `.mois .case:nth-child(7n+1)
{border-left:0}` (`agenda.html:29` ; la ligne 28 porte `.mois .case`
elle-même) ; sans cette exception, le trait de la
première case double la bordure gauche de la `Carte`. Aucun conteneur
intermédiaire autour des en-têtes ni des cases : un `display:contents`
casserait le décompte de 49 enfants du test (§ 9). Hors mois : numéro
`text-text-muted` sans opacité sur la case (B-414), **littéral conservé tel
quel**, § 9 ; aujourd'hui : numéro
`h-[1.4rem] w-[1.4rem] rounded-full bg-accent-fill text-accent-ink grid
place-items-center`. Puces : bouton `text-sm truncate border-l-2
border-domaine-agenda bg-domaine-agenda-tint text-domaine-agenda px-1.5 py-0.5
rounded-sm hover:brightness-95` + anneau **rentrant** (§ 3.0 : la `Carte`
défile, elle clippe). « +N autre » / « +N autres » inchangé,
`text-xs` (non cliquable).

Le test actuel compte deux `div.grid-cols-7` et 42 enfants de la seconde
(`semaineFrancaise.test.tsx:53-56`). Une seule grille maquette : aligner
ce décompte (une seule grille, `grilles[0]`, 7 en-têtes + 42 cases), § 9. Ce
sélecteur ne s'exécute qu'en vue Mois (`viewMode: 'month'` posé au
`beforeEach`, `semaineFrancaise.test.tsx:35-47`), donc la sous-grille
`grid grid-cols-7` de la piste horaire Semaine (§ 3.1) ne le perturbe pas ;
c'est le seul site du dépôt qui interroge ce sélecteur.

## 5. Jour et liste

**Ces deux vues ont le même châssis que les deux autres** (§ 3.0), elles ne
sont pas laissées sans racine : Jour = `Carte as="section"
aria-labelledby="agenda-periode" className="flex-1 min-h-0 flex flex-col"`
(comme la Semaine : le défilement reste sur la piste horaire interne,
`CalendarView.tsx:671`) ; Liste = `Carte as="section"
aria-labelledby="agenda-periode" className="flex-1 min-h-0 overflow-y-auto"`
(comme le Mois : c'est la carte qui défile, d'où l'anneau rentrant sur ses
lignes). Aucune des deux ne garde son `h-full` de racine
(`CalendarView.tsx:637` et `:105`) : la hauteur vient désormais du `flex-1`.

Jour : mêmes jetons et `text-sm` sur les blocs horaires ; `DAY_SLOT_HEIGHT_PX`
et bornes 6-22 inchangés (marqueur B-238 : `06:00`). Gabarit `flex` + gouttière
`w-16` conservé (une seule colonne, rien à aligner sur sept) ; cette colonne
unique porte `border-l border-border` et les lignes d'heure `border-t
border-border`, mêmes traits pleins qu'en semaine (§ 3.1). Aucun fond de
colonne au Jour (la vue entière **est** le jour), donc pas de `z-[1]` à poser
ici. Blocs horaires : `z-10`, `hover:brightness-95` et anneau rentrant, comme
en semaine. Jetons « Toute la journée » (`CalendarView.tsx:661`) : mêmes
classes que les jetons « Journée » de la semaine, `domaine-agenda` au lieu de
`bg-accent-magenta/20`, `hover:brightness-95` et anneau rentrant. **Garder** les
demi-heures `:30` (`CalendarView.tsx:686-697`) et le `h3` interne + suffixe
« (aujourd'hui) » (`CalendarView.tsx:643-649`) : le `h3#agenda-periode` du
panneau porte la date civile complète, le `h3` interne reste le titre de
la grille Jour. Le `h3` interne : `className="text-base font-semibold"`
**sans** `capitalize` (aujourd'hui `CalendarView.tsx:644` ; lot 2 / § 1 :
jamais `capitalize`, première lettre seule en capitale, même règle que
`h3#agenda-periode`). Blocs horaires Jour : même horaire que la semaine,
`HH:MM à HH:MM` (`formatTime(start_datetime)` + ` à ` + `formatTime(end_datetime)`,
plus le ` - ` actuel, `CalendarView.tsx:761-762`) ; si `location`, même
ligne, séparateur ` · `, **sans** garde `layout.height > 50`
(`CalendarView.tsx:764` aujourd'hui masque le lieu sur un bloc court). Même
`px-2 py-0.5` qu'en semaine (§ 3), titre et horaire l'un comme l'autre
`truncate` : à `DAY_SLOT_HEIGHT_PX = 80` inchangé, les
44 px de contenu tiennent **dès 33 minutes** ; en dessous, la ligne d'horaire
est rognée et reste entière dans le nom accessible. Le repère de l'heure du
Jour garde son libellé texte **et sa chaîne de classe exacte** `text-xs
font-medium text-instant ml-2` (`CalendarView.tsx:732-734`) : ce `span` n'est
pas dans un interactif, la garde (6) du § 9 ne le vise pas, et
`lot9DA.test.ts:30` (B-365) reste vert sans qu'on y touche.
Rangée « Toute la journée » **conservée** au-dessus de la
grille (`CalendarView.tsx:652-668`), mêmes jetons `domaine-agenda` que la
semaine, filtre `allDayEvents` inchangé, libellé gutter `text-sm
text-text-muted` « Toute la journée ».

Encres d'accent du Jour et de la Liste : le `h3` interne et son suffixe
« (aujourd'hui) » (`CalendarView.tsx:644` et `647`) ainsi que le `h3` de groupe
de la Liste (`CalendarView.tsx:114`) quittent `text-accent-cyan-ink` pour
`text-accent` (le suffixe garde `ml-2 text-xs font-normal`, il n'est pas dans
un interactif).

Liste : plus de `motion.button` ni `scale` ; **pas** `Ligne`
(`Ligne.tsx:49-55` : le `<button>` ne contient que `{titre}`, aucune prop
`aria-label` : l'horaire et le lieu sortiraient du nom accessible ;
aujourd'hui le `motion.button` concatène résumé + lieu + heure,
`CalendarView.tsx:123-143`). Chaque rendez-vous = un `<button type="button"
className="w-full text-left grid grid-cols-[2rem_1fr_auto] gap-3 items-center
px-4 py-3 border-t border-border hover:bg-surface-2">`
(mêmes colonnes que `Ligne`) + anneau **rentrant** (§ 3.0 : la `Carte`
défile). **Pas de `first:border-t-0`** : la première ligne ne touche jamais le
haut de la `Carte`, le `h3` du premier groupe est au-dessus d'elle
(`CalendarView.tsx:105-143` : un `div` par jour, `h3` puis les boutons), et ce
`border-t` est précisément le trait qui sépare le titre de jour de sa première
ligne. Les lignes d'un groupe sont **accolées**, sans `space-y-2` : c'est le
`border-t` qui les sépare, comme dans `Ligne`. Le survol reste
`hover:bg-surface-2` (motif de
`components/ui/Ligne.tsx:63`) : la ligne n'a pas de teinte de domaine à
préserver, contrairement aux blocs des grilles (§ 3.1) ; puce `aria-hidden`
`h-8 w-8 rounded-sm bg-domaine-agenda-tint
text-domaine-agenda` ; titre `font-semibold text-text` = `summary` ; si
`location`, `p className="text-sm text-text-muted"` = lieu ; droite
`text-text-muted` = `event.all_day ? 'Toute la journée' :
formatTime(event.start_datetime!)`. Nom accessible = concaténation des nœuds
texte (résumé, lieu s'il existe, horaire). Chaîne exacte `Toute la journée`
(pas « toute la journée »). Vide : `EtatVide
titre="Aucun événement"`, sans action. Groupes par jour : `h3 className="text-sm
font-semibold px-4 pt-3 pb-1"` — même `px-4` que les lignes, pour que le titre
de jour et les rendez-vous qu'il coiffe s'alignent sur la même marge gauche —,
`parseLocalDateKey` conservé, tri descendant
`b.localeCompare(a)` inchangé (`CalendarView.tsx:101`). L'espacement entre
groupes vient du `pt-3` du `h3` suivant, plus de `space-y-6` ni de `space-y-2`
(`CalendarView.tsx:111`, `121`) : deux mécanismes d'écartement sur la même
liste, ce sont deux rythmes qui se contredisent.

Fiche : garder « Événement introuvable » si `event` est nul
(`EventDetail.tsx:74-78`).

## 6. Formulaire (`EventForm`, état `nouveau`)

Toujours le remplaçant de la grille : c'est la branche « remplacement
conservé » de la décision 5, la seule que ce document décrive. Tête : retour
`Button ghost icon` `aria-label="Retour"`
(B-578) ; titre `h3` « Nouveau rendez-vous » / « Modifier l'événement » ;
`Button primary md` « Enregistrer » (spinner inchangé). Corps : `FormField`
+ `Input` / `Textarea`. **`htmlFor` = l'id déjà listé** pour chaque champ
(`FormField` n'associe le `<label>` que via `htmlFor`,
`FormField.tsx:53-55` ; sans lui `getByLabelText` casse) :

| Champ | `label` | `htmlFor` / `id` | `required` |
|---|---|---|---|
| Titre | Titre | `eventform-titre` | oui |
| Date de début | Date de début | `eventform-date-de-debut` | oui |
| Heure de début | Heure de début | `eventform-heure-de-debut` | oui (masqué si `allDay`) |
| Date de fin | Date de fin | `eventform-date-de-fin` | oui |
| Heure de fin | Heure de fin | `eventform-heure-de-fin` | oui (masqué si `allDay`) |
| Lieu | Lieu ou visio | `eventform-lieu` | non |
| Description | Description | `eventform-description` | non |
| Participants | Participants | `eventform-participants` | non |
| Agenda affiché | Agenda | `eventform-agenda` | non |

Les quatre libellés d'horaire restent ceux d'aujourd'hui (`EventForm.tsx:317-353`) :
« Date de début », « Heure de début », « Date de fin », « Heure de fin »
(la maquette fusionne en « Date » / « Heure » = P-083, hors lot). L'astérisque
vient de `FormField required`, pas du texte du label.

**Et l'obligation ne doit pas sortir du nom accessible en chemin.** Aujourd'hui
l'astérisque est dans le texte du `<label>` (`EventForm.tsx:290` « Titre * »,
idem `:317`, `:327`, `:341`, `:351`), donc annoncé ; dans `FormField` il
devient `<span … aria-hidden="true">*</span>` (`FormField.tsx:61`), c'est-à-dire
une marque pour l'œil seul. Les cinq champs marqués « oui » dans le tableau
ci-dessus portent donc **l'attribut `required` sur l'`Input`** (Titre, Date de
début, Heure de début, Date de fin, Heure de fin) : `Input` étend
`InputHTMLAttributes` (`Input.tsx:11-14`) et passe l'attribut tel quel, qui
expose `aria-required` implicitement. Aucune validation native n'est
introduite au passage : il n'y a **pas de `<form>`** dans `EventForm`,
l'enregistrement passe par `onClick={handleSave}` (`EventForm.tsx:265`), donc
rien ne peut bloquer une soumission qui n'existe pas. Les deux heures ne sont
rendues qu'en dehors de `allDay` : la garde du § 9 les cherche dans cet état
et vérifie qu'elles disparaissent du DOM dans l'autre. Case à cocher **hors**
`FormField` (le `label` de `FormField` est `block` au-dessus,
`FormField.tsx:53-62`) : rangée `flex items-center gap-3` actuelle
(`EventForm.tsx:301-312`), `<input type="checkbox" id="all-day">` +
`<label htmlFor="all-day" className="text-sm text-text">Événement sur toute
la journée</label>` à côté, pas au-dessus. `htmlFor="all-day"` seul. La case
garde sa classe actuelle (`EventForm.tsx:307`) à une substitution près :
`text-accent-cyan-ink` devient `text-accent` (garde (6) du § 9).
`getByLabelText('Événement sur toute la journée')` conservé.
Participants : `description="Séparez les emails par des virgules"` (aide
actuelle). Placeholder titre « Titre de l'événement » conservé (test).
Placeholder lieu « Atelier, adresse ou lien ».

Erreur : **une seule** `Alerte` `children={formError || guardError}`
(aujourd'hui `const error = formError || guardError` alimente un seul
bandeau, `EventForm.tsx:51,282-286` ; `children` = `error` / `formError`
seul laisserait `guardError` muet). Sans `action`, `data-testid` absent
aujourd'hui. `FormField` ne reçoit **pas**
`error={formError}` : `FormField` rend `<p role="alert">`
(`FormField.tsx:72-76`) et un second « date de fin » ferait échouer
`EventForm.test.tsx:157` `findByText(/date de fin/)`. `FormField error`
seulement si le message est retiré du bandeau.

Agenda affiché : `FormField htmlFor="eventform-agenda" label="Agenda"`
+ `Input id="eventform-agenda" readOnly aria-readonly="true"`
`value={selectedCalendar?.summary ?? ''}`. Le `?? ''` n'est pas décoratif :
`selectedCalendar` vaut `undefined` dès que `currentCalendarId` est nul
(`EventForm.tsx:56`), cas nommé par le garde `EventForm.tsx:48` « Aucun
calendrier sélectionné », et `value={undefined}` ferait basculer un `Input`
contrôlé en non contrôlé. C'est le **seul élément nouveau de l'écran**
(maquette `agenda.html:101`) : il rend visible la destination de
l'enregistrement, qui n'apparaissait jusqu'ici que dans la confirmation
externe (`EventForm.tsx:154`, `162-163`) ; ajout assumé au § 10. **Pas**
`disabled` : `Input` pose `disabled:opacity-50`, le champ sort de la
tabulation, souvent non annoncé, valeur non copiable ; la maquette
`agenda.html:101` est un champ ordinaire. Pas un second sélecteur. Confirmation externe et
`confirm('Abandonner les modifications ?')` inchangés. Grille
`grid-cols-2 max-[1023px]:grid-cols-1`.

## 7. Fiche (`EventDetail`)

Pas d'état maquetté. Tête : `Button variant="ghost" size="icon"`
`aria-label="Retour"` `onClick={() => setCurrentEvent(null)}` (comme § 6 ;
aujourd'hui un `<button>` maison, `EventDetail.tsx:97-103`). Titre **`h3`**
conservé (B-238 le reconnaît). Si
`event` est nul : « Événement introuvable » (`EventDetail.tsx:74-78`),
inchangé. Statut : n'afficher `Etiquette` **que si** `event.status !==
'confirmed'` (`EventDetail.tsx:136-144` aujourd'hui ; sans cette garde
tout rendez-vous `confirmed` sortait « Annulé »). `ton={event.status ===
'tentative' ? 'attention' : 'erreur'}` enfants « Provisoire » / « Annulé ».
Confirmation de suppression : `div` (pas
`Alerte` : ce n'est pas une erreur, lot 3) + `Button ghost md` « Conserver
le rendez-vous » + `Button danger md` « Supprimer définitivement » ; textes
inchangés. Modifier / Supprimer : `Button ghost icon`, `aria-label`
conservés. Horaires, lieu, participants (pluriel `1 participant` /
`N participants`), récurrence, description : `text-sm`, icônes 18 px
`text-accent`.

## 8. Les états (priorité = cascade actuelle, `CalendarPanel.tsx:569-580`)

Les bandeaux stale et erreur totale vivent **au-dessus** de cette cascade
(comme l'erreur #124 aujourd'hui, `CalendarPanel.tsx:562-566`), y compris
quand le formulaire ou la fiche est ouvert. Ils ne rentrent pas dans le
ternaire `loading` / `EventForm` / `EventDetail` / `CalendarView`.

**Un seul bandeau à l'écran, et aucune information supprimée.** Les deux
états ne s'excluent **pas** tout seuls via `classifyCalendarError` :
`loadCalendars` peut laisser `error` (403) et relever `calendarsReady`
(`CalendarPanel.tsx:161-171`) ; `loadEvents` avec `hasCache` pose
`staleWarning` et `error: null` **sur son propre retour**
(`calendarErrors.ts:68`) sans effacer l'erreur agendas
(`CalendarPanel.tsx:180-181` + `215-224`). Aujourd'hui les deux messages sont
rendus (`CalendarPanel.tsx:428-432` et `562-566`) avec deux « Réessayer » :
c'est le **doublon de geste** qu'on ferme, pas la péremption qu'on tait. Une
erreur plus grave ne rend pas la grille moins périmée.

| `error && !needsReauth` | `staleWarning` | Ce qui est rendu |
|---|---|---|
| non | non | rien |
| non | oui | `Alerte` stale (ligne « cache périmé » du tableau ci-dessous) |
| oui | non | `Alerte` erreur totale (ligne « erreur totale » ci-dessous) |
| oui | oui | **une seule `Alerte` fusionnée**, décrite juste après |

`Alerte` **fusionnée** (403 agendas **et** rafraîchissement d'événements raté
avec cache) : `data-testid="calendar-stale-warning"` **conservé** (P-029/P-030
et la garde (1) du § 9 le cherchent dès que `staleWarning` est posé),
`titre={error}` (le message d'agendas, 403 actionnable, #124), `children` = la
phrase de conservation du stale **amputée de son préfixe** « Dernier
rafraîchissement échoué : », soit `Données conservées` suivi de
` (synchronisées le ${lastSyncAt formaté})` quand `lastSyncAt` existe et rien
sinon, `icone={AlertTriangle 18 px}`, **un seul** `action` = `Button
variant="secondary" size="md"` « Réessayer » → `handleSync` (celui de
l'erreur, pas le `ghost` du stale). L'utilisateur lit dans le même bandeau que
l'agenda est en échec **et** que la grille sous ses yeux date.

| État | Aujourd'hui | Cible |
|---|---|---|
| chargement | icône `RefreshCw` qui tourne | trois rangées `aria-hidden` façon semaine : chaque rangée `flex items-center gap-2`, un `Squelette classeBarre="h-8 rounded-sm" largeur="w-8"` **puis** un `Squelette classeBarre="h-8 rounded-sm" largeur="w-[60%]"` (`SqueletteProps.largeur` unique, `Squelette.tsx:12,21` : un seul `Squelette` ne porte pas deux largeurs) ; puis `role="status"` « Chargement de l'agenda… » `text-sm text-text-muted` |
| `isEventFormOpen` | `EventForm` | § 6 |
| `currentEventId` | `EventDetail` | § 7 |
| sinon | `CalendarView` | § 3-5 |
| cache périmé (`staleWarning`) | `<p role="status" className="text-xs text-warning" data-testid="calendar-stale-warning">` « Dernier rafraîchissement échoué : données conservées… » sous le titre | `Alerte data-testid="calendar-stale-warning"` (la primitive impose `role="alert"`, test lot 2 : un `role` appelant ne l'écrase pas ; la maquette aussi) titre « L'agenda est affiché tel qu'il était. » `children` = texte actuel (un seul horodatage `lastSyncAt`, on n'invente pas 11:20 / 11:50) `icone={AlertTriangle 18 px}` `action` = `Button ghost md` Réessayer → `handleSync` ; enveloppe `px-4 pt-3` ; **hors du ternaire** ; si une erreur agendas coexiste, c'est l'`Alerte` fusionnée ci-dessus qui est rendue, jamais deux bandeaux |
| erreur totale (`error && !needsReauth`) | bandeau `bg-error/10` au-dessus de la cascade | `Alerte` titre absent, `children` = `error` (403 actionnable conservé, #124), `icone={AlertCircle 18 px}` `action` = `Button secondary md` Réessayer → `handleSync` ; si `staleWarning` coexiste, c'est l'`Alerte` fusionnée ci-dessus (titre = `error`, corps = la conservation) |
| reauth | bandeau ambre + « Reconnecter » | hors `Alerte` (pas une erreur de lecture) ; `px-4 py-3 border-b border-border bg-warning-tint` (l'utilitaire existe : `--color-warning-tint` est déclaré dans `@theme`, `src/frontend/src/styles/globals.css:141`, contrairement aux teintes restées dans `:root`, B-109) ; texte actuel ; **toute** la couleur d'agent retirée, pas seulement le fond : `text-agent-amber` du paragraphe (`CalendarPanel.tsx:534`) devient `text-warning`, l'icône `AlertTriangle` voisine est déjà `text-warning` (`CalendarPanel.tsx:533`) et ne bouge pas, et le `Button ghost md` « Reconnecter » / « En attente... » + `Spinner` perd la surcharge `className="text-agent-amber hover:text-agent-amber"` (`CalendarPanel.tsx:542`) : un état dit en deux couleurs se lit comme deux états |
| overlay | `bg-black/60` | `bg-bg/80` (plus de `black`) |

Un seul « Réessayer » à l'écran, dans tous les cas : 1 sur l'`Alerte` stale,
1 sur l'`Alerte` d'erreur totale, 1 sur l'`Alerte` fusionnée quand les deux
états coexistent, 0 sur chargement, grilles, formulaire, fiche, reauth, vide
liste (le bandeau reauth garde son « Reconnecter », qui n'est pas un
« Réessayer »). Jamais deux bandeaux d'erreur ensemble, et jamais un état tu
parce qu'un autre est plus grave.

Pied sous la grille (prêt seulement, pas sur formulaire / fiche /
chargement) : `shrink-0 text-xs font-medium text-text-muted`, second enfant du
conteneur `h-full flex flex-col gap-2 p-4` de la branche « grille » (§ 3.0 —
le `gap-2` remplace le `mt-2`, et le `shrink-0` empêche la carte de le
comprimer). Il n'existe pas aujourd'hui : c'est, avec le champ « Agenda » du
formulaire, le second des deux seuls éléments nouveaux de l'écran, assumé au
§ 10. Résumé = calendrier
**courant** (`const courant = calendars.find(c => c.id === currentCalendarId)`).
**Aucun pied du tout si `courant` est `undefined`** : c'est l'état de premier
lancement, celui que protège BUG-143 (aucune création d'agenda avant geste
explicite), et `calendars: []` avec `currentCalendarId: null` s'y montent
ensemble (`src/frontend/src/components/calendar/CalendarPanel.nomsAccessibles.test.tsx:52`
rend exactement cet état, puis la grille). Sans cette garde, `courant.provider`
lève, et le suffixe ci-dessous s'afficherait sur une liste vide en annonçant
« aucun agenda en ligne branché » là où il n'existe aucun agenda. Quand
`courant` existe : `Agenda local « {summary} »` si `courant.provider ===
'local'`, sinon `{summary}`. Suffixe ` · aucun agenda en ligne branché` si
**aucun** des `calendars` n'est en ligne, liste non vide :
`calendars.length > 0 && !calendars.some(c => c.provider !== 'local')`
(`Calendar.provider` vaut `'local' | 'google' | 'caldav'`,
`src/frontend/src/services/api/calendar.ts:16` ; un CalDAV branché **est**
en ligne). Pas `=== 'google'` seul (un CalDAV sans Google affichait le
suffixe à tort). Pas « le courant n'est pas google ». Pas de légende
Rendez-vous / Prospects / Tâches (P-082).

## 9. Gardes mécaniques et tests à aligner

Nouveaux, rouges d'abord :

`CalendarPanel.da.test.tsx` : (1) `data-testid="calendar-panel"` et
`calendar-stale-warning` encore là ; (2) `Segments` nommé « Vue de l'agenda »,
quatre `aria-pressed`, clic « Semaine » appelle `setViewMode('week')` et
`setCurrentEvent(null)` ; (3) « Nouveau rendez-vous » `size` visuel `h-11`,
clic pose `isEventFormOpen` ; (4) un seul « Réessayer » à l'écran dans tous les cas ; le cas
403 calendriers + échec events avec cache rend **une seule** `Alerte`, qui
porte `data-testid="calendar-stale-warning"`, dont le **titre contient le
message 403** et le corps la phrase de conservation, avec **un** seul
« Réessayer » : ni deux bandeaux, ni une péremption tue ; stale seul appelle
`handleSync` ; zéro « Réessayer » sur grille saine, reauth, chargement ;
stale visible aussi formulaire / fiche ouverts (hors ternaire) ; (5)
sélecteur `aria-label="Agenda affiché"` est un `Select`, liste vide
sans bouton créer, et **plus aucune occurrence de « Calendrier »** dans un
`aria-label` des quatre fichiers (dialogue compris, `CalendarPanel.tsx:617`) :
le lexique porte aussi sur les noms accessibles (§ 1) ; (6) aucune classe
`text-xs` dans le sous-arbre d'un
interactif ; **garde de palette nommée**, et non l'extension
d'`aucuneCouleurEnDur` : ce test ne cherche que `#hex`, `rgb(`, `hsl(` et
`color-mix(` hors commentaire (`components/ui/aucuneCouleurEnDur.test.ts:38-39`)
alors que les quatre fichiers n'en contiennent aucune aujourd'hui (le seul
`#124` est en commentaire, `CalendarPanel.tsx:69` et `180`), donc l'étendre
donnerait une garde verte avant la première ligne de code et aveugle à tout ce
que ce lot retire. La garde utile interdit **nommément**, dans
`CalendarPanel.tsx`, `CalendarView.tsx`, `EventForm.tsx` et `EventDetail.tsx`,
toute occurrence de `bg-black` et des familles `(bg|text|border)-accent-cyan`,
`(bg|text|border)-accent-magenta`, `(bg|text|border)-agent-amber` (regex ancrée
sur le préfixe, pour attraper les variantes d'opacité `bg-black/60`,
`bg-accent-cyan/5`, `bg-accent-magenta/20`, `bg-agent-amber/10`,
`border-agent-amber/20`, et les encres `text-accent-cyan-ink`,
`text-agent-amber`). Elle est rouge aujourd'hui, et voici **les vingt-trois
lignes** qu'elle doit faire tomber, celles que rend
`grep -nE 'bg-black|(bg|text|border)-accent-(cyan|magenta)|(bg|text|border)-agent-amber'`
sur les quatre fichiers, sans en omettre une : `CalendarPanel.tsx:445`, `532`,
`534`, `542`, `572`, `608` ; `CalendarView.tsx:114`, `257`, `407`, `413`,
`441`, `509`, `522`, `644`, `647`, `661`, `750` ; `EventForm.tsx:307` ;
`EventDetail.tsx:140`, `153`, `183`, `191`, `210`. Aucune n'est laissée sans
destination : le
sélecteur de vue et le `RefreshCw` disparaissent (§ 2, § 8), les blocs et les
puces passent en `domaine-agenda` (§ 3, § 4, § 5), les jetons « Toute la
journée » du Jour (`CalendarView.tsx:661`) aussi (§ 5), les numéros et encres
d'accent passent en `text-accent` (§ 3), la case à cocher et le suffixe
« (aujourd'hui) » sont traités § 6 et § 5, le badge de statut
(`EventDetail.tsx:140`) devient `Etiquette ton="attention"` et les quatre
icônes de la fiche (`EventDetail.tsx:153`, `183`, `191`, `210`) passent en
`text-accent` (§ 7). `bg-instant` et `text-instant`
restent permis, ce sont les jetons du repère ; (7) overlay : plus de
`bg-black` ; (8) groupe Segments + « Nouveau rendez-vous » porte `ml-auto` ;
(9) pied : **aucun pied rendu** quand `calendars: []` et
`currentCalendarId: null` (l'état monté par
`src/frontend/src/components/calendar/CalendarPanel.nomsAccessibles.test.tsx:52`),
donc ni résumé ni suffixe sur une liste vide ; suffixe « aucun agenda en ligne
branché » absent si un `provider === 'caldav'` (présent seulement si au moins
un agenda existe et que tous sont `local`) ; (10) chargement : chaque rangée = deux `Squelette` (`w-8` puis
`w-[60%]`), pas un seul ; (11) **châssis** : sur la branche « grille », le
parent commun de la vue et du pied porte `h-full flex flex-col`, le pied porte
`shrink-0`, et la zone de contenu (`CalendarPanel.tsx:569`) garde
`flex-1 overflow-hidden` **inchangé** ; formulaire, fiche et chargement ne
reçoivent pas ce conteneur (le padding ne se double pas).

`CalendarView.da.test.tsx` : (1) semaine : 7 colonnes, « lun. » … « dim. »,
ligne `bg-instant` avec `role="img"` et `aria-label` `/Il est/` **seulement
si `nowLineTop !== null`** (même garde que `CalendarView.tsx:379-382` : pas
dès que aujourd'hui est dans la semaine) ; en-tête, rangée « Journée » et
piste horaire partagent `grid-cols-[3.5rem_repeat(7,1fr)]` (pas de `w-16`
sur « Journée ») ; les sept colonnes de jour portent `border-l border-border`
dans les trois gabarits et la gouttière des heures n'en porte aucune ; les
lignes d'heure portent `z-[1]` et les blocs `z-10` (le fond `bg-surface-2` de
la colonne du jour ne les efface pas) ; la colonne de la piste du jour courant
est `bg-surface-2` et **jamais** `bg-accent-tint`, réservé à sa cellule
d'en-tête ; (2) un bloc = un `button`, titre
en `text-sm`, résumé entier dans le nom accessible (chaîne non coupée) ;
horaire `HH:MM à HH:MM` **en semaine et en jour** ; Jour : lieu sur la
même ligne s'il existe (pas de garde `height > 50`) ; aucun `capitalize`
sur le `h3` interne Jour ; (3) deux rendez-vous au même créneau : **asserter
le `style` des deux boutons** (`left: '0%'` et `left: '50%'`, `width`
correspondant), pas seulement `leftPercent` du helper ; (4) mois : 7
en-têtes `lun.`…`dim.` + 42 cellules, première = lundi, aujourd'hui en
`bg-accent-fill` ; **c'est la `Carte` qui défile** (`overflow-y-auto`) et le
`div.grid-cols-7` ne porte **aucun** `overflow` ; la grille porte `min-h-full`
et `grid-rows-[auto_repeat(6,minmax(5.5rem,1fr))]`, aucune cellule ne porte
`min-h-[5.5rem]` ; les sept en-têtes portent `sticky top-0` et un fond opaque ;
(5) liste :
un `<button>` par événement dont le nom accessible **contient** le résumé
et l'horaire (ou « Toute la journée ») ; droite visuelle « Toute la journée »
pour un `all_day` ; chaque ligne porte `border-t border-border` et **aucune**
ne porte `first:border-t-0` (le `h3` de groupe la précède, § 5) ; vide =
`EtatVide` « Aucun événement » ; (6) **les quatre vues** : la racine est une `section`
qui porte `aria-labelledby="agenda-periode"` et les classes `flex-1` et
`min-h-0`, et **aucune ne porte `h-full`** ; (7) survol et focus : chaque bloc,
jeton et puce des vues Semaine, Mois et Jour porte `hover:brightness-95`, la
ligne de la Liste `hover:bg-surface-2`, et tout interactif d'une vue porte
`focus-visible:outline-offset-[-3px]` (anneau rentrant, § 3.0).

`EventForm.da.test.tsx` : ids des champs encore là, chaque `FormField`
porte `htmlFor` égal à l'id, `FormField` « Lieu ou visio », case « toute
la journée » **hors** `FormField` (`getByLabelText('Événement sur toute la
journée')` via `htmlFor="all-day"`), Enregistrer
toujours `md`, titre « Nouveau rendez-vous » hors édition, agenda affiché
`readOnly` + `aria-readonly="true"` (pas `disabled`), une seule
`role="alert"` pour `formError || guardError` (les deux sources, un bandeau) ;
**obligation annoncée** : `expect(getByLabelText(/^Titre/)).toBeRequired()` et
les quatre champs d'horaire de même, `allDay` décochée ; `allDay` cochée, les
deux heures sortent du DOM (`queryByLabelText(/^Heure de début/)` nul) et les
trois autres restent requis. Le champ « Agenda » n'est **pas** requis. Les
regex sont **ancrées, pas des chaînes exactes** : `FormField` colle
l'astérisque au libellé (`{label}` puis
`{required && <span … aria-hidden="true">*</span>}`,
`FormField.tsx:60-61`) et `aria-hidden` ne retire rien du `textContent` que
lit `getByLabelText`, donc le label vaut `Titre*` et une égalité stricte
échouerait — pour une raison qui n'a rien à voir avec ce qu'on veut prouver.
Aucun test existant n'est concerné : les deux seuls `getByLabelText` du
périmètre visent la case à cocher, hors `FormField`
(`EventForm.test.tsx:138`), et `/Participants/i`, champ non requis
(`EventForm.agendaLocal.test.tsx:30`) ; rien à aligner de ce côté.

`EventDetail.da.test.tsx` : titre `h3`, `Button ghost icon` `aria-label="Retour"`
appelle `setCurrentEvent(null)`, confirmation sans `role="alert"`,
boutons `md` / `icon`, « Événement introuvable » si id inconnu ;
`Etiquette` absente si `status === 'confirmed'`, « Provisoire »
`ton="attention"` si `tentative`, « Annulé » `ton="erreur"` si autre
statut non confirmé.

**Gardes textuelles existantes qui lisent le nœud exact réécrit par ce lot,
à garder vertes sans réécrire une seule assertion** :

- `src/frontend/src/test/lot11.test.ts:48-53` (B-414) exige
  `/isCurrentMonth \? 'text-text' : 'text-text-muted'/` dans
  `CalendarView.tsx`. Le § 4 réécrit ce nœud : la chaîne
  `isCurrentMonth ? 'text-text' : 'text-text-muted'` (guillemets **simples**,
  espaces compris) doit survivre **telle quelle**, comme sous-expression du
  ternaire imbriqué `isToday ? PASTILLE : isCurrentMonth ? 'text-text' :
  'text-text-muted'`. Le test n'est pas réécrit : c'est le code qui garde le
  littéral.
- `src/frontend/src/test/lot9DA.test.ts:30` (B-365) exige
  `/text-xs font-medium text-instant ml-2/` dans le même fichier, pourtant
  entièrement restylé. La chaîne reste sur le `span` de l'heure du repère Jour
  (`CalendarView.tsx:732-734`, § 5), qui n'est pas dans un interactif : la
  garde (6) ne le vise pas, rien à réécrire non plus.

À aligner, forme seulement : `CalendarView.semaineFrancaise.test.tsx`
`['Lun','Mar','Mer','Jeu','Ven','Sam','Dim']` → `['lun.','mar.','mer.','jeu.','ven.','sam.','dim.']`
(regex d'`etiquettesJours` idem, ancrée sur le texte **entier** d'un `div`,
d'où les deux nœuds jour / numéro en semaine et les 7 en-têtes séparés en
mois) ; le test « première cellule » (`:50-62`) : ne plus exiger
`grilles.length === 2` mais `grilles.length === 1`, et lire `grilles[0]` et
non `grilles[1]` ; 7 en-têtes + 42 cases
(`enfants.length === 49`, `enfants.slice(7)` pour les numéros `['31','1','2']`).
Le sélecteur `container.querySelectorAll('div.grid-cols-7')` (`:53`) reste
**inchangé** : la grille est un `div` enfant de la `Carte` (§ 4), pas la
`section` elle-même ;
`CalendarPanel.retourGrille.test.tsx` marqueur Mois/Semaine `'Mer'` → `'mer.'`,
Liste `heading level 4` → `getByRole('button', { name: (n) => n.includes(RESUME) })`
(le nom concatène résumé + horaire, égalité stricte sur `RESUME` seul
casserait) ;
`EventForm.test.tsx` placeholder titre **inchangé**, `findByText(/date de
fin/)` **inchangé** (une seule occurrence : le bandeau) ; `getByLabelText(
'Événement sur toute la journée')` (`EventForm.test.tsx:138`) et
`getByLabelText(/Participants/i)` (`EventForm.agendaLocal.test.tsx:30`)
conservés par `htmlFor`. Aucune assertion de comportement n'est retirée.
`parcours-07` clique « Nouvel événement » sur `MeetingConversationCard` :
hors lot.

## 10. Ce que ce lot ajoute, et ce qu'il ne fait pas

**Ce qu'il ajoute à l'écran**, et ce sont les deux seuls éléments nouveaux.

1. **Le champ « Agenda »** en lecture seule du formulaire (`FormField` +
   `Input readOnly aria-readonly`, § 6 ; maquette `agenda.html:101`). Il rend
   visible la destination de l'enregistrement, qui n'apparaissait jusqu'ici
   que dans la confirmation externe (`EventForm.tsx:154`, `162-163`).
2. **Le pied sous la grille** (§ 8). Aucun équivalent aujourd'hui : le grep
   sur « en ligne branché » et « Agenda local » ne rend rien dans
   `src/frontend/src`, et la maquette ne montre à cet endroit qu'une légende
   de domaines, écartée (P-082, `agenda.html:92`). Il est assumé parce qu'il
   répond à une question que l'écran laissait sans réponse : sur quel agenda
   j'écris, et est-ce qu'il monte quelque part. C'est la contrepartie visible
   de BUG-143 — on ne crée aucun agenda en ligne à la place de l'utilisateur,
   donc on lui dit quand il n'en a pas — et c'est exactement pour cela qu'il
   **disparaît entièrement** quand il n'existe aucun agenda du tout (§ 8,
   garde (9) du § 9).

Ni l'un ni l'autre ne touche les données, le store ou la destination : c'est
de l'affichage, et les deux se testent (§ 9, `EventForm.da.test.tsx` et
`CalendarPanel.da.test.tsx`). En revanche le `h3` de période ne gagne **pas**
de suffixe « (aujourd'hui) » (§ 1) : `getNavLabel()` n'en a pas
(`CalendarPanel.tsx:333-341`), la vue Jour en rend déjà un dix pixels plus bas
(`CalendarView.tsx:646-648`), et un troisième élément nouveau qui répète le
deuxième n'aurait rien apporté. Le reste de ce paragraphe énumère ce qui
**n'est pas** fait.

- Panneau latéral 26 rem, grille encore visible pendant la saisie (`.panneau`,
  `agenda.html:36-38`). Aujourd'hui le formulaire remplace le contenu ; le
  superposer changerait les cibles de clic. **Écart déjà dessiné** (état
  maquetté `nouveau`, critère `ecrans.json:123`), nommé et non escamoté : ce
  document décrit intégralement la branche « remplacement conservé », et la
  branche « panneau 26 rem » réclame une version dédiée du design avant toute
  ligne de code, dont la décision 5 liste les cinq points à fixer.
  L'arbitrage est à Ludo. Un numéro de portail n'esquive pas cet état.
- Tâches et prospects dessinés sur la grille, légende de domaines, pastille
  « à préparer ». L'API ne livre que des `CalendarEvent`. **P-082**.
- Champ « Avec » qui résout un contact et propose de le créer s'il est
  absent ; plage « 10:00 à 11:00 » en un champ. Aujourd'hui : e-mails et
  quatre champs d'horaire (« Date de début », « Heure de début », « Date de
  fin », « Heure de fin »). **P-083**.
- `MeetingConversationCard` / scénario `meeting` (autre surface).
- Aucun changement de données, d'API, de store ni de navigation.

## 11. Plan de preuve

1. Tests rouges d'abord (§ 9), vérifiés rouges pour la bonne raison,
   sabotage par remplacement inverse, `.agents-sync-paused` posé.
2. Six portes : ruff, pytest (XML), vitest json, tsc, eslint (27), mypy 951.
3. Recette visuelle sur la pile jetable (17393 et 1420, jamais 17293) :
   états forcés par interception Playwright de `/api/calendar/calendars` et
   `/api/calendar/events` (semaine avec deux rendez-vous qui se chevauchent ;
   mois ; liste vide ; `stale` = 500 events + cache déjà là ; 403 Google ;
   403 calendriers **puis** échec events avec cache = **un seul bandeau qui
   dit les deux** (titre 403, corps « données conservées », un « Réessayer ») ;
   reauth ; chargement lent ; ouverture « Nouveau rendez-vous »). Largeurs
   1280, 1024, 840, 800 px **et deux hauteurs, 900 et 640 px** (une hauteur,
   pas seulement une largeur : c'est elle qui décide si la sixième semaine du
   mois est atteignable) ; clair, sombre, contraste élevé ; trois tailles
   de police. Captures `.cartography-work/validation/da-lot8/`, rapport
   `docs/da/2026-09-11-lot8-recette.md`. Vérifier : sept colonnes, ligne de
   l'heure (sur les sept colonnes de jour, jamais dans la gouttière des
   heures), titre entier au focus, un seul « Réessayer », BUG-143 (pas de
   création d'agenda, et **aucun pied** quand la liste d'agendas est vide),
   établi visible, anneau 3 px sur un bloc et un segment, rangée « Journée »
   si un `all_day`, libellé de semaine à cheval sur deux mois, bordure gauche
   du mois sur un seul trait, et horaire encore lisible sur un rendez-vous de
   45 minutes en semaine comme en jour. S'y ajoutent, et ce sont des contrôles
   à part entière :
   - **la grille horaire défile encore, et la ligne de l'heure est atteinte au
     montage** (semaine et jour, aux deux hauteurs) : la vue ouverte sur
     l'heure courante sans geste, et le bas de la journée accessible à la
     molette ;
   - **un bloc posé sur la colonne du jour courant se détache du fond**, et
     le quadrillage des heures reste visible sous ce fond (`z-[1]`) ;
   - **en vue Mois sur 640 px de haut**, la sixième semaine s'atteint au
     défilement et les sept en-têtes restent en place ; sur 900 px, aucune
     bande vide sous la grille à l'intérieur de la carte ;
   - **le pied reste sous la grille** aux deux hauteurs, sans être comprimé ni
     emporté par le défilement ;
   - **le survol** d'un bloc, d'une puce et d'une ligne de liste, dans les
     trois thèmes (en contraste élevé le retour de survol ne se voit pas, § 3 ;
     c'est l'anneau de focus qui fait foi, et il doit, lui, se voir partout) ;
   - **à montrer à l'humain** : le lexique étendu aux noms accessibles (§ 1),
     `aria-label="Agenda"` sur le dialogue et « Agenda affiché » sur le
     sélecteur. Rien dans le dépôt ne tranchait ce périmètre ; la décision est
     prise ici par défaut et Ludo peut la renvoyer au texte visible seul.
4. Revue adverse du diff avant le tag, `/release-therese 0.72.0-alpha` avec
   le GO de Ludo (toute la DA, pas ce lot seul). L'arbitrage de la décision 5
   se rend **avant le code**, pas avant le tag : coder la branche
   « remplacement conservé » décrite ici, c'est la choisir de fait.

## Points non repris

**Revue de la v4 : aucune ligne « Non repris ».** Les douze constats du
journal `.cartography-work/reviews/opus-da-lot8-agenda-design-v4.log`
(1-12, VERDICT NO-GO) ont été vérifiés un par un dans les fichiers cités, et
les douze sont fondés : douze repris, zéro non repris.

| # | Sujet | Preuve vérifiée | Où c'est repris |
|---|---|---|---|
| 1 | P1, `min-h-0` inerte, la grille perd sa hauteur | les quatre racines tiennent leur hauteur d'un `h-full` (`CalendarView.tsx:390`, `225`, `637`, `105`) ; la zone parente est `flex-1 overflow-hidden` (`CalendarPanel.tsx:569`) | § 3.0 châssis (`flex-1 min-h-0` sur une `Carte` cette fois flex, zone de contenu inchangée et justifiée) ; § 3.1, § 4, § 5 ; § 9 garde (11) et `CalendarView.da` (6) ; § 11.3 « la grille horaire défile encore, la ligne de l'heure est atteinte au montage » |
| 2 | P2, colonne du jour de la même teinte que les blocs | `--color-accent-tint` et `--color-domaine-agenda-tint` : `#DEF4F9` / `#DEF4F9` (`globals.css:47`, `:86`), `#15314B` / `#15334D` (`:200`, `:215`), `#000000` / `#000000` (`:546`, `:521`) | § 3.1, colonne et cellule « Journée » en `bg-surface-2`, `bg-accent-tint` réservé à l'en-tête ; lignes d'heure en `z-[1]` pour survivre au fond opaque ; § 9 `CalendarView.da` (1) ; § 11.3 |
| 3 | P2, liste des lignes de palette incomplète | le grep rend 23 lignes, dont `EventDetail.tsx:140`, `153`, `183`, `191`, `210` et `CalendarView.tsx:661`, absentes des 17 listées | § 9 garde (6), 23 lignes et leur destination nommée |
| 4 | P2, suffixe « (aujourd'hui) » = second élément nouveau et doublon | `getNavLabel()` n'a aucun suffixe (`CalendarPanel.tsx:333-341`) et le Jour en rend déjà un (`CalendarView.tsx:646-648`) | § 1 ligne « Période » (suffixe retiré) ; intro et § 10, qui recensent les deux vrais ajouts, champ « Agenda » et pied |
| 5 | P2, Mois : hauteur minimale sans défilement | aujourd'hui `flex-1 grid grid-cols-7 gap-2 overflow-hidden` sans hauteur minimale (`CalendarView.tsx:236`), parent clippant (`CalendarPanel.tsx:569`) | § 4, `Carte` en `overflow-y-auto`, grille en `min-h-full grid-rows-[auto_repeat(6,minmax(5.5rem,1fr))]`, en-têtes `sticky`, anneau rentrant ; § 9 `CalendarView.da` (4) ; § 11.3 deux hauteurs |
| 6 | P2, obligation perdue dans le nom accessible | `FormField.tsx:61` rend l'astérisque `aria-hidden`, là où `EventForm.tsx:290`, `317`, `327`, `341`, `351` la portent dans le texte du label | § 6, `required` sur les cinq `Input` (et pas de `<form>`, `EventForm.tsx:265`) ; § 9 `EventForm.da` |
| 7 | P3, semaine sans séparateurs de colonnes | `CalendarView.tsx:406`, `435`, `508` portent `border-l` ; maquette `agenda.html:10` et `:15` | § 3.1, `border-l border-border` sur les sept colonnes, rien sur la gouttière, lignes d'heure au trait plein ; § 9 `CalendarView.da` (1) |
| 8 | P3, Jour et Liste sans châssis | `CalendarView.tsx:637` et `:105` n'étaient visés par aucune consigne | § 3.0 et § 5, les quatre vues sont des `Carte as="section"` ; § 9 `CalendarView.da` (6) |
| 9 | P3, `agenda-periode` inutilisé, sections non nommées | maquette `agenda.html:73` et `:84` nomment les deux sections | § 1 et § 3.0, `aria-labelledby="agenda-periode"` pour les quatre vues |
| 10 | P3, survol retiré des grilles, conservé sur la Liste | `CalendarView.tsx:257`, `441`, `522` portent un `hover:` aujourd'hui | § 3.1, `hover:brightness-95` (motif `Button.tsx:31`) sur blocs, jetons et puces, `hover:bg-surface-2` sur la Liste, limite du contraste élevé écrite ; § 9 `CalendarView.da` (7) ; § 11.3 |
| 11 | P3, deux renvois de maquette faux | l'élément `.actions` est en `agenda.html:69` (la 70 est vide), `nth-child(7n+1)` en `agenda.html:29` (la 28 porte `.mois .case`) | § 1, § 2 et § 4, renvois corrigés |
| 12 | P3, « Agenda » à l'œil, « Calendrier » au lecteur d'écran | `CalendarPanel.tsx:617` et `:516` ; l'extracteur du lexique ne lit que `<h1-3>` et le `<p>` de titre (`lexiqueTitres.test.ts:44-59`) | § 1, note du lexique : `aria-label="Agenda"` sur le dialogue, « Agenda affiché » sur le `Select` ; § 9 garde (5) ; § 11.3, point montré à l'humain |

Deux précisions de forme, qui ne changent rien au fond repris. Le constat 2
renvoie à « la garde (7) du § 9 » pour l'interdiction de `color-mix(` : la
garde (7) porte sur l'overlay, et l'interdiction vient d'ailleurs
(`aucuneCouleurEnDur.test.ts:38`, dont le balayage ne couvre même pas ces
quatre fichiers, `:27-32`) ; le § 3.1 le dit exactement, et n'ouvre pas la
brèche pour autant. Le constat 5 chiffre six rangées à 33 rem : c'est le cas
au `rem` par défaut, et davantage aux tailles de police supérieures, ce qui
renforce le constat plutôt que de l'affaiblir — d'où les deux hauteurs de
recette et non une seule.

Aucun constat de la v3 n'est écarté non plus, et la vérification a porté sur
les fichiers cités, pas sur le libellé du constat. Les 10 constats du journal
`.cartography-work/reviews/opus-da-lot8-agenda-design-v3.log` (1-10,
VERDICT NO-GO) sont tous fondés et repris dans le corps :

| # | Sujet | Où c'est repris |
|---|---|---|
| 1 | P1, péremption tue par l'erreur 403 | § 8, `Alerte` fusionnée + § 9 garde (4) + § 11.3 |
| 2 | P1, hauteur d'heure ramenée à 48 px | § 3, `HOUR_HEIGHT_PX = 60` conservé, seuils 44 min / 33 min, `py-0.5` ; § 5 |
| 3 | P1, pied de grille sans agenda courant | § 8, pied absent si `courant` indéfini ; § 9 garde (9) ; § 11.3 |
| 4 | P2, gardes textuelles non listées | § 9, littéraux `lot11.test.ts` et `lot9DA.test.ts` conservés tels quels |
| 5 | P2, garde « aucune couleur en dur » sans portée | § 9 garde (6), garde de palette nommée, rouge aujourd'hui |
| 6 | P2, champ « Agenda » non contrôlé et non annoncé | § 6, `?? ''` ; § 10, ajout assumé ; intro |
| 7 | P2, une seule des deux issues de la décision 5 | intro, décision 5 (cinq points à fixer), § 6, § 10, § 11.4 |
| 8 | P3, grille Mois et sélecteur du test | § 4, `div` enfant de la `Carte`, sans bordure redoublée |
| 9 | P3, conteneur positionné de la ligne de l'heure | § 3, `col-start-2 col-span-7 relative` |
| 10 | P3, couleur d'agent restante sur reauth | § 8, `text-warning` et `Button ghost md` sans surcharge |

Deux précisions de fond, plutôt que des exemptions : le constat 2 dit que
l'horaire d'un rendez-vous « de moins d'une heure » n'est plus visible ; le
seuil réel d'aujourd'hui est 40 minutes (`text-xs`, 40 px de contenu à 60 px
par heure), et il passe à 44 minutes après ce lot, ce que le § 3 chiffre au
lieu de le laisser deviner. Le constat 4 dit que `lot9DA.test.ts` passera au
rouge ; la chaîne visée vit sur un `span` non interactif que rien n'oblige à
changer, et le § 5 la fige explicitement pour que ce risque ne se réalise pas.
Aucun des deux ne justifie de ne rien faire, les deux sont donc repris.

Les 12 constats de la v2
(`.cartography-work/reviews/grok-da-lot8-agenda-design-v2.log`) et les 19 de
la v1 (`.cartography-work/reviews/grok-da-lot8-agenda-design-v1.log`) restent
repris.
