/**
 * B-1401 (persona Zoé, cycle 13) : « Travaux » restait ouvert sous le Centre
 * de confiance ; les deux fenêtres d'en-tête se recouvraient au même coin
 * (titre coupé « Tr », frise qui dépasse). Ouvrir le Centre ferme « Travaux » ;
 * l'inverse ne se produit pas : le Centre rend le fond inerte, « Travaux »
 * n'est pas cliquable pendant qu'il est ouvert.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { fetchSetupStatus } from '../../services/api/dashboard';
import { useProcessingTasksStore } from '../../stores/processingTasksStore';
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

describe('Travaux et Centre de confiance s’excluent (B-1401)', () => {
  it('ouvrir le Centre ferme Travaux', async () => {
    vi.mocked(fetchSetupStatus).mockResolvedValue(etat(true));
    useProcessingTasksStore.setState({ panneauOuvert: false });
    render(<ConversationCanvasPrototype />);
    fireEvent.click(screen.getByRole('button', { name: /^Travaux/ }));
    await screen.findByRole('dialog', { name: 'Travaux en cours' });

    fireEvent.click(screen.getByRole('button', { name: 'Contrôle des données' }));
    await screen.findByRole('dialog', { name: 'Centre de confiance' });
    // Le Centre rend le fond inerte : on lit la présence réelle, pas l'arbre d'accessibilité.
    await waitFor(() => expect(document.getElementById('traitements-panneau')).toBeNull());
    expect(useProcessingTasksStore.getState().panneauOuvert).toBe(false);
  });

});
