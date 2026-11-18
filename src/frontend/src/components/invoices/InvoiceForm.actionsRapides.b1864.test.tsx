/**
 * B-1864 : Marquer comme payée, Accepter, Refuser et Convertir partaient de
 * la pièce déjà enregistrée, puis fermaient le formulaire. Une retouche de
 * brouillon (prix, lignes) n'était ni confirmée ni écrite.
 *
 * « Mettre à jour » sauve déjà ces retouches avant un paiement (B-1147).
 * Les actions rapides doivent faire de même, et annoncer le montant saisi.
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';
import { useBillingProfileStore } from '../../stores/billingProfileStore';
import { useStatusStore } from '../../stores/statusStore';
import { type Invoice } from '../../services/api';
import { PrototypeExternalActionConfirmationProvider } from '../app/ExternalActionConfirmation';

const { updateInvoiceMock, markInvoicePaidMock, updateDevisStatusMock, convertDevisToInvoiceMock } = vi.hoisted(() => ({
  updateInvoiceMock: vi.fn(),
  markInvoicePaidMock: vi.fn(),
  updateDevisStatusMock: vi.fn(),
  convertDevisToInvoiceMock: vi.fn(),
}));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    listContacts: vi.fn().mockResolvedValue([
      { id: 'contact-1', first_name: 'Jean', last_name: 'Dupont', email: 'jean@example.com' },
    ]),
    listInvoices: vi.fn().mockResolvedValue([]),
    createInvoice: vi.fn(),
    updateInvoice: updateInvoiceMock,
    markInvoicePaid: markInvoicePaidMock,
    updateDevisStatus: updateDevisStatusMock,
    convertDevisToInvoice: convertDevisToInvoiceMock,
    getBillingProfileStatus: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
  };
});

const piece: Invoice = {
  id: 'invoice-1', invoice_number: 'PROV-abc', contact_id: 'contact-1',
  document_type: 'facture', tva_applicable: true, currency: 'EUR',
  issue_date: '2026-07-01T00:00:00Z', due_date: '2026-07-31T00:00:00Z', status: 'draft',
  subtotal_ht: 100, total_tax: 20, total_ttc: 120, notes: null, payment_terms: null,
  payment_method: null, late_penalty_rate: null, legal_mentions: null, converted_from_id: null,
  validite_jours: null, payment_date: null, created_at: '2026-07-01T08:00:00Z',
  updated_at: '2026-07-01T08:00:00Z',
  lines: [{
    id: 'line-1', invoice_id: 'invoice-1', description: 'Accompagnement',
    quantity: 1, unit_price_ht: 100, tva_rate: 20, total_ht: 100, total_ttc: 120,
  }],
};

function rendre(documentType: 'facture' | 'devis') {
  return render(
    <PrototypeExternalActionConfirmationProvider>
      <InvoiceForm
        invoice={{ ...piece, document_type: documentType, invoice_number: documentType === 'devis' ? 'DEV-2026-001' : piece.invoice_number }}
        onClose={vi.fn()}
        onSave={vi.fn()}
      />
    </PrototypeExternalActionConfirmationProvider>,
  );
}

async function retoucherLePrix() {
  fireEvent.change(await screen.findByLabelText('Prix HT ligne 1'), { target: { value: '250' } });
}

describe('B-1864 : une action rapide emporte les retouches du brouillon', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useBillingProfileStore.setState({ missing: null });
    useStatusStore.setState({ notifications: [] });
    updateInvoiceMock.mockResolvedValue({ ...piece, total_ttc: 300 });
    markInvoicePaidMock.mockResolvedValue({ ...piece, status: 'paid', total_ttc: 300 });
    updateDevisStatusMock.mockResolvedValue({ ...piece, document_type: 'devis', status: 'accepted' });
    convertDevisToInvoiceMock.mockResolvedValue({ ...piece, document_type: 'facture', id: 'fac-nouvelle' });
  });

  it('Marquer comme payée confirme 300,00 € et enregistre le prix avant le paiement', async () => {
    rendre('facture');
    await retoucherLePrix();
    fireEvent.click(screen.getByRole('button', { name: 'Marquer comme payée' }));
    const confirmation = screen.getByTestId('external-action-confirmation');
    expect(confirmation).toHaveTextContent('300,00');
    expect(confirmation).not.toHaveTextContent('120,00');
    fireEvent.click(within(confirmation).getByRole('button', { name: 'Confirmer le paiement' }));
    await waitFor(() => expect(markInvoicePaidMock).toHaveBeenCalledWith('invoice-1', expect.any(String)));
    expect(updateInvoiceMock).toHaveBeenCalledWith('invoice-1', expect.objectContaining({
      status: undefined,
      lines: [expect.objectContaining({ unit_price_ht: 250, description: 'Accompagnement' })],
    }));
    expect(updateInvoiceMock.mock.invocationCallOrder[0]).toBeLessThan(markInvoicePaidMock.mock.invocationCallOrder[0]);
  });

  it.each([
    ['Accepter', 'Confirmer l’acceptation', 'accepted'],
    ['Refuser', 'Confirmer le refus', 'refused'],
  ] as const)('%s confirme le montant saisi et l’enregistre avant le statut', async (bouton, confirmer, statut) => {
    rendre('devis');
    await retoucherLePrix();
    fireEvent.click(screen.getByRole('button', { name: bouton }));
    const confirmation = screen.getByTestId('external-action-confirmation');
    expect(confirmation).toHaveTextContent('300,00');
    expect(confirmation).not.toHaveTextContent('120,00');
    fireEvent.click(within(confirmation).getByRole('button', { name: confirmer }));
    await waitFor(() => expect(updateDevisStatusMock).toHaveBeenCalledWith('invoice-1', statut));
    expect(updateInvoiceMock).toHaveBeenCalledWith('invoice-1', expect.objectContaining({
      status: undefined,
      lines: [expect.objectContaining({ unit_price_ht: 250 })],
    }));
    expect(updateInvoiceMock.mock.invocationCallOrder[0]).toBeLessThan(updateDevisStatusMock.mock.invocationCallOrder[0]);
  });

  it('Convertir enregistre le prix saisi avant de créer la facture', async () => {
    rendre('devis');
    await retoucherLePrix();
    fireEvent.click(screen.getByRole('button', { name: 'Convertir en facture' }));
    const dialogue = screen.getByRole('dialog', { name: 'Confirmer la conversion' });
    fireEvent.click(within(dialogue).getByRole('button', { name: 'Convertir' }));
    await waitFor(() => expect(convertDevisToInvoiceMock).toHaveBeenCalledWith('invoice-1', expect.any(Object)));
    expect(updateInvoiceMock).toHaveBeenCalledWith('invoice-1', expect.objectContaining({
      lines: [expect.objectContaining({ unit_price_ht: 250 })],
    }));
    expect(updateInvoiceMock.mock.invocationCallOrder[0]).toBeLessThan(convertDevisToInvoiceMock.mock.invocationCallOrder[0]);
  });

  it('une sauvegarde refusée empêche de marquer payée', async () => {
    updateInvoiceMock.mockRejectedValueOnce(new Error('Sauvegarde impossible'));
    rendre('facture');
    await retoucherLePrix();
    fireEvent.click(screen.getByRole('button', { name: 'Marquer comme payée' }));
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer le paiement' }));
    await waitFor(() => expect(useStatusStore.getState().notifications).toEqual(expect.arrayContaining([
      expect.objectContaining({ type: 'error', message: 'Sauvegarde impossible' }),
    ])));
    expect(markInvoicePaidMock).not.toHaveBeenCalled();
  });

  it('une ligne vidée n’ouvre pas la confirmation de paiement', async () => {
    rendre('facture');
    fireEvent.change(await screen.findByLabelText('Description ligne 1'), { target: { value: ' ' } });
    fireEvent.click(screen.getByRole('button', { name: 'Marquer comme payée' }));
    expect(screen.queryByTestId('external-action-confirmation')).not.toBeInTheDocument();
    // La validation pose deux alertes (la ligne et le pied) : on vise le message de la ligne.
    expect(screen.getByText(/Renseigne la description de cette ligne/)).toBeInTheDocument();
    expect(markInvoicePaidMock).not.toHaveBeenCalled();
    expect(updateInvoiceMock).not.toHaveBeenCalled();
  });
});
