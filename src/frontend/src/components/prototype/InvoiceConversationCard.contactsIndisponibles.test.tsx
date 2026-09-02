/**
 * B-015 - une source indisponible n'est pas une affirmation sur la donnée.
 *
 * Quand `/api/memory/contacts` répond 500, `usePrototypeInvoiceData` retombe
 * sur `contacts: []` et inscrit « contacts » dans `unavailableSources` : un
 * bandeau « Source indisponible : contacts. » s'affiche en bas de la carte.
 * Mais chaque ligne continuait d'annoncer « Contact introuvable », c'est-à-dire
 * d'affirmer que le client du document n'existe pas, alors que la seule chose
 * qu'on sache est qu'on n'a pas pu lire le carnet.
 *
 * B-014 avait fermé la moitié du trou : quand la facture porte `contact_name`,
 * c'est ce nom qui s'affiche. Reste le cas où elle ne le porte pas - le champ
 * est absent pour un document dont le join n'a rien rendu - et là l'écran
 * inventait encore une absence.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { Contact, Invoice } from '../../services/api';
import { InvoiceWorkspaceCanvas, InvoiceWorkspaceCard } from './InvoiceConversationCard';
import type { InvoiceWorkspaceData } from './usePrototypeInvoiceData';

const SANS_NOM_PORTE: Invoice = {
  id: 'facture-sans-nom',
  invoice_number: 'FACT-2026-001',
  contact_id: 'dc81b97b-6a91-4484-85c1-fe5678008d7e',
  contact_name: null,
  document_type: 'facture', tva_applicable: true, currency: 'EUR',
  issue_date: '2026-09-01T00:00:00Z', due_date: '2026-10-01T00:00:00Z', status: 'draft',
  subtotal_ht: 1100, total_tax: 220, total_ttc: 1320, notes: null, payment_terms: null,
  payment_method: null, late_penalty_rate: null, legal_mentions: null, converted_from_id: null,
  validite_jours: 30, payment_date: null, created_at: '2026-09-01T08:00:00Z',
  updated_at: '2026-09-01T08:00:00Z',
  lines: [{
    id: 'line-1', invoice_id: 'facture-sans-nom', description: 'Accompagnement',
    quantity: 1, unit_price_ht: 1100, tva_rate: 20, total_ht: 1100, total_ttc: 1320,
  }],
};

function contactsIndisponibles(): InvoiceWorkspaceData {
  return {
    invoices: [SANS_NOM_PORTE],
    contacts: [] as Contact[],
    billingProfile: { is_complete: true, missing: [] },
    unavailableSources: ['contacts'],
  };
}

describe('B-015 - contacts illisibles : la carte le dit, elle n’invente pas une absence', () => {
  it('la liste n’affirme pas « Contact introuvable » quand la source est indisponible', () => {
    render(
      <InvoiceWorkspaceCard
        resource={{ status: 'ready', data: contactsIndisponibles(), error: null }}
        onRetry={vi.fn()}
        onOpenInvoice={vi.fn()}
        onCreateDevis={vi.fn()}
        onOpenClassic={vi.fn()}
      />,
    );

    expect(screen.queryByText(/Contact introuvable/)).toBeNull();
    // Et il reste QUELQUE CHOSE à lire : sans cette exigence, vider la
    // mention neutre laisserait « · facture » tout seul, et le test vert.
    expect(screen.getByText(/Client non chargé/)).toBeInTheDocument();
    // Le bandeau de source reste, lui : c'est la seule chose qu'on sache.
    expect(screen.getByText(/Source indisponible : contacts\./)).toBeInTheDocument();
  });

  it('le détail du document non plus', () => {
    render(
      <InvoiceWorkspaceCanvas
        resource={{ status: 'ready', data: contactsIndisponibles(), error: null }}
        invoiceResource={{ status: 'ready', data: SANS_NOM_PORTE, error: null }}
        selection={SANS_NOM_PORTE.id}
        onRetry={vi.fn()}
        onRetryInvoice={vi.fn()}
        onCreateDraft={vi.fn()}
        onCreateContact={vi.fn()}
        onOpenClassic={vi.fn()}
      />,
    );

    const detail = screen.getByTestId('invoice-detail');
    expect(detail).not.toHaveTextContent('Contact introuvable');
    expect(detail).toHaveTextContent('Client non chargé');
  });

  it('témoin : source lisible et contact vraiment absent, l’écran le dit encore', () => {
    // Sans ce témoin, remplacer partout « Contact introuvable » par une
    // mention neutre passerait pour un correctif : on perdrait l'information
    // juste (le contact a bien disparu côté serveur) au lieu de la corriger.
    render(
      <InvoiceWorkspaceCard
        resource={{
          status: 'ready',
          data: { ...contactsIndisponibles(), unavailableSources: [] },
          error: null,
        }}
        onRetry={vi.fn()}
        onOpenInvoice={vi.fn()}
        onCreateDevis={vi.fn()}
        onOpenClassic={vi.fn()}
      />,
    );

    expect(screen.getByText(/Contact introuvable/)).toBeInTheDocument();
  });
});
