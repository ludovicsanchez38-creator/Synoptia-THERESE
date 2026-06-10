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

  it('revue adversariale : un onEscape recréé à chaque rendu ne fait pas sauter le focus', () => {
    function UnstableHarness() {
      const [open, setOpen] = useState(false);
      const [text, setText] = useState('');
      const ref = useRef<HTMLDivElement>(null);
      // closure recréée à CHAQUE rendu (cas EnvVarModal + polling ToolsPanel)
      useDialogFocusTrap(ref, { active: open, onEscape: () => setOpen(false) });
      return (
        <div>
          <button data-testid="trigger" onClick={() => setOpen(true)}>
            Ouvrir
          </button>
          {open && (
            <div ref={ref} role="dialog" aria-modal="true" aria-label="Test">
              <button data-testid="first">Premier</button>
              <input
                data-testid="champ"
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
            </div>
          )}
        </div>
      );
    }
    const { getByTestId } = render(<UnstableHarness />);
    fireEvent.click(getByTestId('trigger'));
    const champ = getByTestId('champ') as HTMLInputElement;
    champ.focus();
    // Chaque frappe re-rend le parent -> nouvelle identité onEscape ;
    // le focus doit RESTER dans le champ (avant : téléporté au 1er focusable)
    fireEvent.change(champ, { target: { value: 'sk-test' } });
    expect(document.activeElement).toBe(champ);
  });

  it('revue adversariale : deux modales empilées - seule celle du dessus pilote Tab et Escape', () => {
    function StackedHarness() {
      const [bottomOpen, setBottomOpen] = useState(false);
      const [topOpen, setTopOpen] = useState(false);
      const bottomRef = useRef<HTMLDivElement>(null);
      const topRef = useRef<HTMLDivElement>(null);
      useDialogFocusTrap(bottomRef, { active: bottomOpen, onEscape: () => setBottomOpen(false) });
      useDialogFocusTrap(topRef, { active: topOpen, onEscape: () => setTopOpen(false) });
      return (
        <div>
          <button data-testid="open-bottom" onClick={() => setBottomOpen(true)}>
            Ouvrir A
          </button>
          {bottomOpen && (
            <div ref={bottomRef} role="dialog" aria-modal="true" aria-label="A">
              <button data-testid="a-first">A1</button>
              <button data-testid="open-top" onClick={() => setTopOpen(true)}>
                Ouvrir B
              </button>
            </div>
          )}
          {topOpen && (
            <div ref={topRef} role="dialog" aria-modal="true" aria-label="B">
              <button data-testid="b-first">B1</button>
              <button data-testid="b-last">B2</button>
            </div>
          )}
        </div>
      );
    }
    const { getByTestId, queryByLabelText } = render(<StackedHarness />);
    fireEvent.click(getByTestId('open-bottom'));
    fireEvent.click(getByTestId('open-top'));

    // Tab depuis le dernier de B boucle DANS B (A ne recapture pas)
    getByTestId('b-last').focus();
    fireEvent.keyDown(document, { key: 'Tab' });
    expect(document.activeElement).toBe(getByTestId('b-first'));

    // Un seul Escape ne ferme QUE la modale du dessus
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(queryByLabelText('B')).toBeNull();
    expect(queryByLabelText('A')).toBeTruthy();
  });
});
