/**
 * B-860 (cycle 9) : « Écrire » (chooseScenario('email')) ouvre une rédaction
 * libre dans le canevas, mais le lien profond `?scenario=email` laissait le
 * canevas fermé : arriver par la porte de l'URL ne montrait pas la même chose
 * qu'arriver par le clic.
 */
import { act, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

const CANEVAS = '[aria-labelledby="prototype-context-canvas-title"]';

describe('Coque - B-860, le lien profond email ouvre la même rédaction que le clic', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _clearEscapeHandlers();
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
    useNavigationStore.setState({ activeView: null, history: [] } as never);
    window.history.replaceState({}, '', '/?interface=conversation-canvas&scenario=email');
  });

  it('monte le canevas « Nouveau message » dès l’URL', async () => {
    render(<ConversationCanvasPrototype />);
    await act(async () => { await Promise.resolve(); });

    const canevas = document.querySelector(CANEVAS) as HTMLElement | null;
    expect(canevas).not.toBeNull();
    expect(within(canevas!).getByText('Nouveau message')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Fermer ce panneau' })).toBeInTheDocument();
  });
});
