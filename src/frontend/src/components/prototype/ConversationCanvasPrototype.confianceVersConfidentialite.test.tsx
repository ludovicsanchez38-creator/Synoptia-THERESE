/**
 * B-1359 et B-1360 (persona Claire, cycle 13) : « Confidentialité », dans le
 * Centre de confiance, ouvrait Paramètres SOUS le Centre, qui en masquait la
 * moitié du texte ; Échap fermait ensuite Paramètres (la couche lue) et
 * laissait le Centre. Une seule cause : le Centre restait ouvert. Il se ferme
 * quand il passe la main aux Paramètres.
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
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

describe('Centre de confiance vers Confidentialité (B-1359, B-1360)', () => {
  it('le Centre se ferme quand il ouvre la Confidentialité', async () => {
    vi.mocked(fetchSetupStatus).mockResolvedValue(etat(true));
    render(<ConversationCanvasPrototype />);
    fireEvent.click(screen.getByRole('button', { name: 'Contrôle des données' }));
    const centre = await screen.findByRole('dialog', { name: 'Centre de confiance' });

    fireEvent.click(within(centre).getByRole('button', { name: 'Confidentialité' }));

    expect(usePanelStore.getState().showSettings).toBe(true);
    expect(usePanelStore.getState().requestedSettingsTab).toBe('privacy');
    await waitFor(() => {
      expect(screen.queryByRole('dialog', { name: 'Centre de confiance' })).not.toBeInTheDocument();
    });
  });

  it('fermer ensuite les Paramètres rend le focus au bouton du Centre', async () => {
    vi.mocked(fetchSetupStatus).mockResolvedValue(etat(true));
    render(<ConversationCanvasPrototype />);
    // Comme dans Chrome, un clic focalise le bouton (jsdom ne le fait pas seul).
    const declencheur = screen.getByRole('button', { name: 'Contrôle des données' });
    declencheur.focus();
    fireEvent.click(declencheur);
    const centre = await screen.findByRole('dialog', { name: 'Centre de confiance' });
    const confidentialite = within(centre).getByRole('button', { name: 'Confidentialité' });
    confidentialite.focus();
    fireEvent.click(confidentialite);
    await waitFor(() => {
      expect(screen.queryByRole('dialog', { name: 'Centre de confiance' })).not.toBeInTheDocument();
    });

    usePanelStore.getState().closeSettings();

    await waitFor(() => expect(declencheur).toHaveFocus());
  });
});
