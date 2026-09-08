/**
 * B-638 (persona Nadia, c4) : la Décision ouverte (⌘D), les raccourcis ⌘E,
 * ⌘T, ⌘I, ⌘P, ⌘O changeaient la vue DERRIÈRE la fenêtre modale ; ⌘E
 * empilait même deux dialogues, et Échap laissait l'utilisateur dans une vue
 * jamais vue s'ouvrir. Tant qu'un dialogue modal est ouvert, il absorbe les
 * raccourcis de navigation ; seul Échap passe.
 */
import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useKeyboardShortcuts } from './useKeyboardShortcuts';

function frappe(key: string, shift = false) {
  return new KeyboardEvent('keydown', { key, ctrlKey: true, metaKey: true, shiftKey: shift, bubbles: true });
}

describe('B-638 : un dialogue modal absorbe les raccourcis de navigation', () => {
  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('avec une modale ouverte, ⌘E ⌘T ⌘I ⌘P ⌘O ne font rien, Échap passe', () => {
    document.body.innerHTML = '<div role="dialog" aria-modal="true" aria-label="Décision"></div>';
    const handlers = {
      onToggleEmailPanel: vi.fn(),
      onOpenTasks: vi.fn(),
      onToggleInvoicesPanel: vi.fn(),
      onOpenPipeline: vi.fn(),
      onOpenFiles: vi.fn(),
      onEscape: vi.fn(),
    };
    renderHook(() => useKeyboardShortcuts(handlers));

    act(() => {
      for (const k of ['e', 't', 'i', 'p', 'o']) document.dispatchEvent(frappe(k));
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    });

    expect(handlers.onToggleEmailPanel).not.toHaveBeenCalled();
    expect(handlers.onOpenTasks).not.toHaveBeenCalled();
    expect(handlers.onToggleInvoicesPanel).not.toHaveBeenCalled();
    expect(handlers.onOpenPipeline).not.toHaveBeenCalled();
    expect(handlers.onOpenFiles).not.toHaveBeenCalled();
    expect(handlers.onEscape).toHaveBeenCalledTimes(1);
  });

  it('sans modale, ⌘E fonctionne comme avant', () => {
    const handlers = { onToggleEmailPanel: vi.fn() };
    renderHook(() => useKeyboardShortcuts(handlers));
    act(() => {
      document.dispatchEvent(frappe('e'));
    });
    expect(handlers.onToggleEmailPanel).toHaveBeenCalledTimes(1);
  });
});
