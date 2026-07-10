/**
 * BUG-134 - auto-dismiss des toasts : durées par TYPE.
 *
 * 5 s uniformes coupaient la lecture des messages d'erreur/validation de
 * 2 lignes (retour Dr_logic : « le texte explicatif est incomplet »).
 * Spec : success 4 s, info 5 s, warning 8 s, error 10 s ; `duration`
 * explicite respectée ; `duration: 0` = persistant.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useStatusStore } from './statusStore';

function notificationTitles(): string[] {
  return useStatusStore.getState().notifications.map((n) => n.title);
}

describe('BUG-134 - durées d\'auto-dismiss par type', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    useStatusStore.setState({ notifications: [] });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('un warning reste lisible 8 s (pas 5)', () => {
    useStatusStore.getState().addNotification({
      type: 'warning',
      title: 'Champ requis',
      message: "Renseigne la description d'au moins une ligne",
    });

    vi.advanceTimersByTime(5000);
    expect(notificationTitles()).toContain('Champ requis');
    vi.advanceTimersByTime(3000);
    expect(notificationTitles()).not.toContain('Champ requis');
  });

  it('une erreur reste lisible 10 s', () => {
    useStatusStore.getState().addNotification({ type: 'error', title: 'Échec' });

    vi.advanceTimersByTime(8000);
    expect(notificationTitles()).toContain('Échec');
    vi.advanceTimersByTime(2000);
    expect(notificationTitles()).not.toContain('Échec');
  });

  it('un succès disparaît en 4 s', () => {
    useStatusStore.getState().addNotification({ type: 'success', title: 'Enregistré' });

    vi.advanceTimersByTime(4000);
    expect(notificationTitles()).not.toContain('Enregistré');
  });

  it('une durée explicite est respectée', () => {
    useStatusStore.getState().addNotification({
      type: 'warning',
      title: 'Custom',
      duration: 1000,
    });

    vi.advanceTimersByTime(1000);
    expect(notificationTitles()).not.toContain('Custom');
  });

  it('duration: 0 = persistant', () => {
    useStatusStore.getState().addNotification({ type: 'error', title: 'Bloquant', duration: 0 });

    vi.advanceTimersByTime(60000);
    expect(notificationTitles()).toContain('Bloquant');
  });
});
