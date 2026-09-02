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
 *
 * B-221 a changé le contrat de FORME : le nombre s'écrit en fr-FR (virgule
 * décimale, milliers séparés par une espace fine insécable U+202F) et le
 * symbole est précédé d'une insécable U+00A0. Les attentes sont construites
 * avec `Intl`, jamais tapées au clavier : une espace ordinaire aurait fait
 * échouer du code correct.
 */
import { describe, expect, it } from 'vitest';

import { montantAvecDevise } from './devise';

const fr = (montant: number) =>
  new Intl.NumberFormat('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    .format(montant);
const attendu = (montant: number, symbole: string) => `${fr(montant)}\u00A0${symbole}`;

describe('Un montant porte sa devise', () => {
  it('affiche le symbole de la devise du document', () => {
    expect(montantAvecDevise(1200, 'EUR')).toBe(attendu(1200, '€'));
    expect(montantAvecDevise(1200, 'CHF')).toBe(attendu(1200, 'CHF'));
    expect(montantAvecDevise(1200, 'USD')).toBe(attendu(1200, '$'));
    expect(montantAvecDevise(1200, 'GBP')).toBe(attendu(1200, '£'));
  });

  it("rend le code tel quel pour une devise qu'on ne connaît pas", () => {
    expect(montantAvecDevise(50, 'JPY')).toBe(attendu(50, 'JPY'));
  });

  it('ne suppose pas l’euro quand la devise manque', () => {
    expect(montantAvecDevise(50, undefined)).toBe(attendu(50, '€'));
  });

  it('arrondit à deux décimales', () => {
    expect(montantAvecDevise(0.30000000000000004, 'EUR')).toBe(attendu(0.3, '€'));
  });
});
