/**
 * Cycle 6, lecteur #198 (useAutosave.ts) : le nettoyage annulait le minuteur
 * sans rien écrire ; taper puis démonter le composeur (fermeture, changement
 * de conversation) avant cinq secondes ne laissait aucun brouillon.
 */
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useAutosave } from './useAutosave';

describe('#198 : un brouillon en attente est écrit au démontage', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.mocked(localStorage.setItem).mockReset();
  });
  afterEach(() => { vi.useRealTimers(); });

  it('démonter avant l’échéance écrit quand même le texte', () => {
    const { result, unmount } = renderHook(() => useAutosave('conversation-1'));
    act(() => { result.current.saveDraft('Texte tapé puis fermé'); });
    expect(localStorage.setItem).not.toHaveBeenCalled();
    unmount();
    expect(localStorage.setItem).toHaveBeenCalledWith('therese-draft-conversation-1', 'Texte tapé puis fermé');
  });

  it('rien en attente : le démontage n’écrit rien', () => {
    const { unmount } = renderHook(() => useAutosave('conversation-1'));
    unmount();
    expect(localStorage.setItem).not.toHaveBeenCalled();
  });
});
