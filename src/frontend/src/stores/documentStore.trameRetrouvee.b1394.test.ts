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

  it.each(['avant', 'après'])('R2-6 : un sondage de A terminé %s la lecture de B ne détourne pas son ouverture', async (ordre) => {
    useDocumentStore.getState().closeDocument();
    api.getDocument.mockReset().mockResolvedValue(vide);
    let terminerSondage!: (traitements: typeof enCours[]) => void;
    api.listerTraitements.mockReset().mockResolvedValue([]).mockResolvedValueOnce([enCours])
      .mockImplementationOnce(() => new Promise(resolve => { terminerSondage = resolve; }));
    await useDocumentStore.getState().openDocument('doc-1');
    await vi.advanceTimersByTimeAsync(3000);
    expect(terminerSondage).toBeTypeOf('function');
    let terminerLecture!: (doc: typeof vide) => void;
    api.getDocument.mockImplementationOnce(() => new Promise(resolve => { terminerLecture = resolve; }));
    const ouvertureB = useDocumentStore.getState().openDocument('doc-2');
    if (ordre === 'après') {
      terminerLecture({ ...vide, id: 'doc-2' });
      await ouvertureB;
    }
    terminerSondage([]);
    await vi.advanceTimersByTimeAsync(0);
    if (ordre === 'avant') terminerLecture({ ...vide, id: 'doc-2' });
    await ouvertureB;

    expect(api.getDocument.mock.calls.map(([id]) => id)).toEqual(['doc-1', 'doc-2']);
    expect(useDocumentStore.getState().currentDocument?.id).toBe('doc-2');
    expect(useDocumentStore.getState().isLoading).toBe(false);
    expect(useDocumentStore.getState().outlineGeneration).toBeNull();
    api.generateOutline.mockResolvedValue([]);
    await useDocumentStore.getState().generateOutline('doc-2');
    expect(api.generateOutline).toHaveBeenCalledWith('doc-2', expect.any(String));
  });

  it('R2-6 : une relecture interne conserve la surveillance de la même session', async () => {
    useDocumentStore.getState().closeDocument();
    api.getDocument.mockReset().mockResolvedValue(vide);
    api.listerTraitements.mockReset().mockResolvedValueOnce([enCours]).mockResolvedValue([]);
    await useDocumentStore.getState().openDocument('doc-1');
    await vi.advanceTimersByTimeAsync(0);
    await useDocumentStore.getState().openDocument('doc-1');
    api.getDocument.mockResolvedValue(trame);
    await vi.advanceTimersByTimeAsync(3000);

    expect(useDocumentStore.getState().currentDocument?.sections_total).toBe(1);
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
