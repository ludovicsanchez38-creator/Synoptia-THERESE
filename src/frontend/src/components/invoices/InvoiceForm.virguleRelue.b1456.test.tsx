/**
 * B-1456 (recette P-146, lot 3) : un prix saisi « 33,33 » se relisait
 * « 33.33 » en modification : le champ était rempli par `String(nombre)`.
 * Les décimaux d'une pièce enregistrée se relisent avec la virgule.
 */
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
  status: 'draft', subtotal_ht: 83.33, total_tax: 16.67, total_ttc: 100, notes: null, payment_terms: null,
  payment_method: null, late_penalty_rate: null, legal_mentions: null, converted_from_id: null,
  validite_jours: null, payment_date: null, created_at: '2026-09-25T08:00:00Z', updated_at: '2026-09-25T08:00:00Z',
  lines: [{ id: 'l1', invoice_id: 'invoice-1', description: 'Conseil', quantity: 2.5, unit_price_ht: 33.33,
    tva_rate: 20, total_ht: 83.33, total_ttc: 100 }],
} as unknown as Invoice;

describe('B-1456 : les décimaux se relisent avec la virgule', () => {
  it('prix et quantité', async () => {
    render(<InvoiceForm invoice={FACTURE} onClose={vi.fn()} onSave={vi.fn()} />);
    expect(await screen.findByDisplayValue('33,33')).toBeInTheDocument();
    expect(screen.getByDisplayValue('2,5')).toBeInTheDocument();
    expect(screen.queryByDisplayValue('33.33')).toBeNull();
  });
});
