import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useChatStore } from '../../stores/chatStore';
import { useAccessibilityStore } from '../../stores/accessibilityStore';
import { usePanelStore } from '../../stores/panelStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { runAction } from '../../lib/actionRegistry';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

const voiceHarness = vi.hoisted(() => ({
  onTranscript: null as ((text: string) => void) | null,
  toggleRecording: vi.fn(),
}));

const activityHarness = vi.hoisted(() => ({
  boardRun: { status: 'idle' } as any,
  atelierRun: { status: 'idle' } as any,
  cancelBoard: vi.fn(),
  cancelAtelier: vi.fn().mockResolvedValue(undefined),
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
      cancelProcessing: vi.fn(),
      elapsedSeconds: 0,
      error: null,
    };
  }),
}));

// Revue 0.40 : le bouton de dictée pré-vérifie le consentement Groq - mock
// pour rester hors réseau et garder le comportement « dictée directe ».
vi.mock('../../services/api/voice', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  needsVoiceCloudConsent: vi.fn().mockResolvedValue(false),
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
    run: activityHarness.boardRun,
    refresh: vi.fn(),
    openDecision: vi.fn(),
    retryDecision: vi.fn(),
    startDeliberation: vi.fn(),
    cancelDeliberation: activityHarness.cancelBoard,
    resetRun: vi.fn(),
  }),
}));

vi.mock('./usePrototypeAtelierData', () => ({
  usePrototypeAtelierData: () => ({
    resource: { status: 'loading', data: null, error: null },
    taskResource: { status: 'loading', data: null, error: null },
    diffResource: { status: 'loading', data: null, error: null },
    run: activityHarness.atelierRun,
    actionPending: null,
    refresh: vi.fn(),
    openTask: vi.fn(),
    retryTask: vi.fn(),
    startMission: vi.fn(),
    cancelMission: activityHarness.cancelAtelier,
    mutateTask: vi.fn(),
    resetRun: vi.fn(),
  }),
}));

describe('ConversationCanvasPrototype - recette UI 16/07', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    voiceHarness.onTranscript = null;
    activityHarness.boardRun = { status: 'idle' };
    activityHarness.atelierRun = { status: 'idle' };
    window.history.replaceState({}, '', '/?interface=conversation-canvas');
    useChatStore.setState({
      conversations: [],
      currentConversationId: null,
      isStreaming: false,
    });
    useAccessibilityStore.setState({ theme: 'light', highContrast: false });
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
    useNavigationStore.setState({ activeView: 'chat' });
  });

  it('ajoute la dictée classique au composeur de la coque', async () => {
    render(<ConversationCanvasPrototype />);

    const composer = screen.getByPlaceholderText('Demande à Thérèse d’organiser, créer ou agir…');
    fireEvent.change(composer, { target: { value: 'Prépare le rendez-vous' } });
    fireEvent.click(screen.getByTestId('prototype-chat-voice-btn'));

    await waitFor(() => expect(voiceHarness.toggleRecording).toHaveBeenCalledTimes(1));
    expect(voiceHarness.onTranscript).not.toBeNull();

    act(() => voiceHarness.onTranscript?.('avec Camille demain'));

    expect(composer).toHaveValue('Prépare le rendez-vous avec Camille demain');
    expect(composer).toHaveFocus();
  });

  it('le + du rail crée directement une conversation sans rouvrir un tiroir (fin du double +), et un seul bouton mène aux conversations', () => {
    render(<ConversationCanvasPrototype />);
    const navigation = within(screen.getByRole('navigation', { name: 'Navigation principale' }));

    // Décision Ludo 16/07 : le + du rail ouvre directement le chat vierge, sans
    // passer par le tiroir qui a lui-même un « Nouvelle conversation » (double +).
    fireEvent.click(navigation.getByRole('button', { name: 'Nouvelle conversation' }));
    expect(screen.getByTestId('prototype-chat-surface')).toBeInTheDocument();
    expect(screen.queryByTestId('prototype-conversation-drawer')).not.toBeInTheDocument();

    // Entrée 4 (28/08) : les deux boutons « Rechercher » et « Historique »
    // ouvraient le MÊME tiroir, où la surface ne changeait que le focus
    // initial. Un seul subsiste. « Rechercher » reste dans l'en-tête, où il
    // désigne la palette — celle-là indexe tout, contrairement à la loupe du
    // rail qui ne filtrait que des titres de conversation.
    fireEvent.click(navigation.getByRole('button', { name: 'Conversations' }));
    expect(screen.getByLabelText('Rechercher une conversation')).toHaveFocus();
    expect(screen.queryByRole('dialog', { name: 'Rechercher dans Thérèse' })).not.toBeInTheDocument();
    expect(navigation.queryByRole('button', { name: 'Historique' })).toBeNull();
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

  it('ne laisse pas de languette de réouverction après fermeture d’un canevas (retirée, recette Ludo)', () => {
    window.history.replaceState({}, '', '/?interface=conversation-canvas&scenario=memory');
    render(<ConversationCanvasPrototype />);

    // Décision Ludo 16/07 : la languette à chevron intriguait plus qu'elle
    // n'aidait, elle est retirée. Fermer un canevas revient simplement au fil.
    fireEvent.click(screen.getByRole('button', { name: 'Fermer le canevas' }));
    expect(screen.queryByTestId('reopen-right-panel-tab')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Rouvrir le panneau/ })).not.toBeInTheDocument();
  });

  it('n’a plus d’icône calendrier isolée dans l’en-tête (retirée, recette Ludo)', () => {
    render(<ConversationCanvasPrototype />);

    // Décision Ludo 16/07 : l'ancien bouton cloche recyclé en raccourci agenda
    // faisait doublon avec la capacité Agenda ; il est retiré de l'en-tête.
    const header = screen.getByRole('banner');
    expect(within(header).queryByRole('button', { name: 'Agenda' })).not.toBeInTheDocument();
  });

  it('garde le nom d’espace comme étiquette passive sans ouvrir les réglages', () => {
    render(<ConversationCanvasPrototype />);

    const workspaceLabel = screen.getByTestId('workspace-label');
    expect(workspaceLabel.tagName).toBe('DIV');
    fireEvent.click(workspaceLabel);
    expect(usePanelStore.getState().showSettings).toBe(false);
  });

  it('masque les travaux engagés sans les annuler et permet de les rouvrir depuis la coque', () => {
    activityHarness.boardRun = { status: 'running', phase: 'Synthèse', question: 'Décider', advisors: {} };
    activityHarness.atelierRun = { status: 'running', phase: 'Tests', instruction: 'Modifier', agents: {}, events: [], tests: [] };
    window.history.replaceState({}, '', '/?interface=conversation-canvas&scenario=atelier');
    render(<ConversationCanvasPrototype />);

    fireEvent.click(screen.getByRole('button', { name: 'Fermer le canevas' }));
    expect(activityHarness.cancelAtelier).not.toHaveBeenCalled();
    expect(activityHarness.cancelBoard).not.toHaveBeenCalled();
    expect(screen.getByTestId('shell-background-activities')).toHaveTextContent('Atelier en arrière-plan · Tests');
    expect(screen.getByTestId('shell-background-activities')).toHaveTextContent('Board en arrière-plan · Synthèse');

    fireEvent.click(screen.getByRole('button', { name: /Board en arrière-plan/ }));
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(activityHarness.cancelBoard).not.toHaveBeenCalled();
    expect(screen.getByTestId('shell-background-activities')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Retrouver' }));
    expect(activityHarness.cancelAtelier).not.toHaveBeenCalled();
    expect(activityHarness.cancelBoard).not.toHaveBeenCalled();
  });

  // BUG-157 / BUG-159 (27/07/2026) - L'engrenage affiché à la place des
  // initiales était l'icône de secours du bouton Profil : le testeur l'a pris
  // pour un accès aux Paramètres, qui n'existait nulle part en permanence.
  describe('accès aux Paramètres et état du profil', () => {
    it('propose un bouton Paramètres permanent qui ouvre les Paramètres', () => {
      render(<ConversationCanvasPrototype />);

      const navigation = screen.getByLabelText('Navigation principale');
      const bouton = within(navigation).getByRole('button', { name: 'Paramètres' });
      fireEvent.click(bouton);

      expect(usePanelStore.getState().showSettings).toBe(true);
    });

    it('n’utilise jamais l’icône des Paramètres comme repli du bouton Profil', () => {
      render(<ConversationCanvasPrototype />);

      const navigation = screen.getByLabelText('Navigation principale');
      const profil = within(navigation).getByTestId('shell-profile-button');
      const parametres = within(navigation).getByRole('button', { name: 'Paramètres' });

      expect(profil).not.toBe(parametres);
      expect(profil.innerHTML).not.toBe(parametres.innerHTML);
    });

    it('annonce le chargement du profil au lieu de faire croire à un profil vide', () => {
      // getProfile est mocké par une promesse jamais résolue : état de chargement.
      render(<ConversationCanvasPrototype />);

      const profil = screen.getByTestId('shell-profile-button');
      expect(profil).toHaveAttribute('aria-label', 'Chargement du profil…');
      expect(profil).toBeDisabled();
    });

    it('affiche les initiales une fois le profil chargé', async () => {
      const { getProfile } = await import('../../services/api/config');
      vi.mocked(getProfile).mockResolvedValueOnce({ nickname: 'Ludo', display_name: 'Ludovic' } as never);

      render(<ConversationCanvasPrototype />);

      await waitFor(() => {
        expect(screen.getByTestId('shell-profile-button')).toHaveTextContent('LU');
      });
      expect(screen.getByTestId('shell-profile-button')).toHaveAttribute('aria-label', 'Ouvrir le profil');
    });

    it('signale un profil indisponible au lieu de rester muet', async () => {
      const { getProfile } = await import('../../services/api/config');
      vi.mocked(getProfile).mockRejectedValueOnce(new Error('backend injoignable'));

      render(<ConversationCanvasPrototype />);

      await waitFor(() => {
        expect(screen.getByTestId('shell-profile-button')).toHaveAttribute(
          'aria-label',
          'Profil indisponible - ouvrir le profil',
        );
      });
    });

    // Revue Soso 27/07 (F6) : le profil n'était chargé qu'au montage. Modifier
    // son nom dans les Paramètres laissait les initiales et la salutation de la
    // coque sur l'ancienne valeur jusqu'au redémarrage.
    it('recharge le profil quand il vient d’être enregistré', async () => {
      const { getProfile } = await import('../../services/api/config');
      vi.mocked(getProfile)
        .mockResolvedValueOnce({ nickname: 'Ludo', display_name: 'Ludovic' } as never)
        .mockResolvedValueOnce({ nickname: 'Perrine', display_name: 'Perrine' } as never);

      render(<ConversationCanvasPrototype />);
      await waitFor(() => expect(screen.getByTestId('shell-profile-button')).toHaveTextContent('LU'));

      await act(async () => {
        window.dispatchEvent(new CustomEvent('therese:profile-updated'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('shell-profile-button')).toHaveTextContent('PE');
      });
    });

    // Contre-vérification N4 : deux chargements qui se chevauchent. La réponse
    // la plus ancienne, arrivée en dernier, ne doit pas réafficher l'ancien nom.
    it('une réponse tardive n’écrase pas un profil plus récent', async () => {
      const { getProfile } = await import('../../services/api/config');
      let resoudreLent: ((v: unknown) => void) | null = null;
      vi.mocked(getProfile)
        .mockImplementationOnce(
          () => new Promise((r) => { resoudreLent = r as unknown as (v: unknown) => void; }) as never,
        )
        .mockResolvedValueOnce({ nickname: 'Perrine', display_name: 'Perrine' } as never);

      render(<ConversationCanvasPrototype />);

      await act(async () => {
        window.dispatchEvent(new CustomEvent('therese:profile-updated'));
      });
      await waitFor(() => expect(screen.getByTestId('shell-profile-button')).toHaveTextContent('PE'));

      await act(async () => {
        resoudreLent?.({ nickname: 'Ludo', display_name: 'Ludovic' });
        await Promise.resolve();
      });

      expect(screen.getByTestId('shell-profile-button')).toHaveTextContent('PE');
    });
  });

  // J0a (30/07/2026) - Navigation canonique.
  // La coque pilotait ses vues par un état local sans observer
  // `navigationStore`, alors que `HomeView` y est montée et que ses composants
  // (actions rapides, conversations récentes, panneaux du jour) naviguent tous
  // par ce store, comme le registre d'actions commun. Résultat en 0.41.3 :
  // ces clics changeaient un état que personne n'affichait.
  describe('navigation canonique', () => {
    it('ouvre la vue demandée par le registre d’actions', async () => {
      render(<ConversationCanvasPrototype />);

      await act(async () => {
        runAction('invoices.open');
      });

      await waitFor(() => {
        expect(screen.getByTestId('conversation-canvas-prototype')).toHaveAttribute('data-embedded-view', 'invoices');
      });
    });

    it('suit une navigation posée directement dans le store', async () => {
      render(<ConversationCanvasPrototype />);

      await act(async () => {
        useNavigationStore.getState().setView('crm');
      });

      await waitFor(() => {
        expect(screen.getByTestId('conversation-canvas-prototype')).toHaveAttribute('data-embedded-view', 'crm');
      });
    });

    it('reflète dans le store une vue ouverte depuis la coque', async () => {
      render(<ConversationCanvasPrototype />);

      await act(async () => {
        screen.getByLabelText('Projets').click();
      });

      await waitFor(() => {
        expect(useNavigationStore.getState().activeView).toBe('projects');
      });
    });
  });
});
