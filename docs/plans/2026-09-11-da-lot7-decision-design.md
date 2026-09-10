# DA « Application affinée », lot 7 : l'écran Décision (Board) (design à challenger avant le code)

Version 1, 11/09/2026. Précédent : lot 3 (Tiroir), livré sur `main` ;
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
   hotfix 0.48.1). La maquette est une page à 66 rem : page pleine = P-0xz.
3. Les cinq noms officiels restent (L'Analyste, Le Stratège, L'Avocat du
   Diable, Le Pragmatique, Le Visionnaire). Les noms maquette (Financier,
   Opérationnel, Voix du client, Contradicteur) sont P-0xy.
4. Les portraits (`CharacterPortrait` index 1 à 5) restent l'avatar de
   chaque conseiller (le glyphe lettre de la maquette est un bouche-trou).
5. La formulation de la maquette remplace les mentions techniques là où
   l'état est le même (tête du canevas, statut enregistré / en cours,
   « Réfléchit… »). Les états sans équivalent maquetté (erreur de flux,
   sauvegarde non vérifiée, annulée, formulaire, historique vide / erreur)
   gardent leur prose.
6. Toute taille de bouton est `md` (36 px) ou `icon` (36 px) ; `sm` n'y
   est pas employé. « Préparer la délibération » est le grand geste, en
   `lg` (44 px).
7. Le radiogroup Cloud / Souverain (roving, descriptions) reste un
   `radiogroup` ; `Segments` n'est pas monté ici.

## 1. La carte d'historique : `BoardHistoryCard`

Maquette : pas de liste (elle ouvre déjà une décision). On habille la carte
du scénario `board` (entrée), comme le brief du lot 2.

| Élément | Aujourd'hui | Cible |
|---|---|---|
| Cadre | `section` ombre `rgba`, `data-testid="board-history-card"` | `Carte as="section"` `aria-labelledby="board-history-title"` même testid ; `shadow-sm` |
| Tête | portrait index 1 + `h2` « Décision » + meta | `CarteTete idTitre="board-history-title"` icône `Gavel` 18 px, titre « Décision » ; meta inchangée : chargement « Lecture de l'historique local » ; `ready` → `libelleDecisionsChargees(n)` (`n >= 30` : « n décisions chargées (total non mesuré) » ; sinon « n décision(s) enregistrée(s) », pluriel `n > 1`) |
| Actions | boutons maison « Nouvelle question » + `BoutonOuvrirLaVue` | `Button variant="primary" size="md"` « Nouvelle question », `Plus` 18 px, même `onNewBoard` ; `BoutonOuvrirLaVue vue="board"` avec `className` local qui reproduit `Button secondary md` (lot 2), libellé « Ouvrir Décision » inchangé |
| Run en cours | bouton `data-testid="board-current-run"`, titre `text-xs` | enveloppe le même testid ; `Ligne domaine="prospects"` `onClick={onOpenCurrent}` puce = `Spinner` / `CheckCircle2` / `AlertCircle` 18 px selon `running` / `complete` / autre ; titre = `run.question` en `text-sm` ; detail = `run.phase \|\| run.status` ; `ChevronRight` 18 px muted |
| Lignes | bouton flex, reco + date `text-xs`, `truncate` | `Ligne domaine="prospects"` puce `History` 18 px, `onClick={() => onOpenDecision(id)}` ; titre = `decision.question` sans `truncate` ; detail = `decision.recommendation` en `text-sm` sans `truncate` ; `droite` = `Etiquette ton={high → succes, medium → attention, low → erreur, sinon neutre}>{confidenceLabel}</Etiquette>` + `ChevronRight` 18 px. Date et mode restent dans le détail du canevas, ils quittent la ligne (la reco doit rester visible : test « affiche l'historique réel ») |

## 2. Le canevas : `BoardWorkspaceCanvas`

Panneau inchangé (largeur, fermer, `role="region"`). Pied : `BoutonOuvrirLaVue`
comme en tête de carte (même className).

| Élément | Aujourd'hui | Cible |
|---|---|---|
| Sur-titre | « Board réel » uppercase 12 px | retiré (mention technique) |
| `h2` | « Délibération stratégique » / « Décision enregistrée » | « Décision » toujours (pas d'`id` aujourd'hui, on n'en invente pas) |
| Sous-titre | « Cinq regards… » | inchangé |

Ordre du corps, identique à `BoardWorkspaceCanvas.tsx:317-323` : 1) resource
loading ; 2) resource error ; 3) `showRun` ; 4) formulaire si `new-board` /
`current` ; 5) decision loading ; 6) decision error ; 7) `DecisionDetail`.

## 3. Question, statut, synthèse, avis

Ordre dans `BoardRunView` et `DecisionDetail`, de haut en bas : question
(§ 3.1), synthèse si elle existe (§ 3.2), avis (§ 3.3), divergences (§ 3.4),
bandeaux d'état (§ 5), pied d'actions. La synthèse passe **au-dessus** des
avis (critère « présentée tôt ») ; les gestionnaires ne changent pas.

### 3.1 Question

`Carte as="section"`. `h3 className="text-xl font-bold leading-6"` = la
question (le label uppercase 12 px « Question soumise » / « Décision du … »
sort : la date va dans la meta). Meta `text-sm font-medium text-text-muted`,
segments séparés par « · » :

- `Etiquette` de statut (un seul, selon l'état, § 5) ;
- « Mode souverain » / « Mode cloud » (`run.mode` ou `decision.mode`) ;
- « 5 conseillers » ;
- en `DecisionDetail` seulement : `formatDate(created_at)` (helper actuel,
  « Date inconnue » inchangé) ;
- `decision.context` / `run.context` inchangé, sous la meta, `text-sm`.

Pas de durée, pas de « Contexte lu : contact, 2 devis » (P-0xz).

### 3.2 Synthèse (`data-testid="board-synthesis"` conservé)

`Carte as="article" className="border-l-[3px] border-l-accent-fill"`.
`CarteTete` titre « Synthèse », meta « Ce que les avis ont en commun, et ce
qui les sépare » (forme ; les points viennent toujours de
`consensus_points`). Bloc recommandation : `bg-accent-tint rounded-sm p-3`,
`<b className="text-accent">` puis `synthesis.recommendation` (pas de préfixe
inventé). Consensus : liste `text-sm`, `CheckCircle2` 18 px `text-success`,
rôle visuel seulement. Prochaines étapes : `ol` numérotée `text-sm`, mêmes
`next_steps`. Pas de bouton Copier ni « Créer les tâches » (P-0xx).
`CompactMarkdown` n'est pas monté sur la synthèse (aujourd'hui du texte
brut) : inchangé.

### 3.3 Avis

Grille `grid grid-cols-1 sm:grid-cols-2 gap-3` (le panneau fait 620 px, pas
de 3e colonne). Cinq cartes dans `advisorOrder` pour le run ; pour le
détail, `decision.opinions` tel quel (on n'invente pas un avis manquant).
Chaque avis : `Carte as="section"` (le test Markdown fait `closest('section')`).
Tête : portrait `h-8 w-8 rounded-full` sans bordure ni ombre ; `h4 text-sm
font-semibold` = `info.name` / `opinion.name` ; meta `text-sm text-text-muted`
= `advisor.provider \|\| info.personality` (run) ou
`provider · modèle · coût` (détail, `formaterCout`, « provider inconnu » /
« modèle non mesuré » inchangés). Pastille lettre S/F/O/C hors lot.
Position Accepte / Refuse : P-0xy ; à la place, l'état visuel actuel :

| État de l'avis | Cible |
|---|---|
| `isRunning` avec contenu | texte `whitespace-pre-wrap text-sm` + curseur pulse (streaming, pas de Markdown) |
| `isRunning` sans contenu | `Etiquette ton="neutre"` « Réfléchit… » + deux `Squelette` `largeur="w-[80%]"` et `w-[60%]` |
| attente (pas encore dans `run.advisors`) | même squelette, sans étiquette « Réfléchit… » |
| `isComplete` avec contenu | `CompactMarkdown className="mt-3 text-sm leading-6"` |
| terminé ou en erreur, sans contenu | `Etiquette ton="erreur"` « Avis non rendu » ; **pas** de bouton « Redemander cet avis » (P-0xy) |

### 3.4 Divergences

Après la grille, si `divergence_points.length > 0` : `h3 text-base` « Où
les avis divergent », liste `text-sm` des points (plus dans la carte
synthèse). Si vide : « Aucune divergence enregistrée. » inchangé, sous le
même `h3`. Extraits web et ligne d'usage de la synthèse : cartes `text-sm`,
libellés exacts conservés (« Extraits du moteur de recherche »).

## 4. Le formulaire (`data-testid="board-new-form"`)

`fieldset` `data-testid="board-form-fields"` et le gel `disabled` inchangés.
`FormField htmlFor="board-question"` label « Question stratégique » +
`Textarea id="board-question"` mêmes `aria-label`, `aria-invalid`,
`aria-describedby`, placeholder, `h-28`. Contexte : `FormField` « Contexte
utile, facultatif » + `Textarea aria-label="Contexte du Board"` (conservé).
Erreur : `p#board-form-error` `role="alert"` `text-sm` inchangé (pas le
`text-xs` de `FormField.error`). Mode : même `radiogroup`
`aria-labelledby="board-mode-label"`, roving, deux radios ; cartes
`rounded-md border p-3 text-left text-sm`, actif
`border-accent bg-accent-tint`. Rangée des cinq portraits inchangée (noms
réels, `text-sm`). Confirmation `data-testid="board-confirmation"` : textes
exactement ceux d'aujourd'hui (six appels, Ollama sans repli) ;
`Button variant="ghost" size="md"` Annuler ;
`Button variant="primary" size="md"` « Confirmer et lancer ». Geste :
`Button variant="primary" size="lg"` « Préparer la délibération », `Gavel`
18 px, même `requestConfirmation`.

## 5. Les états

| État | Aujourd'hui | Cible |
|---|---|---|
| historique, chargement | spinner + « Je consulte les décisions… » | trois rangées façon `Ligne` `aria-hidden` (puce `Squelette classeBarre="h-8 rounded-sm" largeur="w-8"`, deux barres 60 % / 40 %), puis le texte actuel en `role="status"` `px-4 py-3 text-sm text-text-muted` |
| historique, erreur | icône + « Historique indisponible » + message + Réessayer + Ouvrir | `Alerte data-testid="board-history-error"` `icone={AlertCircle 18 px}` titre « Historique indisponible », `children` = `resource.error`, `action` = `Button variant="secondary" size="md"` Réessayer ; « Ouvrir Décision » reste en tête (un seul Réessayer) |
| historique, vide | « Aucune décision enregistrée » + « Convoquer le Board » | `EtatVide data-testid="board-history-empty"` titre et texte actuels, `action` = `Button variant="primary" size="md"` « Convoquer le Board » |
| canevas, chargement resource / décision | spinner + « Chargement du Board… » / « Chargement de la décision… » | mêmes textes en `role="status"`, plus deux `Squelette` |
| canevas, erreur resource / décision | message + Réessayer | `Alerte` titre = le message actuel, `action` = `Button secondary md` Réessayer (`onRetry` / `onRetryDecision`) |
| run `running` | barre + phase + N/5 | `Etiquette ton="info"` « Délibération en cours · N/5 avis » (N = `completed`) ; `role="progressbar"` conservé, mêmes `aria-*`, `aria-valuetext` pluriel `completed > 1` ; phase actuelle en `role="status"` `text-sm` ; bouton `Button variant="danger" size="md"` « Annuler la délibération » |
| run `running`, confirmation | `data-testid="board-cancel-confirmation"` | le même `div` (pas `Alerte` : ce n'est pas une erreur), textes conservés ; `Button secondary md` « Continuer en arrière-plan » ; `Button danger md` « Confirmer l'annulation » |
| run `complete` | bandeau vert + identifiant | `Etiquette ton="succes"` « Décision enregistrée » ; identifiant en meta `text-sm` s'il existe ; `Button primary md` « Nouvelle question » |
| run `error` / `persistence_error` | bandeau `role="alert"` | `Alerte` titres exacts « Sauvegarde non vérifiée. » / « Délibération incomplète. », `children` = `run.error` + la phrase actuelle sur les avis partiels ; pas de Réessayer (aucun aujourd'hui) |
| run `cancelled` | bandeau warning sans `role="alert"` | inchangé sémantiquement : `div` (pas `Alerte`) + texte actuel ; `Button primary md` « Nouvelle question » |

Un seul « Réessayer » par état : historique erreur, canevas resource
erreur, canevas décision erreur. Zéro ailleurs.

## 6. Gardes mécaniques et tests à aligner

Nouveaux (`BoardConversationCard.da.test.tsx`, rouges d'abord) :

1. une ligne d'historique = un seul `button`, grille `2rem 1fr auto`, le
   badge porte `data-etiquette` ;
2. la synthèse (`board-synthesis`) précède la première carte d'avis dans
   le DOM, en run `complete` avec synthèse **et** en `DecisionDetail` ;
3. « Réfléchit… » seulement sur un avis `isRunning` sans contenu ; « Avis
   non rendu » sans bouton « Redemander » ; `CompactMarkdown` sur un avis
   complet (pas de `###`) ;
4. statut : « Décision enregistrée » en `complete` / détail ; « Délibération
   en cours · 2/5 avis » pour `completed === 2` ; titres d'erreur de run
   inchangés ;
5. un seul « Réessayer » sur historique erreur, canevas resource erreur,
   canevas décision erreur ; zéro sur vide, chargement, run `complete`,
   run `error` ;
6. tête du canevas : plus de « Board réel », `h2` « Décision » ;
7. aucune classe `text-xs` sur un interactif **ni dans son sous-arbre**
   (carte + canevas) ; aucune couleur en dur dans `BoardConversationCard.tsx` ;
8. primitives : `CarteTete` pose `idTitre` sur l'historique ; `Alerte` /
   `EtatVide` transmettent les testid et rendent `action`.

À aligner dans le même commit, forme seulement :
`aucuneCouleurEnDur.test.ts` (ajouter `BoardConversationCard.tsx` aux
sources, l'ombre `rgba` disparaît). `BoardConversationCard.test.tsx` ne
change pas de chaînes (reco, consensus, extraits, confirmation, plafond 30,
Markdown `closest('section')` : `Carte as="section"`). Aucune assertion de
comportement n'est retirée.

## 7. Ce que ce lot ne fait pas

- Page pleine 66 rem, fil d'Ariane « Décisions › Décision du … », durée,
  « Contexte lu : contact, 2 devis, agenda » : le canevas reste le panneau
  620 px. Fonctionnalité : **P-0xz** (numéro à attribuer par l'orchestrateur).
- « Copier », « Créer les tâches », « Exporter en Markdown », « Poser une
  autre question » (on garde « Nouvelle question »), « modifiable tant
  qu'aucune tâche n'est créée » : **P-0xx**.
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
   délibération 2/5 avec squelettes (encours) ; quatre avis + un vide
   (partiel / erreur de run) ; historique vide ; historique en panne ;
   chargement lent. Largeurs 1280, 1024, 840, 800 px ; clair, sombre,
   contraste élevé ; trois tailles de police. Captures
   `.cartography-work/validation/da-lot7/`, rapport
   `docs/da/2026-09-11-lot7-recette.md`. Vérifier : synthèse au-dessus des
   avis, Markdown rendu, étiquette de statut, un seul Réessayer, anneau 3 px
   sur une ligne, établi visible, composeur non recouvert.
4. Revue Grok du diff avant le tag, `/release-therese 0.72.0-alpha` avec le
   GO de Ludo (toute la DA, pas ce lot seul).
