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
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';
import { useStatusStore } from '../../stores/statusStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { APP_ACTIONS, runAction } from '../../lib/actionRegistry';
import { runNavigationAction } from '../../lib/clientActions';
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

/**
 * Toutes les actions du registre qui demandent une VUE, quel que soit leur
 * groupe. La sélection précédente ne retenait que `group === 'Navigation'` et
 * ratait donc `memory.open` et `memory.search` (groupe Mémoire) : le gate
 * prétendait couvrir la parité sans les voir (finding 6 de la revue).
 *
 * Les vues connues font foi, pas une convention de nommage : une action
 * ajoutée hors convention sera signalée par le test de complétude.
 */
const VUES_CONNUES = [
  'home', 'memory', 'crm', 'email', 'calendar', 'tasks', 'invoices', 'files', 'projects', 'documents',
] as const;

const ACTIONS_DE_VUE = APP_ACTIONS
  .filter((a) => {
    const cible = a.id.replace(/\.(open|search)$/, '');
    return (a.id.endsWith('.open') || a.id.endsWith('.search'))
      && (VUES_CONNUES as readonly string[]).includes(cible);
  })
  .map((a) => a.id);

describe('Gate de parité par source d’action', () => {
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
    // Réinitialisation exhaustive : ces stores sont des singletons de module et
    // survivent d'un fichier de test à l'autre. `skipDashboard` en particulier
    // ferait ouvrir le chat au montage et fausserait tout le gate.
    // La pile Échap est un singleton de module : un handler laissé par un autre
    // fichier de test consommerait la touche avant la pile unifiée.
    _clearEscapeHandlers();
    useNavigationStore.setState({ activeView: 'chat', history: [] });
    usePersonalisationStore.setState({ skipDashboard: false });
  });

  it('couvre toutes les actions d’ouverture du registre', () => {
    // Ce test était TAUTOLOGIQUE (relevé par la revue Soso) : la liste attendue
    // et `ACTIONS_DE_VUE` dérivaient toutes deux de `VUES_CONNUES`. Ajouter une
    // action `reports.open` sans toucher à cette liste la faisait disparaître
    // des DEUX côtés — le gate restait vert alors que la coque ne la servait
    // pas. Exactement le trou que J0a a mis au jour.
    //
    // On part donc du registre ENTIER. Toute action d'ouverture doit être soit
    // couverte par le gate, soit exemptée NOMMÉMENT ci-dessous.
    const PANNEAUX_HORS_GATE = [
      // Ces actions n'ouvrent pas une vue embarquée mais un panneau ou une
      // modale par-dessus. Leur ouverture est vérifiée ailleurs.
      'actions.open',
      'board.open',
      'guided.open',
      'settings.open',
      'shortcuts.open',
      // Trouvée par CE test dès sa réécriture : l'ancienne version, filtrée sur
      // `VUES_CONNUES` des deux côtés, ne la voyait pas du tout.
      'prompt-library.open',
    ];

    const toutesLesOuvertures = APP_ACTIONS
      .filter((a) => a.id.endsWith('.open') || a.id.endsWith('.search'))
      .map((a) => a.id);

    const aCouvrir = toutesLesOuvertures.filter((id) => !PANNEAUX_HORS_GATE.includes(id));

    expect(ACTIONS_DE_VUE.slice().sort()).toEqual(aCouvrir.slice().sort());
  });

  it.each(ACTIONS_DE_VUE)('%s ouvre une vue visible dans la coque', async (actionId) => {
    render(<ConversationCanvasPrototype />);

    await act(async () => {
      runAction(actionId);
    });

    const vueAttendue = actionId.replace(/\.(open|search)$/, '');
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

  // Remédiation du NO-GO Soso sur J0 (31/07) : trois défauts critiques.
    it('la commande déterministe {action: ouvrir ...} aboutit aussi', async () => {
    // Le gate n'éprouvait que `runAction`. Les commandes déterministes du chat
    // passent par un autre chemin : elles doivent aboutir de la même façon.
    render(<ConversationCanvasPrototype />);

    await act(async () => {
      runNavigationAction('crm.open');
    });

    await waitFor(() => {
      expect(screen.getByTestId('conversation-canvas-prototype')).toHaveAttribute('data-embedded-view', 'crm');
    });
  });

  it('le raccourci clavier aboutit aussi', async () => {
    render(<ConversationCanvasPrototype />);

    await act(async () => {
      fireEvent.keyDown(window, { key: 'e', ctrlKey: true, metaKey: true });
    });

    await waitFor(() => {
      expect(screen.getByTestId('conversation-canvas-prototype')).toHaveAttribute('data-embedded-view', 'email');
    });
  });

  describe('navigation réellement unique', () => {
    it('rouvrir une vue après l’avoir fermée fonctionne encore', async () => {
      // Défaut : fermer ne posait que l'état local. Le store restait sur la vue,
      // donc rejouer la même action devenait un no-op (setView ignore l'identique)
      // et la vue ne se rouvrait jamais.
      render(<ConversationCanvasPrototype />);

      await act(async () => { runAction('crm.open'); });
      await waitFor(() => {
        expect(screen.getByTestId('conversation-canvas-prototype')).toHaveAttribute('data-embedded-view', 'crm');
      });

      await act(async () => { screen.getByLabelText('Revenir à la conversation unifiée').click(); });
      await act(async () => { runAction('crm.open'); });

      await waitFor(() => {
        expect(screen.getByTestId('conversation-canvas-prototype')).toHaveAttribute('data-embedded-view', 'crm');
      });
    });

    it('une navigation refusée pendant un flux n’est pas perdue', async () => {
      // Défaut : l'effet avançait sa référence AVANT que la navigation soit
      // refusée pour cause de streaming. La demande disparaissait sans retour.
      useChatStore.setState({ isStreaming: true });
      render(<ConversationCanvasPrototype />);

      await act(async () => { runAction('crm.open'); });
      // Refusée : le flux tourne.
      expect(screen.getByTestId('conversation-canvas-prototype')).not.toHaveAttribute('data-embedded-view', 'crm');

      await act(async () => { useChatStore.setState({ isStreaming: false }); });
      await act(async () => { runAction('crm.open'); });

      await waitFor(() => {
        expect(screen.getByTestId('conversation-canvas-prototype')).toHaveAttribute('data-embedded-view', 'crm');
      });
    });

    it('branche Échap sur la pile unifiée', async () => {
      // Deux versions creuses avant celle-ci. La première cherchait le mot
      // « Escape » dans le fichier source. La seconde vérifiait que
      // `resolveEscape` est bien une fonction et créait un espion jamais
      // utilisé — ce qui ne prouve rien non plus (relevé par Soso).
      //
      // Ce qui compte : la coque doit consommer Échap DANS L'ORDRE de la pile
      // unifiée. Un handler poussé sur la pile partagée est le plus récent :
      // c'est lui qui doit répondre en premier, avant les panneaux de la coque.
      const { pushEscapeHandler } = await import('../../lib/escapeStack');

      const handlerDeLaPile = vi.fn(() => true);
      usePanelStore.setState({ showSettings: true });

      render(<ConversationCanvasPrototype />);
      const retirer = pushEscapeHandler(handlerDeLaPile);

      await act(async () => {
        fireEvent.keyDown(window, { key: 'Escape' });
      });

      expect(handlerDeLaPile).toHaveBeenCalled();
      // Il a consommé la touche : les Réglages ne doivent PAS s'être fermés.
      expect(usePanelStore.getState().showSettings).toBe(true);

      retirer();

      // Une fois la pile vidée, la coque reprend la main sur ses propres
      // panneaux.
      await act(async () => {
        fireEvent.keyDown(window, { key: 'Escape' });
      });
      expect(usePanelStore.getState().showSettings).toBe(false);
    });

    it('n’écoute l’insertion de prompt qu’une seule fois', async () => {
      // Finding 7 du NO-GO Soso : la coque enregistrait DEUX écouteurs de
      // `therese:insert-prompt`. Les deux consultent la garde de streaming, et
      // celle-ci notifie l'utilisateur quand elle refuse — d'où deux bandeaux
      // « Réponse en cours » identiques pour un seul geste.
      useChatStore.setState({ isStreaming: true });
      useStatusStore.setState({ notifications: [] });

      render(<ConversationCanvasPrototype />);

      await act(async () => {
        window.dispatchEvent(
          new CustomEvent('therese:insert-prompt', { detail: 'Prépare la relance' })
        );
      });

      const refus = useStatusStore
        .getState()
        .notifications.filter((n) => n.title === 'Réponse en cours');
      expect(refus).toHaveLength(1);
    });

    it('signale la perte de connexion en dehors du chat', async () => {
      // Finding MINEUR n°10 : `ConnectionStatus` n'était monté que dans la
      // surface de chat (`PrototypeChatSurface`). L'ancien bandeau couvrait
      // toute l'application. Depuis le retrait du classic, un utilisateur qui
      // travaille dans CRM, Fichiers ou Factures ne voit plus rien quand le
      // backend tombe : ses actions échouent sans explication.
      useStatusStore.setState({ connectionState: 'disconnected' });

      render(<ConversationCanvasPrototype />);

      await act(async () => { runAction('crm.open'); });
      await waitFor(() => {
        expect(screen.getByTestId('conversation-canvas-prototype'))
          .toHaveAttribute('data-embedded-view', 'crm');
      });

      expect(screen.getByTestId('etat-connexion-coque')).toBeTruthy();
    });

    it('ne rejoue pas un lien profond à chaque rechargement', async () => {
      // Finding MINEUR n°9 de la revue Soso : les paramètres n'étaient pas
      // retirés après consommation. Un lien `?action=settings.open` rouvrait
      // donc les Réglages à CHAQUE rechargement de la page — impossible de s'en
      // débarrasser sans éditer l'URL à la main.
      window.history.replaceState(
        {}, '', '/?interface=conversation-canvas&view=crm&panel=board&action=settings.open'
      );

      render(<ConversationCanvasPrototype />);

      await waitFor(() => {
        expect(window.location.search).not.toContain('view=');
      });
      expect(window.location.search).not.toContain('panel=');
      expect(window.location.search).not.toContain('action=');
      // Le paramètre qui identifie la coque, lui, doit rester.
      expect(window.location.search).toContain('interface=conversation-canvas');
    });

    it('rouvre le chat quand un résultat arrive après sa fermeture', async () => {
      // Finding MAJEUR n°7 de la revue Soso. Fermer le chat ne touchait que
      // l'état local `chatOpen` ; le store de navigation restait sur `chat`.
      // Un `setView('chat')` ultérieur devenait donc un no-op.
      //
      // Pour l'utilisateur : il lance une Action longue, ferme le chat, et le
      // résultat est ajouté à une conversation qui ne se rouvre pas. Le travail
      // paraît perdu jusqu'à une réouverture manuelle.
      // Le `beforeEach` laisse le store sur `chat` : partir de l'accueil pour
      // que l'ouverture soit un vrai changement de vue.
      useNavigationStore.setState({ activeView: 'home', history: [] });
      render(<ConversationCanvasPrototype />);

      await act(async () => { useNavigationStore.getState().setView('chat'); });
      await waitFor(() => {
        expect(screen.getByTestId('conversation-canvas-prototype'))
          .toHaveAttribute('data-embedded-view', 'chat');
      });

      await act(async () => {
        fireEvent.keyDown(window, { key: 'Escape' });
      });
      await waitFor(() => {
        expect(screen.getByTestId('conversation-canvas-prototype'))
          .not.toHaveAttribute('data-embedded-view', 'chat');
      });

      // Ce que fait `actionsStore` à la fin d'une Action.
      await act(async () => {
        useNavigationStore.getState().setView('chat');
      });

      await waitFor(() => {
        expect(screen.getByTestId('conversation-canvas-prototype'))
          .toHaveAttribute('data-embedded-view', 'chat');
      });
    });
  });
});
