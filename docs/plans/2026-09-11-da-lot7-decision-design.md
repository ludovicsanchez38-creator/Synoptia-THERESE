# DA « Application affinée », lot 7 : l'écran Décision (Board) (design à challenger avant le code)

Version 4, 11/09/2026 01:09, après la revue de la v3 (6 points repris, 0 non repris) ; journal `.cartography-work/reviews/grok-da-lot7-decision-design-v3.log`. Précédent : lot 3 (Tiroir), livré sur `main` ;
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
   Opérationnel, Voix du client, Contradicteur) sont P-0xy.
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
| Cadre | `section` ombre `rgba`, `data-testid="board-history-card"` | `Carte as="section"` `aria-labelledby="board-history-title"` même testid ; `shadow-sm` |
| Tête | portrait index 1 + `h2` « Décision » + meta | `CarteTete idTitre="board-history-title"` icône `Gavel` 18 px, titre « Décision » ; meta inchangée : chargement « Lecture de l'historique local » ; `ready` → `libelleDecisionsChargees(n)` (`n >= 30` : « n décisions chargées (total non mesuré) » ; sinon « n décision(s) enregistrée(s) », pluriel `n > 1`) |
| Actions | boutons maison « Nouvelle question » + `BoutonOuvrirLaVue` | `Button variant="primary" size="md"` « Nouvelle question », `Plus` 18 px, même `onNewBoard` ; `BoutonOuvrirLaVue vue="board"` `className={CLASSE_BOUTON_VUE}`, libellé « Ouvrir Décision » inchangé |
| Run en cours | bouton `data-testid="board-current-run"`, titre `text-xs` | `<div data-testid="board-current-run">` enveloppe `Ligne` (pas une prop de `Ligne` : `Ligne.tsx:26-35` n'a ni rest props ni `data-testid`) ; `Ligne domaine="prospects"` `onClick={onOpenCurrent}` puce = `Spinner taille="bouton"` (16 px, dans la puce `h-8`, comme lot 2 ; `Spinner` n'a pas 18 px : `ligne` 14, `bouton` 16, `zone` 24, `Spinner.tsx:17-24`) / `CheckCircle2` 18 px / `AlertCircle` 18 px selon `running` / `complete` / autre ; titre = `run.question` en `text-sm` ; detail = `run.phase \|\| run.status` ; `ChevronRight` 18 px muted |
| Lignes | bouton flex, reco + date `text-xs`, `truncate` | `Ligne domaine="prospects"` puce `History` 18 px, `onClick={() => onOpenDecision(id)}` ; titre = `decision.question` sans `truncate` ; `Ligne.detail` = `decision.recommendation` **seul** (le `p` de `Ligne.tsx:80` a ce textContent exact : le test `getByText(synthesis.recommendation)` de `BoardConversationCard.test.tsx:51-52` reste vert ; une concaténation `reco · date · mode` le casserait, matcher exact par défaut) ; `droite` = `<span className="text-sm text-text-muted">{formatDate(decision.created_at)} · {decision.mode === 'sovereign' ? 'Souverain' : 'Cloud'}</span>` (sans « Mode », scan d'une liste de 5 ; le canevas § 3.1 porte « Mode souverain » / « Mode cloud ») + `Etiquette ton={high → succes, medium → neutre, low → neutre, sinon neutre}>{confidenceLabel(decision.confidence)}</Etiquette>` (jamais `erreur` : un consensus faible est un accord entre avis, revue 30/08, `BoardConversationCard.tsx:64-70` « Consensus faible ») + `ChevronRight` 18 px. Date et mode restent dans la ligne (`droite`) **et** dans la meta du canevas § 3.1 |

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
| `h2` | « Délibération stratégique » / « Décision enregistrée » | « Décision » toujours (pas d'`id` aujourd'hui, on n'en invente pas) |
| Sous-titre | « Cinq regards… » | inchangé |

Ordre du corps, identique à `BoardWorkspaceCanvas.tsx:317-323` : 1) resource
loading ; 2) resource error ; 3) `showRun` ; 4) formulaire si `new-board` /
`current` ; 5) decision loading ; 6) decision error ; 7) `DecisionDetail`.

## 3. Question, statut, synthèse, avis

Ordre dans `BoardRunView` et `DecisionDetail`, de haut en bas : question
(§ 3.1), synthèse (§ 3.2 : carte pleine si elle existe, **placeholder** si
`run.status === 'running'` sans `run.synthesis`), avis (§ 3.3), divergences
(§ 3.4, seulement si une synthèse existe), extraits web, ligne d'usage
de la synthèse, bandeaux d'état (§ 5), pied d'actions. Extraits et usage
n'existent aujourd'hui que dans `DecisionDetail` (`BoardConversationCard.tsx:281-283`,
après `SynthesisView`) : ils restent là, mais **après** les divergences et
**avant** les bandeaux (absents du détail) et le pied. `BoardRunView` n'a
ni extraits ni usage : question → synthèse → avis → divergences → bandeaux
§ 5 → pied. La synthèse passe **au-dessus** des avis (critère « présentée
tôt ») ; les gestionnaires ne changent pas.

### 3.1 Question

`Carte as="section"`. `h3 className="text-xl font-bold leading-6"` = la
question (le label uppercase 12 px « Question soumise » / « Décision du … »
sort : la date va dans la meta). Meta `text-sm font-medium text-text-muted`,
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
    « Délibération partielle · N/5 avis » (N = nombre d'avis avec contenu
    non vide **ou** `isComplete`, **le même prédicat** que « au moins un
    avis rendu » et que l'affichage de l'étiquette ; pas `completed` seul :
    un avis interrompu avec du texte compte dans N, un avis vide coincé
    `isRunning: true` ne compte pas ; maquette `#statut-partiel`,
    `decision.html:63`, `ecrans.json` état `partiel`) ;
  - **`BoardRunView`**, sinon : pas d'étiquette de statut dans la meta
    (échec sans avis, `persistence_error`, `cancelled` : bandeaux § 5
    seulement) ;
- « Mode souverain » / « Mode cloud » (`run.mode` ou `decision.mode`) :
  le préfixe « Mode » est **uniquement** dans la meta du canevas (maquette
  `decision.html:63` « Mode souverain ») ; la ligne d'historique § 1 reste
  « Souverain » / « Cloud » sans « Mode » (scan, aujourd'hui
  `BoardConversationCard.tsx:130`) ;
- « 5 conseillers » ;
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
pas d'icône (v1 n'en demandait pas) ; titre en `h3` « Synthèse » (sans
classe : `@layer base` 1 rem) ; meta `p className="text-xs font-medium text-text-muted"`
« Ce que les cinq avis ont en commun, et ce qui les sépare » (chaîne
maquette `normal`, `decision.html:68`). L'état maquette `partiel` la
change (`decision.html` script l.96 : « Ce que les quatre avis rendus ont
en commun ; le Contradicteur n'a pas répondu ») : **on ne suit pas** ;
en `error` avec avis manquant, garder cette meta `normal` (pas de
synthèse provisoire sans API).

Trois montages, un seul `data-testid="board-synthesis"` :

1. **`run.status === 'running'` et pas de `run.synthesis`** (état maquette
   `encours`, `decision.html:75` `#attente`, script `:94`) : `Carte as="article"
   className="border-l-[3px] border-l-accent-fill"`, tête ci-dessus, corps
   `<p className="text-sm text-text-muted">Synthèse en préparation, elle arrive après le dernier avis.</p>`
   + deux `Squelette` `largeur="w-[80%]"` et `largeur="w-[60%]"` (comme
   `.attente .chargement`, `decision.html:31-32`). Pas un trou.
2. **`run.synthesis` ou `decision.synthesis` existe** : même `Carte as="article"
   className="border-l-[3px] border-l-accent-fill"`, même tête. Bloc
   recommandation : `bg-accent-tint rounded-sm p-3`,
   `<b className="text-accent">{synthesis.recommendation}</b>` (toute la
   reco, **sans** préfixe « Recommandation : »). Sous la reco :
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

Grille `grid grid-cols-1 sm:grid-cols-2 gap-3` (le panneau fait 620 px, pas
de 3e colonne). Cinq cartes dans `advisorOrder` pour le run ; pour le
détail, `decision.opinions` tel quel (on n'invente pas un avis manquant).
Chaque avis : `Carte as="section"` (le test Markdown fait `closest('section')`).
Tête : portrait `h-8 w-8 rounded-full` sans bordure ni ombre ; **pas de
`h4`** (sinon le `h3` « Où les avis divergent » § 3.4 vient après des
`h4` : même rupture d'ordre que h2 après h3, § 3.2 « ordre h2 → h3 → h2
interdit »). Nom = `strong className="block text-sm font-semibold"` =
`info.name` / `opinion.name` (détail actuel `BoardConversationCard.tsx:273`
déjà en `strong` ; maquette `decision.html:78` `<b>La Stratège</b>`, pas un
titre) ; meta `p className="text-sm text-text-muted"`
= `advisor.provider \|\| info.personality` (run) ou
`provider · modèle · coût` (détail, `formaterCout`, « provider inconnu » /
« modèle non mesuré » inchangés). Pastille lettre S/F/O/C hors lot.
Position Accepte / Refuse : P-0xy. Icônes de tête (run
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
| `run.status !== 'running'` et contenu vide (avis absent, `isRunning` coincé sans texte, ou `isComplete` sans texte) | `Etiquette ton="erreur"` « Avis non rendu » ; **jamais** le squelette ; **pas** de bouton « Redemander cet avis » (P-0xy) |

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
maquette `encours` masque `#divergences`, `decision.html:94`) :

- si `divergence_points.length > 0` : `h3 text-base` « Où les avis
  divergent », liste `text-sm` des points (plus dans la carte synthèse) ;
- si vide : le même `h3`, puis « Aucune divergence enregistrée. » inchangé.

Ce `h3` vient **après des non-titres** (noms d'avis en `strong` / `p`,
§ 3.3 ; maquette `decision.html:78` `<b>La Stratège</b>` puis l.86
`<h3>Où les avis divergent</h3>`), pas après des `h4` d'avis. Les `h4`
« Consensus » / « Prochaines étapes » restent **à l'intérieur** de
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
`border-accent bg-accent-tint`. Rangée des cinq portraits : grille
`grid-cols-5`, portraits index 1 à 5, `truncate` inchangés ; **ligne
« Conseillers réellement configurés » en `text-sm font-bold`** (aujourd'hui
`text-xs font-bold`, `BoardConversationCard.tsx:249`) ; **noms
`truncate text-sm text-text-muted`** (aujourd'hui `truncate text-xs`,
même ligne ; sans ces deux phrases le code recopie `text-xs` deux fois).
Confirmation
`data-testid="board-confirmation"` : textes exactement ceux d'aujourd'hui
(six appels, Ollama sans repli) ; `Button variant="ghost" size="md"` Annuler ;
`Button variant="primary" size="md"` « Confirmer et lancer ». Geste :
`Button variant="primary" size="md"` « Préparer la délibération », `Gavel`
18 px, même `requestConfirmation`.

## 5. Les états

L'`Etiquette` de statut vit **uniquement** dans la meta § 3.1. Cette section
ne porte plus que progressbar, phase, bandeaux, boutons.

| État | Aujourd'hui | Cible |
|---|---|---|
| historique, chargement | spinner + « Je consulte les décisions… » | même `div` grille que `SqueletteDeLigne` (`TodayDashboardCard.tsx:71-81`) : `div className="grid grid-cols-[2rem_1fr_auto] items-center gap-3 border-t border-border px-4 py-3"` + `Squelette largeur="w-8" classeBarre="h-8 rounded-sm"` + deux barres `largeur="w-[60%]"` / `largeur="w-[40%]"` ; trois rangées dans un `div aria-hidden="true"` (pas `Ligne` : `Ligne.tsx:26-35` n'a pas de rest props, `aria-hidden` ignoré / refusé par TS) ; puis le texte actuel en `role="status"` `px-4 py-3 text-sm text-text-muted` |
| historique, erreur | icône + « Historique indisponible » + message + Réessayer + Ouvrir | `Alerte data-testid="board-history-error"` `icone={AlertCircle 18 px}` titre « Historique indisponible », `children` = `resource.error`, `action` = `Button variant="secondary" size="md"` Réessayer ; « Ouvrir Décision » reste en tête (un seul Réessayer) |
| historique, vide | « Aucune décision enregistrée » + « Convoquer le Board » | `EtatVide data-testid="board-history-empty"` titre et texte actuels, `action` = `Button variant="primary" size="md"` « Convoquer le Board » |
| canevas, chargement resource / décision | spinner + « Chargement du Board… » / « Chargement de la décision… » | mêmes textes en `role="status"`, plus deux `Squelette` |
| canevas, erreur resource / décision | message + Réessayer | `Alerte` titre = le message actuel, `action` = `Button secondary md` Réessayer (`onRetry` / `onRetryDecision`) |
| run `running` | barre + phase + N/5 | pas d'`Etiquette` ici (meta § 3.1) ; barre visible `div.mt-2.h-1.5.overflow-hidden.rounded-full.bg-surface` `role="progressbar"` `aria-label="Progression de la délibération"` `aria-valuemin={0}` `aria-valuemax={5}` `aria-valuenow={completed}` `aria-valuetext={`${completed} conseiller${completed > 1 ? 's' : ''} sur 5 terminé${completed > 1 ? 's' : ''}`}` (mêmes `aria-*` qu'aujourd'hui, `BoardConversationCard.tsx:173` ; la maquette n'a pas de barre, l'écran actuel si) ; remplissage `h-full bg-domaine-prospects` `width: ${Math.max(4, completed / 5 * 100)}%` ; phase actuelle en `role="status"` `text-sm` ; bouton `Button variant="danger" size="md"` « Annuler la délibération » |
| run `running`, confirmation | `data-testid="board-cancel-confirmation"` | le même `div` (pas `Alerte` : ce n'est pas une erreur), textes conservés ; `Button secondary md` « Continuer en arrière-plan » ; `Button danger md` « Confirmer l'annulation » |
| run `complete` | bandeau vert + identifiant | pas d'`Etiquette` ici (meta § 3.1 « Décision enregistrée ») ; identifiant déjà dans la meta § 3.1 (`Identifiant : {run.decisionId}`) ; `Button variant="primary" size="md"` « Nouvelle question » `onReset` (pied commun, ci-dessous) |
| run `error` / `persistence_error` | bandeau `role="alert"` à deux `<p>` | `Alerte` titre = le gras actuel (« Sauvegarde non vérifiée. » / « Délibération incomplète. ») ; `children` = **un seul texte** (les deux phrases concaténées, espace au milieu) : `{run.error}` + « Les avis partiels restent visibles mais aucune conclusion ne doit être considérée comme sauvegardée. » (si `run.error` est vide, la seconde phrase seule). `Alerte` enveloppe `children` dans un seul `<p>` (`Alerte.tsx:38`) : deux `<p>` dans `children` = HTML invalide. Pas de Réessayer (aucun aujourd'hui). Cette `Alerte` n'est **pas** le statut : si `run.status === 'error'` et au moins un avis rendu, le statut est l'`Etiquette ton="attention"` § 3.1, l'`Alerte` se colle **sous** ; si zéro avis, pas d'étiquette, l'`Alerte` « Délibération incomplète. » reste seule. `persistence_error` : pas l'étiquette partielle (ce n'est pas un avis manquant), `Alerte` « Sauvegarde non vérifiée. » seule. Pied : `Button variant="primary" size="md"` « Nouvelle question » `onReset` (aujourd'hui `BoardConversationCard.tsx:185` : `running` ? Annuler : Nouvelle question, donc aussi sur erreur). Le canevas affiche `BoardRunView` tant que `status !== 'idle'` (`:312`) ; sous `xl`, le canevas est un calque `absolute` `max-w-[620px]` (`ConversationCanvasPrototype.tsx:333`, `xl:relative`) qui recouvre la carte (où le même geste existe encore) : sans ce bouton, plus aucun geste dans le panneau. |
| run `cancelled` | bandeau warning sans `role="alert"` | `div` (pas `Alerte`) `className="rounded-md border border-warning/40 bg-[var(--color-warning-tint)] p-3 text-sm text-warning"` (aujourd'hui `text-xs`, `BoardConversationCard.tsx:182`) ; texte inchangé : « Délibération annulée. Aucun résultat complet n'est présenté comme une décision. » ; `Button variant="primary" size="md"` « Nouvelle question » `onReset` (pied commun, ci-dessous) |

Un seul « Réessayer » par état : historique erreur, canevas resource
erreur, canevas décision erreur. Zéro ailleurs.

`Button variant="primary" size="md"` « Nouvelle question » `onReset` sur
tout run dont `status !== 'running'` (`complete`, `cancelled`, `error` et
`persistence_error` compris), pas seulement `complete` et `cancelled`.

## 6. Gardes mécaniques et tests à aligner

Nouveaux (`BoardConversationCard.da.test.tsx`, rouges d'abord) :

1. une ligne d'historique = un seul `button`, grille `2rem 1fr auto`, le
   badge porte `data-etiquette` ; `detail` est exactement
   `decision.recommendation` (pas une concaténation) ; `droite` contient
   `formatDate(decision.created_at)` · « Souverain » ou « Cloud » (sans
   « Mode ») puis l'`Etiquette` ; `ton` du consensus `low` / `medium` n'est
   pas `erreur` ; le run en cours porte `data-testid="board-current-run"`
   sur le `div` enveloppe, pas sur `Ligne` ;
2. la synthèse (`board-synthesis`) précède la première carte d'avis dans
   le DOM, en run `complete` avec synthèse, en `DecisionDetail`, **et** en
   run `running` sans synthèse (placeholder « Synthèse en préparation, elle
   arrive après le dernier avis. ») ; pas de `h2` « Synthèse » dans le
   canevas (tête en `h3`) ; extraits et usage, s'ils existent, viennent
   après les divergences et avant les bandeaux § 5 ;
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
   cours · 2/5 avis » pour `completed === 2` (run `running`) ; « Délibération
   partielle · 4/5 avis » pour `run.status === 'error'` et 4 avis avec
   contenu non vide ou `isComplete` (N = ce prédicat, pas `completed` seul :
   un 5e avis interrompu avec du texte fait 5/5) ; titres
   d'erreur de run inchangés ; meta de synthèse = « Ce que les cinq avis
   ont en commun, et ce qui les sépare » (pas la variante `partiel`) ;
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
   portraits `truncate text-sm text-text-muted`.

À aligner dans le même commit, forme seulement :
`aucuneCouleurEnDur.test.ts` (ajouter `BoardConversationCard.tsx` aux
sources, l'ombre `rgba` disparaît). `BoardConversationCard.test.tsx` ne
change pas de chaînes (reco, consensus, extraits, confirmation, plafond 30,
Markdown `closest('section')` : `Carte as="section"`). Aucune assertion de
comportement n'est retirée.

## 7. Ce que ce lot ne fait pas

- Page pleine 66 rem, fil d'Ariane « Décisions › Décision du … », durée,
  « Contexte lu : contact, 2 devis, agenda » : le canevas reste le panneau
  620 px. Fonctionnalité : **P-080** (numéro à attribuer par l'orchestrateur).
- « Copier », « Créer les tâches », « Exporter en Markdown », « Poser une
  autre question » (on garde « Nouvelle question »), « modifiable tant
  qu'aucune tâche n'est créée » : **P-081**.
- « Redemander cet avis », positions Accepte / Refuse / sous condition,
  renommage des cinq conseillers : **P-0xy**.
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
   étiquette « Délibération partielle · 4/5 avis », le 5e « Avis non
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
   anneau 3 px sur une ligne, établi visible, composeur non recouvert.
4. Revue Grok du diff avant le tag, `/release-therese 0.72.0-alpha` avec le
   GO de Ludo (toute la DA, pas ce lot seul).

## Points non repris

Aucun de la v3. Les 6 points de `.cartography-work/reviews/grok-da-lot7-decision-design-v3.log` (1 P1, 1 P2, 4 P3) sont repris ci-dessus. Les 9 points de `.cartography-work/reviews/grok-da-lot7-decision-design-v2.log` (2 P1, 2 P2, 5 P3) et les 20 points de `.cartography-work/reviews/grok-da-lot7-decision-design-v1.log` (4 P1, 10 P2, 6 P3) restent repris.
