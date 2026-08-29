/**
 * Un montant s'affiche dans SA devise.
 *
 * Trouvé par F1 (test de cohérence entre couches, 0.55) : le panneau
 * Facturation écrivait `{invoice.total_ttc.toFixed(2)} €`, l'euro en dur.
 * Une facture en CHF ou en USD s'y affichait donc étiquetée en euros — un
 * montant juste, une devise fausse, ce qui est pire qu'un montant absent.
 *
 * Le backend a déjà sa table (`CURRENCY_SYMBOLS` dans invoice_pdf.py) : le PDF
 * imprime le bon symbole depuis longtemps. C'est l'écran qui divergeait de son
 * propre PDF.
 */
import { describe, expect, it } from 'vitest';

import { montantAvecDevise } from './devise';

describe('Un montant porte sa devise', () => {
  it('affiche le symbole de la devise du document', () => {
    expect(montantAvecDevise(1200, 'EUR')).toBe('1200.00 €');
    expect(montantAvecDevise(1200, 'CHF')).toBe('1200.00 CHF');
    expect(montantAvecDevise(1200, 'USD')).toBe('1200.00 $');
    expect(montantAvecDevise(1200, 'GBP')).toBe('1200.00 £');
  });

  it("rend le code tel quel pour une devise qu'on ne connaît pas", () => {
    expect(montantAvecDevise(50, 'JPY')).toBe('50.00 JPY');
  });

  it('ne suppose pas l’euro quand la devise manque', () => {
    expect(montantAvecDevise(50, undefined)).toBe('50.00 €');
  });

  it('arrondit à deux décimales', () => {
    expect(montantAvecDevise(0.30000000000000004, 'EUR')).toBe('0.30 €');
  });
});
