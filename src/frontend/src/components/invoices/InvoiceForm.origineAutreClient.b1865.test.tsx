/**
 * B-1865 : la facture d'origine d'un avoir appartient au client choisi.
 * Changer de client doit l'oublier, sinon l'enregistrement envoie encore
 * la facture de l'ancien client.
 */
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';
import { useBillingProfileStore } from '../../stores/billingProfileStore';
import { type Invoice } from '../../services/api';
import { PrototypeExternalActionConfirmationProvider } from '../app/ExternalActionConfirmation';

const { updateInvoiceMock, getBillingProfileStatusMock, listInvoicesMock, contacts } = vi.hoisted(() => ({
  updateInvoiceMock: vi.fn(),
  getBillingProfileStatusMock: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
  listInvoicesMock: vi.fn(),
  contacts: [
    { id: 'contact-1', first_name: 'Jean', last_name: 'Dupont', email: 'jean@example.com', address: '1 rue A' },
    { id: 'contact-2', first_name: 'Marie', last_name: 'Martin', email: 'marie@example.com', address: '2 rue B' },
  ],
}));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');

  return {
    ...actual,
    listContacts: vi.fn().mockResolvedValue(contacts),
    getContact: vi.fn().mockResolvedValue(contacts[0]),
    updateInvoice: updateInvoiceMock,
    listInvoices: listInvoicesMock,
    getBillingProfileStatus: getBillingProfileStatusMock,
  };
});

const invoice: Invoice = {
  id: 'avoir-1', invoice_number: 'AV-2026-001', contact_id: 'contact-1',
  document_type: 'avoir', tva_applicable: true, currency: 'EUR',
  issue_date: '2026-07-01T00:00:00Z', due_date: '2026-07-31T00:00:00Z', status: 'draft',
  subtotal_ht: 100, total_tax: 20, total_ttc: 120, notes: null, payment_terms: null,
  payment_method: null, late_penalty_rate: null, legal_mentions: null, converted_from_id: null,
  validite_jours: null, payment_date: null, created_at: '2026-07-01T08:00:00Z',
  updated_at: '2026-07-01T08:00:00Z',
  lines: [{
    id: 'line-1', invoice_id: 'avoir-1', description: 'Accompagnement',
    quantity: 1, unit_price_ht: 100, tva_rate: 20, total_ht: 100, total_ttc: 120,
  }],
};

describe('B-1865 : changer de client oublie la facture d’origine', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [] });
    useBillingProfileStore.setState({ missing: null });
    listInvoicesMock.mockImplementation(async (params: { contact_id?: string }) => {
      if (params.contact_id === 'contact-2') {
        return [{ ...invoice, id: 'facture-2', invoice_number: 'FAC-2026-002', contact_id: 'contact-2', document_type: 'facture', status: 'sent' }];
      }
      return [{ ...invoice, id: 'facture-1', invoice_number: 'FAC-2026-001', contact_id: 'contact-1', document_type: 'facture', status: 'sent' }];
    });
    updateInvoiceMock.mockImplementation(async (id: string, data: object) => ({ ...invoice, id, ...data }));
  });

  it('envoie un avoir sans la facture de l’ancien client', async () => {
    render(
      <PrototypeExternalActionConfirmationProvider>
        <InvoiceForm invoice={invoice} onClose={vi.fn()} onSave={vi.fn()} />
      </PrototypeExternalActionConfirmationProvider>,
    );
    const origine = await screen.findByLabelText('Facture d’origine') as HTMLSelectElement;
    await waitFor(() => expect(Array.from(origine.options).map((o) => o.value)).toContain('facture-1'));
    fireEvent.change(origine, { target: { value: 'facture-1' } });
    expect(origine).toHaveValue('facture-1');

    fireEvent.change(screen.getByLabelText('Client *'), { target: { value: 'contact-2' } });
    await waitFor(() => expect(listInvoicesMock).toHaveBeenCalledWith({ contact_id: 'contact-2', document_type: 'facture' }));
    expect(origine).toHaveValue('');

    fireEvent.click(screen.getByRole('button', { name: 'Mettre à jour' }));
    await waitFor(() => expect(updateInvoiceMock).toHaveBeenCalled());
    expect(updateInvoiceMock.mock.calls[0][1]).toMatchObject({
      contact_id: 'contact-2',
      converted_from_id: null,
    });
  });
});
