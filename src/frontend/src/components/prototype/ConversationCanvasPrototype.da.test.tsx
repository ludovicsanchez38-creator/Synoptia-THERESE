/**
 * DA « Application affinée », lot 1 (10/09/2026) : la coque.
 *
 * `base.css` de la DA validée : barre de 3,25 rem, rail de 3,5 rem à boutons
 * de 2,5 rem (actif = teinte d'accent, pas le cyan plein), colonne de 56 rem,
 * composeur flottant qui porte l'établi des cinq verbes en tête, bouton
 * d'envoi de 2,25 rem sans bordure d'encre. Le badge « Interface unifiée »
 * (persona 08 : « je ne sais pas ce que c'est ») disparaît.
 *
 * Tailwind ne génère que ce qu'il lit littéralement : ces classes doivent
 * être dans le JSX telles quelles, d'où des assertions sur `className`.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
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

describe('La coque prend la forme de la DA', () => {
  it('le rail fait 3,5 rem sur fond de surface, ses boutons 2,5 rem', () => {
    render(<ConversationCanvasPrototype />);
    const rail = screen.getByRole('navigation', { name: 'Navigation principale' });
    expect(rail.className).toMatch(/\bw-14\b/);
    expect(rail.className).not.toMatch(/\bw-16\b/);
    expect(rail.className).toMatch(/\bbg-surface\b/);
    const accueil = screen.getByRole('button', { name: 'Accueil' });
    expect(accueil.className).toMatch(/\bh-10\b/);
    expect(accueil.className).toMatch(/\bw-10\b/);
    expect(accueil.className).toMatch(/\brounded-sm\b/);
  });

  it('le rail dit où l’on est : Accueil porte aria-current à l’accueil, Projets quand la vue Projets est ouverte', async () => {
    render(<ConversationCanvasPrototype />);
    const accueil = screen.getByRole('button', { name: 'Accueil' });
    expect(accueil).toHaveAttribute('aria-current', 'page');
    // Actif = teinte d'accent, jamais le cyan plein (réservé au geste principal).
    expect(accueil.className).toMatch(/\bbg-accent-tint\b/);
    expect(accueil.className).not.toMatch(/\bbg-accent-fill\b/);

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Projets' }));
    });
    expect(screen.getByRole('button', { name: 'Projets' })).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('button', { name: 'Accueil' })).not.toHaveAttribute('aria-current');
  });

  it('la barre n’affiche plus « Interface unifiée » et garde l’espace de travail', () => {
    render(<ConversationCanvasPrototype />);
    expect(screen.queryByText('Interface unifiée')).toBeNull();
    expect(screen.getByTestId('workspace-label')).toBeInTheDocument();
  });

  it('la colonne et le composeur partagent la largeur de 56 rem', () => {
    render(<ConversationCanvasPrototype />);
    const fil = screen.getByTestId('prototype-conversation-scroll');
    expect((fil.firstElementChild as HTMLElement).className).toMatch(/\bmax-w-colonne\b/);
    const carte = screen.getByTestId('composeur-carte');
    expect((carte.parentElement as HTMLElement).className).toMatch(/\bmax-w-colonne\b/);
  });

  it('l’établi est le premier enfant de la carte du composeur, et le verbe pressé est en teinte', async () => {
    render(<ConversationCanvasPrototype />);
    const carte = screen.getByTestId('composeur-carte');
    const etabli = screen.getByTestId('etabli-composeur');
    expect(carte.firstElementChild).toBe(etabli);
    // Le libellé reste celui que les tests de l'établi cherchent.
    expect(etabli).toHaveTextContent('Par où commencer');

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Retrouver' }));
    });
    const retrouver = screen.getByRole('button', { name: 'Retrouver' });
    expect(retrouver).toHaveAttribute('aria-pressed', 'true');
    expect(retrouver.className).toMatch(/\bbg-accent-tint\b/);
    expect(retrouver.className).not.toMatch(/\bbg-accent-fill\b/);
    // Plus de bloc « Par où commencer » au bas de la colonne.
    expect(screen.getAllByText('Par où commencer')).toHaveLength(1);
  });

  it('la carte du composeur porte l’ombre et l’anneau des jetons, le bouton d’envoi fait 2,25 rem sans bordure d’encre', () => {
    render(<ConversationCanvasPrototype />);
    const carte = screen.getByTestId('composeur-carte');
    expect(carte.className).toMatch(/\bshadow-lg\b/);
    expect(carte.className).not.toMatch(/rgba/);
    const envoyer = screen.getByRole('button', { name: 'Poursuivre dans le chat' });
    expect(envoyer.className).toMatch(/\bh-9\b/);
    expect(envoyer.className).toMatch(/\bw-9\b/);
    expect(envoyer.className).not.toMatch(/\bborder-text\b/);
    expect(envoyer.className).not.toMatch(/translate/);
  });

  it('le titre d’accueil laisse la couche base poser sa taille', () => {
    render(<ConversationCanvasPrototype />);
    const h1 = screen.getByRole('heading', { level: 1 });
    expect(h1.className).not.toMatch(/\btext-2xl\b/);
    expect(h1.className).not.toMatch(/tracking-\[/);
  });
});
