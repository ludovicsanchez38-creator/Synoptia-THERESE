import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { PrototypeConversationDrawer } from './PrototypeConversationDrawer';
import { useChatStore } from '../../stores/chatStore';

vi.mock('../../hooks/useConversationSync', () => ({
  useConversationSync: vi.fn(() => ({ syncConversations: vi.fn(), loadConversationMessages: vi.fn() })),
}));

const { renameRemote, deleteRemote, exportRemote } = vi.hoisted(() => ({
  renameRemote: vi.fn(),
  deleteRemote: vi.fn(),
  exportRemote: vi.fn(),
}));

vi.mock('../../services/api/chat', () => ({
  renameConversation: renameRemote,
  deleteConversation: deleteRemote,
  exportConversation: exportRemote,
}));

describe('PrototypeConversationDrawer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    renameRemote.mockResolvedValue({});
    deleteRemote.mockResolvedValue(undefined);
    exportRemote.mockResolvedValue(undefined);
    useChatStore.setState({
      conversations: [{
        id: 'conversation-1',
        title: 'Préparation rendez-vous réel',
        messages: [],
        messageCount: 3,
        createdAt: new Date(),
        updatedAt: new Date(),
        synced: true,
      }],
      currentConversationId: null,
    });
  });

  it('affiche uniquement les conversations du store et ouvre la sélection', () => {
    const onClose = vi.fn();
    const onOpenChat = vi.fn();
    render(<PrototypeConversationDrawer onClose={onClose} onOpenChat={onOpenChat} />);

    expect(screen.getByText('Préparation rendez-vous réel')).toBeInTheDocument();
    expect(screen.queryByText(/PROPULSER|Programme parrainage|12 conversations/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByText('Préparation rendez-vous réel'));

    expect(useChatStore.getState().currentConversationId).toBe('conversation-1');
    expect(onClose).toHaveBeenCalledTimes(1);
    expect(onOpenChat).toHaveBeenCalledTimes(1);
  });

  it('recherche et crée une vraie conversation locale', () => {
    const onClose = vi.fn();
    const onOpenChat = vi.fn();
    render(<PrototypeConversationDrawer onClose={onClose} onOpenChat={onOpenChat} />);

    fireEvent.change(screen.getByLabelText('Rechercher une conversation'), { target: { value: 'absente' } });
    expect(screen.getByText('Aucune conversation trouvée')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Rechercher une conversation'), { target: { value: '' } });
    fireEvent.click(screen.getByRole('button', { name: 'Nouvelle conversation' }));

    expect(useChatStore.getState().conversations[0].title).toBe('Nouvelle conversation');
    expect(onOpenChat).toHaveBeenCalledTimes(1);
  });

  it('expose les trois surfaces du tiroir sans panneau concurrent', () => {
    const { rerender } = render(
      <PrototypeConversationDrawer
        surface="new"
        onClose={vi.fn()}
        onOpenChat={vi.fn()}
      />,
    );

    expect(screen.getByRole('button', { name: 'Nouvelle conversation' })).toHaveFocus();

    rerender(
      <PrototypeConversationDrawer
        surface="search"
        onClose={vi.fn()}
        onOpenChat={vi.fn()}
      />,
    );
    expect(screen.getByLabelText('Rechercher une conversation')).toHaveFocus();

    fireEvent.change(screen.getByLabelText('Rechercher une conversation'), {
      target: { value: 'rendez-vous' },
    });
    rerender(
      <PrototypeConversationDrawer
        surface="history"
        onClose={vi.fn()}
        onOpenChat={vi.fn()}
      />,
    );

    expect(screen.getByLabelText('Historique des conversations')).toHaveFocus();
    expect(screen.getByLabelText('Rechercher une conversation')).toHaveValue('');
  });

  it('persiste le renommage dans le backend', async () => {
    render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: 'Actions pour Préparation rendez-vous réel' }));
    fireEvent.click(screen.getByRole('button', { name: 'Renommer' }));
    fireEvent.change(screen.getByLabelText('Nouveau titre'), { target: { value: 'Rendez-vous Camille' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));

    await waitFor(() => expect(renameRemote).toHaveBeenCalledWith('conversation-1', 'Rendez-vous Camille'));
    expect(useChatStore.getState().conversations[0].title).toBe('Rendez-vous Camille');
  });

  it('demande une confirmation avant la suppression backend', async () => {
    render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: 'Actions pour Préparation rendez-vous réel' }));
    fireEvent.click(screen.getByRole('button', { name: 'Supprimer' }));

    expect(screen.getByTestId('conversation-delete-confirmation')).toBeInTheDocument();
    expect(deleteRemote).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Confirmer la suppression' }));
    await waitFor(() => expect(deleteRemote).toHaveBeenCalledWith('conversation-1'));
    expect(useChatStore.getState().conversations).toHaveLength(0);
  });

  it('conserve la conversation courante pendant une réponse en cours', () => {
    const onClose = vi.fn();
    const onOpenChat = vi.fn();
    render(
      <PrototypeConversationDrawer
        navigationLocked
        onClose={onClose}
        onOpenChat={onOpenChat}
      />,
    );

    fireEvent.click(screen.getByText('Préparation rendez-vous réel'));

    expect(screen.getByRole('alert')).toHaveTextContent(
      'Arrête la réponse en cours avant de changer de conversation.',
    );
    expect(useChatStore.getState().currentConversationId).toBeNull();
    expect(onClose).not.toHaveBeenCalled();
    expect(onOpenChat).not.toHaveBeenCalled();
  });
});
