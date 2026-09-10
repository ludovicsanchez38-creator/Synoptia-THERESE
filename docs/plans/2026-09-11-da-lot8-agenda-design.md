# DA « Application affinée », lot 8 : l'écran Agenda (design à challenger avant le code)

Version 1, 11/09/2026. Précédent : lot 3 (Tiroir), sur `main` ; cadence : une
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
en consommant les primitives du lot 1 (`Carte`, `Segments`, `Alerte`,
`EtatVide`, `Squelette`, `Ligne`, `Etiquette`, `Button`, `Input`, `Select`,
`Textarea`, `FormField`) ; les mêmes données, les mêmes états, les mêmes
destinations. Aucun appel réseau, aucun store, aucun parcours ne change.

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
5. Création : le formulaire **remplace** encore la grille (cascade actuelle).
   Le panneau latéral 26 rem, grille visible, est une fonctionnalité (P-071).
6. Toute taille de bouton est `md` (36 px) ou `icon` (36 px) ; `sm` n'y est
   pas employé. « Nouveau rendez-vous » est le grand geste, en `lg`.
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
| Titre | `<p className="text-lg font-semibold">Agenda</p>` | inchangé (B-241) ; meta email `text-sm text-text-muted` conservée |
| Nav | `Button ghost sm`, `aria-label` « Période précédente/suivante » | `Button variant="secondary" size="icon"` (mêmes `aria-label` et `title`) ; « Aujourd'hui » `Button variant="secondary" size="md"` |
| Période | `<h3 className="capitalize">` + `getNavLabel()` | `<h3 id="agenda-periode" className="text-base font-semibold">` ; jour : `toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })` puis première lettre seule en capitale (lot 2, jamais `capitalize`) ; semaine : « Semaine du » + jour du lundi (`1` → « 1er ») + « au » + jour du dimanche + mois long + année (mêmes bornes lundi-dimanche) ; mois/liste : mois long + année, première lettre seule en capitale |
| Sélecteur | `<select aria-label="Calendrier affiché">` maison, `Z_LAYER.ONBOARDING` | `Select` même `aria-label`, `options={calendars.map(c => ({ value: c.id, label: c.summary }))}`, `value={currentCalendarId \|\| ''}`, même `onChange` ; wrapper `relative` + z-index conservé (BUG-049) ; liste vide : aucune option, pas de bouton « créer » (BUG-143) |
| Sync / ICS | `Button ghost sm` | `Button variant="ghost" size="icon"` ; `aria-label` / `title` conservés (« Synchroniser l'agenda », « Importer un fichier .ics », « Exporter en .ics ») ; `input.hidden` inchangé |
| Fermer (overlay) | `<button>` sans nom | `Button variant="ghost" size="icon"` `aria-label="Fermer l'agenda"` (absent en `standalone`) |

`data-testid="calendar-panel"` conservé sur les deux racines.

## 2. Segments et geste principal

Ordre visuel de la maquette, ids du store : Jour `day`, Semaine `week`,
Mois `month`, Liste `list`. `Segments label="Vue de l'agenda" valeur={viewMode}
onChange={(id) => choisirVue(id as …)}` (groupe + `aria-pressed`, pas un
`tablist`). Pas `sm` : `classeSegment` est déjà `text-sm`. Geste :
`Button variant="primary" size="lg"` icône `Plus` 18 px, libellé « Nouveau
rendez-vous », `onClick={handleNewEvent}`.

## 3. Grille semaine (`CalendarView` `WeekView`)

`Carte as="section" aria-label={période}`. Grille
`grid-cols-[3.5rem_repeat(7,1fr)]` (gutter `3.5rem` de la maquette, **7**
colonnes). En-tête : `text-sm text-text-muted` « lun. » … « dim. » + numéro
`text-base font-semibold tabular-nums` ; aujourd'hui : numéro `text-accent`,
colonne `bg-accent-tint`. Heures : `text-xs tabular-nums text-text-muted`
(non interactif, plancher 12 px). Pas de `bg-accent-cyan/5`.

Blocs horaires : `absolute`, `getTimedEventLayout` inchangé (côte à côte =
chevauchement lisible), `HOUR_HEIGHT_PX = 48` (3 rem). Classe
`left-1 right-1 rounded-sm border-l-[3px] border-domaine-agenda
bg-domaine-agenda-tint text-domaine-agenda px-2 py-1 text-left overflow-hidden
focus-visible:outline focus-visible:outline-[3px] focus-visible:outline-offset-[-3px]
focus-visible:outline-ring` ; titre `text-sm font-semibold truncate` (le DOM
garde le résumé entier) ; horaire `text-sm` ; lieu si présent, même ligne.
Journée entière : mêmes jetons (plus de magenta). Ligne de l'heure : `bg-instant`
conservé (repère, pas une erreur), `aria-label={`Il est ${HH}:${MM}`}` sur la
semaine (le jour affiche déjà l'heure). `whileHover` / `scale` retirés.

## 4. Grille mois (`MonthView`)

`Carte as="section"`. Une grille `grid-cols-7` sans `gap`,
`overflow-hidden rounded-md` ; cellules `min-h-[5.5rem] p-1.5 border-t border-l
border-border text-sm` ; hors mois : numéro `text-text-muted` sans opacité
sur la case (B-414) ; aujourd'hui : numéro `h-[1.4rem] w-[1.4rem] rounded-full
bg-accent-fill text-accent-ink grid place-items-center`. Puces : bouton
`text-sm truncate border-l-2 border-domaine-agenda bg-domaine-agenda-tint
text-domaine-agenda px-1.5 py-0.5 rounded-sm` + anneau du socle. « +N autre »
/ « +N autres » inchangé, `text-xs` (non cliquable). 42 cellules, lundi d'abord.

## 5. Jour et liste

Jour : mêmes jetons et `text-sm` sur les blocs ; `DAY_SLOT_HEIGHT_PX` et
bornes 6-22 inchangés (marqueur B-238 : `06:00`). Liste : plus de
`motion.button` ni `scale` ; chaque rendez-vous = `Ligne domaine="agenda"
titre={summary} detail={lieu} droite={toute la journée \| HH:MM} onClick=…`.
Vide : `EtatVide titre="Aucun événement"`, sans action. Groupes par jour :
`h3 text-sm font-semibold`, `parseLocalDateKey` conservé.

## 6. Formulaire (`EventForm`, état `nouveau`)

Toujours le remplaçant de la grille (P-071 au portail). Tête : retour
`Button ghost icon` `aria-label="Retour"` (B-578) ; titre `h3`
« Nouveau rendez-vous » / « Modifier l'événement » ; `Button primary md`
« Enregistrer » (spinner inchangé). Corps : `FormField` + `Input` / `Textarea`
(`error` si `formError` concerne le champ). Ids conservés (`eventform-titre`,
`eventform-date-de-debut`, `eventform-heure-de-debut`, `eventform-date-de-fin`,
`eventform-heure-de-fin`, `eventform-lieu`, `eventform-description`,
`eventform-participants`, `all-day`). Libellés : « Titre » `required` ;
« Événement sur toute la journée » ; dates et heures de début/fin ; « Lieu ou
visio » placeholder « Atelier, adresse ou lien » ; « Description » ;
« Participants » + aide actuelle « Séparez les emails par des virgules ».
Placeholder titre « Titre de l'événement » conservé (test). Erreur :
`Alerte data-testid` absent aujourd'hui, `role="alert"` déjà là, `children` =
`error`, sans `action`. Grille `grid-cols-2 max-[1023px]:grid-cols-1`.
Calendrier affiché en `FormField` lecture seule (`Input disabled`, valeur =
`selectedCalendar?.summary`), pas un second sélecteur. Confirmation externe
et `confirm('Abandonner les modifications ?')` inchangés.

## 7. Fiche (`EventDetail`)

Pas d'état maquetté. Titre **`h3`** conservé (B-238 le reconnaît). Statut
`Etiquette ton={tentative ? 'attention' : 'erreur'}` « Provisoire » /
« Annulé ». Confirmation de suppression : `div` (pas `Alerte` : ce n'est pas
une erreur, lot 3) + `Button ghost md` « Conserver le rendez-vous » +
`Button danger md` « Supprimer définitivement » ; textes inchangés. Modifier /
Supprimer : `Button ghost icon`, `aria-label` conservés. Horaires, lieu,
participants (pluriel `1 participant` / `N participants`), récurrence,
description : `text-sm`, icônes 18 px `text-accent`.

## 8. Les états (priorité = cascade actuelle, `CalendarPanel.tsx:569-580`)

| État | Aujourd'hui | Cible |
|---|---|---|
| chargement | icône `RefreshCw` qui tourne | trois rangées `aria-hidden` façon semaine (gutter `Squelette classeBarre="h-8 rounded-sm" largeur="w-8"` + barre `w-[60%]`) puis `role="status"` « Chargement de l'agenda… » `text-sm text-text-muted` |
| `isEventFormOpen` | `EventForm` | § 6 |
| `currentEventId` | `EventDetail` | § 7 |
| sinon | `CalendarView` | § 3-5 |
| cache périmé (`staleWarning`) | `<p role="status" className="text-xs text-warning" data-testid="calendar-stale-warning">` « Dernier rafraîchissement échoué : données conservées… » | `Alerte data-testid="calendar-stale-warning"` (la primitive impose `role="alert"`, test lot 2 : un `role` appelant ne l'écrase pas ; la maquette aussi) titre « L'agenda est affiché tel qu'il était. » `children` = texte actuel (un seul horodatage `lastSyncAt`, on n'invente pas 11:20 / 11:50) `icone={AlertTriangle 18 px}` `action` = `Button ghost md` Réessayer → `handleSync` ; enveloppe `px-4 pt-3` |
| erreur totale (`error && !needsReauth`) | bandeau `bg-error/10` | `Alerte` titre absent, `children` = `error` (403 actionnable conservé, #124), `icone={AlertCircle 18 px}` `action` = `Button secondary md` Réessayer → `handleSync` ; un seul « Réessayer » : stale et erreur totale s'excluent (`classifyCalendarError`) |
| reauth | bandeau ambre + « Reconnecter » | hors `Alerte` (pas une erreur de lecture) ; `px-4 py-3 border-b border-border bg-[var(--color-warning-tint)]` texte actuel, `Button ghost md` « Reconnecter » / « En attente... » + `Spinner` ; `bg-agent-amber` retiré |
| overlay | `bg-black/60` | `bg-bg/80` (plus de `black`) |

Un seul « Réessayer » par état : 1 sur stale, 1 sur erreur totale, 0 sur
chargement, grilles, formulaire, fiche, reauth, vide liste.

Pied sous la grille (prêt seulement) : `text-xs font-medium text-text-muted
mt-2` « Agenda local « {summary} » » si `provider === 'local'`, sinon
`summary` ; suffixe « · aucun agenda en ligne branché » si aucun calendrier
`provider === 'google'`. Pas de légende Rendez-vous / Prospects / Tâches
(P-072).

## 9. Gardes mécaniques et tests à aligner

Nouveaux, rouges d'abord :

`CalendarPanel.da.test.tsx` : (1) `data-testid="calendar-panel"` et
`calendar-stale-warning` encore là ; (2) `Segments` nommé « Vue de l'agenda »,
quatre `aria-pressed`, clic « Semaine » appelle `setViewMode('week')` et
`setCurrentEvent(null)` ; (3) « Nouveau rendez-vous » `size` visuel `h-11`,
clic pose `isEventFormOpen` ; (4) un seul « Réessayer » sur stale (appelle
`handleSync`) et sur erreur totale, zéro sur grille saine, reauth, chargement ;
(5) sélecteur `aria-label="Calendrier affiché"` est un `Select`, liste vide
sans bouton créer ; (6) aucune classe `text-xs` dans le sous-arbre d'un
interactif, aucune couleur en dur dans les quatre fichiers (étendre
`aucuneCouleurEnDur` : `CalendarPanel.tsx`, `CalendarView.tsx`, `EventForm.tsx`,
`EventDetail.tsx` ; `bg-instant` est un jeton) ; (7) overlay : plus de
`bg-black`.

`CalendarView.da.test.tsx` : (1) semaine : 7 colonnes, « lun. » … « dim. »,
ligne `bg-instant` avec `aria-label` `/Il est/` quand aujourd'hui est dans la
semaine ; (2) un bloc = un `button`, titre en `text-sm`, résumé entier dans
le nom accessible (chaîne non coupée) ; (3) deux rendez-vous au même créneau
gardent `leftPercent` 0 et 50 (layout) ; (4) mois : 42 cellules, première =
lundi, aujourd'hui en `bg-accent-fill` ; (5) liste : une `Ligne` par
événement, vide = `EtatVide` « Aucun événement ».

`EventForm.da.test.tsx` : ids des champs encore là, `FormField` « Lieu ou
visio », Enregistrer toujours `md`, titre « Nouveau rendez-vous » hors
édition.

`EventDetail.da.test.tsx` : titre `h3`, confirmation sans `role="alert"`,
boutons `md` / `icon`.

À aligner, forme seulement : `CalendarView.semaineFrancaise.test.tsx`
`['Lun','Mar','Mer','Jeu','Ven','Sam','Dim']` → `['lun.','mar.','mer.','jeu.','ven.','sam.','dim.']`
(regex d'`etiquettesJours` idem) ; `CalendarPanel.retourGrille.test.tsx`
marqueur Mois/Semaine `'Mer'` → `'mer.'`, Liste `heading level 4` →
`getByRole('button', { name: RESUME })` (`Ligne`) ; `EventForm.test.tsx`
placeholder titre **inchangé**. Aucune assertion de comportement n'est
retirée. `parcours-07` clique « Nouvel événement » sur
`MeetingConversationCard` : hors lot.

## 10. Ce que ce lot ne fait pas

- Panneau latéral 26 rem, grille encore visible pendant la saisie (`.panneau`).
  Aujourd'hui le formulaire remplace le contenu ; le superposer changerait les
  cibles de clic. Fonctionnalité : **P-071** (numéro à confirmer par
  l'orchestrateur).
- Tâches et prospects dessinés sur la grille, légende de domaines, pastille
  « à préparer ». L'API ne livre que des `CalendarEvent`. **P-072**.
- Champ « Avec » qui résout un contact et propose de le créer s'il est
  absent ; plage « 10:00 à 11:00 » en un champ. Aujourd'hui : e-mails et
  quatre champs d'horaire. **P-073**.
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
   reauth ; chargement lent ; ouverture « Nouveau rendez-vous »). Largeurs
   1280, 1024, 840, 800 px ; clair, sombre, contraste élevé ; trois tailles
   de police. Captures `.cartography-work/validation/da-lot8/`, rapport
   `docs/da/2026-09-11-lot8-recette.md`. Vérifier : sept colonnes, ligne de
   l'heure, titre entier au focus, un seul « Réessayer », BUG-143 (pas de
   création d'agenda), établi visible, anneau 3 px sur un bloc et un segment.
4. Revue Grok du diff avant le tag, `/release-therese 0.72.0-alpha` avec le
   GO de Ludo (toute la DA, pas ce lot seul).
