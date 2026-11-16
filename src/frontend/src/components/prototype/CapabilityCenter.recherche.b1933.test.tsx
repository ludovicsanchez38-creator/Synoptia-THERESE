/**
 * B-1933 : pendant une recherche, aucun onglet ne filtre, mais le panneau
 * reste étiqueté par le groupe qui était sélectionné. La liste, elle, mélange
 * les intentions.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { CapabilityCenter } from './CapabilityCenter';

describe('CapabilityCenter : le panneau dit ce que la recherche affiche (B-1933)', () => {
  it('une recherche qui sort du groupe ne laisse pas le panneau au nom de ce groupe', () => {
    render(<CapabilityCenter onClose={vi.fn()} onChoose={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('Rechercher une capacité'), { target: { value: 'pipeline' } });

    const panneau = screen.getByRole('tabpanel');
    expect(screen.getByRole('button', { name: /Pipeline/ })).toBeInTheDocument();
    expect(panneau).toHaveAccessibleName('Résultats de la recherche');
    expect(panneau).not.toHaveAccessibleName(/Organiser mon quotidien/);

    fireEvent.change(screen.getByLabelText('Rechercher une capacité'), { target: { value: '' } });
    expect(screen.getByRole('tabpanel')).toHaveAccessibleName(/Organiser mon quotidien/);
  });
});
