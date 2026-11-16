/**
 * B-1938 : dès qu’une recherche est saisie, plus aucun onglet n’est
 * sélectionné, mais celui du groupe reste dans l’ordre de tabulation.
 * La liste, elle, ignore le groupe.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { CapabilityCenter } from './CapabilityCenter';

function ongletDansLOrdre(): HTMLElement | undefined {
  return screen.getAllByRole('tab').find((onglet) => onglet.tabIndex === 0);
}

describe('CapabilityCenter : l’ordre de tabulation suit la recherche (B-1938)', () => {
  it('pendant une recherche, aucun onglet ne reste tabulable', () => {
    render(<CapabilityCenter onClose={vi.fn()} onChoose={vi.fn()} />);

    expect(ongletDansLOrdre()).toHaveAccessibleName(/Organiser mon quotidien/);
    expect(ongletDansLOrdre()).toHaveAttribute('aria-selected', 'true');

    fireEvent.change(screen.getByLabelText('Rechercher une capacité'), { target: { value: 'pipeline' } });

    expect(screen.getByRole('button', { name: /Pipeline/ })).toBeInTheDocument();
    expect(screen.getAllByRole('tab').some((onglet) => onglet.getAttribute('aria-selected') === 'true')).toBe(false);
    expect(ongletDansLOrdre()).toBeUndefined();

    fireEvent.change(screen.getByLabelText('Rechercher une capacité'), { target: { value: '' } });
    expect(ongletDansLOrdre()).toHaveAccessibleName(/Organiser mon quotidien/);
    expect(ongletDansLOrdre()).toHaveAttribute('aria-selected', 'true');
  });
});
