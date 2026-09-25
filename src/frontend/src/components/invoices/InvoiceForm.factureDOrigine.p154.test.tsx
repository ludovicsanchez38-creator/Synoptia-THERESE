/**
 * P-154 (recette P-146, lot 3 ; acceptée le 25/09) : un avoir se relie à la
 * facture qu'il corrige, choisie parmi les factures du client.
 */
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';
import { useBillingProfileStore } from '../../stores/billingProfileStore';
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

describe('P-154 : un avoir et sa facture d’origine', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [] });
    useBillingProfileStore.setState({ missing: null });
    listInvoicesMock.mockResolvedValue([{ ...invoice, id: 'facture-1', invoice_number: 'FAC-2026-001' }]);
    updateInvoiceMock.mockImplementation(async (id: string, data: object) => ({ ...invoice, id, ...data }));
  });

  it('le formulaire d’un avoir propose les factures du client et garde le choix', async () => {
    rendre({ ...invoice, id: 'avoir-1', invoice_number: 'AV-2026-001', document_type: 'avoir', converted_from_id: null });
    const champ = await screen.findByLabelText('Facture d’origine') as HTMLSelectElement;
    await waitFor(() => expect(Array.from(champ.options).some((o) => (o.textContent ?? '').includes('FAC-2026-001'))).toBe(true));
    expect(listInvoicesMock).toHaveBeenCalledWith({ contact_id: 'contact-1', document_type: 'facture' });
    fireEvent.change(champ, { target: { value: 'facture-1' } });
    fireEvent.click(screen.getByRole('button', { name: 'Mettre à jour' }));
    await waitFor(() => expect(updateInvoiceMock).toHaveBeenCalled());
    expect(updateInvoiceMock.mock.calls[0][1]).toMatchObject({ converted_from_id: 'facture-1' });
  });

  it('une facture n’a pas ce champ', () => {
    rendre(invoice);
    expect(screen.queryByLabelText('Facture d’origine')).toBeNull();
  });
});
