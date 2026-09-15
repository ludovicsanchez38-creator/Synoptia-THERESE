/**
 * B-857 (cycle 9) : pendant une recherche, l'onglet d'intention restait
 * annoncé sélectionné (`aria-selected`) alors qu'il ne filtrait plus rien :
 * la mise en avant visuelle tenait compte de la requête, pas l'attribut.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { CapabilityCenter } from './CapabilityCenter';

function ongletsSelectionnes(): HTMLElement[] {
  return screen.getAllByRole('tab').filter((onglet) => onglet.getAttribute('aria-selected') === 'true');
}

describe('CapabilityCenter - B-857, aria-selected suit la recherche', () => {
  it('un seul onglet sélectionné au repos, aucun pendant une recherche', () => {
    render(<CapabilityCenter onClose={vi.fn()} onChoose={vi.fn()} />);
    expect(ongletsSelectionnes()).toHaveLength(1);

    fireEvent.change(screen.getByLabelText('Rechercher une capacité'), { target: { value: 'facture' } });
    expect(ongletsSelectionnes()).toHaveLength(0);

    fireEvent.change(screen.getByLabelText('Rechercher une capacité'), { target: { value: '' } });
    expect(ongletsSelectionnes()).toHaveLength(1);
  });
});
