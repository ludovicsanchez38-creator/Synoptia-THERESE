/**
 * Audit bêta du 27/10/2026 (A2-06, A2-07) : Gérard clique « Continuer » sans
 * nom ; le message « Le nom est obligatoire » s'affiche en haut du formulaire,
 * hors de sa vue, et rien ne bouge. Il clique trois fois et croit le bouton
 * cassé. Le refus doit ramener le focus et la vue sur le champ en faute.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ProfileStep } from './ProfileStep';

const apiMocks = vi.hoisted(() => ({ setProfile: vi.fn(), importClaudeMd: vi.fn() }));
vi.mock('../../services/api', () => apiMocks);

describe('ProfileStep : le refus du nom vide se voit', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Element.prototype.scrollIntoView = vi.fn();
  });

  it.each(['', '   ', '\t', '\n'])('nom %j : le champ prend le focus et vient à l’écran', (saisie) => {
    render(<ProfileStep onNext={vi.fn()} onBack={vi.fn()} />);
    const champ = screen.getByLabelText('Nom complet *');
    fireEvent.change(champ, { target: { value: saisie } });
    screen.getByTestId('onboarding-next-btn').focus();

    fireEvent.click(screen.getByTestId('onboarding-next-btn'));

    expect(document.activeElement).toBe(champ);
    expect(champ.scrollIntoView).toHaveBeenCalled();
    expect(apiMocks.setProfile).not.toHaveBeenCalled();
  });

  it('un nom renseigné ne déplace pas le focus vers le champ', () => {
    apiMocks.setProfile.mockReturnValue(new Promise(() => {}));
    render(<ProfileStep onNext={vi.fn()} onBack={vi.fn()} />);
    const champ = screen.getByLabelText('Nom complet *');
    fireEvent.change(champ, { target: { value: 'Gérard Martin' } });
    const bouton = screen.getByTestId('onboarding-next-btn');
    bouton.focus();

    fireEvent.click(bouton);

    expect(champ.scrollIntoView).not.toHaveBeenCalled();
  });
});
