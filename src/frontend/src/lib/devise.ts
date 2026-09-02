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
 * B-221 : le montant s'écrit à la française — virgule décimale, milliers
 * séparés — parce que c'est un produit français qui écrit des sommes à ses
 * clients. `toFixed(2)` rendait « 2400.00 € » sur le seul écran où
 * l'application chiffre, quand quatre autres surfaces formataient déjà en
 * fr-FR.
 */
const NOMBRE_FR = new Intl.NumberFormat('fr-FR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/**
 * L'espace insécable U+00A0, celle qu'`Intl` place avant un symbole monétaire.
 *
 * Écrite par son code point et non en clair : une insécable littérale est
 * refusée par `no-irregular-whitespace`, et son échappement littéral par la
 * garde BUG-096 (un échappement JS reste tel quel dans un nœud texte JSX).
 */
const INSECABLE = String.fromCharCode(0xa0);

/**
 * Un montant, arrondi au centime, suivi du symbole de SA devise.
 *
 * Une devise inconnue est rendue par son code plutôt que remplacée par l'euro :
 * mieux vaut « 50,00 JPY » qu'un montant japonais étiqueté en euros. Les
 * centimes sont toujours écrits, y compris pour les devises sans subdivision :
 * une facture montre ses centimes.
 *
 * L'espace qui précède le symbole est insécable (U+00A0), comme celle que pose
 * `Intl.NumberFormat` en style monétaire : un montant ne se coupe pas en fin
 * de ligne.
 */
export function montantAvecDevise(montant: number, devise?: string | null): string {
  const code = devise || 'EUR';
  return `${NOMBRE_FR.format(montant)}${INSECABLE}${SYMBOLES[code] ?? code}`;
}
