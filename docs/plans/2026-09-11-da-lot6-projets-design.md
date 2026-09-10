# DA « Application affinée », lot 6 : l'écran Projets et tâches (design à challenger avant le code)

Version 2, 11/09/2026 00:07, après la revue de la v1 (14 points repris, 0 non repris) ; journal `.cartography-work/reviews/grok-da-lot6-projets-design-v1.log`. Précédent : lot 3 (Tiroir), sur `main` ; cadence : une
seule release pour toute la DA (décision Ludo 11/09, 0.72.0-alpha porte
l'ensemble). Maquette :
`docs/da/2026-09-05-propositions/maquettes/projets.html` (états `normal`
Colonnes, `liste`, `nouvelle` titre manquant), critères de `ecrans.json` :
« Colonnes et liste, échéances civiles, une tâche se crée en trois secondes.
Liste, colonnes, changements d'état et échéances conservés ; trois secondes =
titre, échéance optionnelle, Entrée, depuis n'importe quel écran. » Déjà
décidé côté UX, pas à rejuger : P-001 contraste du bleu d'agent ; échéances
au jour civil (0.66.1, `isPastParisCivilDate`) ; état vide des tâches dessiné
(27/08, titre + sortie « Créer une tâche ») ; B-241 le titre accessible de
la région est celui de la coque, le libellé du panneau n'est plus un titre.

Deux vues distinctes dans `PrototypeUnifiedViewCanvas.tsx` : `tasks` monte
`TasksPanel standalone` (qui monte `TaskKanban` / `TaskList` / `TaskForm`) ;
`projects` monte `ProjectsPanel` (qui monte `ProjectsKanban` + `ProjectModal`).
La maquette en fait un seul écran : fusion, saisie rapide et cartes enrichies
sont des fonctionnalités (§ 10). Aucune primitive nouvelle : `CarteTete` n'est
pas montée (l'en-tête n'est pas une carte), `Ligne` non plus (décision 6).

## Ce que le lot change, en une phrase

Les six composants de ces deux vues prennent la forme de la maquette en
consommant les primitives du lot 1 (`Carte`, `Etiquette`, `Segments`,
`EtatVide`, `Alerte`, `Squelette`, `Button`, `Input`, `Select`, `Textarea`,
`FormField`) ; les mêmes données, les mêmes états, les mêmes destinations.
Aucun appel réseau, aucun store, aucun parcours ne change.

## Décisions tranchées par défaut (Ludo peut corriger)

1. **Deux vues restent deux vues.** `tasks` et `projects` ne fusionnent pas
   (P-071). Le libellé visible « Tâches » / « Projets » reste un `<p>`
   (B-241), pas un `h1`.
2. La création d'une tâche reste `TaskForm` qui **remplace** le corps (pas
   la saisie rapide au-dessus des colonnes, P-072). L'état `nouvelle` de la
   maquette habille ce formulaire.
3. `Segments` (groupe + `aria-pressed`) habille Colonnes / Liste ; ids
   inchangés (`kanban` / `list`). Libellés visibles : « Colonnes », « Liste ».
4. La formulation de la maquette remplace les mentions là où l'état est le
   même (erreur de titre). Un état sans équivalent maquetté garde ses mots
   (vide 27/08, troncature B-098, erreurs de chargement, colonnes vides).
5. Toute taille de bouton est `md` (36 px) ou `icon` (36 px) ; `sm` n'y est
   pas employé. « Nouvelle tâche » et « Nouveau projet » sont les gestes
   principaux, en `md` (le `.btn-primaire` de la maquette fait 2,25 rem),
   pas `lg`.
6. `Ligne` n'est pas montée : une case à cocher et une corbeille dans la
   puce seraient recouvertes par le `before:inset-0` du titre. Grille locale
   `grid-cols-[2.25rem_1fr_auto]` (colonne de la case = `Button size="icon"`
   `h-9 w-9`, `Button.tsx:35` ; 2 rem = 32 px recouvrirait le bouton 36 px.
   Décision 5 intacte). `ProjectModal` est une couche sans maquette : hors
   lot.
7. `whileHover` / `whileTap` de `scale` retirés (leçon du clipping sous le
   pointeur). Drag : listeners sur toute la carte, `activationConstraint`
   8 px, inchangés (BUG-041).
8. Anneau de focus : celui du socle (`:focus-visible` 3 px `outline-ring`)
   pour tout contrôle hors `Button` / `Input` / `Select` / `Textarea`, qui
   gardent l'anneau de leur primitive. Rien sous 12 px ; tout interactif à
   14 px au moins (les `Button` le sont par construction).
9. Pluriel, règle unique, déjà testée : tâche / tâches et projet / projets
   selon `n > 1` (0 et 1 au singulier). « 0 tâche », « 1 tâche », « 2
   tâches » ; « 0 projet », « 1 projet », « 2 projets », « 200+ projets ».

## 1. En-tête de `TasksPanel`

`data-testid="tasks-panel"` conservé (standalone et dialogue).

| Élément | Aujourd'hui | Cible |
|---|---|---|
| Pastille 2,5 rem `ListTodo` | `w-10 h-10` `border-[var(--btn-ink)]` | retirée (la maquette n'en a pas) |
| Libellé | `<p className="text-lg font-semibold">Tâches</p>` | inchangé en rôle ; `text-lg font-semibold text-text` |
| Compteur | `{n} tâche` / `{n} tâches` (B-210, `n > 1`) | **exactement** ces deux chaînes ; pas « ouvertes », pas de retard, pas de projets (P-073) |
| Vue | deux boutons icône, `aria-label` « Afficher les tâches en kanban / en liste », `title` Kanban / Liste | `Segments label="Vue des tâches"` options `{ id: 'kanban', label: 'Colonnes' }`, `{ id: 'list', label: 'Liste' }`, `valeur={viewMode}`, `onChange=setViewMode` |
| Filtrer | `Button ghost sm` icône, `aria-label="Filtrer les tâches"` | `Button variant="secondary" size="md"` texte visible « Filtrer », **même** `aria-label` et `aria-expanded` |
| Rafraîchir | `Button ghost sm` icône | `Button variant="ghost" size="icon"` `aria-label="Rafraîchir les tâches"` conservé, `RefreshCw` 18 px |
| Geste | `Button primary sm` « Nouvelle tâche » | `Button variant="primary" size="md"`, `Plus` 18 px, même `handleNewTask` |
| Fermer (hors standalone) | bouton maison, `aria-label="Fermer les tâches"` | `Button variant="ghost" size="icon"`, même nom |
| Rangée | `px-6 py-4 border-b border-border/30` | `flex flex-wrap items-end gap-3 px-4 pt-4 pb-2` ; actions `ml-auto flex flex-wrap gap-2 max-[840px]:basis-full max-[840px]:ml-0` |

## 2. Filtres (rangée dépliée, BUG-118)

Même règle d'apparition (`showFilters`), mêmes `aria-label`, mêmes options
(« Tous les statuts », « À faire » accentué B-616, « En cours », « Terminé »,
« Annulé » ; priorités Urgent / Haute / Moyenne / Basse ; projets ; tags).
Chaque `<select>` maison devient `Select` (`options` inclut `{ value: '',
label: '…' }`, pas `placeholder` : la valeur vide reste choisissable).
« Réinitialiser » : `Button variant="ghost" size="md"`, mêmes quatre
`set…(null)`, rendu seulement si l'un des quatre filtres est posé.
Projets et tags : le `Select` n'existe que si `projects.length > 0` /
`availableTags.length > 0`, comme aujourd'hui. Rangée :
`flex flex-wrap items-center gap-3 px-4 py-3 border-b border-border`.
Pas de ligne « Projet : tous · Échéance : toutes · Tri : échéance » (P-073).

Options exactes, dans cet ordre :

| Select `aria-label` | `options.value` / `label` |
|---|---|
| Filtrer par statut | `''` Tous les statuts, `todo` À faire, `in_progress` En cours, `done` Terminé, `cancelled` Annulé |
| Filtrer par priorité | `''` Toutes les priorités, `urgent` Urgent, `high` Haute, `medium` Moyenne, `low` Basse |
| Filtrer par projet | `''` Tous les projets, puis `p.id` / `p.name` |
| Filtrer par étiquette | `''` Tous les tags, puis le tag tel quel |

## 3. Colonnes : `TaskKanban`

Trois colonnes inchangées (`todo` / `in_progress` / `done`) ; `cancelled`
reste hors grille. `data-testid="task-item"` conservé, absent de l'overlay.

| Élément | Aujourd'hui | Cible |
|---|---|---|
| Grille | `flex gap-4 p-6 overflow-x-auto`, colonne `min-w-[300px]` | `grid grid-cols-3 max-[1023px]:grid-cols-2 max-[840px]:grid-cols-1 gap-3 p-4` ; colonne `bg-surface-2 rounded-md p-2 min-h-0` ; `isOver` : `bg-accent-tint` (plus de `bg-accent-cyan/5`) |
| Tête | icône + `h3 text-sm` + compte `text-xs` | `Etiquette` À faire `ton="neutre"` / En cours `ton="info"` / Terminé `ton="succes"` ; compte `ml-auto text-sm tabular-nums text-text-muted` ; plus d'icône, plus de `text-agent-*` |
| Vide de colonne | « Aucune tâche » | inchangé, `text-sm text-text-muted` |
| Carte | `bg-surface-elevated/60`, badge priorité `text-xs`, `whileHover scale` | `bg-surface border border-border rounded-sm p-3` ; plus de `scale` ; barre `w-1 h-[1.1rem] rounded-sm shrink-0` ; **quatre teintes distinctes**, pas de fusion urgent/high (aujourd'hui error / ambre / bleu / muted + le mot, `TaskKanban.tsx:312-317`) : `urgent` `bg-error` `aria-label="Priorité urgente"` ; `high` `bg-warning` `aria-label="Priorité haute"` ; `medium` `bg-info` `aria-label="Priorité moyenne"` ; `low` `bg-border` `aria-label="Priorité basse"` ; plus le mot « Urgent » / « Haute » / « Moyenne » / « Basse » |
| Retard | « En retard » `text-xs` + `AlertCircle` 12 px | `Etiquette ton="erreur"` « En retard » (pas « de N jours », P-073) |
| Titre | `h4 text-sm` | `font-semibold text-sm text-text` ; `done` : `line-through text-text-muted` (les deux vues) ; `maskTextFn(task.title)` conservé (`TaskKanban.tsx:368`) |
| Description | `text-sm line-clamp-2` | inchangée (corps, B-134) ; `maskTextFn(task.description)` conservé (`TaskKanban.tsx:372`) |
| Échéance | `toLocaleDateString` jour + mois court, `text-xs` | inchangée (pas « Aujourd'hui » ni `JJ/MM`, P-073) ; `text-xs font-medium text-text-muted` |
| Tags | `text-xs bg-accent-tint` | `Etiquette ton="neutre"` |
| Projet sur la carte | absent | reste absent (P-073) |
| Commandes | icônes 12 px, `title` seul, overlay `absolute top-2 right-2` (`TaskKanban.tsx:401-406`) | `Button variant="ghost" size="icon"` `aria-label` = les `title` actuels (« Marquer en cours », « Marquer terminé », « Rouvrir ») ; **rangée dans le flux** de la carte, après les tags : `flex items-center gap-1 mt-2`, `onClick` stoppe la propagation ; **pas** `absolute top-2 right-2` (trois `h-9 w-9` recouvriraient titre et barre) ; révélation focus + survol inchangée (B-209, `showActions && !isOverlay`) |
| « Ajouter une tâche » en pied de colonne | absent | reste absent (P-072) |

## 4. Liste : `TaskList`

Pas `Ligne` (décision 6). Conteneur `h-full overflow-y-auto` (plus `px-6
py-4`). Chaque `data-testid="task-item"` :

`grid grid-cols-[2.25rem_1fr_auto] gap-3 items-start px-4 py-3 border-t border-border hover:bg-surface-2 relative cursor-pointer` ; `onClick={() => handleTaskClick(task.id)}` **conservé** sur la rangée (aujourd'hui `TaskList.tsx:142` ; D105 : « la carte s'ouvre à la souris ») ; pas de `tabIndex` ni de `role="button"` sur la rangée (au clavier, c'est le titre). Plus de `scale`, plus d'`opacity-60` (le titre `done` se barre). Case à cocher : `Button variant="ghost" size="icon"` dans la colonne 2,25 rem, `relative z-10`, `onClick` stoppe la propagation, `aria-label` actuels conservés (`Marquer la tâche ${title} terminée` / `Rouvrir la tâche ${title}`), icônes `CheckCircle2` / `Circle` 18 px. Colonne `1fr` : `flex items-start gap-2` ; **même barre de priorité que le kanban** (`w-1 h-[1.1rem] rounded-sm shrink-0` + les quatre `aria-label` / teintes du § 3) à gauche du bloc titre (aujourd'hui le mot `getByText('Moyenne')`, `TaskList.tsx:187-196` ; la maquette pose `<div class="priorite haute">`, `projets.html:82` ; `droite` n'avait plus ni mot ni barre). Titre : `<button type="button" aria-label={`Ouvrir la tâche ${title}`}>` conservé (D105, tab stop), `onClick` stoppe la propagation puis `handleTaskClick`, `className="font-semibold text-left text-text"` + `line-through text-text-muted` si `done` ; contenu `{maskText(task.title)}` (`TaskList.tsx:177`). Description `text-sm text-text-muted line-clamp-1` inchangée ; contenu `{maskText(task.description)}` (`TaskList.tsx:206`). `droite` (`flex items-center gap-2 relative z-10`) : `Etiquette ton="erreur"` « En retard » si dû, échéance `text-xs font-medium text-text-muted` (liste : jour + mois court + année, format actuel), tags `Etiquette ton="neutre"`, corbeille `Button ghost icon` `aria-label={`Supprimer la tâche ${title}`}` (`onClick` stoppe la propagation). L'icône `Clock` 18 px `text-info` reste si `in_progress` (pas de détail
« · en cours » inventé, P-073). Confirmation en ligne : `div` (pas `Alerte` : ce n'est pas une erreur, aujourd'hui sans `role="alert"`), textes exacts « Supprimer « {maskText(task.title)} » ? » (`TaskList.tsx:262`), « Cette action est irréversible. », `Button ghost md` « Conserver la tâche », `Button danger md` « Supprimer définitivement » ; `onClick` stoppe la propagation, Échap via `pushEscapeHandler` inchangé.

Vide (27/08), deux titres : sans requête « Aucune tâche pour l'instant » /
« Note ce que tu ne veux pas oublier : Thérèse le gardera avec le reste de
ton contexte. » ; avec `searchQuery` « Aucune tâche ne correspond » /
`Rien ne correspond à « ${filtre} ». Essaie un autre mot, ou crée cette
tâche.` `EtatVide` + `action` = `Button variant="primary" size="md"`
« Créer une tâche » (`setCurrentTask(null)` + `setIsTaskFormOpen(true)`).

## 5. Formulaire : `TaskForm` (état `nouvelle`)

Remplace toujours le corps. En-tête : `Button ghost icon` `aria-label="Retour"` (le chevron n'avait pas de nom) + `<h3>` « Nouvelle tâche » / « Modifier la tâche » ; enregistrer `Button primary md`, libellé « Enregistrer » ou, si `saving`, `Spinner taille="bouton"` + « Enregistrement... » (points de suspension conservés). Champs dans l'ordre actuel, `FormField` + primitive, `htmlFor` conservés. Statut et Priorité restent côte à côte : un `div` `className="grid grid-cols-2 gap-4"` enveloppe les deux `FormField` (layout actuel, `TaskForm.tsx:193`), pas une table empilée.

| `htmlFor` | Label | Primitive | Notes |
|---|---|---|---|
| `taskform-titre` | Titre | `Input` | `FormField label="Titre" htmlFor="taskform-titre" required` : l'astérisque vient de `required && <span className="text-error ml-0.5" aria-hidden="true">*</span>` (`FormField.tsx:61`), pas de la chaîne « Titre * » ; `Input` `id="taskform-titre"` `required` `aria-required="true"` (B-621) `error={Boolean(erreurTitre)}` (`error?: boolean`, `Input.tsx:12,27` : bordure `border-error`, pas le texte) ; `placeholder="Titre de la tâche"` |
| `taskform-description` | Description | `Textarea` | `rows={4}`, placeholder actuel |
| `taskform-statut` | Statut | `Select` | À faire / En cours / Terminé / Annulé, mêmes `value` ; dans la grille 2 colonnes |
| `taskform-priorite` | Priorité | `Select` | Basse / Moyenne / Haute / Urgent, mêmes `value` ; dans la grille 2 colonnes |
| `taskform-date-limite` | Date limite | `Input type="date"` | |
| `taskform-tags` | Tags | `Input` | description FormField « Séparez les tags par des virgules » (plus `text-xs` hors primitive) |

Erreur titre : état distinct `erreurTitre` (pas le `error` du bandeau). `handleSave` si `!title.trim()` : `setErreurTitre("Ajoute un titre : c'est la seule chose obligatoire.")` puis `return` (aujourd'hui `setError('Ajoute un titre')`, `TaskForm.tsx:59-61`, un seul slot alimente le bandeau). **Ce cas ne monte pas `Alerte`** (réservée à la sauvegarde). `FormField error={erreurTitre}` pose le message, clone `aria-describedby="taskform-titre-error"` et `aria-invalid` sur l'enfant (`FormField.tsx:37-48`) ; le `<p id="taskform-titre-error" role="alert">` du `FormField` est le message de champ (maquette `.erreur-champ`), pas le bandeau. `Input error` booléen = bordure seulement. Au passage valide : `setErreurTitre(null)` avant l'appel. Les autres erreurs (`Échec de la sauvegarde`, `err.message`) : `Alerte` déjà `role="alert"`, `icone={<AlertCircle className="h-[18px] w-[18px]" />}`. `confirm('Abandonner les modifications ?')` inchangé. Champ projet commenté : inchangé (P-072). `#189` : l'effet de chargement reste branché sur `tacheChargeeRef`, pas sur l'identité de l'objet.

## 6. En-tête et corps de `ProjectsPanel`

Pas de `data-testid` racine aujourd'hui : on n'en invente pas. Pastille
`Briefcase` retirée. Libellé `<p className="text-lg font-semibold text-text">Projets</p>`
(B-241). Compteur `{n}{listeTronquee ? '+' : ''} projet{n > 1 ? 's' : ''}`
**exactement** : « 199 projets », jamais « 200 projets » (B-098). Troncature :
`role="alert"`, texte actuel « Liste incomplète : seuls les 200 premiers
projets sont affichés, d'autres existent. », `text-sm text-warning
px-4 py-2 bg-[var(--color-warning-tint)]` (pas `Alerte`, réservée à
l'erreur). Geste : `Button primary md` « Nouveau projet », `Plus` 18 px,
même `handleNew`. Wrapper du kanban : `<Carte as="section">` (prop `as?: 'article' | 'section'`, défaut `'article'`, `Carte.tsx:13-17` ; quatre groupes, pas une unité). `max-w-[760px]` retiré (la
colonne de la coque, 56 rem, suffit ; 72 rem de la maquette est P-071).
Dialogue de suppression : `role="dialog"` `aria-modal="true"`
`aria-labelledby="delete-project-title"` conservés, piège de focus et
`pushEscapeHandler` inchangés ; overlay `bg-text/50` (plus de `bg-black/50`) ;
boîte `bg-surface border border-border rounded-md p-5 shadow-lg` ; Annuler
`Button ghost md` `autoFocus` ; Supprimer `Button danger md`. Overlay du
dialogue Tâches (hors standalone) : même `bg-text/50` à la place de
`bg-black/60`. `therese:memory-changed` resynchronise toujours.

## 7. `ProjectsKanban`

Quatre groupes, libellés en casse de phrase (P-046) : Actif, En attente, Terminé, Annulé. Tête : `Etiquette` succes / attention / info / erreur + compte `text-sm tabular-nums text-text-muted` ; plus de `uppercase`, plus de `text-agent-*`. Vide de groupe : « Glisser ici ». Vide total : **un seul lieu, le panneau** (§ 8.3) ; `ProjectsKanban` n'est pas monté quand `projects.length === 0`. Filet si le kanban reçoit `[]` (tests isolés) : `EtatVide` titre « Aucun projet », sans action. Carte : `bg-surface border border-border rounded-sm`, plus de `scale` ; nom `text-sm font-semibold` ; description `text-sm text-text-muted` (plus `text-xs` sur ce texte, le plancher) ; budget inchangé ; supprimer `Button ghost icon` `aria-label={`Supprimer ${name}`}` conservé. Pas de barre de progression, pas de pièce, pas de séance (P-074).

## 8. Les états (priorité = ordre actuel)

Ordre du corps de `TasksPanel` (`TasksPanel.tsx`, le `tasksContent` actuel) :

| Priorité | Condition | Cible |
|---|---|---|
| 1 | `loading` et pas de cache | trois rangées `aria-hidden` façon carte, **chacune** `flex gap-3 items-center px-4 py-3 border-t border-border` contenant **trois** `Squelette` (la primitive est `flex flex-col gap-2`, `Squelette.tsx:36` : une seule instance ne compose pas puce + 60 % + 40 % en rangée) : `<Squelette largeur="w-8" classeBarre="h-8 rounded-sm" />`, `<Squelette largeur="w-[60%]" />`, `<Squelette largeur="w-[40%]" />` ; **sans** nouvelle chaîne (le `RefreshCw` d'aujourd'hui est muet) |
| 2 | `error` | `Alerte` (pas de `data-testid` aujourd'hui, on n'en invente pas), `icone` `AlertCircle` 18 px, `children` = « Impossible de charger les tâches » ou « Impossible de rafraîchir les tâches : la liste affichée peut être périmée. » ; **pas** d'`action` Réessayer (il n'y en a pas) ; le corps en cache s'affiche encore dessous (B-532) |
| 3 | `isTaskFormOpen` | `TaskForm` (§ 5), y compris l'état `nouvelle` |
| 4 | `viewMode === 'kanban'` | colonnes, y compris trois « Aucune tâche » si la liste filtrée est vide |
| 5 | sinon | liste ; si vide, `EtatVide` (§ 4), jamais les colonnes |

Zéro « Réessayer » sur Tâches, dans tous les états. `hasCachedTasks` et le
rechargement silencieux quand le cache existe restent.

Ordre de `ProjectsPanel` :

| Priorité | Condition | Cible |
|---|---|---|
| 1 | `loading` | trois rangées `aria-hidden`, chacune `flex gap-3` + trois `Squelette` (même composition que Tâches, `Squelette.tsx:36`) + « Chargement des projets… » en `role="status"` (le `Spinner` seul disparaît ; le texte, lui, existe déjà) |
| 2 | `error` | `Alerte` titre « Impossible de charger les projets. », `action` = `Button variant="secondary" size="md"` « Réessayer » (`onClick={load}`) : **un seul** |
| 3 | `projects.length === 0` | `EtatVide` titre « Aucun projet », sans action (le geste « Nouveau projet » est en tête) ; **kanban non monté** |
| 4 | sinon | `<Carte as="section">` + `ProjectsKanban` ; si troncature, le `role="alert"` warning est **au-dessus**, zéro Réessayer |

## 9. Gardes mécaniques et tests à aligner

Nouveaux, rouges d'abord :

`TasksPanel.da.test.tsx` : 1) `Segments` Colonnes / Liste, `aria-pressed` suit `viewMode` ; 2) compteur « 0 tâche » / « 2 tâches », aucune chaîne « tache » ; 3) Filtrer garde le nom « Filtrer les tâches », selects inchangés une fois dépliés ; 4) aucun `text-xs` sur un interactif (sous-arbre), aucun `sm` sur un `Button`, aucune couleur en dur ; 5) zéro « Réessayer » (erreur avec et sans cache).

`TaskKanban.da.test.tsx` : 1) trois `Etiquette` + comptes ; 2) barre `aria-label="Priorité moyenne"` (plus le mot « Moyenne ») ; `getByLabelText('Priorité urgente')` et `getByLabelText('Priorité haute')` sont deux barres, `bg-error` vs `bg-warning` (pas la même classe) ; 3) « En retard » porte `data-etiquette` ; 4) `task-item` présent, absent de l'overlay ; 5) « Marquer terminé » nommé, révélé au focus ; les trois commandes sont dans le flux (`mt-2`), pas `absolute top-2 right-2`.

`TaskList.da.test.tsx` : 1) grille `2.25rem 1fr auto` ; 2) D105 / D106 noms conservés ; 3) `EtatVide` + « Créer une tâche » `md` ; 4) confirmation : pas `role="alert"` sur le bandeau ; 5) barre `getByLabelText('Priorité moyenne')` dans la rangée (plus `getByText('Moyenne')`) ; 6) clic sur la rangée hors titre, case et corbeille ouvre la tâche (`currentTaskId` posé) ; le titre reste le seul tab stop d'ouverture.

`TaskForm.da.test.tsx` : 1) titre `required` + `aria-invalid` quand l'erreur maquette est posée ; `FormField required` affiche l'astérisque, le label accessible reste « Titre » ; 2) chaîne exacte « Ajoute un titre : c'est la seule chose obligatoire. » sur `#taskform-titre-error` ; `queryByRole` ne trouve **pas** de bandeau `Alerte` (composant) pour ce cas ; 3) ids `taskform-*` conservés ; `Input` `id="taskform-titre"` ; 4) Retour nommé ; 5) Statut et Priorité dans un `grid-cols-2`.

`ProjectsPanel.da.test.tsx` : 1) « 199 projets » sans alerte, 200 → `role="alert"` /Liste incomplète/ et pas « 200 projets » ; 2) un « Réessayer » sur erreur, zéro sinon ; 3) « Nouveau projet » `md` ; 4) pas de `bg-black/` ; 5) `projects=[]` → `EtatVide` « Aucun projet », kanban absent.

`ProjectsKanban.da.test.tsx` : 1) « Actif » sans `uppercase` ; 2) `Etiquette` sur les quatre têtes ; 3) `EtatVide` « Aucun projet » si monté avec `[]` (filet ; l'état utilisateur est le panneau).

`aucuneCouleurEnDur.test.ts` étendu aux six fichiers.

À aligner, forme seulement : `tailleDuCorps.test.tsx` (`getByText('Moyenne')` + `text-xs` → `getByLabelText('Priorité moyenne')` sur **les deux vues** : la liste porte désormais la même barre que le kanban, § 4 ; la barre est `w-1`, sans `text-xs` ; la description reste `text-sm` ; l'échéance, présente dans le jeu `due_date: '2026-09-18T00:00:00Z'`, porte `text-xs`) ; `TasksPanel.nomsAccessibles.test.tsx` (les bascules n'ont plus de `title` : leur nom est « Colonnes » / « Liste », le cas « nom du seul title » reste vert). Aucune assertion de comportement n'est retirée. Inchangés : `TasksPanel.orthographe.test.tsx`, `accentAFaire.test.tsx`, `TaskKanban.test.tsx` / `.clavier.test.tsx`, `TaskList.cycle6` / `.etatVide` / `.nomsAccessibles` / `.suppression.cycle6`, `TaskForm.titreRequis` / `.cycle6`, `ProjectsKanban.test.tsx` / `.casse.test.tsx`, `ProjectsPanel.troncature.test.tsx`.

## 10. Ce que ce lot ne fait pas

- Un seul écran « Tâches » + grille « Projets » dessous, colonne 72 rem : aujourd'hui deux destinations (`tasks`, `projects`). Fonctionnalité : **P-071** (numéro à confirmer par l'orchestrateur).
- Saisie rapide (titre, Entrée, Échap, projet courant) et « Ajouter une tâche » en pied de colonne ; « trois secondes depuis n'importe quel écran ». Fonctionnalité : **P-072**.
- Compteurs « N tâches ouvertes · M en retard · K projets actifs », résumé de filtres, tri par échéance, filtre d'échéance, nom du projet et pastille sur la carte, « En retard de N jours » / « Aujourd'hui » / `JJ/MM`. Fonctionnalité : **P-073**.
- Cartes projet en grille (barre de progression, devis/facture, séance, pastille de domaine) à la place du kanban par statut. Fonctionnalité : **P-074**.
- `ProjectModal`, sync de dossier, palette « Ajouter un projet ».
- Aucun changement de données, d'API, de store ni de navigation.

## 11. Plan de preuve

1. Tests rouges d'abord (§ 9), vérifiés rouges pour la bonne raison,
   sabotage par remplacement inverse, `.agents-sync-paused` posé.
2. Six portes : ruff, pytest (XML), vitest json, tsc, eslint (27), mypy 951.
3. Recette visuelle sur la pile jetable (17393 et 1420, jamais 17293) :
   états forcés par interception Playwright `page.route` de
   `**/api/tasks*` et `**/api/memory/projects*` : cinq tâches (deux en
   retard, une `done`) en Colonnes puis Liste ; liste vide ; titre manquant
   (ouvrir « Nouvelle tâche », Enregistrer à vide) ; projets 3 / 0 / 200
   (troncature) ; panne `tasks` et panne `projects`. Largeurs 1280, 1024,
   840, 800 px ; clair, sombre, contraste élevé ; trois tailles de police.
   Captures `.cartography-work/validation/da-lot6/`, rapport
   `docs/da/2026-09-11-lot6-recette.md`. Vérifier : Colonnes lisibles à
   800 px, anneau 3 px sur un segment et une carte, un seul Réessayer sur
   l'erreur projets, zéro sur Tâches, établi visible, `task-item` comptable,
   drag 8 px intact.
4. Revue Grok du diff avant le tag, `/release-therese 0.72.0-alpha` avec le
   GO de Ludo (toute la DA, pas ce lot seul).

## Points non repris

Aucun. Les 14 points de `.cartography-work/reviews/grok-da-lot6-projets-design-v1.log` sont fondés (preuve relue dans les fichiers cités) et repris dans les sections ci-dessus.
