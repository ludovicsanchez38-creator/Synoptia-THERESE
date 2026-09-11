# DA « Application affinée », lot 9 : l'écran Paramètres (design à challenger avant le code)

Version 4, 11/09/2026 09:52, après la revue de la v3 (23 points repris, 0 non repris) ; journal `.cartography-work/reviews/opus-da-lot9-parametres-design-v3.log`.
Précédent : lot 3 (Tiroir), sur `main` ; cadence : une
seule release pour toute la DA (décision Ludo 11/09, 0.72.0-alpha porte
l'ensemble). Maquette :
`docs/da/2026-09-05-propositions/maquettes/parametres.html` (états `normal`,
`profil`, `invalide`), critères de `ecrans.json` : « Neuf rubriques, clé de
service visible sans la dévoiler, coûts en dollars annoncés. Rubriques et
fonctions avancées préservées ; service configuré, clé masquée, clé invalide
et service indisponible distingués. » Déjà décidé côté UX, pas à rejuger :
P-009 récapitulatif après refus de clé ; P-012 clé vérifiée avant
« configurée » ; P-018 fournisseurs déjà munis d'une clé visibles ; BUG-156
(pas de fermeture au clic sur le fond) ; BUG-159 (rubriques masquées nommées
en mode standard) ; B-201 (refus de clé porté par `role="alert"`) ; B-526
(un interrupteur de visibilité par champ de clé) ; coûts affichés en dollars
(`UNITE_COUT`, 0.48.1).

## Ce que le lot change, en une phrase

La modale `SettingsModal.tsx` (ouverte par `usePanelStore().openSettings()`),
la rubrique Service d'IA (`LLMTab.tsx`, y compris `EffortSelector`) et la
rubrique Profil (`ProfileTab.tsx`, y compris `DemoModeSection`) prennent la
forme de la maquette en consommant les primitives du lot 1 (`Carte`,
`CarteTete`, `Etiquette`, `Alerte`, `Squelette`, `Button`, `Input`, `Select`,
`Textarea`, `FormField`) ; les mêmes données, les mêmes états, les mêmes
destinations. Aucun appel réseau, aucun store, aucun parcours ne change.

Ce lot touche **trois** primitives, pas une (revue v3, point 16) :

1. `Alerte.ton` passe de `'erreur'` à `'erreur' | 'attention'` (le warning de
   lecture partielle ne doit pas se teinter en erreur) ;
2. `CarteTete` reçoit `niveau?: 'h2' | 'h3'` (défaut `'h2'` ; aujourd'hui
   Carte.tsx:52 pose un `<h2>` figé, or les cartes clé / modèle sont des `h3`
   sous le `h2` de section, parametres.html:82) ;
3. `FormField` passe sa `description` **et** son message d'erreur de
   `text-xs` à `text-sm` (FormField.tsx:65 et 76) : ces deux textes sont
   rattachés au champ par `aria-describedby` (FormField.tsx:37-48), donc liés
   à un interactif, et la règle du lot bannit `text-xs` là (§ 4, rangée
   Effort ; garde 7). `FormField` n'a aujourd'hui **aucun** consommateur hors
   `ui/index.ts` (vérifié : `grep -rl FormField src/frontend/src` ne rend que
   `FormField.tsx` et `index.ts`), ce lot est son premier ; le seul test à
   aligner est `FormField.test.tsx:95-96`, sur la classe, pas sur le
   comportement.

Le composant `Carte` lui-même ne bouge pas ; seule `CarteTete` gagne `niveau`.

## Décisions tranchées par défaut (Ludo peut corriger)

1. Les Paramètres restent une **modale** (`role="dialog"` `aria-modal="true"`
   `data-testid="settings-modal"`) : la maquette en page est P-084. Overlay,
   piège de focus, Échap, BUG-156 inchangés.
2. Les neuf `id` de `ALL_TABS` restent ; seuls les libellés visibles des six
   rubriques du mode standard suivent la maquette. Outils, Agents, Avancé
   restent contributeur, nommés par BUG-159. Pas de 10e destination.
3. La liste `FOURNISSEURS` (14 ids, Anthropic en tête, Ollama en queue) reste
   entière et dans cet ordre, en grille 2 colonnes (`grid-cols-2`, comme
   `.fournisseurs` de la maquette, **sans** césure à 840 px), `role="group"`
   `aria-label="Choix du service d'IA"`. Chaque carte = `button type="button"`
   `aria-pressed` (maquette `role="button"` `aria-pressed`, parametres.html:74),
   **pas** `role="radio"` : `setLLMConfig` est un POST, la flèche ne doit pas
   persister, donc le motif APG radio n'est pas tenu. **Doctrine `Segments`,
   entière** : `role="group"` nommé + `aria-pressed` + `tabIndex` naturel
   (aucun `tabIndex={-1}`, aucun `tabIndex={0}` calculé) + **aucune** gestion
   de flèches, Home ou End (`Segments.tsx:3-6` : « Pas de tablist : sans
   onglets, sans roving, sans flèches, un tablist mentirait au lecteur
   d'écran […] role="group" nommé + aria-pressed » ; `Segments.tsx:34-42` ne
   pose ni `tabIndex` ni `onKeyDown`). Aucune règle du dépôt n'impose un rôle
   composite ici : `docs/rules/RULES-DESIGN.md` ne contient ni « roving », ni
   « radiogroup », ni « toolbar ». Ce choix ferme aussi le défaut préexistant
   de `LLMTab.tsx:191,194` : aujourd'hui le roving met `tabIndex={-1}` sur les
   13 cartes non courantes, donc si Ollama est le fournisseur courant **et**
   indisponible il est `disabled` et **plus aucune** carte n'est atteignable
   au clavier. Avec le `tabIndex` naturel, une carte `disabled` est la seule
   que le clavier saute ; les 13 autres restent atteignables. `LLMTab`
   n'importe donc plus `handleRovingFocus` ; le helper et son `click()` ne
   changent pas pour ses autres appelants (`AccessibilityTab`, `ServicesTab`,
   `CRMPanel`, `BoardConversationCard`). Pas de carte « Autres + 6 »
   (P-085, P-018).
4. Les noms du catalogue (`provider.name`) restent. Les formulations de la
   maquette remplacent la prose là où l'état est le même (étiquettes de clé,
   tête, vide Ollama). Un état sans équivalent maquetté garde ses mots
   (clé corrompue, Qwen, effort + outils, mode démo, THERESE.md).
5. Toute taille de bouton est `md` (36 px) ou `icon` (36 px) ; `sm` n'y est
   pas employé. « Enregistrer » du profil est le geste principal, en `md`
   (déjà au pied, `data-testid="settings-save-btn"`), pas en `lg`.
6. P-012 (tester la clé, quatre derniers caractères, date de vérification)
   reste au portail : ce lot n'ajoute aucun appel ni champ. On cesse d'écrire
   « configurée » pour une clé seulement stockée.

## 1. La coque : `SettingsModal`

Maquette `.reglages` : grille `15rem 1fr`, gap `--espace-4` ; sous 1024 px,
une colonne, rubriques en 3 colonnes.

| Élément | Aujourd'hui | Cible |
|---|---|---|
| Cadre | `max-w-3xl` `shadow-2xl` `rounded-md` `bg-surface` | `max-w-6xl` (72 rem, `.colonne` de la maquette), `shadow-lg`, mêmes `role` / `aria-label` / testid / `data-active-tab` / `data-requested-tab` ; overlay `data-dialog-backdrop` `bg-black/60` conservé (motif de `DialogShell`, pas un jeton nouveau) |
| Tête | `<h2 className="text-lg">Paramètres` + fermer | `<h1 id="settings-title">Paramètres</h1>` (registre : `@layer base` pose déjà `font-family: var(--font-family-display)`, `src/frontend/src/styles/globals.css:608-614` ; **pas** `className="font-editorial"`, la maquette est un `h1` sans `.editorial`, `parametres.html:56`, `base.css:48-49`) ; le dialogue passe `aria-labelledby="settings-title"` et **garde** `aria-label="Paramètres"` (filet) ; `Button variant="ghost" size="icon"` `data-testid="settings-close-btn"` `aria-label="Fermer les paramètres"` |
| Corps | `<div className="flex min-h-0 flex-1 flex-col overflow-hidden sm:flex-row">` (SettingsModal.tsx:784) | `flex min-h-0 flex-1 flex-col overflow-hidden min-[1024px]:flex-row` : **la césure du corps passe de 640 à 1024 px**, sinon entre 640 et 1023 px la nav en grille de 3 colonnes occupe toute la largeur d'une rangée flex et le panneau tombe à zéro (maquette `parametres.html:30` : `.reglages{grid-template-columns:1fr}` sous 1024 px, nav au-dessus) |
| Nav | `role="tablist"` `aria-label="Rubriques des paramètres"` `flex w-full shrink-0 items-stretch gap-1 overflow-x-auto border-b border-border/30 bg-background/30 p-2 sm:block sm:w-44 sm:overflow-y-auto sm:border-b-0 sm:border-r sm:py-2` (SettingsModal.tsx:786) | mêmes rôle, nom, ids `settings-tab-${id}`, `aria-selected` / `aria-controls` / roving (flèches, Home, End : ici le `tablist` **garde** son roving, c'est le motif APG des onglets ; seule la grille des fournisseurs y renonce, décision 3) ; **aucune** variante `sm:` ne survit, les six passent en `min-[1024px]:` une par une : `w-full min-[1024px]:w-60`, `max-[1023px]:grid max-[1023px]:grid-cols-3 min-[1024px]:block`, `min-[1024px]:overflow-y-auto`, `border-b border-border/30 min-[1024px]:border-b-0`, `min-[1024px]:border-r`, `p-2 min-[1024px]:py-2` (laisser un seul `sm:` fait se croiser les bordures entre 640 et 1023 px : `sm:border-b-0` couperait la bordure basse alors que la nav est encore au-dessus du panneau) ; le premier enfant (bloc Contributeur + `settings-hidden-tabs`, SettingsModal.tsx:787-815) porte `max-[1023px]:col-span-3` et ses cinq `sm:` (`sm:mb-2 sm:min-w-0 sm:border-b sm:border-r-0 sm:px-4 sm:py-3`, SettingsModal.tsx:788) passent eux aussi en `min-[1024px]:` : à 800 px la grille 3 colonnes ne porte que les `role="tab"` ; sans ça le toggle occupe une cellule ; courant : `aria-selected` `bg-accent-tint text-accent font-semibold` (plus de `border-r-2 border-accent-cyan`) ; inactif : `text-text-muted hover:bg-surface-2 hover:text-text` ; `min-h-9 px-3 text-sm` ; icône Lucide 18 px |
| Libellés | Profil, IA, Services, Accessibilité, Outils, Agents, Confidentialité, Avancé, À propos | Profil ; **Service d'IA** ; **Services et connecteurs** ; **Accessibilité et affichage** ; Outils ; Agents ; **Sécurité et confidentialité** ; Avancé ; **À propos et mise à jour** |
| Mode contributeur | interrupteur 20 px, libellé `text-xs` | interrupteur `w-10 h-6` (`role` natif du `input` `data-testid="ux-mode-toggle"`) dans un `<label>` qui ne contient **que** l'interrupteur et le libellé `text-sm font-medium` « Mode Contributeur » ; l'aide `text-xs text-text-muted` « Fonctions avancées » est un `<p>` **hors** du `label` (garde 7 : pas de `text-xs` dans le sous-arbre d'un interactif) ; `settings-hidden-tabs` inchangé (« Masquées ici : Outils, Agents, Avancé. ») |
| Pied | Fermer ghost + Enregistrer primary (onglet profil) | `Button variant="ghost" size="md"` Fermer ; `Button variant="primary" size="md"` `data-testid="settings-save-btn"` : « Enregistrement... » / « Enregistrer », mêmes `disabled` |

## 2. Alertes et chargement de la coque

Si `loading` : le corps de la rubrique est remplacé par **six** `Squelette` +
`role="status"` « Lecture des réglages… » ; `error` et `operationStatus` sont
**masqués** (`loadSettings` ne vide pas `error` au début,
SettingsModal.tsx:176-177, un refus précédent resterait à l'écran).
Hors chargement, ordre dans le `tabpanel` : alertes de coque, puis le contenu
de la rubrique.

**`loadWarnings`, lui, n'est pas masqué pendant `loading`** (revue v3, point
12). La v3 le masquait, et « Réessayer le chargement » se démontait donc sous
le doigt qui venait de le cliquer : le focus retombait sur `body`. Trois
règles, toutes à coder, aucune laissée au codeur :

1. `loadSettings` **ne vide plus** `loadWarnings` au début : la ligne
   `setLoadWarnings([])` de SettingsModal.tsx:178 est retirée. La liste est de
   toute façon remplacée à chaque retour de lecture par
   `setLoadWarnings(unavailable)` (SettingsModal.tsx:199), placé **avant** le
   `try` (:212) : aucun chemin ne la laisse périmée. Tant que la relecture
   court, l'écran continue donc d'annoncer l'état connu, et le `role="status"`
   dit qu'une relecture est en cours.
2. Le bouton « Réessayer le chargement » porte `aria-disabled={loading}`,
   **jamais** `disabled` : un `disabled` posé sur l'élément qui a le focus le
   renvoie au `body`, exactement le défaut qu'on répare. Son `onClick` sort
   immédiatement si `loading` est vrai. `Button` ne peint que l'attribut
   `disabled` (`Button.tsx:24`, `disabled:opacity-50
   disabled:cursor-not-allowed`) et ne connaît pas `aria-disabled` : le
   bouton porte donc en propre
   `className="aria-disabled:opacity-50 aria-disabled:cursor-wait"`, sans
   quoi il resterait visuellement actif pendant la relecture.
3. Si la relecture **réussit**, `loadWarnings` devient `[]` et le bandeau
   disparaît pour de bon : le focus serait perdu de la même façon. Le
   `onClick` doit donc déplacer le focus sur le `tabpanel`
   (`SettingsModal.tsx:845-849`, déjà `tabIndex={0}` et
   `id="settings-panel-${activeTab}"`), atteint par un `ref`. Cible stable,
   déjà focalisable, aucune primitive nouvelle. **Attention au piège de
   fermeture** : `if (loadWarnings.length === 0)` dans le `onClick` lirait la
   valeur du rendu où le bouton a été monté, donc **non vide** par
   construction (sans quoi le bouton n'existerait pas), et la condition
   serait toujours fausse. `loadSettings` **retourne** donc la liste qu'elle
   vient de poser : elle est déjà `async` et calcule `unavailable` en
   `SettingsModal.tsx:196-198`, il suffit d'ajouter `return unavailable;`
   après `setLoadWarnings(unavailable)` (:199) et de typer
   `Promise<string[]>`. Le handler s'écrit alors
   `const restants = await loadSettings(); if (restants.length === 0)
   panneauRef.current?.focus();`. Les autres appelants de `loadSettings`
   (effet d'ouverture, autres Réessayer) ignorent la valeur de retour, rien
   ne change pour eux.

Extension de primitive, testée (`Alerte.tsx`, `Alerte.test.tsx`) : `ton?:
'erreur' | 'attention'` (défaut `'erreur'`). `'erreur'` inchangé
(`bg-[var(--color-error-tint)] border-error/30`, titre `text-error`).
`'attention'` : `bg-[var(--color-warning-tint)] border-warning/30`, titre
`text-warning`. `role="alert"` dans les deux cas. Lot 2 a déjà ajouté
`action` et l'étalement des attributs ; ce lot n'y touche pas.

| État | Aujourd'hui | Cible |
|---|---|---|
| chargement | `Spinner taille="zone"` centré | **six** `Squelette` (`largeur="w-full"` `classeBarre="h-16 rounded-sm"`) `aria-hidden` en grille `grid-cols-2 gap-2.5` : trois rangées de deux, **pas** six rangées (12 barres) ; puis `role="status"` `text-sm text-text-muted` « Lecture des réglages… » ; **rien d'autre, sauf** le bandeau `loadWarnings` s'il est non vide (voir les trois règles ci-dessus) |
| lecture partielle (`loadWarnings`) | bandeau maison `settings-load-warning` `bg-[var(--color-warning-tint)]` | `Alerte ton="attention"` `data-testid="settings-load-warning"` `icone={<AlertCircle className="h-[18px] w-[18px]" />}` ; `titre` : 1 warning → « Ce réglage n’a pas pu être lu : {liste}. » ; N > 1 → « Ces réglages n’ont pas pu être lus : {liste}. » (liste dans le titre, comme aujourd'hui, SettingsModal.tsx:858-859) ; `children` = « Les valeurs affichées ici sont des valeurs par défaut, pas ta configuration réelle. » (**pas** un `children` qui commence par « : {liste} » : `Alerte` enveloppe déjà `children` dans un `<p>` sous le `titre`, Alerte.tsx:37-38) ; `action` = `Button variant="secondary" size="md"` « Réessayer le chargement », `aria-disabled={loading}` + `className="aria-disabled:opacity-50 aria-disabled:cursor-wait"`, `onClick` = « si `loading`, sortir ; sinon `const restants = await loadSettings(); if (restants.length === 0) panneauRef.current?.focus();` » (§ 2, règles 2 et 3 ; `loadSettings` retourne désormais la liste des lectures en échec) |
| `operationStatus` | `role="status"` teinté info | `p role="status"` `px-4 py-3 text-sm text-info` (pas `Alerte` : ce n'est pas une erreur) |
| `error` de coque | bandeau + Réessayer si `retryOperation` | `Alerte` (ton défaut `'erreur'`) `icone={AlertCircle 18 px}` `children={error}` ; `action` = `Button variant="ghost" size="md"` « Réessayer » **si** `retryOperation` (même quand `loadWarnings.length > 0` : ce bouton appelle `retryOperation()`, pas `loadSettings`) ; **sauf** si `cleInvalide` : ce refus n'a **qu'une** `Alerte`, dans la carte clé (§ 4), maquette `#alerte-cle` seule (parametres.html:84). `getByRole('alert')` de B-201 vise cette occurrence unique : au modal complet, coque et carte clé ne montent pas la même `error` |

**Règle générale, une erreur ne s'annonce qu'une fois** (revue v3, point 7).
La v3 ne la posait que pour la clé, et le profil la violait : la coque passe
`error={error}` à `ProfileTab` (SettingsModal.tsx:631) et `ProfileTab` le rend
à son tour (`ProfileTab.tsx:402-407`), donc le même message serait monté deux
fois, en deux `Alerte` `role="alert"`. Tranché du côté de la coque, qui est le
créneau partagé : **`ProfileTab` ne rend plus `error`**, et la prop `error`
disparaît de `ProfileTabProps` (`ProfileTab.tsx:36,48` ; `setError` reste,
elle sert aux remises à zéro). Le `mdError` de la modale THERESE.md
(`ProfileTab.tsx:179`) est un état local distinct, il ne bouge pas. La seule
exception à « c'est la coque qui rend » reste `cleInvalide`, où c'est
l'inverse : la carte clé rend, la coque se tait. Jamais les deux.

Un Réessayer **par action**, noms distincts, jamais fusionnés : « Réessayer
le chargement » → `loadSettings` ; « Réessayer » → `retryOperation()`
(fournisseur, modèle, dossier, stats, Ollama, recherche web, extraction) ;
« Réessayer l'effort » → `handleChange(failedEffort)` dans `EffortSelector`.
On n'unifie deux boutons que s'ils relancent la **même** fonction (aucun de
ces trois couples).

## 3. Service d'IA : `LLMTab` dans `Carte`

- `Carte as="section"` `aria-labelledby="settings-ia-title"`.
- `CarteTete idTitre="settings-ia-title"` icône `Cpu` 18 px, titre « Service
  d'IA », meta « Le modèle qui répond. En local, rien ne quitte ton
  ordinateur. En ligne, chaque fournisseur demande ton accord une fois. »
- Grille `grid grid-cols-2 gap-2.5 px-4 pb-4` (comme
  `.fournisseurs{grid-template-columns:repeat(2,1fr)}`, parametres.html:14 ;
  **pas** `min-[840px]:grid-cols-2` : le 840 px de `base.css:142` ne touche
  pas `.fournisseurs`, seulement `.barre .etat.secondaire` et `.recherche`).

Chaque fournisseur = **un** `button type="button"`
`aria-pressed={selectedProvider === provider.id}` (maquette
`role="button"` `aria-pressed`, parametres.html:74). **Pas** `role="radio"`
ni `role="radiogroup"` : un radio APG se coche à la flèche
(`rovingFocus.ts:35` `next.click()`), or `setLLMConfig` est un POST. Conteneur
`role="group"` `aria-label="Choix du service d'IA"` (« Fournisseur LLM » est
interdit par le lexique, `docs/rules/RULES-DESIGN.md:385` « LLM / provider →
Service d'IA » ; et un nom distinct du titre de section évite deux noms
accessibles identiques emboîtés, voir § 7 garde 9).

Clavier : **rien**. Pas de `tabIndex` posé sur les cartes (ordre naturel du
DOM, les 14 boutons sont 14 arrêts de tabulation), pas de `onKeyDown`, pas de
flèches, pas de Home ni End, pas d'appel à `handleRovingFocus`. C'est la
doctrine `Segments` du lot 1, prise entière (`Segments.tsx:3-6` et 34-42), et
la décision 3 dit pourquoi. Conséquences à coder telles quelles :

- `LLMTab.tsx:191` (`tabIndex={selectedProvider === provider.id ? 0 : -1}`) et
  `:193` (`onKeyDown={(event) => handleRovingFocus(event, '[role="radio"]', 'vertical')}`)
  disparaissent, et l'import de `handleRovingFocus` (`LLMTab.tsx:11`) avec
  eux ;
- `setLLMConfig` part uniquement sur activation native (`click`, Espace,
  Entrée : un `button` le fait déjà), jamais sur un déplacement de focus ;
- `disabled` sur la carte Ollama indisponible (`LLMTab.tsx:194`) devient
  inoffensif : le clavier saute cette carte et atteint les 13 autres. Avec le
  roving de la v3, si Ollama était **à la fois** courant et indisponible, la
  seule carte à `tabIndex={0}` était `disabled` et la grille entière sortait
  du clavier ;
- `handleRovingFocus` et son `click()` ne changent pas : `AccessibilityTab`,
  `ServicesTab`, `CRMPanel` et `BoardConversationCard` continuent de
  l'appeler.

`grid grid-cols-[1fr_auto] gap-x-2.5 gap-y-0.5 p-3 rounded-sm border text-left text-sm min-h-9` ;
courant (`aria-pressed={true}`) : `border-accent bg-accent-tint ring-2 ring-ring/30 ring-offset-0` ;
sinon `border-border hover:bg-surface-2` ; Ollama indisponible : `disabled`
`opacity-50 cursor-not-allowed` (comme aujourd'hui) ;
`focus-visible:outline focus-visible:outline-[3px] focus-visible:outline-offset-2 focus-visible:outline-ring`.

**Sélection et focus ne se peignent pas pareil** (revue v3, point 19). La
maquette pose le halo de sélection à 30 % :
`.fournisseur[aria-pressed="true"]{border-color:var(--color-accent);box-shadow:0 0 0 2px color-mix(in srgb,var(--color-ring) 30%,transparent)}`
(parametres.html:16). La v3 posait un `outline-2 outline-ring` pleine opacité,
c'est-à-dire la couleur et la forme de l'anneau de focus 3 px : à l'écran, la
carte courante et la carte focalisée devenaient difficiles à distinguer. Donc
**sélection** = `ring-2 ring-ring/30` (2 px, 30 %, `box-shadow` en Tailwind, le
littéral `color-mix(` n'apparaît jamais dans le `.tsx`, ce que la garde
`aucuneCouleurEnDur` étendue exige ; `ring-ring/30` est déjà employé ailleurs
dans `src/frontend/src`, dont `Input.tsx:34`) et **focus** = `outline` plein de
3 px avec `outline-offset-2`. Les deux peuvent coexister sur la même carte
sans se confondre : anneau intérieur pâle, contour extérieur net.
Titre : `font-semibold` = `provider.name`. Ligne `.quoi` :
`col-span-2 text-sm text-text-muted`, **une** chaîne, jamais une
concaténation `description` + compte. Hors Ollama : `provider.description`
seul. Ollama : **jamais** `provider.description` (`'100% local - Aucune clé
API requise'`, catalogueModeles.ts:315) ; une chaîne par cas, N =
`ollamaStatus?.models.length ?? 0` (pas `ollamaModels`, `string[]` sans le
champ) :
- `!ollamaStatus?.available` : « Service local injoignable »
- disponible et N = 0 : « Aucun modèle installé »
- N = 1 : si `selectedProvider === 'ollama'` et `selectedModel` non vide :
  `{selectedModel} · 1 modèle installé` ; sinon « 1 modèle installé »
- N > 1 : si `selectedProvider === 'ollama'` et `selectedModel` non vide :
  `{selectedModel} · N modèles installés` ; sinon « N modèles installés »
  (maquette `gemma4-tia · 2 modèles installés`, parametres.html:74)

Puis, collé à **cette** chaîne, ` · outils pris en charge` seulement si
`selectedProvider === 'ollama'` **et**
`const fiche = ollamaStatus.models.find((m) => m.name === selectedModel)`
est défini **et** `fiche.gere_les_outils === true` (`undefined` n'affiche pas
la mention ; `gere_les_outils !== false` ment hors Ollama, où `find` est
`undefined` et `undefined !== false` est vrai ;
`OllamaModel.gere_les_outils?: boolean`, config.ts:241). Droite : étiquettes
de gauche à droite :

- Anthropic : « Recommandé » `ton="info"` (comme aujourd'hui), à gauche de l'état.
- si `id === selectedProvider` **et** pas (`id === 'ollama' && !ollamaStatus?.available`) : `ton="succes"` « Actif », **en plus** de l'état de clé, jamais à sa place.
- puis **une** étiquette d'état, première règle vraie :
  1. `corruptedKeys.includes(id)` → `ton="erreur"` « Clé corrompue »
  2. `id === 'ollama' && !ollamaStatus?.available` → `ton="attention"` « Indisponible »
  3. `id !== 'ollama' && apiKeys[id]` → `ton="info"` « Clé enregistrée »
  4. `id !== 'ollama'` → `ton="neutre"` « Sans clé »

Un fournisseur courant sans clé porte donc « Actif » **et** « Sans clé »
(aujourd'hui l'icône `Key`). Ollama disponible et sélectionné : « Actif »
seul (pas d'état de clé). Pastilles Check / Key / XCircle retirées (l'étiquette
porte l'état).

## 4. Carte clé, modèle, effort

Seconde `Carte` si `needsApiKey` (pas Ollama) : **uniquement** la clé (champ,
succès, refus, lien console). `CarteTete niveau="h3"` (extension de primitive
n° 2, annoncée en tête de document : `niveau?: 'h2' | 'h3'`, défaut `'h2'`
pour les têtes de section ; aujourd'hui Carte.tsx:52 pose un `<h2>` figé, et
`Carte.test.tsx:51-52, 63, 87` le verrouille — d'où le cas `niveau="h3"` à
ajouter à ce test, § 7) titre =
`Clé API {currentProviderConfig?.name}` — **accès optionnel conservé, sans
repli** : `FOURNISSEURS.find(...)` peut rendre `undefined`, c'est déjà ce que
fait `LLMTab.tsx:247`, et le comportement d'aujourd'hui (titre « Clé API »
seul) ne change pas. Aucune chaîne de secours n'est inventée : la décision 4
n'autorise à écrire des mots que pour un état réellement atteignable, or
cette carte n'est montée que si `needsApiKey`, donc que si le fournisseur
courant est dans le catalogue. Meta : `hasApiKey` → « La clé est
chiffrée sur ton ordinateur et n'est jamais affichée en entier. » ; sinon →
« Nécessaire pour utiliser ce fournisseur ». La maquette titre cette carte
en `h3` sous le `h2` de section (parametres.html:82).

Booléen `cleInvalide` (état de `SettingsModal`, passé à `LLMTab` en
`cleInvalide?: boolean`, défaut `false` : `LLMTab.refusAnnonce.test.tsx:22-42`,
`LLMTab.qwen.test.tsx` et `LLMTab.test.tsx` rendent `LLMTab` sans cette prop).
Posé `true` uniquement dans `handleSaveApiKey` (vide « Entre une clé API »,
préfixe `La clé API doit commencer par "${providerConfig.keyPrefix}"`, catch
de `setApiKey`). Remis à `false` à **chaque** `setError(null)` : saisie du
champ `#settings-api-key` (LLMTab.tsx:281-284), `selectTab`
(SettingsModal.tsx:720), `handleSelectProvider` (SettingsModal.tsx:454),
début de `handleSaveApiKey` avant l'appel, succès, et tout autre
`setError(null)` (Groq, Brave, dossier, profil, Ollama, ToolsPanel, stats,
recherche web, extraction). Les `setError(...)` de `setLLMConfig`
(fournisseur, modèle), Groq, Brave, dossier, profil, Ollama, ToolsPanel,
stats, recherche web, extraction **ne** posent **pas** `cleInvalide`.
`Input error={cleInvalide}` (donc `aria-invalid`) **seulement** tant que
l'`Alerte` de refus est visible (`cleInvalide && error`) : un refus de
préfixe, puis une frappe ou un autre onglet, ne laisse pas `aria-invalid`
sans alerte (WCAG 3.3.1).

| Élément | Aujourd'hui | Cible |
|---|---|---|
| Statut | bandeaux « Clé API configurée » / « Aucune clé » / « corrompue » | Les trois **bandeaux** sont retirés : l'étiquette de la grille (§ 3) dit l'état, le refus vit dans l'`Alerte`. **Sauf la consigne de reprise** : si `corruptedKeys.includes(selectedProvider)`, la meta de la `CarteTete` devient « Clé API corrompue - ressaisis-la » (chaîne exacte de `LLMTab.tsx:258`), à la place des deux metas ci-dessus. La v3 ne gardait que l'étiquette « Clé corrompue », donc l'état sans le geste à faire, alors que la décision 4 promet qu'un état sans équivalent maquetté garde ses mots — et la clé corrompue y est nommément citée. L'étiquette de la grille reste « Clé corrompue » : elle porte l'état, la meta porte la consigne |
| Champ | `<input id="settings-api-key">` maison + œil `absolute` + « Sauver » | **Pas** de `FormField` : il clone tout enfant (FormField.tsx:41-48), donc ni rangée en enfant unique (l'`aria-invalid` irait sur le `div`) ni `FormField` `flex-1` dans la rangée (le label et l'input formeraient un seul item flex, œil et geste calés à droite du bloc entier). Maquette : `<label for="cle">` puis `<div class="cle">` (parametres.html:19, 83). Cible : `<label htmlFor="settings-api-key" className="block text-sm font-semibold">Clé d'API</label>` puis `.cle` = `div` `className="flex gap-2 items-center"` contenant (1) `div` `className="flex-1 min-w-0"` autour de `Input id="settings-api-key"` `type={showApiKey ? 'text' : 'password'}` `className="font-mono tracking-widest"` `error={Boolean(cleInvalide && error)}` `placeholder={currentProviderConfig?.keyPlaceholder || '...'}` (**placeholder conservé**, LLMTab.tsx:290 : c'est lui qui donne le format attendu de la clé ; et l'accès reste optionnel, `currentProviderConfig` pouvant être `undefined`) (`Input` pose `aria-invalid` + bordure, Input.tsx:27 ; le `relative` d'`Input` est interne, Input.tsx:19, d'où le wrapper `flex-1 min-w-0` plutôt qu'une `className` sur `Input`, qui atterrit sur le `<input>`), (2) `Button variant="ghost" size="icon"` œil `aria-label` / `aria-pressed` conservés (B-526), (3) `Button variant="primary" size="md"` : `hasApiKey` → « Remplacer », sinon « Enregistrer » ; `saving` → `Spinner taille="bouton"` ; `disabled={saving \|\| !apiKeyInput.trim()}` ; Entrée inchangée |
| Succès | `role="status"` « Clé API enregistrée » | inchangé (B-201) |
| Refus | `<p role="alert">` + `error` | `Alerte` (ton `'erreur'`) `icone={AlertCircle 18 px}` `children={error}` sans `action` si `cleInvalide` (pas de `retryOperation` sur `handleSaveApiKey`). **Seule** `Alerte` de ce refus : la coque ne le remonte pas (§ 2). B-201 (`LLMTab.refusAnnonce.test.tsx`) passe `cleInvalide={true}` avec `error={REFUS}` |
| Lien console | `text-xs` | inchangé, `text-sm` |
| Ollama | bandeau + Re-tester `size="sm"` | **hors** de la carte clé (Ollama n'a pas `needsApiKey`). Indisponible : **pas** d'`Alerte` (revue v3, point 8 : `Alerte.tsx:25` pose `role="alert"` en dur, donc une annonce assertive relue à **chaque** montage de la rubrique, pour un état de service permanent ; aujourd'hui ce bandeau n'a aucun rôle, `LLMTab.tsx:370-375` ; et dans la maquette la seule `role="alert"` est `#alerte-cle`, parametres.html:84, l'indisponibilité y étant une étiquette `e-attention`, :78). Cible : `p role="status"` en teinte attention, `className="px-4 py-3 text-sm text-warning"`, texte = `{ollamaStatus?.error \|\| 'Ollama non disponible'}` **suivi de** « Démarrez Ollama pour utiliser des modèles locaux. » (chaîne de `LLMTab.tsx:358`, la seule qui dit quoi faire ; la v3 la perdait, revue v3 point 18). Disponible : `p role="status"` `className="px-4 py-3 text-sm text-text-muted"` « Ollama connecté ({base_url}) ». Dans les deux cas, `Button variant="ghost" size="icon"` `aria-label="Re-tester la connexion Ollama"` (icône `RefreshCw` seule : `size="icon"` = 36 px, pas `size="md"` `h-9 px-4` autour d'une icône sans nom visible ; LLMTab.tsx:379-381 est aujourd'hui `size="sm"` + icône). L'`Alerte` reste réservée aux refus et aux échecs d'enregistrement |

Modèle, effort, Qwen et `LocalModelFeasibility` : **toujours hors** de la
carte clé, visibles pour Ollama (sinon le sélecteur disparaît avec
`needsApiKey`). Une `Carte` toujours rendue, `CarteTete niveau="h3"` titre =
`currentProviderConfig.name` (maquette `h3` « OpenAI » / réglages du modèle,
parametres.html:82), contenant les deux rangées ; Qwen et la faisabilité à
la suite, hors de cette carte aussi.

| Élément | Aujourd'hui | Cible |
|---|---|---|
| Modèle | `<select id="settings-llm-model">` + « Custom » | rangée `grid grid-cols-[1fr_auto] items-center gap-x-4 gap-y-1 py-2.5 border-t border-border px-4` : **rangée 1** — `<label htmlFor="settings-llm-model" className="text-sm font-semibold">Modèle</label>` en colonne 1 (pas un `<b>` : le `Select` n'aurait plus de nom accessible, WCAG 4.1.2 ; `getByLabelText('Modèle')` de `SettingsModal.fournisseurIA.test.tsx:93` et `LLMTab.test.tsx:49`) + `Select id="settings-llm-model"` `options` = `availableModels` en colonne 2 (label `name` + badge entre parenthèses, comme aujourd'hui). **Rangée 2** — le bouton « Custom » (revue v3, point 17 : la v3 ne lui laissait aucune place dans une grille à deux colonnes déjà pleines). Il descend sous le label, en `col-start-1 justify-self-start`, comme l'aide de la maquette (`.ligne-reglage .aide{grid-column:1}`, parametres.html:23) : `Button variant="ghost" size="md"` icône `Plus` 18 px, libellé « Custom » conservé (décision 4), rendu seulement si `selectedProvider !== 'ollama'` (condition d'aujourd'hui, LLMTab.tsx:478). **Sous la rangée**, pleine largeur : le champ « modèle hors liste » quand `showCustomInput`, et le bloc Qwen ; inchangés sauf boutons `md` et `Input` / `FormField` ; Qwen : le bouton d'adresse dit **« Enregistrer l'adresse »** (jamais « Enregistrer » : collision avec la clé si `!hasApiKey` ; `LLMTab.qwen.test.tsx:70` `name: 'Enregistrer'` à aligner) |
| Effort | `<select id="llm-effort">` | même rangée (`grid-cols-[1fr_auto]`, comme `.ligne-reglage`) ; `<label htmlFor="llm-effort" className="text-sm font-semibold">Effort de raisonnement</label>` + `Select id="llm-effort"` (`getByLabelText('Effort de raisonnement')` et `aria-describedby`, `LLMTab.effortOpenAI.test.tsx:20`) ; sous le label, `p` `id="llm-effort-aide"` `className="text-sm text-text-muted col-start-1"` (`.ligne-reglage .aide{grid-column:1}`, parametres.html:23) : « Appliqué aux modèles qui le gèrent (Claude récents, GPT-5.6, Grok 4.5, modèles Ollama « thinking »). Auto laisse le modèle décider. » (LLMTab.tsx:635-638, conservé ; la maquette dit « Envoyé seulement aux modèles qui le prennent en charge. », parametres.html:87) ; le `Select` a `aria-describedby` qui inclut `llm-effort-aide` **et**, si `mentionOutils`, `llm-effort-outils` ; options et `disabled={saving}` inchangés ; `data-testid="effort-mention-outils"` : `text-sm` (plus `text-xs` sur un texte lié à un interactif) ; **ligne de statut conservée** (revue v3, point 9 : la v3 décrivait la rangée entière sauf elle, et l'enregistrement de l'effort serait devenu muet) : `p role="status" className="col-span-2 mt-2 text-sm text-info"` rendu si `status` est non nul (le `col-span-2` est nécessaire : la rangée est une grille `grid-cols-[1fr_auto]`, sans lui la ligne de statut tomberait en colonne 1 et déplacerait le `Select`), avec ses deux chaînes exactes « Enregistrement de l'effort… » (LLMTab.tsx:602) et « Effort de raisonnement enregistré. » (:610), en `text-sm` et non plus `text-xs` (LLMTab.tsx:664) ; erreur d'effort : `Alerte` `className="col-span-2"` (même raison que la ligne de statut) + `Button variant="ghost" size="md"` « Réessayer l'effort » (`onClick={() => failedEffort && void handleChange(failedEffort)}`, LLMTab.tsx:668) — **toujours** rendu si `failedEffort`, même si la coque a `retryOperation` ou `loadWarnings` |

Pas de jauge « Ce mois-ci », pas d'interrupteur d'accord cloud (P-086).
`LocalModelFeasibility` inchangé hors classes de couleur en dur s'il en reste.

## 5. Profil : `ProfileTab`

- `Carte as="section"` `aria-labelledby="settings-profil-title"`.
- `CarteTete idTitre="settings-profil-title"` icône `User` 18 px, titre
  « Profil », meta « Ce que Thérèse sait de toi pour te répondre juste.
  Modifiable à tout moment, exportable, effaçable. »
  `actions` : `Button variant="ghost" size="md"` « Voir THERESE.md » ;
  `Button variant="secondary" size="md"` « Importer THERESE.md » (`onImport`).
- Bandeau « Profil configuré : {display_name} » / « Profil non configuré… »
  → `Etiquette ton="succes"` / `ton="attention"`, mêmes chaînes.
- Première `Carte`, grille `grid grid-cols-1 min-[1024px]:grid-cols-2 gap-x-4`
  `px-4 pb-4` : **uniquement** l'identité, chaque champ = `FormField` +
  `Input`, **mêmes `id`**, mêmes `placeholder`, mêmes handlers.
  **1024 px, pas 840** (revue v3, point 2) : le socle fait tomber `.grille-2`
  à une colonne sous 1024 px (`base.css:140-141`), et le seul `840` de
  `base.css` (:142) ne concerne que `.barre .etat.secondaire` et
  `.recherche` — c'est d'ailleurs ce que le § 3 invoque pour refuser une
  césure à 840 px sur les fournisseurs. Une grille à deux colonnes dès 840 px
  donnerait, entre 840 et 1023 px, un écran qui n'est pas celui de la
  maquette. Ids **dans la grille** : `settings-profile-name`,
  `settings-profile-nickname`, `settings-profile-company`,
  `settings-profile-role`, `settings-profile-email`,
  `settings-profile-location`.
- **Le champ de contexte est hors de la grille**, en pleine largeur, juste
  en dessous (revue v3, point 3) : `settings-profile-context`, `Textarea`
  dans un `FormField`. La maquette le pose ainsi — quatre champs dans
  `.grille-2` (parametres.html:94) puis `<div class="champ"><label
  for="contexte">` **après** la grille (:95). Pas de `col-span-2` : sous
  1024 px la grille n'a qu'une colonne, et un `col-span-2` y créerait une
  seconde colonne implicite qui casserait la mise en page. Label « Ce que
  Thérèse doit savoir » (la maquette) ; description actuelle conservée en
  `FormField description`, **rendue en `text-sm`** (revue v3, point 21) :
  `FormField.tsx:65` la pose aujourd'hui en `text-xs` et la rattache au champ
  par `aria-describedby` (:37-48), ce qui en fait exactement le cas que la
  règle de la rangée Effort interdit (« plus de `text-xs` sur un texte lié à
  un interactif »). La règle ne souffre pas d'exception ici : on corrige la
  primitive plutôt que de s'en exempter. Le message d'erreur de `FormField`
  (`:76`) suit la même bascule, pour la même raison.
- **Libellés et étoile** (revue v3, point 6) : chaque `FormField` reçoit
  `htmlFor={id}` (c'est la seule chose qui relie le label au champ,
  `FormField.tsx:54`) et le libellé **sans** son étoile :
  `label="Nom complet"` + `required`, jamais `label="Nom complet *"`. Une
  seule étoile à l'écran, celle de `FormField.tsx:61`, et le texte du label
  devient `Nom complet*` (sans espace, le `<span>` est collé). Les cinq
  autres champs de la grille n'ont ni `required` ni étoile, comme aujourd'hui.
  Conséquences sur les requêtes, à écrire telles quelles : en Playwright
  `getByLabel('Nom complet')` (le défaut est une correspondance de
  sous-chaîne, donc `Nom complet*` est trouvé) ; en testing-library
  `getByLabelText(/^Nom complet/)` (une chaîne y est **exacte** par défaut,
  `'Nom complet'` échouerait). `ProfileStep` de l'onboarding garde son
  `Nom complet *` écrit à la main (`ProfileStep.tsx:167`) : il est hors lot,
  et ses quatre tests ne bougent pas.
- `saved` → `role="status"` « Profil enregistré ». **Pas d'`error` rendu
  ici** : la coque le rend, une fois (§ 2, « une erreur ne s'annonce qu'une
  fois »).
- Seconde `Carte` : `CarteTete` titre « Profil émetteur des factures », meta
  « SIRET, TVA, adresse et mentions légales, utilisés sur chaque devis et
  facture. » **Seule** occurrence des champs facture, éditables (pas un
  résumé Complet : P-087), mêmes `id` / handlers / placeholders. Ids de
  cette carte : `settings-profile-address`, `settings-profile-siren`,
  `settings-profile-tva`, `settings-profile-siret`, `settings-profile-ape`,
  `settings-profile-nda`. Libellés conservés (Adresse, SIREN, TVA, SIRET,
  APE, NDA). Un `id` n'apparaît qu'une fois dans le document.
- `DemoModeSection` : `data-testid="mode-demo-section"` conservé ; tête en
  `text-sm` ; prose B-131 inchangée ; état actif : `Alerte` n'est pas le bon
  ton, donc `p role="status"` « Mode démo actif - … ».
  **L'interrupteur reçoit son rôle et son nom en même temps que sa taille**
  (revue v3, point 20) : aujourd'hui `ProfileTab.tsx:447-458` est un
  `<button onClick={toggleDemo}>` sans `type`, sans rôle, sans nom
  accessible — un bouton muet, que le lecteur d'écran annonce « bouton ».
  Cible : `type="button"` (absent aujourd'hui, donc `submit` par défaut dans
  un formulaire), `role="switch"`, `aria-checked={demoEnabled}`,
  `aria-label="Mode démo"`, et la taille `w-10 h-6` (le `w-11 h-6` actuel
  devient `w-10 h-6`, comme l'interrupteur du mode contributeur, § 1, et
  `.interrupteur{width:2.6rem;height:1.5rem}` de parametres.html:24). Le
  curseur passe de `translate-x-5` à `translate-x-4` pour rester dans la
  piste. On ne touche pas au `toggleDemo` du store.
- **La phrase « Tu peux aussi importer ton profil depuis un fichier
  THERESE.md » est retirée** (revue v3, point 23) : `ProfileTab.tsx:418-420`
  la pose en `text-xs` au pied de la rubrique, à distance du geste qu'elle
  décrit. Le geste « Importer THERESE.md » est désormais un `Button` nommé,
  en tête de la carte Profil (`CarteTete actions`, ci-dessus) : la phrase
  redirait ce que le bouton dit déjà, en plus petit et plus loin. Décision
  écrite, pas un oubli.
- Modale THERESE.md : hors restyle profond (overlay `bg-black/60` du motif
  commun) ; boutons `md`. Son `mdError` local garde son `role="alert"`
  (`ProfileTab.tsx:179`), il n'est pas l'`error` de la coque.

Le pied de la coque reste le seul « Enregistrer » (testid) du profil.

## 6. Les états (priorité)

Sur le panneau visible, de haut en bas :

1. si `loading` : `loadWarnings` s'il est non vide (son Réessayer en
   `aria-disabled`, § 2), puis squelettes + « Lecture des réglages… » ;
   `error` et `operationStatus` masqués, même non nuls ;
2. sinon : `loadWarnings` ; `operationStatus` ; `error` de coque ; corps
   de la rubrique (IA : grille, carte clé si besoin, Ollama, modèle, effort,
   Qwen ; Profil : carte identité, carte émetteur, démo).

Réessayer : un bouton par action, noms distincts (§ 2). L'effort ajoute le
sien dès que `failedEffort` est non nul, **même** si la coque a le sien.

`invalide` (maquette) = `error` non nul sur l'onglet `ai` **et** `cleInvalide`
(refus de clé, `aria-invalid` sur `#settings-api-key`) ; clé précédente
intact (`apiKeys` non muté, déjà le cas). Un `error` de `setLLMConfig` sans
`cleInvalide` n'est **pas** l'état `invalide` de la maquette. `profil` =
`activeTab === 'profile'`. `normal` = `activeTab === 'ai'` sans erreur.

## 7. Gardes mécaniques et tests à aligner

Nouveaux (`SettingsModal.da.test.tsx`, `LLMTab.da.test.tsx`,
`ProfileTab.da.test.tsx`, plus les trois tests de primitives étendus —
`Alerte.test.tsx` pour `ton="attention"`, `Carte.test.tsx` pour
`niveau="h3"`, `FormField.test.tsx` pour le `text-sm` — rouges d'abord,
**sauf** la garde 7 bis, dite plus bas, qui naît verte et le dit) :

1. nav : 9 ids, libellés cibles (§ 1), `aria-selected` sur l'onglet courant,
   `settings-tab-ai` / `settings-hidden-tabs` / `ux-mode-toggle` présents ;
   classes de la nav : `max-[1023px]:grid-cols-3`, `min-[1024px]:block` et
   `min-[1024px]:w-60` ; et **aucune** classe commençant par `sm:` dans la
   `className` du corps (SettingsModal.tsx:784), de la nav (:786) ni de son
   premier enfant (:788) — assertion sur la chaîne, `/\bsm:/` ne doit rien
   trouver (revue v3, point 11 : la v3 ne retirait que `sm:w-44` et laissait
   `sm:flex-row` et cinq autres, donc un panneau écrasé entre 640 et
   1023 px) ;
2. une carte fournisseur = un `button` `aria-pressed` (`getByRole('button',
   { pressed: true })` rend la carte courante, et `queryAllByRole('radio')`
   est vide), grille `grid-cols-2` **sans** aucune classe de césure (ni
   `min-[840px]:`, ni `md:`, ni `lg:`) ; l'état porte `data-etiquette` ;
   P-018 : un fournisseur à clé hors sélection reste visible avec « Clé
   enregistrée » ; le courant sans clé porte « Actif » **et** « Sans clé » ;
   la garde 2 est réécrite ici parce que la v3 la laissait prescrire un
   `radio` et une césure à 840 px, en contradiction avec sa propre décision 3
   (revue v3, point 4) — et une garde est ce qui sera codé en rouge, donc ce
   qui gagne en cas de désaccord ;
   2 bis. **clavier de la grille** : aucune des 14 cartes ne porte de
   `tabIndex` (`element.hasAttribute('tabindex')` faux partout) ; une
   `keyDown` `ArrowDown` / `ArrowRight` / `Home` / `End` sur une carte
   n'appelle **pas** `setLLMConfig` et ne déplace pas le focus ; et avec
   `selectedProvider = 'ollama'` et `ollamaStatus.available = false`, la carte
   Ollama est `disabled` **et** les 13 autres restent atteignables au clavier
   (aucune n'a `tabIndex={-1}`) — c'est le défaut préexistant que la doctrine
   `Segments` ferme (revue v3, point 1) ;
3. pluriel Ollama : 0 / 1 / 2 modèles, chaînes exactes ; « · outils pris en
   charge » absent si `selectedProvider !== 'ollama'` ou si
   `gere_les_outils` n'est pas `true` ;
4. « Enregistrer » vs « Remplacer » selon `hasApiKey` ; `#settings-api-key`
   `aria-invalid` **seulement** si `cleInvalide` (refus de préfixe ou de
   `setApiKey`), **pas** si `error` vient de `setLLMConfig` / Groq / dossier ;
   B-201 : `getByRole('alert')` contient le refus, le succès reste « Clé API
   enregistrée » ; Qwen sans clé : un bouton « Enregistrer » (la clé) et un
   bouton « Enregistrer l'adresse », pas deux « Enregistrer » ;
5. hors chargement : « Réessayer le chargement » présent ssi `loadWarnings` ;
   « Réessayer » (nom exact) présent ssi `retryOperation` ; les deux
   coexistent si les deux états sont vrais ; « Réessayer l'effort » présent
   ssi `failedEffort` ; zéro sur IA sans erreur ni warning. Pendant
   `loading` : « Réessayer » et « Réessayer l'effort » **absents** ;
   « Réessayer le chargement » **présent** si `loadWarnings` est non vide,
   avec `aria-disabled="true"` et **sans** attribut `disabled` (revue v3,
   point 12 : un `disabled` posé sur l'élément focalisé renvoie le focus au
   `body`, exactement ce qu'on répare) ; un clic dessus pendant `loading`
   n'appelle pas `loadSettings` une seconde fois ;
   5 bis. **le focus survit à la reprise** : on focalise « Réessayer le
   chargement », on clique, la relecture réussit (`loadWarnings` vide), et
   `document.activeElement` est le `tabpanel` `settings-panel-ai`, **pas**
   `document.body` ;
6. Profil : les 13 `id` `settings-profile-*` existent **une fois**, `FormField`
   pose le label (donc chaque `FormField` a un `htmlFor` égal à l'`id` du
   champ qu'il enveloppe), identité et émetteur ne partagent aucun `id` ;
   `settings-save-btn` unique ; `mode-demo-section` présent ;
   `getByLabelText(/^Nom complet/)` rend le champ, et le document ne contient
   **qu'une** étoile dans ce label (`label.textContent` vaut `Nom complet*`,
   une seule occurrence de `*`) ; `settings-profile-context` n'est **pas**
   enfant de la grille `grid-cols-1 min-[1024px]:grid-cols-2` ; l'interrupteur
   du mode démo est `getByRole('switch', { name: 'Mode démo' })` avec
   `aria-checked` qui suit le store ;
7. aucune classe `text-xs` sur un interactif **ni dans son sous-arbre**
   (SettingsModal, LLMTab, ProfileTab) ; l'aide « Fonctions avancées » est
   hors du `<label>` du checkbox ; `CarteTete` `meta` (`text-xs font-medium`,
   Carte.tsx:53) n'est **pas** une violation (paragraphe, hors interactif) ;
   boutons `sm` absents ;
   7 bis. `aucuneCouleurEnDur` étendu aux trois fichiers de la rubrique.
   **C'est un cliquet, pas une preuve** (revue v3, point 14) : vérifié le
   11/09, `SettingsModal.tsx`, `LLMTab.tsx` et `ProfileTab.tsx` ne
   contiennent aujourd'hui **aucun** hex, `rgb(`, `hsl(` ni `color-mix(`
   (`grep -cPE` rend 0 sur les trois). Cette extension ne sera donc jamais
   rouge avant le code ; elle est là pour empêcher une régression pendant le
   restyle, et elle ne voit pas les classes Tailwind brutes (`bg-red-500`),
   que seule la relecture attrape. Elle ne figure pas parmi les tests
   « rouges d'abord » ;
8. `h1#settings-title` « Paramètres », **sans** `font-editorial` ;
9. **lexique des noms accessibles** (revue v3, point 13). `lexique.test.ts`
   refuse par construction le balayage brut du code (`lexique.test.ts:3-6` :
   il ne lit que des registres exportés, pour ne pas se tromper sur des
   identifiants et des commentaires) — donc l'extension est un test **de
   rendu**, pas un `grep` : on monte `SettingsModal` (onglets IA puis Profil),
   on collecte les `aria-label` et les noms accessibles des `role="group"`,
   `role="dialog"`, `role="tablist"`, `role="switch"` et des boutons, et on
   les passe aux mêmes `INTERDITS` (`lexique.test.ts:29-38`, dont
   `['LLM', /\bLLMs?\b/]` et `['provider', /\bproviders?\b/i]`). La v3 laissait
   « Fournisseur LLM » comme nom du groupe : le terme interdit ne survivait
   que pour le lecteur d'écran, et l'annonce divergeait de ce qui est écrit à
   l'écran. Chaîne cible : « Choix du service d'IA » ;
10. **perte de couverture de B-201, réparée** (revue v3, point 15). En passant
    par `Alerte`, les trois fichiers sortiraient du champ de
    `erreursAnnoncees.test.ts` : le balayage cherche `text-error` ou
    `color-error-tint` dans la première balise rendue (`MARQUEUR_ERREUR`,
    :65) et `<Alerte ...>` n'en porte aucun ; la propriété resterait vraie
    par construction, la garde deviendrait aveugle. On ajoute donc
    `<Alerte\b` **aux deux** motifs, jamais à un seul : à `MARQUEUR_ERREUR`
    (sinon le site d'appel n'est même pas examiné) **et** à `ANNONCE`
    (`/role="alert"|aria-live=/`, :43 — sinon chaque `<Alerte>` devient un
    « muet », son `role="alert"` vivant dans `Alerte.tsx:25` et non dans la
    balise scannée). Un bandeau d'erreur écrit à la main reste attrapé comme
    avant.

À aligner, forme seulement :

- `SettingsModal.fournisseurIA.test.tsx` — **la principale casse du lot**, et
  la v3 ne citait de ce fichier que `getByLabelText('Modèle')` (revue v3,
  point 5). C'est le test de non-régression de B-225 : il interroge la grille
  **huit** fois par le rôle `radio`, aux lignes 51, 68, 71, 88, 90, 108, 112,
  et assène `toHaveAttribute('aria-checked', 'true')` en 51-54. Forme cible :
  `getByRole('button', { name: /Mistral AI/, pressed: true })` pour
  l'assertion d'état, `getByRole('button', { name: ... })` pour les sept
  `fireEvent.click`. Les `getByLabelText('Modèle')` de :93 et :101 ne
  bougent pas. **Aucune** assertion de comportement (les `setLLMConfig`
  attendus, l'ordre des envois, le modèle retrouvé) n'est touchée. Balayage
  fait : `grep -n "getByRole('radio'\|aria-checked\|role=\"radio\""
  src/frontend/src/components/settings/*.test.tsx` ne rend que ce fichier et
  un commentaire d'`AdvancedTab.nomDesInterrupteurs.test.tsx` (:5, qui parle
  de `role="switch"`, hors sujet) ; `TodayDashboardCard.variateur.test.tsx`
  interroge de vrais `<input type="radio">`, hors lot ;
- `tests/e2e/stories/parcours-05-settings.spec.ts` — non listé par la v3
  (revue v3, point 6) : `:202` remplit le champ par
  `getByLabel('Nom complet *')`, requête qui tombe dès que l'étoile vient de
  `FormField` (le libellé devient `Nom complet*`, sans espace). Nouvelle
  requête : `modale.getByLabel('Nom complet')`, sans `{ exact: true }` — la
  correspondance par défaut de Playwright est une sous-chaîne. Le reste du
  parcours (bouton activé, « Profil enregistré », fermeture) ne change pas ;
- `SettingsModal.fermeture.test.tsx` (libellé d'onglet jamais lu, testid
  conservés) ;
- `LLMTab.refusAnnonce.test.tsx` (l'alerte peut être `Alerte`, le rôle et la
  chaîne `REFUS` restent) ;
- `LLMTab.effortOpenAI.test.tsx` (`effort-mention-outils`,
  `getByLabelText('Effort de raisonnement')`, `aria-describedby`) ;
- `LLMTab.test.tsx` (`getByLabelText('Modèle')`) ;
- `LLMTab.qwen.test.tsx` (`name: 'Enregistrer l'adresse'`) ;
- `modeDemoPerimetre.test.tsx` (prose B-131 ; il importe `DemoModeSection`,
  qui gagne `role="switch"` et un nom) ;
- `Alerte.test.tsx` (ton `'attention'` : `bg-[var(--color-warning-tint)]`,
  titre `text-warning` ; le défaut reste `'erreur'`) ;
- `Carte.test.tsx` — extension de primitive n° 2 (revue v3, point 16) : ses
  trois assertions verrouillent le `h2` (`:51-52` `getByRole('heading',
  { level: 2 })` et `titre.tagName`, `:63` le libellé du cas icône, `:87`
  `container.querySelector('h2')`). Elles restent telles quelles, le défaut
  de `niveau` étant `'h2'` ; on **ajoute** un cas `niveau="h3"` qui vérifie
  `getByRole('heading', { level: 3 })` et que `idTitre` est bien posé dessus ;
- `FormField.test.tsx:95-96` — extension de primitive n° 3 : les deux
  `toMatch(/text-xs/)` (description et message d'erreur) deviennent
  `toMatch(/text-sm/)`. Assertions de classe, pas de comportement ; le
  rattachement `aria-describedby` testé ailleurs dans le fichier ne bouge pas.

Aucune assertion de comportement n'est retirée. Onboarding (`Sauver` de
`LLMStep`, `Nom complet *` de `ProfileStep`) hors lot.

## 8. Ce que ce lot ne fait pas

- Paramètres en page, rail `aria-current`, colonne 72 rem hors modale : **P-084**.
- Tester / quatre derniers caractères / date de vérification / badge
  « Clé refusée » distinct d'une clé encore en place : **P-012** déjà au
  portail. Service cloud 503 (« Indisponible depuis HH:MM ») : même fiche,
  l'app ne le connaît que pour Ollama.
- Carte « Autres + 6 » (masquerait GLM, Kimi, Qwen, MiniMax ; Groq n'est pas
  un fournisseur LLM) : **P-085**.
- Jauge « Ce mois-ci » et accord cloud dans Service d'IA (les données vivent
  dans `LimitsTab` / `PrivacyTab`) : **P-086**.
- Rubriques de premier rang « Coûts et limites », « Stockage et sauvegardes »,
  item « Katia et Zézette » ; scinder Nom complet / Surnom en Prénom / Nom ;
  carte émetteur résumé « Complet » qui cacherait les champs : **P-087**.
- Restyle des contenus Services, Accessibilité, Confidentialité, À propos,
  Avancé, Outils, Agents (non maquettés). `LimitsTab` reste dans Avancé.
- Aucun changement de données, d'API, de store ni de navigation.
- Pas de navigation bidimensionnelle dans `rovingFocus.ts` (les flèches
  restent un cran DOM) ; pas de `click()` retiré du helper global. Depuis la
  v4, `LLMTab` ne l'appelle plus du tout (décision 3, § 3) : le helper ne
  change pas d'une ligne, il perd un appelant. `AccessibilityTab:53,107`,
  `ServicesTab:130`, `CRMPanel:214` et `BoardConversationCard` gardent le
  leur, et leurs `role="radio"` ne sont pas rejugés par ce lot.
- Pas de refonte de `ProfileStep` (onboarding) : son `Nom complet *` écrit à
  la main reste tel quel, ses tests aussi. Les deux écrans divergeront donc
  d'une espace avant l'étoile jusqu'au lot qui prendra l'onboarding.

## 9. Plan de preuve

1. Tests rouges d'abord (§ 7), vérifiés rouges pour la bonne raison,
   sabotage par remplacement inverse, `.agents-sync-paused` posé.
2. Six portes : ruff, pytest (XML), vitest json, tsc, eslint (27), mypy 951.
3. Recette visuelle sur la pile jetable (17393 et 1420, jamais 17293) :
   états forcés par interception de `/api/config/` (clés, `corrupted_keys`),
   `/api/config/llm`, `/api/config/profile`, `/api/config/ollama/status`
   (Playwright `page.route`) : IA avec Ollama actif et 2 modèles ; IA avec
   OpenAI `has_openai_key` ; IA sans clé ; refus de préfixe (saisie `sk-`
   chez Anthropic) ; lecture `clés API` en échec ; **Ollama courant et
   indisponible** (le cas de la carte `disabled`) ; Profil Marie Exemple ;
   chargement lent. Largeurs 1280, 1024, 1023, 840, 800 px ; clair, sombre,
   contraste élevé ; trois tailles de police. Captures
   `.cartography-work/validation/da-lot9/`, rapport
   `docs/da/2026-09-11-lot9-recette.md`. Vérifier (liste réécrite en v4 : la
   v3 y prescrivait encore un radio et une césure à 840 px, contre sa propre
   décision 3 — revue v3, point 4) :
   - nav 3 colonnes à 800 px **et** à 1023 px, panneau **sous** elle et non à
     côté aux deux largeurs (à 1024 px la grille reprend `15rem 1fr`,
     maquette `max-width:1023px`) ; à 800 px, le panneau n'est pas écrasé à
     zéro (c'est le défaut que la césure `sm:` provoquait) ;
   - grille fournisseurs : **2 colonnes à toutes les largeurs**, 800 px
     compris, sans césure ;
   - halo de sélection à 30 % sur la carte courante, anneau de focus plein de
     3 px sur la carte focalisée et sur un onglet : les deux doivent rester
     distinguables l'un de l'autre, y compris en contraste élevé ;
   - clavier : Tab traverse les 14 cartes une à une, les flèches ne font
     rien ; avec Ollama courant et indisponible, Tab atteint bien les 13
     autres cartes ;
   - grille d'identité du profil : 1 colonne à 1023 px, 2 colonnes à 1024 px ;
     le champ de contexte en pleine largeur sous la grille aux deux largeurs ;
   - un Réessayer par action (chargement / enregistrement / effort), pas un
     seul pour les trois ; et sur « lecture en échec », cliquer « Réessayer le
     chargement » ne fait pas sauter le focus au `body` (le vérifier au
     clavier, pas à la souris) ;
   - clé jamais en clair une fois enregistrée ; dollars absents de l'onglet IA
     (ils restent dans Avancé) ; overlay `fixed inset-0` (décision 1,
     BUG-156) recouvre établi et composeur : les juger **derrière**
     l'overlay, pas à côté.
4. Revue Grok du diff avant le tag, `/release-therese 0.72.0-alpha` avec le
   GO de Ludo (toute la DA, pas ce lot seul).

## Points non repris

**Revue de la v3 (23 points) : aucun non repris.** Les 23 sont fondés, preuve
relue une par une avant correction, dans la maquette
(`parametres.html:16, 23, 24, 30, 74, 78, 82, 84, 94, 95`), le socle
(`base.css:140-142`), les primitives (`Segments.tsx:3-6, 34-42`,
`Alerte.tsx:25`, `Carte.tsx:52`, `FormField.tsx:54, 61, 65, 76`,
`Input.tsx:34`, `Etiquette.tsx:16-25`), les trois fichiers de la rubrique
(`SettingsModal.tsx:176-178, 199, 631, 784, 786-788, 845-849, 855-864`,
`LLMTab.tsx:11, 191, 193-194, 247, 258, 290, 358, 370-375, 477-488, 602, 610,
664`, `ProfileTab.tsx:36, 48, 179, 402-407, 418-420, 447-458`), les règles
(`docs/rules/RULES-DESIGN.md:385`), les gardes
(`lexique.test.ts:3-6, 29-38`, `erreursAnnoncees.test.ts:43, 65, 99`,
`aucuneCouleurEnDur.test.ts:47`, `Carte.test.tsx:51-52, 63, 87`,
`FormField.test.tsx:95-96`) et les tests cités
(`SettingsModal.fournisseurIA.test.tsx:51-54, 68, 71, 88, 90, 93, 101, 108,
112`, `tests/e2e/stories/parcours-05-settings.spec.ts:202`).

**Correction de l'en-tête de la v3.** Elle annonçait « 17 points repris,
0 non repris » et une section « Points non repris : aucun » — c'était faux
(revue v3, constat 3). Deux points de la revue de la v2 n'étaient pas repris
dans le texte : le champ de contexte hors de la grille du profil, et
l'arbitrage de l'étoile du champ obligatoire. Ils reviennent ici comme points
3 et 6 de la revue de la v3, et sont tranchés au § 5. La leçon vaut pour la
suite : un décompte en en-tête n'est vrai que si chaque point a laissé une
trace vérifiable dans le corps du document, ce qui est la raison d'être des
mentions « revue v3, point n » semées dans les sections.

**Revue de la v1 (15 points), rappel.** Tous fondés, tous repris dès la v2 ;
preuve relue alors dans la maquette, `base.css`, `Alerte.tsx:12`,
`FormField.tsx:41-48`, `Input.tsx:19`, `Carte.tsx:53`, `rovingFocus.ts:10-35`,
`config.ts:241`, `SettingsModal.tsx:176-177, 462-467, 653, 754, 856`,
`LLMTab.tsx:478, 668`. La doctrine clavier posée alors (roving local sans
`click()`) est la seule décision de la v1 que la v4 renverse, au profit de la
doctrine `Segments` (décision 3) : elle valait contre le `click()` du helper,
elle ne réglait pas le `tabIndex={-1}` sur une grille dont la seule carte
focalisable peut être `disabled`.
