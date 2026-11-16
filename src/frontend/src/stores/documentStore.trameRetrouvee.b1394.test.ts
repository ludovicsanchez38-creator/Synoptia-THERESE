/**
 * B-1394 (persona Zoé, cycle 13) : après un rechargement, l'Atelier disait
 * « Aucune section pour l'instant » et proposait « Générer la trame » pendant
 * que la trame se générait encore côté moteur ; le clic renvoyait 409.
 *
 * Le suivi de la génération ne vivait qu'en mémoire. À l'ouverture d'un
 * document, une génération encore active pour lui (liste des traitements,
 * `entity_id`) est désormais retrouvée et suivie jusqu'à sa fin, puis le
 * document est relu.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({ getDocument: vi.fn(), listerTraitements: vi.fn(), generateOutline: vi.fn() }));
vi.mock('../services/api/documents', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  getDocument: api.getDocument,
  generateOutline: api.generateOutline,
}));
vi.mock('../services/api/processingTasks', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listerTraitements: api.listerTraitements,
}));

import { useDocumentStore } from './documentStore';

const vide = { id: 'doc-1', title: 'Zoé document', sections: [], sections_total: 0 };
const trame = { ...vide, sections: [{ id: 's1', title: 'Introduction' }], sections_total: 1 };
const enCours = { id: 't-1', type: 'document_outline', entity_id: 'doc-1', state: 'running' };

describe('documentStore - B-1394, une trame en cours est retrouvée à la réouverture', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    useDocumentStore.setState({ outlineGeneration: null, currentDocument: null, error: null, isLoading: false } as never);
  });
  afterEach(() => vi.useRealTimers());

  it('la génération active est suivie, puis le document est relu à sa fin', async () => {
    api.getDocument.mockResolvedValueOnce(vide).mockResolvedValue(trame);
    api.listerTraitements.mockResolvedValueOnce([enCours]).mockResolvedValueOnce([enCours]).mockResolvedValue([]);

    await useDocumentStore.getState().openDocument('doc-1');
    await vi.waitFor(() => expect(useDocumentStore.getState().outlineGeneration).toMatchObject({ documentId: 'doc-1', taskId: 't-1' }));

    await vi.advanceTimersByTimeAsync(10_000);
    await vi.waitFor(() => expect(useDocumentStore.getState().outlineGeneration).toBeNull());
    expect(useDocumentStore.getState().currentDocument?.sections_total).toBe(1);
  });

  it('sans génération active, rien n’est suivi', async () => {
    api.getDocument.mockResolvedValue(vide);
    api.listerTraitements.mockResolvedValue([{ ...enCours, entity_id: 'autre-doc' }]);

    await useDocumentStore.getState().openDocument('doc-1');
    await vi.advanceTimersByTimeAsync(0);
    expect(useDocumentStore.getState().outlineGeneration).toBeNull();
  });

  it.each(['fermeture', 'autre document', 'réouverture du même document'])('R1-6 : une recherche tardive ne réinstalle pas le suivi après %s', async (action) => {
    useDocumentStore.getState().closeDocument();
    api.getDocument.mockReset().mockImplementation(async (id: string) => ({ ...vide, id }));
    api.generateOutline.mockReset().mockResolvedValue([]);
    let terminer!: (traitements: typeof enCours[]) => void;
    api.listerTraitements.mockReset().mockResolvedValue([]).mockImplementationOnce(
      () => new Promise(resolve => { terminer = resolve; }),
    );
    await useDocumentStore.getState().openDocument('doc-1');
    expect(terminer).toBeTypeOf('function');
    if (action !== 'autre document') useDocumentStore.getState().closeDocument();
    if (action !== 'fermeture') await useDocumentStore.getState().openDocument(action === 'autre document' ? 'doc-2' : 'doc-1');
    terminer([enCours]);
    await vi.advanceTimersByTimeAsync(0);

    expect(useDocumentStore.getState().outlineGeneration).toBeNull();
    await useDocumentStore.getState().openDocument('doc-2');
    await useDocumentStore.getState().generateOutline('doc-2');
    expect(api.generateOutline).toHaveBeenCalledWith('doc-2', expect.any(String));
    expect(useDocumentStore.getState().outlineNotice).toBeNull();
    useDocumentStore.getState().closeDocument();
  });
});
