/**
 * Cycle 6, lecteur #144 (CreateCommandForm.tsx) : le bouton de retour n'avait
 * que l'icône pour contenu, sans aria-label ni type="button" ; il s'annonçait
 * « bouton » (même famille que B-285).
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { CreateCommandForm } from './CreateCommandForm';

describe('#144 : le retour du formulaire de commande a un nom', () => {
  it('est un bouton nommé « Retour », de type button', () => {
    render(<CreateCommandForm onSubmit={vi.fn()} onBack={vi.fn()} />);
    const retour = screen.getByRole('button', { name: /Retour/ });
    expect(retour).toHaveAttribute('type', 'button');
    expect(retour).toHaveAttribute('aria-label', 'Retour');
  });
});
