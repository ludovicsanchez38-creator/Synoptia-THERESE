/**
 * B-292 / B-405 (cycle 4) : la flèche du Select était un SVG en data-URI dont
 * le trait était figé en gris #888, seule couleur du composant à ignorer les
 * jetons du thème et le mode contraste élevé.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Select } from './Select';

const OPTIONS = [
  { value: 'a', label: 'Alpha' },
  { value: 'b', label: 'Bravo' },
];

describe('Select : la flèche suit le thème', () => {
  it("n'embarque plus de couleur figée dans une image de fond", () => {
    render(<Select aria-label="Choix" options={OPTIONS} />);
    const select = screen.getByRole('combobox', { name: 'Choix' });
    expect(select.className).not.toMatch(/%23888|#888|data:image/);
  });

  it('dessine la flèche avec une icône décorative peinte par un jeton', () => {
    const { container } = render(<Select aria-label="Choix" options={OPTIONS} />);
    const fleche = container.querySelector('svg');
    expect(fleche).not.toBeNull();
    expect(fleche?.getAttribute('aria-hidden')).toBe('true');
    expect(fleche?.getAttribute('class') ?? '').toMatch(/text-text-muted/);
    expect(fleche?.getAttribute('class') ?? '').toMatch(/pointer-events-none/);
  });

  it('reste un select natif utilisable, placeholder compris', () => {
    render(<Select aria-label="Choix" options={OPTIONS} placeholder="Choisir" defaultValue="" />);
    const select = screen.getByRole('combobox', { name: 'Choix' }) as HTMLSelectElement;
    expect(select.options).toHaveLength(3);
    expect(select.options[0].disabled).toBe(true);
  });
});

describe('Select : forme DA', () => {
  it('pose surface, rayon sm, min-h-9 et l’anneau d’accent', () => {
    render(<Select aria-label="Choix" options={OPTIONS} />);
    const champ = screen.getByRole('combobox', { name: 'Choix' });
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
    render(<Select aria-label="Choix" options={OPTIONS} error />);
    const champ = screen.getByRole('combobox', { name: 'Choix' });
    expect(champ.className).toMatch(/border-error/);
    expect(champ.className).toMatch(/focus:ring-error\/30/);
    expect(champ).toHaveAttribute('aria-invalid', 'true');
  });
});
