/** B-1493 : la validation native du champ Validité (min 1, max 365)
 * bloquait l'enregistrement d'un devis existant hors de ces bornes, même
 * quand on ne changeait que ses notes. La règle ne vaut que pour une
 * validité saisie, et c'est le formulaire qui la dit. */
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

describe('B-1493 : la validité hors bornes', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [] });
    useBillingProfileStore.setState({ missing: null });
  });

  it('un devis existant à 400 jours s’enregistre quand on ne change que ses notes', async () => {
    const devis = { ...invoice, invoice_number: 'DEV-2026-005', document_type: 'devis' as const, status: 'draft' as const, validite_jours: 400 };
    updateInvoiceMock.mockResolvedValue(devis);
    render(
      <PrototypeExternalActionConfirmationProvider>
        <InvoiceForm invoice={devis} onClose={vi.fn()} onSave={vi.fn()} />
      </PrototypeExternalActionConfirmationProvider>,
    );

    fireEvent.change(await screen.findByLabelText(/Notes/), { target: { value: 'Relancé par téléphone' } });
    fireEvent.click(screen.getByRole('button', { name: 'Mettre à jour' }));

    await waitFor(() => expect(updateInvoiceMock).toHaveBeenCalled());
    expect(updateInvoiceMock.mock.calls[0][1].validite_jours).toBe(400);
  });

  it('une validité saisie hors bornes est refusée avec un message', async () => {
    const devis = { ...invoice, invoice_number: 'DEV-2026-006', document_type: 'devis' as const, status: 'draft' as const, validite_jours: 30 };
    render(
      <PrototypeExternalActionConfirmationProvider>
        <InvoiceForm invoice={devis} onClose={vi.fn()} onSave={vi.fn()} />
      </PrototypeExternalActionConfirmationProvider>,
    );

    fireEvent.change(await screen.findByLabelText('Validité (jours)'), { target: { value: '400' } });
    fireEvent.click(screen.getByRole('button', { name: 'Mettre à jour' }));

    expect(await screen.findByText(/entre 1 et 365 jours/)).toBeInTheDocument();
    expect(updateInvoiceMock).not.toHaveBeenCalled();
  });
});
