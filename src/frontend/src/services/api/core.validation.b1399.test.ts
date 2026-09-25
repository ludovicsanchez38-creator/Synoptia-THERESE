/**
 * B-1399 (persona Zoé, cycle 13) : un prénom de 300 caractères donnait
 * « Données invalides dans la requête », sans le champ ni la limite, alors que
 * le moteur les renvoie (`details: [{field, message}]`). Le message affiché
 * nomme le champ et dit la règle, en français.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { request } from './core';

function repondre(details: Array<{ field: string; message: string }>) {
  global.fetch = vi.fn(async () => new Response(JSON.stringify({
    code: 'VALIDATION_ERROR', message: 'Données invalides dans la requête', details,
  }), { status: 422, statusText: 'Unprocessable Entity', headers: { 'Content-Type': 'application/json' } })) as typeof fetch;
}

describe('ApiError 422 lisible (B-1399)', () => {
  const realFetch = global.fetch;
  beforeEach(() => vi.clearAllMocks());
  afterEach(() => { global.fetch = realFetch; });

  it('nomme le champ et dit la limite', async () => {
    repondre([{ field: 'first_name', message: 'String should have at most 200 characters' }]);
    await expect(request('/api/memory/contacts', { method: 'POST' }))
      .rejects.toMatchObject({ status: 422, message: 'Prénom : 200 caractères au maximum.' });
  });

  it('un champ obligatoire et un champ inconnu se disent aussi', async () => {
    repondre([
      { field: 'title', message: 'Field required' },
      { field: 'champ_maison', message: 'Valeur étrange' },
    ]);
    await expect(request('/api/tasks', { method: 'POST' }))
      .rejects.toMatchObject({ message: 'Titre : obligatoire. champ_maison : Valeur étrange.' });
  });

  it('sans détail, le message du moteur reste', async () => {
    repondre([]);
    await expect(request('/api/tasks', { method: 'POST' }))
      .rejects.toMatchObject({ message: 'Données invalides dans la requête' });
  });
});
