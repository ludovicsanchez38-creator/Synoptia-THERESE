/**
 * B-207 : le refus du serveur n'arrivait pas à l'écran, moitié suppression.
 *
 * La moitié « PDF » de ce bug est déjà fermée (B-218, cf
 * `InvoicesPanel.causePdf.test.tsx`). La cause racine relevée à la
 * reproduction nommait un second site, jamais touché : le `catch` de
 * `confirmDeleteInvoice`, qui remplaçait le message du serveur par
 * « Impossible de supprimer la facture ». Le serveur dit pourquoi il refuse -
 * la frontière d'erreurs 0.48 lui impose une phrase française et lisible - et
 * `services/api/invoices.ts` la porte fidèlement dans l'`Error`. Elle
 * n'existait plus qu'en console, où l'utilisatrice ne regarde pas.
 *
 * Le test lit la notification affichée, pas l'appel d'API : c'est l'écran qui
 * était fautif, pas le client HTTP.
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useInvoiceStore } from '../../stores/invoiceStore';
import { useStatusStore } from '../../stores/statusStore';
import type { Invoice } from '../../services/api';

const mockListInvoices = vi.fn();
const mockDeleteInvoice = vi.fn();

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    listInvoices: (...args: unknown[]) => mockListInvoices(...args),
    deleteInvoice: (...args: unknown[]) => mockDeleteInvoice(...args),
    generateInvoicePDF: vi.fn(),
    sendInvoiceByEmail: vi.fn(),
  };
});

vi.mock('./InvoiceForm', () => ({ InvoiceForm: () => <div data-testid="invoice-form" /> }));

import { InvoicesPanel } from './InvoicesPanel';

/** Message verbatim du gestionnaire 429 de `main.py` : il traverse
 *  `d.message` et arrive dans `error.message`. */
const CAUSE_SERVEUR = 'Trop de requêtes, patiente un instant.';

const facture: Invoice = {
  id: 'inv-1',
  invoice_number: 'FAC-001',
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
};

async function demanderLaSuppression() {
  render(<InvoicesPanel standalone />);
  await screen.findByText('FAC-001');
  fireEvent.click(screen.getByTitle('Supprimer'));
  const dialogue = await screen.findByRole('dialog', { name: 'Confirmer la suppression' });
  fireEvent.click(within(dialogue).getByRole('button', { name: 'Supprimer' }));
}

describe('B-207 : le refus du serveur arrive à l’écran, aussi à la suppression', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    mockListInvoices.mockResolvedValue([facture]);
    useInvoiceStore.setState({
      invoices: [],
      currentInvoiceId: null,
      filters: { status: 'all' },
      isInvoicePanelOpen: true,
      draftInvoice: null,
    });
    useStatusStore.setState({ notifications: [] });
  });

  it('affiche le message du serveur, pas le générique', async () => {
    mockDeleteInvoice.mockRejectedValue(new Error(CAUSE_SERVEUR));

    await demanderLaSuppression();

    await waitFor(() => {
      expect(useStatusStore.getState().notifications).toHaveLength(1);
    });
    const notification = useStatusStore.getState().notifications[0];
    expect(notification.type).toBe('error');
    expect(notification.message).toBe(CAUSE_SERVEUR);
    expect(notification.message).not.toBe('Impossible de supprimer la facture');
  });

  it('garde un message lisible quand le serveur n’en donne aucun', async () => {
    // Une coupure réseau ne rejette pas toujours avec une phrase utile : la
    // notification ne doit pas devenir vide en voulant devenir précise.
    mockDeleteInvoice.mockRejectedValue(new Error(''));

    await demanderLaSuppression();

    await waitFor(() => {
      expect(useStatusStore.getState().notifications).toHaveLength(1);
    });
    expect(useStatusStore.getState().notifications[0].message).toBe(
      'Impossible de supprimer la facture',
    );
  });
});
