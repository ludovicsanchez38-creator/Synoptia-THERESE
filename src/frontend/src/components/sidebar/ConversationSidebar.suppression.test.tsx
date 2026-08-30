/**
 * Revue 30/08 : une conversation synced dont la suppression serveur
 * échoue ne doit pas disparaître de l'état local.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ConversationSidebar } from './ConversationSidebar';
import { useChatStore } from '../../stores/chatStore';
import { useStatusStore } from '../../stores/statusStore';

const deleteRemote = vi.fn();

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    deleteConversation: (...args: unknown[]) => deleteRemote(...args),
    getConversationMessages: vi.fn(),
    renameConversation: vi.fn(),
    exportConversation: vi.fn(),
  };
});

vi.mock('../../hooks', () => ({
  useDemoMask: () => ({ maskText: (t: string) => t }),
}));

function poserConversation(synced: boolean) {
  useChatStore.setState({
    conversations: [
      {
        id: 'conv-1',
        title: 'À garder',
        messages: [],
        createdAt: new Date(),
        updatedAt: new Date(),
        synced,
      },
    ],
    currentConversationId: 'conv-1',
  });
}

describe('ConversationSidebar — suppression honnête', () => {
  beforeEach(() => {
    deleteRemote.mockReset();
    useStatusStore.setState({ notifications: [] });
    poserConversation(true);
  });

  it('garde la conversation et signale l’échec si le serveur refuse', async () => {
    deleteRemote.mockRejectedValue(new Error('backend down'));
    render(<ConversationSidebar isOpen onClose={() => {}} />);

    const item = screen.getByTestId('sidebar-conversation-item');
    const menuButton = item.querySelector('button');
    expect(menuButton).toBeTruthy();
    fireEvent.click(menuButton!);
    fireEvent.click(screen.getByText('Supprimer'));

    await waitFor(() => {
      expect(deleteRemote).toHaveBeenCalledWith('conv-1');
    });
    expect(useChatStore.getState().conversations.map((c) => c.id)).toContain('conv-1');
    expect(useStatusStore.getState().notifications.some((n) => n.type === 'error')).toBe(true);
  });
});
