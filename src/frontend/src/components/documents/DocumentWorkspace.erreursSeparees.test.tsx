/**
 * B-630 (persona Sophie, c4) : « Document vide : rien à exporter. »
 * s'affichait deux fois (trame ET éditeur), loin du bouton cliqué, avec un
 * « Reprendre » qui n'avait rien à reprendre. Chaque erreur s'affiche une
 * fois, à côté du geste qui l'a produite.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { DocumentDetail, DocumentSection } from '../../services/api/documents';

interface EtatFactice {
  currentDocument: DocumentDetail | null;
  sectionActive: string | null;
  isStreaming: boolean;
  isLoading: boolean;
  error: string | null;
  draftError: string | null;
  exportError: string | null;
  [k: string]: unknown;
}

vi.mock('../../stores/documentStore', () => {
  const state: EtatFactice = {
    currentDocument: null,
    sectionActive: null,
    isStreaming: false,
    isLoading: false,
    error: null,
    draftError: null,
    exportError: null,
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
    (selector?: (s: EtatFactice) => unknown) => (selector ? selector(state) : state),
    { getState: () => state, setState: (p: Partial<EtatFactice>) => Object.assign(state, p) }
  );
  return { useDocumentStore };
});

import { useDocumentStore } from '../../stores/documentStore';
import { DocumentWorkspace } from './DocumentWorkspace';

function section(overrides: Partial<DocumentSection> = {}): DocumentSection {
  return {
    id: 's1',
    document_id: 'doc-1',
    title: 'Introduction',
    brief: '',
    order: 10,
    depth: 0,
    content: 'Début',
    summary: '',
    status: 'brouillon',
    orphan: false,
    created_at: '2026-07-01T00:00:00Z',
    updated_at: '2026-07-01T00:00:00Z',
    ...overrides,
  };
}

function detail(): DocumentDetail {
  return {
    id: 'doc-1',
    title: 'Proposition',
    brief: '',
    status: 'en_cours',
    project_id: null,
    contact_id: null,
    created_at: '2026-07-01T00:00:00Z',
    updated_at: '2026-07-01T00:00:00Z',
    sections_total: 1,
    sections_validees: 0,
    sections: [section()],
    pistes: [],
  };
}

describe('B-630 : chaque erreur de l’atelier s’affiche une fois, près du geste', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useDocumentStore.setState({
      currentDocument: detail(),
      sectionActive: 's1',
      error: null,
      draftError: null,
      exportError: null,
    });
  });

  it('une erreur d’export apparaît une seule fois, dans l’en-tête, sans « Reprendre »', () => {
    useDocumentStore.setState({ exportError: 'Document vide : rien à exporter.' });
    render(<DocumentWorkspace documentId="doc-1" onBack={vi.fn()} />);

    const occurrences = screen.getAllByText('Document vide : rien à exporter.');
    expect(occurrences).toHaveLength(1);
    expect(occurrences[0].closest('[data-testid="atelier-entete"]')).not.toBeNull();
    expect(occurrences[0].closest('[data-testid="section-editor"]')).toBeNull();
    expect(screen.queryByRole('button', { name: /Reprendre/ })).toBeNull();
  });

  it('une erreur de rédaction apparaît une seule fois, dans l’éditeur, avec « Reprendre »', () => {
    useDocumentStore.setState({ draftError: 'Erreur du fournisseur IA pendant la rédaction : timeout' });
    render(<DocumentWorkspace documentId="doc-1" onBack={vi.fn()} />);

    const occurrences = screen.getAllByText(/Erreur du fournisseur IA pendant la rédaction/);
    expect(occurrences).toHaveLength(1);
    expect(occurrences[0].closest('[data-testid="section-editor"]')).not.toBeNull();
    expect(screen.getByRole('button', { name: /Reprendre/ })).toBeInTheDocument();
  });

  it('une erreur du document apparaît une seule fois, dans la trame', () => {
    useDocumentStore.setState({ error: 'La réorganisation ne couvre pas exactement les sections.' });
    render(<DocumentWorkspace documentId="doc-1" onBack={vi.fn()} />);

    const occurrences = screen.getAllByText(/La réorganisation ne couvre pas/);
    expect(occurrences).toHaveLength(1);
    expect(occurrences[0].closest('[data-testid="section-editor"]')).toBeNull();
    expect(occurrences[0].closest('[data-testid="atelier-entete"]')).toBeNull();
    expect(screen.queryByRole('button', { name: /Reprendre/ })).toBeNull();
  });
});
