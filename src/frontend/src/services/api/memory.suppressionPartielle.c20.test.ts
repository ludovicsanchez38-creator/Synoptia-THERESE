import { beforeEach, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({ request: vi.fn(), notify: vi.fn() }));
vi.mock('./core', async () => ({
  ...await vi.importActual<typeof import('./core')>('./core'),
  request: mocks.request,
}));
vi.mock('./memoryCards', async () => ({
  ...await vi.importActual<typeof import('./memoryCards')>('./memoryCards'),
  notifyMemoryChange: mocks.notify,
}));

import { deleteContactWithCascade, deleteProject } from './memory';

beforeEach(() => vi.clearAllMocks());

it.each([
  ['projet', () => deleteProject('dossier-test'), '/api/memory/projects/dossier-test?cascade=true'],
  ['contact', () => deleteContactWithCascade('contact-test', true), '/api/memory/contacts/contact-test?cascade=true'],
] as const)('transmet le résultat partiel de suppression du %s', async (_type, supprimer, url) => {
  const resultat = { deleted: false, id: 'test', cascade_deleted: {}, message: 'Des fichiers restent sur disque.' };
  mocks.request.mockResolvedValue(resultat);
  expect(await supprimer()).toEqual(resultat);
  expect(mocks.request).toHaveBeenCalledWith(url, { method: 'DELETE' });
  expect(mocks.notify).toHaveBeenCalledOnce();
});
