import { describe, expect, it } from 'vitest';
import { isPastParisCivilDate, localDateKey } from './civilDate';

describe('localDateKey - clé de jour civile', () => {
  it('reflète la date locale, pas la date UTC', () => {
    // Minuit et demi local : en fuseau positif (France), toISOString rend la
    // VEILLE - le bug qui décalait tout le calendrier d'un jour.
    const d = new Date(2026, 6, 18, 0, 30);
    expect(localDateKey(d)).toBe('2026-07-18');
    if (d.getTimezoneOffset() < 0) {
      // Fuseau à l'est d'UTC (cas de la France) : la clé UTC serait fausse.
      expect(d.toISOString().split('T')[0]).toBe('2026-07-17');
    }
  });

  it('pad les mois et jours à deux chiffres', () => {
    expect(localDateKey(new Date(2026, 0, 5, 12))).toBe('2026-01-05');
  });
});

describe('isPastParisCivilDate - échéance métier', () => {
  const soirDu4Septembre = new Date('2026-09-04T20:30:00+02:00');

  it('ne classe pas une tâche du jour comme en retard après minuit', () => {
    expect(isPastParisCivilDate('2026-09-04T00:00:00', soirDu4Septembre)).toBe(false);
  });

  it('classe la veille en retard et pas le lendemain', () => {
    expect(isPastParisCivilDate('2026-09-03T23:59:00+02:00', soirDu4Septembre)).toBe(true);
    expect(isPastParisCivilDate('2026-09-05T00:00:00+02:00', soirDu4Septembre)).toBe(false);
  });

  it('convertit une échéance zonée vers le jour de Paris', () => {
    // 22 h 30 UTC appartient déjà au 5 septembre à Paris.
    expect(isPastParisCivilDate('2026-09-04T22:30:00Z', soirDu4Septembre)).toBe(false);
  });
});
