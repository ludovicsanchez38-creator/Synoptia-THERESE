/**
 * P-126 (persona Hugo, cycle 13) : « avec trois clients et plusieurs
 * conversations chacun, je ne sais pas où je clique ». Aucune ligne du tiroir
 * n'affichait son projet, aucun filtre par projet.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, within } from '@testing-library/react';
import { PrototypeConversationDrawer } from './PrototypeConversationDrawer';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { useChatStore } from '../../stores/chatStore';

vi.mock('../../hooks/useConversationSync', () => ({
  useConversationSync: vi.fn(() => ({ syncConversations: vi.fn(), loadConversationMessages: vi.fn() })),
}));
vi.mock('../../services/api/chat', () => ({
  renameConversation: vi.fn(),
  deleteConversation: vi.fn(),
  exportConversation: vi.fn(),
}));
const apiMocks = vi.hoisted(() => ({ listProjects: vi.fn() }));
vi.mock('../../services/api/memory', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api/memory')>()),
  listProjects: apiMocks.listProjects,
}));

const conversation = (id: string, title: string, projectId: string | null) => ({
  id, title, projectId, messages: [{ id: `${id}-m`, role: 'user', content: title, timestamp: new Date() }],
  createdAt: new Date(), updatedAt: new Date(), synced: true,
});

function ligne(titre: string): HTMLElement {
  return screen.getByText(titre).closest('button') as HTMLElement;
}

describe('P-126 : le tiroir dit à quel projet appartient une conversation', () => {
  beforeEach(() => {
    _clearEscapeHandlers();
    apiMocks.listProjects.mockResolvedValue([
      { id: 'p-asso', name: 'Site de l’association' },
      { id: 'p-orion', name: 'API client Orion' },
    ]);
    useChatStore.setState({
      conversations: [
        conversation('c1', 'Maquette de la page d’accueil', 'p-asso'),
        conversation('c2', 'Quota de l’API', 'p-orion'),
        conversation('c3', 'Idées de week-end', null),
      ],
      currentConversationId: null,
    } as never);
  });

  it('chaque ligne rattachée nomme son projet', async () => {
    render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={vi.fn()} />);
    expect(await within(ligne('Maquette de la page d’accueil')).findByText(/Site de l’association/)).toBeInTheDocument();
    expect(within(ligne('Quota de l’API')).getByText(/API client Orion/)).toBeInTheDocument();
    expect(ligne('Idées de week-end')).not.toHaveTextContent(/Projet/);
  });

  it('le filtre par projet ne garde que ses conversations, ou celles sans projet', async () => {
    render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={vi.fn()} />);
    const filtre = await screen.findByRole('combobox', { name: 'Filtrer par projet' });
    await within(filtre).findByRole('option', { name: 'API client Orion' });

    fireEvent.change(filtre, { target: { value: 'p-orion' } });
    expect(screen.getByText('Quota de l’API')).toBeInTheDocument();
    expect(screen.queryByText('Maquette de la page d’accueil')).toBeNull();
    expect(screen.queryByText('Idées de week-end')).toBeNull();

    fireEvent.change(filtre, { target: { value: '__sans_projet__' } });
    expect(screen.getByText('Idées de week-end')).toBeInTheDocument();
    expect(screen.queryByText('Quota de l’API')).toBeNull();
  });

  it('un filtre sans conversation ne prétend pas que l’historique est vide', async () => {
    useChatStore.setState({ conversations: [conversation('c2', 'Quota de l’API', 'p-orion')] } as never);
    render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={vi.fn()} />);
    const filtre = await screen.findByRole('combobox', { name: 'Filtrer par projet' });
    fireEvent.change(filtre, { target: { value: '__sans_projet__' } });
    expect(screen.getByText('Aucune conversation trouvée')).toBeInTheDocument();
    expect(screen.queryByText(/Ta première demande/)).toBeNull();
  });

  it('P-127 : la recherche trouve une conversation par le nom de son projet', async () => {
    render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={vi.fn()} surface="search" />);
    await within(ligne('Quota de l’API')).findByText(/API client Orion/);
    fireEvent.change(screen.getByRole('searchbox', { name: 'Rechercher une conversation' }), { target: { value: 'orion' } });
    expect(screen.getByText('Quota de l’API')).toBeInTheDocument();
    expect(screen.queryByText('Maquette de la page d’accueil')).toBeNull();
  });

  it('noms de projets illisibles : la ligne dit « Projet rattaché » sans inventer de nom', async () => {
    apiMocks.listProjects.mockRejectedValue(new Error('panne'));
    render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={vi.fn()} />);
    expect(await within(ligne('Quota de l’API')).findByText(/Projet rattaché/)).toBeInTheDocument();
  });
});
