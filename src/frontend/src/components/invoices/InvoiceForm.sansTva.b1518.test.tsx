/** B-1518 : la fenêtre d'une pièce ignorait `tva_applicable`. Le moteur et
 * le PDF rendent TTC = HT quand la TVA ne s'applique pas ; la fenêtre
 * appliquait le taux des lignes et affichait un TTC qui n'existe pas. */
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

describe('B-1518 : pièce sans TVA applicable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [] });
    useBillingProfileStore.setState({ missing: null });
  });

  it('les totaux affichés suivent la pièce : TTC = HT, TVA nulle', async () => {
    const piece = { ...invoice, tva_applicable: false, subtotal_ht: 100, total_tax: 0, total_ttc: 100 };
    render(
      <PrototypeExternalActionConfirmationProvider>
        <InvoiceForm invoice={piece} onClose={vi.fn()} onSave={vi.fn()} />
      </PrototypeExternalActionConfirmationProvider>,
    );

    const libelle = await screen.findByText('Total TTC');
    const montant = libelle.nextElementSibling as HTMLElement;
    expect(montant.textContent?.replace(/\s/g, '')).toMatch(/^100[,.]00/);
    const tva = (screen.getByText('Total TVA').nextElementSibling as HTMLElement).textContent?.replace(/\s/g, '');
    expect(tva).toMatch(/^0[,.]00/);
  });
});
