import { useEffect } from 'react';
import { act, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ChatLayout } from './ChatLayout';
import { useToolConfirmationStore } from '../../stores/toolConfirmationStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';

vi.mock('./ChatHeader', () => ({
  ChatHeader: () => <div data-testid="chat-header" />,
}));

vi.mock('./MessageList', () => ({
  MessageList: ({ onGuidedPanelChange }: { onGuidedPanelChange?: (active: boolean) => void }) => {
    useEffect(() => {
      onGuidedPanelChange?.(true);
    }, [onGuidedPanelChange]);
    return <div data-testid="message-list" />;
  },
}));

vi.mock('./ChatInput', () => ({
  ChatInput: () => <div data-testid="chat-input" />,
}));

vi.mock('./CommandPalette', () => ({
  CommandPalette: () => null,
}));

vi.mock('./ConversationMemoryChip', () => ({
  ConversationMemoryChip: () => <div data-testid="conversation-memory-chip" />,
}));

vi.mock('./ShortcutsModal', () => ({
  ShortcutsModal: () => null,
}));

vi.mock('../sidebar/ConversationSidebar', () => ({
  ConversationSidebar: () => null,
}));

vi.mock('../files/DropZone', () => ({
  DropZone: () => null,
}));

vi.mock('./PanelContainer', () => ({
  PanelContainer: () => null,
}));

vi.mock('../ui/SideToggle', () => ({
  SideToggle: () => null,
}));

vi.mock('../ui/ConnectionStatus', () => ({
  ConnectionStatus: () => null,
}));

vi.mock('../../hooks', () => ({
  useKeyboardShortcuts: () => {},
  useConversationSync: () => {},
  useFileDrop: () => ({ isDragging: false }),
  useOnlineStatus: () => true,
}));

vi.mock('../../services/api/commands', () => ({
  listUserCommands: vi.fn().mockResolvedValue([]),
}));

describe('ChatLayout', () => {
  beforeEach(() => {
    localStorage.setItem('therese-skip-dashboard', 'true');
    usePersonalisationStore.setState({ skipDashboard: true });
    useNavigationStore.setState({ activeView: 'chat', history: [], initializeView: () => {} });
    useToolConfirmationStore.setState({
      pending: [
        {
          confirmation_id: 'bug114',
          tool_name: 'send_email',
          arguments: {
            to: 'merci@example.fr',
            subject: 'Merci',
            body: 'Merci pour votre retour.',
          },
        },
      ],
    });
  });

  it('affiche la confirmation d\'envoi même si le panneau guidé est actif', async () => {
    render(<ChatLayout />);
    act(() => {
      useNavigationStore.setState({ activeView: 'chat' });
    });

    expect(await screen.findByText("Confirmer l'envoi de l'email")).toBeInTheDocument();
    expect(screen.getByText('merci@example.fr')).toBeInTheDocument();
  });
});