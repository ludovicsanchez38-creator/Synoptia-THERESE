# DA « Application affinée », lot 4 : l'écran Contacts et pipeline (design à challenger avant le code)

Version 1, 11/09/2026. Précédent : lot 2 (Accueil), GO v6. Maquette de
référence : `docs/da/2026-09-05-propositions/maquettes/contacts.html` (états
`normal`, `deplace`, `fiche`), critères de `ecrans.json` : « Lire une fiche,
faire glisser une étape, voir la prochaine relance. Contacts hors pipeline
toujours accessibles ; déplacement au clavier préservé ; accès à la fiche
depuis chaque carte ; pipeline qui défile sans perdre les colonnes. » Déjà
décidé côté UX, pas à rejuger : P-002 adresses et badges lisibles ; P-016
retrouver un client par son nom ; pipeline complet par étape (0.66.1) ; titres
`viewLabels.crm = 'Pipeline'` et `viewLabels.memory = 'Contacts'` (`lexique.test.ts`) ;
cartes qui ouvrent leur destination (27/08) ; B-241 (la coque pose le titre,
le panneau n'ajoute pas de second `h1`) ; B-219 (onglets = `tablist` / `tab` /
`aria-selected` + flèches) ; B-237 (clavier dnd-kit, consignes en français,
Échap absorbe le glissé).

## Ce que le lot change, en une phrase

`CRMPanel.tsx`, `PipelineView.tsx`, `ActivityTimeline.tsx` et `MemoryPanel.tsx`
prennent la forme de la maquette en consommant les primitives du lot 1
(`Carte`, `CarteTete`, `Ligne`, `Etiquette`, `Segments` via
`CLASSES_SEGMENTS` / `classeSegment`, `Alerte`, `EtatVide`, `Squelette`,
`Button`, `Input`, `Select`, `Textarea`, `FormField`) ; les mêmes données, les
mêmes états, les mêmes destinations. Aucun appel réseau, aucun store, aucun
parcours ne change. Les deux vues de la coque restent deux vues.

## Décisions tranchées par défaut (Ludo peut corriger)

1. L'écran DA `contacts` correspond aujourd'hui à **deux** destinations :
   `crm` (`CRMPanel standalone`, titre coque « Pipeline ») et `memory`
   (`MemoryPanel standalone`, titre coque « Contacts »). Les fusionner en un
   seul écran à trois onglets (Pipeline / Liste / Activités) changerait les
   destinations : hors lot (§ 10).
2. Les sept colonnes et leurs libellés exacts restent (0.66.1, e2e
   `parcours-04-crm.spec.ts`) : Contact, Découverte, Proposition, Signature,
   Livraison, Actif, Archive. La maquette n'en montre que quatre et renomme
   « Proposition » en « Devis envoyé » : non repris.
3. Le bandeau Pipeline / Activités **garde** `role="tablist"` (B-219, 4 tests)
   et prend la forme des segments en consommant `CLASSES_SEGMENTS` /
   `classeSegment(actif)` ; `Segments` (`role="group"` + `aria-pressed`) n'est
   pas monté ici. Le `layoutId="activeTab"` (soulignement animé) disparaît :
   la maquette n'a pas de trait, et ce `layoutId` est le jumeau de celui qui
   gelait AnimatePresence sur le Board.
4. « Nouveau contact » est le grand geste des deux vues : `Button variant="primary" size="lg"`. Tout autre bouton de ces écrans est `md` (36 px) ;
   `sm` n'y est plus employé. CRM aujourd'hui : « Ajouter un contact » →
   « Nouveau contact » (même `onClick`, même modale `aria-label="Nouveau contact CRM"`). Import : « Import .vcf » → « Importer (.vcf) ».
5. Cadence : une seule release pour toute la DA (décision Ludo du 11/09, lot 2).
6. Le placeholder de recherche Contacts ne recopie pas « Nom, société, e-mail… »
   (la recherche est sémantique, P-016). Libellé accessible : « Retrouver un
   contact ». `data-testid="memory-search-input"` conservé.

## 1. Deux vues, un lot (coque inchangée)

`PrototypeUnifiedViewCanvas.tsx` : `view === 'crm'` monte `CRMPanel standalone`,
`view === 'memory'` monte `MemoryPanel standalone onNewContact onEditContact`.
Le `h2` de coque, Retour, `viewLabels`, et le mode tiroir / modale
(`standalone={false}`) : hors lot (la coque n'emprunte que `standalone`).

## 2. L'en-tête de `CRMPanel` (vue `crm`)

Maquette `.vue-tete` : flex, alignés en bas, actions à droite, wrap.

| Élément | Aujourd'hui | Cible |
|---|---|---|
| Pastille 2,5 rem `LayoutDashboard` | présente | retirée (le titre vit dans la coque, B-241) |
| Libellé | `<p className="text-lg font-semibold">Pipeline</p>` | inchangé (pas un titre) |
| Meta | `{n} contact(s)` + `+` si `contactsTronques` + ` · {m} projet(s)` | inchangée, `tabular-nums` sur les nombres ; pluriel actuel : 0 et 1 sans s, n > 1 avec s |
| Troncature | `<p role="alert">Liste incomplète : le pipeline ne montre que les 200 contacts les plus récents.</p>` | `Alerte data-testid="crm-troncature"` titre « Liste incomplète », même phrase, `icone={AlertCircle 18 px}` ; pas de bouton |
| Import | `<label>` `text-sm` + input fichier caché | `Button variant="secondary" size="md"` « Importer (.vcf) » qui déclenche le même `input accept=".vcf"` ; `Upload` 18 px |
| Créer | bouton maison « Ajouter un contact » | `Button variant="primary" size="lg"` « Nouveau contact », `UserPlus` 18 px, `onClick={() => setShowCreateForm(true)}` |
| Fermer (non standalone) | icône X | `Button variant="ghost" size="icon"` inchangé fonctionnellement |

Conteneur : `flex flex-wrap items-end gap-3 px-4 pt-4 pb-2` ; actions
`ml-auto flex flex-wrap gap-2 max-[840px]:basis-full max-[840px]:ml-0`.
`data-testid="crm-panel"` conservé sur le racine standalone.

## 3. Le bandeau d'onglets

Ordre : en-tête (§ 2), bandeau, `Alerte` d'erreur de chargement (§ 6), corps.
`role="tablist"` `aria-label="Vues du CRM"` ; classes `CLASSES_SEGMENTS` +
`px-4 pt-3`. Chaque onglet : `id={`crm-tab-${id}`}`, `role="tab"`,
`aria-selected`, `aria-controls={`crm-panel-${id}`}`, `tabIndex` 0 / -1,
`onKeyDown` → `handleRovingFocus(..., 'horizontal')`, `onClick` →
`setActiveTab`, `className={classeSegment(isActive)}` +
`focus-visible:outline focus-visible:outline-[3px] focus-visible:outline-offset-2 focus-visible:outline-ring`.
Libellés inchangés : « Pipeline », « Activités ». Icônes retirées (la maquette
n'en a pas ; `textContent` des tests reste le libellé). Plus de `motion.div
layoutId="activeTab"`. Le `tabpanel` garde `id`, `aria-labelledby`,
`tabIndex={0}`, `flex-1 overflow-auto`. Pas de troisième onglet « Liste ».

## 4. Les colonnes : `PipelineView`

Conteneur : `grid grid-flow-col auto-cols-[minmax(15rem,1fr)] gap-3 overflow-x-auto pb-2 snap-x snap-proximity` (la maquette `.pipeline` ; les sept
colonnes débordent, le défilement horizontal reste, critère ecrans.json).
Chaque colonne : `useDroppable({ id: stage.id })`, `snap-start`, `min-h-[22rem]`,
fond `bg-surface-2 rounded-md p-2 grid gap-2 content-start`. Plus de barre
colorée `stage.color` + `text-ink-on-fill`. Tête : `flex items-center gap-2
px-2 py-1`, puis `<h3><Etiquette domaine={domaine}>{stage.label}</Etiquette></h3>`
et un frère `<span className="ml-auto text-sm font-medium text-text-muted tabular-nums">{count}</span>`.
Le `h3` contient **uniquement** le libellé (e2e `toHaveText` exact sur les
sept noms). Pas de total en euros. `isOver` : `ring-2 ring-ring bg-accent-tint`
(jeton, plus `bg-accent-cyan/5`).

| stage.id | domaine `Etiquette` |
|---|---|
| contact, discovery, proposition, signature | prospects |
| delivery | agenda |
| active | (pas de domaine) `ton="succes"` |
| archive | `ton="neutre"` |

Colonne vide : aucun texte « Dépose ici… » (§ 10). `SortableContext` /
capteurs / `accessibiliteGlisserDeposer` / `pushEscapeHandler` inchangés.

## 5. Les fiches : `ContactCard` / `SortableContactCard`

`data-testid="crm-contact-item"` conservé (absent sur l'overlay, B-151).
Carte : `bg-surface border border-border rounded-sm p-3 cursor-grab` ;
`text-sm` partout (plus de `text-xs` : la carte est un interactif). Titre
`font-semibold` : `{first_name} {last_name}` (icône `User` retirée, redondante
avec le nom). Société : `text-sm text-text-muted` si présente. E-mail : idem,
conservé (donnée déjà montrée, la maquette ne l'a pas). Pied : `flex flex-wrap
gap-2 items-center text-sm text-text-muted` ; `tabular-nums` sur le score ;
libellé « Score » + valeur + `HelpCircle` 18 px, **même** `title` /
`aria-label` qu'aujourd'hui (pas « de 0 à 100 », `scoreLibelle.test.tsx`) ;
`source` → `<Etiquette ton="neutre">{source}</Etiquette>` si présente.

État `deplace` (glissé actif) : la carte d'overlay (`isOverlay`) porte
`outline outline-2 outline-dashed outline-accent outline-offset-2 bg-accent-tint`
et `aria-grabbed="true"`. La source reste à `opacity-40`. Aucun changement de
capteur, de collision, ni de `onStageChange`. Clic : toujours
`onContactClick` → `setSelectedContact` + `setActiveTab('activities')`.

## 6. Les états (CRM)

Priorité inchangée (`CRMPanel.tsx` : erreur, puis loading, puis onglet).

| État | Aujourd'hui | Cible |
|---|---|---|
| chargement CRM | spinner 12×12 cyan | trois colonnes `aria-hidden` de trois rangées `Squelette` (`classeBarre="h-8 rounded-sm"` pour la puce, `largeur="w-[60%]"` / `w-[40%]`) + `role="status"` « Chargement du pipeline… » |
| erreur de chargement (D69) | bandeau `role="alert"` + `error` | `Alerte data-testid="crm-erreur"` `icone={AlertCircle 18 px}`, `children` = `error` ; **pas** de Réessayer (il n'y en a pas aujourd'hui) ; la liste en cache reste visible |
| troncature | phrase warning | `Alerte` § 2, sans action |
| pipeline, N ≥ 1 | colonnes + cartes | § 4 et § 5 |
| pipeline, N = 0 | sept colonnes vides | idem, sans texte inventé |
| activités, contact sélectionné | nom + société + « Ajouter une activité » + Prestations + Historique | `Carte` : `CarteTete` titre = prénom + nom, meta = société si présente, `actions` = `Button variant="primary" size="md"` « Ajouter une activité » (même `setShowAddActivity`) ; `ListeDesPrestations` inchangée sous un `h3` « Prestations » ; `ActivityTimeline` sous un `h3` « Historique » |
| activités, aucun contact | puces de filtre + fil global | filtres : `role="group"` habillé par `CLASSES_SEGMENTS` / `classeSegment` (pas `Segments` : les puces portent encore une icône 18 px), mêmes ids `all` / `email` / `call` / `meeting` / `note`, mêmes libellés ; une ligne par activité : date `tabular-nums text-sm text-text-muted` + titre `text-sm` + nom du contact (B-205, magasin complet) + type ; `maskText` conservé |
| activités globales, chargement | spinner | `Squelette` 3 lignes `aria-hidden` + `role="status"` |
| activités globales, panne (B-527) | alerte + Réessayer | `Alerte data-testid="crm-activites-erreur"` même phrase, `action` = `Button variant="secondary" size="md"` « Réessayer » ; un seul Réessayer |
| activités globales, vide | icône + phrase + `text-xs` | `EtatVide data-testid="crm-activites-vide"` titre = phrase actuelle (« Aucune activité enregistrée » / `Aucune activité de type "…"`), texte « Clique sur un contact dans le Pipeline pour ajouter une activité. », sans action |
| timeline (chargement / vide / panne) | spinner ; « Aucune activité pour ce contact » ; silence | `Squelette` 3 lignes ; `EtatVide` ce titre sans action ; panne inchangée (pas de Réessayer inventé) |
| trace annulée / score (B-566) | `line-through` + « Note annulée par son auteur » ; « Score recalculé : x → y » | conservés (`traceAnnulee.test.tsx` lit la classe) |

Un seul « Réessayer » par état où il existe déjà. `ListeDesPrestations` n'est
pas réécrite (ses propres alertes restent).

## 7. La vue Contacts : `MemoryPanel` (vue `memory`)

C'est la « Liste » de la maquette, déjà une destination. En-tête aligné sur
§ 2 : pastille `Users` retirée ; `<p>Contacts</p>` conservé (B-241) ;
troncature → `Alerte data-testid="memory-troncature"` (phrase actuelle, P-016) ;
actions standalone : `Button secondary md` « Importer », `Button ghost md`
« Exporter », `Button primary lg` « Nouveau contact »
(`data-testid="memory-add-contact-btn"`). Recherche : `Input type="search"`,
`icon={<Search 18 px>}`, `aria-label="Retrouver un contact"`, placeholder
« Rechercher... », même debounce 250 ms. Périmètre : `CLASSES_SEGMENTS` /
`classeSegment`, mêmes quatre boutons Tout / Global / Projet / Conv. (les
tests ciblent `getByRole('button', { name: 'Projet' })`). Bandeau RGPD
(`expires_ou_bientot`) : hors `Alerte` (ton `erreur` seulement) ; jetons
`text-warning` / `bg-[var(--color-warning-tint)]`, `text-sm`, phrase actuelle.

Liste : chaque contact → `<Ligne domaine="prospects" puce={initiales 2 rem
rounded-full} titre=… detail=… droite=… onClick=…>`. Titre = prénom + nom
(« Sans nom » si vide). Détail = société, sinon e-mail, `text-sm`. `droite` =
`<Etiquette>` du badge RGPD actuel (mêmes lettres C / CT / IL / OL, même `!`
et triangle d'échéance, P-002) + actions RGPD / supprimer déjà présentes
(`relative z-10`, la `Ligne` laisse passer boutons et liens).
`data-testid` aucun sur la ligne aujourd'hui : on n'en invente pas.
État vide : `EtatVide data-testid="contacts-etat-vide"` titre = `etatVide.message`
(les trois phrases B-240, mot pour mot), `action` = `Button ghost md` si
`actionLabel`. Erreur store : `Alerte` + `Button secondary md` « Réessayer »
(un seul). Chargement : `Squelette` 4 lignes, plus le `Spinner`. Pied tiroir
(`memory-add-contact-btn-drawer`) : hors lot (mode non standalone).

## 8. Modales du panneau CRM (création, activité)

`CreateContactModal` / `AddActivityModal` : `Alerte` pour l'erreur de
formulaire ; champs via `FormField` + `Input` / `Select` / `Textarea` ; ids
conservés (`crmpanel-prenom`, `crmpanel-nom`, `crmpanel-entreprise`,
`crmpanel-email`, `crmpanel-telephone`, `crmpanel-source`, `crmpanel-stage`,
`crmpanel-titre`, `crmpanel-description`) ; boutons `md` « Annuler »
(`ghost`) et soumettre (`primary`) ; `pushEscapeHandler` inchangé (B-262,
B-336). Types d'activité : `CLASSES_SEGMENTS` / `classeSegment`, mêmes ids.
`ContactModal` (édition depuis Contacts) : hors lot (couche modale, pas l'état
`fiche` de la maquette).

## 9. Gardes mécaniques et tests à aligner

Nouveaux, rouges d'abord :

- `CRMPanel.da.test.tsx` : `tablist` habillé `CLASSES_SEGMENTS`, plus de
  `layoutId` ; un seul « Réessayer » sur la panne d'activités, zéro sur
  l'erreur de chargement CRM et le vide ; « Nouveau contact » ouvre la
  même modale ; aucune classe `text-xs` sur un interactif ; aucune couleur
  en dur (hex / rgba / hsl / color-mix / `bg-black`) dans le fichier.
- `PipelineView.da.test.tsx` : sept `h3` aux libellés exacts, compte hors
  `h3` ; une carte = `data-testid="crm-contact-item"` ; overlay de glissé
  `aria-grabbed="true"` ; badge `data-etiquette` ; `overflow-x` sur le
  conteneur ; score 145 affiché, pas « de 0 à 100 ».
- `ActivityTimeline.da.test.tsx` : vide = `EtatVide` ; chargement =
  `Squelette aria-hidden` ; « Score recalculé » et `line-through` toujours
  là.
- `MemoryPanel.da.test.tsx` : `Ligne` (une commande, grille `2rem 1fr auto`) ;
  `EtatVide` transmet `contacts-etat-vide` ; « Réessayer » = 1 sur panne, 0
  sur vide constaté ; `memory-search-input` et `memory-add-contact-btn`
  présents ; interactifs ≥ 14 px.

À aligner dans le même commit (forme, pas comportement) :
`CRMPanel.echap.test.tsx` (`/Ajouter un contact/i` → `/Nouveau contact/i`) ;
`tests/e2e/stories/parcours-04-crm.spec.ts` (titre du cas et
`getByRole('button', { name: /ajouter un contact/i })` → `/nouveau contact/i` ;
`getByText(/import.*\.vcf/i)` reste vrai pour « Importer (.vcf) » ; commentaire
B-148 : la collision « Contact » / « Ajouter un contact » disparaît, les sept
`h3` restent l'ancre) ; `CRMPanel.onglets.test.tsx` (les `textContent` restent
`['Pipeline', 'Activités']`, plus d'icône dans le nom). Aucune assertion de
comportement n'est retirée.

## 10. Ce que ce lot ne fait pas

- Fusionner Contacts et Pipeline en un écran « Contacts et pipeline » à trois
  onglets, avec recherche et tri « prochaine relance » sur le pipeline.
  Fonctionnalité, pas DA : P-068 (numéro à confirmer par l'orchestrateur).
- La section « Hors pipeline », le bandeau « Prochaine relance », les montants
  sur les cartes et les colonnes, le bouton « Relancer », le fil d'Ariane, la
  fiche deux colonnes (identité + chrono), le texte visible d'aide clavier, le
  « Dépose ici… » des colonnes vides, le compteur « à relancer cette semaine ».
  Même P-068.
- Réduire ou renommer les étapes (0.66.1).
- `ListeDesPrestations.tsx`, `ContactModal.tsx`, le mode tiroir / modale, les
  six autres vues de la coque.
- Aucun changement de données, d'API, de store ni de navigation.

## 11. Plan de preuve

1. Tests rouges d'abord (§ 9), vérifiés rouges pour la bonne raison, sabotage
   par remplacement inverse, `.agents-sync-paused` posé.
2. Six portes : ruff, pytest (XML), vitest json, tsc, eslint (27), mypy 951.
3. Recette visuelle sur pile jetable (17393 et 1420, jamais 17293) : états
   forcés par interception Playwright (`page.route`) de `/api/memory/contacts`,
   `/api/memory/projects`, `/api/crm/activities`, `/api/prestations`,
   `/api/rgpd/stats` (quatre contacts dont un sans source et un score 145 ;
   carnet vide ; panne contacts avec cache ; panne activités ; contact
   sélectionné avec une trace annulée ; recherche Contacts sans résultat ;
   troncature 200). Largeurs 1280 / 1024 / 840 / 800, clair / sombre /
   contraste élevé, trois tailles de police. Captures
   `.cartography-work/validation/da-lot4/`, rapport
   `docs/da/2026-09-11-lot4-recette.md`. Vérifier : sept colonnes qui défilent
   à 800 px, saisie Espace + flèches, Entrée ouvre Activités, anneau 3 px,
   un seul « Réessayer » par état, Contacts hors pipeline via la vue Contacts.
4. Revue Grok du diff avant le tag, GO de Ludo ; pas de release intermédiaire.
