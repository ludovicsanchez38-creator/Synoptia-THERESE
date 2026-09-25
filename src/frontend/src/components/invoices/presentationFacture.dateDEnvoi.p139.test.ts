/**
 * P-139 (acceptée le 25/09) : le moteur garde la date du premier envoi
 * (sent_at). Quand elle est connue, la colonne Envoi la dit, y compris sur
 * une facture payée, à la place d'« Envoi non tracé » (B-1449) ; sans elle
 * (pièces anciennes), l'affichage reste celui d'avant.
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

describe('P-139 : la colonne Envoi dit la date d’envoi quand elle est tracée', () => {
  it('une facture envoyée : la date d’envoi, pas celle d’émission', () => {
    const { envoi } = cellulesStatut(piece({ status: 'sent', sent_at: '2026-09-28T09:00:00+00:00' }));
    expect(envoi.texte).toBe('Envoyée le 28/09/2026');
  });

  it('une facture payée et envoyée : plus d’« Envoi non tracé »', () => {
    const { envoi } = cellulesStatut(piece({ status: 'paid', sent_at: '2026-09-28T09:00:00+00:00' }));
    expect(envoi.texte).toBe('Envoyée le 28/09/2026');
  });

  it('un devis envoyé : masculin', () => {
    const { envoi } = cellulesStatut(piece({ status: 'sent', document_type: 'devis', sent_at: '2026-09-28T09:00:00+00:00' }));
    expect(envoi.texte).toBe('Envoyé le 28/09/2026');
  });

  it('sans date tracée, l’affichage d’avant reste', () => {
    expect(cellulesStatut(piece({ status: 'paid' })).envoi.texte).toBe('Envoi non tracé');
    expect(cellulesStatut(piece({ status: 'sent' })).envoi.texte).toBe('Envoyée le 25/09/2026');
  });
});
