/**
 * BUG-182 (Discord, Dr_logic-3D, 23/09/2026) : dans « Contacts et mémoire »,
 * l'heure affichée à côté de THÉRÈSE restait celle de l'ouverture de
 * l'application. Le code annonce pourtant « l'heure du contenu affiché, figée
 * à son apparition » : elle était figée au montage du canevas, qui ne se
 * remonte pas quand on change de vue.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

describe('BUG-182 : l’heure dit quand le contenu affiché est apparu', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('ouvrir « Retrouver » deux heures après le lancement affiche l’heure de cette ouverture', async () => {
    vi.useFakeTimers({ toFake: ['Date'], shouldAdvanceTime: true });
    vi.setSystemTime(new Date(2026, 8, 23, 4, 11));
    const { useChatStore } = await import('../../stores/chatStore');
    const { useNavigationStore } = await import('../../stores/navigationStore');
    const { _clearEscapeHandlers } = await import('../../lib/escapeStack');
    const { ConversationCanvasPrototype } = await import('./ConversationCanvasPrototype');

    _clearEscapeHandlers();
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
    useNavigationStore.setState({ activeView: null, history: [] } as never);
    window.history.replaceState({}, '', '/?interface=conversation-canvas');

    render(<ConversationCanvasPrototype />);
    await act(async () => { await Promise.resolve(); });

    vi.setSystemTime(new Date(2026, 8, 23, 6, 11));
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /^Retrouver/ }));
    });

    const heures = () => screen.queryAllByText(/^·\s\d\d:\d\d$/).map((noeud) => noeud.textContent);
    await waitFor(() => expect(heures()).toEqual(['· 06:11']));
  }, 30000);
});
