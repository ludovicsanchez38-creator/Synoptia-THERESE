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
