/**
 * B-379 : garde de source, les quatre vues (liste, mois, semaine, jour)
 * dérivent leurs clés de jour de clesDeJoursCouverts, et la liste ne
 * reconstruit plus une date UTC depuis une clé civile (B-369).
 */
import { readFileSync } from 'node:fs';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

describe('B-369 / B-379 - CalendarView', () => {
  const src = readFileSync(path.join(__dirname, 'CalendarView.tsx'), 'utf-8');

  it('les quatre vues passent par clesDeJoursCouverts', () => {
    expect((src.match(/clesDeJoursCouverts\(/g) ?? []).length).toBeGreaterThanOrEqual(4);
    expect(src).not.toMatch(/event\.start_date \|\| event\.start_datetime\?\.split\('T'\)\[0\]/);
  });

  it("la liste lit sa clé en local", () => {
    expect(src).not.toMatch(/new Date\(date\)\.toLocaleDateString/);
    expect(src).toContain('parseLocalDateKey(');
  });
});
