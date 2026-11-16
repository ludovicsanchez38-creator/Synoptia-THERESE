/**
 * B-1983 : Quantité et Prix HT gardent un intitulé visible sous le seuil sm.
 * L'en-tête de grille est `hidden` jusqu'à sm ; une légende dont le plus
 * proche `.hidden` est nul reste lisible sur le petit écran (Vitest ne charge
 * pas Tailwind, la classe fait foi).
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { Contact } from '../../services/api';
import { InvoiceWorkspaceCanvas } from './InvoiceConversationCard';

const contact: Contact = {
  id: 'contact-1', first_name: 'Camille', last_name: 'Martin', company: 'Atelier Martin', email: 'camille@example.test',
  phone: null, address: null, notes: null, tags: [], stage: 'client', score: 80, source: 'local', last_interaction: null,
  created_at: '2026-07-01', updated_at: '2026-07-12',
};

function legendeVisible(texte: string) {
  return screen.getAllByText(texte).find((noeud) => noeud.closest('.hidden') === null);
}

describe('B-1983 : quantité et prix HT restent nommés sous sm', () => {
  it('affiche Qté et Prix HT hors de l’en-tête masqué', () => {
    render(
      <InvoiceWorkspaceCanvas
        resource={{ status: 'ready', data: { invoices: [], contacts: [contact], billingProfile: { is_complete: true, missing: [] }, unavailableSources: [], contactsTronques: false }, error: null }}
        invoiceResource={null}
        selection="new-devis"
        onRetry={vi.fn()}
        onRetryInvoice={vi.fn()}
        onCreateDraft={vi.fn()}
        onCreateContact={vi.fn()}
        onOpenClassic={vi.fn()}
      />,
    );
    expect(legendeVisible('Qté')).toBeTruthy();
    expect(legendeVisible('Prix HT')).toBeTruthy();
  });
});
