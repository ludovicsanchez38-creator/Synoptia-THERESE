/**
 * THÉRÈSE v2 - Invoice Form
 *
 * Formulaire de création/édition de facture.
 * Phase 4 - Invoicing
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { X, Plus, Trash2, Save } from 'lucide-react';
import { createInvoice, updateInvoice, type Invoice, type InvoiceLineRequest, listContacts, type Contact, markInvoicePaid } from '../../services/api';
import { cn } from '../../lib/utils';

interface InvoiceFormProps {
  invoice: Invoice | null;
  onClose: () => void;
  onSave: (invoice: Invoice) => void;
}

const TVA_RATES = [
  { value: 20.0, label: '20% (normale)' },
  { value: 10.0, label: '10% (intermédiaire)' },
  { value: 5.5, label: '5,5% (réduite)' },
  { value: 2.1, label: '2,1% (super réduite)' },
  { value: 0.0, label: '0% (exonéré)' },
];

export function InvoiceForm({ invoice, onClose, onSave }: InvoiceFormProps) {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [contactId, setContactId] = useState(invoice?.contact_id || '');
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

  const [isSaving, setIsSaving] = useState(false);

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
  }

  function removeLine(index: number) {
    setLines(lines.filter((_, i) => i !== index));
  }

  function updateLine(index: number, field: keyof InvoiceLineRequest, value: any) {
    const newLines = [...lines];
    newLines[index] = { ...newLines[index], [field]: value };
    setLines(newLines);
  }

  function calculateLineTotals(line: InvoiceLineRequest) {
    const totalHT = line.quantity * line.unit_price_ht;
    const totalTTC = totalHT * (1 + line.tva_rate / 100);
    return { totalHT, totalTTC };
  }

  function calculateInvoiceTotals() {
    let subtotalHT = 0;
    let totalTax = 0;

    for (const line of lines) {
      const { totalHT, totalTTC } = calculateLineTotals(line);
      subtotalHT += totalHT;
      totalTax += (totalTTC - totalHT);
    }

    const totalTTC = subtotalHT + totalTax;

    return { subtotalHT, totalTax, totalTTC };
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!contactId) {
      alert('Veuillez sélectionner un contact');
      return;
    }

    if (lines.length === 0 || lines.every((line) => !line.description)) {
      alert('Veuillez ajouter au moins une ligne de facturation');
      return;
    }

    setIsSaving(true);

    try {
      const data = {
        contact_id: contactId,
        issue_date: issueDate,
        due_date: dueDate,
        lines,
        notes: notes || undefined,
        status: status !== 'draft' ? status : undefined,
      };

      let savedInvoice: Invoice;

      if (invoice) {
        // Mise à jour
        savedInvoice = await updateInvoice(invoice.id, data);
      } else {
        // Création
        savedInvoice = await createInvoice(data);
      }

      onSave(savedInvoice);
    } catch (error) {
      console.error('Failed to save invoice:', error);
      alert('Erreur lors de la sauvegarde');
    } finally {
      setIsSaving(false);
    }
  }

  async function handleMarkPaid() {
    if (!invoice) return;

    if (!confirm('Marquer cette facture comme payée ?')) {
      return;
    }

    try {
      const updatedInvoice = await markInvoicePaid(invoice.id);
      onSave(updatedInvoice);
    } catch (error) {
      console.error('Failed to mark paid:', error);
      alert('Erreur lors de la mise à jour');
    }
  }

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
            {invoice ? `Modifier ${invoice.invoice_number}` : 'Nouvelle facture'}
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
                <option value="">Sélectionner un contact</option>
                {contacts.map((contact) => (
                  <option key={contact.id} value={contact.id}>
                    {contact.display_name}
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
                onChange={(e) => setStatus(e.target.value)}
                className={cn(
                  'w-full px-3 py-2 rounded-lg',
                  'bg-bg border border-border/50',
                  'text-text',
                  'focus:outline-none focus:ring-2 focus:ring-accent-cyan'
                )}
              >
                <option value="draft">Brouillon</option>
                <option value="sent">Envoyée</option>
                <option value="paid">Payée</option>
                <option value="overdue">En retard</option>
                <option value="cancelled">Annulée</option>
              </select>
            </div>

            <div>
              <label htmlFor="issueDate" className="block text-sm font-medium text-text mb-2">
                Date d'émission *
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
                Date d'échéance *
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
                const { totalHT, totalTTC } = calculateLineTotals(line);

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
                        <label className="block text-xs text-text-muted mb-1">Quantité</label>
                        <input
                          type="number"
                          min="1"
                          step="0.01"
                          value={line.quantity}
                          onChange={(e) => updateLine(index, 'quantity', parseFloat(e.target.value))}
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
                        <label className="block text-xs text-text-muted mb-1">Prix HT (€)</label>
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={line.unit_price_ht}
                          onChange={(e) => updateLine(index, 'unit_price_ht', parseFloat(e.target.value))}
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
                          {totalHT.toFixed(2)} €
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
              placeholder="Notes internes ou mentions spécifiques..."
            />
          </div>

          {/* Totals */}
          <div className="p-4 rounded-lg bg-surface-elevated/50 border border-border/50 space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-text-muted">Total HT</span>
              <span className="font-medium text-text">{subtotalHT.toFixed(2)} €</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-text-muted">Total TVA</span>
              <span className="font-medium text-text">{totalTax.toFixed(2)} €</span>
            </div>
            <div className="h-px bg-border/50" />
            <div className="flex items-center justify-between">
              <span className="font-semibold text-text">Total TTC</span>
              <span className="text-2xl font-bold text-accent-cyan">{totalTTC.toFixed(2)} €</span>
            </div>
          </div>
        </form>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-border/50 flex items-center justify-between">
          <div>
            {invoice && invoice.status !== 'paid' && invoice.status !== 'cancelled' && (
              <button
                type="button"
                onClick={handleMarkPaid}
                className="px-4 py-2 rounded-lg bg-green-500/20 text-green-500 hover:bg-green-500/30 transition-colors"
              >
                Marquer comme payée
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
              {isSaving ? 'Sauvegarde...' : invoice ? 'Mettre à jour' : 'Créer'}
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
