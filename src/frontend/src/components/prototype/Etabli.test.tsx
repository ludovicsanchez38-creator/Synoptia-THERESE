/**
 * B1 (0.48) — un établi, un tiroir.
 *
 * L'accueil propose QUATRE actions (Écrire, Retrouver, Préparer, Facturer),
 * depuis une source unique (lib/etabli.ts) suivie aussi par la palette ⌘K et
 * « Essayer un autre parcours ». Les puces priorités/décision/mission sortent
 * de l'accueil : leurs capacités vivent au tiroir (« Plus d'outils », la porte
 * renommée du rail). Le placeholder inactif est une constante partagée des
 * deux composeurs.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import {
  ACTIONS_ETABLI,
  PLACEHOLDER_COMPOSEUR,
} from '../../lib/etabli';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

vi.mock('../../services/api/voice', async (importOriginal) => ({
  ...(await importOriginal<object>()),
}));

describe('La source unique de l’établi', () => {
  it('déclare exactement les quatre actions, ids et libellés figés', () => {
    expect(ACTIONS_ETABLI).toEqual([
      { id: 'email', label: 'Écrire' },
      { id: 'memory', label: 'Retrouver' },
      { id: 'meeting', label: 'Préparer' },
      { id: 'invoice', label: 'Facturer' },
    ]);
  });

  it('fige le placeholder partagé des composeurs', () => {
    expect(PLACEHOLDER_COMPOSEUR).toBe(
      'Demande à Thérèse d’organiser, créer ou agir…',
    );
  });
});

describe('L’accueil est un établi', () => {
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

  it('propose les quatre actions et ne montre plus priorités/décision/mission', () => {
    render(<ConversationCanvasPrototype />);

    for (const action of ACTIONS_ETABLI) {
      expect(
        screen.getByRole('button', { name: action.label }),
      ).toBeInTheDocument();
    }
    expect(screen.queryByRole('button', { name: 'Mes priorités du jour' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Éclairer une décision' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Confier une mission' })).toBeNull();
  });

  it('la porte du rail s’appelle « Plus d’outils » et ouvre le tiroir', async () => {
    render(<ConversationCanvasPrototype />);

    expect(screen.queryByRole('button', { name: 'Aide' })).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Plus d’outils' }));
    expect(
      await screen.findByRole('heading', { name: 'Ce que Thérèse sait mobiliser' }),
    ).toBeInTheDocument();
  });

  it('le composeur n’a plus de bouton « Capacités »', () => {
    render(<ConversationCanvasPrototype />);

    expect(screen.queryByRole('button', { name: /Capacités/ })).toBeNull();
  });

  it('le composeur inactif porte le placeholder partagé', () => {
    render(<ConversationCanvasPrototype />);

    expect(screen.getByPlaceholderText(PLACEHOLDER_COMPOSEUR)).toBeInTheDocument();
  });

  it('« Essayer un autre parcours » suit la même liste', async () => {
    render(<ConversationCanvasPrototype />);

    // Entrer dans un scénario pour voir le bloc « Essayer un autre parcours »
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Retrouver' }));
    });

    const parcours = await screen.findByText('Essayer un autre parcours');
    const bloc = parcours.parentElement as HTMLElement;
    for (const action of ACTIONS_ETABLI) {
      expect(bloc.textContent).toContain(action.label);
    }
    expect(bloc.textContent).not.toContain('Éclairer une décision');
    expect(bloc.textContent).not.toContain('Confier une mission');
    expect(bloc.textContent).not.toContain('Mes priorités du jour');
  });
});
