/**
 * B-903 (cycle 9, relecteur V4) : le suivi d'une génération de trame ne
 * refusait un second lancement que pour le MÊME document ; lancée depuis un
 * autre document, la seconde génération remplaçait le suivi de la première,
 * dont l'arrêt devenait injoignable.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({ generateOutline: vi.fn() }));
vi.mock('../services/api/documents', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  generateOutline: api.generateOutline,
}));

import { useDocumentStore } from './documentStore';

describe('documentStore - B-903, une seule génération de trame suivie à la fois', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useDocumentStore.setState({ outlineGeneration: null, outlineNotice: null, error: null, isLoading: false } as never);
  });

  it('un second document ne remplace pas le suivi de la première génération', async () => {
    api.generateOutline.mockImplementation(() => new Promise(() => {}));
    void useDocumentStore.getState().generateOutline('doc-a');
    await Promise.resolve();
    const suivi = useDocumentStore.getState().outlineGeneration;
    expect(suivi?.documentId).toBe('doc-a');

    await useDocumentStore.getState().generateOutline('doc-b');
    expect(api.generateOutline).toHaveBeenCalledTimes(1);
    expect(useDocumentStore.getState().outlineGeneration).toEqual(suivi);
    expect(useDocumentStore.getState().outlineNotice).toMatch(/déjà en cours/);
  });
});
