/** P-056 (ronde B2 ; design V2 après revue COCO, finding 8) : la génération de trame est identifiée par document et traitement ; elle s'annule ; une annulation est une fin neutre ; une réponse tardive n'écrase pas un autre document. */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { DocumentDetail } from '../services/api/documents';

vi.mock('../services/api/documents', () => ({
  listDocuments: vi.fn(), getDocument: vi.fn(), createDocument: vi.fn(), deleteDocument: vi.fn(),
  generateOutline: vi.fn(), createSection: vi.fn(), updateSection: vi.fn(), reorderSections: vi.fn(),
  draftSection: vi.fn(), validateSection: vi.fn(), exportDocument: vi.fn(), listPistes: vi.fn(), createPiste: vi.fn(), updatePiste: vi.fn(),
  ReorderConflictError: class extends Error {},
}));
vi.mock('../services/api/processingTasks', () => ({ annulerTraitement: vi.fn(), listerTraitements: vi.fn() }));

import { generateOutline } from '../services/api/documents';
import { annulerTraitement } from '../services/api/processingTasks';
import { ApiError } from '../services/api/core';
import { useDocumentStore } from './documentStore';

const detail = (id: string): DocumentDetail => ({
  id, title: 'Proposition', brief: '', status: 'vide', created_at: '', updated_at: '', sections_total: 0, sections_validees: 0, sections: [], pistes: [],
} as unknown as DocumentDetail);

describe('documentStore : trame annulable (P-056)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useDocumentStore.setState({ currentDocument: detail('d1'), documents: [detail('d1') as never], sectionActive: null, error: null, outlineGeneration: null, outlineNotice: null, isLoading: false });
  });

  it('envoie un identifiant de traitement, tient l’état pendant l’appel, puis le libère', async () => {
    let terminer: (v: unknown[]) => void = () => {};
    vi.mocked(generateOutline).mockImplementation(() => new Promise((resolve) => { terminer = resolve as never; }));
    const promesse = useDocumentStore.getState().generateOutline('d1');
    const enCours = useDocumentStore.getState().outlineGeneration;
    expect(enCours?.documentId).toBe('d1');
    expect(enCours?.taskId).toMatch(/^[0-9a-f-]{36}$/);
    expect(generateOutline).toHaveBeenCalledWith('d1', enCours?.taskId);
    terminer([]);
    await promesse;
    expect(useDocumentStore.getState().outlineGeneration).toBeNull();
  });

  it('une annulation est une fin neutre : notice, pas d’erreur', async () => {
    vi.mocked(generateOutline).mockRejectedValue(new ApiError(409, 'Conflict', 'Génération de la trame annulée.', 'outline_cancelled'));
    await useDocumentStore.getState().generateOutline('d1');
    const etat = useDocumentStore.getState();
    expect(etat.error).toBeNull();
    expect(etat.outlineNotice).toMatch(/annulée/);
    expect(etat.outlineGeneration).toBeNull();
  });

  it('un autre 409 reste une erreur', async () => {
    vi.mocked(generateOutline).mockRejectedValue(new ApiError(409, 'Conflict', 'Ce document a déjà des sections rédigées.'));
    await useDocumentStore.getState().generateOutline('d1');
    expect(useDocumentStore.getState().error).toMatch(/déjà des sections/);
    expect(useDocumentStore.getState().outlineNotice).toBeNull();
  });

  it('cancelOutline demande l’arrêt du traitement en cours et le marque', async () => {
    vi.mocked(generateOutline).mockImplementation(() => new Promise(() => {}));
    vi.mocked(annulerTraitement).mockResolvedValue({ state: 'cancel_requested', resultat: 'accepted', transmise: true });
    void useDocumentStore.getState().generateOutline('d1');
    const taskId = useDocumentStore.getState().outlineGeneration?.taskId;
    await useDocumentStore.getState().cancelOutline();
    expect(annulerTraitement).toHaveBeenCalledWith(taskId);
    expect(useDocumentStore.getState().outlineGeneration?.arretDemande).toBe(true);
  });

  it('une réponse tardive pour un document quitté n’écrase pas le document ouvert', async () => {
    let terminer: (v: unknown[]) => void = () => {};
    vi.mocked(generateOutline).mockImplementation(() => new Promise((resolve) => { terminer = resolve as never; }));
    const promesse = useDocumentStore.getState().generateOutline('d1');
    useDocumentStore.setState({ currentDocument: detail('d2') });
    terminer([{ id: 's1', document_id: 'd1', title: 'Contexte', order: 10, depth: 0 }]);
    await promesse;
    expect(useDocumentStore.getState().currentDocument?.id).toBe('d2');
    expect(useDocumentStore.getState().currentDocument?.sections).toEqual([]);
  });
});
