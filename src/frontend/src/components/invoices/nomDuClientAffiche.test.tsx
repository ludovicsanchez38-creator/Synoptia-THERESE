/**
 * B4 — le nom du client doit être À L'ÉCRAN, pas seulement dans le JSON.
 *
 * Campagne dix personas, finding F5 de l'artisan : « On voit DEV-2026-001,
 * badge Devis, Brouillon, dates, montant. Pas le client. Je retiens Moreau. »
 *
 * Premier jet : j'ai ajouté `contact_name` à l'API et au brief… et aucun écran
 * ne le lisait. Verdict de la relecture : « Un champ JSON que l'UI n'affiche
 * pas, c'est POST qui jetait l'adresse : même geste. » Le finding était intact.
 *
 * B-018 : les trois derniers tests de ce fichier prétendaient fermer la porte
 * en lisant le TEXTE SOURCE des fichiers et en y cherchant `contact_name`. Ils
 * restaient verts sur un écran qui n'affichait plus rien du client : une
 * déclaration de type, un import mort ou une variable inutilisée leur
 * suffisait. Ils sont remplacés par un rendu réel, qui regarde ce qui est
 * effectivement écrit à l'écran. Le typage des jeux d'essai ci-dessous tient
 * l'autre moitié de la promesse : si `Invoice` perdait `contact_name`, tsc
 * refuserait ce fichier.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { buildTodayAttentionItems } from '../prototype/prototypeReadModels';
import type { Invoice } from '../../services/api';
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

vi.mock('./InvoiceForm', () => ({ InvoiceForm: () => <div data-testid="invoice-form" /> }));

import { InvoicesPanel } from './InvoicesPanel';

const facture: Invoice = {
  id: 'inv-1',
  invoice_number: 'FACT-2026-001',
  contact_id: 'c1',
  contact_name: 'Sophie Garcia',
  document_type: 'facture',
  tva_applicable: true,
  currency: 'EUR',
  issue_date: '2026-07-01T00:00:00Z',
  due_date: '2026-07-15T00:00:00Z',
  status: 'overdue',
  subtotal_ht: 165,
  total_tax: 33,
  total_ttc: 198,
  notes: null,
  payment_terms: null,
  payment_method: null,
  late_penalty_rate: null,
  legal_mentions: null,
  converted_from_id: null,
  validite_jours: null,
  payment_date: null,
  created_at: '2026-07-01T00:00:00Z',
  updated_at: '2026-07-01T00:00:00Z',
  lines: [],
};

describe('B4 — l’écran nomme le client', () => {
  it('le brief du jour titre avec le client, pas la référence', () => {
    const items = buildTodayAttentionItems({
      date: '2026-08-28',
      events: [],
      urgent_tasks: [],
      due_follow_ups: [],
      stale_prospects: [],
      summary: {},
      overdue_invoices: [
        {
          id: 'inv-1',
          invoice_number: 'FACT-2026-001',
          contact_id: 'c1',
          contact_name: 'Sophie Garcia',
          total_ttc: 198,
          currency: 'EUR',
          due_date: '2026-07-15',
          status: 'overdue',
        },
      ],
    } as never);

    const facture = items.find((i) => i.kind === 'invoice');
    expect(facture).toBeDefined();
    expect(facture!.title).toContain('Garcia');
  });

  it('retombe sur la référence quand le client est inconnu', () => {
    const items = buildTodayAttentionItems({
      date: '2026-08-28',
      events: [],
      urgent_tasks: [],
      due_follow_ups: [],
      stale_prospects: [],
      summary: {},
      overdue_invoices: [
        {
          id: 'inv-2',
          invoice_number: 'FACT-2026-002',
          contact_id: 'c2',
          contact_name: null,
          total_ttc: 100,
          currency: 'EUR',
          due_date: null,
          status: 'overdue',
        },
      ],
    } as never);

    const facture = items.find((i) => i.kind === 'invoice');
    expect(facture!.title).toContain('FACT-2026-002');
  });
});

describe('B-018 : la liste Devis et factures affiche vraiment le client', () => {
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

  it('écrit le nom du client dans la ligne du document', async () => {
    mockListInvoices.mockResolvedValue([facture]);
    render(<InvoicesPanel standalone />);

    expect(await screen.findByText(/Garcia/)).toBeInTheDocument();
  });

  it('écrit la référence quand le client est inconnu', async () => {
    mockListInvoices.mockResolvedValue([{ ...facture, id: 'inv-2', contact_name: null }]);
    render(<InvoicesPanel standalone />);

    expect(await screen.findByText('FACT-2026-001')).toBeInTheDocument();
    expect(screen.queryByText(/Garcia/)).not.toBeInTheDocument();
  });
});
