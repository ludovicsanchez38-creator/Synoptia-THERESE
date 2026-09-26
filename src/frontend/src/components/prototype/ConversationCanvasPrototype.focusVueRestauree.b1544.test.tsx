/**
 * B-1544 : une vue rouverte après un rechargement (P-142) n'a pas de
 * déclencheur mémorisé ; à sa fermeture, le focus tombait sur la page.
 * Il revient au composeur de l'accueil, l'entrée principale.
 */
import { act, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

describe('B-1544 : fermer une vue restaurée rend le focus à l’accueil', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _clearEscapeHandlers();
    sessionStorage.clear();
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
    useNavigationStore.setState({ activeView: null, history: [] } as never);
    window.history.replaceState({}, '', '/?interface=conversation-canvas');
  });

  it('le focus va au composeur, pas sur la page', async () => {
    sessionStorage.setItem('therese:vue-quittee', 'projects');
    const { container } = render(<ConversationCanvasPrototype />);
    await act(async () => { await Promise.resolve(); });
    expect(container.querySelector('[data-embedded-view]')?.getAttribute('data-embedded-view')).toBe('projects');

    await act(async () => {
      useNavigationStore.getState().retourAccueil();
      await new Promise((fin) => setTimeout(fin, 20));
    });

    expect(document.activeElement).not.toBe(document.body);
    expect(document.activeElement).toBe(screen.getByLabelText('Message à Thérèse'));
  });
});
