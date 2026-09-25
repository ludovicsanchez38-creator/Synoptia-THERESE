/**
 * B-1439 (recette P-146, lot 2, H1) : à la création, le formulaire proposait
 * un « Statut » (Envoyée, Payée…) que le moteur ignore : toute pièce naît en
 * brouillon. La facture revenait « Brouillon » sans un mot. À la création, le
 * formulaire dit le statut réel ; le sélecteur n'existe qu'en modification.
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
  id: 'invoice-1', invoice_number: 'FAC-2026-001', contact_id: 'contact-1', document_type: 'facture',
  tva_applicable: true, currency: 'EUR', issue_date: '2026-07-01T00:00:00Z', due_date: '2026-07-31T00:00:00Z',
  status: 'sent', subtotal_ht: 100, total_tax: 20, total_ttc: 120, notes: null, payment_terms: null,
  payment_method: null, late_penalty_rate: null, legal_mentions: null, converted_from_id: null,
  validite_jours: null, payment_date: null, created_at: '2026-07-01T08:00:00Z', updated_at: '2026-07-01T08:00:00Z',
  lines: [],
} as Invoice;

describe('B-1439 : le statut à la création dit la vérité', () => {
  it('une nouvelle pièce naît en brouillon, sans sélecteur trompeur', async () => {
    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByRole('combobox', { name: 'Devise' });
    expect(screen.queryByRole('combobox', { name: 'Statut' })).toBeNull();
    expect(screen.getByText(/naît en brouillon/)).toBeInTheDocument();
  });

  it('une pièce existante garde son sélecteur de statut', async () => {
    render(<InvoiceForm invoice={FACTURE} onClose={vi.fn()} onSave={vi.fn()} />);
    expect(await screen.findByRole('combobox', { name: 'Statut' })).toBeInTheDocument();
  });
});
