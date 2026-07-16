import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useChatStore } from '../../stores/chatStore';
import { useAccessibilityStore } from '../../stores/accessibilityStore';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

const voiceHarness = vi.hoisted(() => ({
  onTranscript: null as ((text: string) => void) | null,
  toggleRecording: vi.fn(),
}));

vi.mock('../../hooks/useVoiceRecorder', () => ({
  useVoiceRecorder: vi.fn((options: { onTranscript?: (text: string) => void }) => {
    voiceHarness.onTranscript = options.onTranscript ?? null;
    return {
      state: 'idle',
      isRecording: false,
      isProcessing: false,
      pluginReady: true,
      startRecording: vi.fn(),
      stopRecording: vi.fn(),
      toggleRecording: voiceHarness.toggleRecording,
      error: null,
    };
  }),
}));

vi.mock('../../hooks/useConversationSync', () => ({
  useConversationSync: vi.fn(),
}));

vi.mock('../../services/api/config', async (importOriginal) => {
  const original = await importOriginal<typeof import('../../services/api/config')>();
  return { ...original, getProfile: vi.fn(() => new Promise(() => {})) };
});

vi.mock('../../services/api/commands', () => ({
  listUserCommands: vi.fn(() => new Promise(() => {})),
}));

vi.mock('./usePrototypeReadData', () => ({
  useTodayDashboardResource: () => ({
    resource: { status: 'loading', data: null, error: null },
    refresh: vi.fn(),
  }),
  useContactsResource: () => ({
    resource: { status: 'loading', data: null, error: null },
    refresh: vi.fn(),
  }),
}));

vi.mock('./usePrototypeEmailData', () => ({
  usePrototypeEmailData: () => ({
    inboxResource: { status: 'loading', data: null, error: null },
    messageResource: { status: 'loading', data: null, error: null },
    refreshInbox: vi.fn(),
    openMessage: vi.fn(),
    retryMessage: vi.fn(),
    generateDraft: vi.fn(),
    saveDraft: vi.fn(),
  }),
}));

vi.mock('./usePrototypeMeetingData', () => ({
  meetingEventKey: vi.fn(() => 'event'),
  usePrototypeMeetingData: () => ({
    resource: { status: 'loading', data: null, error: null },
    eventResource: { status: 'loading', data: null, error: null },
    refresh: vi.fn(),
    openEvent: vi.fn(),
    retryEvent: vi.fn(),
    createCalendarEvent: vi.fn(),
    createMeetingNote: vi.fn(),
  }),
}));

vi.mock('./usePrototypeInvoiceData', () => ({
  usePrototypeInvoiceData: () => ({
    resource: { status: 'loading', data: null, error: null },
    invoiceResource: { status: 'loading', data: null, error: null },
    refresh: vi.fn(),
    openInvoice: vi.fn(),
    retryInvoice: vi.fn(),
    createDevisDraft: vi.fn(),
    createInvoiceContact: vi.fn(),
  }),
}));

vi.mock('./usePrototypeBoardData', () => ({
  usePrototypeBoardData: () => ({
    resource: { status: 'loading', data: null, error: null },
    decisionResource: { status: 'loading', data: null, error: null },
    run: { status: 'idle' },
    refresh: vi.fn(),
    openDecision: vi.fn(),
    retryDecision: vi.fn(),
    startDeliberation: vi.fn(),
    cancelDeliberation: vi.fn(),
    resetRun: vi.fn(),
  }),
}));

vi.mock('./usePrototypeAtelierData', () => ({
  usePrototypeAtelierData: () => ({
    resource: { status: 'loading', data: null, error: null },
    taskResource: { status: 'loading', data: null, error: null },
    diffResource: { status: 'loading', data: null, error: null },
    run: { status: 'idle' },
    actionPending: null,
    refresh: vi.fn(),
    openTask: vi.fn(),
    retryTask: vi.fn(),
    startMission: vi.fn(),
    cancelMission: vi.fn(),
    mutateTask: vi.fn(),
    resetRun: vi.fn(),
  }),
}));

describe('ConversationCanvasPrototype - recette UI 16/07', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    voiceHarness.onTranscript = null;
    window.history.replaceState({}, '', '/?interface=conversation-canvas');
    useChatStore.setState({
      conversations: [],
      currentConversationId: null,
      isStreaming: false,
    });
    useAccessibilityStore.setState({ theme: 'light', highContrast: false });
  });

  it('ajoute la dictée classique au composeur de la coque', () => {
    render(<ConversationCanvasPrototype />);

    const composer = screen.getByPlaceholderText('Demande à Thérèse d’organiser, créer ou agir…');
    fireEvent.change(composer, { target: { value: 'Prépare le rendez-vous' } });
    fireEvent.click(screen.getByTestId('prototype-chat-voice-btn'));

    expect(voiceHarness.toggleRecording).toHaveBeenCalledTimes(1);
    expect(voiceHarness.onTranscript).not.toBeNull();

    act(() => voiceHarness.onTranscript?.('avec Camille demain'));

    expect(composer).toHaveValue('Prépare le rendez-vous avec Camille demain');
    expect(composer).toHaveFocus();
  });

  it('route nouvelle conversation, recherche et historique vers le même tiroir', () => {
    render(<ConversationCanvasPrototype />);
    const navigation = within(screen.getByRole('navigation', { name: 'Navigation principale' }));

    fireEvent.click(navigation.getByRole('button', { name: 'Nouvelle conversation' }));
    const drawer = screen.getByTestId('prototype-conversation-drawer');
    expect(drawer).toBeInTheDocument();
    expect(within(drawer).getByRole('button', { name: 'Nouvelle conversation' })).toHaveFocus();

    fireEvent.click(navigation.getByRole('button', { name: 'Rechercher' }));
    expect(screen.getByLabelText('Rechercher une conversation')).toHaveFocus();
    expect(screen.queryByRole('dialog', { name: 'Rechercher dans Thérèse' })).not.toBeInTheDocument();

    fireEvent.click(navigation.getByRole('button', { name: 'Historique' }));
    expect(screen.getByLabelText('Historique des conversations')).toHaveFocus();
  });

  it('propage le thème et le contraste sur la racine de la coque et garde le fond du composeur tokenisé', () => {
    useAccessibilityStore.setState({ theme: 'dark', highContrast: true });
    render(<ConversationCanvasPrototype />);

    const shell = screen.getByTestId('conversation-canvas-prototype');
    expect(shell).toHaveAttribute('data-theme', 'dark');
    expect(shell).toHaveAttribute('data-high-contrast', 'true');
    expect(screen.getByTestId('prototype-composer-backdrop').className).toContain('var(--color-bg)');

    act(() => useAccessibilityStore.setState({ theme: 'light', highContrast: false }));
    expect(shell).toHaveAttribute('data-theme', 'light');
    expect(shell).not.toHaveAttribute('data-high-contrast');
  });
});
