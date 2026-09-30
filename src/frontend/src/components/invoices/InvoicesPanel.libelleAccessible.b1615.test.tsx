/**
 * B-1615 : deux brouillons sans nom de contact ne doivent pas porter
 * le même nom accessible. Le parcours par Tab les distingue par le type,
 * la date, le montant et l'identité disponible.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { InvoicesPanel } from './InvoicesPanel';
import { useInvoiceStore } from '../../stores/invoiceStore';

const mockListInvoices = vi.fn();

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<Record<string, unknown>>('../../services/api');
  return {
    ...reel,
    listContacts: vi.fn().mockResolvedValue([]),
    listInvoices: (...args: unknown[]) => mockListInvoices(...args),
    getBillingProfileStatus: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
    deleteInvoice: vi.fn(),
    generateInvoicePDF: vi.fn(),
    sendInvoiceByEmail: vi.fn(),
  };
});

const brouillon = {
  id: 'inv-a',
  invoice_number: 'PROV-aaa',
  contact_id: 'c-1',
  contact_name: null as string | null,
  document_type: 'facture' as const,
  tva_applicable: true,
  currency: 'EUR',
  issue_date: '2026-01-07T12:00:00Z',
  due_date: '2026-02-06T12:00:00Z',
  status: 'draft' as const,
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
  created_at: '2026-01-07T12:00:00Z',
  updated_at: '2026-01-07T12:00:00Z',
  lines: [],
};

function ouvrir() {
  useInvoiceStore.setState({
    invoices: [],
    currentInvoiceId: null,
    filters: { status: 'all' },
    isInvoicePanelOpen: true,
    draftInvoice: null,
  });
  render(<InvoicesPanel standalone />);
}

describe('B-1615 : libellé accessible d’une pièce', () => {
  it('deux brouillons sans nom se distinguent par la date et le montant', async () => {
    mockListInvoices.mockResolvedValue([
      brouillon,
      {
        ...brouillon,
        id: 'inv-b',
        invoice_number: 'PROV-bbb',
        contact_name: '',
        issue_date: '2026-06-15T12:00:00Z',
        total_ttc: 80,
      },
    ]);
    ouvrir();

    const premier = await screen.findByRole('button', { name: /120,00/ });
    const second = screen.getByRole('button', { name: /80,00/ });
    for (const bouton of [premier, second]) {
      expect(bouton).toHaveAccessibleName(/Facture/);
      expect(bouton).toHaveAccessibleName(/Brouillon, numéro à l'émission/);
      expect(bouton).toHaveAccessibleName(/Client non nommé/);
      expect(bouton).toHaveAccessibleName(/\d{2}\/\d{2}\/\d{4}/);
      expect(bouton).not.toHaveAccessibleName(/PROV-/);
    }
    expect(premier.getAttribute('aria-label')).not.toBe(second.getAttribute('aria-label'));
  });

  it('une pièce nommée garde le client dans son libellé accessible', async () => {
    mockListInvoices.mockResolvedValue([{
      ...brouillon,
      invoice_number: 'FACT-2026-004',
      contact_name: 'Sophie Garcia',
      status: 'sent' as const,
      total_ttc: 198,
    }]);
    ouvrir();

    const bouton = await screen.findByRole('button', { name: /Sophie Garcia/ });
    expect(bouton).toHaveAccessibleName(/Facture/);
    expect(bouton).toHaveAccessibleName(/FACT-2026-004/);
    expect(bouton).toHaveAccessibleName(/198,00/);
    expect(bouton).toHaveTextContent('Sophie Garcia');
  });
});
