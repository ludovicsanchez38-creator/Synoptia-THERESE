/**
 * B-568 (05/09/2026) : modifier une facture dont le client n'est pas dans les
 * 200 contacts les plus récents affichait « Sélectionner un contact » à la
 * place du vrai client. Le contact de la pièce est chargé à part et proposé.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';
import { useBillingProfileStore } from '../../stores/billingProfileStore';
import { type Invoice } from '../../services/api';

const { getBillingProfileStatusMock, getContactMock } = vi.hoisted(() => ({
  getBillingProfileStatusMock: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
  getContactMock: vi.fn(),
}));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    listContacts: vi.fn().mockResolvedValue(
      Array.from({ length: 200 }, (_, i) => ({ id: `recent-${i}`, first_name: 'Contact', last_name: `Récent ${i}`, email: `c${i}@example.com` })),
    ),
    getContact: getContactMock,
    createInvoice: vi.fn(), updateInvoice: vi.fn(), markInvoicePaid: vi.fn(), updateDevisStatus: vi.fn(),
    getBillingProfileStatus: getBillingProfileStatusMock,
  };
});

const factureDeClaire: Invoice = {
  id: 'FACT-2026-002', invoice_number: 'FACT-2026-002', contact_id: 'claire-roux-id',
  document_type: 'facture', tva_applicable: true, currency: 'EUR',
  issue_date: '2026-07-25T00:00:00Z', due_date: '2026-08-25T00:00:00Z', status: 'overdue',
  subtotal_ht: 1200, total_tax: 240, total_ttc: 1440, notes: null, payment_terms: null,
  payment_method: null, late_penalty_rate: null, legal_mentions: null, converted_from_id: null,
  validite_jours: null, payment_date: null, created_at: '2026-07-01T08:00:00Z', updated_at: '2026-07-01T08:00:00Z',
  lines: [{ id: 'line-1', invoice_id: 'FACT-2026-002', description: 'Prestation', quantity: 1, unit_price_ht: 1200, tva_rate: 20, total_ht: 1200, total_ttc: 1440 }],
};

describe('InvoiceForm : client hors des 200 contacts récents (B-568)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [] });
    getContactMock.mockResolvedValue({ id: 'claire-roux-id', first_name: 'Claire', last_name: 'Roux', email: 'claire@roux.test' });
    useBillingProfileStore.setState({ missing: null });
  });

  it('le sélecteur propose et affiche le client de la pièce', async () => {
    render(<InvoiceForm invoice={factureDeClaire} onClose={vi.fn()} onSave={vi.fn()} />);
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent(/Liste incomplète/));
    await waitFor(() => expect(getContactMock).toHaveBeenCalledWith('claire-roux-id'));

    const selecteur = screen.getByLabelText('Client *') as HTMLSelectElement;
    await waitFor(() => expect(Array.from(selecteur.options).map((o) => o.value)).toContain('claire-roux-id'));
    expect(selecteur.value).toBe('claire-roux-id');
    expect(selecteur.selectedOptions[0]?.textContent).toBe('Claire Roux');
  });
});
