import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useAutosave } from './useAutosave';

describe('useAutosave', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.mocked(localStorage.setItem).mockReset();
    vi.mocked(localStorage.getItem).mockReset();
    vi.mocked(localStorage.removeItem).mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('n’annonce la sauvegarde qu’après succès et permet de réessayer la même saisie', () => {
    vi.mocked(localStorage.setItem).mockImplementationOnce(() => {
      throw new Error('Quota dépassé');
    });
    const { result } = renderHook(() => useAutosave('conversation-1'));

    act(() => {
      result.current.saveDraft('Texte à conserver');
      vi.advanceTimersByTime(5000);
    });

    expect(result.current.lastSavedAt).toBeNull();
    expect(result.current.draftError).toMatch(/reste dans le champ/);

    vi.mocked(localStorage.setItem).mockImplementation(() => undefined);
    act(() => result.current.retrySave());

    expect(localStorage.setItem).toHaveBeenLastCalledWith(
      'therese-draft-conversation-1',
      'Texte à conserver',
    );
    expect(result.current.draftError).toBeNull();
    expect(result.current.lastSavedAt).toBeInstanceOf(Date);
  });
});
