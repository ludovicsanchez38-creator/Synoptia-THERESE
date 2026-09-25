/**
 * B-1449 (recette P-146, lots 1 et 3) : B-1388 avait remplacé « Envoyée le »
 * par « Émise le » sur une facture payée, faute de date d'envoi en base. La
 * colonne Envoi affichait donc « Émise le 25/09/2026 » comme un état, et rien
 * ne disait qu'une facture passée de Brouillon à Payée n'était jamais partie.
 * Un brouillon disait aussi « Émise le », alors qu'il n'est pas émis.
 * Tant que l'envoi n'est pas tracé (P-139), la colonne le dit.
 */
import { describe, expect, it } from 'vitest';

import type { Invoice } from '../../services/api';
import { cellulesStatut } from './presentationFacture';

function piece(patch: Partial<Invoice>): Invoice {
  return {
    id: 'i', invoice_number: 'FACT-2026-001', contact_id: 'c', document_type: 'facture', tva_applicable: true,
    currency: 'EUR', issue_date: '2026-09-25T00:00:00Z', due_date: '2026-10-25T00:00:00Z', status: 'draft',
    subtotal_ht: 100, total_tax: 20, total_ttc: 120, notes: null, payment_terms: null, payment_method: null,
    late_penalty_rate: null, legal_mentions: null, converted_from_id: null, validite_jours: null,
    payment_date: null, created_at: '2026-09-25T08:00:00Z', updated_at: '2026-09-25T08:00:00Z', lines: [],
    ...patch,
  } as Invoice;
}

describe('B-1449 : la colonne Envoi ne présente pas l’émission comme un état', () => {
  it('une facture payée dit « Envoi non tracé », date d’émission en dessous', () => {
    const { envoi } = cellulesStatut(piece({ status: 'paid' }));
    expect(envoi.texte).toBe('Envoi non tracé');
    expect('sous' in envoi && envoi.sous).toMatch(/^Émise le /);
  });

  it('un brouillon est daté, pas émis', () => {
    const { envoi } = cellulesStatut(piece({ status: 'draft' }));
    expect(envoi.texte).toBe('Brouillon');
    expect('sous' in envoi && envoi.sous).toMatch(/^Datée du /);
    const devis = cellulesStatut(piece({ status: 'draft', document_type: 'devis' })).envoi;
    expect('sous' in devis && devis.sous).toMatch(/^Daté du /);
  });
});
