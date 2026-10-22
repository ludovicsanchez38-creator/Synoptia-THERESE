import { fireEvent, render, renderHook } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { useKeyboardShortcuts } from './useKeyboardShortcuts';

it.each([false, true])('R6 : une autre modale garde la priorité, avec réglages=%s', (reglages) => {
  render(<>
    {reglages && <div role="dialog" aria-modal="true" data-allow-command-palette />}
    <div role="dialog" aria-modal="true" aria-label="Confirmation" />
  </>);
  const ouvrir = vi.fn();
  renderHook(() => useKeyboardShortcuts({ onCommandPalette: ouvrir }));
  fireEvent.keyDown(window, { key: 'k', ctrlKey: true, metaKey: true });
  expect(ouvrir).not.toHaveBeenCalled();
});
