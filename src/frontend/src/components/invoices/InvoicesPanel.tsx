/**
 * THÉRÈSE v2 - Invoices Panel
 *
 * Panel principal pour la gestion de facturation.
 * Phase 4 - Invoicing
 */

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Plus,
  FileText,
  Download,
  Mail,
  CheckCircle2,
  AlertCircle,
  Clock,
  Ban,
  Filter,
} from 'lucide-react';
import { useInvoiceStore } from '../../stores/invoiceStore';
import { listInvoices, deleteInvoice, generateInvoicePDF, sendInvoiceByEmail, type Invoice } from '../../services/api';
import { InvoiceForm } from './InvoiceForm';
import { cn } from '../../lib/utils';

const STATUS_CONFIG = {
  draft: { label: 'Brouillon', icon: FileText, color: 'text-text-muted' },
  sent: { label: 'Envoyée', icon: Mail, color: 'text-blue-500' },
  paid: { label: 'Payée', icon: CheckCircle2, color: 'text-green-500' },
  overdue: { label: 'En retard', icon: AlertCircle, color: 'text-red-500' },
  cancelled: { label: 'Annulée', icon: Ban, color: 'text-text-muted' },
};

interface InvoicesPanelProps {
  standalone?: boolean;
}

export function InvoicesPanel({ standalone = false }: InvoicesPanelProps) {
  const {
    isInvoicePanelOpen,
    setIsInvoicePanelOpen,
    invoices,
    setInvoices,
    getFilteredInvoices,
    filters,
    setFilters,
    setCurrentInvoiceId,
    removeInvoice,
    updateInvoiceInStore,
  } = useInvoiceStore();

  const [isLoading, setIsLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingInvoice, setEditingInvoice] = useState<Invoice | null>(null);

  const effectiveOpen = standalone || isInvoicePanelOpen;

  // Charger les factures au montage
  useEffect(() => {
    if (effectiveOpen) {
      loadInvoices();
    }
  }, [effectiveOpen]);

  async function loadInvoices() {
    setIsLoading(true);
    try {
      const data = await listInvoices();
      setInvoices(data);
    } catch (error) {
      console.error('Failed to load invoices:', error);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleGeneratePDF(invoice: Invoice) {
    try {
      const result = await generateInvoicePDF(invoice.id);
      console.log('PDF generated:', result.pdf_path);
      // TODO: Ouvrir le PDF ou proposer le téléchargement
      alert(`PDF généré: ${result.invoice_number}\nChemin: ${result.pdf_path}`);
    } catch (error) {
      console.error('Failed to generate PDF:', error);
      alert('Erreur lors de la génération du PDF');
    }
  }

  async function handleSendEmail(invoice: Invoice) {
    if (!confirm(`Envoyer la facture ${invoice.invoice_number} par email ?`)) {
      return;
    }

    try {
      const result = await sendInvoiceByEmail(invoice.id);
      console.log('Email sent:', result);

      // Mettre à jour le statut
      if (invoice.status === 'draft') {
        const updatedInvoice = { ...invoice, status: 'sent' as const };
        updateInvoiceInStore(updatedInvoice);
      }

      alert(result.message || 'Email envoyé avec succès');
    } catch (error) {
      console.error('Failed to send email:', error);
      alert('Erreur lors de l\'envoi de l\'email');
    }
  }

  async function handleDeleteInvoice(invoice: Invoice) {
    if (!confirm(`Supprimer la facture ${invoice.invoice_number} ?`)) {
      return;
    }

    try {
      await deleteInvoice(invoice.id);
      removeInvoice(invoice.id);
    } catch (error) {
      console.error('Failed to delete invoice:', error);
      alert('Erreur lors de la suppression');
    }
  }

  function handleCreateNew() {
    setEditingInvoice(null);
    setShowForm(true);
  }

  function handleEdit(invoice: Invoice) {
    setEditingInvoice(invoice);
    setShowForm(true);
  }

  function handleCloseForm() {
    setShowForm(false);
    setEditingInvoice(null);
  }

  function handleInvoiceCreatedOrUpdated(invoice: Invoice) {
    if (editingInvoice) {
      updateInvoiceInStore(invoice);
    } else {
      loadInvoices(); // Recharger pour avoir toutes les données
    }
    handleCloseForm();
  }

  const filteredInvoices = getFilteredInvoices();

  if (!effectiveOpen) return null;

  const invoicesHeader = (
    <div className="flex items-center justify-between px-6 py-4 border-b border-border/50">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-accent-cyan/20 flex items-center justify-center">
          <FileText className="w-5 h-5 text-accent-cyan" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-text">Factures</h2>
          <p className="text-sm text-text-muted">{filteredInvoices.length} facture{filteredInvoices.length > 1 ? 's' : ''}</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={handleCreateNew}
          className={cn(
            'px-4 py-2 rounded-lg',
            'bg-accent-cyan text-bg font-medium',
            'hover:bg-accent-cyan/90 transition-colors',
            'flex items-center gap-2'
          )}
        >
          <Plus className="w-4 h-4" />
          Nouvelle facture
        </button>

        {!standalone && (
          <button
            onClick={() => setIsInvoicePanelOpen(false)}
            className="p-2 rounded-lg hover:bg-surface-elevated transition-colors"
          >
            <X className="w-5 h-5 text-text-muted" />
          </button>
        )}
      </div>
    </div>
  );

  const invoicesFilters = (
    <div className="px-6 py-3 border-b border-border/50 flex items-center gap-2">
      <Filter className="w-4 h-4 text-text-muted" />
      <div className="flex items-center gap-2">
        {(['all', 'draft', 'sent', 'paid', 'overdue', 'cancelled'] as const).map((status) => (
          <button
            key={status}
            onClick={() => setFilters({ ...filters, status })}
            className={cn(
              'px-3 py-1 rounded-lg text-sm transition-colors',
              filters.status === status
                ? 'bg-accent-cyan text-bg font-medium'
                : 'bg-surface-elevated text-text-muted hover:bg-surface-elevated/70'
            )}
          >
            {status === 'all' ? 'Toutes' : STATUS_CONFIG[status].label}
          </button>
        ))}
      </div>
    </div>
  );

  const invoicesList = (
    <div className="flex-1 overflow-y-auto p-6">
      {isLoading ? (
        <div className="flex items-center justify-center h-full">
          <div className="text-text-muted">Chargement...</div>
        </div>
      ) : filteredInvoices.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full gap-4">
          <FileText className="w-16 h-16 text-text-muted/30" />
          <p className="text-text-muted">Aucune facture</p>
          <button
            onClick={handleCreateNew}
            className="px-4 py-2 rounded-lg bg-accent-cyan text-bg hover:bg-accent-cyan/90"
          >
            Créer une facture
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          {filteredInvoices.map((invoice) => {
            const StatusIcon = STATUS_CONFIG[invoice.status].icon;

            return (
              <motion.div
                key={invoice.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn(
                  'p-4 rounded-lg border border-border/50',
                  'hover:bg-surface-elevated/30 transition-colors',
                  'cursor-pointer group'
                )}
                onClick={() => handleEdit(invoice)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-medium text-text">{invoice.invoice_number}</h3>
                      <div className={cn('flex items-center gap-1.5', STATUS_CONFIG[invoice.status].color)}>
                        <StatusIcon className="w-4 h-4" />
                        <span className="text-sm">{STATUS_CONFIG[invoice.status].label}</span>
                      </div>
                    </div>

                    <div className="text-sm text-text-muted space-y-1">
                      <p>Emise le {new Date(invoice.issue_date).toLocaleDateString('fr-FR')}</p>
                      <p>Echeance le {new Date(invoice.due_date).toLocaleDateString('fr-FR')}</p>
                      {invoice.payment_date && (
                        <p>Payée le {new Date(invoice.payment_date).toLocaleDateString('fr-FR')}</p>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-col items-end gap-2">
                    <div className="text-right">
                      <p className="text-2xl font-bold text-accent-cyan">{invoice.total_ttc.toFixed(2)} €</p>
                      <p className="text-sm text-text-muted">TTC</p>
                    </div>

                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleGeneratePDF(invoice);
                        }}
                        className="p-2 rounded-lg bg-surface-elevated hover:bg-surface-elevated/70"
                        title="Télécharger PDF"
                      >
                        <Download className="w-4 h-4 text-text-muted" />
                      </button>

                      {invoice.status !== 'paid' && invoice.status !== 'cancelled' && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSendEmail(invoice);
                          }}
                          className="p-2 rounded-lg bg-surface-elevated hover:bg-surface-elevated/70"
                          title="Envoyer par email"
                        >
                          <Mail className="w-4 h-4 text-text-muted" />
                        </button>
                      )}

                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteInvoice(invoice);
                        }}
                        className="p-2 rounded-lg bg-red-500/10 hover:bg-red-500/20"
                        title="Supprimer"
                      >
                        <X className="w-4 h-4 text-red-500" />
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );

  const formModal = showForm ? (
    <InvoiceForm
      invoice={editingInvoice}
      onClose={handleCloseForm}
      onSave={handleInvoiceCreatedOrUpdated}
    />
  ) : null;

  // Mode standalone : pleine page
  if (standalone) {
    return (
      <div className="h-full flex flex-col bg-bg">
        {invoicesHeader}
        {invoicesFilters}
        {invoicesList}
        {formModal}
      </div>
    );
  }

  // Mode modal
  return (
    <AnimatePresence>
      <div
        className="fixed inset-0 z-50 flex items-center justify-center"
        onClick={() => setIsInvoicePanelOpen(false)}
      >
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        />

        {/* Panel */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ duration: 0.2 }}
          className={cn(
            'relative w-full max-w-6xl h-[85vh] mx-4',
            'bg-surface/95 backdrop-blur-xl border border-border/50 rounded-xl',
            'shadow-2xl overflow-hidden flex flex-col'
          )}
          onClick={(e) => e.stopPropagation()}
        >
          {invoicesHeader}
          {invoicesFilters}
          {invoicesList}
        </motion.div>
      </div>

      {formModal}
    </AnimatePresence>
  );
}
