/**
 * B-830 (cycle 9) : après « Annuler », relancer la trame pendant que le moteur
 * finit d'arrêter la précédente rend un 409 `outline_in_progress` ; le magasin
 * le traitait comme une panne (erreur) au lieu de la notice déjà prévue pour
 * ce cas côté client.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { DocumentDetail } from '../services/api/documents';

vi.mock('../services/api/documents', () => ({
  listDocuments: vi.fn(), getDocument: vi.fn(), createDocument: vi.fn(), deleteDocument: vi.fn(),
  generateOutline: vi.fn(), createSection: vi.fn(), updateSection: vi.fn(), reorderSections: vi.fn(),
  deleteSection: vi.fn(), draftSection: vi.fn(), exportDocument: vi.fn(),
}));
vi.mock('../services/api/processingTasks', () => ({ annulerTraitement: vi.fn(), listerTraitements: vi.fn() }));

import { generateOutline } from '../services/api/documents';
import { ApiError } from '../services/api/core';
import { useDocumentStore } from './documentStore';

const detail = (id: string): DocumentDetail => ({ id, title: 'Doc', brief: '', status: 'draft', project_id: null, sections: [], sections_total: 0, created_at: '', updated_at: '' } as never);

describe('documentStore - B-830, une trame déjà en cours côté moteur est une notice', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useDocumentStore.setState({ currentDocument: detail('d1'), documents: [detail('d1') as never], sectionActive: null, error: null, outlineGeneration: null, outlineNotice: null, isLoading: false } as never);
  });

  it('409 outline_in_progress : notice, pas d’erreur', async () => {
    vi.mocked(generateOutline).mockRejectedValue(new ApiError(409, 'Conflict', 'Une génération de trame est déjà en cours pour ce document.', 'outline_in_progress'));
    await useDocumentStore.getState().generateOutline('d1');
    const etat = useDocumentStore.getState();
    expect(etat.error).toBeNull();
    expect(etat.outlineNotice).toMatch(/déjà en cours/);
    expect(etat.outlineGeneration).toBeNull();
  });
});
