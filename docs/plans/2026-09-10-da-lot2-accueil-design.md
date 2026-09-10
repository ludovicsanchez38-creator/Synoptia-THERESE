# DA « Application affinée », lot 2 : l'écran Accueil (design à challenger avant le code)

Version 6, 11/09/2026 00:15, après cinq revues Grok (v1 NO-GO 4 P1, 9 P2,
4 P3 ; v2 NO-GO 2 P1, 3 P2, 3 P3 ; v3 NO-GO 1 P1, 2 P2, 3 P3 ; v4 NO-GO
1 P1, 2 P2, 3 P3 ; v5 NO-GO 1 P1, 5 P2, 3 P3), toutes reprises ici ; journaux
`.cartography-work/reviews/grok-da-lot2-design-v{1,2,3,4,5b}.log`. Un point
de la v5 est repris autrement que proposé : le geste principal reste visible
en mode démo (masqué comme la ligne), les tests passent par le rôle. Précédent : lot 1
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
| Titre | `<h1>` Bonjour Sophie. | `<h1 className="font-editorial">Bonjour <em className="not-italic">Sophie</em>.` ; sans `displayName`, « Bonjour. » sans `em` ni espace, comme aujourd'hui (la maquette : `h1.editorial em{font-style:normal}`, aucune couleur ; `font-editorial` est l'utilitaire du jeton `--font-editorial`, la classe `.editorial` de la maquette n'existe pas dans l'application) |
| Sous-titre | `text-sm leading-6 text-text-muted` | inchangé (`.sous`) |
| Ligne « THÉRÈSE · 19:01 » (mini-portrait) | présente | retirée ; remplacée par `<p data-testid="accueil-jour" className="text-xs font-medium text-text-muted">` (le `.meta` de la maquette), toujours rendue sur le scénario `today`, composée de segments séparés par « · » : (a) la date, seulement quand `resource.data` existe (en `ready`, et pendant une revalidation où `data` est encore là, B-426) : `AAAA-MM-JJ` découpé, puis `new Date(annee, mois - 1, jour)`, jamais `new Date('AAAA-MM-JJ')` (BUG-125), formaté par `Intl.DateTimeFormat('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })` puis premier caractère seul mis en capitale en JS (`s.charAt(0).toLocaleUpperCase('fr-FR') + s.slice(1)`, jamais `capitalize` Tailwind qui toucherait le mois) ; (b) « Sources : agenda, tâches, factures » avec LA MÊME règle que le pied (§ 5) : sources présentes (liste non vide), ordre de `NOM_DE_SOURCE`, minuscules ; absent sans source ; (c) « Rafraîchi à HH:MM » dès que `heureDAffichage` existe, quel que soit l'état de la ressource (c'est l'heure de la coque, dite aujourd'hui hors ressource, `ConversationCanvasPrototype.tsx:1723`). Exemple : « Jeudi 10 septembre · Sources : agenda, tâches, factures · Rafraîchi à 21:40 » ; en chargement initial : « Rafraîchi à 21:40 » |
| Heure | dans la ligne THÉRÈSE | dans la ligne du jour ci-dessus, jamais au pied de la carte (la carte ne reçoit pas de prop d'heure) |

Le bloc portrait + `h1` + sous-titre est aujourd'hui partagé par les sept
scénarios (`ConversationCanvasPrototype.tsx:1694-1714`) : il est scindé par
`scenario === 'today'` (avatar rond, `font-editorial`, ligne du jour) ;
les six autres scénarios (`memory`, `email`, `meeting`, `invoice`, `board`,
`atelier`) gardent leur bloc actuel, ligne « THÉRÈSE · heure » comprise :
hors lot.

## 2. La carte du brief : `Carte` + `CarteTete`

### 2.1 Extensions des primitives (petites, testées)

- `CarteTete` : prop `idTitre?: string` posée sur le `<h2>` ; le conteneur
  garde `flex items-center gap-3 px-4 pt-4 pb-2` et reçoit en plus
  `flex-wrap` ; `actions` passe de `ml-auto flex gap-2` à `ml-auto flex
  flex-wrap gap-2 max-[840px]:basis-full max-[840px]:ml-0` : sous 840 px les actions
  occupent une ligne entière sous le titre (le titre garde `min-w-0 flex-1`
  sur sa ligne, rien ne se comprime).
- `Alerte` : étale les attributs natifs (`HTMLAttributes<HTMLDivElement>`,
  donc `data-testid`) ; prop `action?: ReactNode` rendue hors du `<p>`, sous le
  texte (`mt-2`). Dans la carte, deux usages et une variante chacun :
  erreur totale → `Button variant="secondary" size="md"` Réessayer ; panne
  partielle → `Button variant="ghost" size="md"` Réessayer (§ 6 reprend
  ces deux formes, sans autre).
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
| ready, N = 0, au moins une source en panne (vide non constaté) | « Ta journée » | « Agenda indisponible, lecture incomplète » / « Agenda, Tâches indisponibles, lecture incomplète » |

  `todayBriefTitle(0)` devient « Rien ne presse aujourd'hui » et n'est plus
  appelé que pour le vide constaté ; M = nombre d'éléments `urgent`.
- Actions de tête : `BoutonOuvrirLaVue` avec un `className` local qui reproduit `Button secondary md` (`inline-flex h-9 items-center rounded-md border border-border bg-surface px-4 text-sm font-semibold text-text hover:bg-surface-2 transition-colors` + l'anneau de focus), libellé « Ouvrir Agenda » inchangé ; le défaut du composant partagé n'est pas touché (les six autres cartes gardent le leur, § 8) puis, en `ready` avec
  N ≥ 1, le geste principal : `Button variant="primary" size="md"`, texte
  visible « Commencer : <titre du premier élément> » (masqué en mode démo,
  sans `truncate` : le bouton s'écrit en entier, sur deux lignes au besoin
  (`h-auto min-h-9 whitespace-normal text-left min-w-0 max-w-full`, et
  `basis-full` sous 840 px comme le conteneur `actions`), pas d'`aria-label` : le nom accessible est le
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

`droite` = `<Etiquette ton={kind === 'invoice' ? 'attention' : urgent ? 'erreur' : 'neutre'}>{badge}</Etiquette>` (la maquette peint les factures en `e-attention`, « Impayée » / « À relancer » ; les retards de tâches et de relances en `e-erreur` ; présentation seule, `urgent` reste ce qu'il est pour le tri et le repli)
+ `ChevronRight` 18 px muted (transparent au clic, la `Ligne` s'en charge).
Titre et détail masqués en mode démo. Le détail n'est plus tronqué (la
maquette l'écrit sur deux lignes) : `text-sm`, ligne cliquable (plancher
14 px). Le repli « Voir les N autres » devient `Button variant="ghost"
size="md"` pleine largeur, bordure haute, libellé `libelleDuRepli` inchangé.

## 5. Le pied `.sources`

`border-t bg-surface-2 px-4 py-2.5 text-xs font-medium text-text-muted`,
rendu en `ready` seulement s'il a quelque chose à dire : « source présente »
= tableau non vide dans la réponse (`events`, `urgent_tasks`,
`due_follow_ups`, `overdue_invoices`, `stale_prospects`), exactement la règle
actuelle (`TodayDashboardCard.tsx:395-399`), donc le pied existe aussi à
N = 0 quand `events` ne contient que des rendez-vous solo (qui ne font pas de
ligne, `prototypeReadModels.ts:183`) ; ou au moins une clé de
`indisponibles`. Sans rien de tout cela (le `brief-vide` de la maquette), pas
de pied. La ligne du jour (§ 1) suit la même définition :
« Lu dans » + une `Etiquette domaine=…` par source présente, cinq libellés
distincts conservés (Agenda, Tâches, Relances, Factures, CRM ; Relances et
CRM en `domaine="prospects"`) + une `Etiquette ton="neutre"` « <Source>
indisponible » par clé de `indisponibles` (nom de `NOM_DE_SOURCE`, ou la clé
telle quelle si inconnue, jamais avalée) ; pas d'heure au pied (elle est dans la ligne du jour, § 1).

## 6. Les états (corps de la carte)

| État | Aujourd'hui | Cible |
|---|---|---|
| chargement | spinner + « Je rassemble ta journée… » | trois rangées `aria-hidden` façon `Ligne` (`grid grid-cols-[2rem_1fr_auto] gap-3 items-center px-4 py-3 border-t border-border`) : une puce `Squelette largeur="w-8" className="h-8 rounded-sm"`, puis une colonne de deux barres `Squelette largeur="w-[60%]"` et `largeur="w-[40%]"`, rien à droite ; puis le texte actuel « Je rassemble ta journée… » en `role="status"`, `px-4 py-3 text-sm text-text-muted` |
| erreur | icône + « Brief indisponible » + message + bouton plein | `Alerte data-testid="today-dashboard-error"` titre « Brief indisponible », `children` = `resource.error`, `action` = `Button variant="secondary" size="md"` Réessayer |
| panne (toute source dans `indisponibles`), quel que soit le corps | bandeau warning 12 px sans bouton | `Alerte data-testid="today-dashboard-indisponible"` rendue dans TOUS les corps `ready`, entre le variateur et le corps, dans une enveloppe `px-4 pt-3` (l'alerte en retrait de la maquette, `padding:.75rem var(--espace-3) 0`, jamais collée aux bords ; même enveloppe pour l'erreur totale), texte actuel inchangé (« Je n'ai pas pu lire Agenda. Ce qui en vient manque ici : ce n'est pas forcément une journée calme. ») ; `action` = `Button variant="ghost" size="md"` Réessayer SEULEMENT quand le corps n'en porte pas (N ≥ 1, ou sans messagerie) : un seul Réessayer dans la carte |
| corps, par priorité (exactement l'ordre actuel, `TodayDashboardCard.tsx:289-306`) | idem | 1) N ≥ 1 → lignes (la liste gagne dès qu'elle n'est pas vide, messagerie branchée ou non) ; 2) sinon `has_email === false` → sans messagerie ; 3) sinon panne → vide non constaté ; 4) sinon → vide constaté |
| vide non constaté | « Ta journée est incomplète » + bouton | `EtatVide data-testid="today-dashboard-incomplet"` titre « Ta journée est incomplète », texte actuel (« Rien ne remonte, mais la lecture n'a pas abouti : ce n'est pas une journée calme constatée. »), `action` = `Button variant="secondary" size="md"` Réessayer (l'`Alerte` au-dessus n'en a pas). Jamais la formulation du vide constaté |
| vide constaté | coche verte « Rien d'urgent pour le moment » | `EtatVide data-testid="today-dashboard-empty"` titre « Ta journée est dégagée. », texte « Quand tu ajouteras une tâche, un rendez-vous ou une facture, ils apparaîtront ici avec leur échéance. », sans action (« Ouvrir Agenda » est déjà en tête) |
| sans messagerie | « Branche tes mails… » + bouton plein | `EtatVide data-testid="today-dashboard-setup-email"` titre et texte actuels, `action` = `Button variant="primary" size="md"` « Brancher mes mails » ; avec une panne, l'`Alerte` au-dessus porte Réessayer (test « la panne est nommée même quand l'écran invite à brancher les mails ») |
| mise en route | `SetupChecklist` (surface-2, boutons maison) | inchangé dans ce lot, sauf une prop `niveau?: 'h2' \| 'h3'` (défaut `h2`, les montages seuls ne changent pas) que la carte passe à `h3` (elle porte déjà le `h2`) ; rendu sous l'`EtatVide`, avant le pied, dans les trois corps à N = 0 (sans messagerie, vide non constaté, vide constaté), comme aujourd'hui (`TodayDashboardCard.tsx:338-346`), dans un `px-4 pb-4` |

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
   exactement « 4 éléments, dont 2 en retard » et « 3 éléments » sur des jeux
   sans `indisponibles` ; un cas séparé vérifie le suffixe « · Agenda
   indisponible » ;
4. le pied écrit « Lu dans », une étiquette par source, « Agenda
   indisponible » en panne, n'existe pas sur un jeu sans aucun tableau ni
   panne, et existe avec « Agenda » sur un jeu réduit à un rendez-vous solo
   (N = 0) ;
5. le chargement montre des squelettes `aria-hidden` et un `role="status"` ;
6. la panne partielle est un `role="alert"` qui nomme la source ; le
   nombre de « Réessayer » dans la carte est exactement 1 sur erreur totale,
   panne avec N ≥ 1, vide non constaté, sans messagerie avec panne, et
   exactement 0 sur chargement, liste sans panne, vide constaté, sans
   messagerie sans panne ; le vide constaté n'a pas d'alerte ;
7. aucune classe `text-xs` sur un interactif de la carte, aucune couleur en
   dur dans `TodayDashboardCard.tsx` (extension de `aucuneCouleurEnDur` au
   fichier) ;
8. dans la coque : plus de ligne « THÉRÈSE · heure » sur le scénario `today`,
   la ligne du jour écrit « Rafraîchi à HH:MM » dès le chargement, puis la
   date en français (« Jeudi 10 septembre », premier caractère seul en
   capitale) et les sources présentes en `ready`, le `h1` porte
   `font-editorial` ; sur `memory`, la ligne « THÉRÈSE · heure » est intacte ;
9. primitives : `CarteTete` pose `idTitre`, `Alerte` et `EtatVide`
   transmettent `data-testid` et rendent `action`, `Segments` expose ses
   classes et les consomme.

À aligner dans le même commit, avec la raison dans le message (ils figent la
forme, pas le comportement) : `lot9DA.test.ts` B-363 (les couleurs viennent
de `Ligne domaine`, le test vérifie la table kind → domaine),
`TodayDashboardCard.test.tsx` (« Rien d'urgent » → « Ta journée est
dégagée. », « Sources réelles » → « Lu dans », « 1 élément issu de tes
données » → « 1 élément » exactement), `TodayDashboardCard.variateur.test.tsx`
(« Aucune priorité détectée » → « Rien ne presse aujourd'hui » ;
`dashboard(9, 0)` n'a aucun retard, donc « 9 éléments issus de tes données »
→ « 9 éléments » exactement ; un jeu avec retards écrit « 9 éléments, dont
2 en retard »), `AccueilMoinsCharge.test.tsx` (commentaire), `InformationsVides.test.tsx:49`
(`getByText('THÉRÈSE', { selector: 'div' })` visait la ligne « THÉRÈSE ·
heure » du scénario `today`, rendue sans ressource : l'assertion vise
désormais `getByTestId('accueil-jour')` et son « Rafraîchi à », présent dès
le chargement, donc sans mock supplémentaire),
`TodayDashboardCard.modeDemo.test.tsx:56` et `:78` (le geste principal
reste rendu en mode démo, avec le titre masqué comme la ligne : cacher une
fonction en démonstration serait un autre écran ; `getByText(/Claire
Fontaine/)` et `getByText(/Nathalie BALLOT/)` trouveraient la ligne ET
« Commencer : … » : les deux cas passent par `getByRole('button', { name:
'Relancer Nathalie BALLOT' })` pour la ligne et `{ name: /^Commencer :/ }`
pour le geste, et vérifient « aucun nom réel » sur les deux boutons). Aucune assertion de comportement n'est retirée.

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

## 11. Revue v6 : GO (11/09/2026 00:40), six reprises à l'implémentation

Journal `.cartography-work/reviews/grok-da-lot2-design-v6.log`. Aucun P1.
Repris tels quels dans le code : (1) `Squelette` reçoit `classeBarre` pour
que la puce du chargement soit `h-8 rounded-sm` ; (2) tests démo : allumé →
`queryByRole` « Relancer Nathalie BALLOT » absent, `getByRole` « Relancer
Claire Fontaine » et `/^Commencer :/` sans nom réel ; éteint → `getByRole`
« Relancer Nathalie BALLOT » ; (3) les deux `Alerte` portent `icone`
(`AlertCircle` 18 px) ; (4) anneau du variateur écrit sur le `label` :
`focus-within:outline focus-within:outline-[3px] focus-within:outline-offset-2
focus-within:outline-ring` ; (5) `SetupChecklist` reçoit
`status={setup.has_email === false ? { ...setup, has_email: true } : setup}`
comme aujourd'hui ; (6) formes minuscules des sources dans la ligne du jour
par table : agenda, tâches, relances, factures, CRM (sigle conservé).
