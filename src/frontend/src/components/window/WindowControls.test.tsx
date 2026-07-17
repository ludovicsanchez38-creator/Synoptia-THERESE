import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';

const minimize = vi.fn().mockResolvedValue(undefined);
const toggleMaximize = vi.fn().mockResolvedValue(undefined);
const close = vi.fn().mockResolvedValue(undefined);

vi.mock('@tauri-apps/api/window', () => ({
  getCurrentWindow: () => ({ minimize, toggleMaximize, close }),
}));

import { WindowControls } from './WindowControls';

function setPlatform(value: string) {
  Object.defineProperty(window.navigator, 'platform', { value, configurable: true });
}

describe('WindowControls', () => {
  beforeEach(() => {
    minimize.mockClear();
    toggleMaximize.mockClear();
    close.mockClear();
  });
  afterEach(() => {
    // @ts-expect-error nettoyage du flag Tauri de test
    delete window.__TAURI__;
    setPlatform('');
  });

  it('ne rend rien hors Tauri (pas de fausse affordance en navigateur)', () => {
    setPlatform('MacIntel');
    const { container } = render(<WindowControls />);
    expect(container.firstChild).toBeNull();
  });

  it('macOS : pastilles à gauche, câblées sur l’API de fenêtre', async () => {
    setPlatform('MacIntel');
    // @ts-expect-error simulation contexte Tauri
    window.__TAURI__ = {};
    render(<WindowControls side="left" />);

    screen.getByLabelText('Réduire la fenêtre').click();
    screen.getByLabelText('Agrandir ou restaurer la fenêtre').click();
    screen.getByLabelText('Fermer la fenêtre').click();

    expect(minimize).toHaveBeenCalledTimes(1);
    expect(toggleMaximize).toHaveBeenCalledTimes(1);
    expect(close).toHaveBeenCalledTimes(1);
  });

  it('macOS : rien côté droit (les pastilles vivent à gauche)', () => {
    setPlatform('MacIntel');
    // @ts-expect-error simulation contexte Tauri
    window.__TAURI__ = {};
    const { container } = render(<WindowControls side="right" />);
    expect(container.firstChild).toBeNull();
  });

  it('Windows : aucune pastille macOS à gauche (revue 0.40)', () => {
    setPlatform('Win32');
    // @ts-expect-error simulation contexte Tauri
    window.__TAURI__ = {};
    const { container } = render(<WindowControls side="left" />);
    expect(container.firstChild).toBeNull();
  });

  it('Windows : contrôles à droite avec glyphes, câblés sur l’API de fenêtre', () => {
    setPlatform('Win32');
    // @ts-expect-error simulation contexte Tauri
    window.__TAURI__ = {};
    render(<WindowControls side="right" />);

    screen.getByLabelText('Réduire la fenêtre').click();
    screen.getByLabelText('Agrandir ou restaurer la fenêtre').click();
    screen.getByLabelText('Fermer la fenêtre').click();

    expect(minimize).toHaveBeenCalledTimes(1);
    expect(toggleMaximize).toHaveBeenCalledTimes(1);
    expect(close).toHaveBeenCalledTimes(1);
  });

  it('Linux : mêmes contrôles à droite que Windows, rien à gauche', () => {
    setPlatform('Linux x86_64');
    // @ts-expect-error simulation contexte Tauri
    window.__TAURI__ = {};
    const left = render(<WindowControls side="left" />);
    expect(left.container.firstChild).toBeNull();
    left.unmount();

    render(<WindowControls side="right" />);
    expect(screen.getByLabelText('Fermer la fenêtre')).toBeTruthy();
    expect(screen.getByLabelText('Réduire la fenêtre')).toBeTruthy();
  });
});
