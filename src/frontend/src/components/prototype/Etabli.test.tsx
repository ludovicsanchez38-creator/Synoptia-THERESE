/**
 * B1 (0.48) — un établi, un tiroir.
 *
 * L'accueil propose CINQ actions (Écrire, Retrouver, Préparer, Facturer,
 * Décider), depuis une source unique (lib/etabli.ts) suivie aussi par la
 * palette ⌘K et « Essayer un autre parcours ». Les puces priorités et mission
 * restent hors de l'accueil : leurs capacités vivent au tiroir (« Plus
 * d'outils », la porte renommée du rail). Le placeholder inactif est une
 * constante partagée des deux composeurs.
 *
 * « Décider » (26/08, demande de Ludo) : le Board est la capacité la plus
 * distinctive du produit et le seul geste de RECUL parmi des verbes
 * d'exécution ; le laisser au tiroir le rendait invisible. Le principe
 * « un établi, un tiroir » borne l'accueil à peu d'actions, il n'impose
 * pas le nombre quatre.
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
  ICONES_ETABLI,
  PLACEHOLDER_COMPOSEUR,
} from '../../lib/etabli';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

vi.mock('../../services/api/voice', async (importOriginal) => ({
  ...(await importOriginal<object>()),
}));

describe('La source unique de l’établi', () => {
  it('déclare exactement les cinq actions, ids et libellés figés', () => {
    expect(ACTIONS_ETABLI).toEqual([
      { id: 'email', label: 'Écrire' },
      { id: 'memory', label: 'Retrouver' },
      { id: 'meeting', label: 'Préparer' },
      { id: 'invoice', label: 'Facturer' },
      { id: 'board', label: 'Décider' },
    ]);
  });

  /**
   * Le piège que ce test ferme : la palette choisissait l'icône par une
   * cascade de ternaires dont la branche finale servait de fourre-tout.
   * Une action ajoutée y héritait SILENCIEUSEMENT de l'icône de la
   * facture - rien ne cassait, l'écran mentait. Une table exhaustive et
   * injective rend l'oubli impossible à compiler.
   */
  it('donne à chaque action une icône propre, sans branche fourre-tout', () => {
    const icones = ACTIONS_ETABLI.map((action) => ICONES_ETABLI[action.id]);

    for (const [index, icone] of icones.entries()) {
      expect(icone, `icône manquante pour ${ACTIONS_ETABLI[index].id}`).toBeTruthy();
    }
    expect(new Set(icones).size).toBe(ACTIONS_ETABLI.length);
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

  it('propose les cinq actions et ne montre plus priorités/mission', () => {
    render(<ConversationCanvasPrototype />);

    for (const action of ACTIONS_ETABLI) {
      expect(
        screen.getByRole('button', { name: action.label }),
      ).toBeInTheDocument();
    }
    expect(screen.queryByRole('button', { name: 'Mes priorités du jour' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Confier une mission' })).toBeNull();
    // L'ancien libellé long ne revient pas : la puce s'appelle « Décider ».
    expect(screen.queryByRole('button', { name: 'Éclairer une décision' })).toBeNull();
  });

  it('« Décider » ouvre le parcours du Board, pas une autre vue', async () => {
    render(<ConversationCanvasPrototype />);

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Décider' }));
    });

    // Le bloc de parcours n'apparaît qu'une fois DANS un scénario, et la
    // puce active y est marquée : c'est la preuve que board est ouvert.
    const parcours = await screen.findByText('Essayer un autre parcours');
    const bloc = parcours.parentElement as HTMLElement;
    const puce = Array.from(bloc.querySelectorAll('button')).find(
      (b) => b.textContent === 'Décider',
    );
    expect(puce?.getAttribute('aria-pressed')).toBe('true');
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
