/**
 * B-1985 : le sous-titre compte tous les documents chargés, la liste n'en
 * montre que six. Le sous-titre doit le dire.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { Invoice } from '../../services/api';
import { InvoiceWorkspaceCard } from './InvoiceConversationCard';
import type { InvoiceWorkspaceData } from './usePrototypeInvoiceData';

const invoice = {
  id: 'invoice-1', invoice_number: 'DEV-2026-014', contact_id: 'contact-1', document_type: 'devis',
  tva_applicable: true, currency: 'EUR', issue_date: '2026-07-13T00:00:00Z', due_date: '2026-08-12T00:00:00Z',
  status: 'draft', subtotal_ht: 100, total_tax: 20, total_ttc: 120, notes: null, payment_terms: null,
  payment_method: null, late_penalty_rate: null, legal_mentions: null, converted_from_id: null,
  validite_jours: 30, payment_date: null, created_at: '2026-07-13T08:00:00Z', updated_at: '2026-07-13T08:00:00Z',
  lines: [],
} as unknown as Invoice;

function donnees(n: number): InvoiceWorkspaceData {
  return {
    invoices: Array.from({ length: n }, (_, i) => ({
      ...invoice,
      id: `inv-${i}`,
      invoice_number: `DEV-${String(i).padStart(3, '0')}`,
      updated_at: `2026-07-${String(28 - (i % 27)).padStart(2, '0')}T08:00:00Z`,
    })),
    contacts: [],
    billingProfile: { is_complete: true, missing: [] },
    unavailableSources: [],
  };
}

describe('B-1985 : le sous-titre dit combien de documents sont affichés', () => {
  it('annonce les six lignes visibles quand il y en a davantage', () => {
    render(
      <InvoiceWorkspaceCard
        resource={{ status: 'ready', data: donnees(8), error: null }}
        onRetry={vi.fn()} onOpenInvoice={vi.fn()} onCreateDevis={vi.fn()} onOpenClassic={vi.fn()}
      />,
    );
    expect(screen.getByText('8 documents enregistrés, 6 affichés ici')).toBeInTheDocument();
    const lignes = screen.getAllByRole('button').filter((bouton) => /DEV-/.test(bouton.textContent ?? ''));
    expect(lignes).toHaveLength(6);
  });
});
