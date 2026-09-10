# DA « Application affinée », lot 3 : l'écran Tiroir (design à challenger avant le code)

Version 1, 11/09/2026. Précédent : lot 2 (Accueil), livré sur `main` ;
cadence : une seule release pour toute la DA (décision Ludo 11/09, 0.72.0-alpha
porte l'ensemble). Maquette :
`docs/da/2026-09-05-propositions/maquettes/tiroir.html` (états `normal`,
`catalogue`, `vide`), critères de `ecrans.json` : « Retrouver, relancer,
comprendre les 30 capacités sans lire 90 puces. Distinguer retrouver une
conversation et choisir une capacité ; destinations directes conservées ;
détails accessibles progressivement. » Déjà décidé côté UX, pas à rejuger :
commande « Conversations » rebranchée (le store `showConversationSidebar`
ouvre le tiroir vivant) ; 20 destinations ouvertes au clic, 3 prompts
(`web-research`, `legal`, `skills-commands`) relus avant envoi (27/08,
`CarteOuvreSaDestination.test.tsx`) ; région nommée « Conversations » (P-053) ;
fantôme ⌘N absent, brouillon local listé (P-054, revue 0.69.0) ; puces
d'infrastructure retirées, champ `features` conservé pour la recherche
(entrée 7).

## Ce que le lot change, en une phrase

Le tiroir vivant (`PrototypeConversationDrawer.tsx`) et le catalogue
(`CapabilityCenter`, fonction du même nom) prennent la forme de la maquette
en consommant les primitives du lot 1 (`Button`, `Input`, `EtatVide`,
`Alerte`, `Etiquette`) ; les mêmes données, les mêmes états, les mêmes
destinations. Aucun appel réseau, aucun store, aucun parcours ne change.

## Décisions tranchées par défaut (Ludo peut corriger)

1. **Le tiroir affiché n'est pas `ConversationSidebar.tsx`** (zéro import hors
   deux tests). Leçon B-613 : on habille `PrototypeConversationDrawer`, monté
   ligne 1659 de la coque. `ConversationSidebar` hors lot.
2. Conversations et Capacités restent deux surfaces (tiroir région / dialogue
   modal). Les onglets de la maquette sont une fonctionnalité (P-068, § 8).
3. Les six groupes et les 30 ids du catalogue 0.40 restent ; les six
   intentions maquettées (autres titres, scissions, fusions) sont P-069.
4. Pas d'étiquette Action / Décision / Document sur une conversation : ces
   genres n'existent pas dans le store. L'aperçu du dernier message non plus
   dans le tiroir vivant. Les deux vont à P-070.
5. `TrustCenter` (même fichier que le catalogue) n'est pas l'écran : hors lot,
   y compris ses ombres `rgba`.
6. Toute taille de bouton est `md` (36 px) ou `icon` (36 px) ; `sm` n'y est
   pas employé. « Nouvelle conversation » est le geste principal, en `md`
   pleine largeur (le `.btn-primaire` de la maquette fait 2,25 rem).
7. Les libellés de la maquette remplacent la prose là où l'état est le même
   (vide sans requête, titre du catalogue, pied du catalogue). Un état sans
   équivalent maquetté garde ses mots (recherche vide, verrouillage, erreurs
   de renommage / suppression / export, « Brouillon en attente »,
   « non enregistrée »).

## 1. Le tiroir des conversations : coque du panneau

Maquette `.tiroir` : `width: 22rem`, grille `auto auto 1fr auto`, `role="region"`.

| Élément | Aujourd'hui | Cible |
|---|---|---|
| Panneau | `aside` `w-[306px]` `left-16` `shadow-[12px_0_40px_rgba(16,28,54,0.10)]` `xl:relative xl:left-0 xl:shadow-none` | mêmes `role="region"`, `aria-labelledby="prototype-conversation-drawer-title"`, `tabIndex={-1}`, `data-testid="prototype-conversation-drawer"` ; `w-[22rem]` ; `left-14` (rail lot 1 = `w-14`, plus l'écart de 8 px) ; `shadow-lg xl:shadow-none` ; isolation, voile de la coque, Échap, surfaces `new` / `search` / `history` inchangés |
| Tête | `h-14`, `<span>` 14 px « Conversations », fermer 32 px | `<h2 id="prototype-conversation-drawer-title">Conversations</h2>` (taille du `h2` de `@layer base`, pas `text-sm`) ; `Button variant="ghost" size="icon"` `aria-label="Fermer les conversations"` (libellé conservé, tests et cascade) |
| Recherche | `<input>` maison, placeholder « Rechercher… » | `Input type="search" icon={<Search className="h-[18px] w-[18px]" />}` `aria-label="Rechercher une conversation"` (conservé : les tests ciblent ce nom), `placeholder="Rechercher dans les conversations"`, `data-testid` absent aujourd'hui, on n'en invente pas |
| Geste principal | en tête, classes maison + `shadow-[var(--shadow-card)]` | **pied** `border-t border-border px-4 py-2.5` : `Button variant="primary" size="md" className="w-full"` `ref={newConversationRef}` « Nouvelle conversation », icône `Plus` 18 px ; même `startConversation` |
| Liste | `data-testid="prototype-conversation-list"` | conservé ; `aria-label="Historique des conversations"` conservé |

Pas d'onglets Conversations / Capacités (P-068). Le voile reste
`VoilePanneau` de la coque, non cliquable (BUG-156).

## 2. Les lignes de conversation

Pas `Ligne` : la maquette `.conv` est `1fr auto`, sans puce 2 rem (poser
`Ligne` inventerait une colonne). Chaque entrée reste **un** `button` (plus
le menu d'actions, déjà au-dessus via `absolute`).

| Élément | Aujourd'hui | Cible |
|---|---|---|
| Grille | flex, icône absente, `py-2.5 pr-10` | `grid grid-cols-[1fr_auto] gap-x-2 gap-y-0.5 px-3 py-2.5 pr-11 text-left rounded-sm` ; courant : `aria-current="page"` (conservé, test P-054) `bg-accent-tint` sans bordure extra ; hover `bg-surface-2` ; `focus-visible:outline focus-visible:outline-[3px] focus-visible:outline-offset-[-3px] focus-visible:outline-ring` |
| Titre | `text-sm font-semibold truncate` | inchangé (`.conv b`) ; repli `conversation.title \|\| 'Nouvelle conversation'` inchangé |
| Quand | `updatedLabel` = jour + mois + heure, `text-xs` | `text-sm tabular-nums text-text-muted` ; même `updatedAt` : jour civil = `toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })` ; hier idem ; 2 à 6 jours = `toLocaleDateString('fr-FR', { weekday: 'short' })` ; au-delà = `toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })` ; `Date inconnue` inchangé |
| Compte | `compteMessages` + suffixe sync, `text-xs` | `col-span-2 text-sm text-text-muted truncate` ; chaînes exactes conservées : « Brouillon en attente » si 0 ; « 1 message » / « N messages » si N ≥ 1 (`N > 1`) ; suffixe ` · non enregistrée` si `!synced` |
| Groupe | `text-xs` uppercase + icône `History` 12 px | `text-xs font-semibold uppercase tracking-wider text-text-muted px-2 py-1.5` sans icône (maquette `.groupe`) ; libellés `dateLabel` inchangés (`Aujourd’hui`, `Hier`, `Cette semaine`, mois + année, `Date inconnue`) |
| Menu | déclencheur 28 px, `data-testid="conversation-actions-menu"` | `Button variant="ghost" size="icon"` `aria-label={`Actions pour ${title}`}` et le menu (Renommer, Exporter en Markdown, Exporter en Word, Supprimer) inchangés ; testid conservé |
| Renommer | input maison | `Input aria-label="Nouveau titre"` `maxLength={120}` ; `Button variant="ghost" size="md"` Annuler ; `Button variant="primary" size="md"` Enregistrer ; Entrée / Échap inchangés |
| Suppression | bandeau maison, `data-testid="conversation-delete-confirmation"` | `Alerte` ce testid, titre « Supprimer définitivement cette conversation ? », `action` = Annuler `secondary md` + Confirmer `danger md` « Confirmer la suppression » ; textes des boutons conservés |

Filtre, tri, verrouillage (`navigationLocked`), `openConversation` /
`onClose` / `onOpenChat` : inchangés.

## 3. Le catalogue : `CapabilityCenter` (la fonction, pas `TrustCenter`)

Le catalogue reste un `role="dialog"` `aria-modal="true"` centré, ouvert par
« Plus d'outils », fermé par `onClose` / clic sur le voile (comportement
actuel du modal, distinct du voile du tiroir). `useDialogFocusTrap`,
`data-dialog-autofocus` unique sur le champ, `onChoose` inchangés.

| Élément | Aujourd'hui | Cible |
|---|---|---|
| Cadre | `max-w-[1120px]`, ombre `rgba`, `h-[min(760px,88vh)]` | `shadow-lg` à la place des `rgba` ; `hover:-translate-y-0.5` retiré (leçon du clipping sous le pointeur) ; largeur, `flex-col md:flex-row`, `role="tablist"` / `role="tab"` / `aria-controls` / roving : inchangés (`ResponsiveShellContract` garde `flex-col md:flex-row`) |
| Titre | `<h2 id="capability-center-title">Ce que Thérèse sait mobiliser</h2>` 20 px | même `id`, texte **« Capacités »** ; pastille `{n} capacité{n > 1 ? 's' : ''}` en `text-sm font-semibold text-text-muted` (`n = capabilities.length`, jamais `30` en dur) ; sous-titre « Tu demandes un résultat… » retiré (la maquette n'en a pas ; le pied le dit) |
| Fermer | 44 px, `aria-label="Fermer les capacités"` | `Button variant="ghost" size="icon"`, même `aria-label` |
| Recherche | input maison, `data-dialog-autofocus` | `Input type="search"` même `aria-label="Rechercher une capacité"`, même placeholder, même autofocus |
| Groupes | `shortTitle` 12 px, icône `style={{ backgroundColor: tint }}` | `title` (nom long déjà dans les données) en `text-sm font-semibold` ; compte `n capacité(s)` en `text-sm` ; icône pastille ronde 2 rem `bg-*-tint` **par classes**, table `id → classes` : `organize` agenda, `business` factures, `create` taches, `decide` prospects, `automate` `bg-[var(--color-success-tint)] text-success`, `control` `bg-surface-2 text-text-muted` ; plus aucun `style={{ color }}` ; `id={`capability-group-${id}`}`, `role="tab"`, flèches : inchangés |
| Cartes | bouton 2 col., description 12 px, portraits Board / agents | un bouton pleine largeur, grille `1fr auto` façon `.capacite` : `<b className="text-sm font-semibold">` titre, type à droite (§ 3.1), description `col-span-2 text-sm text-text-muted` ; icône de `capability.icon` 18 px dans la pastille du groupe (plus de `CharacterPortrait`) ; `onClick={() => onChoose(capability)}` inchangé |
| Encadré « Toujours sous contrôle » | 12 px, présent en `md` | retiré (absent de la maquette ; le Centre de confiance reste le bouton de la barre) |
| Pied | deux phrases, 12 px | `text-sm text-text-muted px-4 py-3` : « Une capacité Vue ou Parcours s'ouvre au clic. Une Demande relue pose une phrase dans le composeur, que tu relis avant l'envoi. » |
| Vide recherche | titre + texte 12 px | `EtatVide` titre « Aucune capacité trouvée », texte actuel (« Essaie avec le résultat souhaité, par exemple « devis » ou « analyser ». »), sans action |
| Status | `n capacité(s) affichée(s)` | inchangé, y compris la règle de pluriel `> 1` |

Les 30 ids, `destination` / `scenario`, `features` (recherche) : inchangés.

### 3.1 Type affiché (présentation seule)

Fonction exportée `typeCapacite(item): 'Demande relue' | 'Action' | 'Parcours' | 'Vue'` :

1. `destination.kind === 'prompt'` → « Demande relue » (`text-sm font-semibold text-accent`)
2. sinon `destination.kind === 'follow-ups'` → « Action »
3. sinon `destination.kind === 'action'` et `action === 'guided.open'` → « Action »
4. sinon `scenario` défini → « Parcours »
5. sinon → « Vue »

Les trois prompts restent relus ; ce n'est pas une étiquette `Etiquette`
(la maquette `.type` n'est pas une pilule). Plancher 14 px (la rangée est
un bouton). Ordre de priorité ci-dessus, un seul libellé par carte.

## 4. Les états

Ordre de priorité du **corps du tiroir**, identique à aujourd'hui
(`PrototypeConversationDrawer.tsx` : `filtered.length === 0` puis `query`) :

| État | Aujourd'hui | Cible |
|---|---|---|
| liste, N ≥ 1 | groupes + lignes | § 2 |
| vide avec requête | « Aucune conversation trouvée » | `EtatVide` ce titre, sans action (pas d'équivalent maquette, mots conservés) |
| vide sans requête | « Aucune conversation enregistrée » + « Commence une conversation pour la retrouver ici. » | `EtatVide` titre **« Aucune conversation »**, texte **« Ta première demande à Thérèse apparaîtra ici, avec ce qu'elle a produit. »**, sans action (« Nouvelle conversation » est déjà au pied) |
| erreur d'action | `role="alert"` 12 px, un message | `Alerte` `role="alert"` (natif), `children` = le message actuel exact (« Arrête la réponse en cours avant de changer de conversation. » / « Le renommage n'a pas pu être enregistré. » / « La conversation n'a pas pu être supprimée. » / « L'export Markdown a échoué. » / « L'export Word a échoué. ») ; **pas de Réessayer** (l'action se relance depuis le menu ou la ligne ; un seul bandeau, `error` est déjà mono-slot) |
| catalogue | dialogue 30 cartes | § 3 |
| catalogue, requête sans hit | « Aucune capacité trouvée » | `EtatVide` ci-dessus |

Pas d'état chargement : le tiroir lit le store déjà hydraté. Pas de
`conversationsTruncated` : le tiroir vivant ne l'affiche pas (l'ajouter
serait une fonctionnalité).

## 5. Gardes mécaniques et tests à aligner

Nouveaux, rouges d'abord :

`PrototypeConversationDrawer.da.test.tsx`

1. le panneau fait `w-[22rem]`, le titre est un `h2` d'id
   `prototype-conversation-drawer-title`, la région s'en nomme ;
2. « Nouvelle conversation » est le `Button` `primary` du pied, et
   `surface="new"` lui donne encore le focus ;
3. une ligne courante porte `aria-current="page"` et `bg-accent-tint` ;
   le déclencheur d'actions est un bouton 36 px ; Entrée sur la ligne
   appelle encore `onOpenChat` ;
4. vide sans requête : titre « Aucune conversation », pas « enregistrée » ;
   vide avec requête : « Aucune conversation trouvée » ; un seul
   « Nouvelle conversation » (le pied), y compris à vide ;
5. `Alerte` sur verrouillage, zéro bouton « Réessayer » dans le tiroir ;
6. aucune classe `text-xs` sur un interactif, aucune couleur en dur dans
   `PrototypeConversationDrawer.tsx` (étendre `aucuneCouleurEnDur` à ce
   fichier).

`CapabilityCenter.da.test.tsx`

1. le `h2#capability-center-title` dit « Capacités » ; le compte écrit
   « 30 capacités » via `capabilities.length` ;
2. `typeCapacite` : les 3 prompts → « Demande relue », `attention` →
   « Action », `office` → « Action », `email` / `decision-board` →
   « Parcours », `tasks` → « Vue » ; un clic `onChoose` inchangé ;
3. un seul `[data-dialog-autofocus]`, le focus va au champ (les deux cas
   actuels restent, ici ou délégués) ;
4. `role="tablist"` nommé « Intentions », six `role="tab"`, le premier
   groupe reste `organize` ; plus de `style={{ backgroundColor` dans la
   fonction `CapabilityCenter` ;
5. `EtatVide` « Aucune capacité trouvée » sur une requête absurde ;
6. aucune classe `text-xs` sur un interactif de la fonction, plus de
   `hover:-translate-y`, plus d'ombre `rgba` **sur le dialogue et les
   cartes** (`TrustCenter` exclu) ;
7. le pied contient « Demande relue » et « s'ouvre au clic ».

À aligner dans le même commit, forme seulement : `CarteOuvreSaDestination.test.tsx:41`,
`Etabli.test.tsx:123`, `tests/e2e/stories/parcours-08-capacites-prototype.spec.ts:179`
(« Ce que Thérèse sait mobiliser » → « Capacités ») ; `PrototypeConversationDrawer.test.tsx`
(le bouton « Nouvelle conversation » reste unique, désormais au pied ;
placeholder « Rechercher dans les conversations ») ;
`ResponsiveShellContract.test.ts` inchangé sur `flex-col md:flex-row` et
sur `left-4 right-4` / `sm:w-[360px]` (TrustCenter). `Etabli.test.tsx`
(`queryByRole('button', { name: /Capacités/ })` absent) reste vert : le
nouveau titre est un `h2`, pas un bouton. Aucune assertion de comportement
n'est retirée.

## 6. Ce que ce lot ne fait pas

- Onglets Conversations | Capacités dans un même tiroir 22 rem, titre qui
  bascule, catalogue en `details` : aujourd'hui deux ouvertures (« Conversations »
  / « Plus d'outils »), deux modèles d'Échap, un modal. Fonctionnalité : **P-068**.
- Six intentions maquettées (Écrire et répondre, etc.), scinder Email,
  fusionner Images et voix, renommer les 30 cartes : **P-069**.
- Étiquette de genre (Action, Décision, Document) et aperçu du dernier
  message sur une ligne de conversation : **P-070**.
- `ConversationSidebar.tsx`, `TrustCenter`, palette ⌘K, Accueil, autres lots.
- Aucun changement de données, d'API, de store ni de navigation.

## 7. Plan de preuve

1. Tests rouges d'abord (§ 5), vérifiés rouges pour la bonne raison,
   sabotage par remplacement inverse, `.agents-sync-paused` posé.
2. Six portes : ruff, pytest (XML), vitest json, tsc, eslint (27), mypy 951.
3. Recette visuelle sur la pile jetable (17393 et 1420, jamais 17293) :
   conversations forcées par interception de `**/api/chat/conversations*`
   (Playwright `page.route`) : liste groupée (aujourd'hui, hier, semaine) ;
   liste vide ; recherche sans hit ; verrouillage (stream en cours) ; ouverture
   du catalogue via « Plus d'outils » (données locales, 30 cartes, un groupe,
   recherche « xyzabc » → vide, clic « Tâches » → vue `tasks`, clic
   « Recherche web » → phrase dans le composeur non envoyée). Largeurs 1280,
   1024, 840, 800 px ; clair, sombre, contraste élevé ; trois tailles de
   police. Captures `.cartography-work/validation/da-lot3/`, rapport
   `docs/da/2026-09-11-lot3-recette.md`. Vérifier : pied du tiroir visible
   à 800 px, anneau 3 px sur une ligne et sur un onglet d'intention, un
   seul « Nouvelle conversation », destinations 20+3 intactes, établi
   visible, composeur non recouvert.
4. Revue Grok du diff avant le tag, `/release-therese 0.72.0-alpha` avec le
   GO de Ludo (toute la DA, pas ce lot seul).
