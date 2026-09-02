/**
 * B-228 : une seule pression d'Échap fermait DEUX couches.
 *
 * `consommeEchapUnifie` (ConversationCanvasPrototype) interroge d'abord la pile
 * `runTopEscapeHandler`, puis les modales du panelStore. La modale « Nouvelle
 * facture » n'était ni dans l'une ni dans l'autre : la fonction rendait false,
 * la cascade tombait sur `else if (embeddedView) collapseEmbeddedView()` et
 * démontait le panneau Devis et factures — donc son enfant, brouillon compris.
 * La fiche des raccourcis promet pourtant « Fermer le panneau actif », au
 * singulier, et cinq autres surfaces modales s'inscrivent bien dans la pile.
 *
 * Le commentaire d'autorité de la coque le dit déjà : « Une surface nouvelle
 * doit s'inscrire dans l'une des deux — il n'y a pas de troisième endroit. »
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';
import { useBillingProfileStore } from '../../stores/billingProfileStore';
import { _clearEscapeHandlers, runTopEscapeHandler } from '../../lib/escapeStack';
import type { Invoice } from '../../services/api';

const { getBillingProfileStatusMock } = vi.hoisted(() => ({
  getBillingProfileStatusMock: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
}));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    listContacts: vi.fn().mockResolvedValue([
      { id: 'contact-1', first_name: 'Jean', last_name: 'Dupont', email: 'jean@example.com' },
    ]),
    createInvoice: vi.fn(),
    getBillingProfileStatus: getBillingProfileStatusMock,
  };
});

const devis: Invoice = {
  id: 'devis-1', invoice_number: 'DEV-2026-001', contact_id: 'contact-1',
  document_type: 'devis', tva_applicable: true, currency: 'EUR',
  issue_date: '2026-07-01T00:00:00Z', due_date: '2026-07-31T00:00:00Z', status: 'sent',
  subtotal_ht: 100, total_tax: 20, total_ttc: 120, notes: null, payment_terms: null,
  payment_method: null, late_penalty_rate: null, legal_mentions: null, converted_from_id: null,
  validite_jours: null, payment_date: null, created_at: '2026-07-01T08:00:00Z',
  updated_at: '2026-07-01T08:00:00Z',
  lines: [{
    id: 'line-1', invoice_id: 'devis-1', description: 'Accompagnement',
    quantity: 1, unit_price_ht: 100, tva_rate: 20, total_ht: 100, total_ttc: 120,
  }],
};

describe('B-228 : Échap ne ferme que la modale de facture', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _clearEscapeHandlers();
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [] });
    useBillingProfileStore.setState({ missing: null });
  });

  afterEach(() => {
    _clearEscapeHandlers();
  });

  it("la modale s'inscrit dans la pile Échap, et une pression ferme le formulaire seul", async () => {
    const fermer = vi.fn();
    render(<InvoiceForm invoice={null} onClose={fermer} onSave={vi.fn()} />);

    await screen.findByLabelText(/Client/i);

    // La pile a un preneur : la cascade de la coque s'arrête là et ne descend
    // donc jamais jusqu'à `collapseEmbeddedView()`, qui démonterait le panneau.
    expect(runTopEscapeHandler()).toBe(true);
    expect(fermer).toHaveBeenCalledTimes(1);
  });

  it('le dialogue de conversion imbriqué se ferme avant le formulaire (LIFO)', async () => {
    const fermer = vi.fn();
    render(<InvoiceForm invoice={devis} onClose={fermer} onSave={vi.fn()} />);

    fireEvent.click(await screen.findByRole('button', { name: /Convertir en facture/i }));
    await screen.findByRole('dialog', { name: /Confirmer la conversion/i });

    // Le dessus de la pile est le dialogue de conversion, pas le formulaire.
    expect(runTopEscapeHandler()).toBe(true);
    await waitFor(() =>
      expect(screen.queryByRole('dialog', { name: /Confirmer la conversion/i })).toBeNull(),
    );
    expect(fermer).not.toHaveBeenCalled();

    // Et le formulaire reste joignable au coup suivant.
    expect(runTopEscapeHandler()).toBe(true);
    expect(fermer).toHaveBeenCalledTimes(1);
  });
});
