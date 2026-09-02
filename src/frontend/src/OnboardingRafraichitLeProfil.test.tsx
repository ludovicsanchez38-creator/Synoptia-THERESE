/**
 * B-214 — juste après l'assistant, l'accueil salue « Bonjour. » sans prénom.
 *
 * Constat du 02/09/2026 : le canevas lit le profil une fois au montage puis se
 * réabonne au seul évènement `therese:profile-updated`
 * (ConversationCanvasPrototype.tsx:874-897). Il est monté en permanence, à
 * côté de l'assistant et non à sa place : il ne se remonte donc pas quand
 * l'assistant se ferme. Or `handleOnboardingComplete` n'émettait rien, et
 * l'évènement n'était émis que par les Paramètres. Le premier écran qui suit la
 * configuration affichait donc le profil d'AVANT — c'est-à-dire aucun — jusqu'au
 * prochain rechargement de la fenêtre.
 *
 * Le mécanisme de rattrapage existait déjà (écouteur du 27/07, finding F6) ;
 * seul l'assistant ne s'en servait pas.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from './stores/chatStore';
import { useAccessibilityStore } from './stores/accessibilityStore';
import { useNavigationStore } from './stores/navigationStore';

// L'assistant réel n'est pas le sujet : on ne veut prouver que ce que sa
// fermeture déclenche. Le bouton du double joue « Commencer ».
vi.mock('./components/onboarding', () => ({
  OnboardingWizard: ({ isOpen, onComplete }: { isOpen: boolean; onComplete: () => void }) =>
    isOpen ? (
      <button type="button" onClick={onComplete}>
        Terminer la configuration
      </button>
    ) : null,
}));

vi.mock('./hooks/useHealthCheck', () => ({ useHealthCheck: vi.fn() }));
vi.mock('./lib/capacites/generation', () => ({
  controlerGenerationAuDemarrage: vi.fn().mockResolvedValue(undefined),
}));

vi.mock('./services/api', async (importOriginal) => {
  const original = await importOriginal<typeof import('./services/api')>();
  return {
    ...original,
    initializeAuth: vi.fn().mockResolvedValue(undefined),
    getOnboardingStatus: vi.fn().mockResolvedValue({ completed: false }),
  };
});

// Le profil lu par le canevas : une valeur mutable plutôt qu'une file de
// réponses, l'ordre des appels du canevas (jeton anti-chevauchement) n'étant
// pas le sujet de ce test.
const profil = vi.hoisted(() => ({ courant: null as unknown }));
vi.mock('./services/api/config', async (importOriginal) => {
  const original = await importOriginal<typeof import('./services/api/config')>();
  return { ...original, getProfile: vi.fn(() => Promise.resolve(profil.courant)) };
});

vi.mock('./services/api/commands', () => ({ listUserCommands: vi.fn(() => new Promise(() => {})) }));
vi.mock('./hooks/useConversationSync', () => ({ useConversationSync: vi.fn() }));
vi.mock('./services/api/voice', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  needsVoiceCloudConsent: vi.fn().mockResolvedValue(false),
}));
vi.mock('./hooks/useVoiceRecorder', () => ({
  useVoiceRecorder: vi.fn(() => ({
    state: 'idle', isRecording: false, isProcessing: false, pluginReady: true,
    startRecording: vi.fn(), stopRecording: vi.fn(), toggleRecording: vi.fn(),
    cancelProcessing: vi.fn(), elapsedSeconds: 0, error: null,
  })),
}));

const ressourceInerte = { resource: { status: 'loading', data: null, error: null }, refresh: vi.fn() };
vi.mock('./components/prototype/usePrototypeReadData', () => ({
  useTodayDashboardResource: () => ressourceInerte,
  useContactsResource: () => ressourceInerte,
}));
vi.mock('./components/prototype/usePrototypeEmailData', () => ({
  usePrototypeEmailData: () => ({
    inboxResource: { status: 'loading', data: null, error: null },
    messageResource: { status: 'loading', data: null, error: null },
    refreshInbox: vi.fn(), openMessage: vi.fn(), retryMessage: vi.fn(),
    generateDraft: vi.fn(), saveDraft: vi.fn(),
  }),
}));
vi.mock('./components/prototype/usePrototypeMeetingData', () => ({
  meetingEventKey: vi.fn(() => 'event'),
  usePrototypeMeetingData: () => ({
    resource: { status: 'loading', data: null, error: null },
    eventResource: { status: 'loading', data: null, error: null },
    refresh: vi.fn(), openEvent: vi.fn(), retryEvent: vi.fn(),
    createCalendarEvent: vi.fn(), createMeetingNote: vi.fn(),
  }),
}));
vi.mock('./components/prototype/usePrototypeInvoiceData', () => ({
  usePrototypeInvoiceData: () => ({
    resource: { status: 'loading', data: null, error: null },
    invoiceResource: { status: 'loading', data: null, error: null },
    refresh: vi.fn(), openInvoice: vi.fn(), retryInvoice: vi.fn(),
    createDevisDraft: vi.fn(), createInvoiceContact: vi.fn(),
  }),
}));
vi.mock('./components/prototype/usePrototypeBoardData', () => ({
  usePrototypeBoardData: () => ({
    resource: { status: 'loading', data: null, error: null },
    decisionResource: { status: 'loading', data: null, error: null },
    run: { status: 'idle' }, refresh: vi.fn(), openDecision: vi.fn(), retryDecision: vi.fn(),
    startDeliberation: vi.fn(), cancelDeliberation: vi.fn(), resetRun: vi.fn(),
  }),
}));
vi.mock('./components/prototype/usePrototypeAtelierData', () => ({
  usePrototypeAtelierData: () => ({
    resource: { status: 'loading', data: null, error: null },
    taskResource: { status: 'loading', data: null, error: null },
    diffResource: { status: 'loading', data: null, error: null },
    run: { status: 'idle' }, actionPending: null, refresh: vi.fn(), openTask: vi.fn(),
    retryTask: vi.fn(), startMission: vi.fn(), cancelMission: vi.fn().mockResolvedValue(undefined),
    mutateTask: vi.fn(), resetRun: vi.fn(),
  }),
}));

import App from './App';

describe('B-214 — la fin de l’assistant rafraîchit le profil', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    profil.courant = null;
    window.history.replaceState({}, '', '/?interface=conversation-canvas');
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
    useAccessibilityStore.setState({ theme: 'light', highContrast: false });
    useNavigationStore.setState({ activeView: 'chat' });
  });

  it('salue par le prénom saisi, sans attendre un rechargement', async () => {
    const { getProfile } = await import('./services/api/config');

    render(<App />);

    // Écran d'accueil monté derrière l'assistant, profil encore vide. Le
    // canevas arrive par `lazy` : on attend sa coque avant de lire le titre,
    // sinon l'absence de h1 signifierait « pas encore chargé » et non « pas de
    // prénom ».
    await screen.findByTestId('conversation-canvas-prototype', {}, { timeout: 5000 });
    await waitFor(() => expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Bonjour.'));
    expect(vi.mocked(getProfile)).toHaveBeenCalledTimes(1);

    // L'étape 2 de l'assistant vient d'enregistrer le prénom côté serveur.
    profil.courant = { display_name: 'Marc Dupont', nickname: '' };

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Terminer la configuration' }));
    });

    await waitFor(() => expect(vi.mocked(getProfile)).toHaveBeenCalledTimes(2));
    await waitFor(() =>
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Bonjour Marc.'),
    );
  });
});
