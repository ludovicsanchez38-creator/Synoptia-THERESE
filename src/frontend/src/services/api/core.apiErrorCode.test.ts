/** P-056 (revue COCO, finding 7) : un code métier renvoyé par le backend (`{code, message}`) doit survivre jusqu'à l'appelant ; ApiError ne gardait que le message. */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError, request } from './core';

describe('ApiError.code (P-056)', () => {
  const realFetch = global.fetch;
  beforeEach(() => {
    global.fetch = vi.fn(async () => new Response(JSON.stringify({ code: 'outline_cancelled', message: 'Génération de la trame annulée.' }), { status: 409, statusText: 'Conflict', headers: { 'Content-Type': 'application/json' } })) as typeof fetch;
  });
  afterEach(() => { global.fetch = realFetch; });

  it('conserve le code et le message du corps JSON', async () => {
    await expect(request('/api/documents/d1/outline', { method: 'POST' })).rejects.toMatchObject({ name: 'ApiError', status: 409, code: 'outline_cancelled', message: 'Génération de la trame annulée.' });
    expect(new ApiError(500, 'Erreur').code).toBeUndefined();
  });
});
