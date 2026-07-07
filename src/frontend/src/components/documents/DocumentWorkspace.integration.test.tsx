/**
 * THÉRÈSE v2 - Test d'intégration réel : documentStore <-> DocumentWorkspace
 * (Atelier documentaire, revue adversariale lot D, finding I).
 *
 * Contrairement à `DocumentWorkspace.test.tsx` (qui mocke `documentStore` en
 * entier - pattern getState/setState), ce fichier utilise le VRAI store
 * Zustand : seule `services/api/documents` est mockée, au niveau module.
 * C'est le filet qui manque : la suite actuelle prouve que le store gère le
 * streaming correctement (`documentStore.test.ts`, store seul) et que
 * `SectionEditor`/`DocumentWorkspace` réagissent correctement aux props
 * qu'on leur injecte à la main (`SectionEditor.test.tsx`,
 * `DocumentWorkspace.test.tsx`, store mocké) - mais rien ne vérifie que le
 * CÂBLAGE réel entre les deux (souscription Zustand -> re-render -> DOM)
 * fonctionne de bout en bout.
 *
 * Deux scénarios :
 * 1. Rédaction en 3 chunks gated (mêmes deltas que
 *    `documentStore.test.ts`) : le DOM de `SectionEditor` doit grandir
 *    chunk par chunk (assertions intermédiaires), pas seulement à la fin.
 * 2. Réorganisation rejetée par un 409 structuré (`ReorderConflictError`) :
 *    l'erreur doit apparaître dans le DOM ET `openDocument` (rechargement
 *    anti-perte) doit avoir été appelé. Le déplacement est déclenché en
 *    appelant directement `reorderSections` du store plutôt qu'un geste DnD
 *    complet : jsdom ne mesure aucun rect de layout réel, la détection de
 *    collision de @dnd-kit n'est donc pas fiable à piloter précisément en
 *    test (même limite déjà actée par `OutlineTree.test.tsx`, qui ne teste
 *    que le DÉMARRAGE du drag). Ce test-ci vérifie le câblage store -> DOM
 *    du composant MONTÉ, pas le geste DnD lui-même.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { DocumentDetail, DocumentSection, DraftStreamChunk } from '../../services/api/documents';

vi.mock('../../services/api/documents', () => {
  class ReorderConflictError extends Error {
    code: string;
    missing_ids: string[];
    unknown_ids: string[];
    constructor(body: { code: string; message: string; missing_ids: string[]; unknown_ids: string[] }) {
      super(body.message);
      this.name = 'ReorderConflictError';
      this.code = body.code;
      this.missing_ids = body.missing_ids;
      this.unknown_ids = body.unknown_ids;
    }
  }
  return {
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
    downloadExportedDocument: vi.fn(),
    ReorderConflictError,
  };
});

import { getDocument, reorderSections, draftSection, ReorderConflictError } from '../../services/api/documents';
import { useDocumentStore } from '../../stores/documentStore';
import { DocumentWorkspace } from './DocumentWorkspace';

function makeSection(overrides: Partial<DocumentSection> = {}): DocumentSection {
  return {
    id: 's1',
    document_id: 'd1',
    title: 'Introduction',
    brief: 'Poser le contexte',
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

function makeDetail(overrides: Partial<DocumentDetail> = {}): DocumentDetail {
  return {
    id: 'd1',
    title: 'Proposition Client X',
    brief: 'Une proposition commerciale',
    status: 'en_cours',
    project_id: null,
    contact_id: null,
    created_at: '2026-07-01T00:00:00Z',
    updated_at: '2026-07-01T00:00:00Z',
    sections_total: 1,
    sections_validees: 0,
    sections: [makeSection()],
    pistes: [],
    ...overrides,
  };
}

describe('DocumentWorkspace <-> documentStore (câblage réel, finding I)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useDocumentStore.setState({
      documents: [],
      currentDocument: null,
      sectionActive: null,
      isStreaming: false,
      isLoading: false,
      error: null,
      createModalRequested: false,
    });
  });

  it('draft en 3 chunks gated : le DOM de SectionEditor grandit chunk par chunk', async () => {
    useDocumentStore.setState({ currentDocument: makeDetail(), sectionActive: 's1' });

    let releaseChunk2: () => void = () => {};
    let releaseChunk3: () => void = () => {};
    vi.mocked(draftSection).mockImplementation(async function* (): AsyncGenerator<DraftStreamChunk> {
      yield { type: 'text', content: 'Bon' };
      await new Promise<void>((resolve) => {
        releaseChunk2 = resolve;
      });
      yield { type: 'text', content: 'jour' };
      await new Promise<void>((resolve) => {
        releaseChunk3 = resolve;
      });
      yield { type: 'text', content: ' monde' };
    });

    render(<DocumentWorkspace documentId="d1" onBack={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: /^Rédiger$/i }));

    await waitFor(() => {
      expect(screen.getByTestId('section-content')).toHaveTextContent('Bon');
    });

    releaseChunk2();
    await waitFor(() => {
      expect(screen.getByTestId('section-content')).toHaveTextContent('Bonjour');
    });

    releaseChunk3();
    await waitFor(() => {
      expect(screen.getByTestId('section-content')).toHaveTextContent('Bonjour monde');
    });
  });

  it('reorder rejeté (ReorderConflictError) : erreur visible dans le DOM + openDocument (reload) appelé', async () => {
    useDocumentStore.setState({
      currentDocument: makeDetail({
        sections: [makeSection({ id: 's1', order: 10 }), makeSection({ id: 's2', title: 'Contexte', order: 20 })],
      }),
    });

    vi.mocked(reorderSections).mockRejectedValueOnce(
      new ReorderConflictError({
        code: 'SECTIONS_INCOMPLETE',
        message: 'La réorganisation ne couvre pas exactement les sections existantes du document - aucune écriture effectuée.',
        missing_ids: ['s2'],
        unknown_ids: [],
      })
    );
    vi.mocked(getDocument).mockResolvedValueOnce(
      makeDetail({ sections: [makeSection({ id: 's1', order: 10 }), makeSection({ id: 's2', title: 'Contexte', order: 20 })] })
    );

    render(<DocumentWorkspace documentId="d1" onBack={vi.fn()} />);

    await useDocumentStore.getState().reorderSections('d1', [{ id: 's1', order: 10, depth: 0 }]);

    await waitFor(() => {
      expect(screen.getByText(/ne couvre pas exactement/i)).toBeInTheDocument();
    });
    expect(getDocument).toHaveBeenCalledWith('d1');
  });
});
