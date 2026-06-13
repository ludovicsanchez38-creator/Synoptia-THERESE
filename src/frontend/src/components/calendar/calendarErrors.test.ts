import { describe, it, expect } from 'vitest';
import { isGoogleAuthError, classifyCalendarError } from './calendarErrors';

const MSG_403 =
  "Google refuse l'accès au calendrier (403). Active l'API « Google Calendar » dans ta " +
  'console Google Cloud (APIs et services > Bibliothèque > Google Calendar API > Activer), ' +
  "puis relance la synchronisation. Si le souci persiste, vérifie que l'accès au calendrier " +
  'a bien été autorisé pour ce compte.';

describe('isGoogleAuthError (BUG-109 / boucle "connexion expirée", lcjp 12/06/2026)', () => {
  it('classe une vraie expiration / credentials manquants comme reauth (cas légitime backend 401)', () => {
    // Message réel levé par ensure_valid_access_token (email.py) quand le refresh échoue
    expect(isGoogleAuthError('OAuth credentials not found. Please reconnect your account.')).toBe(true);
    expect(isGoogleAuthError('token expired')).toBe(true);
    expect(isGoogleAuthError('refresh token revoked')).toBe(true);
    expect(isGoogleAuthError('Unauthorized (401)')).toBe(true);
  });

  it('NE classe PAS un 403 calendrier comme expiration (sinon bannière trompeuse + boucle infinie)', () => {
    const msg403 =
      "Google refuse l'accès au calendrier (403). Active l'API « Google Calendar » dans ta " +
      'console Google Cloud (APIs et services > Bibliothèque > Google Calendar API > Activer), ' +
      "puis relance la synchronisation. Si le souci persiste, vérifie que l'accès au calendrier " +
      'a bien été autorisé pour ce compte.';
    expect(isGoogleAuthError(msg403)).toBe(false);
  });

  it('ignore les erreurs génériques et les valeurs vides', () => {
    expect(isGoogleAuthError('Impossible de charger les calendriers')).toBe(false);
    expect(isGoogleAuthError('')).toBe(false);
    expect(isGoogleAuthError(null)).toBe(false);
    expect(isGoogleAuthError(undefined)).toBe(false);
  });
});

describe('classifyCalendarError', () => {
  it('arme la reconnexion sur une vraie expiration', () => {
    expect(classifyCalendarError('Please reconnect your account.', { fallback: 'X' })).toEqual({
      error: 'Connexion Google expirée.',
      needsReauth: true,
    });
  });

  it('DÉSARME la reconnexion sur un 403 calendrier et affiche le message actionnable (BUG-109)', () => {
    // Le point clé du must-fix : needsReauth doit repasser à false, sinon la
    // bannière jaune (état partagé avec l'email) masque le message et boucle.
    const action = classifyCalendarError(MSG_403, { fallback: 'X' });
    expect(action.error).toBe(MSG_403);
    expect(action.needsReauth).toBe(false);
  });

  it('ne touche PAS à needsReauth sur une erreur générique', () => {
    expect(classifyCalendarError('boom réseau', { fallback: 'Échec de la synchronisation' })).toEqual({
      error: 'Échec de la synchronisation',
    });
  });

  it("n'affiche rien sur erreur générique si du cache est disponible", () => {
    expect(classifyCalendarError('boom', { fallback: 'X', hasCache: true })).toEqual({ error: null });
  });
});
