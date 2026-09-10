# DA « Application affinée », lot 2 : l'écran Accueil (design à challenger avant le code)

Version 3, 10/09/2026 22:35, après les revues Grok de la v1 (NO-GO, 4 P1,
9 P2, 4 P3) et de la v2 (NO-GO, 2 P1, 3 P2, 3 P3), toutes reprises ici ;
journaux `.cartography-work/reviews/grok-da-lot2-design-v{1,2}.log`. Précédent : lot 1
(socle et coque), livré en v0.71.0-alpha. Maquette de référence :
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
`Squelette`, `Button`), quatre primitives recevant une extension (§ 2.1) ;
les mêmes données, les mêmes états, les mêmes destinations. Aucun appel
réseau, aucun store, aucun parcours ne change.

## Décisions tranchées par défaut (Ludo peut corriger)

1. Le portrait de THÉRÈSE (`CharacterPortrait`) reste l'avatar du message
   d'accueil, dans la pastille ronde de 2 rem de la maquette (le « T » de la
   maquette est un bouche-trou).
2. « Ouvrir Agenda » garde son libellé (décision persona 08) là où la maquette
   écrit « Voir tout mon agenda ».
3. Le variateur garde sa sémantique `radiogroup` (un seul choix, 24 tests) et
   prend la forme des segments de la DA en partageant les classes de
   `Segments` ; `Segments` (groupe + `aria-pressed`) n'est pas monté ici.
4. La formulation de la maquette remplace les mentions techniques là où
   l'état est le même (vide constaté, tête, pied). Les états « incomplet »
   et « sans messagerie » gardent leur prose actuelle : ils n'ont pas
   d'équivalent maquetté et leurs mots ont été pesés (B-051, B1 0.48).
5. Toute taille de bouton dans la carte est `md` (36 px, le `.btn` du socle) ;
   `sm` (32 px) n'y est pas employé.

## 1. L'en-tête de l'Accueil (dans la coque, scénario `today` seulement)

Maquette `.message` : grille `2rem 1fr`, gap .75 rem, marge basse `--espace-4`.

| Élément | Aujourd'hui | Cible |
|---|---|---|
| Avatar | portrait 2 rem `rounded-md border border-text shadow-card` | portrait 2 rem `rounded-full`, sans bordure ni ombre |
| Titre | `<h1>` Bonjour Sophie. | `<h1 className="font-editorial">Bonjour <em className="not-italic">Sophie</em>.` (la maquette : `h1.editorial em{font-style:normal}`, aucune couleur ; `font-editorial` est l'utilitaire du jeton `--font-editorial`, la classe `.editorial` de la maquette n'existe pas dans l'application) |
| Sous-titre | `text-sm leading-6 text-text-muted` | inchangé (`.sous`) |
| Ligne « THÉRÈSE · 19:01 » (mini-portrait) | présente | retirée ; remplacée par `<p className="text-xs font-medium text-text-muted">` (le `.meta` de la maquette) : « Jeudi 10 septembre · Sources : agenda, tâches, relances, factures, CRM ». La date vient de `resource.data.date` (`AAAA-MM-JJ` découpé, puis `new Date(annee, mois - 1, jour)`, jamais `new Date('AAAA-MM-JJ')` (BUG-125), formaté par `Intl.DateTimeFormat('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })`, jour de la semaine capitalisé) et n'est écrite qu'en `ready`. Les sources suivent LA MÊME règle que le pied (§ 5) : les sources présentes (liste non vide), dans l'ordre de `NOM_DE_SOURCE`, en minuscules ; les pannes ne sont pas listées ici (elles le sont dans la meta de tête et au pied). Sans aucune source présente, la date seule. Hors `ready` : rien |
| Heure | dans la ligne THÉRÈSE | dans le pied de la carte : « Rafraîchi à HH:MM » (prop `rafraichiA` de la carte, alimentée par `heureDAffichage`) |

Les six autres scénarios (`memory`, `email`, `meeting`, `invoice`, `board`,
`atelier`) gardent leur en-tête actuel : hors lot.

## 2. La carte du brief : `Carte` + `CarteTete`

### 2.1 Extensions des primitives (petites, testées)

- `CarteTete` : prop `idTitre?: string` posée sur le `<h2>` ; conteneur
  `flex flex-wrap` et `actions` en `ml-auto flex flex-wrap gap-2
  max-[840px]:basis-full max-[840px]:ml-0` : sous 840 px les actions
  occupent une ligne entière sous le titre (le titre garde `min-w-0 flex-1`
  sur sa ligne, rien ne se comprime).
- `Alerte` : étale les attributs natifs (`HTMLAttributes<HTMLDivElement>`,
  donc `data-testid`) ; prop `action?: ReactNode` rendue hors du `<p>`, sous le
  texte (`mt-2`) ; ici toujours un `Button variant="ghost" size="md"`.
- `Segments` : exporte `CLASSES_SEGMENTS` (« `inline-flex gap-1 p-1
  rounded-full bg-surface-2` ») et `classeSegment(actif)` (« `rounded-full
  px-3 py-1 text-sm font-medium` » + actif `bg-surface text-text shadow-sm`
  / inactif `text-text-muted hover:text-text`) et les consomme lui-même ;
  seul le `hover` est nouveau pour `Segments`.
- `Squelette` : inchangé ; `largeur` est une classe Tailwind (`w-8`,
  `w-[60%]`, `w-[40%]`).

### 2.2 La carte

- `Carte as="section"`, `aria-labelledby="today-dashboard-title"`,
  `data-testid="today-dashboard-card"` conservés ; ombre `shadow-sm` (la
  carte perd son ombre `rgba` en dur, § 7).
- `CarteTete idTitre="today-dashboard-title"` ; icône `Sparkles` 18 px.
- Titre de tête, par état (le garde `ready` actuel est conservé) :

| État | Titre | Meta |
|---|---|---|
| chargement | « Ta journée » | « Lecture des sources locales » |
| erreur | « Ta journée » | « Lecture impossible » |
| ready, N ≥ 1 | `todayBriefTitle(N)` (« Un point mérite ton attention » / « Ton attention aujourd'hui ») | « 1 élément » / « N éléments » + (M ≥ 1 ? « , dont 1 en retard » / « , dont M en retard » : rien) + (B-425 ? « , et 1 autre non affiché » / « , et K autres non affichés » : rien) ; puis, si des sources sont en panne, « · Agenda indisponible » / « · Agenda, Tâches indisponibles » |
| ready, N = 0, sans panne, messagerie branchée (vide constaté) | « Rien ne presse aujourd'hui » | « Aucune échéance, aucune facture en attente » |
| ready, N = 0, sans messagerie | « Ta journée » | « Messagerie non branchée » |
| ready, N = 0, au moins une source en panne (vide non constaté) | « Ta journée » | « <sources> indisponible(s), lecture incomplète » |

  `todayBriefTitle(0)` devient « Rien ne presse aujourd'hui » et n'est plus
  appelé que pour le vide constaté ; M = nombre d'éléments `urgent`.
- Actions de tête : `BoutonOuvrirLaVue`, dont le rendu par défaut devient `Button variant="secondary" size="md"` (libellé « Ouvrir <vue> » inchangé, `className` de remplacement conservé ; les six autres cartes en héritent, c'est la même consommation du socle que `Button` au lot 1) puis, en `ready` avec
  N ≥ 1, le geste principal : `Button variant="primary" size="md"`, texte
  visible « Commencer : <titre du premier élément> » (masqué en mode démo,
  sans `truncate` : le bouton s'écrit en entier, sur deux lignes au besoin
  (`h-auto min-h-9 whitespace-normal text-left`), pas d'`aria-label` : le nom accessible est le
  texte, distinct du titre de la ligne pour `getByText` et `getByRole`), qui
  appelle exactement le gestionnaire de la première ligne :
  `onOpenItem ? onOpenItem(item) : onOpenView(item.targetView)` (repli
  inclus, comme `TodayDashboardCard.tsx:356`).

## 3. Le variateur (`.filtre`)

Ordre dans la carte, de haut en bas : tête (§ 2.2), variateur, `Alerte` de
panne (§ 6), corps (lignes ou état), pied (§ 5). Rangée « Montre-moi » (`text-sm text-text-muted`) + le `radiogroup` actuel
habillé par `CLASSES_SEGMENTS` / `classeSegment(coché)` ; radios `sr-only`,
`focus-within` anneau 3 px (socle). Même règle d'apparition (au moins deux
mots utiles), mêmes libellés, même stockage.

## 4. Les lignes : `Ligne`

Chaque élément devient `<Ligne domaine=… puce=<Icône 18 px> titre=… detail=…
droite=… onClick=…>` :

| kind | domaine | puce |
|---|---|---|
| event | agenda | Calendar |
| task | taches | ListTodo |
| follow_up | prospects | Mail |
| invoice | factures | Receipt |
| prospect | prospects | Users |

`droite` = `<Etiquette ton={urgent ? 'erreur' : 'neutre'}>{badge}</Etiquette>`
+ `ChevronRight` 18 px muted (transparent au clic, la `Ligne` s'en charge).
Titre et détail masqués en mode démo. Le détail n'est plus tronqué (la
maquette l'écrit sur deux lignes) : `text-sm`, ligne cliquable (plancher
14 px). Le repli « Voir les N autres » devient `Button variant="ghost"
size="md"` pleine largeur, bordure haute, libellé `libelleDuRepli` inchangé.

## 5. Le pied `.sources`

`border-t bg-surface-2 px-4 py-2.5 text-xs font-medium text-text-muted`,
rendu en `ready` seulement s'il a quelque chose à dire (au moins une source
présente ou en panne ; le vide constaté n'a pas de pied, comme `brief-vide`) :
« Lu dans » + une `Etiquette domaine=…` par source présente, cinq libellés
distincts conservés (Agenda, Tâches, Relances, Factures, CRM ; Relances et
CRM en `domaine="prospects"`) + une `Etiquette ton="neutre"` « <Source>
indisponible » par clé de `indisponibles` (nom de `NOM_DE_SOURCE`, ou la clé
telle quelle si inconnue, jamais avalée) + à droite « Rafraîchi à HH:MM »
(`ml-auto`, `tabular-nums`) quand `rafraichiA` est donné.

## 6. Les états (corps de la carte)

| État | Aujourd'hui | Cible |
|---|---|---|
| chargement | spinner + « Je rassemble ta journée… » | trois `Squelette` (`w-8`, `w-[60%]`, `w-[40%]`) `aria-hidden`, puis le texte actuel en `role="status"`, `text-sm text-text-muted` |
| erreur | icône + « Brief indisponible » + message + bouton plein | `Alerte data-testid="today-dashboard-error"` titre « Brief indisponible », `children` = `resource.error`, `action` = `Button variant="secondary" size="md"` Réessayer |
| panne (toute source dans `indisponibles`), quel que soit le corps | bandeau warning 12 px sans bouton | `Alerte data-testid="today-dashboard-indisponible"` rendue dans TOUS les corps `ready`, entre le variateur et le corps, texte actuel inchangé (« Je n'ai pas pu lire Agenda. Ce qui en vient manque ici : ce n'est pas forcément une journée calme. ») ; `action` = `Button variant="ghost" size="md"` Réessayer SEULEMENT quand le corps n'en porte pas (N ≥ 1, ou sans messagerie) : un seul Réessayer dans la carte |
| corps, par priorité (comme aujourd'hui, `TodayDashboardCard.tsx:291-306`) | idem | 1) `has_email === false` → sans messagerie ; 2) sinon N ≥ 1 → lignes ; 3) sinon panne → vide non constaté ; 4) sinon → vide constaté |
| vide non constaté | « Ta journée est incomplète » + bouton | `EtatVide data-testid="today-dashboard-incomplet"` titre « Ta journée est incomplète », texte actuel (« Rien ne remonte, mais la lecture n'a pas abouti : ce n'est pas une journée calme constatée. »), `action` = `Button variant="secondary" size="md"` Réessayer (l'`Alerte` au-dessus n'en a pas). Jamais la formulation du vide constaté |
| vide constaté | coche verte « Rien d'urgent pour le moment » | `EtatVide data-testid="today-dashboard-empty"` titre « Ta journée est dégagée. », texte « Quand tu ajouteras une tâche, un rendez-vous ou une facture, ils apparaîtront ici avec leur échéance. », sans action (« Ouvrir Agenda » est déjà en tête) |
| sans messagerie | « Branche tes mails… » + bouton plein | `EtatVide data-testid="today-dashboard-setup-email"` titre et texte actuels, `action` = `Button variant="primary" size="md"` « Brancher mes mails » ; avec une panne, l'`Alerte` au-dessus porte Réessayer (test « la panne est nommée même quand l'écran invite à brancher les mails ») |
| mise en route | `SetupChecklist` (surface-2, boutons maison) | inchangé dans ce lot, sauf son titre en `h3` (la carte porte déjà le `h2`) |

`EtatVide` reçoit les attributs natifs (`data-testid`) : extension de la
primitive, même geste que `Alerte`.

## 7. Gardes mécaniques et tests à aligner

Nouveaux (`TodayDashboardCard.da.test.tsx`, rouges d'abord) :

1. une ligne = une seule commande (un `button`), la grille `2rem 1fr auto`,
   le badge porte `data-etiquette` ;
2. le geste principal « Commencer : … » appelle le même gestionnaire que la
   première ligne (avec et sans `onOpenItem`) et n'existe pas quand la liste
   est vide, ni hors `ready` ;
3. la tête garde son `id` (la section a un nom accessible), la meta écrit
   « 4 éléments, dont 2 en retard » et « 3 éléments » quand aucun retard ;
4. le pied écrit « Lu dans », une étiquette par source, « Agenda
   indisponible » en panne, « Rafraîchi à 11:58 » quand la prop est donnée,
   et n'existe pas sur le vide constaté ;
5. le chargement montre des squelettes `aria-hidden` et un `role="status"` ;
6. la panne partielle est un `role="alert"` qui nomme la source ; un seul
   « Réessayer » dans la carte, quel que soit l'état ; le vide constaté n'a
   pas d'alerte ;
7. aucune classe `text-xs` sur un interactif de la carte, aucune couleur en
   dur dans `TodayDashboardCard.tsx` (extension de `aucuneCouleurEnDur` au
   fichier) ;
8. dans la coque : plus de ligne « THÉRÈSE · heure » sur le scénario `today`,
   la date du jour est écrite en français, le `h1` porte `font-editorial` ;
9. primitives : `CarteTete` pose `idTitre`, `Alerte` et `EtatVide`
   transmettent `data-testid` et rendent `action`, `Segments` expose ses
   classes et les consomme.

À aligner dans le même commit, avec la raison dans le message (ils figent la
forme, pas le comportement) : `lot9DA.test.ts` B-363 (les couleurs viennent
de `Ligne domaine`, le test vérifie la table kind → domaine),
`TodayDashboardCard.test.tsx` (« Rien d'urgent » → « Ta journée est
dégagée. », « Sources réelles » → « Lu dans », « issu de tes données » →
« éléments »), `TodayDashboardCard.variateur.test.tsx` (« Aucune priorité
détectée » → « Rien ne presse aujourd'hui », « 9 éléments issus de tes
données » → « 9 éléments, dont … » ou « 9 éléments » selon les retards du
jeu de données), `AccueilMoinsCharge.test.tsx` (commentaire), `InformationsVides.test.tsx:49`
(`getByText('THÉRÈSE', { selector: 'div' })` visait la ligne « THÉRÈSE ·
heure » du scénario `today`, qui devient « Rafraîchi à HH:MM » au pied de la
carte : l'assertion suit l'heure, hors vide constaté),
`TodayDashboardCard.modeDemo.test.tsx:56` (`getByText(/Claire Fontaine/)`
trouverait la ligne ET « Commencer : … » : passer par `getAllByText` ou
`getByRole('button', { name })`, l'invariant « aucun nom réel » est vérifié
sur les deux). Aucune assertion de comportement n'est retirée.

## 8. Ce que ce lot ne fait pas

- Les états `relance` (relance préparée, brouillon, fil des objets) et
  `validee` (relance envoyée, suivant) de la maquette : c'est un parcours
  « préparer une relance depuis le brief » qui n'existe pas aujourd'hui (le
  clic ouvre l'objet, B-563). Fonctionnalité, pas DA : P-067 enregistrée au
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
   deux en retard ; vide ; agenda indisponible avec liste ; agenda
   indisponible sans liste ; panne totale ; sans messagerie ; chargement
   lent), à 1280, 1024, 840 et 800 px, en clair, sombre et contraste élevé,
   aux trois tailles de police ; captures avant/après dans
   `.cartography-work/validation/da-lot2/`, rapport
   `docs/da/2026-09-10-lot2-recette.md`. Vérifier : le geste principal
   visible et entier à 800 px, l'établi toujours visible, le composeur qui ne
   recouvre pas le pied de la carte (e2e B-320), l'anneau de focus sur une
   ligne et sur un segment, un seul « Réessayer » par état.
4. Revue Grok du diff avant le tag, `/release-therese 0.72.0-alpha` avec le
   GO de Ludo.
