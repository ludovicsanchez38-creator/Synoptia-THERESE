/**
 * Les symboles de devise, alignés sur `CURRENCY_SYMBOLS` du backend
 * (`services/invoice_pdf.py`). Le PDF imprimait déjà le bon symbole ; c'est
 * l'écran qui écrivait « € » en dur et divergeait de son propre PDF.
 */
const SYMBOLES: Record<string, string> = {
  EUR: '€',
  CHF: 'CHF',
  GBP: '£',
  USD: '$',
  CAD: 'CA$',
};

/**
 * Un montant, arrondi au centime, suivi du symbole de SA devise.
 *
 * Une devise inconnue est rendue par son code plutôt que remplacée par l'euro :
 * mieux vaut « 50.00 JPY » qu'un montant japonais étiqueté en euros.
 */
export function montantAvecDevise(montant: number, devise?: string | null): string {
  const code = devise || 'EUR';
  return `${montant.toFixed(2)} ${SYMBOLES[code] ?? code}`;
}
