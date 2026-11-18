/**
 * B-1943 : « Contrôle des données » est `hidden` jusqu’au palier sm, et le
 * nom d’espace jusqu’à md. `display: none` les retire de l’arbre. La
 * recherche, elle, est restée joignable (B-1403, B-761).
 *
 * Le test pose la règle CSS réelle de l’utilitaire `hidden` : jsdom ne charge
 * pas la feuille Tailwind.
 */
import { isInaccessible } from '@testing-library/dom';
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

let style: HTMLStyleElement;

beforeEach(() => {
  vi.clearAllMocks();
  _clearEscapeHandlers();
  window.history.replaceState({}, '', '/?interface=conversation-canvas');
  useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
  useNavigationStore.setState({ activeView: null, history: [] } as never);
  usePersonalisationStore.setState({ skipDashboard: false });
  usePanelStore.setState({
    showSettings: false, showSaveCommand: false, showContactModal: false, showProjectModal: false,
    showBoardPanel: false, showShortcuts: false, showPromptLibrary: false, showCommandPalette: false,
    showConversationSidebar: false,
  } as never);
  style = document.createElement('style');
  style.textContent = '.hidden { display: none !important; }';
  document.head.appendChild(style);
});

afterEach(() => {
  style.remove();
});

describe('B-1943 : les contrôles d’en-tête restent dans l’arbre', () => {
  it('Contrôle des données s’ouvre, il n’est pas retiré de l’écran', () => {
    render(<ConversationCanvasPrototype />);
    const controle = screen.queryByRole('button', { name: 'Contrôle des données' });
    expect(controle).not.toBeNull();
    fireEvent.click(controle!);
    expect(screen.getByRole('dialog', { name: 'Centre de confiance' })).toBeInTheDocument();
  });

  it('le nom d’espace reste annonçable', () => {
    render(<ConversationCanvasPrototype />);
    const espace = screen.getByTestId('workspace-label');
    expect(isInaccessible(espace)).toBe(false);
    expect(espace).toHaveAccessibleName(/Espace de travail/);
  });
});
