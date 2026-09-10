/** Cycle 6, persona Sophie (sophie-07) : la fin de la mise en route promet ⌘, « à tout moment » ; le raccourci était muet dans le composeur. */
import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { useKeyboardShortcuts } from './useKeyboardShortcuts';

describe('⌘, ouvre les Paramètres même depuis un champ de saisie', () => {
  afterEach(() => { document.body.innerHTML = ''; });

  it('depuis le composeur (textarea), ⌘, appelle onOpenSettings', () => {
    const onOpenSettings = vi.fn();
    renderHook(() => useKeyboardShortcuts({ onOpenSettings }));
    const zone = document.createElement('textarea');
    document.body.appendChild(zone);
    zone.focus();
    act(() => {
      zone.dispatchEvent(new KeyboardEvent('keydown', { key: ',', metaKey: true, ctrlKey: true, bubbles: true }));
    });
    expect(onOpenSettings).toHaveBeenCalled();
  });
});
