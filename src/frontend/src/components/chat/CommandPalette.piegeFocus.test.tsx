/**
 * B-359 (cycle 4) : la palette de commandes annonçait role="dialog" et
 * aria-modal="true" sans piège de focus : la tabulation sortait de la surface
 * annoncée modale.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeAll, describe, expect, it, vi } from 'vitest';

import { CommandPalette } from './CommandPalette';

describe('CommandPalette : piège de focus (B-359)', () => {
  beforeAll(() => {
    // jsdom n'implémente pas scrollIntoView, que la palette appelle à la sélection.
    Element.prototype.scrollIntoView = vi.fn();
  });

  it('Tab depuis le dernier élément focalisable revient dans la palette', () => {
    render(
      <>
        <button type="button" data-testid="dehors">Dehors</button>
        <CommandPalette isOpen onClose={vi.fn()} />
      </>,
    );
    const dialog = screen.getByRole('dialog', { name: 'Palette de commandes' });
    const focalisables = dialog.querySelectorAll<HTMLElement>('button, [href], input, [tabindex]:not([tabindex="-1"])');
    expect(focalisables.length).toBeGreaterThan(0);
    focalisables[focalisables.length - 1].focus();
    fireEvent.keyDown(document, { key: 'Tab' });
    // jsdom ne déplace pas le focus sur Tab : seul le piège le fait boucler
    // sur le premier élément. Sans piège, le focus resterait sur le dernier.
    expect(document.activeElement).toBe(focalisables[0]);
  });
});
