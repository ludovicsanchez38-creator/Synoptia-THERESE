import { describe, expect, it } from 'vitest';
import { localDateKey } from './civilDate';

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
