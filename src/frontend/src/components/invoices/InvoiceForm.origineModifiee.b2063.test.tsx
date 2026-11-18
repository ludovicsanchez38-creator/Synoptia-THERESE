/** B-2063 : une retouche de la facture d’origine doit être enregistrée ou confirmée avant abandon. */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';
import { useBillingProfileStore } from '../../stores/billingProfileStore';
import { type Invoice } from '../../services/api';
import { PrototypeExternalActionConfirmationProvider } from '../app/ExternalActionConfirmation';

const { mettreÀJour, rembourser } = vi.hoisted(() => ({
  mettreÀJour: vi.fn(),
  rembourser: vi.fn(),
}));

vi.mock('../../services/api', async () => {
  const api = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...api,
    listContacts: vi.fn().mockResolvedValue([
      { id: 'client-1', first_name: 'Élodie', last_name: 'Martin', email: 'elodie@example.test' },
    ]),
    listInvoices: vi.fn().mockResolvedValue([
      { id: 'facture-1', invoice_number: 'FACT-2026-001', status: 'sent', issue_date: '2026-07-01' },
      { id: 'facture-2', invoice_number: 'FACT-2026-002', status: 'sent', issue_date: '2026-07-02' },
    ]),
    getBillingProfileStatus: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
    updateInvoice: mettreÀJour,
    markInvoicePaid: rembourser,
  };
});

const avoir: Invoice = {
  id: 'avoir-1', invoice_number: 'PROV-avoir', contact_id: 'client-1',
  document_type: 'avoir', tva_applicable: true, currency: 'EUR',
  issue_date: '2026-07-01T00:00:00Z', due_date: '2026-07-31T00:00:00Z', status: 'draft',
  subtotal_ht: 100, total_tax: 20, total_ttc: 120, notes: null, payment_terms: null,
  payment_method: null, late_penalty_rate: null, legal_mentions: null, converted_from_id: 'facture-1',
  validite_jours: null, payment_date: null, created_at: '2026-07-01T08:00:00Z',
  updated_at: '2026-07-01T08:00:00Z',
  lines: [{
    id: 'ligne-1', invoice_id: 'avoir-1', description: 'Prestation corrigée',
    quantity: 1, unit_price_ht: 100, tva_rate: 20, total_ht: 100, total_ttc: 120,
  }],
};

async function changerSeulementLaFactureDOrigine() {
  const champ = await screen.findByLabelText('Facture d’origine');
  await screen.findByRole('option', { name: /FACT-2026-002/ });
  fireEvent.change(champ, { target: { value: 'facture-2' } });
  expect(champ).toHaveValue('facture-2');
}

function rendre(fermer = vi.fn()) {
  render(
    <PrototypeExternalActionConfirmationProvider>
      <InvoiceForm invoice={avoir} onClose={fermer} onSave={vi.fn()} />
    </PrototypeExternalActionConfirmationProvider>,
  );
}

describe('B-2063 : la facture d’origine compte parmi les retouches de l’avoir', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useBillingProfileStore.setState({ missing: null });
    mettreÀJour.mockResolvedValue({ ...avoir, converted_from_id: 'facture-2' });
    rembourser.mockResolvedValue({ ...avoir, status: 'paid', converted_from_id: 'facture-2' });
  });

  it('enregistre la nouvelle référence avant de marquer l’avoir comme remboursé', async () => {
    rendre();
    await changerSeulementLaFactureDOrigine();
    fireEvent.click(screen.getByRole('button', { name: 'Marquer comme remboursé' }));
    const confirmation = screen.getByTestId('external-action-confirmation');
    fireEvent.click(within(confirmation).getByRole('button', { name: 'Confirmer le remboursement' }));

    await waitFor(() => expect(rembourser).toHaveBeenCalledWith('avoir-1', expect.any(String)));
    expect(mettreÀJour).toHaveBeenCalledWith('avoir-1', expect.objectContaining({
      converted_from_id: 'facture-2',
    }));
    expect(mettreÀJour.mock.invocationCallOrder[0]).toBeLessThan(rembourser.mock.invocationCallOrder[0]);
  });

  it('demande confirmation à la fermeture après la seule modification de la référence', async () => {
    const fermer = vi.fn();
    rendre(fermer);
    await changerSeulementLaFactureDOrigine();
    fireEvent.click(screen.getByRole('button', { name: 'Fermer' }));

    expect(screen.getByText('Abandonner les modifications ?')).toBeInTheDocument();
    expect(fermer).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Abandonner' }));
    expect(fermer).toHaveBeenCalledOnce();
  });
});
