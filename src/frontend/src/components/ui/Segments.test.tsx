/**
 * Segments : un groupe de boutons exclusifs, pas une tablist.
 *
 * Une tablist sans onglets, sans roving tabindex et sans flèches est un
 * mensonge pour le lecteur d'écran (l'établi a déjà le bon motif :
 * role="group" + aria-pressed). On le reprend tel quel.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { Segments } from './Segments';

const OPTIONS = [
  { id: 'semaine', label: 'Semaine' },
  { id: 'mois', label: 'Mois' },
  { id: 'annee', label: 'Année' },
];

describe('Segments', () => {
  it('est un groupe nommé, jamais une tablist', () => {
    render(<Segments label="Période" options={OPTIONS} valeur="mois" onChange={() => {}} />);

    const groupe = screen.getByRole('group', { name: 'Période' });
    expect(groupe.className).toMatch(/inline-flex/);
    expect(groupe.className).toMatch(/gap-1/);
    expect(groupe.className).toMatch(/p-1/);
    expect(groupe.className).toMatch(/rounded-full/);
    expect(groupe.className).toMatch(/bg-surface-2/);

    expect(screen.queryByRole('tablist')).not.toBeInTheDocument();
    expect(screen.queryByRole('tab')).not.toBeInTheDocument();
  });

  it('marque l’option courante avec aria-pressed, les autres relâchées', () => {
    render(<Segments label="Période" options={OPTIONS} valeur="mois" onChange={() => {}} />);

    expect(screen.getByRole('button', { name: 'Semaine' })).toHaveAttribute('aria-pressed', 'false');
    expect(screen.getByRole('button', { name: 'Mois' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: 'Année' })).toHaveAttribute('aria-pressed', 'false');

    const presse = screen.getByRole('button', { name: 'Mois' });
    expect(presse).toHaveAttribute('type', 'button');
    expect(presse.className).toMatch(/bg-surface/);
    expect(presse.className).toMatch(/text-text/);
    expect(presse.className).toMatch(/shadow-sm/);

    const autre = screen.getByRole('button', { name: 'Semaine' });
    expect(autre.className).toMatch(/text-text-muted/);
    expect(autre.className).toMatch(/rounded-full/);
    expect(autre.className).toMatch(/px-3/);
    expect(autre.className).toMatch(/py-1/);
    expect(autre.className).toMatch(/text-sm/);
    expect(autre.className).toMatch(/font-medium/);
  });

  it('signale le changement au clic, y compris au clavier natif du bouton', () => {
    const onChange = vi.fn();
    render(<Segments label="Période" options={OPTIONS} valeur="mois" onChange={onChange} />);

    fireEvent.click(screen.getByRole('button', { name: 'Année' }));
    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith('annee');

    expect(screen.getByRole('button', { name: 'Année' }).tagName).toBe('BUTTON');
  });
});
