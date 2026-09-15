/**
 * B-817 (cycle 9) : depuis l'atelier documentaire, un seul Échap refermait deux
 * niveaux (l'atelier ET la liste Documents) parce que l'atelier ouvert ne
 * s'inscrivait pas sur la pile Échap unifiée : la cascade de la coque passait
 * directement au retour de vue.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { DocumentResponse } from '../../services/api/documents';
import { _clearEscapeHandlers, runTopEscapeHandler } from '../../lib/escapeStack';

// --- Mock documentStore (pattern getState/setState, fidèle à Zustand) ------

interface MockDocumentState {
  documents: DocumentResponse[];
  isLoading: boolean;
  error: string | null;
  createModalRequested: boolean;
  loadDocuments: ReturnType<typeof vi.fn>;
  openDocument: ReturnType<typeof vi.fn>;
  createDocument: ReturnType<typeof vi.fn>;
  generateOutline: ReturnType<typeof vi.fn>;
  clearError: ReturnType<typeof vi.fn>;
  clearCreateModalRequest: ReturnType<typeof vi.fn>;
}

vi.mock('../../stores/documentStore', () => {
  const state: MockDocumentState = {
    documents: [],
    isLoading: false,
    error: null,
    createModalRequested: false,
    loadDocuments: vi.fn(),
    openDocument: vi.fn(),
    createDocument: vi.fn(),
    generateOutline: vi.fn().mockResolvedValue(undefined),
    clearError: vi.fn(),
    clearCreateModalRequest: vi.fn(() => {
      state.createModalRequested = false;
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

describe('DocumentsList - B-817, Échap referme l’atelier, pas la vue', () => {
  beforeEach(() => {
    _clearEscapeHandlers();
    mockListProjects.mockResolvedValue([]);
    useDocumentStore.setState({ documents: [makeDocument({ id: 'doc-1', title: 'Compte rendu' })], isLoading: false, error: null });
  });

  it('l’atelier ouvert consomme Échap et rend la liste', async () => {
    render(<DocumentsList />);
    fireEvent.click(await screen.findByText('Compte rendu'));
    expect(screen.getByTestId('document-workspace-mock')).toBeInTheDocument();

    let consomme = false;
    await act(async () => { consomme = runTopEscapeHandler(); });
    expect(consomme).toBe(true);
    expect(screen.queryByTestId('document-workspace-mock')).toBeNull();
    expect(screen.getByText('Compte rendu')).toBeInTheDocument();
  });
});
