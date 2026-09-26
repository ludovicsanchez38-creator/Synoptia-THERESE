/**
 * B-1370 (persona Zoé, cycle 13) : « Nouveau devis ou facture » posait le
 * focus sur la croix « Fermer », premier élément focalisable du dialogue.
 * Le formulaire s'ouvre désormais sur son premier champ : le type de document
 * pour une création, le client pour une modification.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { Invoice } from '../../services/api';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    listContacts: vi.fn().mockResolvedValue([{ id: 'contact-1', first_name: 'Jean', last_name: 'Dupont', email: 'jean@example.com' }]),
    getBillingProfileStatus: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
  };
});

import { InvoiceForm } from './InvoiceForm';

const facture = {
  id: 'invoice-1', invoice_number: 'FAC-2026-001', contact_id: 'contact-1', document_type: 'facture',
  tva_applicable: true, currency: 'EUR', issue_date: '2026-07-01T00:00:00Z', due_date: '2026-07-31T00:00:00Z',
  status: 'sent', subtotal_ht: 100, total_tax: 20, total_ttc: 120, notes: null, payment_terms: null,
  payment_method: null, late_penalty_rate: null, legal_mentions: null, converted_from_id: null,
  validite_jours: null, payment_date: null, created_at: '2026-07-01T08:00:00Z', updated_at: '2026-07-01T08:00:00Z',
  lines: [],
} as unknown as Invoice;

describe('B-1370 : le formulaire de devis s’ouvre sur son premier champ', () => {
  it('création : le type de document choisi a le focus, pas la croix', async () => {
    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);

    const choisi = screen.getByRole('button', { name: 'Facture', pressed: true });
    await waitFor(() => expect(document.activeElement).toBe(choisi));
  });

  it('modification d’un brouillon : le client a le focus', async () => {
    render(<InvoiceForm invoice={{ ...facture, status: 'draft' }} onClose={vi.fn()} onSave={vi.fn()} />);

    await waitFor(() => expect(document.activeElement).toBe(screen.getByLabelText(/Client/)));
  });

  it('B-1614 : sur une pièce émise, figée, le statut a le focus', async () => {
    render(<InvoiceForm invoice={facture} onClose={vi.fn()} onSave={vi.fn()} />);

    await waitFor(() => expect(document.activeElement).toBe(screen.getByLabelText('Statut')));
  });
});
