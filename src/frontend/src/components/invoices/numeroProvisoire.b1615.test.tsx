/**
 * B-1615 : un brouillon de facture n'affiche pas un numéro définitif.
 * Le jeton PROV- reste en base ; l'écran dit que le numéro viendra à l'émission.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';
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
  id: 'inv-prov',
  invoice_number: 'PROV-abc123',
  contact_id: 'c-1',
  contact_name: 'Claire Roux',
  document_type: 'facture' as const,
  tva_applicable: true,
  currency: 'EUR',
  issue_date: '2026-09-29T00:00:00Z',
  due_date: '2026-10-29T00:00:00Z',
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
  created_at: '2026-09-29T00:00:00Z',
  updated_at: '2026-09-29T00:00:00Z',
  lines: [{
    id: 'l-1', invoice_id: 'inv-prov', description: 'Conseil', quantity: 1,
    unit_price_ht: 100, tva_rate: 20, total_ht: 100, total_ttc: 120,
  }],
};

describe('B-1615 : mention provisoire du brouillon', () => {
  it('le formulaire n’affiche pas le jeton PROV-', async () => {
    render(<InvoiceForm invoice={brouillon} onClose={vi.fn()} onSave={vi.fn()} />);
    expect(await screen.findByRole('heading', { name: /Brouillon, numéro à l'émission/ })).toBeInTheDocument();
    expect(screen.queryByText(/PROV-abc123/)).not.toBeInTheDocument();
  });

  it('la liste n’affiche pas le jeton PROV-', async () => {
    mockListInvoices.mockResolvedValue([brouillon]);
    useInvoiceStore.setState({
      invoices: [],
      currentInvoiceId: null,
      filters: { status: 'all' },
      isInvoicePanelOpen: true,
      draftInvoice: null,
    });
    render(<InvoicesPanel standalone />);
    expect(await screen.findByText("Brouillon, numéro à l'émission")).toBeInTheDocument();
    expect(screen.queryByText('PROV-abc123')).not.toBeInTheDocument();
  });

  it('un brouillon déjà numéroté garde son numéro à l’écran', async () => {
    mockListInvoices.mockResolvedValue([{ ...brouillon, id: 'inv-legacy', invoice_number: 'FACT-2026-007' }]);
    useInvoiceStore.setState({
      invoices: [],
      currentInvoiceId: null,
      filters: { status: 'all' },
      isInvoicePanelOpen: true,
      draftInvoice: null,
    });
    render(<InvoicesPanel standalone />);
    expect(await screen.findByText('FACT-2026-007')).toBeInTheDocument();
  });
});
