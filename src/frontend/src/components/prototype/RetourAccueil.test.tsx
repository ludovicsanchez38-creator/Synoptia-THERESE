/**
 * Signalé par Ludo le 28/08 : « il manque pas un bouton pour retourner à la
 * page d'accueil ? »
 *
 * Il manquait, et le lot précédent l'avait aggravé. Le rail n'a aucun bouton
 * d'accueil : on ne peut que FERMER ce qu'on a ouvert, ce qui suppose de
 * savoir ce qu'on a ouvert. Et la seule action nommée « Accueil » — avec son
 * raccourci H et ses mots-clés « accueil, home » — menait au second accueil,
 * celui que le plan veut justement retirer.
 *
 * Autrement dit : aucun chemin nommé ne ramenait à l'accueil réel.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { runAction } from '../../lib/actionRegistry';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

function reinitialiser() {
  vi.clearAllMocks();
  _clearEscapeHandlers();
  useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
  useNavigationStore.setState({ activeView: null, history: [] } as never);
  window.history.replaceState({}, '', '/?interface=conversation-canvas');
}

describe('Revenir à l’accueil', () => {
  beforeEach(reinitialiser);

  it('le rail porte un bouton qui y ramène', async () => {
    render(<ConversationCanvasPrototype />);
    await act(async () => { await Promise.resolve(); });

    const rail = screen.getByRole('navigation', { name: 'Navigation principale' });
    expect(rail).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Accueil' })).toBeInTheDocument();
  });

  it('depuis une vue, il ramène à l’accueil en un geste', async () => {
    render(<ConversationCanvasPrototype />);
    await act(async () => { await Promise.resolve(); });

    await act(async () => { runAction('crm.open'); });
    expect(screen.getByTestId('prototype-unified-view')).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Accueil' }));
    });

    expect(screen.queryByTestId('prototype-unified-view')).not.toBeInTheDocument();
    expect(useNavigationStore.getState().activeView).toBeNull();
  });

  it('depuis une conversation aussi : fermer le chat n’est pas au fond de l’écran', async () => {
    render(<ConversationCanvasPrototype />);
    await act(async () => { await Promise.resolve(); });

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Nouvelle conversation' }));
    });
    expect(screen.getByTestId('prototype-chat-surface')).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Accueil' }));
    });

    expect(screen.queryByTestId('prototype-chat-surface')).not.toBeInTheDocument();
  });

  it('l’action nommée « Accueil » ne mène plus au second accueil', async () => {
    render(<ConversationCanvasPrototype />);
    await act(async () => { await Promise.resolve(); });

    await act(async () => { runAction('crm.open'); });
    await act(async () => { runAction('home.open'); });

    // Le faux accueil s'affichait sous ce nom : plus maintenant.
    expect(useNavigationStore.getState().activeView).not.toBe('home');
    expect(screen.queryByTestId('prototype-unified-view')).not.toBeInTheDocument();
  });
});
