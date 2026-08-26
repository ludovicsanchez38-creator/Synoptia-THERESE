/**
 * Revue Soso S2-4 : les tarifs des modèles sont relevés en USD chez tous les
 * fournisseurs (docs officielles). Les afficher avec « € » sans conversion
 * annonce un chiffre commercial FAUX (~9 % d'écart au taux courant).
 * Tant qu'aucun taux n'est sourcé dans l'app, on dit la vérité : USD.
 */
import { describe, expect, it } from 'vitest';

import { formaterCout, UNITE_COUT } from './coutAffiche';

describe('L’unité du coût dit la vérité', () => {
  it('affiche des dollars, jamais des euros non convertis', () => {
    expect(UNITE_COUT).toBe('$');
    expect(formaterCout(4)).toBe('4.00 $');
    expect(formaterCout(0.0123, 4)).toBe('0.0123 $');
  });

  it('tolère l’absence de montant', () => {
    expect(formaterCout(undefined)).toBe('—');
    expect(formaterCout(null)).toBe('—');
  });
});
