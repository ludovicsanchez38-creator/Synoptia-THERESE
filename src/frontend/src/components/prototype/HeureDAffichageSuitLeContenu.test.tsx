/**
 * BUG-182 (Discord, Dr_logic-3D, 23/09/2026) : dans « Contacts et mémoire »,
 * l'heure affichée à côté de THÉRÈSE restait celle de l'ouverture de
 * l'application. Le code annonce pourtant « l'heure du contenu affiché, figée
 * à son apparition » : elle était figée au montage du canevas, qui ne se
 * remonte pas quand on change de vue.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

// B-981 : un brief frais à chaque lecture, comme le serveur en renvoie un.
vi.mock('../../services/api/dashboard', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  fetchTodayDashboard: vi.fn(async () => ({
    date: '2026-09-23', events: [], urgent_tasks: [], due_follow_ups: [], overdue_invoices: [], stale_prospects: [], indisponibles: [],
    summary: { events_count: 0, tasks_count: 0, follow_ups_count: 0, invoices_count: 0, prospects_count: 0 },
  })),
}));

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

  it('B-981 : « Accueil » depuis l’accueil rafraîchit le brief et l’heure « Rafraîchi à »', async () => {
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
    await waitFor(() => expect(screen.getByTestId('accueil-jour').textContent).toContain('Rafraîchi à 04:11'));

    vi.setSystemTime(new Date(2026, 8, 23, 6, 11));
    await act(async () => {
      fireEvent.click(screen.getAllByRole('button', { name: /^Accueil$/ })[0]);
    });

    await waitFor(() => expect(screen.getByTestId('accueil-jour').textContent).toContain('Rafraîchi à 06:11'));
  }, 30000);

  it('B-997 : une relecture du brief en échec ne refixe pas « Rafraîchi à »', async () => {
    vi.useFakeTimers({ toFake: ['Date'], shouldAdvanceTime: true });
    vi.setSystemTime(new Date(2026, 8, 23, 4, 11));
    const dashboard = await import('../../services/api/dashboard');
    const { useChatStore } = await import('../../stores/chatStore');
    const { useNavigationStore } = await import('../../stores/navigationStore');
    const { _clearEscapeHandlers } = await import('../../lib/escapeStack');
    const { ConversationCanvasPrototype } = await import('./ConversationCanvasPrototype');

    _clearEscapeHandlers();
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
    useNavigationStore.setState({ activeView: null, history: [] } as never);
    window.history.replaceState({}, '', '/?interface=conversation-canvas');

    render(<ConversationCanvasPrototype />);
    await waitFor(() => expect(screen.getByTestId('accueil-jour').textContent).toContain('Rafraîchi à 04:11'));

    vi.mocked(dashboard.fetchTodayDashboard).mockRejectedValue(new Error('moteur injoignable'));
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: /^Retrouver/ })); });
    vi.setSystemTime(new Date(2026, 8, 23, 6, 11));
    const appelsAvant = vi.mocked(dashboard.fetchTodayDashboard).mock.calls.length;
    await act(async () => {
      fireEvent.click(screen.getAllByRole('button', { name: /^Accueil$/ })[0]);
    });
    await waitFor(() => expect(vi.mocked(dashboard.fetchTodayDashboard).mock.calls.length).toBeGreaterThan(appelsAvant));
    for (let tour = 0; tour < 6; tour++) { await act(async () => { await Promise.resolve(); }); }
    expect(screen.getByTestId('accueil-jour').textContent).toContain('Rafraîchi à 04:11');
    expect(screen.getByTestId('accueil-jour').textContent).not.toContain('06:11');
  }, 30000);
});
