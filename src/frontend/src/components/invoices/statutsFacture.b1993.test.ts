import { describe, expect, it } from 'vitest';
import { libelleStatutPiece } from './statutsFacture';

describe('B-1993 : les statuts s’accordent avec le type de pièce', () => {
  it.each([
    ['accepted', 'Acceptée', 'Accepté'],
    ['refused', 'Refusée', 'Refusé'],
    ['expired', 'Expirée', 'Expiré'],
    ['converted', 'Convertie', 'Converti'],
  ])('%s reste féminin pour une facture et masculin pour devis et avoir', (statut, feminin, masculin) => {
    expect(libelleStatutPiece(statut, 'facture')).toBe(feminin);
    expect(libelleStatutPiece(statut, 'devis')).toBe(masculin);
    expect(libelleStatutPiece(statut, 'avoir')).toBe(masculin);
  });
});
