/**
 * Tests DocumentWorkspace (Atelier documentaire, D3).
 *
 * Vérifie : bascule retour (closeDocument() du store appelé AVANT onBack -
 * anti-flash D2), et l'export qui déclenche le téléchargement navigateur
 * (`downloadExportedDocument`, mocké) une fois les métadonnées obtenues -
 * `exportDocument` du store ne télécharge JAMAIS lui-même (décision D1).
 *
 * OutlineTree et SectionEditor ne sont PAS mockés ici : avec une trame vide
 * et aucune section active, ils retombent sur leurs propres états vides
 * (déjà couverts par leurs tests dédiés) - ce qui vérifie au passage que le
 * câblage des props ne plante rien.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { DocumentDetail, DocumentExportResponse } from '../../services/api/documents';

// --- Mock documentStore (pattern getState/setState, fidèle à Zustand) ------

interface MockDocumentState {
  currentDocument: DocumentDetail | null;
  sectionActive: string | null;
  isStreaming: boolean;
  isLoading: boolean;
  error: string | null;
  setSectionActive: ReturnType<typeof vi.fn>;
  reorderSections: ReturnType<typeof vi.fn>;
  createSection: ReturnType<typeof vi.fn>;
  generateOutline: ReturnType<typeof vi.fn>;
  updateSection: ReturnType<typeof vi.fn>;
  draftSection: ReturnType<typeof vi.fn>;
  validateSection: ReturnType<typeof vi.fn>;
  exportDocument: ReturnType<typeof vi.fn>;
  closeDocument: ReturnType<typeof vi.fn>;
}

vi.mock('../../stores/documentStore', () => {
  const state: MockDocumentState = {
    currentDocument: null,
    sectionActive: null,
    isStreaming: false,
    isLoading: false,
    error: null,
    setSectionActive: vi.fn(),
    reorderSections: vi.fn(),
    createSection: vi.fn(),
    generateOutline: vi.fn(),
    updateSection: vi.fn(),
    draftSection: vi.fn(),
    validateSection: vi.fn(),
    exportDocument: vi.fn(),
    closeDocument: vi.fn(),
  };
  const useDocumentStore = Object.assign(
    (selector?: (s: MockDocumentState) => unknown) => (selector ? selector(state) : state),
    {
      getState: () => state,
      setState: (partial: Partial<MockDocumentState>) => Object.assign(state, partial),
    }
  );
  return { useDocumentStore };
});

// --- Mock du téléchargement (mécanique exportConversation, chat.ts) --------

const mockDownloadExportedDocument = vi.fn();
vi.mock('../../services/api/documents', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../services/api/documents')>();
  return {
    ...actual,
    downloadExportedDocument: (...args: [DocumentExportResponse]) => mockDownloadExportedDocument(...args),
  };
});

import { useDocumentStore } from '../../stores/documentStore';
import { DocumentWorkspace } from './DocumentWorkspace';

function makeDetail(overrides: Partial<DocumentDetail> = {}): DocumentDetail {
  return {
    id: 'doc-1',
    title: 'Proposition Client X',
    brief: 'Une proposition commerciale',
    status: 'en_cours',
    project_id: null,
    contact_id: null,
    created_at: '2026-07-01T00:00:00Z',
    updated_at: '2026-07-01T00:00:00Z',
    sections_total: 0,
    sections_validees: 0,
    sections: [],
    pistes: [],
    ...overrides,
  };
}

describe('DocumentWorkspace', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useDocumentStore.setState({
      currentDocument: null,
      sectionActive: null,
      isStreaming: false,
      isLoading: false,
      error: null,
    });
  });

  it('affiche un état de chargement tant que currentDocument est vide', () => {
    render(<DocumentWorkspace documentId="doc-1" onBack={vi.fn()} />);
    expect(screen.getByText(/Chargement du document/i)).toBeInTheDocument();
  });

  it('« Retour aux documents » ferme le document dans le store PUIS appelle onBack (anti-flash D2)', () => {
    useDocumentStore.setState({ currentDocument: makeDetail() });
    const onBack = vi.fn();
    render(<DocumentWorkspace documentId="doc-1" onBack={onBack} />);

    fireEvent.click(screen.getByRole('button', { name: /Retour aux documents/i }));

    expect(useDocumentStore.getState().closeDocument).toHaveBeenCalledTimes(1);
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it('« Exporter .docx » récupère les métadonnées puis déclenche le téléchargement', async () => {
    useDocumentStore.setState({ currentDocument: makeDetail() });
    const exported: DocumentExportResponse = {
      success: true,
      format: 'docx',
      file_name: 'Proposition_abc12345.docx',
      download_url: '/api/skills/download/abc12345',
    };
    vi.mocked(useDocumentStore.getState().exportDocument).mockResolvedValue(exported);

    render(<DocumentWorkspace documentId="doc-1" onBack={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /Exporter \.docx/i }));

    await waitFor(() => {
      expect(useDocumentStore.getState().exportDocument).toHaveBeenCalledWith('doc-1', 'docx');
    });
    await waitFor(() => {
      expect(mockDownloadExportedDocument).toHaveBeenCalledWith(exported);
    });
  });

  it('« Exporter .md » : si exportDocument échoue (retourne null), aucun téléchargement n\'est déclenché', async () => {
    useDocumentStore.setState({ currentDocument: makeDetail() });
    vi.mocked(useDocumentStore.getState().exportDocument).mockResolvedValue(null);

    render(<DocumentWorkspace documentId="doc-1" onBack={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /Exporter \.md/i }));

    await waitFor(() => {
      expect(useDocumentStore.getState().exportDocument).toHaveBeenCalledWith('doc-1', 'md');
    });
    expect(mockDownloadExportedDocument).not.toHaveBeenCalled();
  });

  it('câble la trame et la section active vers OutlineTree/SectionEditor sans planter (états vides)', () => {
    useDocumentStore.setState({ currentDocument: makeDetail(), sectionActive: null });
    render(<DocumentWorkspace documentId="doc-1" onBack={vi.fn()} />);

    expect(screen.getByTestId('outline-tree')).toBeInTheDocument();
    expect(screen.getByTestId('section-editor-empty')).toBeInTheDocument();
  });
});
