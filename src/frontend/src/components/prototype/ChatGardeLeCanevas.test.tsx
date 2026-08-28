/**
 * Entrée 9 du plan du 28/08 : le chat tuait l'objet qu'il commente.
 *
 * Poser une question sur le message affiché coûtait : perdre le message,
 * poser la question, fermer le chat, refaire « Écrire », recliquer la ligne.
 *
 * Deux erreurs de ma première tentative, corrigées par la relecture :
 *
 *   - je cherchais la carte du parcours, qui vit dans la colonne principale —
 *     celle que le ternaire démonte quand le chat s'ouvre. Le canevas, lui,
 *     est ailleurs : c'est l'aside `prototype-context-canvas-title` ;
 *   - je croyais le canevas prisonnier de la branche accueil. Il ne l'est pas,
 *     il est déjà rendu à part. Le seul verrou est la fermeture dans `openChat`.
 *
 * Le contrat d'écran, lui, ne bouge pas : sous le seuil, le canevas recouvre
 * la colonne et l'isole (voile 0.48.1). L'y laisser poserait `inert` sur la
 * conversation — un chat à l'écran et mort.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

function poserLargeur(coteACote: boolean) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: query.includes('min-width: 1280px') ? coteACote : false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })) as unknown as typeof window.matchMedia;
}

/**
 * Relecture Grok du 28/08, objection 2 : `estCoteACote()` est un INSTANTANÉ lu
 * à l'ouverture, alors que l'isolation, elle, suit la largeur en continu
 * (`usePanneauCouvrant` écoute `matchMedia`, `useDialogFocusTrap` se réarme).
 * Ouvrir large puis rétrécir reproduisait donc l'échec que ce lot refuse, avec
 * un geste de retard. Le mock ci-dessus ne peut pas le montrer : ses listeners
 * sont des `vi.fn()`, personne ne reçoit jamais `change`.
 */
function poserLargeurPilotable(coteACote: boolean) {
  const auditeurs = new Set<(evenement: MediaQueryListEvent) => void>();
  let large = coteACote;
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    get matches() { return query.includes('min-width: 1280px') ? large : false; },
    media: query,
    onchange: null,
    addListener: (l: (e: MediaQueryListEvent) => void) => auditeurs.add(l),
    removeListener: (l: (e: MediaQueryListEvent) => void) => auditeurs.delete(l),
    addEventListener: (_type: string, l: (e: MediaQueryListEvent) => void) => auditeurs.add(l),
    removeEventListener: (_type: string, l: (e: MediaQueryListEvent) => void) => auditeurs.delete(l),
    dispatchEvent: vi.fn(),
  })) as unknown as typeof window.matchMedia;
  return (suivant: boolean) => {
    large = suivant;
    auditeurs.forEach((auditeur) => auditeur({ matches: suivant } as MediaQueryListEvent));
  };
}

function reinitialiser() {
  vi.clearAllMocks();
  _clearEscapeHandlers();
  useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
  useNavigationStore.setState({ activeView: null, history: [] } as never);
  // Le scénario « meeting » monte son canevas dès l'URL.
  window.history.replaceState({}, '', '/?interface=conversation-canvas&scenario=meeting');
}

const CANEVAS = '[aria-labelledby="prototype-context-canvas-title"]';

describe('Entrée 9 : le chat garde l’objet qu’il commente', () => {
  beforeEach(reinitialiser);

  it('grand écran : l’objet reste à l’écran quand la conversation s’ouvre', async () => {
    poserLargeur(true);
    render(<ConversationCanvasPrototype />);
    await act(async () => { await Promise.resolve(); });
    expect(document.querySelector(CANEVAS)).toBeTruthy();

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Nouvelle conversation' }));
    });

    expect(screen.getByTestId('prototype-chat-surface')).toBeInTheDocument();

    // `AnimatePresence` garde l'élément le temps de sa sortie : lire le DOM
    // juste après le clic ne distingue pas « il reste » de « il s'en va ». On
    // laisse la sortie se produire — le cas étroit ci-dessous montre qu'elle
    // aboutit — avant d'affirmer qu'il est toujours là.
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 500));
    });

    expect(document.querySelector(CANEVAS)).toBeTruthy();
    // Et la conversation reste vivante : rien ne l'a rendue inerte.
    expect(screen.getByTestId('prototype-chat-surface').closest('[inert]')).toBeNull();
  });

  it('rétrécir APRÈS coup rend la place, plutôt que d’isoler la conversation', async () => {
    const redimensionner = poserLargeurPilotable(true);
    render(<ConversationCanvasPrototype />);
    await act(async () => { await Promise.resolve(); });

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Nouvelle conversation' }));
    });
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 500));
    });
    expect(document.querySelector(CANEVAS)).toBeTruthy();

    // La fenêtre passe sous le seuil : le canevas devient couvrant.
    await act(async () => { redimensionner(false); });

    await waitFor(() => expect(document.querySelector(CANEVAS)).toBeNull());
    expect(screen.getByTestId('prototype-chat-surface').closest('[inert]')).toBeNull();
  });

  it('écran étroit : l’objet cède la place, sinon le chat serait inerte', async () => {
    poserLargeur(false);
    render(<ConversationCanvasPrototype />);
    await act(async () => { await Promise.resolve(); });
    expect(document.querySelector(CANEVAS)).toBeTruthy();

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Nouvelle conversation' }));
    });

    expect(screen.getByTestId('prototype-chat-surface')).toBeInTheDocument();
    // `AnimatePresence` garde l'élément le temps de sa sortie : on attend la
    // disparition réelle plutôt que de lire le DOM à l'instant du clic.
    await waitFor(() => expect(document.querySelector(CANEVAS)).toBeNull());
  });
});
