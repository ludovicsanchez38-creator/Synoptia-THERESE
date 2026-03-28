/**
 * THERESE v2 - Invoice Form
 *
 * Formulaire de creation/edition de facture.
 * Phase 4 - Invoicing
 * US-018 : Conversion devis -> facture + conditions de paiement
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { X, Plus, Trash2, Save, FileCheck } from 'lucide-react';
import { createInvoice, updateInvoice, convertDevisToInvoice, type Invoice, type InvoiceLineRequest, listContacts, type Contact, markInvoicePaid } from '../../services/api';
import { useStatusStore } from '../../stores/statusStore';
import { cn } from '../../lib/utils';

interface InvoiceFormProps {
  invoice: Invoice | null;
  onClose: () => void;
  onSave: (invoice: Invoice) => void;
}

interface InvoiceLineInputState {
  quantity: string;
  unit_price_ht: string;
}

const TVA_RATES = [
  { value: 20.0, label: '20% (normale)' },
  { value: 10.0, label: '10% (intermediaire)' },
  { value: 5.5, label: '5,5% (reduite)' },
  { value: 2.1, label: '2,1% (super reduite)' },
  { value: 0.0, label: '0% (exonere)' },
];

const CURRENCIES = [
  { value: 'EUR', label: 'EUR (\u20ac)' },
  { value: 'CHF', label: 'CHF' },
  { value: 'USD', label: 'USD ($)' },
  { value: 'GBP', label: 'GBP (\u00a3)' },
];

const CURRENCY_SYMBOLS: Record<string, string> = {
  EUR: '\u20ac',
  CHF: 'CHF',
  USD: '$',
  GBP: '\u00a3',
};

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

export function InvoiceForm({ invoice, onClose, onSave }: InvoiceFormProps) {
  const addNotification = useStatusStore((s) => s.addNotification);

  const [contacts, setContacts] = useState<Contact[]>([]);
  const [documentType, setDocumentType] = useState<'devis' | 'facture' | 'avoir'>(
    (invoice?.document_type as 'devis' | 'facture' | 'avoir') || 'facture'
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

  // Charger les contacts
  useEffect(() => {
    loadContacts();
  }, []);

  async function loadContacts() {
    try {
      const data = await listContacts();
      setContacts(data);
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

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!contactId) {
      addNotification({ type: 'warning', title: 'Champ requis', message: 'Veuillez selectionner un contact' });
      return;
    }

    if (lines.length === 0 || lines.every((line) => !line.description)) {
      addNotification({ type: 'warning', title: 'Champ requis', message: 'Veuillez ajouter au moins une ligne de facturation' });
      return;
    }

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
      alert('Veuillez saisir des nombres valides pour les quantités et montants');
      return;
    }

    if (normalizedLines.some((line) => line.quantity < 1 || line.unit_price_ht < 0)) {
      alert('Veuillez saisir une quantité supérieure ou égale à 1 et un prix positif ou nul');
      return;
    }

    setIsSaving(true);

    try {
      const data = {
        contact_id: contactId,
        document_type: documentType,
        currency,
        issue_date: issueDate,
        due_date: dueDate,
        lines: normalizedLines,
        notes: notes || undefined,
        status: status !== 'draft' ? status : undefined,
      };

      let savedInvoice: Invoice;

      if (invoice) {
        // Mise a jour
        savedInvoice = await updateInvoice(invoice.id, data);
        addNotification({ type: 'success', title: 'Facture mise a jour', message: savedInvoice.invoice_number });
      } else {
        // Creation
        savedInvoice = await createInvoice(data);
        addNotification({ type: 'success', title: 'Facture creee', message: savedInvoice.invoice_number });
      }

      onSave(savedInvoice);
    } catch (error) {
      console.error('Failed to save invoice:', error);
      const msg = error instanceof Error ? error.message : 'Erreur lors de la sauvegarde';
      addNotification({ type: 'error', title: 'Erreur', message: msg });
    } finally {
      setIsSaving(false);
    }
  }

  async function handleMarkPaid() {
    if (!invoice) return;
    try {
      const updatedInvoice = await markInvoicePaid(invoice.id);
      addNotification({ type: 'success', title: 'Facture payee', message: `${invoice.invoice_number} marquee comme payee` });
      onSave(updatedInvoice);
    } catch (error) {
      console.error('Failed to mark paid:', error);
      addNotification({ type: 'error', title: 'Erreur', message: 'Impossible de marquer comme payee' });
    }
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
        message: `Facture ${newInvoice.invoice_number} creee a partir du devis ${invoice.invoice_number}`,
      });
      onSave(newInvoice);
    } catch (error) {
      console.error('Failed to convert devis:', error);
      const msg = error instanceof Error ? error.message : 'Erreur lors de la conversion';
      addNotification({ type: 'error', title: 'Conversion echouee', message: msg });
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

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center"
      onClick={onClose}
    >
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
      />

      {/* Modal */}
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
          'bg-surface/95 backdrop-blur-xl border border-border/50 rounded-xl',
          'shadow-2xl overflow-hidden flex flex-col'
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border/50">
          <h2 className="text-lg font-semibold text-text">
            {invoice ? `Modifier ${invoice.invoice_number}` : `${documentType === 'devis' ? 'Nouveau devis' : documentType === 'avoir' ? 'Nouvel avoir' : 'Nouvelle facture'}`}
          </h2>

          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-surface-elevated transition-colors"
          >
            <X className="w-5 h-5 text-text-muted" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Type de document */}
          {!invoice && (
            <div>
              <label className="block text-sm font-medium text-text mb-2">Type de document</label>
              <div className="flex gap-2">
                {([['devis', 'Devis'], ['facture', 'Facture'], ['avoir', 'Avoir']] as const).map(([type, label]) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => setDocumentType(type)}
                    className={cn(
                      'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                      documentType === type
                        ? 'bg-accent-cyan/20 text-accent-cyan border border-accent-cyan/50'
                        : 'bg-surface border border-border/50 text-text-muted hover:bg-surface-elevated'
                    )}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Contact & Dates */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="contact" className="block text-sm font-medium text-text mb-2">
                Client *
              </label>
              <select
                id="contact"
                value={contactId}
                onChange={(e) => setContactId(e.target.value)}
                className={cn(
                  'w-full px-3 py-2 rounded-lg',
                  'bg-bg border border-border/50',
                  'text-text placeholder:text-text-muted/70',
                  'focus:outline-none focus:ring-2 focus:ring-accent-cyan'
                )}
                required
              >
                <option value="">Selectionner un contact</option>
                {contacts.map((contact) => (
                  <option key={contact.id} value={contact.id}>
                    {[contact.first_name, contact.last_name].filter(Boolean).join(' ') || contact.company || contact.email || contact.id}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="status" className="block text-sm font-medium text-text mb-2">
                Statut
              </label>
              <select
                id="status"
                value={status}
                onChange={(e) => setStatus(e.target.value as typeof status)}
                className={cn(
                  'w-full px-3 py-2 rounded-lg',
                  'bg-bg border border-border/50',
                  'text-text',
                  'focus:outline-none focus:ring-2 focus:ring-accent-cyan'
                )}
              >
                <option value="draft">Brouillon</option>
                <option value="sent">Envoyee</option>
                <option value="accepted">Accepte</option>
                <option value="paid">Payee</option>
                <option value="overdue">En retard</option>
                <option value="cancelled">Annulee</option>
              </select>
            </div>

            <div>
              <label htmlFor="currency" className="block text-sm font-medium text-text mb-2">
                Devise
              </label>
              <select
                id="currency"
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className={cn(
                  'w-full px-3 py-2 rounded-lg',
                  'bg-bg border border-border/50',
                  'text-text',
                  'focus:outline-none focus:ring-2 focus:ring-accent-cyan'
                )}
              >
                {CURRENCIES.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="issueDate" className="block text-sm font-medium text-text mb-2">
                Date d'emission *
              </label>
              <input
                type="date"
                id="issueDate"
                value={issueDate}
                onChange={(e) => setIssueDate(e.target.value)}
                className={cn(
                  'w-full px-3 py-2 rounded-lg',
                  'bg-bg border border-border/50',
                  'text-text',
                  'focus:outline-none focus:ring-2 focus:ring-accent-cyan'
                )}
                required
              />
            </div>

            <div>
              <label htmlFor="dueDate" className="block text-sm font-medium text-text mb-2">
                Date d'echeance *
              </label>
              <input
                type="date"
                id="dueDate"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className={cn(
                  'w-full px-3 py-2 rounded-lg',
                  'bg-bg border border-border/50',
                  'text-text',
                  'focus:outline-none focus:ring-2 focus:ring-accent-cyan'
                )}
                required
              />
            </div>
          </div>

          {/* Lines */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="block text-sm font-medium text-text">
                Lignes de facturation *
              </label>
              <button
                type="button"
                onClick={addLine}
                className="px-3 py-1 rounded-lg bg-accent-cyan/20 text-accent-cyan hover:bg-accent-cyan/30 transition-colors flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Ajouter une ligne
              </button>
            </div>

            <div className="space-y-2">
              {lines.map((line, index) => {
                const { totalHT } = calculateLineTotals(line, index);

                return (
                  <div key={index} className="p-4 rounded-lg bg-bg border border-border/50 space-y-3">
                    <div className="flex items-start gap-3">
                      <div className="flex-1">
                        <input
                          type="text"
                          placeholder="Description"
                          value={line.description}
                          onChange={(e) => updateLine(index, 'description', e.target.value)}
                          className={cn(
                            'w-full px-3 py-2 rounded-lg',
                            'bg-surface border border-border/50',
                            'text-text placeholder:text-text-muted/70',
                            'focus:outline-none focus:ring-2 focus:ring-accent-cyan'
                          )}
                          required
                        />
                      </div>

                      <button
                        type="button"
                        onClick={() => removeLine(index)}
                        className="p-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 transition-colors"
                      >
                        <Trash2 className="w-4 h-4 text-red-500" />
                      </button>
                    </div>

                    <div className="grid grid-cols-4 gap-3">
                      <div>
                        <label className="block text-xs text-text-muted mb-1">Quantite</label>
                        <input
                          aria-label={`Quantité ligne ${index + 1}`}
                          type="text"
                          inputMode="decimal"
                          value={lineInputs[index]?.quantity ?? formatDecimalInput(line.quantity)}
                          onChange={(e) => updateDecimalLineInput(index, 'quantity', e.target.value)}
                          className={cn(
                            'w-full px-3 py-2 rounded-lg',
                            'bg-surface border border-border/50',
                            'text-text',
                            'focus:outline-none focus:ring-2 focus:ring-accent-cyan'
                          )}
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-xs text-text-muted mb-1">Prix HT ({CURRENCY_SYMBOLS[currency] || currency})</label>
                        <input
                          aria-label={`Prix HT ligne ${index + 1}`}
                          type="text"
                          inputMode="decimal"
                          value={lineInputs[index]?.unit_price_ht ?? formatDecimalInput(line.unit_price_ht)}
                          onChange={(e) => updateDecimalLineInput(index, 'unit_price_ht', e.target.value)}
                          className={cn(
                            'w-full px-3 py-2 rounded-lg',
                            'bg-surface border border-border/50',
                            'text-text',
                            'focus:outline-none focus:ring-2 focus:ring-accent-cyan'
                          )}
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-xs text-text-muted mb-1">TVA</label>
                        <select
                          value={line.tva_rate}
                          onChange={(e) => updateLine(index, 'tva_rate', parseFloat(e.target.value))}
                          className={cn(
                            'w-full px-3 py-2 rounded-lg',
                            'bg-surface border border-border/50',
                            'text-text',
                            'focus:outline-none focus:ring-2 focus:ring-accent-cyan'
                          )}
                        >
                          {TVA_RATES.map((rate) => (
                            <option key={rate.value} value={rate.value}>
                              {rate.label}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="block text-xs text-text-muted mb-1">Total HT</label>
                        <div className="px-3 py-2 rounded-lg bg-surface-elevated text-text font-medium">
                          {totalHT.toFixed(2)} {CURRENCY_SYMBOLS[currency] || currency}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Notes */}
          <div>
            <label htmlFor="notes" className="block text-sm font-medium text-text mb-2">
              Notes
            </label>
            <textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              className={cn(
                'w-full px-3 py-2 rounded-lg',
                'bg-bg border border-border/50',
                'text-text placeholder:text-text-muted/70',
                'focus:outline-none focus:ring-2 focus:ring-accent-cyan',
                'resize-none'
              )}
              placeholder="Notes internes ou mentions specifiques..."
            />
          </div>

          {/* Payment info (read-only if present from conversion) */}
          {invoice?.payment_terms && (
            <div className="p-4 rounded-lg bg-surface-elevated/30 border border-border/50 space-y-2">
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
                <div className="mt-2 pt-2 border-t border-border/30">
                  <p className="text-xs text-text-muted whitespace-pre-line">{invoice.legal_mentions}</p>
                </div>
              )}
            </div>
          )}

          {/* Totals */}
          <div className="p-4 rounded-lg bg-surface-elevated/50 border border-border/50 space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-text-muted">Total HT</span>
              <span className="font-medium text-text">{subtotalHT.toFixed(2)} {CURRENCY_SYMBOLS[currency] || currency}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-text-muted">Total TVA</span>
              <span className="font-medium text-text">{totalTax.toFixed(2)} {CURRENCY_SYMBOLS[currency] || currency}</span>
            </div>
            <div className="h-px bg-border/50" />
            <div className="flex items-center justify-between">
              <span className="font-semibold text-text">Total TTC</span>
              <span className="text-2xl font-bold text-accent-cyan">{totalTTC.toFixed(2)} {CURRENCY_SYMBOLS[currency] || currency}</span>
            </div>
          </div>
        </form>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-border/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {invoice && invoice.status !== 'paid' && invoice.status !== 'cancelled' && invoice.status !== 'converted' && (
              <button
                type="button"
                onClick={handleMarkPaid}
                className="px-4 py-2 rounded-lg bg-green-500/20 text-green-500 hover:bg-green-500/30 transition-colors"
              >
                Marquer comme payee
              </button>
            )}

            {/* Bouton Convertir en facture (devis uniquement) */}
            {canConvert && (
              <button
                type="button"
                onClick={() => setShowConvertDialog(true)}
                disabled={isConverting}
                className={cn(
                  'px-4 py-2 rounded-lg font-medium transition-colors',
                  'bg-purple-500/20 text-purple-400 hover:bg-purple-500/30',
                  'flex items-center gap-2',
                  isConverting && 'opacity-50 cursor-not-allowed'
                )}
              >
                <FileCheck className="w-4 h-4" />
                {isConverting ? 'Conversion...' : 'Convertir en facture'}
              </button>
            )}
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-surface-elevated text-text hover:bg-surface-elevated/70 transition-colors"
            >
              Annuler
            </button>
            <button
              type="submit"
              onClick={handleSubmit}
              disabled={isSaving}
              className={cn(
                'px-4 py-2 rounded-lg font-medium transition-colors',
                'bg-accent-cyan text-bg hover:bg-accent-cyan/90',
                'flex items-center gap-2',
                isSaving && 'opacity-50 cursor-not-allowed'
              )}
            >
              <Save className="w-4 h-4" />
              {isSaving ? 'Sauvegarde...' : invoice ? 'Mettre a jour' : 'Creer'}
            </button>
          </div>
        </div>

        {/* Confirm convert dialog */}
        {showConvertDialog && (
          <div
            className="absolute inset-0 z-10 flex items-center justify-center"
            onClick={() => setShowConvertDialog(false)}
          >
            <div className="absolute inset-0 bg-black/50 backdrop-blur-sm rounded-xl" />
            <div
              role="dialog"
              aria-modal="true"
              aria-label="Confirmer la conversion"
              className={cn(
                'relative w-full max-w-md mx-4 p-6',
                'bg-surface/95 backdrop-blur-xl border border-border/50 rounded-xl',
                'shadow-2xl space-y-4'
              )}
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-text">Convertir en facture ?</h3>
              <p className="text-sm text-text-muted">
                Une facture sera creee a partir du devis <strong>{invoice?.invoice_number}</strong> avec
                les memes lignes et montants. Le devis sera marque comme converti.
              </p>
              <div className="p-3 rounded-lg bg-surface-elevated/50 border border-border/30 text-sm space-y-1">
                <p className="text-text-muted">
                  <span className="font-medium text-text">Conditions :</span> 30 jours, virement bancaire
                </p>
                <p className="text-text-muted">
                  <span className="font-medium text-text">Mentions legales :</span> ajoutees automatiquement
                </p>
              </div>
              <div className="flex items-center justify-end gap-3">
                <button
                  onClick={() => setShowConvertDialog(false)}
                  className="px-4 py-2 rounded-lg bg-surface-elevated text-text hover:bg-surface-elevated/70 transition-colors"
                >
                  Annuler
                </button>
                <button
                  onClick={handleConvertToInvoice}
                  className={cn(
                    'px-4 py-2 rounded-lg font-medium transition-colors',
                    'bg-purple-500 text-white hover:bg-purple-600',
                    'flex items-center gap-2'
                  )}
                >
                  <FileCheck className="w-4 h-4" />
                  Convertir
                </button>
              </div>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
}
