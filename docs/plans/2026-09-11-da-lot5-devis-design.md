# DA « Application affinée », lot 5 : l'écran Devis et factures (design à challenger avant le code)

Version 1, 11/09/2026. Précédents : lot 1 (socle et coque, v0.71.0-alpha),
lot 2 (Accueil). Maquette de référence :
`docs/da/2026-09-05-propositions/maquettes/devis.html` (états `normal`,
`vide`, `nouveau`), critères de `ecrans.json` : « Statut lisible, montants
alignés, PDF conforme, thème sombre au même niveau. Types, filtres, actions
et historique préservés ; statut d'envoi, de paiement et d'échéance
distincts ; création et erreurs de formulaire testées ; le PDF ReportLab
n'est pas concerné par le CSS. » Déjà décidé côté UX, pas à rejuger : P-014
(devis accepté vers facture sans ressaisie), P-015 (actions nommées devis
ET facture), P-028 (franchise de TVA), Factur-X (P-026) à venir ; le titre
de la vue est posé par la coque, le panneau ne le redouble pas en `h1`
(B-241) ; « Nouveau devis » depuis le filtre Devis (B-388) ; conversion,
acceptation, refus et paiement derrière confirmation ; Échap sur la pile
(formulaire B-228, confirmation de suppression).

Montage : `PrototypeUnifiedViewCanvas` vue `invoices` rend
`<InvoicesPanel standalone />` ; `InvoiceForm` n'est monté que par le
panneau (`showForm`). Le mode calque (`standalone={false}`) garde le même
intérieur.

## Ce que le lot change, en une phrase

`InvoicesPanel.tsx` et `InvoiceForm.tsx` prennent la forme de la maquette
en consommant les primitives du lot 1 (`Carte`, `Etiquette`, `Segments`,
`EtatVide`, `Alerte`, `Squelette`, `Button`, `Input`, `Select`, `Textarea`,
`FormField`) ; les mêmes données, les mêmes états, les mêmes destinations.
Aucun appel réseau, aucun store, aucun parcours ne change.

## Décisions tranchées par défaut (Ludo peut corriger)

1. Deux rangées `Segments` (type : Tout / Devis / Factures / Avoirs ; statut
   : `statutsProposesPour`) : la maquette fond « En retard » dans le type et
   oublie les avoirs ; types et filtres sont préservés.
2. Liste en `<table>` jetons (`.tableau` de la maquette), pas `Ligne` : sept
   colonnes, trois statuts distincts ; `Ligne` est une grille `2rem 1fr auto`.
3. Le formulaire reste une modale (Échap, `id="invoice-form"`, pied hors
   défilement). La création en page de la maquette va au portail (§ 7).
4. Le grand geste de l'écran, `Button variant="primary" size="lg"` : libellé
   actuel `Nouveau devis` / `Nouvelle facture` (P-015). Tout autre bouton
   du panneau et du formulaire est `md` (36 px) ; `sm` n'y est pas employé.
5. Cadence : une seule release pour toute la DA, lots enchaînés sur `main`
   sans tag intermédiaire (Ludo, 11/09, lot 2).
6. Aucune extension de primitive : `idTitre`, `action`, attributs natifs,
   `CLASSES_SEGMENTS`, `classeBarre` sont déjà là.

## 1. L'en-tête du panneau

Pas de `h1` (B-241). Pastille cyan 2,5 rem retirée.

| Élément | Aujourd'hui | Cible |
|---|---|---|
| Titre visible | `<p className="text-lg font-semibold text-text">Devis et factures</p>` | même nœud, `className="font-editorial text-lg font-semibold text-text"` |
| Compteur | `{n}{+?} document(s)` dans le même `<p>` | même `<p data-testid="invoices-compteur">` : `{n}{listeTronquee ? '+' : ''} pièce{n > 1 ? 's' : ''}` ; si M ≥ 1 factures `status === 'overdue'` dans `filteredInvoices` : `, dont 1 facture échue` / `, dont M factures échues` (M = ce filtre, pas l'encours réel hors plafond). 0 / 1 : « pièce » sans s. Jeux de tests tout `draft` : pas de « dont » |
| Troncature | `<p role="alert" className="text-sm text-warning">Liste incomplète : seuls les 100 documents les plus récents de ce filtre sont affichés.</p>` | inchangé (texte, `role`, jeton `warning`) ; pas une `Alerte` (teinte d'erreur) |
| Geste | `<button>` maison « Nouveau devis » / « Nouvelle facture » | `Button variant="primary" size="lg"` + `Plus` 18 px, mêmes libellés, `handleCreateNew` |
| Fermer (hors standalone) | `<button>` icône `X` sans nom | `Button variant="ghost" size="icon"` `aria-label="Fermer"`, `setIsInvoicePanelOpen(false)` |

Conteneur : `flex flex-wrap items-end gap-3 px-4 py-4 border-b border-border` ;
actions `ml-auto flex flex-wrap gap-2 max-[840px]:basis-full max-[840px]:ml-0`.

## 2. Les filtres

Ordre : en-tête, filtres, corps, formulaire, confirmation de suppression.

Deux groupes, libellé visible `text-sm text-text-muted` (« Type », « Statut »)
+ `Segments` (`role="group"`, `aria-pressed`, `CLASSES_SEGMENTS`,
`className="flex-wrap"`) :

- Type, `label="Type"`, `valeur={filters.document_type ?? 'all'}`, options
  `{id,label}` : `all` Tout, `devis` Devis, `facture` Factures, `avoir`
  Avoirs ; `onChange` appelle `setFilters(filtresAvecType(filters, id ===
  'all' ? undefined : id))` (B-005).
- Statut, `label="Statut"`, `valeur={filters.status ?? 'all'}`, options =
  `statutsProposesPour(filters.document_type)` avec `all` → « Toutes »,
  sinon `STATUS_CONFIG[status].label` (Envoyée, Payée, Accepté, …) ;
  `onChange` → `setFilters({ ...filters, status: id })`.

Pas de champ recherche, pas de « Tri : échéance ».

## 3. La liste : tableau dans une `Carte`

`Carte as="section" className="overflow-x-auto" aria-labelledby` inutilisé
(le nom de la région est celui de la coque). `<table className="w-full
border-collapse">` : `th` `text-left text-xs font-semibold text-text-muted
px-4 py-2 border-b border-border tracking-wide` ; « Montant TTC » en
`text-right` ; dernière `th` `sr-only` « Actions ». `td` `px-4 py-2.5
border-b border-border align-middle` ; `tr:hover td` via
`hover:[&>td]:bg-surface-2`. Chaque `tr` porte `data-testid="invoice-item"` ;
plus de `onClick` ni de `motion` sur la rangée (la commande d'ouverture
reste le bouton du client, B-208).

| Colonne | Contenu |
|---|---|
| Pièce | `span.font-mono.text-sm.whitespace-nowrap` = `invoice_number` ; sous-ligne `text-xs font-medium text-text-muted` : « Devis » / « Avoir » / « Facture » +, pour une facture, ` · ` + mois `Intl.DateTimeFormat('fr-FR', { month: 'long' })` sur `new Date(issue_date)` (même parseur qu'aujourd'hui, minuscule) |
| Client | `<button type="button">` actuel (nom, référence à défaut, `handleEdit`, stopPropagation) `font-semibold text-sm text-left` + anneau du `Button` (`focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg`) ; pas de raison sociale (absente du DTO) |
| Envoi | `Etiquette` § 3.1 |
| Paiement | `Etiquette` ou `span` muted « Sans objet » § 3.1 |
| Échéance | `tabular-nums` § 3.1 |
| Montant TTC | `montantAvecDevise(total_ttc, currency)`, `text-right font-semibold tabular-nums whitespace-nowrap text-text` (plus `text-2xl` ni `text-accent-cyan-ink`) |
| Actions | toujours visibles (plus `opacity-0 group-hover`) : `Button variant="ghost" size="md"` titre inchangé « Générer et ouvrir le PDF », texte « PDF » ; `Button variant="ghost" size="md" className="text-error"` titre « Supprimer », texte « Supprimer ». Mêmes `onClick` stoppés |

Statut inconnu (B-010) : `Etiquette ton="neutre"` = `invoice.status` brut,
icône `FileText` 18 px dans Envoi seulement ; Paiement « Sans objet » ;
échéance = date d'échéance.

### 3.1 Trois colonnes, champs existants (présentation)

`sent` du `STATUS_CONFIG` reste « Envoyée » dans les filtres. Dates :
`toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })` sur le
même `new Date(...)` qu'aujourd'hui.

| Type | status | Envoi | Paiement | Échéance |
|---|---|---|---|---|
| tout | `draft` | neutre « Brouillon » | `span` muted « Sans objet » | muted « Non envoyé » |
| tout | `cancelled` | neutre « Annulée » | Sans objet | `due_date` muted |
| devis | `sent` | info « Envoyé le {issue} » | neutre « En attente d'accord » | « Valable jusqu'au {due} » |
| devis | `accepted` | info « Envoyé le {issue} » | succes « Accepté » | « Valable jusqu'au {due} » |
| devis | `refused` | info « Envoyé le {issue} » | attention « Refusé » | « Valable jusqu'au {due} » |
| devis | `expired` | info « Envoyé le {issue} » | attention « Expiré » | « Valable jusqu'au {due} » |
| devis | `converted` | info « Envoyé le {issue} » | neutre « Converti » | « Valable jusqu'au {due} » |
| facture, avoir | `sent` | info « Envoyée le {issue} » | attention « Impayée » | `due_date` |
| facture, avoir | `overdue` | info « Envoyée le {issue} » | erreur « Impayée » | `font-semibold text-error` « {due} · échue » |
| facture, avoir | `paid` | info « Envoyée le {issue} » | succes « Payée le {payment_date} » (repli : « Payée » si date absente) | `due_date` muted |

`STATUS_CONFIG` ne sert plus qu'aux libellés de filtres (plus `badgeBg`
`bg-gray-500/20`, plus `text-agent-*` dans la liste).

## 4. Le formulaire (`InvoiceForm`)

Calque, `role="dialog"`, `aria-label`, `Z_LAYER.MODAL_NESTED`, pile Échap,
`id="invoice-form"` : inchangés. Voile `bg-text/60` (plus `bg-black/70`).
Surface `bg-surface border border-border rounded-md shadow-sm`, plus
`backdrop-blur-xl` ni `shadow-2xl`.

| Zone | Aujourd'hui | Cible |
|---|---|---|
| Tête | `h2` « Nouveau devis » / « Nouvelle facture » / « Nouvel avoir » / `Modifier {n}` ; `X` nommé Fermer | mêmes chaînes ; `h2` `font-editorial` ; `Button ghost icon` Fermer |
| Profil incomplet / illisible | bandeaux `bg-agent-amber/10` | mêmes textes, `bg-[var(--color-warning-tint)] border border-warning/30 text-warning` ; illisible garde `role="alert"` |
| Type (création) | trois `<button>` | `Segments label="Type de document"` Devis / Facture / Avoir, `valeur={documentType}` |
| Champs | `<label>` + `<input>`/`<select>`/`<textarea>` maison | `FormField` + `Input` / `Select` / `Textarea` ; ids `contact`, `status`, `currency`, `issueDate`, `dueDate`, `validiteJours`, `notes`, `invoiceform-quantite-{i}`, `invoiceform-tva-{i}` conservés ; option vide « Sélectionner un contact » (`value=""`), pas `placeholder` disabled du `Select` ; `required` natifs conservés |
| Lignes | cartes empilées, labels `text-xs` | `<table>` de lignes (jetons), `Input aria-label={`Description ligne ${i+1}`}` `placeholder="Description"` ; après un submit bloqué par BUG-132, chaque ligne sans description trimée : `error` + `aria-invalid` + `FormField error="Renseigne la description de cette ligne, ou supprime-la."` ; la notification actuelle est conservée |
| Ajouter / supprimer ligne | boutons maison | `Button ghost md` « Ajouter une ligne » ; `Button ghost icon` `aria-label={`Supprimer la ligne ${i+1}`}` |
| Totaux | `text-2xl text-accent-cyan-ink` | `grid grid-cols-[1fr_auto] justify-end gap-x-6 gap-y-1 tabular-nums` ; « Total TTC » `font-semibold text-lg` ; `montantAvecDevise` inchangé |
| Pied | Marquer comme payée / Accepter / Refuser / Convertir / Annuler / Créer | mêmes libellés, mêmes gardes, `Button md` : payée et Accepter `secondary`, Refuser `ghost`, Convertir `secondary`, Annuler `secondary`, soumission `primary` liée à `form={ID_FORMULAIRE}` (« Créer » / « Mettre à jour » / « Sauvegarde... ») |
| Conversion | dialogue actuel | mêmes chaînes ; Annuler `secondary md`, Convertir `primary md` |

Conditions de paiement : bloc en lecture seule s'il existe, jetons seulement.

## 5. Les états (corps du panneau)

Priorité inchangée (`InvoicesPanel.tsx`, `isLoading` puis `loadError` puis
vide filtré puis vide défaut puis liste). Un seul « Réessayer », sur
l'erreur de chargement.

| État | Aujourd'hui | Cible |
|---|---|---|
| chargement | « Chargement... » centré | trois rangées `aria-hidden` façon ligne de tableau (`grid grid-cols-[6rem_1fr_auto] gap-3 px-4 py-3 border-t border-border`) : `Squelette largeur="w-24"`, `largeur="w-[60%]"`, `largeur="w-16"` ; puis « Chargement... » `role="status"` `px-4 py-3 text-sm text-text-muted` |
| erreur | icône 4 rem + texte + bouton plein | `Alerte data-testid="invoices-load-error" icone={<AlertCircle 18 px />} titre="Chargement impossible"` `children` = `loadError` (`Impossible de charger les factures pour le moment.`) `action` = `Button secondary md` Réessayer → `loadInvoices` |
| vide, filtre `overdue` | « Aucun document ne correspond à ce filtre. » + Réinitialiser | `EtatVide data-testid="invoices-empty-overdue"` titre « Aucune pièce en retard », texte « Les factures échues et impayées apparaîtront ici. », `action` = `Button secondary md` « Réinitialiser les filtres » (`setFilters({})`) ; pas de Relancer |
| vide, autre filtre effectif (B-646) | même phrase générique + Réinitialiser | `EtatVide data-testid="invoices-empty-filtre"` titre « Aucun document ne correspond à ce filtre. », même action |
| vide, aucun filtre effectif | « Aucune facture » + « Créer une facture » | `EtatVide data-testid="invoices-empty"` titre « Aucune facture », `action` = `Button primary md` « Créer une facture » → `handleCreateNew` |

`filtreEffectif` inchangé. Confirmation de suppression : surface jetons,
Annuler `secondary md`, Supprimer `danger md`, chaînes inchangées.

## 6. Gardes mécaniques et tests à aligner

Nouveaux, rouges d'abord :

`InvoicesPanel.da.test.tsx` : (1) une ligne = `data-testid="invoice-item"`
sur un `tr`, bouton client + PDF + Supprimer, zéro `onClick` sur le `tr` ;
(2) une facture `overdue` montre trois `data-etiquette` (info / erreur /
erreur d'échéance en `text-error`) et le montant en `tabular-nums` ;
(3) un devis `sent` écrit « Envoyé le », « En attente d'accord », « Valable
jusqu'au » ; (4) compteur « 1 pièce », « 2 pièces », « 0 pièce », « 2 pièces,
dont 1 facture échue » / « dont 2 factures échues », « 100+ pièces » sans
« dont » si aucun `overdue` ; (5) Segments Type et Statut : `aria-pressed`
sur Tout + Toutes au départ, clic Devis appelle le même assainissement
qu'aujourd'hui ; (6) un seul « Réessayer » sur l'erreur, zéro ailleurs ;
squelettes `aria-hidden` + `role="status"` au chargement ; vide `overdue`
≠ vide défaut ≠ vide autre filtre ; (7) aucun interactif en `text-xs`,
aucune couleur en dur dans les deux fichiers (extension de
`aucuneCouleurEnDur` à `InvoicesPanel.tsx` et `InvoiceForm.tsx`) ; (8)
« Nouveau devis » / « Nouvelle facture » est `h-11`, les autres boutons du
panneau `h-9`.

`InvoiceForm.da.test.tsx` : (1) `form="invoice-form"` toujours sur le seul
`type="submit"` ; (2) BUG-132 : notification conservée ET `aria-invalid` +
le texte d'erreur de ligne ; (3) `Segments` Type de document en création ;
(4) Fermer et Supprimer la ligne 1 restent nommés ; (5) ids uniques.

À aligner dans le même commit (forme, pas comportement) :
`InvoicesPanel.chargementEchoue.test.tsx` (`'100+ documents'` →
`'100+ pièces'`, `compteur.textContent === '0 document'` → `'0 pièce'`),
`InvoicesPanel.troncature.test.tsx` (`'100+ documents'` → `'100+ pièces'`,
`'1 document'` → `'1 pièce'`, `'2 documents'` → `'2 pièces'`),
`InvoicesPanel.etatVideParDefaut.test.tsx` (le cas `status: 'paid'` vise
toujours `/ne correspond à ce filtre/` ; un cas `overdue` éventuel viserait
« Aucune pièce en retard », à n'ajouter que si le fichier teste déjà
`overdue` : il ne le teste pas), `InvoicesPanel.clavier.test.tsx`
(commentaire « carte » → « ligne » ; assertions de rôles inchangées),
`InvoicesPanel.test.tsx` (getByTitle PDF / Supprimer conservés ; « Aucune
facture » conservé). `InvoiceForm.soumission.test.tsx` (`/Créer/`),
`InvoiceForm.test.tsx` (placeholder `Description`, `/Créer/`),
`InvoiceForm.francais.test.tsx`, `InvoiceForm.nomsAccessibles.test.tsx`,
`InvoiceForm.identifiants.test.tsx` : aucune chaîne métier à changer.
Aucune assertion de comportement n'est retirée.

## 7. Ce que ce lot ne fait pas

- Quatre cartes de résumé, bouton Exporter, recherche « Client, référence… »,
  « Tri : échéance », raison sociale sous le client, nom d'atelier dans le
  sous-titre : données ou agrégats absents (le plafond 100 rendrait un total
  local menteur). Portail, P-068.
- « Relancer » sur la ligne et dans le vide en retard : aucun envoi (test
  « ne présente pas un envoi email »). Portail, P-069.
- « Convertir » sur la ligne : le parcours vit dans le formulaire (P-014).
  Portail, P-070.
- Création en page : fil d'Ariane, champ Objet, client créé depuis le champ,
  « Valable jusqu'au » en date, conditions saisies, brouillon auto, aperçu
  PDF, libellé « Valider le devis ». Portail, P-071.
- Factur-X (pied de maquette) : déjà P-026. Franchise de TVA : déjà P-028.
- PDF ReportLab, API, store, navigation, mode calque du panneau.

## 8. Plan de preuve

1. Tests rouges d'abord (§ 6), vérifiés rouges pour la bonne raison,
   sabotage par remplacement inverse, `.agents-sync-paused` posé.
2. Six portes : ruff, pytest (XML), vitest json, tsc, eslint (27), mypy 951.
3. Recette visuelle, pile jetable (17393 et 1420, jamais 17293) : états
   forcés par `page.route` sur `**/api/invoices*` et
   `**/api/invoices/billing/profile-status` (liste de quatre pièces dont une
   `overdue` ; vide sans filtre ; vide `status=overdue` ; vide `status=paid` ;
   chargement lent ; 500 ; formulaire nouveau avec ligne vide soumise ; profil
   incomplet), à 1280, 1024, 840 et 800 px, clair, sombre, contraste élevé,
   trois tailles de police ; captures
   `.cartography-work/validation/da-lot5/`, rapport
   `docs/da/2026-09-11-lot5-recette.md`. Vérifier : montants à droite en
   chiffres tabulaires, trois colonnes de statut, Avoirs toujours là, un
   seul Réessayer, anneau de focus sur une ligne (bouton client) et sur un
   segment, `Nouveau devis` entier à 800 px, placeholder `Description`
   conservé.
4. Revue Grok du diff avant fusion dans `main` ; pas de tag de lot.
