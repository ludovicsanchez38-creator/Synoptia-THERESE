Excellent! J'ai maintenant une compréhension complète du projet. Laissez-moi compiler les user stories basées sur le code exploré :

## RAPPORT USER STORIES - THÉRÈSE v2

### Module CRM - Phase 5

```
### US-300 : Créer et gérer les contacts du CRM
**En tant que** solopreneur/TPE
**Je veux** créer et maintenir une base de contacts structurée
**Afin de** gérer mes prospects et clients dans un pipeline commercial

**Critères d'acceptation :**
- [ ] Créer un contact avec nom, entreprise, email, téléphone, adresse, notes
- [ ] Source automatique par défaut = 'THERESE' si non fournie
- [ ] Score initial = 50, calculé dynamiquement (email +20, phone +15, company +10, etc.)
- [ ] Stage initial = 'contact' (contact → discovery → proposition → signature → delivery → active → archive)
- [ ] Synchroniser vers Google Sheets si configuré (OAuth Google + spreadsheet_id)
- [ ] Importer contacts depuis CSV/Excel/JSON avec mapping automatique colonnes FR/EN
- [ ] Importer contacts VCard (.vcf) avec détection doublons par email

**Composants :** 
- Backend: `/src/backend/app/routers/crm.py` (POST /contacts, POST /import/contacts, POST /import/vcf)
- Frontend: `/src/frontend/src/components/crm/CRMPanel.tsx`
- Services: `/src/backend/app/services/crm_import.py`, `/src/backend/app/services/crm_utils.py`
- Models: `Contact` (entities.py), `CreateCRMContactRequest` (schemas.py)

**data-testid :** crm-panel
```

```
### US-301 : Pipeline commercial avec 7 stages
**En tant que** solopreneur/TPE
**Je veux** visualiser et gérer mon pipeline de ventes avec drag & drop
**Afin de** suivre l'avancement de mes prospects dans le parcours commercial

**Critères d'acceptation :**
- [ ] Vue Kanban avec 7 colonnes (Contact, Découverte, Proposition, Signature, Livraison, Actif, Archive)
- [ ] Drag & Drop contacts entre stages (utilise @dnd-kit)
- [ ] Changement de stage crée automatiquement une activité 'stage_change'
- [ ] Recalcul du score au changement de stage
- [ ] Affichage score moyen et nombre de contacts par stage
- [ ] Statistiques pipeline (total contacts, répartition par stage, taux conversion)

**Composants :**
- Backend: `/src/backend/app/routers/crm.py` (PATCH /contacts/{id}/stage, GET /pipeline/stats)
- Frontend: `/src/frontend/src/components/crm/PipelineView.tsx`
- Models: `UpdateContactStageRequest` (schemas.py)

**data-testid :** pipeline-view, stage-column-{stage_id}, contact-card
```

```
### US-302 : Système de scoring des prospects
**En tant que** solopreneur/TPE
**Je veux** que chaque contact soit noté selon son potentiel commercial
**Afin de** prioriser mes actions commerciales

**Critères d'acceptation :**
- [ ] Score = base 50 + points qualitatifs (email +20, phone +15, company +10)
- [ ] Bonus source = referral +25, website +15, linkedin +20
- [ ] Bonus interaction = meeting +25, call +15, email +10, stage_change basé stage
- [ ] Decay = -5 points tous les 30 jours d'inactivité
- [ ] Recalcul manuel via POST /contacts/{id}/recalculate-score
- [ ] Recalcul batch automatique au changement de stage ou interaction
- [ ] Créer activité 'score_change' lors du changement de score

**Composants :**
- Backend: `/src/backend/app/services/scoring.py`, `/src/backend/app/routers/crm.py`
- Models: `Activity` (type='score_change'), `ContactScoreUpdate` (schemas.py)

**data-testid :** score-badge, score-details
```

```
### US-303 : Timeline des activités du contact
**En tant que** solopreneur/TPE
**Je veux** voir l'historique complet des interactions avec un contact
**Afin de** assurer un suivi continu et contextuel

**Critères d'acceptation :**
- [ ] Afficher activités par contact (email, call, meeting, note, stage_change, score_change)
- [ ] Format humanisé des dates (à l'instant, il y a Xmin, il y a Xj, date)
- [ ] Icône et couleur par type d'activité
- [ ] Description et extra_data (JSON) optionnels
- [ ] Créer automatiquement au changement de stage ou score
- [ ] Créer manuellement via create_activity + titre + description
- [ ] Supprimer une activité (delete)

**Composants :**
- Backend: `/src/backend/app/routers/crm.py` (GET /activities, POST /activities, DELETE /activities/{id})
- Frontend: `/src/frontend/src/components/crm/ActivityTimeline.tsx`
- Models: `Activity`, `CreateActivityRequest`, `ActivityResponse` (schemas.py)

**data-testid :** activity-timeline, activity-item-{activity_id}, activity-icon-{type}
```

```
### US-304 : Synchronisation Google Sheets biirectionnelle
**En tant que** solopreneur/TPE
**Je veux** synchroniser mon CRM local avec un Google Sheets comme source externe
**Afin de** mutualiser les données avec mon équipe ou un outil externe

**Critères d'acceptation :**
- [ ] Configurer spreadsheet_id dans préférences (POST /sync/config)
- [ ] OAuth Google Sheets (3-legged flow, scopes GSHEETS_SCOPES)
- [ ] Sync unidirectionnelle : Google Sheets → THERESE (master data = Sheets)
- [ ] Structure auto-créée : Clients, Projects, Deliverables, Tasks
- [ ] Upsert contacts/projects/deliverables/tasks avec mapping colonnes
- [ ] Créer activité à la création d'un contact via push (inversement)
- [ ] Tracker last_sync_time en préférence
- [ ] Gérer erreurs de sync (token expiré, sheet invalide) avec fallback

**Composants :**
- Backend: `/src/backend/app/routers/crm.py` (GET /sync/config, POST /sync/config, POST /sync/credentials, POST /sync)
- Services: `/src/backend/app/services/crm_sync.py`, `/src/backend/app/services/sheets_service.py`
- Models: `CRMSyncConfigRequest`, `CRMSyncConfigResponse`, `CRMSyncResponse` (schemas.py)

**data-testid :** sync-config-panel, sync-status
```

```
### US-305 : Export CRM en CSV/Excel/JSON
**En tant que** solopreneur/TPE
**Je veux** exporter mes données CRM dans des formats standards
**Afin de** les importer dans un autre outil ou créer des rapports

**Critères d'acceptation :**
- [ ] Exporter contacts avec filtres (stage, source)
- [ ] Exporter projets avec filtres (status, contact_id)
- [ ] Exporter livrables avec filtres (status, project_id)
- [ ] Export tout (contacts + projets + livrables) en Excel multi-onglets
- [ ] Formats : CSV, Excel (openpyxl), JSON
- [ ] Noms de fichiers : crm_contacts_YYYY-MM-DD.{ext}

**Composants :**
- Backend: `/src/backend/app/routers/crm.py` (POST /export/contacts, POST /export/projects, POST /export/deliverables, POST /export/all)
- Services: `/src/backend/app/services/crm_export.py`

**data-testid :** export-button-{format}
```

```
### US-306 : Livrables et jalons par projet
**En tant que** solopreneur/TPE
**Je veux** découper mes projets en livrables avec dates d'échéance
**Afin de** suivre l'avancement des réalisations

**Critères d'acceptation :**
- [ ] Créer livrable pour un projet (title, description, due_date, status)
- [ ] Statuts livrables : a_faire, en_cours, en_revision, valide
- [ ] Auto-remplir completed_at au changement status → valide
- [ ] Lister livrables par projet ou globalement
- [ ] Mettre à jour (titre, description, statut, date)
- [ ] Supprimer un livrable (cascade du projet)

**Composants :**
- Backend: `/src/backend/app/routers/crm.py` (POST /deliverables, GET /deliverables, PUT /deliverables/{id}, DELETE /deliverables/{id})
- Frontend: `/src/frontend/src/components/crm/DeliverablesList.tsx`
- Models: `Deliverable`, `DeliverableResponse`, `CreateDeliverableRequest` (schemas.py)

**data-testid :** deliverables-list, deliverable-item-{deliverable_id}
```

---

### Module Factures - Phase 4

```
### US-307 : Créer et gérer les factures
**En tant que** solopreneur/TPE
**Je veux** créer des factures professionnelles avec lignes détaillées
**Afin de** facturer mes clients régulièrement

**Critères d'acceptation :**
- [ ] Créer facture liée à un contact
- [ ] Types de documents : devis, facture, avoir
- [ ] Numérotation auto : DEV-YYYY-NNN, FACT-YYYY-NNN, AV-YYYY-NNN
- [ ] Lignes avec description, quantité, prix unitaire HT, taux TVA
- [ ] Calcul auto : total_ht = qty * unit_price, total_ttc = total_ht * (1 + tva/100)
- [ ] Totaux facture : subtotal_ht, total_tax, total_ttc
- [ ] Dates : issue_date (aujourd'hui), due_date (+30j par défaut)
- [ ] Statuts : draft, sent, paid, overdue, cancelled, converted
- [ ] Devise : EUR, CHF, USD, GBP
- [ ] TVA applicable ou exonérée (art. 293 B CGI)
- [ ] Notes et conditions de paiement optionnelles

**Composants :**
- Backend: `/src/backend/app/routers/invoices.py` (POST /api/invoices/, GET /api/invoices/, GET /api/invoices/{id}, PUT /api/invoices/{id})
- Frontend: `/src/frontend/src/components/invoices/InvoicesPanel.tsx`, `/src/frontend/src/components/invoices/InvoiceForm.tsx`
- Models: `Invoice`, `InvoiceLine`, `CreateInvoiceRequest`, `UpdateInvoiceRequest`, `InvoiceResponse` (schemas.py)

**data-testid :** invoices-panel, invoice-form, invoice-list-item-{invoice_id}
```

```
### US-308 : Conversion devis → facture
**En tant que** solopreneur/TPE
**Je veux** convertir un devis accepté en facture
**Afin de** basculer rapidement du devis au processus de facturation

**Critères d'acceptation :**
- [ ] Endpoint POST /invoices/{id}/convert-to-invoice
- [ ] Copier toutes les lignes du devis vers la facture
- [ ] Générer nouveau numéro FACT-YYYY-NNN (auto-incrémental)
- [ ] Ajouter conditions de paiement (30j par défaut)
- [ ] Ajouter méthode de paiement (virement, chèque, etc.)
- [ ] Générer mentions légales obligatoires (pénalité retard, remboursement)
- [ ] Issue_date = aujourd'hui, due_date = issue_date + payment_days
- [ ] Marquer le devis source comme 'converted'
- [ ] Conserver link via converted_from_id

**Composants :**
- Backend: `/src/backend/app/routers/invoices.py` (POST /api/invoices/{id}/convert-to-invoice)
- Models: `ConvertDevisRequest` (schemas.py), `Invoice.converted_from_id`

**data-testid :** convert-devis-button
```

```
### US-309 : Génération PDF conforme facture française
**En tant que** solopreneur/TPE
**Je veux** générer des PDFs professionnels pour mes factures
**Afin de** les envoyer ou imprimer

**Critères d'acceptation :**
- [ ] Endpoint GET /api/invoices/{id}/pdf
- [ ] Layout conforme réglementation française
- [ ] En-tête : données profil utilisateur (nom, SIREN, SIRET, adresse, TVA intra)
- [ ] Destinataire : données du contact (nom, adresse, email)
- [ ] Tableau lignes : description, quantité, PU HT, TVA, total HT, total TTC
- [ ] Totaux : sous-total HT, TVA totale, montant TTC
- [ ] Mentions légales : conditions paiement, pénalité retard (11.62%), indemnité forfaitaire 40€
- [ ] Métadonnées : numéro facture, dates, devise, TVA applicable
- [ ] Stockage : répertoire {working_directory}/factures ou ~/.therese/invoices
- [ ] Format : PDF avec répertoire de sortie conforme (BUG-094)

**Composants :**
- Backend: `/src/backend/app/routers/invoices.py` (GET /api/invoices/{id}/pdf)
- Services: `/src/backend/app/services/invoice_pdf.py` (InvoicePDFGenerator)
- Config: preferences.working_directory pour localisation PDFs

**data-testid :** generate-pdf-button
```

```
### US-310 : Marquer facture comme payée
**En tant que** solopreneur/TPE
**Je veux** enregistrer le paiement d'une facture
**Afin de** mettre à jour mon statut de facturation

**Critères d'acceptation :**
- [ ] Endpoint PATCH /api/invoices/{id}/mark-paid
- [ ] Changer statut → 'paid'
- [ ] Enregistrer payment_date (aujourd'hui par défaut ou fournie)
- [ ] Créer notification de paiement (optional)
- [ ] Vérifier avant : facture existe, statut != déjà payée

**Composants :**
- Backend: `/src/backend/app/routers/invoices.py` (PATCH /api/invoices/{id}/mark-paid)
- Models: `MarkPaidRequest` (schemas.py), `Invoice.payment_date`

**data-testid :** mark-paid-button
```

```
### US-311 : Filtrage et listing des factures
**En tant que** solopreneur/TPE
**Je veux** filtrer et parcourir mes factures
**Afin de** trouver rapidement une facture

**Critères d'acceptation :**
- [ ] Lister avec pagination (skip, limit)
- [ ] Filtrer par : status (draft/sent/paid/overdue), contact_id, document_type
- [ ] Ordre anti-chronologique (recent first)
- [ ] Afficher : numéro, contact, montant TTC, statut, dates
- [ ] Indicateurs visuels par statut (couleurs, icons)

**Composants :**
- Backend: `/src/backend/app/routers/invoices.py` (GET /api/invoices/)
- Frontend: `/src/frontend/src/components/invoices/InvoicesPanel.tsx`
- Models: `InvoiceResponse` (schemas.py)

**data-testid :** invoice-filter-{filter_name}, invoice-list
```

```
### US-312 : Suppression de facture
**En tant que** solopreneur/TPE
**Je veux** supprimer une facture
**Afin de** corriger une erreur ou nettoyer ma base

**Critères d'acceptation :**
- [ ] Endpoint DELETE /api/invoices/{id}
- [ ] Supprimer cascade les lignes (InvoiceLine)
- [ ] Supprimer le PDF généré si existant (InvoicePDFGenerator.delete_invoice_pdf)
- [ ] Confirmation avant suppression

**Composants :**
- Backend: `/src/backend/app/routers/invoices.py` (DELETE /api/invoices/{id})
- Services: `/src/backend/app/services/invoice_pdf.py`

**data-testid :** delete-invoice-button
```

---

### Email-CRM Linking - Features futures

```
### US-313 : Associer emails aux contacts
**En tant que** solopreneur/TPE
**Je veux** lier automatiquement mes emails aux contacts correspondants
**Afin de** avoir un historique d'interactions complètes par contact

**Critères d'acceptation :**
- [ ] Champ contact_id sur EmailMessage entity
- [ ] Auto-matching email → contact par from_email, to_emails, domain
- [ ] Afficher emails liés dans ActivityTimeline du contact
- [ ] Créer activité 'email' lors du sync si contact_id trouvé

**Composants :**
- Backend: `EmailMessage.contact_id` (entities.py), auto-matching logic
- Models: activité type='email' avec body_plain/body_html

**data-testid :** email-activity, linked-email-badge
```

```
### US-314 : FollowUp (suivi métier avec relance)
**En tant que** solopreneur/TPE
**Je veux** être notifié des contacts à relancer
**Afin de** ne pas oublier de prospects chauds

**Critères d'acceptation :**
- [ ] Identifier contacts inactifs (last_interaction > 30j par exemple)
- [ ] Créer notification de relance automatique
- [ ] Action proposée : "Relancer" avec raccourci pour créer activité
- [ ] Tracker en Notification entity (source='crm', action_url='/crm/contacts/{id}')

**Composants :**
- Backend: notification logic, scoring decay
- Models: `Notification` (entities.py)

**data-testid :** followup-notification, relance-button
```

---

### Résumé d'intégration

**Fichiers clés lus :**
- `/src/backend/app/routers/crm.py` (13,569 lignes - 11 endpoints CRM)
- `/src/backend/app/routers/invoices.py` (768 lignes - 9 endpoints factures)
- `/src/frontend/src/components/crm/` (CRMPanel, PipelineView, ActivityTimeline, DeliverablesList)
- `/src/frontend/src/components/invoices/` (InvoicesPanel, InvoiceForm)
- `/src/backend/app/models/entities.py` (Contact, Activity, Invoice, Deliverable, EmailMessage, Project)
- `/src/backend/app/services/scoring.py`, `crm_sync.py`, `crm_export.py`, `crm_import.py`, `invoice_pdf.py`

**Modules couverts :**
- ✅ CRM: Pipeline 7-stages, Scoring, Activités, Livrables, Sync Google Sheets, Import/Export
- ✅ Factures: Devis/Facture/Avoir, PDF conforme FR, Conversion devis→facture, Paiement
- ⚠️ Email-CRM Linking: Champ contact_id sur EmailMessage (prêt mais pas complètement intégré)
- ⚠️ FollowUp: Logique decay en scoring, notifications possibles