/** Cycle 6, persona Sophie (sophie-05) : un refus de variable montrait l'enveloppe JSON du serveur. */
import { describe, expect, it, vi } from 'vitest';

const apiFetch = vi.fn();
vi.mock('./core', async () => {
  const actual = await vi.importActual<typeof import('./core')>('./core');
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});

import { createVariable } from './variables';

describe('variables — un refus est une phrase, pas une enveloppe JSON', () => {
  it('409 : le message du serveur est repris tel quel', async () => {
    const corps = { code: 'HTTP_ERROR', message: 'La variable « nom_client » existe déjà. Utilise « remplacer » pour changer sa valeur.' };
    apiFetch.mockResolvedValue(new Response(JSON.stringify(corps), { status: 409, statusText: 'Conflict', headers: { 'Content-Type': 'application/json' } }));
    await expect(createVariable('nom_client', 'text', 'x')).rejects.toMatchObject({ status: 409, message: corps.message });
  });

  it('422 : la validation est lisible aussi', async () => {
    const corps = { code: 'VALIDATION_ERROR', message: 'Données invalides dans la requête', details: [{ field: 'name', message: 'Nom invalide' }] };
    apiFetch.mockResolvedValue(new Response(JSON.stringify(corps), { status: 422, statusText: 'Unprocessable', headers: { 'Content-Type': 'application/json' } }));
    await expect(createVariable('mauvais-nom', 'text', 'x')).rejects.toSatisfy((e: Error) => !e.message.trim().startsWith('{') && e.message.includes('invalide'));
  });
});
