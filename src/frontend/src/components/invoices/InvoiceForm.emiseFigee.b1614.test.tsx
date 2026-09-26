/** B-1614 (suite de B-1506) : une facture émise se modifiait encore depuis
 * le formulaire (client, dates, lignes, notes). Son contenu est figé : les
 * champs sont désactivés, une phrase dit pourquoi, et seul le statut part. */
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';
import { useBillingProfileStore } from '../../stores/billingProfileStore';
import type { Invoice } from '../../services/api';
import { PrototypeExternalActionConfirmationProvider } from '../app/ExternalActionConfirmation';

const { createInvoiceMock, updateInvoiceMock, getBillingProfileStatusMock, markInvoicePaidMock, updateDevisStatusMock } = vi.hoisted(() => ({
  createInvoiceMock: vi.fn(),
  updateInvoiceMock: vi.fn(),
  getBillingProfileStatusMock: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
  markInvoicePaidMock: vi.fn(),
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

describe('B-1614 : une facture émise est figée dans le formulaire', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [] });
    useBillingProfileStore.setState({ missing: null });
  });

  it('client, dates, lignes et notes sont désactivés, le statut ne l’est pas', async () => {
    render(
      <PrototypeExternalActionConfirmationProvider>
        <InvoiceForm invoice={invoice} onClose={vi.fn()} onSave={vi.fn()} />
      </PrototypeExternalActionConfirmationProvider>,
    );
    expect(await screen.findByLabelText('Statut')).not.toBeDisabled();
    expect(screen.getByLabelText(/Client/)).toBeDisabled();
    expect(screen.getByLabelText(/Date d'émission/)).toBeDisabled();
    expect(screen.getByLabelText(/Notes/)).toBeDisabled();
    expect(screen.getByDisplayValue('Accompagnement')).toBeDisabled();
    expect(screen.getByText(/émets un avoir/)).toBeInTheDocument();
  });

  it('seul le statut part à l’enregistrement', async () => {
    updateInvoiceMock.mockResolvedValue({ ...invoice, status: 'paid' });
    render(
      <PrototypeExternalActionConfirmationProvider>
        <InvoiceForm invoice={invoice} onClose={vi.fn()} onSave={vi.fn()} />
      </PrototypeExternalActionConfirmationProvider>,
    );
    fireEvent.change(await screen.findByLabelText('Statut'), { target: { value: 'paid' } });
    fireEvent.click(screen.getByRole('button', { name: 'Mettre à jour' }));
    const confirmer = screen.queryByRole('button', { name: 'Confirmer le changement de statut' });
    if (confirmer) fireEvent.click(confirmer);

    await waitFor(() => expect(updateInvoiceMock).toHaveBeenCalledWith('invoice-1', { status: 'paid' }));
  });
});
