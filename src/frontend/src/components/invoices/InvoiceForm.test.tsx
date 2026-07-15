import { render, screen, waitFor, act, fireEvent } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';
import { useBillingProfileStore } from '../../stores/billingProfileStore';
import { useStatusStore } from '../../stores/statusStore';
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

describe('InvoiceForm décimaux', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    createInvoiceMock.mockResolvedValue({ id: 'inv-1' });
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [] });
    useBillingProfileStore.setState({ missing: null });
  });

  it('accepte le point du pavé numérique dans le prix HT', async () => {
    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);

    const priceInput = await screen.findByLabelText('Prix HT ligne 1');
    fireEvent.change(priceInput, { target: { value: '12' } });
    fireEvent.change(priceInput, { target: { value: '12.' } });
    fireEvent.change(priceInput, { target: { value: '12.5' } });

    expect(priceInput).toHaveValue('12.5');
    expect(screen.getAllByText(/12.50 €/i)).toHaveLength(2);
  });

  it('accepte aussi la virgule dans le prix HT', async () => {
    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);

    const priceInput = await screen.findByLabelText('Prix HT ligne 1');
    fireEvent.change(priceInput, { target: { value: '12' } });
    fireEvent.change(priceInput, { target: { value: '12,' } });
    fireEvent.change(priceInput, { target: { value: '12,5' } });

    expect(priceInput).toHaveValue('12,5');
    expect(screen.getAllByText(/12.50 €/i)).toHaveLength(2);
  });

  it('bloque les valeurs vides ou invalides à la soumission', async () => {
    window.alert = vi.fn();
    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);

    fireEvent.change(await screen.findByLabelText(/Client/i), { target: { value: 'contact-1' } });
    fireEvent.change(screen.getByPlaceholderText('Description'), { target: { value: 'Prestation' } });
    fireEvent.change(screen.getByLabelText('Quantité ligne 1'), { target: { value: '' } });

    fireEvent.click(screen.getByRole('button', { name: /Créer/i }));

    expect(createInvoiceMock).not.toHaveBeenCalled();
    expect(window.alert).toHaveBeenCalled();
  });
});

describe('InvoiceForm - BUG-132 validation description de ligne', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    createInvoiceMock.mockResolvedValue({ id: 'inv-1' });
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [] });
    useBillingProfileStore.setState({ missing: null });
  });

  it('une ligne par défaut sans description est bloquée avec un message ciblé, pas « ajoute une ligne »', async () => {
    const notifSpy = vi.fn();
    useStatusStore.setState({ addNotification: notifSpy });

    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);

    // Contact requis (sinon on bloque avant la ligne).
    fireEvent.change(await screen.findByLabelText(/Client/i), { target: { value: 'contact-1' } });
    // La ligne par défaut existe (quantité 1) mais sa description est vide.
    fireEvent.click(screen.getByRole('button', { name: /Créer/i }));

    expect(createInvoiceMock).not.toHaveBeenCalled();
    const messages = notifSpy.mock.calls.map((c) => (c[0]?.message as string) ?? '');
    expect(messages.some((m) => /description/i.test(m))).toBe(true);
    expect(messages.some((m) => /ajoute au moins une ligne/i.test(m))).toBe(false);
  });

  it('accepte la soumission une fois la description renseignée', async () => {
    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);

    fireEvent.change(await screen.findByLabelText(/Client/i), { target: { value: 'contact-1' } });
    fireEvent.change(screen.getByPlaceholderText('Description'), { target: { value: 'Prestation conseil' } });
    fireEvent.change(screen.getByLabelText('Prix HT ligne 1'), { target: { value: '100' } });

    fireEvent.click(screen.getByRole('button', { name: /Créer/i }));

    await waitFor(() => expect(createInvoiceMock).toHaveBeenCalled());
  });
});

describe('InvoiceForm - garde-fou profil émetteur (P0-PROD-2)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    createInvoiceMock.mockResolvedValue({ id: 'inv-1' });
    useBillingProfileStore.setState({ missing: null });
  });

  it('affiche l\'avertissement quand le profil émetteur est incomplet', async () => {
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: false, missing: ['SIRET', 'adresse'] });

    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);

    expect(await screen.findByText(/Profil émetteur incomplet/i)).toBeInTheDocument();
  });

  it('fait disparaître l\'avertissement quand le profil est complété via les Réglages, sans remonter le formulaire', async () => {
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: false, missing: ['SIRET'] });

    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);

    expect(await screen.findByText(/Profil émetteur incomplet/i)).toBeInTheDocument();

    // Simule la sauvegarde du profil dans Réglages (autre modale, ce composant
    // reste monté) : SettingsModal appelle useBillingProfileStore.getState().refresh()
    // après un save réussi.
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [] });
    await act(async () => {
      await useBillingProfileStore.getState().refresh();
    });

    await waitFor(() => {
      expect(screen.queryByText(/Profil émetteur incomplet/i)).not.toBeInTheDocument();
    });
  });
});

describe('InvoiceForm - confirmations métier 0.40', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [] });
    useBillingProfileStore.setState({ missing: null });
    markInvoicePaidMock.mockResolvedValue({ ...invoice, status: 'paid' });
    updateInvoiceMock.mockResolvedValue(invoice);
  });

  it('attend la confirmation avant de marquer une facture payée', async () => {
    render(
      <PrototypeExternalActionConfirmationProvider>
        <InvoiceForm invoice={invoice} onClose={vi.fn()} onSave={vi.fn()} />
      </PrototypeExternalActionConfirmationProvider>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Marquer comme payée' }));

    const preview = screen.getByTestId('external-action-confirmation');
    expect(preview).toHaveTextContent('FAC-2026-001');
    expect(preview).toHaveTextContent('120.00 €');
    expect(markInvoicePaidMock).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Confirmer le paiement' }));

    await waitFor(() => expect(markInvoicePaidMock).toHaveBeenCalledWith('invoice-1'));
  });

  it.each([
    ['Accepter', 'Confirmer l’acceptation', 'accepted'],
    ['Refuser', 'Confirmer le refus', 'refused'],
  ] as const)('attend la confirmation avant l’action devis « %s »', async (buttonLabel, confirmLabel, status) => {
    const devis = { ...invoice, invoice_number: 'DEV-2026-001', document_type: 'devis' as const };
    updateDevisStatusMock.mockResolvedValue({ ...devis, status });
    render(
      <PrototypeExternalActionConfirmationProvider>
        <InvoiceForm invoice={devis} onClose={vi.fn()} onSave={vi.fn()} />
      </PrototypeExternalActionConfirmationProvider>,
    );

    fireEvent.click(screen.getByRole('button', { name: buttonLabel }));

    expect(screen.getByTestId('external-action-confirmation')).toHaveTextContent('DEV-2026-001');
    expect(updateDevisStatusMock).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: confirmLabel }));

    await waitFor(() => expect(updateDevisStatusMock).toHaveBeenCalledWith('invoice-1', status));
  });

  it('ne permet pas de contourner la confirmation via le sélecteur de statut', async () => {
    const devis = { ...invoice, invoice_number: 'DEV-2026-002', document_type: 'devis' as const };
    updateInvoiceMock.mockResolvedValue({ ...devis, status: 'accepted' });
    render(
      <PrototypeExternalActionConfirmationProvider>
        <InvoiceForm invoice={devis} onClose={vi.fn()} onSave={vi.fn()} />
      </PrototypeExternalActionConfirmationProvider>,
    );

    fireEvent.change(await screen.findByLabelText('Statut'), { target: { value: 'accepted' } });
    fireEvent.click(screen.getByRole('button', { name: 'Mettre à jour' }));

    expect(screen.getByTestId('external-action-confirmation')).toHaveTextContent('Nouveau statutAccepté');
    expect(updateInvoiceMock).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Confirmer le changement de statut' }));

    await waitFor(() => {
      expect(updateInvoiceMock).toHaveBeenCalledWith(
        'invoice-1',
        expect.objectContaining({ status: 'accepted' }),
      );
    });
  });
});
