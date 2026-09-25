/**
 * P-142 : la coque rouvre l'écran quitté après un rechargement, sauf lien
 * profond ; revenir à l'accueil oublie l'écran.
 */
import { act, render } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

function ecranAffiche(container: HTMLElement): string | null {
  return container.querySelector('[data-embedded-view]')?.getAttribute('data-embedded-view') ?? null;
}

describe('P-142 : reprendre l’écran quitté', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _clearEscapeHandlers();
    sessionStorage.clear();
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
    useNavigationStore.setState({ activeView: null, history: [] } as never);
    window.history.replaceState({}, '', '/?interface=conversation-canvas');
  });

  it('un rechargement rouvre la vue quittée', async () => {
    sessionStorage.setItem('therese:vue-quittee', 'projects');
    const { container } = render(<ConversationCanvasPrototype />);
    await act(async () => { await Promise.resolve(); });
    expect(ecranAffiche(container)).toBe('projects');
  });

  it('un lien profond l’emporte', async () => {
    sessionStorage.setItem('therese:vue-quittee', 'projects');
    window.history.replaceState({}, '', '/?interface=conversation-canvas&scenario=email');
    const { container } = render(<ConversationCanvasPrototype />);
    await act(async () => { await Promise.resolve(); });
    expect(ecranAffiche(container)).not.toBe('projects');
  });

  it('revenir à l’accueil oublie l’écran', async () => {
    sessionStorage.setItem('therese:vue-quittee', 'projects');
    render(<ConversationCanvasPrototype />);
    await act(async () => { await Promise.resolve(); });
    await act(async () => { useNavigationStore.getState().retourAccueil(); await Promise.resolve(); });
    expect(sessionStorage.getItem('therese:vue-quittee')).toBeNull();
  });
});
