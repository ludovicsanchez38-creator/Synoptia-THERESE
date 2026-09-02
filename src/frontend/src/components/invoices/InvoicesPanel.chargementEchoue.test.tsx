/**
 * B-009 : après un chargement tronqué puis un échec, trois messages
 * contradictoires à l'écran.
 *
 * Mesuré au navigateur : le compteur disait « 0+ document », un bandeau
 * role=alert affirmait que les 100 documents les plus récents étaient
 * affichés, et un second role=alert disait que le chargement était
 * impossible. Le « 0 » et le « + » venaient de deux sources qui ne se
 * parlaient pas : le drapeau de troncature du chargement précédent, jamais
 * remis à zéro, et une liste périmée refiltrée sur le nouveau statut.
 *
 * Un échec efface les affirmations du chargement précédent : il ne reste
 * qu'un seul état, celui de l'échec.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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

describe('B-009 : un échec de rechargement efface le chargement précédent', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Le composant journalise l'échec : on ne veut pas de bruit dans la sortie.
    vi.spyOn(console, 'error').mockImplementation(() => {});
    mockListInvoices.mockResolvedValue(CENT);
    useInvoiceStore.setState({
      invoices: [],
      currentInvoiceId: null,
      filters: { status: 'all' },
      isInvoicePanelOpen: true,
      draftInvoice: null,
    });
  });

  it('l’écran ne garde ni le bandeau de troncature ni le compteur périmé', async () => {
    render(<InvoicesPanel standalone />);

    const compteur = await screen.findByText('100+ documents');
    expect(screen.getByText(/Liste incomplète/)).toBeInTheDocument();

    // Le filtre change une dépendance de l'effet SANS démonter le panneau :
    // c'est le geste qui a produit les trois messages.
    mockListInvoices.mockRejectedValue(new Error('500'));
    fireEvent.click(screen.getByRole('button', { name: 'Payée' }));

    expect(
      await screen.findByText(/Impossible de charger les factures/),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(compteur.textContent).toBe('0 document');
    });
    expect(screen.queryByText(/Liste incomplète/)).not.toBeInTheDocument();

    // Un seul état affirmé : l'échec.
    const alertes = screen.getAllByRole('alert').map((n) => n.textContent ?? '');
    expect(alertes.filter((t) => /Liste incomplète/.test(t))).toEqual([]);
    // 20 s : 100 lignes framer-motion en jsdom dépassent parfois les 5 s par
    // défaut quand plusieurs fichiers de test tournent en parallèle.
  }, 20000);
});
