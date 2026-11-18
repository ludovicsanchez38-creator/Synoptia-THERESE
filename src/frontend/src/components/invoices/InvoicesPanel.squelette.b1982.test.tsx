/**
 * B-1982 : le squelette de chargement aligne autant de colonnes que le tableau.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { InvoicesPanel } from './InvoicesPanel';
import { useInvoiceStore } from '../../stores/invoiceStore';
import type { Invoice } from '../../services/api';

const { listInvoicesMock } = vi.hoisted(() => ({ listInvoicesMock: vi.fn() }));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, listInvoices: listInvoicesMock };
});

const piece: Invoice = {
  id: 'inv-1', invoice_number: 'FAC-2026-001', contact_id: 'contact-1', contact_name: 'Jean Dupont',
  document_type: 'facture', tva_applicable: true, currency: 'EUR',
  issue_date: '2026-07-01T00:00:00Z', due_date: '2026-07-31T00:00:00Z', status: 'draft',
  subtotal_ht: 100, total_tax: 20, total_ttc: 120, notes: null, payment_date: null,
  validite_jours: null, payment_terms: null, payment_method: null, late_penalty_rate: null,
  legal_mentions: null, converted_from_id: null,
  created_at: '2026-07-01T00:00:00Z', updated_at: '2026-07-01T00:00:00Z', lines: [],
};

describe('B-1982 : le squelette suit les colonnes du tableau', () => {
  beforeEach(() => {
    useInvoiceStore.setState({
      invoices: [],
      currentInvoiceId: null,
      filters: { status: 'all' },
      isInvoicePanelOpen: true,
      draftInvoice: null,
    });
  });

  it('compte autant de cases que d’en-têtes', async () => {
    let livrer: (lignes: Invoice[]) => void = () => {};
    listInvoicesMock.mockImplementation(() => new Promise<Invoice[]>((resolve) => { livrer = resolve; }));
    render(<InvoicesPanel standalone />);
    await screen.findByText('Chargement...');
    const rang = document.querySelector('[aria-hidden="true"].grid');
    expect(rang).not.toBeNull();
    const cases = rang!.childElementCount;
    livrer([piece]);
    await screen.findByRole('columnheader', { name: 'Montant TTC' });
    expect(cases).toBe(screen.getAllByRole('columnheader').length);
  });
});
