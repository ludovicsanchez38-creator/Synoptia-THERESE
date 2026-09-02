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
  status?: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled' | 'accepted' | 'refused' | 'expired' | 'converted' | 'all';
  document_type?: 'devis' | 'facture' | 'avoir';
  contact_id?: string;
}

type StatutDeFiltre = NonNullable<InvoiceFilters['status']>;
type TypeDeDocument = NonNullable<InvoiceFilters['document_type']>;

/**
 * Les statuts qu'un type de document peut porter. Un devis ne se paie pas, une
 * facture ne s'accepte pas : ce sont deux vocabulaires distincts, et le
 * panneau ne construit sa rangée de boutons qu'à partir du type. Source
 * unique, ici, pour que la rangée à l'écran et le contrôle des filtres ne
 * puissent pas diverger.
 */
export const STATUTS_DE_DEVIS: readonly StatutDeFiltre[] = [
  'all', 'draft', 'sent', 'accepted', 'refused', 'expired', 'converted',
];
export const STATUTS_DE_FACTURE: readonly StatutDeFiltre[] = [
  'all', 'draft', 'sent', 'paid', 'overdue', 'cancelled',
];

export function statutsProposesPour(documentType?: TypeDeDocument): readonly StatutDeFiltre[] {
  return documentType === 'devis' ? STATUTS_DE_DEVIS : STATUTS_DE_FACTURE;
}

const TYPES_DE_DOCUMENT: readonly TypeDeDocument[] = ['devis', 'facture', 'avoir'];

const FILTRES_PAR_DEFAUT: InvoiceFilters = { status: 'all' };

/**
 * B-005 : les filtres relus du stockage sont fusionnés avec le défaut, puis
 * contrôlés. La fusion de zustand est un étalement de PREMIER niveau : l'objet
 * `filters` persisté remplaçait le défaut en bloc, donc un objet partiel
 * perdait `status: 'all'`, une paire impossible revenait telle quelle, et
 * `null` faisait tomber la liste au premier document.
 *
 * B-004 : `contact_id` n'est jamais relu. Aucun contrôle d'écran ne le vide ;
 * relu, il bornait silencieusement toute la facturation à un client, en
 * travers du rechargement et des deux boutons de réinitialisation.
 */
export function assainirFiltres(bruts: unknown): InvoiceFilters {
  const source =
    bruts && typeof bruts === 'object' ? (bruts as Record<string, unknown>) : {};

  const documentType = TYPES_DE_DOCUMENT.includes(source.document_type as TypeDeDocument)
    ? (source.document_type as TypeDeDocument)
    : undefined;

  const status = statutsProposesPour(documentType).includes(source.status as StatutDeFiltre)
    ? (source.status as StatutDeFiltre)
    : FILTRES_PAR_DEFAUT.status;

  return documentType ? { status, document_type: documentType } : { status };
}

/**
 * B-005, second site : changer de type de document assainit le statut au lieu
 * de le traîner. « Payée » choisi sur les factures puis « Devis » produisait
 * une paire que la rangée de statuts ne sait pas afficher — aucun bouton
 * sélectionné au-dessus d'une liste vide, sans rien pour l'expliquer.
 */
export function filtresAvecType(
  filtres: InvoiceFilters,
  documentType?: TypeDeDocument
): InvoiceFilters {
  const status = statutsProposesPour(documentType).includes(filtres.status as StatutDeFiltre)
    ? filtres.status
    : FILTRES_PAR_DEFAUT.status;
  return { ...filtres, document_type: documentType, status };
}

interface InvoiceStore {
  // State
  invoices: Invoice[];
  /**
   * B-003 : la liste ci-dessus a DEUX écrivains (le panneau Factures et le
   * hook du parcours prototype). Le drapeau de troncature vivait dans le
   * panneau, il ne décrivait donc que le dernier chargement du panneau :
   * après une écriture de l'autre écrivain, l'en-tête annonçait « 1+
   * document » et gardait son bandeau au-dessus d'une liste d'un élément.
   * Il vit ici, posé par la MÊME action que la liste qu'il décrit.
   */
  listeTronquee: boolean;
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
  /** `tronquee` par défaut à faux : un écrivain sans notion de plafond
   *  n'hérite jamais de l'avertissement d'un autre. */
  setInvoices: (invoices: Invoice[], tronquee?: boolean) => void;
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
      listeTronquee: false,
      currentInvoiceId: null,
      filters: { status: 'all' },
      isInvoicePanelOpen: false,
      draftInvoice: null,

      // Actions
      setInvoices: (invoices, tronquee = false) => set({ invoices, listeTronquee: tronquee }),

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

          // Filter by document type
          if (filters.document_type && invoice.document_type !== filters.document_type) {
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
        // B-004 : le client filtré ne part pas au stockage - rien à l'écran ne
        // le vide, il se figerait pour de bon.
        filters: { status: state.filters?.status, document_type: state.filters?.document_type },
        // On ne persiste PAS les factures (trop volumineuses)
        // Elles seront rechargées depuis l'API
      }),
      // B-005 : fusion en profondeur sur les filtres, et contrôle avant usage.
      // Le stockage peut être partiel, incohérent ou hérité d'une version
      // antérieure ; l'étalement de premier niveau de zustand le laissait
      // remplacer le défaut en bloc.
      merge: (persiste, courant) => {
        const brut = (persiste ?? {}) as Partial<InvoiceStore>;
        return { ...courant, ...brut, filters: assainirFiltres(brut.filters) };
      },
    }
  )
);
