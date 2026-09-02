/**
 * B-003 : deux écrivains pour une liste, un seul suivi par l'indicateur.
 *
 * `invoices` est un état PARTAGÉ du store : le panneau l'écrit après son
 * chargement plafonné à 100, et `usePrototypeInvoiceData` l'écrit aussi
 * (`setInvoices`, `addInvoice`, `updateInvoiceInStore`). L'indicateur de
 * troncature, lui, était un `useState` LOCAL au panneau, calculé au seul
 * chargement du panneau.
 *
 * Résultat : après une écriture du second écrivain, l'en-tête affichait
 * « 1+ document » et gardait le bandeau « Liste incomplète : seuls les 100
 * documents les plus récents » au-dessus d'une liste d'un seul élément. Un
 * avertissement qui décrit des données disparues est pire que pas
 * d'avertissement.
 *
 * L'invariant que fixe ce test : l'indicateur décrit la liste AFFICHÉE, quel
 * que soit l'écrivain qui l'a remplie.
 */
import { act, render, screen, waitFor } from '@testing-library/react';
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

const facture = (rang: number): Invoice => ({
  id: `inv-${rang}`,
  invoice_number: `FAC-${String(rang).padStart(3, '0')}`,
  contact_id: 'contact-1',
  document_type: 'facture',
  tva_applicable: true,
  currency: 'EUR',
  issue_date: '2026-03-14T00:00:00Z',
  due_date: '2026-03-31T00:00:00Z',
  status: 'draft',
  subtotal_ht: 100,
  total_tax: 20,
  total_ttc: 120,
  notes: null,
  payment_terms: null,
  payment_method: null,
  late_penalty_rate: null,
  legal_mentions: null,
  converted_from_id: null,
  validite_jours: null,
  payment_date: null,
  created_at: '2026-03-14T00:00:00Z',
  updated_at: '2026-03-14T00:00:00Z',
  lines: [],
});

const CENT = Array.from({ length: 100 }, (_, i) => facture(i + 1));

describe('B-003 : la troncature suit la liste affichée, pas le dernier chargement du panneau', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockListInvoices.mockResolvedValue(CENT);
    useInvoiceStore.setState({
      invoices: [],
      currentInvoiceId: null,
      filters: { status: 'all' },
      isInvoicePanelOpen: true,
      draftInvoice: null,
    });
  });

  it('une écriture du second écrivain retire le « + » et le bandeau', async () => {
    render(<InvoicesPanel standalone />);

    // Le chargement du panneau atteint le plafond : l'avertissement est juste.
    // Le compteur est fait de plusieurs nœuds texte dans un même <p> : on garde
    // l'élément, React réutilise le nœud d'un rendu à l'autre.
    const compteur = await screen.findByText('100+ documents');
    expect(screen.getByText(/Liste incomplète/)).toBeInTheDocument();

    // Second écrivain : le hook du parcours prototype remplit le même store
    // avec sa propre liste, non tronquée.
    act(() => {
      useInvoiceStore.getState().setInvoices([facture(1)]);
    });

    await waitFor(() => {
      expect(compteur.textContent).toBe('1 document');
    });
    expect(screen.queryByText(/Liste incomplète/)).not.toBeInTheDocument();
    // 20 s : cf InvoicesPanel.chargementEchoue.test.tsx, même fixture de 100.
  }, 20000);

  it('une liste sous le plafond n’affiche aucun avertissement', async () => {
    mockListInvoices.mockResolvedValue([facture(1), facture(2)]);

    render(<InvoicesPanel standalone />);

    expect(await screen.findByText('2 documents')).toBeInTheDocument();
    expect(screen.queryByText(/Liste incomplète/)).not.toBeInTheDocument();
  });
});
