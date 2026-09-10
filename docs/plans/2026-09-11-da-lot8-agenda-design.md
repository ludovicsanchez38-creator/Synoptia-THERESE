# DA « Application affinée », lot 8 : l'écran Agenda (design à challenger avant le code)

Version 2, 11/09/2026 00:37, après la revue de la v1 (19 points repris, 0 non repris) ; journal `.cartography-work/reviews/grok-da-lot8-agenda-design-v1.log`. Précédent : lot 3 (Tiroir), sur `main` ; cadence : une
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
lot 1 (`Carte`, `Segments`, `Alerte`, `EtatVide`, `Squelette`, `Ligne`,
`Etiquette`, `Button`, `Input`, `Select`, `Textarea`, `FormField`) ; les
mêmes données, les mêmes états, les mêmes destinations. L'état maquetté
`nouveau` (`.panneau` 26 rem, grille encore visible, `agenda.html:36-38` et
`ecrans.json:123` « création sans modale imbriquée ») **n'est pas l'écran
livré** : le formulaire remplace encore la grille (décision 5). Aucun appel
réseau, aucun store, aucun parcours ne change (à condition que Ludo
donne un GO explicite sur ce remplacement ; sinon le panneau entre dans le
lot et cette phrase devient fausse).

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
   cibles de clic. **Ludo tranche avant le code** : soit un GO explicite sur
   ce remplacement pour `nouveau`, soit le panneau entre dans le lot et
   « aucun parcours ne change » est faux. Ce n'est pas un numéro de portail
   (P-071) qui escamote un état déjà dessiné.
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

Ordre visuel de la maquette, ids du store : Jour `day`, Semaine `week`,
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
**7** colonnes). En-tête : **deux nœuds distincts** par jour (comme
aujourd'hui, pas collés « mar.1 » comme `agenda.html:75`) : un `div` dont
le texte entier est `lun.` … `dim.` (`text-sm text-text-muted`) + un nœud
numéro `text-base font-semibold tabular-nums` ; aujourd'hui : numéro
`text-accent`, colonne `bg-accent-tint`. Heures : `text-xs tabular-nums
text-text-muted` (non interactif, plancher 12 px). Pas de `bg-accent-cyan/5`.

Rangée « Journée » **conservée** au-dessus de la grille horaire
(`CalendarView.tsx:423-450`). `getTimedEventLayout` exige
`start_datetime` / `end_datetime` et retourne `null` sans eux
(`calendarEventLayout.ts:90-92`) : un `all_day` n'a pas de `top` dans la
grille horaire. Filtre `allDayByDate` inchangé. Libellé gutter
`text-sm text-text-muted` « Journée » (plus `text-xs`). Jetons : `<button>`
`text-sm truncate border-l-[3px] border-domaine-agenda bg-domaine-agenda-tint
text-domaine-agenda px-2 py-0.5 rounded-sm` (plus de magenta
`bg-accent-magenta/20`).

Blocs horaires : `absolute`, `getTimedEventLayout` inchangé (côte à côte =
chevauchement lisible), `HOUR_HEIGHT_PX = 48` (3 rem). **Pas** `left-1
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
bg-domaine-agenda-tint text-domaine-agenda px-2 py-1 text-left overflow-hidden
focus-visible:outline focus-visible:outline-[3px] focus-visible:outline-offset-[-3px]
focus-visible:outline-ring` ; titre `text-sm font-semibold truncate` (le DOM
garde le résumé entier) ; horaire `text-sm`, **début et fin conservés**,
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

`Carte as="section"`. Une seule grille `grid-cols-7` sans `gap`,
`overflow-hidden rounded-md` : **7 en-têtes** puis **42 cases** (49 enfants),
lundi d'abord. En-têtes : nœuds séparés `text-sm text-text-muted`, texte
entier `lun.` … `dim.` (maquette `.jt`, `agenda.html:85` ; la regex
d'`etiquettesJours` lit le texte entier). Cellules `min-h-[5.5rem] p-1.5
border-t border-l border-border text-sm` ; hors mois : numéro
`text-text-muted` sans opacité sur la case (B-414) ; aujourd'hui : numéro
`h-[1.4rem] w-[1.4rem] rounded-full bg-accent-fill text-accent-ink grid
place-items-center`. Puces : bouton `text-sm truncate border-l-2
border-domaine-agenda bg-domaine-agenda-tint text-domaine-agenda px-1.5 py-0.5
rounded-sm` + anneau du socle. « +N autre » / « +N autres » inchangé,
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
la grille Jour. Rangée « Toute la journée » **conservée** au-dessus de la
grille (`CalendarView.tsx:652-668`), mêmes jetons `domaine-agenda` que la
semaine, filtre `allDayEvents` inchangé, libellé gutter `text-sm
text-text-muted` « Toute la journée ».

Liste : plus de `motion.button` ni `scale` ; chaque rendez-vous = `Ligne
domaine="agenda" titre={summary} detail={lieu} droite={event.all_day ?
'Toute la journée' : formatTime(event.start_datetime!)} onClick=…`. Chaîne
exacte `Toute la journée` (pas « toute la journée »). Vide : `EtatVide
titre="Aucun événement"`, sans action. Groupes par jour : `h3 text-sm
font-semibold`, `parseLocalDateKey` conservé, tri descendant
`b.localeCompare(a)` inchangé (`CalendarView.tsx:101`).

Fiche : garder « Événement introuvable » si `event` est nul
(`EventDetail.tsx:74-78`).

## 6. Formulaire (`EventForm`, état `nouveau`)

Toujours le remplaçant de la grille (décision 5 ; Ludo GO sur cet écart
avant le code). Tête : retour `Button ghost icon` `aria-label="Retour"`
(B-578) ; titre `h3` « Nouveau rendez-vous » / « Modifier l'événement » ;
`Button primary md` « Enregistrer » (spinner inchangé). Corps : `FormField`
+ `Input` / `Textarea`. **`htmlFor` = l'id déjà listé** pour chaque champ
(`FormField` n'associe le `<label>` que via `htmlFor`,
`FormField.tsx:53-55` ; sans lui `getByLabelText` casse) :

| Champ | `label` | `htmlFor` / `id` | `required` |
|---|---|---|---|
| Titre | Titre | `eventform-titre` | oui |
| Toute la journée | Événement sur toute la journée | `all-day` | non |
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
(la maquette fusionne en « Date » / « Heure » = P-073, hors lot). L'astérisque
vient de `FormField required`, pas du texte du label. Case à cocher : garder
`htmlFor="all-day"` ; le `<label>` reste **à côté** de la case (flex actuel),
pas au-dessus via le `label` de `FormField` si ça casse la rangée : l'association
`htmlFor` suffit à `getByLabelText('Événement sur toute la journée')`.
Participants : `description="Séparez les emails par des virgules"` (aide
actuelle). Placeholder titre « Titre de l'événement » conservé (test).
Placeholder lieu « Atelier, adresse ou lien ».

Erreur : **une seule** `Alerte` (`children` = `error` / `formError`, sans
`action`, `data-testid` absent aujourd'hui). `FormField` ne reçoit **pas**
`error={formError}` : `FormField` rend `<p role="alert">`
(`FormField.tsx:72-76`) et un second « date de fin » ferait échouer
`EventForm.test.tsx:157` `findByText(/date de fin/)`. `FormField error`
seulement si le message est retiré du bandeau.

Calendrier affiché : `FormField htmlFor="eventform-agenda" label="Agenda"`
+ `Input id="eventform-agenda" readOnly aria-readonly="true"`
`value={selectedCalendar?.summary}` (**pas** `disabled` : `Input` pose
`disabled:opacity-50`, le champ sort de la tabulation, souvent non annoncé,
valeur non copiable ; la maquette `agenda.html:101` est un champ ordinaire).
Pas un second sélecteur. Confirmation externe et
`confirm('Abandonner les modifications ?')` inchangés. Grille
`grid-cols-2 max-[1023px]:grid-cols-1`.

## 7. Fiche (`EventDetail`)

Pas d'état maquetté. Titre **`h3`** conservé (B-238 le reconnaît). Si
`event` est nul : « Événement introuvable » (`EventDetail.tsx:74-78`),
inchangé. Statut `Etiquette ton={tentative ? 'attention' : 'erreur'}`
« Provisoire » / « Annulé ». Confirmation de suppression : `div` (pas
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

**Une seule branche d'affichage** entre stale et erreur totale :
`error && !needsReauth` (erreur agendas, #124) **prioritaire**, sinon
`staleWarning`. Ils ne s'excluent **pas** tout seuls via
`classifyCalendarError` : `loadCalendars` peut laisser `error` (403) ;
`loadEvents` avec `hasCache` pose `staleWarning` et `error: null`
**sur son propre retour** (`calendarErrors.ts:68`) sans effacer l'erreur
agendas (`CalendarPanel.tsx:180-181` + `215-224`). Les deux bandeaux et
deux « Réessayer » peuvent donc coexister aujourd'hui. La branche d'affichage
ferme ce cas.

| État | Aujourd'hui | Cible |
|---|---|---|
| chargement | icône `RefreshCw` qui tourne | trois rangées `aria-hidden` façon semaine (gutter `Squelette classeBarre="h-8 rounded-sm" largeur="w-8"` + barre `w-[60%]`) puis `role="status"` « Chargement de l'agenda… » `text-sm text-text-muted` |
| `isEventFormOpen` | `EventForm` | § 6 |
| `currentEventId` | `EventDetail` | § 7 |
| sinon | `CalendarView` | § 3-5 |
| cache périmé (`staleWarning`) | `<p role="status" className="text-xs text-warning" data-testid="calendar-stale-warning">` « Dernier rafraîchissement échoué : données conservées… » sous le titre | `Alerte data-testid="calendar-stale-warning"` (la primitive impose `role="alert"`, test lot 2 : un `role` appelant ne l'écrase pas ; la maquette aussi) titre « L'agenda est affiché tel qu'il était. » `children` = texte actuel (un seul horodatage `lastSyncAt`, on n'invente pas 11:20 / 11:50) `icone={AlertTriangle 18 px}` `action` = `Button ghost md` Réessayer → `handleSync` ; enveloppe `px-4 pt-3` ; **hors du ternaire**, derrière la branche « pas d'erreur agendas » |
| erreur totale (`error && !needsReauth`) | bandeau `bg-error/10` au-dessus de la cascade | `Alerte` titre absent, `children` = `error` (403 actionnable conservé, #124), `icone={AlertCircle 18 px}` `action` = `Button secondary md` Réessayer → `handleSync` ; prioritaire sur stale |
| reauth | bandeau ambre + « Reconnecter » | hors `Alerte` (pas une erreur de lecture) ; `px-4 py-3 border-b border-border bg-[var(--color-warning-tint)]` texte actuel, `Button ghost md` « Reconnecter » / « En attente... » + `Spinner` ; `bg-agent-amber` retiré |
| overlay | `bg-black/60` | `bg-bg/80` (plus de `black`) |

Un seul « Réessayer » par état : 1 sur stale (quand la branche stale est
prise), 1 sur erreur totale (quand la branche agendas est prise), 0 sur
chargement, grilles, formulaire, fiche, reauth, vide liste. Jamais les deux
ensemble.

Pied sous la grille (prêt seulement, pas sur formulaire / fiche /
chargement) : `text-xs font-medium text-text-muted mt-2`. Résumé = calendrier
**courant** (`calendars.find(c => c.id === currentCalendarId)`) :
`Agenda local « {summary} »` si `courant.provider === 'local'`, sinon
`{summary}`. Suffixe ` · aucun agenda en ligne branché` si **aucun** des
`calendars` n'a `provider === 'google'` (`!calendars.some(c => c.provider
=== 'google')`), pas « le courant n'est pas google ». Pas de légende
Rendez-vous / Prospects / Tâches (P-072).

## 9. Gardes mécaniques et tests à aligner

Nouveaux, rouges d'abord :

`CalendarPanel.da.test.tsx` : (1) `data-testid="calendar-panel"` et
`calendar-stale-warning` encore là ; (2) `Segments` nommé « Vue de l'agenda »,
quatre `aria-pressed`, clic « Semaine » appelle `setViewMode('week')` et
`setCurrentEvent(null)` ; (3) « Nouveau rendez-vous » `size` visuel `h-11`,
clic pose `isEventFormOpen` ; (4) un seul « Réessayer » : branche unique
(erreur agendas #124 prioritaire, sinon stale) ; le cas 403 calendriers +
échec events avec cache n'affiche **que** l'Alerte 403 (pas
`calendar-stale-warning`, un seul « Réessayer ») ; stale seul appelle
`handleSync` ; zéro « Réessayer » sur grille saine, reauth, chargement ;
stale visible aussi formulaire / fiche ouverts (hors ternaire) ; (5)
sélecteur `aria-label="Calendrier affiché"` est un `Select`, liste vide
sans bouton créer ; (6) aucune classe `text-xs` dans le sous-arbre d'un
interactif, aucune couleur en dur dans les quatre fichiers (étendre
`aucuneCouleurEnDur` : `CalendarPanel.tsx`, `CalendarView.tsx`, `EventForm.tsx`,
`EventDetail.tsx` ; `bg-instant` est un jeton) ; (7) overlay : plus de
`bg-black`.

`CalendarView.da.test.tsx` : (1) semaine : 7 colonnes, « lun. » … « dim. »,
ligne `bg-instant` avec `role="img"` et `aria-label` `/Il est/` **seulement
si `nowLineTop !== null`** (même garde que `CalendarView.tsx:379-382` : pas
dès que aujourd'hui est dans la semaine) ; (2) un bloc = un `button`, titre
en `text-sm`, résumé entier dans le nom accessible (chaîne non coupée) ;
horaire `HH:MM à HH:MM` ; (3) deux rendez-vous au même créneau : **asserter
le `style` des deux boutons** (`left: '0%'` et `left: '50%'`, `width`
correspondant), pas seulement `leftPercent` du helper ; (4) mois : 7
en-têtes `lun.`…`dim.` + 42 cellules, première = lundi, aujourd'hui en
`bg-accent-fill` ; (5) liste : une `Ligne` par événement,
`droite` « Toute la journée » pour un `all_day`, vide = `EtatVide` « Aucun
événement ».

`EventForm.da.test.tsx` : ids des champs encore là, chaque `FormField`
porte `htmlFor` égal à l'id, `FormField` « Lieu ou visio », Enregistrer
toujours `md`, titre « Nouveau rendez-vous » hors édition, agenda affiché
`readOnly` + `aria-readonly="true"` (pas `disabled`), une seule
`role="alert"` pour `formError`.

`EventDetail.da.test.tsx` : titre `h3`, confirmation sans `role="alert"`,
boutons `md` / `icon`, « Événement introuvable » si id inconnu.

À aligner, forme seulement : `CalendarView.semaineFrancaise.test.tsx`
`['Lun','Mar','Mer','Jeu','Ven','Sam','Dim']` → `['lun.','mar.','mer.','jeu.','ven.','sam.','dim.']`
(regex d'`etiquettesJours` idem, ancrée sur le texte **entier** d'un `div`,
d'où les deux nœuds jour / numéro en semaine et les 7 en-têtes séparés en
mois) ; le test « première cellule » (`:50-62`) : ne plus exiger
`grilles.length === 2` ; une seule `grid-cols-7`, 7 en-têtes + 42 cases
(`enfants.length === 49`, `enfants.slice(7)` pour les numéros `['31','1','2']`) ;
`CalendarPanel.retourGrille.test.tsx` marqueur Mois/Semaine `'Mer'` → `'mer.'`,
Liste `heading level 4` → `getByRole('button', { name: RESUME })` (`Ligne`) ;
`EventForm.test.tsx` placeholder titre **inchangé**, `findByText(/date de
fin/)` **inchangé** (une seule occurrence : le bandeau) ; `getByLabelText(
'Événement sur toute la journée')` (`EventForm.test.tsx:138`) et
`getByLabelText(/Participants/i)` (`EventForm.agendaLocal.test.tsx:30`)
conservés par `htmlFor`. Aucune assertion de comportement n'est retirée.
`parcours-07` clique « Nouvel événement » sur `MeetingConversationCard` :
hors lot.

## 10. Ce que ce lot ne fait pas

- Panneau latéral 26 rem, grille encore visible pendant la saisie (`.panneau`,
  `agenda.html:36-38`). Aujourd'hui le formulaire remplace le contenu ; le
  superposer changerait les cibles de clic. **Écart déjà dessiné** (état
  maquetté `nouveau`, critère `ecrans.json:123`) : Ludo GO sur le remplacement
  actuel, ou le panneau entre dans le lot (décision 5). Le numéro P-071
  n'esquive pas cet état.
- Tâches et prospects dessinés sur la grille, légende de domaines, pastille
  « à préparer ». L'API ne livre que des `CalendarEvent`. **P-072**.
- Champ « Avec » qui résout un contact et propose de le créer s'il est
  absent ; plage « 10:00 à 11:00 » en un champ. Aujourd'hui : e-mails et
  quatre champs d'horaire (« Date de début », « Heure de début », « Date de
  fin », « Heure de fin »). **P-073**.
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
   403 calendriers **puis** échec events avec cache = un seul bandeau ;
   reauth ; chargement lent ; ouverture « Nouveau rendez-vous »). Largeurs
   1280, 1024, 840, 800 px ; clair, sombre, contraste élevé ; trois tailles
   de police. Captures `.cartography-work/validation/da-lot8/`, rapport
   `docs/da/2026-09-11-lot8-recette.md`. Vérifier : sept colonnes, ligne de
   l'heure, titre entier au focus, un seul « Réessayer », BUG-143 (pas de
   création d'agenda), établi visible, anneau 3 px sur un bloc et un segment,
   rangée « Journée » si un `all_day`, libellé de semaine à cheval sur deux
   mois.
4. Revue Grok du diff avant le tag, `/release-therese 0.72.0-alpha` avec le
   GO de Ludo (toute la DA, pas ce lot seul), y compris le GO sur le
   remplacement du formulaire (décision 5).

## Points non repris

Aucun. Les 19 constats du journal `.cartography-work/reviews/grok-da-lot8-agenda-design-v1.log` (1–19, VERDICT NO-GO) sont repris dans le corps.
