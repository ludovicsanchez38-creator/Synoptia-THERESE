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
    // B-605 : quatre occurrences dans le fichier ne prouvent pas quatre vues ;
    // on découpe le source par vue et on exige l'appel dans chacune.
    const vues = ['ListView', 'MonthView', 'WeekView', 'DayView'];
    const positions = vues.map((v) => src.search(new RegExp(`function ${v}\\b`)));
    positions.forEach((p, i) => expect(p, `${vues[i]} introuvable`).toBeGreaterThan(-1));
    const tri = [...positions].sort((a, b) => a - b);
    for (const [i, debut] of tri.entries()) {
      const fin = tri[i + 1] ?? src.length;
      const nom = vues[positions.indexOf(debut)];
      expect(src.slice(debut, fin), `${nom} ne passe pas par clesDeJoursCouverts`).toMatch(/clesDeJoursCouverts\(/);
    }
    expect(src).not.toMatch(/event\.start_date \|\| event\.start_datetime\?\.split\('T'\)\[0\]/);
  });

  it("la liste lit sa clé en local", () => {
    expect(src).not.toMatch(/new Date\(date\)\.toLocaleDateString/);
    expect(src).toContain('parseLocalDateKey(');
  });
});
