/**
 * B-208 : ouvrir un devis pour le modifier n'existait qu'à la souris.
 *
 * La ligne de la liste portait son seul `onClick` d'ouverture sur le conteneur
 * animé, un `<div>` sans rôle, sans `tabIndex` et sans gestionnaire clavier :
 * la tabulation ne l'atteignait pas et rien n'annonçait qu'il s'agissait d'une
 * commande. Les deux boutons visibles de la ligne mènent au PDF et à la
 * suppression, jamais à l'édition.
 *
 * Le test demande une commande NOMMÉE par le client (ou par la référence quand
 * le client manque) et vérifie qu'elle ouvre le formulaire. Il ne passe pas par
 * un `keyDown` : un vrai `<button>` transforme lui-même Entrée et Espace en
 * clic, ce que jsdom ne simule pas ; c'est justement la garantie qu'on veut.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useInvoiceStore } from '../../stores/invoiceStore';
import { useStatusStore } from '../../stores/statusStore';

const mockListInvoices = vi.fn();

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    listInvoices: (...args: unknown[]) => mockListInvoices(...args),
    generateInvoicePDF: vi.fn(),
    deleteInvoice: vi.fn(),
    sendInvoiceByEmail: vi.fn(),
  };
});

vi.mock('./InvoiceForm', () => ({
  InvoiceForm: ({ invoice }: { invoice?: { invoice_number: string } | null }) => (
    <div data-testid="invoice-form">{invoice ? invoice.invoice_number : 'nouveau'}</div>
  ),
}));

import { InvoicesPanel } from './InvoicesPanel';

const devis = {
  id: 'devis-1',
  invoice_number: 'DEV-2026-001',
  contact_id: 'contact-1',
  contact_name: 'Sophie Garcia',
  currency: 'EUR',
  document_type: 'devis' as const,
  issue_date: '2026-03-14T00:00:00Z',
  due_date: '2026-03-31T00:00:00Z',
  status: 'draft' as const,
  subtotal_ht: 100,
  total_tax: 20,
  total_ttc: 120,
  notes: null,
  payment_date: null,
  created_at: '2026-03-14T00:00:00Z',
  updated_at: '2026-03-14T00:00:00Z',
  lines: [],
};

const sansClient = { ...devis, id: 'devis-2', invoice_number: 'DEV-2026-002', contact_name: null };

describe('B-208 : la carte d’un document est une commande atteignable au clavier', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useInvoiceStore.setState({
      invoices: [],
      currentInvoiceId: null,
      filters: { status: 'all' },
      isInvoicePanelOpen: true,
      draftInvoice: null,
    });
    useStatusStore.setState({ notifications: [] });
  });

  it('expose une commande nommée par le client, qui ouvre le formulaire', async () => {
    mockListInvoices.mockResolvedValue([devis]);
    render(<InvoicesPanel standalone />);

    const commande = await screen.findByRole('button', { name: /Sophie Garcia/ });
    expect(commande).toBeInTheDocument();

    fireEvent.click(commande);

    expect(await screen.findByTestId('invoice-form')).toHaveTextContent('DEV-2026-001');
  });

  it('retombe sur la référence pour nommer la commande quand le client manque', async () => {
    mockListInvoices.mockResolvedValue([sansClient]);
    render(<InvoicesPanel standalone />);

    const commande = await screen.findByRole('button', { name: /DEV-2026-002/ });
    fireEvent.click(commande);

    expect(await screen.findByTestId('invoice-form')).toHaveTextContent('DEV-2026-002');
  });

  it('ouvrir le PDF depuis la ligne n’ouvre pas aussi le formulaire', async () => {
    // Garde anti-régression : rendre la ligne ENTIÈRE cliquable au clavier
    // ferait remonter Entrée depuis « Supprimer » ou « Générer le PDF »
    // jusqu'à l'édition. La commande d'ouverture doit rester distincte.
    mockListInvoices.mockResolvedValue([devis]);
    render(<InvoicesPanel standalone />);

    await screen.findByRole('button', { name: /Sophie Garcia/ });
    fireEvent.click(screen.getByTitle('Générer et ouvrir le PDF'));

    expect(screen.queryByTestId('invoice-form')).not.toBeInTheDocument();
  });
});
