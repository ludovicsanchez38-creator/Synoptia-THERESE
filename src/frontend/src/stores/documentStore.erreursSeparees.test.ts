/**
 * B-630 (persona Sophie, c4) : `error` était mono-slot. Une erreur d'export
 * (« Document vide : rien à exporter. ») s'affichait à la fois en tête de la
 * trame et dans l'éditeur, avec un bouton « Reprendre » qui laissait croire à
 * un échec de rédaction. Trois erreurs, trois origines : le document
 * (`error`), la rédaction (`draftError`), l'export (`exportError`).
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { DocumentDetail, DraftStreamChunk } from '../services/api/documents';

vi.mock('../services/api/documents', () => ({
  listDocuments: vi.fn(),
  getDocument: vi.fn(),
  createDocument: vi.fn(),
  deleteDocument: vi.fn(),
  generateOutline: vi.fn(),
  createSection: vi.fn(),
  updateSection: vi.fn(),
  reorderSections: vi.fn(),
  draftSection: vi.fn(),
  validateSection: vi.fn(),
  exportDocument: vi.fn(),
  listPistes: vi.fn(),
  createPiste: vi.fn(),
  updatePiste: vi.fn(),
  ReorderConflictError: class extends Error {},
}));

import { draftSection, exportDocument } from '../services/api/documents';
import { useDocumentStore } from './documentStore';

function makeDetail(): DocumentDetail {
  return {
    id: 'd1',
    title: 'Proposition',
    brief: '',
    status: 'en_cours',
    project_id: null,
    contact_id: null,
    created_at: '2026-07-01T00:00:00Z',
    updated_at: '2026-07-01T00:00:00Z',
    sections_total: 1,
    sections_validees: 0,
    sections: [
      {
        id: 's1',
        document_id: 'd1',
        title: 'Introduction',
        brief: '',
        order: 10,
        depth: 0,
        content: 'Ancien contenu',
        summary: '',
        status: 'brouillon',
        orphan: false,
        created_at: '2026-07-01T00:00:00Z',
        updated_at: '2026-07-01T00:00:00Z',
      },
    ],
    pistes: [],
  };
}

describe('B-630 : une erreur par origine', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useDocumentStore.setState({
      currentDocument: makeDetail(),
      sectionActive: 's1',
      error: null,
      draftError: null,
      exportError: null,
      isStreaming: false,
    });
  });

  it('un export refusé pose exportError, pas error', async () => {
    vi.mocked(exportDocument).mockRejectedValueOnce(new Error('Document vide : rien à exporter.'));
    const resultat = await useDocumentStore.getState().exportDocument('d1');
    expect(resultat).toBeNull();
    expect(useDocumentStore.getState().exportError).toBe('Document vide : rien à exporter.');
    expect(useDocumentStore.getState().error).toBeNull();
    expect(useDocumentStore.getState().draftError).toBeNull();
  });

  it('une rédaction en échec pose draftError, pas error', async () => {
    vi.mocked(draftSection).mockImplementation(async function* (): AsyncGenerator<DraftStreamChunk> {
      yield { type: 'error', content: 'Fournisseur en panne' } as DraftStreamChunk;
    });
    await useDocumentStore.getState().draftSection('s1');
    expect(useDocumentStore.getState().draftError).toBe('Fournisseur en panne');
    expect(useDocumentStore.getState().error).toBeNull();
    expect(useDocumentStore.getState().exportError).toBeNull();
  });

  it('un nouvel export efface l’erreur d’export précédente sans toucher aux autres', async () => {
    useDocumentStore.setState({ exportError: 'Ancienne', draftError: 'Rédaction cassée' });
    vi.mocked(exportDocument).mockResolvedValueOnce({
      success: true,
      format: 'md',
      file_name: 'p.md',
      download_url: '/x',
    });
    await useDocumentStore.getState().exportDocument('d1');
    expect(useDocumentStore.getState().exportError).toBeNull();
    expect(useDocumentStore.getState().draftError).toBe('Rédaction cassée');
  });

  it('closeDocument et clearError remettent les trois erreurs à zéro', () => {
    useDocumentStore.setState({ error: 'a', draftError: 'b', exportError: 'c' });
    useDocumentStore.getState().clearError();
    expect(useDocumentStore.getState()).toMatchObject({ error: null, draftError: null, exportError: null });

    useDocumentStore.setState({ error: 'a', draftError: 'b', exportError: 'c' });
    useDocumentStore.getState().closeDocument();
    expect(useDocumentStore.getState()).toMatchObject({ error: null, draftError: null, exportError: null });
  });
});
