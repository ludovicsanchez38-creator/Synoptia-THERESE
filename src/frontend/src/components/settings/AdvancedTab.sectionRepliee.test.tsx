/**
 * B-357 (05/09/2026) : le bouton d'une section repliée référençait par
 * aria-controls un panneau démonté du DOM. Le panneau reste monté et masqué.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { AdvancedTab } from './AdvancedTab';

describe('AdvancedTab : aria-controls d’une section repliée (B-357)', () => {
  it('le panneau référencé existe replié (masqué) et s’affiche déplié', () => {
    render(<AdvancedTab stats={null} workingDir={null} onSelectWorkingDir={() => {}} />);
    const bouton = screen.getByRole('button', { name: 'Comportement au lancement' });
    expect(bouton).toHaveAttribute('aria-expanded', 'false');

    const panneau = document.getElementById(bouton.getAttribute('aria-controls')!);
    expect(panneau).not.toBeNull();
    expect(panneau).toHaveAttribute('hidden');

    fireEvent.click(bouton);
    expect(bouton).toHaveAttribute('aria-expanded', 'true');
    expect(panneau).not.toHaveAttribute('hidden');
  });
});
