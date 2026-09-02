/**
 * B-014 - la carte Facturer nomme le client avec le nom que porte la facture.
 *
 * Constat du 02/09/2026 (reproduction RP02) : l'API rend `contact_name` sur
 * chaque devis/facture (`routers/invoices.py` le remplit par le join, et
 * `services/api/invoices.ts` le déclare). La carte l'ignorait et résolvait le
 * nom en cherchant le contact dans la liste chargée par
 * `listContacts(0, 100)`. Hors de cette fenêtre de cent, ou quand l'appel
 * contacts échoue (`contacts: []`), elle affichait « Contact introuvable »
 * pendant que le nom voyageait dans la facture elle-même.
 *
 * L'autre écran de la même application lit déjà ce champ
 * (`InvoicesPanel.tsx` : `{invoice.contact_name || invoice.invoice_number}`) :
 * deux surfaces, une seule lisait la donnée garantie.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { Contact, Invoice } from '../../services/api';
import { InvoiceWorkspaceCanvas, InvoiceWorkspaceCard } from './InvoiceConversationCard';
import type { InvoiceWorkspaceData } from './usePrototypeInvoiceData';

const FACTURE: Invoice = {
  id: 'invoice-hors-fenetre',
  invoice_number: 'DEV-2026-001',
  contact_id: 'dc81b97b-6a91-4484-85c1-fe5678008d7e',
  contact_name: 'Sophie Moreau',
  document_type: 'devis', tva_applicable: true, currency: 'EUR',
  issue_date: '2026-09-01T00:00:00Z', due_date: '2026-10-01T00:00:00Z', status: 'draft',
  subtotal_ht: 99.99, total_tax: 20.01, total_ttc: 120, notes: null, payment_terms: null,
  payment_method: null, late_penalty_rate: null, legal_mentions: null, converted_from_id: null,
  validite_jours: 30, payment_date: null, created_at: '2026-09-01T08:00:00Z',
  updated_at: '2026-09-01T08:00:00Z',
  lines: [{
    id: 'line-1', invoice_id: 'invoice-hors-fenetre', description: 'Accompagnement',
    quantity: 3, unit_price_ht: 33.33, tva_rate: 20, total_ht: 99.99, total_ttc: 120,
  }],
};

/** Le contact est HORS des cent chargés : la liste est vide, la facture non. */
function donneesSansContacts(): InvoiceWorkspaceData {
  return {
    invoices: [FACTURE], contacts: [] as Contact[],
    billingProfile: { is_complete: true, missing: [] }, unavailableSources: [],
  };
}

describe('B-014 - le nom du client vient de la facture, pas d’une fenêtre de cent', () => {
  it('la liste nomme le client hors de la fenêtre de contacts chargés', () => {
    render(
      <InvoiceWorkspaceCard
        resource={{ status: 'ready', data: donneesSansContacts(), error: null }}
        onRetry={vi.fn()}
        onOpenInvoice={vi.fn()}
        onCreateDevis={vi.fn()}
        onOpenClassic={vi.fn()}
      />,
    );

    expect(screen.getByText(/Moreau/)).toBeInTheDocument();
    expect(screen.queryByText(/Contact introuvable/)).toBeNull();
  });

  it('le détail du document aussi, quand la source contacts est indisponible', () => {
    // `usePrototypeInvoiceData` retombe sur `contacts: []` quand l'appel
    // contacts échoue : c'est le second chemin qui produisait « Contact
    // introuvable » alors que le nom était sous les yeux du composant.
    const indisponible: InvoiceWorkspaceData = {
      ...donneesSansContacts(),
      unavailableSources: ['contacts'],
    };
    render(
      <InvoiceWorkspaceCanvas
        resource={{ status: 'ready', data: indisponible, error: null }}
        invoiceResource={{ status: 'ready', data: FACTURE, error: null }}
        selection={FACTURE.id}
        onRetry={vi.fn()}
        onRetryInvoice={vi.fn()}
        onCreateDraft={vi.fn()}
        onCreateContact={vi.fn()}
        onOpenClassic={vi.fn()}
      />,
    );

    const detail = screen.getByTestId('invoice-detail');
    expect(detail).toHaveTextContent('Sophie Moreau');
    expect(detail).not.toHaveTextContent('Contact introuvable');
  });

  it('témoin : sans nom porté par la facture, la résolution par contact tient encore', () => {
    // Le champ est absent quand le contact a disparu côté serveur. Le repli
    // sur la liste chargée doit rester en place, sinon on remplace un trou
    // par un autre.
    const contact: Contact = {
      id: FACTURE.contact_id, first_name: 'Camille', last_name: 'Martin', company: 'Atelier Martin',
      email: 'camille@example.test', phone: null, address: null, notes: null, tags: [],
      stage: 'client', score: 80, source: 'local', last_interaction: null,
      created_at: '2026-07-01', updated_at: '2026-07-12',
    };
    render(
      <InvoiceWorkspaceCard
        resource={{
          status: 'ready',
          data: {
            ...donneesSansContacts(),
            invoices: [{ ...FACTURE, contact_name: null }],
            contacts: [contact],
          },
          error: null,
        }}
        onRetry={vi.fn()}
        onOpenInvoice={vi.fn()}
        onCreateDevis={vi.fn()}
        onOpenClassic={vi.fn()}
      />,
    );

    expect(screen.getByText(/Camille Martin/)).toBeInTheDocument();
  });
});
