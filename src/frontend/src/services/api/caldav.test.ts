/**
 * B-129 : les deux routes CalDAV ont enfin un appelant, et c'est bien
 * `caldav-test` / `caldav-setup` qui sont appelées. Un composant qui n'appelle
 * pas la bonne route laisse la porte fermée tout en ayant l'air ouverte.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockApiFetch = vi.fn();

vi.mock('./core', async () => {
  const actual = await vi.importActual<typeof import('./core')>('./core');
  return {
    ...actual,
    API_BASE: 'http://127.0.0.1:17293',
    apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  };
});

import { setupCaldavCalendars, testCaldavConnection } from './calendar';

const identifiants = {
  url: 'https://cloud.exemple.fr/remote.php/dav',
  username: 'ludo',
  password: 'motdepasse-application',
};

describe('API CalDAV', () => {
  beforeEach(() => vi.clearAllMocks());

  it('testCaldavConnection appelle POST /calendars/caldav-test', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ success: true, message: 'ok', calendars: [] }),
    });

    await testCaldavConnection(identifiants);

    expect(mockApiFetch).toHaveBeenCalledWith(
      'http://127.0.0.1:17293/api/calendar/calendars/caldav-test',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(identifiants),
      }),
    );
  });

  it('setupCaldavCalendars appelle POST /calendars/caldav-setup', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve([{ id: 'c1', summary: 'Personnel' }]),
    });

    await setupCaldavCalendars(identifiants);

    expect(mockApiFetch).toHaveBeenCalledWith(
      'http://127.0.0.1:17293/api/calendar/calendars/caldav-setup',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(identifiants),
      }),
    );
  });

  it('une réponse en erreur remonte le motif du serveur', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: () => Promise.resolve({ detail: 'Connection failed: 401 Unauthorized' }),
    });

    await expect(setupCaldavCalendars(identifiants)).rejects.toThrow(/401/);
  });
});
