/**
 * B-412 (cycle 4) : « Hier » désignait « entre 24 et 48 heures », si bien
 * qu'un élément d'avant-hier soir était annoncé « Hier » le surlendemain
 * matin. Décision : « Hier » et « Il y a N jours » se comptent en jours
 * civils, comme les dates civiles de l'agenda ; sous 24 heures, l'affichage
 * en heures reste.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { formatRelativeDate } from './utils';

describe('formatRelativeDate : jours civils', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-09-07T08:00:00'));
  });
  afterEach(() => vi.useRealTimers());

  it("avant-hier soir n'est pas « Hier »", () => {
    expect(formatRelativeDate(new Date('2026-09-05T23:00:00'))).toBe('Il y a 2 jours');
  });

  it('hier soir, à moins de 24 heures, reste en heures (plus précis que « Hier »)', () => {
    expect(formatRelativeDate(new Date('2026-09-06T23:30:00'))).toBe('Il y a 8h');
  });

  it('hier matin est « Hier »', () => {
    expect(formatRelativeDate(new Date('2026-09-06T07:00:00'))).toBe('Hier');
  });

  it("ce matin plus tôt reste en heures", () => {
    expect(formatRelativeDate(new Date('2026-09-07T05:00:00'))).toBe('Il y a 3h');
  });

  it('il y a six jours civils reste en jours, sept passe à la date', () => {
    expect(formatRelativeDate(new Date('2026-09-01T23:00:00'))).toBe('Il y a 6 jours');
    expect(formatRelativeDate(new Date('2026-08-31T23:00:00'))).toBe('31 août');
  });
});
