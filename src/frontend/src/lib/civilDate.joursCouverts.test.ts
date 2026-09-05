/**
 * B-369 et B-379 (05/09/2026), agenda.
 * B-369 : `new Date('2026-09-06')` construit minuit UTC ; à l'ouest de
 * Greenwich, la liste titrait la veille. Une clé civile se lit en composants
 * locaux. B-379 : un événement sur plusieurs jours n'existait que dans la
 * case de son premier jour, dans les quatre vues.
 */
import { afterEach, describe, expect, it } from 'vitest';

import { clesDeJoursCouverts, parseLocalDateKey } from './civilDate';

const TZ_INITIAL = process.env.TZ;

afterEach(() => {
  process.env.TZ = TZ_INITIAL;
});

describe('B-369 - une clé civile se lit en local', () => {
  it('garde le bon jour à Honolulu', () => {
    process.env.TZ = 'Pacific/Honolulu';
    expect(parseLocalDateKey('2026-09-06').getDate()).toBe(6);
    expect(new Date('2026-09-06').getDate()).toBe(5); // le piège corrigé
  });
});

describe('B-379 - les jours couverts par un événement', () => {
  it('une journée entière du 1er au 3 couvre trois clés', () => {
    expect(clesDeJoursCouverts({ all_day: true, start_date: '2026-09-01', end_date: '2026-09-03' })).toEqual([
      '2026-09-01',
      '2026-09-02',
      '2026-09-03',
    ]);
  });

  it('un rendez-vous horodaté garde sa seule clé de début', () => {
    expect(
      clesDeJoursCouverts({ all_day: false, start_datetime: '2026-09-01T23:00:00', end_datetime: '2026-09-02T01:00:00' }),
    ).toEqual(['2026-09-01']);
  });

  it('sans fin, la clé de début seule', () => {
    expect(clesDeJoursCouverts({ all_day: true, start_date: '2026-09-01', end_date: null })).toEqual(['2026-09-01']);
  });
});
