/**
 * B-646 (persona Nadia, c4) : « Devis et factures » vide, avec Type = Tout et
 * Statut = Toutes (les valeurs par défaut), affichait « Aucun document ne
 * correspond à ce filtre » et « Réinitialiser les filtres », qui ne peut rien
 * changer. Sans filtre effectif, l'état vide dit « rien encore » et propose
 * de créer.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useInvoiceStore } from '../../stores/invoiceStore';

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...reel, listInvoices: vi.fn().mockResolvedValue([]), deleteInvoice: vi.fn(), generateInvoicePDF: vi.fn(), sendInvoiceByEmail: vi.fn() };
});
vi.mock('./InvoiceForm', () => ({ InvoiceForm: () => <div data-testid="invoice-form" /> }));

import { InvoicesPanel } from './InvoicesPanel';

describe('B-646 : état vide sans filtre effectif', () => {
  beforeEach(() => {
    useInvoiceStore.setState({ invoices: [], isLoading: false, error: null, filters: { status: 'all' } } as never);
  });

  it('avec Statut = Toutes, propose de créer une facture au lieu d’accuser un filtre', async () => {
    render(<InvoicesPanel standalone />);
    expect(await screen.findByText('Aucune facture')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Créer une facture/ })).toBeInTheDocument();
    expect(screen.queryByText(/ne correspond à ce filtre/)).toBeNull();
  });

  it('avec un vrai filtre de statut, garde le message de filtre', async () => {
    useInvoiceStore.setState({ filters: { status: 'paid' } } as never);
    render(<InvoicesPanel standalone />);
    expect(await screen.findByText(/ne correspond à ce filtre/)).toBeInTheDocument();
  });
});
