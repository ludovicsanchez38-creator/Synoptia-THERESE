import { useState } from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { Contact, Invoice } from '../../services/api';
import { InvoiceWorkspaceCanvas, InvoiceWorkspaceCard } from './InvoiceConversationCard';
import type { InvoiceWorkspaceData } from './usePrototypeInvoiceData';

const contact: Contact = {
  id: 'contact-1', first_name: 'Camille', last_name: 'Martin', company: 'Atelier Martin',
  email: 'camille@example.test', phone: null, notes: null, tags: [], stage: 'client', score: 80,
  source: 'local', last_interaction: null, created_at: '2026-07-01', updated_at: '2026-07-12',
};

const invoice: Invoice = {
  id: 'invoice-1', invoice_number: 'DEV-2026-014', contact_id: contact.id,
  document_type: 'devis', tva_applicable: true, currency: 'EUR',
  issue_date: '2026-07-13T00:00:00Z', due_date: '2026-08-12T00:00:00Z', status: 'draft',
  subtotal_ht: 100, total_tax: 20, total_ttc: 120, notes: null, payment_terms: null,
  payment_method: null, late_penalty_rate: null, legal_mentions: null, converted_from_id: null,
  validite_jours: 30, payment_date: null, created_at: '2026-07-13T08:00:00Z',
  updated_at: '2026-07-13T08:00:00Z',
  lines: [{
    id: 'line-1', invoice_id: 'invoice-1', description: 'Accompagnement réel', quantity: 1,
    unit_price_ht: 100, tva_rate: 20, total_ht: 100, total_ttc: 120,
  }],
};

function data(overrides: Partial<InvoiceWorkspaceData> = {}): InvoiceWorkspaceData {
  return {
    invoices: [invoice], contacts: [contact],
    billingProfile: { is_complete: true, missing: [] }, unavailableSources: [],
    ...overrides,
  };
}

describe('InvoiceWorkspaceCard', () => {
  it('affiche uniquement les documents et contacts réels puis ouvre le détail', () => {
    const onOpenInvoice = vi.fn();
    render(
      <InvoiceWorkspaceCard
        resource={{ status: 'ready', data: data(), error: null }}
        onRetry={vi.fn()}
        onOpenInvoice={onOpenInvoice}
        onCreateDevis={vi.fn()}
        onOpenClassic={vi.fn()}
      />,
    );

    expect(screen.getByText('DEV-2026-014')).toBeInTheDocument();
    expect(screen.getByText(/Camille Martin/)).toBeInTheDocument();
    expect(screen.queryByText(/Claire Fontaine|PROPULSER/)).not.toBeInTheDocument();
    fireEvent.click(screen.getByText('DEV-2026-014'));
    expect(onOpenInvoice).toHaveBeenCalledWith('invoice-1');
  });
});

describe('InvoiceWorkspaceCanvas', () => {
  it('affiche le détail chargé par l’API sans action externe', () => {
    render(
      <InvoiceWorkspaceCanvas
        resource={{ status: 'ready', data: data(), error: null }}
        invoiceResource={{ status: 'ready', data: invoice, error: null }}
        selection="invoice-1"
        onRetry={vi.fn()}
        onRetryInvoice={vi.fn()}
        onCreateDraft={vi.fn()}
        onCreateContact={vi.fn()}
        onOpenClassic={vi.fn()}
      />,
    );

    expect(screen.getByTestId('invoice-detail')).toHaveTextContent('Accompagnement réel');
    expect(screen.getByTestId('invoice-detail')).toHaveTextContent('Lecture seule');
    expect(screen.queryByRole('button', { name: /envoyer/i })).not.toBeInTheDocument();
  });

  it('demande confirmation et ignore un double clic avant de créer le devis brouillon', async () => {
    let resolveCreation: ((value: Invoice) => void) | undefined;
    const onCreateDraft = vi.fn().mockImplementation(() => new Promise<Invoice>((resolve) => {
      resolveCreation = resolve;
    }));
    render(
      <InvoiceWorkspaceCanvas
        resource={{ status: 'ready', data: data({ invoices: [] }), error: null }}
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
    fireEvent.change(screen.getByLabelText('Description ligne 1'), { target: { value: 'Diagnostic IA' } });
    fireEvent.change(screen.getByLabelText('Prix HT ligne 1'), { target: { value: '490' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer le brouillon' }));

    expect(screen.getByTestId('devis-draft-confirmation')).toHaveTextContent('Camille Martin');
    expect(screen.getByTestId('devis-draft-confirmation')).toHaveTextContent('588');
    expect(screen.getByLabelText('Client du devis')).toBeDisabled();
    expect(screen.getByLabelText('Description ligne 1')).toBeDisabled();
    expect(screen.getByLabelText('Prix HT ligne 1')).toBeDisabled();
    expect(onCreateDraft).not.toHaveBeenCalled();

    const confirm = screen.getByRole('button', { name: 'Confirmer le brouillon' });
    fireEvent.click(confirm);
    fireEvent.click(confirm);
    expect(onCreateDraft).toHaveBeenCalledTimes(1);
    expect(onCreateDraft).toHaveBeenCalledWith(expect.objectContaining({
      contact_id: contact.id,
      document_type: 'devis',
      currency: 'EUR',
      lines: [{ description: 'Diagnostic IA', quantity: 1, unit_price_ht: 490, tva_rate: 20 }],
    }));

    resolveCreation?.({ ...invoice, subtotal_ht: 490, total_tax: 98, total_ttc: 588 });
    expect(await screen.findByTestId('devis-draft-saved')).toHaveTextContent('Aucun PDF n’a été généré et aucun email n’a été envoyé');
  });

  it('crée le premier contact dans le canevas puis le sélectionne pour poursuivre le devis', async () => {
    const onCreateContact = vi.fn().mockResolvedValue(contact);

    function FirstDevisHarness() {
      const [workspace, setWorkspace] = useState(() => data({ invoices: [], contacts: [] }));
      return (
        <InvoiceWorkspaceCanvas
          resource={{ status: 'ready', data: workspace, error: null }}
          invoiceResource={null}
          selection="new-devis"
          onRetry={vi.fn()}
          onRetryInvoice={vi.fn()}
          onCreateDraft={vi.fn()}
          onCreateContact={async (payload) => {
            const createdContact = await onCreateContact(payload);
            setWorkspace((current) => ({ ...current, contacts: [createdContact] }));
            return createdContact;
          }}
          onOpenClassic={vi.fn()}
        />
      );
    }

    render(<FirstDevisHarness />);
    expect(screen.getByTestId('invoice-first-contact-form')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Entreprise du nouveau contact'), { target: { value: 'Atelier Martin' } });
    fireEvent.change(screen.getByLabelText('Email du nouveau contact'), { target: { value: 'camille@example.test' } });
    const createButton = screen.getByRole('button', { name: 'Créer et continuer le devis' });
    fireEvent.click(createButton);
    fireEvent.click(createButton);

    await waitFor(() => expect(onCreateContact).toHaveBeenCalledTimes(1));
    expect(onCreateContact).toHaveBeenCalledWith(expect.objectContaining({
      company: 'Atelier Martin',
      email: 'camille@example.test',
    }));
    expect(await screen.findByLabelText('Client du devis')).toHaveValue(contact.id);
  });
});
