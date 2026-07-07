/**
 * THÉRÈSE v2 - Tests DocumentsList (Atelier documentaire, D2/D3)
 *
 * Vérifie : rendu de la liste mockée + progression (« x/y sections
 * validées »), vide guidé, bascule vers l'atelier au clic, et la création
 * via la modale (mock du documentStore - pas d'appel réseau réel).
 * Régression layout (leçon 0.24.3) : la racine doit être `flex-1 min-h-0`,
 * jamais `h-full` (sinon la vue déborde de son conteneur).
 *
 * `DocumentWorkspace` (D3, trame draggable + éditeur de section) est mocké
 * ici en composant enfant superficiel - sa propre logique (dont l'appel à
 * `closeDocument()` au retour) est testée dans `DocumentWorkspace.test.tsx`.
 * Ce fichier ne teste que la responsabilité de `DocumentsList` : bascule
 * liste <-> atelier + transmission de `documentId`/`onBack`.
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { DocumentResponse } from '../../services/api/documents';

// --- Mock documentStore (pattern getState/setState, fidèle à Zustand) ------

interface MockDocumentState {
  documents: DocumentResponse[];
  isLoading: boolean;
  error: string | null;
  createModalRequested: boolean;
  loadDocuments: ReturnType<typeof vi.fn>;
  openDocument: ReturnType<typeof vi.fn>;
  createDocument: ReturnType<typeof vi.fn>;
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

describe('DocumentsList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockListProjects.mockResolvedValue([]);
    useDocumentStore.setState({
      documents: [],
      isLoading: false,
      error: null,
      createModalRequested: false,
    });
  });

  it('rend les documents mockés avec la progression « x/y sections validées »', () => {
    useDocumentStore.setState({
      documents: [
        makeDocument({ id: 'doc-1', title: 'Proposition Client X', sections_total: 12, sections_validees: 7 }),
        makeDocument({ id: 'doc-2', title: 'Dossier Y', sections_total: 0, sections_validees: 0, status: 'en_cours' }),
      ],
    });

    render(<DocumentsList />);

    expect(screen.getByText('Proposition Client X')).toBeInTheDocument();
    expect(screen.getByText('7/12 sections validées')).toBeInTheDocument();
    expect(screen.getByText('Dossier Y')).toBeInTheDocument();
    expect(screen.getByText('Trame non générée')).toBeInTheDocument();

    // loadDocuments doit être appelé au montage (chargement initial de la liste)
    expect(useDocumentStore.getState().loadDocuments).toHaveBeenCalled();
  });

  it('régression layout (0.24.3) : la racine liste est flex-1 min-h-0, pas h-full', () => {
    render(<DocumentsList />);
    const root = screen.getByTestId('documents-list');
    expect(root.className).toContain('flex-1');
    expect(root.className).toContain('min-h-0');
    expect(root.className).not.toContain('h-full');
  });

  it('vide guidé : une phrase + bouton créer quand il n\'y a aucun document', () => {
    render(<DocumentsList />);

    expect(screen.getByText(/Crée ton premier document/i)).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /Nouveau document/i }).length).toBeGreaterThan(0);
  });

  it('clic sur un document appelle openDocument et affiche l\'atelier (DocumentWorkspace, D3)', () => {
    useDocumentStore.setState({
      documents: [makeDocument({ id: 'doc-42', title: 'Rapport annuel' })],
    });

    render(<DocumentsList />);
    fireEvent.click(screen.getByText('Rapport annuel'));

    expect(useDocumentStore.getState().openDocument).toHaveBeenCalledWith('doc-42');
    const workspace = screen.getByTestId('document-workspace-mock');
    expect(workspace).toBeInTheDocument();
    expect(workspace).toHaveAttribute('data-document-id', 'doc-42');
  });

  it('le retour de l\'atelier (onBack de DocumentWorkspace) revient à la liste', () => {
    useDocumentStore.setState({
      documents: [makeDocument({ id: 'doc-42', title: 'Rapport annuel' })],
    });

    render(<DocumentsList />);
    fireEvent.click(screen.getByText('Rapport annuel'));
    expect(screen.getByTestId('document-workspace-mock')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Retour \(mock atelier\)/i }));
    expect(screen.getByTestId('documents-list')).toBeInTheDocument();
  });

  it('la modale crée un document via le store (mock) puis se ferme', async () => {
    const created = makeDocument({ id: 'doc-new', title: 'Nouveau dossier' });
    vi.mocked(useDocumentStore.getState().createDocument).mockResolvedValue(created);

    render(<DocumentsList />);

    fireEvent.click(screen.getAllByRole('button', { name: /Nouveau document/i })[0]);

    const dialog = await screen.findByRole('dialog', { name: /Nouveau document/i });
    const titleInput = within(dialog).getByLabelText(/Titre/i);
    fireEvent.change(titleInput, { target: { value: 'Nouveau dossier' } });

    fireEvent.click(within(dialog).getByRole('button', { name: /^Créer$/i }));

    await waitFor(() => {
      expect(useDocumentStore.getState().createDocument).toHaveBeenCalledWith({
        title: 'Nouveau dossier',
        brief: '',
        project_id: null,
      });
    });

    await waitFor(() => {
      expect(screen.queryByRole('dialog', { name: /Nouveau document/i })).not.toBeInTheDocument();
    });
  });

  it('la modale affiche une erreur si le titre est vide (pas d\'appel API)', async () => {
    render(<DocumentsList />);

    fireEvent.click(screen.getAllByRole('button', { name: /Nouveau document/i })[0]);
    const dialog = await screen.findByRole('dialog', { name: /Nouveau document/i });

    fireEvent.click(within(dialog).getByRole('button', { name: /^Créer$/i }));

    expect(await within(dialog).findByText(/titre du document est requis/i)).toBeInTheDocument();
    expect(useDocumentStore.getState().createDocument).not.toHaveBeenCalled();
  });

  it('createModalRequested (D4, ⌘K/Accueil « Nouveau document ») ouvre la modale et efface le drapeau', async () => {
    useDocumentStore.setState({ createModalRequested: true });

    render(<DocumentsList />);

    await screen.findByRole('dialog', { name: /Nouveau document/i });
    expect(useDocumentStore.getState().clearCreateModalRequest).toHaveBeenCalledTimes(1);
  });

  it('état dégradé : si listProjects échoue, la modale affiche « Projets indisponibles » à la place du select', async () => {
    // L'échec est loggé en console.error par la modale : neutralisé pour ne
    // pas polluer la sortie du test.
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    mockListProjects.mockRejectedValue(new Error('backend indisponible'));

    render(<DocumentsList />);
    fireEvent.click(screen.getAllByRole('button', { name: /Nouveau document/i })[0]);
    const dialog = await screen.findByRole('dialog', { name: /Nouveau document/i });

    expect(await within(dialog).findByText(/Projets indisponibles/i)).toBeInTheDocument();
    expect(within(dialog).queryByRole('combobox')).not.toBeInTheDocument();

    consoleSpy.mockRestore();
  });
});
