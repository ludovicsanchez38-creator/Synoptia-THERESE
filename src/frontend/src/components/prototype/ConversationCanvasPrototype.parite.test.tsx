/**
 * J0b (30/07/2026) - Gate de parité PAR SOURCE D'ACTION.
 *
 * Condition posée au plan 0.42 avant de supprimer l'interface classique : il ne
 * suffit pas que chaque vue existe dans la coque, il faut que chaque *source*
 * qui demande une navigation aboutisse à un changement visible.
 *
 * C'est la leçon de J0a : la parité par composant était vérifiée (17 des 21
 * composants du classic existaient dans la coque), et pourtant l'accueil était
 * inerte parce que la source de navigation n'était pas observée.
 *
 * Ce fichier verrouille le contrat. Toute action de navigation ajoutée au
 * registre sans être servie par la coque fera échouer la suite.
 */
import { act, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { APP_ACTIONS, runAction } from '../../lib/actionRegistry';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

const voiceHarness = vi.hoisted(() => ({ toggleRecording: vi.fn() }));
const activityHarness = vi.hoisted(() => ({
  boardRun: { status: 'idle' } as any,
  atelierRun: { status: 'idle' } as any,
}));

vi.mock('../../hooks/useVoiceRecorder', () => ({
  useVoiceRecorder: () => ({
    state: 'idle', isRecording: false, isProcessing: false, pluginReady: true,
    startRecording: vi.fn(), stopRecording: vi.fn(), toggleRecording: voiceHarness.toggleRecording,
    cancelProcessing: vi.fn(), elapsedSeconds: 0, error: null,
  }),
}));
vi.mock('../../services/api/voice', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  needsVoiceCloudConsent: vi.fn().mockResolvedValue(false),
}));
vi.mock('../../hooks/useConversationSync', () => ({ useConversationSync: vi.fn() }));
vi.mock('../../services/api/config', async (importOriginal) => {
  const original = await importOriginal<typeof import('../../services/api/config')>();
  return { ...original, getProfile: vi.fn(() => new Promise(() => {})) };
});
vi.mock('../../services/api/commands', () => ({ listUserCommands: vi.fn(() => new Promise(() => {})) }));
vi.mock('./usePrototypeReadData', () => ({
  useTodayDashboardResource: () => ({ resource: { status: 'loading', data: null, error: null }, refresh: vi.fn() }),
  useContactsResource: () => ({ resource: { status: 'loading', data: null, error: null }, refresh: vi.fn() }),
}));
vi.mock('./usePrototypeEmailData', () => ({
  usePrototypeEmailData: () => ({
    inboxResource: { status: 'loading', data: null, error: null },
    messageResource: { status: 'loading', data: null, error: null },
    refreshInbox: vi.fn(), openMessage: vi.fn(), retryMessage: vi.fn(),
    generateDraft: vi.fn(), saveDraft: vi.fn(),
  }),
}));
vi.mock('./usePrototypeMeetingData', () => ({
  meetingEventKey: vi.fn(() => 'event'),
  usePrototypeMeetingData: () => ({
    resource: { status: 'loading', data: null, error: null },
    eventResource: { status: 'loading', data: null, error: null },
    refresh: vi.fn(), openEvent: vi.fn(), retryEvent: vi.fn(),
    createCalendarEvent: vi.fn(), createMeetingNote: vi.fn(),
  }),
}));
vi.mock('./usePrototypeInvoiceData', () => ({
  usePrototypeInvoiceData: () => ({
    resource: { status: 'loading', data: null, error: null },
    invoiceResource: { status: 'loading', data: null, error: null },
    refresh: vi.fn(), openInvoice: vi.fn(), retryInvoice: vi.fn(),
    createDevisDraft: vi.fn(), createInvoiceContact: vi.fn(),
  }),
}));
vi.mock('./usePrototypeBoardData', () => ({
  usePrototypeBoardData: () => ({
    resource: { status: 'loading', data: null, error: null },
    decisionResource: { status: 'loading', data: null, error: null },
    run: activityHarness.boardRun, refresh: vi.fn(), openDecision: vi.fn(),
    retryDecision: vi.fn(), startDeliberation: vi.fn(), cancelDeliberation: vi.fn(), resetRun: vi.fn(),
  }),
}));
vi.mock('./usePrototypeAtelierData', () => ({
  usePrototypeAtelierData: () => ({
    resource: { status: 'loading', data: null, error: null },
    taskResource: { status: 'loading', data: null, error: null },
    diffResource: { status: 'loading', data: null, error: null },
    run: activityHarness.atelierRun, actionPending: null, refresh: vi.fn(),
    openTask: vi.fn(), retryTask: vi.fn(), startMission: vi.fn(),
    cancelMission: vi.fn(), mutateTask: vi.fn(), resetRun: vi.fn(),
  }),
}));

/** Les actions du registre qui demandent une VUE (les autres ouvrent des panneaux). */
const ACTIONS_DE_VUE = APP_ACTIONS
  .filter((a) => a.group === 'Navigation' && a.id.endsWith('.open'))
  .map((a) => a.id)
  // `board.open` est dans le groupe Navigation mais ouvre un panneau, pas une vue.
  .filter((id) => id !== 'board.open');

describe('Gate de parité par source d’action', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.history.replaceState({}, '', '/?interface=conversation-canvas');
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
    useNavigationStore.setState({ activeView: 'chat' });
  });

  it('couvre toutes les actions de navigation du registre', () => {
    // Garde-fou du gate lui-même : si le registre gagne une entrée, ce test
    // rappelle qu'elle doit être servie par la coque.
    expect(ACTIONS_DE_VUE.length).toBeGreaterThanOrEqual(9);
  });

  it.each(ACTIONS_DE_VUE)('%s ouvre une vue visible dans la coque', async (actionId) => {
    render(<ConversationCanvasPrototype />);

    await act(async () => {
      runAction(actionId);
    });

    const vueAttendue = actionId.replace('.open', '');
    await waitFor(() => {
      expect(screen.getByTestId('conversation-canvas-prototype')).toHaveAttribute(
        'data-embedded-view',
        vueAttendue,
      );
    });
  });

  // J0b : ce que seule l'ancienne coque portait et qui ne doit pas disparaître
  // avec elle (relevé par le challenge du plan).
  describe('reprises de l’ancienne coque', () => {
    it('expose le pont de recette window.__therese', async () => {
      render(<ConversationCanvasPrototype />);

      await waitFor(() => {
        const pont = (window as unknown as { __therese?: { runAction?: unknown; stores?: unknown } }).__therese;
        expect(pont).toBeDefined();
        expect(typeof pont?.runAction).toBe('function');
        expect(pont?.stores).toBeDefined();
      });
    });

    it('ouvre la vue demandée par un lien profond ?view=', async () => {
      window.history.replaceState({}, '', '/?interface=conversation-canvas&view=crm');

      render(<ConversationCanvasPrototype />);

      await waitFor(() => {
        expect(screen.getByTestId('conversation-canvas-prototype')).toHaveAttribute('data-embedded-view', 'crm');
      });
    });

    it('insère un prompt reçu par événement et bascule sur le chat', async () => {
      // Le test précédent pose ?view=crm : sans remise à zéro, le lien profond
      // de CE rendu ouvrirait CRM. Isolation explicite.
      window.history.replaceState({}, '', '/?interface=conversation-canvas');

      render(<ConversationCanvasPrototype />);

      await act(async () => {
        window.dispatchEvent(new CustomEvent('therese:insert-prompt', { detail: 'Prépare la relance' }));
      });

      await waitFor(() => {
        expect(screen.getByTestId('conversation-canvas-prototype')).toHaveAttribute('data-embedded-view', 'chat');
      });
    });
  });
});
