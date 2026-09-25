/**
 * B-1386 (persona Nathalie, cycle 13) : depuis le panneau « Relances et
 * alertes », « Créer depuis un email » ouvre la vue E-mail. « Retour » (ou
 * Échap) menait ensuite au Pipeline, sans le panneau d'où l'on venait : ouvrir
 * une vue ferme les panneaux-outils, et la pile de navigation ne connaît que
 * les vues. Le panneau est désormais retenu comme origine de la vue qu'il a
 * ouverte, et un geste de retour le rouvre, sur l'écran qui était dessous.
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

function ecranAffiche(): string | null {
  const vue = document
    .querySelector('[data-testid="conversation-canvas-prototype"]')
    ?.getAttribute('data-embedded-view') ?? null;
  return vue === 'accueil' ? null : vue;
}

async function ouvrirLesRelances() {
  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name: 'Plus d’outils' }));
  });
  await screen.findByRole('heading', { name: 'Capacités' });
  await act(async () => {
    fireEvent.click(screen.getAllByRole('button', { name: /Relances et alertes/ })[0]);
  });
  await screen.findByTestId('follow-ups-workspace-canvas');
}

async function creerDepuisUnEmail() {
  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name: /Créer depuis un email/ }));
  });
  await waitFor(() => expect(ecranAffiche()).toBe('email'));
  expect(screen.queryByTestId('follow-ups-workspace-canvas')).not.toBeInTheDocument();
}

describe('B-1386 : revenir au panneau des relances', () => {
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

  it('« Retour » depuis l’e-mail rouvre le panneau, sur l’accueil', async () => {
    render(<ConversationCanvasPrototype />);
    await ouvrirLesRelances();
    await creerDepuisUnEmail();

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Revenir à l’écran précédent' }));
    });

    await screen.findByTestId('follow-ups-workspace-canvas');
    expect(ecranAffiche()).toBeNull();
    expect(useNavigationStore.getState().activeView).toBeNull();
  });

  it('depuis le Pipeline : la pile suit l’écran, « Retour » ne ramène pas au Pipeline', async () => {
    // Le parcours de Nathalie : le tiroir referme le Pipeline pour ouvrir le
    // panneau, mais la pile gardait `crm`. « Retour » depuis l'e-mail menait
    // donc à un écran qu'elle avait quitté, et le panneau avait disparu.
    render(<ConversationCanvasPrototype />);
    await act(async () => {
      fireEvent.keyDown(window, { key: 'p', ctrlKey: true, metaKey: true });
    });
    await waitFor(() => expect(ecranAffiche()).toBe('crm'));
    await ouvrirLesRelances();
    expect(ecranAffiche()).toBeNull();
    expect(useNavigationStore.getState().activeView).toBeNull();
    await creerDepuisUnEmail();

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Revenir à l’écran précédent' }));
    });

    await screen.findByTestId('follow-ups-workspace-canvas');
    expect(ecranAffiche()).toBeNull();
    expect(useNavigationStore.getState().activeView).toBeNull();
  });

  it('Échap sur la vue E-mail rouvre aussi le panneau', async () => {
    render(<ConversationCanvasPrototype />);
    await ouvrirLesRelances();
    await creerDepuisUnEmail();

    await act(async () => {
      fireEvent.keyDown(window, { key: 'Escape' });
    });

    await screen.findByTestId('follow-ups-workspace-canvas');
    expect(ecranAffiche()).toBeNull();
  });

  it('une vue ouverte autrement ne rouvre pas le panneau', async () => {
    render(<ConversationCanvasPrototype />);
    await ouvrirLesRelances();
    await creerDepuisUnEmail();
    // L'utilisateur part ailleurs : l'origine est oubliée.
    await act(async () => {
      useNavigationStore.getState().setView('tasks');
    });
    await waitFor(() => expect(ecranAffiche()).toBe('tasks'));
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Revenir à l’écran précédent' }));
    });
    await waitFor(() => expect(ecranAffiche()).toBe('email'));
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Revenir à l’écran précédent' }));
    });
    await waitFor(() => expect(ecranAffiche()).toBeNull());
    expect(screen.queryByTestId('follow-ups-workspace-canvas')).not.toBeInTheDocument();
  });

  it('une carte qui mène à une vue garde l’écran précédent dans la pile', async () => {
    // Régression de la première version de B-1386 : la pile était vidée pour
    // toute carte, et Pipeline → carte « Tâches » → « Retour » menait à
    // l'Accueil au lieu du Pipeline.
    render(<ConversationCanvasPrototype />);
    await act(async () => {
      fireEvent.keyDown(window, { key: 'p', ctrlKey: true, metaKey: true });
    });
    await waitFor(() => expect(ecranAffiche()).toBe('crm'));
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Plus d’outils' }));
    });
    await screen.findByRole('heading', { name: 'Capacités' });
    await act(async () => {
      fireEvent.click(screen.getAllByRole('button', { name: /^Tâches/ })[0]);
    });
    await waitFor(() => expect(ecranAffiche()).toBe('tasks'));

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Revenir à l’écran précédent' }));
    });

    await waitFor(() => expect(ecranAffiche()).toBe('crm'));
  });
});
