/**
 * THÉRÈSE v2 - Tests ChatHeader (D2, entrée Documents)
 *
 * Vérifie que le bouton « Documents » de la barre de navigation du header
 * existe (aria-label, pattern du bouton « Projets ») et déclenche bien son
 * callback - le câblage callback -> setView('documents') est couvert côté
 * ChatLayout (ChatLayout.test.tsx).
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ChatHeader } from './ChatHeader';

// Tauri indisponible en jsdom : les contrôles de fenêtre sont hors sujet ici.
vi.mock('@tauri-apps/api/window', () => ({
  getCurrentWindow: () => ({
    startDragging: vi.fn(),
    minimize: vi.fn(),
    toggleMaximize: vi.fn(),
    close: vi.fn(),
  }),
}));

// La cloche de notifications poll le backend : neutralisée.
vi.mock('../ui/NotificationCenter', () => ({
  NotificationCenter: () => null,
}));

describe('ChatHeader - bouton Documents (D2)', () => {
  it('rend le bouton « Documents » et déclenche onToggleDocumentsPanel au clic', () => {
    const onToggleDocumentsPanel = vi.fn();
    render(<ChatHeader onToggleDocumentsPanel={onToggleDocumentsPanel} />);

    const button = screen.getByRole('button', { name: 'Documents' });
    fireEvent.click(button);

    expect(onToggleDocumentsPanel).toHaveBeenCalledTimes(1);
  });

  it('le bouton « Projets » (pattern de référence) reste présent à côté', () => {
    const onToggleProjectsPanel = vi.fn();
    render(<ChatHeader onToggleProjectsPanel={onToggleProjectsPanel} />);

    fireEvent.click(screen.getByRole('button', { name: 'Projets' }));
    expect(onToggleProjectsPanel).toHaveBeenCalledTimes(1);
  });
});
