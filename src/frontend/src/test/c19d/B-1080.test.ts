import { readFileSync } from 'node:fs';
import { expect, it } from 'vitest';
it('B-1080 : contrat du libellé ou de la structure', () => {
  const source = readFileSync('src/components/invoices/InvoicesPanel.tsx', 'utf8');
  expect(source.includes('aria-label={`Générer et ouvrir le PDF : ${libelleAccessiblePiece(invoice)}`}')).toBe(true); expect(source.includes('aria-label={`Supprimer : ${libelleAccessiblePiece(invoice)}`}')).toBe(true);
});
