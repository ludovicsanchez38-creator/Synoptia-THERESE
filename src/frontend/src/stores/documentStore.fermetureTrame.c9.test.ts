/**
 * B-919 (cycle 9, relecteur W2) : depuis B-903, une seule génération de
 * trame est suivie à la fois. Fermer le document pendant la génération
 * laissait ce suivi en place sans bouton d'arrêt à l'écran : plus aucune
 * trame ne pouvait partir, sur aucun document, tant que la requête vivait.
 * Fermer le document demande désormais l'arrêt de la génération suivie.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({ generateOutline: vi.fn(), annulerTraitement: vi.fn() }));
vi.mock('../services/api/documents', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  generateOutline: api.generateOutline,
}));
vi.mock('../services/api/processingTasks', () => ({ annulerTraitement: api.annulerTraitement, listerTraitements: vi.fn() }));

import { useDocumentStore } from './documentStore';

describe('documentStore - B-919, fermer le document demande l’arrêt de la trame suivie', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useDocumentStore.setState({ outlineGeneration: null, outlineNotice: null, error: null, isLoading: false, currentDocument: null } as never);
    api.annulerTraitement.mockResolvedValue({ state: 'cancel_requested', resultat: 'accepted', transmise: true });
  });

  it('closeDocument pendant une génération appelle l’arrêt avec l’identifiant suivi', async () => {
    api.generateOutline.mockImplementation(() => new Promise(() => {}));
    void useDocumentStore.getState().generateOutline('doc-a');
    await Promise.resolve();
    const suivi = useDocumentStore.getState().outlineGeneration;
    expect(suivi?.documentId).toBe('doc-a');

    useDocumentStore.getState().closeDocument();
    await Promise.resolve();
    expect(api.annulerTraitement).toHaveBeenCalledWith(suivi!.taskId);
    expect(useDocumentStore.getState().outlineGeneration?.arretDemande).toBe(true);
  });
});
