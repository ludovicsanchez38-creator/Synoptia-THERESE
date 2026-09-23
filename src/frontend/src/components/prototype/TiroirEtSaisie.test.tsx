/**
 * Revue Codex n°13 du cycle 11 (23/09/2026), tiroir des conversations.
 *
 * B-991 (R-4) : choisir une conversation (ou en commencer une) sélectionnait
 * la conversation et posait la vue chat AVANT que la coque ne consulte la
 * saisie en cours : « Continuer la saisie » laissait un formulaire affiché
 * sur une navigation déjà passée au chat.
 *
 * B-992 (R-6) : Échap, focus dans le tiroir, fermait tout le tiroir alors
 * que son menu d'actions (ou le renommage, ou la confirmation) était ouvert.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { _viderSaisiesEnCours, inscrireSaisieEnCours } from '../../lib/saisieEnCours';
import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { runAction } from '../../lib/actionRegistry';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';
import { PrototypeConversationDrawer } from './PrototypeConversationDrawer';

const CONVERSATION = {
  id: 'conversation-1', title: 'Préparation rendez-vous réel', messages: [], messageCount: 3,
  createdAt: new Date(), updatedAt: new Date(), synced: true,
};

beforeEach(() => {
  _clearEscapeHandlers();
  _viderSaisiesEnCours();
  window.history.replaceState({}, '', '/?interface=conversation-canvas');
  useChatStore.setState({ conversations: [CONVERSATION] as never, currentConversationId: null, isStreaming: false });
  useNavigationStore.setState({ activeView: 'tasks', history: [] } as never);
  usePanelStore.setState({
    showSettings: false, showSaveCommand: false, showContactModal: false, showProjectModal: false,
    showBoardPanel: false, showShortcuts: false, showPromptLibrary: false, showCommandPalette: false,
    showConversationSidebar: false,
  } as never);
});
afterEach(() => { _clearEscapeHandlers(); _viderSaisiesEnCours(); });

describe('B-991 : le tiroir consulte la saisie en cours avant de naviguer', () => {
  it('conversation choisie avec un formulaire modifié : rien ne bouge, la question est posée', () => {
    const garde = vi.fn(() => true);
    inscrireSaisieEnCours(garde);
    const onOpenChat = vi.fn();
    render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={onOpenChat} />);

    fireEvent.click(screen.getByRole('button', { name: /^Préparation rendez-vous réel/ }));
    expect(garde).toHaveBeenCalled();
    expect(useChatStore.getState().currentConversationId).toBeNull();
    expect(useNavigationStore.getState().activeView).toBe('tasks');
    expect(onOpenChat).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Nouvelle conversation' }));
    expect(useChatStore.getState().conversations).toHaveLength(1);
    expect(onOpenChat).not.toHaveBeenCalled();
  });

  it('témoin : sans saisie en cours, la conversation s’ouvre', () => {
    const onOpenChat = vi.fn();
    render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={onOpenChat} />);
    fireEvent.click(screen.getByRole('button', { name: /^Préparation rendez-vous réel/ }));
    expect(useChatStore.getState().currentConversationId).toBe('conversation-1');
    expect(onOpenChat).toHaveBeenCalledTimes(1);
  });
});

describe('B-992 : Échap ferme d’abord le menu du tiroir, par le vrai chemin clavier', () => {
  it('menu ouvert : Échap le ferme et garde le tiroir ; Échap suivant ferme le tiroir', async () => {
    useNavigationStore.setState({ activeView: 'chat', history: [] } as never);
    render(<ConversationCanvasPrototype />);
    await act(async () => { runAction('conversations.toggle'); });
    await waitFor(() => screen.getByTestId('prototype-conversation-drawer'));

    fireEvent.click(screen.getByRole('button', { name: 'Actions pour Préparation rendez-vous réel' }));
    expect(screen.getByRole('menuitem', { name: 'Renommer' })).toHaveFocus();

    await act(async () => { fireEvent.keyDown(window, { key: 'Escape' }); });
    expect(screen.queryByRole('menu')).toBeNull();
    expect(screen.queryByTestId('prototype-conversation-drawer')).not.toBeNull();

    await act(async () => { fireEvent.keyDown(window, { key: 'Escape' }); });
    await waitFor(() => expect(screen.queryByTestId('prototype-conversation-drawer')).toBeNull());
  });
});

describe('B-994 : une navigation posée dans le store respecte la saisie en cours', () => {
  const vueAffichee = () => screen.getByTestId('conversation-canvas-prototype').getAttribute('data-embedded-view');

  it('vue demandée par le registre ou la palette pendant une saisie retenue : le store revient à la vue affichée', async () => {
    useNavigationStore.setState({ activeView: null, history: [] } as never);
    render(<ConversationCanvasPrototype />);
    await act(async () => { runAction('tasks.open'); });
    await waitFor(() => expect(vueAffichee()).toBe('tasks'));

    const garde = vi.fn(() => true);
    const desinscrire = inscrireSaisieEnCours(garde);
    await act(async () => { runAction('memory.open'); });
    expect(garde).toHaveBeenCalled();
    expect(vueAffichee()).toBe('tasks');
    expect(useNavigationStore.getState().activeView).toBe('tasks');

    await act(async () => { window.dispatchEvent(new CustomEvent('therese:client-action', { detail: { actionId: 'memory.open' } })); });
    expect(vueAffichee()).toBe('tasks');
    expect(useNavigationStore.getState().activeView).toBe('tasks');

    // Saisie abandonnée : la même demande aboutit, le store et l'écran s'accordent.
    desinscrire();
    await act(async () => { runAction('memory.open'); });
    await waitFor(() => expect(vueAffichee()).toBe('memory'));
    expect(useNavigationStore.getState().activeView).toBe('memory');
  });
});
