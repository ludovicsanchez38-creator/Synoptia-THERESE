/** B-1537 (RFC P-121 V4, R-121-3) : depuis B-1506, le moteur refuse (409)
 * qu'une facture ou un avoir émis repasse en brouillon ; la modale proposait
 * encore « Brouillon ». Un devis et un brouillon de facture le gardent. */
import { render, screen } from '@testing-library/react';
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

async function statutsProposes(piece: Invoice): Promise<string[]> {
  render(
    <PrototypeExternalActionConfirmationProvider>
      <InvoiceForm invoice={piece} onClose={vi.fn()} onSave={vi.fn()} />
    </PrototypeExternalActionConfirmationProvider>,
  );
  const select = (await screen.findByLabelText('Statut')) as HTMLSelectElement;
  return Array.from(select.options).map((option) => option.value);
}

describe('B-1537 : une pièce émise ne propose plus le brouillon', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [] });
    useBillingProfileStore.setState({ missing: null });
  });

  it('une facture envoyée ne propose pas « Brouillon »', async () => {
    const statuts = await statutsProposes(invoice);
    expect(statuts).not.toContain('draft');
    expect(statuts).toContain('paid');
  });

  it('un avoir payé ne propose pas « Brouillon »', async () => {
    expect(await statutsProposes({ ...invoice, document_type: 'avoir', status: 'paid' })).not.toContain('draft');
  });

  it('témoin : un brouillon de facture garde « Brouillon »', async () => {
    expect(await statutsProposes({ ...invoice, status: 'draft' })).toContain('draft');
  });

  it('témoin : un devis envoyé garde « Brouillon »', async () => {
    expect(await statutsProposes({ ...invoice, document_type: 'devis', status: 'sent' })).toContain('draft');
  });
});
