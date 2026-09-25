/**
 * B-1378 (persona Hugo, cycle 13) : « Retirer la capacité » ôtait l'étiquette
 * mais laissait sa phrase (« Fais une recherche actuelle… ») dans le champ, et
 * le focus tombait sur la page. Retirer la capacité retire la demande qu'elle
 * avait posée (si on ne l'a pas retouchée) et rend le focus au champ.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

vi.mock('../../services/api/voice', async (importOriginal) => ({
  ...(await importOriginal<object>()),
}));

async function ouvrirLeTiroir() {
  render(<ConversationCanvasPrototype />);
  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name: 'Plus d’outils' }));
  });
  await screen.findByRole('heading', { name: 'Capacités' });
}

const PHRASE = 'Fais une recherche actuelle et cite précisément les sources utilisées.';

async function choisirRechercheWeb() {
  await ouvrirLeTiroir();
  const groupe = screen.queryAllByRole('button', { name: /Comprendre et décider/ })[0]
    ?? screen.queryAllByRole('tab', { name: /Comprendre et décider/ })[0];
  if (groupe) await act(async () => { fireEvent.click(groupe); });
  await act(async () => {
    fireEvent.click(screen.getAllByRole('button', { name: /Recherche web/ })[0]);
  });
  await screen.findByRole('button', { name: 'Retirer la capacité' });
}

describe('B-1378 : retirer une capacité retire sa demande', () => {
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
    useNavigationStore.setState(useNavigationStore.getInitialState());
    usePersonalisationStore.setState({ skipDashboard: false });
  });

  it('la phrase posée par la capacité part avec elle, le focus revient au champ', async () => {
    await choisirRechercheWeb();
    const champ = screen.getByDisplayValue(PHRASE) as HTMLTextAreaElement;
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Retirer la capacité' }));
    });
    expect(champ.value).toBe('');
    await waitFor(() => expect(document.activeElement).toBe(champ));
  });

  it('une phrase retouchée reste : c’est la saisie de l’utilisateur', async () => {
    await choisirRechercheWeb();
    const champ = screen.getByDisplayValue(PHRASE) as HTMLTextAreaElement;
    fireEvent.change(champ, { target: { value: PHRASE + ' Sur les salons pro 2026.' } });
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Retirer la capacité' }));
    });
    expect(champ.value).toBe(PHRASE + ' Sur les salons pro 2026.');
  });
});
