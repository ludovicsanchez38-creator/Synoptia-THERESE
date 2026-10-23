import { readFileSync } from 'node:fs';
import { expect, it } from 'vitest';
it('B-1085 : contrat du libellé ou de la structure', () => {
  const source = readFileSync('src/components/calendar/EventForm.tsx', 'utf8');
  expect(source.includes('Aucun agenda sélectionné. Choisis un agenda dans le menu déroulant.')).toBe(true); expect(source.includes("label: 'Calendrier'")).toBe(false);
});
