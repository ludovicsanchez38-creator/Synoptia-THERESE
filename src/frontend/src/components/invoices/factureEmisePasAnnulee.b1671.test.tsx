/**
 * B-1671 : une facture émise ne propose plus « Annulée ».
 * Un devis envoyé garde « Annulé ».
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<Record<string, unknown>>('../../services/api');
  return {
    ...reel,
    listContacts: vi.fn().mockResolvedValue([]),
    getBillingProfileStatus: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
  };
});

function piece(documentType: 'devis' | 'facture' | 'avoir', status: 'draft' | 'sent') {
  return {
    id: 'inv-1',
    invoice_number: documentType === 'devis' ? 'DEV-2026-001' : 'FACT-2026-001',
    contact_id: 'c-1',
    document_type: documentType,
    tva_applicable: true,
    currency: 'EUR',
    issue_date: '2026-08-01T00:00:00Z',
    due_date: '2026-09-01T00:00:00Z',
    status,
    subtotal_ht: 1000,
    total_tax: 200,
    total_ttc: 1200,
    notes: null,
    payment_terms: null,
    payment_method: null,
    late_penalty_rate: null,
    legal_mentions: null,
    converted_from_id: null,
    validite_jours: 30,
    payment_date: null,
    created_at: '2026-08-01T00:00:00Z',
    updated_at: '2026-08-01T00:00:00Z',
    lines: [{
      id: 'l-1', invoice_id: 'inv-1', description: 'Prestation', quantity: 1,
      unit_price_ht: 1000, tva_rate: 20, total_ht: 1000, total_ttc: 1200,
    }],
  };
}

function valeursStatut(): string[] {
  const statut = screen.getByLabelText('Statut') as HTMLSelectElement;
  return Array.from(statut.querySelectorAll('option')).map((option) => option.value);
}

describe('B-1671 : Annulée sort du sélecteur d’une facture émise', () => {
  it('une facture envoyée ne propose pas cancelled', async () => {
    render(<InvoiceForm invoice={piece('facture', 'sent') as never} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByLabelText('Statut');
    expect(valeursStatut()).not.toContain('cancelled');
    expect(valeursStatut()).toEqual(expect.arrayContaining(['sent', 'paid', 'overdue']));
  });

  it('un avoir envoyé ne propose pas cancelled', async () => {
    render(<InvoiceForm invoice={piece('avoir', 'sent') as never} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByLabelText('Statut');
    expect(valeursStatut()).not.toContain('cancelled');
    expect(valeursStatut()).toEqual(expect.arrayContaining(['sent', 'paid', 'overdue']));
  });

  it('un devis envoyé propose encore cancelled', async () => {
    render(<InvoiceForm invoice={piece('devis', 'sent') as never} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByLabelText('Statut');
    expect(valeursStatut()).toContain('cancelled');
  });

  it('un brouillon de facture propose encore cancelled', async () => {
    render(<InvoiceForm invoice={piece('facture', 'draft') as never} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByLabelText('Statut');
    expect(valeursStatut()).toContain('cancelled');
  });
});
