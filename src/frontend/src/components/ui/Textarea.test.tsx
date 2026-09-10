/**
 * Alignement DA du textarea : même forme que Input et Select.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Textarea } from './Textarea';

describe('Textarea : forme DA', () => {
  it('pose surface, rayon sm, min-h-9 et l’anneau d’accent', () => {
    render(<Textarea aria-label="Notes" />);
    const champ = screen.getByRole('textbox', { name: 'Notes' });
    expect(champ.className).toMatch(/rounded-sm/);
    expect(champ.className).toMatch(/bg-surface/);
    expect(champ.className).not.toMatch(/bg-surface-2/);
    expect(champ.className).toMatch(/min-h-9/);
    expect(champ.className).toMatch(/px-3/);
    expect(champ.className).toMatch(/py-2/);
    expect(champ.className).toMatch(/text-sm/);
    expect(champ.className).toMatch(/border-border/);
    expect(champ.className).toMatch(/focus:border-accent/);
    expect(champ.className).toMatch(/focus:ring-\[3px\]/);
    expect(champ.className).toMatch(/focus:ring-ring\/30/);
    expect(champ.className).toMatch(/focus:outline-none/);
    expect(champ.className).toMatch(/disabled:opacity-50/);
  });

  it('en erreur, borde en error et teinte l’anneau', () => {
    render(<Textarea aria-label="Notes" error />);
    const champ = screen.getByRole('textbox', { name: 'Notes' });
    expect(champ.className).toMatch(/border-error/);
    expect(champ.className).toMatch(/focus:ring-error\/30/);
    expect(champ).toHaveAttribute('aria-invalid', 'true');
  });
});
