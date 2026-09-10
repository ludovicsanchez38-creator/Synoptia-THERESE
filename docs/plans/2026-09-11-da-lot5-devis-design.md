# DA « Application affinée », lot 5 : l'écran Devis et factures (design à challenger avant le code)

Version 3.1, 11/09/2026, après la revue de la v3 (6 points repris, 0 non repris) ; journal `.cartography-work/reviews/grok-da-lot5-devis-design-v3.log`. Version 3, 11/09/2026 00:17, après la revue de la v2 (13 points repris, 0 non repris) ; journal `.cartography-work/reviews/grok-da-lot5-devis-design-v2.log`.
Précédents : lot 1 (socle et coque, v0.71.0-alpha),
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
   actuel `Nouveau devis` / `Nouvelle facture` (P-015). Tout autre `Button`
   du panneau et du formulaire est `md` (36 px, `h-9`) ; `sm` n'y est pas
   employé. Les boutons de `Segments` (`[role=group] button`) ne sont pas
   des `Button` : `classeSegment` = `rounded-full px-3 py-1 text-sm`
   (`segments.classes.ts`).
5. Cadence : une seule release pour toute la DA, lots enchaînés sur `main`
   sans tag intermédiaire (Ludo, 11/09, lot 2).
6. Aucune extension de primitive : `idTitre`, `action`, attributs natifs,
   `CLASSES_SEGMENTS`, `classeBarre` sont déjà là. Pas de prop `texte` sur
   `EtatVide` (`titre` / `children` / `action`).

## 1. L'en-tête du panneau

Pas de `h1` (B-241). Pastille cyan 2,5 rem retirée.

Deux `<p>` distincts (c'est déjà le cas : `InvoicesPanel.tsx` titre l.236,
compteur l.237-238). On ne fusionne pas titre et compteur.

| Élément | Aujourd'hui | Cible |
|---|---|---|
| Titre visible | `<p className="text-lg font-semibold text-text">Devis et factures</p>` | même nœud (le premier `<p>`), `className="font-editorial text-lg font-semibold text-text"` ; pas de `data-testid` |
| Compteur | `{n}{+?} document(s)` dans un second `<p className="text-sm text-text-muted">` | ce second `<p data-testid="invoices-compteur" className="text-sm text-text-muted">` : `{n}{listeTronquee ? '+' : ''} pièce{n > 1 ? 's' : ''}` ; si M ≥ 1 pièces `status === 'overdue'` dans `filteredInvoices` (tous `document_type` : un avoir `overdue` compte, § 3.1) : `, dont 1 pièce échue` / `, dont M pièces échues` (M = ce filtre, pas l'encours réel hors plafond). 0 / 1 : « pièce » sans s. Jeux de tests tout `draft` : pas de « dont » |
| Troncature | `<p role="alert" className="text-sm text-warning">Liste incomplète : seuls les 100 documents les plus récents de ce filtre sont affichés.</p>` | même `role="alert"`, même jeton `warning`, pas une `Alerte` (teinte d'erreur) ; le mot suit le compteur : `Liste incomplète : seules les {PLAFOND_FACTURES} pièces les plus récentes de ce filtre sont affichées.` (accord féminin ; un seul mot, « pièce », dans les deux chaînes) |
| Geste | `<button>` maison « Nouveau devis » / « Nouvelle facture » | `Button variant="primary" size="lg"` `type="button"` + `Plus` 18 px, mêmes libellés, `handleCreateNew` |
| Fermer (hors standalone) | `<button>` icône `X` sans nom | `Button variant="ghost" size="icon"` `type="button"` `aria-label="Fermer"` children `<X className="h-[18px] w-[18px]" />`, `setIsInvoicePanelOpen(false)` |

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

`Segments` pose déjà `type="button"` sur chaque option (`Segments.tsx`).
Pas de champ recherche, pas de « Tri : échéance ».

## 3. La liste : tableau dans une `Carte`

Corps : `flex-1 min-h-0 overflow-y-auto` (scroller vertical nommé, inchangé
à `p-6`). `Carte as="section" className="overflow-x-auto"` ; `aria-labelledby`
inutilisé (le nom de la région est celui de la coque). Chargement, erreur et
vides remplacent le `<table>` **dans cette même `Carte`**, ils ne s'affichent ni
à sa place hors carte ni au-dessus (§ 5). `<table className="w-full
border-collapse">` : `th` `text-left text-xs font-semibold text-text-muted
px-4 py-2 border-b border-border tracking-wide` ; « Montant TTC » en
`text-right` ; dernière `th` `sr-only` « Actions ». `td` `px-4 py-2.5
border-b border-border align-middle` ; `tr:hover td` via
`hover:[&>td]:bg-surface-2`. Chaque `tr` porte `data-testid="invoice-item"`
et `onClick={() => handleEdit(invoice)}` (souris : numéro, montant, dates
ouvrent encore le document ; B-208 a ajouté le bouton client sans retirer
ce clic, `InvoicesPanel.tsx:386`). **Pas** de `tabIndex` sur le `tr`
(clavier = bouton client, B-208 ; la maquette `tabindex="0"` n'est pas
reprise). Plus de `motion`. PDF et Supprimer gardent `stopPropagation`.
La 1re colonne (référence) reste un `span.font-mono`, pas un second bouton.

| Colonne | Contenu |
|---|---|
| Pièce | `span.font-mono.text-sm.whitespace-nowrap` = `invoice_number` ; sous-ligne `text-xs font-medium text-text-muted` : « Devis » / « Avoir » / « Facture » +, pour une facture, ` · ` + mois `Intl.DateTimeFormat('fr-FR', { month: 'long' })` sur `new Date(issue_date)` (même parseur qu'aujourd'hui, minuscule) |
| Client | `<button type="button">` (`handleEdit`, stopPropagation) `font-semibold text-sm text-left` + anneau du `Button` (`focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg`) : texte = `contact_name` s'il existe ; sinon **aucun** texte (la Pièce dit déjà `invoice_number`) et `aria-label={invoice_number}` (B-208, la commande reste nommée) ; pas de raison sociale (absente du DTO) |
| Envoi | `Etiquette` § 3.1 |
| Paiement | `Etiquette` ou `span` muted « Sans objet » § 3.1 |
| Échéance | `tabular-nums` § 3.1 ; **pas** une `Etiquette` (maquette : `td.num` en `text-error` ou muted) |
| Montant TTC | `montantAvecDevise(total_ttc, currency)`, `text-right font-semibold tabular-nums whitespace-nowrap text-text` (plus `text-2xl` ni `text-accent-cyan-ink`) |
| Actions | toujours visibles (plus `opacity-0 group-hover`) : `Button variant="ghost" size="md"` `type="button"` `title` et `aria-label` « Générer et ouvrir le PDF » (2.5.3 : le texte « PDF » est dans le nom), texte « PDF » ; `Button variant="ghost" size="md" className="text-error"` `type="button"` titre « Supprimer », texte « Supprimer ». Mêmes `onClick` stoppés |

Statut inconnu (B-010) : `Etiquette ton="neutre"` = `invoice.status` brut,
icône `FileText` 18 px dans Envoi seulement ; Paiement « Sans objet » ;
échéance = date d'échéance.

`STATUS_CONFIG` : uniquement `label` et `icon` (plus `color` ni `badgeBg`).
Les classes `bg-gray-500/20`, `text-agent-amber`, `bg-agent-amber/20`,
`text-agent-purple`, `bg-agent-purple/20`, `bg-agent-blue/20`,
`text-agent-blue` sortent du fichier (plus de pastille de type colorée :
le type est la sous-ligne muted). Ne sert plus qu'aux libellés de filtres.

### 3.1 Trois colonnes, champs existants (présentation)

`sent` du `STATUS_CONFIG` reste « Envoyée » dans les filtres. Dates de la
liste, helper unique `dateListe(iso)` =
`new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' })`
(même parseur `new Date(...)` qu'aujourd'hui ; **l'année est conservée**,
aujourd'hui `toLocaleDateString('fr-FR')` sans options). `{issue}`, `{due}`,
`{payment_date}` ci-dessous passent par `dateListe`.

Accord d'envoi : devis et avoir « Envoyé le {issue} » ; facture
« Envoyée le {issue} » (un avoir est masculin). Brouillon : devis et avoir
« Émis le {issue} » ; facture « Émise le {issue} ». Accord de paiement de
l'avoir : « Impayé » / « Payé » / « Payé le {payment_date} » (pas
« Impayée » / « Payée », réservés à la facture).

| Type | status | Envoi | Paiement | Échéance |
|---|---|---|---|---|
| tout | `draft` | neutre « Brouillon » ; sous la pilule, `text-xs text-text-muted` « Émis le {issue} » / « Émise le {issue} » | `span` muted « Sans objet » | muted `{due}` ; si devis et `validite_jours` : ligne suivante muted « Validité : {n} jours » (pas « Non envoyé ») |
| tout | `cancelled` | neutre « Annulée » | Sans objet | `{due}` muted |
| devis | `sent` | info « Envoyé le {issue} » | neutre « En attente d'accord » | « Valable jusqu'au {due} » |
| devis | `accepted` | info « Envoyé le {issue} » | succes « Accepté » | « Valable jusqu'au {due} » |
| devis | `refused` | info « Envoyé le {issue} » | attention « Refusé » | « Valable jusqu'au {due} » |
| devis | `expired` | info « Envoyé le {issue} » | attention « Expiré » | « Valable jusqu'au {due} » |
| devis | `converted` | info « Envoyé le {issue} » | neutre « Converti » | « Valable jusqu'au {due} » |
| facture | `sent` | info « Envoyée le {issue} » | attention « Impayée » | `{due}` |
| facture | `overdue` | info « Envoyée le {issue} » | erreur « Impayée » | `td` `className="font-semibold text-error tabular-nums whitespace-nowrap"` « {due} · échue » (texte, pas `Etiquette`) |
| facture | `paid` | info « Envoyée le {issue} » | succes « Payée le {payment_date} » (repli : « Payée » si date absente) | `{due}` muted |
| avoir | `sent` | info « Envoyé le {issue} » | attention « Impayé » | `{due}` |
| avoir | `overdue` | info « Envoyé le {issue} » | erreur « Impayé » | même `td` `text-error` « {due} · échue » que la facture |
| avoir | `paid` | info « Envoyé le {issue} » | succes « Payé le {payment_date} » (repli : « Payé » si date absente) | `{due}` muted |

## 4. Le formulaire (`InvoiceForm`)

Calque, `role="dialog"`, `aria-label`, `Z_LAYER.MODAL_NESTED`, pile Échap,
`id="invoice-form"` : inchangés. Voile `bg-black/60` (plus `bg-black/70`) :
`--color-text` vaut `#E6EDF7` en thème sombre (`globals.css` l.190), donc
`bg-text/60` deviendrait un voile clair ; le voile actuel est toujours
noir (`InvoiceForm.tsx:443` `bg-black/70`, `:967` `bg-black/50`,
`InvoicesPanel.tsx:580` `bg-black/60`). Même classe `bg-black/60` sur le
voile du dialogue de conversion. Exception assumée dans le test couleurs
(§ 6) : un voile reste noir dans les deux thèmes. Surface `bg-surface
border border-border rounded-md shadow-sm`, plus `backdrop-blur-xl` ni
`shadow-2xl`.

| Zone | Aujourd'hui | Cible |
|---|---|---|
| Tête | `h2` « Nouveau devis » / « Nouvelle facture » / « Nouvel avoir » / `Modifier {n}` ; `X` nommé Fermer | mêmes chaînes ; `h2` `font-editorial` ; `Button variant="ghost" size="icon"` `type="button"` `aria-label="Fermer"` children `<X className="h-[18px] w-[18px]" />` |
| Profil incomplet / illisible | bandeaux `bg-agent-amber/10` | mêmes textes, `bg-[var(--color-warning-tint)] border border-warning/30 text-warning` ; illisible garde `role="alert"` |
| Type (création) | trois `<button type="button">` | `Segments label="Type de document"` Devis / Facture / Avoir, `valeur={documentType}` (`type="button"` déjà dans la primitive) |
| Champs | `<label>` + `<input>`/`<select>`/`<textarea>` maison | `FormField` + `Input` / `Select` / `Textarea` ; ids `contact`, `status`, `currency`, `issueDate`, `dueDate`, `validiteJours`, `notes`, `invoiceform-description-{i}`, `invoiceform-quantite-{i}`, `invoiceform-prix-{i}`, `invoiceform-tva-{i}` ; option vide « Sélectionner un contact » (`value=""`), pas `placeholder` disabled du `Select` ; `required` natifs conservés **sauf** la description des lignes (contact, `issueDate`, `dueDate`, quantité, prix HT). `FormField.label` = libellés actuels, étoile **dans la chaîne**, **sans** `FormField.required` (le `*` de `FormField.tsx:61` est `aria-hidden="true"`, le nom accessible deviendrait « Client » et casserait `InvoiceForm.clientHorsFenetre.test.tsx:54` `getByLabelText('Client *')`) : `label="Client *"` `htmlFor="contact"` (`Select` `id="contact"` `required`) ; `label="Statut"` `htmlFor="status"` ; `label="Devise"` `htmlFor="currency"` ; `label="Date d'émission *"` `htmlFor="issueDate"` (`Input` `required`) ; `label="Date d'échéance *"` `htmlFor="dueDate"` (`Input` `required`) ; `label="Validité (jours)"` `htmlFor="validiteJours"` ; `label="Notes"` `htmlFor="notes"`. `Select` Statut : mêmes deux listes qu'aujourd'hui (`InvoiceForm.tsx:588-604`) — devis : Brouillon / Envoyé / Accepté / Refusé / Expiré / Converti en facture / Annulée ; facture et avoir : Brouillon / Envoyé / Payée / En retard / Annulée (`statutsProposes.test.tsx` conservé, pas à aligner). Titre du bloc lignes : nœud visible `text-sm font-medium text-text` « Lignes de facturation * » (`InvoiceForm.tsx:697`, pas « Lignes ») ; ce n'est pas un `FormField` |
| Client, bandeau contacts | `contactsTronques` : `<p role="alert" className="mt-1 text-sm text-warning">Liste incomplète : seuls les {PLAFOND_CONTACTS} contacts les plus récents sont proposés.</p>` (`InvoiceForm.tsx:563-568`) | inchangé (chaînes, `role`, jeton `warning`) ; sous le `Select` client, pas une `Alerte` |
| Lignes | cartes empilées, labels `text-xs` | `<table>` de lignes (jetons) ; `th` : « Description », « Quantité » (pas « Qté » de la maquette : `InvoiceForm.francais.test.tsx` exige `getByText('Quantité')`), « Prix HT », « TVA », « Total HT », dernière `th` `sr-only` « Actions ». **Aucun** `<label>` visuel dans les `td` : le `th` + `aria-label` du champ suffisent (`getByText('Quantité')` jette s'il reste le `label` actuel `InvoiceForm.tsx:750` en plus du `th`) |
| Description d'une ligne | `<input required aria-label={`Description ligne ${i+1}`}>` `placeholder="Description"` | `Input` `id={`invoiceform-description-${i}`}` `aria-label={`Description ligne ${i+1}`}` `placeholder="Description"` **sans `required`**. Après `handleSubmit` : **chaque** ligne dont `!description.trim()` reçoit `error` + `aria-invalid` (prop `error` de `Input`) + `aria-describedby={`invoiceform-description-${i}-erreur`}` vers un `p` `id={`invoiceform-description-${i}-erreur`}` `role="alert"` `className="mt-1 font-medium text-error text-sm"` (maquette `.erreur-champ`) « Renseigne la description de cette ligne, ou supprime-la. » **Pas** un `FormField` dans la `td` (`FormField.label` est obligatoire ; sans `htmlFor`, `errorId` n'est pas calculé, `FormField.tsx:12` et `:30-47`). Au moment du `return` de validation, **avant** de sortir de `handleSubmit` : `document.getElementById(\`invoiceform-description-${i}\`)?.focus()` sur la première ligne vide (l'`id` est sur l'`<input>` interne, `Input` transmet `...props` ; le pied vit hors du bloc défilant, B-011 `InvoiceForm.tsx:478-482`, le `required` natif ne scrolle plus vers le champ). L'erreur d'une ligne tombe au `onChange` de sa description dès que `description.trim()` est non vide (`error` / `aria-invalid` / `p role="alert"` retirés pour cette ligne) ; une ligne encore vide reste marquée jusqu'à saisie ou prochaine soumission. |
| Validation BUG-132 | `if (lines.every((line) => !line.description.trim()))` + notification ; le `required` natif bloque avant `onSubmit` si une ligne est vraiment vide | valider **chaque** ligne sans description trimée (état maquette `nouveau` : ligne 1 remplie, ligne 2 vide, message sous le champ). Notification BUG-132 « Renseigne la description d'au moins une ligne » **seulement si toutes** les lignes sont vides ; si au moins une ligne est remplie, pas de notification, uniquement les `p role="alert"` des lignes vides. `return` dans les deux cas (pas d'enregistrement). |
| Quantité / Prix HT / TVA | `aria-label={`Quantité ligne ${i+1}`}` + `id={`invoiceform-quantite-${i}`}` ; Prix HT : `aria-label={`Prix HT ligne ${i+1}`}` sans `id` (`InvoiceForm.nomsAccessibles.test.tsx:47-48`, `InvoiceForm.soumission.test.tsx`, `InvoiceForm.test.tsx`) ; TVA : `<label htmlFor={`invoiceform-tva-${index}`}>TVA</label>` + `<select id={`invoiceform-tva-${index}`}>` sans `aria-label` (`InvoiceForm.tsx:786-787`) | garder les deux `aria-label` quantité et prix ; `id={`invoiceform-quantite-${i}`}` conservé ; **ajouter** `id={`invoiceform-prix-${i}`}` (le prix est aujourd'hui anonyme hors `aria-label`) ; `required` conservé sur les deux. TVA : `Select` `id={`invoiceform-tva-${i}`}` `aria-label={`TVA ligne ${i+1}`}` (comme `InvoiceConversationCard.tsx:615`) `options={TVA_RATES.map((r) => ({ value: String(r.value), label: r.label }))}` `value={String(line.tva_rate)}` ; **pas** de `label` visuel dans la `td` ; **pas** de `FormField` dans la `td` ; pas de `required` sur la TVA (inchangé) |
| Ajouter / supprimer ligne | boutons maison, `type="button"` déjà (`InvoiceForm.tsx:700`, `:739`) | `Button ghost md` `type="button"` « Ajouter une ligne » **sous** le `<table>` (maquette `devis.html:102`, pas à droite du titre) ; `Button ghost icon` `type="button"` `aria-label={`Supprimer la ligne ${i+1}`}` children `<Trash2 className="h-[18px] w-[18px]" />` |
| Totaux | `text-2xl text-accent-cyan-ink` | `grid grid-cols-[1fr_auto] justify-end gap-x-6 gap-y-1 tabular-nums` ; « Total TTC » `font-semibold text-lg` ; `montantAvecDevise` inchangé |
| Pied | Marquer comme payée / Accepter / Refuser / Convertir en facture / Annuler / Créer | mêmes libellés, mêmes gardes ; le bouton du pied reste **« Convertir en facture »** (`InvoiceForm.tsx:932`) ; le dialogue seul dit « Convertir » (`InvoiceForm.tsx:1008`). `Button md` : payée et Accepter `secondary`, Refuser `secondary` (comme Annuler : `Button.tsx:30` `ghost` = `text-accent hover:bg-accent-tint`, ce n'est pas un refus), Convertir en facture `secondary`, Annuler `secondary`, soumission `primary` liée à `form={ID_FORMULAIRE}` (`type="submit"`, seul submit) « Créer » / « Mettre à jour » / « Sauvegarde... ». **Chaque `Button` hors soumission porte `type="button"`** (un `Button` dans un `<form>` sans `type` devient submit) |
| Conversion | dialogue actuel | mêmes chaînes ; Annuler `secondary md` `type="button"`, Convertir `primary md` `type="button"` ; voile `bg-black/60` ; surface jetons comme le formulaire |

Conditions de paiement : bloc en lecture seule s'il existe, jetons seulement.

## 5. Les états (corps du panneau)

Priorité inchangée (`InvoicesPanel.tsx`, `isLoading` puis `loadError` puis
vide filtré puis vide défaut puis liste). Un seul « Réessayer », sur
l'erreur de chargement. Chargement, erreur, vides et tableau sont
**enfants de la même `Carte`** du § 3 : les trois états remplacent le
`<table>`, ils ne s'affichent ni hors carte ni à côté.

| État | Aujourd'hui | Cible |
|---|---|---|
| chargement | « Chargement... » centré | dans la `Carte`, à la place du `<table>` : trois rangées `aria-hidden` `grid grid-cols-7 gap-3 px-4 py-3 border-t border-border` (7 pistes = 7 colonnes, pas `grid-cols-[6rem_1fr_auto]`) : `Squelette` `largeur="w-24"`, `largeur="w-[60%]"`, `largeur="w-20"`, `largeur="w-20"`, `largeur="w-16"`, `largeur="w-16"`, `largeur="w-12"` ; puis « Chargement... » `role="status"` `px-4 py-3 text-sm text-text-muted` |
| erreur | icône 4 rem + texte + bouton plein | dans la `Carte`, à la place du `<table>` : `Alerte data-testid="invoices-load-error" icone={<AlertCircle 18 px />} titre="Chargement impossible"` `children` = `loadError` (`Impossible de charger les factures pour le moment.`) `action` = `Button secondary md` `type="button"` Réessayer → `loadInvoices` |
| vide, filtre `overdue` | « Aucun document ne correspond à ce filtre. » + Réinitialiser | dans la `Carte`, à la place du `<table>` : `EtatVide data-testid="invoices-empty-overdue"` titre « Aucune pièce en retard », `children` = « Les factures échues et impayées apparaîtront ici. » (pas de prop `texte` : `EtatVide.tsx:11-16` expose `titre` / `children` / `action`), `action` = `Button secondary md` `type="button"` « Réinitialiser les filtres » (`setFilters({})`) ; pas de Relancer |
| vide, autre filtre effectif (B-646) | même phrase générique + Réinitialiser | dans la `Carte`, à la place du `<table>` : `EtatVide data-testid="invoices-empty-filtre"` titre « Aucun document ne correspond à ce filtre. », même action |
| vide, aucun filtre effectif | « Aucune facture » + « Créer une facture » | dans la `Carte`, à la place du `<table>` : `EtatVide data-testid="invoices-empty"` titre « Aucune facture », `action` = `Button primary md` `type="button"` « Créer une facture » → `handleCreateNew` |

`filtreEffectif` inchangé. Confirmation de suppression : surface
`bg-surface border border-border rounded-md shadow-sm` (plus
`backdrop-blur-xl` ni `shadow-2xl`), voile `bg-black/60` (plus
`bg-black/70`), Annuler `secondary md` `type="button"`, Supprimer
`danger md` `type="button"`, chaînes inchangées.

Voile du panneau en mode calque (`standalone={false}`) : `bg-black/60`
(classe actuelle `InvoicesPanel.tsx:580`, conservée). Tous les
`bg-black/*` des deux fichiers deviennent `bg-black/60` (formulaire
`:443` `/70`, conversion `:967` `/50`, confirmation panneau `:495`
`/70`, calque `:580` `/60`). Pas `bg-text/60` : le jeton s'inverse en
thème sombre.

## 6. Gardes mécaniques et tests à aligner

Nouveaux, rouges d'abord :

`InvoicesPanel.da.test.tsx` : (1) une ligne = `data-testid="invoice-item"`
sur un `tr` **sans** `tabIndex` ; `onClick` d'ouverture présent (clic sur
la `td` Pièce, hors boutons, appelle `handleEdit`) ; bouton client + PDF +
Supprimer ; (2) une facture `overdue` montre **deux** `data-etiquette`
(envoi `ton="info"`, paiement `ton="erreur"`) + une `td` d'échéance
`text-error` « · échue » (pas une `Etiquette`) et le montant en
`tabular-nums` ; (3) un devis `sent` écrit « Envoyé le », « En attente
d'accord », « Valable jusqu'au » ; un avoir `sent` écrit « Envoyé le »
(pas « Envoyée le ») et « Impayé » (pas « Impayée ») ; un avoir `paid`
écrit « Payé le » / « Payé » (pas « Payée ») ; un avoir `overdue` écrit
« Impayé » + « · échue » ; (4) compteur « 1 pièce », « 2 pièces », « 0 pièce »,
« 2 pièces, dont 1 pièce échue » / « dont 2 pièces échues », « 100+
pièces » sans « dont » si aucun `overdue` ; un brouillon devis montre
`{due}` avec année et, si `validite_jours`, « Validité : {n} jours » (pas
« Non envoyé ») ; (5) Segments Type et Statut : `aria-pressed` sur Tout +
Toutes au départ, clic Devis appelle le même assainissement qu'aujourd'hui ;
(6) un seul « Réessayer » sur l'erreur, zéro ailleurs ; squelettes
`aria-hidden` `grid-cols-7` (7 `Squelette`) + `role="status"` au chargement,
**dans** la `Carte` à la place du `<table>` ; vide `overdue` ≠ vide
défaut ≠ vide autre filtre, mêmes trois `EtatVide` dans la `Carte` ; (7) aucun interactif en `text-xs` ; dans
`InvoicesPanel.tsx` et `InvoiceForm.tsx`, hors commentaires : la regex
existante `COULEUR_EN_DUR` (`#[0-9A-Fa-f]`, `rgba?(`, `hsla?(`,
`color-mix(`) **et** aucune occurrence de `bg-black` **sauf** les voiles
`bg-black/60`, aucune de `bg-gray-`, `text-agent-`, `bg-agent-` (l'extension
de `aucuneCouleurEnDur` à ces deux fichiers ne suffit pas : cette regex
ignore les utilitaires Tailwind) ;
(8) « Nouveau devis » / « Nouvelle facture » est `h-11` (`Button
size="lg"`) ; les autres `Button` du panneau sont `h-9` (`size="md"`) ou
`size="icon"` (`h-9 w-9`) ; **exclure** `[role=group] button` (Segments
Type / Statut, `py-1`).

`InvoiceForm.da.test.tsx` : (1) `form="invoice-form"` toujours sur le seul
`type="submit"` ; tous les autres `Button` du formulaire et du dialogue de
conversion portent `type="button"` ; sur un devis `sent` (Refuser visible,
`InvoiceForm.tsx:898`), « Refuser » est `secondary` (`text-text`, pas
`text-accent` du `ghost`) ; (2) BUG-132, toutes les lignes trimées
vides : notification conservée ET `aria-invalid` + le texte d'erreur de
ligne sur chaque ligne ; état maquette `nouveau` (ligne 1 remplie, ligne 2
vide) : **prérequis avant `requestSubmit`** = contact renseigné (le
`Select` `required` et `contactId === ''` bloqueraient sinon, dates déjà
défaut, quantité `1` et prix HT `0` déjà défaut `InvoiceForm.tsx:122-131`)
puis `requestSubmit` atteint `handleSubmit` (plus de `required` sur la
description), **pas** de notification BUG-132, `aria-invalid` + message
sous la ligne 2 seulement, `document.activeElement` = l'`input`
`id="invoiceform-description-1"` ; saisie d'une description trimée sur
cette ligne : `aria-invalid` et le `p role="alert"` disparaissent pour
elle ; (3) `Segments` Type de document en création ; (4) Fermer et
Supprimer la ligne 1 restent nommés (`aria-label="Fermer"` /
`aria-label="Supprimer la ligne 1"`) et portent `<X className="h-[18px] w-[18px]" />` /
`<Trash2 className="h-[18px] w-[18px]" />` ; (5) ids uniques, y
compris `invoiceform-description-{i}`, `invoiceform-prix-{i}` et
`invoiceform-tva-{i}` ; `getByLabelText('Quantité ligne 1')`,
`getByLabelText('Prix HT ligne 1')` et `getByLabelText('TVA ligne 1')`
restent vrais ; `getByLabelText('Client *')`,
`getByLabelText("Date d'émission *")`, `getByText('Lignes de facturation *')`.

À aligner dans le même commit (forme, pas comportement) :
`InvoicesPanel.chargementEchoue.test.tsx` (`'100+ documents'` →
`'100+ pièces'`, `compteur.textContent === '0 document'` → `'0 pièce'` ;
commentaire du bandeau « 100 documents » → « 100 pièces »),
`InvoicesPanel.troncature.test.tsx` (`'100+ documents'` → `'100+ pièces'`,
`'1 document'` → `'1 pièce'`, `'2 documents'` → `'2 pièces'` ; bandeau
toujours `/Liste incomplète/`, texte désormais « seules les 100 pièces les
plus récentes » ; le commentaire « plusieurs nœuds texte dans un même
`<p>` » désigne le `<p data-testid="invoices-compteur">`, pas le titre),
`InvoicesPanel.etatVideParDefaut.test.tsx` (le cas `status: 'paid'` vise
toujours `/ne correspond à ce filtre/` ; un cas `overdue` éventuel viserait
« Aucune pièce en retard », à n'ajouter que si le fichier teste déjà
`overdue` : il ne le teste pas), `InvoicesPanel.clavier.test.tsx`
(commentaire « carte » → « ligne » ; assertions de rôles inchangées : la
commande nommée reste le bouton client, le `tr` n'a pas de `tabIndex`),
`InvoicesPanel.test.tsx` (getByTitle PDF / Supprimer conservés ; « Aucune
facture » conservé ; le cas « formulaire parent » l.100-122 reste vert grâce
aux `type="button"` du panneau). `InvoiceForm.soumission.test.tsx` (`/Créer/`,
`getByLabelText('Prix HT ligne 1')` conservé ; le 4e cas
l.95-112 « description laissée VIDE : le champ porte `required` » /
`expect(invalide).toHaveBeenCalledTimes(1)` : **retargeter** l'écoute
`invalid` sur le `Select` contact, qui reste `required` — plus sur la
description, désormais sans `required` ; remplir rien, cliquer `/Créer/`,
`getByLabelText('Client *')` reçoit `invalid`),
`InvoiceForm.test.tsx` (placeholder `Description`, `/Créer/`,
`Quantité ligne 1` / `Prix HT ligne 1` conservés),
`InvoiceForm.francais.test.tsx` (`getByText('Quantité')` conservé : un
seul nœud texte, le `th`, plus le `label` de la `td`),
`InvoiceForm.nomsAccessibles.test.tsx` (`Quantité ligne ${rang}` et
`Prix HT ligne ${rang}` conservés),
`InvoiceForm.clientHorsFenetre.test.tsx` (`getByLabelText('Client *')`
conservé : `FormField label="Client *"` sans `FormField.required`),
`InvoiceForm.identifiants.test.tsx` : aucune chaîne métier à changer.
Aucune assertion de comportement n'est retirée.

## 7. Ce que ce lot ne fait pas

- Quatre cartes de résumé, bouton Exporter, recherche « Client, référence… »,
  « Tri : échéance », raison sociale sous le client, nom d'atelier dans le
  sous-titre : données ou agrégats absents (le plafond 100 rendrait un total
  local menteur). Portail, P-072.
- « Relancer » sur la ligne et dans le vide en retard : aucun envoi (test
  « ne présente pas un envoi email »). Portail, P-073.
- « Convertir » sur la ligne : le parcours vit dans le formulaire (P-014).
  Portail, P-074.
- Création en page : fil d'Ariane, champ Objet, client créé depuis le champ,
  « Valable jusqu'au » en date, conditions saisies, brouillon auto, aperçu
  PDF, libellé « Valider le devis ». Portail, P-075.
- Factur-X (pied de maquette) : déjà P-026. Franchise de TVA : déjà P-028.
- PDF ReportLab, API, store, navigation, mode calque du panneau.
- Nombre `validite_jours` des devis déjà envoyés (aujourd'hui « Validité :
  {n} jours ») : remplacé par « Valable jusqu'au {due} », la date de fin
  reste. Conservé en clair sur les brouillons seulement.
- Date d'émission des pièces `cancelled` (aujourd'hui « Émis le » / « Émise
  le ») : l'envoi reste la pilule « Annulée », sans la date.

## 8. Plan de preuve

1. Tests rouges d'abord (§ 6), vérifiés rouges pour la bonne raison,
   sabotage par remplacement inverse, `.agents-sync-paused` posé.
2. Six portes : ruff, pytest (XML), vitest json, tsc, eslint (27), mypy 951.
3. Recette visuelle, pile jetable (17393 et 1420, jamais 17293) : états
   forcés par `page.route` sur `**/api/invoices*` et
   `**/api/invoices/billing/profile-status` (liste de quatre pièces dont une
   `overdue` ; vide sans filtre ; vide `status=overdue` ; vide `status=paid` ;
   chargement lent ; 500 ; formulaire nouveau avec ligne 1 remplie et ligne 2
   vide soumise : message sous le champ, pas de notification BUG-132, focus
   dans la description de la ligne 2 ; profil
   incomplet), à 1280, 1024, 840 et 800 px, clair, sombre, contraste élevé,
   trois tailles de police ; captures
   `.cartography-work/validation/da-lot5/`, rapport
   `docs/da/2026-09-11-lot5-recette.md`. Vérifier : montants à droite en
   chiffres tabulaires, trois colonnes de statut, Avoirs toujours là, un
   seul Réessayer, anneau de focus sur une ligne (bouton client) et sur un
   segment, `Nouveau devis` entier à 800 px, placeholder `Description`
   conservé, dates de liste avec année, clic souris sur la rangée ouvre,
   bandeau de troncature « pièces », compteur « dont M pièces échues »,
   avoir « Impayé » / « Payé », voile toujours sombre en thème sombre,
   `Refuser` en `secondary` (pas en accent), squelette à 7 pistes dans la
   `Carte`.
4. Revue Grok du diff avant fusion dans `main` ; pas de tag de lot.

## 9. Points non repris

Aucun de la revue v3. Les 6 constats du journal
`.cartography-work/reviews/grok-da-lot5-devis-design-v3.log` (3 P2, 3 P3)
sont fondés ; chacun a une correction dans les sections 1 à 6 (bouton Client
sans doublon du numéro, `type="button"` des quatre gestes du panneau, nom
accessible du PDF, scroller vertical du corps, options du `Select` Statut,
« Ajouter une ligne » sous le tableau).

Aucun de la revue v2. Les 13 constats du journal
`.cartography-work/reviews/grok-da-lot5-devis-design-v2.log` (1 P1, 7 P2,
5 P3) sont fondés ; chacun a une correction dans les sections 1 à 8
(fichiers et lignes du journal v2 revus : `InvoiceForm.tsx:240-242`,
`:478-482`, `:697`, `:750`, `:786-787` ; `InvoiceConversationCard.tsx:615` ;
`InvoiceForm.soumission.test.tsx:95-112` ; `InvoiceForm.test.tsx:128-129` ;
`InvoiceForm.clientHorsFenetre.test.tsx:54` ; `InvoiceForm.francais.test.tsx:92` ;
`FormField.tsx:61` ; `Button.tsx:9-13`, `:30` ; `InvoicesPanel.tsx:580` ;
`globals.css:18`, `:190` ; `Input.tsx:27-38`).

Revue v1 (déjà absorbée en v2) : 16 constats (3 P1, 6 P2, 7 P3) fondés
(`InvoiceForm.tsx:252`, `:563-568`, `:700`, `:734`, `:752`, `:770`,
`:932`, `:1008` ; `InvoicesPanel.tsx:236-242`, `:386`, `:436-440` ;
`EtatVide.tsx:11-16` ; `FormField.tsx:12`, `:30-47` ; `segments.classes.ts:12` ;
`aucuneCouleurEnDur.test.ts:36` ; `InvoiceForm.nomsAccessibles.test.tsx:47-48` ;
`InvoiceForm.francais.test.tsx:92` ; maquette `devis.html:74`, `:96`, `:99`).
