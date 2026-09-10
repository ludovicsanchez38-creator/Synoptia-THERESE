# DA « Application affinée », lot 2 : l'écran Accueil (design à challenger avant le code)

Date : 10/09/2026, 21:40. Précédent : lot 1 (socle et coque), livré en
v0.71.0-alpha. Maquette de référence :
`docs/da/2026-09-05-propositions/maquettes/accueil.html` (états `normal`,
`vide`, `erreur` ; `relance` et `validee` sont des canevas, voir § 8), page
`docs/da/2026-09-05-propositions/accueil.html`, critères de `ecrans.json` :
« Dire en une seconde ce qui attend Marie aujourd'hui, un seul geste
principal, un composeur qui ne recouvre rien. Priorité nommée et destination
explicite ; l'établi toujours visible ; les mentions techniques quittent la
lecture. » Déjà décidé côté UX, pas à rejuger : cartes qui ouvrent leur
destination (27/08, B-563), brief rafraîchi au retour (0.66.1), états
indisponibles distincts des états vides (B-051), libellé du bouton de vue
dérivé du nom de la vue (`BoutonOuvrirLaVue`, persona 08), variateur à trois
mots écrits (29/08).

## Ce que le lot change, en une phrase

La carte du brief (`TodayDashboardCard.tsx`) et l'en-tête de l'Accueil dans
la coque prennent la forme de la maquette en consommant les primitives du
lot 1 (`Carte`, `CarteTete`, `Ligne`, `Etiquette`, `Alerte`, `EtatVide`,
`Squelette`, `Button`) ; les mêmes données, les mêmes états, les mêmes
destinations. Aucun appel réseau, aucun store, aucun parcours ne change.

## Décisions tranchées par défaut (Ludo peut corriger)

1. Le portrait de THÉRÈSE (`CharacterPortrait`) reste l'avatar du message
   d'accueil, dans la pastille ronde de 2 rem de la maquette (le « T » de la
   maquette est un bouche-trou).
2. « Ouvrir Agenda » garde son libellé (décision persona 08) là où la maquette
   écrit « Voir tout mon agenda ».
3. Le variateur garde sa sémantique `radiogroup` (un seul choix, 24 tests) et
   prend la forme des segments de la DA ; `Segments` (groupe + `aria-pressed`)
   n'est pas utilisé ici, ses classes sont partagées.
4. La formulation de la maquette remplace les mentions techniques : « Rien ne
   presse aujourd'hui » / « Ta journée est dégagée. », « Lu dans », « N
   éléments, dont M en retard ». Les tests qui figent l'ancienne prose sont
   alignés (listés § 7).

## 1. L'en-tête de l'Accueil (dans la coque, scénario `today` seulement)

Maquette `.message` : grille `2rem 1fr`, gap .75 rem, marge basse `--espace-4`.

| Élément | Aujourd'hui | Cible |
|---|---|---|
| Avatar | portrait 2 rem `rounded-md border border-text shadow-card` | portrait 2 rem `rounded-full`, sans bordure ni ombre |
| Titre | `<h1>` Bonjour Sophie. | `<h1 className="font-editorial">Bonjour <em>Sophie</em>.` (em en accent, non italique : `.editorial em` n'existe pas dans `base.css`, la DA ne colore rien ; `em` reste sémantique et `not-italic`) |
| Sous-titre | `text-sm leading-6 text-text-muted` | inchangé (`.sous`) |
| Ligne « THÉRÈSE · 19:01 » (mini-portrait) | présente | retirée ; remplacée par `.jour.meta` : « Jeudi 10 septembre · Sources : agenda, tâches, factures » (12 px, 500, muted ; date = `resource.data.date` formatée en français, sources = celles présentes dans la réponse, « Sources : aucune lecture » en attendant) |
| Heure | dans la ligne THÉRÈSE | dans le pied de la carte : « Rafraîchi à HH:MM » (prop `rafraichiA` de la carte, alimentée par `heureDAffichage`) |

Les six autres scénarios (`memory`, `email`, `meeting`, `invoice`, `board`,
`atelier`) gardent leur en-tête actuel : hors lot.

## 2. La carte du brief : `Carte` + `CarteTete`

- `Carte as="section"`, `aria-labelledby="today-dashboard-title"`,
  `data-testid="today-dashboard-card"` conservés ; ombre `shadow-sm` (la carte
  perd son ombre `rgba` en dur, § 7).
- `CarteTete` : icône `Sparkles` (pastille accent), titre `todayBriefTitle`
  (« Rien ne presse aujourd'hui » à 0, « Un point mérite ton attention » à 1,
  « Ton attention aujourd'hui » sinon), meta « 4 éléments, dont 2 en retard »
  (+ « , et 3 autres non affichés » quand le serveur plafonne, B-425) ; en
  chargement « Lecture des sources locales ».
- Actions de tête : `BoutonOuvrirLaVue` (secondaire) puis, quand la liste a
  au moins un élément, le geste principal : `Button variant="primary"
  size="sm"` dont le libellé est le titre du premier élément (masqué en mode
  démo, `truncate max-w-[18rem]`, `aria-label="Ouvrir : <titre>"`) et qui
  appelle `onOpenItem(items[0])`, exactement comme le clic sur sa ligne. Sous
  840 px, il passe sous la ligne de titre (`flex-wrap`), jamais coupé.

## 3. Le variateur (`.filtre`)

Rangée « Montre-moi » (14 px muted) + segments : conteneur `inline-flex gap-1
p-1 rounded-full bg-surface-2`, chaque mot `rounded-full px-3 py-1.5 text-sm
font-medium`, actif `bg-surface text-text shadow-sm`, inactif `text-text-muted
hover:text-text`. Les classes sont exportées par `Segments.tsx`
(`CLASSES_SEGMENTS`, `classeSegment(actif)`) et consommées par le variateur
et par `Segments` : une seule source. Radios `sr-only`, `focus-within` anneau
3 px (socle). Même règle d'apparition (au moins deux mots utiles).

## 4. Les lignes : `Ligne`

Chaque élément devient `<Ligne domaine=… puce=<Icône 16 px> titre=… detail=…
droite=… onClick=…>` :

| kind | domaine | puce |
|---|---|---|
| event | agenda | Calendar |
| task | taches | ListTodo |
| follow_up | prospects | Mail |
| invoice | factures | Receipt |
| prospect | prospects | Users |

`droite` = `<Etiquette ton={urgent ? 'erreur' : 'neutre'}>{badge}</Etiquette>`
+ `ChevronRight` 16 px muted (transparent au clic, la `Ligne` s'en charge).
Titre et détail masqués en mode démo. Le détail n'est plus tronqué (la
maquette l'écrit sur deux lignes) : `text-sm`, ligne cliquable (plancher
14 px). Le repli « Voir les N autres » devient `Button variant="ghost"
size="sm"` pleine largeur, bordure haute.

## 5. Le pied `.sources`

`border-t bg-surface-2 px-4 py-2.5 text-xs font-medium text-text-muted` :
« Lu dans » + une `Etiquette domaine=…` par source présente (Agenda,
Tâches, Relances et CRM en `prospects`, Factures) + une `Etiquette
ton="neutre"` « <Source> indisponible » par source en panne + à droite
« Rafraîchi à HH:MM » (`ml-auto`, tabular). Le pied n'apparaît qu'en `ready`
(inchangé).

## 6. Les états

| État | Aujourd'hui | Cible (primitive) |
|---|---|---|
| chargement | spinner + « Je rassemble ta journée… » | trois `Squelette` (2 rem / 60 % / 40 %) `aria-hidden`, plus le texte en `role="status"` visible en 14 px muted sous les squelettes |
| erreur | icône + « Brief indisponible » + message + bouton plein | `Alerte` (role alert) titre « Brief indisponible », message, `Button variant="secondary" size="sm"` Réessayer ; testid conservé |
| source en panne, liste non vide | bandeau warning texte 12 px | `Alerte` dans le corps, au-dessus des lignes : « Je n'ai pas pu lire Agenda. Ce qui en vient manque ici : ce n'est pas forcément une journée calme. » + `Button variant="ghost" size="sm"` Réessayer ; la source reste NOMMÉE (B-051, tests `indisponible`) ; le pied ajoute « Agenda indisponible » |
| vide constaté | coche verte « Rien d'urgent pour le moment » | `EtatVide titre="Ta journée est dégagée."` « Quand tu ajouteras une tâche, un rendez-vous ou une facture, ils apparaîtront ici avec leur échéance. » ; titre de tête « Rien ne presse aujourd'hui », meta « Aucune échéance, aucune facture en attente » |
| vide non constaté (panne) | « Ta journée est incomplète » | `EtatVide` même titre, même texte, `Button secondary` Réessayer ; jamais la formulation du vide constaté |
| sans messagerie | « Branche tes mails… » + bouton plein | `EtatVide` même titre et texte, `Button primary size="sm"` « Brancher mes mails » |
| mise en route | `SetupChecklist` (surface-2, boutons maison) | inchangé dans ce lot (écran « Mise en route » sans maquette, § 8) ; seul son titre passe en `h3` (la carte porte déjà le `h2`) |

Les `data-testid` (`today-dashboard-error`, `-empty`, `-incomplet`,
`-setup-email`, `-indisponible`) sont conservés.

## 7. Gardes mécaniques et tests à aligner

Nouveaux (`TodayDashboardCard.da.test.tsx`, rouges d'abord) :

1. une ligne = une seule commande (un `button`), la grille `2rem 1fr auto`,
   le badge porte `data-etiquette` ;
2. le geste principal ouvre le premier élément (`onOpenItem` reçu avec
   `items[0]`) et n'existe pas quand la liste est vide ;
3. le pied écrit « Lu dans » et une étiquette de domaine par source, plus
   « Rafraîchi à 11:58 » quand la prop est donnée ;
4. le chargement montre des squelettes `aria-hidden` et un `role="status"` ;
5. la panne partielle est un `role="alert"` qui nomme la source et offre
   « Réessayer » ; le vide constaté n'a pas d'alerte ;
6. aucune classe `text-xs` sur un interactif de la carte, aucune couleur en
   dur (`rgba`, `#`) dans `TodayDashboardCard.tsx` (extension de la liste
   `aucuneCouleurEnDur` à `components/prototype/TodayDashboardCard.tsx`) ;
7. dans la coque : plus de ligne « THÉRÈSE · heure » sur le scénario `today`,
   la date du jour est écrite, le `h1` porte `font-editorial`.

À aligner (ils figent la forme, pas le comportement) : `lot9DA.test.ts`
B-363 (les couleurs viennent de `Ligne domaine`, le test vérifie la table
kind → domaine), `TodayDashboardCard.test.tsx` (« Rien d'urgent » → « Ta
journée est dégagée. », « Sources réelles » → « Lu dans »),
`TodayDashboardCard.variateur.test.tsx` (« Aucune priorité détectée » →
« Rien ne presse aujourd'hui »), `AccueilMoinsCharge.test.tsx` (commentaire).
Chaque modification de test est justifiée dans le commit.

## 8. Ce que ce lot ne fait pas

- Les états `relance` (relance préparée, brouillon, fil des objets) et
  `validee` (relance envoyée, suivant) de la maquette : c'est un parcours
  « préparer une relance depuis le brief » qui n'existe pas aujourd'hui (le
  clic ouvre l'objet, B-563). Fonctionnalité, pas DA : proposition P-067 au
  portail humain, avec le canevas Relances comme support.
- « Créer une tâche » dans l'état vide : le brief n'a pas de création de
  tâche ; ouvrir Projets sous ce libellé mentirait. Différé avec P-067.
- `SetupChecklist` et l'écran Mise en route : lot des écrans sans maquette.
- Les six autres scénarios de l'Accueil et leurs cartes (`ContactsMemoryCard`,
  `EmailInboxCard`, …) : lots suivants (tiroir, contacts, devis, agenda).
- Aucun changement de données, d'API, de store ni de navigation.

## 9. Plan de preuve

1. Tests rouges d'abord (§ 7), vérifiés rouges pour la bonne raison,
   sabotage par remplacement inverse, `.agents-sync-paused` posé.
2. Six portes : ruff, pytest (XML), vitest json, tsc, eslint (27), mypy 951.
3. Recette visuelle sur la pile jetable c6 relancée (17393 et 1420, jamais
   17293) : les six états forcés par interception de `/api/dashboard/today`
   (Playwright `page.route`) avec des réponses fixes (quatre éléments dont
   deux en retard ; vide ; agenda indisponible avec liste ; panne totale ;
   sans messagerie ; chargement lent), à 1280, 1024, 840 et 800 px, en clair,
   sombre et contraste élevé, aux trois tailles de police ; captures
   avant/après dans `.cartography-work/validation/da-lot2/`, rapport
   `docs/da/2026-09-10-lot2-recette.md`. Vérifier : le geste principal
   visible et entier à 800 px, l'établi toujours visible, le composeur qui ne
   recouvre pas le pied de la carte (e2e B-320), l'anneau de focus sur une
   ligne et sur un segment.
4. Revue Grok du diff avant le tag, `/release-therese 0.72.0-alpha` avec le
   GO de Ludo.
