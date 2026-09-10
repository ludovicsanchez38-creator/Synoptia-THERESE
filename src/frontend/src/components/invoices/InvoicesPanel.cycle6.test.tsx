/**
 * Cycle 6, lecteur #287 (InvoicesPanel.tsx) : « Supprimer la facture ? » ne
 * s'inscrivait pas sur la pile d'Échap ; la touche remontait à la coque, qui
 * repliait toute la vue Facturer au lieu de la seule confirmation.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useInvoiceStore } from '../../stores/invoiceStore';
import { _clearEscapeHandlers, runTopEscapeHandler } from '../../lib/escapeStack';

const mockListInvoices = vi.fn();
vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...reel, listInvoices: (...a: unknown[]) => mockListInvoices(...a), generateInvoicePDF: vi.fn(), deleteInvoice: vi.fn(), sendInvoiceByEmail: vi.fn() };
});
vi.mock('./InvoiceForm', () => ({ InvoiceForm: () => <div data-testid="invoice-form" /> }));

import { InvoicesPanel } from './InvoicesPanel';

const facture = {
  id: 'fac-1', invoice_number: 'FAC-001', contact_id: 'c1', contact_name: 'Sophie Garcia', currency: 'EUR', document_type: 'facture' as const,
  issue_date: '2026-03-14T00:00:00Z', due_date: '2026-03-31T00:00:00Z', status: 'draft' as const, subtotal_ht: 100, total_tax: 20, total_ttc: 120,
  notes: null, payment_date: null, created_at: '2026-03-14T00:00:00Z', updated_at: '2026-03-14T00:00:00Z', lines: [],
};

describe('#287 : Échap devant « Supprimer la facture ? » ne ferme que la confirmation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _clearEscapeHandlers();
    mockListInvoices.mockResolvedValue([facture]);
    useInvoiceStore.setState({ invoices: [], currentInvoiceId: null, filters: { status: 'all' }, isInvoicePanelOpen: true, draftInvoice: null });
  });

  it('la confirmation prend Échap sur la pile, puis la rend', async () => {
    render(<InvoicesPanel standalone />);
    await screen.findByText('FAC-001');
    fireEvent.click(screen.getByTitle('Supprimer'));
    await screen.findByRole('dialog', { name: 'Confirmer la suppression' });

    let pris = false;
    act(() => { pris = runTopEscapeHandler(); });
    expect(pris).toBe(true);
    expect(screen.queryByRole('dialog', { name: 'Confirmer la suppression' })).toBeNull();
    expect(screen.getByText('FAC-001')).toBeInTheDocument();
    expect(runTopEscapeHandler()).toBe(false);
  });
});
