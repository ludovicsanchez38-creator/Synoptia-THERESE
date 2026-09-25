/**
 * B-919 (cycle 9, relecteur W2) : depuis B-903, une seule génération de
 * trame est suivie à la fois. Fermer le document pendant la génération
 * laissait ce suivi en place sans bouton d'arrêt à l'écran : plus aucune
 * trame ne pouvait partir, sur aucun document, tant que la requête vivait.
 *
 * B-1374 (persona Hugo, cycle 13) : le correctif de B-919 demandait l'arrêt,
 * et la trame en cours était jetée en silence dès qu'on quittait l'Atelier.
 * Fermer le document LIBÈRE désormais le suivi sans arrêter la génération :
 * elle continue en fond (visible et arrêtable dans « Travaux »), une autre
 * trame peut partir, et la réouverture reprend le suivi (B-1394).
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({ generateOutline: vi.fn(), annulerTraitement: vi.fn() }));
vi.mock('../services/api/documents', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  generateOutline: api.generateOutline,
}));
vi.mock('../services/api/processingTasks', () => ({ annulerTraitement: api.annulerTraitement, listerTraitements: vi.fn() }));

import { useDocumentStore } from './documentStore';

describe('documentStore - B-919 et B-1374, fermer le document libère le suivi sans arrêter la trame', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useDocumentStore.setState({ outlineGeneration: null, outlineNotice: null, error: null, isLoading: false, currentDocument: null } as never);
    api.annulerTraitement.mockResolvedValue({ state: 'cancel_requested', resultat: 'accepted', transmise: true });
  });

  it('closeDocument pendant une génération ne demande pas l’arrêt et libère le suivi', async () => {
    api.generateOutline.mockImplementation(() => new Promise(() => {}));
    void useDocumentStore.getState().generateOutline('doc-a');
    await Promise.resolve();
    expect(useDocumentStore.getState().outlineGeneration?.documentId).toBe('doc-a');

    useDocumentStore.getState().closeDocument();
    await Promise.resolve();
    expect(api.annulerTraitement).not.toHaveBeenCalled();
    expect(useDocumentStore.getState().outlineGeneration).toBeNull();
  });

  it('une autre trame peut partir après la fermeture (souci de B-919)', async () => {
    api.generateOutline.mockImplementation(() => new Promise(() => {}));
    void useDocumentStore.getState().generateOutline('doc-a');
    await Promise.resolve();
    useDocumentStore.getState().closeDocument();

    void useDocumentStore.getState().generateOutline('doc-b');
    await Promise.resolve();
    expect(api.generateOutline).toHaveBeenCalledTimes(2);
    expect(useDocumentStore.getState().outlineGeneration?.documentId).toBe('doc-b');
  });

  it('l’échec tardif d’une trame détachée n’écrit pas d’erreur sur l’écran courant', async () => {
    let rejeter: (e: unknown) => void = () => {};
    api.generateOutline.mockImplementationOnce(() => new Promise((_, r) => { rejeter = r; }));
    void useDocumentStore.getState().generateOutline('doc-a');
    await Promise.resolve();
    useDocumentStore.getState().closeDocument();

    rejeter(Object.assign(new Error('Le fournisseur ne répond pas.'), { code: undefined }));
    await new Promise((r) => setTimeout(r, 0));
    expect(useDocumentStore.getState().error).toBeNull();
  });
});
