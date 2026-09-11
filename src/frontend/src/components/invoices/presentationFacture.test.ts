/**
 * DA « Application affinée », lot 5 : reprises de la revue adverse du diff
 * (points 5, 7 et 8 du rapport). Le module de présentation est testé sans
 * rendu : ce sont des fonctions pures, et le panneau les appelle pour
 * chaque rangée.
 */
import { describe, expect, it } from 'vitest';

import type { Invoice } from '../../services/api';
import { cellulesStatut, sousLignePiece } from './presentationFacture';
import { STATUS_CONFIG } from './statutsFacture';

function piece(patch: Partial<Invoice> = {}): Invoice {
  return {
    id: 'inv-1',
    invoice_number: 'FAC-001',
    contact_id: 'c1',
    contact_name: 'Marie Test',
    document_type: 'facture',
    tva_applicable: true,
    currency: 'EUR',
    issue_date: '2026-03-14T00:00:00Z',
    due_date: '2026-03-31T00:00:00Z',
    status: 'draft',
    subtotal_ht: 100,
    total_tax: 20,
    total_ttc: 120,
    notes: null,
    payment_terms: null,
    payment_method: null,
    late_penalty_rate: null,
    legal_mentions: null,
    converted_from_id: null,
    validite_jours: null,
    payment_date: null,
    created_at: '2026-03-14T00:00:00Z',
    updated_at: '2026-03-14T00:00:00Z',
    lines: [],
    ...patch,
  };
}

describe('Point 5 : une date d’émission hors norme n’emporte pas le panneau', () => {
  it('sousLignePiece ne lève pas sur une issue_date invalide et retombe sur « Facture »', () => {
    // `Intl.DateTimeFormat().format(new Date('…'))` lève `RangeError:
    // Invalid time value` là où `toLocaleDateString` rendait « Invalid Date ».
    // B-010 : le garde serveur ne répare pas les lignes déjà écrites en base.
    expect(() => sousLignePiece(piece({ issue_date: 'pas une date' }))).not.toThrow();
    expect(sousLignePiece(piece({ issue_date: 'pas une date' }))).toBe('Facture');
    expect(() => sousLignePiece(piece({ issue_date: '' }))).not.toThrow();
    expect(sousLignePiece(piece({ issue_date: '' }))).toBe('Facture');
  });

  it('le chemin nominal garde le mois en minuscules', () => {
    expect(sousLignePiece(piece({ issue_date: '2026-03-14T00:00:00Z' }))).toBe('Facture · mars');
    expect(sousLignePiece(piece({ document_type: 'devis' }))).toBe('Devis');
    expect(sousLignePiece(piece({ document_type: 'avoir' }))).toBe('Avoir');
  });
});

describe('Point 7 : « Annulé » s’accorde comme les autres libellés', () => {
  it('un devis et un avoir annulés sont masculins, une facture reste féminine', () => {
    expect(cellulesStatut(piece({ document_type: 'devis', status: 'cancelled' })).envoi.texte).toBe(
      'Annulé',
    );
    expect(cellulesStatut(piece({ document_type: 'avoir', status: 'cancelled' })).envoi.texte).toBe(
      'Annulé',
    );
    expect(
      cellulesStatut(piece({ document_type: 'facture', status: 'cancelled' })).envoi.texte,
    ).toBe('Annulée');
  });
});

describe('Point 8 : un couple type/statut non décrit dit le statut réel', () => {
  it('une facture convertie n’est pas présentée « Impayée »', () => {
    const { envoi, paiement } = cellulesStatut(
      piece({ document_type: 'facture', status: 'converted' }),
    );
    expect(envoi.texte).toMatch(/^Envoyée le /);
    expect('ton' in paiement && paiement.ton).toBe('neutre');
    expect(paiement.texte).toBe(STATUS_CONFIG.converted.label);
    expect(paiement.texte).not.toMatch(/Impay/);
  });

  it('un avoir refusé, expiré ou accepté dit son statut en ton neutre', () => {
    for (const statut of ['accepted', 'refused', 'expired'] as const) {
      const { paiement } = cellulesStatut(piece({ document_type: 'avoir', status: statut }));
      expect('ton' in paiement && paiement.ton, statut).toBe('neutre');
      expect(paiement.texte, statut).toBe(STATUS_CONFIG[statut].label);
    }
  });

  it('le couple décrit facture/avoir + sent reste « Impayée » / « Impayé » en attention', () => {
    const facture = cellulesStatut(piece({ document_type: 'facture', status: 'sent' })).paiement;
    expect('ton' in facture && facture.ton).toBe('attention');
    expect(facture.texte).toBe('Impayée');

    const avoir = cellulesStatut(piece({ document_type: 'avoir', status: 'sent' })).paiement;
    expect('ton' in avoir && avoir.ton).toBe('attention');
    expect(avoir.texte).toBe('Impayé');
  });
});
