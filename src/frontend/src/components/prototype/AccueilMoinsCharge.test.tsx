/**
 * Entrées 3, 4 et 7 du plan du 28/08 : ce que l'écran montre sans que ça serve.
 *
 * Le chantier de simplification a établi que le nombre d'écrans n'était pas la
 * cause du ressenti « trop d'interfaces ». La densité, elle, reste : 29
 * éléments interactifs par défaut, 73 % du texte en 12 px, 90 puces de jargon.
 *
 * Les réassurances contextuelles ne sont PAS du bruit et ne bougent pas :
 * « Brouillon confirmé, aucun envoi », « Écriture confirmée », « Worktree
 * isolé » disent chacune ce que le parcours en cours peut faire.
 */
import { act, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

function reinitialiser() {
  vi.clearAllMocks();
  _clearEscapeHandlers();
  useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
  useNavigationStore.setState({ activeView: null, history: [] } as never);
  usePanelStore.setState({ showSettings: false } as never);
  window.history.replaceState({}, '', '/?interface=conversation-canvas');
}

describe('Entrée 3 : une seule rangée de sources sur le brief', () => {
  beforeEach(reinitialiser);

  it('ne répète pas la rangée que la carte du jour affiche déjà', async () => {
    render(<ConversationCanvasPrototype />);
    await act(async () => { await Promise.resolve(); });

    // La carte porte « Sources réelles », conditionnées aux données chargées.
    // La coque en collait une seconde, écrite en dur, juste en dessous.
    const rangees = screen.queryAllByText(/^Sources$/);
    expect(rangees).toHaveLength(0);
  });
});

describe('Entrée 4 : un seul bouton là où deux ouvraient le même tiroir', () => {
  beforeEach(reinitialiser);

  it('le rail ne propose plus « Rechercher » à côté de « Historique »', async () => {
    render(<ConversationCanvasPrototype />);
    await act(async () => { await Promise.resolve(); });

    // Uniquement dans le RAIL : « Rechercher » reste dans l'en-tête, où il
    // désigne la palette, qui indexe tout. Deux icônes pour un même tiroir
    // font douter qu'il s'agisse du même, et la loupe du rail ne cherchait
    // que dans les titres de conversation.
    const rail = screen.getByRole('navigation', { name: 'Navigation principale' });
    const { queryByRole } = within(rail);
    expect(queryByRole('button', { name: 'Rechercher' })).toBeNull();
    expect(queryByRole('button', { name: 'Historique' })).toBeNull();
  });

  it('le tiroir des conversations reste atteignable', async () => {
    render(<ConversationCanvasPrototype />);
    await act(async () => { await Promise.resolve(); });

    expect(screen.getByRole('button', { name: 'Conversations' })).toBeInTheDocument();
  });
});
