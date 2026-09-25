/** B-1450 (recette P-146, lot 3, KO-8) : le bloc « Conditions de paiement »
 *  d'une facture écrivait « Delai » et « Penalites de retard ». */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { Invoice } from '../../services/api';
import { InvoiceForm } from './InvoiceForm';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    listContacts: vi.fn().mockResolvedValue([]),
    getBillingProfileStatus: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
  };
});

const FACTURE = {
  id: 'invoice-1', invoice_number: 'FACT-2026-001', contact_id: 'contact-1', document_type: 'facture',
  tva_applicable: true, currency: 'EUR', issue_date: '2026-09-25T00:00:00Z', due_date: '2026-10-25T00:00:00Z',
  status: 'draft', subtotal_ht: 100, total_tax: 20, total_ttc: 120, notes: null,
  payment_terms: '30 jours', payment_method: 'Virement', late_penalty_rate: 11.62, legal_mentions: null,
  converted_from_id: null, validite_jours: null, payment_date: null,
  created_at: '2026-09-25T08:00:00Z', updated_at: '2026-09-25T08:00:00Z', lines: [],
} as unknown as Invoice;

describe('B-1450 : les conditions de paiement sont accentuées', () => {
  it('Délai et Pénalités de retard', async () => {
    render(<InvoiceForm invoice={FACTURE} onClose={vi.fn()} onSave={vi.fn()} />);
    expect(await screen.findByText('Délai :')).toBeInTheDocument();
    expect(screen.getByText('Pénalités de retard :')).toBeInTheDocument();
  });
});
