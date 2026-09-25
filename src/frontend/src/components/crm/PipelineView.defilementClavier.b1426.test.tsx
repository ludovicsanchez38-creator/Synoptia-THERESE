/**
 * B-1426 (tri de la couverture écran P-145, 25/09) : la grille des sept étapes
 * défile en largeur, mais ne prenait pas le focus. Au clavier, les colonnes
 * sans carte hors champ (Livraison, Actif, Archive vides) restaient
 * invisibles : aucune flèche ne faisait défiler la grille.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import type { ContactResponse } from '../../services/api';
import { PipelineView } from './PipelineView';

const CONTACT = {
  id: 'ct-1', first_name: 'Hélène', last_name: 'Ménard', company: null, email: null, phone: null,
  address: null, notes: null, tags: null, stage: 'contact', score: 0, source: null,
  last_interaction: null, created_at: '2026-09-01T10:00:00Z', updated_at: '2026-09-01T10:00:00Z',
} as ContactResponse;

describe('B-1426 : la grille du pipeline défile au clavier', () => {
  it('la zone défilante est nommée et prend le focus', () => {
    render(<PipelineView contacts={[CONTACT]} onContactClick={() => {}} onStageChange={() => {}} />);
    const grille = screen.getByRole('region', { name: 'Étapes du pipeline' });
    expect(grille).toHaveAttribute('tabindex', '0');
  });
});
