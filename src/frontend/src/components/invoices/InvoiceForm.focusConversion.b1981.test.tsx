/**
 * B-1981 : Tab dans « Confirmer la conversion » ne sort pas vers les champs
 * du formulaire, masqués par le voile.
 */
import { fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';
import { useBillingProfileStore } from '../../stores/billingProfileStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import type { Invoice } from '../../services/api';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    listContacts: vi.fn().mockResolvedValue([
      { id: 'contact-1', first_name: 'Jean', last_name: 'Dupont', email: 'jean@example.com' },
    ]),
    getBillingProfileStatus: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
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

describe('B-1981 : le focus reste dans la confirmation de conversion', () => {
  beforeEach(() => {
    _clearEscapeHandlers();
    useBillingProfileStore.setState({ missing: null, statutLecture: 'lu', tvaIntraRenseigne: false });
  });
  afterEach(() => _clearEscapeHandlers());

  it('Tab depuis Convertir reste dans le dialogue', async () => {
    render(<InvoiceForm invoice={devis} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByLabelText(/Client/);
    fireEvent.click(screen.getByRole('button', { name: 'Convertir en facture' }));
    const dialogue = await screen.findByRole('dialog', { name: 'Confirmer la conversion' });
    const convertir = within(dialogue).getByRole('button', { name: 'Convertir' });
    convertir.focus();
    fireEvent.keyDown(document, { key: 'Tab' });
    expect(dialogue.contains(document.activeElement)).toBe(true);
  });
});
