import { afterEach, describe, expect, it, vi } from 'vitest';
import { initiateCRMOAuth, handleCRMOAuthCallback, syncCRM } from './crm-extended';

afterEach(() => vi.unstubAllGlobals());

describe.each([
  ['connexion', () => initiateCRMOAuth(), 'La connexion au CRM n’a pas pu démarrer'],
  ['retour de connexion', () => handleCRMOAuthCallback('etat-fictif', 'code-fictif'), 'La connexion au CRM n’a pas pu être finalisée'],
  ['synchronisation', () => syncCRM(), 'La synchronisation du CRM a échoué'],
] as const)('B-1967 : erreur de %s', (_etape, appeler, message) => {
  it.each(['{}', 'Service Unavailable'])('le repli est en français avec le statut HTTP, corps %s', async (body) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(body, { status: 503, statusText: 'Service Unavailable' })));
    await expect(appeler()).rejects.toThrow(`${message} (erreur 503).`);
  });

  it('conserve le détail donné par le moteur', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: 'La connexion a expiré.' }), { status: 503 })));
    await expect(appeler()).rejects.toThrow('La connexion a expiré.');
  });

  it('R1-8 : conserve le message du handler HTTP du moteur', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
      code: 'HTTP_ERROR', message: 'La connexion a expiré.',
    }), { status: 400 })));
    await expect(appeler()).rejects.toThrow('La connexion a expiré.');
  });

  it('R1-8 : un corps JSON nul garde le repli et son statut', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('null', { status: 503 })));
    await expect(appeler()).rejects.toThrow(`${message} (erreur 503).`);
  });
});
