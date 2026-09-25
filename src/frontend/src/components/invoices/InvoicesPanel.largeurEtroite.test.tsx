/**
 * B-1387 (personas Nathalie et Zoé, cycle 13) : à 125 % (fenêtre de 1 440 px)
 * ou à 800 px, le tableau des devis et factures débordait de son cadre
 * (1 159 px pour 686) : « Supprimer » hors cadre, montant coupé (« 1 440, »),
 * barre de défilement au bas du tableau, sous la ligne de flottaison.
 *
 * Le montant et les actions forment désormais la dernière colonne, collée à
 * droite du cadre : ils restent visibles quand le reste défile. La sous-ligne
 * de l'échéance peut passer à la ligne (seule la date reste insécable).
 * jsdom ne mesure pas : la structure est vérifiée ici, la mesure a été faite
 * dans Chrome (800 px).
 */
import { render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useInvoiceStore } from '../../stores/invoiceStore';

const mockListInvoices = vi.fn();
vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, listInvoices: (...a: unknown[]) => mockListInvoices(...a) };
});
vi.mock('./InvoiceForm', () => ({ InvoiceForm: () => <div data-testid="invoice-form" /> }));

import { InvoicesPanel } from './InvoicesPanel';

const devis = {
  id: 'inv-1', invoice_number: 'DEV-2026-004', contact_id: 'c1', contact_name: 'Zoé Clavier',
  document_type: 'devis', currency: 'EUR', issue_date: '2026-09-25T00:00:00Z', due_date: '2026-10-25T00:00:00Z',
  status: 'draft', subtotal_ht: 300, total_tax: 60, total_ttc: 360, notes: null, payment_date: null,
  validite_jours: 30, created_at: '2026-09-25T00:00:00Z', updated_at: '2026-09-25T00:00:00Z', lines: [],
};

describe('B-1387 : montant et actions restent dans le cadre', () => {
  beforeEach(() => {
    mockListInvoices.mockResolvedValue([devis]);
    useInvoiceStore.setState({ invoices: [], currentInvoiceId: null, filters: { status: 'all' }, isInvoicePanelOpen: true, draftInvoice: null });
  });

  it('le montant et les boutons partagent la dernière colonne, collée à droite', async () => {
    render(<InvoicesPanel standalone />);
    const ligne = await screen.findByTestId('invoice-item');
    const cellules = within(ligne).getAllByRole('cell');
    const derniere = cellules[cellules.length - 1];

    expect(derniere).toHaveTextContent(/360,00/);
    expect(within(derniere).getByRole('button', { name: 'Supprimer' })).toBeInTheDocument();
    expect(within(derniere).getByRole('button', { name: /PDF/ })).toBeInTheDocument();
    expect(derniere.className).toMatch(/\bsticky\b/);
    expect(derniere.className).toMatch(/\bright-0\b/);

    const entetes = screen.getAllByRole('columnheader');
    expect(entetes[entetes.length - 1]).toHaveTextContent('Montant TTC');
    expect(entetes[entetes.length - 1].className).toMatch(/\bsticky\b/);
  });

  it('seule la date de l’échéance est insécable', async () => {
    render(<InvoicesPanel standalone />);
    const ligne = await screen.findByTestId('invoice-item');
    const echeance = within(ligne).getAllByRole('cell')[4];

    expect(echeance.className).not.toMatch(/whitespace-nowrap/);
    expect(echeance.querySelector('.whitespace-nowrap')).not.toBeNull();
  });
});
