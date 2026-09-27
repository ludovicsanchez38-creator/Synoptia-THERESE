/** B-1728 : Actions ne doit pas masquer les commandes de l'accueil à 1440 px. */
import { act, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ActionPanel } from '../actions/ActionPanel';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { useActionsStore } from '../../stores/actionsStore';
import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

vi.mock('../../services/api/actions', () => ({
  listAgents: vi.fn().mockResolvedValue([]),
  runAction: vi.fn(),
  listTasks: vi.fn().mockResolvedValue([]),
  getTask: vi.fn(),
  cancelTask: vi.fn(),
}));
vi.mock('../../hooks/useConversationSync', () => ({ useConversationSync: vi.fn() }));

function largeur(coteACote: boolean) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: query.includes('min-width: 1280px') ? coteACote : false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })) as unknown as typeof window.matchMedia;
}

function page() {
  render(<><ConversationCanvasPrototype /><ActionPanel /></>);
  return screen.getByTestId('conversation-canvas-prototype');
}

describe('B-1728 : Actions occupe sa propre largeur', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/?interface=conversation-canvas');
    _clearEscapeHandlers();
    useActionsStore.setState({ isPanelOpen: false, activeTask: null, selectedAgent: null, agents: [] } as never);
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
    useNavigationStore.setState({ activeView: 'chat', history: [] });
    usePanelStore.setState({
      showSettings: false, requestedSettingsTab: null, showSaveCommand: false,
      showContactModal: false, showProjectModal: false, showBoardPanel: false,
      showShortcuts: false, showPromptLibrary: false, showCommandPalette: false,
      showConversationSidebar: false,
    });
    usePersonalisationStore.setState({ skipDashboard: false });
  });

  it('à 1440 px, réserve 380 px au panneau et rend toute la largeur après fermeture', () => {
    largeur(true);
    const coque = page();
    expect(coque.style.width).toBe('');

    act(() => useActionsStore.getState().openPanel());
    expect(screen.getByRole('heading', { name: 'Actions' })).toBeInTheDocument();
    expect(coque.style.width).toBe('calc(100vw - 380px)');
    expect(screen.queryByTestId('panneau-voile')).toBeNull();

    act(() => useActionsStore.getState().closePanel());
    expect(coque.style.width).toBe('');
  });

  it('à 800 px, garde la largeur de la coque et isole le fond couvert', () => {
    largeur(false);
    const coque = page();

    act(() => useActionsStore.getState().openPanel());
    expect(coque.style.width).toBe('');
    expect(screen.getByTestId('panneau-voile')).toBeInTheDocument();
    expect(coque.hasAttribute('inert')).toBe(true);
  });
});
