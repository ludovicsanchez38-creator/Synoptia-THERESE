/**
 * P-140 (persona Zoé, cycle 13) : la ligne « Trame : … » des Travaux doit
 * mener à son document. La vue Documents garde en état local le document
 * ouvert ; une demande d'ouverture passe par le store, comme « Nouveau
 * document » (D4), et fonctionne aussi quand la vue est déjà montée.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { DocumentResponse } from '../../services/api/documents';

// --- Mock documentStore (pattern getState/setState, fidèle à Zustand) ------

interface MockDocumentState {
  documents: DocumentResponse[];
  isLoading: boolean;
  error: string | null;
  createModalRequested: boolean;
  ouvertureDemandee: string | null;
  loadDocuments: ReturnType<typeof vi.fn>;
  openDocument: ReturnType<typeof vi.fn>;
  createDocument: ReturnType<typeof vi.fn>;
  generateOutline: ReturnType<typeof vi.fn>;
  clearError: ReturnType<typeof vi.fn>;
  clearCreateModalRequest: ReturnType<typeof vi.fn>;
  effacerLaDemandeDOuverture: ReturnType<typeof vi.fn>;
}

vi.mock('../../stores/documentStore', () => {
  const state: MockDocumentState = {
    documents: [],
    isLoading: false,
    error: null,
    createModalRequested: false,
    ouvertureDemandee: null,
    loadDocuments: vi.fn(),
    openDocument: vi.fn(),
    createDocument: vi.fn(),
    generateOutline: vi.fn().mockResolvedValue(undefined),
    clearError: vi.fn(),
    clearCreateModalRequest: vi.fn(() => {
      state.createModalRequested = false;
    }),
    effacerLaDemandeDOuverture: vi.fn(() => {
      state.ouvertureDemandee = null;
    }),
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

// --- Mock de l'API projets (chargée par la modale de création) -------------

const mockListProjects = vi.fn();
vi.mock('../../services/api', () => ({
  listProjects: (...args: unknown[]) => mockListProjects(...args),
}));

// --- Mock de DocumentWorkspace (D3 - testé isolément ailleurs) -------------

vi.mock('./DocumentWorkspace', () => ({
  DocumentWorkspace: ({ documentId, onBack }: { documentId: string; onBack: () => void }) => (
    <div data-testid="document-workspace-mock" data-document-id={documentId}>
      <button onClick={onBack}>Retour (mock atelier)</button>
    </div>
  ),
}));

import { useDocumentStore } from '../../stores/documentStore';
import { DocumentsList } from './DocumentsList';


function makeDocument(overrides: Partial<DocumentResponse> = {}): DocumentResponse {
  return {
    id: 'doc-1',
    title: 'Proposition Client X',
    brief: 'Une proposition commerciale',
    status: 'en_cours',
    project_id: null,
    contact_id: null,
    created_at: '2026-07-01T00:00:00Z',
    updated_at: '2026-07-01T00:00:00Z',
    sections_total: 12,
    sections_validees: 7,
    ...overrides,
  };
}

describe('P-140 : ouvrir un document à la demande', () => {
  beforeEach(() => {
    mockListProjects.mockResolvedValue([]);
    const etat = useDocumentStore.getState() as unknown as { openDocument: ReturnType<typeof vi.fn> };
    etat.openDocument.mockClear();
    useDocumentStore.setState({ documents: [makeDocument()], ouvertureDemandee: null } as never);
  });

  it('une demande posée avant le montage ouvre l’atelier du document, puis s’efface', () => {
    useDocumentStore.setState({ ouvertureDemandee: 'doc-1' } as never);
    render(<DocumentsList />);
    expect(screen.getByTestId('document-workspace-mock')).toHaveAttribute('data-document-id', 'doc-1');
    const etat = useDocumentStore.getState() as unknown as { openDocument: ReturnType<typeof vi.fn>; ouvertureDemandee: string | null };
    expect(etat.openDocument).toHaveBeenCalledWith('doc-1');
    expect(etat.ouvertureDemandee).toBeNull();
  });
});

describe('P-142 : l’atelier ouvert se rouvre après un rechargement', () => {
  beforeEach(() => {
    mockListProjects.mockResolvedValue([]);
    useDocumentStore.setState({ documents: [makeDocument()], ouvertureDemandee: null } as never);
  });

  it('le document quitté se rouvre, et quitter la vue l’oublie', () => {
    sessionStorage.setItem('therese:document-quitte', 'doc-1');
    const { unmount } = render(<DocumentsList />);
    expect(screen.getByTestId('document-workspace-mock')).toHaveAttribute('data-document-id', 'doc-1');
    expect(sessionStorage.getItem('therese:document-quitte')).toBe('doc-1');
    unmount();
    expect(sessionStorage.getItem('therese:document-quitte')).toBeNull();
  });
});
