/**
 * B-1984 : confirmer une mise à jour de brouillon ne dit plus qu'on crée
 * un document, et le bouton ne reste pas « Confirmer le brouillon ».
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { Contact, Invoice } from '../../services/api';
import { InvoiceWorkspaceCanvas } from './InvoiceConversationCard';

const contact: Contact = {
  id: 'contact-1', first_name: 'Camille', last_name: 'Martin', company: 'Atelier Martin', email: 'camille@example.test',
  phone: null, address: null, notes: null, tags: [], stage: 'client', score: 80, source: 'local', last_interaction: null,
  created_at: '2026-07-01', updated_at: '2026-07-12',
};
const invoice = {
  id: 'invoice-1', invoice_number: 'DEV-2026-014', contact_id: contact.id, document_type: 'devis', tva_applicable: true,
  currency: 'EUR', issue_date: '2026-07-13T00:00:00Z', due_date: '2026-08-12T00:00:00Z', status: 'draft', subtotal_ht: 490,
  total_tax: 98, total_ttc: 588, notes: null, payment_terms: null, payment_method: null, late_penalty_rate: null,
  legal_mentions: null, converted_from_id: null, validite_jours: 30, payment_date: null, created_at: '2026-07-13T08:00:00Z',
  updated_at: '2026-07-13T08:00:00Z', lines: [],
} as unknown as Invoice;

describe('B-1984 : la confirmation d’une mise à jour parle de mise à jour', () => {
  it('distingue la création et la mise à jour', async () => {
    const enregistrer = vi.fn()
      .mockResolvedValueOnce(invoice)
      .mockImplementationOnce(() => new Promise(() => {}));
    render(
      <InvoiceWorkspaceCanvas
        resource={{ status: 'ready', data: { invoices: [], contacts: [contact], billingProfile: { is_complete: true, missing: [] }, unavailableSources: [], contactsTronques: false }, error: null }}
        invoiceResource={null} selection="new-devis" onRetry={vi.fn()} onRetryInvoice={vi.fn()}
        onCreateDraft={enregistrer} onCreateContact={vi.fn()} onOpenClassic={vi.fn()}
      />,
    );
    fireEvent.change(screen.getByLabelText('Client du devis'), { target: { value: contact.id } });
    fireEvent.change(screen.getByLabelText('Description ligne 1'), { target: { value: 'Diagnostic IA' } });
    fireEvent.change(screen.getByLabelText('Prix HT ligne 1'), { target: { value: '490' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer le brouillon' }));
    const creation = screen.getByTestId('devis-draft-confirmation');
    expect(creation).toHaveTextContent('Cette action crée un document local');
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer le brouillon' }));
    await screen.findByTestId('devis-draft-saved');

    fireEvent.change(screen.getByLabelText('Description ligne 1'), { target: { value: 'Diagnostic IA approfondi' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer le brouillon' }));
    const maj = screen.getByTestId('devis-draft-confirmation');
    expect(maj).toHaveTextContent('Cette action met à jour le brouillon');
    expect(maj).not.toHaveTextContent('Cette action crée un document');
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer la mise à jour' }));
    expect(screen.getByRole('button', { name: 'Mise à jour…' })).toBeDisabled();
  });
});
