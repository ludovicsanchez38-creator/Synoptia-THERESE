/**
 * P-155 et P-138 (recette P-146, lot 3 ; acceptées, décisions du 25/09) :
 * « Marquer comme payée » imposait l'instant du clic comme date de paiement,
 * et un brouillon jamais émis passait payé sans un mot. La date réelle se
 * saisit (jamais dans le futur), la confirmation la reprend et signale un
 * brouillon.
 */
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';
import { useBillingProfileStore } from '../../stores/billingProfileStore';
import { useStatusStore } from '../../stores/statusStore';
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
    listInvoices: vi.fn().mockResolvedValue([]),
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

  it('B-1147 : le sélecteur transmet aussi la date saisie au paiement', async () => {
    updateInvoiceMock.mockResolvedValue({ ...invoice, status: 'paid' });
    rendre(invoice);
    fireEvent.change(screen.getByLabelText('Payée le'), { target: { value: '2026-06-18' } });
    fireEvent.change(await screen.findByLabelText('Statut'), { target: { value: 'paid' } });
    fireEvent.click(screen.getByRole('button', { name: 'Mettre à jour' }));
    expect(screen.getByTestId('external-action-confirmation')).toHaveTextContent('18/06/2026');
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer le changement de statut' }));
    await waitFor(() => expect(markInvoicePaidMock).toHaveBeenCalledWith('invoice-1', '2026-06-18'));
    expect(updateInvoiceMock).not.toHaveBeenCalled();
  });

  it('la confirmation dit le numéro définitif renvoyé, pas le jeton provisoire', async () => {
    useStatusStore.setState({ notifications: [] });
    markInvoicePaidMock.mockResolvedValue({ ...invoice, invoice_number: 'FACT-2026-009', status: 'paid' });
    rendre({ ...invoice, invoice_number: 'PROV-abc123', status: 'draft' });
    fireEvent.click(screen.getByRole('button', { name: 'Marquer comme payée' }));
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer le paiement' }));
    await waitFor(() => {
      const messages = useStatusStore.getState().notifications.map((n) => n.message).join(' ');
      expect(messages).toContain('La facture FACT-2026-009 est marquée payée.');
    });
    const messages = useStatusStore.getState().notifications.map((n) => n.message).join(' ');
    expect(messages).not.toContain('PROV-');
    expect(messages).not.toContain("Brouillon, numéro à l'émission");
  });

  it('P-138 : un brouillon est signalé avant de passer payé', () => {
    rendre({ ...invoice, status: 'draft' });
    fireEvent.click(screen.getByRole('button', { name: 'Marquer comme payée' }));
    expect(screen.getByTestId('external-action-confirmation')).toHaveTextContent(/brouillon/i);
  });
});

describe('B-1147 : entrées supplémentaires après correction', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useBillingProfileStore.setState({ missing: null });
    updateInvoiceMock.mockResolvedValue(invoice);
    markInvoicePaidMock.mockResolvedValue({ ...invoice, status: 'paid' });
  });

  it.each([
    ['facture', 'sent', '2024-02-29'],
    ['facture', 'overdue', '2025-12-31'],
    ['facture', 'draft', '2026-01-01'],
    ['avoir', 'sent', '2026-01-07'],
    ['avoir', 'overdue', '2026-01-13'],
    ['avoir', 'draft', '2026-02-02'],
    ['facture', 'sent', '2026-02-14'],
    ['facture', 'draft', '2026-03-08'],
    ['avoir', 'sent', '2026-04-30'],
    ['avoir', 'draft', '2026-05-19'],
  ] as const)('%s %s : date %s conservée', async (documentType, status, date) => {
    rendre({ ...invoice, document_type: documentType, status });
    fireEvent.change(screen.getByLabelText(documentType === 'avoir' ? 'Remboursé le' : 'Payée le'), { target: { value: date } });
    if (status === 'draft') {
      fireEvent.change(screen.getByDisplayValue('Accompagnement'), { target: { value: 'Atelier retouché avant paiement' } });
    }
    fireEvent.change(await screen.findByLabelText('Statut'), { target: { value: 'paid' } });
    fireEvent.click(screen.getByRole('button', { name: 'Mettre à jour' }));
    expect(screen.getByTestId('external-action-confirmation')).toHaveTextContent(date.split('-').reverse().join('/'));
    expect(markInvoicePaidMock).not.toHaveBeenCalled();
    expect(updateInvoiceMock).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer le changement de statut' }));
    await waitFor(() => expect(markInvoicePaidMock).toHaveBeenCalledWith('invoice-1', date));
    if (status === 'draft') {
      expect(updateInvoiceMock).toHaveBeenCalledWith('invoice-1', expect.objectContaining({
        status: undefined,
        lines: [expect.objectContaining({ description: 'Atelier retouché avant paiement' })],
      }));
      expect(updateInvoiceMock.mock.invocationCallOrder[0]).toBeLessThan(markInvoicePaidMock.mock.invocationCallOrder[0]);
    } else {
      expect(updateInvoiceMock).not.toHaveBeenCalled();
    }
  });

  it.each(['', '2999-01-01'])('refuse une date vide ou future : %s', async (date) => {
    rendre(invoice);
    fireEvent.change(screen.getByLabelText('Payée le'), { target: { value: date } });
    fireEvent.change(await screen.findByLabelText('Statut'), { target: { value: 'paid' } });
    fireEvent.click(screen.getByRole('button', { name: 'Mettre à jour' }));
    expect(screen.getByRole('alert')).toHaveTextContent('Indique une date passée ou celle d’aujourd’hui.');
    expect(markInvoicePaidMock).not.toHaveBeenCalled();
    expect(updateInvoiceMock).not.toHaveBeenCalled();
  });

  it('annuler la confirmation ne déclenche aucune écriture', async () => {
    rendre(invoice);
    fireEvent.change(await screen.findByLabelText('Statut'), { target: { value: 'paid' } });
    fireEvent.click(screen.getByRole('button', { name: 'Mettre à jour' }));
    fireEvent.click(within(screen.getByTestId('external-action-confirmation')).getByRole('button', { name: 'Annuler' }));
    expect(markInvoicePaidMock).not.toHaveBeenCalled();
    expect(updateInvoiceMock).not.toHaveBeenCalled();
  });

  it('un brouillon dont la sauvegarde échoue ne passe pas payé', async () => {
    updateInvoiceMock.mockRejectedValueOnce(new Error('Sauvegarde impossible'));
    rendre({ ...invoice, status: 'draft' });
    fireEvent.change(await screen.findByLabelText('Statut'), { target: { value: 'paid' } });
    fireEvent.click(screen.getByRole('button', { name: 'Mettre à jour' }));
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer le changement de statut' }));
    await waitFor(() => expect(useStatusStore.getState().notifications).toEqual(expect.arrayContaining([
      expect.objectContaining({ type: 'error', message: 'Sauvegarde impossible' }),
    ])));
    expect(markInvoicePaidMock).not.toHaveBeenCalled();
  });
});

describe('B-1081 B-1083 : la commande de remboursement d’un avoir', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useBillingProfileStore.setState({ missing: null });
    useStatusStore.setState({ notifications: [] });
    markInvoicePaidMock.mockResolvedValue({ ...invoice, document_type: 'avoir', invoice_number: 'AV-2026-013', status: 'paid' });
  });

  it.each(['sent', 'draft'] as const)('bouton, confirmation et succès nomment l’avoir remboursé (%s)', async (status) => {
    rendre({ ...invoice, document_type: 'avoir', invoice_number: 'AV-2026-013', status });
    fireEvent.change(screen.getByLabelText('Remboursé le'), { target: { value: '2026-07-21' } });
    fireEvent.click(screen.getByRole('button', { name: 'Marquer comme remboursé' }));
    const confirmation = screen.getByTestId('external-action-confirmation');
    expect(confirmation).toHaveTextContent('Confirmer le remboursement de l’avoir');
    expect(confirmation).toHaveTextContent('AV-2026-013');
    expect(confirmation).toHaveTextContent('Date du remboursement');
    expect(confirmation).toHaveTextContent('21/07/2026');
    expect(confirmation).toHaveTextContent('Remboursé');
    expect(confirmation).not.toHaveTextContent(/facture|payée/i);
    if (status === 'draft') expect(confirmation).toHaveTextContent(/brouillon.*jamais été émis/i);
    expect(markInvoicePaidMock).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer le remboursement' }));
    await waitFor(() => expect(markInvoicePaidMock).toHaveBeenCalledWith('invoice-1', '2026-07-21'));
    await waitFor(() => expect(useStatusStore.getState().notifications).toEqual(expect.arrayContaining([
      expect.objectContaining({ type: 'success', title: 'Avoir remboursé', message: 'L’avoir AV-2026-013 est marqué remboursé.' }),
    ])));
  });

  it('annuler la confirmation ne rembourse pas l’avoir', () => {
    rendre({ ...invoice, document_type: 'avoir' });
    fireEvent.click(screen.getByRole('button', { name: 'Marquer comme remboursé' }));
    fireEvent.click(within(screen.getByTestId('external-action-confirmation')).getByRole('button', { name: 'Annuler' }));
    expect(screen.queryByTestId('external-action-confirmation')).toBeNull();
    expect(markInvoicePaidMock).not.toHaveBeenCalled();
  });
});
