/**
 * B-1938 / B-2064 : une recherche désélectionne les onglets, mais garde
 * un point d’entrée clavier sur le premier. La liste ignore le groupe.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { CapabilityCenter } from './CapabilityCenter';

function ongletDansLOrdre(): HTMLElement | undefined {
  return screen.getAllByRole('tab').find((onglet) => onglet.tabIndex === 0);
}

describe('CapabilityCenter : l’ordre de tabulation suit la recherche (B-1938)', () => {
  it('pendant une recherche, seul le premier onglet reste tabulable sans être sélectionné', () => {
    render(<CapabilityCenter onClose={vi.fn()} onChoose={vi.fn()} />);

    expect(ongletDansLOrdre()).toHaveAccessibleName(/Organiser mon quotidien/);
    expect(ongletDansLOrdre()).toHaveAttribute('aria-selected', 'true');
    const onglets = screen.getAllByRole('tab');
    fireEvent.click(onglets[1]);
    expect(ongletDansLOrdre()).toBe(onglets[1]);

    fireEvent.change(screen.getByLabelText('Rechercher une capacité'), { target: { value: 'pipeline' } });

    expect(screen.getByRole('button', { name: /Pipeline/ })).toBeInTheDocument();
    expect(screen.getAllByRole('tab').some((onglet) => onglet.getAttribute('aria-selected') === 'true')).toBe(false);
    expect(screen.getAllByRole('tab').filter((onglet) => onglet.tabIndex === 0)).toEqual([onglets[0]]);

    fireEvent.change(screen.getByLabelText('Rechercher une capacité'), { target: { value: '' } });
    expect(ongletDansLOrdre()).toBe(onglets[1]);
    expect(ongletDansLOrdre()).toHaveAttribute('aria-selected', 'true');
  });

  it.each([
    ['ArrowRight', 1], ['ArrowDown', 1], ['ArrowLeft', -1], ['ArrowUp', -1],
  ])('la flèche %s fonctionne depuis l’onglet tabulable pendant une recherche', (touche, décalage) => {
    render(<CapabilityCenter onClose={vi.fn()} onChoose={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('Rechercher une capacité'), { target: { value: 'pipeline' } });
    const onglets = screen.getAllByRole('tab');
    const tabulables = onglets.filter((onglet) => onglet.tabIndex === 0);
    expect(tabulables).toEqual([onglets[0]]);
    const entrée = tabulables[0];
    expect(entrée).toHaveAttribute('aria-selected', 'false');
    entrée.focus();
    fireEvent.keyDown(entrée, { key: touche });

    const cible = onglets[(onglets.length + décalage) % onglets.length];
    expect(cible).toHaveFocus();
    expect(cible).toHaveAttribute('aria-selected', 'true');
    expect(screen.getAllByRole('tab').filter((onglet) => onglet.tabIndex === 0)).toEqual([cible]);
  });
});
