/**
 * US-013 : le focus est piégé dans les modales et restauré à la fermeture.
 */
import { fireEvent, render } from '@testing-library/react';
import { useRef, useState } from 'react';
import { describe, expect, it } from 'vitest';
import { useDialogFocusTrap } from './useDialogFocusTrap';

function Harness({ withEscape = true }: { withEscape?: boolean }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useDialogFocusTrap(ref, {
    active: open,
    onEscape: withEscape ? () => setOpen(false) : undefined,
  });
  return (
    <div>
      <button data-testid="trigger" onClick={() => setOpen(true)}>
        Ouvrir
      </button>
      {open && (
        <div ref={ref} role="dialog" aria-modal="true" aria-label="Test">
          <button data-testid="first">Premier</button>
          <button data-testid="last">Dernier</button>
        </div>
      )}
    </div>
  );
}

describe('useDialogFocusTrap (US-013)', () => {
  it('focus initial sur le premier élément focusable', () => {
    const { getByTestId } = render(<Harness />);
    fireEvent.click(getByTestId('trigger'));
    expect(document.activeElement).toBe(getByTestId('first'));
  });

  it('Tab depuis le dernier élément boucle sur le premier', () => {
    const { getByTestId } = render(<Harness />);
    fireEvent.click(getByTestId('trigger'));
    getByTestId('last').focus();
    fireEvent.keyDown(document, { key: 'Tab' });
    expect(document.activeElement).toBe(getByTestId('first'));
  });

  it('Shift+Tab depuis le premier boucle sur le dernier', () => {
    const { getByTestId } = render(<Harness />);
    fireEvent.click(getByTestId('trigger'));
    fireEvent.keyDown(document, { key: 'Tab', shiftKey: true });
    expect(document.activeElement).toBe(getByTestId('last'));
  });

  it('Escape ferme et le focus REVIENT au déclencheur', () => {
    const { getByTestId, queryByRole } = render(<Harness />);
    const trigger = getByTestId('trigger');
    trigger.focus();
    fireEvent.click(trigger);
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(queryByRole('dialog')).toBeNull();
    expect(document.activeElement).toBe(trigger);
  });

  it("sans onEscape, Escape ne ferme pas (wizards multi-étapes)", () => {
    const { getByTestId, queryByRole } = render(<Harness withEscape={false} />);
    fireEvent.click(getByTestId('trigger'));
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(queryByRole('dialog')).toBeTruthy();
  });
});
