/**
 * THERESE v2 - Invoice Form
 *
 * Formulaire de creation/edition de facture.
 * Phase 4 - Invoicing
 * US-018 : Conversion devis -> facture + conditions de paiement
 */

import { useState, useEffect, useRef, type FormEvent } from 'react';
import { motion } from 'framer-motion';
import { X, Plus, Trash2, Save, FileCheck, AlertTriangle } from 'lucide-react';
import { createInvoice, updateInvoice, convertDevisToInvoice, updateDevisStatus, type Invoice, type InvoiceLineRequest, listContacts, getContact, type Contact, markInvoicePaid } from '../../services/api';
import { PLAFOND_CONTACTS } from '../../stores/contactsStore';
import { useStatusStore } from '../../stores/statusStore';
import { useBillingProfileStore } from '../../stores/billingProfileStore';
import { montantAvecDevise } from '../../lib/devise';
import { cn } from '../../lib/utils';
import { Z_LAYER } from '../../styles/z-layers';
import { pushEscapeHandler } from '../../lib/escapeStack';
import { useExternalActionConfirmation } from '../app/useExternalActionConfirmation';
import { Button } from '../ui/Button';
import { FormField } from '../ui/FormField';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { Segments } from '../ui/Segments';
import { Textarea } from '../ui/Textarea';

interface InvoiceFormProps {
  invoice: Invoice | null;
  /** B-388 : type ouvert depuis une liste filtrée (devis) */
  defaultDocumentType?: 'devis' | 'facture' | 'avoir';
  onClose: () => void;
  onSave: (invoice: Invoice) => void;
}

interface InvoiceLineInputState {
  quantity: string;
  unit_price_ht: string;
}

const TVA_RATES = [
  { value: 20.0, label: '20% (normale)' },
  { value: 10.0, label: '10% (intermédiaire)' },
  { value: 5.5, label: '5,5% (réduite)' },
  { value: 2.1, label: '2,1% (super réduite)' },
  { value: 0.0, label: '0% (exonéré)' },
];

const CURRENCIES = [
  { value: 'EUR', label: 'EUR (€)' },
  { value: 'CHF', label: 'CHF' },
  { value: 'USD', label: 'USD ($)' },
  { value: 'GBP', label: 'GBP (£)' },
  { value: 'CAD', label: 'CAD (CA$)' },
];

const OPTIONS_TYPE_DOCUMENT = [
  { id: 'devis', label: 'Devis' },
  { id: 'facture', label: 'Facture' },
  { id: 'avoir', label: 'Avoir' },
];

const OPTIONS_STATUT_DEVIS = [
  { value: 'draft', label: 'Brouillon' },
  { value: 'sent', label: 'Envoyé' },
  { value: 'accepted', label: 'Accepté' },
  { value: 'refused', label: 'Refusé' },
  { value: 'expired', label: 'Expiré' },
  { value: 'converted', label: 'Converti en facture' },
  { value: 'cancelled', label: 'Annulée' },
];

const OPTIONS_STATUT_FACTURE = [
  { value: 'draft', label: 'Brouillon' },
  { value: 'sent', label: 'Envoyé' },
  { value: 'paid', label: 'Payée' },
  { value: 'overdue', label: 'En retard' },
  { value: 'cancelled', label: 'Annulée' },
];

/** Rattache le bouton d'envoi, rendu hors du bloc défilant, à son formulaire. */
const ID_FORMULAIRE = 'invoice-form';

function formatDecimalInput(value: number) {
  return String(value);
}

function isValidDecimalDraft(value: string) {
  return /^\d*([.,]\d*)?$/.test(value);
}

function parseDecimalDraft(value: string) {
  if (!value.trim()) return null;
  const normalized = value.replace(',', '.').trim();
  if (!/^\d*(\.\d*)?$/.test(normalized)) return null;
  const parsed = Number.parseFloat(normalized);
  return Number.isNaN(parsed) ? null : parsed;
}

export function InvoiceForm({ invoice, onClose, onSave, defaultDocumentType }: InvoiceFormProps) {
  const requestExternalAction = useExternalActionConfirmation();
  const addNotification = useStatusStore((s) => s.addNotification);

  const [contacts, setContacts] = useState<Contact[]>([]);
  const [contactsTronques, setContactsTronques] = useState(false);
  // P0-PROD-2 : garde-fou profil émetteur (raison sociale + SIRET + adresse).
  // État dans un store partagé (pas un useState local) : le formulaire de facture
  // et les Réglages sont deux modales indépendantes qui peuvent rester montées
  // simultanément, donc compléter le profil doit se refléter ici sans remontage.
  const billingMissing = useBillingProfileStore((s) => s.missing);
  const statutLectureProfil = useBillingProfileStore((s) => s.statutLecture);
  const refreshBillingStatus = useBillingProfileStore((s) => s.refresh);
  useEffect(() => {
    void refreshBillingStatus();
  }, [refreshBillingStatus]);
  const [documentType, setDocumentType] = useState<'devis' | 'facture' | 'avoir'>(
    (invoice?.document_type as 'devis' | 'facture' | 'avoir') || defaultDocumentType || 'facture'
  );
  const [contactId, setContactId] = useState(invoice?.contact_id || '');
  const [currency, setCurrency] = useState(invoice?.currency || 'EUR');
  const [issueDate, setIssueDate] = useState(
    invoice?.issue_date.split('T')[0] || new Date().toISOString().split('T')[0]
  );
  const [dueDate, setDueDate] = useState(() => {
    if (invoice?.due_date) {
      return invoice.due_date.split('T')[0];
    }
    const date = new Date();
    date.setDate(date.getDate() + 30);
    return date.toISOString().split('T')[0];
  });
  const [status, setStatus] = useState(invoice?.status || 'draft');
  const [notes, setNotes] = useState(invoice?.notes || '');
  const [validiteJours, setValiditeJours] = useState<number>(
    invoice?.validite_jours ?? 30
  );
  const [lines, setLines] = useState<InvoiceLineRequest[]>(
    invoice?.lines.map((line) => ({
      description: line.description,
      quantity: line.quantity,
      unit_price_ht: line.unit_price_ht,
      tva_rate: line.tva_rate,
    })) || [
      { description: '', quantity: 1, unit_price_ht: 0, tva_rate: 20.0 },
    ]
  );
  const [lineInputs, setLineInputs] = useState<InvoiceLineInputState[]>(
    invoice?.lines.map((line) => ({
      quantity: formatDecimalInput(line.quantity),
      unit_price_ht: formatDecimalInput(line.unit_price_ht),
    })) || [
      { quantity: '1', unit_price_ht: '0' },
    ]
  );

  const [isSaving, setIsSaving] = useState(false);
  const [isConverting, setIsConverting] = useState(false);
  const [showConvertDialog, setShowConvertDialog] = useState(false);
  const [lignesSansDescription, setLignesSansDescription] = useState<number[]>([]);

  // B-228 : la modale n'était inscrite NI dans la pile Échap NI dans le
  // panelStore. `consommeEchapUnifie` rendait donc false, la cascade de la coque
  // tombait sur `collapseEmbeddedView()` et démontait le panneau Devis et
  // factures AVEC son enfant — brouillon compris, en une seule pression.
  // Le ref suit le pattern de SignatureEditorModal : sans lui, une identité de
  // `onClose` recréée à chaque rendu réinscrirait un handler par rendu.
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;
  useEffect(() => pushEscapeHandler(() => onCloseRef.current()), []);

  // Le dialogue de conversion est une couche AU-DESSUS : la pile étant LIFO, il
  // se ferme le premier et laisse le formulaire ouvert.
  useEffect(() => {
    if (!showConvertDialog) return;
    return pushEscapeHandler(() => setShowConvertDialog(false));
  }, [showConvertDialog]);

  // Charger les contacts
  useEffect(() => {
    void loadContacts(invoice?.contact_id);
  }, [invoice?.contact_id]);

  async function loadContacts(clientDeLaPiece?: string) {
    try {
      const data = await listContacts(0, PLAFOND_CONTACTS);
      setContacts(data);
      // Lot F : le devis n'offrait que 50 contacts. Même plafond que le
      // carnet, et on le dit si on l'atteint.
      setContactsTronques(data.length >= PLAFOND_CONTACTS);
      // B-568 : le client de la pièce en cours d'édition peut être hors de la
      // fenêtre des contacts récents ; on le charge à part pour le proposer,
      // sinon le sélecteur retombait sur « Sélectionner un contact ».
      if (clientDeLaPiece && !data.some((c) => c.id === clientDeLaPiece)) {
        try {
          const client = await getContact(clientDeLaPiece);
          setContacts([client, ...data]);
        } catch (error) {
          console.error('Failed to load invoice contact:', error);
        }
      }
    } catch (error) {
      console.error('Failed to load contacts:', error);
    }
  }

  function addLine() {
    setLines([...lines, { description: '', quantity: 1, unit_price_ht: 0, tva_rate: 20.0 }]);
    setLineInputs([...lineInputs, { quantity: '1', unit_price_ht: '0' }]);
  }

  function removeLine(index: number) {
    setLines(lines.filter((_, i) => i !== index));
    setLineInputs(lineInputs.filter((_, i) => i !== index));
    setLignesSansDescription((prev) =>
      prev.filter((i) => i !== index).map((i) => (i > index ? i - 1 : i)),
    );
  }

  function updateLine(index: number, field: keyof InvoiceLineRequest, value: any) {
    const newLines = [...lines];
    newLines[index] = { ...newLines[index], [field]: value };
    setLines(newLines);
  }

  function updateDecimalLineInput(index: number, field: keyof InvoiceLineInputState, rawValue: string) {
    if (!isValidDecimalDraft(rawValue)) {
      return;
    }

    const newInputs = [...lineInputs];
    newInputs[index] = { ...newInputs[index], [field]: rawValue };
    setLineInputs(newInputs);
  }

  function getLineNumericValues(index: number) {
    const quantity = parseDecimalDraft(lineInputs[index]?.quantity ?? '') ?? 0;
    const unitPrice = parseDecimalDraft(lineInputs[index]?.unit_price_ht ?? '') ?? 0;
    return { quantity, unitPrice };
  }

  function calculateLineTotals(line: InvoiceLineRequest, index: number) {
    const { quantity, unitPrice } = getLineNumericValues(index);
    const totalHT = quantity * unitPrice;
    const totalTTC = totalHT * (1 + line.tva_rate / 100);
    return { totalHT, totalTTC };
  }

  function calculateInvoiceTotals() {
    let subtotalHT = 0;
    let totalTax = 0;

    for (const [index, line] of lines.entries()) {
      const { totalHT, totalTTC } = calculateLineTotals(line, index);
      subtotalHT += totalHT;
      totalTax += (totalTTC - totalHT);
    }

    const totalTTC = subtotalHT + totalTax;

    return { subtotalHT, totalTax, totalTTC };
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();

    if (!contactId) {
      addNotification({ type: 'warning', title: 'Champ requis', message: 'Sélectionne un contact' });
      return;
    }

    if (lines.length === 0) {
      addNotification({ type: 'warning', title: 'Champ requis', message: 'Ajoute au moins une ligne de facturation' });
      return;
    }

    // BUG-132 : une ligne par défaut existe mais sans description -> ne pas
    // afficher « ajoute une ligne » (trompeur), viser le vrai champ manquant.
    // Chaque ligne vide est marquée ; la notification ne part que si toutes
    // le sont (état maquette `nouveau` : ligne remplie + ligne vide).
    const vides = lines
      .map((line, index) => (line.description.trim() ? -1 : index))
      .filter((index) => index >= 0);
    if (vides.length > 0) {
      setLignesSansDescription(vides);
      if (vides.length === lines.length) {
        addNotification({
          type: 'warning',
          title: 'Champ requis',
          message: 'Renseigne la description d’au moins une ligne',
        });
      }
      document.getElementById(`invoiceform-description-${vides[0]}`)?.focus();
      return;
    }
    setLignesSansDescription([]);

    const normalizedLines = lines.map((line, index) => {
      const quantity = parseDecimalDraft(lineInputs[index]?.quantity ?? '');
      const unitPrice = parseDecimalDraft(lineInputs[index]?.unit_price_ht ?? '');
      return {
        ...line,
        quantity,
        unit_price_ht: unitPrice,
      };
    });

    if (normalizedLines.some((line) => line.quantity === null || line.unit_price_ht === null)) {
      addNotification({ type: 'warning', title: 'Valeur invalide', message: 'Saisis des nombres valides pour les quantités et montants' });
      return;
    }

    if (normalizedLines.some((line) => line.quantity! < 1 || line.unit_price_ht! < 0)) {
      addNotification({ type: 'warning', title: 'Valeur invalide', message: 'Saisis une quantité supérieure ou égale à 1 et un prix positif ou nul' });
      return;
    }

    // À ce stade, null est exclu par les guards ci-dessus
    const validLines = normalizedLines.map((line) => ({
      ...line,
      quantity: line.quantity as number,
      unit_price_ht: line.unit_price_ht as number,
    }));

    const data = {
      contact_id: contactId,
      document_type: documentType,
      currency,
      issue_date: issueDate,
      due_date: dueDate,
      lines: validLines,
      notes: notes || undefined,
      status: status !== 'draft' ? status : undefined,
      validite_jours: documentType === 'devis' ? validiteJours : undefined,
    };

    const persistInvoice = async () => {
      setIsSaving(true);

      try {
        let savedInvoice: Invoice;

        if (invoice) {
          // Mise a jour
          savedInvoice = await updateInvoice(invoice.id, data);
          addNotification({ type: 'success', title: 'Facture mise à jour', message: savedInvoice.invoice_number });
        } else {
          // Creation
          savedInvoice = await createInvoice(data);
          addNotification({ type: 'success', title: 'Facture créée', message: savedInvoice.invoice_number });
        }

        onSave(savedInvoice);
      } catch (error) {
        console.error('Failed to save invoice:', error);
        const msg = error instanceof Error ? error.message : 'Erreur lors de la sauvegarde';
        addNotification({ type: 'error', title: 'Erreur', message: msg });
      } finally {
        setIsSaving(false);
      }
    };

    const sensitiveStatusChange = invoice
      && invoice.status !== status
      && (status === 'paid' || status === 'accepted' || status === 'refused');
    if (sensitiveStatusChange) {
      const statusLabel = status === 'paid' ? 'Payée' : status === 'accepted' ? 'Accepté' : 'Refusé';
      requestExternalAction({
        title: `Confirmer le passage au statut « ${statusLabel} »`,
        description: 'La mise à jour du document ne sera enregistrée qu’après ta confirmation.',
        confirmLabel: 'Confirmer le changement de statut',
        details: [
          { label: 'Document', value: invoice.invoice_number },
          { label: 'Statut actuel', value: invoice.status },
          { label: 'Nouveau statut', value: statusLabel },
          { label: 'Montant TTC', value: montantAvecDevise(totalTTC, currency) },
        ],
      }, persistInvoice);
      return;
    }

    await persistInvoice();
  }

  function handleMarkPaid() {
    if (!invoice) return;

    requestExternalAction({
      title: 'Confirmer le paiement de la facture',
      description: 'Cette action changera le statut de la facture et enregistrera sa date de paiement.',
      confirmLabel: 'Confirmer le paiement',
      details: [
        { label: 'Facture', value: invoice.invoice_number },
        { label: 'Montant TTC', value: montantAvecDevise(invoice.total_ttc, invoice.currency) },
        { label: 'Nouveau statut', value: 'Payée' },
      ],
    }, async () => {
      try {
        const updatedInvoice = await markInvoicePaid(invoice.id);
        addNotification({ type: 'success', title: 'Facture payée', message: `${invoice.invoice_number} marquée comme payée` });
        onSave(updatedInvoice);
      } catch (error) {
        console.error('Failed to mark paid:', error);
        addNotification({ type: 'error', title: 'Erreur', message: 'Impossible de marquer comme payée' });
      }
    });
  }

  function handleDevisStatus(nextStatus: 'accepted' | 'refused') {
    if (!invoice) return;

    const accepted = nextStatus === 'accepted';
    requestExternalAction({
      title: accepted ? 'Confirmer l’acceptation du devis' : 'Confirmer le refus du devis',
      description: `Cette action changera le statut du devis en « ${accepted ? 'Accepté' : 'Refusé'} ».`,
      confirmLabel: accepted ? 'Confirmer l’acceptation' : 'Confirmer le refus',
      details: [
        { label: 'Devis', value: invoice.invoice_number },
        { label: 'Montant TTC', value: montantAvecDevise(invoice.total_ttc, invoice.currency) },
        { label: 'Nouveau statut', value: accepted ? 'Accepté' : 'Refusé' },
      ],
    }, async () => {
      try {
        const updated = await updateDevisStatus(invoice.id, nextStatus);
        addNotification({
          type: 'success',
          title: accepted ? 'Devis accepté' : 'Devis refusé',
          message: invoice.invoice_number,
        });
        onSave(updated);
      } catch (err) {
        addNotification({ type: 'error', title: 'Erreur', message: String(err) });
      }
    });
  }

  async function handleConvertToInvoice() {
    if (!invoice) return;
    setIsConverting(true);
    setShowConvertDialog(false);

    try {
      const newInvoice = await convertDevisToInvoice(invoice.id, {
        payment_terms: '30 jours',
        payment_method: 'Virement bancaire',
      });
      addNotification({
        type: 'success',
        title: 'Devis converti en facture',
        message: `Facture ${newInvoice.invoice_number} créée à partir du devis ${invoice.invoice_number}`,
      });
      onSave(newInvoice);
    } catch (error) {
      console.error('Failed to convert devis:', error);
      const msg = error instanceof Error ? error.message : 'Erreur lors de la conversion';
      addNotification({ type: 'error', title: 'Conversion échouée', message: msg });
    } finally {
      setIsConverting(false);
    }
  }

  // Peut-on convertir ce devis ?
  const canConvert = invoice
    && invoice.document_type === 'devis'
    && invoice.status !== 'converted'
    && invoice.status !== 'cancelled';

  const { subtotalHT, totalTax, totalTTC } = calculateInvoiceTotals();

  const nomContact = (contact: Contact) =>
    [contact.first_name, contact.last_name].filter(Boolean).join(' ')
    || contact.company
    || contact.email
    || contact.id;

  const titreFormulaire = invoice
    ? `Modifier ${invoice.invoice_number}`
    : documentType === 'devis'
      ? 'Nouveau devis'
      : documentType === 'avoir'
        ? 'Nouvel avoir'
        : 'Nouvelle facture';

  const bandeauProfil = 'flex items-start gap-3 p-3 rounded-md bg-[var(--color-warning-tint)] border border-warning/30 text-warning';

  return (
    <div
      className={`fixed inset-0 ${Z_LAYER.MODAL_NESTED} flex items-center justify-center`}
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 bg-black/60"
      />

      <motion.div
        role="dialog"
        aria-modal="true"
        aria-label={invoice ? `Modifier ${invoice.invoice_number}` : 'Nouvelle facture'}
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        transition={{ duration: 0.2 }}
        className={cn(
          'relative w-full max-w-4xl max-h-[90vh] mx-4',
          'bg-surface border border-border rounded-md shadow-sm',
          'overflow-hidden flex flex-col',
        )}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h2 className="font-editorial text-lg font-semibold text-text">{titreFormulaire}</h2>
          <Button variant="ghost" size="icon" type="button" aria-label="Fermer" onClick={onClose}>
            <X className="h-[18px] w-[18px]" />
          </Button>
        </div>

        {/* B-011 : la barre d'actions vit HORS du bloc défilant, à dessein. Le
            bouton d'envoi était donc orphelin (`.form === null`) : Entrée ne
            soumettait rien, les six champs `required` n'étaient jamais évalués
            et `onSubmit` était du code mort. L'attribut `form` rattache le
            bouton sans rien déplacer à l'écran. */}
        <form id={ID_FORMULAIRE} onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
          {billingMissing && billingMissing.length > 0 && (
            <div className={bandeauProfil}>
              <AlertTriangle className="h-[18px] w-[18px] shrink-0 mt-0.5" />
              <p className="text-sm">
                Infos de ta société incomplètes ({billingMissing.join(', ')}). Une facture sans ces
                informations n'est pas conforme. Complète-les dans Réglages &gt; Profil avant de
                générer le PDF.
              </p>
            </div>
          )}

          {statutLectureProfil === 'illisible' && (
            <div role="alert" className={bandeauProfil}>
              <AlertTriangle className="h-[18px] w-[18px] shrink-0 mt-0.5" />
              <p className="text-sm">
                Impossible de vérifier les infos de ta société pour le moment. Elles ne sont
                peut-être pas complètes : ouvre Réglages &gt; Profil avant de générer le PDF.
              </p>
            </div>
          )}

          {!invoice && (
            <div className="space-y-1.5">
              {/* `Segments` n'expose son `label` qu'en `aria-label` : sans ce
                  <span>, Devis / Facture / Avoir restaient le seul champ du
                  formulaire sans intitulé lisible. Motif du § 2 du design. */}
              <span className="block text-sm font-semibold text-text">Type de document</span>
              <Segments
                label="Type de document"
                valeur={documentType}
                options={OPTIONS_TYPE_DOCUMENT}
                onChange={(id) => setDocumentType(id as 'devis' | 'facture' | 'avoir')}
              />
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <FormField label="Client *" htmlFor="contact">
                <Select
                  id="contact"
                  value={contactId}
                  onChange={(e) => setContactId(e.target.value)}
                  required
                  options={[
                    { value: '', label: 'Sélectionner un contact' },
                    ...contacts.map((contact) => ({ value: contact.id, label: nomContact(contact) })),
                  ]}
                />
              </FormField>
              {contactsTronques && (
                <p role="alert" className="mt-1 text-sm text-warning">
                  Liste incomplète : seuls les {PLAFOND_CONTACTS} contacts les plus récents
                  sont proposés.
                </p>
              )}
            </div>

            <FormField label="Statut" htmlFor="status">
              <Select
                id="status"
                value={status}
                onChange={(e) => setStatus(e.target.value as typeof status)}
                options={documentType === 'devis' ? OPTIONS_STATUT_DEVIS : OPTIONS_STATUT_FACTURE}
              />
            </FormField>

            <FormField label="Devise" htmlFor="currency">
              <Select
                id="currency"
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                options={CURRENCIES}
              />
            </FormField>

            <FormField label="Date d'émission *" htmlFor="issueDate">
              <Input
                type="date"
                id="issueDate"
                value={issueDate}
                onChange={(e) => setIssueDate(e.target.value)}
                required
              />
            </FormField>

            <FormField label="Date d'échéance *" htmlFor="dueDate">
              <Input
                type="date"
                id="dueDate"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                required
              />
            </FormField>

            {documentType === 'devis' && (
              <FormField label="Validité (jours)" htmlFor="validiteJours">
                <Input
                  type="number"
                  id="validiteJours"
                  min={1}
                  max={365}
                  value={validiteJours}
                  onChange={(e) => setValiditeJours(parseInt(e.target.value, 10) || 30)}
                />
              </FormField>
            )}
          </div>

          <div>
            <p className="text-sm font-medium text-text mb-3">Lignes de facturation *</p>
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className="text-left text-xs font-semibold text-text-muted px-4 py-2 border-b border-border tracking-wide">Description</th>
                  <th className="text-left text-xs font-semibold text-text-muted px-4 py-2 border-b border-border tracking-wide">Quantité</th>
                  <th className="text-left text-xs font-semibold text-text-muted px-4 py-2 border-b border-border tracking-wide">Prix HT</th>
                  <th className="text-left text-xs font-semibold text-text-muted px-4 py-2 border-b border-border tracking-wide">TVA</th>
                  <th className="text-left text-xs font-semibold text-text-muted px-4 py-2 border-b border-border tracking-wide">Total HT</th>
                  <th className="sr-only">Actions</th>
                </tr>
              </thead>
              <tbody>
                {lines.map((line, index) => {
                  const { totalHT } = calculateLineTotals(line, index);
                  const erreurDescription = lignesSansDescription.includes(index);
                  return (
                    <tr key={index}>
                      <td className="px-4 py-2.5 border-b border-border align-middle">
                        <Input
                          id={`invoiceform-description-${index}`}
                          aria-label={`Description ligne ${index + 1}`}
                          placeholder="Description"
                          value={line.description}
                          onChange={(e) => {
                            const valeur = e.target.value;
                            updateLine(index, 'description', valeur);
                            if (valeur.trim()) {
                              setLignesSansDescription((prev) => prev.filter((i) => i !== index));
                            }
                          }}
                          error={erreurDescription}
                          aria-describedby={erreurDescription ? `invoiceform-description-${index}-erreur` : undefined}
                        />
                        {erreurDescription && (
                          <p
                            id={`invoiceform-description-${index}-erreur`}
                            role="alert"
                            className="mt-1 font-medium text-error text-sm"
                          >
                            Renseigne la description de cette ligne, ou supprime-la.
                          </p>
                        )}
                      </td>
                      <td className="px-4 py-2.5 border-b border-border align-middle">
                        <Input
                          id={`invoiceform-quantite-${index}`}
                          aria-label={`Quantité ligne ${index + 1}`}
                          type="text"
                          inputMode="decimal"
                          value={lineInputs[index]?.quantity ?? formatDecimalInput(line.quantity)}
                          onChange={(e) => updateDecimalLineInput(index, 'quantity', e.target.value)}
                          required
                        />
                      </td>
                      <td className="px-4 py-2.5 border-b border-border align-middle">
                        <Input
                          id={`invoiceform-prix-${index}`}
                          aria-label={`Prix HT ligne ${index + 1}`}
                          type="text"
                          inputMode="decimal"
                          value={lineInputs[index]?.unit_price_ht ?? formatDecimalInput(line.unit_price_ht)}
                          onChange={(e) => updateDecimalLineInput(index, 'unit_price_ht', e.target.value)}
                          required
                        />
                      </td>
                      <td className="px-4 py-2.5 border-b border-border align-middle">
                        <Select
                          id={`invoiceform-tva-${index}`}
                          aria-label={`TVA ligne ${index + 1}`}
                          options={TVA_RATES.map((r) => ({ value: String(r.value), label: r.label }))}
                          value={String(line.tva_rate)}
                          onChange={(e) => updateLine(index, 'tva_rate', parseFloat(e.target.value))}
                        />
                      </td>
                      <td className="px-4 py-2.5 border-b border-border align-middle tabular-nums whitespace-nowrap">
                        {montantAvecDevise(totalHT, currency)}
                      </td>
                      <td className="px-4 py-2.5 border-b border-border align-middle">
                        <Button
                          variant="ghost"
                          size="icon"
                          type="button"
                          aria-label={`Supprimer la ligne ${index + 1}`}
                          onClick={() => removeLine(index)}
                        >
                          <Trash2 className="h-[18px] w-[18px]" />
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <div className="mt-2">
              <Button variant="ghost" size="md" type="button" onClick={addLine}>
                <Plus className="h-[18px] w-[18px]" />
                Ajouter une ligne
              </Button>
            </div>
          </div>

          <FormField label="Notes" htmlFor="notes">
            <Textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              placeholder="Notes internes ou mentions spécifiques..."
            />
          </FormField>

          {invoice?.payment_terms && (
            <div className="p-4 rounded-md bg-surface-2 border border-border space-y-2">
              <h3 className="text-sm font-medium text-text mb-2">Conditions de paiement</h3>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-text-muted">Delai :</span>{' '}
                  <span className="text-text">{invoice.payment_terms}</span>
                </div>
                <div>
                  <span className="text-text-muted">Mode :</span>{' '}
                  <span className="text-text">{invoice.payment_method}</span>
                </div>
                {invoice.late_penalty_rate && (
                  <div>
                    <span className="text-text-muted">Penalites de retard :</span>{' '}
                    <span className="text-text">{invoice.late_penalty_rate}% annuel</span>
                  </div>
                )}
              </div>
              {invoice.legal_mentions && (
                <div className="mt-2 pt-2 border-t border-border">
                  <p className="text-sm text-text-muted whitespace-pre-line">{invoice.legal_mentions}</p>
                </div>
              )}
            </div>
          )}

          <div className="grid grid-cols-[1fr_auto] justify-end gap-x-6 gap-y-1 tabular-nums">
            <span className="text-text-muted">Total HT</span>
            <span className="font-medium text-text">{montantAvecDevise(subtotalHT, currency)}</span>
            <span className="text-text-muted">Total TVA</span>
            <span className="font-medium text-text">{montantAvecDevise(totalTax, currency)}</span>
            <span className="font-semibold text-lg">Total TTC</span>
            <span className="font-semibold text-lg">{montantAvecDevise(totalTTC, currency)}</span>
          </div>
        </form>

        <div className="px-6 py-4 border-t border-border flex items-center justify-between">
          <div className="flex flex-wrap items-center gap-2">
            {invoice && invoice.document_type !== 'devis' && invoice.status !== 'paid' && invoice.status !== 'cancelled' && invoice.status !== 'converted' && (
              <Button variant="secondary" size="md" type="button" onClick={handleMarkPaid}>
                Marquer comme payée
              </Button>
            )}

            {invoice && invoice.document_type === 'devis' && invoice.status !== 'accepted' && invoice.status !== 'refused' && invoice.status !== 'converted' && invoice.status !== 'cancelled' && invoice.status !== 'expired' && (
              <div className="flex items-center gap-2">
                <Button variant="secondary" size="md" type="button" onClick={() => handleDevisStatus('accepted')}>
                  Accepter
                </Button>
                <Button variant="secondary" size="md" type="button" onClick={() => handleDevisStatus('refused')}>
                  Refuser
                </Button>
              </div>
            )}

            {canConvert && (
              <Button
                variant="secondary"
                size="md"
                type="button"
                onClick={() => setShowConvertDialog(true)}
                disabled={isConverting}
              >
                <FileCheck className="h-[18px] w-[18px]" />
                {isConverting ? 'Conversion...' : 'Convertir en facture'}
              </Button>
            )}
          </div>

          <div className="flex items-center gap-3">
            <Button variant="secondary" size="md" type="button" onClick={onClose}>
              Annuler
            </Button>
            <Button variant="primary" size="md" type="submit" form={ID_FORMULAIRE} disabled={isSaving}>
              <Save className="h-[18px] w-[18px]" />
              {isSaving ? 'Sauvegarde...' : invoice ? 'Mettre à jour' : 'Créer'}
            </Button>
          </div>
        </div>

        {showConvertDialog && (
          <div
            className="absolute inset-0 z-10 flex items-center justify-center"
            onClick={() => setShowConvertDialog(false)}
          >
            <div className="absolute inset-0 bg-black/60 rounded-md" />
            <div
              role="dialog"
              aria-modal="true"
              aria-label="Confirmer la conversion"
              className="relative w-full max-w-md mx-4 p-6 bg-surface border border-border rounded-md shadow-sm space-y-4"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-text">Convertir en facture ?</h3>
              <p className="text-sm text-text-muted">
                Une facture sera créée à partir du devis <strong>{invoice?.invoice_number}</strong> avec
                les mêmes lignes et montants. Le devis sera marqué comme converti.
              </p>
              <div className="p-3 rounded-md bg-surface-2 border border-border text-sm space-y-1">
                <p className="text-text-muted">
                  <span className="font-medium text-text">Conditions :</span> 30 jours, virement bancaire
                </p>
                <p className="text-text-muted">
                  <span className="font-medium text-text">Mentions legales :</span> ajoutees automatiquement
                </p>
              </div>
              <div className="flex items-center justify-end gap-3">
                <Button variant="secondary" size="md" type="button" onClick={() => setShowConvertDialog(false)}>
                  Annuler
                </Button>
                <Button variant="primary" size="md" type="button" onClick={handleConvertToInvoice}>
                  <FileCheck className="h-[18px] w-[18px]" />
                  Convertir
                </Button>
              </div>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
}
