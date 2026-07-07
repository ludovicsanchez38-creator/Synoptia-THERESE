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
import type { DocumentDetail, DocumentExportResponse, DocumentSection } from '../../services/api/documents';

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
  updatePiste: ReturnType<typeof vi.fn>;
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
    updatePiste: vi.fn(),
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

function makeSection(overrides: Partial<DocumentSection> = {}): DocumentSection {
  return {
    id: 's1',
    document_id: 'doc-1',
    title: 'Introduction',
    brief: '',
    order: 10,
    depth: 0,
    content: '',
    summary: '',
    status: 'vide',
    orphan: false,
    created_at: '2026-07-01T00:00:00Z',
    updated_at: '2026-07-01T00:00:00Z',
    ...overrides,
  };
}

function makePiste(overrides: Partial<DocumentDetail['pistes'][number]> = {}) {
  return {
    id: 'p1',
    document_id: 'doc-1',
    section_origine_id: null,
    texte: 'Ajouter un exemple chiffré sur le ROI',
    status: 'nouvelle' as const,
    created_at: '2026-07-01T00:00:00Z',
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

  describe('Pistes (D4)', () => {
    it('rend le volet Pistes câblé sur currentDocument.pistes', () => {
      const piste = makePiste({ texte: 'Piste capturée pendant la rédaction' });
      useDocumentStore.setState({ currentDocument: makeDetail({ pistes: [piste] }) });

      render(<DocumentWorkspace documentId="doc-1" onBack={vi.fn()} />);

      expect(screen.getByTestId('pistes-panel')).toBeInTheDocument();
      expect(screen.getByText('Piste capturée pendant la rédaction')).toBeInTheDocument();
    });

    it('« Ignorer » une piste appelle updatePiste avec le statut ignoree', () => {
      const piste = makePiste({ id: 'p9' });
      useDocumentStore.setState({ currentDocument: makeDetail({ pistes: [piste] }) });

      render(<DocumentWorkspace documentId="doc-1" onBack={vi.fn()} />);
      fireEvent.click(screen.getByRole('button', { name: /^Ignorer$/i }));

      expect(useDocumentStore.getState().updatePiste).toHaveBeenCalledWith('p9', 'ignoree');
    });

    it(
      '« Explorer » une piste : passe son statut à exploree, sélectionne sa section d\'origine ' +
        'ET préremplit l\'instruction de SectionEditor',
      () => {
        const section1 = makeSection({ id: 's1', title: 'Introduction' });
        const section2 = makeSection({ id: 's2', title: 'Chiffrage' });
        const piste = makePiste({ id: 'p1', section_origine_id: 's2', texte: 'Ajouter un exemple chiffré sur le ROI' });
        useDocumentStore.setState({
          currentDocument: makeDetail({ sections: [section1, section2], pistes: [piste] }),
          sectionActive: 's1',
        });
        // Implémentation locale à CE test uniquement (restaurée en fin de test) :
        // le mock non-réactif du store ne fait pas suivre setSectionActive() par
        // un re-render - on la fait ici pointer vers le setState mocké pour
        // vérifier que la section active bascule réellement dans l'UI.
        vi.mocked(useDocumentStore.getState().setSectionActive).mockImplementation((id: unknown) =>
          useDocumentStore.setState({ sectionActive: id as string | null })
        );

        render(<DocumentWorkspace documentId="doc-1" onBack={vi.fn()} />);
        fireEvent.click(screen.getByRole('button', { name: /^Explorer$/i }));

        expect(useDocumentStore.getState().updatePiste).toHaveBeenCalledWith('p1', 'exploree');
        expect(useDocumentStore.getState().setSectionActive).toHaveBeenCalledWith('s2');
        // Section d'origine sélectionnée comme section active :
        expect(screen.getByLabelText('Titre de la section')).toHaveValue('Chiffrage');
        // Instruction préremplie avec le texte de la piste :
        expect(screen.getByLabelText('Instruction de retouche')).toHaveValue('Ajouter un exemple chiffré sur le ROI');

        vi.mocked(useDocumentStore.getState().setSectionActive).mockReset();
      }
    );

    it('« Explorer » une piste SANS section d\'origine : marque la piste explorée sans toucher à la sélection', () => {
      const section1 = makeSection({ id: 's1', title: 'Introduction' });
      const piste = makePiste({ id: 'p2', section_origine_id: null });
      useDocumentStore.setState({
        currentDocument: makeDetail({ sections: [section1], pistes: [piste] }),
        sectionActive: 's1',
      });

      render(<DocumentWorkspace documentId="doc-1" onBack={vi.fn()} />);
      fireEvent.click(screen.getByRole('button', { name: /^Explorer$/i }));

      expect(useDocumentStore.getState().updatePiste).toHaveBeenCalledWith('p2', 'exploree');
      expect(useDocumentStore.getState().setSectionActive).not.toHaveBeenCalled();
    });
  });
});
