/**
 * B-1412 (étape 5.5 de Claire, relevé par la RFC P-121) : après « Confirmer le
 * brouillon », une retouche affiche « Modifications non enregistrées depuis le
 * dernier brouillon » ; « Enregistrer le brouillon » créait pourtant un SECOND
 * devis (DEV-…-002), le premier restant tel quel. La retouche met désormais à
 * jour le brouillon enregistré ; la confirmation reste, et le dit.
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

describe('B-1412 : retoucher un brouillon enregistré le met à jour', () => {
  it('le second enregistrement vise le devis créé, sans en créer un autre', async () => {
    const enregistrer = vi.fn().mockResolvedValue(invoice);
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
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer le brouillon' }));
    await screen.findByTestId('devis-draft-saved');

    fireEvent.change(screen.getByLabelText('Description ligne 1'), { target: { value: 'Diagnostic IA approfondi' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer le brouillon' }));
    expect(screen.getByText(/Confirmer la mise à jour de DEV-2026-014/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer le brouillon' }));
    await screen.findByTestId('devis-draft-saved');

    expect(enregistrer).toHaveBeenCalledTimes(2);
    expect(enregistrer.mock.calls[0][1]).toBeUndefined();
    expect(enregistrer.mock.calls[1][1]).toBe('invoice-1');
  });
});
