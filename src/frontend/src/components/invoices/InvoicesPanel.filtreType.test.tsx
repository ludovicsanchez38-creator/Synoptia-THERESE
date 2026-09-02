/**
 * B-005, second site : le panneau produisait lui-même la paire impossible.
 *
 * Factures > Payée > Devis laissait `status: 'paid'` collé à
 * `document_type: 'devis'` — « payée » n'est pas un statut de devis. La rangée
 * de statuts n'est construite qu'à partir du type : aucun bouton ne paraissait
 * sélectionné, la liste revenait vide, et rien à l'écran ne l'expliquait. La
 * paire partait ensuite dans le stockage, donc au redémarrage aussi.
 *
 * Assainir la seule rehydratation aurait laissé ce chemin ouvert : l'écran
 * serait resté fautif tant que personne ne redémarre.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useInvoiceStore } from '../../stores/invoiceStore';
import { InvoicesPanel } from './InvoicesPanel';

const mockListInvoices = vi.fn();

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    listInvoices: (...args: unknown[]) => mockListInvoices(...args),
    deleteInvoice: vi.fn(),
    generateInvoicePDF: vi.fn(),
    sendInvoiceByEmail: vi.fn(),
  };
});

vi.mock('./InvoiceForm', () => ({
  InvoiceForm: () => <div data-testid="invoice-form" />,
}));

describe('B-005 : changer de type de document assainit le statut', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockListInvoices.mockResolvedValue([]);
    useInvoiceStore.setState({ invoices: [], filters: { status: 'all' } });
  });

  it("« Payée » ne survit pas au passage sur les devis", async () => {
    render(<InvoicesPanel standalone />);
    await waitFor(() => expect(mockListInvoices).toHaveBeenCalled());

    fireEvent.click(screen.getByRole('button', { name: 'Factures' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Payée' }));
    expect(useInvoiceStore.getState().filters.status).toBe('paid');

    fireEvent.click(screen.getByRole('button', { name: 'Devis' }));

    expect(useInvoiceStore.getState().filters.status).toBe('all');
    expect(useInvoiceStore.getState().filters.document_type).toBe('devis');
  });

  it("un statut valable des deux côtés traverse le changement de type", async () => {
    render(<InvoicesPanel standalone />);
    await waitFor(() => expect(mockListInvoices).toHaveBeenCalled());

    fireEvent.click(screen.getByRole('button', { name: 'Factures' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Brouillon' }));
    fireEvent.click(screen.getByRole('button', { name: 'Devis' }));

    expect(useInvoiceStore.getState().filters.status).toBe('draft');
  });

  it('la rangée de statuts propose toujours un bouton sélectionné', async () => {
    render(<InvoicesPanel standalone />);
    await waitFor(() => expect(mockListInvoices).toHaveBeenCalled());

    fireEvent.click(screen.getByRole('button', { name: 'Factures' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Payée' }));
    fireEvent.click(screen.getByRole('button', { name: 'Devis' }));

    const statutCourant = useInvoiceStore.getState().filters.status;
    const proposes = ['Toutes', 'Brouillon', 'Envoyée', 'Accepté', 'Refusé', 'Expiré', 'Converti'];
    expect(statutCourant).toBe('all');
    for (const libelle of proposes) {
      expect(screen.getByRole('button', { name: libelle })).toBeInTheDocument();
    }
  });
});
