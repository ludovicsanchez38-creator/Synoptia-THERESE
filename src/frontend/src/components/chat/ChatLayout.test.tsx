import { useEffect } from 'react';
import { act, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ChatLayout } from './ChatLayout';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';
import { usePanelStore } from '../../stores/panelStore';

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
    window.history.replaceState({}, '', '/');
    localStorage.setItem('therese-skip-dashboard', 'true');
    usePersonalisationStore.setState({ skipDashboard: true });
    useNavigationStore.setState({ activeView: 'chat', history: [], initializeView: () => {} });
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
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

  it('ouvre la vue classique demandée par le repli de la 0.40', async () => {
    window.history.replaceState({}, '', '/?interface=classic&view=documents');
    render(<ChatLayout />);

    await waitFor(() => expect(useNavigationStore.getState().activeView).toBe('documents'));
    expect(await screen.findByTestId('documents-list-view')).toBeInTheDocument();
  });

  it('conserve l’onglet de réglages demandé jusqu’au montage différé de la modale', async () => {
    window.history.replaceState({}, '', '/?interface=classic&view=chat&action=settings.open&settings_tab=advanced');
    render(<ChatLayout />);

    await waitFor(() => expect(usePanelStore.getState().showSettings).toBe(true));
    expect(usePanelStore.getState().requestedSettingsTab).toBe('advanced');
    expect(new URL(window.location.href).searchParams.has('settings_tab')).toBe(false);
  });
});
