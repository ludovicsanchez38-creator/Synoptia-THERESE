/**
 * Le panneau Facturation affiche la devise du document, pas l'euro par défaut.
 *
 * Ce test REND le panneau et lit ce qui s'affiche, plutôt que de vérifier que
 * `montantAvecDevise` existe : la fonction pouvait être parfaite et l'écran
 * continuer d'écrire « € » en dur juste à côté.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useInvoiceStore } from '../../stores/invoiceStore';

const facture = (devise: string) => ({
  id: 'inv-1', invoice_number: 'FACT-2026-001', contact_id: 'c-1',
  document_type: 'facture', tva_applicable: true, currency: devise,
  issue_date: '2026-08-01T00:00:00Z', due_date: '2026-09-01T00:00:00Z',
  status: 'sent', subtotal_ht: 1000, total_tax: 200, total_ttc: 1200,
  notes: null, payment_terms: null, payment_method: null, late_penalty_rate: null,
  legal_mentions: null, converted_from_id: null, validite_jours: 30,
  payment_date: null, created_at: '2026-08-01T00:00:00Z',
  updated_at: '2026-08-01T00:00:00Z', contact_name: 'Camille Martin',
  lines: [{ id: 'l-1', invoice_id: 'inv-1', description: 'Prestation', quantity: 1,
            unit_price_ht: 1000, tva_rate: 20, total_ht: 1000, total_ttc: 1200 }],
});

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<Record<string, unknown>>('../../services/api');
  return {
    ...reel,
    listInvoices: vi.fn(),
    listContacts: vi.fn().mockResolvedValue([]),
    getBillingProfileStatus: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
  };
});

import * as api from '../../services/api';
import { InvoicesPanel } from './InvoicesPanel';

describe('Le panneau Facturation affiche la bonne devise', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Le panneau ne rend rien sans son store ouvert : sans ce montage, mon
    // premier jet testait un <div /> vide et aurait pu passer au vert pour
    // une raison qui n'a rien à voir avec la devise.
    useInvoiceStore.setState({
      invoices: [], currentInvoiceId: null, filters: { status: 'all' },
      isInvoicePanelOpen: true, draftInvoice: null,
    });
  });

  it('une facture en CHF ne s’affiche pas en euros', async () => {
    vi.mocked(api.listInvoices).mockResolvedValue([facture('CHF')] as never);
    render(<InvoicesPanel standalone />);

    await waitFor(() => expect(screen.getByText(/1200\.00/)).toBeInTheDocument());
    expect(screen.getByText(/1200\.00 CHF/)).toBeInTheDocument();
    expect(screen.queryByText(/1200\.00 €/)).not.toBeInTheDocument();
  });

  it('une facture en euros garde son symbole', async () => {
    vi.mocked(api.listInvoices).mockResolvedValue([facture('EUR')] as never);
    render(<InvoicesPanel standalone />);

    await waitFor(() => expect(screen.getByText(/1200\.00 €/)).toBeInTheDocument());
  });
});
