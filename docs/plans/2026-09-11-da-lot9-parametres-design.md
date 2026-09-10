# DA « Application affinée », lot 9 : l'écran Paramètres (design à challenger avant le code)

Version 1, 11/09/2026. Précédent : lot 3 (Tiroir), sur `main` ; cadence : une
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
| Tête | `<h2 className="text-lg">Paramètres` + fermer | `<h1 id="settings-title" className="font-editorial">Paramètres</h1>` ; le dialogue passe `aria-labelledby="settings-title"` et **garde** `aria-label="Paramètres"` (filet) ; `Button variant="ghost" size="icon"` `data-testid="settings-close-btn"` `aria-label="Fermer les paramètres"` |
| Nav | `role="tablist"` `aria-label="Rubriques des paramètres"` `sm:w-44` | mêmes rôle, nom, ids `settings-tab-${id}`, `aria-selected` / `aria-controls` / roving (flèches, Home, End) ; `w-60` (15 rem) ; sous `max-[1023px]:grid max-[1023px]:grid-cols-3` `sm:block` ; courant : `aria-selected` `bg-accent-tint text-accent font-semibold` (plus de `border-r-2 border-accent-cyan`) ; inactif : `text-text-muted hover:bg-surface-2 hover:text-text` ; `min-h-9 px-3 text-sm` ; icône Lucide 18 px |
| Libellés | Profil, IA, Services, Accessibilité, Outils, Agents, Confidentialité, Avancé, À propos | Profil ; **Service d'IA** ; **Services et connecteurs** ; **Accessibilité et affichage** ; Outils ; Agents ; **Sécurité et confidentialité** ; Avancé ; **À propos et mise à jour** |
| Mode contributeur | interrupteur 20 px, libellé `text-xs` | interrupteur `w-10 h-6` (`role` natif du `input` `data-testid="ux-mode-toggle"`) ; libellé `text-sm font-medium` « Mode Contributeur » ; aide `text-xs` « Fonctions avancées » ; `settings-hidden-tabs` inchangé (« Masquées ici : Outils, Agents, Avancé. ») |
| Pied | Fermer ghost + Enregistrer primary (onglet profil) | `Button variant="ghost" size="md"` Fermer ; `Button variant="primary" size="md"` `data-testid="settings-save-btn"` : « Enregistrement... » / « Enregistrer », mêmes `disabled` |

## 2. Alertes et chargement de la coque

Ordre dans le `tabpanel` : alertes de coque, puis le contenu de la rubrique.

| État | Aujourd'hui | Cible |
|---|---|---|
| chargement | `Spinner taille="zone"` centré | six rangées `aria-hidden` en grille `grid-cols-2 gap-2.5` : chaque cellule `Squelette largeur="w-full" classeBarre="h-16 rounded-sm"` ; puis `role="status"` `text-sm text-text-muted` « Lecture des réglages… » |
| lecture partielle (`loadWarnings`) | bandeau maison `settings-load-warning` | `Alerte data-testid="settings-load-warning"` `icone={<AlertCircle className="h-[18px] w-[18px]" />}` ; titre : 1 warning → « Ce réglage n’a pas pu être lu » ; N > 1 → « Ces réglages n’ont pas pu être lus » ; `children` = « : {liste}. Les valeurs affichées ici sont des valeurs par défaut, pas ta configuration réelle. » ; `action` = `Button variant="secondary" size="md"` « Réessayer le chargement » |
| `operationStatus` | `role="status"` teinté info | `p role="status"` `px-4 py-3 text-sm text-info` (pas `Alerte` : ce n'est pas une erreur) |
| `error` de coque | bandeau + Réessayer si `retryOperation` | `Alerte` `icone={AlertCircle 18 px}` `children={error}` ; `action` = `Button variant="ghost" size="md"` Réessayer **seulement** si `retryOperation` ; un seul Réessayer dans la coque |

`Alerte` n'a que le ton `erreur` : le warning de lecture réutilise `Alerte`
(rôle `alert`) ; le titre porte le mot « lu », pas « Indisponible ».

## 3. Service d'IA : `LLMTab` dans `Carte`

- `Carte as="section"` `aria-labelledby="settings-ia-title"`.
- `CarteTete idTitre="settings-ia-title"` icône `Cpu` 18 px, titre « Service
  d'IA », meta « Le modèle qui répond. En local, rien ne quitte ton
  ordinateur. En ligne, chaque fournisseur demande ton accord une fois. »
- Grille `grid grid-cols-1 min-[840px]:grid-cols-2 gap-2.5 px-4 pb-4`.

Chaque fournisseur = **un** `button role="radio"` (roving vertical conservé) :

`grid grid-cols-[1fr_auto] gap-x-2.5 gap-y-0.5 p-3 rounded-sm border text-left text-sm min-h-9` ;
courant (`aria-checked`) : `border-accent bg-accent-tint` + `outline outline-2 outline-offset-0 outline-ring` ;
sinon `border-border hover:bg-surface-2` ; Ollama indisponible : `disabled`
`opacity-50 cursor-not-allowed` (comme aujourd'hui) ;
`focus-visible:outline focus-visible:outline-[3px] focus-visible:outline-offset-2 focus-visible:outline-ring`.
Titre : `font-semibold` = `provider.name`. Ligne `.quoi` : `col-span-2 text-sm text-text-muted` = `provider.description` ; si `provider.id === 'ollama'` et `ollamaStatus` : N = `ollamaModels.length`, « 1 modèle installé » / « N modèles installés » (`N > 1`) + (si le modèle sélectionné a `gere_les_outils !== false` : « · outils pris en charge ») ; si Ollama disponible et N = 0 : « Aucun modèle installé ». Droite : une `Etiquette` selon la **première** règle vraie :

1. `corruptedKeys.includes(id)` → `ton="erreur"` « Clé corrompue »
2. `id === 'ollama' && !ollamaStatus?.available` → `ton="attention"` « Indisponible »
3. `id === selectedProvider` → `ton="succes"` « Actif »
4. `id !== 'ollama' && apiKeys[id]` → `ton="info"` « Clé enregistrée »
5. `id !== 'ollama'` → `ton="neutre"` « Sans clé »

Anthropic : l'étiquette « Recommandé » actuelle **en plus**, `ton="info"`,
à gauche de l'état. Pastilles Check / Key / XCircle retirées (l'étiquette
porte l'état).

## 4. Carte clé, modèle, effort

Seconde `Carte` si `needsApiKey` (pas Ollama). `CarteTete` titre =
`Clé API {currentProviderConfig.name}`, meta : `hasApiKey` → « La clé est
chiffrée sur ton ordinateur et n'est jamais affichée en entier. » ; sinon →
« Nécessaire pour utiliser ce fournisseur ».

| Élément | Aujourd'hui | Cible |
|---|---|---|
| Statut | bandeaux « Clé API configurée » / « Aucune clé » / « corrompue » | **retirés** : l'étiquette de la grille (§ 3) dit l'état ; le refus vit dans l'`Alerte` |
| Champ | `<input id="settings-api-key">` maison + œil + « Sauver » | `FormField label="Clé d'API" htmlFor="settings-api-key"` + `Input id="settings-api-key"` `type={showApiKey ? 'text' : 'password'}` `className="font-mono tracking-widest"` `aria-invalid` si `error` ; bouton œil `Button variant="ghost" size="icon"` `aria-label` / `aria-pressed` conservés (B-526) ; `Button variant="primary" size="md"` : `hasApiKey` → « Remplacer », sinon « Enregistrer » ; `saving` → `Spinner taille="bouton"` ; `disabled={saving \|\| !apiKeyInput.trim()}` ; Entrée inchangée |
| Succès | `role="status"` « Clé API enregistrée » | inchangé (B-201) |
| Refus | `<p role="alert">` + `error` | `Alerte` `icone={AlertCircle 18 px}` `children={error}` sans `action` (la coque porte Réessayer s'il y a `retryOperation`) |
| Lien console | `text-xs` | inchangé, `text-sm` |
| Ollama | bandeau + Re-tester `size="sm"` | `Alerte` si indisponible (`ollamaStatus.error \|\| 'Ollama non disponible'`) ; sinon `p role="status"` « Ollama connecté ({base_url}) » ; `Button variant="ghost" size="md"` `aria-label="Re-tester la connexion Ollama"` |
| Modèle | `<select id="settings-llm-model">` + « Custom » | rangée `grid grid-cols-[1fr_auto] items-center gap-4 py-2.5 border-t border-border px-4` : `<b className="text-sm">Modèle</b>` + `Select id="settings-llm-model"` `options` = `availableModels` (label `name` + badge entre parenthèses, comme aujourd'hui) ; Custom, modèle hors liste, Qwen : inchangés sauf boutons `md` et `Input` / `FormField` |
| Effort | `<select id="llm-effort">` | même rangée ; `Select id="llm-effort"` ; options et `disabled={saving}` inchangés ; `data-testid="effort-mention-outils"` : `text-sm` (plus `text-xs` sur un texte lié à un interactif) ; erreur d'effort : `Alerte` + `Button variant="ghost" size="md"` Réessayer (uniquement dans cette carte, si la coque n'en a pas : `!retryOperation && !loadWarnings.length`) |

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
- Grille `grid grid-cols-1 min-[840px]:grid-cols-2 gap-x-4` `px-4 pb-4` :
  chaque champ devient `FormField` + `Input` (ou `Textarea` pour le contexte),
  **mêmes `id`**, mêmes `placeholder`, mêmes handlers. Libellés conservés
  (Nom complet *, Surnom, Entreprise, Rôle, Email, Localisation, Adresse,
  SIREN, TVA, SIRET, APE, NDA). Contexte : label « Ce que Thérèse doit
  savoir » (la maquette), description actuelle conservée en
  `FormField description`. `saved` → `role="status"` « Profil enregistré » ;
  `error` local → `Alerte` sans Réessayer.
- Seconde `Carte` : `CarteTete` titre « Profil émetteur des factures », meta
  « SIRET, TVA, adresse et mentions légales, utilisés sur chaque devis et
  facture. » Les champs facture (adresse, SIREN, TVA, SIRET, APE, NDA) y
  **restent éditables** (pas un résumé Complet : P-090).
- `DemoModeSection` : `data-testid="mode-demo-section"` conservé ; tête en
  `text-sm` ; interrupteur `w-10 h-6` ; prose B-131 inchangée ; état actif
  `Alerte` n'est pas le bon ton : `p role="status"` « Mode démo actif - … ».
- Modale THERESE.md : hors restyle profond (overlay `bg-black/60` du motif
  commun) ; boutons `md`.

Le pied de la coque reste le seul « Enregistrer » (testid).

## 6. Les états (priorité)

Sur le panneau visible, de haut en bas, **exactement** l'ordre actuel de
`renderContent` + bandeaux de coque : 1) chargement (rien d'autre) ;
2) `loadWarnings` ; 3) `operationStatus` ; 4) `error` de coque ; 5) corps
de la rubrique (IA : grille, carte clé si besoin, Ollama, modèle, effort,
Qwen ; Profil : carte identité, carte émetteur, démo). Un seul « Réessayer »
**de coque** à la fois (`loadWarnings` gagne sur `retryOperation` : on n'en
rend pas deux). L'effort n'ajoute le sien que si la coque n'en a pas.

`invalide` (maquette) = `error` non nul sur l'onglet `ai`, clé précédente
intact (`apiKeys` non muté, déjà le cas). `profil` = `activeTab === 'profile'`.
`normal` = `activeTab === 'ai'` sans erreur.

## 7. Gardes mécaniques et tests à aligner

Nouveaux (`SettingsModal.da.test.tsx`, `LLMTab.da.test.tsx`,
`ProfileTab.da.test.tsx`, rouges d'abord) :

1. nav : 9 ids, libellés cibles (§ 1), `aria-selected` sur l'onglet courant,
   `settings-tab-ai` / `settings-hidden-tabs` / `ux-mode-toggle` présents ;
2. une carte fournisseur = un `radio`, grille 2 colonnes dès 840 px, l'état
   porte `data-etiquette` ; P-018 : un fournisseur à clé hors sélection reste
   visible avec « Clé enregistrée » ;
3. pluriel Ollama : 0 / 1 / 2 modèles, chaînes exactes ;
4. « Enregistrer » vs « Remplacer » selon `hasApiKey` ; `settings-api-key`
   `aria-invalid` si `error` ; B-201 : `getByRole('alert')` contient le refus,
   le succès reste « Clé API enregistrée » ;
5. un « Réessayer » (nom `/^Réessayer/`) dans la modale sur lecture en panne,
   zéro sur chargement et sur IA sans erreur ; « Réessayer le chargement »
   unique quand `loadWarnings` ;
6. Profil : les 13 `id` `settings-profile-*` existent, `FormField` pose le
   label, `settings-save-btn` unique ; `mode-demo-section` présent ;
7. aucune classe `text-xs` sur un interactif **ni dans son sous-arbre**
   (SettingsModal, LLMTab, ProfileTab) ; `aucuneCouleurEnDur` étendu aux
   trois fichiers ; boutons `sm` absents ;
8. `h1#settings-title` « Paramètres », `font-editorial`.

À aligner, forme seulement : `SettingsModal.fermeture.test.tsx` (libellé
d'onglet jamais lu, testid conservés) ; `LLMTab.refusAnnonce.test.tsx` (l'alerte
peut être `Alerte`, le rôle et la chaîne `REFUS` restent) ;
`LLMTab.effortOpenAI.test.tsx` (`effort-mention-outils`) ;
`modeDemoPerimetre.test.tsx` (prose B-131). Aucune assertion de comportement
n'est retirée. Onboarding (`Sauver` de `LLMStep`) hors lot.

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
   chargement lent. Largeurs 1280, 1024, 840, 800 px ; clair, sombre,
   contraste élevé ; trois tailles de police. Captures
   `.cartography-work/validation/da-lot9/`, rapport
   `docs/da/2026-09-11-lot9-recette.md`. Vérifier : nav 3 colonnes à 1024 px,
   grille fournisseurs 1 colonne à 800 px, anneau 3 px sur un radio et sur
   un onglet, un seul Réessayer par état, clé jamais en clair une fois
   enregistrée, dollars absents de l'onglet IA (ils restent dans Avancé),
   établi visible, composeur non recouvert.
4. Revue Grok du diff avant le tag, `/release-therese 0.72.0-alpha` avec le
   GO de Ludo (toute la DA, pas ce lot seul).
