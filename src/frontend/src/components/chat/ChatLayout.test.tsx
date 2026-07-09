import { useEffect } from 'react';
import { act, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ChatLayout } from './ChatLayout';
import { useToolConfirmationStore } from '../../stores/toolConfirmationStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';

vi.mock('./ChatHeader', () => ({
  // Mock minimal exposant le bouton Documents : teste le câblage ChatLayout
  // (onToggleDocumentsPanel -> setView('documents')) sans rendre le vrai
  // header (Tauri). Le vrai bouton est couvert par ChatHeader.test.tsx.
  ChatHeader: ({ onToggleDocumentsPanel }: { onToggleDocumentsPanel?: () => void }) => (
    <div data-testid="chat-header">
      <button data-testid="header-documents-btn" onClick={onToggleDocumentsPanel}>
        Documents
      </button>
    </div>
  ),
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

// Vue Documents (lazy) : mockée pour ne pas déclencher le vrai documentStore
// (appels réseau) - on teste ici le routage, pas le contenu de la vue.
vi.mock('../documents/DocumentsList', () => ({
  DocumentsList: () => <div data-testid="documents-list-view" />,
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

  it('D2 : le bouton Documents du header navigue vers la vue documents', async () => {
    render(<ChatLayout />);
    act(() => {
      useNavigationStore.setState({ activeView: 'chat' });
    });

    act(() => {
      screen.getByTestId('header-documents-btn').click();
    });

    expect(useNavigationStore.getState().activeView).toBe('documents');
    // La vue Documents (lazy, mockée) est bien rendue dans la zone principale.
    expect(await screen.findByTestId('documents-list-view')).toBeInTheDocument();
  });

  it('BUG-116 : la back-bar affiche Retour quand elle revient à la vue précédente', async () => {
    render(<ChatLayout />);

    act(() => {
      useNavigationStore.setState({ activeView: 'email' });
    });

    expect(await screen.findByRole('button', { name: 'Retour' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Retour au chat' })).not.toBeInTheDocument();
  });
});