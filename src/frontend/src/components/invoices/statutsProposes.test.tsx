/**
 * Le sélecteur de statut ne propose pas « Accepté » sur une facture.
 *
 * « Accepté » est un statut de DEVIS. Le choisir sur une facture la sortait de
 * l'encours, qui ne regarde que `sent` et `overdue` : une créance de 1 200 €
 * disparaissait par un clic de menu. Le backend refuse désormais, mais laisser
 * l'option à l'écran remplacerait une perte silencieuse par une erreur — le
 * choix ne doit pas être offert.
 *
 * Ce test REND le formulaire et lit les options, plutôt que de relire le JSX :
 * la branche `documentType === 'devis' ? … : …` était juste sous les yeux et
 * proposait la même option des deux côtés.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<Record<string, unknown>>('../../services/api');
  return {
    ...reel,
    listContacts: vi.fn().mockResolvedValue([]),
    getBillingProfileStatus: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
  };
});

function piece(documentType: 'devis' | 'facture') {
  return {
    id: 'inv-1', invoice_number: documentType === 'devis' ? 'DEV-2026-001' : 'FACT-2026-001',
    contact_id: 'c-1', document_type: documentType, tva_applicable: true, currency: 'EUR',
    issue_date: '2026-08-01T00:00:00Z', due_date: '2026-09-01T00:00:00Z', status: 'sent',
    subtotal_ht: 1000, total_tax: 200, total_ttc: 1200, notes: null, payment_terms: null,
    payment_method: null, late_penalty_rate: null, legal_mentions: null,
    converted_from_id: null, validite_jours: 30, payment_date: null,
    created_at: '2026-08-01T00:00:00Z', updated_at: '2026-08-01T00:00:00Z',
    lines: [{ id: 'l-1', invoice_id: 'inv-1', description: 'Prestation', quantity: 1,
              unit_price_ht: 1000, tva_rate: 20, total_ht: 1000, total_ttc: 1200 }],
  };
}

// B-1537 : une facture envoyée ne propose plus « Brouillon » ; le sélecteur
// se trouve par son nom, plus par cette option.
function statutsProposes(): string[] {
  const statut = screen.getByLabelText('Statut') as HTMLSelectElement;
  return Array.from(statut.querySelectorAll('option')).map((o) => o.value);
}

describe('Les statuts proposés suivent le type du document', () => {
  it("une facture ne propose pas « Accepté »", async () => {
    render(<InvoiceForm invoice={piece('facture') as never} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByLabelText('Statut');

    expect(statutsProposes()).not.toContain('accepted');
  });

  it('une facture propose bien ses propres statuts', async () => {
    render(<InvoiceForm invoice={piece('facture') as never} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByLabelText('Statut');

    const statuts = statutsProposes();
    // Envoyée, donc émise : plus de retour au brouillon (B-1506, B-1537).
    expect(statuts).toEqual(expect.arrayContaining(['sent', 'paid', 'overdue', 'cancelled']));
    expect(statuts).not.toContain('draft');
  });

  it('un devis garde « Accepté »', async () => {
    render(<InvoiceForm invoice={piece('devis') as never} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByLabelText('Statut');

    expect(statutsProposes()).toContain('accepted');
  });
});
