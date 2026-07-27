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

  it('modale ⌘K fantôme (revue finale, finding minor 4) : createModalRequested pendant que l\'atelier est ouvert efface le drapeau SANS afficher la modale, et elle ne surgit pas au retour à la liste', async () => {
    useDocumentStore.setState({
      documents: [makeDocument({ id: 'doc-42', title: 'Rapport annuel' })],
    });

    const { rerender } = render(<DocumentsList />);
    fireEvent.click(screen.getByText('Rapport annuel'));
    expect(screen.getByTestId('document-workspace-mock')).toBeInTheDocument();

    // Simule une requête ⌘K « Nouveau document » déclenchée pendant que
    // l'atelier est affiché (le store n'est pas réactif dans ce mock -
    // rerender force DocumentsList à relire l'état frais).
    useDocumentStore.setState({ createModalRequested: true });
    rerender(<DocumentsList />);

    // Rien ne s'affiche pendant que l'atelier est ouvert (pas de dialog) ET
    // le drapeau est bien consommé (pas laissé en attente).
    expect(screen.queryByRole('dialog', { name: /Nouveau document/i })).not.toBeInTheDocument();
    expect(useDocumentStore.getState().clearCreateModalRequest).toHaveBeenCalledTimes(1);
    expect(useDocumentStore.getState().createModalRequested).toBe(false);

    // Retour à la liste : la modale ne doit PAS surgir après coup.
    fireEvent.click(screen.getByRole('button', { name: /Retour \(mock atelier\)/i }));
    expect(screen.getByTestId('documents-list')).toBeInTheDocument();
    expect(screen.queryByRole('dialog', { name: /Nouveau document/i })).not.toBeInTheDocument();
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

  // BUG-154 (27/07/2026) - Le badge « En cours » désignait l'état de rédaction
  // du document, pas un traitement : le testeur a attendu 40 minutes une
  // génération qui n'avait jamais été lancée. Et après création, le document
  // restait sans trame, sans que rien ne l'indique.
  describe('BUG-154 - lisibilité de l’état et enchaînement de la trame', () => {
    it('un document sans trame l’annonce au lieu d’afficher « En cours »', () => {
      useDocumentStore.setState({
        documents: [makeDocument({ id: 'doc-vide', title: 'Plan de test', sections_total: 0, sections_validees: 0 })],
      });

      render(<DocumentsList />);

      const carte = screen.getByTestId('document-card');
      expect(within(carte).getByText('Sans trame')).toBeInTheDocument();
      expect(within(carte).queryByText('En cours')).toBeNull();
    });

    it('un document déjà structuré est en rédaction, pas « en cours » de traitement', () => {
      useDocumentStore.setState({
        documents: [makeDocument({ id: 'doc-2', sections_total: 4, sections_validees: 1 })],
      });

      render(<DocumentsList />);

      const carte = screen.getByTestId('document-card');
      expect(within(carte).getByText('Rédaction')).toBeInTheDocument();
    });

    it('après création, le document s’ouvre et la trame est lancée', async () => {
      const generateOutline = vi.fn().mockResolvedValue(undefined);
      useDocumentStore.setState({
        documents: [],
        generateOutline,
        createDocument: vi.fn().mockResolvedValue(makeDocument({ id: 'doc-neuf', sections_total: 0 })),
      } as never);
      mockListProjects.mockResolvedValue([]);

      render(<DocumentsList />);
      fireEvent.click(screen.getAllByRole('button', { name: /Nouveau document/i })[0]);
      const dialog = await screen.findByRole('dialog', { name: /Nouveau document/i });
      fireEvent.change(within(dialog).getByLabelText(/Titre/i), { target: { value: 'Plan de test' } });
      fireEvent.click(within(dialog).getByRole('button', { name: /^Créer/i }));

      await waitFor(() => {
        expect(useDocumentStore.getState().openDocument).toHaveBeenCalledWith('doc-neuf');
      });
      await waitFor(() => {
        expect(generateOutline).toHaveBeenCalledWith('doc-neuf');
      });
    });

    // Revue Soso 27/07 (F5) : openDocument n'était pas attendu et isLoading est
    // partagé - un GET rapide rendait le bouton « Générer la trame » cliquable
    // pendant que le modèle travaillait, d'où deux générations et deux jeux de
    // sections possibles pour le même document.
    it('n’enchaîne la trame qu’après l’ouverture du document', async () => {
      const ordre: string[] = [];
      const openDocument = vi.fn().mockImplementation(async () => {
        await new Promise((r) => setTimeout(r, 10));
        ordre.push('open');
      });
      const generateOutline = vi.fn().mockImplementation(async () => {
        ordre.push('outline');
      });
      useDocumentStore.setState({
        documents: [],
        openDocument,
        generateOutline,
        createDocument: vi.fn().mockResolvedValue(makeDocument({ id: 'doc-neuf', sections_total: 0 })),
      } as never);
      mockListProjects.mockResolvedValue([]);

      render(<DocumentsList />);
      fireEvent.click(screen.getAllByRole('button', { name: /Nouveau document/i })[0]);
      const dialog = await screen.findByRole('dialog', { name: /Nouveau document/i });
      fireEvent.change(within(dialog).getByLabelText(/Titre/i), { target: { value: 'Plan de test' } });
      fireEvent.click(within(dialog).getByRole('button', { name: /^Créer/i }));

      await waitFor(() => expect(generateOutline).toHaveBeenCalledTimes(1));
      expect(ordre).toEqual(['open', 'outline']);
    });
  });
});
