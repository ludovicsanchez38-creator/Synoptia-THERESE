/**
 * B-1355 (persona Claire, cycle 13) : dans le panneau « Facturer », la ligne
 * du devis débordait (le bouton « Supprimer la ligne 1 » finissait à 1 305 px
 * pour un panneau qui s'arrête à 1 280), et quantité et prix n'avaient aucune
 * étiquette visible (seulement « 1 » et « 0 »).
 *
 * Un champ de formulaire garde sa largeur intrinsèque dans une grille tant
 * qu'il n'a pas `min-w-0` : la colonne souple ne pouvait pas rétrécir. Les
 * colonnes portent désormais un intitulé visible.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { Contact, Invoice } from '../../services/api';
import { InvoiceWorkspaceCanvas } from './InvoiceConversationCard';
import type { InvoiceWorkspaceData } from './usePrototypeInvoiceData';

const contact: Contact = {
  id: 'contact-1', first_name: 'Camille', last_name: 'Martin', company: 'Atelier Martin', email: 'camille@example.test',
  phone: null, address: null, notes: null, tags: [], stage: 'client', score: 80, source: 'local', last_interaction: null,
  created_at: '2026-07-01', updated_at: '2026-07-12',
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

describe('ligne de devis du panneau Facturer (B-1355)', () => {
  it('chaque champ de la ligne peut rétrécir dans sa colonne', () => {
    rendre({});
    const description = screen.getByLabelText('Description ligne 1');
    const ligne = description.parentElement as HTMLElement;
    for (const champ of Array.from(ligne.children)) {
      expect(champ.className, champ.getAttribute('aria-label') ?? champ.tagName).toMatch(/\bmin-w-0\b/);
    }
  });

  it('les colonnes ont des intitulés visibles', () => {
    rendre({});
    const entete = screen.getByTestId('devis-lignes-entete');
    for (const intitule of ['Description', 'Qté', 'Prix HT', 'TVA']) {
      expect(entete.textContent).toContain(intitule);
    }
  });
});
