import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';

const minimize = vi.fn().mockResolvedValue(undefined);
const toggleMaximize = vi.fn().mockResolvedValue(undefined);
const close = vi.fn().mockResolvedValue(undefined);

vi.mock('@tauri-apps/api/window', () => ({
  getCurrentWindow: () => ({ minimize, toggleMaximize, close }),
}));

import { WindowControls } from './WindowControls';

describe('WindowControls', () => {
  beforeEach(() => {
    minimize.mockClear();
    toggleMaximize.mockClear();
    close.mockClear();
  });
  afterEach(() => {
    // @ts-expect-error nettoyage du flag Tauri de test
    delete window.__TAURI__;
  });

  it('ne rend rien hors Tauri (pas de fausse affordance en navigateur)', () => {
    const { container } = render(<WindowControls />);
    expect(container.firstChild).toBeNull();
  });

  it('câble réduire, agrandir et fermer sur l’API de fenêtre sous Tauri', async () => {
    // @ts-expect-error simulation contexte Tauri
    window.__TAURI__ = {};
    render(<WindowControls />);

    screen.getByLabelText('Réduire la fenêtre').click();
    screen.getByLabelText('Agrandir ou restaurer la fenêtre').click();
    screen.getByLabelText('Fermer la fenêtre').click();

    expect(minimize).toHaveBeenCalledTimes(1);
    expect(toggleMaximize).toHaveBeenCalledTimes(1);
    expect(close).toHaveBeenCalledTimes(1);
  });
});
