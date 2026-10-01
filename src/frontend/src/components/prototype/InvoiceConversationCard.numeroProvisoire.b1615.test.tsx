/**
 * B-1615 : la carte de facturation réelle n'affiche pas le jeton PROV-.
 * Liste, détail et messages de brouillon disent que le numéro viendra à l'émission.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { Contact, Invoice } from '../../services/api';
import { InvoiceWorkspaceCanvas, InvoiceWorkspaceCard } from './InvoiceConversationCard';
import type { InvoiceWorkspaceData } from './usePrototypeInvoiceData';

const contact: Contact = {
  id: 'contact-1', first_name: 'Claire', last_name: 'Roux', company: null,
  email: 'claire@example.test', phone: null, address: null, notes: null, tags: [], stage: 'client', score: 80,
  source: 'local', last_interaction: null, created_at: '2026-07-01', updated_at: '2026-07-12',
};

const brouillon: Invoice = {
  id: 'inv-prov', invoice_number: 'PROV-abc123', contact_id: contact.id,
  document_type: 'facture', tva_applicable: true, currency: 'EUR',
  issue_date: '2026-09-29T00:00:00Z', due_date: '2026-10-29T00:00:00Z', status: 'draft',
  subtotal_ht: 100, total_tax: 20, total_ttc: 120, notes: null, payment_terms: null,
  payment_method: null, late_penalty_rate: null, legal_mentions: null, converted_from_id: null,
  validite_jours: null, payment_date: null, created_at: '2026-09-29T08:00:00Z',
  updated_at: '2026-09-29T08:00:00Z',
  lines: [{
    id: 'line-1', invoice_id: 'inv-prov', description: 'Conseil', quantity: 1,
    unit_price_ht: 100, tva_rate: 20, total_ht: 100, total_ttc: 120,
  }],
};

function donnees(): InvoiceWorkspaceData {
  return {
    invoices: [brouillon], contacts: [contact],
    billingProfile: { is_complete: true, missing: [] }, unavailableSources: [],
  };
}

describe('B-1615 : la carte de facturation masque le jeton provisoire', () => {
  it('la liste et le détail disent « Brouillon, numéro à l’émission »', () => {
    render(
      <InvoiceWorkspaceCard
        resource={{ status: 'ready', data: donnees(), error: null }}
        onRetry={vi.fn()}
        onOpenInvoice={vi.fn()}
        onCreateDevis={vi.fn()}
        onOpenClassic={vi.fn()}
      />,
    );
    expect(screen.getByText("Brouillon, numéro à l'émission")).toBeInTheDocument();
    expect(screen.queryByText(/PROV-abc123/)).not.toBeInTheDocument();

    render(
      <InvoiceWorkspaceCanvas
        resource={{ status: 'ready', data: donnees(), error: null }}
        invoiceResource={{ status: 'ready', data: brouillon, error: null }}
        selection="inv-prov"
        onRetry={vi.fn()}
        onRetryInvoice={vi.fn()}
        onCreateDraft={vi.fn()}
        onCreateContact={vi.fn()}
        onOpenClassic={vi.fn()}
      />,
    );
    expect(screen.getByTestId('invoice-detail')).toHaveTextContent("Brouillon, numéro à l'émission");
    expect(screen.getByTestId('invoice-detail')).not.toHaveTextContent('PROV-abc123');
  });

  it('le message d’enregistrement et la confirmation de mise à jour masquent le jeton', async () => {
    const onCreateDraft = vi.fn().mockResolvedValue(brouillon);
    render(
      <InvoiceWorkspaceCanvas
        resource={{ status: 'ready', data: { ...donnees(), invoices: [] }, error: null }}
        invoiceResource={null}
        selection="new-devis"
        onRetry={vi.fn()}
        onRetryInvoice={vi.fn()}
        onCreateDraft={onCreateDraft}
        onCreateContact={vi.fn()}
        onOpenClassic={vi.fn()}
      />,
    );
    fireEvent.change(screen.getByLabelText('Client du devis'), { target: { value: contact.id } });
    fireEvent.change(screen.getByLabelText('Description ligne 1'), { target: { value: 'Conseil' } });
    fireEvent.change(screen.getByLabelText('Prix HT ligne 1'), { target: { value: '100' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer le brouillon' }));
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer le brouillon' }));
    const sauve = await screen.findByTestId('devis-draft-saved');
    expect(sauve).toHaveTextContent("Brouillon, numéro à l'émission");
    expect(sauve).not.toHaveTextContent('PROV-abc123');

    fireEvent.change(screen.getByLabelText('Description ligne 1'), { target: { value: 'Conseil approfondi' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer le brouillon' }));
    const confirmation = screen.getByTestId('devis-draft-confirmation');
    expect(confirmation).toHaveTextContent("Brouillon, numéro à l'émission");
    expect(confirmation).not.toHaveTextContent('PROV-abc123');
  });
});
