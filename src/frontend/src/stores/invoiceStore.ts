/**
 * THÉRÈSE v2 - Invoice Store
 *
 * Zustand store pour la gestion de l'état des factures.
 * Phase 4 - Invoicing
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Invoice, InvoiceLineRequest } from '../services/api';

interface InvoiceFilters {
  status?: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled' | 'all';
  contact_id?: string;
}

interface InvoiceStore {
  // State
  invoices: Invoice[];
  currentInvoiceId: string | null;
  filters: InvoiceFilters;
  isInvoicePanelOpen: boolean;

  // Draft invoice for form
  draftInvoice: {
    contact_id: string;
    issue_date: string;
    due_date: string;
    lines: InvoiceLineRequest[];
    notes: string;
  } | null;

  // Actions
  setInvoices: (invoices: Invoice[]) => void;
  addInvoice: (invoice: Invoice) => void;
  updateInvoiceInStore: (invoice: Invoice) => void;
  removeInvoice: (invoiceId: string) => void;

  setCurrentInvoiceId: (id: string | null) => void;
  setFilters: (filters: InvoiceFilters) => void;

  setIsInvoicePanelOpen: (isOpen: boolean) => void;
  toggleInvoicePanel: () => void;

  // Draft invoice
  setDraftInvoice: (draft: InvoiceStore['draftInvoice']) => void;
  clearDraftInvoice: () => void;

  // Helpers
  getFilteredInvoices: () => Invoice[];
}

export const useInvoiceStore = create<InvoiceStore>()(
  persist(
    (set, get) => ({
      // Initial state
      invoices: [],
      currentInvoiceId: null,
      filters: { status: 'all' },
      isInvoicePanelOpen: false,
      draftInvoice: null,

      // Actions
      setInvoices: (invoices) => set({ invoices }),

      addInvoice: (invoice) =>
        set((state) => ({ invoices: [invoice, ...state.invoices] })),

      updateInvoiceInStore: (invoice) =>
        set((state) => ({
          invoices: state.invoices.map((inv) =>
            inv.id === invoice.id ? invoice : inv
          ),
        })),

      removeInvoice: (invoiceId) =>
        set((state) => ({
          invoices: state.invoices.filter((inv) => inv.id !== invoiceId),
        })),

      setCurrentInvoiceId: (id) => set({ currentInvoiceId: id }),

      setFilters: (filters) => set({ filters }),

      setIsInvoicePanelOpen: (isOpen) => set({ isInvoicePanelOpen: isOpen }),

      toggleInvoicePanel: () =>
        set((state) => ({ isInvoicePanelOpen: !state.isInvoicePanelOpen })),

      setDraftInvoice: (draft) => set({ draftInvoice: draft }),

      clearDraftInvoice: () => set({ draftInvoice: null }),

      // Helpers
      getFilteredInvoices: () => {
        const { invoices, filters } = get();

        return invoices.filter((invoice) => {
          // Filter by status
          if (filters.status && filters.status !== 'all' && invoice.status !== filters.status) {
            return false;
          }

          // Filter by contact
          if (filters.contact_id && invoice.contact_id !== filters.contact_id) {
            return false;
          }

          return true;
        });
      },
    }),
    {
      name: 'therese-invoice-storage',
      partialize: (state) => ({
        filters: state.filters,
        // On ne persiste PAS les factures (trop volumineuses)
        // Elles seront rechargées depuis l'API
      }),
    }
  )
);
