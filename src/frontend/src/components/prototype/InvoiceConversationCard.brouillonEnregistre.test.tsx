/**
 * B-574 et B-575 (05/09/2026) : le canevas Facturer ne disait pas que sa
 * liste de clients était tronquée, et laissait ré-enregistrer un brouillon
 * identique d'un second clic.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { Contact, Invoice } from '../../services/api';
import { InvoiceWorkspaceCanvas } from './InvoiceConversationCard';
import type { InvoiceWorkspaceData } from './usePrototypeInvoiceData';

const contact: Contact = {
  id: 'contact-1', first_name: 'Camille', last_name: 'Martin', company: 'Atelier Martin', email: 'camille@example.test',
  phone: null, address: null, notes: null, tags: [], stage: 'client', score: 80, source: 'local', last_interaction: null,
  created_at: '2026-07-01', updated_at: '2026-07-12',
};
const invoice: Invoice = {
  id: 'invoice-1', invoice_number: 'DEV-2026-014', contact_id: contact.id, document_type: 'devis', tva_applicable: true,
  currency: 'EUR', issue_date: '2026-07-13T00:00:00Z', due_date: '2026-08-12T00:00:00Z', status: 'draft', subtotal_ht: 490,
  total_tax: 98, total_ttc: 588, notes: null, payment_terms: null, payment_method: null, late_penalty_rate: null,
  legal_mentions: null, converted_from_id: null, validite_jours: 30, payment_date: null, created_at: '2026-07-13T08:00:00Z',
  updated_at: '2026-07-13T08:00:00Z', lines: [],
};
function data(overrides: Partial<InvoiceWorkspaceData> = {}): InvoiceWorkspaceData {
  return { invoices: [], contacts: [contact], billingProfile: { is_complete: true, missing: [] }, unavailableSources: [], contactsTronques: false, ...overrides };
}
function rendre(props: { onCreateDraft?: () => Promise<Invoice>; donnees?: InvoiceWorkspaceData }) {
  return render(
    <InvoiceWorkspaceCanvas
      resource={{ status: 'ready', data: props.donnees ?? data(), error: null }}
      invoiceResource={null} selection="new-devis" onRetry={vi.fn()} onRetryInvoice={vi.fn()}
      onCreateDraft={props.onCreateDraft ?? vi.fn()} onCreateContact={vi.fn()} onOpenClassic={vi.fn()}
    />,
  );
}

describe('InvoiceWorkspaceCanvas : brouillon enregistré (B-575) et liste tronquée (B-574)', () => {
  it('après un enregistrement réussi, le bouton reste inactif tant que rien n’a changé', async () => {
    rendre({ onCreateDraft: vi.fn().mockResolvedValue(invoice) });
    fireEvent.change(screen.getByLabelText('Client du devis'), { target: { value: contact.id } });
    fireEvent.change(screen.getByLabelText('Description ligne 1'), { target: { value: 'Diagnostic IA' } });
    fireEvent.change(screen.getByLabelText('Prix HT ligne 1'), { target: { value: '490' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer le brouillon' }));
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer le brouillon' }));
    await screen.findByTestId('devis-draft-saved');

    expect(screen.getByRole('button', { name: 'Enregistrer le brouillon' })).toBeDisabled();

    fireEvent.change(screen.getByLabelText('Description ligne 1'), { target: { value: 'Diagnostic IA approfondi' } });
    expect(screen.getByRole('button', { name: 'Enregistrer le brouillon' })).toBeEnabled();
  });

  it('dit quand la liste des clients est tronquée', () => {
    rendre({ donnees: data({ contactsTronques: true }) });
    expect(screen.getByRole('alert')).toHaveTextContent(/Liste incomplète/);
  });
});
