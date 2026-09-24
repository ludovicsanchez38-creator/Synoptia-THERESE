/**
 * P-098 (acceptée par Ludo le 24/09/2026, suggestion S3 de Dr_logic-3D) : les
 * cartes portaient les badges PARCOURS, VUE et ACTION, mais la légende ne
 * parlait que de « Vue », « Parcours » et « Demande relue ». « Action »
 * n'était expliqué nulle part, alors qu'une carte « Action » s'ouvre au clic
 * comme une Vue. Règle : un seul mot par catégorie, le même sur le badge et
 * dans la légende.
 */
import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { CapabilityCenter } from './CapabilityCenter';

describe('P-098 : chaque mot de badge est expliqué, à l’identique, dans la légende', () => {
  it('sur tous les onglets, aucun badge n’échappe à la légende, et « Action » n’existe plus', () => {
    render(<CapabilityCenter onClose={vi.fn()} onChoose={vi.fn()} />);
    const dialogue = screen.getByRole('dialog');
    const legende = dialogue.querySelector('footer')?.textContent ?? '';
    const onglets = within(dialogue).getAllByRole('tab');
    const vus = new Set<string>();
    for (const onglet of onglets) {
      fireEvent.click(onglet);
      for (const carte of within(dialogue).getAllByRole('button').filter((b) => b.querySelector('b'))) {
        const badge = carte.querySelector('b')?.parentElement?.nextElementSibling?.textContent?.trim();
        if (badge) vus.add(badge);
      }
    }
    expect([...vus].sort()).toEqual(['Demande relue', 'Parcours', 'Vue']);
    for (const mot of vus) expect(legende, mot).toContain(mot);
  });
});
