/**
 * P-136 (acceptée le 25/09) : avertir, sans bloquer, qu'une facture avec TVA
 * de plus de 150 € HT partirait sans le numéro de TVA de l'émetteur.
 * Règle : service-public.fr F31808 (vérifié le 11 août 2026), relevée le
 * 26/09/2026.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';
import { type Invoice } from '../../services/api';
import { PrototypeExternalActionConfirmationProvider } from '../app/ExternalActionConfirmation';

const { createInvoiceMock, updateInvoiceMock, getBillingProfileStatusMock, markInvoicePaidMock, updateDevisStatusMock, listInvoicesMock } = vi.hoisted(() => ({
  createInvoiceMock: vi.fn(),
  updateInvoiceMock: vi.fn(),
  getBillingProfileStatusMock: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
  markInvoicePaidMock: vi.fn(),
  listInvoicesMock: vi.fn(),
  updateDevisStatusMock: vi.fn(),
}));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');

  return {
    ...actual,
    listContacts: vi.fn().mockResolvedValue([
      {
        id: 'contact-1',
        first_name: 'Jean',
        last_name: 'Dupont',
        email: 'jean@example.com',
      },
    ]),
    createInvoice: createInvoiceMock,
    updateInvoice: updateInvoiceMock,
    markInvoicePaid: markInvoicePaidMock,
    listInvoices: listInvoicesMock,
    updateDevisStatus: updateDevisStatusMock,
    getBillingProfileStatus: getBillingProfileStatusMock,
  };
});

const invoice: Invoice = {
  id: 'invoice-1', invoice_number: 'FAC-2026-001', contact_id: 'contact-1',
  document_type: 'facture', tva_applicable: true, currency: 'EUR',
  issue_date: '2026-07-01T00:00:00Z', due_date: '2026-07-31T00:00:00Z', status: 'sent',
  subtotal_ht: 100, total_tax: 20, total_ttc: 120, notes: null, payment_terms: null,
  payment_method: null, late_penalty_rate: null, legal_mentions: null, converted_from_id: null,
  validite_jours: null, payment_date: null, created_at: '2026-07-01T08:00:00Z',
  updated_at: '2026-07-01T08:00:00Z',
  lines: [{
    id: 'line-1', invoice_id: 'invoice-1', description: 'Accompagnement',
    quantity: 1, unit_price_ht: 100, tva_rate: 20, total_ht: 100, total_ttc: 120,
  }],
};

function rendre(piece: Invoice) {
  return render(
    <PrototypeExternalActionConfirmationProvider>
      <InvoiceForm invoice={piece} onClose={vi.fn()} onSave={vi.fn()} />
    </PrototypeExternalActionConfirmationProvider>,
  );
}

const AVERTISSEMENT = /numéro de TVA/;

describe('P-136 : le numéro de TVA de l’émetteur', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    listInvoicesMock.mockResolvedValue([]);
  });

  it('sans numéro, une facture avec TVA de plus de 150 € HT avertit', async () => {
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [], tva_intra_renseigne: false });
    rendre({ ...invoice, lines: [{ ...invoice.lines[0], quantity: 2, unit_price_ht: 450, tva_rate: 20 }] });
    expect(await screen.findByText(AVERTISSEMENT)).toBeInTheDocument();
  });

  it('avec le numéro, rien', async () => {
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [], tva_intra_renseigne: true });
    rendre({ ...invoice, lines: [{ ...invoice.lines[0], quantity: 2, unit_price_ht: 450, tva_rate: 20 }] });
    await waitFor(() => expect(getBillingProfileStatusMock).toHaveBeenCalled());
    expect(screen.queryByText(AVERTISSEMENT)).toBeNull();
  });

  it('150 € HT ou moins, ou sans TVA : rien', async () => {
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [], tva_intra_renseigne: false });
    const { unmount } = rendre({ ...invoice, lines: [{ ...invoice.lines[0], quantity: 1, unit_price_ht: 150, tva_rate: 20 }] });
    await waitFor(() => expect(getBillingProfileStatusMock).toHaveBeenCalled());
    expect(screen.queryByText(AVERTISSEMENT)).toBeNull();
    unmount();
    rendre({ ...invoice, lines: [{ ...invoice.lines[0], quantity: 2, unit_price_ht: 450, tva_rate: 0 }] });
    expect(screen.queryByText(AVERTISSEMENT)).toBeNull();
  });
});
