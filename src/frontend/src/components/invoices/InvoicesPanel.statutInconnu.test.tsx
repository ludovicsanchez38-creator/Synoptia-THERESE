/**
 * B-010 : un statut hors catalogue emportait toute l'application.
 *
 * `const StatusIcon = STATUS_CONFIG[invoice.status].icon;` lisait la table
 * sans optionnel, alors que les trois lectures suivantes du MÊME objet
 * utilisent déjà `?.` avec un repli. Une facture au statut inconnu levait
 * donc `TypeError: Cannot read properties of undefined (reading 'icon')`,
 * l'erreur remontait jusqu'au GlobalErrorBoundary, et l'écran entier était
 * remplacé par « Oups ! ». Ce n'est pas la ligne qui tombait, c'est l'app.
 *
 * Atteignable en vrai : le commentaire du routeur (invoices.py) rappelle que
 * la porte générique acceptait, avant la 0.55, des statuts inventés par un
 * modèle (« partiellement paye », « en attente »). Le garde serveur posé
 * ensuite ne répare pas les lignes déjà écrites en base.
 */
import { render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useInvoiceStore } from '../../stores/invoiceStore';
import type { Invoice } from '../../services/api';

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

import { InvoicesPanel } from './InvoicesPanel';

const facture = (id: string, numero: string, statut: string): Invoice =>
  ({
    id,
    invoice_number: numero,
    contact_id: 'contact-1',
    currency: 'EUR',
    issue_date: '2026-03-14T00:00:00Z',
    due_date: '2026-03-31T00:00:00Z',
    status: statut,
    subtotal_ht: 100,
    total_tax: 20,
    total_ttc: 120,
    notes: null,
    payment_date: null,
    created_at: '2026-03-14T00:00:00Z',
    updated_at: '2026-03-14T00:00:00Z',
    lines: [],
  }) as unknown as Invoice;

describe('B-010 : un statut hors catalogue n’empêche pas le rendu', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => {});
    mockListInvoices.mockResolvedValue([
      facture('inv-1', 'FAC-001', 'draft'),
      facture('inv-2', 'FAC-002', 'partiellement_paye'),
    ]);
    useInvoiceStore.setState({
      invoices: [],
      listeTronquee: false,
      currentInvoiceId: null,
      filters: { status: 'all' },
      isInvoicePanelOpen: true,
      draftInvoice: null,
    });
  });

  it('les deux lignes s’affichent, la valeur brute servant de libellé', async () => {
    render(<InvoicesPanel standalone />);

    await waitFor(() => {
      expect(screen.getAllByTestId('invoice-item')).toHaveLength(2);
    });

    const [saine, inconnue] = screen.getAllByTestId('invoice-item');

    // La ligne saine est intacte... (« Brouillon » est aussi un bouton de
    // filtre, d'où la recherche dans la ligne et non dans tout l'écran)
    expect(within(saine).getByText('FAC-001')).toBeInTheDocument();
    expect(within(saine).getByText('Brouillon')).toBeInTheDocument();

    // ... et l'inconnue s'affiche avec ce que la base contient, faute de mieux.
    expect(within(inconnue).getByText('FAC-002')).toBeInTheDocument();
    expect(within(inconnue).getByText('partiellement_paye')).toBeInTheDocument();
  });
});
