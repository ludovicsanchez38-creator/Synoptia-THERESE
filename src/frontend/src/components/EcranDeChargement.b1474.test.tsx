/** B-1474 (recette P-146, lot 5, KO-12) : l'écran de chargement disait « THERESE ». */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { EcranDeChargement } from './EcranDeChargement';

describe('B-1474 : écran de chargement', () => {
  it('écrit le nom avec ses accents', () => {
    render(<EcranDeChargement />);
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('THÉRÈSE');
  });
});
