# DA « Application affinée », lot 9 : l'écran Paramètres (design à challenger avant le code)

Version 2, 11/09/2026 00:46, après la revue de la v1 (15 points repris, 0 non repris) ; journal `.cartography-work/reviews/grok-da-lot9-parametres-design-v1.log`.
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
Ce lot étend `Alerte.ton` de `'erreur'` à `'erreur' | 'attention'` (le warning
de lecture partielle ne doit pas se teinter en erreur).

## Décisions tranchées par défaut (Ludo peut corriger)

1. Les Paramètres restent une **modale** (`role="dialog"` `aria-modal="true"`
   `data-testid="settings-modal"`) : la maquette en page est P-086. Overlay,
   piège de focus, Échap, BUG-156 inchangés.
2. Les neuf `id` de `ALL_TABS` restent ; seuls les libellés visibles des six
   rubriques du mode standard suivent la maquette. Outils, Agents, Avancé
   restent contributeur, nommés par BUG-159. Pas de 10e destination.
3. La liste `FOURNISSEURS` (14 ids, Anthropic en tête, Ollama en queue) reste
   entière et dans cet ordre, en grille 2 colonnes, `role="radiogroup"`
   `aria-label="Fournisseur LLM"`. Pas de carte « Autres + 6 » (P-087, P-018).
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
| Nav | `role="tablist"` `aria-label="Rubriques des paramètres"` `sm:w-44` | mêmes rôle, nom, ids `settings-tab-${id}`, `aria-selected` / `aria-controls` / roving (flèches, Home, End) ; `max-[1023px]:grid max-[1023px]:grid-cols-3 min-[1024px]:block min-[1024px]:w-60` (**pas** `sm:block` : entre 640 px et 1023 px `sm:block` et `max-[1023px]:grid` ont la même spécificité ; la maquette, `parametres.html:30`, passe en 3 colonnes sous 1024 px) ; courant : `aria-selected` `bg-accent-tint text-accent font-semibold` (plus de `border-r-2 border-accent-cyan`) ; inactif : `text-text-muted hover:bg-surface-2 hover:text-text` ; `min-h-9 px-3 text-sm` ; icône Lucide 18 px |
| Libellés | Profil, IA, Services, Accessibilité, Outils, Agents, Confidentialité, Avancé, À propos | Profil ; **Service d'IA** ; **Services et connecteurs** ; **Accessibilité et affichage** ; Outils ; Agents ; **Sécurité et confidentialité** ; Avancé ; **À propos et mise à jour** |
| Mode contributeur | interrupteur 20 px, libellé `text-xs` | interrupteur `w-10 h-6` (`role` natif du `input` `data-testid="ux-mode-toggle"`) dans un `<label>` qui ne contient **que** l'interrupteur et le libellé `text-sm font-medium` « Mode Contributeur » ; l'aide `text-xs text-text-muted` « Fonctions avancées » est un `<p>` **hors** du `label` (garde 7 : pas de `text-xs` dans le sous-arbre d'un interactif) ; `settings-hidden-tabs` inchangé (« Masquées ici : Outils, Agents, Avancé. ») |
| Pied | Fermer ghost + Enregistrer primary (onglet profil) | `Button variant="ghost" size="md"` Fermer ; `Button variant="primary" size="md"` `data-testid="settings-save-btn"` : « Enregistrement... » / « Enregistrer », mêmes `disabled` |

## 2. Alertes et chargement de la coque

Si `loading` : uniquement les six squelettes + `role="status"` « Lecture des
réglages… » ; `loadWarnings`, `error` et `operationStatus` sont **masqués**
(`loadSettings` ne vide pas `error` au début, SettingsModal.tsx:176-177, un
refus précédent resterait à l'écran). Hors chargement, ordre dans le
`tabpanel` : alertes de coque, puis le contenu de la rubrique.

Extension de primitive, testée (`Alerte.tsx`, `Alerte.test.tsx`) : `ton?:
'erreur' | 'attention'` (défaut `'erreur'`). `'erreur'` inchangé
(`bg-[var(--color-error-tint)] border-error/30`, titre `text-error`).
`'attention'` : `bg-[var(--color-warning-tint)] border-warning/30`, titre
`text-warning`. `role="alert"` dans les deux cas. Lot 2 a déjà ajouté
`action` et l'étalement des attributs ; ce lot n'y touche pas.

| État | Aujourd'hui | Cible |
|---|---|---|
| chargement | `Spinner taille="zone"` centré | six rangées `aria-hidden` en grille `grid-cols-2 gap-2.5` : chaque cellule `Squelette largeur="w-full" classeBarre="h-16 rounded-sm"` ; puis `role="status"` `text-sm text-text-muted` « Lecture des réglages… » ; **rien d'autre** |
| lecture partielle (`loadWarnings`) | bandeau maison `settings-load-warning` `bg-[var(--color-warning-tint)]` | `Alerte ton="attention"` `data-testid="settings-load-warning"` `icone={<AlertCircle className="h-[18px] w-[18px]" />}` ; titre : 1 warning → « Ce réglage n’a pas pu être lu » ; N > 1 → « Ces réglages n’ont pas pu être lus » ; `children` = « : {liste}. Les valeurs affichées ici sont des valeurs par défaut, pas ta configuration réelle. » ; `action` = `Button variant="secondary" size="md"` « Réessayer le chargement » (`onClick={() => void loadSettings()}`) |
| `operationStatus` | `role="status"` teinté info | `p role="status"` `px-4 py-3 text-sm text-info` (pas `Alerte` : ce n'est pas une erreur) |
| `error` de coque | bandeau + Réessayer si `retryOperation` | `Alerte` (ton défaut `'erreur'`) `icone={AlertCircle 18 px}` `children={error}` ; `action` = `Button variant="ghost" size="md"` « Réessayer » **si** `retryOperation` (même quand `loadWarnings.length > 0` : ce bouton appelle `retryOperation()`, pas `loadSettings`) |

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
- Grille `grid grid-cols-1 min-[840px]:grid-cols-2 gap-2.5 px-4 pb-4`.

Chaque fournisseur = **un** `button role="radio"`. `onKeyDown` **ne** délègue
**pas** à `handleRovingFocus` (rovingFocus.ts:33-35 : `next.focus()` puis
`next.click()` ; `click()` appellerait `onSelectProvider` → `setLLMConfig`).
Handler local : flèches / Home / End déplacent le `tabIndex` 0 et le `focus()`
le long de l'ordre DOM (les quatre flèches, comme `orientation="both"`)
**sans** `click()`. `setLLMConfig` uniquement sur activation native (`click`,
Espace, Entrée). `handleRovingFocus` et son `click()` restent inchangés pour
les autres appelants. En grille 2 colonnes, `ArrowDown` va au voisin DOM
(colonne de droite) : ce n'est qu'un déplacement de focus.

`grid grid-cols-[1fr_auto] gap-x-2.5 gap-y-0.5 p-3 rounded-sm border text-left text-sm min-h-9` ;
courant (`aria-checked`) : `border-accent bg-accent-tint` + `outline outline-2 outline-offset-0 outline-ring` ;
sinon `border-border hover:bg-surface-2` ; Ollama indisponible : `disabled`
`opacity-50 cursor-not-allowed` (comme aujourd'hui) ;
`focus-visible:outline focus-visible:outline-[3px] focus-visible:outline-offset-2 focus-visible:outline-ring`.
Titre : `font-semibold` = `provider.name`. Ligne `.quoi` : `col-span-2 text-sm text-text-muted` = `provider.description` ; si `provider.id === 'ollama'` et `ollamaStatus` : N = `ollamaStatus.models.length` (pas `ollamaModels`, `string[]` sans le champ), « 1 modèle installé » / « N modèles installés » (`N > 1`) ; « · outils pris en charge » seulement si `selectedProvider === 'ollama'` **et** `const fiche = ollamaStatus.models.find((m) => m.name === selectedModel)` est défini **et** `fiche.gere_les_outils === true` (`undefined` n'affiche pas la mention ; `gere_les_outils !== false` ment hors Ollama, où `find` est `undefined` et `undefined !== false` est vrai ; `OllamaModel.gere_les_outils?: boolean`, config.ts:241) ; si Ollama disponible et N = 0 : « Aucun modèle installé ». Droite : étiquettes de gauche à droite :

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

Seconde `Carte` si `needsApiKey` (pas Ollama). `CarteTete` titre =
`Clé API {currentProviderConfig.name}`, meta : `hasApiKey` → « La clé est
chiffrée sur ton ordinateur et n'est jamais affichée en entier. » ; sinon →
« Nécessaire pour utiliser ce fournisseur ».

Booléen `cleInvalide` (état de `SettingsModal`, passé à `LLMTab`) : posé
`true` uniquement dans `handleSaveApiKey` (vide « Entre une clé API »,
préfixe `La clé API doit commencer par "${providerConfig.keyPrefix}"`, catch
de `setApiKey`) ; remis à `false` dès `setError(null)` sur ce chemin, ou
succès. Les `setError` de `setLLMConfig` (fournisseur, modèle), Groq, Brave,
dossier, profil, Ollama, ToolsPanel, stats, recherche web, extraction **ne**
posent **pas** `cleInvalide`.

| Élément | Aujourd'hui | Cible |
|---|---|---|
| Statut | bandeaux « Clé API configurée » / « Aucune clé » / « corrompue » | **retirés** : l'étiquette de la grille (§ 3) dit l'état ; le refus vit dans l'`Alerte` |
| Champ | `<input id="settings-api-key">` maison + œil `absolute` + « Sauver » | `FormField label="Clé d'API" htmlFor="settings-api-key"` n'a **qu'un** enfant : `Input id="settings-api-key"` `type={showApiKey ? 'text' : 'password'}` `className="font-mono tracking-widest"` `error={cleInvalide}` (`Input` pose `aria-invalid` + bordure, Input.tsx:27 ; `FormField` sans prop `error`, sinon `Children.map` clonerait `aria-invalid` sur tout enfant, FormField.tsx:41-48). À côté, **hors** de `FormField`, rangée `flex gap-2 items-center` (maquette `.cle`, pas d'overlay : le `relative` d'`Input` est interne, Input.tsx:19, un œil `absolute` ne s'y cale pas) : le `FormField` `flex-1` ; `Button variant="ghost" size="icon"` œil `aria-label` / `aria-pressed` conservés (B-526) ; `Button variant="primary" size="md"` : `hasApiKey` → « Remplacer », sinon « Enregistrer » ; `saving` → `Spinner taille="bouton"` ; `disabled={saving \|\| !apiKeyInput.trim()}` ; Entrée inchangée |
| Succès | `role="status"` « Clé API enregistrée » | inchangé (B-201) |
| Refus | `<p role="alert">` + `error` | `Alerte` (ton `'erreur'`) `icone={AlertCircle 18 px}` `children={error}` sans `action` si le refus vient de `handleSaveApiKey` (pas de `retryOperation` sur ce chemin) |
| Lien console | `text-xs` | inchangé, `text-sm` |
| Ollama | bandeau + Re-tester `size="sm"` | `Alerte` si indisponible (`ollamaStatus.error \|\| 'Ollama non disponible'`) ; sinon `p role="status"` « Ollama connecté ({base_url}) » ; `Button variant="ghost" size="md"` `aria-label="Re-tester la connexion Ollama"` |
| Modèle | `<select id="settings-llm-model">` + « Custom » | rangée `grid grid-cols-[1fr_auto] items-center gap-4 py-2.5 border-t border-border px-4` : `<label htmlFor="settings-llm-model" className="text-sm font-semibold">Modèle</label>` (pas un `<b>` : le `Select` n'aurait plus de nom accessible, WCAG 4.1.2 ; `getByLabelText('Modèle')` de `SettingsModal.fournisseurIA.test.tsx:93` et `LLMTab.test.tsx:49`) + `Select id="settings-llm-model"` `options` = `availableModels` (label `name` + badge entre parenthèses, comme aujourd'hui) ; Custom, modèle hors liste, Qwen : inchangés sauf boutons `md` et `Input` / `FormField` ; Qwen : le bouton d'adresse dit **« Enregistrer l'adresse »** (jamais « Enregistrer » : collision avec la clé si `!hasApiKey` ; `LLMTab.qwen.test.tsx:70` `name: 'Enregistrer'` à aligner) |
| Effort | `<select id="llm-effort">` | même rangée ; `<label htmlFor="llm-effort" className="text-sm font-semibold">Effort de raisonnement</label>` + `Select id="llm-effort"` (`getByLabelText('Effort de raisonnement')` et `aria-describedby`, `LLMTab.effortOpenAI.test.tsx:20`) ; options et `disabled={saving}` inchangés ; `data-testid="effort-mention-outils"` : `text-sm` (plus `text-xs` sur un texte lié à un interactif) ; erreur d'effort : `Alerte` + `Button variant="ghost" size="md"` « Réessayer l'effort » (`onClick={() => failedEffort && void handleChange(failedEffort)}`, LLMTab.tsx:668) — **toujours** rendu si `failedEffort`, même si la coque a `retryOperation` ou `loadWarnings` |

Pas de jauge « Ce mois-ci », pas d'interrupteur d'accord cloud (P-088).
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
- Première `Carte`, grille `grid grid-cols-1 min-[840px]:grid-cols-2 gap-x-4`
  `px-4 pb-4` : **uniquement** l'identité, chaque champ = `FormField` +
  `Input` (ou `Textarea` pour le contexte), **mêmes `id`**, mêmes
  `placeholder`, mêmes handlers. Ids de cette carte :
  `settings-profile-name`, `settings-profile-nickname`,
  `settings-profile-company`, `settings-profile-role`,
  `settings-profile-email`, `settings-profile-location`,
  `settings-profile-context`. Libellés conservés (Nom complet *, Surnom,
  Entreprise, Rôle, Email, Localisation). Contexte : label « Ce que Thérèse
  doit savoir » (la maquette), description actuelle conservée en
  `FormField description`. `saved` → `role="status"` « Profil enregistré » ;
  `error` local → `Alerte` sans Réessayer.
- Seconde `Carte` : `CarteTete` titre « Profil émetteur des factures », meta
  « SIRET, TVA, adresse et mentions légales, utilisés sur chaque devis et
  facture. » **Seule** occurrence des champs facture, éditables (pas un
  résumé Complet : P-090), mêmes `id` / handlers / placeholders. Ids de
  cette carte : `settings-profile-address`, `settings-profile-siren`,
  `settings-profile-tva`, `settings-profile-siret`, `settings-profile-ape`,
  `settings-profile-nda`. Libellés conservés (Adresse, SIREN, TVA, SIRET,
  APE, NDA). Un `id` n'apparaît qu'une fois dans le document.
- `DemoModeSection` : `data-testid="mode-demo-section"` conservé ; tête en
  `text-sm` ; interrupteur `w-10 h-6` ; prose B-131 inchangée ; état actif
  `Alerte` n'est pas le bon ton : `p role="status"` « Mode démo actif - … ».
- Modale THERESE.md : hors restyle profond (overlay `bg-black/60` du motif
  commun) ; boutons `md`.

Le pied de la coque reste le seul « Enregistrer » (testid) du profil.

## 6. Les états (priorité)

Sur le panneau visible, de haut en bas :

1. si `loading` : uniquement squelettes + « Lecture des réglages… »
   (`loadWarnings` / `error` / `operationStatus` masqués, même non nuls) ;
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
`ProfileTab.da.test.tsx`, `Alerte.test.tsx` étendu, rouges d'abord) :

1. nav : 9 ids, libellés cibles (§ 1), `aria-selected` sur l'onglet courant,
   `settings-tab-ai` / `settings-hidden-tabs` / `ux-mode-toggle` présents ;
   classes de la nav : `max-[1023px]:grid-cols-3` et `min-[1024px]:block`,
   **pas** `sm:block` ;
2. une carte fournisseur = un `radio`, grille 2 colonnes dès 840 px, l'état
   porte `data-etiquette` ; P-018 : un fournisseur à clé hors sélection reste
   visible avec « Clé enregistrée » ; le courant sans clé porte « Actif »
   **et** « Sans clé » ;
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
   ssi `failedEffort` ; zéro de ces trois pendant `loading` ; zéro sur IA
   sans erreur ni warning ;
6. Profil : les 13 `id` `settings-profile-*` existent **une fois**, `FormField`
   pose le label, identité et émetteur ne partagent aucun `id` ;
   `settings-save-btn` unique ; `mode-demo-section` présent ;
7. aucune classe `text-xs` sur un interactif **ni dans son sous-arbre**
   (SettingsModal, LLMTab, ProfileTab) ; l'aide « Fonctions avancées » est
   hors du `<label>` du checkbox ; `CarteTete` `meta` (`text-xs font-medium`,
   Carte.tsx:53) n'est **pas** une violation (paragraphe, hors interactif) ;
   `aucuneCouleurEnDur` étendu aux trois fichiers ; boutons `sm` absents ;
8. `h1#settings-title` « Paramètres », **sans** `font-editorial`.

À aligner, forme seulement : `SettingsModal.fermeture.test.tsx` (libellé
d'onglet jamais lu, testid conservés) ; `LLMTab.refusAnnonce.test.tsx` (l'alerte
peut être `Alerte`, le rôle et la chaîne `REFUS` restent) ;
`LLMTab.effortOpenAI.test.tsx` (`effort-mention-outils`,
`getByLabelText('Effort de raisonnement')`, `aria-describedby`) ;
`SettingsModal.fournisseurIA.test.tsx` (`getByLabelText('Modèle')`) ;
`LLMTab.test.tsx` (`getByLabelText('Modèle')`) ;
`LLMTab.qwen.test.tsx` (`name: 'Enregistrer l'adresse'`) ;
`modeDemoPerimetre.test.tsx` (prose B-131) ;
`Alerte.test.tsx` (ton `'attention'` : `bg-[var(--color-warning-tint)]`,
titre `text-warning` ; le défaut reste `'erreur'`). Aucune assertion de
comportement n'est retirée. Onboarding (`Sauver` de `LLMStep`) hors lot.

## 8. Ce que ce lot ne fait pas

- Paramètres en page, rail `aria-current`, colonne 72 rem hors modale : **P-086**
  (à attribuer par l'orchestrateur).
- Tester / quatre derniers caractères / date de vérification / badge
  « Clé refusée » distinct d'une clé encore en place : **P-012** déjà au
  portail. Service cloud 503 (« Indisponible depuis HH:MM ») : même fiche,
  l'app ne le connaît que pour Ollama.
- Carte « Autres + 6 » (masquerait GLM, Kimi, Qwen, MiniMax ; Groq n'est pas
  un fournisseur LLM) : **P-087**.
- Jauge « Ce mois-ci » et accord cloud dans Service d'IA (les données vivent
  dans `LimitsTab` / `PrivacyTab`) : **P-088**.
- Rubriques de premier rang « Coûts et limites », « Stockage et sauvegardes »,
  item « Katia et Zézette » ; scinder Nom complet / Surnom en Prénom / Nom ;
  carte émetteur résumé « Complet » qui cacherait les champs : **P-089**.
- Restyle des contenus Services, Accessibilité, Confidentialité, À propos,
  Avancé, Outils, Agents (non maquettés). `LimitsTab` reste dans Avancé.
- Aucun changement de données, d'API, de store ni de navigation.
- Pas de navigation bidimensionnelle dans `rovingFocus.ts` (les flèches
  restent un cran DOM) ; pas de `click()` retiré du helper global.

## 9. Plan de preuve

1. Tests rouges d'abord (§ 7), vérifiés rouges pour la bonne raison,
   sabotage par remplacement inverse, `.agents-sync-paused` posé.
2. Six portes : ruff, pytest (XML), vitest json, tsc, eslint (27), mypy 951.
3. Recette visuelle sur la pile jetable (17393 et 1420, jamais 17293) :
   états forcés par interception de `/api/config/` (clés, `corrupted_keys`),
   `/api/config/llm`, `/api/config/profile`, `/api/config/ollama/status`
   (Playwright `page.route`) : IA avec Ollama actif et 2 modèles ; IA avec
   OpenAI `has_openai_key` ; IA sans clé ; refus de préfixe (saisie `sk-`
   chez Anthropic) ; lecture `clés API` en échec ; Profil Marie Exemple ;
   chargement lent. Largeurs 1280, 1024, 1023, 840, 800 px ; clair, sombre,
   contraste élevé ; trois tailles de police. Captures
   `.cartography-work/validation/da-lot9/`, rapport
   `docs/da/2026-09-11-lot9-recette.md`. Vérifier : nav 3 colonnes à 800 px
   **et** à 1023 px (à 1024 px la grille reste `15rem 1fr`, maquette
   `max-width:1023px`) ; grille fournisseurs 1 colonne à 800 px, 2 colonnes
   dès 840 px ; anneau 3 px sur un radio et sur un onglet ; un Réessayer par
   action (chargement / enregistrement / effort), pas un seul pour les trois ;
   clé jamais en clair une fois enregistrée ; dollars absents de l'onglet IA
   (ils restent dans Avancé) ; overlay `fixed inset-0` (décision 1, BUG-156)
   recouvre établi et composeur : les juger **derrière** l'overlay, pas
   à côté.
4. Revue Grok du diff avant le tag, `/release-therese 0.72.0-alpha` avec le
   GO de Ludo (toute la DA, pas ce lot seul).

## Points non repris

Aucun. Les 15 points de
`.cartography-work/reviews/grok-da-lot9-parametres-design-v1.log` sont
fondés (preuve relue dans maquette, `base.css`, `Alerte.tsx:12`,
`FormField.tsx:41-48`, `Input.tsx:19`, `Carte.tsx:53`, `rovingFocus.ts:10-35`,
`config.ts:241`, `SettingsModal.tsx:176-177, 462-467, 653, 754, 856`,
`LLMTab.tsx:478, 668`, tests cités).
