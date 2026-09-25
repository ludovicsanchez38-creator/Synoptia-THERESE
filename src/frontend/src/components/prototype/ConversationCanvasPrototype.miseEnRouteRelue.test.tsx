/**
 * B-1348 (persona Claire, cycle 13) : l'Accueil demandait encore de compléter
 * une facturation que l'on venait de compléter.
 *
 * La coque lisait `setup-status` une seule fois, au montage. Claire remplit sa
 * facturation dans Paramètres, ferme, revient : la carte « Compléter le profil
 * de facturation » restait, alors que l'API répondait `billing_complete: true`.
 * Tout ce que la mise en route mesure (facturation, messagerie, agenda, clé)
 * se règle dans Paramètres : la coque relit l'état à leur fermeture.
 */
import { act, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { fetchSetupStatus } from '../../services/api/dashboard';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

vi.mock('../../services/api/voice', async (importOriginal) => ({
  ...(await importOriginal<object>()),
}));

const briefVide = vi.hoisted(() => ({
  date: '2026-09-25',
  events: [],
  urgent_tasks: [],
  due_follow_ups: [],
  overdue_invoices: [],
  stale_prospects: [],
  indisponibles: [],
  summary: { events_count: 0, tasks_count: 0, follow_ups_count: 0, invoices_count: 0, prospects_count: 0 },
}));

const etat = (billing_complete: boolean) => ({
  has_calendar: true, has_email: true, billing_complete, has_invoices: false, has_llm_key: true, indisponibles: [],
});

vi.mock('../../services/api/dashboard', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  fetchTodayDashboard: vi.fn(async () => briefVide),
  fetchSetupStatus: vi.fn(),
}));

beforeEach(() => {
  vi.clearAllMocks();
  window.history.replaceState({}, '', '/?interface=conversation-canvas');
  useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
  usePanelStore.setState({
    showSettings: false, requestedSettingsTab: null, showSaveCommand: false,
    showContactModal: false, showProjectModal: false, showBoardPanel: false,
    showShortcuts: false, showPromptLibrary: false, showCommandPalette: false,
    showConversationSidebar: false,
  });
  _clearEscapeHandlers();
  useNavigationStore.setState({ activeView: 'chat', history: [] });
  usePersonalisationStore.setState({ skipDashboard: false });
});

describe('mise en route relue après les Paramètres (B-1348)', () => {
  it('la carte de facturation disparaît une fois la facturation complétée', async () => {
    vi.mocked(fetchSetupStatus)
      .mockResolvedValueOnce(etat(false))
      .mockResolvedValue(etat(true));
    render(<ConversationCanvasPrototype />);
    expect(await screen.findByText('Compléter le profil de facturation')).toBeInTheDocument();

    act(() => { usePanelStore.setState({ showSettings: true }); });
    act(() => { usePanelStore.setState({ showSettings: false }); });

    await waitFor(() => {
      expect(screen.queryByText('Compléter le profil de facturation')).not.toBeInTheDocument();
    });
  });

  it('ne relit pas l\'état tant que les Paramètres restent ouverts', async () => {
    vi.mocked(fetchSetupStatus).mockResolvedValue(etat(false));
    render(<ConversationCanvasPrototype />);
    await screen.findByText('Compléter le profil de facturation');
    const lecturesAuMontage = vi.mocked(fetchSetupStatus).mock.calls.length;

    act(() => { usePanelStore.setState({ showSettings: true }); });

    expect(vi.mocked(fetchSetupStatus).mock.calls.length).toBe(lecturesAuMontage);
  });
});
