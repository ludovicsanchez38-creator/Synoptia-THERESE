/**
 * B-1397 (persona Zoé, cycle 13) : un double-clic sur « Convertir en facture »
 * ouvrait la confirmation au premier clic, et le second tombait sur son voile,
 * qui la refermait : rien ne se passait. Au clic simple, le focus restait
 * derrière, sur le bouton du formulaire.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';
import { useBillingProfileStore } from '../../stores/billingProfileStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import type { Invoice } from '../../services/api';

const { getBillingProfileStatusMock } = vi.hoisted(() => ({
  getBillingProfileStatusMock: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
}));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    listContacts: vi.fn().mockResolvedValue([
      { id: 'contact-1', first_name: 'Jean', last_name: 'Dupont', email: 'jean@example.com' },
    ]),
    createInvoice: vi.fn(),
    getBillingProfileStatus: getBillingProfileStatusMock,
  };
});

const devis: Invoice = {
  id: 'devis-1', invoice_number: 'DEV-2026-001', contact_id: 'contact-1',
  document_type: 'devis', tva_applicable: true, currency: 'EUR',
  issue_date: '2026-07-01T00:00:00Z', due_date: '2026-07-31T00:00:00Z', status: 'sent',
  subtotal_ht: 100, total_tax: 20, total_ttc: 120, notes: null, payment_terms: null,
  payment_method: null, late_penalty_rate: null, legal_mentions: null, converted_from_id: null,
  validite_jours: null, payment_date: null, created_at: '2026-07-01T08:00:00Z',
  updated_at: '2026-07-01T08:00:00Z',
  lines: [{
    id: 'line-1', invoice_id: 'devis-1', description: 'Accompagnement',
    quantity: 1, unit_price_ht: 100, tva_rate: 20, total_ht: 100, total_ttc: 120,
  }],
};

describe('B-1397 : la confirmation de conversion résiste au double-clic', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _clearEscapeHandlers();
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [] });
    useBillingProfileStore.setState({ missing: null });
  });
  afterEach(() => _clearEscapeHandlers());

  it('le second clic d’un double-clic ne referme pas la confirmation', async () => {
    render(<InvoiceForm invoice={devis} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByLabelText(/Client/i);
    fireEvent.click(screen.getByRole('button', { name: 'Convertir en facture' }), { detail: 1 });
    const dialogue = await screen.findByRole('dialog', { name: 'Confirmer la conversion' });
    fireEvent.click(dialogue.parentElement as HTMLElement, { detail: 2 });
    expect(screen.getByRole('dialog', { name: 'Confirmer la conversion' })).toBeInTheDocument();
  });

  it('le focus entre dans la confirmation', async () => {
    render(<InvoiceForm invoice={devis} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByLabelText(/Client/i);
    fireEvent.click(screen.getByRole('button', { name: 'Convertir en facture' }));
    const dialogue = await screen.findByRole('dialog', { name: 'Confirmer la conversion' });
    await waitFor(() => expect(dialogue.contains(document.activeElement)).toBe(true));
  });
});
