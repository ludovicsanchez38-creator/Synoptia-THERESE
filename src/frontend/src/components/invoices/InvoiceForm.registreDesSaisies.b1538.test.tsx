/** B-1538 (RFC P-121 V4, R-121-4) : une modale de devis ou de facture
 * modifiée était fermée sans question par une navigation posée dans le store
 * (« Voir » sur la notification d'une Action finie) : la modale n'était pas
 * inscrite au registre des saisies que la coque consulte avant de démonter
 * une vue. InvoiceForm s'y inscrit ; Contact et Projet, que rien ne démonte,
 * non. */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';
import { useBillingProfileStore } from '../../stores/billingProfileStore';
import type { Invoice } from '../../services/api';
import { PrototypeExternalActionConfirmationProvider } from '../app/ExternalActionConfirmation';
import { _viderSaisiesEnCours, sortieRetenueParUneSaisie } from '../../lib/saisieEnCours';

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

function ouvrir() {
  render(
    <PrototypeExternalActionConfirmationProvider>
      <InvoiceForm invoice={{ ...invoice, status: 'draft' }} onClose={vi.fn()} onSave={vi.fn()} />
    </PrototypeExternalActionConfirmationProvider>,
  );
}

describe('B-1538 : une navigation venue du store consulte la modale de pièce', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _viderSaisiesEnCours();
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [] });
    useBillingProfileStore.setState({ missing: null });
  });

  it('modifiée, elle retient la sortie et pose sa question', async () => {
    ouvrir();
    fireEvent.change(await screen.findByDisplayValue('Accompagnement'), { target: { value: 'Accompagnement mensuel' } });

    let retenue = false;
    act(() => { retenue = sortieRetenueParUneSaisie(); });

    expect(retenue).toBe(true);
    expect(screen.getByText('Abandonner les modifications ?')).toBeInTheDocument();
  });

  it('témoin : intacte, elle laisse passer la sortie', async () => {
    ouvrir();
    await screen.findByDisplayValue('Accompagnement');
    expect(sortieRetenueParUneSaisie()).toBe(false);
  });
});
