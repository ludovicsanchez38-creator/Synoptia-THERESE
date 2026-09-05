/**
 * B-452 : l'isolation d'un dialogue s'arrêtait une génération avant le corps
 * du document. La boucle remontait les parents tant que `parent !== body`,
 * donc les frères de la branche directement sous <body> (un <aside>, un
 * portail, une barre latérale) n'étaient jamais rendus inertes.
 */
import { fireEvent, render } from '@testing-library/react';
import { useRef, useState } from 'react';
import { afterEach, describe, expect, it } from 'vitest';
import { useDialogFocusTrap } from './useDialogFocusTrap';

function Harness() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useDialogFocusTrap(ref, { active: open, onEscape: () => setOpen(false), isolateBackground: true });
  return (
    <div>
      <button data-testid="trigger" onClick={() => setOpen(true)}>Ouvrir</button>
      {open && (
        <div ref={ref} role="dialog" aria-modal="true" aria-label="Test">
          <button>Dedans</button>
        </div>
      )}
    </div>
  );
}

describe('useDialogFocusTrap - isolation jusqu’à la racine (B-452)', () => {
  let aside: HTMLElement;
  afterEach(() => aside.remove());

  it('rend inerte un frère de la branche placé directement sous <body>', () => {
    aside = document.createElement('aside');
    aside.innerHTML = '<button>Hors dialogue</button>';
    document.body.appendChild(aside);

    const { getByTestId } = render(<Harness />);
    fireEvent.click(getByTestId('trigger'));

    expect(aside.getAttribute('aria-hidden')).toBe('true');
    expect(aside.hasAttribute('inert')).toBe(true);
  });
});
