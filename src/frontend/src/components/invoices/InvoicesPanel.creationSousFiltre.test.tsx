/**
 * B-569 (05/09/2026) : un devis créé pendant que le filtre « En retard » est
 * actif disparaissait aussitôt de la liste, sans explication. Le filtre de
 * statut est levé pour montrer le document que l'on vient de créer.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { InvoicesPanel } from './InvoicesPanel';
import { useInvoiceStore } from '../../stores/invoiceStore';
import type { Invoice } from '../../services/api';

const mockListInvoices = vi.fn();

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, listInvoices: (...args: unknown[]) => mockListInvoices(...args), deleteInvoice: vi.fn(), generateInvoicePDF: vi.fn(), sendInvoiceByEmail: vi.fn() };
});

const devisCree = {
  id: 'dev-2026-020', invoice_number: 'DEV-2026-020', document_type: 'devis', contact_id: 'contact-1', currency: 'EUR',
  issue_date: '2026-09-05T00:00:00Z', due_date: '2026-10-05T00:00:00Z', status: 'draft' as const,
  subtotal_ht: 1490, total_tax: 298, total_ttc: 1788, notes: null, payment_date: null,
  created_at: '2026-09-05T13:20:00Z', updated_at: '2026-09-05T13:20:00Z', lines: [],
} as unknown as Invoice;

vi.mock('./InvoiceForm', () => ({
  InvoiceForm: ({ onSave }: { onSave: (inv: unknown) => void }) => (
    <button data-testid="simuler-creation-devis" onClick={() => onSave(devisCree)}>Créer</button>
  ),
}));

const factureEnRetard = {
  id: 'fact-2026-002', invoice_number: 'FACT-2026-002', document_type: 'facture', contact_id: 'claire', currency: 'EUR',
  issue_date: '2026-07-25T00:00:00Z', due_date: '2026-08-25T00:00:00Z', status: 'overdue' as const,
  subtotal_ht: 1200, total_tax: 240, total_ttc: 1440, notes: null, payment_date: null,
  created_at: '2026-07-25T00:00:00Z', updated_at: '2026-07-25T00:00:00Z', lines: [],
} as unknown as Invoice;

describe('InvoicesPanel : création sous un filtre de statut (B-569)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockListInvoices.mockResolvedValue([factureEnRetard]);
    useInvoiceStore.setState({ invoices: [factureEnRetard], currentInvoiceId: null, filters: { status: 'overdue' }, isInvoicePanelOpen: true, draftInvoice: null });
  });

  it('le document créé est visible : le filtre de statut est levé', async () => {
    render(<InvoicesPanel standalone />);
    await screen.findByText('FACT-2026-002');
    fireEvent.click(screen.getByRole('button', { name: /Nouvelle facture|Nouveau devis/ }));
    mockListInvoices.mockResolvedValue([factureEnRetard, devisCree]);

    fireEvent.click(screen.getByTestId('simuler-creation-devis'));

    await waitFor(() => expect(screen.getByText('DEV-2026-020')).toBeInTheDocument());
    expect(useInvoiceStore.getState().filters.status).toBe('all');
  });
});
