import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockRequest = vi.fn();

vi.mock('./core', async () => {
  const actual = await vi.importActual<typeof import('./core')>('./core');
  return { ...actual, request: (...args: unknown[]) => mockRequest(...args) };
});

import { searchMemory } from './memory';

describe('searchMemory', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRequest.mockResolvedValue({ query: '', results: [], total: 0, search_time_ms: 0 });
  });

  // Trouvé le 01/09/2026 pendant la cartographie. Le client envoyait `types`,
  // le schéma serveur attend `entity_types` (MemorySearchRequest, schemas.py),
  // et Pydantic ignore en silence un champ qu'il ne connaît pas : le filtre par
  // type n'était JAMAIS appliqué. Les valeurs divergeaient aussi — pluriel côté
  // client, singulier côté serveur — donc renommer seul aurait produit un 422.
  // Le seul test existant bouchonnait searchMemory, il ne pouvait pas le voir.
  it('envoie le nom de champ et les valeurs que le serveur sait lire', async () => {
    await searchMemory('jean', ['contacts', 'projects']);

    const [, options] = mockRequest.mock.calls[0] as [string, { body: string }];
    const corps = JSON.parse(options.body);

    expect(corps.entity_types).toEqual(['contact', 'project']);
    expect(corps).not.toHaveProperty('types');
  });

  it('laisse passer le singulier tel quel', async () => {
    await searchMemory('jean', ['contact']);

    const [, options] = mockRequest.mock.calls[0] as [string, { body: string }];
    expect(JSON.parse(options.body).entity_types).toEqual(['contact']);
  });
});
