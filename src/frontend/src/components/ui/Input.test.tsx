/**
 * Alignement DA du champ : surface, rayon sm, anneau 3 px.
 *
 * L'API ne change pas (zéro import de production aujourd'hui) ; c'est la
 * forme qui s'aligne pour les écrans à venir. On assert les classes, pas
 * le style calculé : jsdom ne résout pas Tailwind.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Input } from './Input';

describe('Input : forme DA', () => {
  it('pose surface, rayon sm, min-h-9 et l’anneau d’accent', () => {
    render(<Input aria-label="Nom" />);
    const champ = screen.getByRole('textbox', { name: 'Nom' });
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
    render(<Input aria-label="Mail" error />);
    const champ = screen.getByRole('textbox', { name: 'Mail' });
    expect(champ.className).toMatch(/border-error/);
    expect(champ.className).toMatch(/focus:ring-error\/30/);
    expect(champ).toHaveAttribute('aria-invalid', 'true');
  });
});
