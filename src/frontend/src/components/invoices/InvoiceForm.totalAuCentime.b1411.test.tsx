/**
 * B-1411 (relevé par la RFC P-121, reproduit ici) : la modale sommait des
 * montants bruts et n'arrondissait qu'à l'affichage. Trois lignes de 33,33 €
 * à 20 % affichaient 119,99 € pour une pièce que le serveur enregistre à
 * 120,00 € (`_montants_de_ligne`, arrondi à la ligne). Le panneau Facturer
 * arrondissait déjà là où le montant naît (B-017) ; la modale fait de même.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { Invoice } from '../../services/api';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    listContacts: vi.fn().mockResolvedValue([{ id: 'c1', first_name: 'Jean', last_name: 'Dupont', email: 'j@example.com' }]),
    getBillingProfileStatus: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
  };
});

import { InvoiceForm } from './InvoiceForm';

const ligne = (id: string) => ({ id, invoice_id: 'inv-1', description: 'Séance', quantity: 1, unit_price_ht: 33.33, tva_rate: 20, total_ht: 33.33, total_ttc: 40 });
const piece = {
  id: 'inv-1', invoice_number: 'DEV-2026-001', contact_id: 'c1', document_type: 'devis', tva_applicable: true, currency: 'EUR',
  issue_date: '2026-09-25T00:00:00Z', due_date: '2026-10-25T00:00:00Z', status: 'draft', subtotal_ht: 99.99, total_tax: 20.01,
  total_ttc: 120, notes: null, payment_terms: null, payment_method: null, late_penalty_rate: null, legal_mentions: null,
  converted_from_id: null, validite_jours: 30, payment_date: null, created_at: '2026-09-25T08:00:00Z',
  updated_at: '2026-09-25T08:00:00Z', lines: [ligne('l1'), ligne('l2'), ligne('l3')],
} as unknown as Invoice;

describe('B-1411 : la modale annonce le total que le serveur enregistre', () => {
  it('trois lignes de 33,33 € à 20 % : 120,00 € TTC, pas 119,99 €', async () => {
    render(<InvoiceForm invoice={piece} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByDisplayValue('DEV-2026-001').catch(() => null);

    const texte = document.body.textContent ?? '';
    expect(texte).toMatch(/120[,.]00/);
    expect(texte).not.toMatch(/119[,.]99/);
  });
});
