# DA « Application affinée », lot 8 : l'écran Agenda (design à challenger avant le code)

Version 4, 11/09/2026 09:39, après la revue de la v3 (10 points repris, 0 non repris) ; journal `.cartography-work/reviews/opus-da-lot8-agenda-design-v3.log`. Précédent : lot 3 (Tiroir), sur `main` ; cadence : une
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
mêmes données, les mêmes états, les mêmes destinations. **Un seul élément
nouveau apparaît à l'écran** : le champ « Agenda » en lecture seule du
formulaire, qui affiche une donnée déjà connue du composant (maquette
`agenda.html:101`, § 6, assumé au § 10) ; tout le reste est déjà rendu
aujourd'hui. L'état maquetté
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
| Période | `<h3 className="capitalize">` + `getNavLabel()` | `<h3 id="agenda-periode" className="text-base font-semibold">` ; jour : `toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })` puis première lettre seule en capitale (lot 2, jamais `capitalize`) ; si `localDateKey(selectedDate) === localDateKey(new Date())`, suffixe ` (aujourd'hui)` ; semaine : libellé ci-dessous (bornes lundi-dimanche inchangées, `getDay()` + offset actuel) ; mois/liste : mois long + année, première lettre seule en capitale |
| Sélecteur | `<select aria-label="Calendrier affiché">` maison, `Z_LAYER.ONBOARDING` | `Select` même `aria-label`, `options={calendars.map(c => ({ value: c.id, label: c.summary }))}`, `value={currentCalendarId \|\| ''}`, même `onChange` ; wrapper `relative` + z-index conservé (BUG-049) ; liste vide : aucune option, pas de bouton « créer » (BUG-143) |
| Sync / ICS | `Button ghost sm` | `Button variant="ghost" size="icon"` ; `aria-label` / `title` conservés (« Synchroniser l'agenda », « Importer un fichier .ics », « Exporter en .ics ») ; `input.hidden` inchangé |
| Segments + geste | modes + « Nouvel événement » dans `calendarHeader` (droite) | dans la rangée fusionnée, groupe `className="ml-auto flex flex-wrap gap-2"` (`basis-full` sous 840 px, déjà annoncé sur le conteneur) = `Segments` puis le `Button variant="primary" size="lg"` « Nouveau rendez-vous » ; maquette `.vue-tete .actions{margin-left:auto}` (`agenda.html:7,70`). Sans `ml-auto` le groupe reste collé au sélecteur / sync, pas à droite |
| Fermer (overlay) | `<button>` sans nom | `Button variant="ghost" size="icon"` `aria-label="Fermer l'agenda"` (absent en `standalone`) |

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
seconde barre ; maquette `.vue-tete .actions`, `agenda.html:7,70`). Ordre
visuel de la maquette, ids du store : Jour `day`, Semaine `week`,
Mois `month`, Liste `list`. `Segments label="Vue de l'agenda" valeur={viewMode}
onChange={(id) => choisirVue(id as …)}` (groupe + `aria-pressed`, pas un
`tablist`). Pas `sm` : `classeSegment` est déjà `text-sm`. Geste :
`Button variant="primary" size="lg"` icône `Plus` 18 px, libellé « Nouveau
rendez-vous », `onClick={handleNewEvent}`.

## 3. Grille semaine (`CalendarView` `WeekView`)

`Carte as="section" aria-label={période} className="flex flex-col min-h-0"`
(**sans** `overflow-hidden`). La maquette pose `.semaine{overflow:hidden}`
(`agenda.html:8`) ; collée sur la carte, elle tuerait le scroll interne
actuel `flex-1 overflow-y-auto` (`CalendarView.tsx:453`). Le scroll reste
sur la grille horaire.

Grille `grid-cols-[3.5rem_repeat(7,1fr)]` (gutter `3.5rem` de la maquette,
**7** colonnes). **Même gabarit** pour l'en-tête, la rangée « Journée » et
la piste horaire : aujourd'hui les trois sont du `flex` + gutter `w-16`
(4 rem, `CalendarView.tsx:396-398`, `423-450`, `456`) ; coller `3.5rem` sur
l'en-tête / les heures et garder `w-16` sur « Journée » décale les jetons
sous le mauvais jour. En-tête : **deux nœuds distincts** par jour (comme
aujourd'hui, pas collés « mar.1 » comme `agenda.html:75`) : un `div` dont
le texte entier est `lun.` … `dim.` (`text-sm text-text-muted`) + un nœud
numéro `text-base font-semibold tabular-nums` ; aujourd'hui : numéro
`text-accent`, colonne `bg-accent-tint`. Heures : `text-xs tabular-nums
text-text-muted` (non interactif, plancher 12 px). Pas de `bg-accent-cyan/5`.

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
text-domaine-agenda px-2 py-0.5 rounded-sm` (plus de magenta
`bg-accent-magenta/20`).

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

Classe `absolute rounded-sm border-l-[3px] border-domaine-agenda
bg-domaine-agenda-tint text-domaine-agenda px-2 py-0.5 text-left overflow-hidden
focus-visible:outline focus-visible:outline-[3px] focus-visible:outline-offset-[-3px]
focus-visible:outline-ring` ; titre `text-sm font-semibold truncate` (le DOM
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

`Carte as="section"`, et **à l'intérieur** un `div` qui porte la grille :
`<div className="grid grid-cols-7">`, **7 en-têtes** puis **42 cases**
(49 enfants), lundi d'abord, sans `gap`. La grille est un `div` **enfant** de
la `Carte`, jamais la `Carte` elle-même : `semaineFrancaise.test.tsx:53`
sélectionne `container.querySelectorAll('div.grid-cols-7')`, et une `section`
ne répond pas à ce sélecteur. Ce `div` ne reprend **ni** `rounded-md` **ni**
`border border-border` : `Carte.tsx:20` les pose déjà, les redoubler dessine
deux traits. **Pas** `overflow-hidden` sur ce conteneur (la maquette
`.mois{overflow:hidden}`, `agenda.html:26`, collée ici couperait l'anneau
du socle `:focus-visible{outline:3px solid;outline-offset:2px}`,
`docs/da/2026-09-05-propositions/maquettes/da/base.css:23` : 3 px + offset
2 px = 5 px hors boîte ; la semaine évite déjà ce clip § 3). En-têtes :
nœuds séparés `text-sm text-text-muted`, texte
entier `lun.` … `dim.` (maquette `.jt`, `agenda.html:85` ; la regex
d'`etiquettesJours` lit le texte entier) ; ces en-têtes portent `border-b
border-border` et **aucun** `border-l`. Cellules `min-h-[5.5rem] p-1.5
border-t border-l border-border text-sm` plus `[&:nth-child(7n+1)]:border-l-0` :
les sept en-têtes occupent les enfants 1 à 7 et les 42 cases les enfants 8 à
49, donc `7n+1` retombe exactement sur la première case de chaque rangée (8,
15, 22, 29, 36, 43), comme la maquette `.mois .case:nth-child(7n+1)
{border-left:0}` (`agenda.html:28`) ; sans cette exception, le trait de la
première case double la bordure gauche de la `Carte`. Aucun conteneur
intermédiaire autour des en-têtes ni des cases : un `display:contents`
casserait le décompte de 49 enfants du test (§ 9). Hors mois : numéro
`text-text-muted` sans opacité sur la case (B-414), **littéral conservé tel
quel**, § 9 ; aujourd'hui : numéro
`h-[1.4rem] w-[1.4rem] rounded-full bg-accent-fill text-accent-ink grid
place-items-center`. Puces : bouton `text-sm truncate border-l-2
border-domaine-agenda bg-domaine-agenda-tint text-domaine-agenda px-1.5 py-0.5
rounded-sm` + anneau du socle (défaut, pas rentrant : plus de parent qui
clippe). « +N autre » / « +N autres » inchangé,
`text-xs` (non cliquable).

Le test actuel compte deux `div.grid-cols-7` et 42 enfants de la seconde
(`semaineFrancaise.test.tsx:53-56`). Une seule grille maquette : aligner
ce décompte (7 en-têtes + 42 cases), § 9.

## 5. Jour et liste

Jour : mêmes jetons et `text-sm` sur les blocs horaires ; `DAY_SLOT_HEIGHT_PX`
et bornes 6-22 inchangés (marqueur B-238 : `06:00`). **Garder** les
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
px-4 py-3 border-t border-border hover:bg-surface-2">` (mêmes colonnes que
`Ligne`) ; puce `aria-hidden` `h-8 w-8 rounded-sm bg-domaine-agenda-tint
text-domaine-agenda` ; titre `font-semibold text-text` = `summary` ; si
`location`, `p className="text-sm text-text-muted"` = lieu ; droite
`text-text-muted` = `event.all_day ? 'Toute la journée' :
formatTime(event.start_datetime!)`. Nom accessible = concaténation des nœuds
texte (résumé, lieu s'il existe, horaire). Chaîne exacte `Toute la journée`
(pas « toute la journée »). Vide : `EtatVide
titre="Aucun événement"`, sans action. Groupes par jour : `h3 text-sm
font-semibold`, `parseLocalDateKey` conservé, tri descendant
`b.localeCompare(a)` inchangé (`CalendarView.tsx:101`).

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
vient de `FormField required`, pas du texte du label. Case à cocher **hors**
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

Calendrier affiché : `FormField htmlFor="eventform-agenda" label="Agenda"`
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
chargement) : `text-xs font-medium text-text-muted mt-2`. Résumé = calendrier
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
sélecteur `aria-label="Calendrier affiché"` est un `Select`, liste vide
sans bouton créer ; (6) aucune classe `text-xs` dans le sous-arbre d'un
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
`text-agent-amber`). Elle est rouge aujourd'hui, et voici les lignes qu'elle
doit faire tomber : `CalendarPanel.tsx:445`, `532`, `534`, `542`, `572`, `608` ;
`CalendarView.tsx:114`, `257`, `407`, `413`, `441`, `509`, `522`, `644`, `647`,
`750` ; `EventForm.tsx:307`. Aucune n'est laissée sans destination : le
sélecteur de vue et le `RefreshCw` disparaissent (§ 2, § 8), les blocs et les
puces passent en `domaine-agenda` (§ 3, § 4, § 5), les numéros et encres
d'accent passent en `text-accent` (§ 3), la case à cocher et le suffixe
« (aujourd'hui) » sont traités § 6 et § 5. `bg-instant` et `text-instant`
restent permis, ce sont les jetons du repère ; (7) overlay : plus de
`bg-black` ; (8) groupe Segments + « Nouveau rendez-vous » porte `ml-auto` ;
(9) pied : **aucun pied rendu** quand `calendars: []` et
`currentCalendarId: null` (l'état monté par
`src/frontend/src/components/calendar/CalendarPanel.nomsAccessibles.test.tsx:52`),
donc ni résumé ni suffixe sur une liste vide ; suffixe « aucun agenda en ligne
branché » absent si un `provider === 'caldav'` (présent seulement si au moins
un agenda existe et que tous sont `local`) ; (10) chargement : chaque rangée = deux `Squelette` (`w-8` puis
`w-[60%]`), pas un seul.

`CalendarView.da.test.tsx` : (1) semaine : 7 colonnes, « lun. » … « dim. »,
ligne `bg-instant` avec `role="img"` et `aria-label` `/Il est/` **seulement
si `nowLineTop !== null`** (même garde que `CalendarView.tsx:379-382` : pas
dès que aujourd'hui est dans la semaine) ; en-tête, rangée « Journée » et
piste horaire partagent `grid-cols-[3.5rem_repeat(7,1fr)]` (pas de `w-16`
sur « Journée ») ; (2) un bloc = un `button`, titre
en `text-sm`, résumé entier dans le nom accessible (chaîne non coupée) ;
horaire `HH:MM à HH:MM` **en semaine et en jour** ; Jour : lieu sur la
même ligne s'il existe (pas de garde `height > 50`) ; aucun `capitalize`
sur le `h3` interne Jour ; (3) deux rendez-vous au même créneau : **asserter
le `style` des deux boutons** (`left: '0%'` et `left: '50%'`, `width`
correspondant), pas seulement `leftPercent` du helper ; (4) mois : 7
en-têtes `lun.`…`dim.` + 42 cellules, première = lundi, aujourd'hui en
`bg-accent-fill` ; la grille mois n'a **pas** `overflow-hidden` ; (5) liste :
un `<button>` par événement dont le nom accessible **contient** le résumé
et l'horaire (ou « Toute la journée ») ; droite visuelle « Toute la journée »
pour un `all_day` ; vide = `EtatVide` « Aucun événement ».

`EventForm.da.test.tsx` : ids des champs encore là, chaque `FormField`
porte `htmlFor` égal à l'id, `FormField` « Lieu ou visio », case « toute
la journée » **hors** `FormField` (`getByLabelText('Événement sur toute la
journée')` via `htmlFor="all-day"`), Enregistrer
toujours `md`, titre « Nouveau rendez-vous » hors édition, agenda affiché
`readOnly` + `aria-readonly="true"` (pas `disabled`), une seule
`role="alert"` pour `formError || guardError` (les deux sources, un bandeau).

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
`grilles.length === 2` ; une seule `grid-cols-7`, 7 en-têtes + 42 cases
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

**Ce qu'il ajoute à l'écran**, et c'est le seul élément nouveau : le champ
« Agenda » en lecture seule du formulaire (`FormField` + `Input readOnly
aria-readonly`, § 6 ; maquette `agenda.html:101`). Il rend visible la
destination de l'enregistrement, qui n'apparaissait jusqu'ici que dans la
confirmation externe (`EventForm.tsx:154`, `162-163`). Il ne touche ni les
données, ni le store, ni la destination : c'est de l'affichage, et il se teste
(§ 9, `EventForm.da.test.tsx`). Le reste de ce paragraphe énumère ce qui
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
   1280, 1024, 840, 800 px ; clair, sombre, contraste élevé ; trois tailles
   de police. Captures `.cartography-work/validation/da-lot8/`, rapport
   `docs/da/2026-09-11-lot8-recette.md`. Vérifier : sept colonnes, ligne de
   l'heure (sur les sept colonnes de jour, jamais dans la gouttière des
   heures), titre entier au focus, un seul « Réessayer », BUG-143 (pas de
   création d'agenda, et **aucun pied** quand la liste d'agendas est vide),
   établi visible, anneau 3 px sur un bloc et un segment, rangée « Journée »
   si un `all_day`, libellé de semaine à cheval sur deux mois, bordure gauche
   du mois sur un seul trait, et horaire encore lisible sur un rendez-vous de
   45 minutes en semaine comme en jour.
4. Revue adverse du diff avant le tag, `/release-therese 0.72.0-alpha` avec
   le GO de Ludo (toute la DA, pas ce lot seul). L'arbitrage de la décision 5
   se rend **avant le code**, pas avant le tag : coder la branche
   « remplacement conservé » décrite ici, c'est la choisir de fait.

## Points non repris

Aucun constat de la v3 n'est écarté, et la vérification a porté sur les
fichiers cités, pas sur le libellé du constat. Les 10 constats du journal
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
