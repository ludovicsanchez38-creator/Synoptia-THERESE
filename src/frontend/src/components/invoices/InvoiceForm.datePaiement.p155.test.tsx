/**
 * P-155 et P-138 (recette P-146, lot 3 ; acceptées, décisions du 25/09) :
 * « Marquer comme payée » imposait l'instant du clic comme date de paiement,
 * et un brouillon jamais émis passait payé sans un mot. La date réelle se
 * saisit (jamais dans le futur), la confirmation la reprend et signale un
 * brouillon.
 */
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';
import { useBillingProfileStore } from '../../stores/billingProfileStore';
import { type Invoice } from '../../services/api';
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

function rendre(piece: Invoice) {
  return render(
    <PrototypeExternalActionConfirmationProvider>
      <InvoiceForm invoice={piece} onClose={vi.fn()} onSave={vi.fn()} />
    </PrototypeExternalActionConfirmationProvider>,
  );
}

describe('P-155 : la date réelle du paiement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [] });
    useBillingProfileStore.setState({ missing: null });
    markInvoicePaidMock.mockResolvedValue({ ...invoice, status: 'paid' });
  });

  it('la date saisie part avec le paiement et la confirmation la dit', async () => {
    rendre(invoice);
    const champ = screen.getByLabelText('Payée le') as HTMLInputElement;
    expect(champ.type).toBe('date');
    expect(champ.max).toBeTruthy();
    fireEvent.change(champ, { target: { value: '2026-07-20' } });
    fireEvent.click(screen.getByRole('button', { name: 'Marquer comme payée' }));
    expect(screen.getByTestId('external-action-confirmation')).toHaveTextContent('20/07/2026');
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer le paiement' }));
    await waitFor(() => expect(markInvoicePaidMock).toHaveBeenCalledWith('invoice-1', '2026-07-20'));
  });

  it('P-138 : un brouillon est signalé avant de passer payé', () => {
    rendre({ ...invoice, status: 'draft' });
    fireEvent.click(screen.getByRole('button', { name: 'Marquer comme payée' }));
    expect(screen.getByTestId('external-action-confirmation')).toHaveTextContent(/brouillon/i);
  });
});
